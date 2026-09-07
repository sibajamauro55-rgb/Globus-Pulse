from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pulse.db import init_db, session_scope  # noqa: E402
from pulse.engine import run_cycle  # noqa: E402
from pulse.models import Campaign, CycleLog, Piece, PublishJob  # noqa: E402
from pulse.settings import get_settings  # noqa: E402


def cmd_init(_: argparse.Namespace) -> int:
    settings = get_settings()
    init_db(settings)
    print(f"db lista: {settings.database_url}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    settings = get_settings()
    init_db(settings)
    result = run_cycle(settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    settings = get_settings()
    init_db(settings)
    with session_scope(settings) as session:
        pieces = session.query(Piece).order_by(Piece.created_at.desc()).limit(20).all()
        jobs = session.query(PublishJob).order_by(PublishJob.created_at.desc()).limit(20).all()
        print("PIEZAS")
        for p in pieces:
            print(f"  {p.status:12} {p.category:12} {p.platform:10} {p.headline[:60]}")
        print("JOBS")
        for j in jobs:
            print(f"  {j.status:12} {j.platform:10} attempts={j.attempt} err={j.error[:80]}")
        print("CICLOS")
        for c in session.query(CycleLog).order_by(CycleLog.started_at.desc()).limit(5):
            print(f"  gen={c.generated} pub={c.published} fail={c.failed} block={c.blocked}")
        camps = session.query(Campaign).all()
        print("CAMPAÑAS", [c.code for c in camps])
    return 0


def cmd_worker(_: argparse.Namespace) -> int:
    from apscheduler.schedulers.blocking import BlockingScheduler

    settings = get_settings()
    init_db(settings)

    def tick():
        print(json.dumps(run_cycle(settings), ensure_ascii=False))

    sched = BlockingScheduler(timezone=settings.timezone)
    sched.add_job(tick, "interval", hours=6, id="pulse-cycle", max_instances=1, coalesce=True)
    print(f"worker activo cada 6h tz={settings.timezone}")
    tick()
    sched.start()
    return 0


def cmd_serve(_: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("pulse.api:app", host="0.0.0.0", port=8088, reload=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="pulse", description="Globus-Pulse")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    p_run = sub.add_parser("run")
    p_run.set_defaults(fn=cmd_run)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("worker").set_defaults(fn=cmd_worker)
    sub.add_parser("serve").set_defaults(fn=cmd_serve)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
