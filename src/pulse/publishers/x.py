from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from requests_oauthlib import OAuth1

from pulse.publishers.base import PublishResult, Publisher
from pulse.settings import Settings

TWEETS_URL = "https://api.x.com/2/tweets"
MEDIA_URL = "https://upload.twitter.com/1.1/media/upload.json"


class XPublisher(Publisher):
    platform = "x"
    adapter = "x_oauth1"

    def __init__(self, settings: Settings):
        self.settings = settings

    def ready(self) -> tuple[bool, str]:
        s = self.settings
        if not all([s.x_api_key, s.x_api_secret, s.x_access_token, s.x_access_token_secret]):
            return False, "x.credentials_missing"
        return True, ""

    def _auth(self) -> OAuth1:
        s = self.settings
        return OAuth1(s.x_api_key, s.x_api_secret, s.x_access_token, s.x_access_token_secret)

    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        ok, reason = self.ready()
        if not ok:
            return PublishResult(False, self.platform, self.adapter, "blocked", error=reason)
        text = str(payload.get("caption") or payload.get("headline") or "")
        media_id = None
        try:
            auth = self._auth()
            if asset_path and Path(asset_path).is_file():
                import requests

                with open(asset_path, "rb") as fh:
                    up = requests.post(MEDIA_URL, files={"media": fh}, auth=auth, timeout=40)
                if up.status_code >= 400:
                    return PublishResult(
                        False, self.platform, self.adapter, "live", error=f"x.media_{up.status_code}:{up.text[:160]}"
                    )
                media_id = (up.json() or {}).get("media_id_string")
            import requests

            body: dict[str, Any] = {"text": text}
            if media_id:
                body["media"] = {"media_ids": [media_id]}
            resp = requests.post(TWEETS_URL, json=body, auth=auth, timeout=30)
            if resp.status_code >= 400:
                return PublishResult(
                    False, self.platform, self.adapter, "live", error=f"x.http_{resp.status_code}:{resp.text[:180]}"
                )
            tweet_id = ((resp.json() or {}).get("data") or {}).get("id")
            return PublishResult(True, self.platform, self.adapter, "live", external_id=str(tweet_id or ""))
        except Exception as exc:
            return PublishResult(False, self.platform, self.adapter, "live", error=f"x.error:{exc}")
