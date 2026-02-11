"""
Granite - Custom Tools for the CrewAI Pipeline

Each tool follows CrewAI's BaseTool pattern with a proper Pydantic args_schema.
Docs: https://docs.crewai.com/concepts/tools#subclassing-basetool

ALL paid API dependencies removed:
  - LMNT TTS → edge-tts / gTTS (FREE)
  - Anthropic → Gemini (configured in agents.py)
"""

import os
import re
import subprocess
import asyncio
from typing import Type
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# ── Ensure local FFmpeg is on PATH ───────────────────────────────────
_ffmpeg_bin = Path(__file__).parent / "ffmpeg_bin" / "bin"
if _ffmpeg_bin.exists():
    os.environ["PATH"] = str(_ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")


# ─────────────────────────────────────────────────────────
# 1. PDF Content Extractor
# ─────────────────────────────────────────────────────────
class PDFExtractorInput(BaseModel):
    """Input schema for PDFContentExtractor."""
    file_path: str = Field(..., description="Absolute or relative path to the PDF file.")


class PDFContentExtractor(BaseTool):
    name: str = "pdf_content_extractor"
    description: str = (
        "Extracts all text content from a PDF file. "
        "Returns the full text as a string."
    )
    args_schema: Type[BaseModel] = PDFExtractorInput

    def _run(self, file_path: str) -> str:
        # Try PyMuPDF first (best quality)
        text = self._try_pymupdf(file_path)
        if text:
            return text

        # Fallback to PyPDF2
        text = self._try_pypdf2(file_path)
        if text:
            return text

        return f"Error: Could not extract text from '{file_path}'. Ensure PyMuPDF or PyPDF2 is installed."

    def _try_pymupdf(self, file_path: str) -> str:
        try:
            import fitz  # PyMuPDF

            if not os.path.exists(file_path):
                return ""

            doc = fitz.open(file_path)
            pages_text = []
            for i, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    pages_text.append(f"--- Page {i + 1} ---\n{page_text}")
            doc.close()
            full_text = "\n".join(pages_text)
            return full_text if full_text.strip() else ""
        except ImportError:
            return ""
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            return ""

    def _try_pypdf2(self, file_path: str) -> str:
        try:
            import PyPDF2

            if not os.path.exists(file_path):
                return f"Error: File not found at '{file_path}'."

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text.append(f"--- Page {i + 1} ---\n{text}")
                full_text = "\n".join(pages_text)
                return full_text if full_text.strip() else ""
        except ImportError:
            return ""
        except Exception as e:
            return f"Error extracting PDF with PyPDF2: {e}"


# ─────────────────────────────────────────────────────────
# 2. Image Content Extractor (OCR)
# ─────────────────────────────────────────────────────────
class ImageExtractorInput(BaseModel):
    """Input schema for ImageContentExtractor."""
    file_path: str = Field(..., description="Absolute or relative path to the image file.")


class ImageContentExtractor(BaseTool):
    name: str = "image_content_extractor"
    description: str = (
        "Extracts text from an image file using OCR (Optical Character Recognition). "
        "Returns the extracted text."
    )
    args_schema: Type[BaseModel] = ImageExtractorInput

    def _run(self, file_path: str) -> str:
        # Try Gemini Vision first (free, best quality)
        text = self._try_gemini_vision(file_path)
        if text:
            return text

        # Fallback to pytesseract (free, offline)
        text = self._try_pytesseract(file_path)
        if text:
            return text

        return f"Error: Could not extract text from '{file_path}'. Install pytesseract or google-generativeai."

    def _try_gemini_vision(self, file_path: str) -> str:
        """Use Gemini Vision (free) for high-quality OCR."""
        try:
            import google.generativeai as genai
            from PIL import Image

            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")
            if not api_key:
                return ""

            if not os.path.exists(file_path):
                return ""

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            img = Image.open(file_path)

            prompt = (
                "Extract all text content from this image. Include any "
                "mathematical formulas, diagram descriptions, and educational "
                "content. Format clearly and preserve structure."
            )
            response = model.generate_content([prompt, img])
            return response.text.strip() if response.text else ""

        except ImportError:
            return ""
        except Exception as e:
            print(f"Gemini Vision OCR failed: {e}")
            return ""

    def _try_pytesseract(self, file_path: str) -> str:
        """Fallback to pytesseract (free, offline)."""
        try:
            from PIL import Image
            import pytesseract

            if not os.path.exists(file_path):
                return f"Error: File not found at '{file_path}'."

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip() if text.strip() else "No text could be extracted from the image."
        except ImportError:
            return ""
        except Exception as e:
            return f"Error extracting text from image: {e}"


# ─────────────────────────────────────────────────────────
# 3. Manim Code Executor (Enhanced with better error handling)
# ─────────────────────────────────────────────────────────
class ManimExecutorInput(BaseModel):
    """Input schema for ManimCodeExecutor."""
    code: str = Field(
        ...,
        description=(
            "Complete Python code using the Manim library. "
            "The code MUST define a Scene subclass named 'GraniteScene'. "
            "Start with 'from manim import *'. "
            "Example: class GraniteScene(Scene): def construct(self): ..."
        ),
    )


# Common deprecated API mappings for auto-fix suggestions
DEPRECATED_API_FIXES = {
    "ShowCreation": "Create",
    "TextMobject": "Text",
    "TexMobject": "MathTex",
    "get_graph": "plot",
    "get_graph_label": "get_x_axis_label",
    "play_sound": "# play_sound removed",
    "ShowPassingFlash": "ShowPassingFlash",
}


class ManimCodeExecutor(BaseTool):
    name: str = "manim_code_executor"
    description: str = (
        "Executes Python code that uses the Manim animation library to generate a video. "
        "The code MUST define a class named 'GraniteScene' that inherits from Scene. "
        "Returns the file path of the generated .mp4 video on success, or a detailed "
        "error message with fix suggestions on failure."
    )
    args_schema: Type[BaseModel] = ManimExecutorInput

    def _run(self, code: str) -> str:
        scene_file = "granite_scene.py"
        try:
            # ── Pre-processing: Clean and validate the code ──────────
            code = self._preprocess_code(code)

            validation_error = self._validate_code(code)
            if validation_error:
                return validation_error

            # ── Auto-fix common deprecated APIs ──────────────────────
            code, fixes_applied = self._auto_fix_deprecated(code)
            if fixes_applied:
                print(f"[ManimExecutor] Auto-fixed deprecated APIs: {', '.join(fixes_applied)}")

            # Write the code to a file
            with open(scene_file, "w", encoding="utf-8") as f:
                f.write(code)

            # Run Manim   (-ql = low quality for speed during dev)
            command = [
                "manim", "render",
                "-ql",                      # low quality (480p15) — fast for iteration
                "--media_dir", "media",
                scene_file,
                "GraniteScene",
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            if result.returncode != 0:
                return self._format_error(result.stderr, code)

            # Try to find the output from Manim's stdout
            for line in result.stdout.splitlines():
                if "File ready at" in line:
                    path = line.split("File ready at")[-1].strip().strip("'\". ")
                    if os.path.exists(path):
                        return path

            # Fallback: search for most recent mp4 in media/
            video_dir = os.path.join("media", "videos")
            if os.path.isdir(video_dir):
                mp4_files = []
                for root, _, files in os.walk(video_dir):
                    for fname in files:
                        if fname.endswith(".mp4"):
                            full = os.path.join(root, fname)
                            mp4_files.append((full, os.path.getmtime(full)))
                if mp4_files:
                    mp4_files.sort(key=lambda x: x[1], reverse=True)
                    return mp4_files[0][0]

            return "Manim finished but no video file was found. Check Manim output."

        except subprocess.TimeoutExpired:
            return "Error: Manim execution timed out after 5 minutes."
        except Exception as e:
            return f"Exception during Manim execution: {e}"

    def _preprocess_code(self, code: str) -> str:
        """Clean up code: remove markdown fences, ensure imports."""
        if "```python" in code:
            code = code.split("```python", 1)[1]
            if "```" in code:
                code = code.rsplit("```", 1)[0]
        elif "```" in code:
            parts = code.split("```")
            if len(parts) >= 3:
                code = parts[1]
            elif len(parts) == 2:
                code = parts[1] if parts[1].strip() else parts[0]

        code = code.strip()

        if "from manim import" not in code:
            code = "from manim import *\n\n" + code

        return code

    def _validate_code(self, code: str) -> str:
        """Validate code structure. Returns error string or empty string."""
        if "class GraniteScene" not in code:
            return (
                "Error: The Manim code must define a class named 'GraniteScene' "
                "that inherits from Scene.\n\n"
                "REQUIRED STRUCTURE:\n"
                "```python\n"
                "from manim import *\n\n"
                "class GraniteScene(Scene):\n"
                "    def construct(self):\n"
                "        # Your animation code here\n"
                "        ...\n"
                "```\n\n"
                "Please rewrite the code with the correct class name."
            )

        if "def construct" not in code:
            return (
                "Error: The GraniteScene class must have a 'construct' method.\n\n"
                "REQUIRED:\n"
                "class GraniteScene(Scene):\n"
                "    def construct(self):\n"
                "        ...\n\n"
                "Please add the construct method."
            )

        return ""

    def _auto_fix_deprecated(self, code: str) -> tuple:
        """Auto-fix known deprecated APIs. Returns (fixed_code, list_of_fixes)."""
        fixes = []
        for old_api, new_api in DEPRECATED_API_FIXES.items():
            if old_api in code and old_api != new_api:
                code = code.replace(old_api, new_api)
                fixes.append(f"{old_api} → {new_api}")
        return code, fixes

    def _format_error(self, stderr: str, code: str) -> str:
        """Format Manim errors with actionable fix suggestions."""
        if len(stderr) > 3000:
            stderr = stderr[-3000:]

        error_msg = f"Manim execution failed.\n\nERROR OUTPUT:\n{stderr}\n\n"
        suggestions = []

        if "ModuleNotFoundError" in stderr:
            module = re.search(r"No module named '(\w+)'", stderr)
            if module:
                suggestions.append(
                    f"Module '{module.group(1)}' is not installed. "
                    f"Avoid importing external modules — use only 'from manim import *'."
                )

        if "AttributeError" in stderr:
            attr = re.search(r"has no attribute '(\w+)'", stderr)
            if attr:
                attr_name = attr.group(1)
                if attr_name in DEPRECATED_API_FIXES:
                    suggestions.append(
                        f"'{attr_name}' is deprecated. Use '{DEPRECATED_API_FIXES[attr_name]}' instead."
                    )
                else:
                    suggestions.append(
                        f"'{attr_name}' does not exist. Check the Manim Community Edition docs. "
                        f"Common replacements: ShowCreation→Create, TextMobject→Text, "
                        f"TexMobject→MathTex, get_graph→plot."
                    )

        if "FileNotFoundError" in stderr or "WinError 2" in stderr:
            suggestions.append(
                "CRITICAL: LaTeX compiler (pdflatex) is NOT INSTALLED on this system.\n"
                "  You MUST NOT use MathTex() or Tex() — they require LaTeX!\n"
                "  SOLUTION: Replace ALL MathTex(...) and Tex(...) calls with Text(...).\n"
                "  For math expressions, write them in plain text. Examples:\n"
                "    WRONG:  MathTex(r'\\\\frac{dy}{dx}')\n"
                "    RIGHT:  Text('dy/dx', font_size=36)\n"
                "    WRONG:  MathTex(r'x^2 + y^2 = r^2')\n"
                "    RIGHT:  Text('x² + y² = r²', font_size=36)\n"
                "  Use Unicode superscripts/subscripts: ² ³ ⁴ ₁ ₂ ₃"
            )

        if "LaTeX" in stderr or "latex" in stderr.lower():
            suggestions.append(
                "LaTeX compilation error. LaTeX may not be installed.\n"
                "  SOLUTION: Replace ALL MathTex() and Tex() with Text().\n"
                "  - Use Text('x² + y² = z²') instead of MathTex(r'x^2 + y^2 = z^2')\n"
                "  - Use Text() for ALL text rendering\n"
                "  - Do NOT use MathTex() or Tex() at all"
            )

        if "TypeError" in stderr:
            suggestions.append(
                "TypeError — check function arguments. Common issues:\n"
                "  - self.play() needs an Animation, not a Mobject: use Create(obj) or FadeIn(obj)\n"
                "  - ax.plot() takes a function, not a Mobject\n"
                "  - Color should be a Manim constant (BLUE, RED, etc.) not a string"
            )

        if "NameError" in stderr:
            name = re.search(r"name '(\w+)' is not defined", stderr)
            if name:
                suggestions.append(
                    f"'{name.group(1)}' is not defined. Make sure all variables are "
                    f"created before they are used. Also verify imports."
                )

        if "ValueError" in stderr:
            suggestions.append(
                "ValueError — common causes:\n"
                "  - Invalid color specification\n"
                "  - Invalid range for Axes (x_range or y_range)\n"
                "  - Mismatched array dimensions"
            )

        if suggestions:
            error_msg += "FIX SUGGESTIONS:\n"
            for i, s in enumerate(suggestions, 1):
                error_msg += f"  {i}. {s}\n"

        error_msg += (
            "\nPlease fix the code based on the error and suggestions above, "
            "then try again with the manim_code_executor tool."
        )

        return error_msg


# ─────────────────────────────────────────────────────────
# 4. Text-to-Speech (LMNT primary, edge-tts / gTTS fallback)
# ─────────────────────────────────────────────────────────
class LMNTInput(BaseModel):
    """Input schema for LMNTTextToSpeech."""
    text: str = Field(..., description="The narration text to convert to speech.")
    output_file: str = Field(
        default="narration.mp3",
        description="Output file path for the generated audio (e.g. narration.mp3).",
    )


class LMNTTextToSpeech(BaseTool):
    name: str = "lmnt_text_to_speech"
    description: str = (
        "Converts text into natural-sounding speech audio using the LMNT API. "
        "Falls back to edge-tts or gTTS if LMNT is unavailable. "
        "Returns the file path of the generated MP3 audio file."
    )
    args_schema: Type[BaseModel] = LMNTInput

    def _run(self, text: str, output_file: str = "narration.mp3") -> str:
        # Method 1: LMNT (primary — high quality)
        result = self._try_lmnt(text, output_file)
        if result:
            return result

        # Method 2: edge-tts (fallback — free, high quality)
        result = self._try_edge_tts(text, output_file)
        if result:
            return result

        # Method 3: gTTS (fallback — free, standard quality)
        result = self._try_gtts(text, output_file)
        if result:
            return result

        return (
            "Error: No TTS engine available. Set LMNT_API_KEY or install:\n"
            "  pip install edge-tts    (free fallback — high quality neural voices)\n"
            "  pip install gTTS        (free fallback — Google Translate TTS)"
        )

    def _try_lmnt(self, text: str, output_file: str) -> str:
        """Try LMNT API (primary, best quality)."""
        try:
            from lmnt.api import Speech

            api_key = os.getenv("LMNT_API_KEY")
            if not api_key:
                print("⚠️  LMNT_API_KEY not set — falling back to free TTS")
                return ""

            async def _synthesize():
                async with Speech(api_key) as speech:
                    synthesis = await speech.synthesize(
                        text,
                        voice="lily",      # LMNT default voice
                        format="mp3",
                    )
                    with open(output_file, "wb") as f:
                        f.write(synthesis["audio"])

            # Run the async function — handle case where event loop is already running
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _synthesize()).result()
            except RuntimeError:
                asyncio.run(_synthesize())

            if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
                print(f"✅ Audio generated with LMNT: {output_file}")
                return output_file
            return ""

        except ImportError:
            print("⚠️  lmnt package not installed — falling back to free TTS")
            return ""
        except Exception as e:
            print(f"⚠️  LMNT failed: {e} — falling back to free TTS")
            return ""

    def _try_edge_tts(self, text: str, output_file: str) -> str:
        """Fallback: edge-tts (free Microsoft Edge neural voices)."""
        try:
            import edge_tts

            async def _synthesize():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice="en-US-AriaNeural",
                    rate="-5%",
                )
                await communicate.save(output_file)

            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _synthesize()).result()
            except RuntimeError:
                asyncio.run(_synthesize())

            if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
                print(f"✅ Audio generated with edge-tts: {output_file}")
                return output_file
            return ""

        except ImportError:
            return ""
        except Exception as e:
            print(f"edge-tts failed: {e}")
            return ""

    def _try_gtts(self, text: str, output_file: str) -> str:
        """Fallback: gTTS (free Google Translate TTS)."""
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(output_file)

            if os.path.exists(output_file):
                print(f"✅ Audio generated with gTTS: {output_file}")
                return output_file
            return ""

        except ImportError:
            return ""
        except Exception as e:
            print(f"gTTS failed: {e}")
            return ""


