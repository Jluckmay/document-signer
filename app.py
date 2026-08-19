import io
import json
import os
import re
import tempfile
import uuid
import warnings
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image, UnidentifiedImageError
from werkzeug.middleware.proxy_fix import ProxyFix

from pyhanko import stamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import signers
from pyhanko.sign.fields import (
    SigFieldSpec,
    SigSeedSubFilter,
    append_signature_field,
)
from pyhanko.sign.signers import SimpleSigner

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


app = Flask(__name__)

STAMP_WIDTH = 240
STAMP_HEIGHT = 68

MAX_REQUEST_SIZE = 30 * 1024 * 1024
MAX_PDF_SIZE = 25 * 1024 * 1024
MAX_CERTIFICATE_SIZE = 5 * 1024 * 1024
MAX_SIGNATURE_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4000
MAX_PASSWORD_LENGTH = 512
MAX_JSON_FIELD_LENGTH = 10_000

FULL_SIGNATURE_RATIO = 2.2
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG"}

IS_PRODUCTION = os.environ.get(
    "APP_ENV",
    "development",
).lower() == "production"

ENFORCE_HTTPS = os.environ.get(
    "ENFORCE_HTTPS",
    "true" if IS_PRODUCTION else "false",
).lower() == "true"

REQUIRE_ORIGIN = os.environ.get(
    "REQUIRE_ORIGIN",
    "true" if IS_PRODUCTION else "false",
).lower() == "true"

app.config.update(
    MAX_CONTENT_LENGTH=MAX_REQUEST_SIZE,
    MAX_FORM_MEMORY_SIZE=1 * 1024 * 1024,
    MAX_FORM_PARTS=20,
)

trusted_hosts_env = os.environ.get(
    "TRUSTED_HOSTS",
    "",
).strip()

if trusted_hosts_env:
    app.config["TRUSTED_HOSTS"] = [
        host.strip()
        for host in trusted_hosts_env.split(",")
        if host.strip()
    ]

# Render/reverse proxy: confia em exatamente uma camada de proxy.
if IS_PRODUCTION:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )

try:
    APP_TIMEZONE = ZoneInfo(
        os.environ.get(
            "APP_TIMEZONE",
            "America/Sao_Paulo",
        )
    )
except Exception:
    APP_TIMEZONE = ZoneInfo("UTC")


def ler_origens_permitidas():
    origens = {
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://localhost:3000",
    }

    origem_principal = os.environ.get(
        "ALLOWED_ORIGIN",
        "",
    ).strip()

    if origem_principal:
        origens.add(
            origem_principal.rstrip("/")
        )

    origens_extras = os.environ.get(
        "ALLOWED_ORIGINS",
        "",
    )

    for origem in origens_extras.split(","):
        origem = origem.strip().rstrip("/")

        if origem:
            origens.add(origem)

    return sorted(origens)


ALLOWED_ORIGINS = ler_origens_permitidas()

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "expose_headers": [
                "X-Signature-Image-Mode",
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "Retry-After",
            ],
            "max_age": 600,
        }
    },
)


RATE_LIMIT_STORAGE_URI = os.environ.get(
    "RATELIMIT_STORAGE_URI",
    "memory://",
)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[
        "200 per day",
        "50 per hour",
    ],
    storage_uri=RATE_LIMIT_STORAGE_URI,
    strategy="fixed-window",
    headers_enabled=True,
)


# Evita imagens que expandem de forma excessiva após decodificação.
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_DIMENSION * MAX_IMAGE_DIMENSION

warnings.simplefilter(
    "error",
    Image.DecompressionBombWarning,
)


def agora():
    return datetime.now(APP_TIMEZONE)


def criar_arquivo_temporario(suffix):
    fd, caminho = tempfile.mkstemp(
        suffix=suffix
    )

    try:
        os.chmod(caminho, 0o600)
    except OSError:
        pass

    os.close(fd)

    return caminho


def remover_arquivo(caminho):
    if not caminho:
        return

    try:
        if os.path.exists(caminho):
            os.remove(caminho)
    except OSError:
        pass


def validar_tamanho_bytes(
    dados,
    limite,
    mensagem,
):
    if len(dados) > limite:
        raise ValueError(mensagem)


def validar_origem():
    origem = request.headers.get(
        "Origin"
    )

    if not origem:
        if REQUIRE_ORIGIN:
            return False

        return True

    return (
        origem.rstrip("/")
        in ALLOWED_ORIGINS
    )


