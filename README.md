# 🎬 TikTok Review Maker

Turn up to 10 product photos + a description into a scroll-stopping vertical TikTok video — fully automated with Ken Burns effects, text overlays, crossfade transitions, and optional background music.

## Features

- Upload 1–10 product images (JPEG, PNG, WebP)
- Manual caption entry: product name + up to 5 feature bullets
- Optional AI caption generation via Gemini API (free tier)
- Optional background music (MP3/WAV), auto-trimmed to video length
- Output: 1080×1920 MP4, H.264, ~30 seconds, ready for TikTok

## Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- **FFmpeg** — must be on your PATH

### Install FFmpeg (Windows)

```powershell
# Option A: winget
winget install Gyan.FFmpeg

# Option B: Chocolatey
choco install ffmpeg
```

Verify: `ffmpeg -version`

## Setup

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env — add GEMINI_API_KEY if you want AI captions (optional)
```

### 2. Frontend

```powershell
cd frontend
npm install
```

## Running

Open two terminals:

**Terminal 1 — Backend**

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn main:app --reload
# Runs at http://localhost:8000
```

**Terminal 2 — Frontend**

```powershell
cd frontend
npm run dev
# Opens at http://localhost:5173
```

## Usage

1. Upload 1–10 product images (drag & drop, reorder with ◀▶ buttons)
2. Enter a **Product Name** and up to 5 **Feature Bullets**
   - Or paste a description and click **✨ Generate with AI** (requires Gemini key)
3. Optionally upload background music
4. Click **🎬 Generate TikTok Video** and wait 30–90 seconds
5. Preview and download your MP4

## Project Structure

```
tool-ai/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── services/
│   │   ├── ai_caption.py        # Gemini AI caption generation
│   │   ├── image_processor.py   # Smart crop/resize to 1080×1920
│   │   └── video_renderer.py    # FFmpeg pipeline (Ken Burns, text, music)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.tsx
        ├── api/client.ts
        └── components/
            ├── ImageUploader.tsx
            ├── CaptionEditor.tsx
            ├── MusicUploader.tsx
            └── VideoPreview.tsx
```

tool sử dụng ai
