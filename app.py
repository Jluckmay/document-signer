import io
import json
import os
import re
import tempfile
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image, UnidentifiedImageError

from pyhanko import stamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import signers
from pyhanko.sign.fields import (
    SigFieldSpec,
    SigSeedSubFilter,
    append_signature_field
)
from pyhanko.sign.signers import SimpleSigner

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


app = Flask(__name__)

STAMP_WIDTH = 240
STAMP_HEIGHT = 68

MAX_UPLOAD_SIZE = 30 * 1024 * 1024
MAX_SIGNATURE_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4000

FULL_SIGNATURE_RATIO = 2.2
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG"}

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

try:
    APP_TIMEZONE = ZoneInfo(
        os.environ.get("APP_TIMEZONE", "America/Sao_Paulo")
    )
except Exception:
    APP_TIMEZONE = ZoneInfo("UTC")


ALLOWED_ORIGIN = os.environ.get(
    "ALLOWED_ORIGIN",
    "http://127.0.0.1:5500"
)

ALLOWED_ORIGINS = list(dict.fromkeys([
    ALLOWED_ORIGIN,
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000"
]))

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ALLOWED_ORIGINS
        }
    }
)


limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day"],
    storage_uri=os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )
)


def agora():
    return datetime.now(APP_TIMEZONE)


def criar_arquivo_temporario(suffix):
    fd, caminho = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return caminho


def remover_arquivo(caminho):
    if caminho and os.path.exists(caminho):
        try:
            os.remove(caminho)
        except OSError:
            pass


def normalizar_nome_assinante(nome):
    if not nome:
        return "Assinante"

    nome = str(nome).strip()

    nome = re.sub(
        r"\s*:\s*(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})\s*$",
        "",
        nome
    )

    return nome.strip() or "Assinante"


def obter_nome_assinante(signer):
    try:
        subject = signer.signing_cert.subject.native

        return normalizar_nome_assinante(
            subject.get("common_name")
        )
    except Exception:
        return "Assinante"


def ajustar_texto_largura(
    texto,
    fonte,
    tamanho_inicial,
    tamanho_minimo,
    largura_maxima
):
    texto = str(texto).strip()
    tamanho = tamanho_inicial

    while (
        tamanho > tamanho_minimo
        and stringWidth(texto, fonte, tamanho) > largura_maxima
    ):
        tamanho -= 0.2

    if stringWidth(texto, fonte, tamanho) <= largura_maxima:
        return texto, tamanho

    while (
        texto
        and stringWidth(
            texto + "...",
            fonte,
            tamanho
        ) > largura_maxima
    ):
        texto = texto[:-1]

    return texto.rstrip() + "...", tamanho


def validar_imagem_assinatura(arquivo):
    if not arquivo or not arquivo.filename:
        return None

    dados = arquivo.read()

    if not dados:
        raise ValueError("A imagem personalizada está vazia.")

    if len(dados) > MAX_SIGNATURE_IMAGE_SIZE:
        raise ValueError(
            "A imagem personalizada deve ter no máximo 2 MB."
        )

    try:
        imagem_teste = Image.open(io.BytesIO(dados))
        imagem_teste.verify()
    except (UnidentifiedImageError, OSError):
        raise ValueError(
            "A imagem personalizada não é um PNG ou JPEG válido."
        )

    imagem = Image.open(io.BytesIO(dados))

    if imagem.format not in ALLOWED_IMAGE_FORMATS:
        raise ValueError(
            "Utilize somente imagens PNG ou JPEG."
        )

    if (
        imagem.width > MAX_IMAGE_DIMENSION
        or imagem.height > MAX_IMAGE_DIMENSION
    ):
        raise ValueError(
            "A imagem personalizada possui resolução excessiva."
        )

    if imagem.width < 10 or imagem.height < 10:
        raise ValueError(
            "A imagem personalizada possui dimensões inválidas."
        )

    largura = imagem.width
    altura = imagem.height
    proporcao = largura / altura

    imagem = imagem.convert("RGBA")
    imagem.thumbnail((1200, 1200))

    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    return {
        "buffer": buffer,
        "width": largura,
        "height": altura,
        "ratio": proporcao
    }


def determinar_modo_imagem(imagem_info, modo_solicitado):
    if not imagem_info:
        return "default"

    if modo_solicitado == "full":
        return "full"

    if modo_solicitado == "logo":
        return "logo"

    if imagem_info["ratio"] >= FULL_SIGNATURE_RATIO:
        return "full"

    return "logo"


