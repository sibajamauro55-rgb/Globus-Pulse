from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from pulse.publishers.base import PublishResult, Publisher
from pulse.settings import Settings

GRAPH = "https://graph.facebook.com/v21.0"


class InstagramPublisher(Publisher):
    platform = "instagram"
    adapter = "instagram_graph"

    def __init__(self, settings: Settings):
        self.settings = settings

    def ready(self) -> tuple[bool, str]:
        if not self.settings.meta_access_token or not self.settings.instagram_business_id:
            return False, "instagram.credentials_missing"
        return True, ""

    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        ok, reason = self.ready()
        if not ok:
            return PublishResult(False, self.platform, self.adapter, "blocked", error=reason)
        image_url = payload.get("public_asset_url")
        if not image_url:
            return PublishResult(
                False,
                self.platform,
                self.adapter,
                "blocked",
                error="instagram.public_asset_url_required",
            )
        caption = str(payload.get("caption") or "")
        try:
            with httpx.Client(timeout=40.0) as client:
                container = client.post(
                    f"{GRAPH}/{self.settings.instagram_business_id}/media",
                    data={
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": self.settings.meta_access_token,
                    },
                )
                if container.status_code >= 400:
                    return PublishResult(
                        False,
                        self.platform,
                        self.adapter,
                        "live",
                        error=f"instagram.container_{container.status_code}:{container.text[:160]}",
                    )
                creation_id = (container.json() or {}).get("id")
                pub = client.post(
                    f"{GRAPH}/{self.settings.instagram_business_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": self.settings.meta_access_token},
                )
                if pub.status_code >= 400:
                    return PublishResult(
                        False,
                        self.platform,
                        self.adapter,
                        "live",
                        error=f"instagram.publish_{pub.status_code}:{pub.text[:160]}",
                    )
                return PublishResult(True, self.platform, self.adapter, "live", external_id=str((pub.json() or {}).get("id")))
        except httpx.HTTPError as exc:
            return PublishResult(False, self.platform, self.adapter, "live", error=f"instagram.network:{exc}")


class FacebookPublisher(Publisher):
    platform = "facebook"
    adapter = "facebook_page"

    def __init__(self, settings: Settings):
        self.settings = settings

    def ready(self) -> tuple[bool, str]:
        if not self.settings.meta_access_token or not self.settings.facebook_page_id:
            return False, "facebook.credentials_missing"
        return True, ""

    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        ok, reason = self.ready()
        if not ok:
            return PublishResult(False, self.platform, self.adapter, "blocked", error=reason)
        message = str(payload.get("caption") or payload.get("headline") or "")
        try:
            with httpx.Client(timeout=40.0) as client:
                if asset_path and Path(asset_path).is_file():
                    with open(asset_path, "rb") as fh:
                        resp = client.post(
                            f"{GRAPH}/{self.settings.facebook_page_id}/photos",
                            data={"caption": message, "access_token": self.settings.meta_access_token},
                            files={"source": fh},
                        )
                else:
                    resp = client.post(
                        f"{GRAPH}/{self.settings.facebook_page_id}/feed",
                        data={"message": message, "access_token": self.settings.meta_access_token},
                    )
            if resp.status_code >= 400:
                return PublishResult(
                    False, self.platform, self.adapter, "live", error=f"facebook.http_{resp.status_code}:{resp.text[:160]}"
                )
            return PublishResult(True, self.platform, self.adapter, "live", external_id=str((resp.json() or {}).get("id")))
        except httpx.HTTPError as exc:
            return PublishResult(False, self.platform, self.adapter, "live", error=f"facebook.network:{exc}")
