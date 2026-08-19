# 🔏 Assinador Digital PAdES | Digital Signer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)

---

### 🎓 Sobre o Certificado ICPEdu (RNP)
O **[ICPEdu - Certificado Pessoal](https://pessoal.icpedu.rnp.br/)** é um serviço da Rede Nacional de Ensino e Pesquisa (RNP) que emite certificados digitais gratuitos para alunos, professores e servidores das instituições participantes da CAFe. Essa identidade virtual em formato de arquivo `.p12` ou `.pfx` permite assinar documentos, cifrar dados e se autenticar em sistemas com garantia de autoria e integridade. 

👉 **[Clique aqui para emitir o seu certificado pessoal na ICPEdu](https://pessoal.icpedu.rnp.br/)**

## 🇧🇷 Sobre o Projeto

O **Assinador Digital** é uma aplicação web de código aberto projetada para assinar documentos PDF criptograficamente utilizando certificados digitais `.p12` / `.pfx` (como os fornecidos pela ICPEdu/RNP ou ICP-Brasil). 

O projeto adota o padrão **PAdES** (PDF Advanced Electronic Signatures), garantindo validade técnica e legal reconhecida por validadores oficiais (ITI, Portal Gov.br, Adobe Acrobat). 

### ✨ Recursos
* **Assinatura PAdES Válida:** Implementada usando a biblioteca `pyHanko`.
* **Posicionamento Visual:** Integração com `PDF.js` para renderizar o documento na tela e permitir o posicionamento preciso da assinatura.
* **Privacidade e Segurança:** Processamento em memória (RAM), CORS estrito, autenticação via X-API-KEY e Rate Limiting.

### 🚀 Como Executar Localmente
1. **Clone o repositório:** `git clone ...`
2. **Instale as dependências:** `pip install -r requirements.txt`
3. **Inicie o Servidor:** `python app.py` (Disponível em `http://localhost:5000`)
4. **Frontend:** Abra o `index.html` em qualquer navegador.

### ⚙️ Implantação
* **Frontend:** GitHub Pages.
* **Backend:** Render.

---

### 🎓 About the ICPEdu Certificate (RNP)
The **[ICPEdu - Personal Certificate](https://pessoal.icpedu.rnp.br/)** is a free service provided by the Brazilian National Research and Educational Network (RNP). It allows students, professors, and staff from academic institutions participating in the CAFe federation to issue their own virtual identity (a digital certificate in `.p12` or `.pfx` format). This certificate can be used to digitally sign academic documents, ensuring authorship and data integrity.

👉 **[Click here to issue your ICPEdu certificate](https://pessoal.icpedu.rnp.br/)** *(Service intended for Brazilian academic institutions)*

## 🇺🇸 About the Project

The **Digital Signer** is an open-source web application designed to cryptographically sign PDF documents using `.p12` / `.pfx` digital certificates.

The project strictly follows the **PAdES** standard, ensuring technical and legal validity recognized by official government validators and Adobe Acrobat.

### ✨ Features
* **Valid PAdES Signature:** Implemented using the `pyHanko` library.
* **Visual Positioning:** Integrated with `PDF.js` for precise signature placement.
* **Privacy & Security:** In-memory (RAM) processing, strict CORS, X-API-KEY auth, and Rate Limiting.

### 🚀 How to Run Locally
1. **Clone the repository:** `git clone ...`
2. **Install Backend dependencies:** `pip install -r requirements.txt`
3. **Start the Local Server:** `python app.py` (Starts at `http://localhost:5000`)
4. **Open the Frontend:** Open the `index.html` file in any modern web browser.

### ⚙️ Production Deployment
* **Frontend:** GitHub Pages.
* **Backend:** Render.

---
Developed with security and usability in mind.