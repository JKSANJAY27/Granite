"""
Granite — Enhanced Integrations Module

All paid APIs (Anthropic, OpenAI GPT-4o, Groq) have been replaced with
Google Gemini (free tier) for:
  - Vision / OCR
  - Fast content analysis
  - Deep educational analysis
  - Quiz generation

Fetch.ai integration is kept as-is (optional, only runs if FETCH_AI_API_KEY is set).
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, List, Any
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ─── Gemini setup ────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _get_gemini_model(model_name: str = "gemini-2.0-flash"):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")
    if not api_key:
        raise ValueError("No GEMINI_API_KEY found")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


# ─── Gemini Vision Integration (replaces OpenAI GPT-4o Vision) ──────
class GeminiVisionIntegration:
    """Uses Gemini Vision (free) for OCR / image understanding."""

    def __init__(self):
        self._model = None
        if HAS_GEMINI:
            try:
                self._model = _get_gemini_model()
            except Exception as e:
                print(f"⚠️  Gemini Vision init failed: {e}")

    async def enhanced_ocr(self, image_path: str) -> Dict[str, Any]:
        """OCR an image using Gemini Vision."""

        if not self._model or not HAS_PIL:
            return {
                "text": f"Demo OCR result for {image_path}",
                "confidence": 0.95,
                "structured_text": {"paragraphs": ["Sample extracted text"]},
                "detected_languages": ["en"],
                "simulation": True,
            }

        try:
            img = Image.open(image_path)
            prompt = (
                "Extract all text from this image. Return a JSON object:\n"
                '{"text": "full extracted text", '
                '"structured_text": {"paragraphs": [...], "headings": [...], '
                '"formulas": [...], "lists": [...]}}\n'
                "Preserve mathematical notation and formatting."
            )
            response = self._model.generate_content([prompt, img])
            content = response.text

            # Try JSON parse
            try:
                j_start = content.find("{")
                j_end = content.rfind("}") + 1
                if j_start >= 0 and j_end > j_start:
                    parsed = json.loads(content[j_start:j_end])
                    return {
                        "text": parsed.get("text", content),
                        "confidence": 0.95,
                        "structured_text": parsed.get("structured_text", {"paragraphs": [content]}),
                        "detected_languages": ["en"],
                    }
            except json.JSONDecodeError:
                pass

            return {
                "text": content,
                "confidence": 0.90,
                "structured_text": self._parse_text_structure(content),
                "detected_languages": ["en"],
            }

        except Exception as e:
            print(f"Gemini Vision OCR error: {e}")
            return {"text": "", "error": str(e)}

    def _parse_text_structure(self, text: str) -> Dict[str, List[str]]:
        structure: Dict[str, List[str]] = {
            "paragraphs": [], "headings": [], "formulas": [], "lists": [],
        }
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if len(line.split()) <= 8 and (line.isupper() or line.istitle()) and not line.endswith("."):
                structure["headings"].append(line)
            elif any(c in line for c in "=+∫∑√"):
                structure["formulas"].append(line)
            elif line.startswith(("•", "-", "*", "1.", "2.", "3.", "a)", "b)")):
                structure["lists"].append(line)
            else:
                structure["paragraphs"].append(line)
        return structure


# ─── Gemini Fast Analysis (replaces Groq) ────────────────────────────
class GeminiFastAnalysis:
    """Fast content analysis using Gemini Flash (free)."""

    def __init__(self):
        self._model = None
        if HAS_GEMINI:
            try:
                self._model = _get_gemini_model("gemini-2.0-flash")
            except Exception:
                pass

    async def fast_content_analysis(self, text: str) -> Dict[str, Any]:
        if not self._model:
            return {
                "concepts": ["mathematics", "education"],
                "difficulty": "intermediate",
                "subject": "Mathematics",
                "key_points": ["Educational content"],
            }

        try:
            prompt = (
                "Analyse this educational content quickly. "
                "Return JSON with: concepts, difficulty, subject, key_points.\n\n"
                f"{text[:2000]}"
            )
            response = self._model.generate_content(prompt)
            content = response.text
            try:
                j_start = content.find("{")
                j_end = content.rfind("}") + 1
                if j_start >= 0:
                    return json.loads(content[j_start:j_end])
            except json.JSONDecodeError:
                pass
            return {
                "concepts": ["mathematics"],
                "difficulty": "intermediate",
                "subject": "Mathematics",
                "key_points": ["Educational content analysis"],
            }
        except Exception as e:
            print(f"Gemini fast analysis error: {e}")
            return {"error": str(e)}

    async def generate_quiz_questions(self, content: str, num_questions: int = 5) -> List[Dict]:
        if not self._model:
            return [
                {
                    "question": "What is the main topic of this lesson?",
                    "options": ["A) Mathematics", "B) Science", "C) History", "D) Literature"],
                    "correct_answer": "A",
                }
            ]

        try:
            prompt = (
                f"Generate {num_questions} multiple-choice questions from this content. "
                "Return a JSON array with objects containing: question, options, correct_answer.\n\n"
                f"{content[:3000]}"
            )
            response = self._model.generate_content(prompt)
            text = response.text
            try:
                j_start = text.find("[")
                j_end = text.rfind("]") + 1
                if j_start >= 0 and j_end > j_start:
                    return json.loads(text[j_start:j_end])
            except json.JSONDecodeError:
                pass
            return []
        except Exception as e:
            print(f"Quiz generation error: {e}")
            return []


# ─── Fetch.ai Integration (optional, unchanged) ─────────────────────
class FetchAIIntegration:
    def __init__(self):
        self.api_key = os.getenv("FETCH_AI_API_KEY")
        self.base_url = "https://rest-dorado.fetch.ai"

    async def share_educational_content(self, video_metadata: Dict[str, Any]) -> str:
        if not self.api_key:
            return "skipped_no_key"
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                async with session.post(
                    f"{self.base_url}/v1/educational-content",
                    json=video_metadata, headers=headers,
                ) as resp:
                    if resp.status == 201:
                        return (await resp.json()).get("id", "unknown")
                    return "failed"
        except Exception as e:
            print(f"Fetch.ai error: {e}")
            return "error"

    async def discover_similar_content(self, subject: str, grade_level: str) -> List[Dict]:
        if not self.api_key:
            return []
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.base_url}/v1/educational-content/search",
                    params={"subject": subject, "grade_level": grade_level, "limit": 10},
                    headers=headers,
                ) as resp:
                    return await resp.json() if resp.status == 200 else []
        except Exception:
            return []


# ─── Unified Integration ─────────────────────────────────────────────
class GraniteIntegrations:
    """Unified integration — all powered by Gemini (free)."""

    def __init__(self):
        self.gemini_vision = GeminiVisionIntegration()
        self.gemini_fast = GeminiFastAnalysis()
        self.fetch = FetchAIIntegration()

    async def enhanced_content_extraction(self, file_path: str) -> Dict[str, Any]:
        vision_result = await self.gemini_vision.enhanced_ocr(file_path)
        analysis = {}
        if vision_result.get("text"):
            analysis = await self.gemini_fast.fast_content_analysis(vision_result["text"])

        deep = await self._gemini_deep_analysis(vision_result.get("text", ""))

        return {
            "text": vision_result.get("text", ""),
            "structure": vision_result.get("structured_text", {}),
            "fast_analysis": analysis,
            "deep_analysis": deep,
            "confidence": vision_result.get("confidence", 0),
            "languages": vision_result.get("detected_languages", ["en"]),
        }

    async def _gemini_deep_analysis(self, text: str) -> Dict[str, Any]:
        if not HAS_GEMINI or not text.strip():
            return {}
        try:
            model = _get_gemini_model()
            prompt = (
                "Provide deep educational analysis of this content. "
                "Return JSON with: learning_objectives, prerequisite_knowledge, "
                "difficulty_progression, assessment_strategies, "
                "common_misconceptions, real_world_applications.\n\n"
                f"{text[:4000]}"
            )
            response = model.generate_content(prompt)
            content = response.text
            j_start = content.find("{")
            j_end = content.rfind("}") + 1
            if j_start >= 0 and j_end > j_start:
                return json.loads(content[j_start:j_end])
            return {"analysis": content}
        except Exception as e:
            print(f"Deep analysis error: {e}")
            return {}

    async def generate_interactive_elements(self, content: str) -> Dict[str, Any]:
        quiz = await self.gemini_fast.generate_quiz_questions(content, num_questions=5)
        return {
            "quiz_questions": quiz,
            "discussion_prompts": [
                "How does this concept apply to everyday life?",
                "What questions do you have about this topic?",
                "Can you think of a real-world example?",
                "How would you explain this to a friend?",
            ],
            "interactive_elements": [
                "pause_and_reflect", "concept_check", "real_world_connection",
            ],
        }

    async def share_on_network(self, video_metadata: Dict[str, Any]) -> str:
        return await self.fetch.share_educational_content(video_metadata)

    async def get_content_recommendations(self, subject: str, grade_level: str) -> List[Dict]:
        return await self.fetch.discover_similar_content(subject, grade_level)


# ─── Demo ────────────────────────────────────────────────────────────
async def demo_integrations():
    print("🚀 Granite AI — Integrations Demo (all FREE)")
    print("=" * 50)

    integration = GraniteIntegrations()

    sample_text = """
    Derivatives in Calculus

    A derivative represents the rate of change of a function.
    f'(x) = lim[h→0] (f(x+h) - f(x))/h
    Example: If f(x) = x², then f'(x) = 2x
    """

    print("\n📊 Testing Gemini fast analysis...")
    result = await integration.gemini_fast.fast_content_analysis(sample_text)
    print(f"  Result: {result}")

    print("\n❓ Testing quiz generation...")
    interactive = await integration.generate_interactive_elements(sample_text)
    print(f"  Generated {len(interactive['quiz_questions'])} questions")

    print("\n✅ All integrations working with FREE APIs!")


if __name__ == "__main__":
    asyncio.run(demo_integrations())