def desenhar_identidade_padrao(c):
    azul = HexColor("#2563EB")
    azul_escuro = HexColor("#1E3A8A")

    c.setFillColor(azul)
    c.circle(25, 34, 18, fill=1, stroke=0)

    c.setStrokeColor(white)
    c.setLineWidth(3)
    c.setLineCap(1)
    c.line(16, 34, 22, 28)
    c.line(22, 28, 34, 41)

    c.setStrokeColor(azul_escuro)
    c.setLineWidth(0.7)
    c.line(50, 59, 230, 59)


def desenhar_imagem_logo(c, imagem_info):
    buffer = imagem_info["buffer"]

    buffer.seek(0)
    imagem = Image.open(buffer)

    largura_original, altura_original = imagem.size

    max_width = 40
    max_height = 48

    escala = min(
        max_width / largura_original,
        max_height / altura_original
    )

    largura = largura_original * escala
    altura = altura_original * escala

    x = 5 + (max_width - largura) / 2
    y = 10 + (max_height - altura) / 2

    buffer.seek(0)

    c.drawImage(
        ImageReader(buffer),
        x,
        y,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask="auto"
    )

    c.setStrokeColor(HexColor("#CBD5E1"))
    c.setLineWidth(0.7)
    c.line(50, 59, 230, 59)


def desenhar_imagem_completa(c, imagem_info):
    buffer = imagem_info["buffer"]

    buffer.seek(0)
    imagem = Image.open(buffer)

    largura_original, altura_original = imagem.size

    margem_x = 3
    margem_superior = 3

    date_band_height = 11
    margem_inferior_imagem = date_band_height + 1

    area_width = STAMP_WIDTH - (margem_x * 2)
    area_height = (
        STAMP_HEIGHT
        - margem_superior
        - margem_inferior_imagem
    )

    escala = min(
        area_width / largura_original,
        area_height / altura_original
    )

    largura = largura_original * escala
    altura = altura_original * escala

    x = (STAMP_WIDTH - largura) / 2
    y = margem_inferior_imagem + (
        area_height - altura
    ) / 2

    buffer.seek(0)

    c.drawImage(
        ImageReader(buffer),
        x,
        y,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask="auto"
    )

    c.setStrokeColor(HexColor("#E2E8F0"))
    c.setLineWidth(0.4)
    c.line(
        4,
        date_band_height,
        STAMP_WIDTH - 4,
        date_band_height
    )

    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica", 5.8)
    c.drawRightString(
        STAMP_WIDTH - 5,
        3.2,
        f"Data: {agora().strftime('%d/%m/%Y %H:%M')}"
    )


def criar_carimbo_padrao(
    nome_assinante,
    config,
    imagem_info=None
):
    caminho = criar_arquivo_temporario(".pdf")

    c = canvas.Canvas(
        caminho,
        pagesize=(STAMP_WIDTH, STAMP_HEIGHT)
    )

    c.setFillColor(white)
    c.rect(
        0,
        0,
        STAMP_WIDTH,
        STAMP_HEIGHT,
        fill=1,
        stroke=0
    )

    if imagem_info:
        desenhar_imagem_logo(c, imagem_info)
    else:
        desenhar_identidade_padrao(c)

    titulo = str(
        config.get(
            "titulo",
            "Assinado digitalmente por"
        )
    ).strip()[:60]

    if not titulo:
        titulo = "Assinado digitalmente por"

    mostrar_data = (
        config.get("mostrarData", True) is True
    )

    mostrar_tipo = (
        config.get("mostrarTipo", True) is True
    )

    titulo_exibicao, tamanho_titulo = ajustar_texto_largura(
        titulo,
        "Helvetica",
        7.4,
        5.5,
        175
    )

    c.setFillColor(black)
    c.setFont(
        "Helvetica",
        tamanho_titulo
    )
    c.drawString(
        55,
        49,
        titulo_exibicao
    )

    nome_exibicao, tamanho_nome = ajustar_texto_largura(
        nome_assinante,
        "Helvetica-Bold",
        8.2,
        5.5,
        175
    )

    c.setFont(
        "Helvetica-Bold",
        tamanho_nome
    )
    c.drawString(
        55,
        38,
        nome_exibicao
    )

    pos_y = 27

    if mostrar_data:
        c.setFont("Helvetica", 6.9)
        c.drawString(
            55,
            pos_y,
            f"Data: {agora().strftime('%d/%m/%Y %H:%M')}"
        )
        pos_y -= 10

    if mostrar_tipo:
        c.setFillColor(HexColor("#475569"))
        c.setFont("Helvetica", 6.5)
        c.drawString(
            55,
            pos_y,
            "Assinatura digital PAdES"
        )

    c.save()

    return caminho


