from PySide6.QtWidgets import QLabel


def seconds_to_hhmmss(value: int) -> str:
    if value <= 0:
        return "00:00"
    hours = value // 3600
    mins = (value % 3600) // 60
    secs = value % 60
    if hours:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def make_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    return label
