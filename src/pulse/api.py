from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import select

from pulse.db import init_db, session_scope
from pulse.engine import run_cycle
from pulse.models import CycleLog, Piece, PublishJob
from pulse.settings import get_settings

settings = get_settings()
init_db(settings)

app = FastAPI(title="Globus-Pulse", version="0.1.0")


@app.get("/health")
def health():
    return {"ok": True, "service": "globus-pulse"}


@app.get("/jobs")
def jobs():
    with session_scope(settings) as session:
        rows = session.scalars(select(PublishJob).order_by(PublishJob.created_at.desc()).limit(50)).all()
        return [
            {
                "id": j.id,
                "platform": j.platform,
                "status": j.status,
                "error": j.error,
                "external_id": j.external_id,
                "attempt": j.attempt,
            }
            for j in rows
        ]


@app.get("/pieces")
def pieces():
    with session_scope(settings) as session:
        rows = session.scalars(select(Piece).order_by(Piece.created_at.desc()).limit(50)).all()
        return [
            {
                "id": p.id,
                "status": p.status,
                "category": p.category,
                "headline": p.headline,
                "platform": p.platform,
                "asset_path": p.asset_path,
                "destination": p.destination,
            }
            for p in rows
        ]


@app.post("/cycle")
def cycle():
    return run_cycle(settings)


@app.get("/cycles")
def cycles():
    with session_scope(settings) as session:
        rows = session.scalars(select(CycleLog).order_by(CycleLog.started_at.desc()).limit(20)).all()
        return [
            {
                "id": c.id,
                "generated": c.generated,
                "published": c.published,
                "failed": c.failed,
                "blocked": c.blocked,
            }
            for c in rows
        ]
