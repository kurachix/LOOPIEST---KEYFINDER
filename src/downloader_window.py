"""
Main Application Window for LOOPIEST - MP3 & STREAM DOWNLOADER.
Provides sleek dark/neon studio UI for downloading audio from YouTube, SoundCloud,
TikTok, Instagram, Bandcamp, and other providers, with optional automatic BPM & Key tagging.
"""

import os
import subprocess
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPixmap, QColor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar, QGraphicsDropShadowEffect,
    QStackedWidget, QFrame, QFileDialog, QCheckBox, QButtonGroup
)

from src.worker import DownloadWorker, formatar_duracao
from src.downloader_engine import (
    detectar_provedor,
    validar_url_download,
    obter_pasta_padrao_downloads
)


class DownloaderWindow(QWidget):
    """
    Frameless Studio Window for LOOPIEST DOWNLOADER:
    - Page 0: Link Input, Live Provider Detection, Format Selector (MP3 320k / 192k / WAV),
              Destination Folder, Auto-KeyFinder Toggle, and Real-Time Download Progress.
    - Page 1: Download Complete Card with Track Metadata, Detected Key/BPM (if enabled),
              Open in Explorer button, and Send to KeyFinder button.
    """

    return_to_hub_requested = Signal()
    open_in_keyfinder_requested = Signal(str)

    def __init__(self, logo_path: str, qss_path: str = None, passkey: str = None, username: str = None):
        super().__init__()

        self.logo_path = logo_path
        self.qss_path = qss_path
        self.passkey = passkey
        self.username = username
        self.drag_position = QPoint()
        self.is_pinned = False

        self.download_worker = None
        self.output_dir = obter_pasta_padrao_downloads()
        self.selected_format = "mp3_320"
        self.last_downloaded_result = {}

        self.init_window()
        self.init_ui()

        if self.qss_path and os.path.exists(self.qss_path):
            self.load_stylesheet(self.qss_path)

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
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
            y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        """Construct window layout, top header bar, and stacked pages."""
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(self.main_container)

        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(22, 16, 22, 22)
        container_layout.setSpacing(10)

        # -------------------------------------------------------------
        # 1. Top Header Bar (Perfectly Centered @L8PIEST via Symmetric Side Containers)
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Left Container (Fixed width 132px to balance Right Container)
        left_controls = QWidget(self.main_container)
        left_controls.setFixedSize(132, 30)
        left_layout = QHBoxLayout(left_controls)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.btn_back_hub = QPushButton("◄ CENTRAL", left_controls)
        self.btn_back_hub.setObjectName("HubReturnButton")
        self.btn_back_hub.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_hub.setToolTip("Voltar para a Central de Softwares")
        self.btn_back_hub.clicked.connect(self._on_return_hub_clicked)
        left_layout.addWidget(self.btn_back_hub)

        self.btn_pin = QPushButton("📌", left_controls)
        self.btn_pin.setObjectName("PinButton")
        self.btn_pin.setFixedSize(28, 28)
        self.btn_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pin.setToolTip("Fixar Janela no Topo (Modo FL Studio)")
        self.btn_pin.setStyleSheet("color: #8E8EA0; font-size: 13px; border: none; background: transparent;")
        self.btn_pin.clicked.connect(self.toggle_always_on_top)
        left_layout.addWidget(self.btn_pin)

        header_layout.addWidget(left_controls)

        # Centered Header Tag (100% Geometrically Centered)
        self.header_tag = QLabel(
            '<a href="https://www.instagram.com/l8piest/" style="color: #8A2BE2; text-decoration: none;">@L8PIEST</a>',
            self.main_container
        )
        self.header_tag.setObjectName("HeaderTag")
        self.header_tag.setFixedHeight(30)
        self.header_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_tag.setOpenExternalLinks(True)
        self.header_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.username or self.passkey:
            tooltip_items = []
            if self.username:
                tooltip_items.append(f"Produtor: {self.username}")
            if self.passkey:
                tooltip_items.append(f"Passkey Ativa: {self.passkey}")
            self.header_tag.setToolTip("\n".join(tooltip_items))
        header_layout.addWidget(self.header_tag, 1, Qt.AlignmentFlag.AlignCenter)

        # Right Container (Fixed width 132px to match Left Container)
        right_controls = QWidget(self.main_container)
        right_controls.setFixedSize(132, 30)
        right_layout = QHBoxLayout(right_controls)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.btn_close = QPushButton("✕", right_controls)
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Fechar Aplicação")
        self.btn_close.clicked.connect(self.close)
        right_layout.addWidget(self.btn_close)

        header_layout.addWidget(right_controls)

        container_layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # 2. QStackedWidget for Multi-Page Navigation
        # -------------------------------------------------------------
        self.stacked_widget = QStackedWidget(self.main_container)
        container_layout.addWidget(self.stacked_widget, 1)

        self.page_form = self.create_download_form_page()
        self.page_complete = self.create_complete_page()

        self.stacked_widget.addWidget(self.page_form)      # Index 0
        self.stacked_widget.addWidget(self.page_complete)  # Index 1
        self.stacked_widget.setCurrentIndex(0)

    # -------------------------------------------------------------
    # Page 0: Download Input & Configuration Page
    # -------------------------------------------------------------
    def create_download_form_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(10)

        # Logo Header
        self.logo_label = QLabel(page)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo_image()
        layout.addWidget(self.logo_label)

        title_text = f"LOOPIEST DOWNLOADER • {self.username.upper()}" if self.username else "LOOPIEST DOWNLOADER"
        self.title_label = QLabel(title_text, page)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 15px; letter-spacing: 2px;")
        layout.addWidget(self.title_label)

        self.providers_subtitle = QLabel(
            "YOUTUBE  •  SOUNDCLOUD  •  TIKTOK  •  INSTAGRAM  •  BANDCAMP",
            page
        )
        self.providers_subtitle.setObjectName("AppSubtitle")
        self.providers_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.providers_subtitle.setStyleSheet("font-size: 9px; letter-spacing: 2px; color: #A07CFE;")
        layout.addWidget(self.providers_subtitle)

        layout.addSpacing(2)

        # URL Card Container
        url_card = QFrame(page)
        url_card.setObjectName("VerificationCard")
        url_card_layout = QVBoxLayout(url_card)
        url_card_layout.setContentsMargins(14, 12, 14, 12)
        url_card_layout.setSpacing(8)

        # Top row inside URL Card: Label + Dynamic Provider Badge
        url_header_row = QHBoxLayout()
        url_label = QLabel("LINK DA FAIXA / VÍDEO:", url_card)
        url_label.setObjectName("VerificationTitle")
        url_header_row.addWidget(url_label)

        url_header_row.addStretch(1)

        self.provider_badge = QLabel("● AGUARDANDO LINK", url_card)
        self.provider_badge.setObjectName("ProviderBadge")
        self.provider_badge.setStyleSheet(
            "color: #8E8EA0; font-size: 10px; font-weight: 800; letter-spacing: 1px;"
        )
        url_header_row.addWidget(self.provider_badge)
        url_card_layout.addLayout(url_header_row)

        # Input + Paste Button Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.url_input = QLineEdit(url_card)
        self.url_input.setObjectName("UsernameInput")
        self.url_input.setPlaceholderText("Cole o link do YouTube, SoundCloud, TikTok...")
        self.url_input.textChanged.connect(self._on_url_text_changed)
        self.url_input.returnPressed.connect(self.start_download)
        input_row.addWidget(self.url_input, 1)

        self.btn_paste = QPushButton("COLAR", url_card)
        self.btn_paste.setObjectName("PasteButton")
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.setFixedHeight(38)
        self.btn_paste.clicked.connect(self.paste_from_clipboard)
        input_row.addWidget(self.btn_paste)

        url_card_layout.addLayout(input_row)
        layout.addWidget(url_card)

        # Quality / Format Selection Card
        format_card = QFrame(page)
        format_card.setObjectName("VerificationCard")
        format_layout = QVBoxLayout(format_card)
        format_layout.setContentsMargins(14, 10, 14, 12)
        format_layout.setSpacing(8)

        fmt_title = QLabel("FORMATO & QUALIDADE DE ESTÚDIO:", format_card)
        fmt_title.setObjectName("VerificationTitle")
        format_layout.addWidget(fmt_title)

        fmt_buttons_row = QHBoxLayout()
        fmt_buttons_row.setSpacing(8)

        self.format_group = QButtonGroup(self)
        self.format_group.setExclusive(True)

        self.btn_mp3_320 = QPushButton("MP3 320kbps", format_card)
        self.btn_mp3_320.setObjectName("FormatPillButton")
        self.btn_mp3_320.setCheckable(True)
        self.btn_mp3_320.setChecked(True)
        self.btn_mp3_320.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mp3_320.clicked.connect(lambda: self._set_format("mp3_320"))

        self.btn_mp3_192 = QPushButton("MP3 192kbps", format_card)
        self.btn_mp3_192.setObjectName("FormatPillButton")
        self.btn_mp3_192.setCheckable(True)
        self.btn_mp3_192.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mp3_192.clicked.connect(lambda: self._set_format("mp3_192"))

        self.btn_wav = QPushButton("WAV Lossless", format_card)
        self.btn_wav.setObjectName("FormatPillButton")
        self.btn_wav.setCheckable(True)
        self.btn_wav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_wav.clicked.connect(lambda: self._set_format("wav"))

        self.format_group.addButton(self.btn_mp3_320)
        self.format_group.addButton(self.btn_mp3_192)
        self.format_group.addButton(self.btn_wav)

        fmt_buttons_row.addWidget(self.btn_mp3_320, 1)
        fmt_buttons_row.addWidget(self.btn_mp3_192, 1)
        fmt_buttons_row.addWidget(self.btn_wav, 1)

        format_layout.addLayout(fmt_buttons_row)
        layout.addWidget(format_card)

        # Output Folder & Auto-KeyFinder Options Card
        folder_card = QFrame(page)
        folder_card.setObjectName("VerificationCard")
        folder_layout = QVBoxLayout(folder_card)
        folder_layout.setContentsMargins(14, 10, 14, 12)
        folder_layout.setSpacing(8)

        folder_title = QLabel("PASTA DE DESTINO:", folder_card)
        folder_title.setObjectName("VerificationTitle")
        folder_layout.addWidget(folder_title)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)

        self.folder_path_label = QLabel(self._format_short_path(self.output_dir), folder_card)
        self.folder_path_label.setObjectName("AudioMetadataBox")
        self.folder_path_label.setToolTip(self.output_dir)
        folder_row.addWidget(self.folder_path_label, 1)

        self.btn_choose_folder = QPushButton("📁 PASTA", folder_card)
        self.btn_choose_folder.setObjectName("PasteButton")
        self.btn_choose_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_choose_folder.setFixedHeight(32)
        self.btn_choose_folder.clicked.connect(self.choose_output_directory)
        folder_row.addWidget(self.btn_choose_folder)

        folder_layout.addLayout(folder_row)

        # Auto KeyFinder Checkbox
        self.chk_auto_keyfinder = QCheckBox(
            "Auto-detectar BPM & Tonalidade (KeyFinder) e renomear arquivo",
            folder_card
        )
        self.chk_auto_keyfinder.setChecked(True)
        self.chk_auto_keyfinder.setCursor(Qt.CursorShape.PointingHandCursor)
        folder_layout.addWidget(self.chk_auto_keyfinder)

        layout.addWidget(folder_card)

        layout.addStretch(1)

        # Status & Progress Bar
        self.status_label = QLabel("", page)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(page)
        self.progress_bar.setFixedHeight(7)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Error Alert Box
        self.error_alert_box = QLabel("", page)
        self.error_alert_box.setObjectName("ErrorAlertBox")
        self.error_alert_box.setWordWrap(True)
        self.error_alert_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_alert_box.hide()
        layout.addWidget(self.error_alert_box)

        # Primary Action Button
        self.btn_download = QPushButton("BAIXAR ÁUDIO AGORA", page)
        self.btn_download.setObjectName("StartButton")
        self.btn_download.setFixedHeight(44)
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.clicked.connect(self.start_download)
        layout.addWidget(self.btn_download)

        return page

    # -------------------------------------------------------------
    # Page 1: Download Completed View
    # -------------------------------------------------------------
    def create_complete_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(14)

        layout.addStretch(1)

        # Result Highlight Card
        self.result_card = QFrame(page)
        self.result_card.setObjectName("KeyHighlightCard")
        card_layout = QVBoxLayout(self.result_card)
        card_layout.setContentsMargins(18, 20, 18, 20)
        card_layout.setSpacing(8)

        self.done_badge = QLabel("● DOWNLOAD & CONVERSÃO CONCLUÍDOS", self.result_card)
        self.done_badge.setObjectName("BadgeAvailable")
        self.done_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.done_badge, 0, Qt.AlignmentFlag.AlignCenter)

        self.res_title_label = QLabel("Faixa Baixada", self.result_card)
        self.res_title_label.setObjectName("HubCardTitle")
        self.res_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.res_title_label.setWordWrap(True)
        self.res_title_label.setStyleSheet("font-size: 16px; color: #FFFFFF; font-weight: 800;")
        card_layout.addWidget(self.res_title_label)

        self.res_artist_label = QLabel("Canal / Artista: --", self.result_card)
        self.res_artist_label.setObjectName("StatusLabel")
        self.res_artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.res_artist_label)

        self.res_meta_label = QLabel("YOUTUBE  •  MP3 320 kbps  •  3m 20s", self.result_card)
        self.res_meta_label.setObjectName("TuningLabel")
        self.res_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.res_meta_label)

        # KeyFinder Auto-Analysis Pill (Shown when Auto-KeyFinder ran)
        self.res_key_bpm_label = QLabel("🎹 Key: --  |  BPM: --", self.result_card)
        self.res_key_bpm_label.setObjectName("RelativeKeyLabel")
        self.res_key_bpm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.res_key_bpm_label.hide()
        card_layout.addWidget(self.res_key_bpm_label)

        layout.addWidget(self.result_card)

        # Saved File Name Box
        self.saved_file_box = QLabel("", page)
        self.saved_file_box.setObjectName("AudioMetadataBox")
        self.saved_file_box.setWordWrap(True)
        self.saved_file_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.saved_file_box)

        # Secondary Action Buttons Row (Open Folder & Open in KeyFinder)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.btn_open_folder = QPushButton("📂 Abrir na Pasta", page)
        self.btn_open_folder.setObjectName("RenameButton")
        self.btn_open_folder.setMinimumWidth(160)
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self.open_file_in_explorer)
        actions_row.addWidget(self.btn_open_folder, 1)

        self.btn_send_keyfinder = QPushButton("🎹 Abrir no KeyFinder", page)
        self.btn_send_keyfinder.setObjectName("RenameButton")
        self.btn_send_keyfinder.setMinimumWidth(160)
        self.btn_send_keyfinder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_keyfinder.clicked.connect(self.send_to_keyfinder)
        actions_row.addWidget(self.btn_send_keyfinder, 1)

        layout.addLayout(actions_row)

        layout.addStretch(1)

        # Button to Download Another Track
        self.btn_download_another = QPushButton("Baixar Outra Música", page)
        self.btn_download_another.setObjectName("StartButton")
        self.btn_download_another.setFixedHeight(44)
        self.btn_download_another.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download_another.clicked.connect(self.reset_for_new_download)
        layout.addWidget(self.btn_download_another)

        return page

    # -------------------------------------------------------------
    # Helper & Interaction Methods
    # -------------------------------------------------------------
    def load_logo_image(self):
        try:
            if os.path.exists(self.logo_path):
                pixmap = QPixmap(self.logo_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        68, 68,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    return
        except Exception:
            pass
        self.logo_label.setText("❖")

    def _format_short_path(self, path: str) -> str:
        if len(path) <= 44:
            return path
        return "..." + path[-41:]

    def _set_format(self, fmt_code: str):
        self.selected_format = fmt_code

    def _on_url_text_changed(self, text: str):
        self.error_alert_box.hide()
        info = detectar_provedor(text)
        name = info["name"]
        color = info["color"]
        self.provider_badge.setText(f"● {name}")
        self.provider_badge.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 800; letter-spacing: 1px;"
        )

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clip_text = clipboard.text().strip()
            if clip_text:
                self.url_input.setText(clip_text)

    def choose_output_directory(self):
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta para Salvar Downloads",
            self.output_dir
        )
        if chosen:
            self.output_dir = chosen
            self.folder_path_label.setText(self._format_short_path(chosen))
            self.folder_path_label.setToolTip(chosen)

    def start_download(self):
        # If currently downloading, clicking cancels the active download
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait(800)
            self._set_downloading_ui_state(False)
            self.status_label.setText("Download cancelado.")
            self.status_label.show()
            return

        url = self.url_input.text().strip()
        if not url:
            self.show_error_alert("Cole o link da música ou vídeo (YouTube, SoundCloud, etc.) para baixar.")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_input.setText(url)

        if not validar_url_download(url):
            self.show_error_alert("Link inválido. Verifique o endereço copiado e tente novamente.")
            return

        self.error_alert_box.hide()
        self._set_downloading_ui_state(True)

        self.download_worker = DownloadWorker(
            url=url,
            output_dir=self.output_dir,
            quality_format=self.selected_format,
            auto_keyfinder=self.chk_auto_keyfinder.isChecked(),
            parent=self
        )
        self.download_worker.progress_changed.connect(self.progress_bar.setValue)
        self.download_worker.status_changed.connect(self.status_label.setText)
        self.download_worker.download_completed.connect(self.on_download_succeeded)
        self.download_worker.download_failed.connect(self.on_download_failed)
        self.download_worker.start()

    def _set_downloading_ui_state(self, active: bool):
        self.url_input.setEnabled(not active)
        self.btn_paste.setEnabled(not active)
        self.btn_mp3_320.setEnabled(not active)
        self.btn_mp3_192.setEnabled(not active)
        self.btn_wav.setEnabled(not active)
        self.btn_choose_folder.setEnabled(not active)
        self.chk_auto_keyfinder.setEnabled(not active)

        if active:
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.status_label.setText("Inicializando extrator...")
            self.status_label.show()
            self.btn_download.setText("CANCELAR EXTRAÇÃO")
        else:
            self.progress_bar.hide()
            self.btn_download.setText("BAIXAR ÁUDIO AGORA")

    def on_download_succeeded(self, result: dict):
        self._set_downloading_ui_state(False)
        self.status_label.hide()
        self.last_downloaded_result = result

        title = result.get("title", "Faixa de Áudio")
        uploader = result.get("uploader", "Artista")
        provider = result.get("provider", "STREAM")
        quality_label = result.get("quality_label", "MP3 320 kbps")
        duration_sec = result.get("duration_sec", 0.0)
        file_name = result.get("file_name", "")

        self.res_title_label.setText(title)
        self.res_artist_label.setText(f"Canal / Artista: {uploader}")

        dur_str = formatar_duracao(duration_sec) if duration_sec > 0 else "--"
        self.res_meta_label.setText(f"{provider}   •   {quality_label}   •   {dur_str}")

        bpm = result.get("bpm")
        key = result.get("key")
        rel_key = result.get("relative_key")

        if bpm and key:
            rel_txt = f" (Rel: {rel_key})" if rel_key else ""
            self.res_key_bpm_label.setText(f"🎹 Tom: {key}{rel_txt}   |   ⚡ BPM: {bpm}")
            self.res_key_bpm_label.show()
        else:
            self.res_key_bpm_label.hide()

        self.saved_file_box.setText(f"Salvo como: {file_name}")
        self.saved_file_box.setToolTip(result.get("file_path", ""))

        self.stacked_widget.setCurrentIndex(1)

    def on_download_failed(self, error_msg: str):
        self._set_downloading_ui_state(False)
        self.show_error_alert(error_msg)

    def open_file_in_explorer(self):
        file_path = self.last_downloaded_result.get("file_path", "")
        if file_path and os.path.exists(file_path):
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(file_path)])
            return
        if os.path.exists(self.output_dir) and os.name == "nt":
            os.startfile(self.output_dir)

    def send_to_keyfinder(self):
        file_path = self.last_downloaded_result.get("file_path", "")
        if file_path and os.path.exists(file_path):
            self.open_in_keyfinder_requested.emit(file_path)
            self.close()

    def reset_for_new_download(self):
        self.url_input.clear()
        self.error_alert_box.hide()
        self.status_label.hide()
        self.progress_bar.hide()
        self.stacked_widget.setCurrentIndex(0)

    def show_error_alert(self, message: str):
        self.status_label.hide()
        self.progress_bar.hide()
        self.error_alert_box.setText(f"⚠️ {message}")
        self.error_alert_box.show()

    def _on_return_hub_clicked(self):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait(500)
        self.return_to_hub_requested.emit()
        self.close()

    def toggle_always_on_top(self):
        self.is_pinned = not self.is_pinned
        pos = self.pos()
        if self.is_pinned:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.btn_pin.setToolTip("Desafixar Janela do Topo")
            self.btn_pin.setStyleSheet("color: #00E676; font-size: 13px; border: none; background: transparent;")
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.btn_pin.setToolTip("Fixar Janela no Topo (Modo FL Studio)")
            self.btn_pin.setStyleSheet("color: #8E8EA0; font-size: 13px; border: none; background: transparent;")
        self.show()
        self.move(pos)

    def apply_drop_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(138, 43, 226, 120))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

    def load_stylesheet(self, qss_path: str):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as err:
            print(f"[Erro] Falha ao carregar QSS ({err}).")

    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait(800)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

