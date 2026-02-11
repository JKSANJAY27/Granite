"""
Audio Narration Agent for Educational Videos
Uses edge-tts (free, high-quality Microsoft Edge voices) as primary TTS.
Falls back to gTTS (Google Text-to-Speech, also free).

Replaces the original LMNT-based narrator (paid API).
"""

import os
import asyncio
import struct
from typing import Dict, List, Any, Optional
from pathlib import Path

from crewai import Agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ─── Optional TTS imports ────────────────────────────────────────────
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    print("⚠️  edge-tts not installed — install with: pip install edge-tts")

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    print("⚠️  gTTS not installed — install with: pip install gTTS")


# ─── Pydantic models ────────────────────────────────────────────────
class VoiceConfig(BaseModel):
    """Voice configuration for TTS."""
    voice_id: str = Field(default="en-US-AriaNeural", description="Edge-TTS voice name")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    emotion: Optional[str] = Field(default=None, description="Emotion/style modifier")
    clarity_boost: bool = Field(default=True, description="Enhance clarity for education")
    pause_at_punctuation: bool = Field(default=True, description="Natural pauses")
    emphasis_keywords: List[str] = Field(default_factory=list)


class AudioSegment(BaseModel):
    """Individual audio segment with timing."""
    text: str = Field(description="Text for this segment")
    start_time: float = Field(description="Start time in seconds")
    duration: float = Field(description="Duration in seconds")
    audio_data: Optional[bytes] = Field(default=None, description="Audio data")
    sync_event: Optional[str] = Field(default=None, description="Associated visual event")

    class Config:
        arbitrary_types_allowed = True


class EnhancedAudioNarration(BaseModel):
    """Enhanced audio narration output."""
    audio_path: str = Field(description="Path to generated audio file")
    duration: float = Field(description="Total duration in seconds")
    transcript: str = Field(description="Full narration transcript")
    segments: List[AudioSegment] = Field(default_factory=list)
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)
    sync_points: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


# ─── Educational voice presets (Edge-TTS voices) ─────────────────────
VOICE_PRESETS = {
    "math_teacher": {
        "voice_id": "en-US-AriaNeural",
        "speed": 0.95,
        "clarity_boost": True,
    },
    "science_explainer": {
        "voice_id": "en-US-GuyNeural",
        "speed": 1.0,
        "clarity_boost": True,
    },
    "friendly_tutor": {
        "voice_id": "en-US-JennyNeural",
        "speed": 1.05,
        "emotion": "cheerful",
    },
    "professor": {
        "voice_id": "en-US-DavisNeural",
        "speed": 0.9,
        "emotion": "calm",
    },
}


