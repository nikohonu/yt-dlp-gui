import json
from pathlib import Path

from appdirs import user_config_dir


class Settings:
    def __init__(self):
        self.directory = Path(user_config_dir("yt-dlp-gui", "Niko Honu"))
        self.directory.mkdir(parents=True, exist_ok=True)
        self.filename = self.directory / "settings.json"
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.filename, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self):
        with open(self.filename, "w") as file:
            json.dump(self.data, file, indent=4)

    def __del__(self):
        self.save_data()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
