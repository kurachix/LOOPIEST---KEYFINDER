# LOOPIEST - KEYSEARCH Splash Screen

Uma **Splash Screen (Tela Inicial)** elegante, minimalista e funcional desenvolvida em **Python 3** com **PySide6 (Qt 6)**.

---

## 🎨 Características Visuais & Funcionalidades

- **Estilo Dark/Neon Purple:** Palette inspirada em `#0A0A0E` ( obsidian), `#2D0B5A` (roxo profundo) e `#8A2BE2` (roxo neon).
- **Sem Bordas (Frameless):** Transparência de sistema, bordas arredondadas e sombra suave (`QGraphicsDropShadowEffect`).
- **Movimentação Drag & Drop:** Arraste a janela livremente clicando no fundo.
- **Botão Fechar Customizado (X):** Botão "✕" minimalista no canto superior direito com efeito hover neon.
- **Logo Central:** Exibição da logo com redimensionamento suave e tratamento de erros (fallback embutido).
- **Carregamento Assíncrono:** Multithreading com `QThread` para garantir animação de carregamento fluida a 60 FPS.

---

## 📁 Estrutura de Pastas

```text
LOOPIEST - KEYSEARCH/
│── assets/
│   └── logo.png              # Imagem oficial da logo
│── styles/
│   └── theme.qss             # Estilização QSS (Dark/Neon Purple)
│── src/
│   ├── __init__.py
│   ├── splash_screen.py      # Interface visual da Splash Screen (PySide6)
│   └── worker.py             # Thread assíncrona de inicialização
│── main.py                   # Ponto de entrada da aplicação
│── skill.md                  # Padrões e diretrizes de desenvolvimento GUI
│── requirements.txt          # Dependências do projeto
└── README.md                 # Guia do projeto
```

---

## 🚀 Como Executar

### 1. Requisitos Prévios
- Python 3.10+ instalado.

### 2. Instalar Dependências
No terminal, execute:
```bash
pip install -r requirements.txt
```

### 3. Executar a Aplicação
```bash
python main.py
```

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.11**
- **PySide6 / Qt 6 for Python**
