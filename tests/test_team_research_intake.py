"""Scoped evidence intake and real research-loop integration, without I/O."""
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, ResearchEvidence, ResearchModelReply, ResearchToolCall,
)
from polymarket_alpha_lab.team_research_intake import (
    GammaMarketSnapshot, evidence_content_sha256, prepare_team_research_from_gamma,
)
from polymarket_alpha_lab.team_research_market_pipeline import (
    MarketTeamResearchRun, run_team_research_from_market_snapshot,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS

NOW = datetime(2026, 9, 12, 0, 0, tzinfo=UTC)


def market(**changes):
    value = {
        "conditionId": "fixture-condition", "slug": "fixture-market",
        "question": "Will the synthetic event happen?",
        "description": "Resolve YES only when the specified synthetic event is confirmed.",
        "active": True, "closed": False, "archived": False,
        "outcomes": '["Yes","No"]', "endDate": "2026-09-13T00:00:00Z",
        "updatedAt": "2026-09-11T23:59:00Z", "resolutionSource": "https://example.invalid/rules",
        "outcomePrices": '["0.99","0.01"]', "ignored": "SENTINEL-DO-NOT-SEND-RAW-PAYLOAD",
    }
    value.update(changes)
    return value


def snapshot(value=None, **changes):
    raw = json.dumps(market() if value is None else value).encode("utf-8")
    return replace(GammaMarketSnapshot("fixture-market", NOW, raw), **changes)


def evidence(team="crypto_eth", **changes):
    item = ResearchEvidence("source-1", team, "fixture-condition", "Synthetic source",
                            "Synthetic observation, not a real market fact.", "synthetic:source",
                            NOW - timedelta(seconds=60))
    return replace(item, **changes)


def prepare(snap=None, **changes):
    args = dict(task_id="fixture", team_id="crypto_eth", condition_id="fixture-condition",
                as_of=NOW, evidence=(evidence(),))
    args.update(changes)
    return prepare_team_research_from_gamma(snapshot() if snap is None else snap, **args)


class Model:
    def __init__(self):
        self.messages = []

    def complete(self, *, messages_json, max_output_tokens):
        messages = json.loads(messages_json)
        self.messages.append(messages)
        step = len(self.messages)
        if step == 1:
            name, args = "search_evidence", {"query": "*"}
        elif step == 2:
            name, args = "read_evidence", {"source_id": "source-1"}
        else:
            name, args = "finish_research", dict(probability_yes="0.6", confidence="0.5",
                summary="Synthetic cited result.", source_ids=["source-1"])
        return ResearchModelReply((ResearchToolCall(f"call-{step}", name, json.dumps(args)),), 5)


def run(snap=None, **changes):
    args = dict(task_id="fixture", team_id="crypto_eth", condition_id="fixture-condition",
                as_of=NOW, evidence=(evidence(),), model_factory=lambda _: Model())
    args.update(changes)
    return run_team_research_from_market_snapshot(snapshot() if snap is None else snap, **args)


@pytest.mark.parametrize("team", TEAM_IDS)
def test_all_ten_teams_intake_and_actual_agent_loop(team):
    model = Model()
    row = run(team_id=team, evidence=(evidence(team),), model_factory=lambda _: model)
    assert row.intake.status == "prepared"
    assert row.research.status == "completed"
    assert row.research.probability_yes == Decimal("0.6")
    assert row.research.tool_trace == ("search_evidence", "read_evidence", "finish_research")
    assert row.research.total_tokens == 15
    assert row.intake.task.question == market()["question"]
    assert row.intake.task.resolution_criteria == market()["description"]
    assert row.intake.task.evidence == (evidence(team),)
    transcript = json.dumps(model.messages)
    assert "SENTINEL-DO-NOT-SEND-RAW-PAYLOAD" not in transcript
    assert "outcomePrices" not in transcript
    assert "https://example.invalid/rules" not in transcript
    assert "Synthetic observation" in transcript
    assert row.intake.market_content_sha256 == sha256(snapshot().raw_json).hexdigest()
    for obj in (row, row.intake, row.intake.task, row.research, *row.intake.source_receipts):
        assert obj.paper_only is obj.report_only is obj.readonly is True


@pytest.mark.parametrize("outcomes", ('["Yes","No"]', '["No","Yes"]', ["yes", "NO"]))
def test_binary_order_never_reorients_probability(outcomes):
    row = run(snapshot(market(outcomes=outcomes)))
    assert row.research.probability_yes == Decimal("0.6")


@pytest.mark.parametrize(("changes", "reason"), (
    ({"conditionId": "other"}, "market_identity_mismatch"),
    ({"slug": "other-market"}, "market_identity_mismatch"),
    ({"active": False}, "market_not_open"), ({"active": 1}, "market_not_open"),
    ({"active": "true"}, "market_not_open"), ({"closed": True}, "market_not_open"),
    ({"closed": None}, "market_not_open"), ({"closed": 0}, "market_not_open"),
    ({"archived": True}, "market_not_open"), ({"archived": None}, "market_not_open"),
    ({"outcomes": '["Up","Down"]'}, "unsupported_market_outcomes"),
    ({"outcomes": '["Yes","No","Other"]'}, "unsupported_market_outcomes"),
    ({"outcomes": '["Yes","Yes"]'}, "unsupported_market_outcomes"),
    ({"outcomes": '[true,false]'}, "unsupported_market_outcomes"),
    ({"outcomes": None}, "unsupported_market_outcomes"),
    ({"outcomes": '{"a":1,"a":2}'}, "unsupported_market_outcomes"),
    ({"outcomes": '[" Yes","No"]'}, "unsupported_market_outcomes"),
    ({"question": ""}, "invalid_market_payload"),
    ({"question": None}, "invalid_market_payload"),
    ({"question": "x" * 2001}, "invalid_market_payload"),
    ({"description": ""}, "missing_resolution_criteria"),
    ({"description": None}, "missing_resolution_criteria"),
    ({"description": "x" * 4001}, "missing_resolution_criteria"),
    ({"description": "embedded\x00text"}, "missing_resolution_criteria"),
    ({"endDate": None}, "invalid_market_time"),
    ({"endDate": "2026-09-13"}, "invalid_market_time"),
    ({"endDate": "2026-09-13T00:00:00"}, "invalid_market_time"),
    ({"endDate": "not-a-date"}, "invalid_market_time"),
    ({"endDate": "2026-09-12T00:00:00Z"}, "market_already_ended"),
    ({"endDate": "2026-09-11T00:00:00Z"}, "market_already_ended"),
    ({"updatedAt": "2026-09-12T00:00:01Z"}, "invalid_market_time"),
    ({"updatedAt": "2026-09-11"}, "invalid_market_time"),
))
def test_unsafe_market_context_blocks_before_factory(changes, reason):
    calls = []
    row = run(snapshot(market(**changes)), model_factory=lambda _: calls.append(1))
    assert row.intake.status == "blocked"
    assert row.intake.reason_code == reason
    assert row.intake.task is None and row.intake.source_receipts == ()
    assert row.research is None and calls == []
    assert "SENTINEL" not in repr(row)


@pytest.mark.parametrize("raw", (b"[]", b"null", b"true", b"not-json", b"\xff",
    b'{"a":1,"a":2}', b'{"value":NaN}', b'{"value":Infinity}', b'"string"'))
def test_invalid_raw_payloads_are_blocked(raw):
    row = prepare(snapshot(raw_json=raw))
    assert row.reason_code == "invalid_market_payload"


@pytest.mark.parametrize("key", ("conditionId", "slug", "question", "description", "active", "closed", "endDate", "outcomes"))
def test_missing_required_context_field_never_prepares(key):
    value = market()
    del value[key]
    assert prepare(snapshot(value)).status == "blocked"


def test_optional_metadata_and_old_update_time_not_retrieval_freshness():
    value = market()
    del value["archived"]
    del value["resolutionSource"]
    value["updatedAt"] = "2020-01-01T00:00:00Z"
    assert prepare(snapshot(value)).status == "prepared"
    value["updatedAt"] = None
    assert prepare(snapshot(value)).status == "prepared"


@pytest.mark.parametrize(("delta", "status", "reason"), (
    (timedelta(seconds=1), "blocked", "market_context_from_future"),
    (-timedelta(seconds=301), "blocked", "market_context_stale"),
    (-timedelta(seconds=300), "prepared", "research_intake_prepared"),
    (timedelta(0), "prepared", "research_intake_prepared"),
))
def test_retrieval_time_boundary(delta, status, reason):
    snap = snapshot(market(updatedAt=None), fetched_at=NOW + delta)
    intake = prepare(snap)
    assert (intake.status, intake.reason_code) == (status, reason)


def test_newly_fetched_context_cannot_be_used_for_earlier_as_of():
    row = run(as_of=NOW - timedelta(seconds=1))
    assert row.intake.reason_code == "market_context_from_future"
    assert row.research is None


def test_market_description_and_prices_cannot_substitute_for_evidence():
    calls = []
    row = run(evidence=(), model_factory=lambda _: calls.append(1))
    assert row.intake.reason_code == "no_eligible_evidence"
    assert row.research is None and calls == []


def test_stale_and_future_evidence_filtered_and_receipts_only_cover_eligible_sources():
    fresh = evidence()
    boundary = evidence(source_id="boundary", observed_at=NOW - timedelta(days=1))
    stale = evidence(source_id="stale", observed_at=NOW - timedelta(days=1, microseconds=1))
    future = evidence(source_id="future", observed_at=NOW + timedelta(microseconds=1))
    row = prepare(evidence=(fresh, stale, future, boundary))
    assert row.task.evidence == (fresh, boundary)
    assert row.stale_source_ids == ("stale",) and row.future_source_ids == ("future",)
    assert tuple(item.source_id for item in row.source_receipts) == ("source-1", "boundary")
    for item, receipt in zip(row.task.evidence, row.source_receipts, strict=True):
        assert receipt.content_sha256 == evidence_content_sha256(item)
        assert receipt.reference == item.reference
    assert prepare(evidence=(stale, future)).reason_code == "no_eligible_evidence"


def test_shared_evidence_age_limit_is_applied_before_model_and_in_runtime():
    row = run(limits=ResearchAgentLimits(max_evidence_age_seconds=59))
    assert row.intake.reason_code == "no_eligible_evidence"
    assert row.research is None


@pytest.mark.parametrize("change", ({"team_id": "crypto_btc"}, {"condition_id": "other"}))
def test_cross_scope_sources_rejected_before_model(change):
    calls = []
    with pytest.raises(ValueError):
        run(evidence=(evidence(**change),), model_factory=lambda _: calls.append(1))
    assert calls == []


def test_duplicate_source_ids_rejected():
    with pytest.raises(ValueError):
        prepare(evidence=(evidence(), evidence()))


def test_snapshot_and_evidence_copy_resist_caller_mutation_during_factory():
    item = evidence()
    snap = snapshot()
    def factory(_):
        object.__setattr__(item, "text", "CHANGED-AFTER-INTAKE")
        object.__setattr__(snap, "raw_json", b"{}")
        return Model()
    row = run(snap, evidence=(item,), model_factory=factory)
    assert row.research.status == "completed"
    assert row.intake.task.evidence[0].text != item.text
    assert row.intake.market_content_sha256 != snap.content_sha256
    with pytest.raises(FrozenInstanceError):
        row.intake.status = "ready"


@pytest.mark.parametrize("field", ("paper_only", "report_only", "readonly"))
def test_hard_flags_revalidated_on_corrupted_inputs(field):
    snap = snapshot()
    object.__setattr__(snap, field, False)
    with pytest.raises(ValueError):
        prepare(snap)
    item = evidence()
    object.__setattr__(item, field, False)
    with pytest.raises(ValueError):
        prepare(evidence=(item,))


@pytest.mark.parametrize("slug", ("", "../x", "https://example.invalid", "x?y=1", "%2f", "x/y", "X", "a_b", "-x", "x-", "x--y", "x"*201))
def test_invalid_slugs(slug):
    with pytest.raises(ValueError):
        snapshot(market_slug=slug)


@pytest.mark.parametrize("changes", ({"raw_json": b""}, {"raw_json": "{}"}, {"raw_json": b"x" * 1048577},
                                     {"fetched_at": NOW.replace(tzinfo=None)}, {"readonly": 1}))
def test_invalid_snapshot_contract(changes):
    with pytest.raises(ValueError):
        snapshot(**changes)


@pytest.mark.parametrize("value", (-1, True, 86401, "300"))
def test_invalid_context_age_limit(value):
    with pytest.raises(ValueError):
        prepare(max_context_age_seconds=value)


def test_record_hash_binds_content_scope_and_provenance():
    item = evidence()
    original = evidence_content_sha256(item)
    for changes in ({"text": "Different observation"}, {"title": "Other title"},
                    {"reference": "synthetic:other"}, {"condition_id": "other"},
                    {"team_id": "macro_rates"}, {"observed_at": NOW}, {"source_id": "other"}):
        assert evidence_content_sha256(replace(item, **changes)) != original
    equivalent = replace(item, observed_at=item.observed_at.astimezone(timezone(timedelta(hours=8))))
    assert evidence_content_sha256(equivalent) == original


def test_forged_source_receipt_and_intake_rejected():
    row = prepare()
    bad_receipt = replace(row.source_receipts[0], content_sha256="0" * 64)
    for changes in ({"source_receipts": (bad_receipt,)}, {"condition_id": "other"},
                    {"status": "blocked"}, {"status": "ready"}, {"task": None},
                    {"stale_source_ids": ("source-1",)}, {"paper_only": False}):
        with pytest.raises(ValueError):
            replace(row, **changes)


def test_factory_failure_and_invalid_client_isolation(capsys):
    def factory(_):
        raise RuntimeError("synthetic-sensitive-error")
    for callback in (factory, lambda _: object()):
        row = run(model_factory=callback)
        assert row.research.status == "failed"
        assert row.research.reason_code == "model_factory_failed"
        assert row.research.model_calls == 0
        assert "synthetic-sensitive-error" not in repr(row)
    assert capsys.readouterr() == ("", "")


def test_run_cannot_mix_blocked_intake_or_other_market_result():
    row = run()
    with pytest.raises(ValueError):
        replace(row, research=replace(row.research, condition_id="other"))
    with pytest.raises(ValueError):
        MarketTeamResearchRun(prepare(evidence=()), row.research)
    with pytest.raises(ValueError):
        replace(row, research=replace(row.research, source_ids=("invented",)))
