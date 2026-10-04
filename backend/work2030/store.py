import copy
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data" / "horizon.json"


class DomainError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def initial_state():
    seed = json.loads(SEED.read_text())
    return {
        **seed, "phase": 0, "paused": False, "roles": 0, "context": [],
        "constraints": {"budget": 6000, "visitors": 120, "aisle_cm": 90, "quiet_places": 0},
        "space_id": "pavillon", "assignments": {}, "annotations": [], "documents": [],
        "messages": [], "schedule": [], "budget": None, "proposal": None,
        "recording": False, "recorded": [], "recipe": None, "last_replay": None,
        "perturbation": None, "goal": "", "provider": "demo", "generation": str(uuid.uuid4()),
    }


class Store:
    def __init__(self, path=None):
        self.path = str(path or os.getenv("WORK2030_DB", str(ROOT / "runtime/work2030.sqlite")))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, name TEXT NOT NULL,
              state TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0, spent REAL NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id TEXT NOT NULL, time TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS snapshots(id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id TEXT NOT NULL, state TEXT NOT NULL, label TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS event_session ON events(session_id,id);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def create(self, name):
        sid = str(uuid.uuid4())
        with self.lock, self.connect() as db:
            db.execute("INSERT INTO sessions(id,name,state) VALUES(?,?,?)", (sid, name, json.dumps(initial_state())))
            self._event(db, sid, "session.created", {"name": name})
        return self.get(sid)

    def seed_five(self):
        with self.lock:
            existing = self.list()
            if len(existing) > 5:
                raise DomainError("Maximum cinq groupes")
            for i in range(len(existing), 5):
                self.create(f"Trinôme {i + 1:02}")
        return self.list()

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT id FROM sessions ORDER BY rowid").fetchall()
        return [self.get(r["id"]) for r in rows]

    def get(self, sid):
        with self.connect() as db:
            r = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
            if not r:
                raise DomainError("Session introuvable")
            return {"id": r["id"], "name": r["name"], "revision": r["revision"],
                    "api_reserved_usd": r["spent"], "state": json.loads(r["state"])}

    def _event(self, db, sid, kind, payload):
        db.execute("INSERT INTO events(session_id,time,kind,payload) VALUES(?,?,?,?)",
                   (sid, now(), kind, json.dumps(payload, ensure_ascii=False)))

    def event(self, sid, kind, payload):
        with self.lock, self.connect() as db:
            self._event(db, sid, kind, payload)

    def events(self, sid, after=0):
        self.get(sid)
        with self.connect() as db:
            rows = db.execute("SELECT * FROM events WHERE session_id=? AND id>? ORDER BY id", (sid, after)).fetchall()
        return [{"id": r["id"], "time": r["time"], "kind": r["kind"], "payload": json.loads(r["payload"])} for r in rows]

    def mutate(self, sid, label, fn, snapshot=True, allow_paused=False):
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            r = db.execute("SELECT state FROM sessions WHERE id=?", (sid,)).fetchone()
            if not r:
                raise DomainError("Session introuvable")
            state = json.loads(r["state"])
            if state["paused"] and not allow_paused:
                raise DomainError("L'animateur a mis cette session en pause")
            result = fn(state)
            if snapshot:
                db.execute("INSERT INTO snapshots(session_id,state,label) VALUES(?,?,?)", (sid, r["state"], label))
            db.execute("UPDATE sessions SET state=?,revision=revision+1 WHERE id=?", (json.dumps(state), sid))
            self._event(db, sid, label, result if isinstance(result, dict) else {"result": result})
            return result

    def reset(self, sid):
        def reset(s):
            s.clear()
            s.update(initial_state())
            return {"message": "Jeu de données restauré"}
        self.mutate(sid, "session.reset", reset, snapshot=False, allow_paused=True)
        with self.lock, self.connect() as db:
            db.execute("DELETE FROM snapshots WHERE session_id=?", (sid,))
        # API reservations stay charged: resetting is not a way to bypass a spend cap.

    def undo(self, sid):
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            r = db.execute("SELECT * FROM snapshots WHERE session_id=? ORDER BY id DESC LIMIT 1", (sid,)).fetchone()
            if not r:
                raise DomainError("Aucune modification à restaurer")
            current = db.execute("SELECT state FROM sessions WHERE id=?", (sid,)).fetchone()
            if json.loads(current["state"])["paused"]:
                raise DomainError("Session en pause")
            state = json.loads(r["state"])
            state["proposal"] = None
            state["recording"] = False
            db.execute("UPDATE sessions SET state=?,revision=revision+1 WHERE id=?", (json.dumps(state), sid))
            db.execute("DELETE FROM snapshots WHERE id=?", (r["id"],))
            self._event(db, sid, "workspace.undo", {"restored": r["label"]})

    def reserve_api(self, sid, amount, cap):
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            r = db.execute("SELECT spent FROM sessions WHERE id=?", (sid,)).fetchone()
            if not r or r["spent"] + amount > cap or amount <= 0:
                raise DomainError("Plafond de réservation API atteint ; utilisez le mode démo")
            db.execute("UPDATE sessions SET spent=spent+? WHERE id=?", (amount, sid))

    def capture(self, sid):
        return copy.deepcopy(self.get(sid)["state"])

    def restore(self, sid, state, label="mission.rollback"):
        def restore(s):
            if s["generation"] != state["generation"]:
                raise DomainError("La session a été réinitialisée")
            paused = s["paused"]
            s.clear()
            s.update(copy.deepcopy(state))
            s["paused"] = paused
            return {"message": "État restauré", "reason": label}
        self.mutate(sid, label, restore, snapshot=False, allow_paused=True)
