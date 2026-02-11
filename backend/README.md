# Granite Backend

This is the backend for Granite, an automated video generation pipeline.

## Prerequisites

1.  **Python 3.10+** (Recommended 3.11 or 3.12)
2.  **FFmpeg**: Required for video processing and Manim.
    -   Download from [ffmpeg.org](https://ffmpeg.org/download.html).
    -   Add `bin` folder to your System PATH.
    -   Verify by running `ffmpeg -version` in terminal.
3.  **LaTeX** (Optional but recommended for math rendering):
    -   Install [MiKTeX](https://miktex.org/download) or TeX Live.
    -   Required if you want to render complex mathematical equations in animations.

## Setup

1.  **Install Python Dependencies**:
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    -   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Edit `.env` and add your API keys:
        -   `GOOGLE_API_KEY`: For Gemini (Link to get key: [Google AI Studio](https://aistudio.google.com/))
        -   `LMNT_API_KEY`: For voiceover (Link to get key: [LMNT](https://lmnt.com/))

## Running the Server

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

-   `POST /api/generate`: Upload a file or provide a concept text to generate a video.

## Architecture

-   **CrewAI**: Orchestrates the agents.
-   **Agents**:
    -   Content Extractor
    -   Lesson Planner
    -   Manim Animator (Generates code)
    -   Narrator (LMNT TTS)
    -   Video Composer (ffmpeg/moviepy)
    -   Quality Checker
