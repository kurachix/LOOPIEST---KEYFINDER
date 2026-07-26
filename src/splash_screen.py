"""
Splash Screen GUI Module using PySide6.
Features:
- Frameless, translucent background with rounded corners and drop shadow.
- Central logo display with exception/fallback handling.
- Drag-and-drop window positioning.
- Modern dark/neon purple QSS aesthetic.
- Asynchronous progress updating via LoadingWorker thread.
"""

import os
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGraphicsDropShadowEffect
)

from src.worker import LoadingWorker


class SplashScreen(QWidget):
    """
    Modern Minimalist Splash Screen with frameless window design,
    custom purple/neon dark palette, and animated progress loading.
    """

    def __init__(self, logo_path: str, qss_path: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.drag_position = QPoint()
        self.worker = None

        # Setup Window Flags & Geometry
        self.init_window()

        # Build UI Elements
        self.init_ui()

        # Load QSS Stylesheet
        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

        # Apply Drop Shadow Effect
        self.apply_drop_shadow()

        # Start Worker Thread
        self.start_worker()

    def init_window(self):
        """Configure frameless window properties, taskbar icon, and screen centering."""
        # Frameless and translucent background for rounded corners
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set Window Taskbar Icon
        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        # Fixed compact size
        self.resize(450, 550)

        # Center on primary screen
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        """Construct all UI widgets and layout hierarchy."""
        # Outer main container for QSS background styling
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)  # Margin for drop shadow
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 16, 20, 24)
        container_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Top Header Bar (Centered @L8PIEST & Close Button 'X')
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left dummy spacer matching close button width for exact centering
        left_spacer = QWidget(self.main_container)
        left_spacer.setFixedSize(28, 28)
        header_layout.addWidget(left_spacer)

        # Centered Tag Label
        self.header_tag = QLabel("@L8PIEST", self.main_container)
        self.header_tag.setObjectName("HeaderTag")
        self.header_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.header_tag, 1)

        # Right Close Button
        self.btn_close = QPushButton("✕", self.main_container)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Fechar Aplicação")
        self.btn_close.clicked.connect(self.close_application)
        header_layout.addWidget(self.btn_close)

        container_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. Central Logo & Title Section
        # -------------------------------------------------------------
        container_layout.addStretch(1)

        self.logo_label = QLabel(self.main_container)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        container_layout.addWidget(self.logo_label)

        # App Title Text
        self.title_label = QLabel("LOOPIEST", self.main_container)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("K E Y F I N D E R", self.main_container)
        self.subtitle_label.setObjectName("AppSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.subtitle_label)
        container_layout.addStretch(1)

        # -------------------------------------------------------------
        # 3. Loading Animation & Progress Bar Section
        # -------------------------------------------------------------
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(4, 0, 4, 0)

        self.status_label = QLabel("Inicializando...", self.main_container)
        self.status_label.setObjectName("StatusLabel")

        self.percentage_label = QLabel("0%", self.main_container)
        self.percentage_label.setObjectName("PercentageLabel")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.percentage_label)

        container_layout.addLayout(status_layout)

        # Progress Bar
        self.progress_bar = QProgressBar(self.main_container)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        container_layout.addWidget(self.progress_bar)

    def load_logo_image(self):
        """Safely load and display logo with exception handling and fallback."""
        try:
            if os.path.exists(self.logo_path):
                pixmap = QPixmap(self.logo_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        220, 220,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    return
            
            # Fallback if image path is invalid or corrupted
            self.render_fallback_logo("LOGO NÃO ENCONTRADA")
        except Exception as err:
            print(f"[Aviso] Falha ao carregar logo ({err}). Utilizando fallback.")
            self.render_fallback_logo("ERRO LOGO")

    def render_fallback_logo(self, message: str):
        """Render a stylized vector/text placeholder if logo fails to load."""
        self.logo_label.setText(f"❖\n{message}")
        self.logo_label.setStyleSheet("""
            color: #8A2BE2;
            font-size: 16px;
            font-weight: bold;
            border: 2px dashed #2D0B5A;
            border-radius: 12px;
            padding: 30px;
        """)

    def apply_drop_shadow(self):
        """Apply a sleek neon purple glow/drop shadow around the frameless container."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(138, 43, 226, 120))  # #8A2BE2 with translucent alpha
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

    def load_stylesheet(self, qss_path: str):
        """Read and apply external QSS stylesheet."""
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as err:
            print(f"[Erro] Não foi possível carregar o arquivo QSS ({err}).")

    def start_worker(self):
        """Instantiate and start the background loading thread."""
        self.worker = LoadingWorker(self)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.status_changed.connect(self.update_status)
        self.worker.loading_complete.connect(self.on_loading_complete)
        self.worker.start()

    def update_progress(self, value: int):
        """Update progress bar value and percentage text."""
        self.progress_bar.setValue(value)
        self.percentage_label.setText(f"{value}%")

    def update_status(self, text: str):
        """Update status description text."""
        self.status_label.setText(text)

    def on_loading_complete(self):
        """Triggered when background loading reaches 100%."""
        self.status_label.setText("Pronto para iniciar!")
        # Brief timeout before launching main application logic / closing splash
        # In a real app, this would trigger opening the main window.

    def close_application(self):
        """Clean shutdown handler for the close button."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
        self.close()

    # -------------------------------------------------------------
    # Drag and Drop Window Movement (Frameless Support)
    # -------------------------------------------------------------
    def mousePressEvent(self, event):
        """Record initial position when left mouse button is pressed."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Drag window to new cursor position while left mouse button is held."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
