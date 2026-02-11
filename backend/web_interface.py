"""
Granite - Web Interface
Gradio-based UI for the educational video generation system.

ALL paid APIs replaced with free alternatives:
  - Gemini (free) for LLM + Vision
  - edge-tts / gTTS for TTS
"""

import gradio as gr
import asyncio
import os
from typing import Optional
from pathlib import Path
from datetime import datetime

from granite_unified_agent import GraniteVideoGenerator
from simple_document_processor import SimpleDocumentProcessor
from audio_narrator import VoiceConfig

from dotenv import load_dotenv

load_dotenv()


class GraniteAgentInterface:
    """Web interface for the educational video generation system."""

    def __init__(self):
        self.video_generator = GraniteVideoGenerator()
        self.simple_processor = SimpleDocumentProcessor()

        self.voice_options = {
            "Math Teacher": "math_teacher",
            "Science Explainer": "science_explainer",
            "Friendly Tutor": "friendly_tutor",
            "Professor": "professor",
        }

        self.subject_options = [
            "Mathematics", "Physics", "Chemistry", "Biology",
            "Computer Science", "Statistics", "Engineering", "Other",
        ]

        self.grade_options = [
            "Elementary School", "Middle School", "High School",
            "College", "Graduate Level",
        ]

    def create_interface(self):
        """Build the Gradio Blocks interface."""

        with gr.Blocks(
            title="Granite AI — Educational Video Generator",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container { max-width: 1200px !important; }
            .header { text-align: center; margin-bottom: 30px; }
            .demo-section {
                border: 2px dashed #ccc; padding: 20px;
                margin: 10px 0; border-radius: 10px;
            }
            """,
        ) as interface:

            has_gemini = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2"))

            try:
                import edge_tts
                has_tts = True
            except ImportError:
                try:
                    from gtts import gTTS
                    has_tts = True
                except ImportError:
                    has_tts = False

            if has_gemini and has_tts:
                mode_badge = "🎬 **FULL PIPELINE MODE** — Generating videos with Manim + Gemini AI + TTS"
                mode_color = "#4caf50"
            elif has_gemini:
                mode_badge = "🎯 **PARTIAL MODE** — Gemini AI available, TTS fallback (install edge-tts for best audio)"
                mode_color = "#ff9800"
            else:
                mode_badge = "🎯 **DEMO MODE** — Add GEMINI_API_KEY for full functionality"
                mode_color = "#ff9800"

            # ── Header ───────────────────────────────────────────────
            gr.Markdown(
                f"""
                # 🎓 Granite AI — Educational Video Generator
                ### Transform any educational document into engaging videos with AI
                *Powered by CrewAI, Manim, Gemini Vision, edge-tts, and moviepy*

                <div style="background-color: {mode_color}; color: white; padding: 10px;
                     border-radius: 5px; margin: 10px 0; text-align: center;">
                {mode_badge}
                </div>
                """,
                elem_classes=["header"],
            )

            # ── Tab: Generate Video ──────────────────────────────────
            with gr.Tab("📁 Generate Video"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("## 📤 Upload Educational Content")
                        file_input = gr.File(
                            label="Upload PDF or Image",
                            file_types=[".pdf", ".png", ".jpg", ".jpeg"],
                            file_count="single",
                        )

                        gr.Markdown("## ⚙️ Configuration")
                        voice_choice = gr.Dropdown(
                            choices=list(self.voice_options.keys()),
                            value="Math Teacher",
                            label="Narrator Voice",
                        )
                        subject_choice = gr.Dropdown(
                            choices=self.subject_options,
                            value="Mathematics",
                            label="Subject Area",
                        )
                        grade_choice = gr.Dropdown(
                            choices=self.grade_options,
                            value="High School",
                            label="Grade Level",
                        )
                        duration_slider = gr.Slider(
                            minimum=0.5, maximum=5, value=2, step=0.5,
                            label="Target Duration (minutes)",
                        )

                        with gr.Accordion("♿ Accessibility Features", open=False):
                            include_captions = gr.Checkbox(value=True, label="Include Captions/Subtitles")
                            include_transcript = gr.Checkbox(value=True, label="Generate Transcript")
                            slow_narration = gr.Checkbox(value=False, label="Slower Narration Speed")

                        generate_btn = gr.Button(
                            "🎬 Generate Educational Video",
                            variant="primary", size="lg",
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("## 📊 Processing Status")
                        status_text = gr.Textbox(
                            label="Current Status",
                            value="Ready to generate…",
                            interactive=False, lines=2,
                        )

                        gr.Markdown("## 🎬 Generated Video")
                        video_output = gr.Video(label="Educational Video", height=400)

                        with gr.Row():
                            video_download = gr.File(label="Download Video", visible=False)
                            transcript_download = gr.File(label="Download Transcript", visible=False)

                        metadata_json = gr.JSON(label="Video Metadata", visible=False)

            # ── Tab: Demo Examples ───────────────────────────────────
            with gr.Tab("📊 Demo Examples"):
                gr.Markdown("## 🎯 Try These Quick Demo Examples")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown(
                            """
                            ### Sample Educational Content

                            **Mathematics — Calculus**
                            - Derivatives and rate of change
                            - Integration techniques

                            **Physics — Motion**
                            - Newton's laws of motion
                            - Kinematic equations

                            **Chemistry — Molecular Structure**
                            - Chemical bonding
                            - Molecular geometry
                            """,
                            elem_classes=["demo-section"],
                        )
                        demo_btn1 = gr.Button("📐 Try Calculus Demo")
                        demo_btn2 = gr.Button("⚛️ Try Physics Demo")
                        demo_btn3 = gr.Button("🧪 Try Chemistry Demo")
                    with gr.Column():
                        demo_video = gr.Video(label="Demo Video Preview", height=400)

            # ── Tab: About ───────────────────────────────────────────
            with gr.Tab("ℹ️ About"):
                gr.Markdown(
                    """
                    ## About Granite AI

                    Granite AI transforms static educational content into engaging,
                    accessible videos using cutting-edge AI — **entirely with free APIs**.

                    ### 🔧 Technology Stack
                    | Component | Technology | Cost |
                    |---|---|---|
                    | Multi-Agent Orchestration | CrewAI | Free |
                    | Animation Engine | Manim Community | Free |
                    | LLM + Vision | Google Gemini | Free tier |
                    | Text-to-Speech | edge-tts / gTTS | Free |
                    | Video Composition | moviepy + ffmpeg | Free |
                    | Content Extraction | PyMuPDF + pytesseract | Free |

                    ### ✨ Key Features
                    - 📄 PDF & Image Processing (OCR + AI Vision)
                    - 🎬 Automated Manim Animations
                    - 🎙️ Professional Narration (edge-tts neural voices)
                    - ♿ Accessibility (captions, transcripts)
                    - 📱 Responsive Web Interface
                    """
                )

            # ── Event handlers ───────────────────────────────────────
            generate_btn.click(
                fn=self.generate_video,
                inputs=[
                    file_input, voice_choice, subject_choice, grade_choice,
                    duration_slider, include_captions, include_transcript, slow_narration,
                ],
                outputs=[
                    video_output, status_text, metadata_json,
                    video_download, transcript_download,
                ],
                show_progress=True,
            )

            demo_btn1.click(fn=lambda: self.load_demo("calculus"), outputs=[demo_video])
            demo_btn2.click(fn=lambda: self.load_demo("physics"), outputs=[demo_video])
            demo_btn3.click(fn=lambda: self.load_demo("chemistry"), outputs=[demo_video])

        return interface

    # ── Video generation handler ─────────────────────────────────────
    def generate_video(
        self, file_input, voice_choice, subject_choice, grade_choice,
        duration_minutes, include_captions, include_transcript, slow_narration,
    ):
        if not file_input:
            return "", "❌ Please upload a file first!", {}, None, None

        has_gemini = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2"))
        demo_mode = not has_gemini

        if demo_mode:
            return self._simulate_video_generation(
                file_input, voice_choice, subject_choice, grade_choice,
                duration_minutes, include_captions, include_transcript, slow_narration,
            )

        try:
            result = asyncio.run(
                self._async_generate_video(
                    file_input, voice_choice, subject_choice, grade_choice,
                    duration_minutes, include_captions, include_transcript, slow_narration,
                )
            )

            if result["success"]:
                video_file = result.get("video_path")
                if video_file and not os.path.exists(video_file):
                    video_file = None

                metadata = {
                    "mode": "Full Video Generation",
                    "duration": f"{result['duration']:.1f} seconds",
                    "resolution": "1920×1080",
                    "voice_used": voice_choice,
                    "subject": subject_choice,
                    "grade_level": grade_choice,
                    "pipeline": "CrewAI + Manim + Gemini + edge-tts",
                }

                return (
                    video_file,
                    "✅ Educational video generated successfully!",
                    metadata,
                    gr.File(video_file, visible=True) if video_file else None,
                    None,
                )
            else:
                return None, f"❌ Error: {result['error']}", {}, None, None

        except Exception as e:
            return None, f"❌ Video generation failed: {e}", {}, None, None

    async def _async_generate_video(
        self, file_input, voice_choice, subject_choice, grade_choice,
        duration_minutes, include_captions, include_transcript, slow_narration,
    ):
        try:
            voice_preset = self.voice_options.get(voice_choice, "math_teacher")
            options = {
                "target_audience": grade_choice,
                "duration_minutes": duration_minutes,
                "voice_preset": voice_preset,
                "subject": subject_choice,
            }
            final_video = await self.video_generator.generate_video(file_input.name, **options)
            return {
                "success": True,
                "video_path": final_video.video_path,
                "duration": final_video.duration,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Simulation for demo mode ─────────────────────────────────────
    def _simulate_video_generation(
        self, file_input, voice_choice, subject_choice, grade_choice,
        duration_minutes, include_captions, include_transcript, slow_narration,
    ):
        demo_dir = Path("demo_outputs")
        demo_dir.mkdir(exist_ok=True)
        demo_file = demo_dir / f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        metadata = {
            "duration": f"{int(duration_minutes * 60)} seconds",
            "voice_used": voice_choice,
            "subject": subject_choice,
            "grade_level": grade_choice,
            "simulation": True,
            "message": "Add GEMINI_API_KEY for real video generation",
        }

        demo_file.write_text(
            f"🎓 Granite AI — Demo Output\n"
            f"Input: {getattr(file_input, 'name', 'uploaded')}\n"
            f"Subject: {subject_choice} | Grade: {grade_choice}\n"
            f"Voice: {voice_choice} | Duration: {duration_minutes} min\n"
        )

        return (
            None,
            "✅ Demo complete — add GEMINI_API_KEY for real videos",
            metadata,
            gr.File(str(demo_file), visible=True),
            None,
        )

    def load_demo(self, demo_type):
        demos = {
            "calculus": "demo_calculus.mp4",
            "physics": "demo_physics.mp4",
            "chemistry": "demo_chemistry.mp4",
        }
        path = demos.get(demo_type)
        return path if path and os.path.exists(path) else None

    def launch(self, **kwargs):
        interface = self.create_interface()
        return interface.launch(**kwargs)


def main():
    app = GraniteAgentInterface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
    )


if __name__ == "__main__":
    main()
