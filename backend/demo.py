"""
Granite — Demo Script

Demonstrates the educational video generation pipeline
using Gemini (free) for all AI features.
"""

import asyncio
import os
from dotenv import load_dotenv

from granite_unified_agent import (
    ContentExtractorAgent,
    LessonPlannerAgent,
    GraniteVideoGenerator,
)

load_dotenv()


async def demo_content_analysis():
    """Demo: Analyse sample educational content."""
    print("🎓 Demo: Content Analysis with Gemini")
    print("=" * 50)

    extractor = ContentExtractorAgent()

    sample_text = (
        "Derivatives in Calculus\n\n"
        "A derivative represents the rate of change of a function with respect to "
        "its variable. For a function f(x), the derivative f'(x) tells us how "
        "quickly f(x) is changing at any point x.\n\n"
        "The formal definition uses limits:\n"
        "f'(x) = lim[h→0] (f(x+h) - f(x))/h\n\n"
        "Example: If f(x) = x², then f'(x) = 2x\n"
        "This means the slope of x² at any point x is 2x."
    )

    content = await extractor.analyze_content(sample_text)

    print(f"📚 Subject: {content.subject_area}")
    print(f"📊 Difficulty: {content.difficulty_level}")
    print(f"🧠 Concepts: {content.concepts}")
    print(f"🎬 Visual elements: {content.visual_elements}")
    print()


async def demo_lesson_planning():
    """Demo: Create a lesson plan from analysed content."""
    print("\n🎓 Demo: Lesson Planning with Gemini")
    print("=" * 50)

    extractor = ContentExtractorAgent()
    planner = LessonPlannerAgent()

    sample_text = (
        "Linear regression creates a line of best fit through all data points. "
        "The equation is y = mx + b where m is the slope and b is the intercept. "
        "The slope represents the rate of change."
    )

    content = await extractor.analyze_content(sample_text)
    lesson = await planner.create_lesson_plan(
        content, duration_minutes=5, audience="High School"
    )

    print(f"📚 Lesson: {lesson.title}")
    print(f"⏱️  Duration: {lesson.total_duration} minutes")
    print(f"📖 Sections: {len(lesson.sections)}")
    print()

    for i, section in enumerate(lesson.sections):
        print(f"  📝 Section {i + 1}: {section.title}")
        print(f"     Content: {section.content[:100]}...")
        if section.visualization_concept:
            print(f"     🎬 Visualisation: {section.visualization_concept}")
        print()

    if lesson.learning_objectives:
        print("🎯 Learning Objectives:")
        for obj in lesson.learning_objectives:
            print(f"   • {obj}")

    if lesson.assessment_questions:
        print("\n❓ Assessment Questions:")
        for q in lesson.assessment_questions[:3]:
            print(f"   • {q}")


async def demo_full_pipeline():
    """Demo: Full pipeline (if a sample PDF exists)."""
    print("\n🎓 Demo: Full Pipeline")
    print("=" * 50)

    sample_pdf = os.path.abspath("../sample_calculus.pdf")
    if not os.path.exists(sample_pdf):
        print(f"⚠️  No sample PDF found at {sample_pdf}")
        print("   Provide a PDF to test the full pipeline.")
        return

    generator = GraniteVideoGenerator()
    video = await generator.generate_video(
        sample_pdf,
        target_audience="High School",
        duration_minutes=3,
        voice_preset="math_teacher",
    )

    print(f"🎬 Video path: {video.video_path}")
    print(f"⏱️  Duration: {video.duration:.1f}s")
    print(f"📊 Quality: {video.metadata.get('quality_report', {}).get('educational_effectiveness', 'N/A')}")


async def main():
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")
    if not gemini_key:
        print("❌ ERROR: Please set GEMINI_API_KEY in .env file")
        return

    try:
        await demo_content_analysis()
        await demo_lesson_planning()
        await demo_full_pipeline()

        print("\n🎉 Demo completed successfully!")
        print("All features running on FREE APIs (Gemini + edge-tts).")

    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
