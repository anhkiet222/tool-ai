import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# FFmpeg binary resolution (cross-platform: Windows dev + Linux/Render prod)
# Lazy init: resolved on first use, not at import time, so the app starts
# cleanly even if FFmpeg is not yet on PATH during module load.
# ---------------------------------------------------------------------------
_WINGET_BIN = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"

_FFMPEG: str | None = None
_FFPROBE: str | None = None


def _find_bin(name: str) -> str:
    # 1. Check PATH first (works on Linux/Render where ffmpeg is installed via apt)
    found = shutil.which(name)
    if found:
        return found
    # 2. Scan entire WinGet Packages directory recursively (covers ngrok, ffmpeg, etc.)
    winget_root = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    if winget_root.exists():
        for candidate in sorted(winget_root.rglob(f"{name}.exe")):
            return str(candidate)
    # 3. Common absolute fallback paths for Windows
    fallbacks = [
        Path.home() / f"AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1-full_build/bin/{name}.exe",
        Path(r"C:/ffmpeg/bin") / f"{name}.exe",
        Path(r"C:/Program Files/ffmpeg/bin") / f"{name}.exe",
    ]
    for path in fallbacks:
        if path.exists():
            return str(path)
    raise FileNotFoundError(
        f"'{name}' not found. Install FFmpeg and ensure it is on your PATH."
    )


def _get_ffmpeg() -> str:
    global _FFMPEG
    if _FFMPEG is None:
        _FFMPEG = _find_bin("ffmpeg")
    return _FFMPEG


def _get_ffprobe() -> str:
    global _FFPROBE
    if _FFPROBE is None:
        _FFPROBE = _find_bin("ffprobe")
    return _FFPROBE

# ---------------------------------------------------------------------------
# Video constants
# ---------------------------------------------------------------------------
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
SECONDS_PER_IMAGE = 3
TRANSITION_DURATION = 0.5
FRAMES_PER_IMAGE = FPS * SECONDS_PER_IMAGE  # 90 frames

_FONT_CANDIDATES = [
    # Linux / Render (Debian/Ubuntu)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    # Windows (local dev)
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
]


