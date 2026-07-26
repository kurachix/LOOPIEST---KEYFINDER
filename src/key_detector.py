"""
LOOPIEST KEYFINDER - Motor de Detecção Tonal e Escalas Relativas.
"""

import math
from typing import List, Dict, Union, Tuple, Any

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 2.98, 2.69, 3.34, 3.17]

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Mapeamento de Escalas Relativas / Equivalentes (Maior <-> Menor)
MAPA_ESCALAS_RELATIVAS = {
    "C Major": "A Minor", "A Minor": "C Major",
    "G Major": "E Minor", "E Minor": "G Major",
    "D Major": "B Minor", "B Minor": "D Major",
    "A Major": "F# Minor", "F# Minor": "A Major",
    "E Major": "C# Minor", "C# Minor": "E Major",
    "B Major": "G# Minor", "G# Minor": "B Major",
    "F# Major": "D# Minor", "D# Minor": "F# Major",
    "F Major": "D Minor", "D Minor": "F Major",
    "Bb Major": "G Minor", "G Minor": "Bb Major",
    "Eb Major": "C Minor", "C Minor": "Eb Major",
    "Ab Major": "F Minor", "F Minor": "Ab Major",
    "Db Major": "Bb Minor", "Bb Minor": "Db Major",
    "Gb Major": "Eb Minor", "Eb Minor": "Gb Major"
}


def obter_escala_relativa(tom: str) -> str:
    """
    Retorna a escala relativa (equivalente) para uma dada tonalidade.
    Exemplo: 'A Minor' -> 'C Major', 'C Major' -> 'A Minor'
    """
    tom_clean = tom.replace("Key: ", "").strip()

    if tom_clean in MAPA_ESCALAS_RELATIVAS:
        return MAPA_ESCALAS_RELATIVAS[tom_clean]

    # Mapeamento enarmônico para variações sustenido / bemol
    enarmonicos = {
        "A# Minor": "Bb Minor", "Bb Minor": "A# Minor",
        "D# Minor": "Eb Minor", "Eb Minor": "D# Minor",
        "G# Minor": "Ab Minor", "Ab Minor": "G# Minor",
        "C# Minor": "Db Minor", "Db Minor": "C# Minor",
        "F# Major": "Gb Major", "Gb Major": "F# Major",
        "C# Major": "Db Major", "Db Major": "C# Major",
    }

    if tom_clean in enarmonicos:
        norm = enarmonicos[tom_clean]
        if norm in MAPA_ESCALAS_RELATIVAS:
            return MAPA_ESCALAS_RELATIVAS[norm]

    return ""


def gerar_dicionario_escalas() -> Dict[str, List[str]]:
    escalas = {}
    for i, tônica in enumerate(PITCH_CLASSES):
        notas_maior = [PITCH_CLASSES[(i + interval) % 12] for interval in MAJOR_INTERVALS]
        escalas[f"{tônica} Major"] = notas_maior

        notas_menor = [PITCH_CLASSES[(i + interval) % 12] for interval in MINOR_INTERVALS]
        escalas[f"{tônica} Minor"] = notas_menor

    return escalas


DICIONARIO_ESCALAS = gerar_dicionario_escalas()


def _correlacao_pearson(x: List[float], y: List[float]) -> float:
    n = len(x)
    if n == 0 or len(y) != n:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    den_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    denominator = math.sqrt(den_x * den_y)
    if denominator == 0:
        return 0.0

    return num / denominator


def converter_para_vetor_pitch(notas_predominantes: Union[List[str], List[Dict[str, Any]], Dict[str, float]]) -> List[float]:
    vetor = [0.0] * 12

    if isinstance(notas_predominantes, dict):
        for nota, val in notas_predominantes.items():
            nota_clean = nota.upper().strip()
            if nota_clean in PITCH_CLASSES:
                idx = PITCH_CLASSES.index(nota_clean)
                vetor[idx] += float(val)

    elif isinstance(notas_predominantes, list):
        for idx_elem, item in enumerate(notas_predominantes):
            if isinstance(item, str):
                nota_clean = item.upper().strip()
                if nota_clean in PITCH_CLASSES:
                    idx = PITCH_CLASSES.index(nota_clean)
                    vetor[idx] += max(1.0, (len(notas_predominantes) - idx_elem))
            elif isinstance(item, dict):
                nota = item.get("nota", "").upper().strip()
                val = item.get("relevancia_pct", item.get("intensidade_media", 1.0))
                if nota in PITCH_CLASSES:
                    idx = PITCH_CLASSES.index(nota)
                    vetor[idx] += float(val)

    return vetor


def descobrir_tom(notas_predominantes: Union[List[str], List[Dict[str, Any]], Dict[str, float]], detalhado: bool = False) -> Union[str, Tuple[str, List[Dict[str, Any]]]]:
    vetor_pitch = converter_para_vetor_pitch(notas_predominantes)

    if sum(vetor_pitch) == 0:
        return "Key: Undefined" if not detalhado else ("Key: Undefined", [])

    resultados = []

    for i in range(12):
        tônica = PITCH_CLASSES[i]

        perfil_maior_rotacionado = MAJOR_PROFILE[-i:] + MAJOR_PROFILE[:-i]
        perfil_menor_rotacionado = MINOR_PROFILE[-i:] + MINOR_PROFILE[:-i]

        score_maior = _correlacao_pearson(vetor_pitch, perfil_maior_rotacionado)
        score_menor = _correlacao_pearson(vetor_pitch, perfil_menor_rotacionado)

        resultados.append({
            "key_name": f"{tônica} Major",
            "score": score_maior,
            "tonica": tônica,
            "modo": "Major"
        })
        resultados.append({
            "key_name": f"{tônica} Minor",
            "score": score_menor,
            "tonica": tônica,
            "modo": "Minor"
        })

    resultados_ordenados = sorted(resultados, key=lambda x: x["score"], reverse=True)
    melhor_tom = resultados_ordenados[0]["key_name"]
    resultado_str = f"Key: {melhor_tom}"

    if detalhado:
        return resultado_str, resultados_ordenados[:5]

    return resultado_str


if __name__ == "__main__":
    simulacao_1 = ['A', 'C', 'E', 'G', 'F', 'D', 'B']
    resultado_1 = descobrir_tom(simulacao_1)
    relativa_1 = obter_escala_relativa(resultado_1)
    print(f"Tom Identificado: {resultado_1} | Escala Relativa: {relativa_1}")
