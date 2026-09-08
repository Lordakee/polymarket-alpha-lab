"""Node 4 row-codec contract tests: team evaluation attempts, offline.

Governing plan: docs/superpowers/plans/2026-07-13-team-evidence-aggregation-schema.md; fixtures build
real Node 3 payloads via build_team_forecast_build_envelope over genuine Node 2 results.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json

import pytest
import polymarket_alpha_lab.team_evidence_aggregation_types as n2t
from polymarket_alpha_lab.team_evidence_aggregation import build_team_evidence_aggregation_result
import polymarket_alpha_lab.team_forecast_build_envelope as n3
from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket, TeamForecastPacket
import polymarket_alpha_lab.team_evidence_aggregation_db_row as n4

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)
RECEIPT_TIME = datetime(2026, 7, 13, 8, 59, 30, tzinfo=timezone.utc)
RUN_STARTED_AT = datetime(2026, 7, 13, 9, tzinfo=timezone.utc)
MARKET_SLUG = "will-btc-close-above-105k-on-july-4"
SCOPE_VERSION = "team-evidence-aggregation-schema-test-v1"
PAYLOAD_KEYS = ("scope_version", "domain_context", "provenance", "run_metadata",
                "evaluator_receipts", "node2_config", "node2_input", "node2_result")
ROW_SCALARS = ("tea_id", "tfr_id", "attempted_at", "status", "hard_flag", "scope_version",
               "scope_key", "config_version", "config_digest", "diagnostic_record_count",
               "arithmetic_record_count", "payload_sha256")
HARD_FLAG_SECTIONS = (("run_metadata",), ("evaluator_receipts", 0), ("node2_result", "result"))


def digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


def canonical(value):
    return json.dumps(value, allow_nan=False, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def node2_config(requirements=()):
    return n2t.TeamEvidenceAggregationConfig(
        "generic-test-v1", Decimal("60.000000"), Decimal("20.000000"), Decimal("1.000000"), Decimal("1.000000"), 2,
        Decimal("0.250000"), Decimal("0.750000"), Decimal("0.250000"), Decimal("0.750000"),
        Decimal("0.110000"), Decimal("0.890000"), 128, 32, 1024, 256, requirements)


def req(requirement_id, unmet_status):
    return n2t.TeamEvidenceRequirement(requirement_id, 1, Decimal("0.000000"), unmet_status)


def root_record(stem, probability_yes=Decimal("0.600000"),
                requested_weight=Decimal("0.200000")):
    lid, ld, cd = f"lineage:{stem}", digest(f"lineage-digest:{stem}"), digest(f"content:{stem}")
    t50, t55, t60, t65 = (BASE_TIME + timedelta(seconds=s) for s in (50, 55, 60, 65))
    cap = n2t.TeamEvidenceCapture(f"capture:{stem}", digest(f"capture-digest:{stem}"), lid, ld, cd, t55)
    rev = n2t.TeamEvidenceRevision(f"evidence:{stem}", digest(f"evidence-digest:{stem}"), None, None,
                                   lid, ld, cd, (), t50, t60)
    asm = n2t.TeamEvidenceAssessmentRevision(f"assessment:{stem}", digest(f"assessment-digest:{stem}"), None, None,
                                             f"evidence:{stem}", digest(f"evidence-digest:{stem}"), t65, probability_yes,
                                             requested_weight, digest(f"rationale:{stem}"), f"ind:{stem}", f"corr:{stem}")
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
        "forecast-template-001", "crypto_btc", "0xnode4condition", MARKET_SLUG,
        "Will BTC close above $105,000 on July 4?", "finance.crypto.btc", "crypto_price_threshold", "yes",
        Decimal("0.500000"), Decimal("0.700000"), Decimal("0.650000"), Decimal("0.900000"), Decimal("0.120000"),
        Decimal("0.540000"), Decimal("0.570000"), ("aggregation_ready",), ("btc-memory-2026-q2",),
        ("source-etf-flow-dashboard",), ("weekend_liquidity_gap",), "team-forecast-v0",
        "team-forecast-prompt-v3", RUN_STARTED_AT)


def evidence_template(record) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        "evidence-template-001", "crypto_btc", MARKET_SLUG, f"source-{record.source_lineage.source_lineage_id}",
        "team_evaluator", RECEIPT_TIME, 60, "team_assessment",
        "Evaluator assessment bound to the accepted record identity.",
        record.assessment_revision.requested_weight, ("evaluator_submitted",))


def make_case(mode="ready"):
    requirements = {"watch": (req("req:watch", "watch"),),
                    "blocked": (req("req:blocked", "blocked"),)}.get(mode, ())
    records = ()
    if mode in ("ready", "watch", "blocked"):
        records = (root_record("alpha"),)
    if mode == "contradiction_blocked":
        records = (root_record("cy", Decimal("0.750000"), Decimal("0.500000")),
                   root_record("cn", Decimal("0.250000"), Decimal("0.300000")))
    config_value = node2_config(requirements)
    result = build_team_evidence_aggregation_result(aggregation_input(records), config=config_value)
    envelope = n3.build_team_forecast_build_envelope(
        result, aggregation_input=aggregation_input(records), config=config_value,
        scope=n3.TeamForecastEvaluationScope(SCOPE_VERSION, (("team_id", "crypto_btc"), ("market_slug", MARKET_SLUG)),
                                             ("gamma:market/12345", "clob:book/0xabc")),
        run_metadata=n3.TeamForecastRunMetadata(
            "node4-row-codec-001", "team-forecast-generator-v1", "team-forecast-prompt-v3",
            RUN_STARTED_AT, RUN_STARTED_AT + timedelta(minutes=5)),
        evaluator_receipts=tuple(accepted_receipt(r) for r in records),
        legacy_forecast_packet=forecast_template() if mode == "ready" else None,
        legacy_evidence_packets=tuple(evidence_template(r) for r in records) if mode == "ready" else ())
    return envelope.tea_id, envelope.tfr_id, n3.team_forecast_evaluation_scope_payload(envelope)


def row_for(mode="ready"):
    tea_id, tfr_id, payload = make_case(mode)
    return n4.team_evaluation_attempt_to_db_row(tea_id=tea_id, tfr_id=tfr_id, evaluation_scope_payload=payload)


def row_with_payload(row, payload, **overrides):
    values = {name: getattr(row, name) for name in ROW_SCALARS} | overrides
    return n4.TeamEvaluationAttemptDbRow(evaluation_scope_payload=payload, **values)


def tweak(payload, path, value):
    copied = target = json.loads(json.dumps(payload, allow_nan=False))
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return copied


def test_to_db_row_promotes_columns_hashes_and_parameters():
    tea_id, tfr_id, payload = make_case("ready")
    row = n4.team_evaluation_attempt_to_db_row(
        tea_id=tea_id, tfr_id=tfr_id, evaluation_scope_payload=payload)
    result = payload["node2_result"]["result"]
    assert row.tea_id == tea_id and row.tfr_id == tfr_id
    assert row.attempted_at == EVALUATED_AT and row.attempted_at != RUN_STARTED_AT
    assert row.status == result["status"] == "ready"
    assert row.scope_version == payload["scope_version"] == SCOPE_VERSION
    assert row.config_version == result["config_version"] and row.config_digest == result["config_digest"]
    assert row.diagnostic_record_count == result["diagnostic_record_count"] == 1 and (
        row.arithmetic_record_count == result["arithmetic_record_count"] == 1)
    assert row.hard_flag is False and row.paper_only is True and row.readonly is True
    assert row.scope_key == sha256(canonical(payload["domain_context"])).hexdigest()
    assert row.scope_key != result["core_digest"]
    assert row.payload_sha256 == row_for("ready").payload_sha256 == sha256(canonical(payload)).hexdigest()
    assert row.evaluation_scope_payload == payload  # lossless nested evidence
    assert row.evaluation_scope_payload["provenance"] == ["clob:book/0xabc", "gamma:market/12345"]
    for path, value in (  # sensitive to any nested change
        (("node2_config", "config", "publish_probability_floor"), "0.120000"),
        (("evaluator_receipts", 0, "reason_codes"), ["evaluator_submitted", "late"]),
    ):
        mutated = n4.team_evaluation_attempt_to_db_row(
            tea_id=tea_id, tfr_id=tfr_id, evaluation_scope_payload=tweak(payload, path, value))
        assert mutated.payload_sha256 != row.payload_sha256
    for key in PAYLOAD_KEYS:  # exact eight-key top-level allowlist
        incomplete = json.loads(json.dumps(payload, allow_nan=False)); del incomplete[key]
        with pytest.raises(ValueError, match="top-level keys must be exactly"):
            n4.team_evaluation_attempt_to_db_row(tea_id=tea_id, tfr_id=tfr_id,
                                                 evaluation_scope_payload=incomplete)
    with pytest.raises(ValueError, match="top-level keys must be exactly"):  # extra key rejected
        n4.team_evaluation_attempt_to_db_row(tea_id=tea_id, tfr_id=tfr_id, evaluation_scope_payload=tweak(
            payload, ("decision",), "invented"))
    parameters = n4.team_evaluation_attempt_row_parameters(row)  # JSON-safe output
    assert set(parameters) == set(ROW_SCALARS) | {
        "evaluation_scope_payload", "paper_only", "report_only", "readonly"}
    assert parameters["attempted_at"] == "2026-01-01T00:01:40.000000+00:00"
    assert parameters["scope_key"] == row.scope_key and parameters["hard_flag"] is False
    assert parameters["paper_only"] is True and parameters["readonly"] is True
    assert json.dumps(parameters, allow_nan=False)
    assert parameters["evaluation_scope_payload"] == payload and parameters[
        "evaluation_scope_payload"] is not row.evaluation_scope_payload  # fresh copy


@pytest.mark.parametrize("mode", ("ready", "watch", "blocked", "zero", "contradiction_blocked"))
def test_status_domain_hard_flag_and_null_zero_absent_distinct(mode):
    tea_id, tfr_id, payload = make_case(mode)
    row = n4.team_evaluation_attempt_to_db_row(tea_id=tea_id, tfr_id=tfr_id, evaluation_scope_payload=payload)
    result = payload["node2_result"]["result"]
    assert row.status == result["status"] in ("ready", "watch", "blocked")
    if mode == "zero":  # null, zero, and absent stay distinct; Decimals are strings
        assert result["publishable_probability_yes"] is None and "decision" not in result
        assert type(result["diagnostic_record_count"]) is int and (
            result["diagnostic_record_count"] == row.diagnostic_record_count == 0)
        assert result["requested_weight_total"] == "0.000000"
    if mode == "watch":
        assert result["requested_weight_total"] == "0.200000"
        assert type(result["requested_weight_total"]) is str
    if mode == "contradiction_blocked":  # hard flag only at blocked-level contradiction
        assert row.status == "blocked" and row.hard_flag is True
        ids = [entry["evaluator_input_id"] for entry in payload["evaluator_receipts"]]
        assert ids == sorted(ids) and len(ids) == 2  # nested array order preserved
        with pytest.raises(ValueError, match="hard_flag must match"):
            row_with_payload(row, tweak(payload, ("node2_result", "result", "contradiction", "status"), "none"))
    if mode == "ready":  # 'pass' is outside the status domain
        with pytest.raises(ValueError, match="status must be one of"):
            n4.team_evaluation_attempt_to_db_row(tea_id=tea_id, tfr_id=tfr_id, evaluation_scope_payload=tweak(
                payload, ("node2_result", "result", "status"), "pass"))


def test_false_hard_flags_rejected_in_payload_and_row():
    row = row_for("ready")
    for flag_name in ("paper_only", "report_only", "readonly"):
        for section in HARD_FLAG_SECTIONS:
            with pytest.raises(ValueError, match=flag_name):
                row_with_payload(row, tweak(row.evaluation_scope_payload, (*section, flag_name), False))
        values = {name: getattr(row, name) for name in ROW_SCALARS} | {flag_name: False}
        with pytest.raises(ValueError, match=flag_name):
            n4.TeamEvaluationAttemptDbRow(evaluation_scope_payload=row.evaluation_scope_payload, **values)
