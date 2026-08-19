"use strict";

pdfjsLib.GlobalWorkerOptions.workerSrc =
    "./vendor/pdfjs/pdf.worker.min.js";

/*
 * Substitua pela URL real do backend no Render
 * antes da publicação.
 */
const API_BASE_URL =
    window.location.hostname.includes("github.io")
        ? "https://document-signer-u7ie.onrender.com"
        : "http://127.0.0.1:5000";

const STAMP_WIDTH = 240;
const STAMP_HEIGHT = 68;

const FULL_SIGNATURE_RATIO = 2.2;

const MAX_PDF_SIZE =
    25 * 1024 * 1024;

const MAX_IMAGE_SIZE =
    2 * 1024 * 1024;

const REQUEST_TIMEOUT =
    120000;

const BACKEND_STATUS_TIMEOUT =
    90000;

const BACKEND_STATUS_RETRY_INTERVAL =
    5000;

/* ==========================================
   ESTADO DA APLICAÇÃO
========================================== */

let currentFile = null;
let pdfJsDoc = null;

let currentPageNum = 1;
let totalPages = 1;

let currentRenderScale = 1;

let currentSignatureType =
    "standard";

let customImageFile = null;
let customImageUrl = null;

let imageNaturalWidth = 0;
let imageNaturalHeight = 0;

let detectedImageMode =
    "default";

let currentDownloadUrl = null;

let resizeTimer = null;
let scrollPageLock = false;
let renderToken = 0;

let signaturePos = {
    placed: false,
    x: 0,
    y: 0,
    canvasRectWidth: 0,
    canvasRectHeight: 0,
    page: 1
};

let backendReady = false;
let backendWakePromise = null;
let backendWakeController = null;

/* ==========================================
   TRADUÇÕES
========================================== */

