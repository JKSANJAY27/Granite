"""
Granite - Agent Definitions

Uses CrewAI's native LLM class with Gemini provider.
Docs: https://docs.crewai.com/concepts/agents
      https://docs.crewai.com/concepts/llms
"""

import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools import (
    PDFContentExtractor,
    ImageContentExtractor,
    ManimCodeExecutor,
    LMNTTextToSpeech,
    VideoComposerTool,
    QualityCheckerTool,
)

# Force .env to override any system-level env vars
load_dotenv(override=True)

# Debug: Print which key is being used
_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if _key:
    print(f"[Granite] Using API key ending in: ...{_key[-8:]}")
else:
    print("[Granite] WARNING: No GEMINI_API_KEY or GOOGLE_API_KEY found!")

# ─── Configure Gemini LLM via CrewAI's native LLM class ───────────────
# CrewAI uses the google-genai SDK under the hood for "gemini/" models.
# Requires GEMINI_API_KEY or GOOGLE_API_KEY in .env
gemini_llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.5,
    max_tokens=4096,
)


# ─── Agent Factory ─────────────────────────────────────────────────────
class GraniteAgents:
    """Creates and returns all agents used in the Granite pipeline."""

    def content_extractor(self) -> Agent:
        return Agent(
            role="Content Extraction Specialist",
            goal=(
                "Extract and summarise all meaningful text, key concepts, "
                "definitions, and visual descriptions from the provided "
                "educational material (PDF, image, or raw text)."
            ),
            backstory=(
                "You are an expert at reading educational documents and "
                "distilling them into clear, structured content summaries "
                "that downstream agents can use to plan a lesson."
            ),
            tools=[PDFContentExtractor(), ImageContentExtractor()],
            llm=gemini_llm,
            verbose=True,
            allow_delegation=False,
        )

    def lesson_planner(self) -> Agent:
        return Agent(
            role="Educational Lesson Planner",
            goal=(
                "Create a detailed, scene-by-scene lesson plan for a short "
                "(1-3 minute) animated educational video in the style of "
                "3Blue1Brown.  For each scene provide: (1) the narrator "
                "script, (2) a precise visual description for the animator."
            ),
            backstory=(
                "You are a seasoned educator who excels at breaking complex "
                "topics into simple, intuitive explanations.  You know how "
                "to order concepts so each builds on the last, and you "
                "always suggest clear, minimalistic animations."
            ),
            tools=[],  # pure reasoning agent
            llm=gemini_llm,
            verbose=True,
            allow_delegation=False,
        )

    def manim_animator(self) -> Agent:
        return Agent(
            role="Manim Animation Developer",
            goal=(
                "Write complete, runnable Python code using the Manim "
                "Community library that visualises the lesson plan.  "
                "The code MUST define a class called 'GraniteScene' "
                "inheriting from Scene."
            ),
            backstory=(
                "You are a Python expert with deep knowledge of the Manim "
                "library.  You write clean, error-free Manim code that "
                "produces beautiful, 3Blue1Brown-style animations."
            ),
            tools=[ManimCodeExecutor()],
            llm=gemini_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5,  # allow retries if code fails
        )

    def narrator(self) -> Agent:
        return Agent(
            role="Voiceover Narrator",
            goal=(
                "Generate a high-quality voiceover audio file from the "
                "narration script using the LMNT text-to-speech tool."
            ),
            backstory=(
                "You are an AI voice artist who delivers clear, engaging, "
                "and educational narration that keeps learners interested."
            ),
            tools=[LMNTTextToSpeech()],
            llm=gemini_llm,
            verbose=True,
            allow_delegation=False,
        )

    def video_composer(self) -> Agent:
        return Agent(
            role="Video Production Specialist",
            goal=(
                "Combine the animation video and the voiceover audio into "
                "a single, synchronised, polished MP4 video file."
            ),
            backstory=(
                "You are a skilled video editor who ensures perfect "
                "audio-video synchronisation and smooth transitions."
            ),
            tools=[VideoComposerTool()],
            llm=gemini_llm,
            verbose=True,
            allow_delegation=False,
        )

    def quality_checker(self) -> Agent:
        return Agent(
            role="Quality Assurance Specialist",
            goal=(
                "Verify that the final video exists, plays correctly, and "
                "meets basic technical standards (resolution, duration, "
                "file size).  Report a PASS or FAIL with details."
            ),
            backstory=(
                "You are a meticulous QA engineer who checks every detail "
                "before a video is shipped to learners."
            ),
            tools=[QualityCheckerTool()],
            llm=gemini_llm,
            verbose=True,
            allow_delegation=False,
        )
