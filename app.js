"use strict";

pdfjsLib.GlobalWorkerOptions.workerSrc =
    "./vendor/pdfjs/pdf.worker.min.js";

const API_BASE_URL =
    window.location.hostname.includes("github.io")
        ? "https://seu-projeto-backend.onrender.com"
        : "http://127.0.0.1:5000";

const STAMP_WIDTH = 240;
const STAMP_HEIGHT = 68;
const FULL_SIGNATURE_RATIO = 2.2;
const MAX_PDF_SIZE = 25 * 1024 * 1024;
const MAX_IMAGE_SIZE = 2 * 1024 * 1024;

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

let signaturePos = {
    placed: false,
    x: 0,
    y: 0,
    canvasRectWidth: 0,
    canvasRectHeight: 0,
    page: 1
};

const translations = {
    pt: {
        htmlLang: "pt-BR",
        title: "Assinador Digital",
        steps: [
            "Etapa 1 de 5: Envio do documento",
            "Etapa 2 de 5: Posicionamento",
            "Etapa 3 de 5: Tipo de assinatura",
            "Etapa 4 de 5: Configuração",
            "Etapa 5 de 5: Concluído"
        ],
        languageButton: "EN",
        signedBy: "Assinado digitalmente por",
        signer: "Nome do titular",
        date: "Data da assinatura",
        time: "Hora da assinatura",
        pades: "Assinatura digital PAdES",
        page: "Página {current} de {total}",
        invalidPdf: "Selecione um arquivo PDF válido.",
        pdfTooLarge: "O PDF deve ter no máximo 25 MB.",
        pdfError: "Não foi possível abrir o PDF.",
        positionRequired:
            "Clique no documento para posicionar a assinatura.",
        certificateRequired:
            "Selecione o certificado e informe a senha.",
        imageRequired:
            "Selecione uma imagem para esta opção.",
        invalidImage:
            "Utilize somente uma imagem PNG ou JPEG.",
        imageTooLarge:
            "A imagem deve ter no máximo 2 MB.",
        processing: "Processando...",
        sign: "Assinar documento",
        success:
            "Documento assinado com sucesso. O download está disponível.",
        fullDetected:
            "Detectada como assinatura completa",
        logoDetected:
            "Detectada como logotipo/imagem lateral"
    },

    en: {
        htmlLang: "en",
        title: "Digital Signer",
        steps: [
            "Step 1 of 5: Document upload",
            "Step 2 of 5: Placement",
            "Step 3 of 5: Signature type",
            "Step 4 of 5: Configuration",
            "Step 5 of 5: Completed"
        ],
        languageButton: "PT",
        signedBy: "Digitally signed by",
        signer: "Certificate holder",
        date: "Signature date",
        time: "Signature time",
        pades: "PAdES digital signature",
        page: "Page {current} of {total}",
        invalidPdf: "Select a valid PDF file.",
        pdfTooLarge: "The PDF must be no larger than 25 MB.",
        pdfError: "Unable to open the PDF.",
        positionRequired:
            "Click on the document to position the signature.",
        certificateRequired:
            "Select the certificate and enter its password.",
        imageRequired:
            "Select an image for this option.",
        invalidImage:
            "Use a PNG or JPEG image only.",
        imageTooLarge:
            "The image must be no larger than 2 MB.",
        processing: "Processing...",
        sign: "Sign document",
        success:
            "Document signed successfully. The download is available.",
        fullDetected:
            "Detected as complete signature",
        logoDetected:
            "Detected as logo/side image"
    }
};

const savedLanguage =
    localStorage.getItem(
        "language"
    );

let currentLanguage =
    savedLanguage ||
    (
        navigator.language
            .toLowerCase()
            .startsWith("pt")
            ? "pt"
            : "en"
    );

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
    return window
        .matchMedia(
            "(prefers-color-scheme: dark)"
        )
        .matches;
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

    document
        .getElementById(
            "theme-button"
        )
        .setAttribute(
            "aria-pressed",
            String(dark)
        );
}

function initializeTheme() {
    applyTheme(
        manualTheme ||
        (
            systemPrefersDark()
                ? "dark"
                : "light"
        )
    );
}

