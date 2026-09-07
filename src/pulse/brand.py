from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Colors:
    ink: str
    ink_muted: str
    paper: str
    paper_alt: str
    meridian: str
    meridian_bright: str
    line: str
    surface_dark: str
    danger: str
    ok: str


@dataclass(frozen=True)
class Brand:
    name: str
    tagline: str
    signature: str
    description: str
    what_we_sell: list[str]
    audience: list[str]
    value_proposition: str
    tone: list[str]
    forbidden: list[str]
    cta_library: list[str]
    primary_cta: str
    conversion_path: str
    url: str
    conversion_url: str
    hashtags: list[str]
    colors: Colors
    typeface: dict[str, str]
    space: dict[str, int]
    radius: dict[str, int]
    platforms: dict[str, dict[str, Any]]
    raw: dict[str, Any]

    def limit(self, platform: str) -> dict[str, Any]:
        return self.platforms.get(platform, {"max_chars": 500, "hashtags_max": 4, "frame": "ig_square"})


def load_brand(path: Path) -> Brand:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    ident = raw["identity"]
    colors = Colors(**ident["colors"])
    return Brand(
        name=raw["name"],
        tagline=raw["tagline"],
        signature=raw.get("signature") or raw["name"],
        description=str(raw.get("description") or "").strip(),
        what_we_sell=list(raw.get("what_we_sell") or []),
        audience=list(raw.get("audience") or []),
        value_proposition=str(raw.get("value_proposition") or "").strip(),
        tone=list(raw.get("tone") or []),
        forbidden=list(raw.get("forbidden") or []),
        cta_library=list(raw.get("cta_library") or []),
        primary_cta=raw.get("primary_cta") or "Crea tu propuesta",
        conversion_path=raw.get("conversion_path") or "/crear-propuesta",
        url=raw.get("url") or "https://globus.app",
        conversion_url=raw.get("conversion_url") or "https://globus.app/crear-propuesta",
        hashtags=list(raw.get("hashtags") or []),
        colors=colors,
        typeface=dict(ident.get("type") or {}),
        space={k: int(v) for k, v in (ident.get("space") or {}).items()},
        radius={k: int(v) for k, v in (ident.get("radius") or {}).items()},
        platforms=dict(raw.get("platforms") or {}),
        raw=raw,
    )
