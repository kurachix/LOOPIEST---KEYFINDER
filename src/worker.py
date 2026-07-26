"""
Worker Thread Module for Asynchronous Initialization.
Ensures the GUI remains fluid and non-blocking during startup.
"""

import time
from PySide6.QtCore import QThread, Signal


class LoadingWorker(QThread):
    """
    Worker thread that simulates or handles background loading tasks.
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
            (10, "Carregando arquivos de configuração..."),
            (25, "Inicializando módulos do sistema..."),
            (45, "Verificando chaves de segurança..."),
            (65, "Carregando mecanismo de busca..."),
            (85, "Preparando interface de usuário..."),
            (100, "Inicialização concluída!")
        ]

        current_progress = 0

        for target_progress, status_text in steps:
            if not self._is_running:
                return

            self.status_changed.emit(status_text)

            # Smooth progress increment
            while current_progress < target_progress:
                if not self._is_running:
                    return
                current_progress += 1
                self.progress_changed.emit(current_progress)
                time.sleep(0.025)  # Smooth transition pace

            time.sleep(0.3)  # Brief pause per step milestone

        if self._is_running:
            self.loading_complete.emit()
