import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .models import ModelAdvisor
from .services import effective_constraints, fingerprint, critique
from .store import DomainError


class Orchestrator:
    def __init__(self, store):
        self.store = store
        self.advisor = ModelAdvisor(store)

    @asynccontextmanager
    async def gateway(self, sid):
        env = {**os.environ, "WORK2030_DB": self.store.path, "WORK2030_MCP_SESSION": sid}
        params = StdioServerParameters(command=sys.executable, args=["-m", "work2030.mcp_server"], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await asyncio.wait_for(client.initialize(), 15)
                yield client

    async def checkpoint(self, sid):
        while self.store.get(sid)["state"]["paused"]:
            await asyncio.sleep(.25)

    async def call(self, client, sid, name, args):
        await self.checkpoint(sid)
        self.store.event(sid, "tool.started", {"tool": name, "arguments": args})
        result = await asyncio.wait_for(client.call_tool(name, {"session_id": sid, "args": args}), 15)
        if result.isError:
            details = " ".join(c.text for c in result.content if hasattr(c, "text"))
            raise DomainError(details[:500])
        return json.loads(next(c.text for c in result.content if hasattr(c, "text")))

    async def prepare(self, sid, goal, provider="demo", alternative=False, focus=None):
        def save(s):
            s["goal"], s["provider"] = goal, provider
            s["proposal"] = None
            return {"goal": goal, "provider": provider}
        previous = self.store.get(sid)["state"].get("proposal")
        self.store.mutate(sid, "mission.started", save, snapshot=False)
        async with self.gateway(sid) as client:
            await self.call(client, sid, "Memory", {"query": "accessibilité budget planning lieu"})
            resources = await self.call(client, sid, "Resources", {})
            spaces = await self.call(client, sid, "Space", {})
            await self.call(client, sid, "Calendar", {})
            workspace = await self.call(client, sid, "Workspace", {})
            c = workspace["constraints"]
            available = {r["id"] for r in resources["items"] if r["available"]}
            displays = [d for d in ["led", "screen"] if d in available]
            base_ids = ["audio", "table-a", "table-b", "quiet", "signs"]
            if not displays or not set(base_ids).issubset(available):
                raise DomainError("Aucune solution : un équipement essentiel n'a pas d'alternative disponible")
            candidates = []
            for space in spaces["items"]:
                if not space["accessible"] or space["capacity"] < c["visitors"] or space["aisle_cm"] < c["aisle_cm"] or space["quiet_capacity"] < c["quiet_places"]:
                    continue
                for display in displays:
                    ids = [display, *base_ids]
                    budget = await self.call(client, sid, "Budget", {"space_id": space["id"], "resource_ids": ids})
                    if budget["total"] <= c["budget"]:
                        candidates.append({**space, "total": budget["total"], "resource_ids": ids})
                        break
            if alternative and previous:
                candidates = [s for s in candidates if s["id"] != previous["plan"]["space_id"]]
            if not candidates:
                raise DomainError("Aucun espace ne respecte ces contraintes. Modifiez le budget ou la fréquentation.")
            chosen, reason = await self.advisor.choose(sid, goal, candidates, provider)
            space = next(s for s in candidates if s["id"] == chosen)
            ids = space["resource_ids"]
            calm = min(space["quiet_capacity"], c["visitors"])
            stage = min(space["zones"][0]["capacity"], max(0, c["visitors"] - calm))
            occupancy = {"scene": stage, "atelier": c["visitors"] - calm - stage, "calme": calm}
            focus = focus or {}
            focus_ids = focus.get("resource_ids", [])
            focus_zone = focus.get("zone", "scene")
            if not isinstance(focus_ids, list) or not set(focus_ids).issubset(ids) or focus_zone not in occupancy:
                raise DomainError("Sélection visuelle incompatible avec la mission")
            if any(focus_zone not in r["allowed_zones"] for r in resources["items"] if r["id"] in focus_ids):
                raise DomainError("La zone sélectionnée ne convient pas aux ressources sélectionnées")
            if focus_ids:
                reason += f" Sélection visuelle : {', '.join(focus_ids)} seront affectés à {focus_zone}."
            plan = {"space_id": chosen, "resource_ids": ids, "occupancy": occupancy, "focus": {"resource_ids": focus_ids, "zone": focus_zone}}
            await self.call(client, sid, "Workspace", {"operation": "preview", "plan": plan, "reason": reason, "source": provider})

    async def execute(self, sid, proposal_id):
        baseline = self.store.capture(sid)
        try:
            async with self.gateway(sid) as client:
                def approve(s):
                    p = s["proposal"]
                    if not p or p["id"] != proposal_id or p["status"] != "pending":
                        raise DomainError("Proposition absente ou déjà traitée")
                    if p["fingerprint"] != fingerprint(s) or critique(s, p["plan"]):
                        raise DomainError("Proposition obsolète ou invalide")
                    p["status"] = "executing"
                    return {"proposal_id": proposal_id, "actor": "superviseur", "approved": True}
                # One snapshot covers all service mutations in this mission.
                self.store.mutate(sid, "decision.approved", approve)
                args = {"proposal_id": proposal_id}
                await self.call(client, sid, "Workspace", {**args, "operation": "apply"})
                await self.call(client, sid, "Calendar", {**args, "operation": "schedule"})
                await self.call(client, sid, "Documents", args)
                await self.call(client, sid, "Messaging", args)
                await self.call(client, sid, "Workspace", {**args, "operation": "complete"})
        except BaseException:
            self.store.restore(sid, baseline)
            raise
