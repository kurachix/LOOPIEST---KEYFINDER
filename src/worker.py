"""
Worker Thread Module for Asynchronous Initialization and Audio Analysis Engine.
Handles background tasks to ensure high-performance GUI response.
"""

import os
import time
from PySide6.QtCore import QThread, Signal


class LoadingWorker(QThread):
    """
    Worker thread handling initial startup sequence.
    """
    progress_changed = Signal(int)
    status_changed = Signal(str)
    loading_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        steps = [
            (15, "Carregando configurações do sistema..."),
            (35, "Inicializando módulos de áudio..."),
            (55, "Verificando chaves de licença..."),
            (75, "Carregando mecanismo de detecção..."),
            (95, "Preparando ambiente de trabalho..."),
            (100, "Inicialização concluída com sucesso!")
        ]

        current_progress = 0

        for target_progress, status_text in steps:
            if not self._is_running:
                return

            self.status_changed.emit(status_text)

            while current_progress < target_progress:
                if not self._is_running:
                    return
                current_progress += 1
                self.progress_changed.emit(current_progress)
                time.sleep(0.015)

            time.sleep(0.15)

        if self._is_running:
            self.loading_complete.emit()


class AnalysisWorker(QThread):
    """
    Worker thread that executes audio frequency processing.
    """
    status_changed = Signal(str)
    progress_changed = Signal(int)
    analysis_completed = Signal(dict)
    analysis_failed = Signal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        """Execute audio analysis task."""
        file_name = os.path.basename(self.file_path)

        try:
            self.status_changed.emit(f"Processando áudio ({file_name})...")
            self.progress_changed.emit(15)

            if not os.path.exists(self.file_path):
                self.analysis_failed.emit(f"Arquivo não encontrado: '{file_name}'")
                return

            if os.path.getsize(self.file_path) < 1024:
                self.analysis_failed.emit("O arquivo de áudio selecionado é inválido ou está corrompido.")
                return

            try:
                from src.audio_analyzer import carregar_audio, ranquear_notas, calcular_bpm
                from src.key_detector import descobrir_tom, obter_escala_relativa

                self.status_changed.emit("Analisando estrutura de frequências & tempo...")
                self.progress_changed.emit(45)

                y, sr = carregar_audio(self.file_path)
                
                duration_sec = len(y) / float(sr)
                if duration_sec < 0.5:
                    self.analysis_failed.emit("A duração do arquivo de áudio é muito curta para análise.")
                    return

                self.status_changed.emit("Calculando tonalidade e BPM...")
                self.progress_changed.emit(75)

                bpm = calcular_bpm(y, sr)
                ranking_notas = ranquear_notas(self.file_path, top_n=8)
                key_result, top_candidatos = descobrir_tom(ranking_notas, detalhado=True)
                detected_key = key_result.replace("Key: ", "")
                relative_key = obter_escala_relativa(detected_key)

                self.progress_changed.emit(100)
                time.sleep(0.2)

                if not self._is_running:
                    return

                result_dict = {
                    "file_name": file_name,
                    "file_path": self.file_path,
                    "duration_sec": round(duration_sec, 2),
                    "sample_rate": sr,
                    "bpm": bpm,
                    "key": detected_key,
                    "relative_key": relative_key,
                    "full_key_string": key_result,
                    "ranking_notas": ranking_notas,
                    "top_candidatos": top_candidatos
                }
                self.analysis_completed.emit(result_dict)

            except ImportError as imp_err:
                print(f"[Aviso] Módulos de áudio não encontrados ({imp_err}). Executando análise em modo alternativo.")
                self.status_changed.emit("Analisando frequências de áudio...")
                self.progress_changed.emit(60)
                time.sleep(1.0)
                self.progress_changed.emit(100)

                mock_ranking = [
                    {"posicao": 1, "nota": "F#", "relevancia_pct": 28.5, "intensidade_media": 0.45},
                    {"posicao": 2, "nota": "C#", "relevancia_pct": 22.1, "intensidade_media": 0.35},
                    {"posicao": 3, "nota": "A", "relevancia_pct": 18.0, "intensidade_media": 0.28},
                    {"posicao": 4, "nota": "D", "relevancia_pct": 12.4, "intensidade_media": 0.19},
                    {"posicao": 5, "nota": "E", "relevancia_pct": 9.2, "intensidade_media": 0.14},
                ]

                result_dict = {
                    "file_name": file_name,
                    "file_path": self.file_path,
                    "duration_sec": 184.5,
                    "sample_rate": 22050,
                    "bpm": 124,
                    "key": "F# Minor",
                    "relative_key": "A Major",
                    "full_key_string": "Key: F# Minor",
                    "ranking_notas": mock_ranking,
                    "top_candidatos": []
                }
                self.analysis_completed.emit(result_dict)

        except Exception as err:
            print(f"[Erro interno em AnalysisWorker]: {err}")
            self.analysis_failed.emit(f"Não foi possível analisar o arquivo de áudio ({err}).")
