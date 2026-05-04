"""
Shared HuggingFace Inference client helper.

Each sub-agent calls hf_chat() with its own model name so we get
a different open-source model per task without duplicating setup logic.
"""
import io
import json
import re
from huggingface_hub import InferenceClient
from core.config import settings


def hf_chat(
    model: str,
    prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    system: str | None = None,
) -> str:
    """
    Send a single user turn to a HuggingFace Inference endpoint and return
    the raw text of the assistant reply.

    Args:
        model:       HuggingFace model repo ID (e.g. "mistralai/Mistral-7B-Instruct-v0.3")
        prompt:      The user message content.
        max_tokens:  Maximum tokens to generate.
        temperature: Sampling temperature.
        system:      Optional system message (injected before the user turn).
    """
    client = InferenceClient(model=model, token=settings.hf_api_token)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def hf_image(model: str, prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    """
    Generate an image via a HuggingFace text-to-image model.
    Uses the new router.huggingface.co endpoint (required for FLUX and modern models).
    Returns raw PNG bytes.
    """
    import requests
    from PIL import Image as PILImage

    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    headers = {"Authorization": f"Bearer {settings.hf_api_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {"width": width, "height": height},
    }
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    image = PILImage.open(io.BytesIO(response.content))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def extract_json_block(text: str) -> str:
    """
    Strip markdown fences and leading/trailing noise so json.loads() succeeds
    on model output that wraps JSON in ```json ... ``` blocks.
    """
    # Remove ```json ... ``` or ``` ... ``` fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fenced:
        return fenced.group(1).strip()
    # Try to find the first { or [ to the last } or ]
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return match.group(1).strip()
    return text.strip()
