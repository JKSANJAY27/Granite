"""
Granite - Crew Orchestration

Assembles agents and tasks into a CrewAI Crew and kicks it off.
Docs: https://docs.crewai.com/concepts/crews
"""

from crewai import Crew, Process
from agents import GraniteAgents
from tasks import GraniteTasks


class GraniteCrew:
    """
    Orchestrates the full Granite video-generation pipeline.

    Usage:
        result = GraniteCrew("Explain the Pythagorean theorem").run()
    """

    def __init__(self, topic: str):
        self.topic = topic

    def run(self):
        # ── Instantiate agents ────────────────────────────────────────
        agents = GraniteAgents()

        content_extractor = agents.content_extractor()
        lesson_planner    = agents.lesson_planner()
        manim_animator    = agents.manim_animator()
        narrator          = agents.narrator()
        video_composer    = agents.video_composer()
        quality_checker   = agents.quality_checker()

        # ── Create tasks with dependencies ────────────────────────────
        tasks = GraniteTasks()

        extraction = tasks.extraction_task(content_extractor, self.topic)
        planning   = tasks.planning_task(lesson_planner, extraction)
        animation  = tasks.animation_task(manim_animator, planning)
        narration  = tasks.narration_task(narrator, planning)
        composition = tasks.composition_task(video_composer, animation, narration)
        qa         = tasks.quality_check_task(quality_checker, composition)

        # ── Assemble and launch the crew ──────────────────────────────
        crew = Crew(
            agents=[
                content_extractor,
                lesson_planner,
                manim_animator,
                narrator,
                video_composer,
                quality_checker,
            ],
            tasks=[
                extraction,
                planning,
                animation,
                narration,
                composition,
                qa,
            ],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()
        return result


# ── Quick test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    topic = "Explain the Pythagorean theorem simply."
    print(f"Starting Granite pipeline for: {topic}\n")
    result = GraniteCrew(topic).run()
    print("\n" + "=" * 60)
    print("PIPELINE RESULT:")
    print("=" * 60)
    print(result)
