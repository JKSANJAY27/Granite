"""
Quick test: Run the Granite pipeline with the sample_calculus.pdf
All paid APIs replaced — uses only Gemini (free) + edge-tts/gTTS (free)
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

# Verify API keys are set
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not gemini_key:
    print("ERROR: No GEMINI_API_KEY or GOOGLE_API_KEY found in .env")
    sys.exit(1)

print(f"GEMINI key: ...{gemini_key[-6:]}")

# Check TTS availability
try:
    import edge_tts
    print("TTS engine: edge-tts (high-quality neural voices ✅)")
except ImportError:
    try:
        from gtts import gTTS
        print("TTS engine: gTTS (standard quality ✅)")
    except ImportError:
        print("WARNING: No TTS engine found — install edge-tts or gTTS")

# Run the pipeline
from crew import GraniteCrew

pdf_path = os.path.abspath("../sample_calculus.pdf")
print(f"\nPDF path: {pdf_path}")
print(f"PDF exists: {os.path.exists(pdf_path)}")

topic = f"Extract and analyse the content from this file: {pdf_path}"
print(f"\nStarting Granite pipeline...")
print("=" * 60)

try:
    crew = GraniteCrew(topic)
    result = crew.run()
    print("\n" + "=" * 60)
    print("PIPELINE RESULT:")
    print("=" * 60)
    print(result)
except Exception as e:
    print(f"\nPIPELINE ERROR: {e}")
    import traceback
    traceback.print_exc()
