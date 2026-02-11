
import os
import zipfile
import urllib.request
import shutil
import sys
from pathlib import Path

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
INSTALL_DIR = Path("ffmpeg_bin")

def install_ffmpeg():
    if (INSTALL_DIR / "bin" / "ffmpeg.exe").exists():
        print(f"✅ FFmpeg already found at {INSTALL_DIR}")
        return

    print(f"⬇️ Downloading FFmpeg from {FFMPEG_URL}...")
    zip_path = "ffmpeg.zip"
    try:
        urllib.request.urlretrieve(FFMPEG_URL, zip_path)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return

    print("📦 Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("temp_ffmpeg")
    
    # Move the inner folder content
    extracted_folder = next(Path("temp_ffmpeg").glob("*"))
    shutil.move(str(extracted_folder), str(INSTALL_DIR))
    
    # Cleanup
    os.remove(zip_path)
    shutil.rmtree("temp_ffmpeg")
    
    print(f"✅ FFmpeg installed to {INSTALL_DIR}")
    
    # Verify
    bin_path = INSTALL_DIR / "bin"
    if (bin_path / "ffmpeg.exe").exists():
        print(f"Executable verified at: {bin_path / 'ffmpeg.exe'}")
        
        # Determine strict absolute path to add to PATH
        abs_bin_path = bin_path.resolve()
        print(f"⚠️ ADD THIS TO PATH: {abs_bin_path}")

if __name__ == "__main__":
    install_ffmpeg()
