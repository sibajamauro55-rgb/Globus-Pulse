from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

from pulse.publishers.base import PublishResult, Publisher
from pulse.settings import Settings

API_ROOT = "https://api.linkedin.com/rest"


class LinkedInPublisher(Publisher):
    platform = "linkedin"
    adapter = "linkedin_rest"

    def __init__(self, settings: Settings):
        self.settings = settings

    def ready(self) -> tuple[bool, str]:
        token = self.settings.linkedin_access_token
        author = self.settings.linkedin_author_urn
        if not token or not author:
            return False, "linkedin.credentials_missing"
        if not (author.startswith("urn:li:person:") or author.startswith("urn:li:organization:")):
            return False, "linkedin.author_urn_invalid"
        return True, ""

    def publish(self, payload: dict[str, Any], asset_path: Path | None) -> PublishResult:
        ok, reason = self.ready()
        if not ok:
            return PublishResult(False, self.platform, self.adapter, "blocked", error=reason)
        token = self.settings.linkedin_access_token
        author = self.settings.linkedin_author_urn
        version = self.settings.linkedin_api_version
        try:
            image_urn = None
            if asset_path and Path(asset_path).is_file():
                image_urn = self._upload(token, version, author, Path(asset_path))
            post_id = self._create_post(token, version, author, payload, image_urn)
        except LinkedInError as exc:
            return PublishResult(False, self.platform, self.adapter, "live", error=f"linkedin.http:{exc.code}:{exc.detail[:160]}")
        if not post_id:
            return PublishResult(False, self.platform, self.adapter, "live", error="linkedin.no_post_id")
        return PublishResult(True, self.platform, self.adapter, "live", external_id=post_id)

    def _headers(self, token: str, version: str, content_type: str | None = "application/json") -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Linkedin-Version": version,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _upload(self, token: str, version: str, owner: str, path: Path) -> str:
        raw, headers, status = _request(
            "POST",
            f"{API_ROOT}/images?action=initializeUpload",
            headers=self._headers(token, version),
            body=json.dumps({"initializeUploadRequest": {"owner": owner}}).encode(),
        )
        if status >= 400:
            raise LinkedInError(status, raw[:300])
        value = (json.loads(raw) or {}).get("value") or {}
        upload_url, image_urn = value.get("uploadUrl"), value.get("image")
        if not upload_url or not image_urn:
            raise LinkedInError(status, "initializeUpload incompleto")
        _, _, put_status = _request("PUT", upload_url, headers={"Authorization": f"Bearer {token}"}, body=path.read_bytes())
        if put_status >= 400:
            raise LinkedInError(put_status, "upload imagen falló")
        return str(image_urn)

    def _create_post(self, token: str, version: str, author: str, payload: dict[str, Any], image_urn: str | None) -> str | None:
        commentary = str(payload.get("caption") or payload.get("headline") or "")
        body: dict[str, Any] = {
            "author": author,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if image_urn:
            body["content"] = {
                "media": {
                    "id": image_urn,
                    "title": str(payload.get("headline") or "")[:200],
                    "altText": str(payload.get("headline") or "")[:200],
                }
            }
        raw, headers, status = _request(
            "POST",
            f"{API_ROOT}/posts",
            headers=self._headers(token, version),
            body=json.dumps(body).encode(),
        )
        if status != 201:
            raise LinkedInError(status, raw[:300] or "posts != 201")
        return headers.get("x-restli-id") or headers.get("X-RestLi-Id")


class LinkedInError(Exception):
    def __init__(self, code: int, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"{code} {detail}")


def _request(method: str, url: str, *, headers: dict[str, str], body: bytes | None) -> tuple[str, dict[str, str], int]:
    req = urlrequest.Request(url, data=body, method=method, headers=headers)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            return payload, {k.lower(): v for k, v in resp.headers.items()}, int(resp.status)
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return detail, {k.lower(): v for k, v in exc.headers.items()}, int(exc.code)
