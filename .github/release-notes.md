# Assinador Digital PAdES {{VERSION}} | Digital Signer PAdES {{VERSION}}

<hr>

## 🇧🇷 Português

### Sobre esta versão

Release do **Assinador Digital PAdES**, aplicativo de assinatura criptográfica de documentos PDF no padrão PAdES utilizando certificados digitais PKCS#12 (`.p12` / `.pfx`).

### O que está incluído

- `AssinadorDigital.exe` — versão Desktop empacotada (PyInstaller, PySide6, pyHanko)
- `SHA256.txt` — checksum SHA-256 do executável para verificação de integridade

### Versões disponíveis

- **Web:** frontend estático (HTML/CSS/JS + PDF.js) com backend Flask hospedável no Render
- **Desktop:** aplicação local em PySide6, sem navegador, todo o processamento ocorre no computador do usuário

### Principais recursos

- Assinatura PAdES de PDFs com certificados `.p12` e `.pfx`
- Algoritmo de resumo SHA-256
- Atualização incremental do PDF
- Interface em Português e Inglês
- Tema claro/escuro com preferência do sistema
- Recursos de acessibilidade (ARIA, navegação por teclado, leitores de tela)

### Verificação de integridade

```powershell
Get-FileHash AssinadorDigital.exe -Algorithm SHA256
```

Compare o resultado com o conteúdo de `SHA256.txt`.

<hr>

## 🇺🇸 English

### About this release

Release of **Digital Signer PAdES**, a cryptographic PDF signing application in the PAdES standard using PKCS#12 digital certificates (`.p12` / `.pfx`).

### What is included

- `AssinadorDigital.exe` — packaged Desktop version (PyInstaller, PySide6, pyHanko)
- `SHA256.txt` — SHA-256 checksum of the executable for integrity verification

### Available versions

- **Web:** static frontend (HTML/CSS/JS + PDF.js) with Flask backend deployable on Render
- **Desktop:** local PySide6 application, no browser, all processing occurs on the user's computer

### Main features

- PAdES PDF signing with `.p12` and `.pfx` certificates
- SHA-256 digest algorithm
- Incremental PDF update
- Interface in Portuguese and English
- Light/dark theme with system preference
- Accessibility features (ARIA, keyboard navigation, screen readers)

### Integrity verification

```powershell
Get-FileHash AssinadorDigital.exe -Algorithm SHA256
```

Compare the result with the contents of `SHA256.txt`.
