"""
Quick test: Run the Granite pipeline with the sample_calculus.pdf
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

# Verify API keys are set
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
lmnt_key = os.getenv("LMNT_API_KEY")

if not gemini_key:
    print("ERROR: No GEMINI_API_KEY or GOOGLE_API_KEY found in .env")
    sys.exit(1)
if not lmnt_key:
    print("WARNING: No LMNT_API_KEY found in .env — narration will fail")

print(f"GEMINI key: ...{gemini_key[-6:]}")
print(f"LMNT key:   ...{lmnt_key[-6:] if lmnt_key else 'MISSING'}")

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
