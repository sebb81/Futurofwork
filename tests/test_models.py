import json
import httpx
import pytest
from work2030.models import ModelAdvisor
from work2030.store import DomainError


@pytest.fixture
def model_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fictional-test-key")
    monkeypatch.setenv("API_SESSION_BUDGET_USD", ".2")
    monkeypatch.setenv("API_CALL_RESERVATION_USD", ".1")


async def test_model_tool_choice_is_validated_and_budget_reserved(store, session, monkeypatch, model_env):
    original = httpx.AsyncClient
    def reply(request):
        body = json.loads(request.content)
        assert body["max_tokens"] == 400
        assert body["tools"][0]["function"]["parameters"]["properties"]["space_id"]["enum"] == ["pavillon", "halle"]
        return httpx.Response(200, json={"choices": [{"message": {"tool_calls": [{"function": {"name": "select_venue", "arguments": '{"space_id":"halle","reason":"Budget plus sobre"}'}}]}}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(reply), **kw))
    choice, reason = await ModelAdvisor(store).choose(session["id"], "HORIZON", [{"id": "pavillon"}, {"id": "halle"}], "openai")
    assert choice == "halle"
    assert store.get(session["id"])["api_reserved_usd"] == .1
    assert "fictional-test-key" not in json.dumps(store.events(session["id"]))


@pytest.mark.parametrize("failure", ["timeout", "invalid_tool", "invalid_venue"])
async def test_model_failures_never_authorize_actions(store, session, monkeypatch, model_env, failure):
    original = httpx.AsyncClient
    def reply(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout")
        name = "delete_host" if failure == "invalid_tool" else "select_venue"
        return httpx.Response(200, json={"choices": [{"message": {"tool_calls": [{"function": {"name": name, "arguments": '{"space_id":"loft","reason":"ignored"}'}}]}}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(reply), **kw))
    with pytest.raises(DomainError):
        await ModelAdvisor(store).choose(session["id"], "HORIZON", [{"id": "pavillon"}], "openai")
    assert store.get(session["id"])["state"]["proposal"] is None
