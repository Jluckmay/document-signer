"use strict";

pdfjsLib.GlobalWorkerOptions.workerSrc =
    "./vendor/pdfjs/pdf.worker.min.js";

const API_BASE_URL =
    window.location.hostname.includes("github.io")
        ? "https://document-signer-u7ie.onrender.com"
        : "http://127.0.0.1:5000";

const STAMP_WIDTH = 240;
const STAMP_HEIGHT = 68;
const FULL_SIGNATURE_RATIO = 2.2;
const MAX_PDF_SIZE = 25 * 1024 * 1024;
const MAX_IMAGE_SIZE = 2 * 1024 * 1024;
const REQUEST_TIMEOUT = 120000;
const BACKEND_STATUS_TIMEOUT = 90000;
const BACKEND_STATUS_RETRY_INTERVAL = 5000;

/* ==========================================
   ESTADO DA APLICAÇÃO
========================================== */

let currentFile = null;
let pdfJsDoc = null;
let currentPageNum = 1;
let totalPages = 1;
let currentRenderScale = 1;
let currentSignatureType = "standard";
let customImageFile = null;
let customImageUrl = null;
let imageNaturalWidth = 0;
let imageNaturalHeight = 0;
let detectedImageMode = "default";
let currentDownloadUrl = null;
let resizeTimer = null;
let scrollPageLock = false;
let renderToken = 0;
let backendReady = false;
let backendWakePromise = null;
let backendWakeController = null;
let currentMode = "sign";
let lastVerificationResult = null;
let verificationPdfDoc = null;
let verificationPageNum = 1;
let verificationRenderToken = 0;
let verificationScrollPageLock = false;

let signaturePos = {
    placed: false,
    x: 0,
    y: 0,
    canvasRectWidth: 0,
    canvasRectHeight: 0,
    page: 1
};

/* ==========================================
   TRADUÇÕES
========================================== */

const translations = {
    pt: {
        htmlLang: "pt-BR",
        title: "Assinador Digital",
        skipLink: "Pular para o conteúdo principal",
        preferences: "Preferências da página",
        theme: "Alternar tema",
        languageButton: "EN",
        languageAria: "Mudar idioma para inglês",

        steps: [
            "Etapa 1 de 5: Envio do documento",
            "Etapa 2 de 5: Posicionamento",
            "Etapa 3 de 5: Tipo de assinatura",
            "Etapa 4 de 5: Configuração",
            "Etapa 5 de 5: Concluído"
        ],

        step1Title: "Envio do documento",
        uploadTitle: "Clique para selecionar o documento",
        uploadDescription: "ou escolha um arquivo PDF",
        pdfHelp: "Apenas arquivos PDF.",

        step2Title: "Posicionamento da assinatura",
        positionDescription:
            "Clique na página ou pressione Enter ou Espaço para posicionar a assinatura. Use as setas para ajustar. Ao chegar ao final da página, a próxima será exibida automaticamente.",

        previousPage: "Página anterior",
        nextPage: "Próxima página",
        pagination: "Navegação entre páginas",
        pdfPreview: "Pré-visualização do documento PDF",
        pdfPage:
            "Página do documento. Pressione Enter ou Espaço para posicionar no centro, use as setas para ajustar e pressione Enter novamente para continuar.",

        page: "Página {current} de {total}",
        cancel: "Cancelar",
        confirmPosition: "Confirmar posição",

        signatureTypeTitle:
            "Qual tipo de assinatura deseja utilizar?",

        signatureTypeDescription:
            "Escolha apenas a aparência visual. Todas as opções continuam utilizando o certificado digital.",

        standard: "Padrão",

        standardDescription:
            "Usa a identidade visual padrão do assinador com nome, data e informação PAdES.",

        simple: "Customizada simples",

        simpleDescription:
            "Permite personalizar o texto e escolher as informações mostradas.",

        image: "Customizada com imagem",

        imageDescription:
            "Permite usar logotipo ou uma imagem completa de assinatura.",

        back: "Voltar",
        configureTitle: "Configurar assinatura",

        configureDescription:
            "Configure a aparência e informe seu certificado digital.",

        simpleOptions: "Aparência personalizada",
        customTitle: "Texto superior:",
        imageOptions: "Imagem personalizada",
        imageLabel: "Imagem:",
        imageHelp: "PNG ou JPEG, até 2 MB.",
        imageMode: "Tratamento da imagem:",
        auto: "Detectar automaticamente",
        full: "Assinatura completa",
        logo: "Logotipo / imagem lateral",
        visibleData: "Informações exibidas",
        showDate: "Mostrar data",
        showTime: "Mostrar hora",
        showType: "Mostrar “Assinatura digital PAdES”",
        certificate: "Certificado (.p12 / .pfx):",

        certificateHelp:
            "O certificado é utilizado para criar a assinatura digital do PDF.",

        password: "Senha do certificado:",
        sign: "Assinar documento",
        successTitle: "Documento assinado!",

        successDescription:
            "A assinatura digital PAdES foi aplicada com sucesso.",

        download: "Baixar documento assinado",
        restart: "Assinar outro documento",
        signedBy: "Assinado digitalmente por:",
        signer: "Nome do titular",
        date: "Data da assinatura",
        time: "Hora da assinatura",
        pades: "Assinatura digital PAdES",
        invalidPdf: "Selecione um arquivo PDF válido.",
        pdfTooLarge: "O PDF deve ter no máximo 25 MB.",
        pdfError: "Não foi possível abrir o PDF.",

        positionRequired:
            "Clique no documento para posicionar a assinatura.",

        positionSet:
            "Assinatura posicionada na página {page}.",

        certificateRequired:
            "Selecione o certificado e informe a senha.",

        pdfRequired:
            "Nenhum documento PDF foi selecionado.",

        imageRequired:
            "Selecione uma imagem para esta opção.",

        invalidImage:
            "Utilize somente uma imagem PNG ou JPEG.",

        imageTooLarge:
            "A imagem deve ter no máximo 2 MB.",

        imageLoadError:
            "Não foi possível abrir a imagem selecionada.",

        fullDetected:
            "Detectada como assinatura completa",

        logoDetected:
            "Detectada como logotipo/imagem lateral",

        processing: "Processando...",

        success:
            "Documento assinado com sucesso. O download está disponível.",

        requestTimeout:
            "A operação excedeu o tempo limite. Tente novamente.",

        connectionError:
            "Não foi possível comunicar com o servidor.",

        httpError:
            "Erro HTTP {status}.",

        signedFilenameSuffix: "_assinado",
        backendStarting: "Preparando serviço de assinatura...",
        backendOnline: "Serviço de assinatura disponível",
        backendOffline: "Serviço de assinatura indisponível",
        backendWaking: "Iniciando serviço de assinatura...",

        backendSlow:
            "O serviço está iniciando. Isso pode levar alguns segundos.",

        modeSign: "Assinar",
        modeVerify: "Verificar",
        modeAria: "Modo da aplicação",

        verifySubtitle:
            "Verificação técnica de assinaturas",

        verifyTitle:
            "Verificar assinaturas",

        verifyDescription:
            "Analise tecnicamente assinaturas digitais incorporadas a um PDF.",

        verifyNoticeTitle:
            "Verificação técnica",

        verifyNoticeText:
            "O resultado é informativo e não substitui validadores oficiais nem determina validade jurídica.",

        verifyUploadTitle:
            "Selecionar PDF assinado",

        verifyUploadDescription:
            "O certificado e a senha não são necessários para verificar.",

        verifyHelp:
            "A versão Web envia somente o PDF ao backend para análise.",

        verifyRevocation:
            "Permitir consultas online de revogação (OCSP/CRL) quando disponíveis",

        verifyButton:
            "Verificar assinaturas",

        verifyProcessing:
            "Verificando...",

        verifyNoSignatures:
            "Nenhuma assinatura digital incorporada foi encontrada.",

        verifyCount:
            "{count} assinatura(s) encontrada(s)",

        verifyTechnicalResult:
            "Resultado técnico",

        verifySigner:
            "Titular",

        verifyIssuer:
            "Emissor",

        verifyInfrastructure:
            "Infraestrutura identificada",

        verifyIntegrity:
            "Integridade criptográfica",

        verifyCrypto:
            "Assinatura criptográfica",

        verifyTrust:
            "Cadeia de confiança",

        verifyRevocationStatus:
            "Revogação",

        verifyDigest:
            "Resumo criptográfico",

        verifyMechanism:
            "Mecanismo",

        verifyCoverage:
            "Cobertura do PDF",

        verifyModification:
            "Alterações posteriores",

        verifySigningTime:
            "Data/hora declarada",

        verifyCertificateValidity:
            "Validade do certificado",

        verifySerial:
            "Número de série",

        verifyFingerprint:
            "SHA-256 do certificado",

        verifyChain:
            "Cadeia validada",

        verifyYes:
            "Verificada",

        verifyNo:
            "Não verificada",

        verifyValid:
            "Válida",

        verifyInvalid:
            "Inválida",

        verifyTrusted:
            "Confiável no contexto atual",

        verifyUntrusted:
            "Confiança não estabelecida",

        verifyRevoked:
            "Revogado",

        verifyNotRevoked:
            "Nenhuma revogação detectada",

        verifyIndeterminate:
            "Indeterminado",
        verifyNotChecked:
            "Não consultada",
        verifyDisabled:
            "Desabilitada",

        verifyError:
            "Não foi possível concluir a verificação.",

        verifyDisclaimer:
            "Resultado técnico e informativo; não constitui declaração de validade jurídica."
    },

    en: {
        htmlLang: "en",
        title: "Digital Signer",
        skipLink: "Skip to main content",
        preferences: "Page preferences",
        theme: "Toggle theme",
        languageButton: "PT",
        languageAria: "Change language to Portuguese",

        steps: [
            "Step 1 of 5: Document upload",
            "Step 2 of 5: Placement",
            "Step 3 of 5: Signature type",
            "Step 4 of 5: Configuration",
            "Step 5 of 5: Completed"
        ],

        step1Title: "Document upload",
        uploadTitle: "Click to select the document",
        uploadDescription: "or choose a PDF file",
        pdfHelp: "PDF files only.",

        step2Title: "Signature placement",

        positionDescription:
            "Click the page or press Enter or Space to place the signature. Use the arrow keys to adjust. At the bottom, the next page is displayed automatically.",

        previousPage: "Previous page",
        nextPage: "Next page",
        pagination: "Page navigation",
        pdfPreview: "PDF document preview",

        pdfPage:
            "Document page. Press Enter or Space to place in the center, use the arrow keys to adjust, then press Enter again to continue.",

        page: "Page {current} of {total}",
        cancel: "Cancel",
        confirmPosition: "Confirm position",

        signatureTypeTitle:
            "Which signature type do you want to use?",

        signatureTypeDescription:
            "Choose only the visual appearance. All options continue to use the digital certificate.",

        standard: "Standard",

        standardDescription:
            "Uses the signer's standard visual identity with name, date and PAdES information.",

        simple: "Simple custom",

        simpleDescription:
            "Allows you to customize the text and choose the displayed information.",

        image: "Custom with image",

        imageDescription:
            "Allows you to use a logo or a complete signature image.",

        back: "Back",
        configureTitle: "Configure signature",

        configureDescription:
            "Configure the appearance and provide your digital certificate.",

        simpleOptions: "Custom appearance",
        customTitle: "Top text:",
        imageOptions: "Custom image",
        imageLabel: "Image:",
        imageHelp: "PNG or JPEG, up to 2 MB.",
        imageMode: "Image treatment:",
        auto: "Detect automatically",
        full: "Complete signature",
        logo: "Logo / side image",
        visibleData: "Displayed information",
        showDate: "Show date",
        showTime: "Show time",
        showType: "Show “PAdES digital signature”",
        certificate: "Certificate (.p12 / .pfx):",

        certificateHelp:
            "The certificate is used to create the PDF digital signature.",

        password: "Certificate password:",
        sign: "Sign document",
        successTitle: "Document signed!",

        successDescription:
            "The PAdES digital signature was successfully applied.",

        download: "Download signed document",
        restart: "Sign another document",
        signedBy: "Digitally signed by:",
        signer: "Certificate holder",
        date: "Signature date",
        time: "Signature time",
        pades: "PAdES digital signature",
        invalidPdf: "Select a valid PDF file.",
        pdfTooLarge: "The PDF must be no larger than 25 MB.",
        pdfError: "Unable to open the PDF.",

        positionRequired:
            "Click the document to position the signature.",

        positionSet:
            "Signature positioned on page {page}.",

        certificateRequired:
            "Select the certificate and enter the password.",

        pdfRequired:
            "No PDF document was selected.",

        imageRequired:
            "Select an image for this option.",

        invalidImage:
            "Use only PNG or JPEG images.",

        imageTooLarge:
            "The image must be no larger than 2 MB.",

        imageLoadError:
            "Unable to open the selected image.",

        fullDetected:
            "Detected as a complete signature",

        logoDetected:
            "Detected as a logo/side image",

        processing: "Processing...",

        success:
            "Document signed successfully. The download is available.",

        requestTimeout:
            "The operation timed out. Please try again.",

        connectionError:
            "Unable to communicate with the server.",

        httpError:
            "HTTP error {status}.",

        signedFilenameSuffix: "_signed",
        backendStarting: "Preparing signature service...",
        backendOnline: "Signature service available",
        backendOffline: "Signature service unavailable",
        backendWaking: "Starting signature service...",

        backendSlow:
            "The service is starting. This may take a few seconds.",

        modeSign: "Sign",
        modeVerify: "Verify",
        modeAria: "Application mode",
        verifySubtitle: "Technical signature verification",
        verifyTitle: "Verify signatures",

        verifyDescription:
            "Technically analyse digital signatures embedded in a PDF.",

        verifyNoticeTitle: "Technical verification",

        verifyNoticeText:
            "The result is informational and does not replace official validators or determine legal validity.",

        verifyUploadTitle: "Select signed PDF",

        verifyUploadDescription:
            "The certificate and password are not required for verification.",

        verifyHelp:
            "The Web version sends only the PDF to the backend for analysis.",

        verifyRevocation:
            "Allow online revocation checks (OCSP/CRL) when available",

        verifyButton: "Verify signatures",
        verifyProcessing: "Verifying...",

        verifyNoSignatures:
            "No embedded digital signatures were found.",

        verifyCount:
            "{count} signature(s) found",

        verifyTechnicalResult:
            "Technical result",

        verifySigner: "Holder",
        verifyIssuer: "Issuer",
        verifyInfrastructure: "Identified infrastructure",
        verifyIntegrity: "Cryptographic integrity",
        verifyCrypto: "Cryptographic signature",
        verifyTrust: "Trust chain",
        verifyRevocationStatus: "Revocation",
        verifyDigest: "Cryptographic digest",
        verifyMechanism: "Mechanism",
        verifyCoverage: "PDF coverage",
        verifyModification: "Subsequent changes",
        verifySigningTime: "Declared signing time",
        verifyCertificateValidity: "Certificate validity",
        verifySerial: "Serial number",
        verifyFingerprint: "Certificate SHA-256",
        verifyChain: "Validated chain",
        verifyYes: "Verified",
        verifyNo: "Not verified",
        verifyValid: "Valid",
        verifyInvalid: "Invalid",
        verifyTrusted: "Trusted in current context",
        verifyUntrusted: "Trust not established",
        verifyRevoked: "Revoked",
        verifyNotRevoked: "No revocation detected",
        verifyIndeterminate: "Indeterminate",
        verifyNotChecked: "Not checked",
        verifyDisabled: "Disabled",

        verifyError:
            "Unable to complete verification.",

        verifyDisclaimer:
            "Technical and informational result; it does not constitute a declaration of legal validity."
    }
};

