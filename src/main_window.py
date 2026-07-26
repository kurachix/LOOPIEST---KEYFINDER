"""
Main Application Window for LOOPIEST - KEYFINDER.
Provides sleek commercial UI with Page Navigation (QStackedWidget):
- Page 0: Audio File Reception (Drag & Drop)
- Page 1: Clean Key Result Display (Primary Key, Relative Key, Formatted Duration)
"""

import os
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGraphicsDropShadowEffect,
    QStackedWidget, QFrame
)

from src.drop_zone import DropZoneWidget
from src.worker import AnalysisWorker


def formatar_duracao(duracao_segundos: float) -> str:
    """Format duration in seconds to minutes and seconds string (e.g. 3m 05s)."""
    minutos = int(duracao_segundos // 60)
    segundos = int(round(duracao_segundos % 60))
    if segundos == 60:
        minutos += 1
        segundos = 0
    return f"{minutos}m {segundos:02d}s"


class MainWindow(QWidget):
    """
    Main Frameless Application Window containing stacked pages for:
    - Page 0: Audio File Reception (Drag & Drop + Loading)
    - Page 1: Streamlined Key Analysis Result (Tonalidade & Informações do Arquivo)
    """

    def __init__(self, logo_path: str, qss_path: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.drag_position = QPoint()
        self.analysis_worker = None

        # Window Setup
        self.init_window()

        # UI Hierarchy
        self.init_ui()

        # Load QSS Styles
        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

        # Apply Drop Shadow Glow
        self.apply_drop_shadow()

    def init_window(self):
        """Configure frameless window, taskbar icon, and screen centering."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        self.resize(480, 580)

        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        """Construct window widgets, header with perfectly centered @L8PIEST tag and Close 'X' button."""
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 16, 20, 24)
        container_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Top Header Bar (Perfectly Centered @L8PIEST & Single Close 'X' Button)
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Left Dummy Spacer matching Close Button size (28x28) for exact horizontal centering
        self.left_spacer = QWidget(self.main_container)
        self.left_spacer.setFixedSize(28, 28)
        header_layout.addWidget(self.left_spacer)

        # Centered Header Tag
        self.header_tag = QLabel('<a href="https://www.instagram.com/l8piest/" style="color: #8A2BE2; text-decoration: none;">@L8PIEST</a>', self.main_container)
        self.header_tag.setObjectName("HeaderTag")
        self.header_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_tag.setOpenExternalLinks(True)
        self.header_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self.header_tag, 1)

        # Close Button 'X'
        self.btn_close = QPushButton("✕", self.main_container)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Fechar Aplicação")
        self.btn_close.clicked.connect(self.close)
        header_layout.addWidget(self.btn_close)

        container_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. QStackedWidget for Multi-Page Navigation
        # -------------------------------------------------------------
        self.stacked_widget = QStackedWidget(self.main_container)
        container_layout.addWidget(self.stacked_widget, 1)

        # Build Page 0 (Reception / Drop Zone) and Page 1 (Results)
        self.page_reception = self.create_reception_page()
        self.page_results = self.create_results_page()

        self.stacked_widget.addWidget(self.page_reception)  # Index 0
        self.stacked_widget.addWidget(self.page_results)    # Index 1

        self.stacked_widget.setCurrentIndex(0)

    # -------------------------------------------------------------
    # Page 0 Construction: Audio Reception Page
    # -------------------------------------------------------------
    def create_reception_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        # Logo Header
        self.logo_label = QLabel(page)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        layout.addWidget(self.logo_label)

        self.title_label = QLabel("LOOPIEST KEYFINDER", page)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; letter-spacing: 2px;")
        layout.addWidget(self.title_label)

        # Drop Zone Component
        self.drop_zone = DropZoneWidget(page)
        self.drop_zone.file_selected.connect(self.handle_file_received)
        self.drop_zone.invalid_file_attempted.connect(self.show_error_alert)
        layout.addWidget(self.drop_zone, 1)

        # Selected File Label
        self.file_name_label = QLabel("", page)
        self.file_name_label.setObjectName("FileNameLabel")
        self.file_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_name_label.hide()
        layout.addWidget(self.file_name_label)

        # Status & Progress Indicators
        self.status_label = QLabel("", page)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(page)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Visual Error Alert Box
        self.error_alert_box = QLabel("", page)
        self.error_alert_box.setObjectName("ErrorAlertBox")
        self.error_alert_box.setWordWrap(True)
        self.error_alert_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_alert_box.hide()
        layout.addWidget(self.error_alert_box)

        return page

    # -------------------------------------------------------------
    # Page 1 Construction: Streamlined Analysis Results View
    # -------------------------------------------------------------
    def create_results_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)

        layout.addStretch(1)

        # 1. Primary & Secondary Detected Key Card
        self.key_card = QFrame(page)
        self.key_card.setObjectName("KeyHighlightCard")
        key_layout = QVBoxLayout(self.key_card)
        key_layout.setContentsMargins(20, 24, 20, 24)
        key_layout.setSpacing(10)

        card_title = QLabel("TONALIDADE DETECTADA", self.key_card)
        card_title.setObjectName("SectionTitle")
        card_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Primary Key (Bold Glowing Neon Text)
        self.key_highlight_label = QLabel("Key: --", self.key_card)
        self.key_highlight_label.setObjectName("KeyTextHighlight")
        self.key_highlight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Relative Key (Escala Equivalente)
        self.relative_key_label = QLabel("Escala Equivalente: --", self.key_card)
        self.relative_key_label.setObjectName("RelativeKeyLabel")
        self.relative_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # BPM Display (Beats Per Minute)
        self.bpm_label = QLabel("BPM: --", self.key_card)
        self.bpm_label.setObjectName("BpmLabel")
        self.bpm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Secondary Alternative Key (Shown only if high ambiguity exists)
        self.secondary_key_label = QLabel("", self.key_card)
        self.secondary_key_label.setObjectName("KeySubtext")
        self.secondary_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secondary_key_label.hide()

        key_layout.addWidget(card_title)
        key_layout.addWidget(self.key_highlight_label)
        key_layout.addWidget(self.relative_key_label)
        key_layout.addWidget(self.bpm_label)
        key_layout.addWidget(self.secondary_key_label)

        layout.addWidget(self.key_card)

        # 2. Streamlined File Metadata Box (Arquivo e Duração em min/seg)
        self.metadata_label = QLabel("", page)
        self.metadata_label.setObjectName("AudioMetadataBox")
        self.metadata_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.metadata_label)

        layout.addStretch(1)

        # Button to Analyze Another Song
        self.btn_analyze_another = QPushButton("Analisar Outro Arquivo", page)
        self.btn_analyze_another.setObjectName("StartButton")
        self.btn_analyze_another.setFixedHeight(44)
        self.btn_analyze_another.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_analyze_another.clicked.connect(self.go_to_reception_page)
        layout.addWidget(self.btn_analyze_another)

        return page

    def load_logo_image(self):
        """Safely load header logo image."""
        try:
            if os.path.exists(self.logo_path):
                pixmap = QPixmap(self.logo_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        90, 90,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    return
        except Exception:
            pass
        self.logo_label.setText("❖")

    def apply_drop_shadow(self):
        """Apply neon purple drop shadow effect around container."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(138, 43, 226, 120))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

    def load_stylesheet(self, qss_path: str):
        """Read and apply QSS theme."""
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as err:
            print(f"[Erro] Falha ao carregar QSS ({err}).")

    # -------------------------------------------------------------
    # Navigation & Flow Methods
    # -------------------------------------------------------------
    def go_to_reception_page(self):
        """Switch view back to Audio Reception (Page 0)."""
        self.error_alert_box.hide()
        self.status_label.hide()
        self.progress_bar.hide()
        self.file_name_label.hide()
        self.stacked_widget.setCurrentIndex(0)

    def go_to_results_page(self, result: dict):
        """Populate results data and switch view to Analysis Results (Page 1)."""
        # Primary Key
        key_name = result.get("key", "Indefinida")
        self.key_highlight_label.setText(f"Key: {key_name}")

        # Relative Key (Escala Equivalente / Tom Relativo)
        relative_key = result.get("relative_key", "")
        if not relative_key:
            from src.key_detector import obter_escala_relativa
            relative_key = obter_escala_relativa(key_name)

        if relative_key:
            self.relative_key_label.setText(f"Escala Equivalente: {relative_key}")
            self.relative_key_label.show()
        else:
            self.relative_key_label.hide()

        # BPM Display
        bpm_val = result.get("bpm", "--")
        self.bpm_label.setText(f"BPM: {bpm_val}")
        self.bpm_label.show()

        # Check Ambiguity: Display a 2nd result ONLY if there is high ambiguity between top 2 candidates
        top_candidatos = result.get("top_candidatos", [])
        if len(top_candidatos) >= 2:
            score1 = top_candidatos[0].get("score", 0.0)
            score2 = top_candidatos[1].get("score", 0.0)
            
            if (score1 - score2) < 0.08 and score2 > 0.4:
                alt_key = top_candidatos[1].get("key_name", "")
                self.secondary_key_label.setText(f"Alternativa Provável: {alt_key}")
                self.secondary_key_label.show()
            else:
                self.secondary_key_label.hide()
        else:
            self.secondary_key_label.hide()

        # Clean File & Formatted Duration (e.g. 3m 05s)
        file_name = result.get("file_name", "Desconhecido")
        duration_sec = result.get("duration_sec", 0.0)
        formatted_duration = formatar_duracao(duration_sec)
        self.metadata_label.setText(f"Arquivo: {file_name}   |   Duração: {formatted_duration}")

        # Switch to Results Page
        self.stacked_widget.setCurrentIndex(1)

    # -------------------------------------------------------------
    # Audio Receiver Handlers & Worker Management
    # -------------------------------------------------------------
    def handle_file_received(self, file_path: str):
        """Start audio processing worker in background QThread."""
        self.error_alert_box.hide()

        file_name = os.path.basename(file_path)
        self.file_name_label.setText(f"Arquivo Selecionado: {file_name}")
        self.file_name_label.show()

        self.status_label.setText("Iniciando análise...")
        self.status_label.show()
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.analysis_worker.wait()

        self.analysis_worker = AnalysisWorker(file_path=file_path, parent=self)
        self.analysis_worker.status_changed.connect(self.update_analysis_status)
        self.analysis_worker.progress_changed.connect(self.update_analysis_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_finished)
        self.analysis_worker.analysis_failed.connect(self.show_error_alert)
        self.analysis_worker.start()

    def update_analysis_status(self, text: str):
        """Update status description during background thread execution."""
        self.status_label.setText(text)

    def update_analysis_progress(self, percent: int):
        """Update progress bar value."""
        self.progress_bar.setValue(percent)

    def on_analysis_finished(self, result: dict):
        """Called when background worker completes analysis successfully."""
        self.status_label.hide()
        self.progress_bar.hide()
        self.go_to_results_page(result)

    def show_error_alert(self, message: str):
        """Display visual red alert box on interface if file or processing fails."""
        self.status_label.hide()
        self.progress_bar.hide()
        self.error_alert_box.setText(f"⚠️ {message}")
        self.error_alert_box.show()

    def closeEvent(self, event):
        """Clean shutdown handler for background threads on exit."""
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
