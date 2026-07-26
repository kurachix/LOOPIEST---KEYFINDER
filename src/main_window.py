"""
Main Application Window for LOOPIEST - KEYFINDER.
Provides Audio File Reception (.mp3, .wav) with Drag & Drop support
and asynchronous 3-second mock analysis.
"""

import os
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGraphicsDropShadowEffect
)

from src.drop_zone import DropZoneWidget
from src.worker import AnalysisWorker


class MainWindow(QWidget):
    """
    Main Application Window with frameless dark/neon purple theme,
    Drag and Drop audio receiver, and 3-second mock audio analysis worker.
    """

    def __init__(self, logo_path: str, qss_path: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.drag_position = QPoint()
        self.analysis_worker = None

        # Setup Window Flags & Geometry
        self.init_window()

        # Build UI Layout
        self.init_ui()

        # Load QSS Theme
        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

        # Apply Neon Glow Drop Shadow
        self.apply_drop_shadow()

    def init_window(self):
        """Configure frameless window, taskbar icon, and screen centering."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        self.resize(500, 620)

        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        """Construct window widgets, header, logo, dropzone, and status indicators."""
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 16, 20, 24)
        container_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Top Header Bar (Centered @L8PIEST & Action Buttons)
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left spacer matching right buttons width for exact tag centering (28*2 + spacing = 60)
        left_spacer = QWidget(self.main_container)
        left_spacer.setFixedSize(60, 28)
        header_layout.addWidget(left_spacer)

        self.header_tag = QLabel("@L8PIEST", self.main_container)
        self.header_tag.setObjectName("HeaderTag")
        self.header_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.header_tag, 1)

        # Minimize Button
        self.btn_minimize = QPushButton("—", self.main_container)
        self.btn_minimize.setObjectName("MinimizeButton")
        self.btn_minimize.setFixedSize(28, 28)
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.setToolTip("Minimizar")
        self.btn_minimize.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.btn_minimize)

        # Close Button
        self.btn_close = QPushButton("✕", self.main_container)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Fechar Aplicação")
        self.btn_close.clicked.connect(self.close)
        header_layout.addWidget(self.btn_close)

        container_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. Compact Logo Header
        # -------------------------------------------------------------
        self.logo_label = QLabel(self.main_container)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        container_layout.addWidget(self.logo_label)

        self.title_label = QLabel("LOOPIEST KEYFINDER", self.main_container)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; letter-spacing: 2px;")
        container_layout.addWidget(self.title_label)

        # -------------------------------------------------------------
        # 3. Audio File Reception Area (Drag & Drop Widget)
        # -------------------------------------------------------------
        self.drop_zone = DropZoneWidget(self.main_container)
        self.drop_zone.file_selected.connect(self.handle_file_received)
        self.drop_zone.invalid_file_attempted.connect(self.handle_invalid_file)
        container_layout.addWidget(self.drop_zone, 1)

        # -------------------------------------------------------------
        # 4. File Info, Progress Bar & Result Displays
        # -------------------------------------------------------------
        # Loaded File Label
        self.file_name_label = QLabel("", self.main_container)
        self.file_name_label.setObjectName("FileNameLabel")
        self.file_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_name_label.hide()
        container_layout.addWidget(self.file_name_label)

        # Loading / Status Label
        self.status_label = QLabel("", self.main_container)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        container_layout.addWidget(self.status_label)

        # Progress Bar for Analysis Loading
        self.progress_bar = QProgressBar(self.main_container)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        container_layout.addWidget(self.progress_bar)

        # Mock Analysis Result Display
        self.result_label = QLabel("", self.main_container)
        self.result_label.setObjectName("AnalysisResultLabel")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.hide()
        container_layout.addWidget(self.result_label)

    def load_logo_image(self):
        """Safely load header logo image."""
        try:
            if os.path.exists(self.logo_path):
                pixmap = QPixmap(self.logo_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        100, 100,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    return
        except Exception:
            pass
        self.logo_label.setText("❖")

    def apply_drop_shadow(self):
        """Apply neon purple glow drop shadow effect around main window."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(138, 43, 226, 110))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

    def load_stylesheet(self, qss_path: str):
        """Read and apply QSS theme."""
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as err:
            print(f"[Erro] Falha ao carregar QSS ({err}).")

    def handle_file_received(self, file_path: str):
        """Process valid audio file reception, update UI, and trigger mock analysis worker."""
        file_name = os.path.basename(file_path)

        # Update File Display
        self.file_name_label.setText(f"🎵 Arquivo Selecionado: {file_name}")
        self.file_name_label.show()

        # Reset previous results
        self.result_label.hide()

        # Start Loading Animation
        self.status_label.setText("Iniciando análise de tom...")
        self.status_label.show()
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        # Execute Mock Analysis Worker (3 seconds simulation)
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.analysis_worker.wait()

        self.analysis_worker = AnalysisWorker(file_path=file_path, parent=self)
        self.analysis_worker.status_changed.connect(self.update_analysis_status)
        self.analysis_worker.progress_changed.connect(self.update_analysis_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_finished)
        self.analysis_worker.analysis_failed.connect(self.on_analysis_failed)
        self.analysis_worker.start()

    def handle_invalid_file(self, message: str):
        """Display error when user drops or selects an unsupported file type."""
        self.status_label.setText(f"❌ {message}")
        self.status_label.setStyleSheet("color: #EF4444; font-weight: bold;")
        self.status_label.show()

    def update_analysis_status(self, text: str):
        """Update analysis description label."""
        self.status_label.setStyleSheet("color: #A0A0B8; font-weight: normal;")
        self.status_label.setText(text)

    def update_analysis_progress(self, percent: int):
        """Update analysis progress bar."""
        self.progress_bar.setValue(percent)

    def on_analysis_finished(self, result: dict):
        """Display mock results after 3-second processing completes."""
        self.status_label.hide()
        self.progress_bar.hide()

        output_text = (
            f"✔ Análise Concluída!\n\n"
            f"🎵 Tonalidade: {result['key']}\n"
            f"⚡ BPM: {result['bpm']} | Confiança: {result['confidence']}"
        )
        self.result_label.setText(output_text)
        self.result_label.show()

    def on_analysis_failed(self, error_msg: str):
        """Handle analysis error."""
        self.progress_bar.hide()
        self.status_label.setText(f"❌ Erro na análise: {error_msg}")
        self.status_label.setStyleSheet("color: #EF4444; font-weight: bold;")

    def closeEvent(self, event):
        """Ensure background worker is cleanly terminated on window exit."""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.analysis_worker.wait(1000)
        event.accept()

    # Window Dragging Handlers
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
