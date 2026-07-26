"""
LOOPIEST KEYFINDER - Splash Screen Module.
Minimalist frameless splash screen with purple dark aesthetic.
"""

import os
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGraphicsDropShadowEffect
)

from src.worker import LoadingWorker


class SplashScreen(QWidget):
    """
    Modern Minimalist Splash Screen with frameless window design.
    """

    start_requested = Signal()

    def __init__(self, logo_path: str, qss_path: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.drag_position = QPoint()
        self.worker = None

        self.init_window()
        self.init_ui()

        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

        self.apply_drop_shadow()
        self.start_worker()

    def init_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        self.resize(450, 550)

        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 16, 20, 24)
        container_layout.setSpacing(12)

        # Header Bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        left_spacer = QWidget(self.main_container)
        left_spacer.setFixedSize(28, 28)
        header_layout.addWidget(left_spacer)

        self.header_tag = QLabel('<a href="https://www.instagram.com/l8piest/" style="color: #8A2BE2; text-decoration: none;">@L8PIEST</a>', self.main_container)
        self.header_tag.setObjectName("HeaderTag")
        self.header_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_tag.setOpenExternalLinks(True)
        self.header_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self.header_tag, 1)

        self.btn_close = QPushButton("✕", self.main_container)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Fechar Aplicação")
        self.btn_close.clicked.connect(self.close_application)
        header_layout.addWidget(self.btn_close)

        container_layout.addLayout(header_layout)

        # Central Logo Section
        container_layout.addStretch(1)

        self.logo_label = QLabel(self.main_container)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        container_layout.addWidget(self.logo_label)

        self.title_label = QLabel("LOOPIEST", self.main_container)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("K E Y F I N D E R", self.main_container)
        self.subtitle_label.setObjectName("AppSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.subtitle_label)
        container_layout.addStretch(1)

        # Progress Section
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

        self.progress_bar = QProgressBar(self.main_container)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        container_layout.addWidget(self.progress_bar)

        self.btn_start = QPushButton("INICIAR", self.main_container)
        self.btn_start.setObjectName("StartButton")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setFixedHeight(44)
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_start.hide()
        container_layout.addWidget(self.btn_start)

    def load_logo_image(self):
        try:
            if os.path.exists(self.logo_path):
                pixmap = QPixmap(self.logo_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        200, 200,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    return

            self.render_fallback_logo("LOOPIEST")
        except Exception:
            self.render_fallback_logo("LOOPIEST")

    def render_fallback_logo(self, message: str):
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
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(138, 43, 226, 120))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

    def load_stylesheet(self, qss_path: str):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as err:
            print(f"[Erro] Falha ao carregar QSS ({err}).")

    def start_worker(self):
        self.worker = LoadingWorker(self)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.status_changed.connect(self.update_status)
        self.worker.loading_complete.connect(self.on_loading_complete)
        self.worker.start()

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.percentage_label.setText(f"{value}%")

    def update_status(self, text: str):
        self.status_label.setText(text)

    def on_loading_complete(self):
        self.status_label.setText("Sistema pronto!")
        self.percentage_label.hide()
        self.progress_bar.hide()
        self.btn_start.show()

    def on_start_clicked(self):
        self.start_requested.emit()
        self.close()

    def close_application(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