const translations = {
    pt: {
        htmlLang: "pt-BR",

        title:
            "Assinador Digital",

        skipLink:
            "Pular para o conteúdo principal",

        preferences:
            "Preferências da página",

        theme:
            "Alternar tema",

        languageButton:
            "EN",

        languageAria:
            "Mudar idioma para inglês",

        steps: [
            "Etapa 1 de 5: Envio do documento",
            "Etapa 2 de 5: Posicionamento",
            "Etapa 3 de 5: Tipo de assinatura",
            "Etapa 4 de 5: Configuração",
            "Etapa 5 de 5: Concluído"
        ],

        step1Title:
            "Envio do documento",

        uploadTitle:
            "Clique para selecionar o documento",

        uploadDescription:
            "ou escolha um arquivo PDF",

        pdfHelp:
            "Apenas arquivos PDF.",

        step2Title:
            "Posicionamento da assinatura",

        positionDescription:
            "Clique na página onde deseja posicionar a assinatura. Ao chegar ao final da página, a próxima página será exibida automaticamente.",

        previousPage:
            "Página anterior",

        nextPage:
            "Próxima página",

        pagination:
            "Navegação entre páginas",

        pdfPreview:
            "Pré-visualização do documento PDF",

        pdfPage:
            "Página do documento. Clique para posicionar a assinatura.",

        page:
            "Página {current} de {total}",

        cancel:
            "Cancelar",

        confirmPosition:
            "Confirmar posição",

        signatureTypeTitle:
            "Qual tipo de assinatura deseja utilizar?",

        signatureTypeDescription:
            "Escolha apenas a aparência visual. Todas as opções continuam utilizando o certificado digital.",

        standard:
            "Padrão",

        standardDescription:
            "Usa a identidade visual padrão do assinador com nome, data e informação PAdES.",

        simple:
            "Customizada simples",

        simpleDescription:
            "Permite personalizar o texto e escolher as informações mostradas.",

        image:
            "Customizada com imagem",

        imageDescription:
            "Permite usar logotipo ou uma imagem completa de assinatura.",

        back:
            "Voltar",

        configureTitle:
            "Configurar assinatura",

        configureDescription:
            "Configure a aparência e informe seu certificado digital.",

        simpleOptions:
            "Aparência personalizada",

        customTitle:
            "Texto superior:",

        imageOptions:
            "Imagem personalizada",

        imageLabel:
            "Imagem:",

        imageHelp:
            "PNG ou JPEG, até 2 MB.",

        imageMode:
            "Tratamento da imagem:",

        auto:
            "Detectar automaticamente",

        full:
            "Assinatura completa",

        logo:
            "Logotipo / imagem lateral",

        visibleData:
            "Informações exibidas",

        showDate:
            "Mostrar data",

        showTime:
            "Mostrar hora",

        showType:
            "Mostrar “Assinatura digital PAdES”",

        certificate:
            "Certificado (.p12 / .pfx):",

        certificateHelp:
            "O certificado é utilizado para criar a assinatura digital do PDF.",

        password:
            "Senha do certificado:",

        sign:
            "Assinar documento",

        successTitle:
            "Documento assinado!",

        successDescription:
            "A assinatura digital PAdES foi aplicada com sucesso.",

        download:
            "Baixar documento assinado",

        restart:
            "Assinar outro documento",

        signedBy:
            "Assinado digitalmente por",

        signer:
            "Nome do titular",

        date:
            "Data da assinatura",

        time:
            "Hora da assinatura",

        pades:
            "Assinatura digital PAdES",

        invalidPdf:
            "Selecione um arquivo PDF válido.",

        pdfTooLarge:
            "O PDF deve ter no máximo 25 MB.",

        pdfError:
            "Não foi possível abrir o PDF.",

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

        processing:
            "Processando...",

        success:
            "Documento assinado com sucesso. O download está disponível.",

        requestTimeout:
            "A operação excedeu o tempo limite. Tente novamente.",

        connectionError:
            "Não foi possível comunicar com o servidor.",

        httpError:
            "Erro HTTP {status}.",

        signedFilenameSuffix:
            "_assinado",

        backendStarting:
            "Preparando serviço de assinatura...",

        backendOnline:
            "Serviço de assinatura disponível",

        backendOffline:
            "Serviço de assinatura indisponível",

        backendWaking:
            "Iniciando serviço de assinatura...",

        backendSlow:
            "O serviço está iniciando. Isso pode levar alguns segundos."
    },

    en: {
        htmlLang: "en",

        title:
            "Digital Signer",

        skipLink:
            "Skip to main content",

        preferences:
            "Page preferences",

        theme:
            "Toggle theme",

        languageButton:
            "PT",

        languageAria:
            "Change language to Portuguese",

        steps: [
            "Step 1 of 5: Document upload",
            "Step 2 of 5: Placement",
            "Step 3 of 5: Signature type",
            "Step 4 of 5: Configuration",
            "Step 5 of 5: Completed"
        ],

        step1Title:
            "Document upload",

        uploadTitle:
            "Click to select the document",

        uploadDescription:
            "or choose a PDF file",

        pdfHelp:
            "PDF files only.",

        step2Title:
            "Signature placement",

        positionDescription:
            "Click on the page where you want to place the signature. When you reach the bottom of the page, the next page will be displayed automatically.",

        previousPage:
            "Previous page",

        nextPage:
            "Next page",

        pagination:
            "Page navigation",

        pdfPreview:
            "PDF document preview",

        pdfPage:
            "Document page. Click to position the signature.",

        page:
            "Page {current} of {total}",

        cancel:
            "Cancel",

        confirmPosition:
            "Confirm position",

        signatureTypeTitle:
            "Which signature type would you like to use?",

        signatureTypeDescription:
            "Choose only the visual appearance. All options continue to use the digital certificate.",

        standard:
            "Standard",

        standardDescription:
            "Uses the signer's standard visual identity with name, date and PAdES information.",

        simple:
            "Simple custom",

        simpleDescription:
            "Allows you to customize the text and choose which information is displayed.",

        image:
            "Custom with image",

        imageDescription:
            "Allows you to use a logo or a complete signature image.",

        back:
            "Back",

        configureTitle:
            "Configure signature",

        configureDescription:
            "Configure the appearance and provide your digital certificate.",

        simpleOptions:
            "Custom appearance",

        customTitle:
            "Top text:",

        imageOptions:
            "Custom image",

        imageLabel:
            "Image:",

        imageHelp:
            "PNG or JPEG, up to 2 MB.",

        imageMode:
            "Image treatment:",

        auto:
            "Detect automatically",

        full:
            "Complete signature",

        logo:
            "Logo / side image",

        visibleData:
            "Displayed information",

        showDate:
            "Show date",

        showTime:
            "Show time",

        showType:
            "Show “PAdES digital signature”",

        certificate:
            "Certificate (.p12 / .pfx):",

        certificateHelp:
            "The certificate is used to create the PDF digital signature.",

        password:
            "Certificate password:",

        sign:
            "Sign document",

        successTitle:
            "Document signed!",

        successDescription:
            "The PAdES digital signature was successfully applied.",

        download:
            "Download signed document",

        restart:
            "Sign another document",

        signedBy:
            "Digitally signed by",

        signer:
            "Certificate holder",

        date:
            "Signature date",

        time:
            "Signature time",

        pades:
            "PAdES digital signature",

        invalidPdf:
            "Select a valid PDF file.",

        pdfTooLarge:
            "The PDF must be no larger than 25 MB.",

        pdfError:
            "Unable to open the PDF.",

        positionRequired:
            "Click on the document to position the signature.",

        positionSet:
            "Signature positioned on page {page}.",

        certificateRequired:
            "Select the certificate and enter its password.",

        pdfRequired:
            "No PDF document has been selected.",

        imageRequired:
            "Select an image for this option.",

        invalidImage:
            "Use a PNG or JPEG image only.",

        imageTooLarge:
            "The image must be no larger than 2 MB.",

        imageLoadError:
            "Unable to open the selected image.",

        fullDetected:
            "Detected as complete signature",

        logoDetected:
            "Detected as logo/side image",

        processing:
            "Processing...",

        success:
            "Document signed successfully. The download is available.",

        requestTimeout:
            "The operation timed out. Please try again.",

        connectionError:
            "Unable to communicate with the server.",

        httpError:
            "HTTP error {status}.",

        signedFilenameSuffix:
            "_signed",

        backendStarting:
            "Preparing signing service...",

        backendOnline:
            "Signing service available",

        backendOffline:
            "Signing service unavailable",

        backendWaking:
            "Starting signing service...",

        backendSlow:
            "The service is starting. This may take a few seconds."
    }
};


/* ==========================================
   IDIOMA PADRÃO DO SISTEMA
========================================== */

const savedLanguage =
    localStorage.getItem(
        "language"
    );

let currentLanguage =
    savedLanguage === "pt" ||
        savedLanguage === "en"
        ? savedLanguage
        : navigator.language
            .toLowerCase()
            .startsWith("pt")
            ? "pt"
            : "en";


/* ==========================================
   TEMA PADRÃO DO SISTEMA
========================================== */

let manualTheme =
    localStorage.getItem(
        "theme"
    );

function t() {
    return translations[
        currentLanguage
    ];
}

function systemPrefersDark() {
    return (
        window.matchMedia &&
        window
            .matchMedia(
                "(prefers-color-scheme: dark)"
            )
            .matches
    );
}

function applyTheme(theme) {
    const dark =
        theme === "dark";

    document.documentElement
        .classList
        .toggle(
            "dark-theme",
            dark
        );

    const button =
        document.getElementById(
            "theme-button"
        );

    if (button) {
        button.setAttribute(
            "aria-pressed",
            String(dark)
        );
    }
}

function initializeTheme() {
    if (
        manualTheme === "dark" ||
        manualTheme === "light"
    ) {
        applyTheme(
            manualTheme
        );

        return;
    }

    applyTheme(
        systemPrefersDark()
            ? "dark"
            : "light"
    );
}

