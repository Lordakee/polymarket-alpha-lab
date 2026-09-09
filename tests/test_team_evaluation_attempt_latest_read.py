"""Offline red-batch behavior tests for the Node 8 latest-attempt read module.

Governing plan: docs/superpowers/plans/2026-09-09-team-evaluation-attempt-latest-read.md
(Red/Green items 1-3 plus the Projection And Fail-Closed Contract). The
production module ``src/polymarket_alpha_lab/team_evaluation_attempt_latest_read.py``
is implemented by Worker A against this red batch; until it exists, collection
fails with an ImportError, which is the expected red state.

Happy-path rows are REAL payloads: genuine Node 2 results through
``build_team_forecast_build_envelope`` (ready, watch, blocked, and the
ready-but-watch-gated amendment cases), projected through
``team_forecast_evaluation_scope_payload`` and the Node 4 row codec. Fixture
idioms mirror tests/test_team_forecast_build_envelope.py and
tests/test_team_evidence_aggregation_db_row.py without importing them.

Spy contract pinned here: the production module binds the consumed Node 5
functions (``load_latest_team_evaluation_attempt`` and
``load_latest_team_evaluation_attempt_with_psycopg``) as plain module-level
names; the delegation spies patch those names in both the reader and the Node 5
namespaces and assert exactly one call with exact kwargs and no fallback.
"""

from __future__ import annotations

import copy
from dataclasses import MISSING, FrozenInstanceError, fields as dataclass_fields, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import inspect
import json
import sys
import types
from typing import Any

import pytest

import polymarket_alpha_lab.team_evidence_aggregation_types as n2t
from polymarket_alpha_lab.team_evidence_aggregation import build_team_evidence_aggregation_result
import polymarket_alpha_lab.team_forecast_build_envelope as n3
from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket, TeamForecastPacket
import polymarket_alpha_lab.team_evidence_aggregation_attempt_store as attempt_store
import polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg as attempt_psycopg
from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow, team_evaluation_attempt_to_db_row)
import polymarket_alpha_lab.team_evaluation_attempt_latest_read as reader
from polymarket_alpha_lab.team_evaluation_attempt_latest_read import (
    TeamEvaluationAttemptLatestReadReport, read_latest_team_evaluation_attempt_report,
    read_latest_team_evaluation_attempt_report_with_psycopg)

LOCAL_DSN = "postgresql://postgres:local-secret@localhost:54322/postgres"
REMOTE_DSN = "postgresql://worker:remote-secret-token@db.remote.supabase.co:5432/polymarket"
BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)
RECEIPT_TIME = datetime(2026, 7, 13, 8, 59, 30, tzinfo=timezone.utc)
RUN_STARTED_AT = datetime(2026, 7, 13, 9, tzinfo=timezone.utc)
MARKET_SLUG = "will-btc-close-above-105k-on-july-4"
SCOPE_VERSION = "team-evaluation-attempt-latest-read-test-v1"
GATE_KEY = "external_publication_gate"
PROBABILITY_PATH = ("node2_result", "result", "publishable_probability_yes")
PAYLOAD_KEYS = ("scope_version", "domain_context", "provenance", "run_metadata",
                "evaluator_receipts", "node2_config", "node2_input", "node2_result")
HARD_FLAGS = ("paper_only", "report_only", "readonly")
REPORT_FIELDS = ("attempt_present", "absence_reason", "tea_id", "tfr_id", "attempted_at",
                 "scope_version", "scope_key", "status", "hard_flag", "publication_gate_present",
                 "publication_gate_status", "reason_codes", "publication_gate_reason_codes",
                 "packet_presence", "audit_packet_selected_side",
                 "audit_packet_forecast_probability_yes", "paper_only", "report_only", "readonly")
PROBE_TFR_ID = "tfr:v1:" + sha256(b"node8-latest-read-probe").hexdigest()
EMPTY_NONE_FIELDS = ("tea_id", "tfr_id", "attempted_at", "scope_version", "scope_key", "status",
                     "hard_flag", "publication_gate_present", "publication_gate_status",
                     "packet_presence", "audit_packet_selected_side",
                     "audit_packet_forecast_probability_yes")
# (mode, gate status or None, expected presence, gate present, status, hard flag)
PRESENCE_CASES = (
    ("ready", None, "projected", False, "ready", False),
    ("ready", "ready", "projected", True, "ready", False),
    ("ready", "watch", "suppressed", True, "ready", False),
    ("ready", "blocked", "suppressed", True, "ready", False),
    ("watch", None, "suppressed", False, "watch", False),
    ("blocked", None, "suppressed", False, "blocked", False),
    ("contradiction_blocked", None, "suppressed", False, "blocked", True),
)

def digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()

def node2_config(requirements=()):
    d = Decimal
    return n2t.TeamEvidenceAggregationConfig(
        "generic-test-v1", d("60.000000"), d("20.000000"), d("1.000000"), d("1.000000"), 2,
        d("0.250000"), d("0.750000"), d("0.250000"), d("0.750000"), d("0.110000"), d("0.890000"),
        128, 32, 1024, 256, requirements)

def req(requirement_id, unmet_status):
    return n2t.TeamEvidenceRequirement(requirement_id, 1, Decimal("0.000000"), unmet_status)

