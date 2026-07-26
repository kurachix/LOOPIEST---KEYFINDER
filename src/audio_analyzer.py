"""
Engine de Processamento e Análise de Frequência e Tempo de Áudio.
Módulo de extração de croma, classificação tonal e cálculo preciso de BPM.
"""

import os
import sys
from typing import List, Dict, Tuple, Any

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def verificar_dependencias():
    try:
        import librosa
        import numpy as np
        return True
    except ImportError:
        return False


def carregar_audio(caminho_arquivo: str, sr: int = 22050) -> Tuple[Any, int]:
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: '{caminho_arquivo}'")

    ext = os.path.splitext(caminho_arquivo)[1].lower()
    if ext not in ['.mp3', '.wav']:
        raise ValueError(f"Formato '{ext}' não suportado.")

    import librosa

    try:
        y, sample_rate = librosa.load(caminho_arquivo, sr=sr, mono=True)
        return y, sample_rate
    except Exception as err:
        raise RuntimeError(f"Erro ao processar arquivo de áudio: {err}") from err


def extrair_chromagram(y, sr: int):
    import librosa
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    return chroma


def calcular_bpm(y, sr: int) -> int:
    """
    Calcula o BPM (Beats Per Minute) do sinal de áudio com alta precisão,
    aplicando restrições de janela e correção de oitava rítmica (70-160 BPM).
    """
    import librosa
    import numpy as np

    try:
        # Envelope de força de início de notas (onset strength)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Estimativa de tempo com ponto de partida priorizado em 120.0 BPM
        tempo_array, _ = librosa.beat.beat_track(
            y=y,
            sr=sr,
            onset_envelope=onset_env,
            start_bpm=120.0,
            tightness=100
        )

        # Trata o retorno como escalar float
        if isinstance(tempo_array, np.ndarray):
            tempo = float(tempo_array.item(0)) if tempo_array.size > 0 else 120.0
        else:
            tempo = float(tempo_array)

        # Correção Heurística de Oitava Rítmica (Evita oitava dividida/dobrada)
        if tempo < 70.0:
            tempo *= 2.0
        elif tempo > 165.0:
            tempo /= 2.0

        return max(60, min(200, int(round(tempo))))
    except Exception as e:
        print(f"[Aviso BPM]: {e}")
        return 120  # Fallback seguro


def ranquear_notas(caminho_arquivo: str, top_n: int = 12) -> List[Dict[str, Any]]:
    import numpy as np

    y, sr = carregar_audio(caminho_arquivo)
    chroma = extrair_chromagram(y, sr)
    intensidades_medias = np.mean(chroma, axis=1)

    soma_total = np.sum(intensidades_medias)
    if soma_total > 0:
        percentuais = (intensidades_medias / soma_total) * 100
    else:
        percentuais = np.zeros(12)

    resultado_notas = []
    for i, nota in enumerate(PITCH_CLASSES):
        resultado_notas.append({
            "nota": nota,
            "intensidade_media": float(intensidades_medias[i]),
            "relevancia_pct": round(float(percentuais[i]), 2)
        })

    notas_ordenadas = sorted(resultado_notas, key=lambda x: x["relevancia_pct"], reverse=True)

    for idx, item in enumerate(notas_ordenadas, start=1):
        item["posicao"] = idx

    return notas_ordenadas[:top_n]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("LOOPIEST KEYFINDER - Analisador Tonal & Tempo")
        print("Uso: python src/audio_analyzer.py <caminho_do_arquivo.mp3|.wav>")
        sys.exit(0)

    try:
        y, sr = carregar_audio(sys.argv[1])
        bpm = calcular_bpm(y, sr)
        ranking = ranquear_notas(sys.argv[1])

        print("\n--- RESULTADO DE ANÁLISE ---")
        print(f"♩ BPM Calculado: {bpm}")
        from src.key_detector import descobrir_tom
        tom = descobrir_tom(ranking)
        print(f"{tom}")
    except Exception as e:
        print(f"Erro na análise: {e}")
