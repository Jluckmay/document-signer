# 🔏 Assinador Digital PAdES | Digital Signer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![pyHanko](https://img.shields.io/badge/pyHanko-0.36.2-blue.svg)](https://www.pyhanko.eu/)
[![PAdES](https://img.shields.io/badge/Signature-PAdES-green.svg)](https://en.wikipedia.org/wiki/PAdES)

---

## 🇧🇷 Sobre o Projeto

O **Assinador Digital** é uma aplicação web de código aberto para assinatura criptográfica de documentos PDF utilizando certificados digitais em arquivos `.p12` ou `.pfx`.

O backend utiliza o **pyHanko** para produzir assinaturas digitais no padrão **PAdES (PDF Advanced Electronic Signatures)**, enquanto o frontend utiliza **PDF.js** para visualização e posicionamento da assinatura no documento.

O projeto é compatível com certificados PKCS#12, incluindo certificados pessoais **ICPEdu**, certificados **ICP-Brasil** e outros certificados compatíveis com a infraestrutura utilizada pelo `pyHanko`.

> **Importante:** a aparência visual exibida no documento é independente da assinatura criptográfica. Uma imagem, logotipo ou carimbo visual não substitui o certificado digital nem determina, isoladamente, a validade da assinatura.

---

## ✨ Recursos

### 🔐 Assinatura Digital PAdES

- Assinatura criptográfica de documentos PDF utilizando `pyHanko`;
- suporte a certificados `.p12` e `.pfx`;
- algoritmo de resumo SHA-256;
- assinatura no padrão PAdES;
- preservação do PDF por atualização incremental;
- campos de assinatura com identificadores únicos.

### 📄 Visualização e Posicionamento

- Renderização dos documentos utilizando **PDF.js**;
- suporte a documentos com múltiplas páginas;
- posicionamento visual da assinatura diretamente sobre o documento;
- conversão das coordenadas da interface para as coordenadas reais do PDF;
- navegação entre páginas;
- avanço para a próxima página ao chegar ao final da página atual;
- redimensionamento proporcional da visualização conforme o tamanho da janela;
- campo visual da assinatura com dimensões fixas de **240 × 68 pontos PDF**.

### 🎨 Tipos de Aparência da Assinatura

O usuário pode escolher entre três tipos de aparência.

#### 1. Padrão

Utiliza a identidade visual própria do projeto e pode exibir:

- ícone próprio do Assinador Digital;
- nome do titular obtido diretamente do certificado;
- data da assinatura;
- hora da assinatura, opcional;
- indicação de assinatura digital PAdES.

O CPF eventualmente presente no `Common Name` do certificado não é exibido na representação visual.

A remoção do CPF ocorre apenas no carimbo visual e não modifica o certificado ou a assinatura criptográfica.

#### 2. Customizada Simples

Permite personalizar a representação visual da assinatura, incluindo:

- texto/título;
- exibição da data;
- exibição opcional da hora;
- demais informações visuais disponibilizadas pela aplicação.

#### 3. Customizada com Imagem

Permite utilizar uma imagem personalizada como parte da representação visual.

São aceitos:

- PNG;
- JPEG/JPG.

A imagem pode ser interpretada como:

- logotipo ou imagem lateral;
- imagem completa de assinatura.

O sistema pode detectar automaticamente o tipo da imagem com base em suas proporções.

Imagens horizontais podem ser identificadas como assinaturas visuais completas e redimensionadas proporcionalmente para ocupar praticamente toda a caixa disponível.

---

## 🖼️ Imagens Personalizadas

As imagens enviadas pelo usuário:

- são utilizadas somente na representação visual;
- não substituem a assinatura criptográfica;
- não substituem o certificado digital;
- possuem limite de **2 MB**;
- são validadas pelo backend utilizando **Pillow**;
- aceitam PNG e JPEG;
- possuem limite de resolução;
- mantêm sua proporção durante o redimensionamento.

Para imagens detectadas como assinatura completa, o sistema utiliza praticamente toda a área disponível e pode reservar uma pequena faixa inferior para data e/ou hora.

O campo visual permanece com:

```text
240 × 68 pontos PDF
```

---

## 📅 Data e Hora

A exibição da data é habilitada por padrão.

A exibição da hora é opcional e permanece **desmarcada por padrão**.

Exemplos:

```text
Data ✓ | Hora ✗ → 19/08/2026
Data ✓ | Hora ✓ → 19/08/2026 01:42
Data ✗ | Hora ✓ → 01:42
Data ✗ | Hora ✗ → nenhuma informação temporal
```

O timezone padrão do backend é:

```text
America/Sao_Paulo
```

Ele pode ser alterado pela variável de ambiente:

```text
APP_TIMEZONE
```

---

## ♿ Acessibilidade

A interface inclui recursos voltados à acessibilidade, como:

- suporte a leitores de tela;
- regiões `aria-live`;
- labels associados aos campos;
- informações acessíveis sobre as etapas;
- controles com descrições apropriadas;
- navegação por teclado;
- indicação visual de foco;
- informações acessíveis sobre paginação e posicionamento da assinatura.

---

## 🌐 Idiomas

A aplicação possui interface em:

- 🇧🇷 Português;
- 🇺🇸 Inglês.

Na primeira utilização, o idioma é definido automaticamente com base no idioma configurado no navegador/sistema.

O usuário pode alterar manualmente o idioma pelo controle disponível na interface.

A preferência escolhida pode ser armazenada localmente pelo navegador.

---

## 🌓 Tema Claro e Escuro

Por padrão, a aplicação utiliza a preferência de aparência do sistema operacional/navegador.

Dessa forma:

```text
Sistema em modo claro  → tema claro
Sistema em modo escuro → tema escuro
```

O usuário também pode alternar manualmente entre os temas.

A preferência escolhida pode ser armazenada localmente pelo navegador.

---

## 🛡️ Segurança

O projeto implementa diferentes medidas de segurança durante o processamento.

### Backend

- processamento temporário do certificado PKCS#12;
- remoção do arquivo `.p12`/`.pfx` temporário após o carregamento;
- remoção dos arquivos temporários utilizados na geração da aparência;
- limite de tamanho das requisições;
- limite específico para imagens personalizadas;
- validação das imagens utilizando Pillow;
- aceitação apenas de PNG e JPEG;
- limite de resolução das imagens;
- validação do documento PDF;
- validação da página selecionada;
- validação das coordenadas recebidas;
- CORS configurável;
- Rate Limiting por endereço IP;
- geração de identificadores únicos para campos de assinatura;
- tratamento de erros no backend.

### Limites padrão

```text
Requisição: até 30 MB
Imagem personalizada: até 2 MB
Resolução da imagem: até 4000 × 4000 pixels
Rota de assinatura: 5 requisições por minuto por IP
Limite geral: 200 requisições por dia
```

> O armazenamento `memory://` do Flask-Limiter é adequado principalmente para desenvolvimento ou execução em uma única instância. Ambientes distribuídos podem utilizar um armazenamento compartilhado compatível.

---

## 🎓 Certificado Pessoal ICPEdu

O **[ICPEdu - Certificado Pessoal](https://pessoal.icpedu.rnp.br/)** é um serviço disponibilizado pela Rede Nacional de Ensino e Pesquisa (RNP) para usuários elegíveis de instituições participantes.

O certificado pessoal pode ser disponibilizado em formato PKCS#12 (`.p12`/`.pfx`) e pode ser utilizado pelo projeto para realizar a assinatura criptográfica do PDF.

👉 **[Acessar o Certificado Pessoal ICPEdu](https://pessoal.icpedu.rnp.br/)**

### Identidade visual

Este projeto possui **identidade visual própria** para a representação das assinaturas.

O projeto não depende da identidade visual oficial da RNP/ICPEdu para produzir seus carimbos visuais.

O uso de um certificado ICPEdu neste projeto não significa que o documento tenha sido assinado pelo sistema oficial da RNP.

---

## 🏗️ Arquitetura

O projeto é dividido em frontend e backend:

```text
┌─────────────────────────────┐
│          Frontend           │
│                             │
│ HTML + CSS + JavaScript     │
│ PDF.js                      │
│                             │
│ • Visualização do PDF       │
│ • Posicionamento            │
│ • Escolha da aparência      │
│ • Imagens personalizadas    │
│ • Tema e idioma             │
│ • Acessibilidade            │
└──────────────┬──────────────┘
               │
               │ multipart/form-data
               ▼
┌─────────────────────────────┐
│           Backend           │
│                             │
│ Flask                       │
│ pyHanko                     │
│ ReportLab                   │
│ Pillow                      │
│                             │
│ • Validação                 │
│ • Aparência visual          │
│ • Certificado PKCS#12       │
│ • Assinatura PAdES          │
└──────────────┬──────────────┘
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
- pyHanko;
- ReportLab;
- Pillow;
- Gunicorn.

### Frontend

- HTML5;
- CSS3;
- JavaScript;
- PDF.js.

---

## 📦 Dependências

O `requirements.txt` utilizado pelo backend contém:

```txt
Flask==3.1.3
Flask-Cors==6.0.5
Flask-Limiter==3.12
gunicorn==23.0.0
pyHanko==0.36.2
reportlab==5.0.0
Pillow==11.3.0
```

---

## 🚀 Como Executar Localmente

### 1. Clone o repositório

```bash
git clone <URL-DO-REPOSITORIO>
cd <NOME-DO-REPOSITORIO>
```

### 2. Crie um ambiente virtual

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Inicie o backend

```bash
python app.py
```

Por padrão, o servidor será iniciado em:

```text
http://localhost:5000
```

O endpoint de status pode ser acessado em:

```text
http://localhost:5000/api/status
```

### 5. Execute o frontend

O `index.html` deve ser servido por um servidor HTTP local.

Por exemplo, utilizando a extensão **Live Server** do Visual Studio Code:

```text
http://127.0.0.1:5500
```

---

## ⚙️ Variáveis de Ambiente

### `ALLOWED_ORIGIN`

Define a origem autorizada a acessar a API.

Exemplo:

```env
ALLOWED_ORIGIN=https://usuario.github.io
```

### `APP_TIMEZONE`

Define o timezone utilizado para gerar a data e a hora exibidas na assinatura.

Exemplo:

```env
APP_TIMEZONE=America/Sao_Paulo
```

### `RATELIMIT_STORAGE_URI`

Define o armazenamento utilizado pelo Flask-Limiter.

Exemplo para desenvolvimento:

```env
RATELIMIT_STORAGE_URI=memory://
```

---

## ☁️ Implantação

A arquitetura do projeto pode utilizar:

### Frontend

**GitHub Pages**

O frontend pode ser disponibilizado diretamente a partir do `index.html`.

### Backend

**Render**

O backend pode ser executado com Gunicorn:

```bash
gunicorn app:app
```

A URL de produção correspondente deve ser configurada no frontend.

---

## 🌐 Ícone da Aplicação

A aplicação utiliza o mesmo símbolo da identidade visual da assinatura padrão como ícone da aba do navegador.

Não é necessário manter um arquivo `favicon.svg` separado caso o ícone seja incorporado diretamente no HTML através de um SVG em Data URL.

Exemplo no `<head>` do `index.html`:

```html
<link
    rel="icon"
    type="image/svg+xml"
    href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='28' fill='%232563EB'/%3E%3Cpath d='M18 32 L27 41 L47 20' fill='none' stroke='white' stroke-width='6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"
>
```

---

## 🔎 Verificação das Assinaturas

A assinatura digital pode ser analisada por softwares e serviços compatíveis com PDF/PAdES e com a cadeia de certificação utilizada.

A indicação de confiança pode variar conforme fatores como:

- certificado utilizado;
- autoridade certificadora;
- cadeia de confiança;
- política do validador;
- estado de revogação do certificado;
- perfil da assinatura;
- contexto em que o documento é utilizado.

A representação visual presente no PDF não constitui, por si só, a assinatura criptográfica.

---

## ⚠️ Aviso

Este software realiza operações técnicas de assinatura digital, mas não garante automaticamente que toda assinatura produzida terá determinado efeito jurídico.

A validade ou eficácia jurídica pode depender da legislação aplicável, do certificado utilizado, da identificação do titular, das políticas de confiança e do contexto de uso.

---

# 🇺🇸 Digital Signer

## About the Project

**Digital Signer** is an open-source web application for cryptographically signing PDF documents using `.p12` or `.pfx` digital certificates.

The backend uses **pyHanko** to produce **PAdES (PDF Advanced Electronic Signatures)** signatures, while the frontend uses **PDF.js** to display PDF documents and allow visual signature placement.

The application supports compatible PKCS#12 certificates, including ICPEdu personal certificates, ICP-Brasil certificates and other certificates supported by the underlying cryptographic infrastructure.

> **Important:** the visible signature appearance is separate from the cryptographic signature. An image, logo or visual stamp does not replace the digital certificate.

---

## ✨ Features

### 🔐 PAdES Digital Signatures

- PDF cryptographic signing using `pyHanko`;
- `.p12` and `.pfx` certificate support;
- SHA-256 message digest;
- PAdES signature format;
- incremental PDF updates;
- unique signature fields.

### 📄 PDF Preview and Placement

- PDF rendering using PDF.js;
- multi-page document support;
- visual signature positioning;
- coordinate conversion between the interface and PDF;
- page navigation;
- automatic navigation when reaching the end of the current page;
- responsive PDF scaling.

### 🎨 Signature Appearance

Three appearance modes are available:

1. **Standard**
   - built-in project identity;
   - certificate holder name;
   - date;
   - optional time;
   - PAdES indication.

2. **Simple Custom**
   - customizable text;
   - optional date;
   - optional time;
   - configurable visual information.

3. **Custom with Image**
   - PNG/JPEG images;
   - logo mode;
   - full-signature-image mode;
   - automatic image-type detection.

The visual signature field remains:

```text
240 × 68 PDF points
```

---

## 🖼️ Custom Images

Uploaded images:

- are used only for visual appearance;
- do not replace the cryptographic signature;
- are limited to 2 MB;
- are validated using Pillow;
- support PNG and JPEG;
- preserve their original aspect ratio.

Horizontal images can automatically be detected as complete signature artwork and scaled to use most of the available signature area.

---

## 📅 Date and Time

The signature date is enabled by default.

The time is optional and **disabled by default**.

```text
Date ✓ | Time ✗ → 19/08/2026
Date ✓ | Time ✓ → 19/08/2026 01:42
Date ✗ | Time ✓ → 01:42
Date ✗ | Time ✗ → hidden
```

---

## ♿ Accessibility

The frontend includes support for:

- screen readers;
- ARIA live regions;
- associated labels;
- keyboard navigation;
- visible keyboard focus;
- accessible page navigation;
- step announcements;
- signature-position information.

---

## 🌐 Language

The application supports:

- Portuguese;
- English.

The initial language follows the browser/system language.

Users can manually switch languages, and their preference may be stored locally.

---

## 🌓 Appearance

The initial light/dark mode follows the operating system or browser preference.

Users can manually switch themes, and their preference may be stored locally.

---

## 🎓 About ICPEdu

The **[ICPEdu Personal Certificate](https://pessoal.icpedu.rnp.br/)** is a service provided by Brazil's National Research and Education Network (RNP) for eligible members of participating institutions.

Compatible ICPEdu PKCS#12 certificates can be used by this project to cryptographically sign PDF documents.

👉 **[Access ICPEdu Personal Certificate](https://pessoal.icpedu.rnp.br/)**

### Visual Identity Notice

This project uses its **own visual identity** for signature appearances.

Using an ICPEdu certificate with this project does not mean that the document was signed by RNP's official signing application.

---

## 🚀 Local Development

Clone the repository and create a virtual environment:

```bash
git clone <REPOSITORY-URL>
cd <REPOSITORY-NAME>
python -m venv .venv
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python app.py
```

Backend:

```text
http://localhost:5000
```

Health endpoint:

```text
http://localhost:5000/api/status
```

Serve the frontend through a local HTTP server, such as VS Code Live Server.

---

## ☁️ Deployment

### Frontend

GitHub Pages.

### Backend

Render using Gunicorn:

```bash
gunicorn app:app
```

---

## 📄 License

This project is distributed under the **MIT License**.

See the `LICENSE` file for more information.

---

Developed with a focus on **security, accessibility, privacy and usability**.