def root_record(stem, probability_yes=Decimal("0.600000"), requested_weight=Decimal("0.200000")):
    lid, ld, cd = f"lineage:{stem}", digest(f"lineage-digest:{stem}"), digest(f"content:{stem}")
    t50, t55, t60, t65 = (BASE_TIME + timedelta(seconds=s) for s in (50, 55, 60, 65))
    cap = n2t.TeamEvidenceCapture(f"capture:{stem}", digest(f"capture-digest:{stem}"), lid, ld, cd, t55)
    rev = n2t.TeamEvidenceRevision(f"evidence:{stem}", digest(f"evidence-digest:{stem}"), None, None,
                                   lid, ld, cd, (), t50, t60)
    asm = n2t.TeamEvidenceAssessmentRevision(f"assessment:{stem}", digest(f"assessment-digest:{stem}"),
                                             None, None, f"evidence:{stem}", digest(f"evidence-digest:{stem}"),
                                             t65, probability_yes, requested_weight,
                                             digest(f"rationale:{stem}"), f"ind:{stem}", f"corr:{stem}")
    return n2t.TeamEvidenceAggregationRecord(n2t.TeamEvidenceSourceLineage(lid, ld), cap, rev, asm)

def aggregation_input(records):
    return n2t.TeamEvidenceAggregationInput(
        EVALUATED_AT, records, tuple(n2t.TeamEvidenceCurrentRevisionSelection(
            r.evidence_revision.evidence_revision_id, r.evidence_revision.evidence_revision_digest,
            r.assessment_revision.assessment_revision_id, r.assessment_revision.assessment_revision_digest)
            for r in records))

def accepted_receipt(record):
    return n3.TeamForecastEvaluatorReceipt(
        f"evaluator:{record.capture.capture_id}", digest(f"evaluator-input:{record.capture.capture_id}"),
        RECEIPT_TIME, "accepted", (record.source_lineage.source_lineage_id, record.capture.capture_id,
                                   record.evidence_revision.evidence_revision_id,
                                   record.assessment_revision.assessment_revision_id),
        ("evaluator_submitted",))

def forecast_template() -> TeamForecastPacket:
    return TeamForecastPacket(
        "forecast-template-001", "crypto_btc", "0xnode8condition", MARKET_SLUG,
        "Will BTC close above $105,000 on July 4?", "finance.crypto.btc", "crypto_price_threshold",
        "yes", Decimal("0.500000"), Decimal("0.700000"), Decimal("0.650000"), Decimal("0.900000"),
        Decimal("0.120000"), Decimal("0.540000"), Decimal("0.570000"), ("aggregation_ready",),
        ("btc-memory-2026-q2",), ("source-etf-flow-dashboard",), ("weekend_liquidity_gap",),
        "team-forecast-v0", "team-forecast-prompt-v3", RUN_STARTED_AT)

def evidence_template(record) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        "evidence-template-001", "crypto_btc", MARKET_SLUG,
        f"source-{record.source_lineage.source_lineage_id}", "team_evaluator", RECEIPT_TIME, 60,
        "team_assessment", "Evaluator assessment bound to the accepted record identity.",
        record.assessment_revision.requested_weight, ("evaluator_submitted",))

def policy_gate(status, codes=()):
    return n3.TeamForecastPolicyPublicationGate(status=status, reason_codes=codes)

def make_case(mode="ready", gate=None, probability=Decimal("0.600000")):
    requirements = {"watch": (req("req:watch", "watch"),),
                    "blocked": (req("req:blocked", "blocked"),)}.get(mode, ())
    records = ()
    if mode in ("ready", "watch", "blocked"):
        records = (root_record("alpha", probability),)
    if mode == "contradiction_blocked":
        records = (root_record("cy", Decimal("0.750000"), Decimal("0.500000")),
                   root_record("cn", Decimal("0.250000"), Decimal("0.300000")))
    config_value = node2_config(requirements)
    input_value = aggregation_input(records)
    result = build_team_evidence_aggregation_result(input_value, config=config_value)
    with_packets = mode == "ready" and (gate is None or gate.status == "ready")
    gate_tag = "ungated" if gate is None else gate.status
    return n3.build_team_forecast_build_envelope(
        result, aggregation_input=input_value, config=config_value,
        scope=n3.TeamForecastEvaluationScope(
            SCOPE_VERSION, (("team_id", "crypto_btc"), ("market_slug", MARKET_SLUG)),
            ("gamma:market/12345", "clob:book/0xabc")),
        run_metadata=n3.TeamForecastRunMetadata(
            f"node8-latest-read-{mode}-{gate_tag}", "team-forecast-generator-v1",
            "team-forecast-prompt-v3", RUN_STARTED_AT, RUN_STARTED_AT + timedelta(minutes=5)),
        evaluator_receipts=tuple(accepted_receipt(r) for r in records),
        legacy_forecast_packet=forecast_template() if with_packets else None,
        legacy_evidence_packets=tuple(evidence_template(r) for r in records) if with_packets else (),
        policy_publication_gate=gate)

