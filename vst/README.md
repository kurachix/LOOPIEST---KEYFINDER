# LOOPIEST KEYFINDER - VST3 Plugin para FL Studio

Port nativo em C++ (utilizando o framework JUCE 8) do **LOOPIEST KEYFINDER** projetado especificamente para Digital Audio Workstations, com foco no **FL Studio**.

---

## 🎹 Recursos do Plugin VST3

1. **Análise de Áudio em Tempo Real no Mixer:**
   - Insira o plugin em qualquer canal do Mixer ou no Master do FL Studio.
   - O motor DSP realiza transformada de Fourier (FFT de 4096 pontos) e projeta as frequências em um perfil cromático de 12 classes harmônicas (Chroma STFT).
   - Classificação cognitiva de tonalidade através dos perfis de Krumhansl-Schmuckler e Temperley (identificando as 24 tonalidades Maiores e Menores).

2. **Roda de Camelot Automática:**
   - Conversão instantânea da tonalidade para o formato Camelot (ex: `8A` para Lá Menor, `8B` para Dó Maior, `11A` para Fá# Menor).

3. **Detecção e Sincronização de BPM:**
   - Integração com o PlayHead do FL Studio: sincroniza automaticamente com o andamento da sessão do projeto.
   - Autocorrelação de fluxo de energia para loops independentes.

4. **Detecção de Afinação (Reference Tuning em Hz):**
   - Interpolação parabólica dos picos espectrais para identificar se a música/sample está afinada em 440 Hz, 432 Hz ou 444 Hz.

5. **Drag & Drop Direto do Browser do FL Studio:**
   - Arraste qualquer sample (`.wav`, `.mp3`, `.flac`, `.ogg`, `.aif`) direto do navegador lateral do FL Studio ou do Windows Explorer para dentro da interface do plugin para obter o Tom e BPM instantaneamente.

6. **Ranking de Notas Dominantes:**
   - Gráfico de barras animado em tempo real com as 5 notas predominantes e suas respectivas porcentagens.

7. **Design Dark Purple Exclusivo:**
   - Interface visual moderna em tons escuros e roxo neon desenvolvida em conformidade com a identidade visual da `@L8PIEST`.

---

## 📁 Estrutura do Código C++ (`vst/Source/`)

* [`PluginProcessor.h`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/PluginProcessor.h) / [`.cpp`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/PluginProcessor.cpp): Processamento de áudio em tempo real, buffer FIFO, cálculo de FFT, thread offline para análise de arquivos e sincronização com a DAW.
* [`PluginEditor.h`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/PluginEditor.h) / [`.cpp`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/PluginEditor.cpp): Interface gráfica (GUI) dark purple, badges, cards, animações a 30 FPS e manipulador de Drag & Drop (`juce::FileDragAndDropTarget`).
* [`KeyDetector.h`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/KeyDetector.h) / [`.cpp`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/KeyDetector.cpp): Algoritmo de correlação de Pearson para detecção de tons e tabela Camelot.
* [`BpmDetector.h`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/BpmDetector.h) / [`.cpp`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/BpmDetector.cpp): Detecção de transientes e autocorrelação de andamento (70–180 BPM).
* [`AuthManager.h`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/AuthManager.h) / [`.cpp`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/Source/AuthManager.cpp): Validador da passkey e integração com o cofre de licenças em `C:\loopiest\acess\`.
* [`CMakeLists.txt`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/CMakeLists.txt): Script de compilação automatizado com download automático do JUCE via `FetchContent`.
* [`build_vst.bat`](file:///c:/Users/Aluno/Pictures/LOOPIEST---KEYFINDER/vst/build_vst.bat): Script em lote para compilação e instalação em um clique.

---

## 🛠️ Como Compilar o Plugin VST3

### Requisitos:
1. **CMake 3.20+** ([https://cmake.org/download/](https://cmake.org/download/))
2. **Visual Studio 2022** (com a carga de trabalho *"Desenvolvimento para Desktop com C++"*) ou compilador Clang/GCC.

### Compilação Rápida (Windows):
Abra o terminal na pasta `vst` e execute:

```powershell
cd vst
.\build_vst.bat
```

Ou execute manualmente via CMake:

```powershell
cd vst
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

O binário final será gerado em:
`C:\Program Files\Common Files\VST3\LOOPIEST KEYFINDER.vst3`

---

## 🎛️ Como Usar no FL Studio

1. Abra o **FL Studio**.
2. No menu superior, vá em **Options > Manage plugins**.
3. No painel esquerdo, certifique-se de que o caminho `C:\Program Files\Common Files\VST3\` está listado e clique em **Find installed plugins**.
4. O **LOOPIEST KEYFINDER** aparecerá na lista de plugins instalados.
5. Abra o **Mixer** (F9), clique em um slot de efeito em qualquer canal ou no Master e selecione **LOOPIEST KEYFINDER**.
6. Pronto! Ao dar play no áudio ou arrastar um loop para a janela do plugin, o tom, BPM e tuning serão exibidos imediatamente.