function toggleTheme() {
    const dark =
        document.documentElement
            .classList
            .contains(
                "dark-theme"
            );

    manualTheme =
        dark
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

function toggleLanguage() {
    currentLanguage =
        currentLanguage === "pt"
            ? "en"
            : "pt";

    localStorage.setItem(
        "language",
        currentLanguage
    );

    applyTranslations();
    updateSignaturePreview();
}

function applyTranslations() {
    document.documentElement.lang =
        t().htmlLang;

    document.title =
        t().title;

    document
        .getElementById(
            "title"
        )
        .textContent =
            t().title;

    document
        .getElementById(
            "language-label"
        )
        .textContent =
            t().languageButton;

    updateStepSubtitle();
    updatePagination();
    updateImageInfo();
}

function announce(message) {
    const element =
        document.getElementById(
            "screen-reader-announcer"
        );

    element.textContent = "";

    requestAnimationFrame(
        () => {
            element.textContent =
                message;
        }
    );
}

function announceError(message) {
    const element =
        document.getElementById(
            "screen-reader-alert"
        );

    element.textContent = "";

    requestAnimationFrame(
        () => {
            element.textContent =
                message;
        }
    );
}

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
    const step =
        getCurrentStep();

    document
        .getElementById(
            "subtitle"
        )
        .textContent =
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

    target.scrollIntoView({
        block: "start"
    });
}

async function handleFileUpload(event) {
    const file =
        event.target.files[0];

    if (!file) {
        return;
    }

    const error =
        document.getElementById(
            "error-pdf"
        );

    if (
        file.size >
        MAX_PDF_SIZE
    ) {
        showPdfError(
            t().pdfTooLarge
        );

        event.target.value = "";

        return;
    }

    const isPdf =
        file.type ===
            "application/pdf"
        ||
        file.name
            .toLowerCase()
            .endsWith(".pdf");

    if (!isPdf) {
        showPdfError(
            t().invalidPdf
        );

        event.target.value = "";

        return;
    }

    error.style.display =
        "none";

    currentFile =
        file;

    try {
        const buffer =
            await file.arrayBuffer();

        const bytes =
            new Uint8Array(
                buffer
            );

        if (
            bytes.length < 5
            ||
            String.fromCharCode(
                ...bytes.slice(
                    0,
                    Math.min(
                        1024,
                        bytes.length
                    )
                )
            ).indexOf(
                "%PDF"
            ) === -1
        ) {
            throw new Error(
                t().invalidPdf
            );
        }

        pdfJsDoc =
            await pdfjsLib
                .getDocument({
                    data: bytes
                })
                .promise;

        totalPages =
            pdfJsDoc.numPages;

        goToStep(2);

        await renderPage(
            1,
            true
        );

    } catch (errorPdf) {
        console.error(
            "Falha ao carregar o PDF."
        );

        currentFile =
            null;

        showPdfError(
            errorPdf.message ||
            t().pdfError
        );
    }
}

function showPdfError(message) {
    const error =
        document.getElementById(
            "error-pdf"
        );

    error.textContent =
        message;

    error.style.display =
        "block";

    announceError(
        message
    );
}

