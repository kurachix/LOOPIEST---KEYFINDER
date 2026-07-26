"""
Worker Thread Module for Asynchronous Initialization and Mock Audio Analysis.
Ensures the GUI remains fluid and non-blocking during startup and file processing.
"""

import os
import time
from PySide6.QtCore import QThread, Signal


class LoadingWorker(QThread):
    """
    Worker thread that simulates startup loading tasks for the Splash Screen.
    Emits signals for progress percentage and status updates.
    """
    progress_changed = Signal(int)
    status_changed = Signal(str)
    loading_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True

    def stop(self):
        """Safely request the thread to stop."""
        self._is_running = False

    def run(self):
        """Execute simulated startup sequence with progress signals."""
        steps = [
            (15, "Carregando arquivos de configuração..."),
            (35, "Inicializando módulos do sistema..."),
            (55, "Verificando chaves de segurança..."),
            (75, "Carregando mecanismo de busca de tom..."),
            (95, "Preparando interface de usuário..."),
            (100, "Inicialização concluída!")
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
                time.sleep(0.02)

            time.sleep(0.2)

        if self._is_running:
            self.loading_complete.emit()


class AnalysisWorker(QThread):
    """
    Worker thread that handles mock audio analysis for 3 seconds.
    Emits progress and result signals upon completion.
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
        """Simulate audio feature extraction and key detection over 3 seconds."""
        if not os.path.exists(self.file_path):
            self.analysis_failed.emit("Arquivo não encontrado.")
            return

        file_name = os.path.basename(self.file_path)
        
        # 3 Seconds Mock Analysis Sequence (6 steps of 0.5s)
        stages = [
            (20, f"Lendo cabeçalhos de áudio ({file_name})..."),
            (40, "Decodificando frequências PCM / FFT..."),
            (60, "Extraindo perfis de cromagrama de tom..."),
            (80, "Detectando tonalidade musical & BPM..."),
            (100, "Análise finalizada!")
        ]

        for percent, msg in stages:
            if not self._is_running:
                return
            self.status_changed.emit(msg)
            self.progress_changed.emit(percent)
            time.sleep(0.6)  # 5 steps * 0.6s = 3.0 seconds total

        if self._is_running:
            # Mock Result Data
            result = {
                "file_name": file_name,
                "file_path": self.file_path,
                "key": "F# Menor (F#m)",
                "bpm": 124,
                "confidence": "98.4%"
            }
            self.analysis_completed.emit(result)


def analisar_arquivo(caminho_arquivo: str, on_status=None, on_finish=None):
    """
    Função helper mock de entrada para análise de arquivo de áudio.
    Retorna uma instância de AnalysisWorker pronta para ser executada.
    """
    worker = AnalysisWorker(file_path=caminho_arquivo)
    if on_status:
        worker.status_changed.connect(on_status)
    if on_finish:
        worker.analysis_completed.connect(on_finish)
    return worker
