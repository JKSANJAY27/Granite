"""
Granite - Task Definitions

Each function returns a CrewAI Task object.
Tasks use the `context` parameter to express dependencies.
Docs: https://docs.crewai.com/concepts/tasks
"""

from crewai import Task


class GraniteTasks:
    """Creates all tasks for the Granite video-generation pipeline."""

    # ── 1. Content Extraction ──────────────────────────────────────────
    @staticmethod
    def extraction_task(agent, user_input: str) -> Task:
        return Task(
            description=(
                f"Analyse the following user input and extract the core educational content.\n\n"
                f"USER INPUT:\n{user_input}\n\n"
                "If the input is a file path, use the appropriate tool "
                "(pdf_content_extractor or image_content_extractor) to read it.\n"
                "If the input is a topic or free-form text, research and understand it.\n\n"
                "Produce a structured summary that includes:\n"
                "- Main topic\n"
                "- Key concepts and definitions\n"
                "- Important formulas or relationships\n"
                "- Suggested visual elements for animation"
            ),
            expected_output=(
                "A structured content summary with clearly labelled sections: "
                "Topic, Key Concepts, Formulas, Visual Suggestions."
            ),
            agent=agent,
        )

    # ── 2. Lesson Planning ─────────────────────────────────────────────
    @staticmethod
    def planning_task(agent, extraction_task: Task) -> Task:
        return Task(
            description=(
                "Using the extracted content from the previous task, create a "
                "detailed lesson plan for a short animated video (1-3 minutes).\n\n"
                "Structure the plan into 3-6 scenes. For EACH scene provide:\n"
                "1. **Scene Number & Title**\n"
                "2. **Narrator Script** — the exact words the narrator will say.\n"
                "3. **Visual Description** — a precise description of the Manim "
                "animation to show (shapes, transformations, text, equations, colours).\n"
                "4. **Duration** — approximate seconds for the scene.\n\n"
                "The style should be intuitive and minimalistic, inspired by "
                "3Blue1Brown.  Make sure concepts build on each other logically."
            ),
            expected_output=(
                "A scene-by-scene lesson plan in numbered format with "
                "Narrator Script and Visual Description for each scene."
            ),
            agent=agent,
            context=[extraction_task],
        )

    # ── 3. Manim Animation ─────────────────────────────────────────────
    @staticmethod
    def animation_task(agent, planning_task: Task) -> Task:
        return Task(
            description=(
                "Based on the lesson plan from the previous task, write complete, "
                "runnable Python code using the **Manim Community Edition** library.\n\n"
                "REQUIREMENTS:\n"
                "- The code MUST define a class named `GraniteScene` that inherits from `Scene`.\n"
                "- Include `from manim import *` at the top.\n"
                "- Implement the `construct(self)` method with all animations.\n"
                "- Use Manim objects like Text, MathTex, Circle, Arrow, FadeIn, "
                "Transform, Write, etc.\n"
                "- Keep animations clean and 3Blue1Brown-style.\n\n"
                "After writing the code, use the `manim_code_executor` tool to "
                "run it and generate the video.\n\n"
                "If the code fails, read the error, fix the code, and retry.\n\n"
                "Your FINAL ANSWER must be the file path of the generated .mp4 video."
            ),
            expected_output="The file path of the generated Manim animation video (.mp4).",
            agent=agent,
            context=[planning_task],
        )

    # ── 4. Narration (TTS) ─────────────────────────────────────────────
    @staticmethod
    def narration_task(agent, planning_task: Task) -> Task:
        return Task(
            description=(
                "Extract the complete narrator script from the lesson plan "
                "(combine all scene scripts into one continuous narration).\n\n"
                "Then use the `lmnt_text_to_speech` tool to convert the "
                "script into an audio file.\n\n"
                "Your FINAL ANSWER must be the file path of the generated .mp3 audio file."
            ),
            expected_output="The file path of the generated voiceover audio (.mp3).",
            agent=agent,
            context=[planning_task],
        )

    # ── 5. Video Composition ───────────────────────────────────────────
    @staticmethod
    def composition_task(agent, animation_task: Task, narration_task: Task) -> Task:
        return Task(
            description=(
                "Take the video file from the animation task and the audio "
                "file from the narration task.\n\n"
                "Use the `video_composer` tool to combine them into a single "
                "final video file.\n\n"
                "Your FINAL ANSWER must be the file path of the final composed video."
            ),
            expected_output="The file path of the final composed video (.mp4).",
            agent=agent,
            context=[animation_task, narration_task],
        )

    # ── 6. Quality Check ───────────────────────────────────────────────
    @staticmethod
    def quality_check_task(agent, composition_task: Task) -> Task:
        return Task(
            description=(
                "Use the `quality_checker` tool to verify the final video.\n\n"
                "Check that the file exists, has a reasonable size, duration, "
                "and resolution.\n\n"
                "Your FINAL ANSWER must include:\n"
                "- PASS or FAIL status\n"
                "- The quality report details\n"
                "- The final video file path"
            ),
            expected_output=(
                "A quality assurance report (PASS/FAIL) with technical details "
                "and the final video path."
            ),
            agent=agent,
            context=[composition_task],
        )
