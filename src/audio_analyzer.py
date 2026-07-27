"""
Engine de Processamento e Análise de Frequência e Tempo de Áudio.
Módulo de extração de croma, classificação tonal e Motor de Consenso de BPM.
"""

import os
import sys
import math
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


def _estimar_bpm_motor_a(y, sr: int) -> float:
    """Motor A: Estimativa baseada em Onset Strength + STFT (Librosa)."""
    import librosa
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo_a = librosa.beat.beat_track(
        y=y,
        sr=sr,
        onset_envelope=onset_env,
        start_bpm=120.0,
        tightness=100
    )[0]
    if hasattr(tempo_a, 'item'):
        return float(tempo_a.item(0))
    return float(tempo_a)


def _estimar_bpm_motor_b(y, sr: int) -> Tuple[float, float]:
    """
    Motor B: Estimativa rítmica baseada em Aubio (se disponível) ou Tempogram Autocorrelation.
    Retorna a tupla (bpm_est, confianca_score).
    """
    import librosa
    import numpy as np

    # 1. Tenta utilizar Aubio caso a biblioteca esteja presente no sistema
    try:
        import aubio
        win_s = 1024
        hop_s = 512
        samplerate = sr
        o = aubio.tempo("default", win_s, hop_s, samplerate)

        beats = []
        for i in range(0, len(y) - hop_s, hop_s):
            samples = y[i:i + hop_s].astype(np.float32)
            is_beat = o(samples)
            if is_beat[0]:
                beats.append(o.get_last_s())

        if len(beats) > 1:
            intervals = np.diff(beats)
            intervals = intervals[intervals > 0.2]
            if len(intervals) > 0:
                bpm_aubio = 60.0 / float(np.median(intervals))
                confidence = float(o.get_confidence())
                return bpm_aubio, confidence
    except Exception:
        pass

    # 2. Motor B Alternativo: Tempogram Autocorrelation via Librosa
    try:
        tempogram = librosa.feature.tempogram(y=y, sr=sr)
        ac_mean = np.mean(tempogram, axis=1)
        bpms = librosa.fourier_tempo_frequencies(sr=sr, win_length=tempogram.shape[0])

        valid_idx = np.where((bpms >= 50) & (bpms <= 200))[0]
        if len(valid_idx) > 0:
            best_idx = valid_idx[np.argmax(ac_mean[valid_idx])]
            tempo_b = float(bpms[best_idx])
            confidence_b = float(ac_mean[best_idx])
            return tempo_b, confidence_b
    except Exception:
        pass

    return 0.0, 0.0


def calcular_bpm_consenso(y, sr: int) -> int:
    """
    Motor de Consenso de BPM com Dupla Análise (Motor A + Motor B),
    Alinhamento de Oitava Rítmica (Metade/Dobro) e Heurística de Desempate.
    """
    # 1. Extração Motor A (Principal)
    try:
        bpm_a = _estimar_bpm_motor_a(y, sr)
    except Exception:
        bpm_a = 120.0

    # 2. Extração Motor B (Secundário com Fallback Silencioso)
    bpm_b, conf_b = 0.0, 0.0
    try:
        bpm_b, conf_b = _estimar_bpm_motor_b(y, sr)
    except Exception:
        bpm_b = 0.0

    # Fallback caso Motor B falhar ou retornar zero
    if bpm_b <= 0 or math.isnan(bpm_b):
        if bpm_a < 70.0: bpm_a *= 2.0
        elif bpm_a > 165.0: bpm_a /= 2.0
        return max(60, min(200, int(round(bpm_a))))

    # 3. Correção de Oitava Rítmica (Metade / Dobro entre Motor A e Motor B)
    if bpm_a > 0:
        ratio = bpm_b / bpm_a
        if 1.8 <= ratio <= 2.2:
            # Motor B é o dobro do Motor A
            bpm_a *= 2.0
        elif 0.45 <= ratio <= 0.55:
            # Motor B é a metade do Motor A
            bpm_b *= 2.0

    # Normalização de faixa rítmica individual (70 a 165 BPM)
    if bpm_a < 70.0: bpm_a *= 2.0
    elif bpm_a > 165.0: bpm_a /= 2.0

    if bpm_b < 70.0: bpm_b *= 2.0
    elif bpm_b > 165.0: bpm_b /= 2.0

    # 4. Heurística de Comparação (Core do Consenso)
    diff = abs(bpm_a - bpm_b)

    if diff <= 3.0:
        # Caso 1: Diferença pequena (<= 3 BPM) -> Média entre os dois valores
        bpm_final = (bpm_a + bpm_b) / 2.0
    else:
        # Caso 2: Diferença grande (> 3 BPM) -> Desempate por confiança do transiente
        if conf_b > 0.4:
            bpm_final = bpm_b
        else:
            bpm_final = bpm_a

    return max(60, min(200, int(round(bpm_final))))


def calcular_bpm(y, sr: int) -> int:
    """Função de entrada pública para o cálculo de BPM por consenso."""
    return calcular_bpm_consenso(y, sr)


def estimar_afinacao_hz(y, sr: int) -> int:
    """
    Estima a frequência de afinação base (Reference Tuning Hz, ex: 440 Hz, 432 Hz)
    utilizando a estimativa de desvio espectral da nota Lá (A4).
    """
    import librosa

    try:
        # Estima o desvio de afinação em semitons relativos ao padrão 440.0 Hz
        tuning_offset = librosa.estimate_tuning(y=y, sr=sr)
        
        # Fórmula: f = 440.0 * (2 ** (desvio / 12))
        freq_hz = 440.0 * (2.0 ** (float(tuning_offset) / 12.0))
        
        tuning_int = int(round(freq_hz))
        return max(400, min(480, tuning_int))
    except Exception as e:
        print(f"[Aviso Tuning]: {e}")
        return 440


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
        print("LOOPIEST KEYFINDER - Analisador Tonal & Motor de Consenso de BPM")
        print("Uso: python src/audio_analyzer.py <caminho_do_arquivo.mp3|.wav>")
        sys.exit(0)

    try:
        y, sr = carregar_audio(sys.argv[1])
        bpm = calcular_bpm_consenso(y, sr)
        ranking = ranquear_notas(sys.argv[1])

        print("\n--- RESULTADO DE ANÁLISE ---")
        print(f"BPM Consenso: {bpm}")
        from src.key_detector import descobrir_tom
        tom = descobrir_tom(ranking)
        print(f"{tom}")
    except Exception as e:
        print(f"Erro na análise: {e}")
