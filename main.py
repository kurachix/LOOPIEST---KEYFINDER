"""
Main Entry Point for LOOPIEST - KEYFINDER Application.
Lifecycle Flow:
1. Passkey & Username Gatekeeper:
   - If an active passkey and username are registered: skips onboarding and loads software directly.
   - If passkey is missing: opens Login & Passkey Screen first -> then Username Screen -> Splash.
   - If passkey is present but username is missing: opens Username Screen -> Splash.
2. Splash Screen: Software Loading & Dependency Initialization (0% -> 100%).
3. Main Application Window: Audio Reception & Key Detection.
"""

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.login_window import LoginWindow
from src.username_window import UsernameWindow
from src.splash_screen import SplashScreen
from src.main_window import MainWindow
from src.auth import ensure_pass_file, get_saved_passkey, get_saved_username


def main():
    # Register Windows AppUserModelID so taskbar displays custom logo.png
    if sys.platform == "win32":
        try:
            myappid = "loopiest.keyfinder.gui.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("LOOPIEST - KEYFINDER")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    qss_path = os.path.join(base_dir, "styles", "theme.qss")
    pass_file_path = os.path.join(base_dir, "pass.txt")

    # Ensure pass.txt with 500 active passkeys is available on system launch
    ensure_pass_file(pass_file_path, count=500)

    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Reference holder to prevent active windows from being garbage collected
    window_container = {}

    def launch_main_window(passkey: str = None, username: str = None):
        """Step 3: Launch Main Application Window."""
        main_win = MainWindow(logo_path=logo_path, qss_path=qss_path, passkey=passkey, username=username)
        window_container["window"] = main_win
        main_win.show()

    def launch_splash_screen(passkey: str = None, username: str = None):
        """Step 2: Launch Splash Screen (Software Loading)."""
        splash = SplashScreen(logo_path=logo_path, qss_path=qss_path)
        window_container["splash"] = splash
        splash.start_requested.connect(lambda: launch_main_window(passkey=passkey, username=username))
        splash.show()

    def launch_username_window(passkey: str):
        """Step 1B: Launch Username Registration Window after passkey validation."""
        user_win = UsernameWindow(logo_path=logo_path, qss_path=qss_path)
        window_container["username"] = user_win
        user_win.registered.connect(lambda user: launch_splash_screen(passkey=passkey, username=user))
        user_win.show()

    def on_passkey_authenticated(passkey: str):
        """Callback when passkey is confirmed on LoginWindow."""
        saved_user = get_saved_username()
        if not saved_user:
            # One screen after passkey: request username!
            launch_username_window(passkey=passkey)
        else:
            launch_splash_screen(passkey=passkey, username=saved_user)

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
        print(f"[LOOPIEST AUTH] Passkey autorizada e produtor '{saved_user}' detectados. Pulando telas e iniciando carregamento...")
        launch_splash_screen(passkey=saved_key, username=saved_user)
    elif saved_key and not saved_user:
        print("[LOOPIEST AUTH] Passkey autorizada detectada, mas usuário não cadastrado. Solicitando identificação...")
        launch_username_window(passkey=saved_key)
    else:
        print("[LOOPIEST AUTH] Nenhuma passkey ativa cadastrada. Exibindo tela de autenticação...")
        launch_login_window()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
