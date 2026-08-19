# 🔏 Assinador Digital PAdES | Digital Signer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![pyHanko](https://img.shields.io/badge/pyHanko-0.36.2-blue.svg)](https://www.pyhanko.eu/)
[![PAdES](https://img.shields.io/badge/Signature-PAdES-green.svg)](https://en.wikipedia.org/wiki/PAdES)

**[🇧🇷 Português](#-sobre-o-projeto) | [🇺🇸 English](#-about-the-project)**

---

# 🇧🇷 Português

## 🔏 Sobre o Projeto

O **Assinador Digital PAdES** é uma aplicação web de código aberto para assinatura criptográfica de documentos PDF utilizando certificados digitais em arquivos `.p12` ou `.pfx`.

O backend utiliza **Flask** e **pyHanko** para produzir assinaturas digitais no padrão **PAdES (PDF Advanced Electronic Signatures)**. O frontend utiliza **PDF.js** para renderização do documento, navegação entre páginas e posicionamento visual da assinatura.

A aplicação é compatível com certificados PKCS#12 suportados pela infraestrutura criptográfica utilizada pelo `pyHanko`, incluindo certificados pessoais **ICPEdu**, certificados **ICP-Brasil** e outros certificados compatíveis.

> **Importante:** a representação visual presente no documento é independente da assinatura criptográfica. Imagens, logotipos e carimbos visuais não substituem o certificado digital nem determinam, isoladamente, a validade da assinatura.

---

## ✨ Recursos

### 🔐 Assinatura Digital PAdES

- assinatura criptográfica de documentos PDF utilizando `pyHanko`;
- suporte a certificados `.p12` e `.pfx`;
- algoritmo de resumo SHA-256;
- assinatura no padrão PAdES;
- preservação do documento por atualização incremental;
- campos de assinatura com identificadores únicos;
- nome do titular obtido diretamente do certificado;
- remoção do CPF da representação visual quando presente no `Common Name`.

A remoção do CPF ocorre **somente na representação visual** e não modifica o certificado, seus atributos ou a assinatura criptográfica.

### 📄 Visualização e Posicionamento

- renderização de PDFs utilizando **PDF.js**;
- PDF.js hospedado junto à aplicação, sem dependência de CDN para sua execução;
- suporte a documentos com múltiplas páginas;
- posicionamento da assinatura diretamente sobre o documento;
- conversão das coordenadas da interface para coordenadas reais do PDF;
- navegação entre páginas;
- avanço para a próxima página ao chegar ao final da página atual;
- redimensionamento proporcional da visualização;
- manutenção da proporção original das páginas;
- campo visual da assinatura com dimensões de **240 × 68 pontos PDF**.

---

## 🎨 Tipos de Aparência da Assinatura

A aplicação oferece três opções de representação visual.

### 1. Padrão

Utiliza a identidade visual própria do **Assinador Digital**.

Pode exibir:

- ícone próprio do projeto;
- nome do titular do certificado;
- data da assinatura;
- hora da assinatura, opcional;
- indicação de assinatura digital PAdES.

### 2. Customizada Simples

Permite personalizar a representação visual sem utilizar uma imagem completa.

Pode incluir:

- título personalizado;
- nome do titular;
- data;
- hora opcional;
- indicação de assinatura digital PAdES.

### 3. Customizada com Imagem

Permite utilizar uma imagem personalizada na representação visual.

Formatos aceitos:

- PNG;
- JPEG/JPG.

A imagem pode ser utilizada como:

- logotipo ou imagem lateral;
- imagem completa de assinatura.

O sistema também pode detectar automaticamente o modo mais adequado com base nas características e proporções da imagem.

Imagens horizontais compatíveis com o formato de uma assinatura completa podem ser redimensionadas proporcionalmente para ocupar praticamente toda a área disponível.

---

## 🖼️ Imagens Personalizadas

As imagens enviadas pelo usuário:

- são utilizadas somente na representação visual;
- não substituem a assinatura criptográfica;
- não substituem o certificado digital;
- possuem limite de **2 MB**;
- são validadas pelo backend utilizando **Pillow**;
- aceitam apenas os formatos permitidos pela aplicação;
- possuem limite de resolução;
- mantêm sua proporção durante o redimensionamento.

Para uma imagem tratada como assinatura completa, a aplicação pode utilizar praticamente toda a área disponível, reservando espaço para as informações temporais quando necessário.

O campo visual permanece com:

```text
240 × 68 pontos PDF
```

---

## 📅 Data e Hora

A exibição da **data** é habilitada por padrão.

A exibição da **hora** é opcional e permanece **desmarcada por padrão**.

Exemplos:

```text
Data ✓ | Hora ✗ → 19/08/2026
Data ✓ | Hora ✓ → 19/08/2026 02:00
Data ✗ | Hora ✓ → 02:00
Data ✗ | Hora ✗ → nenhuma informação temporal
```

O timezone padrão do backend é:

```text
America/Sao_Paulo
```

Ele pode ser alterado por meio da variável:

```env
APP_TIMEZONE
```

---

## 🌐 Interface Bilíngue

A interface possui suporte a:

- 🇧🇷 Português;
- 🇺🇸 Inglês.

Na primeira utilização, a aplicação utiliza o idioma configurado no navegador/sistema para determinar o idioma inicial.

O usuário pode alterar manualmente o idioma utilizando o controle disponível na interface.

A preferência escolhida pode ser armazenada localmente pelo navegador.

Além dos textos visíveis, a internacionalização também pode ser aplicada às informações de acessibilidade, como:

- descrições ARIA;
- paginação;
- mensagens de status;
- mensagens de erro;
- descrição das etapas;
- controles de navegação.

---

## 🌓 Tema Claro e Escuro

Por padrão, a aplicação segue a preferência de aparência do sistema operacional/navegador:

```text
Sistema em modo claro  → tema claro
Sistema em modo escuro → tema escuro
```

O usuário também pode alterar manualmente o tema.

A preferência selecionada pode ser armazenada localmente pelo navegador.

---

## ♿ Acessibilidade

A interface inclui recursos de acessibilidade, como:

- suporte a leitores de tela;
- regiões `aria-live`;
- mensagens com `role="alert"`;
- labels associados aos campos;
- descrições ARIA;
- informações acessíveis sobre as etapas;
- navegação por teclado;
- indicação visual de foco;
- link para pular diretamente ao conteúdo principal;
- informações acessíveis de paginação;
- descrição da área de visualização do PDF;
- anúncios de mudanças relevantes da interface.

---

## 🛡️ Segurança e Privacidade

O projeto utiliza diferentes camadas de proteção no frontend e no backend.

### Backend

Entre as medidas implementadas estão:

- processamento controlado de certificados PKCS#12;
- utilização temporária do arquivo `.p12`/`.pfx`;
- remoção do certificado temporário após o carregamento;
- remoção dos arquivos temporários utilizados para gerar a aparência;
- limite de tamanho das requisições;
- limite específico para imagens;
- validação de imagens com Pillow;
- restrição dos formatos de imagem;
- limite de resolução;
- validação do documento PDF;
- validação da página selecionada;
- validação das coordenadas;
- CORS configurável;
- verificação da origem das requisições;
- possibilidade de exigir HTTPS em produção;
- Rate Limiting;
- suporte a Redis para armazenamento compartilhado dos limites;
- identificadores únicos para campos de assinatura;
- tratamento controlado de erros;
- headers HTTP adicionais de segurança.

### Frontend

O frontend também adota medidas como:

- **Content Security Policy (CSP)**;
- PDF.js hospedado localmente;
- restrição das origens permitidas para comunicação com o backend;
- ausência de envio do certificado para serviços de terceiros pelo fluxo normal da aplicação;
- limpeza dos campos sensíveis quando necessário;
- timeout das requisições;
- validações antes do envio.

### Limites padrão

```text
Requisição: até 30 MB
Imagem personalizada: até 2 MB
Resolução da imagem: até 4000 × 4000 pixels
Rota de assinatura: 5 requisições por minuto por IP
Limite geral: 200 requisições por dia
```

> Para produção com múltiplos processos ou instâncias, recomenda-se utilizar um armazenamento compartilhado para o Rate Limiting, como Redis, em vez de `memory://`.

### Senha do certificado

A senha do certificado é necessária para desbloquear a chave privada contida no arquivo PKCS#12 durante o processo de assinatura.

A aplicação deve ser publicada exclusivamente através de **HTTPS** em produção para proteger a comunicação entre cliente e servidor.

---

## 🎓 Certificado Pessoal ICPEdu

O **[ICPEdu - Certificado Pessoal](https://pessoal.icpedu.rnp.br/)** é um serviço disponibilizado pela Rede Nacional de Ensino e Pesquisa (RNP) para usuários elegíveis de instituições participantes.

Certificados pessoais ICPEdu disponibilizados em formato PKCS#12 (`.p12`/`.pfx`) podem ser utilizados pelo projeto quando compatíveis com a infraestrutura criptográfica utilizada.

👉 **[Acessar o Certificado Pessoal ICPEdu](https://pessoal.icpedu.rnp.br/)**

### Aviso sobre identidade visual

Este projeto utiliza **identidade visual própria** para a representação das assinaturas.

O projeto não depende da identidade visual oficial da RNP/ICPEdu para gerar seus carimbos.

Utilizar um certificado ICPEdu neste projeto **não significa que o documento tenha sido assinado pelo sistema oficial da RNP**.

ICPEdu e RNP são referências aos respectivos serviços e organizações e não indicam afiliação ou endosso deste projeto.

---

## 🏗️ Arquitetura

```text
┌──────────────────────────────────┐
│             Frontend             │
│                                  │
│ HTML + CSS + JavaScript          │
│ PDF.js local                     │
│                                  │
│ • Visualização do PDF            │
│ • Posicionamento                 │
│ • Navegação entre páginas        │
│ • Escolha da aparência           │
│ • Imagens personalizadas         │
│ • Tema claro/escuro              │
│ • Português/Inglês               │
│ • Acessibilidade                 │
└────────────────┬─────────────────┘
                 │
                 │ HTTPS
                 │ multipart/form-data
                 ▼
┌──────────────────────────────────┐
│              Backend             │
│                                  │
│ Gunicorn                         │
│ Flask                            │
│ pyHanko                          │
│ ReportLab                        │
│ Pillow                           │
│ Flask-Limiter / Redis            │
│                                  │
│ • Validação                      │
│ • Certificado PKCS#12            │
│ • Aparência visual               │
│ • Assinatura PAdES               │
└────────────────┬─────────────────┘
                 │
                 ▼
          PDF assinado
```

---

## 🧰 Tecnologias

### Backend

- Python;
- Flask;
- Flask-Cors;
- Flask-Limiter;
- Redis;
- pyHanko;
- ReportLab;
- Pillow;
- Gunicorn.

### Frontend

- HTML5;
- CSS3;
- JavaScript;
- PDF.js.

### Implantação

- GitHub Pages — frontend;
- Render — backend;
- Redis — armazenamento compartilhado para Rate Limiting em produção.

---

## 📁 Estrutura do Projeto

```text
projeto/
├── app.py
├── gunicorn.conf.py
├── requirements.txt
├── index.html
├── app.js
├── styles.css
├── README.md
├── LICENSE
└── vendor/
    └── pdfjs/
        ├── pdf.min.js
        └── pdf.worker.min.js
```

O PDF.js é armazenado junto ao frontend para evitar a necessidade de carregar o código da biblioteca diretamente de uma CDN durante o uso da aplicação.

---

## 📦 Dependências

O backend utiliza:

```txt
Flask==3.1.3
Flask-Cors==6.0.5
Flask-Limiter[redis]==3.12
gunicorn==23.0.0
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

Instale utilizando:

```bash
pip install -r requirements.txt
```

---

## 🚀 Executando Localmente

### 1. Clone o repositório

```bash
git clone <URL-DO-REPOSITORIO>
cd <NOME-DO-REPOSITORIO>
```

### 2. Crie um ambiente virtual

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Inicie o backend

Para desenvolvimento:

```bash
python app.py
```

O backend será disponibilizado, por padrão, em:

```text
http://localhost:5000
```

Status:

```text
http://localhost:5000/api/status
```

### 5. Inicie o frontend

O frontend deve ser servido através de um servidor HTTP local.

Por exemplo, utilizando **Live Server** no Visual Studio Code:

```text
http://127.0.0.1:5500
```

> Abrir o `index.html` diretamente através de `file://` pode impedir o funcionamento correto de alguns recursos do navegador e das políticas de segurança.

---

## ⚙️ Variáveis de Ambiente

### `APP_ENV`

Define o ambiente da aplicação.

Produção:

```env
APP_ENV=production
```

### `ALLOWED_ORIGIN`

Define a origem autorizada a utilizar a API.

Exemplo:

```env
ALLOWED_ORIGIN=https://SEU-USUARIO.github.io
```

### `APP_TIMEZONE`

Define o timezone utilizado para data e hora.

```env
APP_TIMEZONE=America/Sao_Paulo
```

### `ENFORCE_HTTPS`

Permite exigir HTTPS.

Produção:

```env
ENFORCE_HTTPS=true
```

### `REQUIRE_ORIGIN`

Permite exigir uma origem HTTP autorizada nas rotas protegidas.

Produção:

```env
REQUIRE_ORIGIN=true
```

### `TRUSTED_HOSTS`

Define os hosts aceitos pela aplicação, quando suportado/configurado pelo backend.

Exemplo:

```env
TRUSTED_HOSTS=seu-backend.onrender.com
```

### `RATELIMIT_STORAGE_URI`

Define o armazenamento do Flask-Limiter.

Desenvolvimento:

```env
RATELIMIT_STORAGE_URI=memory://
```

Produção com Redis:

```env
RATELIMIT_STORAGE_URI=redis://...
```

> Não publique credenciais Redis no repositório. Configure a URI como variável de ambiente no serviço de hospedagem.

---

## 🦄 Gunicorn

Em produção, o Flask deve ser executado através de um servidor WSGI adequado.

O projeto possui:

```text
gunicorn.conf.py
```

No Render, o comando de inicialização pode ser:

```bash
gunicorn -c gunicorn.conf.py app:app
```

O arquivo centraliza configurações de execução do Gunicorn, como workers, threads, timeouts e logs.

Para desenvolvimento local, continue utilizando:

```bash
python app.py
```

---

## ☁️ Implantação

### Frontend — GitHub Pages

Antes da publicação:

1. configure a URL real do backend no frontend;
2. autorize essa URL na diretiva `connect-src` da CSP;
3. mantenha o PDF.js local;
4. confirme que os caminhos dos arquivos estáticos estão corretos.

### Backend — Render

Configure o serviço para instalar:

```bash
pip install -r requirements.txt
```

E iniciar:

```bash
gunicorn -c gunicorn.conf.py app:app
```

Health Check:

```text
/api/status
```

Configure também as variáveis de ambiente de produção.

### Redis

Em produção, Redis pode ser utilizado pelo Flask-Limiter para compartilhar o estado dos limites entre diferentes workers ou instâncias.

Configure a conexão exclusivamente por variável de ambiente.

---

## 🌐 Ícone da Aplicação

A aplicação utiliza o símbolo da identidade visual própria da assinatura padrão como favicon.

O ícone pode ser incorporado diretamente ao `index.html` como SVG através de uma Data URL.

Portanto, **não é obrigatório criar arquivos separados como `favicon.svg` ou `flaticon.svg`**.

---

## 🔎 Verificação das Assinaturas

O PDF resultante contém uma assinatura digital PAdES que pode ser analisada por softwares e serviços compatíveis com PDF/PAdES e com a cadeia de certificação utilizada.

A indicação de validade ou confiança pode depender de fatores como:

- certificado utilizado;
- autoridade certificadora;
- cadeia de confiança;
- política do validador;
- disponibilidade das informações de validação;
- estado de revogação;
- perfil da assinatura;
- contexto de utilização do documento.

A representação visual presente no PDF **não constitui, por si só, a assinatura criptográfica**.

---

## ⚠️ Aviso Legal

Este software executa operações técnicas de assinatura digital, mas não garante automaticamente que toda assinatura produzida terá determinado efeito jurídico.

A validade ou eficácia jurídica pode depender, entre outros fatores, de:

- legislação aplicável;
- certificado utilizado;
- identificação do titular;
- cadeia e política de confiança;
- forma de assinatura;
- contexto de utilização;
- requisitos da organização que recebe o documento.

---

# 🇺🇸 English

## 🔏 About the Project

**Digital Signer PAdES** is an open-source web application for cryptographically signing PDF documents using `.p12` or `.pfx` digital certificates.

The backend uses **Flask** and **pyHanko** to produce **PAdES (PDF Advanced Electronic Signatures)** digital signatures. The frontend uses **PDF.js** to render documents, navigate between pages and visually position the signature.

The application supports PKCS#12 certificates compatible with the cryptographic infrastructure used by `pyHanko`, including **ICPEdu** personal certificates, **ICP-Brasil** certificates and other compatible certificates.

> **Important:** the visible appearance placed on the document is separate from the cryptographic signature. Images, logos and visual stamps do not replace the digital certificate and do not, by themselves, determine whether a signature is valid.

---

## ✨ Features

### 🔐 PAdES Digital Signatures

- cryptographic PDF signing using `pyHanko`;
- `.p12` and `.pfx` certificate support;
- SHA-256 message digest;
- PAdES signature format;
- incremental PDF updates;
- unique signature field identifiers;
- certificate holder name obtained from the certificate;
- removal of a CPF number from the visual appearance when included in the certificate's `Common Name`.

CPF removal affects **only the visual appearance**. It does not modify the certificate, its attributes or the cryptographic signature.

### 📄 PDF Preview and Placement

- PDF rendering using **PDF.js**;
- PDF.js hosted with the application instead of being loaded from a CDN at runtime;
- multi-page document support;
- visual signature placement directly over the document;
- conversion between interface coordinates and actual PDF coordinates;
- page navigation;
- automatic transition to the next page when reaching the end of the current page;
- responsive document scaling;
- preservation of the original page aspect ratio;
- **240 × 68 PDF point** visual signature field.

---

## 🎨 Signature Appearance Modes

The application provides three visual appearance modes.

### 1. Standard

Uses the **Digital Signer** project's own visual identity.

It may display:

- the project's own icon;
- certificate holder name;
- signing date;
- optional signing time;
- PAdES digital signature indication.

### 2. Simple Custom

Allows customization without using a complete signature image.

It may include:

- custom title;
- certificate holder name;
- date;
- optional time;
- PAdES digital signature indication.

### 3. Custom with Image

Allows a custom image to be included in the visible signature appearance.

Supported formats:

- PNG;
- JPEG/JPG.

The image can be treated as:

- a logo or side image;
- a complete signature image.

The application can also automatically determine the most appropriate mode based on the image characteristics and proportions.

Compatible horizontal images may be interpreted as complete signature artwork and proportionally scaled to use most of the available area.

---

## 🖼️ Custom Images

Images uploaded by the user:

- are used only for the visual appearance;
- do not replace the cryptographic signature;
- do not replace the digital certificate;
- are limited to **2 MB**;
- are validated by the backend using **Pillow**;
- are restricted to the image formats accepted by the application;
- have a resolution limit;
- preserve their aspect ratio when resized.

For a complete signature image, the application can use most of the available area while reserving space for date/time information when necessary.

The visual field remains:

```text
240 × 68 PDF points
```

---

## 📅 Date and Time

The **date** is enabled by default.

The **time** is optional and **disabled by default**.

Examples:

```text
Date ✓ | Time ✗ → 19/08/2026
Date ✓ | Time ✓ → 19/08/2026 02:00
Date ✗ | Time ✓ → 02:00
Date ✗ | Time ✗ → no temporal information
```

The backend's default timezone is:

```text
America/Sao_Paulo
```

It can be changed using:

```env
APP_TIMEZONE
```

---

## 🌐 Bilingual Interface

The interface supports:

- 🇧🇷 Portuguese;
- 🇺🇸 English.

On first use, the application determines the initial language from the browser/system language.

Users can manually switch languages using the control available in the interface.

The selected preference may be stored locally by the browser.

Internationalization can also cover accessibility information, including:

- ARIA descriptions;
- pagination;
- status messages;
- error messages;
- step descriptions;
- navigation controls.

---

## 🌓 Light and Dark Themes

By default, the application follows the operating system/browser appearance preference:

```text
Light system theme → light application theme
Dark system theme  → dark application theme
```

Users can manually switch between themes.

The selected preference may be stored locally by the browser.

---

## ♿ Accessibility

The interface includes accessibility features such as:

- screen reader support;
- `aria-live` regions;
- `role="alert"` messages;
- properly associated form labels;
- ARIA descriptions;
- accessible step information;
- keyboard navigation;
- visible keyboard focus;
- skip-to-main-content link;
- accessible pagination information;
- accessible PDF preview descriptions;
- announcements for relevant interface changes.

---

## 🛡️ Security and Privacy

The project uses several security measures on both the frontend and backend.

### Backend

Measures include:

- controlled PKCS#12 certificate processing;
- temporary `.p12`/`.pfx` file handling;
- removal of temporary certificate files after loading;
- cleanup of temporary visual-appearance files;
- request-size limits;
- custom image-size limits;
- image validation using Pillow;
- image-format restrictions;
- image-resolution limits;
- PDF validation;
- selected-page validation;
- coordinate validation;
- configurable CORS;
- request-origin validation;
- optional HTTPS enforcement in production;
- Rate Limiting;
- Redis support for shared Rate Limiting storage;
- unique signature-field identifiers;
- controlled error handling;
- additional HTTP security headers.

### Frontend

Frontend security measures include:

- **Content Security Policy (CSP)**;
- locally hosted PDF.js;
- restricted backend connection origins;
- no third-party certificate upload in the application's normal workflow;
- cleanup of sensitive fields when appropriate;
- request timeout;
- validation before data is submitted.

### Default Limits

```text
Request: up to 30 MB
Custom image: up to 2 MB
Image resolution: up to 4000 × 4000 pixels
Signing endpoint: 5 requests per minute per IP
General limit: 200 requests per day
```

> For production environments using multiple processes or instances, a shared Rate Limiting storage such as Redis is recommended instead of `memory://`.

### Certificate Password

The certificate password is required to unlock the private key contained in the PKCS#12 file during the signing process.

The application should be deployed exclusively through **HTTPS** in production to protect communication between the client and server.

---

## 🎓 ICPEdu Personal Certificate

The **[ICPEdu Personal Certificate](https://pessoal.icpedu.rnp.br/)** is a service provided by Brazil's National Research and Education Network (RNP) for eligible users at participating institutions.

ICPEdu personal certificates provided in PKCS#12 (`.p12`/`.pfx`) format can be used by this project when compatible with the underlying cryptographic infrastructure.

👉 **[Access ICPEdu Personal Certificate](https://pessoal.icpedu.rnp.br/)**

### Visual Identity Notice

This project uses **its own visual identity** for visible signature appearances.

The project does not depend on RNP/ICPEdu's official visual identity to generate its visual stamps.

Using an ICPEdu certificate with this project **does not mean the document was signed using RNP's official signing application**.

ICPEdu and RNP references identify their respective services and organizations and do not imply affiliation with or endorsement of this project.

---

## 🏗️ Architecture

```text
┌──────────────────────────────────┐
│             Frontend             │
│                                  │
│ HTML + CSS + JavaScript          │
│ Local PDF.js                     │
│                                  │
│ • PDF preview                    │
│ • Signature placement            │
│ • Page navigation                │
│ • Appearance selection           │
│ • Custom images                  │
│ • Light/dark themes              │
│ • Portuguese/English             │
│ • Accessibility                  │
└────────────────┬─────────────────┘
                 │
                 │ HTTPS
                 │ multipart/form-data
                 ▼
┌──────────────────────────────────┐
│              Backend             │
│                                  │
│ Gunicorn                         │
│ Flask                            │
│ pyHanko                          │
│ ReportLab                        │
│ Pillow                           │
│ Flask-Limiter / Redis            │
│                                  │
│ • Validation                     │
│ • PKCS#12 certificate            │
│ • Visual appearance              │
│ • PAdES signature                │
└────────────────┬─────────────────┘
                 │
                 ▼
            Signed PDF
```

---

## 🧰 Technologies

### Backend

- Python;
- Flask;
- Flask-Cors;
- Flask-Limiter;
- Redis;
- pyHanko;
- ReportLab;
- Pillow;
- Gunicorn.

### Frontend

- HTML5;
- CSS3;
- JavaScript;
- PDF.js.

### Deployment

- GitHub Pages — frontend;
- Render — backend;
- Redis — shared production Rate Limiting storage.

---

## 📁 Project Structure

```text
project/
├── app.py
├── gunicorn.conf.py
├── requirements.txt
├── index.html
├── app.js
├── styles.css
├── README.md
├── LICENSE
└── vendor/
    └── pdfjs/
        ├── pdf.min.js
        └── pdf.worker.min.js
```

PDF.js is stored with the frontend so the library does not need to be loaded directly from a CDN while the application is being used.

---

## 📦 Dependencies

The backend uses:

```txt
Flask==3.1.3
Flask-Cors==6.0.5
Flask-Limiter[redis]==3.12
gunicorn==23.0.0
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## 🚀 Local Development

### 1. Clone the repository

```bash
git clone <REPOSITORY-URL>
cd <REPOSITORY-NAME>
```

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the backend

For development:

```bash
python app.py
```

By default:

```text
http://localhost:5000
```

Health endpoint:

```text
http://localhost:5000/api/status
```

### 5. Start the frontend

Serve the frontend through a local HTTP server.

For example, using **Live Server** in Visual Studio Code:

```text
http://127.0.0.1:5500
```

> Opening `index.html` directly through `file://` may prevent some browser and security features from working correctly.

---

## ⚙️ Environment Variables

### `APP_ENV`

Sets the application environment:

```env
APP_ENV=production
```

### `ALLOWED_ORIGIN`

Sets the frontend origin authorized to access the API:

```env
ALLOWED_ORIGIN=https://YOUR-USERNAME.github.io
```

### `APP_TIMEZONE`

Sets the timezone used for signature date/time information:

```env
APP_TIMEZONE=America/Sao_Paulo
```

### `ENFORCE_HTTPS`

Enables HTTPS enforcement:

```env
ENFORCE_HTTPS=true
```

### `REQUIRE_ORIGIN`

Enables origin validation on protected routes:

```env
REQUIRE_ORIGIN=true
```

### `TRUSTED_HOSTS`

Defines accepted hosts when supported/configured by the backend:

```env
TRUSTED_HOSTS=your-backend.onrender.com
```

### `RATELIMIT_STORAGE_URI`

Development:

```env
RATELIMIT_STORAGE_URI=memory://
```

Production with Redis:

```env
RATELIMIT_STORAGE_URI=redis://...
```

> Never commit Redis credentials to the repository. Store the connection URI as a deployment environment variable.

---

## 🦄 Gunicorn

Production should use a suitable WSGI server rather than Flask's development server.

The project includes:

```text
gunicorn.conf.py
```

On Render, the start command can be:

```bash
gunicorn -c gunicorn.conf.py app:app
```

The configuration file centralizes Gunicorn settings such as workers, threads, timeouts and logging.

For local development, continue using:

```bash
python app.py
```

---

## ☁️ Deployment

### Frontend — GitHub Pages

Before deployment:

1. configure the real backend URL in the frontend;
2. allow the backend URL in the CSP `connect-src` directive;
3. keep PDF.js locally hosted;
4. verify static file paths.

### Backend — Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn -c gunicorn.conf.py app:app
```

Health Check:

```text
/api/status
```

Configure the required production environment variables in Render.

### Redis

Redis can be used by Flask-Limiter to share Rate Limiting state between workers or instances.

Configure the Redis connection exclusively through an environment variable.

---

## 🌐 Application Icon

The application uses the symbol from its own standard signature visual identity as the browser favicon.

The icon can be embedded directly in `index.html` as an SVG Data URL.

Therefore, separate `favicon.svg` or `flaticon.svg` files are **not required**.

---

## 🔎 Signature Verification

The resulting PDF contains a PAdES digital signature that can be inspected using software and services compatible with PDF/PAdES and the certificate chain being used.

Trust or validity indications can depend on factors such as:

- certificate;
- certificate authority;
- trust chain;
- validator policy;
- availability of validation information;
- certificate revocation status;
- signature profile;
- document usage context.

The visible appearance in the PDF **does not constitute the cryptographic signature by itself**.

---

## ⚠️ Legal Notice

This software performs technical digital-signature operations but does not automatically guarantee that every resulting signature will have a particular legal effect.

Legal validity or effectiveness may depend on factors including:

- applicable law;
- certificate used;
- signer identification;
- trust chain and policies;
- signing method;
- usage context;
- requirements of the organization receiving the document.

---

## 📄 Licença | License

Este projeto é distribuído sob a **Licença MIT**.

Consulte o arquivo `LICENSE` para mais informações.

This project is distributed under the **MIT License**.

See the `LICENSE` file for more information.

---

Desenvolvido com foco em **segurança, privacidade, acessibilidade e usabilidade**.

Developed with a focus on **security, privacy, accessibility and usability**.