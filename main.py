"""
Main Entry Point for LOOPIEST Suite & Tools Ecosystem.
Lifecycle Flow:
1. Passkey & Username Gatekeeper:
   - If an active passkey and username are registered: enters Software Selection Hub directly.
   - If passkey is missing: opens Login & Passkey Screen -> Username Screen -> Software Hub.
   - If passkey is present but username missing: opens Username Screen -> Software Hub.
2. Software Selection Hub (Central de Softwares):
   - Modern dashboard presenting available and upcoming tools with interactive vinyl discs.
   - Available: LOOPIEST KEYFINDER (Audio Analysis & Key Detection).
   - Upcoming: Stem Separator, Mastering Rack (VIP Coming Soon).
3. Tool Execution:
   - Selecting KEYFINDER initializes the Splash Loading sequence -> Main Keyfinder Window.
   - Main Window features a '◄ CENTRAL' button to return to the Software Hub at any time.
"""

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.login_window import LoginWindow
from src.username_window import UsernameWindow
from src.hub_window import SoftwareHubWindow
from src.splash_screen import SplashScreen
from src.main_window import MainWindow
from src.auth import ensure_pass_vault, get_saved_passkey, get_saved_username


def main():
    # Register Windows AppUserModelID so taskbar displays custom logo.png
    if sys.platform == "win32":
        try:
            myappid = "loopiest.suite.gui.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("LOOPIEST SUITE")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    qss_path = os.path.join(base_dir, "styles", "theme.qss")

    # Ensure encrypted pass.dat vault with 500 active passkeys is available in C:\loopiest\acess
    ensure_pass_vault(count=500)

    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Reference holder to prevent active windows from being garbage collected
    window_container = {}

    def launch_main_window(passkey: str = None, username: str = None):
        """Step 3B: Launch Main Application Window for LOOPIEST KEYFINDER."""
        main_win = MainWindow(logo_path=logo_path, qss_path=qss_path, passkey=passkey, username=username)
        window_container["main_window"] = main_win
        main_win.return_to_hub_requested.connect(lambda: launch_software_hub(passkey=passkey, username=username))
        main_win.show()

    def launch_splash_screen(passkey: str = None, username: str = None):
        """Step 3A: Launch Splash Screen (Software Loading for KeyFinder)."""
        splash = SplashScreen(logo_path=logo_path, qss_path=qss_path)
        window_container["splash"] = splash
        splash.start_requested.connect(lambda: launch_main_window(passkey=passkey, username=username))
        splash.show()

    def on_software_selected(software_id: str, passkey: str, username: str):
        """Callback when a software is executed from the Hub."""
        if software_id == "keyfinder":
            # Close Hub and launch KeyFinder splash loading
            if "hub" in window_container and window_container["hub"]:
                window_container["hub"].close()
            launch_splash_screen(passkey=passkey, username=username)

    def launch_software_hub(passkey: str = None, username: str = None):
        """Step 2: Launch Central Software Hub (Multi-Tool Launcher)."""
        hub = SoftwareHubWindow(logo_path=logo_path, qss_path=qss_path, passkey=passkey, username=username)
        window_container["hub"] = hub
        hub.software_selected.connect(lambda sid: on_software_selected(sid, passkey=passkey, username=username))
        hub.show()

    def launch_username_window(passkey: str):
        """Step 1B: Launch Username Registration Window after passkey validation."""
        user_win = UsernameWindow(logo_path=logo_path, qss_path=qss_path)
        window_container["username"] = user_win
        user_win.registered.connect(lambda user: launch_software_hub(passkey=passkey, username=user))
        user_win.show()

    def on_passkey_authenticated(passkey: str):
        """Callback when passkey is confirmed on LoginWindow."""
        saved_user = get_saved_username()
        if not saved_user:
            # First-time onboarding: request username
            launch_username_window(passkey=passkey)
        else:
            # Enters Software Hub directly
            launch_software_hub(passkey=passkey, username=saved_user)

    def launch_login_window():
        """Step 1A: Launch Login Window if no valid key is saved."""
        login_win = LoginWindow(logo_path=logo_path, qss_path=qss_path)
        window_container["login"] = login_win
        login_win.authenticated.connect(on_passkey_authenticated)
        login_win.show()

    # Check registered credentials
    saved_key = get_saved_passkey()
    saved_user = get_saved_username()

    if saved_key and saved_user:
        print(f"[LOOPIEST AUTH] Produtor '{saved_user}' autenticado com sucesso. Abrindo Central de Softwares...")
        launch_software_hub(passkey=saved_key, username=saved_user)
    elif saved_key and not saved_user:
        print("[LOOPIEST AUTH] Passkey autorizada detectada, mas usuário não cadastrado. Solicitando identificação...")
        launch_username_window(passkey=saved_key)
    else:
        print("[LOOPIEST AUTH] Nenhuma passkey ativa cadastrada. Exibindo tela de autenticação...")
        launch_login_window()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