def normalizar_nome_assinante(nome):
    if not nome:
        return "Assinante"

    nome = str(nome).strip()

    # Remove CPF somente da aparência visual.
    nome = re.sub(
        r"\s*:\s*(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})\s*$",
        "",
        nome,
    )

    nome = re.sub(
        r"[\x00-\x1f\x7f]",
        "",
        nome,
    )

    return nome.strip()[:150] or "Assinante"


def obter_nome_assinante(signer):
    try:
        subject = (
            signer
            .signing_cert
            .subject
            .native
        )

        return normalizar_nome_assinante(
            subject.get(
                "common_name"
            )
        )
    except Exception:
        return "Assinante"


def ajustar_texto_largura(
    texto,
    fonte,
    tamanho_inicial,
    tamanho_minimo,
    largura_maxima,
):
    texto = str(texto).strip()
    tamanho = tamanho_inicial

    while (
        tamanho > tamanho_minimo
        and stringWidth(
            texto,
            fonte,
            tamanho,
        ) > largura_maxima
    ):
        tamanho -= 0.2

    if stringWidth(
        texto,
        fonte,
        tamanho,
    ) <= largura_maxima:
        return texto, tamanho

    while (
        texto
        and stringWidth(
            texto + "...",
            fonte,
            tamanho,
        ) > largura_maxima
    ):
        texto = texto[:-1]

    return (
        texto.rstrip() + "...",
        tamanho,
    )


def formatar_data_assinatura(config):
    mostrar_data = (
        config.get(
            "mostrarData",
            True,
        )
        is True
    )

    mostrar_hora = (
        config.get(
            "mostrarHora",
            False,
        )
        is True
    )

    momento = agora()

    if (
        mostrar_data
        and mostrar_hora
    ):
        return momento.strftime(
            "%d/%m/%Y %H:%M"
        )

    if mostrar_data:
        return momento.strftime(
            "%d/%m/%Y"
        )

    if mostrar_hora:
        return momento.strftime(
            "%H:%M"
        )

    return ""


def validar_config_visual(config):
    if not isinstance(config, dict):
        raise ValueError(
            "Configuração visual inválida."
        )

    titulo = config.get(
        "titulo",
        "Assinado digitalmente por",
    )

    if not isinstance(titulo, str):
        raise ValueError(
            "Título da assinatura inválido."
        )

    titulo = re.sub(
        r"[\x00-\x1f\x7f]",
        " ",
        titulo,
    ).strip()[:60]

    config["titulo"] = (
        titulo
        or "Assinado digitalmente por"
    )

    for campo, padrao in (
        ("mostrarData", True),
        ("mostrarHora", False),
        ("mostrarTipo", True),
    ):
        valor = config.get(
            campo,
            padrao,
        )

        if not isinstance(valor, bool):
            raise ValueError(
                "Configuração visual inválida."
            )

        config[campo] = valor

    return config


def validar_imagem_assinatura(arquivo):
    if (
        not arquivo
        or not arquivo.filename
    ):
        return None

    dados = arquivo.read(
        MAX_SIGNATURE_IMAGE_SIZE + 1
    )

    if not dados:
        raise ValueError(
            "A imagem personalizada está vazia."
        )

    validar_tamanho_bytes(
        dados,
        MAX_SIGNATURE_IMAGE_SIZE,
        "A imagem personalizada deve ter no máximo 2 MB.",
    )

    try:
        imagem_teste = Image.open(
            io.BytesIO(dados)
        )

        imagem_teste.verify()
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValueError(
            "A imagem personalizada não é um PNG ou JPEG válido."
        )

    try:
        imagem = Image.open(
            io.BytesIO(dados)
        )

        imagem.load()
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValueError(
            "Não foi possível processar a imagem personalizada."
        )

    if (
        imagem.format
        not in ALLOWED_IMAGE_FORMATS
    ):
        raise ValueError(
            "Utilize somente imagens PNG ou JPEG."
        )

    if (
        imagem.width >
        MAX_IMAGE_DIMENSION
        or imagem.height >
        MAX_IMAGE_DIMENSION
    ):
        raise ValueError(
            "A imagem personalizada possui resolução excessiva."
        )

    if (
        imagem.width < 10
        or imagem.height < 10
    ):
        raise ValueError(
            "A imagem personalizada possui dimensões inválidas."
        )

    largura = imagem.width
    altura = imagem.height

    imagem = imagem.convert(
        "RGBA"
    )

    imagem.thumbnail(
        (1200, 1200)
    )

    buffer = io.BytesIO()

    imagem.save(
        buffer,
        format="PNG",
        optimize=True,
    )

    buffer.seek(0)

    return {
        "buffer": buffer,
        "width": largura,
        "height": altura,
        "ratio": largura / altura,
    }