function toggleTheme() {
    const isDark =
        document.documentElement
            .classList
            .contains(
                "dark-theme"
            );

    manualTheme =
        isDark
            ? "light"
            : "dark";

    localStorage.setItem(
        "theme",
        manualTheme
    );

    applyTheme(
        manualTheme
    );
}


/* ==========================================
   TOGGLE DE IDIOMA
========================================== */

function toggleLanguage() {
    const previousLanguage =
        currentLanguage;

    const previousDefaultTitle =
        translations[
            previousLanguage
        ].signedBy;

    currentLanguage =
        previousLanguage === "pt"
            ? "en"
            : "pt";

    localStorage.setItem(
        "language",
        currentLanguage
    );

    /*
     * Se o usuário ainda não personalizou
     * o título, traduzimos também o valor
     * padrão do input.
     */
    const customTitleInput =
        document.getElementById(
            "customTitle"
        );

    if (
        customTitleInput &&
        (
            !customTitleInput.value.trim() ||
            customTitleInput.value.trim() ===
            previousDefaultTitle
        )
    ) {
        customTitleInput.value =
            t().signedBy;
    }

    applyTranslations();
}

function setText(id, value) {
    const element =
        document.getElementById(
            id
        );

    if (
        element &&
        typeof value === "string"
    ) {
        element.textContent =
            value;
    }
}

function setAriaLabel(
    id,
    value
) {
    const element =
        document.getElementById(
            id
        );

    if (
        element &&
        typeof value === "string"
    ) {
        element.setAttribute(
            "aria-label",
            value
        );
    }
}

function applyTranslations() {
    const language =
        t();

    document.documentElement.lang =
        language.htmlLang;

    document.title =
        language.title;

    setText(
        "title",
        language.title
    );

    setText(
        "skip-link",
        language.skipLink
    );

    setAriaLabel(
        "top-controls",
        language.preferences
    );

    setText(
        "theme-text",
        language.theme
    );

    setAriaLabel(
        "theme-button",
        language.theme
    );

    setText(
        "language-label",
        language.languageButton
    );

    setAriaLabel(
        "language-button",
        language.languageAria
    );

    setText(
        "step-1-title",
        language.step1Title
    );

    setText(
        "upload-title",
        language.uploadTitle
    );

    setText(
        "upload-description",
        language.uploadDescription
    );

    setText(
        "pdf-help",
        language.pdfHelp
    );

    setText(
        "step-2-title",
        language.step2Title
    );

    setText(
        "position-description",
        language.positionDescription
    );

    setText(
        "cancel-button",
        language.cancel
    );

    setText(
        "confirm-position-button",
        language.confirmPosition
    );

    setText(
        "step-3-title",
        language.signatureTypeTitle
    );

    setText(
        "signature-type-description",
        language.signatureTypeDescription
    );

    setText(
        "type-standard-title",
        language.standard
    );

    setText(
        "type-standard-description",
        language.standardDescription
    );

    setText(
        "type-simple-title",
        language.simple
    );

    setText(
        "type-simple-description",
        language.simpleDescription
    );

    setText(
        "type-image-title",
        language.image
    );

    setText(
        "type-image-description",
        language.imageDescription
    );

    setText(
        "back-type-button",
        language.back
    );

    setText(
        "step-4-title",
        language.configureTitle
    );

    setText(
        "step-4-description",
        language.configureDescription
    );

    setText(
        "simple-options-title",
        language.simpleOptions
    );

    setText(
        "custom-title-label",
        language.customTitle
    );

    setText(
        "image-options-title",
        language.imageOptions
    );

    setText(
        "image-label",
        language.imageLabel
    );

    setText(
        "image-help",
        language.imageHelp
    );

    setText(
        "image-mode-label",
        language.imageMode
    );

    setText(
        "image-mode-auto",
        language.auto
    );

    setText(
        "image-mode-full",
        language.full
    );

    setText(
        "image-mode-logo",
        language.logo
    );

    setText(
        "visible-data-title",
        language.visibleData
    );

    setText(
        "show-date-label",
        language.showDate
    );

    setText(
        "show-time-label",
        language.showTime
    );

    setText(
        "show-type-label",
        language.showType
    );

    setText(
        "certificate-label",
        language.certificate
    );

    setText(
        "certificate-help",
        language.certificateHelp
    );

    setText(
        "password-label",
        language.password
    );

    setText(
        "back-config-button",
        language.back
    );

    setText(
        "sign-button",
        language.sign
    );

    setText(
        "step-5-title",
        language.successTitle
    );

    setText(
        "success-description",
        language.successDescription
    );

    setText(
        "download-button",
        language.download
    );

    setText(
        "restart-button",
        language.restart
    );

    setAriaLabel(
        "prev-page",
        language.previousPage
    );

    setAriaLabel(
        "next-page",
        language.nextPage
    );

    setAriaLabel(
        "pagination",
        language.pagination
    );

    setAriaLabel(
        "canvas-container",
        language.pdfPreview
    );

    setAriaLabel(
        "pdf-stage",
        language.pdfPage
    );

    if (backendReady) {
        updateBackendStatus(
            "online"
        );
    } else {
        updateBackendStatus(
            "starting"
        );
    }

    updateStepSubtitle();
    updatePagination();
    updateImageInfo();
    updateSignaturePreview();
}


/* ==========================================
   ACESSIBILIDADE
========================================== */

function announce(message) {
    if (!message) {
        return;
    }

    const element =
        document.getElementById(
            "screen-reader-announcer"
        );

    if (!element) {
        return;
    }

    element.textContent = "";

    requestAnimationFrame(
        () => {
            element.textContent =
                message;
        }
    );
}

function announceError(message) {
    if (!message) {
        return;
    }

    const element =
        document.getElementById(
            "screen-reader-alert"
        );

    if (!element) {
        return;
    }

    element.textContent = "";

    requestAnimationFrame(
        () => {
            element.textContent =
                message;
        }
    );
}


/* ==========================================
   ETAPAS
========================================== */

