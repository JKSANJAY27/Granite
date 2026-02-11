"""
Granite - Custom Tools for the CrewAI Pipeline

Each tool follows CrewAI's BaseTool pattern with a proper Pydantic args_schema.
Docs: https://docs.crewai.com/concepts/tools#subclassing-basetool
"""

import os
import subprocess
import asyncio
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


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
        try:
            import fitz  # PyMuPDF

            if not os.path.exists(file_path):
                return f"Error: File not found at '{file_path}'."

            doc = fitz.open(file_path)
            pages_text = []
            for i, page in enumerate(doc):
                pages_text.append(f"--- Page {i + 1} ---\n{page.get_text()}")
            doc.close()
            full_text = "\n".join(pages_text)
            return full_text if full_text.strip() else "No text content found in the PDF."
        except Exception as e:
            return f"Error extracting text from PDF: {e}"


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
        try:
            from PIL import Image
            import pytesseract

            if not os.path.exists(file_path):
                return f"Error: File not found at '{file_path}'."

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip() if text.strip() else "No text could be extracted from the image."
        except Exception as e:
            return f"Error extracting text from image: {e}"


# ─────────────────────────────────────────────────────────
# 3. Manim Code Executor
# ─────────────────────────────────────────────────────────
class ManimExecutorInput(BaseModel):
    """Input schema for ManimCodeExecutor."""
    code: str = Field(
        ...,
        description=(
            "Complete Python code using the Manim library. "
            "The code MUST define a Scene subclass named 'GraniteScene'. "
            "Example: class GraniteScene(Scene): def construct(self): ..."
        ),
    )


class ManimCodeExecutor(BaseTool):
    name: str = "manim_code_executor"
    description: str = (
        "Executes Python code that uses the Manim animation library to generate a video. "
        "The code MUST define a class named 'GraniteScene' that inherits from Scene. "
        "Returns the file path of the generated .mp4 video on success, or an error message."
    )
    args_schema: Type[BaseModel] = ManimExecutorInput

    def _run(self, code: str) -> str:
        scene_file = "granite_scene.py"
        try:
            # Ensure the Manim import is present
            if "from manim import" not in code:
                code = "from manim import *\n\n" + code

            # Ensure the scene class name is GraniteScene
            if "class GraniteScene" not in code:
                return (
                    "Error: The Manim code must define a class named 'GraniteScene' "
                    "that inherits from Scene. Example:\n"
                    "class GraniteScene(Scene):\n"
                    "    def construct(self):\n"
                    "        ..."
                )

            # Write the code to a file
            with open(scene_file, "w", encoding="utf-8") as f:
                f.write(code)

            # Run Manim   (-ql = low quality for speed during dev, -qm = medium)
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
                stderr = result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr
                return f"Manim execution failed.\nStderr:\n{stderr}"

            # Try to find the output from Manim's stdout
            for line in result.stdout.splitlines():
                if "File ready at" in line:
                    path = line.split("File ready at")[-1].strip().strip("'\".: ")
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


# ─────────────────────────────────────────────────────────
# 4. LMNT Text-to-Speech
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
        "Returns the file path of the generated MP3 audio file."
    )
    args_schema: Type[BaseModel] = LMNTInput

    def _run(self, text: str, output_file: str = "narration.mp3") -> str:
        try:
            from lmnt.api import Speech

            api_key = os.getenv("LMNT_API_KEY")
            if not api_key:
                return "Error: LMNT_API_KEY environment variable is not set."

            async def _synthesize():
                async with Speech(api_key) as speech:
                    synthesis = await speech.synthesize(
                        text,
                        voice="lily",      # LMNT default voice
                        format="mp3",
                    )
                    with open(output_file, "wb") as f:
                        f.write(synthesis["audio"])

            # Run the async function in a new event loop
            asyncio.run(_synthesize())

            if os.path.exists(output_file):
                return output_file
            else:
                return "Error: Audio file was not created."
        except Exception as e:
            return f"Error generating speech with LMNT: {e}"


# ─────────────────────────────────────────────────────────
# 5. Video Composer (merge video + audio)
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
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip

            if not os.path.exists(video_path):
                return f"Error: Video file not found at '{video_path}'."
            if not os.path.exists(audio_path):
                return f"Error: Audio file not found at '{audio_path}'."

            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)

            # If audio is longer than video, loop the video or trim audio
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)

            final = video.set_audio(audio)
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                logger=None,  # suppress moviepy's verbose output
            )

            video.close()
            audio.close()
            final.close()

            if os.path.exists(output_path):
                return output_path
            return "Error: Final video file was not created."
        except Exception as e:
            return f"Error composing video: {e}"


# ─────────────────────────────────────────────────────────
# 6. Quality Checker
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
            if file_size < 1000:  # less than 1 KB is suspicious
                return f"FAIL: Video file is too small ({file_size} bytes). Likely corrupt."

            # Try to get duration using moviepy
            try:
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
