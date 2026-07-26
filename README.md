# LOOPIEST - KEYFINDER

Uma aplicação desktop moderna em **Python 3** e **PySide6** para análise de áudio, acompanhada por um **Módulo Backend de Engenharia de Áudio** (`librosa` / `numpy`) para extração de **Chromagram** e ranqueamento de notas musicais em arquivos `.mp3` e `.wav`.

---

## 🎨 Características Visuais & Funcionalidades

- **Splash Screen Frameless:** Fundo Obsidian (`#0A0A0E`), acentos Roxo Neon (`#8A2BE2`), bordas arredondadas de 16px e sombra projetada.
- **Tag no Cabeçalho:** `@L8PIEST` centralizada na barra superior.
- **Ícone na Barra de Tarefas:** Exibição da logo oficial (`assets/logo.png`) no ícone da barra de tarefas do Windows via `AppUserModelID`.
- **Recepção de Áudio (Drag & Drop):** Solte ou clique para selecionar arquivos de áudio `.mp3` e `.wav`.
- **Análise Backend de Frequência:** Módulo DSP (`src/audio_analyzer.py`) para extração do perfil de croma (Chromagram) e ranking das notas musicais mais assíduas.

---

## 📁 Estrutura do Projeto

```text
LOOPIEST - KEYSEARCH/
│── assets/
│   └── logo.png              # Logo oficial da aplicação
│── styles/
│   └── theme.qss             # Folha de estilos QSS (Dark/Neon Purple)
│── src/
│   ├── __init__.py
│   ├── splash_screen.py      # Splash Screen com transição
│   ├── main_window.py        # Janela Principal de Recepção de Áudio
│   ├── drop_zone.py          # Componente Drag & Drop (.mp3, .wav)
│   ├── worker.py             # Threads assíncronas (LoadingWorker e AnalysisWorker)
│   └── audio_analyzer.py     # Backend MIR: Librosa, Chromagram & Ranking de Notas
│── main.py                   # Ponto de entrada da GUI
│── .gitignore
│── skill.md
│── requirements.txt          # Dependências do projeto
└── README.md                 # Guia e instruções completas
```

---

## 🚀 Guia de Instalação & Dependências

### 1. Requisitos Prévios
- Python 3.10+ instalado.

### 2. Instalar Dependências do Python
No terminal, execute:
```bash
pip install -r requirements.txt
```

---

## 🎼 Instalação do FFmpeg (Crucial para Decodificação de Arquivos MP3)

A biblioteca `librosa` utiliza o **FFmpeg** / `audioread` para descompactar e carregar arquivos MP3 em memória. Se o FFmpeg não estiver presente no sistema, o carregamento de arquivos `.mp3` poderá gerar um erro de decodificação.

### Windows (Escolha um dos métodos):

- **Método A - Via Winget (Recomendado):**
  Abra o Prompt de Comando ou PowerShell e execute:
  ```powershell
  winget install "FFmpeg (Essentials Build)"
  ```
  *Reinicie o terminal após a instalação.*

- **Método B - Via Chocolatey:**
  ```powershell
  choco install ffmpeg
  ```

- **Método C - Instalação Manual:**
  1. Baixe os binários em [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/).
  2. Extraia o arquivo zip em uma pasta (ex: `C:\ffmpeg`).
  3. Adicione a pasta `C:\ffmpeg\bin` às **Variáveis de Ambiente (PATH)** do Windows.

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

### macOS (Via Homebrew):
```bash
brew install ffmpeg
```

---

## 🧪 Uso do Módulo Backend de Análise (`audio_analyzer.py`)

Você pode utilizar o script backend via linha de comando para analisar a distribuição de frequências e notas de qualquer arquivo de áudio:

```bash
python src/audio_analyzer.py <caminho_do_arquivo.mp3|.wav>
```

### Exemplo de Uso Programático no Python:

```python
from src.audio_analyzer import ranquear_notas

# Analisa o arquivo e retorna o ranking das notas
ranking = ranquear_notas("meu_audio.mp3")

for item in ranking:
    print(f"Nota: {item['nota']} | Relevância: {item['relevancia_pct']}% | Intensidade: {item['intensidade_media']}")
```

---

## 🖥️ Executar a Interface Gráfica (GUI)

Para iniciar a interface desktop com Splash Screen e Drag & Drop:

```bash
python main.py
```