def _get_font(size: int) -> ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_video(
    image_paths: list[str],
    product_name: str,
    bullets: list[str],
    output_path: str,
    music_path: str | None = None,
) -> str:
    """Render a TikTok-style vertical video. Returns output_path on success."""
    n = len(image_paths)
    if n == 0:
        raise ValueError("At least one image is required.")

    clip_paths: list[str] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        text_dir = tmp / "text_frames"
        text_dir.mkdir()

        for i, img_path in enumerate(image_paths):
            # Burn text with Pillow — avoids all FFmpeg font/escaping issues on Windows
            text_frame = str(text_dir / f"frame_{i:02d}.jpg")
            _burn_text(img_path, text_frame, i, n, product_name, bullets)

            clip_out = str(tmp / f"clip_{i:02d}.mp4")
            _render_clip(text_frame, clip_out, i)
            clip_paths.append(clip_out)

        combined = str(tmp / "combined.mp4")
        _concat_with_xfade(clip_paths, combined)

        if music_path:
            _mix_music(combined, music_path, output_path)
        else:
            shutil.copy2(combined, output_path)

    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _burn_text(
    img_path: str,
    output_path: str,
    clip_index: int,
    total_clips: int,
    product_name: str,
    bullets: list[str],
) -> None:
    """Draw text overlays onto the image using Pillow before FFmpeg processes it."""
    with Image.open(img_path).convert("RGBA") as base:
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = base.size

        def draw_with_shadow(
            text: str,
            x: int,
            y: int,
            font: ImageFont.ImageFont,
            anchor: str = "mm",
        ) -> None:
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3), (3, 0)]:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 200), anchor=anchor)
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255), anchor=anchor)

        # Semi-transparent gradient bar at the bottom for text readability
        bar_h = int(h * 0.35)
        bar = Image.new("RGBA", (w, bar_h), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar)
        for row in range(bar_h):
            alpha = int(160 * (row / bar_h))
            bar_draw.line([(0, row), (w, row)], fill=(0, 0, 0, alpha))
        overlay.paste(bar, (0, h - bar_h), bar)

        # Product name — first clip only
        if clip_index == 0 and product_name:
            font_name = _get_font(62)
            draw_with_shadow(product_name.upper(), w // 2, int(h * 0.74), font_name)

        # One bullet per clip (cycle if fewer bullets than clips)
        if bullets:
            bullet = bullets[clip_index % len(bullets)]
            font_bullet = _get_font(46)
            draw_with_shadow(bullet, w // 2, int(h * 0.84), font_bullet)

        # Clip counter — bottom right
        font_counter = _get_font(30)
        counter_text = f"{clip_index + 1}/{total_clips}"
        draw.text(
            (w - 28, h - 28),
            counter_text,
            font=font_counter,
            fill=(255, 255, 255, 160),
            anchor="rb",
        )

        composite = Image.alpha_composite(base, overlay).convert("RGB")
        composite.save(output_path, "JPEG", quality=95)


def _render_clip(img_path: str, output_path: str, clip_index: int) -> None:
    """Render a single clip with Ken Burns zoom effect. No text filters."""
    if clip_index % 2 == 0:
        zoompan = (
            f"zoompan=z='min(zoom+0.0012,1.4)'"
            f":x='iw/2-(iw/zoom/2)+{clip_index % 3 * 5}'"
            f":y='ih/2-(ih/zoom/2)'"
            f":d={FRAMES_PER_IMAGE}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"
        )
    else:
        zoompan = (
            f"zoompan=z='if(lte(zoom,1.0),1.4,max(1.0,zoom-0.0012))'"
            f":x='iw/2-(iw/zoom/2)-{clip_index % 3 * 5}'"
            f":y='ih/2-(ih/zoom/2)'"            f":d={FRAMES_PER_IMAGE}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"
        )

    cmd = [
        _get_ffmpeg(), "-y",
        "-loop", "1",
        "-i", img_path,
        "-t", str(SECONDS_PER_IMAGE),
        "-vf", zoompan,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]
    _run(cmd)


def _concat_with_xfade(clip_paths: list[str], output_path: str) -> None:
    """Concatenate clips using xfade transitions."""
    if len(clip_paths) == 1:
        shutil.copy2(clip_paths[0], output_path)
        return

    inputs: list[str] = []
    for p in clip_paths:
        inputs += ["-i", p]

    n = len(clip_paths)
    filter_parts: list[str] = []
    current = "[0:v]"

    for i in range(1, n):
        offset = i * SECONDS_PER_IMAGE - i * TRANSITION_DURATION
        out_label = f"[v{i}]" if i < n - 1 else "[vout]"
        filter_parts.append(
            f"{current}[{i}:v]xfade=transition=fade"
            f":duration={TRANSITION_DURATION}:offset={offset}{out_label}"
        )
        current = f"[v{i}]"

    filtergraph = ";".join(filter_parts)

    cmd = [
        _get_ffmpeg(), "-y",
        *inputs,
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    _run(cmd)


def _mix_music(video_path: str, music_path: str, output_path: str) -> None:
    """Trim/loop music to match video duration and mix into the output."""
    probe_cmd = [
        _get_ffprobe(), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(
        probe_cmd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    duration = float(result.stdout.strip())

    cmd = [
        _get_ffmpeg(), "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", music_path,
        "-map", "0:v",
        "-map", "1:a",
        "-af", (
            f"atrim=0:{duration},"
            f"afade=t=out:st={max(0, duration - 2)}:d=2,"
            "volume=0.4"
        ),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ]
    _run(cmd)


def _run(cmd: list[str]) -> None:
    result = subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        stderr = result.stderr or ""
        stdout = result.stdout or ""
        raise RuntimeError(
            f"FFmpeg error (code {result.returncode}):\n{(stderr + stdout)[-3000:]}"
        )