/* ==========================================
   PREFERÊNCIAS
========================================== */

function getSystemLanguage() {
    const language =
        navigator.language ||
        navigator.userLanguage ||
        "en";

    return language
        .toLowerCase()
        .startsWith("pt")
        ? "pt"
        : "en";
}

function getStoredPreference(key) {
    try {
        return window.localStorage.getItem(key);
    } catch {
        return null;
    }
}

function setStoredPreference(key, value) {
    try {
        window.localStorage.setItem(key, value);
    } catch {
        // Preferences still work for the current page when storage is unavailable.
    }
}

const savedLanguage = getStoredPreference("language");
let currentLanguage =
    savedLanguage === "pt" || savedLanguage === "en"
        ? savedLanguage
        : getSystemLanguage();

function t() {
    return translations[currentLanguage];
}

function getSystemTheme() {
    return window.matchMedia(
        "(prefers-color-scheme: dark)"
    ).matches
        ? "dark"
        : "light";
}

function applyTheme(theme) {
    document.documentElement.dataset.theme =
        theme;

    document.documentElement.classList.toggle(
        "dark-theme",
        theme === "dark"
    );

    document.body.classList.toggle(
        "dark-theme",
        theme === "dark"
    );
}

function initializeTheme() {
    const savedTheme =
        getStoredPreference("theme");

    applyTheme(
        savedTheme === "dark" || savedTheme === "light"
            ? savedTheme
            : getSystemTheme()
    );
}

function toggleTheme() {
    const current =
        document.documentElement.dataset.theme ||
        getSystemTheme();

    const next =
        current === "dark"
            ? "light"
            : "dark";

    setStoredPreference(
        "theme",
        next
    );

    applyTheme(next);
}

function toggleLanguage() {
    currentLanguage =
        currentLanguage === "pt"
            ? "en"
            : "pt";

    setStoredPreference(
        "language",
        currentLanguage
    );

    applyTranslations();
    updateSignaturePreview();

    if (lastVerificationResult) {
        renderVerificationResults(
            lastVerificationResult
        );
    }
}

function setText(id, value) {
    const element =
        document.getElementById(id);

    if (element) {
        element.textContent =
            value;
    }
}

function setAriaLabel(id, value) {
    const element =
        document.getElementById(id);

    if (element) {
        element.setAttribute(
            "aria-label",
            value
        );
    }
}

function applyTranslations() {
    const tr = t();

    document.documentElement.lang =
        tr.htmlLang;

    document.title =
        tr.title;

    setText(
        "title",
        tr.title
    );

    setText(
        "skip-link",
        tr.skipLink
    );

    setAriaLabel(
        "top-controls",
        tr.preferences
    );

    setAriaLabel(
        "theme-button",
        tr.theme
    );

    setText(
        "language-label",
        tr.languageButton
    );

    setAriaLabel(
        "language-button",
        tr.languageAria
    );

    setText(
        "step-1-title",
        tr.step1Title
    );

    setText(
        "upload-title",
        tr.uploadTitle
    );

    setText(
        "upload-description",
        tr.uploadDescription
    );

    setText(
        "pdf-help",
        tr.pdfHelp
    );

    setText(
        "step-2-title",
        tr.step2Title
    );

    setText(
        "position-description",
        tr.positionDescription
    );

    setAriaLabel(
        "prev-page",
        tr.previousPage
    );

    setAriaLabel(
        "next-page",
        tr.nextPage
    );

    setAriaLabel(
        "pagination",
        tr.pagination
    );

    setAriaLabel(
        "canvas-container",
        tr.pdfPreview
    );

    setAriaLabel(
        "pdf-stage",
        tr.pdfPage
    );

    setText(
        "cancel-button",
        tr.cancel
    );

    setText(
        "confirm-position-button",
        tr.confirmPosition
    );

    setText(
        "step-3-title",
        tr.signatureTypeTitle
    );

    setText(
        "signature-type-description",
        tr.signatureTypeDescription
    );

    setText(
        "type-standard-title",
        tr.standard
    );

    setText(
        "type-standard-description",
        tr.standardDescription
    );

    setText(
        "type-simple-title",
        tr.simple
    );

    setText(
        "type-simple-description",
        tr.simpleDescription
    );

    setText(
        "type-image-title",
        tr.image
    );

    setText(
        "type-image-description",
        tr.imageDescription
    );

    setText(
        "back-type-button",
        tr.back
    );

    setText(
        "step-4-title",
        tr.configureTitle
    );

    setText(
        "step-4-description",
        tr.configureDescription
    );

    setText(
        "simple-options-title",
        tr.simpleOptions
    );

    setText(
        "custom-title-label",
        tr.customTitle
    );

    setText(
        "image-options-title",
        tr.imageOptions
    );

    setText(
        "image-label",
        tr.imageLabel
    );

    setText(
        "image-help",
        tr.imageHelp
    );

    setText(
        "image-mode-label",
        tr.imageMode
    );

    setText(
        "image-mode-auto",
        tr.auto
    );

    setText(
        "image-mode-full",
        tr.full
    );

    setText(
        "image-mode-logo",
        tr.logo
    );

    setText(
        "visible-data-title",
        tr.visibleData
    );

    setText(
        "show-date-label",
        tr.showDate
    );

    setText(
        "show-time-label",
        tr.showTime
    );

    setText(
        "show-type-label",
        tr.showType
    );

    setText(
        "certificate-label",
        tr.certificate
    );

    setText(
        "certificate-help",
        tr.certificateHelp
    );

    setText(
        "password-label",
        tr.password
    );

    setText(
        "back-config-button",
        tr.back
    );

    setText(
        "sign-button",
        tr.sign
    );

    setText(
        "step-5-title",
        tr.successTitle
    );

    setText(
        "success-description",
        tr.successDescription
    );

    setText(
        "download-button",
        tr.download
    );

    setText(
        "restart-button",
        tr.restart
    );

    setText("mode-sign-label", tr.modeSign);
    setText("mode-verify-label", tr.modeVerify);
    setAriaLabel("mode-switch", tr.modeAria);
    setText("verify-title", tr.verifyTitle);
    setText("verify-description", tr.verifyDescription);
    setText("verify-notice-title", tr.verifyNoticeTitle);
    setText("verify-notice-text", tr.verifyNoticeText);
    setText("verify-upload-title", tr.verifyUploadTitle);
    setText("verify-upload-description", tr.verifyUploadDescription);
    setText("verify-help", tr.verifyHelp);
    setText("verify-revocation-label", tr.verifyRevocation);
    setText("verify-button", tr.verifyButton);
    setAriaLabel("verify-prev-page", tr.previousPage);
    setAriaLabel("verify-next-page", tr.nextPage);
    setAriaLabel("verify-canvas-container", tr.pdfPreview);

    updateStepSubtitle();
    updatePagination();
}

/* ==========================================
   ACESSIBILIDADE
========================================== */

function announce(message) {
    const announcer =
        document.getElementById(
            "screen-reader-announcer"
        );

    if (!announcer) {
        return;
    }

    announcer.textContent = "";

    window.setTimeout(
        () => {
            announcer.textContent =
                message;
        },
        50
    );
}

function focusHeading(step) {
    const heading =
        document.querySelector(
            `#step-${step} h2`
        );

    if (!heading) {
        return;
    }

    heading.setAttribute(
        "tabindex",
        "-1"
    );

    heading.focus({
        preventScroll: true
    });
}

/* ==========================================
   NAVEGAÇÃO ENTRE ETAPAS
========================================== */

function goToStep(step) {
    document
        .querySelectorAll(".step")
        .forEach((element) => {
            element.classList.remove("active");
            element.hidden = true;
        });

    const target =
        document.getElementById(
            `step-${step}`
        );

    if (!target) {
        console.error(
            "Etapa inexistente:",
            step
        );
        return;
    }

    target.hidden = false;
    target.classList.add("active");

    updateStepSubtitle();
    focusHeading(step);
}

function updateStepSubtitle() {
    const subtitle =
        document.getElementById(
            "subtitle"
        );

    if (!subtitle) {
        return;
    }

    const activeStep =
        document.querySelector(
            ".step.active"
        );

    if (!activeStep) {
        return;
    }

    const match =
        activeStep.id.match(
            /^step-(\d+)$/
        );

    if (!match) {
        return;
    }

    const step =
        Number(match[1]);

    if (
        step < 1 ||
        step > t().steps.length
    ) {
        return;
    }

    subtitle.textContent =
        t().steps[step - 1];
}

/* ==========================================
   MODO ASSINAR / VERIFICAR
========================================== */

