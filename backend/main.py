"""
Granite - FastAPI Application

Exposes a POST /api/generate endpoint that accepts a file upload
and/or a concept description, then runs the CrewAI pipeline.
"""

import os
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import uvicorn

from crew import GraniteCrew

load_dotenv()

app = FastAPI(
    title="Granite API",
    description="Automated educational video generation pipeline",
    version="1.0.0",
)

# Allow frontend to connect from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Granite API is running.", "docs": "/docs"}


@app.post("/api/generate")
async def generate_video(
    file: Optional[UploadFile] = File(None),
    concept: Optional[str] = Form(None),
):
    """
    Generate an educational video.

    - **file**: (optional) A PDF or image to extract content from.
    - **concept**: (optional) A text description of the topic/concept.

    At least one of `file` or `concept` must be provided.
    """
    if not file and not concept:
        raise HTTPException(
            status_code=400,
            detail="Provide at least a file or a concept description.",
        )

    # ── Save uploaded file (if any) ──────────────────────────────────
    file_path = None
    if file:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # ── Build the prompt for the crew ────────────────────────────────
    parts = []
    if file_path:
        parts.append(f"Extract and analyse the content from this file: {file_path}")
    if concept:
        parts.append(f"Focus on explaining this concept: {concept}")
    user_input = " ".join(parts)

    # ── Run the pipeline ─────────────────────────────────────────────
    try:
        crew = GraniteCrew(user_input)
        result = crew.run()

        return {
            "status": "success",
            "result": str(result),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