def row_case(mode="ready", gate=None, probability=Decimal("0.600000")) -> TeamEvaluationAttemptDbRow:
    envelope = make_case(mode=mode, gate=gate, probability=probability)
    return team_evaluation_attempt_to_db_row(
        tea_id=envelope.tea_id, tfr_id=envelope.tfr_id,
        evaluation_scope_payload=n3.team_forecast_evaluation_scope_payload(envelope))

def tweak(payload, path, value):
    copied = target = json.loads(json.dumps(payload, allow_nan=False))
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return copied

def forged(row: TeamEvaluationAttemptDbRow, changes: dict[str, Any]) -> TeamEvaluationAttemptDbRow:
    """Constructor-bypass forgery of the frozen Node 4 row."""
    forged_row = object.__new__(TeamEvaluationAttemptDbRow)
    for field in dataclass_fields(row):
        object.__setattr__(forged_row, field.name, getattr(row, field.name))
    for name, value in changes.items():
        object.__setattr__(forged_row, name, value)
    return forged_row

def rebuilt(row: TeamEvaluationAttemptDbRow, payload) -> TeamEvaluationAttemptDbRow:
    """Rebuild a real row over a codec-tolerable tweaked payload."""
    return team_evaluation_attempt_to_db_row(
        tea_id=row.tea_id, tfr_id=row.tfr_id, evaluation_scope_payload=payload)

class FakeCursor:
    def __init__(self, rows=(), *, fetchall_error=None):
        self.rows, self.fetchall_error = tuple(rows), fetchall_error
        self.calls, self.close_count = [], 0

    def execute(self, sql, params=None): self.calls.append((sql, params))

    def fetchall(self):
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self): self.close_count += 1

class FakeAdapters:
    def __init__(self): self.registered = []

    def register_dumper(self, cls, dumper): self.registered.append((cls, dumper))

class FakeConnection:
    def __init__(self, rows=(), *, fetchall_error=None):
        self.cursor_instance = FakeCursor(rows, fetchall_error=fetchall_error)
        self.adapters = FakeAdapters()
        self.cursor_count = self.commit_count = self.rollback_count = self.close_count = 0

    def cursor(self):
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self): self.commit_count += 1

    def rollback(self): self.rollback_count += 1

    def close(self): self.close_count += 1

def row_record(row: TeamEvaluationAttemptDbRow) -> dict[str, Any]:
    return {column: getattr(row, column) for column in attempt_store.TEAM_EVALUATION_ATTEMPT_COLUMNS}

class FakeJsonbDumper:
    pass

def install_fake_psycopg(monkeypatch: pytest.MonkeyPatch, *, connect) -> None:
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))
    monkeypatch.setitem(sys.modules, "psycopg.types.json",
                        types.SimpleNamespace(JsonbDumper=FakeJsonbDumper))

def _unexpected(name: str):
    def raise_unexpected(*args: Any, **kwargs: Any): raise AssertionError(f"unexpected call: {name}")
    return raise_unexpected

def spy_loader(monkeypatch: pytest.MonkeyPatch, calls: list, result):
    def spy(connection, *, tfr_id=None, scope_version=None, scope_key=None,
            table_name="team_evaluation_attempts"):
        calls.append({"connection": connection, "tfr_id": tfr_id, "scope_version": scope_version,
                      "scope_key": scope_key, "table_name": table_name})
        return result
    monkeypatch.setattr(attempt_store, "load_latest_team_evaluation_attempt", spy)
    monkeypatch.setattr(reader, "load_latest_team_evaluation_attempt", spy, raising=False)

def spy_psycopg_latest(monkeypatch: pytest.MonkeyPatch, calls: list, result):
    def spy(dsn, *, tfr_id=None, scope_version=None, scope_key=None,
            table_name="team_evaluation_attempts"):
        calls.append({"dsn": dsn, "tfr_id": tfr_id, "scope_version": scope_version,
                      "scope_key": scope_key, "table_name": table_name})
        return result
    monkeypatch.setattr(attempt_psycopg, "load_latest_team_evaluation_attempt_with_psycopg", spy)
    monkeypatch.setattr(reader, "load_latest_team_evaluation_attempt_with_psycopg",
                        spy, raising=False)

def forbid_store_surfaces(monkeypatch: pytest.MonkeyPatch, *, latest: bool = False) -> None:
    names = ["load_team_evaluation_attempt_rows", "insert_team_evaluation_attempt",
             "_insert_attempt_rows_atomic"] + (
        ["load_latest_team_evaluation_attempt"] if latest else [])
    for name in names:
        monkeypatch.setattr(attempt_store, name, _unexpected(name))
        monkeypatch.setattr(reader, name, _unexpected(name), raising=False)

def forbid_psycopg_surfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("load_team_evaluation_attempts_with_psycopg",
                 "insert_team_evaluation_attempt_with_psycopg",
                 "insert_team_evaluation_attempts_with_psycopg",
                 "persist_team_evaluation_attempts_with_psycopg"):
        monkeypatch.setattr(attempt_psycopg, name, _unexpected(name))
        monkeypatch.setattr(reader, name, _unexpected(name), raising=False)

def report_for(monkeypatch: pytest.MonkeyPatch, row) -> TeamEvaluationAttemptLatestReadReport:
    spy_loader(monkeypatch, [], row)
    return read_latest_team_evaluation_attempt_report(object(), tfr_id=PROBE_TFR_ID)

