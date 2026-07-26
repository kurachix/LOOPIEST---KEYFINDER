"""
Main Entry Point for LOOPIEST - KEYSEARCH Application.
Initializes PySide6 application lifecycle and displays the Splash Screen.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from src.splash_screen import SplashScreen


def main():
    # Enable High DPI Scaling & Smooth Rendering
    app = QApplication(sys.argv)
    app.setApplicationName("LOOPIEST - KEYSEARCH")

    # Define absolute paths for assets and styles
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo.png")
    qss_path = os.path.join(base_dir, "styles", "theme.qss")

    # Instantiate Splash Screen
    splash = SplashScreen(logo_path=logo_path, qss_path=qss_path)
    splash.show()

    # Run Application Event Loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