def criar_carimbo_imagem_completa(imagem_info):
    caminho = criar_arquivo_temporario(".pdf")

    c = canvas.Canvas(
        caminho,
        pagesize=(STAMP_WIDTH, STAMP_HEIGHT)
    )

    c.setFillColor(white)
    c.rect(
        0,
        0,
        STAMP_WIDTH,
        STAMP_HEIGHT,
        fill=1,
        stroke=0
    )

    desenhar_imagem_completa(
        c,
        imagem_info
    )

    c.save()

    return caminho


def obter_total_paginas(reader):
    pages_obj = reader.root.get("/Pages")

    if hasattr(pages_obj, "get_object"):
        pages_obj = pages_obj.get_object()

    return int(
        pages_obj.get("/Count")
    )


def obter_pagina_writer(writer, page_index):
    resultado = writer.find_page_for_modification(
        page_index
    )

    if isinstance(resultado, tuple):
        page_ref = resultado[0]
    else:
        page_ref = resultado

    if hasattr(page_ref, "get_object"):
        return page_ref.get_object()

    return page_ref


def obter_caixa_pagina(page):
    box = page.get("/CropBox")

    if box is None:
        box = page.get("/MediaBox")

    if box is None:
        raise ValueError(
            "Não foi possível determinar as dimensões da página."
        )

    if hasattr(box, "get_object"):
        box = box.get_object()

    x0 = float(box[0])
    y0 = float(box[1])
    x1 = float(box[2])
    y1 = float(box[3])

    return (
        x0,
        y0,
        x1 - x0,
        y1 - y0
    )


def converter_posicao(
    posicao,
    page_x0,
    page_y0,
    pdf_width,
    pdf_height
):
    try:
        canvas_width = float(
            posicao.get("canvasRectWidth", 0)
        )

        canvas_height = float(
            posicao.get("canvasRectHeight", 0)
        )

        front_x = float(
            posicao.get("x", 0)
        )

        front_y = float(
            posicao.get("y", 0)
        )
    except (TypeError, ValueError):
        raise ValueError(
            "Coordenadas de posicionamento inválidas."
        )

    if canvas_width <= 0 or canvas_height <= 0:
        raise ValueError(
            "Dimensões da prévia do PDF são inválidas."
        )

    ratio_x = pdf_width / canvas_width
    ratio_y = pdf_height / canvas_height

    x = (
        page_x0
        + front_x * ratio_x
    )

    y = (
        page_y0
        + pdf_height
        - (front_y * ratio_y)
        - STAMP_HEIGHT
    )

    min_x = page_x0
    min_y = page_y0

    max_x = (
        page_x0
        + max(
            0,
            pdf_width - STAMP_WIDTH
        )
    )

    max_y = (
        page_y0
        + max(
            0,
            pdf_height - STAMP_HEIGHT
        )
    )

    x = max(
        min_x,
        min(x, max_x)
    )

    y = max(
        min_y,
        min(y, max_y)
    )

    return x, y


@app.get("/api/status")
def status():
    return jsonify({
        "status": "ok",
        "servico": "assinador-digital"
    })


