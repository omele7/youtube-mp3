from src.core.downloader import download


def convert_video_to_audio(url, out_dir, ffmpeg_location, preferredcodec, preferredquality, progress_hook=None):
    return download(
        url=url,
        out_dir=out_dir,
        ffmpeg_location=ffmpeg_location,
        progress_hook=progress_hook,
        preferredcodec=preferredcodec,
        preferredquality=preferredquality,
    )
