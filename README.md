# LOOPIEST KEYFINDER

**LOOPIEST KEYFINDER** é uma aplicação desktop de alta performance projetada para **identificação automática de tonalidade musical (Key) e análise de frequência** em arquivos de áudio nos formatos `.mp3` e `.wav`.

---

## ⚡ Principais Recursos

- **Interface Gráfica Frameless & Dark Neon:** Design minimalista moderno com bordas arredondadas e iluminação purpúrea.
- **Detecção Tonal de Alta Precisão:** Identificação automática da tonalidade principal (ex: `Key: A Minor`, `Key: C Major`).
- **Perfil de Notas Predominantes:** Visualização percentual da presença e intensidade das notas na música.
- **Recepção por Drag & Drop:** Arraste e solte arquivos de áudio diretamente na aplicação ou navegue pelo explorador.
- **Multithreading de Alta Velocidade:** Processamento de áudio em background garantindo 60 FPS e resposta instantânea da interface.

---

## 🖥️ Requisitos do Sistema & Instalação

### Requisitos Prévios
- **Sistema Operacional:** Windows 10/11, macOS ou Linux.
- **Python:** Versão 3.10 ou superior.

### 1. Instalação das Dependências
No terminal da aplicação, execute:
```bash
pip install -r requirements.txt
```

### 2. Suporte a Decodificação de MP3 (FFmpeg)
Para garantir o processamento de arquivos `.mp3`, certifique-se de que o **FFmpeg** está instalado no sistema:

- **Windows (Prompt de Comando / PowerShell):**
  ```powershell
  winget install "FFmpeg (Essentials Build)"
  ```
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```
- **macOS:**
  ```bash
  brew install ffmpeg
  ```

---

## 🚀 Como Executar a Aplicação

Para iniciar o **LOOPIEST KEYFINDER**:

```bash
python main.py
```

---

## 📦 Como Gerar o Executável Distribuível (.EXE)

Para criar o pacote distribuível independente (sem necessidade de Python instalado na máquina do usuário final):

```bash
python build.py
```

O executável pronto para distribuição comercial será gerado no diretório:
`dist/LOOPIEST_KEYFINDER/LOOPIEST_KEYFINDER.exe`
