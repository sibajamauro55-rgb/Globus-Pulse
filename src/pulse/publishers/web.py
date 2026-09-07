from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from pulse.publishers.base import PublishResult, Publisher
from pulse.settings import Settings


class WebSitePublisher(Publisher):
    """Adaptador del sitio Globus.

    No toca Globus-Core-Web. Si hay endpoint, publica por HTTP.
    Si no, deja el payload en outbound/web/ listo para consumo posterior.
    El archivo local NO cuenta como publicación en red; el job queda
    published solo cuando el endpoint responde 2xx, o blocked si no hay endpoint.
    """

    platform = "web"
    adapter = "globus_web"

    def __init__(self, settings: Settings):
        self.settings = settings

    def ready(self) -> tuple[bool, str]:
        if self.settings.web_publish_endpoint:
            return True, ""
        return False, "web.endpoint_missing"

    def _dump(self, payload: dict[str, Any], asset_path: Path | None) -> Path:
        folder = self.settings.outbound_dir / "web"
        folder.mkdir(parents=True, exist_ok=True)
        name = payload.get("id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        dest = folder / f"{name}.json"
        body = dict(payload)
        if asset_path:
            body["asset_path"] = str(asset_path)
        dest.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        return dest

    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        dumped = self._dump(payload, asset_path)
        ok, reason = self.ready()
        if not ok:
            return PublishResult(
                False,
                self.platform,
                self.adapter,
                "blocked",
                error=f"{reason};staged={dumped}",
            )
        headers = {"Content-Type": "application/json"}
        if self.settings.web_publish_token:
            headers["Authorization"] = f"Bearer {self.settings.web_publish_token}"
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(self.settings.web_publish_endpoint, json=payload, headers=headers)
            if resp.status_code >= 400:
                return PublishResult(
                    False, self.platform, self.adapter, "live", error=f"web.http_{resp.status_code}"
                )
            return PublishResult(True, self.platform, self.adapter, "live", external_id=str(resp.status_code))
        except httpx.HTTPError as exc:
            return PublishResult(False, self.platform, self.adapter, "live", error=f"web.network:{exc}")
