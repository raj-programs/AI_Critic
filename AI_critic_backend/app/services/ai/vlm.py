import base64
import json
import os
from pathlib import Path

import requests
from groq import Groq
from app.core.config import settings

from .prompts import (
    VLM_SYSTEM_PROMPT,
    VLM_USER_PROMPT,
)
from .schema import VLMResponse


# ============================================================
# Configuration
# ============================================================

GROQ_VLM_MAX_OUTPUT_TOKENS = 500
OLLAMA_VLM_MAX_OUTPUT_TOKENS = 500


# ============================================================
# Helpers
# ============================================================

def encode_image(image_path: str) -> str:
    """
    Convert a local image into a base64 string.
    """

    with open(image_path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


def load_image_mime_type(image_path: str) -> str:
    """
    Determine the MIME type from the image extension.
    """

    extension = Path(image_path).suffix.lower()

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    return mime_types.get(
        extension,
        "image/png"
    )


# ============================================================
# Groq VLM
# ============================================================

def analyze_with_groq(image_path: str) -> VLMResponse:
    """
    Analyze a screenshot using Groq's Qwen vision model.
    """

    api_key = settings.groq_api_key

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    client = Groq(
        api_key=api_key,
        timeout=45.0,
        max_retries=0,
    )

    base64_image = encode_image(image_path)
    mime_type = load_image_mime_type(image_path)

    image_url = (
        f"data:{mime_type};base64,{base64_image}"
    )

    completion = client.chat.completions.create(
        model=settings.vlm_groq_model,

        messages=[
            {
                "role": "system",
                "content": VLM_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": VLM_USER_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        },
                    },
                ],
            },
        ],

        temperature=0.3,

        max_completion_tokens=GROQ_VLM_MAX_OUTPUT_TOKENS,

        response_format={
            "type": "json_object"
        },
    )

    content = (
        completion
        .choices[0]
        .message
        .content
    )

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    
    data = json.loads(content)

    if isinstance(data, list):
        data = {"findings": data}
    elif isinstance(data, dict) and "findings" not in data and "id" in data:
        data = {"findings": [data]}

    return VLMResponse.model_validate(data)


# ============================================================
# Ollama VLM
# ============================================================

def analyze_with_ollama(image_path: str) -> VLMResponse:
    """
    Analyze a screenshot using a local Ollama vision model.
    """

    base64_image = encode_image(image_path)

    payload = {
        "model": settings.vlm_ollama_model,

        "messages": [
            {
                "role": "system",
                "content": VLM_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": VLM_USER_PROMPT,
                "images": [
                    base64_image
                ],
            },
        ],

        "stream": False,
        "format": "json",
        "options": {"num_predict": OLLAMA_VLM_MAX_OUTPUT_TOKENS},
    }

    response = requests.post(
        f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        json=payload,
        timeout=120,
    )

    response.raise_for_status()
    result = response.json()

    content = result.get(
        "message",
        {}
    ).get(
        "content"
    )

    if not content:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    data = json.loads(content)

    return VLMResponse.model_validate(data)


# ============================================================
# Public VLM Interface
# ============================================================

def analyze_screenshot(
    image_path: str,
    provider: str | None = None,
) -> VLMResponse:
    """
    Analyze a webpage screenshot using the selected VLM provider.

    provider:
        "groq"
        "ollama"
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Screenshot not found: {image_path}"
        )

    selected_provider = (
        provider or settings.vlm_provider
    ).lower()

    if selected_provider == "groq":
        return analyze_with_groq(
            image_path
        )

    if selected_provider == "ollama":
        return analyze_with_ollama(
            image_path
        )

    raise ValueError(
        f"Unsupported VLM provider: {selected_provider}"
    )
