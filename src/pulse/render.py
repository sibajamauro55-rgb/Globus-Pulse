from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pulse.brand import Brand
from pulse.frames import Frame


def _hex(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    if Path(path).exists():
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        trial = f"{current} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def render_piece(
    brand: Brand,
    *,
    frame: Frame,
    template_code: str,
    kicker: str,
    headline: str,
    support: str,
    cta: str,
    destination: str,
    out_path: Path,
) -> Path:
    bg = _hex(brand.colors.paper)
    ink = _hex(brand.colors.ink)
    muted = _hex(brand.colors.ink_muted)
    meridian = _hex(brand.colors.meridian)
    line = _hex(brand.colors.line)
    dark = _hex(brand.colors.surface_dark)

    img = Image.new("RGB", (frame.width, frame.height), bg)
    draw = ImageDraw.Draw(img)
    m = int(min(frame.width, frame.height) * 0.07)

    draw.rectangle([0, 0, frame.width, frame.height], fill=bg)
    draw.rectangle([0, 0, 16, frame.height], fill=meridian)
    draw.rectangle([0, frame.height - 18, frame.width, frame.height], fill=dark)
    draw.rectangle([m, m, frame.width - m, frame.height - m], outline=line, width=2)

    kicker_font = _font(max(18, frame.height // 36), bold=True)
    display_font = _font(max(34, frame.height // 12), bold=True)
    body_font = _font(max(20, frame.height // 28), bold=False)
    meta_font = _font(max(16, frame.height // 38), bold=False)
    cta_font = _font(max(18, frame.height // 32), bold=True)

    max_w = frame.width - m * 2 - 56
    x = m + 36
    y = m + 20

    draw.text((x, y), f"{brand.name.upper()}  ·  {kicker.upper()}", font=kicker_font, fill=meridian)
    y += int(kicker_font.size * 2.0)

    if template_code in {"problem_solution", "compare"}:
        mid = frame.width // 2
        box_h = int(frame.height * 0.42)
        draw.rectangle([x, y, mid - 16, y + box_h], fill=dark)
        draw.rectangle([mid + 8, y, frame.width - m - 20, y + box_h], fill=meridian)
        left_font = _font(max(22, frame.height // 22), bold=True)
        for i, line_t in enumerate(_wrap(draw, headline, left_font, mid - x - 40)[:3]):
            draw.text((x + 20, y + 24 + i * int(left_font.size * 1.2)), line_t, font=left_font, fill=_hex(brand.colors.paper))
        for i, line_t in enumerate(_wrap(draw, support, left_font, frame.width - mid - m - 60)[:3]):
            draw.text((mid + 28, y + 24 + i * int(left_font.size * 1.2)), line_t, font=left_font, fill=_hex(brand.colors.paper))
        y = y + box_h + 28
    elif template_code in {"cta", "promo"}:
        draw.rectangle([0, 0, frame.width, frame.height], fill=dark)
        draw.rectangle([0, 0, 16, frame.height], fill=meridian)
        draw.text((x, m + 24), f"{brand.name.upper()}  ·  {kicker.upper()}", font=kicker_font, fill=meridian)
        y = int(frame.height * 0.28)
        for line_t in _wrap(draw, headline, display_font, max_w)[: frame.max_lines]:
            draw.text((x, y), line_t, font=display_font, fill=_hex(brand.colors.paper))
            y += int(display_font.size * 1.15)
        y += 16
        draw.rectangle([x, y, x + 72, y + 4], fill=meridian)
        y += 28
        for line_t in _wrap(draw, support, body_font, max_w)[:2]:
            draw.text((x, y), line_t, font=body_font, fill=_hex(brand.colors.line))
            y += int(body_font.size * 1.3)
    else:
        for line_t in _wrap(draw, headline, display_font, max_w)[: frame.max_lines]:
            draw.text((x, y), line_t, font=display_font, fill=ink)
            y += int(display_font.size * 1.12)
        y += 10
        draw.rectangle([x, y, x + 72, y + 4], fill=meridian)
        y += 22
        for line_t in _wrap(draw, support, body_font, max_w)[:3]:
            draw.text((x, y), line_t, font=body_font, fill=muted)
            y += int(body_font.size * 1.35)

    pill = f"{cta}  →"
    pw = int(draw.textlength(pill, font=cta_font)) + 40
    ph = int(cta_font.size) + 22
    py = frame.height - m - ph - 36
    draw.rounded_rectangle([x, py, x + pw, py + ph], radius=8, fill=meridian)
    draw.text((x + 20, py + 10), pill, font=cta_font, fill=_hex(brand.colors.paper))

    dest = destination.replace("https://", "")
    dest_w = draw.textlength(dest, font=meta_font)
    draw.text((frame.width - m - 24 - dest_w, frame.height - 14 - meta_font.size), dest, font=meta_font, fill=_hex(brand.colors.paper))
    draw.text((20, frame.height - 14 - meta_font.size), brand.tagline, font=meta_font, fill=_hex(brand.colors.paper))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path