def determinar_modo_imagem(
    imagem_info,
    modo_solicitado,
):
    if not imagem_info:
        return "default"

    if modo_solicitado in {
        "full",
        "logo",
    }:
        return modo_solicitado

    return (
        "full"
        if imagem_info["ratio"]
        >= FULL_SIGNATURE_RATIO
        else "logo"
    )


def desenhar_identidade_padrao(c):
    azul = HexColor(
        "#2563EB"
    )

    azul_escuro = HexColor(
        "#1E3A8A"
    )

    c.setFillColor(azul)

    c.circle(
        25,
        34,
        18,
        fill=1,
        stroke=0,
    )

    c.setStrokeColor(white)
    c.setLineWidth(3)
    c.setLineCap(1)

    c.line(
        16,
        34,
        22,
        28,
    )

    c.line(
        22,
        28,
        34,
        41,
    )

    c.setStrokeColor(
        azul_escuro
    )

    c.setLineWidth(0.7)

    c.line(
        50,
        59,
        230,
        59,
    )


def desenhar_imagem_logo(
    c,
    imagem_info,
):
    buffer = imagem_info[
        "buffer"
    ]

    buffer.seek(0)

    imagem = Image.open(
        buffer
    )

    largura_original, altura_original = (
        imagem.size
    )

    max_width = 40
    max_height = 48

    escala = min(
        max_width /
        largura_original,
        max_height /
        altura_original,
    )

    largura = (
        largura_original *
        escala
    )

    altura = (
        altura_original *
        escala
    )

    x = (
        5
        + (
            max_width -
            largura
        ) / 2
    )

    y = (
        10
        + (
            max_height -
            altura
        ) / 2
    )

    buffer.seek(0)

    c.drawImage(
        ImageReader(buffer),
        x,
        y,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask="auto",
    )

    c.setStrokeColor(
        HexColor("#CBD5E1")
    )

    c.setLineWidth(0.7)

    c.line(
        50,
        59,
        230,
        59,
    )


def desenhar_imagem_completa(
    c,
    imagem_info,
    texto_data,
):
    buffer = imagem_info[
        "buffer"
    ]

    buffer.seek(0)

    imagem = Image.open(
        buffer
    )

    largura_original, altura_original = (
        imagem.size
    )

    margem_x = 3
    margem_superior = 3
    faixa_inferior = (
        11 if texto_data else 3
    )

    area_width = (
        STAMP_WIDTH -
        margem_x * 2
    )

    area_height = (
        STAMP_HEIGHT -
        margem_superior -
        faixa_inferior
    )

    escala = min(
        area_width /
        largura_original,
        area_height /
        altura_original,
    )

    largura = (
        largura_original *
        escala
    )

    altura = (
        altura_original *
        escala
    )

    x = (
        STAMP_WIDTH -
        largura
    ) / 2

    y = (
        faixa_inferior
        + (
            area_height -
            altura
        ) / 2
    )

    buffer.seek(0)

    c.drawImage(
        ImageReader(buffer),
        x,
        y,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask="auto",
    )

    if texto_data:
        c.setStrokeColor(
            HexColor("#E2E8F0")
        )

        c.setLineWidth(0.4)

        c.line(
            4,
            11,
            STAMP_WIDTH - 4,
            11,
        )

        c.setFillColor(
            HexColor("#475569")
        )

        c.setFont(
            "Helvetica",
            5.8,
        )

        c.drawRightString(
            STAMP_WIDTH - 5,
            3.2,
            texto_data,
        )


