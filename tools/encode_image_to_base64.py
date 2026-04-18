import base64
import os
import uuid

from langchain_core.tools import tool

from shared_store import BASE64_STORE


@tool
def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to Base64 without exposing the binary to the LLM.

    Stores the full Base64 string in an in-memory store and returns a
    lightweight UUID placeholder (BASE64_KEY:<uuid>). The post_request tool
    automatically resolves this placeholder before submitting to any server.

    This prevents token overflow, malformed JSON, and LLM context pollution
    from large Base64 blobs.

    Parameters
    ----------
    image_path : str
        Image filename inside the LLMFiles directory (e.g., 'screenshot.png').

    Returns
    -------
    str  Placeholder token: "BASE64_KEY:<uuid>"
    """
    try:
        path = os.path.join("LLMFiles", image_path)
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        key = str(uuid.uuid4())
        BASE64_STORE[key] = encoded
        return f"BASE64_KEY:{key}"
    except Exception as e:
        return f"Encoding error: {e}"
