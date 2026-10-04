import asyncio
import pytest
from work2030.agent import Orchestrator
from work2030.services import Services
from work2030.store import DomainError


async def complete(store, sid):
    Services(store).interact(sid, "context", {"id": "m-access"})
    a = Orchestrator(store)
    await a.prepare(sid, "Préparer HORIZON sans modèle externe", "demo")
    p = store.get(sid)["state"]["proposal"]
    assert p["warnings"] == []
    assert p["budget"]["total"] == 5700
    assert store.get(sid)["state"]["documents"] == []
    await a.execute(sid, p["id"])
    return store.get(sid)["state"]


async def test_complete_mission_real_mcp_no_key_and_undo(store, session, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = await complete(store, session["id"])
    assert len(s["assignments"]) == 6
    assert len(s["documents"]) == len(s["messages"]) == 1
    assert len(s["schedule"]) == 4
    assert s["proposal"]["status"] == "completed"
    calls = {e["payload"]["tool"] for e in store.events(session["id"]) if e["kind"] == "tool.result"}
    assert calls == {"Memory", "Resources", "Space", "Calendar", "Budget", "Documents", "Messaging", "Workspace"}
    assert any(e["kind"] == "decision.approved" for e in store.events(session["id"]))
    store.undo(session["id"])
    assert store.get(session["id"])["state"]["documents"] == []
    assert store.get(session["id"])["state"]["assignments"] == {}


async def test_five_simultaneous_mcp_sessions_and_reset(store):
    groups = store.seed_five()
    states = await asyncio.gather(*(complete(store, g["id"]) for g in groups))
    assert len({s["documents"][0]["id"] for s in states}) == 5
    store.reset(groups[0]["id"])
    assert not store.get(groups[0]["id"])["state"]["documents"]
    assert all(len(store.get(g["id"])["state"]["documents"]) == 1 for g in groups[1:])


async def test_obsolete_proposal_rejected_after_context_change(store, session, services):
    sid = session["id"]
    services.interact(sid, "context", {"id": "m-access"})
    a = Orchestrator(store)
    await a.prepare(sid, "Préparer HORIZON")
    p = store.get(sid)["state"]["proposal"]
    services.interact(sid, "constraint", {"key": "budget", "value": 5500})
    with pytest.raises(BaseExceptionGroup):
        await a.execute(sid, p["id"])
    assert not store.get(sid)["state"]["documents"]


async def test_perturbation_and_alternative_respects_data(store, session, services):
    sid = session["id"]
    await complete(store, sid)
    def perturb(s):
        next(r for r in s["resources"] if r["id"] == "led")["available"] = False
    store.mutate(sid, "test.perturb", perturb)
    a = Orchestrator(store)
    await a.prepare(sid, "Adapter après perte LED")
    p = store.get(sid)["state"]["proposal"]
    assert "screen" in p["plan"]["resource_ids"] and "led" not in p["plan"]["resource_ids"]
    assert p["budget"]["total"] == 5370
    await a.prepare(sid, "Chercher une alternative", alternative=True)
    assert store.get(sid)["state"]["proposal"]["plan"]["space_id"] == "halle"


async def test_model_failure_is_not_silent_demo_success(store, session, services, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    services.interact(session["id"], "context", {"id": "m-access"})
    with pytest.raises(BaseExceptionGroup):
        await Orchestrator(store).prepare(session["id"], "Préparer HORIZON", "openai")
    assert store.get(session["id"])["state"]["proposal"] is None


async def test_mid_execution_failure_rolls_back_all_service_writes(store, session, services, monkeypatch):
    sid = session["id"]
    services.interact(sid, "context", {"id": "m-access"})
    a = Orchestrator(store)
    await a.prepare(sid, "Préparer HORIZON")
    p = store.get(sid)["state"]["proposal"]
    original = a.call
    async def fail(client, sid, name, args):
        if name == "Messaging":
            raise DomainError("Échec injecté")
        return await original(client, sid, name, args)
    monkeypatch.setattr(a, "call", fail)
    with pytest.raises(BaseExceptionGroup):
        await a.execute(sid, p["id"])
    s = store.get(sid)["state"]
    assert not s["documents"] and not s["assignments"] and not s["schedule"]
    assert any(e["kind"] == "mission.rollback" for e in store.events(sid))


async def test_visual_focus_controls_actual_assignment(store, session, services):
    sid = session["id"]
    services.interact(sid, "context", {"id": "m-access"})
    a = Orchestrator(store)
    await a.prepare(sid, "Implanter le support sélectionné", focus={"resource_ids": ["led"], "zone": "atelier"})
    p = store.get(sid)["state"]["proposal"]
    await a.execute(sid, p["id"])
    assert store.get(sid)["state"]["assignments"]["led"]["zone"] == "atelier"


async def test_lower_budget_can_switch_equipment_before_declaring_failure(store, session, services):
    sid = session["id"]
    services.interact(sid, "context", {"id": "m-access"})
    services.interact(sid, "constraint", {"key": "budget", "value": 4900})
    await Orchestrator(store).prepare(sid, "Préparer avec moins de budget")
    p = store.get(sid)["state"]["proposal"]
    assert p["plan"]["space_id"] == "halle" and "screen" in p["plan"]["resource_ids"]
    assert p["budget"]["total"] == 4870


async def test_mcp_client_is_bound_to_one_session(store, session):
    other = store.create("Other")["id"]
    async with Orchestrator(store).gateway(session["id"]) as client:
        result = await client.call_tool("Workspace", {"session_id": other, "args": {}})
        assert result.isError