function getCurrentStep() {
    const active =
        document.querySelector(
            ".step.active"
        );

    if (!active) {
        return 1;
    }

    const match =
        active.id.match(
            /^step-(\d+)$/
        );

    return match
        ? Number(match[1])
        : 1;
}

function updateStepSubtitle() {
    const subtitle =
        document.getElementById(
            "subtitle"
        );

    if (!subtitle) {
        return;
    }

    const step =
        getCurrentStep();

    subtitle.textContent =
        t().steps[
        step - 1
        ];
}

function goToStep(step) {
    document
        .querySelectorAll(
            ".step"
        )
        .forEach(
            element => {
                element
                    .classList
                    .remove(
                        "active"
                    );
            }
        );

    const target =
        document.getElementById(
            `step-${step}`
        );

    if (!target) {
        return;
    }

    target.classList.add(
        "active"
    );

    updateStepSubtitle();

    announce(
        t().steps[
        step - 1
        ]
    );

    const heading =
        target.querySelector(
            "h2"
        );

    if (heading) {
        heading.setAttribute(
            "tabindex",
            "-1"
        );

        heading.focus({
            preventScroll: true
        });
    }

    target.scrollIntoView({
        block: "start",
        behavior: "auto"
    });
}


/* ==========================================
   UPLOAD DO PDF
========================================== */

async function handleFileUpload(
    event
) {
    const file =
        event.target.files[0];

    if (!file) {
        return;
    }

    hidePdfError();

    if (
        file.size >
        MAX_PDF_SIZE
    ) {
        event.target.value = "";

        showPdfError(
            t().pdfTooLarge
        );

        return;
    }

    const filename =
        file.name.toLowerCase();

    const isPdf =
        file.type ===
        "application/pdf" ||
        filename.endsWith(
            ".pdf"
        );

    if (!isPdf) {
        event.target.value = "";

        showPdfError(
            t().invalidPdf
        );

        return;
    }

    try {
        const buffer =
            await file.arrayBuffer();

        const bytes =
            new Uint8Array(
                buffer
            );

        /*
         * Verificação simples adicional.
         * O backend continuará fazendo
         * a validação definitiva.
         */
        const headerLength =
            Math.min(
                1024,
                bytes.length
            );

        let header = "";

        for (
            let i = 0;
            i < headerLength;
            i++
        ) {
            header +=
                String.fromCharCode(
                    bytes[i]
                );
        }

        if (
            bytes.length < 5 ||
            !header.includes(
                "%PDF"
            )
        ) {
            throw new Error(
                t().invalidPdf
            );
        }

        const loadingTask =
            pdfjsLib.getDocument({
                data: bytes
            });

        pdfJsDoc =
            await loadingTask.promise;

        currentFile =
            file;

        totalPages =
            pdfJsDoc.numPages;

        currentPageNum =
            1;

        goToStep(2);

        await renderPage(
            1,
            true
        );

    } catch (error) {
        console.error(
            "Falha ao carregar PDF:",
            error
        );

        currentFile =
            null;

        pdfJsDoc =
            null;

        event.target.value = "";

        showPdfError(
            error?.message ||
            t().pdfError
        );
    }
}

function showPdfError(message) {
    const error =
        document.getElementById(
            "error-pdf"
        );

    if (!error) {
        return;
    }

    error.textContent =
        message;

    error.style.display =
        "block";

    announceError(
        message
    );
}

function hidePdfError() {
    const error =
        document.getElementById(
            "error-pdf"
        );

    if (!error) {
        return;
    }

    error.textContent = "";

    error.style.display =
        "none";
}


/* ==========================================
   RENDERIZAÇÃO DO PDF
========================================== */

async function renderPage(
    pageNumber,
    resetScroll = true
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

    const availableWidth =
        Math.max(
            container.clientWidth -
            20,
            100
        );

    let scale =
        availableWidth /
        originalViewport.width;

    scale =
        Math.max(
            0.1,
            Math.min(
                scale,
                1.5
            )
        );

    currentRenderScale =
        scale;

    const viewport =
        page.getViewport({
            scale
        });

    canvas.width =
        Math.round(
            viewport.width
        );

    canvas.height =
        Math.round(
            viewport.height
        );

    canvas.style.width =
        `${Math.round(
            viewport.width
        )}px`;

    canvas.style.height =
        `${Math.round(
            viewport.height
        )}px`;

    stage.style.width =
        canvas.style.width;

    stage.style.height =
        canvas.style.height;

    context.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    await page.render({
        canvasContext:
            context,
        viewport
    }).promise;

    if (
        token !== renderToken
    ) {
        return;
    }

    resetSignaturePosition();

    if (resetScroll) {
        container.scrollTop =
            0;

        container.scrollLeft =
            0;
    }

    scrollPageLock =
        false;

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
}


/* ==========================================
   PAGINAÇÃO
========================================== */

function updatePagination() {
    if (!pdfJsDoc) {
        return;
    }

    const indicator =
        document.getElementById(
            "page-indicator"
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

    const previous =
        document.getElementById(
            "prev-page"
        );

    const next =
        document.getElementById(
            "next-page"
        );

    if (previous) {
        previous.disabled =
            currentPageNum <= 1;
    }

    if (next) {
        next.disabled =
            currentPageNum >=
            totalPages;
    }
}

async function changePage(
    offset
) {
    if (
        !pdfJsDoc ||
        scrollPageLock
    ) {
        return;
    }

    const newPage =
        currentPageNum +
        offset;

    if (
        newPage < 1 ||
        newPage > totalPages
    ) {
        return;
    }

    scrollPageLock =
        true;

    try {
        await renderPage(
            newPage,
            true
        );
    } finally {
        scrollPageLock =
            false;
    }
}


/* ==========================================
   POSICIONAMENTO DA ASSINATURA
========================================== */

function placeSignature(
    event
) {
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
        !box ||
        !pdfJsDoc
    ) {
        return;
    }

    const rect =
        stage.getBoundingClientRect();

    const width =
        STAMP_WIDTH *
        currentRenderScale;

    const height =
        STAMP_HEIGHT *
        currentRenderScale;

    const clickX =
        event.clientX -
        rect.left;

    const clickY =
        event.clientY -
        rect.top;

    if (
        clickX < 0 ||
        clickX > rect.width ||
        clickY < 0 ||
        clickY > rect.height
    ) {
        return;
    }

    let left =
        clickX -
        width / 2;

    let top =
        clickY -
        height / 2;

    left =
        Math.max(
            0,
            Math.min(
                left,
                Math.max(
                    0,
                    rect.width -
                    width
                )
            )
        );

    top =
        Math.max(
            0,
            Math.min(
                top,
                Math.max(
                    0,
                    rect.height -
                    height
                )
            )
        );

    box.style.width =
        `${Math.min(
            width,
            rect.width
        )}px`;

    box.style.height =
        `${Math.min(
            height,
            rect.height
        )}px`;

    box.style.left =
        `${left}px`;

    box.style.top =
        `${top}px`;

    box.style.display =
        "block";

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
        announceError(
            t().positionRequired
        );

        return;
    }

    goToStep(3);
}