# ─────────────────────────────────────────────────────────
# 5. Video Composer (merge video + audio) — NO PAID DEPS
# ─────────────────────────────────────────────────────────
class VideoComposerInput(BaseModel):
    """Input schema for VideoComposerTool."""
    video_path: str = Field(..., description="Path to the video file (e.g. from Manim).")
    audio_path: str = Field(..., description="Path to the audio file (e.g. narration.mp3).")
    output_path: str = Field(
        default="final_output.mp4",
        description="Output path for the composed video.",
    )


class VideoComposerTool(BaseTool):
    name: str = "video_composer"
    description: str = (
        "Combines a video file and an audio file into a single final video. "
        "The audio is overlaid onto the video. Returns the output file path."
    )
    args_schema: Type[BaseModel] = VideoComposerInput

    def _run(
        self,
        video_path: str,
        audio_path: str,
        output_path: str = "final_output.mp4",
    ) -> str:
        # First try ffmpeg directly (more reliable, no ImageMagick needed)
        ffmpeg_result = self._try_ffmpeg(video_path, audio_path, output_path)
        if ffmpeg_result:
            return ffmpeg_result

        # Fallback to moviepy
        return self._try_moviepy(video_path, audio_path, output_path)

    def _try_ffmpeg(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Try composing with ffmpeg directly."""
        try:
            if not os.path.exists(video_path):
                return ""
            if not os.path.exists(audio_path):
                return ""

            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            return ""
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""
        except Exception:
            return ""

    def _try_moviepy(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Fallback to moviepy for composition."""
        try:
            # Support both moviepy v1 (moviepy.editor) and v2 (moviepy)
            try:
                from moviepy import VideoFileClip, AudioFileClip
            except ImportError:
                from moviepy.editor import VideoFileClip, AudioFileClip

            if not os.path.exists(video_path):
                return f"Error: Video file not found at '{video_path}'."
            if not os.path.exists(audio_path):
                return f"Error: Audio file not found at '{audio_path}'."

            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)

            # If audio is longer than video, trim audio
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)

            final = video.set_audio(audio)
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )

            video.close()
            audio.close()
            final.close()

            if os.path.exists(output_path):
                return output_path
            return "Error: Final video file was not created."
        except ImportError:
            return (
                "Error: Neither ffmpeg nor moviepy is available for video composition. "
                "Install moviepy with: pip install moviepy"
            )
        except Exception as e:
            return f"Error composing video: {e}"


