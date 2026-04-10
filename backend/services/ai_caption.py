import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


@dataclass
class CaptionResult:
    product_name: str
    bullets: list[str]


def is_ai_available() -> bool:
    return bool(_GEMINI_API_KEY)


# Fallback chain: try each model in order, use first one that succeeds
_MODEL_FALLBACKS = [
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
]


def generate_captions(description: str) -> CaptionResult:
    """
    Use Gemini to generate a product name and up to 5 short feature bullets
    from the provided description. Tries multiple models in fallback order.
    Raises RuntimeError if no API key is configured or all models fail.
    """
    if not _GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set. Cannot generate AI captions.")

    import google.generativeai as genai  # lazy import — only needed when key exists

    genai.configure(api_key=_GEMINI_API_KEY)

    prompt = f"""You are a TikTok product review copywriter.
Based on this product description, generate:
1. A short product name (max 5 words, punchy, no brand unless mentioned)
2. Exactly 5 compelling feature bullets (each max 8 words, start with an emoji)

Description: {description}

Respond ONLY in this exact format (no extra text):
NAME: <product name>
BULLET: <bullet 1>
BULLET: <bullet 2>
BULLET: <bullet 3>
BULLET: <bullet 4>
BULLET: <bullet 5>"""

    last_error: Exception | None = None
    for model_name in _MODEL_FALLBACKS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return _parse_response(response.text)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def _parse_response(text: str) -> CaptionResult:
    product_name = ""
    bullets: list[str] = []

    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("NAME:"):
            product_name = line[5:].strip()
        elif line.startswith("BULLET:"):
            bullets.append(line[7:].strip())

    if not product_name:
        product_name = "Product Review"
    bullets = bullets[:5] or ["✨ Must-have item", "🔥 Top quality", "💯 Great value"]

    return CaptionResult(product_name=product_name, bullets=bullets)
