"""
LOOPIEST KEYFINDER - Login & Passkey Authentication Screen.
Minimalist frameless login window with purple dark aesthetic.
Focused exclusively on the passkey entry without exposing internal specifications.
"""

import os
from PySide6.QtCore import Qt, QPoint, Signal, QTimer
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QGraphicsDropShadowEffect
)

from src.auth import (
    validate_passkey,
    get_saved_passkey,
    save_passkey,
    clear_saved_passkey
)


class LoginWindow(QWidget):
    """
    Clean Minimalist Frameless Login Screen.
    Displays only the passkey input field, paste button, and unlock action.
    """

    authenticated = Signal(str)

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
        self.check_saved_passkey()

    def init_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        self.resize(440, 360)

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

        # Central Logo / Header Icon
        self.logo_label = QLabel(self.main_container)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        container_layout.addWidget(self.logo_label)

        container_layout.addSpacing(14)

        # Passkey Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_key = QLineEdit(self.main_container)
        self.input_key.setObjectName("PasskeyInput")
        self.input_key.setPlaceholderText("Passkey...")
        self.input_key.setMaxLength(24)
        self.input_key.textChanged.connect(self.on_text_changed)
        self.input_key.returnPressed.connect(self.attempt_login)
        input_row.addWidget(self.input_key, 1)

        self.btn_paste = QPushButton("📋 Colar", self.main_container)
        self.btn_paste.setObjectName("PasteButton")
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.setToolTip("Colar chave da área de transferência")
        self.btn_paste.clicked.connect(self.paste_from_clipboard)
        input_row.addWidget(self.btn_paste)

        container_layout.addLayout(input_row)

        # Alert Box for Feedback (Error only)
        self.alert_error = QLabel(self.main_container)
        self.alert_error.setObjectName("ErrorAlertBox")
        self.alert_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_error.setWordWrap(True)
        self.alert_error.hide()
        container_layout.addWidget(self.alert_error)

        # Remember Me Option
        self.check_remember = QCheckBox("Lembrar neste computador (Login Automático)", self.main_container)
        self.check_remember.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_remember.setChecked(True)
        container_layout.addWidget(self.check_remember)

        container_layout.addStretch(1)

        # Unlock / Submit Button
        self.btn_unlock = QPushButton("ENTRAR", self.main_container)
        self.btn_unlock.setObjectName("StartButton")
        self.btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_unlock.setFixedHeight(44)
        self.btn_unlock.clicked.connect(self.attempt_login)
        container_layout.addWidget(self.btn_unlock)

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

    def check_saved_passkey(self):
        saved_key = get_saved_passkey()
        if saved_key:
            self.input_key.setText(saved_key)
            self.check_remember.setChecked(True)

    def on_text_changed(self, text: str):
        clean_text = text.strip().upper()
        if clean_text != text:
            cursor_pos = self.input_key.cursorPosition()
            self.input_key.blockSignals(True)
            self.input_key.setText(clean_text)
            self.input_key.setCursorPosition(cursor_pos)
            self.input_key.blockSignals(False)

        self.alert_error.hide()

    def paste_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text().strip().upper()
        if text:
            self.input_key.setText(text)
            self.attempt_login()

    def attempt_login(self):
        key = self.input_key.text().strip().upper()
        if not key:
            self.show_error("Insira sua passkey.")
            return

        is_valid, _, _ = validate_passkey(key)

        if not is_valid:
            self.show_error("Chave inválida.")
            return

        # Handle persistence
        if self.check_remember.isChecked():
            save_passkey(key)
        else:
            clear_saved_passkey()

        # Success state
        self.alert_error.hide()
        self.btn_unlock.setEnabled(False)
        self.btn_unlock.setText("ENTRANDO...")

        # Smooth transition to Next Step
        QTimer.singleShot(250, lambda: self.finish_authentication(key))

    def finish_authentication(self, key: str):
        self.authenticated.emit(key)
        self.close()

    def show_error(self, message: str = "Chave inválida."):
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
