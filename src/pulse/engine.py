from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from pulse.angles import ANGLES, CATEGORY_TO_ANGLES, Angle
from pulse.brand import Brand, load_brand
from pulse.calendar import load_calendar, next_slot, plan_for
from pulse.copywrite import caption_for, fingerprint, hashtags, script_dumps
from pulse.frames import frame_for
from pulse.models import Campaign, CycleLog, JobStatus, Piece, PieceStatus, PublishJob, new_id, utcnow
from pulse.publishers.registry import build_registry
from pulse.render import render_piece
from pulse.settings import Settings, get_settings
from pulse.validate import validate_piece


def as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


TEMPLATE_KICKER = {
    "service_ad": "SERVICIO",
    "problem_solution": "PROBLEMA",
    "tip": "TIP",
    "stat": "DATO",
    "benefit": "BENEFICIO",
    "use_case": "CASO",
    "cta": "ACCIÓN",
    "promo": "PROPUESTA",
    "compare": "ANTES / DESPUÉS",
    "educate": "SISTEMA",
    "institutional": "GLOBUS",
}


def ensure_campaign(session: Session, cal: dict) -> Campaign:
    spec = cal.get("campaign") or {}
    code = spec.get("code") or "always-on-globus"
    existing = session.scalar(select(Campaign).where(Campaign.code == code))
    if existing:
        return existing
    camp = Campaign(
        id=new_id(),
        code=code,
        name=spec.get("name") or "Presencia continua Globus",
        objective=spec.get("objective") or "Conseguir prospectos",
    )
    session.add(camp)
    session.flush()
    return camp


def pick_angle(session: Session, categories: list[str]) -> Angle:
    pool: list[Angle] = []
    for cat in categories:
        pool.extend(CATEGORY_TO_ANGLES.get(cat, []))
    pool.extend(ANGLES)
    seen_ids: set[str] = set()
    ordered: list[Angle] = []
    for a in pool:
        if a.id not in seen_ids:
            seen_ids.add(a.id)
            ordered.append(a)
    counts = dict(session.execute(select(Piece.category, func.count()).group_by(Piece.category)).all())
    ordered.sort(key=lambda a: counts.get(a.category, 0))
    for angle in ordered:
        recent = session.scalar(
            select(func.count()).where(Piece.template_code == angle.template, Piece.headline == angle.headline)
        )
        if not recent:
            return angle
    return ordered[0]


def generate_one(session: Session, settings: Settings, brand: Brand, cal: dict, campaign: Campaign) -> Piece | None:
    when = next_slot(session, cal)
    plan = plan_for(cal, when)
    platforms = settings.platforms()
    if not platforms:
        return None
    platform = platforms[0]
    fmt = plan["formats"][0]
    slot_key = when.strftime("%Y-%m-%d-%H%M%S")
    angle = pick_angle(session, plan["categories"])
    fp = fingerprint(campaign.code, angle.id, platform, slot_key)
    if session.scalar(select(Piece).where(Piece.fingerprint == fp)):
        return None

    frame = frame_for(platform, fmt)
    caption = caption_for(brand, angle, platform)
    tags = hashtags(brand, platform)
    piece = Piece(
        id=new_id(),
        campaign_id=campaign.id,
        fingerprint=fp,
        objective=angle.objective,
        category=angle.category,
        format=fmt if fmt != "banner" else "banner",
        template_code=angle.template,
        frame_code=frame.code,
        platform=platform,
        headline=angle.headline,
        support=angle.support,
        caption=caption,
        cta=brand.primary_cta,
        destination=brand.conversion_url,
        hashtags=" ".join(tags),
        script_json=script_dumps(brand, angle),
        status=PieceStatus.DRAFT.value,
        scheduled_at=when,
    )
    session.add(piece)
    session.flush()

    asset = settings.assets_dir / piece.id / f"{frame.code}.png"
    render_piece(
        brand,
        frame=frame,
        template_code=angle.template,
        kicker=TEMPLATE_KICKER.get(angle.template, "GLOBUS"),
        headline=angle.headline,
        support=angle.support,
        cta=brand.primary_cta,
        destination=brand.conversion_url,
        out_path=asset,
    )
    piece.asset_path = str(asset)
    piece.status = PieceStatus.GENERATED.value

    errors = validate_piece(
        brand,
        headline=piece.headline,
        caption=piece.caption,
        cta=piece.cta,
        destination=piece.destination,
        asset_path=piece.asset_path,
        platform=piece.platform,
    )
    if errors:
        piece.status = PieceStatus.REJECTED.value
        session.flush()
        return piece

    if settings.auto_approve:
        piece.status = PieceStatus.APPROVED.value

    for plat in platforms:
        job = PublishJob(
            id=new_id(),
            piece_id=piece.id,
            platform=plat,
            adapter=plat,
            status=JobStatus.SCHEDULED.value,
            scheduled_at=when if when.tzinfo else when.replace(tzinfo=timezone.utc),
        )
        session.add(job)
    piece.status = PieceStatus.SCHEDULED.value
    session.flush()
    return piece


