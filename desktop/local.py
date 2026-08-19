import io
import locale
import math
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pymupdf
from PIL import Image, UnidentifiedImageError

from PySide6.QtCore import (
    QPoint,
    QRect,
    QSize,
    Qt,
    QThread,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QImage,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

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


APP_NAME = "Assinador Digital"
APP_VERSION = "1.0.0"

STAMP_WIDTH = 240
STAMP_HEIGHT = 68

MAX_PDF_SIZE = 25 * 1024 * 1024
MAX_CERTIFICATE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4000

FULL_SIGNATURE_RATIO = 2.2

ALLOWED_IMAGE_FORMATS = {
    "PNG",
    "JPEG",
}

Image.MAX_IMAGE_PIXELS = (
    MAX_IMAGE_DIMENSION
    * MAX_IMAGE_DIMENSION
)

try:
    APP_TIMEZONE = ZoneInfo(
        "America/Sao_Paulo"
    )
except Exception:
    APP_TIMEZONE = ZoneInfo(
        "UTC"
    )


TRANSLATIONS = {
    "pt": {
        "app_title": "Assinador Digital",
        "step_1": "Etapa 1 de 5: Documento",
        "step_2": "Etapa 2 de 5: Posicionamento",
        "step_3": "Etapa 3 de 5: Tipo de assinatura",
        "step_4": "Etapa 4 de 5: Configuração",
        "step_5": "Etapa 5 de 5: Concluído",
        "select_pdf_title": "Selecione o documento PDF",
        "select_pdf_desc": (
            "O documento permanecerá somente neste computador."
        ),
        "select_pdf": "Selecionar documento PDF",
        "pdf_selected": "Documento selecionado:",
        "invalid_pdf": "Selecione um documento PDF válido.",
        "pdf_too_large": "O PDF deve ter no máximo 25 MB.",
        "open_pdf_error": "Não foi possível abrir o documento PDF.",
        "position_title": "Posicione a assinatura",
        "position_desc": (
            "Clique na página para posicionar a assinatura "
            "ou utilize os controles de posicionamento acessível."
        ),
        "previous": "Anterior",
        "next": "Próxima",
        "page": "Página {current} de {total}",
        "accessible_position": "Posicionamento acessível",
        "accessible_page": "Página:",
        "accessible_location": "Posição:",
        "apply_position": "Aplicar posição",
        "visual_click": "Clique visual",
        "top_left": "Canto superior esquerdo",
        "top_right": "Canto superior direito",
        "bottom_left": "Canto inferior esquerdo",
        "bottom_right": "Canto inferior direito",
        "center": "Centro",
        "position_set": "Assinatura posicionada na página {page}.",
        "position_required": (
            "Defina a posição da assinatura antes de continuar."
        ),
        "cancel": "Cancelar",
        "back": "Voltar",
        "continue": "Continuar",
        "signature_type_title": (
            "Qual tipo de assinatura deseja utilizar?"
        ),
        "signature_type_desc": (
            "A opção escolhida altera somente a aparência visual. "
            "A assinatura criptográfica continua sendo PAdES."
        ),
        "standard": "Padrão",
        "standard_desc": (
            "Identidade visual própria do projeto, "
            "nome do titular e informações da assinatura."
        ),
        "simple": "Customizada simples",
        "simple_desc": (
            "Permite personalizar o título e "
            "as informações exibidas."
        ),
        "image": "Customizada com imagem",
        "image_desc": (
            "Permite utilizar logotipo ou "
            "uma imagem completa de assinatura."
        ),
        "configuration": "Configurar assinatura",
        "custom_title": "Texto superior:",
        "show_date": "Mostrar data",
        "show_time": "Mostrar hora",
        "show_type": "Mostrar “Assinatura digital PAdES”",
        "image_file": "Imagem personalizada:",
        "select_image": "Selecionar imagem",
        "no_image": "Nenhuma imagem selecionada",
        "image_mode": "Tratamento da imagem:",
        "auto": "Detectar automaticamente",
        "full": "Imagem completa",
        "logo": "Logotipo / imagem lateral",
        "image_detected_full": "Detectada como assinatura completa",
        "image_detected_logo": "Detectada como logotipo/imagem lateral",
        "invalid_image": "Utilize somente imagens PNG ou JPEG.",
        "image_too_large": "A imagem deve ter no máximo 2 MB.",
        "certificate": "Certificado (.p12 / .pfx):",
        "select_certificate": "Selecionar certificado",
        "no_certificate": "Nenhum certificado selecionado",
        "password": "Senha do certificado:",
        "sign": "Assinar documento",
        "signing": "Assinando documento...",
        "certificate_required": (
            "Selecione o certificado e informe a senha."
        ),
        "image_required": (
            "Selecione uma imagem para a assinatura "
            "customizada com imagem."
        ),
        "save_title": "Salvar documento assinado",
        "success": "Documento assinado!",
        "success_desc": (
            "A assinatura PAdES foi aplicada com sucesso."
        ),
        "signed_file": "Documento salvo em:",
        "open_folder": "Abrir pasta",
        "sign_another": "Assinar outro documento",
        "error": "Erro",
        "success_dialog": "Documento assinado com sucesso.",
        "language": "EN",
        "toggle_language": "Mudar idioma para inglês",
        "toggle_theme": "Alternar tema",
        "ready": "Pronto",
        "signed_by": "Assinado digitalmente por",
        "certificate_holder": "Nome do titular",
        "date": "Data",
        "time": "Hora",
        "pades": "Assinatura digital PAdES",
        "password_accessible": (
            "Senha utilizada somente para desbloquear "
            "o certificado durante a assinatura."
        ),
    },

    "en": {
        "app_title": "Digital Signer",
        "step_1": "Step 1 of 5: Document",
        "step_2": "Step 2 of 5: Placement",
        "step_3": "Step 3 of 5: Signature type",
        "step_4": "Step 4 of 5: Configuration",
        "step_5": "Step 5 of 5: Completed",
        "select_pdf_title": "Select the PDF document",
        "select_pdf_desc": (
            "The document will remain only on this computer."
        ),
        "select_pdf": "Select PDF document",
        "pdf_selected": "Selected document:",
        "invalid_pdf": "Select a valid PDF document.",
        "pdf_too_large": "The PDF must be no larger than 25 MB.",
        "open_pdf_error": "Unable to open the PDF document.",
        "position_title": "Position the signature",
        "position_desc": (
            "Click on the page to position the signature "
            "or use the accessible placement controls."
        ),
        "previous": "Previous",
        "next": "Next",
        "page": "Page {current} of {total}",
        "accessible_position": "Accessible placement",
        "accessible_page": "Page:",
        "accessible_location": "Position:",
        "apply_position": "Apply position",
        "visual_click": "Visual click",
        "top_left": "Top left",
        "top_right": "Top right",
        "bottom_left": "Bottom left",
        "bottom_right": "Bottom right",
        "center": "Center",
        "position_set": "Signature positioned on page {page}.",
        "position_required": (
            "Define the signature position before continuing."
        ),
        "cancel": "Cancel",
        "back": "Back",
        "continue": "Continue",
        "signature_type_title": (
            "Which signature type would you like to use?"
        ),
        "signature_type_desc": (
            "The selected option changes only the visual appearance. "
            "The cryptographic signature remains PAdES."
        ),
        "standard": "Standard",
        "standard_desc": (
            "Project visual identity, certificate holder name "
            "and signature information."
        ),
        "simple": "Simple custom",
        "simple_desc": (
            "Allows you to customize the title "
            "and displayed information."
        ),
        "image": "Custom with image",
        "image_desc": (
            "Allows you to use a logo "
            "or a complete signature image."
        ),
        "configuration": "Configure signature",
        "custom_title": "Top text:",
        "show_date": "Show date",
        "show_time": "Show time",
        "show_type": "Show “PAdES digital signature”",
        "image_file": "Custom image:",
        "select_image": "Select image",
        "no_image": "No image selected",
        "image_mode": "Image treatment:",
        "auto": "Detect automatically",
        "full": "Complete image",
        "logo": "Logo / side image",
        "image_detected_full": "Detected as complete signature",
        "image_detected_logo": "Detected as logo/side image",
        "invalid_image": "Use PNG or JPEG images only.",
        "image_too_large": "The image must be no larger than 2 MB.",
        "certificate": "Certificate (.p12 / .pfx):",
        "select_certificate": "Select certificate",
        "no_certificate": "No certificate selected",
        "password": "Certificate password:",
        "sign": "Sign document",
        "signing": "Signing document...",
        "certificate_required": (
            "Select the certificate and enter its password."
        ),
        "image_required": (
            "Select an image for the custom image signature."
        ),
        "save_title": "Save signed document",
        "success": "Document signed!",
        "success_desc": (
            "The PAdES signature was successfully applied."
        ),
        "signed_file": "Document saved to:",
        "open_folder": "Open folder",
        "sign_another": "Sign another document",
        "error": "Error",
        "success_dialog": "Document signed successfully.",
        "language": "PT",
        "toggle_language": "Change language to Portuguese",
        "toggle_theme": "Toggle theme",
        "ready": "Ready",
        "signed_by": "Digitally signed by",
        "certificate_holder": "Certificate holder",
        "date": "Date",
        "time": "Time",
        "pades": "PAdES digital signature",
        "password_accessible": (
            "Password used only to unlock the certificate "
            "during the signing process."
        ),
    },
}


def detectar_idioma():
    try:
        idioma = locale.getlocale()[0] or ""
    except Exception:
        idioma = ""

    return (
        "pt"
        if idioma.lower().startswith("pt")
        else "en"
    )


def agora():
    return datetime.now(
        APP_TIMEZONE
    )


def criar_temporario(suffix):
    fd, caminho = tempfile.mkstemp(
        suffix=suffix
    )

    try:
        os.chmod(
            caminho,
            0o600,
        )
    except OSError:
        pass

    os.close(fd)

    return caminho


def remover_temporario(caminho):
    if not caminho:
        return

    try:
        if os.path.exists(caminho):
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
        nome,
    )

    nome = re.sub(
        r"[\x00-\x1f\x7f]",
        "",
        nome,
    )

    return (
        nome.strip()[:150]
        or "Assinante"
    )


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

    if (
        stringWidth(
            texto,
            fonte,
            tamanho,
        )
        <= largura_maxima
    ):
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


def formatar_data(
    mostrar_data,
    mostrar_hora,
):
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


def validar_imagem(
    caminho,
):
    if not caminho:
        return None

    tamanho = os.path.getsize(
        caminho
    )

    if tamanho > MAX_IMAGE_SIZE:
        raise ValueError(
            "A imagem deve ter no máximo 2 MB."
        )

    try:
        with Image.open(
            caminho
        ) as teste:
            teste.verify()
    except (
        UnidentifiedImageError,
        OSError,
    ):
        raise ValueError(
            "Imagem inválida."
        )

    try:
        imagem = Image.open(
            caminho
        )

        imagem.load()
    except Exception:
        raise ValueError(
            "Não foi possível processar a imagem."
        )

    if (
        imagem.format
        not in ALLOWED_IMAGE_FORMATS
    ):
        raise ValueError(
            "Utilize somente PNG ou JPEG."
        )

    if (
        imagem.width >
        MAX_IMAGE_DIMENSION
        or imagem.height >
        MAX_IMAGE_DIMENSION
    ):
        raise ValueError(
            "A resolução da imagem é excessiva."
        )

    largura_original = (
        imagem.width
    )

    altura_original = (
        imagem.height
    )

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
        "width": largura_original,
        "height": altura_original,
        "ratio": (
            largura_original
            / altura_original
        ),
    }


def determinar_modo_imagem(
    imagem_info,
    modo,
):
    if not imagem_info:
        return "default"

    if modo in {
        "full",
        "logo",
    }:
        return modo

    return (
        "full"
        if imagem_info["ratio"]
        >= FULL_SIGNATURE_RATIO
        else "logo"
    )


def desenhar_identidade_padrao(
    c,
):
    azul = HexColor(
        "#2563EB"
    )

    azul_escuro = HexColor(
        "#1E3A8A"
    )

    c.setFillColor(
        azul
    )

    c.circle(
        25,
        34,
        18,
        fill=1,
        stroke=0,
    )

    c.setStrokeColor(
        white
    )

    c.setLineWidth(
        3
    )

    c.setLineCap(
        1
    )

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

    c.setLineWidth(
        0.7
    )

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
        max_width
        / largura_original,
        max_height
        / altura_original,
    )

    largura = (
        largura_original
        * escala
    )

    altura = (
        altura_original
        * escala
    )

    x = (
        5
        + (
            max_width
            - largura
        ) / 2
    )

    y = (
        10
        + (
            max_height
            - altura
        ) / 2
    )

    buffer.seek(0)

    c.drawImage(
        ImageReader(
            buffer
        ),
        x,
        y,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask="auto",
    )

    c.setStrokeColor(
        HexColor(
            "#CBD5E1"
        )
    )

    c.setLineWidth(
        0.7
    )

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
        11
        if texto_data
        else 3
    )

    area_width = (
        STAMP_WIDTH
        - margem_x * 2
    )

    area_height = (
        STAMP_HEIGHT
        - margem_superior
        - faixa_inferior
    )

    escala = min(
        area_width
        / largura_original,
        area_height
        / altura_original,
    )

    largura = (
        largura_original
        * escala
    )

    altura = (
        altura_original
        * escala
    )

    x = (
        STAMP_WIDTH
        - largura
    ) / 2

    y = (
        faixa_inferior
        + (
            area_height
            - altura
        ) / 2
    )

    buffer.seek(0)

    c.drawImage(
        ImageReader(
            buffer
        ),
        x,
        y,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask="auto",
    )

    if texto_data:
        c.setStrokeColor(
            HexColor(
                "#E2E8F0"
            )
        )

        c.setLineWidth(
            0.4
        )

        c.line(
            4,
            11,
            STAMP_WIDTH - 4,
            11,
        )

        c.setFillColor(
            HexColor(
                "#475569"
            )
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


def criar_carimbo_textual(
    nome_assinante,
    titulo,
    mostrar_data,
    mostrar_hora,
    mostrar_tipo,
    imagem_info=None,
):
    caminho = criar_temporario(
        ".pdf"
    )

    c = canvas.Canvas(
        caminho,
        pagesize=(
            STAMP_WIDTH,
            STAMP_HEIGHT,
        ),
    )

    c.setFillColor(
        white
    )

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

    titulo = (
        str(titulo).strip()[:60]
        or "Assinado digitalmente por"
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

    c.setFillColor(
        black
    )

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

    texto_data = formatar_data(
        mostrar_data,
        mostrar_hora,
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
    mostrar_data,
    mostrar_hora,
):
    caminho = criar_temporario(
        ".pdf"
    )

    c = canvas.Canvas(
        caminho,
        pagesize=(
            STAMP_WIDTH,
            STAMP_HEIGHT,
        ),
    )

    c.setFillColor(
        white
    )

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
        formatar_data(
            mostrar_data,
            mostrar_hora,
        ),
    )

    c.save()

    return caminho


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

    if isinstance(
        resultado,
        tuple,
    ):
        page_ref = (
            resultado[0]
        )
    else:
        page_ref = (
            resultado
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


def obter_caixa_pagina(
    page,
):
    box = page.get(
        "/CropBox"
    )

    if box is None:
        box = page.get(
            "/MediaBox"
        )

    if box is None:
        raise ValueError(
            "Não foi possível determinar "
            "as dimensões da página."
        )

    if hasattr(
        box,
        "get_object",
    ):
        box = (
            box.get_object()
        )

    x0 = float(
        box[0]
    )

    y0 = float(
        box[1]
    )

    x1 = float(
        box[2]
    )

    y1 = float(
        box[3]
    )

    return (
        x0,
        y0,
        x1 - x0,
        y1 - y0,
    )


def assinar_documento(
    pdf_path,
    certificado_path,
    senha,
    output_path,
    page_index,
    x_pdf,
    y_pdf,
    signature_type,
    titulo,
    mostrar_data,
    mostrar_hora,
    mostrar_tipo,
    imagem_path=None,
    modo_imagem="auto",
):
    caminho_p12 = None
    caminho_carimbo = None

    try:
        if (
            os.path.getsize(pdf_path)
            > MAX_PDF_SIZE
        ):
            raise ValueError(
                "O PDF excede 25 MB."
            )

        if (
            os.path.getsize(
                certificado_path
            )
            > MAX_CERTIFICATE_SIZE
        ):
            raise ValueError(
                "O certificado excede 5 MB."
            )

        with open(
            pdf_path,
            "rb",
        ) as arquivo_pdf:
            pdf_bytes = (
                arquivo_pdf.read()
            )

        inicio_pdf = pdf_bytes.find(
            b"%PDF",
            0,
            1024,
        )

        if inicio_pdf == -1:
            raise ValueError(
                "O documento não possui "
                "cabeçalho PDF válido."
            )

        pdf_stream = io.BytesIO(
            pdf_bytes[
                inicio_pdf:
            ]
        )

        caminho_p12 = criar_temporario(
            ".p12"
        )

        with open(
            certificado_path,
            "rb",
        ) as origem:
            p12_bytes = (
                origem.read()
            )

        with open(
            caminho_p12,
            "wb",
        ) as destino:
            destino.write(
                p12_bytes
            )

        signer = (
            SimpleSigner
            .load_pkcs12(
                pfx_file=caminho_p12,
                passphrase=senha.encode(
                    "utf-8"
                ),
            )
        )

        if signer is None:
            raise ValueError(
                "Não foi possível carregar "
                "o certificado. Verifique "
                "o arquivo e a senha."
            )

        remover_temporario(
            caminho_p12
        )

        caminho_p12 = None

        nome_assinante = (
            obter_nome_assinante(
                signer
            )
        )

        imagem_info = None
        modo_detectado = (
            "default"
        )

        if (
            signature_type
            == "image"
        ):
            if not imagem_path:
                raise ValueError(
                    "Imagem personalizada ausente."
                )

            imagem_info = validar_imagem(
                imagem_path
            )

            modo_detectado = (
                determinar_modo_imagem(
                    imagem_info,
                    modo_imagem,
                )
            )

        if (
            signature_type == "image"
            and modo_detectado == "full"
        ):
            caminho_carimbo = (
                criar_carimbo_imagem_completa(
                    imagem_info,
                    mostrar_data,
                    mostrar_hora,
                )
            )
        else:
            if (
                signature_type
                == "standard"
            ):
                titulo = (
                    "Assinado digitalmente por"
                )

            caminho_carimbo = (
                criar_carimbo_textual(
                    nome_assinante,
                    titulo,
                    mostrar_data,
                    mostrar_hora,
                    mostrar_tipo,
                    (
                        imagem_info
                        if (
                            signature_type
                            == "image"
                        )
                        else None
                    ),
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

        pdf_stream.seek(
            0
        )

        writer = (
            IncrementalPdfFileWriter(
                pdf_stream
            )
        )

        page = obter_pagina_writer(
            writer,
            page_index,
        )

        (
            page_x0,
            page_y0,
            pdf_width,
            pdf_height,
        ) = obter_caixa_pagina(
            page
        )

        max_x = max(
            page_x0,
            page_x0
            + pdf_width
            - STAMP_WIDTH,
        )

        max_y = max(
            page_y0,
            page_y0
            + pdf_height
            - STAMP_HEIGHT,
        )

        x_pdf = max(
            page_x0,
            min(
                x_pdf,
                max_x,
            ),
        )

        y_pdf = max(
            page_y0,
            min(
                y_pdf,
                max_y,
            ),
        )

        field_name = (
            "Assinatura_"
            + uuid.uuid4().hex[:12]
        )

        append_signature_field(
            writer,
            SigFieldSpec(
                sig_field_name=field_name,
                on_page=page_index,
                box=(
                    x_pdf,
                    y_pdf,
                    x_pdf
                    + STAMP_WIDTH,
                    y_pdf
                    + STAMP_HEIGHT,
                ),
            ),
        )

        metadata = (
            signers
            .PdfSignatureMetadata(
                field_name=field_name,
                md_algorithm="sha256",
                subfilter=(
                    SigSeedSubFilter.PADES
                ),
            )
        )

        pdf_signer = (
            signers.PdfSigner(
                signature_meta=metadata,
                signer=signer,
                stamp_style=estilo_carimbo,
            )
        )

        output_stream = (
            pdf_signer.sign_pdf(
                writer
            )
        )

        output_stream.seek(
            0
        )

        with open(
            output_path,
            "wb",
        ) as output_file:
            output_file.write(
                output_stream.read()
            )

        return {
            "output": output_path,
            "signer": nome_assinante,
            "image_mode": modo_detectado,
        }

    finally:
        remover_temporario(
            caminho_p12
        )

        remover_temporario(
            caminho_carimbo
        )


class SignWorker(QThread):
    success = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        kwargs,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.kwargs = kwargs

    def run(self):
        try:
            resultado = (
                assinar_documento(
                    **self.kwargs
                )
            )

            self.success.emit(
                resultado
            )

        except Exception as exc:
            self.failed.emit(
                str(exc)
            )


class PdfCanvas(QLabel):
    positionChanged = Signal(
        float,
        float,
    )

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setMouseTracking(
            True
        )

        self.base_pixmap = None

        self.render_scale = 1.0

        self.signature_left = None
        self.signature_top = None

        self.setAccessibleName(
            "Página do documento PDF"
        )

        self.setAccessibleDescription(
            "Clique para posicionar "
            "a assinatura visual."
        )

    def set_page_pixmap(
        self,
        pixmap,
        render_scale,
    ):
        self.base_pixmap = (
            pixmap
        )

        self.render_scale = (
            render_scale
        )

        self.signature_left = None
        self.signature_top = None

        self.setFixedSize(
            pixmap.size()
        )

        self.update()

    def clear_signature(
        self,
    ):
        self.signature_left = None
        self.signature_top = None

        self.update()

    def set_signature_position(
        self,
        left,
        top,
        emit_signal=True,
    ):
        if (
            self.base_pixmap
            is None
        ):
            return

        width = (
            STAMP_WIDTH
            * self.render_scale
        )

        height = (
            STAMP_HEIGHT
            * self.render_scale
        )

        max_left = max(
            0,
            self.width()
            - width,
        )

        max_top = max(
            0,
            self.height()
            - height,
        )

        left = max(
            0,
            min(
                float(left),
                max_left,
            ),
        )

        top = max(
            0,
            min(
                float(top),
                max_top,
            ),
        )

        self.signature_left = (
            left
        )

        self.signature_top = (
            top
        )

        self.update()

        if emit_signal:
            self.positionChanged.emit(
                left,
                top,
            )

    def mousePressEvent(
        self,
        event,
    ):
        if (
            self.base_pixmap
            is None
            or event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        width = (
            STAMP_WIDTH
            * self.render_scale
        )

        height = (
            STAMP_HEIGHT
            * self.render_scale
        )

        position = (
            event.position()
        )

        left = (
            position.x()
            - width / 2
        )

        top = (
            position.y()
            - height / 2
        )

        self.set_signature_position(
            left,
            top,
        )

    def paintEvent(
        self,
        event,
    ):
        super().paintEvent(
            event
        )

        if (
            self.base_pixmap
            is not None
        ):
            painter = QPainter(
                self
            )

            painter.drawPixmap(
                0,
                0,
                self.base_pixmap,
            )

            if (
                self.signature_left
                is not None
                and self.signature_top
                is not None
            ):
                width = (
                    STAMP_WIDTH
                    * self.render_scale
                )

                height = (
                    STAMP_HEIGHT
                    * self.render_scale
                )

                rect = QRect(
                    int(
                        self.signature_left
                    ),
                    int(
                        self.signature_top
                    ),
                    max(
                        1,
                        int(width)
                    ),
                    max(
                        1,
                        int(height)
                    ),
                )

                painter.fillRect(
                    rect,
                    QColor(
                        37,
                        99,
                        235,
                        45,
                    ),
                )

                pen = QPen(
                    QColor(
                        "#2563EB"
                    )
                )

                pen.setWidth(
                    2
                )

                pen.setStyle(
                    Qt.PenStyle.DashLine
                )

                painter.setPen(
                    pen
                )

                painter.drawRect(
                    rect
                )

                painter.setPen(
                    QColor(
                        "#1D4ED8"
                    )
                )

                font = painter.font()

                font.setBold(
                    True
                )

                font.setPointSize(
                    8
                )

                painter.setFont(
                    font
                )

                painter.drawText(
                    rect,
                    (
                        Qt.AlignmentFlag.AlignCenter
                        | Qt.TextFlag.TextWordWrap
                    ),
                    "Assinatura",
                )

            painter.end()


class MainWindow(QMainWindow):
    def __init__(
        self,
    ):
        super().__init__()

        self.language = (
            detectar_idioma()
        )

        self.theme_override = (
            None
        )

        self.pdf_path = None
        self.pdf_document = None

        self.current_page = 0
        self.total_pages = 0

        self.render_scale = 1.0

        self.position_page = None
        self.position_left_px = None
        self.position_top_px = None

        self.signature_type = (
            "standard"
        )

        self.image_path = None
        self.certificate_path = None

        self.last_output_path = None

        self.worker = None

        self.resize_timer_id = None

        self.setMinimumSize(
            900,
            650,
        )

        self.resize(
            1100,
            780,
        )

        self.create_ui()
        self.create_toolbar()
        self.apply_system_theme()
        self.retranslate_ui()
        self.go_to_step(
            0
        )

    def tr_text(
        self,
        key,
    ):
        return TRANSLATIONS[
            self.language
        ][key]

    def create_ui(
        self,
    ):
        root = QWidget(
            self
        )

        self.setCentralWidget(
            root
        )

        layout = QVBoxLayout(
            root
        )

        layout.setContentsMargins(
            28,
            22,
            28,
            28,
        )

        layout.setSpacing(
            14
        )

        self.title_label = QLabel()

        title_font = QFont()
        title_font.setPointSize(
            18
        )
        title_font.setBold(
            True
        )

        self.title_label.setFont(
            title_font
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.step_label = QLabel()

        self.step_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.step_label.setObjectName(
            "StepLabel"
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.step_label
        )

        self.stack = QStackedWidget()

        layout.addWidget(
            self.stack,
            1,
        )

        self.create_step_1()
        self.create_step_2()
        self.create_step_3()
        self.create_step_4()
        self.create_step_5()

        self.setStatusBar(
            QStatusBar()
        )

    def create_toolbar(
        self,
    ):
        toolbar = self.addToolBar(
            "Preferências"
        )

        toolbar.setMovable(
            False
        )

        spacer = QWidget()

        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        toolbar.addWidget(
            spacer
        )

        self.theme_action = QAction(
            "🌓",
            self,
        )

        self.theme_action.triggered.connect(
            self.toggle_theme
        )

        toolbar.addAction(
            self.theme_action
        )

        self.language_action = QAction(
            "EN",
            self,
        )

        self.language_action.triggered.connect(
            self.toggle_language
        )

        toolbar.addAction(
            self.language_action
        )

    def create_step_1(
        self,
    ):
        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.step1_title = QLabel()

        font = QFont()
        font.setPointSize(
            15
        )
        font.setBold(
            True
        )

        self.step1_title.setFont(
            font
        )

        self.step1_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.step1_desc = QLabel()

        self.step1_desc.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.step1_desc.setWordWrap(
            True
        )

        self.pdf_button = QPushButton()

        self.pdf_button.setMinimumSize(
            300,
            58,
        )

        self.pdf_button.clicked.connect(
            self.select_pdf
        )

        self.pdf_button.setAccessibleName(
            "Selecionar documento PDF"
        )

        self.pdf_file_label = QLabel()

        self.pdf_file_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.pdf_file_label.setWordWrap(
            True
        )

        layout.addStretch()
        layout.addWidget(
            self.step1_title
        )
        layout.addWidget(
            self.step1_desc
        )
        layout.addSpacing(
            15
        )
        layout.addWidget(
            self.pdf_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        layout.addWidget(
            self.pdf_file_label
        )
        layout.addStretch()

        self.stack.addWidget(
            page
        )

    def create_step_2(
        self,
    ):
        page = QWidget()

        root = QVBoxLayout(
            page
        )

        self.position_title = QLabel()

        font = QFont()
        font.setPointSize(
            14
        )
        font.setBold(
            True
        )

        self.position_title.setFont(
            font
        )

        self.position_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.position_desc = QLabel()

        self.position_desc.setWordWrap(
            True
        )

        self.position_desc.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        root.addWidget(
            self.position_title
        )

        root.addWidget(
            self.position_desc
        )

        nav = QHBoxLayout()

        self.prev_button = QPushButton()

        self.prev_button.clicked.connect(
            lambda:
                self.change_page(-1)
        )

        self.page_label = QLabel()

        self.page_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.next_button = QPushButton()

        self.next_button.clicked.connect(
            lambda:
                self.change_page(1)
        )

        nav.addStretch()
        nav.addWidget(
            self.prev_button
        )
        nav.addWidget(
            self.page_label
        )
        nav.addWidget(
            self.next_button
        )
        nav.addStretch()

        root.addLayout(
            nav
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            False
        )

        self.scroll_area.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.pdf_canvas = PdfCanvas()

        self.pdf_canvas.positionChanged.connect(
            self.visual_position_changed
        )

        self.scroll_area.setWidget(
            self.pdf_canvas
        )

        root.addWidget(
            self.scroll_area,
            1,
        )

        accessible_frame = QFrame()

        accessible_frame.setObjectName(
            "Card"
        )

        accessible_layout = QFormLayout(
            accessible_frame
        )

        self.accessible_title = QLabel()

        accessible_font = QFont()
        accessible_font.setBold(
            True
        )

        self.accessible_title.setFont(
            accessible_font
        )

        accessible_layout.addRow(
            self.accessible_title
        )

        self.accessible_page_label = QLabel()

        self.accessible_page_spin = QSpinBox()

        self.accessible_page_spin.setMinimum(
            1
        )

        self.accessible_page_spin.setAccessibleName(
            "Página da assinatura"
        )

        accessible_layout.addRow(
            self.accessible_page_label,
            self.accessible_page_spin,
        )

        self.accessible_position_label = QLabel()

        self.accessible_position_combo = QComboBox()

        self.accessible_position_combo.setAccessibleName(
            "Posição da assinatura"
        )

        accessible_layout.addRow(
            self.accessible_position_label,
            self.accessible_position_combo,
        )

        self.apply_accessible_button = QPushButton()

        self.apply_accessible_button.clicked.connect(
            self.apply_accessible_position
        )

        accessible_layout.addRow(
            self.apply_accessible_button
        )

        root.addWidget(
            accessible_frame
        )

        buttons = QHBoxLayout()

        self.cancel_button = QPushButton()

        self.cancel_button.clicked.connect(
            self.reset_app
        )

        self.position_continue_button = QPushButton()

        self.position_continue_button.clicked.connect(
            self.confirm_position
        )

        buttons.addWidget(
            self.cancel_button
        )

        buttons.addWidget(
            self.position_continue_button
        )

        root.addLayout(
            buttons
        )

        self.stack.addWidget(
            page
        )

    def create_step_3(
        self,
    ):
        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        self.type_title = QLabel()

        font = QFont()
        font.setPointSize(
            15
        )
        font.setBold(
            True
        )

        self.type_title.setFont(
            font
        )

        self.type_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.type_desc = QLabel()

        self.type_desc.setWordWrap(
            True
        )

        self.type_desc.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.type_title
        )

        layout.addWidget(
            self.type_desc
        )

        cards = QHBoxLayout()

        self.standard_button = (
            self.create_type_button(
                "standard"
            )
        )

        self.simple_button = (
            self.create_type_button(
                "simple"
            )
        )

        self.image_button = (
            self.create_type_button(
                "image"
            )
        )

        cards.addWidget(
            self.standard_button
        )

        cards.addWidget(
            self.simple_button
        )

        cards.addWidget(
            self.image_button
        )

        layout.addStretch()
        layout.addLayout(
            cards
        )
        layout.addStretch()

        self.type_back_button = QPushButton()

        self.type_back_button.clicked.connect(
            lambda:
                self.go_to_step(1)
        )

        layout.addWidget(
            self.type_back_button
        )

        self.stack.addWidget(
            page
        )

    def create_type_button(
        self,
        signature_type,
    ):
        button = QPushButton()

        button.setProperty(
            "signatureType",
            signature_type,
        )

        button.setMinimumHeight(
            150
        )

        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        button.clicked.connect(
            lambda checked=False,
            value=signature_type:
                self.select_signature_type(
                    value
                )
        )

        return button

    def create_step_4(
        self,
    ):
        page = QWidget()

        root = QVBoxLayout(
            page
        )

        self.configuration_title = QLabel()

        font = QFont()
        font.setPointSize(
            15
        )
        font.setBold(
            True
        )

        self.configuration_title.setFont(
            font
        )

        self.configuration_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        root.addWidget(
            self.configuration_title
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        content = QWidget()

        form = QFormLayout(
            content
        )

        form.setVerticalSpacing(
            12
        )

        self.custom_title_label = QLabel()

        self.custom_title_input = QLineEdit(
            "Assinado digitalmente por"
        )

        self.custom_title_input.setMaxLength(
            60
        )

        self.custom_title_input.setAccessibleName(
            "Texto superior da assinatura"
        )

        form.addRow(
            self.custom_title_label,
            self.custom_title_input,
        )

        self.show_date = QCheckBox()

        self.show_date.setChecked(
            True
        )

        form.addRow(
            self.show_date
        )

        self.show_time = QCheckBox()

        self.show_time.setChecked(
            False
        )

        form.addRow(
            self.show_time
        )

        self.show_type = QCheckBox()

        self.show_type.setChecked(
            True
        )

        form.addRow(
            self.show_type
        )

        self.image_file_title = QLabel()

        image_row = QWidget()

        image_layout = QHBoxLayout(
            image_row
        )

        image_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.image_button_select = QPushButton()

        self.image_button_select.clicked.connect(
            self.select_image
        )

        self.image_file_label = QLabel()

        self.image_file_label.setWordWrap(
            True
        )

        image_layout.addWidget(
            self.image_button_select
        )

        image_layout.addWidget(
            self.image_file_label,
            1,
        )

        form.addRow(
            self.image_file_title,
            image_row,
        )

        self.image_mode_label = QLabel()

        self.image_mode_combo = QComboBox()

        self.image_mode_combo.currentIndexChanged.connect(
            self.update_image_detection
        )

        form.addRow(
            self.image_mode_label,
            self.image_mode_combo,
        )

        self.image_detection_label = QLabel()

        self.image_detection_label.setWordWrap(
            True
        )

        form.addRow(
            self.image_detection_label
        )

        self.certificate_label = QLabel()

        certificate_row = QWidget()

        certificate_layout = QHBoxLayout(
            certificate_row
        )

        certificate_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.certificate_button = QPushButton()

        self.certificate_button.clicked.connect(
            self.select_certificate
        )

        self.certificate_file_label = QLabel()

        self.certificate_file_label.setWordWrap(
            True
        )

        certificate_layout.addWidget(
            self.certificate_button
        )

        certificate_layout.addWidget(
            self.certificate_file_label,
            1,
        )

        form.addRow(
            self.certificate_label,
            certificate_row,
        )

        self.password_label = QLabel()

        self.password_input = QLineEdit()

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_input.setMaxLength(
            512
        )

        self.password_input.setAccessibleName(
            "Senha do certificado"
        )

        self.password_input.setAccessibleDescription(
            "Senha utilizada somente para "
            "desbloquear o certificado."
        )

        form.addRow(
            self.password_label,
            self.password_input,
        )

        scroll.setWidget(
            content
        )

        root.addWidget(
            scroll,
            1,
        )

        buttons = QHBoxLayout()

        self.configuration_back_button = QPushButton()

        self.configuration_back_button.clicked.connect(
            lambda:
                self.go_to_step(2)
        )

        self.sign_button = QPushButton()

        self.sign_button.clicked.connect(
            self.start_signing
        )

        buttons.addWidget(
            self.configuration_back_button
        )

        buttons.addWidget(
            self.sign_button
        )

        root.addLayout(
            buttons
        )

        self.stack.addWidget(
            page
        )

    def create_step_5(
        self,
    ):
        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        success_icon = QLabel(
            "✓"
        )

        font = QFont()
        font.setPointSize(
            38
        )
        font.setBold(
            True
        )

        success_icon.setFont(
            font
        )

        success_icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.success_title = QLabel()

        success_title_font = QFont()

        success_title_font.setPointSize(
            18
        )

        success_title_font.setBold(
            True
        )

        self.success_title.setFont(
            success_title_font
        )

        self.success_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.success_desc = QLabel()

        self.success_desc.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.output_label = QLabel()

        self.output_label.setWordWrap(
            True
        )

        self.output_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.open_folder_button = QPushButton()

        self.open_folder_button.clicked.connect(
            self.open_output_folder
        )

        self.restart_button = QPushButton()

        self.restart_button.clicked.connect(
            self.reset_app
        )

        layout.addStretch()
        layout.addWidget(
            success_icon
        )
        layout.addWidget(
            self.success_title
        )
        layout.addWidget(
            self.success_desc
        )
        layout.addWidget(
            self.output_label
        )
        layout.addWidget(
            self.open_folder_button
        )
        layout.addWidget(
            self.restart_button
        )
        layout.addStretch()

        self.stack.addWidget(
            page
        )

    def apply_system_theme(
        self,
    ):
        if self.theme_override:
            dark = (
                self.theme_override
                == "dark"
            )
        else:
            try:
                scheme = (
                    QApplication
                    .styleHints()
                    .colorScheme()
                )

                dark = (
                    scheme
                    == Qt.ColorScheme.Dark
                )
            except Exception:
                palette = (
                    QApplication
                    .palette()
                )

                color = palette.color(
                    QPalette.ColorRole.Window
                )

                dark = (
                    color.lightness()
                    < 128
                )

        self.apply_theme(
            dark
        )

    def apply_theme(
        self,
        dark,
    ):
        if dark:
            stylesheet = """
                QMainWindow, QWidget {
                    background: #0F172A;
                    color: #F8FAFC;
                }

                QLabel#StepLabel {
                    color: #94A3B8;
                }

                QFrame#Card {
                    border: 1px solid #334155;
                    border-radius: 10px;
                    padding: 8px;
                }

                QPushButton {
                    background: #3B82F6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-weight: 600;
                }

                QPushButton:hover {
                    background: #60A5FA;
                }

                QPushButton:disabled {
                    background: #475569;
                }

                QLineEdit,
                QComboBox,
                QSpinBox {
                    background: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #475569;
                    border-radius: 7px;
                    padding: 8px;
                }

                QScrollArea {
                    border: 1px solid #334155;
                    background: #111827;
                }

                QToolBar {
                    background: #0F172A;
                    border: none;
                }
            """
        else:
            stylesheet = """
                QMainWindow, QWidget {
                    background: #F8FAFC;
                    color: #1E293B;
                }

                QLabel#StepLabel {
                    color: #64748B;
                }

                QFrame#Card {
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                    padding: 8px;
                }

                QPushButton {
                    background: #2563EB;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-weight: 600;
                }

                QPushButton:hover {
                    background: #1D4ED8;
                }

                QPushButton:disabled {
                    background: #94A3B8;
                }

                QLineEdit,
                QComboBox,
                QSpinBox {
                    background: white;
                    color: #1E293B;
                    border: 1px solid #CBD5E1;
                    border-radius: 7px;
                    padding: 8px;
                }

                QScrollArea {
                    border: 1px solid #E2E8F0;
                    background: #E2E8F0;
                }

                QToolBar {
                    background: #F8FAFC;
                    border: none;
                }
            """

        QApplication.instance().setStyleSheet(
            stylesheet
        )

    def toggle_theme(
        self,
    ):
        palette = (
            QApplication
            .palette()
        )

        currently_dark = (
            palette.color(
                QPalette.ColorRole.Window
            ).lightness()
            < 128
        )

        self.theme_override = (
            "light"
            if currently_dark
            else "dark"
        )

        self.apply_theme(
            not currently_dark
        )

    def toggle_language(
        self,
    ):
        old_default = (
            TRANSLATIONS[
                self.language
            ]["signed_by"]
        )

        self.language = (
            "en"
            if self.language == "pt"
            else "pt"
        )

        if (
            not self.custom_title_input.text().strip()
            or (
                self.custom_title_input.text().strip()
                == old_default
            )
        ):
            self.custom_title_input.setText(
                self.tr_text(
                    "signed_by"
                )
            )

        self.retranslate_ui()

    def retranslate_ui(
        self,
    ):
        tr = self.tr_text

        self.setWindowTitle(
            tr(
                "app_title"
            )
        )

        self.title_label.setText(
            tr(
                "app_title"
            )
        )

        self.language_action.setText(
            tr(
                "language"
            )
        )

        self.language_action.setToolTip(
            tr(
                "toggle_language"
            )
        )

        self.theme_action.setToolTip(
            tr(
                "toggle_theme"
            )
        )

        self.step1_title.setText(
            tr(
                "select_pdf_title"
            )
        )

        self.step1_desc.setText(
            tr(
                "select_pdf_desc"
            )
        )

        self.pdf_button.setText(
            "📄  "
            + tr(
                "select_pdf"
            )
        )

        if self.pdf_path:
            self.pdf_file_label.setText(
                f"{tr('pdf_selected')} "
                f"{Path(self.pdf_path).name}"
            )
        else:
            self.pdf_file_label.setText(
                ""
            )

        self.position_title.setText(
            tr(
                "position_title"
            )
        )

        self.position_desc.setText(
            tr(
                "position_desc"
            )
        )

        self.prev_button.setText(
            "◀ "
            + tr(
                "previous"
            )
        )

        self.next_button.setText(
            tr(
                "next"
            )
            + " ▶"
        )

        self.accessible_title.setText(
            tr(
                "accessible_position"
            )
        )

        self.accessible_page_label.setText(
            tr(
                "accessible_page"
            )
        )

        self.accessible_position_label.setText(
            tr(
                "accessible_location"
            )
        )

        current_position_index = (
            self.accessible_position_combo
            .currentIndex()
        )

        self.accessible_position_combo.blockSignals(
            True
        )

        self.accessible_position_combo.clear()

        self.accessible_position_combo.addItem(
            tr(
                "top_left"
            ),
            "top_left",
        )

        self.accessible_position_combo.addItem(
            tr(
                "top_right"
            ),
            "top_right",
        )

        self.accessible_position_combo.addItem(
            tr(
                "bottom_left"
            ),
            "bottom_left",
        )

        self.accessible_position_combo.addItem(
            tr(
                "bottom_right"
            ),
            "bottom_right",
        )

        self.accessible_position_combo.addItem(
            tr(
                "center"
            ),
            "center",
        )

        if (
            0
            <= current_position_index
            < self.accessible_position_combo.count()
        ):
            self.accessible_position_combo.setCurrentIndex(
                current_position_index
            )

        self.accessible_position_combo.blockSignals(
            False
        )

        self.apply_accessible_button.setText(
            tr(
                "apply_position"
            )
        )

        self.cancel_button.setText(
            tr(
                "cancel"
            )
        )

        self.position_continue_button.setText(
            tr(
                "continue"
            )
        )

        self.type_title.setText(
            tr(
                "signature_type_title"
            )
        )

        self.type_desc.setText(
            tr(
                "signature_type_desc"
            )
        )

        self.standard_button.setText(
            f"{tr('standard')}\n\n"
            f"{tr('standard_desc')}"
        )

        self.simple_button.setText(
            f"{tr('simple')}\n\n"
            f"{tr('simple_desc')}"
        )

        self.image_button.setText(
            f"{tr('image')}\n\n"
            f"{tr('image_desc')}"
        )

        self.type_back_button.setText(
            tr(
                "back"
            )
        )

        self.configuration_title.setText(
            tr(
                "configuration"
            )
        )

        self.custom_title_label.setText(
            tr(
                "custom_title"
            )
        )

        self.show_date.setText(
            tr(
                "show_date"
            )
        )

        self.show_time.setText(
            tr(
                "show_time"
            )
        )

        self.show_type.setText(
            tr(
                "show_type"
            )
        )

        self.image_file_title.setText(
            tr(
                "image_file"
            )
        )

        self.image_button_select.setText(
            tr(
                "select_image"
            )
        )

        self.image_file_label.setText(
            (
                Path(
                    self.image_path
                ).name
                if self.image_path
                else tr(
                    "no_image"
                )
            )
        )

        self.image_mode_label.setText(
            tr(
                "image_mode"
            )
        )

        selected_mode = (
            self.image_mode_combo
            .currentData()
        )

        self.image_mode_combo.blockSignals(
            True
        )

        self.image_mode_combo.clear()

        self.image_mode_combo.addItem(
            tr(
                "auto"
            ),
            "auto",
        )

        self.image_mode_combo.addItem(
            tr(
                "full"
            ),
            "full",
        )

        self.image_mode_combo.addItem(
            tr(
                "logo"
            ),
            "logo",
        )

        for index in range(
            self.image_mode_combo.count()
        ):
            if (
                self.image_mode_combo
                .itemData(index)
                == selected_mode
            ):
                self.image_mode_combo.setCurrentIndex(
                    index
                )

                break

        self.image_mode_combo.blockSignals(
            False
        )

        self.certificate_label.setText(
            tr(
                "certificate"
            )
        )

        self.certificate_button.setText(
            tr(
                "select_certificate"
            )
        )

        self.certificate_file_label.setText(
            (
                Path(
                    self.certificate_path
                ).name
                if self.certificate_path
                else tr(
                    "no_certificate"
                )
            )
        )

        self.password_label.setText(
            tr(
                "password"
            )
        )

        self.password_input.setAccessibleDescription(
            tr(
                "password_accessible"
            )
        )

        self.configuration_back_button.setText(
            tr(
                "back"
            )
        )

        self.sign_button.setText(
            tr(
                "sign"
            )
        )

        self.success_title.setText(
            tr(
                "success"
            )
        )

        self.success_desc.setText(
            tr(
                "success_desc"
            )
        )

        self.open_folder_button.setText(
            tr(
                "open_folder"
            )
        )

        self.restart_button.setText(
            tr(
                "sign_another"
            )
        )

        self.statusBar().showMessage(
            tr(
                "ready"
            )
        )

        self.update_step_label()
        self.update_page_label()
        self.update_image_detection()

    def update_step_label(
        self,
    ):
        index = (
            self.stack.currentIndex()
        )

        key = (
            f"step_{index + 1}"
        )

        self.step_label.setText(
            self.tr_text(
                key
            )
        )

    def go_to_step(
        self,
        index,
    ):
        self.stack.setCurrentIndex(
            index
        )

        self.update_step_label()

        if index == 1:
            self.render_current_page()

    def select_pdf(
        self,
    ):
        caminho, _ = (
            QFileDialog
            .getOpenFileName(
                self,
                self.tr_text(
                    "select_pdf_title"
                ),
                "",
                "PDF (*.pdf)",
            )
        )

        if not caminho:
            return

        try:
            if (
                os.path.getsize(
                    caminho
                )
                > MAX_PDF_SIZE
            ):
                raise ValueError(
                    self.tr_text(
                        "pdf_too_large"
                    )
                )

            if (
                Path(caminho)
                .suffix
                .lower()
                != ".pdf"
            ):
                raise ValueError(
                    self.tr_text(
                        "invalid_pdf"
                    )
                )

            documento = pymupdf.open(
                caminho
            )

            if (
                documento.page_count
                < 1
            ):
                documento.close()

                raise ValueError(
                    self.tr_text(
                        "invalid_pdf"
                    )
                )

            if self.pdf_document:
                self.pdf_document.close()

            self.pdf_document = (
                documento
            )

            self.pdf_path = (
                caminho
            )

            self.current_page = (
                0
            )

            self.total_pages = (
                documento.page_count
            )

            self.accessible_page_spin.setMaximum(
                self.total_pages
            )

            self.accessible_page_spin.setValue(
                1
            )

            self.clear_position()

            self.pdf_file_label.setText(
                f"{self.tr_text('pdf_selected')} "
                f"{Path(caminho).name}"
            )

            self.go_to_step(
                1
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                self.tr_text(
                    "error"
                ),
                str(exc),
            )

    def render_current_page(
        self,
    ):
        if not self.pdf_document:
            return

        page = (
            self.pdf_document
            .load_page(
                self.current_page
            )
        )

        viewport_width = max(
            500,
            self.scroll_area
            .viewport()
            .width()
            - 30,
        )

        page_width = max(
            1.0,
            page.rect.width,
        )

        zoom = min(
            2.0,
            max(
                0.5,
                viewport_width
                / page_width,
            ),
        )

        matrix = pymupdf.Matrix(
            zoom,
            zoom,
        )

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        image_format = (
            QImage.Format.Format_RGB888
            if pix.n == 3
            else QImage.Format.Format_RGBA8888
        )

        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            image_format,
        ).copy()

        qpixmap = (
            QPixmap.fromImage(
                image
            )
        )

        self.render_scale = (
            zoom
        )

        self.pdf_canvas.set_page_pixmap(
            qpixmap,
            zoom,
        )

        if (
            self.position_page
            == self.current_page
            and self.position_left_px
            is not None
        ):
            self.pdf_canvas.set_signature_position(
                self.position_left_px,
                self.position_top_px,
                emit_signal=False,
            )

        self.update_page_label()

    def change_page(
        self,
        offset,
    ):
        new_page = (
            self.current_page
            + offset
        )

        if not (
            0
            <= new_page
            < self.total_pages
        ):
            return

        self.current_page = (
            new_page
        )

        self.accessible_page_spin.setValue(
            new_page + 1
        )

        self.render_current_page()

    def update_page_label(
        self,
    ):
        if not self.total_pages:
            return

        self.page_label.setText(
            self.tr_text(
                "page"
            )
            .replace(
                "{current}",
                str(
                    self.current_page
                    + 1
                ),
            )
            .replace(
                "{total}",
                str(
                    self.total_pages
                ),
            )
        )

        self.prev_button.setEnabled(
            self.current_page > 0
        )

        self.next_button.setEnabled(
            self.current_page
            < self.total_pages - 1
        )

    def visual_position_changed(
        self,
        left,
        top,
    ):
        self.position_page = (
            self.current_page
        )

        self.position_left_px = (
            left
        )

        self.position_top_px = (
            top
        )

        self.accessible_page_spin.setValue(
            self.current_page
            + 1
        )

        self.statusBar().showMessage(
            self.tr_text(
                "position_set"
            ).replace(
                "{page}",
                str(
                    self.current_page
                    + 1
                ),
            )
        )

    def apply_accessible_position(
        self,
    ):
        if not self.pdf_document:
            return

        page_index = (
            self.accessible_page_spin
            .value()
            - 1
        )

        self.current_page = (
            page_index
        )

        self.render_current_page()

        width = (
            STAMP_WIDTH
            * self.render_scale
        )

        height = (
            STAMP_HEIGHT
            * self.render_scale
        )

        canvas_width = (
            self.pdf_canvas.width()
        )

        canvas_height = (
            self.pdf_canvas.height()
        )

        margin = (
            18
            * self.render_scale
        )

        position = (
            self.accessible_position_combo
            .currentData()
        )

        if position == "top_left":
            left = margin
            top = margin

        elif position == "top_right":
            left = (
                canvas_width
                - width
                - margin
            )
            top = margin

        elif position == "bottom_left":
            left = margin
            top = (
                canvas_height
                - height
                - margin
            )

        elif position == "bottom_right":
            left = (
                canvas_width
                - width
                - margin
            )
            top = (
                canvas_height
                - height
                - margin
            )

        else:
            left = (
                canvas_width
                - width
            ) / 2

            top = (
                canvas_height
                - height
            ) / 2

        self.pdf_canvas.set_signature_position(
            left,
            top,
        )

    def confirm_position(
        self,
    ):
        if (
            self.position_page
            is None
            or self.position_left_px
            is None
        ):
            QMessageBox.warning(
                self,
                self.tr_text(
                    "error"
                ),
                self.tr_text(
                    "position_required"
                ),
            )

            return

        self.go_to_step(
            2
        )

    def select_signature_type(
        self,
        signature_type,
    ):
        self.signature_type = (
            signature_type
        )

        is_custom = (
            signature_type
            in {
                "simple",
                "image",
            }
        )

        is_image = (
            signature_type
            == "image"
        )

        self.custom_title_input.setEnabled(
            is_custom
        )

        self.image_button_select.setEnabled(
            is_image
        )

        self.image_mode_combo.setEnabled(
            is_image
        )

        self.image_file_label.setEnabled(
            is_image
        )

        self.image_detection_label.setEnabled(
            is_image
        )

        self.go_to_step(
            3
        )

    def select_image(
        self,
    ):
        caminho, _ = (
            QFileDialog
            .getOpenFileName(
                self,
                self.tr_text(
                    "select_image"
                ),
                "",
                (
                    "Images (*.png *.jpg *.jpeg);;"
                    "PNG (*.png);;"
                    "JPEG (*.jpg *.jpeg)"
                ),
            )
        )

        if not caminho:
            return

        try:
            if (
                os.path.getsize(
                    caminho
                )
                > MAX_IMAGE_SIZE
            ):
                raise ValueError(
                    self.tr_text(
                        "image_too_large"
                    )
                )

            validar_imagem(
                caminho
            )

            self.image_path = (
                caminho
            )

            self.image_file_label.setText(
                Path(
                    caminho
                ).name
            )

            self.update_image_detection()

        except Exception as exc:
            self.image_path = (
                None
            )

            QMessageBox.warning(
                self,
                self.tr_text(
                    "error"
                ),
                str(exc),
            )

    def update_image_detection(
        self,
    ):
        if not self.image_path:
            self.image_detection_label.setText(
                ""
            )

            return

        try:
            imagem_info = validar_imagem(
                self.image_path
            )

            modo = (
                self.image_mode_combo
                .currentData()
                or "auto"
            )

            detectado = (
                determinar_modo_imagem(
                    imagem_info,
                    modo,
                )
            )

            texto = (
                self.tr_text(
                    "image_detected_full"
                )
                if detectado == "full"
                else self.tr_text(
                    "image_detected_logo"
                )
            )

            self.image_detection_label.setText(
                f"{texto} — "
                f"{imagem_info['width']} × "
                f"{imagem_info['height']} px"
            )

        except Exception:
            self.image_detection_label.setText(
                ""
            )

    def select_certificate(
        self,
    ):
        caminho, _ = (
            QFileDialog
            .getOpenFileName(
                self,
                self.tr_text(
                    "select_certificate"
                ),
                "",
                (
                    "PKCS#12 (*.p12 *.pfx);;"
                    "P12 (*.p12);;"
                    "PFX (*.pfx)"
                ),
            )
        )

        if not caminho:
            return

        if (
            os.path.getsize(
                caminho
            )
            > MAX_CERTIFICATE_SIZE
        ):
            QMessageBox.warning(
                self,
                self.tr_text(
                    "error"
                ),
                "O certificado deve ter no máximo 5 MB.",
            )

            return

        self.certificate_path = (
            caminho
        )

        self.certificate_file_label.setText(
            Path(
                caminho
            ).name
        )

    def calculate_pdf_position(
        self,
    ):
        if (
            self.position_page
            is None
            or self.position_left_px
            is None
        ):
            raise ValueError(
                self.tr_text(
                    "position_required"
                )
            )

        page = (
            self.pdf_document
            .load_page(
                self.position_page
            )
        )

        # A visualização é renderizada proporcionalmente
        # em relação aos pontos da página PDF.
        pdf_width = (
            page.rect.width
        )

        pdf_height = (
            page.rect.height
        )

        visual_width = (
            self.pdf_canvas.width()
            if (
                self.current_page
                == self.position_page
            )
            else (
                pdf_width
                * self.render_scale
            )
        )

        visual_height = (
            self.pdf_canvas.height()
            if (
                self.current_page
                == self.position_page
            )
            else (
                pdf_height
                * self.render_scale
            )
        )

        ratio_x = (
            pdf_width
            / visual_width
        )

        ratio_y = (
            pdf_height
            / visual_height
        )

        x = (
            self.position_left_px
            * ratio_x
        )

        y = (
            pdf_height
            - (
                self.position_top_px
                * ratio_y
            )
            - STAMP_HEIGHT
        )

        x = max(
            0,
            min(
                x,
                max(
                    0,
                    pdf_width
                    - STAMP_WIDTH,
                ),
            ),
        )

        y = max(
            0,
            min(
                y,
                max(
                    0,
                    pdf_height
                    - STAMP_HEIGHT,
                ),
            ),
        )

        return (
            x,
            y,
        )

    def start_signing(
        self,
    ):
        if not self.pdf_path:
            return

        if (
            not self.certificate_path
            or not self.password_input.text()
        ):
            QMessageBox.warning(
                self,
                self.tr_text(
                    "error"
                ),
                self.tr_text(
                    "certificate_required"
                ),
            )

            return

        if (
            self.signature_type
            == "image"
            and not self.image_path
        ):
            QMessageBox.warning(
                self,
                self.tr_text(
                    "error"
                ),
                self.tr_text(
                    "image_required"
                ),
            )

            return

        try:
            x_pdf, y_pdf = (
                self.calculate_pdf_position()
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                self.tr_text(
                    "error"
                ),
                str(exc),
            )

            return

        original = Path(
            self.pdf_path
        )

        suggested_name = (
            original.stem
            + (
                "_assinado.pdf"
                if self.language == "pt"
                else "_signed.pdf"
            )
        )

        output_path, _ = (
            QFileDialog
            .getSaveFileName(
                self,
                self.tr_text(
                    "save_title"
                ),
                str(
                    original.parent
                    / suggested_name
                ),
                "PDF (*.pdf)",
            )
        )

        if not output_path:
            return

        if not output_path.lower().endswith(
            ".pdf"
        ):
            output_path += (
                ".pdf"
            )

        senha = (
            self.password_input.text()
        )

        self.password_input.clear()

        kwargs = {
            "pdf_path":
                self.pdf_path,

            "certificado_path":
                self.certificate_path,

            "senha":
                senha,

            "output_path":
                output_path,

            "page_index":
                self.position_page,

            "x_pdf":
                x_pdf,

            "y_pdf":
                y_pdf,

            "signature_type":
                self.signature_type,

            "titulo":
                (
                    self.custom_title_input
                    .text()
                    .strip()
                    or self.tr_text(
                        "signed_by"
                    )
                ),

            "mostrar_data":
                self.show_date
                .isChecked(),

            "mostrar_hora":
                self.show_time
                .isChecked(),

            "mostrar_tipo":
                self.show_type
                .isChecked(),

            "imagem_path":
                self.image_path,

            "modo_imagem":
                (
                    self.image_mode_combo
                    .currentData()
                    or "auto"
                ),
        }

        self.sign_button.setEnabled(
            False
        )

        self.configuration_back_button.setEnabled(
            False
        )

        self.statusBar().showMessage(
            self.tr_text(
                "signing"
            )
        )

        self.worker = SignWorker(
            kwargs,
            self,
        )

        self.worker.success.connect(
            self.signing_success
        )

        self.worker.failed.connect(
            self.signing_failed
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker.start()

    def signing_success(
        self,
        result,
    ):
        self.worker = None

        self.sign_button.setEnabled(
            True
        )

        self.configuration_back_button.setEnabled(
            True
        )

        self.certificate_path = (
            None
        )

        self.certificate_file_label.setText(
            self.tr_text(
                "no_certificate"
            )
        )

        self.last_output_path = (
            result["output"]
        )

        self.output_label.setText(
            f"{self.tr_text('signed_file')}\n"
            f"{self.last_output_path}"
        )

        self.go_to_step(
            4
        )

        self.statusBar().showMessage(
            self.tr_text(
                "success"
            )
        )

    def signing_failed(
        self,
        message,
    ):
        self.worker = None

        self.sign_button.setEnabled(
            True
        )

        self.configuration_back_button.setEnabled(
            True
        )

        self.password_input.clear()

        self.statusBar().showMessage(
            self.tr_text(
                "ready"
            )
        )

        QMessageBox.critical(
            self,
            self.tr_text(
                "error"
            ),
            message,
        )

    def open_output_folder(
        self,
    ):
        if not self.last_output_path:
            return

        folder = str(
            Path(
                self.last_output_path
            ).parent
        )

        try:
            if sys.platform.startswith(
                "win"
            ):
                os.startfile(
                    folder
                )

            elif sys.platform == "darwin":
                import subprocess

                subprocess.Popen(
                    [
                        "open",
                        folder,
                    ]
                )

            else:
                import subprocess

                subprocess.Popen(
                    [
                        "xdg-open",
                        folder,
                    ]
                )

        except Exception:
            pass

    def clear_position(
        self,
    ):
        self.position_page = (
            None
        )

        self.position_left_px = (
            None
        )

        self.position_top_px = (
            None
        )

        if hasattr(
            self,
            "pdf_canvas",
        ):
            self.pdf_canvas.clear_signature()

    def reset_app(
        self,
    ):
        if (
            self.worker
            and self.worker.isRunning()
        ):
            return

        self.password_input.clear()

        self.certificate_path = (
            None
        )

        self.image_path = (
            None
        )

        self.last_output_path = (
            None
        )

        self.pdf_path = (
            None
        )

        if self.pdf_document:
            try:
                self.pdf_document.close()
            except Exception:
                pass

        self.pdf_document = (
            None
        )

        self.current_page = (
            0
        )

        self.total_pages = (
            0
        )

        self.signature_type = (
            "standard"
        )

        self.show_date.setChecked(
            True
        )

        self.show_time.setChecked(
            False
        )

        self.show_type.setChecked(
            True
        )

        self.custom_title_input.setText(
            self.tr_text(
                "signed_by"
            )
        )

        self.image_mode_combo.setCurrentIndex(
            0
        )

        self.clear_position()

        self.pdf_canvas.clear()

        self.pdf_canvas.setFixedSize(
            QSize(
                1,
                1,
            )
        )

        self.retranslate_ui()

        self.go_to_step(
            0
        )

    def resizeEvent(
        self,
        event,
    ):
        super().resizeEvent(
            event
        )

        if (
            self.stack.currentIndex()
            == 1
            and self.pdf_document
        ):
            self.render_current_page()

    def closeEvent(
        self,
        event,
    ):
        self.password_input.clear()

        if (
            self.worker
            and self.worker.isRunning()
        ):
            self.worker.wait(
                3000
            )

        if self.pdf_document:
            try:
                self.pdf_document.close()
            except Exception:
                pass

        event.accept()


def create_application_icon():
    size = 64

    pixmap = QPixmap(
        size,
        size,
    )

    pixmap.fill(
        Qt.GlobalColor.transparent
    )

    painter = QPainter(
        pixmap
    )

    painter.setRenderHint(
        QPainter.RenderHint.Antialiasing
    )

    painter.setPen(
        Qt.PenStyle.NoPen
    )

    painter.setBrush(
        QColor(
            "#2563EB"
        )
    )

    painter.drawEllipse(
        4,
        4,
        56,
        56,
    )

    pen = QPen(
        QColor(
            "white"
        )
    )

    pen.setWidth(
        6
    )

    pen.setCapStyle(
        Qt.PenCapStyle.RoundCap
    )

    pen.setJoinStyle(
        Qt.PenJoinStyle.RoundJoin
    )

    painter.setPen(
        pen
    )

    painter.drawLine(
        QPoint(
            18,
            32,
        ),
        QPoint(
            27,
            41,
        ),
    )

    painter.drawLine(
        QPoint(
            27,
            41,
        ),
        QPoint(
            47,
            20,
        ),
    )

    painter.end()

    return QIcon(
        pixmap
    )


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    app.setApplicationVersion(
        APP_VERSION
    )

    app.setOrganizationName(
        "Assinador Digital"
    )

    app.setWindowIcon(
        create_application_icon()
    )

    window = MainWindow()

    window.setWindowIcon(
        create_application_icon()
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()