/* ==========================================
   TIPO DE ASSINATURA
========================================== */

function selectSignatureType(
    type
) {
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

    const simpleOptions =
        document.getElementById(
            "simple-options"
        );

    const imageOptions =
        document.getElementById(
            "image-options"
        );

    if (simpleOptions) {
        simpleOptions
            .classList
            .toggle(
                "hidden",
                type === "standard"
            );
    }

    if (imageOptions) {
        imageOptions
            .classList
            .toggle(
                "hidden",
                type !== "image"
            );
    }

    updateSignaturePreview();

    goToStep(4);
}


/* ==========================================
   IMAGEM PERSONALIZADA
========================================== */

function handleSignatureImage(
    event
) {
    const file =
        event.target.files[0];

    if (!file) {
        removeSignatureImage();

        return;
    }

    if (
        ![
            "image/png",
            "image/jpeg"
        ].includes(
            file.type
        )
    ) {
        event.target.value = "";

        announceError(
            t().invalidImage
        );

        return;
    }

    if (
        file.size >
        MAX_IMAGE_SIZE
    ) {
        event.target.value = "";

        announceError(
            t().imageTooLarge
        );

        return;
    }

    if (customImageUrl) {
        URL.revokeObjectURL(
            customImageUrl
        );
    }

    customImageFile =
        file;

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

            updateImageMode();
        };

    image.onerror =
        () => {
            removeSignatureImage();

            announceError(
                t().imageLoadError
            );
        };

    image.src =
        customImageUrl;
}

function removeSignatureImage() {
    customImageFile =
        null;

    imageNaturalWidth =
        0;

    imageNaturalHeight =
        0;

    detectedImageMode =
        "default";

    const input =
        document.getElementById(
            "signatureImage"
        );

    if (input) {
        input.value = "";
    }

    if (customImageUrl) {
        URL.revokeObjectURL(
            customImageUrl
        );

        customImageUrl =
            null;
    }

    const fullImage =
        document.getElementById(
            "full-preview-image"
        );

    if (fullImage) {
        fullImage.removeAttribute(
            "src"
        );
    }

    const info =
        document.getElementById(
            "imageInfo"
        );

    if (info) {
        info.classList.add(
            "hidden"
        );
    }

    updateSignaturePreview();
}

function updateImageMode() {
    if (
        !customImageFile ||
        !imageNaturalHeight
    ) {
        detectedImageMode =
            "default";

        updateSignaturePreview();

        return;
    }

    const select =
        document.getElementById(
            "imageMode"
        );

    const requested =
        select
            ? select.value
            : "auto";

    const ratio =
        imageNaturalWidth /
        imageNaturalHeight;

    if (
        requested === "full" ||
        requested === "logo"
    ) {
        detectedImageMode =
            requested;
    } else {
        detectedImageMode =
            ratio >=
                FULL_SIGNATURE_RATIO
                ? "full"
                : "logo";
    }

    updateImageInfo();
    updateSignaturePreview();
}

function updateImageInfo() {
    const info =
        document.getElementById(
            "imageInfo"
        );

    if (
        !info ||
        !customImageFile ||
        !imageNaturalHeight
    ) {
        return;
    }

    info.classList.remove(
        "hidden"
    );

    setText(
        "imageModeResult",
        detectedImageMode ===
            "full"
            ? t().fullDetected
            : t().logoDetected
    );

    const ratio =
        imageNaturalWidth /
        imageNaturalHeight;

    setText(
        "imageDimensions",
        `${imageNaturalWidth} × ${imageNaturalHeight}px — ${ratio.toFixed(2)}:1`
    );
}

/* ==========================================
   BACKEND
========================================== */

function updateBackendStatus(
    state,
    message = null
) {
    const dot =
        document.getElementById(
            "backend-status-dot"
        );

    const text =
        document.getElementById(
            "backend-status-text"
        );

    if (
        !dot ||
        !text
    ) {
        return;
    }

    dot.classList.remove(
        "backend-status-starting",
        "backend-status-online",
        "backend-status-offline"
    );

    if (
        state === "online"
    ) {
        dot.classList.add(
            "backend-status-online"
        );

        text.textContent =
            message ||
            t().backendOnline;

        return;
    }

    if (
        state === "offline"
    ) {
        dot.classList.add(
            "backend-status-offline"
        );

        text.textContent =
            message ||
            t().backendOffline;

        return;
    }

    dot.classList.add(
        "backend-status-starting"
    );

    text.textContent =
        message ||
        t().backendStarting;
}

