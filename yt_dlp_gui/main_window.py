import shutil
import subprocess
import sys
from collections import OrderedDict
from functools import partial
from pathlib import Path

import requests
from PySide6.QtCore import QProcess, QTextStream
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QWidget,
)

import yt_dlp_gui.settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = QProcess(self)
        if sys.platform.startswith("win"):
            self.yt_dlp_path = Path.cwd() / "yt-dlp.exe"
            if not self.yt_dlp_path.exists():
                path = shutil.which("yt-dlp")
            download = False
            print(self.yt_dlp_path)
            if self.yt_dlp_path:
                self.yt_dlp_path = path
                version = subprocess.check_output(
                    [self.yt_dlp_path, "--version"], universal_newlines=True
                ).strip()
                response = requests.get(
                    "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
                )
                data = response.json()
                if version != data["tag_name"]:
                    download = True
            else:
                download = True
            if download:
                self.yt_dlp_path = Path.cwd() / "yt-dlp.exe"
                response = requests.get(
                    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
                )
                with self.yt_dlp_path.open("wb") as file:
                    file.write(response.content)
        else:
            self.yt_dlp_path = "yt-dlp"
        self.settings = yt_dlp_gui.settings.Settings()
        central_widget = QWidget()
        grid_layout = QGridLayout()
        hbox_layout = QHBoxLayout()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(grid_layout)
        self.resize(600, 600)
        # Creating widgets
        self.text_browser = QTextBrowser()
        self.folder_dialog_button = QPushButton()
        self.download_audio_button = QPushButton()
        self.download_video_button = QPushButton()
        self.stop_button = QPushButton()
        self.label_2 = QLabel()
        self.quality_label = QLabel()
        self.quality_widget = QComboBox()
        self.quality_widget.addItems(["1080p", "720p", "480p", "360p", "240p", "144p"])
        if "quality" in self.settings.data:
            self.quality_widget.setCurrentText(self.settings["quality"])
        else:
            self.quality_widget.setCurrentText("720p")
        self.label = QLabel()
        self.lineEdit = QLineEdit()
        self.output_path_widget = QComboBox(editable=True)
        self.output_path_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if "paths" in self.settings.data:
            self.output_path_widget.addItems(self.settings["paths"])

        # Layout
        grid_layout.addWidget(self.text_browser, 4, 0, 1, 3)
        grid_layout.addWidget(self.folder_dialog_button, 2, 2, 1, 1)
        grid_layout.addWidget(self.label_2, 1, 0, 1, 1)
        grid_layout.addWidget(self.quality_label, 3, 0, 1, 3)
        grid_layout.addWidget(self.quality_widget, 3, 1, 1, 2)
        grid_layout.addWidget(self.label, 2, 0, 1, 1)
        grid_layout.addWidget(self.output_path_widget, 2, 1, 1, 1)
        grid_layout.addWidget(self.lineEdit, 1, 1, 1, 2)

        grid_layout.addLayout(hbox_layout, 5, 0, 1, 3)

        hbox_layout.addWidget(self.download_audio_button)
        hbox_layout.addWidget(self.download_video_button)
        hbox_layout.addWidget(self.stop_button)

        # Signals
        self.output_path_widget.currentIndexChanged.connect(self.output_path_changed)
        self.quality_widget.currentIndexChanged.connect(self.quality_changed)
        self.folder_dialog_button.clicked.connect(self.show_folder_dialog)
        self.download_audio_button.clicked.connect(partial(self.download, True))
        self.download_video_button.clicked.connect(partial(self.download, False))

        # Texts
        self.retranslateUi()

    def retranslateUi(self):
        self.setWindowTitle("yt-dlp gui")
        self.label_2.setText("URL")
        self.label.setText("Output Folder")
        self.folder_dialog_button.setText("Browse")
        self.quality_label.setText("Quality")
        self.download_audio_button.setText("Download Audio")
        self.download_video_button.setText("Download Video")
        self.stop_button.setText("Stop")

    def show_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", str(Path.home())
        )

        if folder_path:
            self.selected_folder = folder_path
            if "paths" in self.settings.data:
                self.settings["paths"].insert(0, str(folder_path))
                self.settings["paths"] = list(
                    OrderedDict.fromkeys(self.settings["paths"])
                )[:5]
            else:
                self.settings["paths"] = [str(folder_path)]
            self.output_path_widget.clear()
            self.output_path_widget.addItems(self.settings["paths"])
            self.output_path_widget.setCurrentText(str(folder_path))

    def output_path_changed(self, index):
        self.output_path_widget.blockSignals(True)
        if index >= 0:
            path = self.settings["paths"][index]
            self.settings["paths"].remove(path)
            self.settings["paths"].insert(0, path)
            self.output_path_widget.removeItem(index)
            self.output_path_widget.insertItem(0, path)
            self.output_path_widget.setCurrentIndex(0)
        self.output_path_widget.blockSignals(False)

    def quality_changed(self, index):
        self.settings["quality"] = self.quality_widget.currentText()

    def download(self, audio_only):
        command = f"{self.yt_dlp_path} '{self.lineEdit.text()}' -P {self.output_path_widget.currentText()}"
        if audio_only:
            command += " --extract-audio"
        else:
            command += f" -f 'bv*[height={self.quality_widget.currentText()[:-1]}]+ba'"
        print(command)
        self.process = QProcess(self)
        self.stop_button.clicked.connect(self.process.kill)
        if sys.platform.startswith("win"):
            self.process.setProgram("cmd.exe")
            self.process.setArguments(["/c", command])
        elif sys.platform.startswith("linux"):
            self.process.setProgram("/bin/bash")
            self.process.setArguments(["-c", command])
        self.process.readyReadStandardOutput.connect(self.update_output)
        self.process.readyReadStandardError.connect(self.update_output)
        self.process.finished.connect(self.process_finished)
        self.process.start()

    def update_output(self):
        data = self.process.readAllStandardOutput()
        error_data = self.process.readAllStandardError()
        if data:
            text = QTextStream(data).readAll()
            self.text_browser.append(text)
        if error_data:
            error_text = QTextStream(error_data).readAll()
            self.text_browser.append(error_text)

    def process_finished(self):
        self.process.close()
        self.text_browser.append("--" * 16 + "Finished" + "--" * 16)