def criar_carimbo_padrao(
    nome_assinante,
    config,
    imagem_info=None,
):
    caminho = (
        criar_arquivo_temporario(
            ".pdf"
        )
    )

    c = canvas.Canvas(
        caminho,
        pagesize=(
            STAMP_WIDTH,
            STAMP_HEIGHT,
        ),
    )

    c.setFillColor(white)

    c.rect(
        0,
        0,
        STAMP_WIDTH,
        STAMP_HEIGHT,
        fill=1,
        stroke=0,
    )

    if imagem_info:
        desenhar_imagem_logo(
            c,
            imagem_info,
        )
    else:
        desenhar_identidade_padrao(
            c
        )

    titulo = config[
        "titulo"
    ]

    mostrar_tipo = (
        config[
            "mostrarTipo"
        ]
    )

    texto_data = (
        formatar_data_assinatura(
            config
        )
    )

    titulo_exibicao, tamanho_titulo = (
        ajustar_texto_largura(
            titulo,
            "Helvetica",
            7.4,
            5.5,
            175,
        )
    )

    c.setFillColor(black)

    c.setFont(
        "Helvetica",
        tamanho_titulo,
    )

    c.drawString(
        55,
        49,
        titulo_exibicao,
    )

    nome_exibicao, tamanho_nome = (
        ajustar_texto_largura(
            nome_assinante,
            "Helvetica-Bold",
            8.2,
            5.5,
            175,
        )
    )

    c.setFont(
        "Helvetica-Bold",
        tamanho_nome,
    )

    c.drawString(
        55,
        38,
        nome_exibicao,
    )

    pos_y = 27

    if texto_data:
        c.setFont(
            "Helvetica",
            6.9,
        )

        c.drawString(
            55,
            pos_y,
            texto_data,
        )

        pos_y -= 10

    if mostrar_tipo:
        c.setFillColor(
            HexColor(
                "#475569"
            )
        )

        c.setFont(
            "Helvetica",
            6.5,
        )

        c.drawString(
            55,
            pos_y,
            "Assinatura digital PAdES",
        )

    c.save()

    return caminho


def criar_carimbo_imagem_completa(
    imagem_info,
    config,
):
    caminho = (
        criar_arquivo_temporario(
            ".pdf"
        )
    )

    c = canvas.Canvas(
        caminho,
        pagesize=(
            STAMP_WIDTH,
            STAMP_HEIGHT,
        ),
    )

    c.setFillColor(white)

    c.rect(
        0,
        0,
        STAMP_WIDTH,
        STAMP_HEIGHT,
        fill=1,
        stroke=0,
    )

    desenhar_imagem_completa(
        c,
        imagem_info,
        formatar_data_assinatura(
            config
        ),
    )

    c.save()

    return caminho


def obter_total_paginas(reader):
    pages_obj = (
        reader.root.get(
            "/Pages"
        )
    )

    if hasattr(
        pages_obj,
        "get_object",
    ):
        pages_obj = (
            pages_obj.get_object()
        )

    total = int(
        pages_obj.get(
            "/Count"
        )
    )

    if total < 1:
        raise ValueError(
            "O documento não possui páginas válidas."
        )

    if total > 10_000:
        raise ValueError(
            "O documento possui páginas demais para processamento."
        )

    return total


def obter_pagina_writer(
    writer,
    page_index,
):
    resultado = (
        writer
        .find_page_for_modification(
            page_index
        )
    )

    page_ref = (
        resultado[0]
        if isinstance(
            resultado,
            tuple,
        )
        else resultado
    )

    if hasattr(
        page_ref,
        "get_object",
    ):
        return (
            page_ref
            .get_object()
        )

    return page_ref


def obter_caixa_pagina(page):
    box = page.get(
        "/CropBox"
    )

    if box is None:
        box = page.get(
            "/MediaBox"
        )

    if box is None:
        raise ValueError(
            "Não foi possível determinar as dimensões da página."
        )

    if hasattr(
        box,
        "get_object",
    ):
        box = (
            box.get_object()
        )

    x0 = float(box[0])
    y0 = float(box[1])
    x1 = float(box[2])
    y1 = float(box[3])

    largura = x1 - x0
    altura = y1 - y0

    if (
        largura <= 0
        or altura <= 0
        or largura > 20_000
        or altura > 20_000
    ):
        raise ValueError(
            "Dimensões da página PDF inválidas."
        )

    return (
        x0,
        y0,
        largura,
        altura,
    )