def assert_empty_report(report) -> None:
    assert report.attempt_present is False
    assert report.absence_reason == "no_matching_attempt"
    for name in EMPTY_NONE_FIELDS:
        assert getattr(report, name) is None, name
    assert type(report.reason_codes) is tuple and report.reason_codes == ()
    assert type(report.publication_gate_reason_codes) is tuple
    assert report.publication_gate_reason_codes == ()
    assert report.paper_only is True and report.report_only is True and report.readonly is True

# --- RED item 1: the locked public contract ---------------------------------
def test_locked_public_surface_and_loader_signatures_are_exact() -> None:
    assert reader.__all__ == (
        "TeamEvaluationAttemptLatestReadReport",
        "read_latest_team_evaluation_attempt_report",
        "read_latest_team_evaluation_attempt_report_with_psycopg")
    assert all(getattr(reader, name, None) is not None for name in reader.__all__)
    for func, first in (
        (read_latest_team_evaluation_attempt_report, "connection"),
        (read_latest_team_evaluation_attempt_report_with_psycopg, "dsn")):
        parameters = inspect.signature(func).parameters
        assert list(parameters) == [first, "tfr_id", "scope_version", "scope_key", "table_name"]
        assert parameters[first].kind in (inspect.Parameter.POSITIONAL_ONLY,
                                          inspect.Parameter.POSITIONAL_OR_KEYWORD)
        assert parameters[first].default is inspect.Parameter.empty
        for name in ("tfr_id", "scope_version", "scope_key", "table_name"):
            assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters["tfr_id"].default is None and parameters["scope_version"].default is None
        assert parameters["scope_key"].default is None
        assert parameters["table_name"].default == "team_evaluation_attempts"
    fields = tuple(dataclass_fields(TeamEvaluationAttemptLatestReadReport))
    assert tuple(f.name for f in fields) == REPORT_FIELDS
    assert all(f.default is (True if f.name in HARD_FLAGS else MISSING) for f in fields)

def test_report_dataclass_is_frozen_slotted_and_hard_flagged(monkeypatch) -> None:
    report = report_for(monkeypatch, row_case("ready"))
    assert TeamEvaluationAttemptLatestReadReport.__dataclass_params__.frozen is True
    assert not hasattr(report, "__dict__")
    assert set(REPORT_FIELDS) <= set(TeamEvaluationAttemptLatestReadReport.__slots__)
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    for flag in HARD_FLAGS:
        for bad in (False, 1):
            with pytest.raises(ValueError, match=flag):
                replace(report, **{flag: bad})
        bypassed = object.__new__(type(report))
        for field in dataclass_fields(report):
            object.__setattr__(bypassed, field.name,
                               False if field.name == flag else getattr(report, field.name))
        with pytest.raises(ValueError, match=flag):
            bypassed.__post_init__()
    for changes, message in (({"audit_packet_selected_side": "yes"}, "selected_side"),
                             ({"absence_reason": "fabricated_absence"}, "absence_reason"),
                             ({"packet_presence": "maybe"}, "packet_presence"),
                             ({"status": "paused"}, "status")):
        with pytest.raises(ValueError, match=message):
            replace(report, **changes)

def test_no_row_yields_the_exact_empty_report(monkeypatch) -> None:
    connection = FakeConnection(rows=())
    report = read_latest_team_evaluation_attempt_report(connection, tfr_id=PROBE_TFR_ID)
    assert connection.cursor_count == 1 and len(connection.cursor_instance.calls) == 1
    assert "LIMIT 1" in connection.cursor_instance.calls[0][0]
    assert connection.commit_count == 0 and connection.rollback_count == 0
    assert_empty_report(report)
    calls: list[dict[str, Any]] = []
    spy_loader(monkeypatch, calls, None)
    forbid_store_surfaces(monkeypatch)
    assert read_latest_team_evaluation_attempt_report(object(), tfr_id=PROBE_TFR_ID) == report
    assert len(calls) == 1
    psycopg_calls: list[dict[str, Any]] = []
    spy_psycopg_latest(monkeypatch, psycopg_calls, None)
    psycopg_report = read_latest_team_evaluation_attempt_report_with_psycopg(
        LOCAL_DSN, scope_version=SCOPE_VERSION, scope_key=digest("node8-scope"))
    assert psycopg_report == report and len(psycopg_calls) == 1# --- RED item 2: read behavior with fake connections and delegation spies ---
@pytest.mark.parametrize("lookup", ("tfr", "scope"))
def test_delegates_exactly_once_to_the_store_loader_with_exact_kwargs(monkeypatch, lookup) -> None:
    row = row_case("ready")
    connection_sentinel = object()
    calls: list[dict[str, Any]] = []
    spy_loader(monkeypatch, calls, row)
    forbid_store_surfaces(monkeypatch)
    if lookup == "tfr":
        report = read_latest_team_evaluation_attempt_report(
            connection_sentinel, tfr_id=row.tfr_id, table_name="research.team_evaluation_attempts")
        expected = {"connection": connection_sentinel, "tfr_id": row.tfr_id,
                    "scope_version": None, "scope_key": None,
                    "table_name": "research.team_evaluation_attempts"}
    else:
        report = read_latest_team_evaluation_attempt_report(
            connection_sentinel, scope_version=row.scope_version, scope_key=row.scope_key)
        expected = {"connection": connection_sentinel, "tfr_id": None,
                    "scope_version": row.scope_version, "scope_key": row.scope_key,
                    "table_name": "team_evaluation_attempts"}
    assert len(calls) == 1 and calls[0] == expected
    assert report.attempt_present is True and report.absence_reason is None
    assert report.tea_id == row.tea_id and report.tfr_id == row.tfr_id

