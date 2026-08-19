# 🔏 Assinador Digital PAdES | Digital Signer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![pyHanko](https://img.shields.io/badge/pyHanko-0.36.2-blue.svg)](https://www.pyhanko.eu/)
[![PAdES](https://img.shields.io/badge/Signature-PAdES-green.svg)](https://en.wikipedia.org/wiki/PAdES)

**[🇧🇷 Português](#-português) | [🇺🇸 English](#-english)**

---

# 🇧🇷 Português

## 🔏 Sobre o projeto

O **Assinador Digital PAdES** é um projeto de código aberto para assinatura criptográfica de documentos PDF utilizando certificados digitais PKCS#12 em arquivos `.p12` ou `.pfx`.

O projeto oferece duas formas de uso:

- **Versão Web:** frontend estático com HTML, CSS, JavaScript e PDF.js, conectado a um backend Flask hospedável no Render;
- **Versão Desktop:** aplicação local em PySide6, sem navegador e sem necessidade de enviar documento, certificado ou senha para um servidor remoto.

As duas versões utilizam **pyHanko** para produzir assinaturas digitais no padrão **PAdES (PDF Advanced Electronic Signatures)**.

> **Importante:** a aparência visual inserida no PDF é independente da assinatura criptográfica. Imagens, logotipos e carimbos visuais não substituem o certificado digital nem determinam, isoladamente, a validade da assinatura.

>**não recomendamos a versão Web para documentos confidenciais, certificados de alto valor ou situações que exijam o maior nível possível de privacidade**.
> Para esses casos, prefira a **versão Desktop** ou a execução da **versão Web** localmente, ambas executam o processo de assinatura localmente no computador e não precisa enviar o documento, o certificado ou a senha para o servidor do projeto.

---

## ✨ Recursos principais

### 🔐 Assinatura PAdES

- assinatura criptográfica de documentos PDF com `pyHanko`;
- suporte a certificados `.p12` e `.pfx`;
- algoritmo de resumo SHA-256;
- atualização incremental do PDF;
- campos de assinatura com identificadores únicos;
- nome do titular obtido diretamente do certificado;
- remoção do CPF apenas da **aparência visual** quando ele estiver anexado ao `Common Name` do certificado;
- campo visual de assinatura com **240 × 68 pontos PDF**.

### 🎨 Aparências disponíveis

A aplicação oferece três tipos de aparência:

1. **Padrão** — identidade visual própria do Assinador Digital;
2. **Customizada simples** — permite personalizar o texto e as informações exibidas;
3. **Customizada com imagem** — permite utilizar um logotipo/imagem lateral ou uma imagem completa de assinatura.

Imagens personalizadas aceitas:

- PNG;
- JPEG/JPG;
- até **2 MB**;
- resolução máxima de **4000 × 4000 pixels**.

O sistema pode detectar automaticamente se uma imagem horizontal deve ser tratada como uma assinatura completa ou como logotipo/imagem lateral.

### 📅 Data e hora

A data é exibida por padrão. A hora é opcional e permanece desmarcada inicialmente.

```text
Data ✓ | Hora ✗ → 19/08/2026
Data ✓ | Hora ✓ → 19/08/2026 04:25
Data ✗ | Hora ✓ → 04:25
Data ✗ | Hora ✗ → nenhuma informação temporal
```

Na versão Web, o timezone pode ser configurado com `APP_TIMEZONE`. Na versão Desktop, o padrão atual é `America/Sao_Paulo`, com fallback para UTC.

---

## 🌐 Versão Web

A versão Web utiliza:

- HTML5;
- CSS3;
- JavaScript;
- PDF.js hospedado localmente no próprio projeto;
- Flask;
- Gunicorn;
- pyHanko;
- ReportLab;
- Pillow;
- Flask-Limiter;
- Redis compatível para Rate Limiting compartilhado em produção.

### Recursos do frontend

- visualização do PDF com PDF.js;
- suporte a documentos multipágina;
- posicionamento visual da assinatura;
- avanço automático para a próxima página ao chegar ao fim do scroll;
- interface em Português e Inglês;
- idioma inicial baseado no navegador/sistema;
- tema claro/escuro com preferência inicial do sistema;
- suporte a leitores de tela com ARIA, regiões `aria-live`, mensagens de alerta e navegação por teclado;
- Content Security Policy (CSP);
- PDF.js sem dependência de CDN durante o uso;
- indicador de disponibilidade do backend.

### Acordar o backend do Render

Ao carregar a página, o frontend chama:

```text
GET /api/status
```

Esse pedido é feito em segundo plano enquanto o usuário seleciona o PDF e posiciona a assinatura. Em serviços do Render que entram em suspensão por inatividade, isso permite iniciar o backend antes de o usuário chegar à etapa final de assinatura.

A interface pode indicar os estados:

```text
🟡 Iniciando serviço de assinatura...
🟢 Serviço de assinatura disponível
🔴 Serviço de assinatura indisponível
```

A rota `/api/status` é isenta da validação de `Origin` e do Rate Limiting para permitir health checks e inicialização do serviço.

---

## 💻 Versão Desktop

A versão Desktop está em:

```text
desktop/local.py
```

Ela utiliza **PySide6** para uma interface gráfica nativa e **PyMuPDF** para renderização local dos PDFs.

### Características

- não utiliza Flask;
- não utiliza navegador;
- não depende do Render;
- não depende de GitHub Pages;
- documento, certificado, senha e imagem permanecem no computador do usuário;
- renderização do PDF em alta resolução com fator interno de qualidade `2.5`;
- navegação multipágina;
- avanço automático para a próxima página ao chegar ao fim do scroll;
- posicionamento visual da assinatura;
- posicionamento acessível opcional por página e região predefinida;
- toggle para exibir ou ocultar os controles de posicionamento acessível;
- Português/Inglês;
- tema inicial baseado no sistema;
- alternância manual de tema corrigida por estado interno explícito;
- etapa de configuração adaptada ao tipo de aparência selecionado;
- assinatura executada em `QThread` para evitar bloquear a interface;
- seleção nativa de PDF, certificado, imagem e local de salvamento;
- possibilidade de empacotamento futuro como `.exe`.

### Posicionamento acessível

O usuário pode ativar:

```text
☑ Utilizar posicionamento acessível
```

E selecionar, sem depender do mouse:

```text
Página: 1
Posição: Canto superior esquerdo
         Canto superior direito
         Canto inferior esquerdo
         Canto inferior direito
         Centro
```

Isso complementa o posicionamento visual por clique e melhora a utilização com teclado e tecnologias assistivas.

> A acessibilidade deve ser validada também com leitores de tela reais, como NVDA no Windows. O uso de widgets Qt nativos e nomes/descritivos acessíveis fornece a base, mas não substitui testes práticos.

---

## 🛡️ Segurança e privacidade

### Versão Web

O backend inclui medidas como:

- limite de tamanho da requisição;
- limite de PDF, certificado e imagem;
- validação de PDF e imagem;
- restrição de formatos de imagem;
- limite de resolução;
- arquivos temporários com limpeza posterior;
- CORS configurável;
- validação explícita do header `Origin`;
- opção de exigir HTTPS em produção;
- Rate Limiting;
- suporte a Redis para limites compartilhados;
- `TRUSTED_HOSTS` configurável;
- headers HTTP adicionais de segurança;
- respostas sensíveis com cache desabilitado;
- tratamento controlado de erros.

No frontend:

- CSP restringe scripts, estilos e conexões;
- PDF.js é hospedado localmente;
- `fetch` usa `credentials: "omit"`;
- campos sensíveis são limpos quando necessário;
- requisições possuem timeout;
- o backend permitido é definido em `connect-src`.

> CORS e `Origin` ajudam a restringir o uso comum da API por outros sites, mas não constituem autenticação. Um cliente HTTP externo pode falsificar o header `Origin`.

### Versão Desktop

Na versão local não existe comunicação cliente-servidor. O fluxo é:

```text
PDF + certificado + senha
          ↓
     processamento local
          ↓
       pyHanko
          ↓
      PDF assinado
```

Mesmo localmente são mantidos:

- limites de tamanho;
- validação de PDF;
- validação de PNG/JPEG;
- limite de resolução de imagem;
- limpeza de arquivos temporários;
- senha mantida apenas durante a operação de assinatura.

---

## 🎓 Certificado Pessoal ICPEdu

O **[ICPEdu - Certificado Pessoal](https://pessoal.icpedu.rnp.br/)** é um serviço disponibilizado pela Rede Nacional de Ensino e Pesquisa (RNP) para usuários elegíveis de instituições participantes.

Certificados pessoais ICPEdu disponibilizados em formato PKCS#12 (`.p12`/`.pfx`) podem ser utilizados no projeto quando compatíveis com a infraestrutura criptográfica utilizada pelo `pyHanko`.

👉 **[Acessar o Certificado Pessoal ICPEdu](https://pessoal.icpedu.rnp.br/)**

### Aviso sobre identidade visual

Este projeto utiliza **identidade visual própria** para suas aparências de assinatura.

Utilizar um certificado ICPEdu neste projeto **não significa que o documento tenha sido assinado pelo sistema oficial da RNP**. As referências a ICPEdu e RNP identificam os respectivos serviços e organizações e não indicam afiliação ou endosso deste projeto.

---

## 🏗️ Arquitetura

```text
Assinador Digital PAdES
│
├── 🌐 Versão Web
│   │
│   ├── GitHub Pages / frontend estático
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── styles.css
│   │   └── vendor/pdfjs/
│   │
│   └── Render / backend
│       ├── Flask
│       ├── Gunicorn
│       ├── pyHanko
│       ├── ReportLab
│       ├── Pillow
│       └── Flask-Limiter / Redis
│
└── 💻 Versão Desktop
    ├── PySide6
    ├── PyMuPDF
    ├── pyHanko
    ├── ReportLab
    └── Pillow
```

---

## 📁 Estrutura do projeto

```text
project/
├── index.html
├── app.js
├── styles.css
├── README.md
├── LICENSE
├── .gitignore
│
├── vendor/
│   └── pdfjs/
│       ├── pdf.min.js
│       └── pdf.worker.min.js
│
├── backend/
│   ├── app.py
│   ├── gunicorn.conf.py
│   └── requirements.txt
│
└── desktop/
    ├── local.py
    └── requirements.txt
```

---

## 📦 Dependências

### Backend Web

`backend/requirements.txt`:

```txt
Flask==3.1.3
Flask-Cors==6.0.5
Flask-Limiter[redis]==3.12
gunicorn==23.0.0
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

### Desktop

`desktop/requirements.txt`:

```txt
PySide6
PyMuPDF
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

As versões de PySide6 e PyMuPDF podem ser fixadas posteriormente após a validação da combinação escolhida para distribuição do executável.

---

## 🚀 Desenvolvimento da versão Web

### 1. Clone o repositório

```bash
git clone <URL-DO-REPOSITORIO>
cd <NOME-DO-REPOSITORIO>
```

### 2. Crie e ative um ambiente virtual

Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale o backend

```bash
pip install -r backend/requirements.txt
```

### 4. Inicie o backend local

A partir da raiz:

```powershell
python backend/app.py
```

No Windows, se o comando `python` não estiver disponível, use:

```powershell
py backend/app.py
```

Por padrão:

```text
http://127.0.0.1:5000
```

Status:

```text
http://127.0.0.1:5000/api/status
```

### 5. Sirva o frontend

Use um servidor HTTP local, como Live Server no VS Code.

Exemplo:

```text
http://127.0.0.1:5500
```

> Abrir `index.html` diretamente por `file://` pode impedir o funcionamento correto de recursos e políticas de segurança do navegador.

---

## 💻 Executando a versão Desktop

Crie um ambiente separado:

```powershell
py -m venv .venv-desktop
.\.venv-desktop\Scripts\Activate.ps1
```

Instale:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r desktop/requirements.txt
```

Valide a sintaxe:

```powershell
python -m py_compile desktop/local.py
```

Execute:

```powershell
python desktop/local.py
```

Execute o comando na raiz do repositório, onde estão as pastas `desktop` e `backend`. No Windows, se `python` não estiver disponível no `PATH`, use:

```powershell
py desktop/local.py
```

O módulo compartilhado `backend/verifier.py` é carregado automaticamente pela aplicação Desktop. Não é necessário copiar `verifier.py` para a pasta `desktop`.

A versão Desktop abre uma janela nativa e não inicia navegador ou servidor HTTP.

### Empacotamento como `.exe`

Uma opção para distribuição no Windows é o PyInstaller. Recomenda-se testar inicialmente em modo `onedir`:

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm --onefile --windowed --name AssinadorDigital desktop/local.py
```

Depois de validar DLLs, plugins Qt, pyHanko, PyMuPDF e demais dependências, pode-se avaliar o modo `--onefile`.


## Versão Standalone

A versão standalone para Windows está disponível através do GitHub Releases.

**[⬇️ Baixar a versão Desktop mais recente](../../releases/latest)**

> A versão Desktop processa o PDF, o certificado e a senha localmente no computador e não precisa utilizar o backend remoto do projeto.

---

## ♿ Acessibilidade

### Web

A interface Web inclui:

- labels associados aos campos;
- `aria-live`;
- `role="alert"`;
- descrições ARIA;
- skip link;
- navegação por teclado;
- indicador de foco;
- mensagens de estado traduzíveis.

### Desktop

A interface Desktop utiliza widgets Qt nativos e inclui controles acessíveis para seleção de página e posição da assinatura.

A acessibilidade completa não deve ser presumida apenas pelo código. Recomenda-se validar as duas versões com leitores de tela e navegação exclusivamente por teclado.

---

## 🔎 Verificação das assinaturas

O PDF gerado contém uma assinatura digital PAdES que pode ser inspecionada por softwares e serviços compatíveis com PDF/PAdES e com a cadeia de certificação utilizada.

A indicação de confiança pode depender de fatores como:

- certificado utilizado;
- autoridade certificadora;
- cadeia de confiança;
- política do validador;
- disponibilidade de informações de validação;
- revogação do certificado;
- perfil da assinatura;
- contexto de uso do documento.

A aparência visual presente no PDF **não constitui, por si só, a assinatura criptográfica**.

---

## ⚠️ Aviso legal

Este software executa operações técnicas de assinatura digital, mas não garante automaticamente que toda assinatura produzida terá determinado efeito jurídico.

A validade ou eficácia jurídica pode depender da legislação aplicável, do certificado, da cadeia e política de confiança, da identificação do titular, do contexto de uso e dos requisitos da organização que recebe o documento.

---

# 🇺🇸 English

## 🔏 About the project

**Digital Signer PAdES** is an open-source project for cryptographically signing PDF documents with PKCS#12 digital certificates stored as `.p12` or `.pfx` files.

The project provides two usage modes:

- **Web version:** static HTML/CSS/JavaScript/PDF.js frontend connected to a Flask backend that can be hosted on Render;
- **Desktop version:** a local PySide6 application that does not require a browser and does not need to upload the document, certificate or password to a remote server.

Both versions use **pyHanko** to create **PAdES (PDF Advanced Electronic Signatures)** digital signatures.

> **Important:** the visible appearance placed on the PDF is separate from the cryptographic signature. Images, logos and visual stamps do not replace the digital certificate and do not, by themselves, determine signature validity.

> **We do not recommend the Web version for confidential documents, high-value certificates, or situations requiring the highest possible level of privacy.**
>
> For these cases, prefer the **Desktop version** or run the **Web version locally**. Both options perform the signing process locally on your computer, without requiring the document, certificate, or password to be sent to the project's server.

---

## ✨ Main features

### 🔐 PAdES signatures

- cryptographic PDF signing with `pyHanko`;
- `.p12` and `.pfx` support;
- SHA-256 message digest;
- incremental PDF updates;
- unique signature field identifiers;
- certificate holder name obtained from the certificate;
- CPF removal only from the **visible appearance** when appended to the certificate `Common Name`;
- **240 × 68 PDF point** visible signature field.

### 🎨 Appearance modes

Three visible signature modes are available:

1. **Standard** — uses the Digital Signer's own visual identity;
2. **Simple custom** — allows customized text and visible information;
3. **Custom with image** — allows a logo/side image or a complete signature image.

Accepted custom images:

- PNG;
- JPEG/JPG;
- up to **2 MB**;
- up to **4000 × 4000 pixels**.

The application can automatically determine whether a horizontal image should be treated as a complete signature image or as a logo/side image.

### 📅 Date and time

Date display is enabled by default. Time display is optional and disabled by default.

```text
Date ✓ | Time ✗ → 19/08/2026
Date ✓ | Time ✓ → 19/08/2026 04:25
Date ✗ | Time ✓ → 04:25
Date ✗ | Time ✗ → no temporal information
```

The Web backend timezone can be configured with `APP_TIMEZONE`. The Desktop version currently defaults to `America/Sao_Paulo`, with UTC as fallback.

---

## 🌐 Web version

The Web version uses:

- HTML5;
- CSS3;
- JavaScript;
- locally hosted PDF.js;
- Flask;
- Gunicorn;
- pyHanko;
- ReportLab;
- Pillow;
- Flask-Limiter;
- Redis-compatible shared Rate Limiting storage in production.

### Frontend features

- PDF preview using PDF.js;
- multi-page documents;
- visual signature placement;
- automatic transition to the next page at the end of the scroll;
- Portuguese and English;
- initial language based on browser/system preferences;
- light/dark theme based initially on system preference;
- screen-reader-oriented ARIA attributes, `aria-live` regions, alerts and keyboard navigation;
- Content Security Policy (CSP);
- locally hosted PDF.js;
- backend availability indicator.

### Waking the Render backend

When the page loads, the frontend calls:

```text
GET /api/status
```

This happens in the background while the user selects the PDF and positions the signature. On Render services that sleep after inactivity, this can start the backend before the user reaches the signing step.

The UI can display:

```text
🟡 Starting signing service...
🟢 Signing service available
🔴 Signing service unavailable
```

`/api/status` is exempt from Origin validation and Rate Limiting so it can be used for health checks and service startup.

---

## 💻 Desktop version

The Desktop application is located at:

```text
desktop/local.py
```

It uses **PySide6** for the native GUI and **PyMuPDF** for local PDF rendering.

### Features

- no Flask;
- no browser;
- no Render dependency;
- no GitHub Pages dependency;
- document, certificate, password and image stay on the user's computer;
- high-resolution PDF rendering with internal quality factor `2.5`;
- multi-page navigation;
- automatic next-page transition at the bottom of the scroll;
- visual placement;
- optional accessible placement controls using page and predefined regions;
- toggle to show/hide accessible placement controls;
- Portuguese/English;
- initial system theme detection;
- manually switchable theme using explicit internal state;
- configuration fields that change according to the appearance selected in step 3;
- signing operation executed in a `QThread` to avoid blocking the GUI;
- native file dialogs for PDF, certificate, image and output path;
- suitable as the basis for a future Windows `.exe` build.

### Accessible placement

Users can enable:

```text
☑ Use accessible placement
```

Then select:

```text
Page: 1
Position: Top left
          Top right
          Bottom left
          Bottom right
          Center
```

This complements click-based placement and improves keyboard and assistive-technology use.

> Accessibility should also be tested with real screen readers such as NVDA on Windows. Native Qt widgets and accessible names/descriptions provide a good foundation but do not replace practical testing.

---

## 🛡️ Security and privacy

### Web version

Backend measures include:

- request-size limits;
- PDF, certificate and image limits;
- PDF and image validation;
- image-format restrictions;
- image-resolution limits;
- temporary file cleanup;
- configurable CORS;
- explicit `Origin` validation;
- optional HTTPS enforcement;
- Rate Limiting;
- Redis support for shared limits;
- configurable trusted hosts;
- additional HTTP security headers;
- disabled caching for sensitive responses;
- controlled error handling.

Frontend measures include:

- CSP restrictions;
- locally hosted PDF.js;
- restricted backend connection origins;
- `credentials: "omit"` requests;
- sensitive-field cleanup;
- request timeouts.

> CORS and `Origin` validation restrict ordinary browser use by other sites, but they are not authentication. An external HTTP client can forge the `Origin` header.

### Desktop version

There is no client-server communication in the Desktop version:

```text
PDF + certificate + password
          ↓
      local processing
          ↓
         pyHanko
          ↓
        signed PDF
```

Local protections still include file-size limits, PDF validation, PNG/JPEG validation, image-resolution limits, temporary-file cleanup and short-lived password handling.

---

## 🎓 ICPEdu Personal Certificate

The **[ICPEdu Personal Certificate](https://pessoal.icpedu.rnp.br/)** is a service provided by Brazil's National Research and Education Network (RNP) for eligible users at participating institutions.

ICPEdu personal certificates supplied in PKCS#12 (`.p12`/`.pfx`) format can be used when compatible with the cryptographic infrastructure used by `pyHanko`.

👉 **[Access ICPEdu Personal Certificate](https://pessoal.icpedu.rnp.br/)**

### Visual identity notice

This project uses **its own visual identity** for visible signature appearances.

Using an ICPEdu certificate with this project **does not mean that the document was signed using RNP's official signing application**. References to ICPEdu and RNP identify their respective services and organizations and do not imply affiliation with or endorsement of this project.

---

## 🏗️ Architecture

```text
Digital Signer PAdES
│
├── 🌐 Web version
│   │
│   ├── GitHub Pages / static frontend
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── styles.css
│   │   └── vendor/pdfjs/
│   │
│   └── Render / backend
│       ├── Flask
│       ├── Gunicorn
│       ├── pyHanko
│       ├── ReportLab
│       ├── Pillow
│       └── Flask-Limiter / Redis
│
└── 💻 Desktop version
    ├── PySide6
    ├── PyMuPDF
    ├── pyHanko
    ├── ReportLab
    └── Pillow
```

---

## 📁 Project structure

```text
project/
├── index.html
├── app.js
├── styles.css
├── README.md
├── LICENSE
├── .gitignore
│
├── vendor/
│   └── pdfjs/
│       ├── pdf.min.js
│       └── pdf.worker.min.js
│
├── backend/
│   ├── app.py
│   ├── gunicorn.conf.py
│   └── requirements.txt
│
└── desktop/
    ├── local.py
    └── requirements.txt
```

---

## 📦 Dependencies

### Web backend

`backend/requirements.txt`:

```txt
Flask==3.1.3
Flask-Cors==6.0.5
Flask-Limiter[redis]==3.12
gunicorn==23.0.0
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

### Desktop

`desktop/requirements.txt`:

```txt
PySide6
PyMuPDF
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

PySide6 and PyMuPDF can be pinned after the exact distribution/test combination has been validated.

---

## 🚀 Web development

Clone the repository:

```bash
git clone <REPOSITORY-URL>
cd <REPOSITORY-NAME>
```

Create a virtual environment.

Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the backend from the repository root:

```powershell
python backend/app.py
```

On Windows, use `py backend/app.py` if the `python` command is not available.

Default local endpoint:

```text
http://127.0.0.1:5000
```

Status endpoint:

```text
http://127.0.0.1:5000/api/status
```

Serve the frontend through a local HTTP server, such as VS Code Live Server.

> Opening `index.html` through `file://` may prevent browser features or security policies from working correctly.

---

## 💻 Running the Desktop version

Create a separate environment:

```powershell
py -m venv .venv-desktop
.\.venv-desktop\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r desktop/requirements.txt
```

Check syntax:

```powershell
python -m py_compile desktop/local.py
```

Run:

```powershell
python desktop/local.py
```

Run this command from the repository root, which contains both `desktop` and `backend`. On Windows, use the following command if `python` is not available on `PATH`:

```powershell
py desktop/local.py
```

The Desktop application automatically loads the shared `backend/verifier.py` module. There is no need to copy `verifier.py` into the `desktop` directory.

The Desktop version opens a native window and does not start a web browser or HTTP server.

### Building a Windows `.exe`

PyInstaller can be used as a distribution option. Start with `onedir` while validating Qt plugins and native dependencies:

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm --onefile --windowed --name AssinadorDigital desktop/local.py
```

After validating PySide6, PyMuPDF, pyHanko and other native dependencies, `--onefile` can be evaluated.


## Standalone Version

A standalone Windows version is available through GitHub Releases.

**[⬇️ Download the latest Desktop release](../../releases/latest)**

> The Desktop version processes the PDF, certificate and password locally on your computer and does not require the project's remote backend.

---

## ♿ Accessibility

### Web

The Web UI includes form labels, `aria-live`, `role="alert"`, ARIA descriptions, a skip link, keyboard navigation, visible focus and translated status messages.

### Desktop

The Desktop UI uses native Qt widgets and offers accessible page/position controls in addition to visual click placement.

Accessibility should not be assumed from implementation alone. Both versions should be tested using screen readers and keyboard-only navigation.

---

## 🔎 Signature verification

The resulting PDF contains a PAdES digital signature that can be inspected by software and services compatible with PDF/PAdES and the certificate chain being used.

Trust indications can depend on the certificate, certificate authority, trust chain, validator policy, validation information availability, revocation status, signature profile and document usage context.

The visible appearance **does not constitute the cryptographic signature by itself**.

---

## ⚠️ Legal notice

This software performs technical digital-signature operations but does not automatically guarantee that every resulting signature will have a particular legal effect.

Legal validity or effectiveness may depend on applicable law, the certificate, trust chain and policies, signer identification, usage context and the requirements of the organization receiving the document.

---

## 📄 Licença | License

Este projeto é distribuído sob a **Licença MIT**.

Consulte o arquivo `LICENSE` para mais informações.

This project is distributed under the **MIT License**.

See the `LICENSE` file for more information.

---

Desenvolvido com foco em **segurança, privacidade, acessibilidade e usabilidade**.

Developed with a focus on **security, privacy, accessibility and usability**.
