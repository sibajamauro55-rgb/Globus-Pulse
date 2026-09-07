#!/usr/bin/env python3
"""Validación completa del flujo Pulse. No toca repos de Core."""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.chdir(ROOT)
os.environ["DATABASE_URL"] = "sqlite:////tmp/pulse-validate.db"
os.environ["ENABLED_PLATFORMS"] = "webhook,web,linkedin"
os.environ["AUTO_APPROVE"] = "true"
os.environ["PUBLISH_DUE"] = "true"
os.environ["GENERATE_PER_CYCLE"] = "1"
os.environ["WEBHOOK_TOKEN"] = "pulse-validate"

received: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            body = {"raw": raw.decode("utf-8", errors="replace")}
        received.append(body)
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"id": f"wh-{len(received)}"}).encode())

    def log_message(self, fmt, *args):
        return


def main() -> int:
    checks = []

    def ok(name: str, cond: bool, detail: str = ""):
        checks.append((name, cond, detail))
        mark = "PASS" if cond else "FAIL"
        print(f"[{mark}] {name} {detail}")

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    os.environ["WEBHOOK_URL"] = f"http://127.0.0.1:{port}/publish"

    from pulse.db import init_db, session_scope
    from pulse.engine import publish_due, run_cycle
    from pulse.models import Campaign, JobStatus, Piece, PublishJob
    from pulse.settings import Settings

    db_path = Path("/tmp/pulse-validate.db")
    if db_path.exists():
        db_path.unlink()

    settings = Settings()
    init_db(settings)

    result1 = run_cycle(settings)
    with session_scope(settings) as session:
        camp = session.query(Campaign).one()
        pieces = session.query(Piece).all()
        jobs = session.query(PublishJob).all()
        piece = pieces[0] if pieces else None
        asset_ok = bool(piece and piece.asset_path and Path(piece.asset_path).is_file() and Path(piece.asset_path).stat().st_size > 2000)
        webhook_jobs = [j for j in jobs if j.platform == "webhook"]
        web_jobs = [j for j in jobs if j.platform == "web"]
        li_jobs = [j for j in jobs if j.platform == "linkedin"]
        ok("1. se configura GLOBUS / campaña", camp.code == "always-on-globus", camp.code)
        ok("2. se genera una campaña", bool(camp.name), camp.name)
        ok("3. se genera contenido", bool(piece), piece.headline if piece else "")
        ok("4. se genera pieza visual real", asset_ok, piece.asset_path if piece else "")
        ok("5. se crea job de publicación", len(jobs) >= 2, f"jobs={len(jobs)}")
        ok(
            "6. publisher real con credenciales (webhook local)",
            bool(webhook_jobs) and webhook_jobs[0].status == JobStatus.PUBLISHED.value and received,
            webhook_jobs[0].external_id if webhook_jobs else "",
        )
        ok(
            "linkedin bloqueado sin credenciales (no fingido)",
            bool(li_jobs) and li_jobs[0].status == JobStatus.BLOCKED.value and "credentials" in (li_jobs[0].error or ""),
            li_jobs[0].error if li_jobs else "",
        )
        ok(
            "web bloqueado sin endpoint, payload staged",
            bool(web_jobs) and web_jobs[0].status == JobStatus.BLOCKED.value,
            web_jobs[0].error if web_jobs else "",
        )
        dest_ok = piece and "crear-propuesta" in piece.destination
        ok("contenido comercial con CTA de conversión", bool(dest_ok), piece.destination if piece else "")

    before = len(received)
    with session_scope(settings) as session:
        stats = publish_due(session, settings)
    ok("7. jobs idempotentes", len(received) == before and stats["published"] == 0, f"recv={len(received)} stats={stats}")

    with session_scope(settings) as session:
        statuses = {j.status for j in session.query(PublishJob).all()}
        piece_statuses = {p.status for p in session.query(Piece).all()}
    expected_job = {JobStatus.PUBLISHED.value, JobStatus.BLOCKED.value}
    ok("8. estados correctos", expected_job <= statuses, f"jobs={statuses} pieces={piece_statuses}")

    class Boom:
        platform = "webhook"
        adapter = "boom"

        def ready(self):
            return True, ""

        def publish(self, payload, asset_path):
            raise RuntimeError("boom")

    import pulse.engine as engine_mod

    original = engine_mod.build_registry

    def patched(settings_):
        r = original(settings_)
        r["webhook"] = Boom()
        return r

    engine_mod.build_registry = patched
    result2 = run_cycle(settings)
    engine_mod.build_registry = original
    ok("9. fallo de publicación no destruye el ciclo", "generated" in result2 and result2["failed"] >= 1, str(result2))

    result3 = run_cycle(settings)
    ok("10. el sistema vuelve a ejecutar el ciclo", result3["generated"] >= 1, str(result3))

    failed = [c for c in checks if not c[1]]
    print("\nRESUMEN", f"{len(checks) - len(failed)}/{len(checks)} pass")
    server.shutdown()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