@pytest.mark.parametrize("mode", ("watch", "blocked", "contradiction_blocked"))
def test_latest_watch_or_blocked_row_is_reported_as_is_without_fallback(monkeypatch, mode) -> None:
    older_ready = row_case("ready")
    latest = row_case(mode)
    assert latest.tea_id != older_ready.tea_id and latest.status != "ready"
    calls: list[dict[str, Any]] = []
    spy_loader(monkeypatch, calls, latest)
    forbid_store_surfaces(monkeypatch)
    report = read_latest_team_evaluation_attempt_report(object(), tfr_id=latest.tfr_id)
    assert len(calls) == 1
    assert report.attempt_present is True and report.tea_id == latest.tea_id
    assert report.tea_id != older_ready.tea_id  # no fallback to the older ready row
    assert report.status == latest.status in ("watch", "blocked")
    assert report.hard_flag is latest.hard_flag
    assert report.packet_presence == "suppressed"
    assert report.audit_packet_forecast_probability_yes is None

def test_fake_connection_projects_ready_row_identity_and_audit_fields() -> None:
    row = row_case("ready")
    payload = row.evaluation_scope_payload
    result = payload["node2_result"]["result"]
    assert forecast_template().selected_side == "yes"  # a packet side exists upstream
    connection = FakeConnection(rows=(row_record(row),))
    report = read_latest_team_evaluation_attempt_report(connection, tfr_id=row.tfr_id)
    assert report.attempt_present is True and report.absence_reason is None
    assert report.tea_id == row.tea_id and report.tfr_id == row.tfr_id
    assert report.attempted_at == row.attempted_at == EVALUATED_AT
    assert report.scope_version == row.scope_version == payload["scope_version"]
    assert report.scope_key == row.scope_key and report.status == "ready"
    assert report.hard_flag is False and report.paper_only is True and report.readonly is True
    assert type(report.reason_codes) is tuple
    assert report.reason_codes == tuple(result["reason_codes"])
    assert report.publication_gate_present is False
    assert report.publication_gate_status is None and report.publication_gate_reason_codes == ()
    assert report.packet_presence == "projected" and report.audit_packet_selected_side is None
    assert type(report.audit_packet_forecast_probability_yes) is Decimal
    assert report.audit_packet_forecast_probability_yes == Decimal("0.600000")
    assert report.report_only is True
    # the read stays owned by Node 5: one latest-attempt SELECT, no commit
    cursor = connection.cursor_instance
    assert connection.cursor_count == 1 and len(cursor.calls) == 1
    assert "ORDER BY attempted_at DESC, tea_id DESC" in cursor.calls[0][0]
    assert connection.commit_count == 0 and connection.rollback_count == 0

def test_gate_extraction_reports_gate_fields_and_separate_reason_codes() -> None:
    row = row_case("ready", gate=policy_gate("watch", ("policy_watch",)))
    payload = row.evaluation_scope_payload
    connection = FakeConnection(rows=(row_record(row),))
    report = read_latest_team_evaluation_attempt_report(
        connection, scope_version=row.scope_version, scope_key=row.scope_key)
    assert payload["run_metadata"][GATE_KEY] == {
        "status": "watch", "reason_codes": ["policy_watch"],
        "paper_only": True, "report_only": True, "readonly": True}
    assert report.publication_gate_present is True and report.publication_gate_status == "watch"
    assert type(report.publication_gate_reason_codes) is tuple
    assert report.publication_gate_reason_codes == ("policy_watch",)
    assert report.reason_codes == tuple(payload["node2_result"]["result"]["reason_codes"])
    assert "policy_watch" not in report.reason_codes  # never merged with Node 2 codes
    assert report.status == "ready" and report.hard_flag is False
    assert report.packet_presence == "suppressed"
    assert report.audit_packet_forecast_probability_yes is None  # gate watch suppresses

@pytest.mark.parametrize(("mode", "gate_status", "presence", "gate_present", "status", "hard"),
                         PRESENCE_CASES)
def test_packet_presence_matrix_and_audit_probability(
        monkeypatch, mode, gate_status, presence, gate_present, status, hard) -> None:
    gate = policy_gate(gate_status, (f"policy_{gate_status}",)) if gate_status else None
    report = report_for(monkeypatch, row_case(mode, gate=gate))
    assert report.status == status and report.hard_flag is hard
    assert report.publication_gate_present is gate_present
    assert report.publication_gate_status == gate_status
    assert report.publication_gate_reason_codes == (
        (f"policy_{gate_status}",) if gate_status else ())
    assert report.packet_presence == presence and report.audit_packet_selected_side is None
    if presence == "projected":
        assert report.audit_packet_forecast_probability_yes == Decimal("0.600000")
    else:
        assert report.audit_packet_forecast_probability_yes is None