async function wakeBackend() {
    if (backendReady) {
        return true;
    }

    if (backendWakePromise) {
        return backendWakePromise;
    }

    backendWakePromise =
        (async () => {
            updateBackendStatus(
                "starting",
                t().backendWaking
            );

            const startedAt =
                Date.now();

            while (
                Date.now() -
                startedAt <
                BACKEND_STATUS_TIMEOUT
            ) {
                backendWakeController =
                    new AbortController();

                const requestTimeout =
                    setTimeout(
                        () => {
                            backendWakeController
                                ?.abort();
                        },
                        12000
                    );

                try {
                    const response =
                        await fetch(
                            `${API_BASE_URL}/api/status`,
                            {
                                method:
                                    "GET",

                                cache:
                                    "no-store",

                                credentials:
                                    "omit",

                                referrerPolicy:
                                    "no-referrer",

                                signal:
                                    backendWakeController
                                        .signal
                            }
                        );

                    clearTimeout(
                        requestTimeout
                    );

                    if (
                        response.ok
                    ) {
                        let data = null;

                        try {
                            data =
                                await response.json();
                        } catch (_) {
                        }

                        if (
                            !data ||
                            data.status ===
                            "ok"
                        ) {
                            backendReady =
                                true;

                            updateBackendStatus(
                                "online"
                            );

                            announce(
                                t().backendOnline
                            );

                            return true;
                        }
                    }

                } catch (error) {
                    clearTimeout(
                        requestTimeout
                    );

                    if (
                        error.name !==
                        "AbortError"
                    ) {
                        console.debug(
                            "Backend ainda não disponível."
                        );
                    }
                }

                const elapsed =
                    Date.now() -
                    startedAt;

                if (
                    elapsed >
                    15000
                ) {
                    updateBackendStatus(
                        "starting",
                        t().backendSlow
                    );
                }

                await new Promise(
                    resolve =>
                        setTimeout(
                            resolve,
                            BACKEND_STATUS_RETRY_INTERVAL
                        )
                );
            }

            backendReady =
                false;

            updateBackendStatus(
                "offline"
            );

            return false;
        })();

    try {
        return await backendWakePromise;

    } finally {
        backendWakePromise =
            null;

        backendWakeController =
            null;
    }
}

/* ==========================================
   PRÉVIA
========================================== */

function getPreviewDateText() {
    const values = [];

    const showDate =
        document.getElementById(
            "showDate"
        );

    const showTime =
        document.getElementById(
            "showTime"
        );

    if (
        showDate &&
        showDate.checked
    ) {
        values.push(
            t().date
        );
    }

    if (
        showTime &&
        showTime.checked
    ) {
        values.push(
            t().time
        );
    }

    return values.join(
        " · "
    );
}

function updateSignaturePreview() {
    const standard =
        document.getElementById(
            "standard-preview"
        );

    const full =
        document.getElementById(
            "full-preview"
        );

    const logo =
        document.getElementById(
            "preview-logo"
        );

    const previewText =
        document.getElementById(
            "preview-text"
        );

    if (
        !standard ||
        !full ||
        !logo ||
        !previewText
    ) {
        return;
    }

    const dateText =
        getPreviewDateText();

    if (
        currentSignatureType ===
        "image" &&
        customImageUrl &&
        detectedImageMode ===
        "full"
    ) {
        standard.style.display =
            "none";

        full.style.display =
            "block";

        const image =
            document.getElementById(
                "full-preview-image"
            );

        if (image) {
            image.src =
                customImageUrl;
        }

        setText(
            "full-preview-date",
            dateText
        );

        return;
    }

    full.style.display =
        "none";

    standard.style.display =
        "flex";

    if (
        currentSignatureType ===
        "image" &&
        customImageUrl &&
        detectedImageMode ===
        "logo"
    ) {
        logo.replaceChildren();

        const image =
            document.createElement(
                "img"
            );

        image.src =
            customImageUrl;

        image.alt = "";

        logo.appendChild(
            image
        );
    } else {
        logo.replaceChildren();

        const defaultIcon =
            document.createElement(
                "div"
            );

        defaultIcon.className =
            "default-icon";

        logo.appendChild(
            defaultIcon
        );
    }

    const customTitleInput =
        document.getElementById(
            "customTitle"
        );

    const customTitle =
        customTitleInput
            ? customTitleInput.value.trim()
            : "";

    const title =
        currentSignatureType ===
            "standard"
            ? t().signedBy
            : (
                customTitle ||
                t().signedBy
            );

    previewText.replaceChildren();

    const strong =
        document.createElement(
            "strong"
        );

    strong.textContent =
        title;

    previewText.appendChild(
        strong
    );

    previewText.appendChild(
        document.createElement(
            "br"
        )
    );

    previewText.appendChild(
        document.createTextNode(
            t().signer
        )
    );

    if (dateText) {
        appendPreviewLine(
            previewText,
            dateText
        );
    }

    const showType =
        document.getElementById(
            "showType"
        );

    if (
        showType &&
        showType.checked
    ) {
        appendPreviewLine(
            previewText,
            t().pades
        );
    }
}

function appendPreviewLine(
    parent,
    text
) {
    parent.appendChild(
        document.createElement(
            "br"
        )
    );

    const small =
        document.createElement(
            "small"
        );

    small.textContent =
        text;

    parent.appendChild(
        small
    );
}


/* ==========================================
   ASSINATURA NO BACKEND
========================================== */

