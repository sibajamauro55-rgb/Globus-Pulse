from __future__ import annotations

import hashlib
import json
import re

from pulse.angles import Angle
from pulse.brand import Brand


def clip(text: str, max_len: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def hashtags(brand: Brand, platform: str) -> list[str]:
    limit = int(brand.limit(platform).get("hashtags_max", 4))
    out: list[str] = []
    for item in brand.hashtags:
        token = item.replace("#", "").strip()
        if token and token not in out:
            out.append(token)
    return out[:limit]


def caption_for(brand: Brand, angle: Angle, platform: str) -> str:
    limit = int(brand.limit(platform).get("max_chars", 500))
    parts = [angle.body.strip(), "", angle.support.strip(), "", f"{brand.primary_cta} → {brand.conversion_url}"]
    if platform == "x":
        parts = [angle.headline, angle.support, brand.conversion_url]
    text = "\n".join(p for p in parts if p is not None)
    tags = " ".join(f"#{t}" for t in hashtags(brand, platform))
    if platform != "x" and tags:
        text = f"{text}\n\n{tags}"
    text = f"{text}\n{brand.signature}"
    return clip(text, limit)


def fingerprint(campaign_code: str, angle_id: str, platform: str, slot_key: str) -> str:
    raw = f"{campaign_code}|{angle_id}|{platform}|{slot_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def video_script(brand: Brand, angle: Angle) -> list[dict[str, str]]:
    return [
        {"scene": "hook", "seconds": "0-4", "on_screen": angle.headline, "voice": angle.headline},
        {"scene": "problem", "seconds": "4-12", "on_screen": angle.support, "voice": angle.body.split(".")[0] + "."},
        {"scene": "system", "seconds": "12-22", "on_screen": brand.tagline, "voice": brand.value_proposition.split(".")[0] + "."},
        {
            "scene": "cta",
            "seconds": "22-30",
            "on_screen": brand.primary_cta,
            "voice": f"{brand.primary_cta}. {brand.conversion_url}",
        },
    ]


def violates_voice(brand: Brand, text: str) -> list[str]:
    hits = []
    lower = text.lower()
    for word in brand.forbidden:
        if word.lower() in lower:
            hits.append(word)
    if re.search(r"[\U0001F300-\U0001FAFF]{3,}", text):
        hits.append("emojis excesivos")
    return hits


def script_dumps(brand: Brand, angle: Angle) -> str:
    return json.dumps(video_script(brand, angle), ensure_ascii=False)
