"""
LOOPIEST KEYFINDER - Username Registration Screen.
Modern minimalist frameless window to register producer/user handle.
Displayed after passkey validation when no user profile is stored.
"""

import os
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGraphicsDropShadowEffect
)

from src.auth import save_username


class UsernameWindow(QWidget):
    """
    User Registration Window for LOOPIEST KEYFINDER.
    Prompts the user for a producer name/handle and saves it locally.
    """

    registered = Signal(str)

    def __init__(self, logo_path: str, qss_path: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.drag_position = QPoint()

        self.init_window()
        self.init_ui()

        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

        self.apply_drop_shadow()

    def init_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        self.resize(460, 480)

        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
            y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(24, 18, 24, 24)
        container_layout.setSpacing(12)

        # Header Bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        left_spacer = QWidget(self.main_container)
        left_spacer.setFixedSize(28, 28)
        header_layout.addWidget(left_spacer)

        self.header_tag = QLabel(
            '<a href="https://www.instagram.com/l8piest/" style="color: #8A2BE2; text-decoration: none;">@L8PIEST</a>',
            self.main_container
        )
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

        container_layout.addStretch(1)

        # Central Logo / Emblem
        self.logo_label = QLabel(self.main_container)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        container_layout.addWidget(self.logo_label)

        # Title & Subtitle
        self.title_label = QLabel("IDENTIFICAÇÃO", self.main_container)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("P E R F I L   D O   U S U Á R I O", self.main_container)
        self.subtitle_label.setObjectName("AppSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.subtitle_label)

        # Description
        self.desc_label = QLabel(
            "Crie seu nome de usuário ou tag de produtor para personalizar seu ambiente no LOOPIEST KEYFINDER.",
            self.main_container
        )
        self.desc_label.setObjectName("StatusLabel")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        container_layout.addWidget(self.desc_label)

        container_layout.addSpacing(6)

        # Username Input
        self.input_username = QLineEdit(self.main_container)
        self.input_username.setObjectName("UsernameInput")
        self.input_username.setPlaceholderText("Ex: Produtor, Beatmaker, @seu_nome...")
        self.input_username.setMaxLength(32)
        self.input_username.returnPressed.connect(self.attempt_submit)
        container_layout.addWidget(self.input_username)

        # Error Alert Box
        self.alert_error = QLabel(self.main_container)
        self.alert_error.setObjectName("ErrorAlertBox")
        self.alert_error.setWordWrap(True)
        self.alert_error.hide()
        container_layout.addWidget(self.alert_error)

        container_layout.addStretch(1)

        # Confirm Button
        self.btn_submit = QPushButton("CONFIRMAR E ENTRAR", self.main_container)
        self.btn_submit.setObjectName("StartButton")
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setFixedHeight(44)
        self.btn_submit.clicked.connect(self.attempt_submit)
        container_layout.addWidget(self.btn_submit)

    def load_logo_image(self):
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

            self.render_fallback_logo()
        except Exception:
            self.render_fallback_logo()

    def render_fallback_logo(self):
        self.logo_label.setText("❖")
        self.logo_label.setStyleSheet("""
            color: #8A2BE2;
            font-size: 38px;
            font-weight: bold;
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

    def attempt_submit(self):
        username = self.input_username.text().strip()
        if not username:
            self.show_error("Por favor, informe seu nome de usuário.")
            return

        if len(username) < 2:
            self.show_error("O nome de usuário deve conter pelo menos 2 caracteres.")
            return

        # Save username to user.txt in software root on C:
        save_username(username)

        self.registered.emit(username)
        self.close()

    def show_error(self, message: str):
        self.alert_error.setText(f"⚠️ {message}")
        self.alert_error.show()

    def close_application(self):
        self.close()
        QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