async function renderPage(
    pageNumber,
    resetScroll = true
) {
    if (!pdfJsDoc) {
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
            .1,
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
}

function updatePagination() {
    if (!pdfJsDoc) {
        return;
    }

    document
        .getElementById(
            "page-indicator"
        )
        .textContent =
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

    document
        .getElementById(
            "prev-page"
        )
        .disabled =
            currentPageNum <= 1;

    document
        .getElementById(
            "next-page"
        )
        .disabled =
            currentPageNum >=
            totalPages;
}

async function changePage(offset) {
    if (
        !pdfJsDoc
        ||
        scrollPageLock
    ) {
        return;
    }

    const newPage =
        currentPageNum +
        offset;

    if (
        newPage < 1
        ||
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

function placeSignature(event) {
    const stage =
        document.getElementById(
            "pdf-stage"
        );

    const box =
        document.getElementById(
            "signature-box"
        );

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
        clickX < 0
        ||
        clickX >
        rect.width
        ||
        clickY < 0
        ||
        clickY >
        rect.height
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
}

function resetSignaturePosition() {
    signaturePos = {
        placed: false,
        x: 0,
        y: 0,
        canvasRectWidth: 0,
        canvasRectHeight: 0,
        page: currentPageNum
    };

    document
        .getElementById(
            "signature-box"
        )
        .style.display =
            "none";
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

function selectSignatureType(type) {
    currentSignatureType =
        type;

    document
        .getElementById(
            "simple-options"
        )
        .classList
        .toggle(
            "hidden",
            type === "standard"
        );

    document
        .getElementById(
            "image-options"
        )
        .classList
        .toggle(
            "hidden",
            type !== "image"
        );

    updateSignaturePreview();

    goToStep(4);
}

function handleSignatureImage(event) {
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
        event.target.value =
            "";

        announceError(
            t().invalidImage
        );

        return;
    }

    if (
        file.size >
        MAX_IMAGE_SIZE
    ) {
        event.target.value =
            "";

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
                t().invalidImage
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

    document
        .getElementById(
            "imageInfo"
        )
        .classList
        .add(
            "hidden"
        );

    updateSignaturePreview();
}

function updateImageMode() {
    if (
        !customImageFile
        ||
        !imageNaturalHeight
    ) {
        detectedImageMode =
            "default";

        updateSignaturePreview();

        return;
    }

    const requested =
        document.getElementById(
            "imageMode"
        ).value;

    const ratio =
        imageNaturalWidth /
        imageNaturalHeight;

    if (
        requested === "full"
        ||
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
    if (
        !customImageFile
        ||
        !imageNaturalHeight
    ) {
        return;
    }

    const info =
        document.getElementById(
            "imageInfo"
        );

    info.classList.remove(
        "hidden"
    );

    document
        .getElementById(
            "imageModeResult"
        )
        .textContent =
            detectedImageMode ===
            "full"
                ? t().fullDetected
                : t().logoDetected;

    document
        .getElementById(
            "imageDimensions"
        )
        .textContent =
            `${imageNaturalWidth} × ${imageNaturalHeight}px`;
}

function getPreviewDateText() {
    const values = [];

    if (
        document.getElementById(
            "showDate"
        ).checked
    ) {
        values.push(
            t().date
        );
    }

    if (
        document.getElementById(
            "showTime"
        ).checked
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

    const dateText =
        getPreviewDateText();

    if (
        currentSignatureType ===
            "image"
        &&
        customImageUrl
        &&
        detectedImageMode ===
            "full"
    ) {
        standard.style.display =
            "none";

        full.style.display =
            "block";

        document
            .getElementById(
                "full-preview-image"
            )
            .src =
                customImageUrl;

        document
            .getElementById(
                "full-preview-date"
            )
            .textContent =
                dateText;

        return;
    }

    full.style.display =
        "none";

    standard.style.display =
        "flex";

    if (
        currentSignatureType ===
            "image"
        &&
        customImageUrl
        &&
        detectedImageMode ===
            "logo"
    ) {
        logo.replaceChildren();

        const img =
            document.createElement(
                "img"
            );

        img.src =
            customImageUrl;

        img.alt = "";

        logo.appendChild(
            img
        );
    } else {
        logo.innerHTML =
            '<div class="default-icon"></div>';
    }

    const customTitle =
        document.getElementById(
            "customTitle"
        ).value.trim();

    const title =
        currentSignatureType ===
            "standard"
            ? t().signedBy
            : (
                customTitle ||
                t().signedBy
            );

    previewText
        .replaceChildren();

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

    if (
        document.getElementById(
            "showType"
        ).checked
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

async function signWithBackend() {
    const certificateInput =
        document.getElementById(
            "p12Input"
        );

    const passwordInput =
        document.getElementById(
            "p12Password"
        );

    const certificate =
        certificateInput.files[0];

    const password =
        passwordInput.value;

    const button =
        document.getElementById(
            "sign-button"
        );

    if (
        !certificate
        ||
        !password
    ) {
        showSignError(
            t().certificateRequired
        );

        return;
    }

    if (
        currentSignatureType ===
            "image"
        &&
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

    formData.append(
        "visual",
        JSON.stringify({
            titulo:
                document
                    .getElementById(
                        "customTitle"
                    )
                    .value
                    .trim(),

            mostrarData:
                document
                    .getElementById(
                        "showDate"
                    )
                    .checked,

            mostrarHora:
                document
                    .getElementById(
                        "showTime"
                    )
                    .checked,

            mostrarTipo:
                document
                    .getElementById(
                        "showType"
                    )
                    .checked
        })
    );

    if (
        currentSignatureType ===
            "image"
    ) {
        formData.append(
            "modo_imagem",
            document
                .getElementById(
                    "imageMode"
                )
                .value
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
        setTimeout(
            () => controller.abort(),
            120000
        );

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/api/assinar`,
                {
                    method: "POST",
                    body: formData,
                    signal:
                        controller.signal,
                    cache: "no-store",
                    credentials:
                        "omit",
                    referrerPolicy:
                        "no-referrer"
                }
            );

        if (!response.ok) {
            let message =
                `HTTP ${response.status}`;

            try {
                const data =
                    await response.json();

                if (data?.erro) {
                    message =
                        data.erro;
                }
            } catch (_) {
            }

            throw new Error(
                message
            );
        }

        const blob =
            await response.blob();

        clearSensitiveCertificateFields();

        if (
            currentDownloadUrl
        ) {
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

        download.classList.remove(
            "hidden"
        );

        download.onclick =
            downloadSignedDocument;

        goToStep(5);

        announce(
            t().success
        );

    } catch (error) {
        if (
            error.name ===
            "AbortError"
        ) {
            showSignError(
                "A operação excedeu o tempo limite."
            );
        } else {
            showSignError(
                error.message
            );
        }
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

function clearSensitiveCertificateFields() {
    document.getElementById(
        "p12Password"
    ).value = "";

    document.getElementById(
        "p12Input"
    ).value = "";
}

function showSignError(message) {
    const error =
        document.getElementById(
            "error-sign"
        );

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

    error.textContent = "";

    error.style.display =
        "none";
}

function downloadSignedDocument() {
    if (
        !currentDownloadUrl
        ||
        !currentFile
    ) {
        return;
    }

    const link =
        document.createElement(
            "a"
        );

    const name =
        currentFile.name;

    link.href =
        currentDownloadUrl;

    link.download =
        name
            .toLowerCase()
            .endsWith(".pdf")
            ? `${name.slice(0, -4)}_assinado.pdf`
            : `${name}_assinado.pdf`;

    link.rel =
        "noopener";

    document.body.appendChild(
        link
    );

    link.click();

    link.remove();
}

function resetApp() {
    clearSensitiveCertificateFields();

    currentFile =
        null;

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

    signaturePos = {
        placed: false,
        x: 0,
        y: 0,
        canvasRectWidth: 0,
        canvasRectHeight: 0,
        page: 1
    };

    document.getElementById(
        "fileInput"
    ).value = "";

    document.getElementById(
        "showDate"
    ).checked = true;

    document.getElementById(
        "showTime"
    ).checked = false;

    document.getElementById(
        "showType"
    ).checked = true;

    document.getElementById(
        "customTitle"
    ).value =
        t().signedBy;

    removeSignatureImage();

    if (
        currentDownloadUrl
    ) {
        URL.revokeObjectURL(
            currentDownloadUrl
        );

        currentDownloadUrl =
            null;
    }

    document.getElementById(
        "download-button"
    ).classList.add(
        "hidden"
    );

    hideSignError();

    goToStep(1);
}

document
    .getElementById(
        "theme-button"
    )
    .addEventListener(
        "click",
        toggleTheme
    );

document
    .getElementById(
        "language-button"
    )
    .addEventListener(
        "click",
        toggleLanguage
    );

document
    .getElementById(
        "fileInput"
    )
    .addEventListener(
        "change",
        handleFileUpload
    );

document
    .getElementById(
        "prev-page"
    )
    .addEventListener(
        "click",
        () => changePage(-1)
    );

document
    .getElementById(
        "next-page"
    )
    .addEventListener(
        "click",
        () => changePage(1)
    );

document
    .getElementById(
        "pdf-stage"
    )
    .addEventListener(
        "click",
        placeSignature
    );

document
    .getElementById(
        "cancel-button"
    )
    .addEventListener(
        "click",
        resetApp
    );

document
    .getElementById(
        "confirm-position-button"
    )
    .addEventListener(
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
    .addEventListener(
        "click",
        () => goToStep(2)
    );

document
    .getElementById(
        "back-config-button"
    )
    .addEventListener(
        "click",
        () => goToStep(3)
    );

document
    .getElementById(
        "signatureImage"
    )
    .addEventListener(
        "change",
        handleSignatureImage
    );

document
    .getElementById(
        "imageMode"
    )
    .addEventListener(
        "change",
        updateImageMode
    );

[
    "customTitle",
    "showDate",
    "showTime",
    "showType"
].forEach(
    id => {
        document
            .getElementById(
                id
            )
            .addEventListener(
                "input",
                updateSignaturePreview
            );
    }
);

document
    .getElementById(
        "sign-button"
    )
    .addEventListener(
        "click",
        signWithBackend
    );

document
    .getElementById(
        "restart-button"
    )
    .addEventListener(
        "click",
        resetApp
    );

document
    .getElementById(
        "canvas-container"
    )
    .addEventListener(
        "scroll",
        async event => {
            const container =
                event.currentTarget;

            if (
                scrollPageLock
                ||
                currentPageNum >=
                totalPages
            ) {
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

window.addEventListener(
    "pagehide",
    () => {
        clearSensitiveCertificateFields();

        if (customImageUrl) {
            URL.revokeObjectURL(
                customImageUrl
            );
        }

        if (currentDownloadUrl) {
            URL.revokeObjectURL(
                currentDownloadUrl
            );
        }
    }
);

const themeQuery =
    window.matchMedia(
        "(prefers-color-scheme: dark)"
    );

themeQuery.addEventListener(
    "change",
    event => {
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

initializeTheme();
applyTranslations();
updateSignaturePreview();