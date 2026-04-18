import base64
import os
from io import BytesIO

import pytesseract
from langchain_core.tools import tool
from PIL import Image


def load_image(image_input):
    """Internal helper to load an image from bytes, file path, base64, or PIL.Image."""
    if isinstance(image_input, bytes):
        return Image.open(BytesIO(image_input)).convert("RGB")
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")
    if isinstance(image_input, str):
        if image_input.startswith("data:"):
            _, b64 = image_input.split(",", 1)
            return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")
        return Image.open(os.path.join("LLMFiles", image_input)).convert("RGB")
    raise ValueError("Unsupported image input type")


@tool
def ocr_image_tool(payload: dict) -> dict:
    """
    Extract text from an image using pytesseract OCR.

    Expected payload:
    {
        "image": bytes | base64 string | file path | PIL.Image,
        "lang": "eng" (optional)
    }

    Returns:
    {
        "text": "<extracted text>",
        "engine": "pytesseract"
    }
    """
    try:
        image_data = payload["image"]
        lang = payload.get("lang", "eng")

        img = load_image(image_data)
        text = pytesseract.image_to_string(img, lang=lang)

        return {
            "text": text.strip(),
            "engine": "pytesseract",
        }
    except Exception as e:
        return {"error": f"Error occurred: {e}"}
