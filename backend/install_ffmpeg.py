
import os
import zipfile
import urllib.request
import shutil
import sys
import time
from pathlib import Path

# Use a specific version link to avoid redirects or "latest" issues sometimes
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
INSTALL_DIR = Path("ffmpeg_bin")
ZIP_PATH = Path("ffmpeg.zip")

def install_ffmpeg():
    # 1. CLEANUP
    print("Cleaning up previous installations...")
    if ZIP_PATH.exists():
        try:
            os.remove(ZIP_PATH)
            print("Deleted old ffmpeg.zip")
        except Exception as e:
            print(f"Warning: Could not delete ffmpeg.zip: {e}")

    if INSTALL_DIR.exists():
        try:
            shutil.rmtree(INSTALL_DIR)
            print("Deleted old ffmpeg_bin directory")
        except Exception as e:
            print(f"Warning: Could not delete ffmpeg_bin: {e}")

    # 2. DOWNLOAD
    print(f"Downloading FFmpeg from {FFMPEG_URL}...")
    try:
        def reporthook(blocknum, blocksize, totalsize):
            readso_far = blocknum * blocksize
            if totalsize > 0:
                percent = readso_far * 1e2 / totalsize
                # Use simple ascii progress bar
                sys.stdout.write(f"\rDownloading: {percent:5.1f}%")
                sys.stdout.flush()
                
        urllib.request.urlretrieve(FFMPEG_URL, ZIP_PATH, reporthook)
        print("\nDownload complete.")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        return

    # 3. EXTRACT
    print("Extracting archive...")
    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall("temp_ffmpeg")
    except zipfile.BadZipFile:
        print("[ERROR] Downloaded file is not a valid zip archive.")
        if ZIP_PATH.exists():
            os.remove(ZIP_PATH)
        return
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return

    # 4. MOVE
    try:
        extracted_root = Path("temp_ffmpeg")
        # The zip usually contains one folder like "ffmpeg-6.0-essentials_build"
        inner_folder = next(extracted_root.glob("*"))
        
        shutil.move(str(inner_folder), str(INSTALL_DIR))
        print(f"Extracted to {INSTALL_DIR}")
        
    except Exception as e:
        print(f"[ERROR] Move failed: {e}")
    finally:
        # Cleanup temp
        if Path("temp_ffmpeg").exists():
            shutil.rmtree("temp_ffmpeg")
        # Keep zip? Better delete to save space
        if ZIP_PATH.exists():
            os.remove(ZIP_PATH)

    # 5. VERIFY
    ffmpeg_exe = INSTALL_DIR / "bin" / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        print(f"FFmpeg executable verified at: {ffmpeg_exe}")
        os.environ["PATH"] = str(INSTALL_DIR / "bin") + os.pathsep + os.environ["PATH"]
        print("Verifying execution...")
        ret = os.system(f'"{ffmpeg_exe}" -version')
        if ret == 0:
            print("[SUCCESS] FFmpeg installed and working.")
        else:
            print("[ERROR] FFmpeg executable failed to run.")
    else:
        print("[ERROR] FFmpeg executable not found after extraction!")

if __name__ == "__main__":
    install_ffmpeg()