@app.post("/api/assinar")
@limiter.limit("5 per minute")
def assinar_pdf():
    caminho_p12 = None
    caminho_carimbo = None

    try:
        if "documento" not in request.files:
            return jsonify({
                "erro": "Documento PDF ausente."
            }), 400

        if "certificado" not in request.files:
            return jsonify({
                "erro": "Certificado digital ausente."
            }), 400

        pdf_file = request.files["documento"]
        p12_file = request.files["certificado"]

        password = request.form.get(
            "senha",
            ""
        )

        if not password:
            return jsonify({
                "erro": "A senha do certificado é obrigatória."
            }), 400

        posicao_str = request.form.get("posicao")

        if not posicao_str:
            return jsonify({
                "erro": "Posição da assinatura ausente."
            }), 400

        try:
            posicao = json.loads(posicao_str)
        except json.JSONDecodeError:
            return jsonify({
                "erro": "Dados de posicionamento inválidos."
            }), 400

        if (
            not isinstance(posicao, dict)
            or not posicao.get("placed")
        ):
            return jsonify({
                "erro": "A posição da assinatura não foi definida."
            }), 400

        config = {}

        config_str = request.form.get("visual")

        if config_str:
            try:
                config = json.loads(config_str)
            except json.JSONDecodeError:
                return jsonify({
                    "erro": "Configuração visual inválida."
                }), 400

            if not isinstance(config, dict):
                return jsonify({
                    "erro": "Configuração visual inválida."
                }), 400

        modo_imagem = request.form.get(
            "modo_imagem",
            "auto"
        ).strip().lower()

        if modo_imagem not in {
            "auto",
            "full",
            "logo"
        }:
            return jsonify({
                "erro": "Modo da imagem inválido."
            }), 400

        imagem_info = None

        if "imagem_assinatura" in request.files:
            imagem_info = validar_imagem_assinatura(
                request.files["imagem_assinatura"]
            )

        modo_detectado = determinar_modo_imagem(
            imagem_info,
            modo_imagem
        )

        pdf_bytes_raw = pdf_file.read()

        if not pdf_bytes_raw:
            return jsonify({
                "erro": "O documento PDF está vazio."
            }), 400

        inicio_pdf = pdf_bytes_raw.find(b"%PDF")

        if inicio_pdf == -1:
            return jsonify({
                "erro": "O documento enviado não possui cabeçalho PDF válido."
            }), 400

        pdf_stream = io.BytesIO(
            pdf_bytes_raw[inicio_pdf:]
        )

        p12_bytes = p12_file.read()

        if not p12_bytes:
            return jsonify({
                "erro": "O certificado enviado está vazio."
            }), 400

        caminho_p12 = criar_arquivo_temporario(
            ".p12"
        )

        with open(
            caminho_p12,
            "wb"
        ) as arquivo_p12:
            arquivo_p12.write(
                p12_bytes
            )

        signer = SimpleSigner.load_pkcs12(
            pfx_file=caminho_p12,
            passphrase=password.encode("utf-8")
        )

        if signer is None:
            return jsonify({
                "erro": (
                    "Não foi possível carregar o certificado. "
                    "Verifique o arquivo e a senha."
                )
            }), 400

        remover_arquivo(caminho_p12)
        caminho_p12 = None

        nome_assinante = obter_nome_assinante(
            signer
        )

        pdf_stream.seek(0)

        reader = PdfFileReader(
            pdf_stream
        )

        total_pages = obter_total_paginas(
            reader
        )

        try:
            page_number = int(
                posicao.get(
                    "page",
                    1
                )
            )
        except (TypeError, ValueError):
            return jsonify({
                "erro": "Número da página inválido."
            }), 400

        if (
            page_number < 1
            or page_number > total_pages
        ):
            return jsonify({
                "erro": (
                    f"Página inválida. O documento possui "
                    f"{total_pages} página(s)."
                )
            }), 400

        page_index = page_number - 1

        pdf_stream.seek(0)

        writer = IncrementalPdfFileWriter(
            pdf_stream
        )

        page = obter_pagina_writer(
            writer,
            page_index
        )

        (
            page_x0,
            page_y0,
            pdf_width,
            pdf_height
        ) = obter_caixa_pagina(page)

        x, y = converter_posicao(
            posicao,
            page_x0,
            page_y0,
            pdf_width,
            pdf_height
        )

        if modo_detectado == "full":
            caminho_carimbo = (
                criar_carimbo_imagem_completa(
                    imagem_info
                )
            )
        else:
            caminho_carimbo = criar_carimbo_padrao(
                nome_assinante,
                config,
                imagem_info
            )

        estilo_carimbo = (
            stamp.StaticStampStyle.from_pdf_file(
                caminho_carimbo,
                page_ix=0,
                border_width=0
            )
        )

        field_name = (
            f"Assinatura_{uuid.uuid4().hex[:12]}"
        )

        append_signature_field(
            writer,
            SigFieldSpec(
                sig_field_name=field_name,
                on_page=page_index,
                box=(
                    x,
                    y,
                    x + STAMP_WIDTH,
                    y + STAMP_HEIGHT
                )
            )
        )

        metadata = signers.PdfSignatureMetadata(
            field_name=field_name,
            md_algorithm="sha256",
            subfilter=SigSeedSubFilter.PADES
        )

        pdf_signer = signers.PdfSigner(
            signature_meta=metadata,
            signer=signer,
            stamp_style=estilo_carimbo
        )

        output_stream = pdf_signer.sign_pdf(
            writer
        )

        output_stream.seek(0)

        remover_arquivo(
            caminho_carimbo
        )

        caminho_carimbo = None

        response = send_file(
            output_stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="documento_assinado.pdf"
        )

        response.headers[
            "X-Signature-Image-Mode"
        ] = modo_detectado

        return response

    except ValueError as e:
        return jsonify({
            "erro": str(e)
        }), 400

    except Exception as e:
        app.logger.exception(
            "Erro ao assinar PDF: %r",
            e
        )

        return jsonify({
            "erro": (
                "Falha ao processar a assinatura. "
                "Verifique o certificado, a senha e o documento."
            )
        }), 500

    finally:
        remover_arquivo(
            caminho_p12
        )

        remover_arquivo(
            caminho_carimbo
        )


@app.errorhandler(413)
def arquivo_muito_grande(_):
    return jsonify({
        "erro": (
            "O envio excede o limite máximo "
            "permitido de 30 MB."
        )
    }), 413


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )