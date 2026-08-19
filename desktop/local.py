import io
import locale
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pymupdf
from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import QPoint, QRect, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QImage, QPainter, QPalette, QPen, QPixmap
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
    QToolBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from pyhanko import stamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec, SigSeedSubFilter, append_signature_field
from pyhanko.sign.signers import SimpleSigner
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from backend.verifier import verificar_pdf

APP_NAME = "Assinador Digital"
APP_VERSION = "1.0.0"
STAMP_WIDTH = 240
STAMP_HEIGHT = 68
MAX_PDF_SIZE = 25 * 1024 * 1024
MAX_CERTIFICATE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4000
FULL_SIGNATURE_RATIO = 2.2
PDF_RENDER_QUALITY = 2.5
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG"}
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_DIMENSION * MAX_IMAGE_DIMENSION

try:
    APP_TIMEZONE = ZoneInfo("America/Sao_Paulo")
except Exception:
    APP_TIMEZONE = ZoneInfo("UTC")

TRANSLATIONS = {
    "pt": {
        "app_title": "Assinador Digital",
        "step_1": "Etapa 1 de 5: Documento",
        "step_2": "Etapa 2 de 5: Posicionamento",
        "step_3": "Etapa 3 de 5: Tipo de assinatura",
        "step_4": "Etapa 4 de 5: Configuração",
        "step_5": "Etapa 5 de 5: Concluído",
        "select_pdf_title": "Selecione o documento PDF",
        "select_pdf_desc": "O documento permanecerá somente neste computador.",
        "select_pdf": "Selecionar documento PDF",
        "pdf_selected": "Documento selecionado:",
        "invalid_pdf": "Selecione um documento PDF válido.",
        "pdf_too_large": "O PDF deve ter no máximo 25 MB.",
        "position_title": "Posicione a assinatura",
        "position_desc": "Clique na página para posicionar a assinatura. Ao chegar ao final da página, a próxima será exibida automaticamente.",
        "previous": "Anterior",
        "next": "Próxima",
        "page": "Página {current} de {total}",
        "show_accessible_position": "Utilizar posicionamento acessível",
        "accessible_position": "Posicionamento acessível",
        "accessible_page": "Página:",
        "accessible_location": "Posição:",
        "apply_position": "Aplicar posição",
        "top_left": "Canto superior esquerdo",
        "top_right": "Canto superior direito",
        "bottom_left": "Canto inferior esquerdo",
        "bottom_right": "Canto inferior direito",
        "center": "Centro",
        "position_set": "Assinatura posicionada na página {page}.",
        "position_required": "Defina a posição da assinatura antes de continuar.",
        "cancel": "Cancelar",
        "back": "Voltar",
        "continue": "Continuar",
        "signature_type_title": "Qual tipo de assinatura deseja utilizar?",
        "signature_type_desc": "A escolha altera apenas a aparência visual. A assinatura criptográfica continua sendo PAdES.",
        "standard": "Padrão",
        "standard_desc": "Identidade visual própria do projeto, nome do titular e informações da assinatura.",
        "simple": "Customizada simples",
        "simple_desc": "Permite personalizar o texto e as informações exibidas.",
        "image": "Customizada com imagem",
        "image_desc": "Permite utilizar um logotipo ou uma imagem completa de assinatura.",
        "configuration": "Configurar assinatura",
        "configuration_standard": "Assinatura padrão selecionada. Será utilizada a identidade visual própria do Assinador Digital.",
        "configuration_simple": "Assinatura customizada simples selecionada. Você pode personalizar o texto e as informações exibidas.",
        "configuration_image": "Assinatura customizada com imagem selecionada. Escolha um logotipo ou uma imagem completa de assinatura.",
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
        "certificate_too_large": "O certificado deve ter no máximo 5 MB.",
        "password": "Senha do certificado:",
        "certificate_required": "Selecione o certificado e informe a senha.",
        "image_required": "Selecione uma imagem para a assinatura customizada com imagem.",
        "sign": "Assinar documento",
        "signing": "Assinando documento...",
        "save_title": "Salvar documento assinado",
        "success": "Documento assinado!",
        "success_desc": "A assinatura PAdES foi aplicada com sucesso.",
        "signed_file": "Documento salvo em:",
        "open_folder": "Abrir pasta",
        "sign_another": "Assinar outro documento",
        "error": "Erro",
        "language": "EN",
        "toggle_language": "Mudar idioma para inglês",
        "toggle_theme": "Alternar tema",
        "ready": "Pronto",
        "signed_by": "Assinado digitalmente por:",
        "password_accessible": "Senha utilizada somente para desbloquear o certificado durante a assinatura.",
        "invalid_dimensions": "Dimensões da visualização inválidas.",
        "pkcs12_error": "Não foi possível abrir o certificado. Verifique se o arquivo e a senha estão corretos.",
        "verify_signatures": "Verificar assinaturas",
        "verify_desc": "Analise tecnicamente assinaturas digitais incorporadas a um PDF.",
        "verify_select": "Selecionar PDF para verificar",
        "verify_online": "Consultar revogação online (OCSP/CRL) quando disponível",
        "verify_processing": "Verificando assinaturas...",
        "verify_back": "Voltar ao assinador",
        "verify_notice": "Resultado técnico e informativo. Não substitui validadores oficiais e não determina validade jurídica.",
        "verify_no_signatures": "Nenhuma assinatura digital incorporada foi encontrada.",
        "verify_count": "{count} assinatura(s) encontrada(s)",
        "verify_signer": "Titular",
        "verify_issuer": "Emissor",
        "verify_infrastructure": "Infraestrutura",
        "verify_integrity": "Integridade criptográfica",
        "verify_crypto": "Assinatura criptográfica",
        "verify_trust": "Cadeia de confiança",
        "verify_revocation": "Revogação",
        "verify_valid": "Válida",
        "verify_invalid": "Inválida",
        "verify_verified": "Verificada",
        "verify_not_verified": "Não verificada",
        "verify_trusted": "Confiável no contexto atual",
        "verify_untrusted": "Confiança não estabelecida",
        "verify_revoked": "Revogado",
        "verify_not_revoked": "Nenhuma revogação detectada",
        "verify_indeterminate": "Indeterminado",
    },
    "en": {
        "app_title": "Digital Signer",
        "step_1": "Step 1 of 5: Document",
        "step_2": "Step 2 of 5: Placement",
        "step_3": "Step 3 of 5: Signature type",
        "step_4": "Step 4 of 5: Configuration",
        "step_5": "Step 5 of 5: Completed",
        "select_pdf_title": "Select the PDF document",
        "select_pdf_desc": "The document will remain only on this computer.",
        "select_pdf": "Select PDF document",
        "pdf_selected": "Selected document:",
        "invalid_pdf": "Select a valid PDF document.",
        "pdf_too_large": "The PDF must be no larger than 25 MB.",
        "position_title": "Position the signature",
        "position_desc": "Click on the page to position the signature. When you reach the bottom, the next page will be displayed automatically.",
        "previous": "Previous",
        "next": "Next",
        "page": "Page {current} of {total}",
        "show_accessible_position": "Use accessible placement",
        "accessible_position": "Accessible placement",
        "accessible_page": "Page:",
        "accessible_location": "Position:",
        "apply_position": "Apply position",
        "top_left": "Top left",
        "top_right": "Top right",
        "bottom_left": "Bottom left",
        "bottom_right": "Bottom right",
        "center": "Center",
        "position_set": "Signature positioned on page {page}.",
        "position_required": "Define the signature position before continuing.",
        "cancel": "Cancel",
        "back": "Back",
        "continue": "Continue",
        "signature_type_title": "Which signature type would you like to use?",
        "signature_type_desc": "The selected option changes only the visual appearance. The cryptographic signature remains PAdES.",
        "standard": "Standard",
        "standard_desc": "Project visual identity, certificate holder name and signature information.",
        "simple": "Simple custom",
        "simple_desc": "Allows you to customize the text and displayed information.",
        "image": "Custom with image",
        "image_desc": "Allows you to use a logo or a complete signature image.",
        "configuration": "Configure signature",
        "configuration_standard": "Standard signature selected. The Digital Signer's own visual identity will be used.",
        "configuration_simple": "Simple custom signature selected. You can customize the text and displayed information.",
        "configuration_image": "Custom image signature selected. Choose a logo or a complete signature image.",
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
        "certificate_too_large": "The certificate must be no larger than 5 MB.",
        "password": "Certificate password:",
        "certificate_required": "Select the certificate and enter its password.",
        "image_required": "Select an image for the custom image signature.",
        "sign": "Sign document",
        "signing": "Signing document...",
        "save_title": "Save signed document",
        "success": "Document signed!",
        "success_desc": "The PAdES signature was successfully applied.",
        "signed_file": "Document saved to:",
        "open_folder": "Open folder",
        "sign_another": "Sign another document",
        "error": "Error",
        "language": "PT",
        "toggle_language": "Change language to Portuguese",
        "toggle_theme": "Toggle theme",
        "ready": "Ready",
        "signed_by": "Digitally signed by:",
        "password_accessible": "Password used only to unlock the certificate during the signing process.",
        "invalid_dimensions": "Invalid preview dimensions.",
        "pkcs12_error": "Could not open the certificate. Check that the file and password are correct.",
        "verify_signatures": "Verify signatures",
        "verify_desc": "Technically analyse digital signatures embedded in a PDF.",
        "verify_select": "Select PDF to verify",
        "verify_online": "Check revocation online (OCSP/CRL) when available",
        "verify_processing": "Verifying signatures...",
        "verify_back": "Back to signer",
        "verify_notice": "Technical and informational result. It does not replace official validators and does not determine legal validity.",
        "verify_no_signatures": "No embedded digital signatures were found.",
        "verify_count": "{count} signature(s) found",
        "verify_signer": "Certificate holder",
        "verify_issuer": "Issuer",
        "verify_infrastructure": "Infrastructure",
        "verify_integrity": "Cryptographic integrity",
        "verify_crypto": "Cryptographic signature",
        "verify_trust": "Trust chain",
        "verify_revocation": "Revocation",
        "verify_valid": "Valid",
        "verify_invalid": "Invalid",
        "verify_verified": "Verified",
        "verify_not_verified": "Not verified",
        "verify_trusted": "Trusted in the current context",
        "verify_untrusted": "Trust not established",
        "verify_revoked": "Revoked",
        "verify_not_revoked": "No revocation detected",
        "verify_indeterminate": "Indeterminate",
    },
}


def detectar_idioma():
    try:
        idioma = locale.getlocale()[0] or ""
    except Exception:
        idioma = ""
    return "pt" if idioma.lower().startswith("pt") else "en"


def agora():
    return datetime.now(APP_TIMEZONE)


def criar_temporario(suffix):
    fd, caminho = tempfile.mkstemp(suffix=suffix)
    try:
        os.chmod(caminho, 0o600)
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
    nome = re.sub(r"\s*:\s*(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})\s*$", "", nome)
    nome = re.sub(r"[\x00-\x1f\x7f]", "", nome)
    return nome.strip()[:150] or "Assinante"


def obter_nome_assinante(signer):
    try:
        return normalizar_nome_assinante(signer.signing_cert.subject.native.get("common_name"))
    except Exception:
        return "Assinante"


def ajustar_texto_largura(texto, fonte, tamanho_inicial, tamanho_minimo, largura_maxima):
    texto = str(texto).strip()
    tamanho = tamanho_inicial
    while tamanho > tamanho_minimo and stringWidth(texto, fonte, tamanho) > largura_maxima:
        tamanho -= 0.2
    if stringWidth(texto, fonte, tamanho) <= largura_maxima:
        return texto, tamanho
    while texto and stringWidth(texto + "...", fonte, tamanho) > largura_maxima:
        texto = texto[:-1]
    return texto.rstrip() + "...", tamanho


def formatar_data(mostrar_data, mostrar_hora):
    momento = agora()
    if mostrar_data and mostrar_hora:
        return momento.strftime("%d/%m/%Y %H:%M")
    if mostrar_data:
        return momento.strftime("%d/%m/%Y")
    if mostrar_hora:
        return momento.strftime("%H:%M")
    return ""


def validar_imagem(caminho):
    if not caminho:
        return None
    if os.path.getsize(caminho) > MAX_IMAGE_SIZE:
        raise ValueError("A imagem deve ter no máximo 2 MB.")
    try:
        with Image.open(caminho) as teste:
            teste.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Imagem inválida.") from exc
    try:
        imagem = Image.open(caminho)
        imagem.load()
    except Exception as exc:
        raise ValueError("Não foi possível processar a imagem.") from exc
    if imagem.format not in ALLOWED_IMAGE_FORMATS:
        raise ValueError("Utilize somente PNG ou JPEG.")
    if imagem.width > MAX_IMAGE_DIMENSION or imagem.height > MAX_IMAGE_DIMENSION:
        raise ValueError("A resolução da imagem é excessiva.")
    largura_original = imagem.width
    altura_original = imagem.height
    imagem = imagem.convert("RGBA")
    imagem.thumbnail((1200, 1200))
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return {
        "buffer": buffer,
        "width": largura_original,
        "height": altura_original,
        "ratio": largura_original / altura_original,
    }


def determinar_modo_imagem(imagem_info, modo):
    if not imagem_info:
        return "default"
    if modo in {"full", "logo"}:
        return modo
    return "full" if imagem_info["ratio"] >= FULL_SIGNATURE_RATIO else "logo"


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
    escala = min(max_width / largura_original, max_height / altura_original)
    largura = largura_original * escala
    altura = altura_original * escala
    x = 5 + (max_width - largura) / 2
    y = 10 + (max_height - altura) / 2
    buffer.seek(0)
    c.drawImage(ImageReader(buffer), x, y, width=largura, height=altura, preserveAspectRatio=True, mask="auto")
    c.setStrokeColor(HexColor("#CBD5E1"))
    c.setLineWidth(0.7)
    c.line(50, 59, 230, 59)


def desenhar_imagem_completa(c, imagem_info, texto_data):
    buffer = imagem_info["buffer"]
    buffer.seek(0)
    imagem = Image.open(buffer)
    largura_original, altura_original = imagem.size
    margem_x = 3
    margem_superior = 3
    faixa_inferior = 11 if texto_data else 3
    area_width = STAMP_WIDTH - margem_x * 2
    area_height = STAMP_HEIGHT - margem_superior - faixa_inferior
    escala = min(area_width / largura_original, area_height / altura_original)
    largura = largura_original * escala
    altura = altura_original * escala
    x = (STAMP_WIDTH - largura) / 2
    y = faixa_inferior + (area_height - altura) / 2
    buffer.seek(0)
    c.drawImage(ImageReader(buffer), x, y, width=largura, height=altura, preserveAspectRatio=True, mask="auto")
    if texto_data:
        c.setStrokeColor(HexColor("#E2E8F0"))
        c.setLineWidth(0.4)
        c.line(4, 11, STAMP_WIDTH - 4, 11)
        c.setFillColor(HexColor("#475569"))
        c.setFont("Helvetica", 5.8)
        c.drawRightString(STAMP_WIDTH - 5, 3.2, texto_data)


def criar_carimbo_textual(nome_assinante, titulo, mostrar_data, mostrar_hora, mostrar_tipo, imagem_info=None):
    caminho = criar_temporario(".pdf")
    c = canvas.Canvas(caminho, pagesize=(STAMP_WIDTH, STAMP_HEIGHT))
    c.setFillColor(white)
    c.rect(0, 0, STAMP_WIDTH, STAMP_HEIGHT, fill=1, stroke=0)
    if imagem_info:
        desenhar_imagem_logo(c, imagem_info)
    else:
        desenhar_identidade_padrao(c)
    titulo = str(titulo).strip()[:60] or "Assinado digitalmente por:"
    titulo_exibicao, tamanho_titulo = ajustar_texto_largura(titulo, "Helvetica", 7.4, 5.5, 175)
    c.setFillColor(black)
    c.setFont("Helvetica", tamanho_titulo)
    c.drawString(55, 49, titulo_exibicao)
    nome_exibicao, tamanho_nome = ajustar_texto_largura(nome_assinante, "Helvetica-Bold", 8.2, 3.5, 175)
    c.setFont("Helvetica-Bold", tamanho_nome)
    c.drawString(55, 38, nome_exibicao)
    texto_data = formatar_data(mostrar_data, mostrar_hora)
    pos_y = 27
    if texto_data:
        c.setFont("Helvetica", 6.9)
        c.drawString(55, pos_y, texto_data)
        pos_y -= 10
    if mostrar_tipo:
        c.setFillColor(HexColor("#475569"))
        c.setFont("Helvetica", 6.5)
        c.drawString(55, pos_y, "Assinatura digital PAdES")
    c.save()
    return caminho


def criar_carimbo_imagem_completa(imagem_info, mostrar_data, mostrar_hora):
    caminho = criar_temporario(".pdf")
    c = canvas.Canvas(caminho, pagesize=(STAMP_WIDTH, STAMP_HEIGHT))
    c.setFillColor(white)
    c.rect(0, 0, STAMP_WIDTH, STAMP_HEIGHT, fill=1, stroke=0)
    desenhar_imagem_completa(c, imagem_info, formatar_data(mostrar_data, mostrar_hora))
    c.save()
    return caminho


def obter_pagina_writer(writer, page_index):
    resultado = writer.find_page_for_modification(page_index)
    page_ref = resultado[0] if isinstance(resultado, tuple) else resultado
    return page_ref.get_object() if hasattr(page_ref, "get_object") else page_ref