def _payload(piece: Piece) -> dict:
    return {
        "id": piece.id,
        "headline": piece.headline,
        "support": piece.support,
        "caption": piece.caption,
        "cta": piece.cta,
        "destination": piece.destination,
        "category": piece.category,
        "format": piece.format,
        "platform": piece.platform,
        "hashtags": piece.hashtags.split(),
        "script": piece.script_json,
    }


def _sync_piece_status(session: Session, piece: Piece) -> None:
    jobs = session.scalars(select(PublishJob).where(PublishJob.piece_id == piece.id)).all()
    states = {j.status for j in jobs}
    if JobStatus.PUBLISHED.value in states:
        piece.status = PieceStatus.PUBLISHED.value
    elif JobStatus.PUBLISHING.value in states:
        piece.status = PieceStatus.PUBLISHING.value
    elif JobStatus.FAILED.value in states:
        piece.status = PieceStatus.FAILED.value
    elif states and states <= {JobStatus.BLOCKED.value}:
        piece.status = PieceStatus.BLOCKED.value
    elif JobStatus.SCHEDULED.value in states:
        piece.status = PieceStatus.SCHEDULED.value


def publish_due(session: Session, settings: Settings) -> dict[str, int]:
    registry = build_registry(settings)
    now = utcnow()
    candidates = session.scalars(
        select(PublishJob).where(
            PublishJob.status.in_([JobStatus.SCHEDULED.value, JobStatus.FAILED.value]),
        )
    ).all()
    jobs = [j for j in candidates if as_utc(j.scheduled_at) is not None and as_utc(j.scheduled_at) <= now]
    stats = {"published": 0, "failed": 0, "blocked": 0, "skipped": 0}
    for job in jobs:
        claimed = session.execute(
            update(PublishJob)
            .where(
                PublishJob.id == job.id,
                PublishJob.status.in_([JobStatus.SCHEDULED.value, JobStatus.FAILED.value]),
            )
            .values(status=JobStatus.PUBLISHING.value, attempt=PublishJob.attempt + 1)
        )
        session.flush()
        if claimed.rowcount != 1:
            stats["skipped"] += 1
            continue
        current = session.get(PublishJob, job.id)
        if current is None:
            stats["skipped"] += 1
            continue

        piece = session.get(Piece, current.piece_id)
        if piece is None:
            current.status = JobStatus.FAILED.value
            current.error = "piece_missing"
            stats["failed"] += 1
            continue
        piece.status = PieceStatus.PUBLISHING.value
        publisher = registry.get(current.platform)
        if publisher is None:
            current.status = JobStatus.BLOCKED.value
            current.error = "adapter_missing"
            piece.status = PieceStatus.BLOCKED.value
            stats["blocked"] += 1
            continue
        asset = Path(piece.asset_path) if piece.asset_path else None
        try:
            result = publisher.publish(_payload(piece), asset)
        except Exception as exc:
            current.status = JobStatus.FAILED.value
            current.error = f"publisher.crash:{exc}"
            piece.status = PieceStatus.FAILED.value
            stats["failed"] += 1
            session.flush()
            continue
        if result.ok:
            current.status = JobStatus.PUBLISHED.value
            current.external_id = result.external_id or ""
            current.error = ""
            current.published_at = utcnow()
            stats["published"] += 1
        elif result.mode == "blocked":
            current.status = JobStatus.BLOCKED.value
            current.error = result.error or "blocked"
            stats["blocked"] += 1
        else:
            current.status = JobStatus.FAILED.value
            current.error = result.error or "publish_failed"
            stats["failed"] += 1
        _sync_piece_status(session, piece)
        session.flush()
    return stats


def run_cycle(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    brand = load_brand(settings.brand_file)
    cal = load_calendar(settings.calendar_file)
    from pulse.db import session_scope

    notes = []
    generated = published = failed = blocked = 0
    with session_scope(settings) as session:
        log = CycleLog(id=new_id())
        session.add(log)
        session.flush()
        campaign = ensure_campaign(session, cal)
        for _ in range(max(1, settings.generate_per_cycle)):
            piece = generate_one(session, settings, brand, cal, campaign)
            if piece and piece.status != PieceStatus.REJECTED.value:
                generated += 1
            elif piece and piece.status == PieceStatus.REJECTED.value:
                notes.append(f"rejected:{piece.id}")
        if settings.publish_due:
            for job in session.scalars(select(PublishJob).where(PublishJob.status == JobStatus.SCHEDULED.value)):
                if as_utc(job.scheduled_at) and as_utc(job.scheduled_at) > utcnow():
                    job.scheduled_at = utcnow()
            session.flush()
            stats = publish_due(session, settings)
            published = stats["published"]
            failed = stats["failed"]
            blocked = stats["blocked"]
        log.generated = generated
        log.published = published
        log.failed = failed
        log.blocked = blocked
        log.finished_at = utcnow()
        log.notes = "; ".join(notes)
        session.flush()
        return {
            "campaign": campaign.code,
            "generated": generated,
            "published": published,
            "failed": failed,
            "blocked": blocked,
            "notes": notes,
        }