def test_audit_probability_keeps_zero_none_and_ceiling_distinct(monkeypatch) -> None:
    ceiling = row_case("ready", probability=Decimal("0.950000"))
    ceiling_report = report_for(monkeypatch, ceiling)
    assert ceiling_report.packet_presence == "projected"
    assert ceiling_report.audit_packet_forecast_probability_yes == Decimal("0.890000")
    assert "publish_probability_ceiling_applied" in ceiling_report.reason_codes
    zero = rebuilt(ceiling, tweak(ceiling.evaluation_scope_payload, PROBABILITY_PATH, "0.000000"))
    zero_probability = report_for(monkeypatch, zero).audit_packet_forecast_probability_yes
    assert zero_probability is not None and zero_probability == Decimal("0.000000")
    unknown = rebuilt(ceiling, tweak(ceiling.evaluation_scope_payload, PROBABILITY_PATH, None))
    assert report_for(monkeypatch, unknown).audit_packet_forecast_probability_yes is None
    watch = row_case("watch")
    assert watch.evaluation_scope_payload["node2_result"]["result"][
        "publishable_probability_yes"] is None
    assert report_for(monkeypatch, watch).audit_packet_forecast_probability_yes is None

def test_audit_selected_side_is_permanently_none(monkeypatch) -> None:
    projected = report_for(monkeypatch, row_case("ready"))
    suppressed = report_for(monkeypatch, row_case("ready", gate=policy_gate("blocked", ("p_b",))))
    calls: list[dict[str, Any]] = []
    spy_loader(monkeypatch, calls, None)
    empty = read_latest_team_evaluation_attempt_report(object(), tfr_id=PROBE_TFR_ID)
    for report in (projected, suppressed, empty):
        assert report.audit_packet_selected_side is None
    assert projected.packet_presence == "projected" and suppressed.packet_presence == "suppressed"

def test_reader_never_mutates_the_row_payload(monkeypatch) -> None:
    row = row_case("ready", gate=policy_gate("watch", ("policy_watch",)))
    snapshot = json.loads(json.dumps(row.evaluation_scope_payload, allow_nan=False))
    report_for(monkeypatch, row)
    assert row.evaluation_scope_payload == snapshot
    assert report_for(monkeypatch, row).attempt_present is True

def test_psycopg_wrapper_delegates_only_to_the_node5_latest_adapter(monkeypatch) -> None:
    row = row_case("watch")
    calls: list[dict[str, Any]] = []
    spy_psycopg_latest(monkeypatch, calls, row)
    forbid_store_surfaces(monkeypatch, latest=True)
    forbid_psycopg_surfaces(monkeypatch)
    report = read_latest_team_evaluation_attempt_report_with_psycopg(
        LOCAL_DSN, tfr_id=row.tfr_id, table_name="research.team_evaluation_attempts")
    assert len(calls) == 1
    assert calls[0] == {"dsn": LOCAL_DSN, "tfr_id": row.tfr_id, "scope_version": None,
                        "scope_key": None, "table_name": "research.team_evaluation_attempts"}
    assert report.attempt_present is True and report.status == "watch" and report.tea_id == row.tea_id
    calls.clear()
    scope_report = read_latest_team_evaluation_attempt_report_with_psycopg(
        LOCAL_DSN, scope_version=row.scope_version, scope_key=row.scope_key)
    assert len(calls) == 1
    assert calls[0] == {"dsn": LOCAL_DSN, "tfr_id": None, "scope_version": row.scope_version,
                        "scope_key": row.scope_key, "table_name": "team_evaluation_attempts"}
    assert scope_report == report

def test_psycopg_wrapper_end_to_end_over_one_owned_fake_connection(monkeypatch) -> None:
    row = row_case("ready")
    connection = FakeConnection(rows=(row_record(row),))
    connect_calls: list[str] = []
    install_fake_psycopg(monkeypatch, connect=lambda dsn: connect_calls.append(dsn) or connection)
    report = read_latest_team_evaluation_attempt_report_with_psycopg(LOCAL_DSN, tfr_id=row.tfr_id)
    assert connect_calls == [LOCAL_DSN]
    assert report.attempt_present is True and report.status == "ready"
    assert report.packet_presence == "projected"
    assert report.audit_packet_forecast_probability_yes == Decimal("0.600000")
    assert connection.adapters.registered == [(dict, FakeJsonbDumper)]
    assert connection.commit_count == 1 and connection.rollback_count == 0
    assert connection.close_count == 1 and connection.cursor_instance.close_count == 1

def test_invalid_dsn_fails_closed_before_any_connection_activity(monkeypatch) -> None:
    events: list[str] = []
    original_validate = attempt_psycopg.validate_local_postgres_dsn

    def validate_spy(value, *, env_var_name):
        events.append("validate")
        original_validate(value, env_var_name=env_var_name)

    def connect_spy(dsn):
        events.append("connect")
        raise AssertionError("connection activity before the DSN validation gate")

    monkeypatch.setattr(attempt_psycopg, "validate_local_postgres_dsn", validate_spy)
    monkeypatch.setattr(attempt_psycopg, "_connect", connect_spy)
    with pytest.raises(ValueError) as exc_info:
        read_latest_team_evaluation_attempt_report_with_psycopg(REMOTE_DSN, tfr_id=PROBE_TFR_ID)
    message = str(exc_info.value)
    assert "POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN" in message
    assert REMOTE_DSN not in message and "remote-secret-token" not in message
    assert events == ["validate"]  # validation runs, connection activity never does

