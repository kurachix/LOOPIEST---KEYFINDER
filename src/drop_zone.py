"""
Custom Drag and Drop Area Widget for Audio File Selection (.mp3, .wav).
Provides drag hover feedback, file validation, and file browser fallback.
"""

import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QFileDialog, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor


class DropZoneWidget(QFrame):
    """
    Drag and Drop component designed for receiving .mp3 and .wav files.
    Triggers open file dialog on click.
    """

    # Custom signal emitted when a valid audio file is selected or dropped
    file_selected = Signal(str)
    invalid_file_attempted = Signal(str)

    ALLOWED_EXTENSIONS = {".mp3", ".wav"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.init_ui()

    def init_ui(self):
        """Build internal layout and labels for the drop area."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon / Symbol
        self.icon_label = QLabel("🎵", self)
        self.icon_label.setObjectName("DropZoneIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # Primary Title
        self.title_label = QLabel("Arraste e solte seu arquivo de áudio aqui", self)
        self.title_label.setObjectName("DropZoneTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("ou clique em qualquer lugar para navegar\nSuporta apenas .MP3 e .WAV", self)
        self.subtitle_label.setObjectName("DropZoneSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)

    # -------------------------------------------------------------
    # Drag and Drop Event Handlers
    # -------------------------------------------------------------
    def dragEnterEvent(self, event):
        """Validate if dragged data contains files with allowed extensions."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    self.setProperty("active", True)
                    self.setObjectName("DropZoneActive")
                    self.setStyle(self.style())
                    event.acceptProposedAction()
                    return

        event.ignore()

    def dragLeaveEvent(self, event):
        """Reset styling when drag exits the component bounds."""
        self.setObjectName("DropZone")
        self.setStyle(self.style())
        event.accept()

    def dropEvent(self, event):
        """Handle file drop action."""
        self.setObjectName("DropZone")
        self.setStyle(self.style())

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    self.file_selected.emit(file_path)
                    event.acceptProposedAction()
                else:
                    self.invalid_file_attempted.emit(f"Formato '{ext}' não suportado. Por favor, envie um arquivo .mp3 ou .wav.")
                    event.ignore()

    def mousePressEvent(self, event):
        """Open system file picker dialog when user clicks on the drop zone."""
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar Arquivo de Áudio",
                "",
                "Arquivos de Áudio (*.mp3 *.wav)"
            )
            if file_path:
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    self.file_selected.emit(file_path)
                else:
                    self.invalid_file_attempted.emit("Por favor, selecione um arquivo válido (.mp3 ou .wav).")
