"""
Main Entry Point for LOOPIEST - KEYFINDER Application.
Manages application lifecycle and smooth transition from Splash Screen to Main Audio Receiver Window.
"""

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.splash_screen import SplashScreen
from src.main_window import MainWindow


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

    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Reference holder to prevent main window from being garbage collected
    main_window_container = {}

    def launch_main_window():
        main_win = MainWindow(logo_path=logo_path, qss_path=qss_path)
        main_window_container["window"] = main_win
        main_win.show()

    # Instantiate Splash Screen
    splash = SplashScreen(logo_path=logo_path, qss_path=qss_path)
    splash.start_requested.connect(launch_main_window)
    splash.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
