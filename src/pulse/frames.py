from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    code: str
    kind: str
    width: int
    height: int
    platform: str
    max_lines: int


FRAMES = {
    "ig_square": Frame("ig_square", "post", 1080, 1080, "instagram", 4),
    "ig_portrait": Frame("ig_portrait", "post", 1080, 1350, "instagram", 5),
    "x_landscape": Frame("x_landscape", "post", 1600, 900, "x", 3),
    "li_landscape": Frame("li_landscape", "post", 1920, 1080, "linkedin", 4),
    "fb_landscape": Frame("fb_landscape", "post", 1920, 1080, "facebook", 4),
    "web_banner": Frame("web_banner", "banner", 1920, 640, "web", 3),
    "flyer_a4": Frame("flyer_a4", "flyer", 1240, 1754, "web", 6),
}


PLATFORM_FRAME = {
    "x": "x_landscape",
    "linkedin": "li_landscape",
    "instagram": "ig_square",
    "facebook": "fb_landscape",
    "web": "web_banner",
    "webhook": "li_landscape",
}


def frame_for(platform: str, format_name: str | None = None) -> Frame:
    if format_name == "banner":
        return FRAMES["web_banner"]
    if format_name == "flyer":
        return FRAMES["flyer_a4"]
    code = PLATFORM_FRAME.get(platform, "ig_square")
    return FRAMES[code]
