import os
import subprocess
import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src import config
from src.core import converter, downloader
from src.core.validators import is_supported_video_url, is_valid_url
from src.gui.widgets import make_label, seconds_to_hhmmss


class AnalyzeWorker(QThread):
    done = Signal(bool, dict, str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            info = downloader.analyze_url(self.url)
            self.done.emit(True, info, "")
        except Exception as exc:
            self.done.emit(False, {}, str(exc))


class ConvertWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    done = Signal(bool, str, str)

    def __init__(self, url: str, out_dir: str, fmt: str, quality: str, ffmpeg_path: str):
        super().__init__()
        self.url = url
        self.out_dir = out_dir
        self.fmt = fmt
        self.quality = quality
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        def hook(data):
            state = data.get("status")
            if state == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                pct = int((downloaded / total) * 100) if total else 0
                speed = data.get("speed") or 0
                speed_kb = speed / 1024 if speed else 0
                self.progress.emit(max(0, min(100, pct)))
                self.status.emit(f"Descargando... {pct}% - {speed_kb:.1f} KB/s")
            elif state == "finished":
                self.progress.emit(100)
                self.status.emit("Descarga completa. Convirtiendo...")

        try:
            output = converter.convert_video_to_audio(
                url=self.url,
                out_dir=self.out_dir,
                ffmpeg_location=self.ffmpeg_path,
                preferredcodec=self.fmt,
                preferredquality=self.quality,
                progress_hook=hook,
            )
            self.done.emit(True, output, "")
        except Exception as exc:
            self.done.emit(False, "", str(exc))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to Audio - Desktop")
        self.resize(840, 620)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.ffmpeg_path = downloader.get_ffmpeg_path()
        self.out_dir = config.get_default_output()
        self.current_info = {}
        self.analyze_worker = None
        self.convert_worker = None

        self._build_ui()
        self._validate_convert_button()

    def _build_ui(self):
        root = QVBoxLayout(self)

        header = make_label("Convierte videos a audio con yt-dlp + ffmpeg embebido")
        root.addWidget(header)

        form = QGridLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_edit.textChanged.connect(self._validate_convert_button)
        self.analyze_btn = QPushButton("Analizar")
        self.analyze_btn.clicked.connect(self.on_analyze)

        form.addWidget(QLabel("URL:"), 0, 0)
        form.addWidget(self.url_edit, 0, 1)
        form.addWidget(self.analyze_btn, 0, 2)

        self.format_combo = QComboBox()
        self.format_combo.addItems(config.SUPPORTED_FORMATS)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(config.SUPPORTED_QUALITIES)
        self.quality_combo.setCurrentText("192")

        form.addWidget(QLabel("Formato:"), 1, 0)
        form.addWidget(self.format_combo, 1, 1)
        form.addWidget(QLabel("Calidad (kbps):"), 1, 2)
        form.addWidget(self.quality_combo, 1, 3)

        self.dest_edit = QLineEdit(self.out_dir)
        self.dest_edit.setReadOnly(True)
        self.dest_btn = QPushButton("Seleccionar carpeta")
        self.dest_btn.clicked.connect(self.choose_folder)
        form.addWidget(QLabel("Destino:"), 2, 0)
        form.addWidget(self.dest_edit, 2, 1, 1, 2)
        form.addWidget(self.dest_btn, 2, 3)

        root.addLayout(form)

        info_box = QGroupBox("Informacion del video")
        info_layout = QVBoxLayout(info_box)
        self.title_label = make_label("Titulo: -")
        self.duration_label = make_label("Duracion: -")
        self.thumb_label = QLabel('Miniatura: <a href="">-</a>')
        self.thumb_label.setOpenExternalLinks(True)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.duration_label)
        info_layout.addWidget(self.thumb_label)
        root.addWidget(info_box)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.status_label = QLabel("Listo")
        root.addWidget(self.progress)
        root.addWidget(self.status_label)

        actions = QHBoxLayout()
        self.convert_btn = QPushButton("Convertir")
        self.convert_btn.clicked.connect(self.on_convert)
        self.update_btn = QPushButton("Buscar actualizaciones")
        self.update_btn.clicked.connect(self.on_update_check)
        actions.addWidget(self.convert_btn)
        actions.addWidget(self.update_btn)
        root.addLayout(actions)

    def _validate_convert_button(self):
        url_ok = is_valid_url(self.url_edit.text().strip())
        self.convert_btn.setEnabled(url_ok)

    def choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Selecciona carpeta destino", self.out_dir)
        if selected:
            self.out_dir = selected
            self.dest_edit.setText(selected)

    def on_analyze(self):
        url = self.url_edit.text().strip()
        self._validate_convert_button()
        if not is_valid_url(url):
            QMessageBox.warning(self, "URL invalida", "Ingresa una URL valida.")
            return
        if not is_supported_video_url(url):
            QMessageBox.warning(self, "Sitio no soportado", "Por ahora se soporta YouTube.")
            return

        self.status_label.setText("Analizando URL...")
        self.analyze_btn.setEnabled(False)
        self.analyze_worker = AnalyzeWorker(url)
        self.analyze_worker.done.connect(self._on_analyze_done)
        self.analyze_worker.start()

    def _on_analyze_done(self, ok: bool, info: dict, error: str):
        self.analyze_btn.setEnabled(True)
        if not ok:
            QMessageBox.critical(self, "Error al analizar", self._humanize_error(error))
            self.status_label.setText("No se pudo analizar la URL")
            return

        self.current_info = info
        self.title_label.setText(f"Titulo: {info.get('title', '-')}")
        self.duration_label.setText(f"Duracion: {seconds_to_hhmmss(info.get('duration', 0))}")
        thumb = info.get("thumbnail") or ""
        self.thumb_label.setText(f'Miniatura: <a href="{thumb}">{thumb or "-"}</a>')
        self.status_label.setText("URL analizada correctamente")

    def on_convert(self):
        url = self.url_edit.text().strip()
        if not is_valid_url(url):
            QMessageBox.warning(self, "URL invalida", "Ingresa una URL valida.")
            return
        if not os.path.exists(self.ffmpeg_path):
            QMessageBox.critical(
                self,
                "ffmpeg no encontrado",
                "No se encontro resources/ffmpeg/ffmpeg.exe. Verifica el binario embebido.",
            )
            return

        self.progress.setValue(0)
        self.status_label.setText("Iniciando descarga...")
        self.convert_btn.setEnabled(False)

        fmt = self.format_combo.currentText()
        quality = self.quality_combo.currentText()

        self.convert_worker = ConvertWorker(
            url=url,
            out_dir=self.out_dir,
            fmt=fmt,
            quality=quality,
            ffmpeg_path=self.ffmpeg_path,
        )
        self.convert_worker.progress.connect(self.progress.setValue)
        self.convert_worker.status.connect(self.status_label.setText)
        self.convert_worker.done.connect(self._on_convert_done)
        self.convert_worker.start()

    def _on_convert_done(self, ok: bool, output_path: str, error: str):
        self.convert_btn.setEnabled(True)
        if not ok:
            QMessageBox.critical(self, "Error de conversion", self._humanize_error(error))
            self.status_label.setText("Error en conversion")
            return

        self.status_label.setText(f"Completado: {output_path}")
        QMessageBox.information(self, "Conversion completa", f"Archivo generado:\n{output_path}")

    def on_update_check(self):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "index", "versions", "yt-dlp"],
                check=False,
                capture_output=True,
                text=True,
            )
            QMessageBox.information(
                self,
                "Actualizaciones",
                "Revisa la salida de pip para confirmar si hay una version mas reciente de yt-dlp.",
            )
        except Exception:
            QMessageBox.warning(
                self,
                "Actualizaciones",
                "No se pudo comprobar automaticamente. Revisa nuevas versiones de la app.",
            )

    @staticmethod
    def _humanize_error(message: str) -> str:
        text = (message or "Error desconocido").lower()
        if "sin conexion" in text or "network" in text:
            return "No hay conexion a internet."
        if "private" in text or "privado" in text:
            return "El video es privado."
        if "unavailable" in text or "eliminado" in text or "not available" in text:
            return "El video no esta disponible o fue eliminado."
        return message or "Error desconocido"
