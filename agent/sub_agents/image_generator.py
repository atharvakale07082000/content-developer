"""
ImageGeneratorAgent — generates platform-specific background/banner images.

Builds a visual prompt from the content analysis (topic, tone, themes),
then calls FLUX.1-schnell via HF Inference to produce a PNG.
Returns base64-encoded PNG so it can be stored directly in MongoDB.

Model: black-forest-labs/FLUX.1-schnell
Chosen for speed (4-step distilled), high quality, and free-tier availability.

Platform dimensions:
  linkedin   → 1024 × 512  (2:1 — post / banner)
  instagram  → 1024 × 1024 (1:1 — square)
  newsletter → 1024 × 256  (4:1 — email header)
"""
import base64
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_image

MODEL = "black-forest-labs/FLUX.1-schnell"

_PLATFORM_SIZE: dict[str, tuple[int, int]] = {
    "linkedin":   (1024, 512),
    "instagram":  (1024, 1024),
    "newsletter": (1024, 256),
}

_TONE_STYLE: dict[str, str] = {
    "educational":   "clean modern geometric shapes, soft blue and white tones, minimalist",
    "conversational": "warm earthy tones, organic textures, approachable and friendly",
    "technical":     "dark background, subtle circuit or grid patterns, cool cyan accents",
    "inspirational": "bright gradient sky, golden light, uplifting wide open space",
    "controversial": "bold high-contrast tones, dramatic shadows, strong visual tension",
}

_PLATFORM_STYLE: dict[str, str] = {
    "linkedin":   "professional banner background, corporate aesthetic, wide format",
    "instagram":  "vibrant square social media background, eye-catching, aesthetic",
    "newsletter": "clean email header background, subtle and elegant, wide panoramic",
}


def _build_prompt(analysis: dict, platform: str) -> str:
    topic = analysis.get("main_topic", "technology and innovation")
    tone = analysis.get("tone_of_source", "educational")
    themes = analysis.get("key_themes", [])

    visual_style = _TONE_STYLE.get(tone, _TONE_STYLE["educational"])
    platform_style = _PLATFORM_STYLE.get(platform, _PLATFORM_STYLE["linkedin"])
    theme_hint = ", ".join(themes[:2]) if themes else topic

    return (
        f"{platform_style}, inspired by the theme of {theme_hint}, "
        f"{visual_style}, abstract background, no text, no people, "
        f"high resolution, professional photography or digital art"
    )


class ImageGeneratorAgent(BaseAgent):
    agent_id = "image_generator"
    capabilities = ["generate_image"]
    model = MODEL

    def run(self, task: AgentTask) -> AgentResult:
        try:
            analysis = task.payload["analysis"]
            platform = task.payload["platform"]

            width, height = _PLATFORM_SIZE.get(platform, (1024, 1024))
            prompt = _build_prompt(analysis, platform)

            raw_bytes = hf_image(self.model, prompt, width=width, height=height)
            b64 = base64.b64encode(raw_bytes).decode("utf-8")

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                output={"platform": platform, "image_b64": b64, "prompt": prompt},
            )
        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                output=None,
                error=str(e),
            )
