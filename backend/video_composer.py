"""
Simple Video Composer for Granite
Combines Manim animation + TTS narration into final polished video.
Works without ImageMagick by using solid-colour backgrounds instead of text overlays.

No paid API dependencies — uses only moviepy + ffmpeg.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from crewai import Agent

# ── Ensure local FFmpeg is on PATH ───────────────────────────────────
_ffmpeg_bin = Path(__file__).parent / "ffmpeg_bin" / "bin"
if _ffmpeg_bin.exists():
    os.environ["PATH"] = str(_ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")

# ── moviepy v1/v2 compatibility ──────────────────────────────────────
try:
    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        CompositeVideoClip,
        concatenate_videoclips,
        ColorClip,
    )
    HAS_MOVIEPY = True
except ImportError:
    try:
        from moviepy.editor import (
            VideoFileClip,
            AudioFileClip,
            CompositeVideoClip,
            concatenate_videoclips,
            ColorClip,
        )
        HAS_MOVIEPY = True
    except ImportError:
        HAS_MOVIEPY = False
        print("⚠️  moviepy not installed — video composition will use fallback")


class VideoComposerAgent(Agent):
    """CrewAI Agent wrapper around SimpleVideoComposer."""

    def __init__(self, **kwargs):
        default_config = {
            "role": "Video Composer",
            "goal": "Create engaging educational videos with animations and narration",
            "backstory": "Expert video editor specialising in educational content",
            "verbose": True,
            "allow_delegation": False,
        }
        config = {**default_config, **kwargs}
        super().__init__(**config)
        self._composer = SimpleVideoComposer()

    async def compose_video(self, lesson_plan, animations, narration):
        return await self._composer.compose_video(lesson_plan, animations, narration)


class SimpleVideoComposer:
    """Simplified video composer that works without ImageMagick."""

    def __init__(self):
        self.resolution = (1920, 1080)
        self.fps = 30

    async def compose_video(
        self, lesson_plan, animations: List, narration
    ) -> Dict[str, Any]:
        """Create a video from animation clips + audio narration."""

        if not HAS_MOVIEPY:
            return self._simulate_video_creation(lesson_plan, animations, narration)

        try:
            job_dir = os.environ.get("GRANITE_JOB_DIR")
            if job_dir:
                output_dir = Path(job_dir)
            else:
                output_dir = Path("output_videos") / "default"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Load audio
            audio_clip = None
            duration = 30.0
            if narration and narration.audio_path and os.path.exists(narration.audio_path):
                try:
                    audio_clip = AudioFileClip(narration.audio_path)
                    duration = audio_clip.duration
                except Exception as e:
                    print(f"Audio load error: {e}")

            # Build clip list
            clips = []

            # Title card (blue)
            clips.append(ColorClip(size=self.resolution, color=(0, 50, 100), duration=3))

            # Animation clips or coloured placeholders
            for i, animation in enumerate(animations[:5]):
                if hasattr(animation, "video_path") and animation.video_path and os.path.exists(animation.video_path):
                    try:
                        clip = VideoFileClip(animation.video_path).resize(self.resolution)
                        clips.append(clip)
                    except Exception as e:
                        print(f"Animation load error: {e}")
                        clips.append(
                            ColorClip(size=self.resolution, color=(50 + i * 30, 50, 50), duration=5)
                        )
                else:
                    clips.append(
                        ColorClip(size=self.resolution, color=(100, 50 + i * 20, 50), duration=5)
                    )

            # Conclusion card (green)
            clips.append(ColorClip(size=self.resolution, color=(0, 100, 50), duration=3))

            if not clips:
                raise RuntimeError("No video clips created")

            final_video = concatenate_videoclips(clips, method="compose")

            if audio_clip:
                final_video = final_video.set_duration(audio_clip.duration)
                final_video = final_video.set_audio(audio_clip)

            output_path = output_dir / f"edu_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            print(f"🎬 Exporting video to: {output_path}")
            try:
                final_video.write_videofile(
                    str(output_path),
                    fps=self.fps,
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile="temp-audio.m4a",
                    remove_temp=True,
                    verbose=False,
                    logger=None,
                    preset="fast",
                    bitrate="1000k",
                )

                if not self._validate_video(output_path):
                    raise RuntimeError("Generated video file is corrupted or incomplete")

                print(f"✅ Video successfully created: {output_path}")

            except Exception as e:
                print(f"❌ Video export failed: {e}")
                if output_path.exists():
                    output_path.unlink()
                raise
            finally:
                final_video.close()
                if audio_clip:
                    audio_clip.close()

            return {
                "video_path": str(output_path),
                "duration": final_video.duration if hasattr(final_video, "duration") else duration,
                "resolution": self.resolution,
                "fps": self.fps,
                "success": True,
            }

        except Exception as e:
            print(f"Video composition error: {e}")
            return self._simulate_video_creation(lesson_plan, animations, narration)

    # ─── Validation ──────────────────────────────────────────────────
    def _validate_video(self, video_path) -> bool:
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_streams", str(video_path),
                ],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False

            probe_data = json.loads(result.stdout)
            streams = probe_data.get("streams", [])
            video_streams = [s for s in streams if s.get("codec_type") == "video"]
            if not video_streams:
                return False

            dur = float(video_streams[0].get("duration", 0))
            if dur < 1.0:
                return False

            print(f"✅ Video validation passed: {dur:.1f}s")
            return True

        except FileNotFoundError:
            # ffprobe not available — skip validation
            return True
        except Exception as e:
            print(f"⚠️  Video validation warning: {e}")
            return False

    # ─── Fallback ────────────────────────────────────────────────────
    def _simulate_video_creation(self, lesson_plan, animations, narration) -> Dict[str, Any]:
        job_dir = os.environ.get("GRANITE_JOB_DIR")
        if job_dir:
            output_dir = Path(job_dir)
        else:
            output_dir = Path("output_videos") / "default"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"demo_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(output_path, "w") as f:
            f.write(f"Demo Video — {lesson_plan.title}\n")
            f.write(f"Duration: {narration.duration if narration else 30} seconds\n")
            f.write(f"Animations: {len(animations)}\n")

        return {
            "video_path": str(output_path),
            "duration": narration.duration if narration else 30,
            "resolution": self.resolution,
            "fps": self.fps,
            "success": False,
        }
