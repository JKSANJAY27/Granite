"""
Granite - Crew Orchestration

Assembles agents and tasks into a CrewAI Crew and kicks it off.
Includes retry logic for transient network errors (SSL, DNS, timeouts).

Docs: https://docs.crewai.com/concepts/crews
"""

import time
import sys
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

# ── Add local FFmpeg to PATH if present ──────────────────────────────
ffmpeg_bin = Path(__file__).parent / "ffmpeg_bin" / "bin"
if ffmpeg_bin.exists():
    os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + os.environ["PATH"]
    print(f"[Granite] Added local FFmpeg to PATH: {ffmpeg_bin}")

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
    # ── Added: catch Gemini 503 / UNAVAILABLE and empty LLM responses ──
    "503",
    "UNAVAILABLE",
    "ServerError",
    "high demand",
    "None or empty",
    "overloaded",
    "capacity",
    "rate limit",
    "quota",
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
    BASE_WAIT_SECONDS = 30  # doubles each retry: 30, 60, 120, 240...

    def __init__(self, topic: str, user_description: str = "", task_callback=None):
        self.topic = topic
        self.user_description = user_description
        self.task_callback = task_callback
        self.job_dir = self._create_job_dir(topic)

    @staticmethod
    def _create_job_dir(topic: str) -> Path:
        """Create a unique output directory for this pipeline run."""
        # Slugify topic: lowercase, keep only alnum/underscore, max 30 chars
        slug = re.sub(r'[^a-z0-9]+', '_', topic.lower()).strip('_')[:30]
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        uid = uuid.uuid4().hex[:4]
        job_name = f"{slug}_{ts}_{uid}"
        job_dir = Path("output_videos") / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

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

        extraction  = tasks.extraction_task(content_extractor, self.topic, self.user_description)
        planning    = tasks.planning_task(lesson_planner, extraction)
        animation   = tasks.animation_task(manim_animator, planning)
        narration   = tasks.narration_task(narrator, planning)
        composition = tasks.composition_task(video_composer, animation, narration)
        qa          = tasks.quality_check_task(quality_checker, composition)

        crew_kwargs = dict(
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
        if self.task_callback:
            crew_kwargs["task_callback"] = self.task_callback

        crew = Crew(**crew_kwargs)
        return crew

    def run(self):
        """Run the pipeline with automatic retries for transient errors."""
        # Set the job directory so all tools write to the same isolated folder
        os.environ["GRANITE_JOB_DIR"] = str(self.job_dir.resolve())
        print(f"📁 Job output directory: {self.job_dir.resolve()}")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(f"\n🚀 Pipeline attempt {attempt}/{self.MAX_RETRIES}")
                crew = self._build_crew()
                result = crew.kickoff()
                print(f"\n✅ Pipeline completed successfully on attempt {attempt}")
                print(f"📁 All outputs saved to: {self.job_dir.resolve()}")
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
