"""
Main Entry Point for LOOPIEST - KEYFINDER Application.
Initializes PySide6 application lifecycle and displays the Splash Screen.
"""

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.splash_screen import SplashScreen


def main():
    # Set Windows AppUserModelID so the Taskbar uses the custom logo icon
    if sys.platform == "win32":
        try:
            myappid = "loopiest.keyfinder.gui.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Enable High DPI Scaling & Smooth Rendering
    app = QApplication(sys.argv)
    app.setApplicationName("LOOPIEST - KEYFINDER")

    # Define absolute paths for assets and styles
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    qss_path = os.path.join(base_dir, "styles", "theme.qss")

    # Set App Window Icon for Taskbar
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Instantiate Splash Screen
    splash = SplashScreen(logo_path=logo_path, qss_path=qss_path)
    splash.show()

    # Run Application Event Loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
