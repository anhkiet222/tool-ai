import os
import shutil
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from services.ai_caption import CaptionResult, generate_captions, is_ai_available
from services.image_processor import process_images
from services.video_renderer import render_video

load_dotenv()

app = FastAPI(title="TikTok Video Generator")

_allowed_origins = ["http://localhost:5173"]
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    _allowed_origins.append(_frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/mp3", "audio/x-wav"}
MAX_IMAGE_SIZE_MB = 15
MAX_AUDIO_SIZE_MB = 30


@app.get("/api/status")
def status():
    return {"ai_available": is_ai_available()}


@app.post("/api/generate-captions")
async def api_generate_captions(description: str = Form(...)):
    if not is_ai_available():
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is not configured.")
    if not description.strip():
        raise HTTPException(status_code=422, detail="Description cannot be empty.")
    try:
        result = generate_captions(description)
        return {"product_name": result.product_name, "bullets": result.bullets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def api_generate(
    images: list[UploadFile] = File(...),
    product_name: str = Form(...),
    bullets: list[str] = Form(default=[]),
    music: UploadFile | None = File(default=None),
):
    # --- Validate inputs ---
    if not 1 <= len(images) <= 10:
        raise HTTPException(status_code=422, detail="Provide between 1 and 10 images.")

    for img in images:
        if img.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported image type: {img.content_type}. Use JPEG, PNG, or WebP.",
            )

    if music and music.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio type: {music.content_type}. Use MP3 or WAV.",
        )

    bullets = [b.strip() for b in bullets if b.strip()][:5]
    if not product_name.strip():
        raise HTTPException(status_code=422, detail="Product name cannot be empty.")

    # --- Process in a temp workspace ---
    job_id = uuid.uuid4().hex
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # Save uploaded images
        raw_dir = tmp / "raw"
        raw_dir.mkdir()
        raw_paths = []
        for i, img in enumerate(images):
            content = await img.read()
            if len(content) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"Image {img.filename} exceeds {MAX_IMAGE_SIZE_MB}MB limit.",
                )
            suffix = Path(img.filename or "img.jpg").suffix or ".jpg"
            raw_path = str(raw_dir / f"img_{i:02d}{suffix}")
            with open(raw_path, "wb") as f:
                f.write(content)
            raw_paths.append(raw_path)

        # Save uploaded music
        music_path = None
        if music:
            content = await music.read()
            if len(content) > MAX_AUDIO_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"Audio file exceeds {MAX_AUDIO_SIZE_MB}MB limit.",
                )
            suffix = Path(music.filename or "music.mp3").suffix or ".mp3"
            music_path = str(tmp / f"music{suffix}")
            with open(music_path, "wb") as f:
                f.write(content)

        # Process images → 1080x1920
        processed_dir = str(tmp / "processed")
        processed_paths = process_images(raw_paths, processed_dir)

        # Render video to temp location first
        tmp_video = str(tmp / "output.mp4")
        try:
            render_video(
                image_paths=processed_paths,
                product_name=product_name.strip(),
                bullets=bullets,
                output_path=tmp_video,
                music_path=music_path,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # Move to persistent outputs dir
        final_path = OUTPUTS_DIR / f"{job_id}.mp4"
        shutil.copy2(tmp_video, final_path)

    return FileResponse(
        path=str(final_path),
        media_type="video/mp4",
        filename="tiktok_review.mp4",
        background=_cleanup_later(str(final_path)),
    )


class _cleanup_later:
    """Background task to delete the output file after it has been sent."""
    def __init__(self, path: str):
        self._path = path

    async def __call__(self):
        try:
            os.remove(self._path)
        except OSError:
            pass
