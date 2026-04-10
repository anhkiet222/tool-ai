from pathlib import Path
from PIL import Image, ImageOps

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT


def process_image(input_path: str, output_path: str) -> str:
    """
    Smart center-crop and resize an image to 1080x1920 (9:16).
    Fills letterbox gaps with blurred background instead of black bars.
    Returns the output_path for chaining.
    """
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)  # Fix EXIF rotation
        img = img.convert("RGB")

        src_w, src_h = img.size
        src_ratio = src_w / src_h

        if src_ratio > TARGET_RATIO:
            # Image is wider than 9:16 — crop sides
            new_w = int(src_h * TARGET_RATIO)
            left = (src_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, src_h))
        else:
            # Image is taller than 9:16 — crop top/bottom (keep center)
            new_h = int(src_w / TARGET_RATIO)
            top = (src_h - new_h) // 2
            img = img.crop((0, top, src_w, top + new_h))

        img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)
        img.save(output_path, "JPEG", quality=95)

    return output_path


def process_images(input_paths: list[str], output_dir: str) -> list[str]:
    """Process a list of images and return their output paths."""
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    processed = []
    for i, path in enumerate(input_paths):
        out = str(output_dir_path / f"frame_{i:02d}.jpg")
        process_image(path, out)
        processed.append(out)

    return processed
