import asyncio
import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .agent import Orchestrator
from .services import Services, effective_constraints, fingerprint, critique, find
from .store import Store, DomainError, ROOT

load_dotenv(ROOT / ".env")


class Action(BaseModel):
    action: str
    data: dict = Field(default_factory=dict)


class Mission(BaseModel):
    goal: str = Field(min_length=3, max_length=2000)
    provider: Literal["demo", "openai", "ollama"] = "demo"
    alternative: bool = False
    focus: dict = Field(default_factory=dict)


class Decision(BaseModel):
    proposal_id: str
    accept: bool


def create_app(store=None):
    db = store or Store()
    services = Services(db)
    agent = Orchestrator(db)
    tasks = {}

    @asynccontextmanager
    async def lifespan(app):
        db.seed_five()
        for g in db.list():
            if (g["state"].get("proposal") or {}).get("status") == "executing":
                db.undo(g["id"])
                db.event(g["id"], "mission.error", {"message": "Exécution interrompue par un redémarrage ; état restauré"})
        yield
        for t in tasks.values():
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks.values(), return_exceptions=True)

    app = FastAPI(title="WORK/2030", lifespan=lifespan)
    app.state.store = db
    app.state.tasks = tasks

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    def admin(request: Request):
        secret = os.getenv("ANIMATOR_TOKEN", "work2030-local")
        auth = request.headers.get("Authorization", "")
        if not secrets.compare_digest(auth, "Bearer " + secret):
            raise HTTPException(401, "Code animateur incorrect")

    def busy(sid):
        return sid in tasks and not tasks[sid].done()

    def idle(sid):
        db.get(sid)
        if busy(sid):
            raise DomainError("Une opération est en cours ; attendez ou utilisez pause/reset animateur")

    def view(sid):
        g = db.get(sid)
        g["active"] = busy(sid)
        g["effective_constraints"] = effective_constraints(g["state"])
        p = g["state"]["proposal"]
        g["proposal_stale"] = bool(p and p["status"] == "pending" and p["fingerprint"] != fingerprint(g["state"]))
        return g

    async def run(sid, coroutine):
        try:
            await coroutine
        except asyncio.CancelledError:
            db.event(sid, "mission.cancelled", {"message": "Exécution annulée"})
            raise
        except BaseException as e:
            # ExceptionGroup from MCP is unpacked without logging credentials.
            def message(exc):
                if isinstance(exc, BaseExceptionGroup):
                    return "; ".join(message(x) for x in exc.exceptions)
                return str(exc) if isinstance(exc, DomainError) else type(exc).__name__
            db.event(sid, "mission.error", {"message": message(e)[:1000]})
        finally:
            db.event(sid, "mission.idle", {})

    async def cancel(sid):
        if busy(sid):
            tasks[sid].cancel()
            await asyncio.gather(tasks[sid], return_exceptions=True)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0", "mode": "local", "sessions": len(db.list())}

    @app.get("/api/sessions")
    def groups():
        return [{"id": g["id"], "name": g["name"], "phase": g["state"]["phase"]} for g in db.list()]

    @app.get("/api/sessions/{sid}")
    def session(sid: str):
        return view(sid)

    @app.post("/api/sessions/{sid}/actions")
    def action(sid: str, body: Action):
        idle(sid)
        services.interact(sid, body.action, body.data)
        return view(sid)

    @app.get("/api/sessions/{sid}/memory")
    def memory(sid: str, q: str = ""):
        return services.call("Memory", sid, {"query": q[:500]})

    @app.post("/api/sessions/{sid}/mission", status_code=202)
    async def mission(sid: str, body: Mission):
        idle(sid)
        if db.get(sid)["state"]["paused"]:
            raise DomainError("Session en pause")
        tasks[sid] = asyncio.create_task(run(sid, agent.prepare(sid, body.goal, body.provider, body.alternative, body.focus)))
        return {"started": True}

    @app.post("/api/sessions/{sid}/decision", status_code=202)
    async def decision(sid: str, body: Decision):
        idle(sid)
        state = db.get(sid)["state"]
        p = state["proposal"]
        if not p or p["id"] != body.proposal_id or p["status"] != "pending":
            raise DomainError("Proposition absente ou déjà traitée")
        if body.accept:
            if state["paused"] or p["fingerprint"] != fingerprint(state) or critique(state, p["plan"]):
                raise DomainError("Proposition obsolète ou invalide. Vérifiez le contexte puis relancez.")
            tasks[sid] = asyncio.create_task(run(sid, agent.execute(sid, body.proposal_id)))
        else:
            def reject(s):
                s["proposal"]["status"] = "rejected"
                return {"proposal_id": body.proposal_id, "actor": "superviseur", "approved": False}
            db.mutate(sid, "decision.rejected", reject, snapshot=False)
        return {"accepted": body.accept}

    @app.post("/api/sessions/{sid}/undo")
    def undo(sid: str):
        idle(sid)
        db.undo(sid)
        return view(sid)

    @app.get("/api/sessions/{sid}/events")
    def events(sid: str, after: int = 0):
        return db.events(sid, after)

    @app.get("/api/sessions/{sid}/stream")
    async def stream(sid: str, request: Request, after: int = 0):
        db.get(sid)
        try:
            after = max(after, int(request.headers.get("last-event-id", "0")))
        except ValueError:
            raise HTTPException(400, "Curseur SSE invalide")
        async def generate():
            cursor = after
            ticks = 0
            while not await request.is_disconnected():
                rows = db.events(sid, cursor)
                for e in rows:
                    cursor = e["id"]
                    yield f"id: {cursor}\ndata: {json.dumps(e, ensure_ascii=False)}\n\n"
                ticks += 1
                if ticks % 20 == 0:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(.4)
        return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/api/sessions/{sid}/export")
    def export(sid: str):
        g = db.get(sid)
        s = g["state"]
        trace = db.events(sid)
        text = f"# WORK/2030 — {g['name']}\n\n## Résultats\n\nContexte : {len(s['context'])} sources. Affectations : {len(s['assignments'])}.\n\n"
        text += f"Mode : {s['provider']}. Les communications sont des brouillons fictifs.\n\n"
        text += "\n\n".join(d["content"] for d in s["documents"])
        text += "\n\n## Communications\n\n" + "\n\n".join(m["content"] for m in s["messages"])
        text += "\n\n## Trace et validations\n\n" + "\n".join(f"- {e['time']} · {e['kind']} · {json.dumps(e['payload'], ensure_ascii=False)}" for e in trace)
        return StreamingResponse(iter([text]), media_type="text/markdown", headers={"Content-Disposition": 'attachment; filename="work2030-resume.md"'})

    @app.get("/api/admin/sessions", dependencies=[Depends(admin)])
    def admin_sessions():
        return [view(g["id"]) for g in db.list()]

    @app.post("/api/admin/seed", dependencies=[Depends(admin)])
    def seed():
        db.seed_five()
        return admin_sessions()

    @app.post("/api/admin/{sid}/control", dependencies=[Depends(admin)])
    async def control(sid: str, body: Action):
        ids = [g["id"] for g in db.list()] if sid == "all" else [sid]
        for ident in ids:
            db.get(ident)
            if body.action == "reset":
                await cancel(ident)
                db.reset(ident)
            elif body.action == "pause":
                paused = bool(body.data.get("paused", True))
                db.mutate(ident, "facilitator.pause", lambda s: s.update(paused=paused) or {"paused": paused}, snapshot=False, allow_paused=True)
            elif body.action == "phase":
                phase = body.data.get("phase")
                if not isinstance(phase, int) or phase not in range(5):
                    raise DomainError("Séquence invalide")
                db.mutate(ident, "facilitator.phase", lambda s: s.update(phase=phase) or {"phase": phase}, snapshot=False, allow_paused=True)
            elif body.action == "perturb":
                await cancel(ident)
                def perturb(s):
                    find(s["resources"], "led")["available"] = False
                    s["perturbation"] = "Le mur LED est indisponible. Proposez une adaptation avec l'écran mobile."
                    return {"resource_id": "led", "message": s["perturbation"]}
                db.mutate(ident, "facilitator.perturbation", perturb, snapshot=False, allow_paused=True)
                state = db.get(ident)["state"]
                if not state["paused"]:
                    tasks[ident] = asyncio.create_task(run(ident, agent.prepare(ident, state["goal"] or "Adapter l'événement HORIZON", "demo")))
            else:
                raise DomainError("Commande animateur inconnue")
        return admin_sessions()

    dist = ROOT / "frontend/dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
        @app.get("/{path:path}")
        def frontend(path: str):
            if path.startswith("api/"):
                raise HTTPException(404)
            return FileResponse(dist / "index.html")
    return app


app = create_app()
