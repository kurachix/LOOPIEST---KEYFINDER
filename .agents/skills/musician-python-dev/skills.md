# Habilidade: Desenvolvedor Python especialista em Interfaces Gráficas (GUI)

Esta habilidade estabelece os padrões e diretrizes de desenvolvimento para a criação de aplicações Python desktop modernas, fluidas e esteticamente refinadas.

---

## 🎨 1. Estética Visual & UI/UX
- **Design Moderno & Minimalista:** Priorizar temas escuros com contrastes elegantes (ex: obsidian `#0A0A0E`, roxo escuro `#2D0B5A` e destaques em roxo neon `#8A2BE2`).
- **Janelas Frameless:** Remover a barra de título legada do sistema operacional (`Qt.WindowType.FramelessWindowHint`).
- **Transparência & Cantos Arredondados:** Utilizar `Qt.WidgetAttribute.WA_TranslucentBackground` e folhas de estilo CSS/QSS com `border-radius`.
- **Efeitos de Sombra:** Adicionar `QGraphicsDropShadowEffect` para criar profundidade e destaque visual da janela sobre o desktop.
- **Tipografia & Contraste:** Fontes legíveis com hierarquia visual bem definida (títulos, etiquetas de status e indicadores percentuais).

---

## 🛠️ 2. Arquitetura Técnica & Performance
- **Framework Preferencial:** `PySide6` (Qt 6 for Python) por sua alta performance, suporte a aceleração por hardware e animações nativas.
- **Multithreading Assíncrono:** NUNCA executar tarefas de IO ou carregamento na thread principal (GUI Thread). Utilizar `QThread` ou `QRunner` e comunicação baseada em Sinais (`Signal`) e Slots para manter a interface a 60 FPS sem congelamentos.
- **Interatividade & Drag-and-Drop:** Implementar manipuladores de eventos de mouse (`mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`) para permitir arrastar a janela frameless intuitivamente.
- **Tratamento de Exceções & Assets:**
  - Garantir tratamento seguro ao carregar recursos externos (logos, ícones, arquivos QSS).
  - Fornecer renderização de fallback graciosa (placeholders estilizados) caso uma imagem não seja encontrada ou falhe no carregamento.

---

## 📁 3. Estrutura Modular de Projeto
- **Separação de Responsabilidades:**
  - `styles/`: Estilos centralizados em arquivos `.qss` para facilitar customizações futuras.
  - `assets/`: Imagens, logos e recursos visuais.
  - `src/`: Lógica da UI (`splash_screen.py`) separada da lógica de background (`worker.py`).
  - `main.py`: Inicialização limpa e gerenciamento do ciclo de vida da aplicação.