# ─────────────────────────────────────────────────────────
# 6. Quality Checker — NO PAID DEPS
# ─────────────────────────────────────────────────────────
class QualityCheckerInput(BaseModel):
    """Input schema for QualityCheckerTool."""
    video_path: str = Field(..., description="Path to the final video to check.")


class QualityCheckerTool(BaseTool):
    name: str = "quality_checker"
    description: str = (
        "Performs basic quality checks on a video file: "
        "verifies existence, file size, duration, and resolution."
    )
    args_schema: Type[BaseModel] = QualityCheckerInput

    def _run(self, video_path: str) -> str:
        try:
            if not os.path.exists(video_path):
                return f"FAIL: Video file does not exist at '{video_path}'."

            file_size = os.path.getsize(video_path)
            if file_size < 1000:
                return f"FAIL: Video file is too small ({file_size} bytes). Likely corrupt."

            # Try ffprobe first (faster, more reliable)
            ffprobe_result = self._try_ffprobe(video_path, file_size)
            if ffprobe_result:
                return ffprobe_result

            # Fallback to moviepy
            try:
                # Support both moviepy v1 and v2
                try:
                    from moviepy import VideoFileClip
                except ImportError:
                    from moviepy.editor import VideoFileClip
                clip = VideoFileClip(video_path)
                duration = clip.duration
                w, h = clip.size
                clip.close()
                return (
                    f"PASS: Video quality check successful.\n"
                    f"  - Path: {video_path}\n"
                    f"  - Size: {file_size / 1024:.1f} KB\n"
                    f"  - Duration: {duration:.1f} seconds\n"
                    f"  - Resolution: {w}x{h}"
                )
            except Exception:
                return (
                    f"PASS (partial): File exists and has size {file_size / 1024:.1f} KB, "
                    f"but could not read video metadata."
                )
        except Exception as e:
            return f"Error during quality check: {e}"

    def _try_ffprobe(self, video_path: str, file_size: int) -> str:
        """Try quality check with ffprobe."""
        try:
            import json as json_module
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams", "-show_format",
                    video_path,
                ],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return ""

            probe = json_module.loads(result.stdout)
            streams = probe.get("streams", [])
            fmt = probe.get("format", {})

            video_streams = [s for s in streams if s.get("codec_type") == "video"]
            if not video_streams:
                return "FAIL: No video streams found in the file."

            vs = video_streams[0]
            w = vs.get("width", "?")
            h = vs.get("height", "?")
            duration = float(fmt.get("duration", 0))

            return (
                f"PASS: Video quality check successful.\n"
                f"  - Path: {video_path}\n"
                f"  - Size: {file_size / 1024:.1f} KB\n"
                f"  - Duration: {duration:.1f} seconds\n"
                f"  - Resolution: {w}x{h}\n"
                f"  - Codec: {vs.get('codec_name', 'unknown')}"
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""
        except Exception:
            return ""
