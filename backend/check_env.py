
import subprocess
import sys
import importlib.util
import os

def check_command(cmd):
    try:
        subprocess.run([cmd, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def check_import(module_name, pip_name=None):
    if not pip_name:
        pip_name = module_name
    
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"❌ Missing python package: {module_name} (pip install {pip_name})")
        return False
    print(f"✅ Found python package: {module_name}")
    return True

print("Checking environment...")

# Check FFmpeg
if check_command("ffmpeg"):
    print("✅ Found ffmpeg binary")
else:
    print("❌ Missing ffmpeg binary (required for Manim/MoviePy)")

# Check key libraries
required_modules = [
    ("manim", "manim"),
    ("moviepy", "moviepy"),
    ("crewai", "crewai"),
    ("edge_tts", "edge-tts"), 
    ("gtts", "gTTS"),
    ("fitz", "pymupdf"),
    ("PIL", "Pillow")
]

all_ok = True
for mod, pip in required_modules:
    if not check_import(mod, pip):
        all_ok = False

if all_ok:
    print("\nEnvironment check passed! 🚀")
else:
    print("\nEnvironment check failed. Please install missing dependencies.")