def converter_posicao(
    posicao,
    page_x0,
    page_y0,
    pdf_width,
    pdf_height,
):
    try:
        canvas_width = float(
            posicao.get(
                "canvasRectWidth",
                0,
            )
        )

        canvas_height = float(
            posicao.get(
                "canvasRectHeight",
                0,
            )
        )

        front_x = float(
            posicao.get(
                "x",
                0,
            )
        )

        front_y = float(
            posicao.get(
                "y",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        raise ValueError(
            "Coordenadas de posicionamento inválidas."
        )

    valores = (
        canvas_width,
        canvas_height,
        front_x,
        front_y,
    )

    if any(
        valor != valor
        or abs(valor) > 1_000_000
        for valor in valores
    ):
        raise ValueError(
            "Coordenadas de posicionamento inválidas."
        )

    if (
        canvas_width <= 0
        or canvas_height <= 0
    ):
        raise ValueError(
            "Dimensões da prévia do PDF são inválidas."
        )

    ratio_x = (
        pdf_width /
        canvas_width
    )

    ratio_y = (
        pdf_height /
        canvas_height
    )

    x = (
        page_x0
        + front_x *
        ratio_x
    )

    y = (
        page_y0
        + pdf_height
        - front_y *
        ratio_y
        - STAMP_HEIGHT
    )

    min_x = page_x0
    min_y = page_y0

    max_x = (
        page_x0
        + max(
            0,
            pdf_width -
            STAMP_WIDTH,
        )
    )

    max_y = (
        page_y0
        + max(
            0,
            pdf_height -
            STAMP_HEIGHT,
        )
    )

    return (
        max(
            min_x,
            min(
                x,
                max_x,
            ),
        ),
        max(
            min_y,
            min(
                y,
                max_y,
            ),
        ),
    )


@app.before_request
def protecoes_antes_da_requisicao():
    if (
        request.path.startswith(
            "/api/"
        )
        and not validar_origem()
    ):
        return jsonify({
            "erro": "Origem da requisição não autorizada."
        }), 403

    if (
        ENFORCE_HTTPS
        and request.path.startswith(
            "/api/"
        )
        and not request.is_secure
    ):
        return jsonify({
            "erro": "HTTPS é obrigatório."
        }), 403

    if (
        request.method == "POST"
        and request.path ==
        "/api/assinar"
    ):
        content_type = (
            request.content_type
            or ""
        ).lower()

        if not content_type.startswith(
            "multipart/form-data"
        ):
            return jsonify({
                "erro": "Content-Type inválido."
            }), 415


@app.after_request
def adicionar_headers_seguranca(response):
    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0, private"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), microphone=(), "
        "geolocation=(), payment=(), "
        "usb=(), serial=()"
    )

    response.headers[
        "Cross-Origin-Opener-Policy"
    ] = "same-origin"

    response.headers[
        "X-Permitted-Cross-Domain-Policies"
    ] = "none"

    if (
        IS_PRODUCTION
        and request.is_secure
    ):
        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )

    return response


@app.get(
    "/api/status"
)
@limiter.exempt
def status():
    return jsonify({
        "status": "ok",
        "servico": (
            "assinador-digital"
        ),
    })


