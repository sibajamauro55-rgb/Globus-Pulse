from __future__ import annotations

from pulse.publishers.base import Publisher
from pulse.publishers.linkedin import LinkedInPublisher
from pulse.publishers.meta import FacebookPublisher, InstagramPublisher
from pulse.publishers.web import WebSitePublisher
from pulse.publishers.webhook import WebhookPublisher
from pulse.publishers.x import XPublisher
from pulse.settings import Settings


def build_registry(settings: Settings) -> dict[str, Publisher]:
    pubs: list[Publisher] = [
        WebhookPublisher(settings),
        WebSitePublisher(settings),
        XPublisher(settings),
        LinkedInPublisher(settings),
        InstagramPublisher(settings),
        FacebookPublisher(settings),
    ]
    return {p.platform: p for p in pubs}
