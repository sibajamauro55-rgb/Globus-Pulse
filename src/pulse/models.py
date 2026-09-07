from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class PieceStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    BLOCKED = "blocked"
    REJECTED = "rejected"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    BLOCKED = "blocked"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    pieces: Mapped[list["Piece"]] = relationship(back_populates="campaign")


class Piece(Base):
    __tablename__ = "pieces"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_piece_fingerprint"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    objective: Mapped[str] = mapped_column(String(40), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    format: Mapped[str] = mapped_column(String(40), nullable=False)
    template_code: Mapped[str] = mapped_column(String(60), nullable=False)
    frame_code: Mapped[str] = mapped_column(String(40), nullable=False)
    platform: Mapped[str] = mapped_column(String(40), nullable=False)
    headline: Mapped[str] = mapped_column(String(240), nullable=False)
    support: Mapped[str] = mapped_column(String(400), default="")
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(String(160), nullable=False)
    destination: Mapped[str] = mapped_column(String(400), nullable=False)
    hashtags: Mapped[str] = mapped_column(String(400), default="")
    script_json: Mapped[str] = mapped_column(Text, default="[]")
    asset_path: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default=PieceStatus.DRAFT.value)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    campaign: Mapped[Campaign] = relationship(back_populates="pieces")
    jobs: Mapped[list["PublishJob"]] = relationship(back_populates="piece")


class PublishJob(Base):
    __tablename__ = "publish_jobs"
    __table_args__ = (UniqueConstraint("piece_id", "platform", name="uq_job_piece_platform"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    piece_id: Mapped[str] = mapped_column(ForeignKey("pieces.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(40), nullable=False)
    adapter: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.SCHEDULED.value)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    external_id: Mapped[str] = mapped_column(String(200), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    piece: Mapped[Piece] = relationship(back_populates="jobs")


class CycleLog(Base):
    __tablename__ = "cycle_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated: Mapped[int] = mapped_column(Integer, default=0)
    published: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    blocked: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