def obter_caixa_pagina(page):
    box = page.get("/CropBox") or page.get("/MediaBox")
    if box is None:
        raise ValueError("Não foi possível determinar as dimensões da página.")
    if hasattr(box, "get_object"):
        box = box.get_object()
    x0, y0, x1, y1 = map(float, box)
    return x0, y0, x1 - x0, y1 - y0


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
        if os.path.getsize(pdf_path) > MAX_PDF_SIZE:
            raise ValueError("O PDF excede 25 MB.")
        if os.path.getsize(certificado_path) > MAX_CERTIFICATE_SIZE:
            raise ValueError("O certificado excede 5 MB.")
        with open(pdf_path, "rb") as arquivo_pdf:
            pdf_bytes = arquivo_pdf.read()
        inicio_pdf = pdf_bytes.find(b"%PDF", 0, 1024)
        if inicio_pdf == -1:
            raise ValueError("O documento não possui cabeçalho PDF válido.")
        pdf_stream = io.BytesIO(pdf_bytes[inicio_pdf:])
        caminho_p12 = criar_temporario(".p12")
        with open(certificado_path, "rb") as origem:
            p12_bytes = origem.read()
        with open(caminho_p12, "wb") as destino:
            destino.write(p12_bytes)
        try:
            signer = SimpleSigner.load_pkcs12(pfx_file=caminho_p12, passphrase=senha.encode("utf-8"))
        except Exception as exc:
            raise ValueError("Não foi possível abrir o certificado. Verifique o arquivo e a senha.") from exc
        if signer is None:
            raise ValueError("Não foi possível abrir o certificado. Verifique o arquivo e a senha.")
        remover_temporario(caminho_p12)
        caminho_p12 = None
        nome_assinante = obter_nome_assinante(signer)
        imagem_info = None
        modo_detectado = "default"
        if signature_type == "image":
            if not imagem_path:
                raise ValueError("Imagem personalizada ausente.")
            imagem_info = validar_imagem(imagem_path)
            modo_detectado = determinar_modo_imagem(imagem_info, modo_imagem)
        if signature_type == "image" and modo_detectado == "full":
            caminho_carimbo = criar_carimbo_imagem_completa(imagem_info, mostrar_data, mostrar_hora)
        else:
            if signature_type == "standard":
                titulo = "Assinado digitalmente por:"
            caminho_carimbo = criar_carimbo_textual(
                nome_assinante,
                titulo,
                mostrar_data,
                mostrar_hora,
                mostrar_tipo,
                imagem_info if signature_type == "image" else None,
            )
        estilo_carimbo = stamp.StaticStampStyle.from_pdf_file(caminho_carimbo, page_ix=0, border_width=0)
        pdf_stream.seek(0)
        writer = IncrementalPdfFileWriter(pdf_stream)
        page = obter_pagina_writer(writer, page_index)
        page_x0, page_y0, pdf_width, pdf_height = obter_caixa_pagina(page)
        max_x = max(page_x0, page_x0 + pdf_width - STAMP_WIDTH)
        max_y = max(page_y0, page_y0 + pdf_height - STAMP_HEIGHT)
        x_pdf = max(page_x0, min(x_pdf, max_x))
        y_pdf = max(page_y0, min(y_pdf, max_y))
        field_name = "Assinatura_" + uuid.uuid4().hex[:12]
        append_signature_field(
            writer,
            SigFieldSpec(
                sig_field_name=field_name,
                on_page=page_index,
                box=(x_pdf, y_pdf, x_pdf + STAMP_WIDTH, y_pdf + STAMP_HEIGHT),
            ),
        )
        metadata = signers.PdfSignatureMetadata(
            field_name=field_name,
            md_algorithm="sha256",
            subfilter=SigSeedSubFilter.PADES,
        )
        pdf_signer = signers.PdfSigner(signature_meta=metadata, signer=signer, stamp_style=estilo_carimbo)
        output_stream = pdf_signer.sign_pdf(writer)
        output_stream.seek(0)
        with open(output_path, "wb") as output_file:
            output_file.write(output_stream.read())
        return {"output": output_path, "signer": nome_assinante, "image_mode": modo_detectado}
    finally:
        remover_temporario(caminho_p12)
        remover_temporario(caminho_carimbo)


class SignWorker(QThread):
    success = Signal(dict)
    failed = Signal(str)

    def __init__(self, kwargs, parent=None):
        super().__init__(parent)
        self.kwargs = kwargs

    def run(self):
        try:
            self.success.emit(assinar_documento(**self.kwargs))
        except Exception as exc:
            self.failed.emit(str(exc))


class VerifyWorker(QThread):
    success = Signal(dict)
    failed = Signal(str)

    def __init__(self, pdf_path, allow_fetching=True, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.allow_fetching = allow_fetching

    def run(self):
        try:
            with open(self.pdf_path, "rb") as stream:
                result = verificar_pdf(stream, allow_fetching=self.allow_fetching)
            self.success.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class PdfCanvas(QLabel):
    positionChanged = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        self.source_pixmap = None
        self.display_scale = 1.0
        self.signature_left = None
        self.signature_top = None
        self.placeholder_title = "Assinado digitalmente por:"
        self.placeholder_name = "Nome do titular"
        self.setAccessibleName("Página do documento PDF")
        self.setAccessibleDescription("Página do documento. Clique para posicionar a assinatura.")

    def set_page_pixmap(self, pixmap, display_width, display_height, display_scale):
        self.source_pixmap = pixmap
        self.display_scale = display_scale
        self.signature_left = None
        self.signature_top = None
        self.setFixedSize(max(1, int(display_width)), max(1, int(display_height)))
        self.update()

    def clear_signature(self):
        self.signature_left = None
        self.signature_top = None
        self.update()

    def set_placeholder_text(self, title, name):
        self.placeholder_title = title
        self.placeholder_name = name
        self.update()

    def set_signature_position(self, left, top, emit_signal=True):
        if self.source_pixmap is None:
            return
        width = STAMP_WIDTH * self.display_scale
        height = STAMP_HEIGHT * self.display_scale
        left = max(0, min(float(left), max(0, self.width() - width)))
        top = max(0, min(float(top), max(0, self.height() - height)))
        self.signature_left = left
        self.signature_top = top
        self.update()
        if emit_signal:
            self.positionChanged.emit(left, top)

    def mousePressEvent(self, event):
        if self.source_pixmap is None or event.button() != Qt.MouseButton.LeftButton:
            return
        width = STAMP_WIDTH * self.display_scale
        height = STAMP_HEIGHT * self.display_scale
        position = event.position()
        self.set_signature_position(position.x() - width / 2, position.y() - height / 2)

    def paintEvent(self, event):
        if self.source_pixmap is None:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawPixmap(self.rect(), self.source_pixmap)
        if self.signature_left is not None and self.signature_top is not None:
            width = STAMP_WIDTH * self.display_scale
            height = STAMP_HEIGHT * self.display_scale
            rect = QRect(int(self.signature_left), int(self.signature_top), max(1, int(width)), max(1, int(height)))
            painter.fillRect(rect, QColor(37, 99, 235, 45))
            pen = QPen(QColor("#2563EB"))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)
            icon_size = max(12, int(28 * self.display_scale))
            icon_x = rect.left() + max(4, int(12 * self.display_scale))
            icon_y = rect.center().y() - icon_size // 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#2563EB"))
            painter.drawEllipse(icon_x, icon_y, icon_size, icon_size)
            painter.setPen(QColor("white"))
            icon_font = painter.font()
            icon_font.setBold(True)
            icon_font.setPointSizeF(max(6, 11 * self.display_scale))
            painter.setFont(icon_font)
            painter.drawText(
                QRect(icon_x, icon_y, icon_size, icon_size),
                Qt.AlignmentFlag.AlignCenter,
                "✓",
            )
            text_left = icon_x + icon_size + max(5, int(8 * self.display_scale))
            text_width = max(1, rect.right() - text_left - 4)
            painter.setPen(QColor("#1E293B"))
            title_font = painter.font()
            title_font.setBold(False)
            title_font.setPointSizeF(max(4, 6.5 * self.display_scale))
            painter.setFont(title_font)
            painter.drawText(text_left, rect.top() + max(9, int(17 * self.display_scale)), self.placeholder_title)
            name_font = painter.font()
            name_font.setBold(True)
            name_size = max(3.5, 8.2 * self.display_scale)
            name_font.setPointSizeF(name_size)
            painter.setFont(name_font)
            while name_size > 3.5 and painter.fontMetrics().horizontalAdvance(self.placeholder_name) > text_width:
                name_size -= 0.25
                name_font.setPointSizeF(name_size)
                painter.setFont(name_font)
            painter.drawText(text_left, rect.top() + max(18, int(32 * self.display_scale)), self.placeholder_name)
        painter.end()


