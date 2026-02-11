#!/usr/bin/env python3
"""
Simple Document Processor for Granite
Uses Google Gemini (free) for AI-powered document processing.
Replaces the original Anthropic Claude-based processor.
"""

import os
import asyncio
import base64
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ─── Gemini Client Setup ─────────────────────────────────────────────
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️  google-generativeai not installed — AI features disabled")

# ─── Optional PDF/Image imports ──────────────────────────────────────
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _get_gemini_model(model_name: str = "gemini-2.0-flash"):
    """Get a Gemini generative model instance."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")
    if not api_key:
        raise ValueError("No GEMINI_API_KEY found in environment")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


class SimpleDocumentProcessor:
    """Simple document processor using Gemini (free) for AI analysis."""

    def __init__(self):
        self._model = None
        if HAS_GEMINI:
            try:
                self._model = _get_gemini_model()
            except Exception as e:
                print(f"⚠️  Gemini init failed: {e}")

    async def process_document(
        self,
        file_path: str,
        duration_minutes: float = 1.0,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """Process a document and create educational content."""
        try:
            # Step 1: Extract content
            if progress_callback:
                await progress_callback("🔍 Extracting content from document...")
            content = await self._extract_content(file_path, progress_callback)

            # Step 2: Generate educational summary with Gemini
            if progress_callback:
                await progress_callback("🤖 Analysing educational content with Gemini AI...")
            summary = await self._generate_educational_summary(content, duration_minutes)

            # Step 3: Write output
            if progress_callback:
                await progress_callback("📝 Generating structured learning content...")
            output_dir = Path("output_videos")
            output_dir.mkdir(exist_ok=True)

            output_file = output_dir / f"edu_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("🎓 Educational Content Summary\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"📄 Source: {Path(file_path).name}\n")
                f.write(f"⏱️ Target Duration: {duration_minutes} minutes\n")
                f.write(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("📝 Content:\n")
                f.write("-" * 20 + "\n")
                f.write(summary)
                f.write("\n\n💡 This content is ready for video creation!")

            return {
                "success": True,
                "output_path": str(output_file),
                "content": summary,
                "duration": duration_minutes * 60,
                "processing_time": "< 10 seconds",
            }

        except Exception as e:
            return {"success": False, "error": str(e), "output_path": None}

    # ─── Content extraction ──────────────────────────────────────────
    async def _extract_content(self, file_path: str, progress_callback=None) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            if progress_callback:
                await progress_callback("📄 Processing PDF document...")
            return await self._extract_from_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            if progress_callback:
                await progress_callback("🖼️ Processing image with Gemini Vision...")
            return await self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF / PyPDF2."""
        text = ""

        # Try PyMuPDF first
        if HAS_PYMUPDF:
            try:
                doc = fitz.open(pdf_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
            except Exception as e:
                print(f"PyMuPDF failed: {e}")

        # Fallback to PyPDF2
        if not text.strip() and HAS_PYPDF2:
            try:
                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text()
            except Exception as e:
                print(f"PyPDF2 failed: {e}")

        # If text extraction failed and we have Gemini Vision, try that
        if not text.strip() and self._model and HAS_PYMUPDF and HAS_PIL:
            text = await self._extract_pdf_with_gemini_vision(pdf_path)

        if not text.strip():
            text = f"Content extracted from {Path(pdf_path).name} (text extraction unavailable)"

        return text.strip()

    async def _extract_pdf_with_gemini_vision(self, pdf_path: str) -> str:
        """Use Gemini Vision to OCR PDF pages that have no selectable text."""
        import io

        try:
            doc = fitz.open(pdf_path)
            all_text = ""
            for i in range(min(len(doc), 5)):  # limit to 5 pages
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                prompt = (
                    f"Extract all educational content from page {i + 1} of this PDF. "
                    "Include all text, mathematical formulas, diagram descriptions, "
                    "table data, and educational concepts. Format clearly."
                )
                response = self._model.generate_content([prompt, img])
                all_text += f"\n--- Page {i + 1} ---\n{response.text}\n"
            doc.close()
            return all_text.strip()
        except Exception as e:
            print(f"Gemini Vision PDF extraction failed: {e}")
            return ""

    async def _extract_from_image(self, image_path: str) -> str:
        """Extract text from image using Gemini Vision (free)."""
        if self._model and HAS_PIL:
            try:
                img = Image.open(image_path)
                prompt = (
                    "Extract all text content from this image. Include any "
                    "mathematical formulas, diagram descriptions, and educational "
                    "content. Format it clearly."
                )
                response = self._model.generate_content([prompt, img])
                return response.text
            except Exception as e:
                print(f"Gemini Vision OCR failed: {e}")

        # Fallback: pytesseract
        try:
            import pytesseract

            img = Image.open(image_path)
            return pytesseract.image_to_string(img)
        except Exception:
            pass

        return f"Image content from {Path(image_path).name} (extraction unavailable)"

    # ─── AI summary ──────────────────────────────────────────────────
    async def _generate_educational_summary(self, content: str, duration_minutes: float) -> str:
        """Generate educational summary using Gemini."""
        if not self._model:
            return f"Educational content (AI unavailable):\n\n{content[:500]}..."

        try:
            prompt = f"""Create an educational summary for a {duration_minutes}-minute video based on this content:

{content[:4000]}

Format your response as:

# Main Topic
[Clear topic title]

## Key Learning Objectives
- [3-4 main learning goals]

## Content Breakdown
[Structured explanation suitable for {duration_minutes} minutes]

## Visual Elements Needed
- [Suggestions for animations/graphics]

## Key Takeaways
- [Main points students should remember]

Keep it concise but comprehensive for the time limit."""

            response = self._model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Educational summary (AI error: {e})\n\nExtracted content:\n{content[:1000]}..."


# ─── Quick test ──────────────────────────────────────────────────────
async def test_processor():
    processor = SimpleDocumentProcessor()
    pdf_files = list(Path("lesson_pdfs").glob("*.pdf"))
    if pdf_files:
        result = await processor.process_document(str(pdf_files[0]), 1.5)
        print(f"Result: {result}")
    else:
        print("No test files found")


if __name__ == "__main__":
    asyncio.run(test_processor())
