from urllib.parse import urlparse


SUPPORTED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}


def is_valid_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


def is_supported_video_url(url: str) -> bool:
    if not is_valid_url(url):
        return False
    host = urlparse(url).netloc.lower()
    return host in SUPPORTED_HOSTS