@app.post(
    "/api/assinar"
)
@limiter.limit(
    "5 per minute;20 per hour"
)
def assinar_pdf():
    caminho_p12 = None
    caminho_carimbo = None
    password = None
    p12_bytes = None

    try:
        documento = (
            request.files.get(
                "documento"
            )
        )

        certificado = (
            request.files.get(
                "certificado"
            )
        )

        if (
            not documento
            or not documento.filename
        ):
            return jsonify({
                "erro": "Documento PDF ausente."
            }), 400

        if (
            not certificado
            or not certificado.filename
        ):
            return jsonify({
                "erro": "Certificado digital ausente."
            }), 400

        password = request.form.get(
            "senha",
            "",
        )

        if not password:
            return jsonify({
                "erro": "A senha do certificado é obrigatória."
            }), 400

        if (
            len(password)
            > MAX_PASSWORD_LENGTH
        ):
            return jsonify({
                "erro": "Senha do certificado inválida."
            }), 400

        tipo_assinatura = (
            request.form.get(
                "tipo_assinatura",
                "standard",
            )
            .strip()
            .lower()
        )

        if tipo_assinatura not in {
            "standard",
            "simple",
            "image",
        }:
            return jsonify({
                "erro": "Tipo de assinatura inválido."
            }), 400

        posicao_str = (
            request.form.get(
                "posicao",
                "",
            )
        )

        if (
            not posicao_str
            or len(posicao_str)
            > MAX_JSON_FIELD_LENGTH
        ):
            return jsonify({
                "erro": "Posição da assinatura inválida."
            }), 400

        try:
            posicao = json.loads(
                posicao_str
            )
        except json.JSONDecodeError:
            return jsonify({
                "erro": "Dados de posicionamento inválidos."
            }), 400

        if (
            not isinstance(
                posicao,
                dict,
            )
            or posicao.get(
                "placed"
            ) is not True
        ):
            return jsonify({
                "erro": "A posição da assinatura não foi definida."
            }), 400

        config_str = (
            request.form.get(
                "visual",
                "{}",
            )
        )

        if (
            len(config_str)
            > MAX_JSON_FIELD_LENGTH
        ):
            return jsonify({
                "erro": "Configuração visual inválida."
            }), 400

        try:
            config = json.loads(
                config_str
            )
        except json.JSONDecodeError:
            return jsonify({
                "erro": "Configuração visual inválida."
            }), 400

        config = (
            validar_config_visual(
                config
            )
        )

        imagem_info = None
        modo_detectado = (
            "default"
        )

        if tipo_assinatura == "image":
            imagem_arquivo = (
                request.files.get(
                    "imagem_assinatura"
                )
            )

            if not imagem_arquivo:
                return jsonify({
                    "erro": (
                        "A imagem personalizada é obrigatória "
                        "para este tipo de assinatura."
                    )
                }), 400

            imagem_info = (
                validar_imagem_assinatura(
                    imagem_arquivo
                )
            )

            modo_imagem = (
                request.form.get(
                    "modo_imagem",
                    "auto",
                )
                .strip()
                .lower()
            )

            if modo_imagem not in {
                "auto",
                "full",
                "logo",
            }:
                return jsonify({
                    "erro": "Modo da imagem inválido."
                }), 400

            modo_detectado = (
                determinar_modo_imagem(
                    imagem_info,
                    modo_imagem,
                )
            )

        pdf_bytes_raw = (
            documento.read(
                MAX_PDF_SIZE + 1
            )
        )

        if not pdf_bytes_raw:
            return jsonify({
                "erro": "O documento PDF está vazio."
            }), 400

        validar_tamanho_bytes(
            pdf_bytes_raw,
            MAX_PDF_SIZE,
            "O documento PDF deve ter no máximo 25 MB.",
        )

        # Só tolera pequeno prefixo antes de %PDF.
        inicio_pdf = (
            pdf_bytes_raw.find(
                b"%PDF",
                0,
                1024,
            )
        )

        if inicio_pdf == -1:
            return jsonify({
                "erro": "O documento enviado não possui cabeçalho PDF válido."
            }), 400

        pdf_bytes = (
            pdf_bytes_raw[
                inicio_pdf:
            ]
        )

        if b"%%EOF" not in (
            pdf_bytes[-8192:]
        ):
            return jsonify({
                "erro": "O arquivo não possui uma estrutura PDF final válida."
            }), 400

        pdf_stream = io.BytesIO(
            pdf_bytes
        )

        p12_bytes = (
            certificado.read(
                MAX_CERTIFICATE_SIZE + 1
            )
        )

        if not p12_bytes:
            return jsonify({
                "erro": "O certificado enviado está vazio."
            }), 400

        validar_tamanho_bytes(
            p12_bytes,
            MAX_CERTIFICATE_SIZE,
            "O certificado deve ter no máximo 5 MB.",
        )

        caminho_p12 = (
            criar_arquivo_temporario(
                ".p12"
            )
        )

        with open(
            caminho_p12,
            "wb",
        ) as arquivo_p12:
            arquivo_p12.write(
                p12_bytes
            )

            arquivo_p12.flush()

            try:
                os.fsync(
                    arquivo_p12.fileno()
                )
            except OSError:
                pass

        signer = (
            SimpleSigner
            .load_pkcs12(
                pfx_file=
                    caminho_p12,
                passphrase=
                    password.encode(
                        "utf-8"
                    ),
            )
        )

        if signer is None:
            return jsonify({
                "erro": (
                    "Não foi possível carregar o certificado. "
                    "Verifique o arquivo e a senha."
                )
            }), 400

        remover_arquivo(
            caminho_p12
        )

        caminho_p12 = None
        p12_bytes = None
        password = None

        nome_assinante = (
            obter_nome_assinante(
                signer
            )
        )

        pdf_stream.seek(0)

        reader = PdfFileReader(
            pdf_stream
        )

        total_pages = (
            obter_total_paginas(
                reader
            )
        )

        try:
            page_number = int(
                posicao.get(
                    "page",
                    1,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return jsonify({
                "erro": "Número da página inválido."
            }), 400

        if not (
            1 <=
            page_number <=
            total_pages
        ):
            return jsonify({
                "erro": (
                    f"Página inválida. "
                    f"O documento possui "
                    f"{total_pages} página(s)."
                )
            }), 400

        page_index = (
            page_number - 1
        )

        pdf_stream.seek(0)

        writer = (
            IncrementalPdfFileWriter(
                pdf_stream
            )
        )

        page = (
            obter_pagina_writer(
                writer,
                page_index,
            )
        )

        (
            page_x0,
            page_y0,
            pdf_width,
            pdf_height,
        ) = obter_caixa_pagina(
            page
        )

        x, y = converter_posicao(
            posicao,
            page_x0,
            page_y0,
            pdf_width,
            pdf_height,
        )

        if (
            tipo_assinatura ==
            "standard"
        ):
            config[
                "titulo"
            ] = (
                "Assinado digitalmente por"
            )

            caminho_carimbo = (
                criar_carimbo_padrao(
                    nome_assinante,
                    config,
                )
            )

        elif (
            tipo_assinatura ==
            "simple"
        ):
            caminho_carimbo = (
                criar_carimbo_padrao(
                    nome_assinante,
                    config,
                )
            )

        elif (
            modo_detectado ==
            "full"
        ):
            caminho_carimbo = (
                criar_carimbo_imagem_completa(
                    imagem_info,
                    config,
                )
            )

        else:
            caminho_carimbo = (
                criar_carimbo_padrao(
                    nome_assinante,
                    config,
                    imagem_info,
                )
            )

        estilo_carimbo = (
            stamp
            .StaticStampStyle
            .from_pdf_file(
                caminho_carimbo,
                page_ix=0,
                border_width=0,
            )
        )

        field_name = (
            "Assinatura_"
            + uuid.uuid4().hex[
                :12
            ]
        )

        append_signature_field(
            writer,
            SigFieldSpec(
                sig_field_name=
                    field_name,
                on_page=
                    page_index,
                box=(
                    x,
                    y,
                    x + STAMP_WIDTH,
                    y + STAMP_HEIGHT,
                ),
            ),
        )

        metadata = (
            signers
            .PdfSignatureMetadata(
                field_name=
                    field_name,
                md_algorithm=
                    "sha256",
                subfilter=
                    SigSeedSubFilter
                    .PADES,
            )
        )

        pdf_signer = (
            signers.PdfSigner(
                signature_meta=
                    metadata,
                signer=
                    signer,
                stamp_style=
                    estilo_carimbo,
            )
        )

        output_stream = (
            pdf_signer.sign_pdf(
                writer
            )
        )

        output_stream.seek(0)

        remover_arquivo(
            caminho_carimbo
        )

        caminho_carimbo = None

        response = send_file(
            output_stream,
            mimetype=
                "application/pdf",
            as_attachment=True,
            download_name=
                "documento_assinado.pdf",
            max_age=0,
        )

        response.headers[
            "Content-Security-Policy"
        ] = (
            "default-src 'none'; "
            "sandbox"
        )

        if (
            tipo_assinatura ==
            "image"
        ):
            response.headers[
                "X-Signature-Image-Mode"
            ] = (
                modo_detectado
            )

        return response

    except ValueError as erro:
        return jsonify({
            "erro": str(erro)
        }), 400

    except Exception:
        # Não registra senha, formulário,
        # certificado ou conteúdo do PDF.
        app.logger.exception(
            "Falha interna durante assinatura do PDF."
        )

        return jsonify({
            "erro": (
                "Falha ao processar a assinatura. "
                "Verifique o certificado, a senha "
                "e o documento."
            )
        }), 500

    finally:
        password = None
        p12_bytes = None

        remover_arquivo(
            caminho_p12
        )

        remover_arquivo(
            caminho_carimbo
        )


@app.errorhandler(400)
def erro_400(_):
    return jsonify({
        "erro": "Requisição inválida."
    }), 400


@app.errorhandler(413)
def arquivo_muito_grande(_):
    return jsonify({
        "erro": (
            "O envio excede o limite "
            "máximo permitido."
        )
    }), 413


@app.errorhandler(429)
def muitas_requisicoes(_):
    return jsonify({
        "erro": (
            "Muitas solicitações. "
            "Aguarde antes de tentar novamente."
        )
    }), 429


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(
            os.environ.get(
                "PORT",
                5000,
            )
        ),
        debug=False,
    )