function setApplicationMode(mode) {
    if (
        mode !== "sign" &&
        mode !== "verify"
    ) {
        return;
    }

    currentMode = mode;

    const signButton =
        document.getElementById(
            "mode-sign-button"
        );

    const verifyButton =
        document.getElementById(
            "mode-verify-button"
        );

    const verifyFlow =
        document.getElementById(
            "verify-panel"
        );

    if (signButton) {
        const selected =
            mode === "sign";

        signButton.classList.toggle(
            "active",
            selected
        );

        signButton.setAttribute(
            "aria-pressed",
            String(selected)
        );
    }

    if (verifyButton) {
        const selected =
            mode === "verify";

        verifyButton.classList.toggle(
            "active",
            selected
        );

        verifyButton.setAttribute(
            "aria-pressed",
            String(selected)
        );
    }

    if (verifyFlow) {
        verifyFlow.hidden =
            mode === "sign";
    }

    if (mode === "sign") {
        goToStep(1);
        wakeBackend();
    } else {
        document
            .querySelectorAll(".step")
            .forEach((element) => {
                element.classList.remove("active");
                element.hidden = true;
            });
        resetVerification();
        updateVerifySubtitle();
        window.requestAnimationFrame(() => {
            document.getElementById("verify-title")?.focus({ preventScroll: true });
        });
        wakeBackend();
    }
}

function updateVerifySubtitle() {
    const subtitle =
        document.getElementById(
            "subtitle"
        );

    if (
        currentMode === "verify" &&
        subtitle
    ) {
        subtitle.textContent =
            t().verifySubtitle;
    }
}

/* ==========================================
   STATUS DO BACKEND / RENDER
========================================== */

function setBackendStatus(
    status,
    message = null
) {
    const indicator =
        document.getElementById(
            "backend-status"
        );

    const text =
        document.getElementById(
            "backend-status-text"
        );

    if (!indicator) {
        return;
    }

    indicator.dataset.status =
        status;

    indicator.classList.remove(
        "backend-starting",
        "backend-online",
        "backend-offline"
    );

    if (status === "online") {
        indicator.classList.add(
            "backend-online"
        );

        if (text) {
            text.textContent =
                message ||
                t().backendOnline;
        }
    } else if (
        status === "starting"
    ) {
        indicator.classList.add(
            "backend-starting"
        );

        if (text) {
            text.textContent =
                message ||
                t().backendStarting;
        }
    } else {
        indicator.classList.add(
            "backend-offline"
        );

        if (text) {
            text.textContent =
                message ||
                t().backendOffline;
        }
    }
}

function delay(milliseconds) {
    return new Promise(
        (resolve) => {
            window.setTimeout(
                resolve,
                milliseconds
            );
        }
    );
}

async function fetchWithTimeout(
    url,
    options = {},
    timeout = REQUEST_TIMEOUT
) {
    const controller =
        new AbortController();

    const timeoutId =
        window.setTimeout(
            () => {
                controller.abort();
            },
            timeout
        );

    try {
        return await fetch(
            url,
            {
                ...options,
                signal:
                    controller.signal
            }
        );
    } finally {
        window.clearTimeout(
            timeoutId
        );
    }
}

async function checkBackendStatus(
    timeout = 10000
) {
    try {
        const response =
            await fetchWithTimeout(
                `${API_BASE_URL}/api/status`,
                {
                    method: "GET",
                    cache: "no-store"
                },
                timeout
            );

        return response.ok;
    } catch {
        return false;
    }
}

async function wakeBackend() {
    if (backendReady) {
        setBackendStatus(
            "online"
        );

        return true;
    }

    if (backendWakePromise) {
        return backendWakePromise;
    }

    backendWakePromise =
        (async () => {
            setBackendStatus(
                "starting",
                t().backendWaking
            );

            const start =
                Date.now();

            let slowMessageShown =
                false;

            while (
                Date.now() - start <
                BACKEND_STATUS_TIMEOUT
            ) {
                const online =
                    await checkBackendStatus(
                        10000
                    );

                if (online) {
                    backendReady = true;

                    setBackendStatus(
                        "online"
                    );

                    announce(
                        t().backendOnline
                    );

                    return true;
                }

                if (
                    !slowMessageShown &&
                    Date.now() - start >
                        15000
                ) {
                    slowMessageShown =
                        true;

                    setBackendStatus(
                        "starting",
                        t().backendSlow
                    );
                }

                await delay(
                    BACKEND_STATUS_RETRY_INTERVAL
                );
            }

            backendReady = false;

            setBackendStatus(
                "offline"
            );

            return false;
        })();

    try {
        return await backendWakePromise;
    } finally {
        backendWakePromise = null;
    }
}

/* ==========================================
   UPLOAD DO PDF PARA ASSINATURA
========================================== */

async function handleFileUpload(event) {
    const file =
        event.target.files?.[0];

    if (!file) {
        return;
    }

    clearSignError();

    const validType =
        file.type ===
            "application/pdf" ||
        file.name
            .toLowerCase()
            .endsWith(".pdf");

    if (!validType) {
        showSignError(
            t().invalidPdf
        );

        event.target.value = "";
        return;
    }

    if (
        file.size >
        MAX_PDF_SIZE
    ) {
        showSignError(
            t().pdfTooLarge
        );

        event.target.value = "";
        return;
    }

    currentFile = file;

    resetSignaturePosition();

    try {
        const arrayBuffer =
            await file.arrayBuffer();

        pdfJsDoc =
            await pdfjsLib
                .getDocument({
                    data:
                        new Uint8Array(
                            arrayBuffer
                        )
                })
                .promise;

        totalPages =
            pdfJsDoc.numPages;

        currentPageNum = 1;

        goToStep(2);

        await renderPage(1);

        wakeBackend();
    } catch (error) {
        console.error(
            "Erro ao abrir PDF:",
            error
        );

        currentFile = null;
        pdfJsDoc = null;
        totalPages = 1;
        currentPageNum = 1;

        showSignError(
            t().pdfError
        );

        goToStep(1);
    }
}

/* ==========================================
   RENDERIZAÇÃO DO PDF
========================================== */

async function renderPage(
    pageNumber,
    preservePosition = false
) {
    if (!pdfJsDoc) {
        return;
    }

    if (
        pageNumber < 1 ||
        pageNumber > totalPages
    ) {
        return;
    }

    const token =
        ++renderToken;

    currentPageNum =
        pageNumber;

    updatePagination();

    const page =
        await pdfJsDoc.getPage(
            pageNumber
        );

    if (
        token !== renderToken
    ) {
        return;
    }

    const canvas =
        document.getElementById(
            "pdf-canvas"
        );

    const stage =
        document.getElementById(
            "pdf-stage"
        );

    const container =
        document.getElementById(
            "canvas-container"
        );

    if (
        !canvas ||
        !stage ||
        !container
    ) {
        return;
    }

    const context =
        canvas.getContext(
            "2d",
            {
                alpha: false
            }
        );

    const originalViewport =
        page.getViewport({
            scale: 1
        });

    const computedStyle =
        window.getComputedStyle(
            container
        );

    const paddingLeft =
        parseFloat(
            computedStyle.paddingLeft
        ) || 0;

    const paddingRight =
        parseFloat(
            computedStyle.paddingRight
        ) || 0;

    const availableWidth =
        Math.max(
            container.clientWidth -
                paddingLeft -
                paddingRight,
            100
        );

    let scale =
        availableWidth /
        originalViewport.width;

    scale =
        Math.min(
            scale,
            1.5
        );

    scale =
        Math.max(
            scale,
            0.1
        );

    currentRenderScale =
        scale;

    const viewport =
        page.getViewport({
            scale
        });

    /*
     * devicePixelRatio melhora a qualidade
     * visual sem alterar as coordenadas CSS
     * usadas para posicionar a assinatura.
     */
    const outputScale =
        Math.max(
            window.devicePixelRatio || 1,
            1
        );

    canvas.width =
        Math.floor(
            viewport.width *
            outputScale
        );

    canvas.height =
        Math.floor(
            viewport.height *
            outputScale
        );

    canvas.style.width =
        `${viewport.width}px`;

    canvas.style.height =
        `${viewport.height}px`;

    stage.style.width =
        `${viewport.width}px`;

    stage.style.height =
        `${viewport.height}px`;

    context.setTransform(
        1,
        0,
        0,
        1,
        0,
        0
    );

    context.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    const renderContext = {
        canvasContext:
            context,
        viewport
    };

    if (
        outputScale !== 1
    ) {
        renderContext.transform = [
            outputScale,
            0,
            0,
            outputScale,
            0,
            0
        ];
    }

    await page.render(
        renderContext
    ).promise;

    if (
        token !== renderToken
    ) {
        return;
    }

    if (signaturePos.placed) {
        restoreSignaturePosition();
    } else {
        resetSignaturePosition();
    }
}

/* ==========================================
   PAGINAÇÃO
========================================== */

function updatePagination() {
    const indicator =
        document.getElementById(
            "page-indicator"
        );

    const previous =
        document.getElementById(
            "prev-page"
        );

    const next =
        document.getElementById(
            "next-page"
        );

    if (indicator) {
        indicator.textContent =
            t()
                .page
                .replace(
                    "{current}",
                    currentPageNum
                )
                .replace(
                    "{total}",
                    totalPages
                );
    }

    if (previous) {
        previous.disabled =
            !pdfJsDoc ||
            currentPageNum <= 1;
    }

    if (next) {
        next.disabled =
            !pdfJsDoc ||
            currentPageNum >=
                totalPages;
    }
}

async function changePage(offset) {
    if (!pdfJsDoc) {
        return;
    }

    const target =
        currentPageNum +
        offset;

    if (
        target < 1 ||
        target > totalPages
    ) {
        return;
    }

    scrollPageLock = true;

    await renderPage(
        target
    );

    const container =
        document.getElementById(
            "canvas-container"
        );

    if (container) {
        if (offset > 0) {
            container.scrollTop = 0;
        } else {
            container.scrollTop =
                Math.max(
                    0,
                    container.scrollHeight -
                    container.clientHeight
                );
        }
        container.dataset.previousScrollTop = String(container.scrollTop);
    }

    announce(
        t()
            .page
            .replace(
                "{current}",
                currentPageNum
            )
            .replace(
                "{total}",
                totalPages
            )
    );

    window.setTimeout(
        () => {
            scrollPageLock =
                false;
        },
        250
    );
}

/* ==========================================
   TROCA AUTOMÁTICA DE PÁGINA PELO SCROLL
========================================== */

async function handlePdfScroll() {
    if (
        !pdfJsDoc ||
        scrollPageLock
    ) {
        return;
    }

    const container =
        document.getElementById(
            "canvas-container"
        );

    if (!container) {
        return;
    }

    const threshold = 8;

    const atBottom =
        container.scrollTop +
            container.clientHeight >=
        container.scrollHeight -
            threshold;

    const atTop =
        container.scrollTop <=
        threshold;

    if (
        atBottom &&
        currentPageNum <
            totalPages
    ) {
        scrollPageLock = true;

        await changePage(1);

        return;
    }

    /*
     * Voltar automaticamente só ocorre
     * quando existe rolagem efetiva.
     * Isso evita trocar de página ao abrir
     * uma página que cabe inteira no container.
     */
    if (
        atTop &&
        container.scrollHeight >
            container.clientHeight +
                threshold &&
        currentPageNum > 1
    ) {
        const previousScrollTop =
            Number(
                container.dataset
                    .previousScrollTop ||
                    0
            );

        if (
            container.scrollTop <
            previousScrollTop
        ) {
            scrollPageLock = true;

            await changePage(-1);
        }
    }

    container.dataset.previousScrollTop =
        String(
            container.scrollTop
        );
}

/* ==========================================
   POSICIONAMENTO DA ASSINATURA
========================================== */

function getSignatureDisplaySize() {
    const width =
        STAMP_WIDTH *
        currentRenderScale;

    const height =
        STAMP_HEIGHT *
        currentRenderScale;

    return {
        width,
        height
    };
}

