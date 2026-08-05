import os
import shutil
import sys
import urllib.request
import zipfile

URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
OUT_DIR = os.path.join("resources", "ffmpeg")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    zip_path = os.path.join(OUT_DIR, "ffmpeg.zip")
    print("Descargando ffmpeg...")
    urllib.request.urlretrieve(URL, zip_path)
    print("Extrayendo...")
    tmp_dir = os.path.join(OUT_DIR, "tmp")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmp_dir)

    # Buscar ffmpeg.exe
    ff = None
    for root, dirs, files in os.walk(tmp_dir):
        if "ffmpeg.exe" in files:
            ff = os.path.join(root, "ffmpeg.exe")
            break

    if not ff:
        print("NO_FFMPEG_FOUND")
        sys.exit(2)

    dest = os.path.join(OUT_DIR, "ffmpeg.exe")
    shutil.copy2(ff, dest)
    # limpieza
    try:
        os.remove(zip_path)
    except Exception:
        pass
    try:
        shutil.rmtree(tmp_dir)
    except Exception:
        pass

    print("FFMPEG_DONE")


if __name__ == "__main__":
    main()