class NarratorAgent(Agent):
    """
    Audio narration agent using **edge-tts** (free, high-quality).
    Optimised for educational content with proper pacing and sync points.
    """

    def __init__(self, **kwargs):
        default_config = {
            "role": "Audio Narration Specialist",
            "goal": "Create crystal-clear, engaging educational narration with perfect timing",
            "backstory": (
                "You are an expert in educational audio production. "
                "You create narrations that enhance learning through optimal pacing, "
                "emphasis, and synchronisation with visual content."
            ),
            "verbose": True,
            "allow_delegation": False,
        }
        config = {**default_config, **kwargs}
        super().__init__(**config)

    # ─── Main API ────────────────────────────────────────────────────
    async def generate_narration(
        self,
        lesson_plan,
        animations,
        voice_preset: str = "math_teacher",
    ) -> EnhancedAudioNarration:
        """Generate narration for an educational lesson."""

        voice_config = VoiceConfig(**VOICE_PRESETS.get(voice_preset, VOICE_PRESETS["math_teacher"]))

        # Build transcript & segments from lesson plan
        transcript, segments = self._create_educational_transcript(lesson_plan, animations)

        # Synthesise full transcript to a single audio file
        audio_path = await self._synthesise_audio(transcript, voice_config)

        # Estimate duration (~150 words/minute for educational content)
        word_count = len(transcript.split())
        estimated_duration = (word_count / 150) * 60  # seconds

        # Build sync points
        sync_points = self._create_sync_points(segments, animations)

        return EnhancedAudioNarration(
            audio_path=audio_path,
            duration=estimated_duration,
            transcript=transcript,
            segments=segments,
            voice_config=voice_config,
            sync_points=sync_points,
            metadata={
                "voice_preset": voice_preset,
                "generation_method": "edge-tts" if HAS_EDGE_TTS else ("gTTS" if HAS_GTTS else "silent"),
                "quality": "high" if HAS_EDGE_TTS else "standard",
                "word_count": word_count,
            },
        )

    # ─── Transcript builder ──────────────────────────────────────────
    def _create_educational_transcript(self, lesson_plan, animations):
        """Create a paced educational transcript from the lesson plan."""
        transcript = f"Welcome to our lesson on {lesson_plan.title}. "
        transcript += "Let's explore this fascinating topic together.\n\n"

        segments: List[AudioSegment] = []
        current_time = 0.0

        # Intro
        intro_text = f"Today, we'll learn about {lesson_plan.title}. "
        if hasattr(lesson_plan, "learning_objectives") and lesson_plan.learning_objectives:
            intro_text += f"By the end of this lesson, you'll understand {lesson_plan.learning_objectives[0]}. "

        segments.append(AudioSegment(text=intro_text, start_time=current_time, duration=5.0, sync_event="intro_animation"))
        current_time += 5.0

        # Sections
        for i, section in enumerate(lesson_plan.sections):
            # Transition pause
            segments.append(AudioSegment(text="", start_time=current_time, duration=1.0, sync_event=f"section_{i}_transition"))
            current_time += 1.0

            section_intro = f"\n\nNow, let's explore {section.title}. "
            content = self._add_educational_emphasis(section.content)

            if hasattr(section, "visualization_concept") and section.visualization_concept:
                viz_narration = f"Watch carefully as we visualise {section.visualization_concept}. "
                full_text = section_intro + content + " " + viz_narration
            else:
                full_text = section_intro + content

            est_dur = max(len(full_text.split()) * 0.4, 3.0)
            segments.append(AudioSegment(text=full_text, start_time=current_time, duration=est_dur, sync_event=f"section_{i}_content"))
            current_time += est_dur

            transcript += full_text

        # Conclusion
        conclusion = "\n\nLet's recap what we've learned today. "
        if hasattr(lesson_plan, "learning_objectives"):
            for obj in lesson_plan.learning_objectives[:2]:
                conclusion += f"{obj}. "
        conclusion += "Thank you for watching!"

        segments.append(AudioSegment(text=conclusion, start_time=current_time, duration=5.0, sync_event="conclusion"))
        transcript += conclusion

        return transcript, segments

    def _add_educational_emphasis(self, content: str) -> str:
        """Add pauses for educational clarity."""
        content = content.replace(". ", ".  ")   # slight pause
        content = content.replace("? ", "?  ")
        content = content.replace(": ", ":  ")
        return content

    # ─── TTS synthesis ───────────────────────────────────────────────
    async def _synthesise_audio(self, text: str, voice_config: VoiceConfig) -> str:
        """Synthesise speech using LMNT (primary) or edge-tts/gTTS (fallback)."""
        output_dir = Path("output_videos")
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / "narration.mp3")

        # Clean text for TTS
        clean_text = text.replace("[pause]", ". ").replace("*", "").strip()
        if not clean_text:
            clean_text = "No narration text was generated."

        # Method 1: LMNT (Primary - Paid)
        lmnt_key = os.getenv("LMNT_API_KEY")
        if lmnt_key:
            try:
                from lmnt.api import Speech
                async with Speech(lmnt_key) as speech:
                    synthesis = await speech.synthesize(
                        clean_text,
                        voice="lily",  # Default LMNT voice
                        format="mp3",
                    )
                    with open(output_path, "wb") as f:
                        f.write(synthesis["audio"])
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    print(f"✅ Audio generated with LMNT: {output_path}")
                    return output_path
            except Exception as e:
                print(f"⚠️  LMNT failed: {e}")

        # Method 2: edge-tts (best quality, free)
        if HAS_EDGE_TTS:
            try:
                # Build rate string  (e.g. "+10%" or "-5%")
                rate_pct = int((voice_config.speed - 1.0) * 100)
                rate_str = f"{rate_pct:+d}%"

                communicate = edge_tts.Communicate(
                    text=clean_text,
                    voice=voice_config.voice_id,
                    rate=rate_str,
                )
                await communicate.save(output_path)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    print(f"✅ Audio generated with edge-tts: {output_path}")
                    return output_path
            except Exception as e:
                print(f"⚠️  edge-tts failed: {e}")

        # Method 3: gTTS (fallback, free)
        if HAS_GTTS:
            try:
                tts = gTTS(text=clean_text, lang="en", slow=voice_config.speed < 0.9)
                tts.save(output_path)
                if os.path.exists(output_path):
                    print(f"✅ Audio generated with gTTS: {output_path}")
                    return output_path
            except Exception as e:
                print(f"⚠️  gTTS failed: {e}")

        # Method 4: generate silent WAV as placeholder
        output_path_wav = str(output_dir / "narration.wav")
        self._generate_silence_file(output_path_wav, duration=30.0)
        print(f"⚠️  Generated silent placeholder: {output_path_wav}")
        return output_path_wav

    def _generate_silence_file(self, path: str, duration: float = 30.0):
        """Write a silent WAV file as ultimate fallback."""
        sample_rate = 24000
        num_samples = int(duration * sample_rate)
        with open(path, "wb") as f:
            # WAV header
            data_size = num_samples * 2
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + data_size))
            f.write(b"WAVEfmt ")
            f.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            f.write(b"\x00\x00" * num_samples)

    # ─── Sync points ─────────────────────────────────────────────────
    def _create_sync_points(self, segments: List[AudioSegment], animations) -> List[Dict[str, Any]]:
        sync_points = []
        for seg in segments:
            if seg.sync_event:
                sync_points.append({
                    "time": seg.start_time,
                    "duration": seg.duration,
                    "event": seg.sync_event,
                    "type": "audio_visual_sync",
                })

        for i, anim in enumerate(animations):
            if hasattr(anim, "sync_points") and anim.sync_points:
                for sp in anim.sync_points:
                    sync_points.append({
                        "time": sp.get("time", 0),
                        "event": f"animation_{i}_{sp.get('event', 'unknown')}",
                        "type": "animation_event",
                    })

        sync_points.sort(key=lambda x: x["time"])
        return sync_points


# ─── Standalone quick test ───────────────────────────────────────────
async def test_narrator():
    """Quick smoke test for the narrator."""
    from pydantic import BaseModel as BM
    from typing import List as L

    class Section(BM):
        title: str = "What is a Derivative?"
        content: str = "A derivative represents the rate of change of a function."
        visualization_concept: str = "tangent line to curve"
        duration_estimate: float = 5.0

    class FakePlan(BM):
        title: str = "Introduction to Derivatives"
        learning_objectives: L[str] = ["Understand rate of change", "Calculate basic derivatives"]
        sections: L[Section] = [Section()]

    narrator = NarratorAgent()
    narration = await narrator.generate_narration(FakePlan(), [], voice_preset="math_teacher")
    print(f"Generated narration: {narration.audio_path}")
    print(f"Estimated duration: {narration.duration:.1f}s")
    print(f"Method: {narration.metadata.get('generation_method')}")


if __name__ == "__main__":
    asyncio.run(test_narrator())
