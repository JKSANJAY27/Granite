"""
Granite - Crew Orchestration

Assembles agents and tasks into a CrewAI Crew and kicks it off.
Includes retry logic for transient network errors (SSL, DNS, timeouts).

Docs: https://docs.crewai.com/concepts/crews
"""

import time
import sys
from crewai import Crew, Process
from agents import GraniteAgents
from tasks import GraniteTasks


# ── Transient error detection ─────────────────────────────────────────
TRANSIENT_ERROR_KEYWORDS = [
    "SSL",
    "UNEXPECTED_EOF",
    "getaddrinfo failed",
    "ConnectError",
    "ConnectionError",
    "ConnectionReset",
    "RESOURCE_EXHAUSTED",
    "429",
    "timeout",
    "TimeoutError",
    "Read timed out",
    "RemoteDisconnected",
    "EOFError",
    "BrokenPipeError",
]


def _is_transient_error(error: Exception) -> bool:
    """Check if an error is a transient network/quota issue worth retrying."""
    error_str = str(error)
    return any(keyword.lower() in error_str.lower() for keyword in TRANSIENT_ERROR_KEYWORDS)


def _get_retry_delay(error: Exception, default: float) -> float:
    """Extract retry delay from API error message, or use default."""
    import re
    error_str = str(error)

    # Check if this is a per-DAY quota (not worth short retries)
    if "PerDay" in error_str:
        print("   [!] Daily quota exhausted — need to wait for quota reset (midnight PT)")
        return max(default, 120)  # Wait at least 2 min, but realistically need to wait hours

    # Parse "Please retry in 18.521668968s" or similar
    match = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", error_str, re.IGNORECASE)
    if match:
        api_delay = float(match.group(1))
        return max(api_delay + 5, default)  # Add 5s buffer

    return default


class GraniteCrew:
    """
    Orchestrates the full Granite video-generation pipeline.

    Usage:
        result = GraniteCrew("Explain the Pythagorean theorem").run()
    """

    MAX_RETRIES = 5
    BASE_WAIT_SECONDS = 10  # doubles each retry: 10, 20, 40, 80, 160

    def __init__(self, topic: str):
        self.topic = topic

    def _build_crew(self):
        """Build agents, tasks, and the Crew object (fresh each attempt)."""
        agents = GraniteAgents()

        content_extractor = agents.content_extractor()
        lesson_planner    = agents.lesson_planner()
        manim_animator    = agents.manim_animator()
        narrator          = agents.narrator()
        video_composer    = agents.video_composer()
        quality_checker   = agents.quality_checker()

        tasks = GraniteTasks()

        extraction  = tasks.extraction_task(content_extractor, self.topic)
        planning    = tasks.planning_task(lesson_planner, extraction)
        animation   = tasks.animation_task(manim_animator, planning)
        narration   = tasks.narration_task(narrator, planning)
        composition = tasks.composition_task(video_composer, animation, narration)
        qa          = tasks.quality_check_task(quality_checker, composition)

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
        return crew

    def run(self):
        """Run the pipeline with automatic retries for transient errors."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(f"\n🚀 Pipeline attempt {attempt}/{self.MAX_RETRIES}")
                crew = self._build_crew()
                result = crew.kickoff()
                print(f"\n✅ Pipeline completed successfully on attempt {attempt}")
                return result

            except Exception as e:
                if _is_transient_error(e) and attempt < self.MAX_RETRIES:
                    default_wait = self.BASE_WAIT_SECONDS * (2 ** (attempt - 1))
                    wait = _get_retry_delay(e, default_wait)
                    print(f"\n   Transient error on attempt {attempt}: {type(e).__name__}")
                    print(f"   {str(e)[:200]}")
                    print(f"   Waiting {wait:.0f}s before retry...")
                    time.sleep(wait)
                else:
                    print(f"\n❌ Fatal error on attempt {attempt}: {e}")
                    raise


# ── Quick test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    topic = "Explain the Pythagorean theorem simply."
    print(f"Starting Granite pipeline for: {topic}\n")
    result = GraniteCrew(topic).run()
    print("\n" + "=" * 60)
    print("PIPELINE RESULT:")
    print("=" * 60)
    print(result)