function placeSignature(event) {
    if (!pdfJsDoc) {
        return;
    }

    /*
     * Permite posicionamento pelo mouse,
     * toque convertido em click e teclado.
     */
    if (
        event.type === "click" &&
        event.button !== undefined &&
        event.button !== 0
    ) {
        return;
    }

    const stage =
        document.getElementById(
            "pdf-stage"
        );

    const box =
        document.getElementById(
            "signature-box"
        );

    if (
        !stage ||
        !box
    ) {
        return;
    }

    const rect =
        stage.getBoundingClientRect();

    const size =
        getSignatureDisplaySize();

    let clickX;
    let clickY;

    if (
        Number.isFinite(
            event.clientX
        ) &&
        Number.isFinite(
            event.clientY
        )
    ) {
        clickX =
            event.clientX -
            rect.left;

        clickY =
            event.clientY -
            rect.top;
    } else {
        clickX =
            rect.width / 2;

        clickY =
            rect.height / 2;
    }

    if (
        clickX < 0 ||
        clickY < 0 ||
        clickX > rect.width ||
        clickY > rect.height
    ) {
        return;
    }

    const visibleWidth =
        Math.min(
            size.width,
            rect.width
        );

    const visibleHeight =
        Math.min(
            size.height,
            rect.height
        );

    let left =
        clickX -
        visibleWidth / 2;

    let top =
        clickY -
        visibleHeight / 2;

    left =
        Math.max(
            0,
            Math.min(
                left,
                rect.width -
                    visibleWidth
            )
        );

    top =
        Math.max(
            0,
            Math.min(
                top,
                rect.height -
                    visibleHeight
            )
        );

    box.style.width =
        `${visibleWidth}px`;

    box.style.height =
        `${visibleHeight}px`;

    box.style.left =
        `${left}px`;

    box.style.top =
        `${top}px`;

    box.style.display =
        "flex";

    signaturePos = {
        placed: true,
        x: left,
        y: top,
        canvasRectWidth:
            rect.width,
        canvasRectHeight:
            rect.height,
        page:
            currentPageNum
    };

    updateSignaturePreview();

    announce(
        t()
            .positionSet
            .replace(
                "{page}",
                currentPageNum
            )
    );
}

function restoreSignaturePosition() {
    if (
        !signaturePos.placed ||
        signaturePos.page !==
            currentPageNum
    ) {
        const box =
            document.getElementById(
                "signature-box"
            );

        if (box) {
            box.style.display =
                "none";
        }

        return;
    }

    const stage =
        document.getElementById(
            "pdf-stage"
        );

    const box =
        document.getElementById(
            "signature-box"
        );

    if (
        !stage ||
        !box
    ) {
        return;
    }

    const rect =
        stage.getBoundingClientRect();

    if (
        signaturePos.canvasRectWidth <= 0 ||
        signaturePos.canvasRectHeight <= 0
    ) {
        resetSignaturePosition();
        return;
    }

    const ratioX =
        rect.width /
        signaturePos.canvasRectWidth;

    const ratioY =
        rect.height /
        signaturePos.canvasRectHeight;

    const size =
        getSignatureDisplaySize();

    const visibleWidth =
        Math.min(
            size.width,
            rect.width
        );

    const visibleHeight =
        Math.min(
            size.height,
            rect.height
        );

    let left =
        signaturePos.x *
        ratioX;

    let top =
        signaturePos.y *
        ratioY;

    left =
        Math.max(
            0,
            Math.min(
                left,
                rect.width -
                    visibleWidth
            )
        );

    top =
        Math.max(
            0,
            Math.min(
                top,
                rect.height -
                    visibleHeight
            )
        );

    box.style.width =
        `${visibleWidth}px`;

    box.style.height =
        `${visibleHeight}px`;

    box.style.left =
        `${left}px`;

    box.style.top =
        `${top}px`;

    box.style.display =
        "flex";

    signaturePos = {
        placed: true,
        x: left,
        y: top,
        canvasRectWidth:
            rect.width,
        canvasRectHeight:
            rect.height,
        page:
            currentPageNum
    };

    updateSignaturePreview();
}

function resetSignaturePosition() {
    signaturePos = {
        placed: false,
        x: 0,
        y: 0,
        canvasRectWidth: 0,
        canvasRectHeight: 0,
        page:
            currentPageNum
    };

    const box =
        document.getElementById(
            "signature-box"
        );

    if (box) {
        box.style.display =
            "none";
    }
}

function confirmPosition() {
    if (
        !signaturePos.placed
    ) {
        alert(
            t().positionRequired
        );

        announce(
            t().positionRequired
        );

        return;
    }

    goToStep(3);
}

/* ==========================================
   POSICIONAMENTO ACESSÍVEL PELO TECLADO
========================================== */

function handlePdfStageKeydown(
    event
) {
    const placementKeys = ["Enter", " "];
    const movement = {
        ArrowLeft: [-1, 0],
        ArrowRight: [1, 0],
        ArrowUp: [0, -1],
        ArrowDown: [0, 1]
    };

    if (!placementKeys.includes(event.key) && !movement[event.key]) {
        return;
    }

    event.preventDefault();

    const stage =
        document.getElementById(
            "pdf-stage"
        );

    if (!stage) {
        return;
    }

    const rect =
        stage.getBoundingClientRect();

    if (
        (event.key === "Enter") &&
        signaturePos.placed &&
        signaturePos.page === currentPageNum
    ) {
        confirmPosition();
        return;
    }

    if (movement[event.key] && signaturePos.placed && signaturePos.page === currentPageNum) {
        const box = document.getElementById("signature-box");
        if (!box) return;
        const step = event.shiftKey ? 10 : 2;
        const [horizontal, vertical] = movement[event.key];
        const maxLeft = Math.max(0, rect.width - box.offsetWidth);
        const maxTop = Math.max(0, rect.height - box.offsetHeight);
        signaturePos.x = Math.max(0, Math.min(maxLeft, signaturePos.x + horizontal * step));
        signaturePos.y = Math.max(0, Math.min(maxTop, signaturePos.y + vertical * step));
        signaturePos.canvasRectWidth = rect.width;
        signaturePos.canvasRectHeight = rect.height;
        box.style.left = `${signaturePos.x}px`;
        box.style.top = `${signaturePos.y}px`;
        announce(t().positionSet.replace("{page}", currentPageNum));
        return;
    }

    if (!placementKeys.includes(event.key)) return;

    placeSignature({
        type: "keyboard",
        clientX:
            rect.left +
            rect.width / 2,
        clientY:
            rect.top +
            rect.height / 2
    });
}

function handlePdfPreviewKeydown(event) {
    const forward = event.key === "PageDown" || event.key === "ArrowDown";
    const backward = event.key === "PageUp" || event.key === "ArrowUp";
    if (!pdfJsDoc || (!forward && !backward)) {
        return;
    }
    if (scrollPageLock) {
        event.preventDefault();
        return;
    }
    const container = event.currentTarget;
    const atTop = container.scrollTop <= 8;
    const atBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 8;
    if (forward && atBottom && currentPageNum < totalPages) {
        event.preventDefault();
        if (event.repeat) return;
        changePage(1);
    } else if (backward && atTop && currentPageNum > 1) {
        event.preventDefault();
        if (event.repeat) return;
        changePage(-1);
    }
}

/* ==========================================
   SELEÇÃO DO TIPO DE ASSINATURA
========================================== */

function selectSignatureType(type) {
    if (
        ![
            "standard",
            "simple",
            "image"
        ].includes(type)
    ) {
        return;
    }

    currentSignatureType =
        type;

    document
        .querySelectorAll(
            "[data-signature-type]"
        )
        .forEach(
            (element) => {
                const selected =
                    element.dataset
                        .signatureType ===
                    type;

                element.classList.toggle(
                    "selected",
                    selected
                );

                element.setAttribute(
                    "aria-pressed",
                    String(selected)
                );
            }
        );

    configureSignatureStep();

    goToStep(4);
}

function configureSignatureStep() {
    const simpleOptions =
        document.getElementById(
            "simple-options"
        );

    const imageOptions =
        document.getElementById(
            "image-options"
        );

    const visibleData =
        document.getElementById(
            "visible-data-options"
        );

    if (simpleOptions) {
        simpleOptions.hidden =
            currentSignatureType !==
            "simple";
    }

    if (imageOptions) {
        imageOptions.hidden =
            currentSignatureType !==
            "image";
    }

    if (visibleData) {
        visibleData.hidden =
            currentSignatureType ===
            "standard";
    }

    updateSignaturePreview();
}

/* ==========================================
   IMAGEM PERSONALIZADA
========================================== */

function changeSignatureImage(event) {
    const file =
        event.target.files?.[0];

    clearSignError();

    if (!file) {
        clearCustomImage();
        return;
    }

    const allowedTypes = [
        "image/png",
        "image/jpeg"
    ];

    if (
        !allowedTypes.includes(
            file.type
        )
    ) {
        event.target.value = "";

        showSignError(
            t().invalidImage
        );

        clearCustomImage();

        return;
    }

    if (
        file.size >
        MAX_IMAGE_SIZE
    ) {
        event.target.value = "";

        showSignError(
            t().imageTooLarge
        );

        clearCustomImage();

        return;
    }

    if (customImageUrl) {
        URL.revokeObjectURL(
            customImageUrl
        );
    }

    customImageFile = file;

    customImageUrl =
        URL.createObjectURL(
            file
        );

    const image =
        new Image();

    image.onload =
        () => {
            imageNaturalWidth =
                image.naturalWidth;

            imageNaturalHeight =
                image.naturalHeight;

            detectedImageMode =
                detectImageMode();

            updateImageInfo();
            updateSignaturePreview();
        };

    image.onerror =
        () => {
            showSignError(
                t().imageLoadError
            );

            clearCustomImage();
        };

    image.src =
        customImageUrl;
}

function clearCustomImage() {
    if (customImageUrl) {
        URL.revokeObjectURL(
            customImageUrl
        );
    }

    customImageFile = null;
    customImageUrl = null;

    imageNaturalWidth = 0;
    imageNaturalHeight = 0;

    detectedImageMode =
        "default";

    const input =
        document.getElementById(
            "signature-image-input"
        );

    if (input) {
        input.value = "";
    }

    updateImageInfo();
    updateSignaturePreview();
}

function detectImageMode() {
    const modeSelect =
        document.getElementById(
            "image-mode"
        );

    const selected =
        modeSelect?.value ||
        "auto";

    if (
        selected === "full" ||
        selected === "logo"
    ) {
        return selected;
    }

    if (
        imageNaturalWidth <= 0 ||
        imageNaturalHeight <= 0
    ) {
        return "default";
    }

    const ratio =
        imageNaturalWidth /
        imageNaturalHeight;

    return (
        ratio >=
        FULL_SIGNATURE_RATIO
            ? "full"
            : "logo"
    );
}

function updateImageMode() {
    detectedImageMode =
        detectImageMode();

    updateImageInfo();
    updateSignaturePreview();
}

function updateImageInfo() {
    const info =
        document.getElementById(
            "image-info"
        );

    if (!info) {
        return;
    }

    if (
        !customImageFile ||
        imageNaturalWidth <= 0 ||
        imageNaturalHeight <= 0
    ) {
        info.textContent = "";
        info.hidden = true;
        return;
    }

    const mode =
        detectedImageMode === "full"
            ? t().fullDetected
            : t().logoDetected;

    info.textContent =
        `${mode} — ` +
        `${imageNaturalWidth} × ` +
        `${imageNaturalHeight}px`;

    info.hidden = false;
}

/* ==========================================
   PRÉVIA DA ASSINATURA
========================================== */

