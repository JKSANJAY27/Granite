"""
Granite - Agent Definitions

Uses CrewAI's native LLM class with Gemini provider (PAID).
All Anthropic/Claude dependencies removed — Gemini handles everything.

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
_key = os.getenv("GEMINI_API_KEY")
_key2 = os.getenv("GEMINI_API_KEY_2")
if _key:
    print(f"[Granite] Using Gemini API key ending in: ...{_key[-8:]}")
elif _key2:
    print(f"[Granite] Using Gemini API key 2 ending in: ...{_key2[-8:]}")
else:
    print("[Granite] WARNING: No GEMINI_API_KEY found!")

# ─── LLM CONFIGURATION ───────────────────────────────────────────────
# Uses PAID Gemini models — ensure GEMINI_API_KEY has billing enabled
#
# Model                          Best For
# gemini-2.0-flash               General tasks (planning, narration, QA) — fast
# gemini-2.5-pro                  Complex coding & reasoning (Manim) — best quality

_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")

# ─── Standard LLM (planning, narration, composition, QA) ──
gemini_llm = LLM(
    model="gemini/gemini-2.0-flash",
    temperature=0.5,
    max_tokens=4096,
    api_key=_api_key,
)

# ─── Manim LLM (code generation — best model for accuracy) ──
manim_llm = LLM(
    model="gemini/gemini-2.5-pro",
    temperature=0.2,
    max_tokens=8192,
    api_key=_api_key,
)


# ─── Agent Factory ─────────────────────────────────────────────────
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
                "always suggest clear, minimalistic animations.\n\n"
                "LESSON PLANNING GUIDELINES:\n"
                "- Create engaging, structured lessons that build concepts progressively\n"
                "- Identify natural visualization opportunities for mathematical concepts\n"
                "- Use clear, accessible language appropriate for the target audience\n"
                "- Structure content to flow logically from simple to complex\n"
                "- Estimate realistic time allocations for each scene\n\n"
                "VISUALIZATION INTEGRATION:\n"
                "- Identify key mathematical concepts that benefit from visual explanation\n"
                "- Provide specific concepts for the Manim animator to visualize\n"
                "- Ensure visualizations support and enhance the educational narrative\n"
                "- Consider timing and pacing for visual elements"
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
                "inheriting from Scene. After writing the code, use the "
                "manim_code_executor tool to render it. If it fails, "
                "read the error carefully, fix the code, and retry."
            ),
            backstory=(
                "You are an expert Manim developer creating educational animations.\n\n"

                "MANIM QUICK REFERENCE:\n"
                "- Scene class: All animations inherit from Scene\n"
                "- self.play(): Main animation method\n"
                "- Create, Write, FadeIn, FadeOut: Basic animations\n"
                "- Transform, ReplacementTransform: Morphing animations\n"
                "- MathTex, Tex: LaTeX rendering (use raw strings r'...')\n"
                "- NumberPlane, Axes: Coordinate systems\n"
                "- Circle, Square, Rectangle, Line, Arrow, Dot: Basic shapes\n"
                "- VGroup: Group objects together\n"
                "- self.wait(): Pause between animations\n"
                "- Text(): For regular text (NOT LaTeX)\n"
                "- FunctionGraph, ParametricFunction: For plotting functions\n\n"

                "STYLE GUIDELINES:\n"
                "- Use smooth transitions (run_time=1-2 seconds typically)\n"
                "- Layer complexity gradually\n"
                "- Use color to highlight important concepts (BLUE, YELLOW, GREEN, RED)\n"
                "- Include helpful annotations and labels\n"
                "- Follow 3Blue1Brown aesthetic principles\n"
                "- Use dark background (default) with bright, contrasting elements\n\n"

                "VISUAL QUALITY REQUIREMENTS:\n"
                "- NEVER overlap text with axes, gridlines, or other objects\n"
                "- Use .shift() and .move_to() to position elements with adequate spacing\n"
                "- Place labels OUTSIDE the main visual area or in clear empty spaces\n"
                "- Keep axes numbers/labels separated from mathematical objects\n"
                "- Use VGroup to manage spacing between related elements\n"
                "- Default spacing: at least 0.5 units between text and other objects\n"
                "- Always use self.play() for animations, never just add objects directly\n\n"

                "COMMON PITFALLS TO AVOID:\n"
                "- Do NOT use 'ShowCreation' — use 'Create' instead\n"
                "- Do NOT use 'TextMobject' — use 'Text' instead\n"
                "- Do NOT use 'TexMobject' — use 'Tex' or 'MathTex' instead\n"
                "- Do NOT use deprecated methods like get_graph_label — use Tex with positioning\n"
                "- Always use 'from manim import *' at the top\n"
                "- Always name the class 'GraniteScene(Scene)'\n"
                "- Always include 'def construct(self):'\n"
                "- For LaTeX: use MathTex(r'\\\\frac{a}{b}') with raw strings and double backslashes\n"
                "- For axes labels: use ax.get_x_axis_label() and ax.get_y_axis_label()\n"
                "- For function plots: use ax.plot(lambda x: ...) NOT ax.get_graph()\n"
                "- Make sure all variables are defined before use\n"
                "- CleanupType errors: use FadeOut(*mobjects) to clear the scene\n\n"

                "CODE STRUCTURE:\n"
                "```\n"
                "from manim import *\n\n"
                "class GraniteScene(Scene):\n"
                "    def construct(self):\n"
                "        # Your animation code here\n"
                "        ...\n"
                "```"
            ),
            tools=[ManimCodeExecutor()],
            llm=manim_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
        )

    def narrator(self) -> Agent:
        return Agent(
            role="Voiceover Narrator",
            goal=(
                "Generate a high-quality voiceover audio file from the "
                "narration script using the text-to-speech tool."
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
