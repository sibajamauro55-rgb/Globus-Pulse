from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from pulse.publishers.base import PublishResult, Publisher
from pulse.settings import Settings


class WebhookPublisher(Publisher):
    """Destino HTTP real. Útil como puente interno o ingestión propia."""

    platform = "webhook"
    adapter = "webhook"

    def __init__(self, settings: Settings):
        self.settings = settings

    def ready(self) -> tuple[bool, str]:
        if not self.settings.webhook_url:
            return False, "webhook.url_missing"
        return True, ""

    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        ok, reason = self.ready()
        if not ok:
            return PublishResult(False, self.platform, self.adapter, "blocked", error=reason)
        headers = {"Content-Type": "application/json"}
        if self.settings.webhook_token:
            headers["Authorization"] = f"Bearer {self.settings.webhook_token}"
        body = dict(payload)
        if asset_path:
            body["asset_path"] = str(asset_path)
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(self.settings.webhook_url, json=body, headers=headers)
            if resp.status_code >= 400:
                return PublishResult(
                    False,
                    self.platform,
                    self.adapter,
                    "live",
                    error=f"webhook.http_{resp.status_code}:{resp.text[:180]}",
                )
            ext = None
            try:
                ext = str((resp.json() or {}).get("id") or resp.status_code)
            except Exception:
                ext = str(resp.status_code)
            return PublishResult(True, self.platform, self.adapter, "live", external_id=ext)
        except httpx.HTTPError as exc:
            return PublishResult(False, self.platform, self.adapter, "live", error=f"webhook.network:{exc}")
