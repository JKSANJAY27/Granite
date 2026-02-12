
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Add local ffmpeg to path
ffmpeg_bin = Path("ffmpeg_bin/bin").resolve()
os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + os.environ["PATH"]

def compose_video():
    # Paths from the failed job
    # Start looking for the latest job output
    output_jobs_dir = Path("output_videos")
    if not output_jobs_dir.exists():
        print("[ERROR] No output_videos directory found.")
        return

    # Find the most recent job folder
    job_dirs = [d for d in output_jobs_dir.iterdir() if d.is_dir()]
    if not job_dirs:
         print("[ERROR] No job directories found.")
         return
         
    # Sort by modification time, newest first
    job_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    job_dir = job_dirs[0]
    print(f"Using latest job directory: {job_dir}")

    # Locate video and audio
    # Video might be in media/videos/... or just in the folder?
    # Usually Manim puts it in media/videos/granite_scene/480p15/GraniteScene.mp4
    # But let's search recursively for .mp4 that isn't the final one
    
    video_path = None
    # Prioritise the GraniteScene.mp4
    candidates = list(job_dir.rglob("GraniteScene.mp4"))
    if candidates:
        video_path = candidates[0]
    else:
        # Fallback to any mp4 that isn't "final" or "composed"
        mp4s = list(job_dir.rglob("*.mp4"))
        for mp4 in mp4s:
            if "final" not in mp4.name and "composed" not in mp4.name:
                video_path = mp4
                break
    
    audio_path = job_dir / "narration.mp3"
    output_path = job_dir / "final_composed_video.mp4"

    if not video_path or not video_path.exists():
        print(f"[ERROR] Video input not found in {job_dir}")
        return
    if not audio_path.exists():
        print(f"[ERROR] Audio input not found at {audio_path}")
        return

    print(f"Merging:\nVideo: {video_path}\nAudio: {audio_path}")
    print(f"Output: {output_path}")

    # FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] Video saved to: {output_path}")
            # Copy to root output for easy access
            latest_copy = output_jobs_dir / "latest_manual_fix.mp4"
            shutil.copy(output_path, latest_copy)
            print(f"[SUCCESS] Also available at: {latest_copy}")
        else:
            print(f"[ERROR] FFmpeg failed:\n{result.stderr}")
    except FileNotFoundError:
        print("[ERROR] FFmpeg not found in PATH. Ensure install_ffmpeg.py finished successfully.")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    compose_video()
