import glob
import os
import socket
import sys
from urllib.error import URLError

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


class VideoDownloadError(Exception):
    """Error de negocio para mostrar mensajes legibles en la UI."""


def _resource_root() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    current = os.path.abspath(__file__)
    # src/core/downloader.py -> raiz del proyecto
    return os.path.dirname(os.path.dirname(os.path.dirname(current)))


def get_ffmpeg_path() -> str:
    return os.path.join(_resource_root(), "resources", "ffmpeg", "ffmpeg.exe")


def ensure_ffmpeg_exists(path: str | None = None) -> str:
    ffmpeg_path = path or get_ffmpeg_path()
    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(
            "No se encontro ffmpeg.exe embebido en resources/ffmpeg."
        )
    return ffmpeg_path


def analyze_url(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title") or "Sin titulo",
                "duration": int(info.get("duration") or 0),
                "thumbnail": info.get("thumbnail") or "",
                "uploader": info.get("uploader") or "",
                "webpage_url": info.get("webpage_url") or url,
            }
    except (URLError, socket.gaierror) as exc:
        raise VideoDownloadError("Sin conexion a internet.") from exc
    except DownloadError as exc:
        raise VideoDownloadError(str(exc)) from exc


def _find_converted_output(out_dir: str, title: str, extension: str) -> str:
    preferred = os.path.join(out_dir, f"{title}.{extension}")
    if os.path.exists(preferred):
        return preferred
    candidates = glob.glob(os.path.join(out_dir, f"{title}*.{extension}"))
    if candidates:
        candidates.sort(key=os.path.getmtime, reverse=True)
        return candidates[0]
    return preferred


def download(
    url: str,
    out_dir: str,
    ffmpeg_location: str | None = None,
    progress_hook=None,
    preferredcodec: str = "mp3",
    preferredquality: str = "192",
) -> str:
    ffmpeg_path = ensure_ffmpeg_exists(ffmpeg_location)
    os.makedirs(out_dir, exist_ok=True)

    outtmpl = os.path.join(out_dir, "%(title).180s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "ffmpeg_location": ffmpeg_path,
        "noplaylist": True,
        "restrictfilenames": False,
        "progress_hooks": [progress_hook] if progress_hook else [],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": preferredcodec,
                "preferredquality": preferredquality,
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "output")
            return _find_converted_output(out_dir, title, preferredcodec)
    except (URLError, socket.gaierror) as exc:
        raise VideoDownloadError("Sin conexion a internet.") from exc
    except DownloadError as exc:
        text = str(exc)
        if "Private video" in text or "private" in text.lower():
            raise VideoDownloadError("El video es privado.") from exc
        if "Video unavailable" in text or "not available" in text.lower():
            raise VideoDownloadError("El video no esta disponible o fue eliminado.") from exc
        raise VideoDownloadError(text) from exc