def test_db_errors_propagate_unchanged_without_catch_or_rewrite(monkeypatch) -> None:
    error = RuntimeError("database exploded without a report")
    # first through the real store loader on a failing fake connection
    fetchall_error = RuntimeError("fetchall failed unchanged")
    failing = FakeConnection(fetchall_error=fetchall_error)
    with pytest.raises(RuntimeError) as fetch_info:
        read_latest_team_evaluation_attempt_report(failing, tfr_id=PROBE_TFR_ID)
    assert fetch_info.value is fetchall_error and failing.cursor_instance.close_count == 1
    # then through the spied Node 5 surfaces: the identical error object reraises
    calls: list[int] = []

    def raising_loader(*args: Any, **kwargs: Any):
        calls.append(1)
        raise error

    def raising_adapter(*args: Any, **kwargs: Any):
        raise error

    monkeypatch.setattr(attempt_store, "load_latest_team_evaluation_attempt", raising_loader)
    monkeypatch.setattr(reader, "load_latest_team_evaluation_attempt",
                        raising_loader, raising=False)
    monkeypatch.setattr(attempt_psycopg, "load_latest_team_evaluation_attempt_with_psycopg",
                        raising_adapter)
    monkeypatch.setattr(reader, "load_latest_team_evaluation_attempt_with_psycopg",
                        raising_adapter, raising=False)
    with pytest.raises(RuntimeError) as dbapi_info:
        read_latest_team_evaluation_attempt_report(object(), tfr_id=PROBE_TFR_ID)
    assert dbapi_info.value is error and calls == [1]
    with pytest.raises(RuntimeError) as psycopg_info:
        read_latest_team_evaluation_attempt_report_with_psycopg(LOCAL_DSN, tfr_id=PROBE_TFR_ID)
    assert psycopg_info.value is error

# --- RED item 3: the fail-closed failure matrix -----------------------------
@pytest.mark.parametrize("bad_row", (
    object(), "row", 7,
    types.SimpleNamespace(tea_id="tea:v1:" + "0" * 64, tfr_id=PROBE_TFR_ID, attempted_at=None,
                          status="ready", hard_flag=False, scope_version="v", scope_key="0" * 64,
                          evaluation_scope_payload={}),
))
def test_rejects_rows_that_are_not_real_attempt_rows(monkeypatch, bad_row) -> None:
    with pytest.raises(ValueError, match="TeamEvaluationAttemptDbRow"):
        report_for(monkeypatch, bad_row)

@pytest.mark.parametrize("missing_key", PAYLOAD_KEYS)
def test_rejects_payloads_missing_one_outer_key(monkeypatch, missing_key: str) -> None:
    row = row_case("ready")
    broken = {key: value for key, value in row.evaluation_scope_payload.items()
              if key != missing_key}
    with pytest.raises(ValueError, match="top-level keys"):
        report_for(monkeypatch, forged(row, {"evaluation_scope_payload": broken}))

def test_rejects_extra_outer_keys_non_dict_payloads_and_broken_sections(monkeypatch) -> None:
    row = row_case("ready")
    payload = row.evaluation_scope_payload
    with pytest.raises(ValueError, match="top-level keys"):
        report_for(monkeypatch, forged(
            row, {"evaluation_scope_payload": dict(payload, decision="invented")}))
    for non_dict in (["not", "a", "dict"], "payload", 7):
        with pytest.raises(ValueError, match="evaluation_scope_payload"):
            report_for(monkeypatch, forged(row, {"evaluation_scope_payload": non_dict}))
    with pytest.raises(ValueError, match="run_metadata"):
        report_for(monkeypatch, forged(
            row, {"evaluation_scope_payload": dict(payload, run_metadata=["list"])}))
    with pytest.raises(ValueError, match="node2_result"):
        report_for(monkeypatch, forged(row, {"evaluation_scope_payload": dict(
            payload, node2_result={"schema_version": "pal.team_evidence_aggregation.result.v1"})}))
    with pytest.raises(ValueError, match="node2_result"):
        report_for(monkeypatch, rebuilt(
            row, tweak(payload, ("node2_result", "schema_version"), "pal.evil.v1")))

def test_rejects_status_hard_flag_and_identity_disagreement(monkeypatch) -> None:
    ready = row_case("ready")
    watch = row_case("watch")
    contradiction = row_case("contradiction_blocked")
    payload_status = tweak(ready.evaluation_scope_payload, ("node2_result", "result", "status"),
                           "watch")
    payload_contra = tweak(contradiction.evaluation_scope_payload,
                           ("node2_result", "result", "contradiction", "status"), "none")
    for row, changes, message in (
        (ready, {"status": "watch"}, "status"),
        (ready, {"status": 7}, "status"),
        (ready, {"evaluation_scope_payload": payload_status}, "status"),
        (ready, {"hard_flag": True}, "hard_flag"),
        (watch, {"hard_flag": True}, "hard_flag"),
        (contradiction, {"hard_flag": False}, "hard_flag"),
        (contradiction, {"evaluation_scope_payload": payload_contra}, "hard_flag"),
        (ready, {"scope_version": "tampered-v1"}, "scope_version"),
        (ready, {"attempted_at": ready.attempted_at + timedelta(seconds=1)}, "attempted_at"),
    ):
        with pytest.raises(ValueError, match=message):
            report_for(monkeypatch, forged(row, changes))

