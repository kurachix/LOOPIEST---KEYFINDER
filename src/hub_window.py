"""
LOOPIEST SUITE - Software Selection Hub (Central de Softwares).
Frameless modern dark/neon hub allowing producers to select and launch tools:
- LOOPIEST KEYFINDER (Available)
- Future Suite Tools (Stem Separator, Mastering Rack - Coming Soon)
Features animated interactive vinyl discs with smooth rotation and modern aesthetics.
"""

import os
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPixmap, QColor, QIcon, QGuiApplication, QPainter,
    QPainterPath, QPen, QBrush, QLinearGradient, QRadialGradient, QFont
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)


class DiscWidget(QWidget):
    """
    Circular Interactive Vinyl Disc Widget.
    Renders high-resolution disc artwork inside a perfect circular mask,
    with an outer neon glow ring and smooth turntable rotation on hover.
    """

    clicked = Signal()

    def __init__(
        self,
        image_path: str,
        size: int = 150,
        border_color: str = "#8A2BE2",
        is_interactive: bool = True,
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.image_path = image_path
        self.disc_size = size
        self.border_color = QColor(border_color)
        self.is_interactive = is_interactive

        self.rotation_angle = 0.0
        self.is_hovered = False

        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor if is_interactive else Qt.CursorShape.ArrowCursor)

        # Load pixmap
        self.pixmap = QPixmap()
        self.load_disc_image()

        # Turntable spin animation timer (approx 40 FPS)
        self.spin_timer = QTimer(self)
        self.spin_timer.setInterval(25)
        self.spin_timer.timeout.connect(self._step_rotation)

    def load_disc_image(self):
        if os.path.exists(self.image_path):
            loaded = QPixmap(self.image_path)
            if not loaded.isNull():
                self.pixmap = loaded.scaled(
                    self.disc_size * 2,
                    self.disc_size * 2,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

    def _step_rotation(self):
        # 1.2 degrees per tick gives a smooth, hypnotic vinyl turntable spin
        self.rotation_angle = (self.rotation_angle + 1.2) % 360.0
        self.update()

    def start_spinning(self):
        if not self.spin_timer.isActive():
            self.spin_timer.start()

    def stop_spinning(self):
        if self.spin_timer.isActive():
            self.spin_timer.stop()

    def enterEvent(self, event):
        self.is_hovered = True
        if self.is_interactive:
            self.start_spinning()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        if self.is_interactive:
            self.stop_spinning()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        margin = 4.0
        draw_size = min(self.width(), self.height()) - (margin * 2.0)
        radius = draw_size / 2.0
        center = QPointF(self.width() / 2.0, self.height() / 2.0)

        # 1. Subtle Outer Glow when hovered
        if self.is_hovered and self.is_interactive:
            glow_gradient = QRadialGradient(center, radius + 4.0)
            glow_gradient.setColorAt(0.85, QColor(138, 43, 226, 120))
            glow_gradient.setColorAt(1.0, QColor(138, 43, 226, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_gradient))
            painter.drawEllipse(center, radius + 4.0, radius + 4.0)

        # 2. Circular Clipping Path for the Vinyl Disc
        clip_path = QPainterPath()
        clip_path.addEllipse(center, radius, radius)

        painter.save()
        painter.setClipPath(clip_path)

        # Rotate around the disc center
        painter.translate(center)
        painter.rotate(self.rotation_angle)
        painter.translate(-center)

        if not self.pixmap.isNull():
            target_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2.0, radius * 2.0)
            painter.drawPixmap(target_rect.toRect(), self.pixmap)
        else:
            self._draw_fallback_vinyl(painter, center, radius)

        painter.restore()

        # 3. Outer Neon Ring Border
        ring_color = self.border_color
        if self.is_hovered and self.is_interactive:
            ring_color = QColor("#B066FE")
        elif not self.is_interactive:
            ring_color = QColor("#3B166A")

        pen = QPen(ring_color, 2.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)

        # 4. Spindle Hole Center Accent
        hole_radius = radius * 0.08
        painter.setPen(QPen(QColor(10, 10, 14), 1.5))
        painter.setBrush(QBrush(QColor(14, 14, 20)))
        painter.drawEllipse(center, hole_radius, hole_radius)

    def _draw_fallback_vinyl(self, painter: QPainter, center: QPointF, radius: float):
        """Vector fallback in case the image asset is missing."""
        # Dark vinyl base
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#0F0F14")))
        painter.drawEllipse(center, radius, radius)

        # Concentric grooves
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen_groove = QPen(QColor(45, 11, 90, 70), 1.0)
        painter.setPen(pen_groove)
        for r in range(int(radius * 0.4), int(radius), 4):
            painter.drawEllipse(center, float(r), float(r))

        # Center label
        label_r = radius * 0.38
        painter.setPen(QPen(QColor("#8A2BE2"), 1.5))
        painter.setBrush(QBrush(QColor("#1A0E2E")))
        painter.drawEllipse(center, label_r, label_r)


