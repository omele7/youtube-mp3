import os

APP_NAME = "VideoToMP3"
SUPPORTED_FORMATS = ["mp3", "wav", "m4a"]
SUPPORTED_QUALITIES = ["128", "192", "320"]


def get_default_output():
    return os.path.join(os.path.expanduser("~"), "Downloads")