function updateSignaturePreview() {
    const preview =
        document.getElementById(
            "signature-box"
        );

    if (!preview) {
        return;
    }

    preview.innerHTML = "";

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "signature-preview-content";

    if (
        currentSignatureType ===
            "image" &&
        customImageUrl &&
        detectedImageMode ===
            "full"
    ) {
        const image =
            document.createElement(
                "img"
            );

        image.src =
            customImageUrl;

        image.alt =
            currentLanguage === "pt"
                ? "Prévia da assinatura personalizada"
                : "Custom signature preview";

        image.className =
            "signature-full-image-preview";

        wrapper.appendChild(
            image
        );

        const dateLine =
            buildDatePreviewText();

        if (dateLine) {
            const metadata =
                document.createElement(
                    "small"
                );

            metadata.textContent =
                dateLine;

            wrapper.appendChild(
                metadata
            );
        }

        preview.appendChild(
            wrapper
        );

        return;
    }

    const visualRow =
        document.createElement(
            "div"
        );

    visualRow.className =
        "signature-preview-row";

    const iconArea =
        document.createElement(
            "div"
        );

    iconArea.className =
        "signature-preview-icon";

    if (
        currentSignatureType ===
            "image" &&
        customImageUrl
    ) {
        const image =
            document.createElement(
                "img"
            );

        image.src =
            customImageUrl;

        image.alt = "";

        image.className =
            "signature-logo-preview";

        iconArea.appendChild(
            image
        );
    } else {
        const symbol =
            document.createElement(
                "span"
            );

        symbol.className =
            "signature-default-symbol";

        symbol.setAttribute(
            "aria-hidden",
            "true"
        );

        symbol.textContent =
            "✓";

        iconArea.appendChild(
            symbol
        );
    }

    const textArea =
        document.createElement(
            "div"
        );

    textArea.className =
        "signature-preview-text";

    const title =
        document.createElement(
            "span"
        );

    title.className =
        "signature-preview-title";

    title.textContent =
        getSignatureTitle();

    textArea.appendChild(
        title
    );

    const name =
        document.createElement(
            "strong"
        );

    name.textContent =
        t().signer;

    textArea.appendChild(
        name
    );

    const dateLine =
        buildDatePreviewText();

    if (dateLine) {
        const date =
            document.createElement(
                "small"
            );

        date.textContent =
            dateLine;

        textArea.appendChild(
            date
        );
    }

    const showType =
        document.getElementById(
            "show-type"
        );

    if (
        currentSignatureType !==
            "standard" &&
        showType?.checked
    ) {
        const type =
            document.createElement(
                "small"
            );

        type.textContent =
            t().pades;

        textArea.appendChild(
            type
        );
    }

    visualRow.appendChild(
        iconArea
    );

    visualRow.appendChild(
        textArea
    );

    wrapper.appendChild(
        visualRow
    );

    preview.appendChild(
        wrapper
    );

    fitSignaturePreviewName(name, textArea);
}

function fitSignaturePreviewName(name, container) {
    let fontSize = 9;
    name.style.fontSize = `${fontSize}px`;
    while (fontSize > 4.5 && name.scrollWidth > container.clientWidth) {
        fontSize -= 0.25;
        name.style.fontSize = `${fontSize}px`;
    }
}

function getSignatureTitle() {
    if (
        currentSignatureType ===
        "standard"
    ) {
        return t().signedBy;
    }

    const input =
        document.getElementById(
            "custom-title"
        );

    const value =
        input?.value?.trim();

    return (
        value ||
        t().signedBy
    );
}

function buildDatePreviewText() {
    const showDate =
        document.getElementById(
            "show-date"
        );

    const showTime =
        document.getElementById(
            "show-time"
        );

    const parts = [];

    if (
        currentSignatureType ===
        "standard"
    ) {
        parts.push(
            t().date
        );

        return parts.join(
            " • "
        );
    }

    if (showDate?.checked) {
        parts.push(
            t().date
        );
    }

    if (showTime?.checked) {
        parts.push(
            t().time
        );
    }

    return parts.join(
        " • "
    );
}

/* ==========================================
   ERROS DA ASSINATURA
========================================== */

function showSignError(message) {
    const element =
        document.getElementById(
            "sign-error"
        );

    if (!element) {
        alert(message);
        return;
    }

    element.textContent =
        message;

    element.hidden = false;

    announce(message);
}

function clearSignError() {
    const element =
        document.getElementById(
            "sign-error"
        );

    if (!element) {
        return;
    }

    element.textContent = "";
    element.hidden = true;
}

/* ==========================================
   CONFIGURAÇÃO VISUAL ENVIADA AO BACKEND
========================================== */

function buildVisualConfiguration() {
    const showDate =
        document.getElementById(
            "show-date"
        );

    const showTime =
        document.getElementById(
            "show-time"
        );

    const showType =
        document.getElementById(
            "show-type"
        );

    /*
     * A assinatura padrão mantém
     * data e identificação PAdES
     * determinadas pelo backend.
     */
    if (
        currentSignatureType ===
        "standard"
    ) {
        return {
            titulo:
                t().signedBy,
            mostrarData:
                true,
            mostrarHora:
                false,
            mostrarTipo:
                true
        };
    }

    return {
        titulo:
            getSignatureTitle(),

        mostrarData:
            Boolean(
                showDate?.checked
            ),

        mostrarHora:
            Boolean(
                showTime?.checked
            ),

        mostrarTipo:
            Boolean(
                showType?.checked
            )
    };
}

/* ==========================================
   VALIDAÇÃO ANTES DA ASSINATURA
========================================== */

function validateSigningInputs() {
    clearSignError();

    if (!currentFile) {
        showSignError(
            t().pdfRequired
        );

        return false;
    }

    if (
        !signaturePos.placed
    ) {
        showSignError(
            t().positionRequired
        );

        return false;
    }

    const certificateInput =
        document.getElementById(
            "certificate-input"
        );

    const passwordInput =
        document.getElementById(
            "certificate-password"
        );

    const certificate =
        certificateInput
            ?.files?.[0];

    const password =
        passwordInput
            ?.value || "";

    if (
        !certificate ||
        !password
    ) {
        showSignError(
            t().certificateRequired
        );

        return false;
    }

    if (
        currentSignatureType ===
            "image" &&
        !customImageFile
    ) {
        showSignError(
            t().imageRequired
        );

        return false;
    }

    return true;
}

/* ==========================================
   ASSINAR DOCUMENTO
========================================== */