async function signWithBackend() {
    const button =
        document.getElementById(
            "sign-button"
        );

    const certificateInput =
        document.getElementById(
            "p12Input"
        );

    const passwordInput =
        document.getElementById(
            "p12Password"
        );

    if (!backendReady) {
        button.disabled =
            true;

        button.textContent =
            t().backendWaking;

        const ready =
            await wakeBackend();

        if (!ready) {
            button.disabled =
                false;

            button.textContent =
                t().sign;

            showSignError(
                t().backendOffline
            );

            return;
        }
    }

    if (
        !button ||
        !certificateInput ||
        !passwordInput
    ) {
        return;
    }

    if (!currentFile) {
        showSignError(
            t().pdfRequired
        );

        return;
    }

    if (!signaturePos.placed) {
        showSignError(
            t().positionRequired
        );

        return;
    }

    const certificate =
        certificateInput.files[0];

    const password =
        passwordInput.value;

    if (
        !certificate ||
        !password
    ) {
        showSignError(
            t().certificateRequired
        );

        return;
    }

    if (
        currentSignatureType ===
        "image" &&
        !customImageFile
    ) {
        showSignError(
            t().imageRequired
        );

        return;
    }

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

    const customTitle =
        document
            .getElementById(
                "customTitle"
            )
            ?.value
            .trim() ||
        t().signedBy;

    formData.append(
        "visual",
        JSON.stringify({
            titulo:
                currentSignatureType ===
                    "standard"
                    ? t().signedBy
                    : customTitle,

            mostrarData:
                Boolean(
                    document
                        .getElementById(
                            "showDate"
                        )
                        ?.checked
                ),

            mostrarHora:
                Boolean(
                    document
                        .getElementById(
                            "showTime"
                        )
                        ?.checked
                ),

            mostrarTipo:
                Boolean(
                    document
                        .getElementById(
                            "showType"
                        )
                        ?.checked
                )
        })
    );

    if (
        currentSignatureType ===
        "image"
    ) {
        const imageMode =
            document.getElementById(
                "imageMode"
            );

        formData.append(
            "modo_imagem",
            imageMode
                ? imageMode.value
                : "auto"
        );

        formData.append(
            "imagem_assinatura",
            customImageFile
        );
    }

    button.disabled =
        true;

    button.textContent =
        t().processing;

    hideSignError();

    const controller =
        new AbortController();

    const timeout =
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
                    method:
                        "POST",

                    body:
                        formData,

                    signal:
                        controller.signal,

                    cache:
                        "no-store",

                    credentials:
                        "omit",

                    referrerPolicy:
                        "no-referrer"
                }
            );

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

                if (
                    typeof data?.erro ===
                    "string" &&
                    data.erro.trim()
                ) {
                    message =
                        data.erro;
                }
            } catch (_) {
                // Mantém a mensagem HTTP.
            }

            throw new Error(
                message
            );
        }

        const contentType =
            response.headers.get(
                "Content-Type"
            ) || "";

        if (
            !contentType
                .toLowerCase()
                .includes(
                    "application/pdf"
                )
        ) {
            throw new Error(
                t().connectionError
            );
        }

        const blob =
            await response.blob();

        clearSensitiveCertificateFields();

        if (currentDownloadUrl) {
            URL.revokeObjectURL(
                currentDownloadUrl
            );
        }

        currentDownloadUrl =
            URL.createObjectURL(
                blob
            );

        const download =
            document.getElementById(
                "download-button"
            );

        if (download) {
            download.classList.remove(
                "hidden"
            );
        }

        goToStep(5);

        announce(
            t().success
        );

    } catch (error) {
        if (
            error?.name ===
            "AbortError"
        ) {
            showSignError(
                t().requestTimeout
            );

            return;
        }

        if (
            error instanceof TypeError
        ) {
            showSignError(
                t().connectionError
            );

            return;
        }

        showSignError(
            error?.message ||
            t().connectionError
        );

    } finally {
        clearTimeout(
            timeout
        );

        button.disabled =
            false;

        button.textContent =
            t().sign;
    }
}


/* ==========================================
   DADOS SENSÍVEIS
========================================== */

function clearSensitiveCertificateFields() {
    const passwordInput =
        document.getElementById(
            "p12Password"
        );

    const certificateInput =
        document.getElementById(
            "p12Input"
        );

    if (passwordInput) {
        passwordInput.value = "";
    }

    if (certificateInput) {
        certificateInput.value = "";
    }
}


/* ==========================================
   ERROS DA ASSINATURA
========================================== */

function showSignError(message) {
    const error =
        document.getElementById(
            "error-sign"
        );

    if (!error) {
        return;
    }

    error.textContent =
        message;

    error.style.display =
        "block";

    announceError(
        message
    );
}

function hideSignError() {
    const error =
        document.getElementById(
            "error-sign"
        );

    if (!error) {
        return;
    }

    error.textContent = "";

    error.style.display =
        "none";
}


/* ==========================================
   DOWNLOAD
========================================== */

function downloadSignedDocument() {
    if (
        !currentDownloadUrl ||
        !currentFile
    ) {
        return;
    }

    const link =
        document.createElement(
            "a"
        );

    const originalName =
        currentFile.name;

    const withoutExtension =
        originalName
            .toLowerCase()
            .endsWith(".pdf")
            ? originalName.slice(
                0,
                -4
            )
            : originalName;

    link.href =
        currentDownloadUrl;

    link.download =
        `${withoutExtension}${t().signedFilenameSuffix}.pdf`;

    link.rel =
        "noopener";

    document.body.appendChild(
        link
    );

    link.click();

    link.remove();
}


/* ==========================================
   RESET
========================================== */

function resetApp() {
    clearSensitiveCertificateFields();

    currentFile =
        null;

    if (pdfJsDoc) {
        try {
            pdfJsDoc.destroy();
        } catch (_) {
        }
    }

    pdfJsDoc =
        null;

    currentPageNum =
        1;

    totalPages =
        1;

    currentRenderScale =
        1;

    currentSignatureType =
        "standard";

    scrollPageLock =
        false;

    renderToken++;

    signaturePos = {
        placed: false,
        x: 0,
        y: 0,
        canvasRectWidth: 0,
        canvasRectHeight: 0,
        page: 1
    };

    const fileInput =
        document.getElementById(
            "fileInput"
        );

    if (fileInput) {
        fileInput.value = "";
    }

    const showDate =
        document.getElementById(
            "showDate"
        );

    const showTime =
        document.getElementById(
            "showTime"
        );

    const showType =
        document.getElementById(
            "showType"
        );

    if (showDate) {
        showDate.checked =
            true;
    }

    if (showTime) {
        /*
         * Hora desmarcada por padrão.
         */
        showTime.checked =
            false;
    }

    if (showType) {
        showType.checked =
            true;
    }

    const customTitle =
        document.getElementById(
            "customTitle"
        );

    if (customTitle) {
        customTitle.value =
            t().signedBy;
    }

    const imageMode =
        document.getElementById(
            "imageMode"
        );

    if (imageMode) {
        imageMode.value =
            "auto";
    }

    const simpleOptions =
        document.getElementById(
            "simple-options"
        );

    const imageOptions =
        document.getElementById(
            "image-options"
        );

    if (simpleOptions) {
        simpleOptions
            .classList
            .add(
                "hidden"
            );
    }

    if (imageOptions) {
        imageOptions
            .classList
            .add(
                "hidden"
            );
    }

    resetSignaturePosition();
    removeSignatureImage();

    if (currentDownloadUrl) {
        URL.revokeObjectURL(
            currentDownloadUrl
        );

        currentDownloadUrl =
            null;
    }

    const download =
        document.getElementById(
            "download-button"
        );

    if (download) {
        download.classList.add(
            "hidden"
        );
    }

    hidePdfError();
    hideSignError();

    updateSignaturePreview();

    goToStep(1);
}


