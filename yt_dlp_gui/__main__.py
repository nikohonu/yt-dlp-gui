import sys

from PySide6.QtWidgets import QApplication

from yt_dlp_gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
