"""HTTP wire tests using a fake opener, never credentials or real requests."""
import json
from dataclasses import asdict

import pytest

from polymarket_alpha_lab import team_research_glm as glm
from polymarket_alpha_lab.team_research_agent import run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, TeamResearchTask
from datetime import UTC, datetime

TOKEN = "synthetic-model-token"
MESSAGES = '[{"role":"user","content":"Synthetic question"}]'


def client(**changes):
    args = dict(api_token=TOKEN, model="synthetic-function-model", allow_model_calls=True)
    args.update(changes)
    return glm.GLMResearchModel(**args)


def envelope(name="search_evidence", args=None, call_id="call-1"):
    return {"choices": [{"message": {"role": "assistant", "content": None,
              "tool_calls": [{"id": call_id, "type": "function", "function": {
                  "name": name, "arguments": json.dumps(args or {"query": "*"})}}]},
              "finish_reason": "tool_calls"}], "usage": {"total_tokens": 20}}


class Response:
    def __init__(self, raw, url=glm.ENDPOINT):
        self.raw = raw
        self.url = url
        self.limits = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def geturl(self):
        return self.url

    def read(self, size):
        self.limits.append(size)
        return self.raw[:size]


def fake_transport(monkeypatch, values):
    observed = []
    responses = [Response(json.dumps(value).encode() if isinstance(value, dict) else value) for value in values]
    handlers = []
    class Opener:
        def open(self, request, timeout):
            observed.append((request, timeout))
            return responses[len(observed) - 1]
    def build(*items):
        handlers.extend(items)
        return Opener()
    monkeypatch.setattr(glm, "build_opener", build)
    return observed, responses, handlers


def test_wire_contract_and_secret_isolation(monkeypatch):
    observed, responses, handlers = fake_transport(monkeypatch, [envelope()])
    model = client()
    reply = model.complete(messages_json=MESSAGES, max_output_tokens=128)
    request, timeout = observed[0]
    assert request.full_url == glm.ENDPOINT
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer " + TOKEN
    assert timeout == 20
    body = json.loads(request.data)
    assert body["max_tokens"] == 128
    assert body["tool_choice"] == "auto"
    assert body["stream"] is False
    assert body["thinking"] == {"type": "disabled"}
    assert len(body["tools"]) == 3
    assert TOKEN not in request.data.decode()
    assert TOKEN not in repr(model) and TOKEN not in repr(reply)
    with pytest.raises(TypeError):
        asdict(model)
    assert reply.total_tokens == 20
    assert reply.calls[0].name == "search_evidence"
    assert responses[0].limits == [glm.MAX_RESPONSE_BYTES + 1]
    assert responses[0].closed
    assert handlers[0].proxies == {}
    assert isinstance(handlers[1], glm._NoRedirect)
    assert handlers[1].redirect_request(None, None, 302, "redirect", {}, "https://example.invalid") is None


def test_disabled_client_cannot_construct_network_opener(monkeypatch):
    def forbidden(*args):
        pytest.fail("disabled model must not use network")
    monkeypatch.setattr(glm, "build_opener", forbidden)
    model = glm.GLMResearchModel(api_token=TOKEN, model="fixture")
    with pytest.raises(ValueError, match="disabled"):
        model.complete(messages_json=MESSAGES, max_output_tokens=128)


@pytest.mark.parametrize("defect", ("json", "oversize", "utf8", "choices", "stop", "length", "role",
                                    "calls", "type", "usage", "bool_usage", "string_usage", "arguments", "duplicate"))
def test_bad_provider_response_is_redacted(monkeypatch, defect):
    value = envelope()
    if defect == "json":
        value = b"synthetic-private-invalid-json"
    elif defect == "oversize":
        value = b"x" * (glm.MAX_RESPONSE_BYTES + 10)
    elif defect == "utf8":
        value = b"\xff"
    elif defect == "choices":
        value["choices"] = []
    elif defect in ("stop", "length"):
        value["choices"][0]["finish_reason"] = defect
    elif defect == "role":
        value["choices"][0]["message"]["role"] = "system"
    elif defect == "calls":
        value["choices"][0]["message"]["tool_calls"] = []
    elif defect == "type":
        value["choices"][0]["message"]["tool_calls"][0]["type"] = "custom"
    elif defect == "usage":
        del value["usage"]
    elif defect == "bool_usage":
        value["usage"]["total_tokens"] = True
    elif defect == "string_usage":
        value["usage"]["total_tokens"] = "20"
    elif defect == "arguments":
        value["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = {}
    elif defect == "duplicate":
        value = b'{"choices":[],"choices":[]}'
    observed, _, _ = fake_transport(monkeypatch, [value])
    with pytest.raises(ValueError) as error:
        client().complete(messages_json=MESSAGES, max_output_tokens=128)
    assert str(error.value) == "research model request failed"
    assert len(observed) == 1
    assert TOKEN not in str(error.value)


def test_network_failure_no_retry_no_exception_text(monkeypatch):
    calls = []
    class Opener:
        def open(self, *args, **kwargs):
            calls.append(1)
            raise RuntimeError(TOKEN)
    monkeypatch.setattr(glm, "build_opener", lambda *args: Opener())
    with pytest.raises(ValueError, match="research model request failed") as error:
        client().complete(messages_json=MESSAGES, max_output_tokens=128)
    assert calls == [1]
    assert TOKEN not in str(error.value)


def test_origin_change_is_rejected(monkeypatch):
    _, responses, _ = fake_transport(monkeypatch, [envelope()])
    responses[0].url = "https://example.invalid/redirect"
    with pytest.raises(ValueError, match="research model request failed"):
        client().complete(messages_json=MESSAGES, max_output_tokens=128)
    assert responses[0].limits == []


@pytest.mark.parametrize("changes", (
    {"api_token": ""}, {"api_token": "fixture\nheader"}, {"model": " "},
    {"timeout_seconds": 0}, {"timeout_seconds": True}, {"timeout_seconds": 61},
    {"allow_model_calls": 1},
))
def test_invalid_client_configuration(changes):
    with pytest.raises(ValueError):
        client(**changes)


def test_complete_runtime_against_fake_http_provider(monkeypatch):
    replies = [envelope(call_id="search"), envelope("read_evidence", {"source_id": "s"}, "read"),
               envelope("finish_research", {"probability_yes": "0.6", "confidence": "0.5",
                        "summary": "Synthetic result.", "source_ids": ["s"]}, "finish")]
    observed, _, _ = fake_transport(monkeypatch, replies)
    now = datetime(2026, 9, 12, tzinfo=UTC)
    evidence = ResearchEvidence("s", "crypto_eth", "c", "Synthetic title", "Synthetic text",
                                "https://example.invalid", now)
    task = TeamResearchTask("t", "crypto_eth", "c", "slug", "Synthetic?", "Synthetic rules", now, (evidence,))
    result = run_team_research_agent(task, model=client())
    assert result.status == "completed"
    assert result.total_tokens == 60
    assert len(observed) == 3
    final_messages = json.loads(observed[2][0].data)["messages"]
    assert final_messages[-1]["role"] == "tool"
    assert final_messages[-1]["tool_call_id"] == "read"
    assert "Synthetic text" in final_messages[-1]["content"]
