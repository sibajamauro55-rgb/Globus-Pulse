from __future__ import annotations

from pathlib import Path

from pulse.brand import Brand
from pulse.copywrite import violates_voice


def validate_piece(brand: Brand, *, headline: str, caption: str, cta: str, destination: str, asset_path: str, platform: str) -> list[str]:
    errors: list[str] = []
    if not headline.strip():
        errors.append("headline vacío")
    if not caption.strip():
        errors.append("caption vacío")
    if not cta.strip():
        errors.append("cta vacío")
    if brand.conversion_path not in destination and "crear-propuesta" not in destination:
        errors.append("destino sin /crear-propuesta")
    if brand.name.lower() not in (headline + caption + cta).lower() and "globus" not in (headline + caption).lower():
        errors.append("la pieza no nombra Globus")
    limit = int(brand.limit(platform).get("max_chars", 2000))
    if len(caption) > limit:
        errors.append(f"caption excede {limit} caracteres")
    errors.extend(f"voz:{w}" for w in violates_voice(brand, headline + " " + caption))
    if asset_path:
        p = Path(asset_path)
        if not p.is_file() or p.stat().st_size < 1000:
            errors.append("asset ausente o demasiado pequeño")
    return errors