async function signWithBackend() {
    if (
        !validateSigningInputs()
    ) {
        return;
    }

    const button =
        document.getElementById(
            "sign-button"
        );

    const certificateInput =
        document.getElementById(
            "certificate-input"
        );

    const passwordInput =
        document.getElementById(
            "certificate-password"
        );

    const certificate =
        certificateInput.files[0];

    const password =
        passwordInput.value;

    button.disabled = true;

    button.textContent =
        t().backendWaking;

    /*
     * Se o Render ainda estiver dormindo,
     * espera o health check ficar disponível
     * antes de enviar certificado e senha.
     */
    if (!backendReady) {
        const ready =
            await wakeBackend();

        if (!ready) {
            showSignError(
                t().backendOffline
            );

            button.disabled = false;

            button.textContent =
                t().sign;

            return;
        }
    }

    button.textContent =
        t().processing;

    const formData =
        new FormData();

    formData.append(
        "documento",
        currentFile
    );

    formData.append(
        "certificado",
        certificate
    );

    formData.append(
        "senha",
        password
    );

    formData.append(
        "posicao",
        JSON.stringify(
            signaturePos
        )
    );

    formData.append(
        "tipo_assinatura",
        currentSignatureType
    );

    formData.append(
        "visual",
        JSON.stringify(
            buildVisualConfiguration()
        )
    );

    if (
        currentSignatureType ===
        "image"
    ) {
        formData.append(
            "imagem_assinatura",
            customImageFile
        );

        formData.append(
            "modo_imagem",
            detectedImageMode
        );
    }

    const controller =
        new AbortController();

    const timeoutId =
        window.setTimeout(
            () => {
                controller.abort();
            },
            REQUEST_TIMEOUT
        );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/api/assinar`,
                {
                    method: "POST",
                    body: formData,
                    signal:
                        controller.signal
                }
            );

        /*
         * A senha deixa de ser necessária
         * assim que a requisição foi enviada.
         */
        passwordInput.value = "";

        if (!response.ok) {
            let message =
                t()
                    .httpError
                    .replace(
                        "{status}",
                        response.status
                    );

            try {
                const data =
                    await response.json();

                if (data?.erro) {
                    message =
                        data.erro;
                }
            } catch {
                /*
                 * Mantém a mensagem HTTP.
                 */
            }

            throw new Error(
                message
            );
        }

        const contentType =
            response.headers.get(
                "content-type"
            ) || "";

        if (
            !contentType.includes(
                "application/pdf"
            )
        ) {
            throw new Error(
                t().connectionError
            );
        }

        const blob =
            await response.blob();

        prepareSignedDownload(
            blob
        );

        /*
         * Também limpa a seleção visual
         * do certificado depois da assinatura.
         */
        certificateInput.value = "";

        goToStep(5);

        announce(
            t().success
        );
    } catch (error) {
        console.error(
            "Erro ao assinar:",
            error
        );

        if (
            error.name ===
            "AbortError"
        ) {
            showSignError(
                t().requestTimeout
            );
        } else if (
            error instanceof TypeError
        ) {
            backendReady = false;

            setBackendStatus(
                "offline"
            );

            showSignError(
                t().connectionError
            );
        } else {
            showSignError(
                error.message ||
                t().connectionError
            );
        }
    } finally {
        window.clearTimeout(
            timeoutId
        );

        button.disabled = false;

        button.textContent =
            t().sign;
    }
}

/* ==========================================
   DOWNLOAD DO PDF ASSINADO
========================================== */

function prepareSignedDownload(blob) {
    if (currentDownloadUrl) {
        URL.revokeObjectURL(
            currentDownloadUrl
        );
    }

    currentDownloadUrl =
        URL.createObjectURL(
            blob
        );

    const button =
        document.getElementById(
            "download-button"
        );

    if (!button) {
        return;
    }

    button.classList.remove("hidden");
    button.hidden = false;

    button.onclick =
        downloadSignedPdf;
}

function downloadSignedPdf() {
    if (
        !currentDownloadUrl
    ) {
        return;
    }

    const anchor =
        document.createElement(
            "a"
        );

    anchor.href =
        currentDownloadUrl;

    const originalName =
        currentFile?.name ||
        "documento.pdf";

    const baseName =
        originalName
            .toLowerCase()
            .endsWith(".pdf")
            ? originalName.slice(
                0,
                -4
            )
            : originalName;

    anchor.download =
        `${baseName}${t().signedFilenameSuffix}.pdf`;

    document.body.appendChild(
        anchor
    );

    anchor.click();

    anchor.remove();
}

/* ==========================================
   RESET DO FLUXO DE ASSINATURA
========================================== */

function resetSigningFlow() {
    currentFile = null;

    if (pdfJsDoc) {
        try {
            pdfJsDoc.destroy();
        } catch {
            /*
             * Nada a fazer.
             */
        }
    }

    pdfJsDoc = null;

    currentPageNum = 1;
    totalPages = 1;
    currentRenderScale = 1;

    currentSignatureType =
        "standard";

    renderToken += 1;
    scrollPageLock = false;

    resetSignaturePosition();
    clearCustomImage();
    clearSignError();

    const fileInput =
        document.getElementById(
            "pdf-input"
        );

    const certificateInput =
        document.getElementById(
            "certificate-input"
        );

    const passwordInput =
        document.getElementById(
            "certificate-password"
        );

    const customTitle =
        document.getElementById(
            "custom-title"
        );

    const showDate =
        document.getElementById(
            "show-date"
        );

    const showTime =
        document.getElementById(
            "show-time"
        );

    const showType =
        document.getElementById(
            "show-type"
        );

    const imageMode =
        document.getElementById(
            "image-mode"
        );

    if (fileInput) {
        fileInput.value = "";
    }

    if (certificateInput) {
        certificateInput.value = "";
    }

    if (passwordInput) {
        passwordInput.value = "";
    }

    if (customTitle) {
        customTitle.value =
            t().signedBy;
    }

    if (showDate) {
        showDate.checked =
            true;
    }

    if (showTime) {
        showTime.checked =
            false;
    }

    if (showType) {
        showType.checked =
            true;
    }

    if (imageMode) {
        imageMode.value =
            "auto";
    }

    if (currentDownloadUrl) {
        URL.revokeObjectURL(
            currentDownloadUrl
        );

        currentDownloadUrl = null;
    }

    const downloadButton =
        document.getElementById(
            "download-button"
        );

    if (downloadButton) {
        downloadButton.classList.remove("hidden");
        downloadButton.hidden =
            true;
    }

    configureSignatureStep();
    updateSignaturePreview();
    updatePagination();

    if (
        currentMode === "sign"
    ) {
        goToStep(1);
    }
}

/* ==========================================
   LIMPEZA DE DADOS SENSÍVEIS
========================================== */

function clearSensitiveFields() {
    const certificateInput =
        document.getElementById(
            "certificate-input"
        );

    const passwordInput =
        document.getElementById(
            "certificate-password"
        );

    if (certificateInput) {
        certificateInput.value =
            "";
    }

    if (passwordInput) {
        passwordInput.value =
            "";
    }
}

/* ==========================================
   UPLOAD PARA VERIFICAÇÃO
========================================== */

function handleVerificationFile(
    event
) {
    const file =
        event.target.files?.[0];

    clearVerificationError();

    lastVerificationResult =
        null;

    clearVerificationResults();

    if (!file) {
        return;
    }

    const validType =
        file.type ===
            "application/pdf" ||
        file.name
            .toLowerCase()
            .endsWith(".pdf");

    if (!validType) {
        showVerificationError(
            t().invalidPdf
        );

        event.target.value =
            "";

        return;
    }

    if (
        file.size >
        MAX_PDF_SIZE
    ) {
        showVerificationError(
            t().pdfTooLarge
        );

        event.target.value =
            "";

        return;
    }

    const filename =
        document.getElementById(
            "verify-file-name"
        );

    if (filename) {
        filename.textContent =
            file.name;
    }

    loadVerificationPreview(file);
}

function handlePdfWheel(event) {
    if (!pdfJsDoc || scrollPageLock || !event.deltaY) return;

    const container = event.currentTarget;
    const threshold = 8;
    const atTop = container.scrollTop <= threshold;
    const atBottom = container.scrollTop + container.clientHeight >=
        container.scrollHeight - threshold;

    if (event.deltaY < 0 && atTop && currentPageNum > 1) {
        event.preventDefault();
        changePage(-1);
    } else if (event.deltaY > 0 && atBottom && currentPageNum < totalPages) {
        event.preventDefault();
        changePage(1);
    }
}

async function loadVerificationPreview(file) {
    clearVerificationPreview();

    try {
        const data = new Uint8Array(
            await file.arrayBuffer()
        );

        verificationPdfDoc = await pdfjsLib
            .getDocument({ data })
            .promise;
        verificationPageNum = 1;

        document
            .getElementById("verify-preview")
            ?.classList.remove("hidden");

        await renderVerificationPreview();
    } catch (error) {
        console.error("Erro ao gerar pré-visualização:", error);
        clearVerificationPreview();
        showVerificationError(t().pdfError);
    }
}

async function renderVerificationPreview() {
    if (!verificationPdfDoc) {
        return;
    }

    const token = ++verificationRenderToken;
    const page = await verificationPdfDoc.getPage(
        verificationPageNum
    );
    const canvas = document.getElementById(
        "verify-pdf-canvas"
    );

    if (!canvas || token !== verificationRenderToken) {
        return;
    }

    const parentWidth = Math.max(
        canvas.parentElement?.clientWidth || 600,
        100
    );
    const baseViewport = page.getViewport({ scale: 1 });
    const scale = Math.min(
        1.5,
        parentWidth / baseViewport.width
    );
    const viewport = page.getViewport({ scale });
    const outputScale = Math.max(window.devicePixelRatio || 1, 1);
    const context = canvas.getContext("2d", { alpha: false });

    canvas.width = Math.floor(viewport.width * outputScale);
    canvas.height = Math.floor(viewport.height * outputScale);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    await page.render({
        canvasContext: context,
        viewport,
        transform: outputScale === 1
            ? undefined
            : [outputScale, 0, 0, outputScale, 0, 0]
    }).promise;

    if (token !== verificationRenderToken) {
        return;
    }

    const indicator = document.getElementById("verify-page-indicator");
    const previous = document.getElementById("verify-prev-page");
    const next = document.getElementById("verify-next-page");

    if (indicator) {
        indicator.textContent = t().page
            .replace("{current}", verificationPageNum)
            .replace("{total}", verificationPdfDoc.numPages);
    }
    if (previous) previous.disabled = verificationPageNum <= 1;
    if (next) next.disabled = verificationPageNum >= verificationPdfDoc.numPages;
}

async function changeVerificationPage(offset) {
    if (!verificationPdfDoc || verificationScrollPageLock) return;
    const target = verificationPageNum + offset;
    if (target < 1 || target > verificationPdfDoc.numPages) return;
    verificationScrollPageLock = true;
    verificationPageNum = target;
    await renderVerificationPreview();

    const container = document.getElementById("verify-canvas-container");
    if (container) {
        container.scrollTop = offset < 0
            ? Math.max(0, container.scrollHeight - container.clientHeight)
            : 0;
    }
    window.setTimeout(() => {
        verificationScrollPageLock = false;
    }, 250);
}

function handleVerificationScroll() {
    if (!verificationPdfDoc || verificationScrollPageLock) return;
    const container = document.getElementById("verify-canvas-container");
    if (!container || verificationPageNum >= verificationPdfDoc.numPages) return;
    const atBottom = container.scrollTop + container.clientHeight >=
        container.scrollHeight - 8;
    if (atBottom && container.scrollHeight > container.clientHeight + 8) {
        changeVerificationPage(1);
    }
}

function handleVerificationWheel(event) {
    if (!verificationPdfDoc || verificationScrollPageLock || !event.deltaY) return;
    const container = event.currentTarget;
    const atTop = container.scrollTop <= 8;
    const atBottom = container.scrollTop + container.clientHeight >=
        container.scrollHeight - 8;
    if (event.deltaY < 0 && atTop && verificationPageNum > 1) {
        event.preventDefault();
        changeVerificationPage(-1);
    } else if (
        event.deltaY > 0 && atBottom &&
        verificationPageNum < verificationPdfDoc.numPages
    ) {
        event.preventDefault();
        changeVerificationPage(1);
    }
}

function handleVerificationPreviewKeydown(event) {
    const forward = event.key === "PageDown" || event.key === "ArrowDown";
    const backward = event.key === "PageUp" || event.key === "ArrowUp";
    if (!verificationPdfDoc || (!forward && !backward)) {
        return;
    }
    if (verificationScrollPageLock) {
        event.preventDefault();
        return;
    }
    const container = event.currentTarget;
    const atTop = container.scrollTop <= 8;
    const atBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 8;
    if (
        forward && atBottom &&
        verificationPageNum < verificationPdfDoc.numPages
    ) {
        event.preventDefault();
        if (event.repeat) return;
        changeVerificationPage(1);
    } else if (backward && atTop && verificationPageNum > 1) {
        event.preventDefault();
        if (event.repeat) return;
        changeVerificationPage(-1);
    }
}

function clearVerificationPreview() {
    verificationRenderToken += 1;
    verificationPdfDoc = null;
    verificationPageNum = 1;
    verificationScrollPageLock = false;
    const preview = document.getElementById("verify-preview");
    if (preview) preview.classList.add("hidden");
}

/* ==========================================
   VERIFICAÇÃO TÉCNICA
========================================== */

async function verifyWithBackend() {
    clearVerificationError();
    clearVerificationResults();

    const input =
        document.getElementById(
            "verify-pdf-input"
        );

    const file =
        input?.files?.[0];

    if (!file) {
        showVerificationError(
            t().pdfRequired
        );

        return;
    }

    const button =
        document.getElementById(
            "verify-button"
        );

    if (!button) {
        return;
    }

    button.disabled =
        true;

    button.textContent =
        t().backendWaking;

    if (!backendReady) {
        const ready =
            await wakeBackend();

        if (!ready) {
            button.disabled =
                false;

            button.textContent =
                t().verifyButton;

            showVerificationError(
                t().backendOffline
            );

            return;
        }
    }

    button.textContent =
        t().verifyProcessing;

    const formData =
        new FormData();

    formData.append(
        "documento",
        file
    );

    const revocation =
        document.getElementById(
            "verify-revocation"
        );

    formData.append(
        "consultar_revogacao",
        String(
            Boolean(
                revocation?.checked
            )
        )
    );

    const controller =
        new AbortController();

    const timeoutId =
        window.setTimeout(
            () => {
                controller.abort();
            },
            REQUEST_TIMEOUT
        );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/api/verificar`,
                {
                    method: "POST",
                    body: formData,
                    signal:
                        controller.signal
                }
            );

        let data = null;

        try {
            data =
                await response.json();
        } catch {
            throw new Error(
                t().connectionError
            );
        }

        if (!response.ok) {
            throw new Error(
                data?.erro ||
                t()
                    .httpError
                    .replace(
                        "{status}",
                        response.status
                    )
            );
        }

        lastVerificationResult =
            data;

        renderVerificationResults(
            data
        );

        announce(
            t()
                .verifyCount
                .replace(
                    "{count}",
                    data?.assinaturas?.length ||
                    0
                )
        );
    } catch (error) {
        console.error(
            "Erro ao verificar:",
            error
        );

        if (
            error.name ===
            "AbortError"
        ) {
            showVerificationError(
                t().requestTimeout
            );
        } else if (
            error instanceof TypeError
        ) {
            backendReady = false;

            setBackendStatus(
                "offline"
            );

            showVerificationError(
                t().connectionError
            );
        } else {
            showVerificationError(
                error.message ||
                t().verifyError
            );
        }
    } finally {
        window.clearTimeout(
            timeoutId
        );

        button.disabled =
            false;

        button.textContent =
            t().verifyButton;
    }
}

/* ==========================================
   ERROS DA VERIFICAÇÃO
========================================== */

function showVerificationError(
    message
) {
    const element =
        document.getElementById(
            "verify-error"
        );

    if (!element) {
        alert(message);
        return;
    }

    element.textContent =
        message;

    element.hidden =
        false;

    announce(message);
}

function clearVerificationError() {
    const element =
        document.getElementById(
            "verify-error"
        );

    if (!element) {
        return;
    }

    element.textContent = "";

    element.hidden =
        true;
}

/* ==========================================
   LIMPEZA DOS RESULTADOS
========================================== */