/* ==========================================
   EVENTOS
========================================== */

document
    .getElementById(
        "theme-button"
    )
    ?.addEventListener(
        "click",
        toggleTheme
    );

document
    .getElementById(
        "language-button"
    )
    ?.addEventListener(
        "click",
        toggleLanguage
    );

document
    .getElementById(
        "fileInput"
    )
    ?.addEventListener(
        "change",
        handleFileUpload
    );

document
    .getElementById(
        "prev-page"
    )
    ?.addEventListener(
        "click",
        () => {
            changePage(-1);
        }
    );

document
    .getElementById(
        "next-page"
    )
    ?.addEventListener(
        "click",
        () => {
            changePage(1);
        }
    );

document
    .getElementById(
        "pdf-stage"
    )
    ?.addEventListener(
        "click",
        placeSignature
    );

document
    .getElementById(
        "cancel-button"
    )
    ?.addEventListener(
        "click",
        resetApp
    );

document
    .getElementById(
        "confirm-position-button"
    )
    ?.addEventListener(
        "click",
        confirmPosition
    );

document
    .querySelectorAll(
        "[data-signature-type]"
    )
    .forEach(
        button => {
            button.addEventListener(
                "click",
                () => {
                    selectSignatureType(
                        button.dataset
                            .signatureType
                    );
                }
            );
        }
    );

document
    .getElementById(
        "back-type-button"
    )
    ?.addEventListener(
        "click",
        () => {
            goToStep(2);
        }
    );

document
    .getElementById(
        "back-config-button"
    )
    ?.addEventListener(
        "click",
        () => {
            goToStep(3);
        }
    );

document
    .getElementById(
        "signatureImage"
    )
    ?.addEventListener(
        "change",
        handleSignatureImage
    );

document
    .getElementById(
        "imageMode"
    )
    ?.addEventListener(
        "change",
        updateImageMode
    );

document
    .getElementById(
        "customTitle"
    )
    ?.addEventListener(
        "input",
        updateSignaturePreview
    );

[
    "showDate",
    "showTime",
    "showType"
].forEach(
    id => {
        document
            .getElementById(id)
            ?.addEventListener(
                "change",
                updateSignaturePreview
            );
    }
);

document
    .getElementById(
        "sign-button"
    )
    ?.addEventListener(
        "click",
        signWithBackend
    );

document
    .getElementById(
        "download-button"
    )
    ?.addEventListener(
        "click",
        downloadSignedDocument
    );

document
    .getElementById(
        "restart-button"
    )
    ?.addEventListener(
        "click",
        resetApp
    );


/* ==========================================
   SCROLL AUTOMÁTICO ENTRE PÁGINAS
========================================== */

document
    .getElementById(
        "canvas-container"
    )
    ?.addEventListener(
        "scroll",
        async event => {
            const container =
                event.currentTarget;

            if (
                !pdfJsDoc ||
                scrollPageLock ||
                currentPageNum >=
                totalPages
            ) {
                return;
            }

            /*
             * Só aplica a troca automática
             * quando existe efetivamente
             * scroll vertical.
             */
            const hasVerticalScroll =
                container.scrollHeight >
                container.clientHeight +
                2;

            if (!hasVerticalScroll) {
                return;
            }

            const reachedBottom =
                container.scrollTop +
                container.clientHeight >=
                container.scrollHeight -
                3;

            if (reachedBottom) {
                await changePage(
                    1
                );
            }
        }
    );


/* ==========================================
   REDIMENSIONAMENTO
========================================== */

window.addEventListener(
    "resize",
    () => {
        if (!pdfJsDoc) {
            return;
        }

        clearTimeout(
            resizeTimer
        );

        resizeTimer =
            setTimeout(
                () => {
                    renderPage(
                        currentPageNum,
                        false
                    );
                },
                200
            );
    }
);


/* ==========================================
   PREFERÊNCIA DE TEMA DO SISTEMA
========================================== */

const themeQuery =
    window.matchMedia(
        "(prefers-color-scheme: dark)"
    );

themeQuery.addEventListener(
    "change",
    event => {
        /*
         * Só acompanha alterações do
         * sistema enquanto o usuário
         * não escolher manualmente.
         */
        if (
            !localStorage.getItem(
                "theme"
            )
        ) {
            applyTheme(
                event.matches
                    ? "dark"
                    : "light"
            );
        }
    }
);


/* ==========================================
   LIMPEZA AO SAIR DA PÁGINA
========================================== */

window.addEventListener(
    "pagehide",
    () => {
        clearSensitiveCertificateFields();

        if (customImageUrl) {
            URL.revokeObjectURL(
                customImageUrl
            );

            customImageUrl =
                null;
        }

        if (currentDownloadUrl) {
            URL.revokeObjectURL(
                currentDownloadUrl
            );

            currentDownloadUrl =
                null;
        }
    }
);


/* ==========================================
   INICIALIZAÇÃO
========================================== */

initializeTheme();
applyTranslations();
updateSignaturePreview();
wakeBackend();