def test_rejects_false_hard_flags_in_run_metadata_and_gate(monkeypatch) -> None:
    gated = row_case("ready", gate=policy_gate("watch", ("policy_watch",)))
    for flag in HARD_FLAGS:
        broken_run = tweak(gated.evaluation_scope_payload, ("run_metadata", flag), False)
        with pytest.raises(ValueError, match=flag):
            report_for(monkeypatch, forged(gated, {"evaluation_scope_payload": broken_run}))
        broken_gate = tweak(gated.evaluation_scope_payload, ("run_metadata", GATE_KEY, flag), False)
        with pytest.raises(ValueError, match=flag):
            report_for(monkeypatch, forged(gated, {"evaluation_scope_payload": broken_gate}))

def test_rejects_invalid_publication_gate_maps(monkeypatch) -> None:
    gated = row_case("ready", gate=policy_gate("watch", ("policy_watch",)))
    payload = gated.evaluation_scope_payload
    gate_path = ("run_metadata", GATE_KEY)
    for status in ("paused", "READY", " ready", "", 1, None):
        with pytest.raises(ValueError, match="external_publication_gate"):
            report_for(monkeypatch, rebuilt(gated, tweak(payload, (*gate_path, "status"), status)))
    for codes in (["z_policy", "a_policy"], ["dupe", "dupe"], "policy_watch", [1],
                  ["Not Canonical"], {"policy_watch": 1}):
        with pytest.raises(ValueError, match="reason_codes"):
            report_for(monkeypatch, rebuilt(
                gated, tweak(payload, (*gate_path, "reason_codes"), codes)))
    gate_map = payload["run_metadata"][GATE_KEY]
    with pytest.raises(ValueError, match="five-field"):
        report_for(monkeypatch, rebuilt(
            gated, tweak(payload, gate_path, {**gate_map, "forged_field": True})))
    with pytest.raises(ValueError, match="five-field"):
        report_for(monkeypatch, rebuilt(
            gated, tweak(payload, gate_path,
                         {k: v for k, v in gate_map.items() if k != "readonly"})))

@pytest.mark.parametrize("bad", ("0.6", "0.6000000", "0.60000a", "-0.000000", "00.600000",
                                 "0.600000 ", "0.60000", "0,6"))
def test_rejects_noncanonical_probability_strings(monkeypatch, bad: str) -> None:
    row = row_case("ready")
    broken = tweak(row.evaluation_scope_payload, PROBABILITY_PATH, bad)
    assert broken["node2_result"]["result"]["publishable_probability_yes"] == bad
    with pytest.raises(ValueError, match="publishable_probability_yes"):
        report_for(monkeypatch, rebuilt(row, broken))

def test_rejects_non_string_probability_values(monkeypatch) -> None:
    row = row_case("ready")
    for bad in (0.6, 7, True, ["0.600000"], Decimal("0.600000")):
        deep = copy.deepcopy(row.evaluation_scope_payload)
        deep["node2_result"]["result"]["publishable_probability_yes"] = bad
        with pytest.raises(ValueError, match="publishable_probability_yes"):
            report_for(monkeypatch, forged(row, {"evaluation_scope_payload": deep}))

def test_rejects_tampered_reason_code_shapes(monkeypatch) -> None:
    row = row_case("ready")
    path = ("node2_result", "result", "reason_codes")
    for bad in ("aggregation_ready", ["z_ready", "a_ready"], ["dupe", "dupe"], [1, 2],
                ["Not Canonical"], {"a": 1}):
        with pytest.raises(ValueError, match="reason_codes"):
            report_for(monkeypatch, rebuilt(row, tweak(row.evaluation_scope_payload, path, bad)))

def test_rejects_injected_packet_shaped_keys(monkeypatch) -> None:
    row = row_case("ready", gate=policy_gate("ready", ("policy_ready",)))
    payload = row.evaluation_scope_payload
    for path, value in (
        (("run_metadata", "selected_side"), "yes"),
        (("run_metadata", "legacy_forecast_packet"), {"forecast_id": "forecast-template-001"}),
        (("run_metadata", "forecast_probability"), "0.500000"),
        (("node2_result", "result", "forecast_probability"), "0.500000"),
        (("node2_result", "result", "selected_side"), "no"),
    ):
        with pytest.raises(ValueError, match="packet"):
            report_for(monkeypatch, rebuilt(row, tweak(payload, path, value)))
    with pytest.raises(ValueError, match="top-level keys"):
        report_for(monkeypatch, forged(row, {"evaluation_scope_payload": dict(
            payload, legacy_forecast_packet={"forecast_id": "forecast-template-001"})}))