function clearVerificationResults() {
    const container =
        document.getElementById(
            "verification-results"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";
    container.hidden = true;
    container.classList.add(
        "hidden"
    );
}

function resetVerification() {
    const input =
        document.getElementById(
            "verify-pdf-input"
        );

    const filename =
        document.getElementById(
            "verify-file-name"
        );

    if (input) {
        input.value = "";
    }

    if (filename) {
        filename.textContent =
            "";
    }

    lastVerificationResult =
        null;

    clearVerificationPreview();
    clearVerificationError();
    clearVerificationResults();
}

/* ==========================================
   RESULTADOS DA VERIFICAÇÃO
========================================== */

function renderVerificationResults(data) {
    const container =
        document.getElementById(
            "verification-results"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";
    container.hidden = false;
    container.classList.remove(
        "hidden"
    );

    const signatures =
        Array.isArray(data?.assinaturas)
            ? data.assinaturas
            : [];

    const heading =
        document.createElement("h3");

    heading.className =
        "verification-results-title";
    heading.id = "verification-results-title";
    heading.tabIndex = -1;

    heading.textContent =
        signatures.length === 0
            ? t().verifyNoSignatures
            : t()
                .verifyCount
                .replace(
                    "{count}",
                    signatures.length
                );

    container.appendChild(
        heading
    );

    if (signatures.length === 0) {
        appendVerificationDisclaimer(
            container,
            data
        );

        heading.focus({ preventScroll: true });
        return;
    }

    signatures.forEach(
        (signature, index) => {
            const card =
                createVerificationCard(
                    signature,
                    index
                );

            container.appendChild(
                card
            );
        }
    );

    appendVerificationDisclaimer(
        container,
        data
    );
    heading.focus({ preventScroll: true });
}

/* ==========================================
   CARTÃO DE UMA ASSINATURA
========================================== */

function createVerificationCard(
    signature,
    index
) {
    signature = normalizeVerificationSignature(signature);
    const article =
        document.createElement(
            "article"
        );

    article.className =
        "verification-card";

    const title =
        document.createElement(
            "h4"
        );

    title.className =
        "verification-card-title";

    const fieldName =
        getFirstValue(
            signature,
            [
                "campo",
                "field_name",
                "nome_campo"
            ]
        );

    title.textContent =
        fieldName
            ? `${t().verifyTechnicalResult} ${index + 1} — ${fieldName}`
            : `${t().verifyTechnicalResult} ${index + 1}`;

    article.appendChild(
        title
    );

    const summary =
        document.createElement(
            "div"
        );

    summary.className =
        "verification-summary";

    appendStatusBadge(
        summary,
        t().verifyIntegrity,
        getBooleanStatus(
            signature,
            [
                "integridade",
                "intact"
            ]
        ),
        t().verifyYes,
        t().verifyNo
    );

    appendStatusBadge(
        summary,
        t().verifyCrypto,
        getBooleanStatus(
            signature,
            [
                "assinatura_valida",
                "valid"
            ]
        ),
        t().verifyValid,
        t().verifyInvalid
    );

    appendTrustBadge(
        summary,
        signature
    );

    appendRevocationBadge(
        summary,
        signature
    );

    article.appendChild(
        summary
    );

    const details =
        document.createElement(
            "dl"
        );

    details.className =
        "verification-details";

    appendDetail(
        details,
        t().verifySigner,
        getFirstValue(
            signature,
            [
                "titular",
                "subject",
                "signer",
                "signer_name"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyIssuer,
        getFirstValue(
            signature,
            [
                "emissor",
                "issuer"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyInfrastructure,
        getFirstValue(
            signature,
            [
                "infraestrutura",
                "infrastructure"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyCertificateValidity,
        formatCertificateValidity(
            signature
        )
    );

    appendDetail(
        details,
        t().verifySerial,
        getFirstValue(
            signature,
            [
                "numero_serie",
                "serial_number",
                "serial"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyFingerprint,
        getFirstValue(
            signature,
            [
                "fingerprint_sha256",
                "sha256",
                "fingerprint"
            ]
        ),
        true
    );

    appendDetail(
        details,
        t().verifySigningTime,
        getFirstValue(
            signature,
            [
                "data_assinatura",
                "signing_time",
                "timestamp"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyDigest,
        getFirstValue(
            signature,
            [
                "algoritmo_digest",
                "digest_algorithm",
                "md_algorithm"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyMechanism,
        getFirstValue(
            signature,
            [
                "mecanismo",
                "signature_mechanism",
                "signature_algorithm"
            ]
        )
    );

    appendDetail(
        details,
        t().verifyCoverage,
        formatCoverage(
            signature
        )
    );

    appendDetail(
        details,
        t().verifyModification,
        formatModification(
            signature
        )
    );

    appendDetail(
        details,
        t().verifyTrust,
        formatTrust(
            signature
        )
    );

    appendDetail(
        details,
        t().verifyRevocationStatus,
        formatRevocation(
            signature
        )
    );

    article.appendChild(
        details
    );

    const chain =
        getFirstValue(
            signature,
            [
                "cadeia",
                "validation_path",
                "certificate_chain"
            ]
        );

    if (
        Array.isArray(chain) &&
        chain.length > 0
    ) {
        article.appendChild(
            createCertificateChain(
                chain
            )
        );
    }

    const warnings =
        getFirstValue(
            signature,
            [
                "avisos",
                "warnings"
            ]
        );

    if (
        Array.isArray(warnings) &&
        warnings.length > 0
    ) {
        article.appendChild(
            createWarningsList(
                warnings
            )
        );
    }

    return article;
}

/* ==========================================
   BADGES DE STATUS
========================================== */

function appendStatusBadge(
    container,
    label,
    status,
    positiveText,
    negativeText
) {
    const item =
        document.createElement(
            "div"
        );

    item.className =
        "verification-status";

    const labelElement =
        document.createElement(
            "span"
        );

    labelElement.className =
        "verification-status-label";

    labelElement.textContent =
        label;

    const badge =
        document.createElement(
            "span"
        );

    badge.classList.add(
        "status-badge"
    );

    if (status === true) {
        badge.classList.add(
            "status-positive"
        );

        badge.textContent =
            positiveText;
    } else if (
        status === false
    ) {
        badge.classList.add(
            "status-negative"
        );

        badge.textContent =
            negativeText;
    } else {
        badge.classList.add(
            "status-neutral"
        );

        badge.textContent =
            t().verifyIndeterminate;
    }

    item.appendChild(
        labelElement
    );

    item.appendChild(
        badge
    );

    container.appendChild(
        item
    );
}

function appendTrustBadge(
    container,
    signature
) {
    const status =
        getBooleanStatus(
            signature,
            [
                "cadeia_confiavel",
                "trusted"
            ]
        );

    appendStatusBadge(
        container,
        t().verifyTrust,
        status,
        t().verifyTrusted,
        t().verifyUntrusted
    );
}

function appendRevocationBadge(
    container,
    signature
) {
    const revoked =
        getBooleanStatus(
            signature,
            [
                "revogado",
                "revoked"
            ]
        );

    const revocationState =
        getFirstValue(
            signature,
            [
                "estado_revogacao",
                "revocation_state"
            ]
        );

    const item =
        document.createElement(
            "div"
        );

    item.className =
        "verification-status";

    const label =
        document.createElement(
            "span"
        );

    label.className =
        "verification-status-label";

    label.textContent =
        t().verifyRevocationStatus;

    const badge =
        document.createElement(
            "span"
        );

    badge.classList.add(
        "status-badge"
    );

    if (revoked === true) {
        badge.classList.add(
            "status-negative"
        );

        badge.textContent =
            t().verifyRevoked;
    } else if (
        revoked === false
    ) {
        badge.classList.add(
            "status-positive"
        );

        /*
         * Não afirmamos que o certificado
         * "não está revogado".
         *
         * Apenas informamos que nenhuma
         * revogação foi detectada nas
         * evidências consultadas.
         */
        badge.textContent =
            t().verifyNotRevoked;
    } else if (
        revocationState ===
        "nao_consultada"
    ) {
        badge.classList.add(
            "status-neutral"
        );

        badge.textContent =
            t().verifyNotChecked;
    } else if (
        revocationState ===
        "desabilitada"
    ) {
        badge.classList.add(
            "status-neutral"
        );

        badge.textContent =
            t().verifyDisabled;
    } else {
        badge.classList.add(
            "status-neutral"
        );

        badge.textContent =
            t().verifyIndeterminate;
    }

    item.appendChild(
        label
    );

    item.appendChild(
        badge
    );

    container.appendChild(
        item
    );
}

/* ==========================================
   DETALHES DA ASSINATURA
========================================== */

function appendDetail(
    container,
    label,
    value,
    monospace = false
) {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return;
    }

    const dt =
        document.createElement(
            "dt"
        );

    dt.textContent =
        label;

    const dd =
        document.createElement(
            "dd"
        );

    dd.textContent =
        String(value);

    if (monospace) {
        dd.classList.add(
            "monospace"
        );
    }

    container.appendChild(
        dt
    );

    container.appendChild(
        dd
    );
}

function getFirstValue(
    object,
    keys
) {
    if (
        !object ||
        typeof object !==
            "object"
    ) {
        return null;
    }

    for (const key of keys) {
        if (
            Object.prototype
                .hasOwnProperty
                .call(
                    object,
                    key
                )
        ) {
            const value =
                object[key];

            if (
                value !== null &&
                value !== undefined &&
                value !== ""
            ) {
                return value;
            }
        }
    }

    return null;
}

function getBooleanStatus(
    object,
    keys
) {
    const value =
        getFirstValue(
            object,
            keys
        );

    if (
        value === true ||
        value === false
    ) {
        return value;
    }

    if (
        typeof value ===
        "number"
    ) {
        if (value === 1) {
            return true;
        }

        if (value === 0) {
            return false;
        }
    }

    if (
        typeof value ===
        "string"
    ) {
        const normalized =
            value
                .trim()
                .toLowerCase();

        if (
            [
                "true",
                "yes",
                "sim",
                "valid",
                "válida",
                "valida",
                "trusted",
                "confiável",
                "confiavel",
                "intact"
            ].includes(
                normalized
            )
        ) {
            return true;
        }

        if (
            [
                "false",
                "no",
                "não",
                "nao",
                "invalid",
                "inválida",
                "invalida",
                "untrusted",
                "revoked"
            ].includes(
                normalized
            )
        ) {
            return false;
        }
    }

    return null;
}

/* ==========================================
   VALIDADE DO CERTIFICADO
========================================== */

function formatCertificateValidity(
    signature
) {
    const validity =
        getFirstValue(
            signature,
            [
                "validade_certificado",
                "certificate_validity"
            ]
        );

    if (
        typeof validity ===
        "string"
    ) {
        return validity;
    }

    if (
        validity &&
        typeof validity ===
            "object"
    ) {
        const from =
            validity.inicio ||
            validity.not_before ||
            validity.from;

        const until =
            validity.fim ||
            validity.not_after ||
            validity.until;

        if (from && until) {
            return `${from} → ${until}`;
        }

        return (
            from ||
            until ||
            null
        );
    }

    const from =
        getFirstValue(
            signature,
            [
                "valido_de",
                "not_before"
            ]
        );

    const until =
        getFirstValue(
            signature,
            [
                "valido_ate",
                "not_after"
            ]
        );

    if (from && until) {
        return `${from} → ${until}`;
    }

    return (
        from ||
        until ||
        null
    );
}

/* ==========================================
   CONFIANÇA
========================================== */

function formatTrust(signature) {
    const trusted =
        getBooleanStatus(
            signature,
            [
                "cadeia_confiavel",
                "trusted"
            ]
        );

    if (trusted === true) {
        return t().verifyTrusted;
    }

    if (trusted === false) {
        return t().verifyUntrusted;
    }

    return t().verifyIndeterminate;
}

/* ==========================================
   REVOGAÇÃO
========================================== */

function formatRevocation(
    signature
) {
    const revoked =
        getBooleanStatus(
            signature,
            [
                "revogado",
                "revoked"
            ]
        );

    if (revoked === true) {
        return t().verifyRevoked;
    }

    if (revoked === false) {
        return t().verifyNotRevoked;
    }

    const status =
        getFirstValue(
            signature,
            [
                "status_revogacao",
                "revocation_status"
            ]
        );

    if (status) {
        return status;
    }

    return t().verifyIndeterminate;
}

/* ==========================================
   COBERTURA DO PDF
========================================== */

function formatCoverage(
    signature
) {
    const coverage =
        getFirstValue(
            signature,
            [
                "cobertura",
                "coverage"
            ]
        );

    if (
        coverage === null ||
        coverage === undefined
    ) {
        return null;
    }

    if (
        typeof coverage ===
        "string"
    ) {
        return coverage;
    }

    if (
        typeof coverage ===
        "object"
    ) {
        return (
            coverage.descricao ||
            coverage.description ||
            coverage.status ||
            JSON.stringify(
                coverage
            )
        );
    }

    return String(
        coverage
    );
}

/* ==========================================
   ALTERAÇÕES POSTERIORES
========================================== */

function formatModification(
    signature
) {
    const modification =
        getFirstValue(
            signature,
            [
                "modificacoes",
                "alteracoes_posteriores",
                "modification_level"
            ]
        );

    if (
        modification === null ||
        modification === undefined
    ) {
        return null;
    }

    if (
        typeof modification ===
        "string"
    ) {
        return modification;
    }

    if (
        typeof modification ===
        "boolean"
    ) {
        if (modification) {
            return currentLanguage === "pt"
                ? "Foram detectadas alterações posteriores."
                : "Subsequent changes were detected.";
        }

        return currentLanguage === "pt"
            ? "Nenhuma alteração posterior detectada."
            : "No subsequent changes detected.";
    }

    if (
        typeof modification ===
        "object"
    ) {
        return (
            modification.descricao ||
            modification.description ||
            modification.status ||
            JSON.stringify(
                modification
            )
        );
    }

    return String(
        modification
    );
}

/* ==========================================
   CADEIA DE CERTIFICADOS
========================================== */

function createCertificateChain(
    chain
) {
    const section =
        document.createElement(
            "section"
        );

    section.className =
        "certificate-chain";

    const title =
        document.createElement(
            "h5"
        );

    title.textContent =
        t().verifyChain;

    section.appendChild(
        title
    );

    const list =
        document.createElement(
            "ol"
        );

    chain.forEach(
        (certificate) => {
            const item =
                document.createElement(
                    "li"
                );

            if (
                typeof certificate ===
                "string"
            ) {
                item.textContent =
                    certificate;
            } else if (
                certificate &&
                typeof certificate ===
                    "object"
            ) {
                const subject =
                    certificate.titular ||
                    certificate.subject ||
                    certificate.common_name ||
                    certificate.nome;

                const issuer =
                    certificate.emissor ||
                    certificate.issuer;

                if (
                    subject &&
                    issuer &&
                    subject !== issuer
                ) {
                    item.textContent =
                        `${subject} — ${issuer}`;
                } else {
                    item.textContent =
                        subject ||
                        issuer ||
                        certificate.serial ||
                        currentLanguage === "pt"
                            ? "Certificado"
                            : "Certificate";
                }
            }

            list.appendChild(
                item
            );
        }
    );

    section.appendChild(
        list
    );

    return section;
}

/* ==========================================
   AVISOS DO VERIFICADOR
========================================== */

function createWarningsList(
    warnings
) {
    const section =
        document.createElement(
            "section"
        );

    section.className =
        "verification-warnings";

    const title =
        document.createElement(
            "h5"
        );

    title.textContent =
        currentLanguage === "pt"
            ? "Observações técnicas"
            : "Technical observations";

    section.appendChild(
        title
    );

    const list =
        document.createElement(
            "ul"
        );

    warnings.forEach(
        (warning) => {
            const item =
                document.createElement(
                    "li"
                );

            item.textContent =
                typeof warning ===
                    "string"
                    ? warning
                    : String(
                        warning?.mensagem ||
                        warning?.message ||
                        warning
                    );

            list.appendChild(
                item
            );
        }
    );

    section.appendChild(
        list
    );

    return section;
}

/* ==========================================
   AVISO JURÍDICO/TÉCNICO
========================================== */

function appendVerificationDisclaimer(
    container,
    data
) {
    const disclaimer =
        document.createElement(
            "div"
        );

    disclaimer.className =
        "verification-disclaimer";

    disclaimer.setAttribute(
        "role",
        "note"
    );

    /*
     * O backend pode fornecer um aviso
     * mais específico. Caso contrário,
     * usamos o texto padrão da interface.
     */
    const backendNotice =
        getFirstValue(
            data,
            [
                "aviso",
                "disclaimer",
                "aviso_legal"
            ]
        );

    disclaimer.textContent =
        backendNotice ||
        t().verifyDisclaimer;

    container.appendChild(
        disclaimer
    );
}

/* ==========================================
   REDIMENSIONAMENTO
========================================== */

function handleWindowResize() {
    if (!pdfJsDoc && !verificationPdfDoc) {
        return;
    }

    window.clearTimeout(
        resizeTimer
    );

    resizeTimer =
        window.setTimeout(
            async () => {
                try {
                    if (currentMode === "sign" && pdfJsDoc) {
                        await renderPage(currentPageNum, signaturePos.placed);
                    } else if (currentMode === "verify" && verificationPdfDoc) {
                        await renderVerificationPreview();
                    }
                } catch (error) {
                    console.error(
                        "Erro ao redimensionar PDF:",
                        error
                    );
                }
            },
            200
        );
}

/* ==========================================
   EVENTOS DA INTERFACE
========================================== */

function bindEvents() {
    const themeButton =
        document.getElementById(
            "theme-button"
        );

    const languageButton =
        document.getElementById(
            "language-button"
        );

    const signModeButton =
        document.getElementById(
            "mode-sign-button"
        );

    const verifyModeButton =
        document.getElementById(
            "mode-verify-button"
        );

    const pdfInput =
        document.getElementById(
            "pdf-input"
        );

    const previousButton =
        document.getElementById(
            "prev-page"
        );

    const nextButton =
        document.getElementById(
            "next-page"
        );

    const pdfStage =
        document.getElementById(
            "pdf-stage"
        );

    const canvasContainer =
        document.getElementById(
            "canvas-container"
        );

    const cancelButton =
        document.getElementById(
            "cancel-button"
        );

    const confirmButton =
        document.getElementById(
            "confirm-position-button"
        );

    const backTypeButton =
        document.getElementById(
            "back-type-button"
        );

    const backConfigButton =
        document.getElementById(
            "back-config-button"
        );

    const customTitle =
        document.getElementById(
            "custom-title"
        );

    const showDate =
        document.getElementById(
            "show-date"
        );

    const showTime =
        document.getElementById(
            "show-time"
        );

    const showType =
        document.getElementById(
            "show-type"
        );

    const imageInput =
        document.getElementById(
            "signature-image-input"
        );

    const imageMode =
        document.getElementById(
            "image-mode"
        );

    const signButton =
        document.getElementById(
            "sign-button"
        );

    const restartButton =
        document.getElementById(
            "restart-button"
        );

    const verifyInput =
        document.getElementById(
            "verify-pdf-input"
        );

    const verifyButton =
        document.getElementById(
            "verify-button"
        );

    const verifyPreviousButton = document.getElementById("verify-prev-page");
    const verifyNextButton = document.getElementById("verify-next-page");

    themeButton?.addEventListener(
        "click",
        toggleTheme
    );

    languageButton?.addEventListener(
        "click",
        toggleLanguage
    );

    signModeButton?.addEventListener(
        "click",
        () => {
            setApplicationMode(
                "sign"
            );
        }
    );

    verifyModeButton?.addEventListener(
        "click",
        () => {
            setApplicationMode(
                "verify"
            );
        }
    );

    pdfInput?.addEventListener(
        "change",
        handleFileUpload
    );

    previousButton?.addEventListener(
        "click",
        () => {
            changePage(-1);
        }
    );

    nextButton?.addEventListener(
        "click",
        () => {
            changePage(1);
        }
    );

    pdfStage?.addEventListener(
        "click",
        placeSignature
    );

    pdfStage?.addEventListener(
        "keydown",
        handlePdfStageKeydown
    );

    canvasContainer?.addEventListener(
        "scroll",
        handlePdfScroll,
        {
            passive: true
        }
    );

    cancelButton?.addEventListener(
        "click",
        resetSigningFlow
    );

    confirmButton?.addEventListener(
        "click",
        confirmPosition
    );

    backTypeButton?.addEventListener(
        "click",
        () => {
            goToStep(2);
        }
    );

    backConfigButton?.addEventListener(
        "click",
        () => {
            goToStep(3);
        }
    );

    document
        .querySelectorAll(
            "[data-signature-type]"
        )
        .forEach(
            (element) => {
                element.addEventListener(
                    "click",
                    () => {
                        selectSignatureType(
                            element.dataset
                                .signatureType
                        );
                    }
                );
            }
        );

    customTitle?.addEventListener(
        "input",
        updateSignaturePreview
    );

    showDate?.addEventListener(
        "change",
        updateSignaturePreview
    );

    showTime?.addEventListener(
        "change",
        updateSignaturePreview
    );

    showType?.addEventListener(
        "change",
        updateSignaturePreview
    );

    imageInput?.addEventListener(
        "change",
        changeSignatureImage
    );

    imageMode?.addEventListener(
        "change",
        updateImageMode
    );

    signButton?.addEventListener(
        "click",
        signWithBackend
    );

    restartButton?.addEventListener(
        "click",
        resetSigningFlow
    );

    verifyInput?.addEventListener(
        "change",
        handleVerificationFile
    );

    verifyButton?.addEventListener(
        "click",
        verifyWithBackend
    );

    canvasContainer?.addEventListener("wheel", handlePdfWheel, {
        passive: false
    });
    canvasContainer?.addEventListener("keydown", handlePdfPreviewKeydown);

    verifyPreviousButton?.addEventListener(
        "click",
        () => changeVerificationPage(-1)
    );

    verifyNextButton?.addEventListener(
        "click",
        () => changeVerificationPage(1)
    );

    const verifyCanvasContainer = document.getElementById("verify-canvas-container");
    verifyCanvasContainer?.addEventListener("scroll", handleVerificationScroll, {
        passive: true
    });
    verifyCanvasContainer?.addEventListener("wheel", handleVerificationWheel, {
        passive: false
    });
    verifyCanvasContainer?.addEventListener("keydown", handleVerificationPreviewKeydown);

    window.addEventListener(
        "resize",
        handleWindowResize
    );

    window.addEventListener(
        "beforeunload",
        clearSensitiveFields
    );
}

/* ==========================================
   TEMA DO SISTEMA
========================================== */

function bindSystemThemeListener() {
    const mediaQuery =
        window.matchMedia(
            "(prefers-color-scheme: dark)"
        );

    const listener =
        (event) => {
            /*
             * Se o usuário escolheu manualmente
             * um tema, não sobrescrevemos
             * essa preferência.
             */
            if (
                getStoredPreference(
                    "theme"
                )
            ) {
                return;
            }

            applyTheme(
                event.matches
                    ? "dark"
                    : "light"
            );
        };

    if (
        typeof mediaQuery
            .addEventListener ===
        "function"
    ) {
        mediaQuery.addEventListener(
            "change",
            listener
        );
    } else if (
        typeof mediaQuery
            .addListener ===
        "function"
    ) {
        mediaQuery.addListener(
            listener
        );
    }
}

/* ==========================================
   CONFIGURAÇÕES INICIAIS DOS CONTROLES
========================================== */

function initializeControls() {
    const showDate =
        document.getElementById(
            "show-date"
        );

    const showTime =
        document.getElementById(
            "show-time"
        );

    const showType =
        document.getElementById(
            "show-type"
        );

    const imageMode =
        document.getElementById(
            "image-mode"
        );

    const revocation =
        document.getElementById(
            "verify-revocation"
        );

    const pdfStage =
        document.getElementById(
            "pdf-stage"
        );

    if (showDate) {
        showDate.checked =
            true;
    }

    /*
     * Hora é opcional e permanece
     * desmarcada por padrão.
     */
    if (showTime) {
        showTime.checked =
            false;
    }

    if (showType) {
        showType.checked =
            true;
    }

    if (imageMode) {
        imageMode.value =
            "auto";
    }

    /* A verificação online de revogação é habilitada por padrão. */
    if (revocation) {
        revocation.checked =
            true;
    }

    /*
     * Torna a área do PDF operável
     * por teclado.
     */
    if (pdfStage) {
        if (
            !pdfStage.hasAttribute(
                "tabindex"
            )
        ) {
            pdfStage.tabIndex =
                0;
        }

        if (
            !pdfStage.hasAttribute(
                "role"
            )
        ) {
            pdfStage.setAttribute(
                "role",
                "button"
            );
        }
    }
}

/* ==========================================
   INICIALIZAÇÃO
========================================== */

function initializeApplication() {
    initializeTheme();

    initializeControls();

    bindEvents();

    bindSystemThemeListener();

    applyTranslations();

    configureSignatureStep();

    updateSignaturePreview();

    updatePagination();

    setApplicationMode(
        "sign"
    );

    /*
     * O health check é iniciado assim que
     * a interface fica pronta. Assim, em
     * hospedagens como Render, o backend
     * pode começar a despertar enquanto
     * o usuário escolhe e posiciona o PDF.
     */
    wakeBackend();
}

/* ==========================================
   INÍCIO
========================================== */

if (
    document.readyState ===
    "loading"
) {
    document.addEventListener(
        "DOMContentLoaded",
        initializeApplication,
        {
            once: true
        }
    );
} else {
    initializeApplication();
}

function normalizeVerificationSignature(signature) {
    const certificate = signature?.certificado || {};
    const revocation = signature?.revogacao || {};
    const infrastructure = certificate?.infraestrutura;

    return {
        ...certificate,
        ...signature,
        titular: certificate.titular,
        emissor: certificate.emissor,
        infraestrutura:
            typeof infrastructure === "object"
                ? infrastructure.nome
                : infrastructure,
        integridade: signature?.integridade_criptografica,
        assinatura_valida:
            signature?.assinatura_criptograficamente_valida,
        revogado: revocation?.revogado,
        estado_revogacao: revocation?.estado,
        status_revogacao:
            formatRevocationEvidence(revocation),
        cadeia: signature?.cadeia_validacao,
        mecanismo:
            signature?.mecanismo_assinatura,
        modificacoes:
            signature?.nivel_modificacao,
        data_assinatura:
            signature?.data_hora_declarada
    };
}

function formatRevocationEvidence(revocation) {
    if (!revocation || typeof revocation !== "object") {
        return null;
    }

    const conclusion = revocation.conclusao || revocation.estado || "";
    const ocspCount = Number(revocation.respostas_ocsp_obtidas || 0);
    const crlCount = Number(revocation.listas_crl_obtidas || 0);

    if (!revocation.consultas_online_habilitadas) {
        return currentLanguage === "pt"
            ? `${conclusion} Consultas online desabilitadas.`.trim()
            : `${conclusion} Online checks disabled.`.trim();
    }

    if (revocation.consulta_realizada) {
        const evidence = currentLanguage === "pt"
            ? `Evidências obtidas: ${ocspCount} OCSP, ${crlCount} CRL.`
            : `Evidence obtained: ${ocspCount} OCSP, ${crlCount} CRL.`;
        return `${conclusion} ${evidence}`.trim();
    }

    return currentLanguage === "pt"
        ? `${conclusion} Nenhuma resposta OCSP ou CRL foi obtida.`.trim()
        : `${conclusion} No OCSP response or CRL was obtained.`.trim();
}