class SoftwareCardWidget(QFrame):
    """
    Interactive Software Selection Card featuring the Vinyl Disc,
    Status Badge, Title, Category Tag, Description and Action Button.
    """

    launch_requested = Signal(str)
    locked_clicked = Signal(str)

    def __init__(
        self,
        software_id: str,
        title: str,
        category: str,
        description: str,
        badge_text: str,
        disc_image_path: str,
        is_available: bool = True,
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.software_id = software_id
        self.software_title = title
        self.is_available = is_available
        self.disc_image_path = disc_image_path

        self.setObjectName("HubCard" if is_available else "HubCardLocked")
        self.setFixedWidth(240)
        self.setMinimumHeight(410)
        self.setCursor(Qt.CursorShape.PointingHandCursor if is_available else Qt.CursorShape.ArrowCursor)

        self.init_ui(title, category, description, badge_text)

    def init_ui(self, title: str, category: str, description: str, badge_text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 18)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # 1. Status Badge
        self.badge_label = QLabel(badge_text, self)
        self.badge_label.setObjectName("BadgeAvailable" if self.is_available else "BadgeLocked")
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.badge_label)

        layout.addSpacing(4)

        # 2. Vinyl Disc Component
        border_color = "#8A2BE2" if self.is_available else "#3B166A"
        self.disc_widget = DiscWidget(
            image_path=self.disc_image_path,
            size=150,
            border_color=border_color,
            is_interactive=self.is_available,
            parent=self
        )
        self.disc_widget.clicked.connect(self._handle_action)
        layout.addWidget(self.disc_widget, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(6)

        # 3. Category Tag
        self.tag_label = QLabel(category.upper(), self)
        self.tag_label.setObjectName("HubCardCategory")
        self.tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.tag_label)

        # 4. Software Title
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("HubCardTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # 5. Description
        self.desc_label = QLabel(description, self)
        self.desc_label.setObjectName("HubCardDesc")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumHeight(48)
        layout.addWidget(self.desc_label)

        layout.addStretch(1)

        # 6. Action Button
        if self.is_available:
            self.action_button = QPushButton("EXECUTAR", self)
            self.action_button.setObjectName("StartButton")
            self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.action_button.setFixedHeight(38)
            self.action_button.clicked.connect(self._handle_action)
        else:
            self.action_button = QPushButton("EM BREVE", self)
            self.action_button.setObjectName("HubDisabledButton")
            self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.action_button.setFixedHeight(38)
            self.action_button.clicked.connect(self._handle_action)

        layout.addWidget(self.action_button)

    def _handle_action(self):
        if self.is_available:
            self.launch_requested.emit(self.software_id)
        else:
            self.locked_clicked.emit(self.software_title)

    def enterEvent(self, event):
        if self.is_available:
            self.disc_widget.start_spinning()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_available:
            self.disc_widget.stop_spinning()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_action()
            event.accept()
        else:
            super().mousePressEvent(event)


class SoftwareHubWindow(QWidget):
    """
    Central Software Hub Window for the LOOPIEST Suite.
    Allows authenticated producers to choose which software tool to execute.
    Currently LOOPIEST KEYFINDER is active, with upcoming tools showcased with disc art.
    """

    software_selected = Signal(str)

    def __init__(self, logo_path: str, qss_path: str = None, passkey: str = None, username: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.passkey = passkey
        self.username = username or "Produtor"
        self.drag_position = QPoint()
        self.is_pinned = False

        self.init_window()
        self.init_ui()

        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

        self.apply_drop_shadow()

    def init_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))

        # Balanced wide dashboard size
        self.resize(870, 610)

        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            x = screen_geom.x() + (screen_geom.width() - self.width()) // 2
            y = screen_geom.y() + (screen_geom.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(24, 18, 24, 22)
        container_layout.setSpacing(12)

        # ---------------------------------------------------------
        # 1. Header Bar
        # ---------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # User profile chip on the left
        user_display = self.username.upper()
        self.user_chip = QLabel(f"🎧 PRODUTOR: {user_display}  <span style='color: #00E676;'>● VIP</span>", self.main_container)
        self.user_chip.setObjectName("HubUserChip")
        if self.passkey:
            self.user_chip.setToolTip(f"Licença Ativa: {self.passkey}\nUsuário Registrado: {self.username}")
        header_layout.addWidget(self.user_chip)

        header_layout.addStretch(1)

        # Centered Instagram Tag
        self.header_tag = QLabel(
            '<a href="https://www.instagram.com/l8piest/" style="color: #8A2BE2; text-decoration: none;">@L8PIEST</a>',
            self.main_container
        )
        self.header_tag.setObjectName("HeaderTag")
        self.header_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_tag.setOpenExternalLinks(True)
        self.header_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self.header_tag)

        header_layout.addStretch(1)

        # Window Action Controls
        self.btn_pin = QPushButton("📌", self.main_container)
        self.btn_pin.setObjectName("PinButton")
        self.btn_pin.setFixedSize(28, 28)
        self.btn_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pin.setToolTip("Fixar Janela no Topo")
        self.btn_pin.setStyleSheet("color: #8E8EA0; font-size: 13px; border: none; background: transparent;")
        self.btn_pin.clicked.connect(self.toggle_pin)
        header_layout.addWidget(self.btn_pin)

        self.btn_min = QPushButton("—", self.main_container)
        self.btn_min.setObjectName("MinButton")
        self.btn_min.setFixedSize(28, 28)
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.setToolTip("Minimizar")
        self.btn_min.setStyleSheet("color: #8E8EA0; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        self.btn_min.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.btn_min)

        self.btn_close = QPushButton("✕", self.main_container)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Fechar Aplicação")
        self.btn_close.clicked.connect(self.close_application)
        header_layout.addWidget(self.btn_close)

        container_layout.addLayout(header_layout)

        # ---------------------------------------------------------
        # 2. Hero Title Section
        # ---------------------------------------------------------
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("LOOPIEST SUITE", self.main_container)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("C E N T R A L   D E   F E R R A M E N T A S", self.main_container)
        self.subtitle_label.setObjectName("AppSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtext_label = QLabel(
            "Selecione o software que deseja executar para a sua sessão de estúdio:",
            self.main_container
        )
        self.subtext_label.setObjectName("StatusLabel")
        self.subtext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        title_box.addWidget(self.subtext_label)
        container_layout.addLayout(title_box)

        container_layout.addSpacing(6)

        # ---------------------------------------------------------
        # 3. Software Disc Cards Row
        # ---------------------------------------------------------
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(18)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        base_assets = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        disc_keyfinder_img = os.path.join(base_assets, "disc_keyfinder.jpg")
        disc_coming_soon_img = os.path.join(base_assets, "disc_coming_soon.jpg")

        # 1. LOOPIEST KEYFINDER (Disponível)
        self.card_keyfinder = SoftwareCardWidget(
            software_id="keyfinder",
            title="KEYFINDER",
            category="Detector de Escala & BPM",
            description="Detecção algorítmica de tonalidade, escala relativa, BPM e renomeador automático de arquivos.",
            badge_text="● DISPONÍVEL",
            disc_image_path=disc_keyfinder_img,
            is_available=True,
            parent=self.main_container
        )
        self.card_keyfinder.launch_requested.connect(self.on_launch_software)
        cards_layout.addWidget(self.card_keyfinder)

        # 2. LOOPIEST STEM SEPARATOR (Em Breve)
        self.card_stems = SoftwareCardWidget(
            software_id="stems",
            title="STEM SEPARATOR",
            category="Isolamento por IA",
            description="Separação cirúrgica de vocais, bateria, baixo e sintetizadores em stems limpos de alta definição.",
            badge_text="🔒 EM BREVE",
            disc_image_path=disc_coming_soon_img,
            is_available=False,
            parent=self.main_container
        )
        self.card_stems.locked_clicked.connect(self.show_locked_feedback)
        cards_layout.addWidget(self.card_stems)

        # 3. LOOPIEST MASTERING RACK (Em Breve)
        self.card_mastering = SoftwareCardWidget(
            software_id="mastering",
            title="MASTERING RACK",
            category="Loudness & Dinâmica",
            description="Cadeia de saturação analógica, limitador de pico e medição LUFS precisa para plataformas de streaming.",
            badge_text="🔒 EM BREVE",
            disc_image_path=disc_coming_soon_img,
            is_available=False,
            parent=self.main_container
        )
        self.card_mastering.locked_clicked.connect(self.show_locked_feedback)
        cards_layout.addWidget(self.card_mastering)

        container_layout.addLayout(cards_layout)

        container_layout.addStretch(1)

        # ---------------------------------------------------------
        # 4. Toast / Feedback Notification Bar
        # ---------------------------------------------------------
        self.toast_label = QLabel("", self.main_container)
        self.toast_label.setObjectName("HubToast")
        self.toast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast_label.hide()
        container_layout.addWidget(self.toast_label)

        # Timer to auto-hide the toast
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast_label.hide)

    def show_locked_feedback(self, software_title: str):
        self.toast_label.setText(
            f"🔒 O software '{software_title}' está em desenvolvimento e será liberado para sua chave em breve!"
        )
        self.toast_label.show()
        self.toast_timer.start(4500)

    def on_launch_software(self, software_id: str):
        self.toast_label.hide()
        self.software_selected.emit(software_id)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        flags = self.windowFlags()
        if self.is_pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self.btn_pin.setStyleSheet("color: #00E676; font-size: 13px; border: none; background: transparent;")
            self.btn_pin.setToolTip("Desafixar Janela (Janela Fixada)")
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
            self.btn_pin.setStyleSheet("color: #8E8EA0; font-size: 13px; border: none; background: transparent;")
            self.btn_pin.setToolTip("Fixar Janela no Topo")

        self.setWindowFlags(flags)
        self.show()

    def apply_drop_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(138, 43, 226, 120))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

    def load_stylesheet(self, qss_path: str):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as err:
            print(f"[Erro] Falha ao carregar QSS ({err}).")

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
