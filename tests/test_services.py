import pytest
from work2030.store import DomainError, Store
from work2030.services import fingerprint, effective_constraints, critique


def test_memory_provenance_and_context_removal(store, session, services):
    sid = session["id"]
    result = services.memory(sid, {"query": "contrainte accessibilité"})
    assert result["items"][0]["id"] == "m-access"
    assert result["items"][0]["evidence"] == "retrouvée"
    assert result["items"][0]["source"]
    services.interact(sid, "context", {"id": "m-access"})
    assert effective_constraints(store.get(sid)["state"])["aisle_cm"] == 140
    services.interact(sid, "context", {"id": "m-access", "enabled": False})
    assert effective_constraints(store.get(sid)["state"])["aisle_cm"] == 90
    with pytest.raises(DomainError, match="obsolète"):
        services.interact(sid, "context", {"id": "m-access-old"})


def test_semantic_recording_replay_atomicity_and_undo(store, session, services):
    sid = session["id"]
    services.interact(sid, "record_start", {})
    services.interact(sid, "assign", {"id": "table-a", "zone": "atelier", "start": "09:00", "end": "12:00"})
    services.interact(sid, "assign", {"id": "table-a", "zone": "atelier", "start": "10:00", "end": "12:00"})
    recipe = services.interact(sid, "record_finish", {})
    assert recipe["variable"] == "resource_id"
    assert len(recipe["steps"]) == 2
    with pytest.raises(DomainError):
        services.interact(sid, "replay", {"ids": ["table-b", "audio"]})
    assert "table-b" not in store.get(sid)["state"]["assignments"]
    services.interact(sid, "replay", {"ids": ["table-b"]})
    assert store.get(sid)["state"]["assignments"]["table-b"]["start"] == "10:00"
    store.undo(sid)
    assert "table-b" not in store.get(sid)["state"]["assignments"]


@pytest.mark.parametrize("data", [
    {"id": "audio", "zone": "calme"},
    {"id": "table-a", "zone": "atelier", "start": "12:00", "end": "09:00"},
    {"id": "table-a", "zone": "atelier", "start": "07:00", "end": "09:00"},
])
def test_constraints_enforced(session, services, data):
    with pytest.raises(DomainError):
        services.interact(session["id"], "assign", data)


def test_service_mutations_require_approval(session, services):
    for service, args in [("Documents", {}), ("Messaging", {}), ("Calendar", {"operation": "schedule"}), ("Workspace", {"operation": "apply"})]:
        with pytest.raises(DomainError, match="Validation humaine"):
            services.call(service, session["id"], args)


def test_print_card_and_five_isolated_persistent_sessions(store, services):
    groups = store.seed_five()
    assert len(groups) == 5
    sid = groups[0]["id"]
    services.interact(sid, "card", {"code": "ACCES140"})
    services.interact(sid, "card", {"code": "BUDGET5500"})
    assert store.get(sid)["state"]["constraints"]["budget"] == 5500
    assert all(not store.get(g["id"])["state"]["context"] for g in groups[1:])
    reopened = Store(store.path)
    assert reopened.get(sid)["state"]["context"] == ["m-access"]
    store.reset(sid)
    assert not store.get(sid)["state"]["context"]
    assert any(e["kind"] == "session.reset" for e in store.events(sid))


def test_critic_uses_actual_capacity_and_missing_context(store, session, services):
    s = store.get(session["id"])["state"]
    plan = {"space_id": "halle", "resource_ids": ["led", "audio", "table-a", "table-b", "quiet", "signs"], "occupancy": {"scene": 50, "atelier": 58, "calme": 12}}
    warnings = critique(s, plan)
    assert any("Fabrique" in w for w in warnings)
    assert any("contexte actif" in w for w in warnings)


def test_api_budget_not_bypassed_by_reset(store, session):
    sid = session["id"]
    store.reserve_api(sid, .1, .15)
    store.reset(sid)
    with pytest.raises(DomainError, match="Plafond"):
        store.reserve_api(sid, .1, .15)
