"""
Audio Frequency & Chromagram Analysis Module (Backend MIR Engine).
Extracts pitch class chromagrams and ranks musical notes by intensity and assiduity.
Supports .wav and .mp3 formats.
"""

import os
import sys
from typing import List, Dict, Tuple, Any

# Pitch Class Mapping (12 Equal Temperament Semitones)
PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def verificar_dependencias():
    """Verifica se librosa e numpy estão instalados no ambiente."""
    try:
        import librosa
        import numpy as np
        return True
    except ImportError as e:
        print(f"[Erro] Dependência não instalada: {e}")
        print("Execute: pip install librosa numpy soundfile scipy")
        return False


def carregar_audio(caminho_arquivo: str, sr: int = 22050) -> Tuple[Any, int]:
    """
    Carrega um arquivo de áudio (.wav ou .mp3) e o converte para sinal mono.

    :param caminho_arquivo: Caminho absoluto ou relativo para o arquivo de áudio.
    :param sr: Taxa de amostragem (default: 22050 Hz).
    :return: Tupla contendo o array do sinal de áudio (y) e a taxa de amostragem (sr).
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: '{caminho_arquivo}'")

    ext = os.path.splitext(caminho_arquivo)[1].lower()
    if ext not in ['.mp3', '.wav']:
        raise ValueError(f"Formato '{ext}' não suportado. Por favor utilize arquivos .mp3 ou .wav.")

    import librosa

    try:
        # Carrega o áudio usando librosa
        y, sample_rate = librosa.load(caminho_arquivo, sr=sr, mono=True)
        return y, sample_rate
    except Exception as err:
        msg = str(err)
        if "audioread" in msg.lower() or "ffmpeg" in msg.lower() or ext == '.mp3':
            raise RuntimeError(
                f"Falha ao decodificar o arquivo MP3 ({err}).\n"
                "Certifique-se de que o FFmpeg está instalado e adicionado às variáveis de ambiente (PATH) do sistema."
            ) from err
        raise RuntimeError(f"Erro ao processar arquivo de áudio: {err}") from err


def extrair_chromagram(y, sr: int):
    """
    Extrai a matriz de Chromagram (Chroma STFT) do sinal de áudio.

    :param y: Array do sinal de áudio.
    :param sr: Taxa de amostragem.
    :return: Matriz NumPy de croma de dimensão (12, n_frames).
    """
    import librosa
    # Extrai o Chromagram utilizando a Transformada de Fourier de Curto Termino (STFT)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    return chroma


def ranquear_notas(caminho_arquivo: str, top_n: int = 12) -> List[Dict[str, Any]]:
    """
    Identifica e ranqueia as notas musicais que aparecem com maior assiduidade
    e intensidade ao longo da trilha de áudio.

    :param caminho_arquivo: Caminho para o arquivo de áudio (.mp3 ou .wav).
    :param top_n: Quantidade de notas a retornar no ranking (default: 12).
    :return: Lista de dicionários contendo 'posicao', 'nota', 'relevancia_pct' e 'intensidade_media'.
    """
    import numpy as np

    # 1. Carrega o sinal de áudio
    y, sr = carregar_audio(caminho_arquivo)

    # 2. Extrai o Chromagram (12 notas x n_quadros de tempo)
    chroma = extrair_chromagram(y, sr)

    # 3. Calcula a intensidade média acumulada de cada nota ao longo do tempo
    intensidades_medias = np.mean(chroma, axis=1)

    # 4. Normalização percentual em relação ao total acumulado
    soma_total = np.sum(intensidades_medias)
    if soma_total > 0:
        percentuais = (intensidades_medias / soma_total) * 100
    else:
        percentuais = np.zeros(12)

    # 5. Constrói a lista de notas com suas métricas
    resultado_notas = []
    for i, nota in enumerate(PITCH_CLASSES):
        resultado_notas.append({
            "nota": nota,
            "intensidade_media": float(intensidades_medias[i]),
            "relevancia_pct": round(float(percentuais[i]), 2)
        })

    # 6. Ordena em ordem decrescente de relevância
    notas_ordenadas = sorted(resultado_notas, key=lambda x: x["relevancia_pct"], reverse=True)

    # 7. Adiciona a posição do ranking
    for idx, item in enumerate(notas_ordenadas, start=1):
        item["posicao"] = idx

    return notas_ordenadas[:top_n]


if __name__ == "__main__":
    print("=========================================================")
    print("LOOPIEST KEYFINDER - Analisador de Frequência & Chromagram")
    print("=========================================================\n")

    if not verificar_dependencias():
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Uso do script CLI:")
        print("  python src/audio_analyzer.py <caminho_do_arquivo.mp3|.wav>\n")
        print("Exemplo:")
        print("  python src/audio_analyzer.py assets/exemplo.mp3")
        sys.exit(0)

    caminho_teste = sys.argv[1]

    try:
        print(f"Analisando áudio: '{caminho_teste}'...")
        ranking = ranquear_notas(caminho_teste)

        print("\n--- RANKING DE NOTAS MAIS PRESENTES ---")
        print(f"{'Pos.':<6}{'Nota':<8}{'Relevância (%)':<18}{'Intensidade Média':<18}")
        print("-" * 50)
        for item in ranking:
            print(f"{item['posicao']:<6}{item['nota']:<8}{item['relevancia_pct']:<18}% {item['intensidade_media']:.4f}")

    except Exception as e:
        print(f"\n[Erro na análise]: {e}")