class PagingScrollArea(QScrollArea):
    nextPageRequested = Signal()
    previousPageRequested = Signal()

    def wheelEvent(self, event):
        scrollbar = self.verticalScrollBar()
        delta = event.angleDelta().y()
        if delta < 0 and scrollbar.value() >= scrollbar.maximum():
            self.nextPageRequested.emit()
            event.accept()
            return
        if delta > 0 and scrollbar.value() <= scrollbar.minimum():
            self.previousPageRequested.emit()
            event.accept()
            return
        super().wheelEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = detectar_idioma()
        self.current_theme = None
        self.theme_override = False
        self.pdf_path = None
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.render_scale = 1.0
        self.position_page = None
        self.position_left_px = None
        self.position_top_px = None
        self.position_page_width_px = None
        self.position_page_height_px = None
        self.signature_type = "standard"
        self.image_path = None
        self.certificate_path = None
        self.last_output_path = None
        self.worker = None
        self.scroll_page_lock = False
        self.verify_pdf_document = None
        self.verify_current_page = 0
        self.verify_total_pages = 0
        self.verify_scroll_page_lock = False
        self.resize_timer = None
        self.setMinimumSize(900, 650)
        self.resize(1100, 780)
        self.create_ui()
        self.create_toolbar()
        self.apply_system_theme()
        try:
            style_hints = QApplication.styleHints()
            style_hints.colorSchemeChanged.connect(self.system_theme_changed)
        except Exception:
            pass
        self.retranslate_ui()
        self.update_signature_configuration()
        self.go_to_step(0)

    def tr_text(self, key):
        return TRANSLATIONS[self.language][key]

    def create_ui(self):
        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(14)
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label = QLabel()
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setObjectName("StepLabel")
        layout.addWidget(self.title_label)
        layout.addWidget(self.step_label)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.create_step_1()
        self.create_step_2()
        self.create_step_3()
        self.create_step_4()
        self.create_step_5()
        self.create_verify_page()
        self.setStatusBar(QStatusBar())

    def create_toolbar(self):
        toolbar = QToolBar("Preferências", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.theme_action = QAction("🌓", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)
        self.language_action = QAction("EN", self)
        self.language_action.triggered.connect(self.toggle_language)
        toolbar.addAction(self.language_action)

    def create_step_1(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step1_title = QLabel()
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.step1_title.setFont(font)
        self.step1_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step1_desc = QLabel()
        self.step1_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step1_desc.setWordWrap(True)
        self.pdf_button = QPushButton()
        self.pdf_button.setMinimumSize(300, 58)
        self.pdf_button.clicked.connect(self.select_pdf)
        self.pdf_button.setAccessibleName("Selecionar documento PDF")
        self.pdf_file_label = QLabel()
        self.pdf_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_file_label.setWordWrap(True)
        self.verify_entry_button = QPushButton()
        self.verify_entry_button.setMinimumSize(300, 50)
        self.verify_entry_button.clicked.connect(lambda: self.go_to_step(5))
        self.verify_entry_button.setAccessibleName("Verificar assinaturas de um PDF")
        layout.addStretch()
        layout.addWidget(self.step1_title)
        layout.addWidget(self.step1_desc)
        layout.addSpacing(15)
        layout.addWidget(self.pdf_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pdf_file_label)
        layout.addSpacing(8)
        layout.addWidget(self.verify_entry_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self.stack.addWidget(page)

    def create_step_2(self):
        page = QWidget()
        root = QVBoxLayout(page)
        self.position_title = QLabel()
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.position_title.setFont(font)
        self.position_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_desc = QLabel()
        self.position_desc.setWordWrap(True)
        self.position_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.position_title)
        root.addWidget(self.position_desc)
        nav = QHBoxLayout()
        self.prev_button = QPushButton()
        self.prev_button.clicked.connect(lambda: self.change_page(-1))
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QPushButton()
        self.next_button.clicked.connect(lambda: self.change_page(1))
        nav.addStretch()
        nav.addWidget(self.prev_button)
        nav.addWidget(self.page_label)
        nav.addWidget(self.next_button)
        nav.addStretch()
        root.addLayout(nav)
        self.scroll_area = PagingScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_canvas = PdfCanvas()
        self.pdf_canvas.positionChanged.connect(self.visual_position_changed)
        self.scroll_area.setWidget(self.pdf_canvas)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.handle_pdf_scroll)
        self.scroll_area.nextPageRequested.connect(
            lambda: self.request_pdf_page_from_scroll(1)
        )
        self.scroll_area.previousPageRequested.connect(
            lambda: self.request_pdf_page_from_scroll(-1)
        )
        root.addWidget(self.scroll_area, 1)
        self.accessible_toggle = QCheckBox()
        self.accessible_toggle.setChecked(False)
        self.accessible_toggle.toggled.connect(self.toggle_accessible_position)
        root.addWidget(self.accessible_toggle)
        self.accessible_frame = QFrame()
        self.accessible_frame.setObjectName("Card")
        self.accessible_frame.setVisible(False)
        accessible_layout = QFormLayout(self.accessible_frame)
        self.accessible_title = QLabel()
        accessible_font = QFont()
        accessible_font.setBold(True)
        self.accessible_title.setFont(accessible_font)
        accessible_layout.addRow(self.accessible_title)
        self.accessible_page_label = QLabel()
        self.accessible_page_spin = QSpinBox()
        self.accessible_page_spin.setMinimum(1)
        self.accessible_page_spin.setAccessibleName("Página da assinatura")
        accessible_layout.addRow(self.accessible_page_label, self.accessible_page_spin)
        self.accessible_position_label = QLabel()
        self.accessible_position_combo = QComboBox()
        self.accessible_position_combo.setAccessibleName("Posição da assinatura")
        accessible_layout.addRow(self.accessible_position_label, self.accessible_position_combo)
        self.apply_accessible_button = QPushButton()
        self.apply_accessible_button.clicked.connect(self.apply_accessible_position)
        accessible_layout.addRow(self.apply_accessible_button)
        root.addWidget(self.accessible_frame)
        buttons = QHBoxLayout()
        self.cancel_button = QPushButton()
        self.cancel_button.clicked.connect(self.reset_app)
        self.position_continue_button = QPushButton()
        self.position_continue_button.clicked.connect(self.confirm_position)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.position_continue_button)
        root.addLayout(buttons)
        self.stack.addWidget(page)

    def create_step_3(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.type_title = QLabel()
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.type_title.setFont(font)
        self.type_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.type_desc = QLabel()
        self.type_desc.setWordWrap(True)
        self.type_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.type_title)
        layout.addWidget(self.type_desc)
        cards = QHBoxLayout()
        self.standard_button = self.create_type_button("standard")
        self.simple_button = self.create_type_button("simple")
        self.image_button = self.create_type_button("image")
        cards.addWidget(self.standard_button)
        cards.addWidget(self.simple_button)
        cards.addWidget(self.image_button)
        layout.addStretch()
        layout.addLayout(cards)
        layout.addStretch()
        self.type_back_button = QPushButton()
        self.type_back_button.clicked.connect(lambda: self.go_to_step(1))
        layout.addWidget(self.type_back_button)
        self.stack.addWidget(page)

    def create_type_button(self, signature_type):
        button = QPushButton()
        button.setMinimumHeight(150)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(lambda checked=False, value=signature_type: self.select_signature_type(value))
        return button

    def create_step_4(self):
        page = QWidget()
        root = QVBoxLayout(page)
        self.configuration_title = QLabel()
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.configuration_title.setFont(font)
        self.configuration_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.configuration_description = QLabel()
        self.configuration_description.setWordWrap(True)
        self.configuration_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.configuration_title)
        root.addWidget(self.configuration_description)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        form.setVerticalSpacing(12)
        self.custom_title_label = QLabel()
        self.custom_title_input = QLineEdit("Assinado digitalmente por:")
        self.custom_title_input.setMaxLength(60)
        self.custom_title_input.setAccessibleName("Texto superior da assinatura")
        form.addRow(self.custom_title_label, self.custom_title_input)
        self.show_date = QCheckBox()
        self.show_date.setChecked(True)
        form.addRow(self.show_date)
        self.show_time = QCheckBox()
        self.show_time.setChecked(False)
        form.addRow(self.show_time)
        self.show_type = QCheckBox()
        self.show_type.setChecked(True)
        form.addRow(self.show_type)
        self.image_file_title = QLabel()
        self.image_row = QWidget()
        image_layout = QHBoxLayout(self.image_row)
        image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_button_select = QPushButton()
        self.image_button_select.clicked.connect(self.select_image)
        self.image_file_label = QLabel()
        self.image_file_label.setWordWrap(True)
        image_layout.addWidget(self.image_button_select)
        image_layout.addWidget(self.image_file_label, 1)
        form.addRow(self.image_file_title, self.image_row)
        self.image_mode_label = QLabel()
        self.image_mode_combo = QComboBox()
        self.image_mode_combo.currentIndexChanged.connect(self.update_image_detection)
        form.addRow(self.image_mode_label, self.image_mode_combo)
        self.image_detection_label = QLabel()
        self.image_detection_label.setWordWrap(True)
        form.addRow(self.image_detection_label)
        self.certificate_label = QLabel()
        self.certificate_row = QWidget()
        certificate_layout = QHBoxLayout(self.certificate_row)
        certificate_layout.setContentsMargins(0, 0, 0, 0)
        self.certificate_button = QPushButton()
        self.certificate_button.clicked.connect(self.select_certificate)
        self.certificate_file_label = QLabel()
        self.certificate_file_label.setWordWrap(True)
        certificate_layout.addWidget(self.certificate_button)
        certificate_layout.addWidget(self.certificate_file_label, 1)
        form.addRow(self.certificate_label, self.certificate_row)
        self.password_label = QLabel()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaxLength(512)
        self.password_input.setAccessibleName("Senha do certificado")
        form.addRow(self.password_label, self.password_input)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        buttons = QHBoxLayout()
        self.configuration_back_button = QPushButton()
        self.configuration_back_button.clicked.connect(lambda: self.go_to_step(2))
        self.sign_button = QPushButton()
        self.sign_button.clicked.connect(self.start_signing)
        buttons.addWidget(self.configuration_back_button)
        buttons.addWidget(self.sign_button)
        root.addLayout(buttons)
        self.stack.addWidget(page)

    def create_step_5(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_icon = QLabel("✓")
        font = QFont()
        font.setPointSize(38)
        font.setBold(True)
        success_icon.setFont(font)
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_title = QLabel()
        success_title_font = QFont()
        success_title_font.setPointSize(18)
        success_title_font.setBold(True)
        self.success_title.setFont(success_title_font)
        self.success_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_desc = QLabel()
        self.success_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_label = QLabel()
        self.output_label.setWordWrap(True)
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.open_folder_button = QPushButton()
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.restart_button = QPushButton()
        self.restart_button.clicked.connect(self.reset_app)
        layout.addStretch()
        layout.addWidget(success_icon)
        layout.addWidget(self.success_title)
        layout.addWidget(self.success_desc)
        layout.addWidget(self.output_label)
        layout.addWidget(self.open_folder_button)
        layout.addWidget(self.restart_button)
        layout.addStretch()
        self.stack.addWidget(page)

    def create_verify_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.verify_title = QLabel()
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.verify_title.setFont(font)
        self.verify_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verify_description = QLabel()
        self.verify_description.setWordWrap(True)
        self.verify_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verify_notice = QLabel()
        self.verify_notice.setWordWrap(True)
        self.verify_notice.setObjectName("VerifyNotice")
        self.verify_online_checkbox = QCheckBox()
        self.verify_online_checkbox.setChecked(True)
        self.verify_select_button = QPushButton()
        self.verify_select_button.clicked.connect(self.select_pdf_to_verify)
        self.verify_preview_nav = QWidget()
        verify_nav = QHBoxLayout(self.verify_preview_nav)
        verify_nav.setContentsMargins(0, 0, 0, 0)
        self.verify_prev_button = QPushButton("<")
        self.verify_prev_button.clicked.connect(lambda: self.change_verify_page(-1))
        self.verify_page_label = QLabel()
        self.verify_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verify_next_button = QPushButton(">")
        self.verify_next_button.clicked.connect(lambda: self.change_verify_page(1))
        verify_nav.addStretch()
        verify_nav.addWidget(self.verify_prev_button)
        verify_nav.addWidget(self.verify_page_label)
        verify_nav.addWidget(self.verify_next_button)
        verify_nav.addStretch()
        self.verify_scroll_area = PagingScrollArea()
        self.verify_scroll_area.setWidgetResizable(False)
        self.verify_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verify_pdf_canvas = QLabel()
        self.verify_pdf_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verify_scroll_area.setWidget(self.verify_pdf_canvas)
        self.verify_scroll_area.verticalScrollBar().valueChanged.connect(
            self.handle_verify_pdf_scroll
        )
        self.verify_scroll_area.nextPageRequested.connect(
            lambda: self.request_verify_page_from_scroll(1)
        )
        self.verify_scroll_area.previousPageRequested.connect(
            lambda: self.request_verify_page_from_scroll(-1)
        )
        self.verify_preview_nav.setVisible(False)
        self.verify_scroll_area.setVisible(False)
        self.verify_results = QTextEdit()
        self.verify_results.setReadOnly(True)
        self.verify_results.setAccessibleName("Resultado da verificação de assinaturas")
        self.verify_back_button = QPushButton()
        self.verify_back_button.clicked.connect(lambda: self.go_to_step(0))
        layout.addWidget(self.verify_title)
        layout.addWidget(self.verify_description)
        layout.addWidget(self.verify_notice)
        layout.addWidget(self.verify_online_checkbox)
        layout.addWidget(self.verify_select_button)
        layout.addWidget(self.verify_preview_nav)
        layout.addWidget(self.verify_scroll_area, 2)
        layout.addWidget(self.verify_results, 1)
        layout.addWidget(self.verify_back_button)
        self.stack.addWidget(page)

    def apply_system_theme(self):
        try:
            scheme = QApplication.styleHints().colorScheme()
            self.current_theme = "dark" if scheme == Qt.ColorScheme.Dark else "light"
        except Exception:
            color = QApplication.palette().color(QPalette.ColorRole.Window)
            self.current_theme = "dark" if color.lightness() < 128 else "light"
        self.apply_theme(self.current_theme)

    def system_theme_changed(self, scheme):
        if self.theme_override:
            return
        self.current_theme = "dark" if scheme == Qt.ColorScheme.Dark else "light"
        self.apply_theme(self.current_theme)

    def toggle_theme(self):
        self.theme_override = True
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(self.current_theme)

    def apply_theme(self, theme):
        self.current_theme = theme
        if theme == "dark":
            stylesheet = """
QMainWindow, QWidget { background: #0F172A; color: #F8FAFC; }
QLabel#StepLabel { color: #94A3B8; }
QFrame#Card { border: 1px solid #334155; border-radius: 10px; padding: 8px; }
QPushButton { background: #3B82F6; color: white; border: none; border-radius: 8px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #60A5FA; }
QPushButton:disabled { background: #475569; }
QLineEdit, QComboBox, QSpinBox, QTextEdit { background: #1E293B; color: #F8FAFC; border: 1px solid #475569; border-radius: 7px; padding: 8px; }
QCheckBox { spacing: 8px; }
QScrollArea { border: 1px solid #334155; background: #111827; }
QToolBar, QStatusBar { background: #0F172A; border: none; }
"""
        else:
            stylesheet = """
QMainWindow, QWidget { background: #F8FAFC; color: #1E293B; }
QLabel#StepLabel { color: #64748B; }
QFrame#Card { border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px; }
QPushButton { background: #2563EB; color: white; border: none; border-radius: 8px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #1D4ED8; }
QPushButton:disabled { background: #94A3B8; }
QLineEdit, QComboBox, QSpinBox, QTextEdit { background: white; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 7px; padding: 8px; }
QCheckBox { spacing: 8px; }
QScrollArea { border: 1px solid #E2E8F0; background: #E2E8F0; }
QToolBar, QStatusBar { background: #F8FAFC; border: none; }
"""
        QApplication.instance().setStyleSheet(stylesheet)

    def toggle_language(self):
        old_default = TRANSLATIONS[self.language]["signed_by"]
        self.language = "en" if self.language == "pt" else "pt"
        current_title = self.custom_title_input.text().strip()
        if not current_title or current_title == old_default:
            self.custom_title_input.setText(self.tr_text("signed_by"))
        self.retranslate_ui()

    def retranslate_ui(self):
        tr = self.tr_text
        self.setWindowTitle(tr("app_title"))
        self.title_label.setText(tr("app_title"))
        self.language_action.setText(tr("language"))
        self.language_action.setToolTip(tr("toggle_language"))
        self.theme_action.setToolTip(tr("toggle_theme"))
        self.step1_title.setText(tr("select_pdf_title"))
        self.step1_desc.setText(tr("select_pdf_desc"))
        self.pdf_button.setText("📄  " + tr("select_pdf"))
        self.verify_entry_button.setText("✓  " + tr("verify_signatures"))
        self.pdf_file_label.setText(f"{tr('pdf_selected')} {Path(self.pdf_path).name}" if self.pdf_path else "")
        self.position_title.setText(tr("position_title"))
        self.position_desc.setText(tr("position_desc"))
        self.pdf_canvas.set_placeholder_text(tr("signed_by"), tr("verify_signer"))
        self.prev_button.setText("◀ " + tr("previous"))
        self.next_button.setText(tr("next") + " ▶")
        self.accessible_toggle.setText(tr("show_accessible_position"))
        self.accessible_title.setText(tr("accessible_position"))
        self.accessible_page_label.setText(tr("accessible_page"))
        self.accessible_position_label.setText(tr("accessible_location"))
        selected_accessible_mode = self.accessible_position_combo.currentData()
        self.accessible_position_combo.blockSignals(True)
        self.accessible_position_combo.clear()
        for key in ("top_left", "top_right", "bottom_left", "bottom_right", "center"):
            self.accessible_position_combo.addItem(tr(key), key)
        if selected_accessible_mode:
            index = self.accessible_position_combo.findData(selected_accessible_mode)
            if index >= 0:
                self.accessible_position_combo.setCurrentIndex(index)
        self.accessible_position_combo.blockSignals(False)
        self.apply_accessible_button.setText(tr("apply_position"))
        self.cancel_button.setText(tr("cancel"))
        self.position_continue_button.setText(tr("continue"))
        self.type_title.setText(tr("signature_type_title"))
        self.type_desc.setText(tr("signature_type_desc"))
        self.standard_button.setText(f"{tr('standard')}\n\n{tr('standard_desc')}")
        self.simple_button.setText(f"{tr('simple')}\n\n{tr('simple_desc')}")
        self.image_button.setText(f"{tr('image')}\n\n{tr('image_desc')}")
        self.type_back_button.setText(tr("back"))
        self.configuration_title.setText(tr("configuration"))
        self.custom_title_label.setText(tr("custom_title"))
        self.show_date.setText(tr("show_date"))
        self.show_time.setText(tr("show_time"))
        self.show_type.setText(tr("show_type"))
        self.image_file_title.setText(tr("image_file"))
        self.image_button_select.setText(tr("select_image"))
        self.image_file_label.setText(Path(self.image_path).name if self.image_path else tr("no_image"))
        self.image_mode_label.setText(tr("image_mode"))
        selected_mode = self.image_mode_combo.currentData()
        self.image_mode_combo.blockSignals(True)
        self.image_mode_combo.clear()
        self.image_mode_combo.addItem(tr("auto"), "auto")
        self.image_mode_combo.addItem(tr("full"), "full")
        self.image_mode_combo.addItem(tr("logo"), "logo")
        if selected_mode:
            index = self.image_mode_combo.findData(selected_mode)
            if index >= 0:
                self.image_mode_combo.setCurrentIndex(index)
        self.image_mode_combo.blockSignals(False)
        self.certificate_label.setText(tr("certificate"))
        self.certificate_button.setText(tr("select_certificate"))
        self.certificate_file_label.setText(Path(self.certificate_path).name if self.certificate_path else tr("no_certificate"))
        self.password_label.setText(tr("password"))
        self.password_input.setAccessibleDescription(tr("password_accessible"))
        self.configuration_back_button.setText(tr("back"))
        self.sign_button.setText(tr("sign"))
        self.success_title.setText(tr("success"))
        self.success_desc.setText(tr("success_desc"))
        self.open_folder_button.setText(tr("open_folder"))
        self.restart_button.setText(tr("sign_another"))
        self.verify_title.setText(tr("verify_signatures"))
        self.verify_description.setText(tr("verify_desc"))
        self.verify_notice.setText(tr("verify_notice"))
        self.verify_online_checkbox.setText(tr("verify_online"))
        self.verify_select_button.setText(tr("verify_select"))
        self.verify_back_button.setText(tr("verify_back"))
        self.update_configuration_description()
        self.statusBar().showMessage(tr("ready"))
        self.update_step_label()
        self.update_page_label()
        self.update_image_detection()

    def update_step_label(self):
        index = self.stack.currentIndex()
        if index == 5:
            self.step_label.setText(self.tr_text("verify_signatures"))
            return
        key = f"step_{index + 1}"
        self.step_label.setText(self.tr_text(key))

    def go_to_step(self, index):
        self.stack.setCurrentIndex(index)
        self.update_step_label()
        if index == 1:
            self.render_current_page()

    def select_pdf_to_verify(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            self.tr_text("verify_select"),
            "",
            "PDF (*.pdf)",
        )
        if not caminho:
            return
        try:
            if os.path.getsize(caminho) > MAX_PDF_SIZE:
                raise ValueError(self.tr_text("pdf_too_large"))
            if Path(caminho).suffix.lower() != ".pdf":
                raise ValueError(self.tr_text("invalid_pdf"))
            documento = pymupdf.open(caminho)
            if documento.page_count < 1:
                documento.close()
                raise ValueError(self.tr_text("invalid_pdf"))
        except Exception as exc:
            QMessageBox.warning(self, self.tr_text("error"), str(exc))
            return
        if self.verify_pdf_document:
            self.verify_pdf_document.close()
        self.verify_pdf_document = documento
        self.verify_current_page = 0
        self.verify_total_pages = documento.page_count
        self.verify_preview_nav.setVisible(True)
        self.verify_scroll_area.setVisible(True)
        self.render_verify_page()
        self.verify_results.clear()
        self.stack.setCurrentIndex(5)
        self.update_step_label()
        self.statusBar().showMessage(self.tr_text("verify_processing"))
        self.verify_select_button.setEnabled(False)
        self.verify_back_button.setEnabled(False)
        self.worker = VerifyWorker(
            caminho,
            allow_fetching=self.verify_online_checkbox.isChecked(),
            parent=self,
        )
        self.worker.success.connect(self.verification_success)
        self.worker.failed.connect(self.verification_failed)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def verification_success(self, result):
        self.worker = None
        self.verify_select_button.setEnabled(True)
        self.verify_back_button.setEnabled(True)
        self.statusBar().showMessage(self.tr_text("ready"))
        self.render_verification_result(result)

    def verification_failed(self, message):
        self.worker = None
        self.verify_select_button.setEnabled(True)
        self.verify_back_button.setEnabled(True)
        self.statusBar().showMessage(self.tr_text("ready"))
        self.verify_results.setPlainText(message)
        QMessageBox.warning(self, self.tr_text("error"), message)

    def _verification_value(self, value, positive, negative):
        if value is True:
            return positive
        if value is False:
            return negative
        return self.tr_text("verify_indeterminate")

    def render_verification_result(self, result):
        tr = self.tr_text
        lines = [tr("verify_notice"), ""]
        signatures = result.get("assinaturas", [])
        count = len(signatures)
        lines.append(
            tr("verify_count").replace("{count}", str(count))
            if count
            else tr("verify_no_signatures")
        )
        for signature in signatures:
            cert = signature.get("certificado", {})
            revocation = signature.get("revogacao", {})
            integrity = self._verification_value(
                signature.get("integridade_criptografica"),
                tr("verify_verified"),
                tr("verify_not_verified"),
            )
            crypto = self._verification_value(
                signature.get("assinatura_criptograficamente_valida"),
                tr("verify_valid"),
                tr("verify_invalid"),
            )
            trust = self._verification_value(
                signature.get("cadeia_confiavel"),
                tr("verify_trusted"),
                tr("verify_untrusted"),
            )
            if revocation.get("revogado") is True:
                rev_text = tr("verify_revoked")
            elif revocation.get("revogado") is False:
                rev_text = tr("verify_not_revoked")
            else:
                rev_text = tr("verify_indeterminate")
            lines.extend([
                "",
                f"--- {tr('verify_signatures')} #{signature.get('indice', '?')} ---",
                f"{tr('verify_signer')}: {cert.get('titular') or '-'}",
                f"{tr('verify_issuer')}: {cert.get('emissor') or '-'}",
                f"{tr('verify_infrastructure')}: {cert.get('infraestrutura', {}).get('nome') or '-'}",
                f"{tr('verify_integrity')}: {integrity}",
                f"{tr('verify_crypto')}: {crypto}",
                f"{tr('verify_trust')}: {trust}",
                f"{tr('verify_revocation')}: {rev_text}",
                f"Digest: {signature.get('algoritmo_digest') or '-'}",
                f"Mecanismo / Mechanism: {signature.get('mecanismo_assinatura') or '-'}",
                f"Cobertura / Coverage: {signature.get('cobertura') or '-'}",
                f"Alterações / Modifications: {signature.get('nivel_modificacao') or '-'}",
                f"SHA-256: {cert.get('sha256') or '-'}",
            ])
            chain = signature.get("cadeia_validacao") or []
            if chain:
                lines.append("Cadeia / Chain:")
                for item in chain:
                    lines.append(f"  • {item.get('titular') or '?'} — {item.get('emissor') or '?'}")
            if signature.get("erro_validacao"):
                lines.append(f"Aviso / Warning: {signature['erro_validacao']}")
        if result.get("observacao_revogacao"):
            lines.extend(["", result["observacao_revogacao"]])
        self.verify_results.setPlainText("\n".join(lines))

    def select_pdf(self):
        caminho, _ = QFileDialog.getOpenFileName(self, self.tr_text("select_pdf_title"), "", "PDF (*.pdf)")
        if not caminho:
            return
        try:
            if os.path.getsize(caminho) > MAX_PDF_SIZE:
                raise ValueError(self.tr_text("pdf_too_large"))
            if Path(caminho).suffix.lower() != ".pdf":
                raise ValueError(self.tr_text("invalid_pdf"))
            documento = pymupdf.open(caminho)
            if documento.page_count < 1:
                documento.close()
                raise ValueError(self.tr_text("invalid_pdf"))
            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = documento
            self.pdf_path = caminho
            self.current_page = 0
            self.total_pages = documento.page_count
            self.accessible_page_spin.setMaximum(self.total_pages)
            self.accessible_page_spin.setValue(1)
            self.clear_position()
            self.pdf_file_label.setText(f"{self.tr_text('pdf_selected')} {Path(caminho).name}")
            self.go_to_step(1)
        except Exception as exc:
            QMessageBox.critical(self, self.tr_text("error"), str(exc))

    def render_verify_page(self, scroll_to_end=False):
        if not self.verify_pdf_document:
            return
        page = self.verify_pdf_document.load_page(self.verify_current_page)
        available_width = max(500, self.verify_scroll_area.viewport().width() - 30)
        page_width = max(1.0, float(page.rect.width))
        page_height = max(1.0, float(page.rect.height))
        display_scale = min(1.5, max(0.45, available_width / page_width))
        render_scale = display_scale * PDF_RENDER_QUALITY
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(render_scale, render_scale), alpha=False
        )
        image_format = (
            QImage.Format.Format_RGB888
            if pix.n == 3
            else QImage.Format.Format_RGBA8888
        )
        image = QImage(
            pix.samples, pix.width, pix.height, pix.stride, image_format
        ).copy()
        width = max(1, round(page_width * display_scale))
        height = max(1, round(page_height * display_scale))
        preview = QPixmap.fromImage(image).scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.verify_pdf_canvas.setPixmap(preview)
        self.verify_pdf_canvas.setFixedSize(preview.size())
        self.verify_page_label.setText(
            self.tr_text("page")
            .replace("{current}", str(self.verify_current_page + 1))
            .replace("{total}", str(self.verify_total_pages))
        )
        self.verify_prev_button.setEnabled(self.verify_current_page > 0)
        self.verify_next_button.setEnabled(
            self.verify_current_page < self.verify_total_pages - 1
        )
        self.verify_scroll_page_lock = True
        scrollbar = self.verify_scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum() if scroll_to_end else 0)
        QTimer.singleShot(350, self.unlock_verify_page_scroll)

    def unlock_verify_page_scroll(self):
        self.verify_scroll_page_lock = False

    def handle_verify_pdf_scroll(self, value):
        if (
            not self.verify_pdf_document
            or self.verify_scroll_page_lock
            or self.verify_current_page >= self.verify_total_pages - 1
        ):
            return
        scrollbar = self.verify_scroll_area.verticalScrollBar()
        if scrollbar.maximum() > 0 and value >= scrollbar.maximum() - 3:
            self.verify_scroll_page_lock = True
            QTimer.singleShot(150, self.go_to_next_verify_page_from_scroll)

    def request_verify_page_from_scroll(self, offset):
        if self.verify_scroll_page_lock:
            return
        target = self.verify_current_page + offset
        if not 0 <= target < self.verify_total_pages:
            return
        self.verify_scroll_page_lock = True
        callback = (
            self.go_to_next_verify_page_from_scroll
            if offset > 0
            else self.go_to_previous_verify_page_from_scroll
        )
        QTimer.singleShot(100, callback)

    def go_to_next_verify_page_from_scroll(self):
        if self.verify_current_page >= self.verify_total_pages - 1:
            self.verify_scroll_page_lock = False
            return
        self.verify_current_page += 1
        self.render_verify_page()

    def go_to_previous_verify_page_from_scroll(self):
        if self.verify_current_page <= 0:
            self.verify_scroll_page_lock = False
            return
        self.verify_current_page -= 1
        self.render_verify_page(scroll_to_end=True)

    def change_verify_page(self, offset):
        target = self.verify_current_page + offset
        if 0 <= target < self.verify_total_pages:
            self.verify_current_page = target
            self.render_verify_page()

    def render_current_page(self, scroll_to_end=False):
        if not self.pdf_document:
            return
        page = self.pdf_document.load_page(self.current_page)
        available_width = max(500, self.scroll_area.viewport().width() - 30)
        page_width = max(1.0, float(page.rect.width))
        page_height = max(1.0, float(page.rect.height))
        display_scale = min(1.5, max(0.45, available_width / page_width))
        render_scale = display_scale * PDF_RENDER_QUALITY
        pix = page.get_pixmap(matrix=pymupdf.Matrix(render_scale, render_scale), alpha=False)
        image_format = QImage.Format.Format_RGB888 if pix.n == 3 else QImage.Format.Format_RGBA8888
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format).copy()
        high_resolution_pixmap = QPixmap.fromImage(image)
        display_width = page_width * display_scale
        display_height = page_height * display_scale
        self.render_scale = display_scale
        self.pdf_canvas.set_page_pixmap(high_resolution_pixmap, display_width, display_height, display_scale)
        if self.position_page == self.current_page and self.position_left_px is not None:
            page_rect = page.rect
            if self.position_page_width_px and self.position_page_height_px:
                left = self.position_left_px * self.pdf_canvas.width() / self.position_page_width_px
                top = self.position_top_px * self.pdf_canvas.height() / self.position_page_height_px
                self.position_left_px = left
                self.position_top_px = top
                self.position_page_width_px = self.pdf_canvas.width()
                self.position_page_height_px = self.pdf_canvas.height()
            self.pdf_canvas.set_signature_position(self.position_left_px, self.position_top_px, emit_signal=False)
        self.update_page_label()
        self.scroll_page_lock = True
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum() if scroll_to_end else 0)
        QTimer.singleShot(350, self.unlock_page_scroll)

    def unlock_page_scroll(self):
        self.scroll_page_lock = False

    def handle_pdf_scroll(self, value):
        if not self.pdf_document or self.scroll_page_lock or self.current_page >= self.total_pages - 1:
            return
        scrollbar = self.scroll_area.verticalScrollBar()
        maximum = scrollbar.maximum()
        if maximum > 0 and value >= maximum - 3:
            self.scroll_page_lock = True
            QTimer.singleShot(150, self.go_to_next_page_from_scroll)

    def request_pdf_page_from_scroll(self, offset):
        if self.scroll_page_lock:
            return
        target = self.current_page + offset
        if not 0 <= target < self.total_pages:
            return
        self.scroll_page_lock = True
        if offset > 0:
            QTimer.singleShot(100, self.go_to_next_page_from_scroll)
        else:
            QTimer.singleShot(100, self.go_to_previous_page_from_scroll)

    def go_to_next_page_from_scroll(self):
        if self.current_page >= self.total_pages - 1:
            self.scroll_page_lock = False
            return
        self.current_page += 1
        self.accessible_page_spin.setValue(self.current_page + 1)
        self.render_current_page()

    def go_to_previous_page_from_scroll(self):
        if self.current_page <= 0:
            self.scroll_page_lock = False
            return
        self.current_page -= 1
        self.accessible_page_spin.setValue(self.current_page + 1)
        self.render_current_page(scroll_to_end=True)

    def change_page(self, offset):
        new_page = self.current_page + offset
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.accessible_page_spin.setValue(new_page + 1)
            self.render_current_page()

    def update_page_label(self):
        if not self.total_pages:
            return
        self.page_label.setText(
            self.tr_text("page").replace("{current}", str(self.current_page + 1)).replace("{total}", str(self.total_pages))
        )
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def visual_position_changed(self, left, top):
        self.position_page = self.current_page
        self.position_left_px = left
        self.position_top_px = top
        self.position_page_width_px = self.pdf_canvas.width()
        self.position_page_height_px = self.pdf_canvas.height()
        self.accessible_page_spin.setValue(self.current_page + 1)
        self.statusBar().showMessage(self.tr_text("position_set").replace("{page}", str(self.current_page + 1)))

    def toggle_accessible_position(self, checked):
        self.accessible_frame.setVisible(checked)
        if checked:
            self.accessible_page_spin.setFocus()

    def apply_accessible_position(self):
        if not self.pdf_document:
            return
        self.current_page = self.accessible_page_spin.value() - 1
        self.render_current_page()
        width = STAMP_WIDTH * self.render_scale
        height = STAMP_HEIGHT * self.render_scale
        canvas_width = self.pdf_canvas.width()
        canvas_height = self.pdf_canvas.height()
        margin = 18 * self.render_scale
        position = self.accessible_position_combo.currentData()
        if position == "top_left":
            left, top = margin, margin
        elif position == "top_right":
            left, top = canvas_width - width - margin, margin
        elif position == "bottom_left":
            left, top = margin, canvas_height - height - margin
        elif position == "bottom_right":
            left, top = canvas_width - width - margin, canvas_height - height - margin
        else:
            left, top = (canvas_width - width) / 2, (canvas_height - height) / 2
        self.pdf_canvas.set_signature_position(left, top)

    def confirm_position(self):
        if self.position_page is None or self.position_left_px is None:
            QMessageBox.warning(self, self.tr_text("error"), self.tr_text("position_required"))
            return
        self.go_to_step(2)

    def select_signature_type(self, signature_type):
        if signature_type not in {"standard", "simple", "image"}:
            return
        self.signature_type = signature_type
        self.update_signature_configuration()
        self.go_to_step(3)

    def update_signature_configuration(self):
        if not hasattr(self, "custom_title_label"):
            return
        is_standard = self.signature_type == "standard"
        is_image = self.signature_type == "image"
        self.custom_title_label.setVisible(not is_standard)
        self.custom_title_input.setVisible(not is_standard)
        self.image_file_title.setVisible(is_image)
        self.image_row.setVisible(is_image)
        self.image_mode_label.setVisible(is_image)
        self.image_mode_combo.setVisible(is_image)
        self.image_detection_label.setVisible(is_image)
        if is_standard:
            self.custom_title_input.setText(self.tr_text("signed_by"))
        self.update_configuration_description()

    def update_configuration_description(self):
        if not hasattr(self, "configuration_description"):
            return
        key = {
            "standard": "configuration_standard",
            "simple": "configuration_simple",
            "image": "configuration_image",
        }[self.signature_type]
        self.configuration_description.setText(self.tr_text(key))

    def select_image(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            self.tr_text("select_image"),
            "",
            "Images (*.png *.jpg *.jpeg);;PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not caminho:
            return
        try:
            if os.path.getsize(caminho) > MAX_IMAGE_SIZE:
                raise ValueError(self.tr_text("image_too_large"))
            validar_imagem(caminho)
            self.image_path = caminho
            self.image_file_label.setText(Path(caminho).name)
            self.update_image_detection()
        except Exception as exc:
            self.image_path = None
            QMessageBox.warning(self, self.tr_text("error"), str(exc))

    def update_image_detection(self):
        if not hasattr(self, "image_detection_label"):
            return
        if not self.image_path:
            self.image_detection_label.setText("")
            return
        try:
            imagem_info = validar_imagem(self.image_path)
            modo = self.image_mode_combo.currentData() or "auto"
            detectado = determinar_modo_imagem(imagem_info, modo)
            texto = self.tr_text("image_detected_full" if detectado == "full" else "image_detected_logo")
            self.image_detection_label.setText(f"{texto} — {imagem_info['width']} × {imagem_info['height']} px")
        except Exception:
            self.image_detection_label.setText("")

    def select_certificate(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            self.tr_text("select_certificate"),
            "",
            "PKCS#12 (*.p12 *.pfx);;P12 (*.p12);;PFX (*.pfx)",
        )
        if not caminho:
            return
        if os.path.getsize(caminho) > MAX_CERTIFICATE_SIZE:
            QMessageBox.warning(self, self.tr_text("error"), self.tr_text("certificate_too_large"))
            return
        self.certificate_path = caminho
        self.certificate_file_label.setText(Path(caminho).name)

    def calculate_pdf_position(self):
        if self.position_page is None or self.position_left_px is None or self.position_top_px is None:
            raise ValueError(self.tr_text("position_required"))
        page = self.pdf_document.load_page(self.position_page)
        pdf_width = float(page.rect.width)
        pdf_height = float(page.rect.height)
        display_width = float(self.position_page_width_px or 0)
        display_height = float(self.position_page_height_px or 0)
        if display_width <= 0 or display_height <= 0:
            raise ValueError(self.tr_text("invalid_dimensions"))
        ratio_x = pdf_width / display_width
        ratio_y = pdf_height / display_height
        x = self.position_left_px * ratio_x
        y = pdf_height - self.position_top_px * ratio_y - STAMP_HEIGHT
        x = max(0, min(x, max(0, pdf_width - STAMP_WIDTH)))
        y = max(0, min(y, max(0, pdf_height - STAMP_HEIGHT)))
        return x, y

    def start_signing(self):
        if not self.pdf_path:
            return
        if not self.certificate_path or not self.password_input.text():
            QMessageBox.warning(self, self.tr_text("error"), self.tr_text("certificate_required"))
            return
        if self.signature_type == "image" and not self.image_path:
            QMessageBox.warning(self, self.tr_text("error"), self.tr_text("image_required"))
            return
        try:
            x_pdf, y_pdf = self.calculate_pdf_position()
        except Exception as exc:
            QMessageBox.warning(self, self.tr_text("error"), str(exc))
            return
        original = Path(self.pdf_path)
        suffix = "_assinado.pdf" if self.language == "pt" else "_signed.pdf"
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr_text("save_title"),
            str(original.parent / (original.stem + suffix)),
            "PDF (*.pdf)",
        )
        if not output_path:
            return
        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"
        senha = self.password_input.text()
        self.password_input.clear()
        kwargs = {
            "pdf_path": self.pdf_path,
            "certificado_path": self.certificate_path,
            "senha": senha,
            "output_path": output_path,
            "page_index": self.position_page,
            "x_pdf": x_pdf,
            "y_pdf": y_pdf,
            "signature_type": self.signature_type,
            "titulo": self.custom_title_input.text().strip() or self.tr_text("signed_by"),
            "mostrar_data": self.show_date.isChecked(),
            "mostrar_hora": self.show_time.isChecked(),
            "mostrar_tipo": self.show_type.isChecked(),
            "imagem_path": self.image_path,
            "modo_imagem": self.image_mode_combo.currentData() or "auto",
        }
        self.sign_button.setEnabled(False)
        self.configuration_back_button.setEnabled(False)
        self.statusBar().showMessage(self.tr_text("signing"))
        self.worker = SignWorker(kwargs, self)
        self.worker.success.connect(self.signing_success)
        self.worker.failed.connect(self.signing_failed)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def signing_success(self, result):
        self.worker = None
        self.sign_button.setEnabled(True)
        self.configuration_back_button.setEnabled(True)
        self.certificate_path = None
        self.certificate_file_label.setText(self.tr_text("no_certificate"))
        self.last_output_path = result["output"]
        self.output_label.setText(f"{self.tr_text('signed_file')}\n{self.last_output_path}")
        self.go_to_step(4)
        self.statusBar().showMessage(self.tr_text("success"))

    def signing_failed(self, message):
        self.worker = None
        self.sign_button.setEnabled(True)
        self.configuration_back_button.setEnabled(True)
        self.password_input.clear()
        self.statusBar().showMessage(self.tr_text("ready"))
        QMessageBox.critical(self, self.tr_text("error"), message)

    def open_output_folder(self):
        if not self.last_output_path:
            return
        folder = str(Path(self.last_output_path).parent)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    def clear_position(self):
        self.position_page = None
        self.position_left_px = None
        self.position_top_px = None
        self.position_page_width_px = None
        self.position_page_height_px = None
        if hasattr(self, "pdf_canvas"):
            self.pdf_canvas.clear_signature()

    def reset_app(self):
        if self.worker and self.worker.isRunning():
            return
        self.password_input.clear()
        self.certificate_path = None
        self.image_path = None
        self.last_output_path = None
        self.pdf_path = None
        if self.pdf_document:
            try:
                self.pdf_document.close()
            except Exception:
                pass
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.signature_type = "standard"
        self.show_date.setChecked(True)
        self.show_time.setChecked(False)
        self.show_type.setChecked(True)
        self.custom_title_input.setText(self.tr_text("signed_by"))
        self.image_mode_combo.setCurrentIndex(0)
        self.accessible_toggle.setChecked(False)
        self.clear_position()
        self.pdf_canvas.clear()
        self.pdf_canvas.source_pixmap = None
        self.pdf_canvas.setFixedSize(QSize(1, 1))
        if hasattr(self, "verify_results"):
            self.verify_results.clear()
        if self.verify_pdf_document:
            try:
                self.verify_pdf_document.close()
            except Exception:
                pass
        self.verify_pdf_document = None
        self.verify_current_page = 0
        self.verify_total_pages = 0
        self.verify_pdf_canvas.clear()
        self.verify_pdf_canvas.setFixedSize(QSize(1, 1))
        self.verify_preview_nav.setVisible(False)
        self.verify_scroll_area.setVisible(False)
        self.retranslate_ui()
        self.update_signature_configuration()
        self.go_to_step(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.resize_timer:
            self.resize_timer.stop()
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        if self.stack.currentIndex() == 1 and self.pdf_document:
            self.resize_timer.timeout.connect(self.render_current_page)
        elif self.stack.currentIndex() == 5 and self.verify_pdf_document:
            self.resize_timer.timeout.connect(self.render_verify_page)
        else:
            return
        self.resize_timer.start(180)

    def closeEvent(self, event):
        self.password_input.clear()
        if self.worker and self.worker.isRunning():
            self.worker.wait(3000)
        if self.pdf_document:
            try:
                self.pdf_document.close()
            except Exception:
                pass
        if self.verify_pdf_document:
            try:
                self.verify_pdf_document.close()
            except Exception:
                pass
        event.accept()


def create_application_icon():
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#2563EB"))
    painter.drawEllipse(4, 4, 56, 56)
    pen = QPen(QColor("white"))
    pen.setWidth(6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawLine(QPoint(18, 32), QPoint(27, 41))
    painter.drawLine(QPoint(27, 41), QPoint(47, 20))
    painter.end()
    return QIcon(pixmap)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Assinador Digital")
    icon = create_application_icon()
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
