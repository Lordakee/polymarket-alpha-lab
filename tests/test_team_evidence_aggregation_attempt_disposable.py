"""Authorized disposable-database proof for the Node 5 atomic attempt writer.

Governing plan: docs/superpowers/plans/2026-07-13-team-forecast-atomic-persistence.md
(Task 5). No database connection is made unless BOTH hold:
``POLYMARKET_ALPHA_LAB_RUN_TEAM_EVIDENCE_AGGREGATION_DISPOSABLE_DB=1`` is set
(default offline runs skip, the green offline state) and
``POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN`` is set and passes
``validate_local_postgres_dsn`` (unset or invalid DSNs skip, never fail).

The runbook's Windows-native procedure creates the dedicated database
``polymarket_alpha_lab_node5_disposable``, applies the migration, runs this
file gated, and drops the database with ``(force)`` in ``finally``. This test
never creates or drops a database; it proves ONLY against the given DSN,
refuses any other database name, and deletes only rows it inserted, by
``tea_id``. Evidence prints redacted metadata only, never the DSN.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from os import environ
from typing import Any
from uuid import uuid4

import pytest

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_team_evidence_aggregation_config import (
    TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR,
)
from polymarket_alpha_lab.team_evidence_aggregation import build_team_evidence_aggregation_result
from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow, team_evaluation_attempt_to_db_row)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig, TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord, TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture, TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceRequirement, TeamEvidenceRevision, TeamEvidenceSourceLineage)
from polymarket_alpha_lab.team_forecast_build_envelope import (
    TeamForecastBuildEnvelope, TeamForecastEvaluatorReceipt,
    TeamForecastEvaluationScope, TeamForecastRunMetadata,
    build_team_forecast_build_envelope)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket, TeamForecastPacket)

RUN_GATE_ENV_VAR = "POLYMARKET_ALPHA_LAB_RUN_TEAM_EVIDENCE_AGGREGATION_DISPOSABLE_DB"
DEDICATED_DATABASE_NAME = "polymarket_alpha_lab_node5_disposable"
TABLE_NAME = "team_evaluation_attempts"
STATUS_ORDER = ("ready", "watch", "blocked")
SCOPE_VERSION = "team-forecast-build-envelope-v1"
DSN_VALIDATOR_MESSAGE_MARKER = "must point to local Postgres/Supabase"
REMOTE_DSN_PROBE = "postgresql://postgres:super-secret-token@db.remote.example.com:5432/postgres"
ORPHAN_SHAPE_ANCHORS = {
    "tea_id mismatch": "tea_id", "run_metadata absent": "run_metadata",
    "tfr_id mismatch": "tfr_id"}
_D = Decimal
def _disposable_dsn() -> str:
    if environ.get(RUN_GATE_ENV_VAR) != "1":
        pytest.skip(f"set {RUN_GATE_ENV_VAR}=1 to run the authorized disposable proof")
    if not (dsn := environ.get(TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR)):
        pytest.skip(f"set {TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR} to run the proof")
    try:
        validate_local_postgres_dsn(dsn, env_var_name=TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR)
    except ValueError:
        pytest.skip(
            f"{TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR} must point to "
            "local Supabase/Postgres")
    return dsn
# Read-back goes through the adapter's thin load wrappers, which own the
# DSN check and one owned connection per read.
def _load_attempts(dsn: str, *, latest: bool = False, **filters: Any) -> Any:
    from polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg import (
        load_latest_team_evaluation_attempt_with_psycopg,
        load_team_evaluation_attempts_with_psycopg)
    if latest:
        return load_latest_team_evaluation_attempt_with_psycopg(dsn, **filters)
    return load_team_evaluation_attempts_with_psycopg(dsn, **filters)

# Node 2C/Node 3 fixture idioms (compact form of the fixture block in
# tests/test_team_forecast_build_envelope.py); every envelope is built through
# the real Node 2 and Node 3 builders; record digests need only cross-field
# equality, not distinctness.
BASE_TIME = datetime(2026, 7, 13, 9, 0, 0, tzinfo=UTC)
RUN_STARTED_AT = datetime(2026, 7, 13, 8, 55, 0, tzinfo=UTC)
RUN_COMPLETED_AT = datetime(2026, 7, 13, 9, 5, 0, tzinfo=UTC)
RECEIPT_TIME = datetime(2026, 7, 13, 8, 59, 30, tzinfo=UTC)
FRESHNESS_ANCHOR = timedelta(seconds=50)  # freshness_anchor_at is this far before evaluated_at
BASE_CONFIG_VALUES: dict[str, Any] = {
    "config_version": "generic-test-v1",
    "max_requirement_assignments_per_evidence": 2, "maximum_records": 128,
    "maximum_requirements": 32, "maximum_requirement_memberships": 1024,
    "maximum_witness_edges": 256, "requirements": (),
    **{name: _D(value) for name, value in (
        ("max_evidence_age_seconds", "60.000000"), ("max_capture_lag_seconds", "20.000000"),
        ("independence_group_weight_cap", "1.000000"),
        ("correlation_group_weight_cap", "1.000000"),
        ("contradiction_no_probability_max", "0.250000"),
        ("contradiction_yes_probability_min", "0.750000"),
        ("contradiction_watch_score", "0.250000"), ("contradiction_block_score", "0.750000"),
        ("publish_probability_floor", "0.110000"), ("publish_probability_ceiling", "0.890000"))},
}
def _digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()

def _mode_config(mode: str) -> TeamEvidenceAggregationConfig:
    values = dict(BASE_CONFIG_VALUES)
    if mode in ("watch", "blocked"):
        values["requirements"] = (TeamEvidenceRequirement(
            requirement_id=f"req:{mode}", minimum_witness_count=1,
            minimum_effective_weight=_D("0.000000"), unmet_status=mode),)
    return TeamEvidenceAggregationConfig(**values)

def _record(evaluated_at: datetime) -> TeamEvidenceAggregationRecord:
    # Record times stay a fixed distance before evaluated_at so the evidence
    # is always fresh (max_evidence_age_seconds=60) at every proof offset.
    d = _digest("alpha")
    anchor = evaluated_at - FRESHNESS_ANCHOR
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(
            source_lineage_id="lineage:alpha", source_lineage_digest=d),
        capture=TeamEvidenceCapture(
            capture_id="capture:alpha", capture_digest=d,
            source_lineage_id="lineage:alpha", source_lineage_digest=d,
            content_digest=d, captured_at=anchor + timedelta(seconds=5)),
        evidence_revision=TeamEvidenceRevision(
            evidence_revision_id="evidence:alpha", evidence_revision_digest=d,
            previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
            source_lineage_id="lineage:alpha", source_lineage_digest=d,
            content_digest=d, requirement_ids=(),
            freshness_anchor_at=anchor, recorded_at=anchor + timedelta(seconds=10)),
        assessment_revision=TeamEvidenceAssessmentRevision(
            assessment_revision_id="assessment:alpha", assessment_revision_digest=d,
            previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
            evidence_revision_id="evidence:alpha", evidence_revision_digest=d,
            assessed_at=anchor + timedelta(seconds=15),
            probability_yes=_D("0.600000"),
            requested_weight=_D("0.200000"), rationale_digest=d,
            independence_key="ind:alpha", correlation_key="corr:alpha"))

def _aggregation_input(
    record: TeamEvidenceAggregationRecord, evaluated_at: datetime,
) -> TeamEvidenceAggregationInput:
    return TeamEvidenceAggregationInput(
        evaluated_at=evaluated_at, records=(record,),
        current_revisions=(TeamEvidenceCurrentRevisionSelection(
            evidence_revision_id=record.evidence_revision.evidence_revision_id,
            evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
            assessment_revision_id=record.assessment_revision.assessment_revision_id,
            assessment_revision_digest=(record.assessment_revision.assessment_revision_digest)),))

def _scope(extra_pair: tuple[str, str] | None = None) -> TeamForecastEvaluationScope:
    domain_context = (("team_id", "crypto_btc"), ("market_slug", "will-btc-105k"))
    if extra_pair is not None: domain_context += (extra_pair,)
    return TeamForecastEvaluationScope(
        scope_version=SCOPE_VERSION, domain_context=domain_context,
        provenance=("gamma:market/12345", "clob:book/0xabc"))

def _metadata(run_label: str) -> TeamForecastRunMetadata:
    return TeamForecastRunMetadata(
        run_label=run_label, generator_version="node5-gen-v1",
        prompt_version="team-forecast-prompt-v3", started_at=RUN_STARTED_AT,
        completed_at=RUN_COMPLETED_AT)

def _receipts(record: TeamEvidenceAggregationRecord) -> tuple[TeamForecastEvaluatorReceipt, ...]:
    capture_id = record.capture.capture_id
    identity = (record.source_lineage.source_lineage_id, capture_id,
                record.evidence_revision.evidence_revision_id,
                record.assessment_revision.assessment_revision_id)
    return (
        TeamForecastEvaluatorReceipt(
            evaluator_input_id=f"evaluator:{capture_id}",
            input_digest=_digest(f"evaluator-input:{capture_id}"),
            receipt_time=RECEIPT_TIME, classification="accepted",
            accepted_record_identity=identity, reason_codes=("evaluator_submitted",)),
        TeamForecastEvaluatorReceipt(
            evaluator_input_id="evaluator:rejected-1",
            input_digest=_digest("evaluator-input:rejected-1"),
            receipt_time=RECEIPT_TIME, classification="rejected",
            accepted_record_identity=None, reason_codes=(
                "evaluator_declined", "format_rejected")))

def _forecast_template() -> TeamForecastPacket:
    return TeamForecastPacket(
        forecast_id="forecast-template-001", team_id="crypto_btc",
        condition_id="0xdisposableproof", question="Will BTC close above $105,000?",
        market_slug="will-btc-105k", category_id="finance.crypto.btc",
        event_template="crypto_price_threshold", selected_side="yes",
        forecast_probability=_D("0.500000"), confidence=_D("0.700000"),
        evidence_quality=_D("0.650000"), data_freshness_score=_D("0.900000"),
        resolution_risk=_D("0.120000"), base_rate=_D("0.540000"),
        market_implied_probability_observed=_D("0.570000"),
        reason_codes=("aggregation_ready",), memory_references=("btc-memory-2026-q2",),
        source_references=("source-etf-flow-dashboard",),
        known_failure_modes=("weekend_liquidity_gap",),
        config_version="team-forecast-v0", prompt_version="team-forecast-prompt-v3",
        generated_at=RUN_STARTED_AT)

def _evidence_template(record: TeamEvidenceAggregationRecord) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id="evidence-template-001", team_id="crypto_btc",
        market_slug="will-btc-105k",
        source_id=f"source-{record.source_lineage.source_lineage_id}",
        source_type="team_evaluator", data_timestamp=RECEIPT_TIME,
        data_freshness_seconds=60, evidence_type="team_assessment",
        evidence_text="Evaluator assessment bound to the accepted record identity.",
        weight=record.assessment_revision.requested_weight,
        reason_codes=("evaluator_submitted",))

def _envelope(
    mode: str, run_label: str, *, evaluated_at: datetime,
    extra_scope_pair: tuple[str, str] | None = None,
) -> TeamForecastBuildEnvelope:
    config = _mode_config(mode)
    record = _record(evaluated_at)
    aggregation_input = _aggregation_input(record, evaluated_at)
    result = build_team_evidence_aggregation_result(aggregation_input, config=config)
    ready = mode == "ready"
    envelope = build_team_forecast_build_envelope(
        result, aggregation_input=aggregation_input, config=config,
        scope=_scope(extra_scope_pair), run_metadata=_metadata(run_label),
        evaluator_receipts=_receipts(record),
        legacy_forecast_packet=_forecast_template() if ready else None,
        legacy_evidence_packets=(_evidence_template(record),) if ready else ())
    assert envelope.evaluation_scope_payload["node2_result"]["result"]["status"] == mode
    return envelope

def _forge(
    base: TeamForecastBuildEnvelope, changes: dict[str, Any],
) -> TeamForecastBuildEnvelope:
    forged = object.__new__(type(base))
    for name in type(base).__slots__:
        object.__setattr__(forged, name, getattr(base, name))
    for name, value in changes.items():
        object.__setattr__(forged, name, value)
    return forged

def _orphan_shapes(envelope: TeamForecastBuildEnvelope) -> dict[str, TeamForecastBuildEnvelope]:
    without_run_metadata = dict(envelope.evaluation_scope_payload)
    del without_run_metadata["run_metadata"]
    return {
        "tea_id mismatch": _forge(envelope, {"tea_id": "tea:v1:" + "f" * 64}),
        "run_metadata absent": _forge(
            envelope, {"evaluation_scope_payload": without_run_metadata}),
        "tfr_id mismatch": _forge(envelope, {"tfr_id": "tfr:v1:" + "f" * 64}),
    }

# Test-owned psycopg helpers (smoke-test precedent); cleanup deletes only this run's rows.
def _with_direct_connection(dsn: str, operation: Any) -> Any:
    import psycopg
    connection = psycopg.connect(dsn)
    try:
        return operation(connection)
    finally:
        connection.close()

def _run_sql(dsn: str, sql: str, params: tuple = (), *, commit: bool = False) -> Any:
    def operation(connection: Any) -> Any:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchone() if cursor.description else None
        finally:
            cursor.close()
        if commit: connection.commit()
        return result
    return _with_direct_connection(dsn, operation)

def _probe_dedicated_database(dsn: str) -> None:
    database_name, table_count, index_count = _run_sql(
        dsn,
        "select current_database(), (select count(*) from information_schema.tables "
        " where table_schema = 'public' and table_name = %s), (select count(*) from pg_indexes "
        " where schemaname = 'public' and tablename = %s)",
        (TABLE_NAME, TABLE_NAME))
    assert database_name == DEDICATED_DATABASE_NAME, "dedicated disposable database required"
    assert table_count == 1, f"migration not applied: {TABLE_NAME} is missing"
    assert index_count >= 2, "migration incomplete: partial indexes are missing"

def _count_rows(dsn: str, tea_id: str) -> int:
    return _run_sql(dsn, f"select count(*) from {TABLE_NAME} where tea_id = %s", (tea_id,))[0]

def _delete_attempt_rows(dsn: str, tea_ids: tuple[str, ...]) -> None:
    if tea_ids:
        _run_sql(dsn, f"delete from public.{TABLE_NAME} where tea_id = any(%s)",
                 (list(tea_ids),), commit=True)

def _expected_row(envelope: TeamForecastBuildEnvelope) -> TeamEvaluationAttemptDbRow:
    return team_evaluation_attempt_to_db_row(
        tea_id=envelope.tea_id, tfr_id=envelope.tfr_id,
        evaluation_scope_payload=envelope.evaluation_scope_payload)

def _assert_row_round_trip(row: TeamEvaluationAttemptDbRow,
                           envelope: TeamForecastBuildEnvelope) -> None:
    expected = _expected_row(envelope)
    for f in fields(TeamEvaluationAttemptDbRow):
        assert getattr(row, f.name) == getattr(expected, f.name), (envelope.tea_id, f.name)

# The authorized disposable proof: one gated test, one redacted evidence block.
def test_team_evidence_aggregation_attempt_disposable_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = _disposable_dsn()
    import polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg as adapter
    import psycopg
    writer = adapter.insert_team_evaluation_attempts_with_psycopg
    _probe_dedicated_database(dsn)
    run_label = f"node5-disposable-proof-{uuid4().hex}"
    attempted_tea_ids: list[str] = []
    try:
        # Proof 1: ready/watch/blocked round trip through the real builders.
        envelopes = {s: _envelope(s, run_label, evaluated_at=BASE_TIME)
                     for s in STATUS_ORDER}
        attempted_tea_ids.extend(e.tea_id for e in envelopes.values())
        batch_results = writer(dsn, tuple(envelopes[s] for s in STATUS_ORDER))
        assert tuple(r.inserted for r in batch_results) == (True, True, True)
        for status in STATUS_ORDER:
            rows = _load_attempts(dsn, tfr_id=envelopes[status].tfr_id)
            assert len(rows) == 1
            _assert_row_round_trip(rows[0], envelopes[status])
            assert rows[0].status == status
            assert rows[0].hard_flag is _expected_row(envelopes[status]).hard_flag

        # Proof 2: retry idempotency on the same ready envelope.
        ready_envelope = envelopes["ready"]
        retry_first_inserted = batch_results[0].inserted is True
        assert _count_rows(dsn, ready_envelope.tea_id) == 1
        retry_second_inserted = writer(dsn, (ready_envelope,))[0].inserted is False
        assert retry_second_inserted
        _assert_row_round_trip(
            _load_attempts(dsn, tfr_id=ready_envelope.tfr_id)[0], ready_envelope)
        retry_row_count_stable = _count_rows(dsn, ready_envelope.tea_id) == 1
        assert retry_row_count_stable

        # Proof 3: every orphan shape is rejected before any connection; the
        # connect tripwire fails on any connect, and the remote-DSN sweep
        # proves the orphan error precedes DSN validation itself.
        def _forbidden_connect(*_args: Any, **_kwargs: Any) -> Any:
            raise AssertionError("orphan rejection must happen before any connect")

        monkeypatch.setattr(adapter, "_connect", _forbidden_connect)
        monkeypatch.setattr(psycopg, "connect", _forbidden_connect)
        for shape, orphan in _orphan_shapes(ready_envelope).items():
            with pytest.raises(ValueError, match=ORPHAN_SHAPE_ANCHORS[shape]):
                writer(dsn, (orphan,))
            with pytest.raises(ValueError) as remote_error:
                writer(REMOTE_DSN_PROBE, (orphan,))
            remote_message = str(remote_error.value)
            assert DSN_VALIDATOR_MESSAGE_MARKER not in remote_message, (
                "orphan rejection must precede DSN validation")
            assert "super-secret-token" not in remote_message
            assert "db.remote.example.com" not in remote_message
        monkeypatch.undo()

        # Proof 4: a real-built envelope whose jsonb payload carries a NUL
        # character passes every Python-side check and fails only at INSERT,
        # rolling the whole batch back so zero rows remain.
        valid_envelope = _envelope(
            "ready", run_label, evaluated_at=BASE_TIME + timedelta(seconds=600))
        broken_envelope = _envelope(
            "ready", run_label, evaluated_at=BASE_TIME + timedelta(seconds=660),
            extra_scope_pair=("nul_probe", f"trigger-{uuid4().hex}\x00fail"))
        attempted_tea_ids.extend((valid_envelope.tea_id, broken_envelope.tea_id))
        with pytest.raises(Exception):
            writer(dsn, (valid_envelope, broken_envelope))
        rollback_zero_rows = (
            _count_rows(dsn, valid_envelope.tea_id) == 0
            and _count_rows(dsn, broken_envelope.tea_id) == 0)
        assert rollback_zero_rows

        # Proof 5: latest-attempt ordering never bypasses a newer blocked row.
        # tfr_id hashes tea_id plus run_metadata, so ordering is proven within
        # the plan's (scope_version, scope_key) grouping, plus each tfr_id.
        probe_pair = ("latest_probe", run_label)
        ready_later = _envelope(
            "ready", run_label, evaluated_at=BASE_TIME + timedelta(seconds=1200),
            extra_scope_pair=probe_pair)
        blocked_later = _envelope(
            "blocked", run_label, evaluated_at=BASE_TIME + timedelta(seconds=1260),
            extra_scope_pair=probe_pair)
        attempted_tea_ids.extend((ready_later.tea_id, blocked_later.tea_id))
        ordering = writer(dsn, (ready_later, blocked_later))
        assert tuple(r.inserted for r in ordering) == (True, True)
        kwargs = {"scope_version": SCOPE_VERSION,
                  "scope_key": _expected_row(blocked_later).scope_key}
        scope_rows = _load_attempts(dsn, **kwargs)
        assert len(scope_rows) == 2
        assert [r.tea_id for r in scope_rows] == [blocked_later.tea_id, ready_later.tea_id]
        assert [r.status for r in scope_rows] == ["blocked", "ready"]
        latest_by_scope = _load_attempts(dsn, latest=True, **kwargs)
        assert latest_by_scope is not None and latest_by_scope.status == "blocked"
        assert latest_by_scope.tea_id == blocked_later.tea_id
        latest_by_run = _load_attempts(dsn, latest=True, tfr_id=blocked_later.tfr_id)
        assert latest_by_run is not None and latest_by_run.tea_id == blocked_later.tea_id

        for line in (
            f"database_name={DEDICATED_DATABASE_NAME}",
            "migration_apply=pass",
            "status_round_trip=ready,watch,blocked",
            f"retry_first_inserted={str(retry_first_inserted).lower()}",
            f"retry_second_inserted={str(retry_second_inserted).lower()}",
            f"retry_row_count_stable={str(retry_row_count_stable).lower()}",
            "orphan_rejected_before_connect=true",
            f"rollback_zero_rows={str(rollback_zero_rows).lower()}",
            "dsn=redacted"):
            print(line, flush=True)
    finally:
        _delete_attempt_rows(dsn, tuple(dict.fromkeys(attempted_tea_ids)))

# Offline gate tests: no connection is made; skip messages never leak the DSN.
def test_disposable_gate_skips_by_default_with_set_flag_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(RUN_GATE_ENV_VAR, raising=False)
    with pytest.raises(pytest.skip.Exception) as exc_info:
        _disposable_dsn()
    message = str(exc_info.value)
    assert RUN_GATE_ENV_VAR in message and "=1" in message

def test_disposable_dsn_skips_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RUN_GATE_ENV_VAR, "1")
    monkeypatch.delenv(TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR, raising=False)
    with pytest.raises(pytest.skip.Exception) as exc_info:
        _disposable_dsn()
    assert TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR in str(exc_info.value)

def test_disposable_dsn_rejects_remote_dsn_without_leaking_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(RUN_GATE_ENV_VAR, "1")
    monkeypatch.setenv(TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR, REMOTE_DSN_PROBE)
    with pytest.raises(pytest.skip.Exception) as exc_info:
        _disposable_dsn()
    message = str(exc_info.value)
    assert TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR in message
    assert "local Supabase/Postgres" in message
    assert "super-secret-token" not in message and "db.remote.example.com" not in message
