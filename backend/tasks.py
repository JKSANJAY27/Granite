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
                "3Blue1Brown.  Make sure concepts build on each other logically.\n\n"
                "IMPORTANT: The Visual Description for each scene must be specific "
                "enough for a Manim developer to implement. Include:\n"
                "- Exact shapes and their colors\n"
                "- Mathematical expressions in LaTeX format\n"
                "- Transformations and transitions\n"
                "- Positioning (top, center, bottom-right, etc.)"
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

                "===================================================\n"
                "  MANDATORY CODE REQUIREMENTS\n"
                "===================================================\n\n"

                "1. Start with: from manim import *\n"
                "2. Define: class GraniteScene(Scene):\n"
                "3. Implement: def construct(self):\n"
                "4. Use ONLY Manim Community Edition API (not manimgl or old ManimCairo).\n\n"

                "===================================================\n"
                "  ⚠️  CRITICAL: NO LATEX AVAILABLE\n"
                "===================================================\n\n"

                "LaTeX is NOT installed on this system!\n"
                "You MUST NOT use MathTex() or Tex() — they WILL crash!\n\n"

                "Use ONLY Text() for ALL text and math rendering.\n"
                "For mathematical expressions, use Unicode symbols:\n"
                "  - Superscripts: x² y³ n⁴ (use ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁰ ⁿ)\n"
                "  - Subscripts:   x₁ y₂ n₃ (use ₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉)\n"
                "  - Fractions:    write as 'a/b' or 'dy/dx'\n"
                "  - Symbols:      → ≥ ≤ ≠ ≈ ∞ Δ Σ π θ α β γ ∫ √ ±\n\n"

                "Examples:\n"
                "  WRONG: MathTex(r'\\\\frac{dy}{dx}')  ← WILL CRASH\n"
                "  RIGHT: Text('dy/dx', font_size=36)\n\n"
                "  WRONG: MathTex(r'x^2 + y^2 = r^2') ← WILL CRASH\n"
                "  RIGHT: Text('x² + y² = r²', font_size=36)\n\n"
                "  WRONG: Tex(r'The derivative of $x^2$') ← WILL CRASH\n"
                "  RIGHT: Text('The derivative of x²', font_size=36)\n\n"

                "===================================================\n"
                "  MANIM QUICK REFERENCE\n"
                "===================================================\n\n"

                "SHAPES & OBJECTS:\n"
                "  Circle(), Square(), Rectangle(), Line(), Arrow(), Dot(),\n"
                "  Polygon(), Arc(), Annulus(), Triangle(), Star()\n\n"

                "TEXT (use ONLY Text, never MathTex or Tex):\n"
                "  Text('Hello', font_size=36)    — regular text\n"
                "  Text('x² + 1', font_size=36)   — math with Unicode\n"
                "  Text('dy/dx', font_size=36)     — fractions as text\n\n"

                "ANIMATIONS:\n"
                "  self.play(Write(text))               — write text\n"
                "  self.play(Create(shape))             — draw a shape\n"
                "  self.play(FadeIn(obj))               — fade in\n"
                "  self.play(FadeOut(obj))              — fade out\n"
                "  self.play(Transform(a, b))           — morph a into b\n"
                "  self.play(ReplacementTransform(a, b))— morph & replace\n"
                "  self.play(Indicate(obj))             — flash highlight\n"
                "  self.play(obj.animate.shift(UP))     — animate property\n"
                "  self.wait(2)                          — pause 2 seconds\n\n"

                "POSITIONING:\n"
                "  obj.to_edge(UP)         obj.to_corner(UL)\n"
                "  obj.shift(RIGHT * 2)    obj.move_to(ORIGIN)\n"
                "  obj.next_to(other, DOWN, buff=0.5)\n\n"

                "AXES & GRAPHS:\n"
                "  ax = Axes(x_range=[-3, 3], y_range=[-2, 2])\n"
                "  graph = ax.plot(lambda x: x**2, color=BLUE)\n"
                "  label = ax.get_x_axis_label(Text('x', font_size=24))\n"
                "  DO NOT use ax.get_graph() — use ax.plot() instead!\n\n"

                "GROUPING:\n"
                "  group = VGroup(obj1, obj2, obj3)\n"
                "  group.arrange(DOWN, buff=0.5)\n\n"

                "===================================================\n"
                "  COMMON PITFALLS -- AVOID THESE!\n"
                "===================================================\n\n"

                "WRONG: MathTex(anything)   -> RIGHT: Text('...') with Unicode\n"
                "WRONG: Tex(anything)       -> RIGHT: Text('...')\n"
                "WRONG: ShowCreation()      -> RIGHT: Create()\n"
                "WRONG: TextMobject()       -> RIGHT: Text()\n"
                "WRONG: TexMobject()        -> RIGHT: Text()\n"
                "WRONG: ax.get_graph()      -> RIGHT: ax.plot()\n"
                "WRONG: play(obj)           -> RIGHT: play(Create(obj)) or play(FadeIn(obj))\n"
                "WRONG: Overlapping text    -> RIGHT: Use .shift() or .next_to() for spacing\n\n"

                "===================================================\n"
                "  INSTRUCTIONS\n"
                "===================================================\n\n"

                "After writing the code, use the `manim_code_executor` tool to "
                "run it and generate the video.\n\n"
                "If the code fails, READ THE ERROR MESSAGE CAREFULLY:\n"
                "- If it mentions 'FileNotFoundError' or 'LaTeX': you used MathTex or Tex — "
                "replace ALL of them with Text() using Unicode symbols.\n"
                "- If it says 'AttributeError': you likely used a deprecated API.\n"
                "- If it says 'TypeError': check your function arguments.\n"
                "Fix the code and retry. You have up to 5 attempts.\n\n"
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
                "Clean up the script for natural speech:\n"
                "- Remove any markdown formatting or special characters\n"
                "- Spell out mathematical symbols (e.g., 'x squared' instead of 'x^2')\n"
                "- Add natural pauses with commas and periods\n"
                "- Keep the tone engaging and educational\n\n"
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
                "IMPORTANT: Extract the exact file paths from the previous tasks' "
                "results. The video_path should be an .mp4 file and the audio_path "
                "should be an .mp3 file.\n\n"
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
