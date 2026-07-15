from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_source_claim_memory_quorum_scorecard_report"
)
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_source_claim_memory_quorum_scorecard_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 9, 30, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class StringSubclass(str):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    event_key: str = "event_alpha",
    claim_key: str = "claim_alpha",
    evidence_key: str = "evidence_alpha",
    **overrides: object,
):
    module = api()
    values: dict[str, object] = {
        "event_key": event_key,
        "claim_key": claim_key,
        "evidence_key": evidence_key,
        "captured_at": GENERATED_AT,
        "claim_present": True,
        "parse_confidence": d("0.800000"),
        "memory_confidence": d("0.900000"),
        "private_material": (
            "candidate-secret-001",
            "market-secret-001",
            "https://private.example/raw-item",
            "raw text must stay private",
            "postgres://private-dsn",
            "private_table",
            "private-token",
        ),
    }
    values.update(overrides)
    return module.ResearchEventSourceClaimMemoryQuorumObservation(**values)


def scorecard_report(*items: object, **overrides: object):
    module = api()
    config = overrides.pop("config", None)
    public_payload = overrides.pop("public_payload", ())
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_research_event_source_claim_memory_quorum_scorecard_report(
        list(items),
        config=config,
        generated_at=generated_at,
        public_payload=public_payload,
    )


def assert_no_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_scalars(item)


def assert_no_decimal_objects(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal object in public payload {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_objects(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_objects(item)


def assert_no_raw_leaks(value: Any) -> None:
    forbidden = {
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    }
    encoded = json.dumps(value, sort_keys=True).lower()
    for word in forbidden:
        assert word not in encoded


def canonical_sha256(payload: dict[str, Any]) -> str:
    unsigned = copy.deepcopy(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = copy.deepcopy(payload)
    rows = resigned.get("rows", [])
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                row["derived_validation_digest"] = canonical_sha256(row)
    resigned["derived_validation_digest"] = canonical_sha256(resigned)
    return resigned


def test_module_exports_public_api_contract() -> None:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None

    module = api()
    assert MODULE_PATH.exists()
    assert set(module.REPORT_STATUSES) == {"pass", "watch", "block"}
    assert module.DEFAULT_RESEARCH_EVENT_SOURCE_CLAIM_MEMORY_QUORUM_SCORECARD_CONFIG_VERSION
    expected_exports = {
        "ResearchEventSourceClaimMemoryQuorumConfig",
        "ResearchEventSourceClaimMemoryQuorumObservation",
        "ResearchEventSourceClaimMemoryQuorumPublicPayloadItem",
        "ResearchEventSourceClaimMemoryQuorumRow",
        "ResearchEventSourceClaimMemoryQuorumReport",
        "build_research_event_source_claim_memory_quorum_scorecard_report",
        "research_event_source_claim_memory_quorum_scorecard_report_payload",
    }
    assert expected_exports.issubset(set(module.__all__))


def test_dataclass_and_public_payload_schemas_are_exact_and_final() -> None:
    module = api()
    expected_fields = {
        module.ResearchEventSourceClaimMemoryQuorumConfig: (
            "config_version",
            "min_agreeing_evidence_count",
            "min_memory_quorum_count",
            "min_memory_confidence",
            "watch_quorum_score",
            "pass_quorum_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchEventSourceClaimMemoryQuorumObservation: (
            "event_key",
            "claim_key",
            "evidence_key",
            "captured_at",
            "claim_present",
            "parse_confidence",
            "memory_confidence",
            "private_material",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem: (
            "key",
            "value",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchEventSourceClaimMemoryQuorumRow: (
            "event_key",
            "claim_key",
            "rank",
            "observation_count",
            "agreeing_evidence_count",
            "memory_quorum_count",
            "support_ratio",
            "average_parse_confidence",
            "average_memory_confidence",
            "quorum_score",
            "status",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchEventSourceClaimMemoryQuorumReport: (
            "generated_at",
            "config_version",
            "min_agreeing_evidence_count",
            "min_memory_quorum_count",
            "min_memory_confidence",
            "watch_quorum_score",
            "pass_quorum_score",
            "status",
            "event_claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_quorum_score",
            "rows",
            "reason_codes",
            "public_payload",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    for class_type, names in expected_fields.items():
        assert tuple(field.name for field in fields(class_type)) == names
        with pytest.raises(TypeError):
            type(f"Bad{class_type.__name__}", (class_type,), {})

    report = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
        observation("event_alpha", "claim_alpha", "evidence_b"),
    )
    payload = report.payload
    assert tuple(payload) == expected_fields[
        module.ResearchEventSourceClaimMemoryQuorumReport
    ]
    assert tuple(payload["rows"][0]) == expected_fields[
        module.ResearchEventSourceClaimMemoryQuorumRow
    ]


def test_scorecard_rollup_and_statuses_are_deterministic() -> None:
    report = scorecard_report(
        observation("event_pass", "claim_pass", "evidence_pass_a"),
        observation("event_pass", "claim_pass", "evidence_pass_b"),
        observation(
            "event_watch",
            "claim_watch",
            "evidence_watch_a",
            parse_confidence=d("0.500000"),
            memory_confidence=d("0.550000"),
        ),
        observation(
            "event_watch",
            "claim_watch",
            "evidence_watch_b",
            parse_confidence=d("0.500000"),
            memory_confidence=d("0.550000"),
        ),
        observation("event_block", "claim_block", "evidence_block_a"),
    )

    assert is_dataclass(report)
    assert report.event_claim_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_quorum_score == d("0.827778")
    assert report.status == "block"
    assert report.reason_codes == (
        "claim_memory_quorum_scorecard_block",
        "claim_memory_quorum_block",
        "claim_memory_quorum_watch",
        "claim_memory_quorum_pass",
    )

    blocked, watched, passed = report.rows
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.event_key == "event_block"
    assert blocked.claim_key == "claim_block"
    assert blocked.observation_count == d("1")
    assert blocked.agreeing_evidence_count == d("1")
    assert blocked.memory_quorum_count == d("1")
    assert blocked.support_ratio == d("1.000000")
    assert blocked.average_parse_confidence == d("0.800000")
    assert blocked.average_memory_confidence == d("0.900000")
    assert blocked.quorum_score == d("0.900000")
    assert blocked.status == "block"
    assert "missing_agreeing_evidence_quorum" in blocked.reason_codes

    assert watched.event_key == "event_watch"
    assert watched.quorum_score == d("0.683333")
    assert watched.status == "watch"
    assert passed.event_key == "event_pass"
    assert passed.quorum_score == d("0.900000")
    assert passed.status == "pass"


def test_source_evidence_is_counted_once_and_input_order_is_irrelevant() -> None:
    evidence_a = observation("event_alpha", "claim_alpha", "evidence_a")
    evidence_b = observation("event_alpha", "claim_alpha", "evidence_b")

    deduplicated = scorecard_report(evidence_a, evidence_b)
    repeated = scorecard_report(evidence_b, evidence_a, evidence_a)

    assert repeated.payload == deduplicated.payload
    assert repeated.rows[0].observation_count == d("2")
    assert repeated.rows[0].agreeing_evidence_count == d("2")
    assert repeated.rows[0].memory_quorum_count == d("2")


def test_public_payload_is_stable_decimal_string_only_and_digest_checked() -> None:
    module = api()
    public_item = module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
        key="review_scope",
        value="event_claim_memory_quorum",
    )
    observations = (
        observation("event_alpha", "claim_alpha", "evidence_b"),
        observation("event_alpha", "claim_alpha", "evidence_a"),
    )
    report = scorecard_report(*observations, public_payload=(public_item,))
    repeated_report = scorecard_report(
        *reversed(observations),
        public_payload=(public_item,),
    )

    payload = module.research_event_source_claim_memory_quorum_scorecard_report_payload(
        report,
    )
    repeated_payload = (
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            repeated_report,
        )
    )

    assert payload == repeated_payload
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        repeated_payload,
        sort_keys=True,
    )
    assert payload["generated_at"] == "2026-07-09T09:30:00+00:00"
    assert payload["event_claim_count"] == "1"
    assert payload["average_quorum_score"] == "0.900000"
    assert payload["rows"][0]["quorum_score"] == "0.900000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_sha256(payload)
    assert payload["rows"][0]["derived_validation_digest"] == canonical_sha256(
        payload["rows"][0],
    )
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_scalars(payload)
    assert_no_decimal_objects(payload)
    assert_no_raw_leaks(payload)

    object.__setattr__(report.rows[0], "quorum_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            report,
        )


def test_public_payload_revalidates_in_memory_derived_fields_after_redigest() -> None:
    module = api()
    report = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
        observation("event_alpha", "claim_alpha", "evidence_b"),
    )

    object.__setattr__(report, "pass_count", d("9"))
    object.__setattr__(report, "derived_validation_digest", module._report_digest(report))

    with pytest.raises(ValueError, match="pass_count"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            report,
        )


def test_in_memory_redigest_cannot_authorize_signed_zero_payload() -> None:
    module = api()
    report = scorecard_report(
        observation(
            claim_present=False,
            parse_confidence=d("0.000000"),
            memory_confidence=d("0.000000"),
        ),
    )
    row = report.rows[0]

    object.__setattr__(row, "support_ratio", d("-0.000000"))
    object.__setattr__(row, "derived_validation_digest", module._row_digest(row))
    object.__setattr__(
        report,
        "derived_validation_digest",
        module._report_digest(report),
    )

    with pytest.raises(
        ValueError,
        match="canonical|derived_validation_digest|tamper",
    ):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            report,
        )


def test_public_payload_revalidates_nested_hard_flags_after_redigest() -> None:
    module = api()
    item = module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
        key="review_scope",
        value="event_claim_memory_quorum",
    )
    report = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
        public_payload=(item,),
    )

    object.__setattr__(item, "readonly", False)
    object.__setattr__(report, "derived_validation_digest", module._report_digest(report))

    with pytest.raises(ValueError, match="readonly"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            report,
        )


def test_report_revalidates_redigested_nested_row_consistency() -> None:
    module = api()
    report = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
        observation("event_alpha", "claim_alpha", "evidence_b"),
    )
    row = report.rows[0]

    object.__setattr__(row, "support_ratio", d("0.500000"))
    object.__setattr__(row, "derived_validation_digest", module._row_digest(row))

    with pytest.raises(ValueError, match="support_ratio"):
        replace(report, derived_validation_digest="")


def test_nested_public_dataclasses_revalidate_exact_fields() -> None:
    module = api()
    public_item = module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
        key="review_scope",
        value="event_claim_memory_quorum",
    )
    object.__setattr__(public_item, "key", "invalid key")
    with pytest.raises(ValueError, match="key"):
        scorecard_report(observation(), public_payload=(public_item,))

    report = scorecard_report(observation())
    row = report.rows[0]
    object.__setattr__(row, "event_key", "invalid key")
    object.__setattr__(row, "derived_validation_digest", module._row_digest(row))
    with pytest.raises(ValueError, match="event_key"):
        replace(report, derived_validation_digest="")


def test_config_version_is_fixed_and_payload_cannot_switch_versions() -> None:
    module = api()
    with pytest.raises(ValueError, match="config_version"):
        module.ResearchEventSourceClaimMemoryQuorumConfig(config_version="v2")

    payload = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
    ).payload
    payload["config_version"] = "v2"
    with pytest.raises(ValueError, match="config_version"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(payload),
        )


def test_public_payload_keys_must_be_unique() -> None:
    module = api()
    items = (
        module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
            key="review_scope",
            value="first",
        ),
        module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
            key="review_scope",
            value="second",
        ),
    )

    with pytest.raises(ValueError, match="duplicate|unique"):
        scorecard_report(observation(), public_payload=items)


def test_datetime_inputs_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        observation(captured_at=datetime(2026, 7, 9, 9, 30))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        scorecard_report(
            observation(),
            generated_at=datetime(2026, 7, 9, 9, 30),
        )


def test_observations_cannot_be_captured_after_report_generation() -> None:
    future_observation = observation(
        captured_at=GENERATED_AT + timedelta(microseconds=1),
    )

    with pytest.raises(ValueError, match="captured_at must not be after generated_at"):
        scorecard_report(future_observation)


def test_sequence_fields_reject_non_sequence_iterables() -> None:
    module = api()
    sample = observation()

    with pytest.raises(ValueError, match="observations must be a sequence"):
        module.build_research_event_source_claim_memory_quorum_scorecard_report(
            (item for item in (sample,)),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must be a sequence"):
        module.build_research_event_source_claim_memory_quorum_scorecard_report(
            object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="private_material must be a sequence"):
        observation(private_material=(item for item in ("private",)))

    public_item = module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
        key="review_scope",
        value="event_claim_memory_quorum",
    )
    with pytest.raises(ValueError, match="public_payload must be a sequence"):
        scorecard_report(
            sample,
            public_payload=(item for item in (public_item,)),
        )

    report = scorecard_report(sample)
    with pytest.raises(ValueError, match="rows must be a sequence"):
        replace(
            report,
            rows=(row for row in report.rows),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_codes must be a sequence"):
        replace(
            report.rows[0],
            reason_codes=(code for code in report.rows[0].reason_codes),
            derived_validation_digest="",
        )


def test_builder_revalidates_mutated_config_and_observation_inputs() -> None:
    module = api()
    config = module.ResearchEventSourceClaimMemoryQuorumConfig()
    object.__setattr__(config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        scorecard_report(observation(), config=config)

    sample = observation()
    object.__setattr__(sample, "claim_present", 1)
    with pytest.raises(ValueError, match="claim_present"):
        scorecard_report(sample)


def test_decimal_math_uses_fixed_context_and_normalizes_signed_zero() -> None:
    module = api()
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        config = module.ResearchEventSourceClaimMemoryQuorumConfig(
            min_memory_confidence=d("-0.000000"),
        )
        sample = observation(
            claim_present=False,
            parse_confidence=d("-0.000000"),
            memory_confidence=d("-0.000000"),
        )
        report = scorecard_report(sample, config=config)

    assert str(config.min_memory_confidence) == "0.000000"
    assert str(sample.parse_confidence) == "0.000000"
    assert str(sample.memory_confidence) == "0.000000"
    assert str(report.rows[0].support_ratio) == "0.000000"
    assert str(report.rows[0].average_parse_confidence) == "0.000000"
    assert str(report.rows[0].average_memory_confidence) == "0.000000"
    assert str(report.rows[0].quorum_score) == "0.000000"


@pytest.mark.parametrize(
    "value",
    (
        d("-0.0000001"),
        d("1.0000001"),
        d("NaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_ratio_validation_uses_raw_bounds_and_rejects_non_finite_values(
    value: Decimal,
) -> None:
    module = api()
    with pytest.raises(ValueError, match="finite|between 0 and 1"):
        module.ResearchEventSourceClaimMemoryQuorumConfig(
            min_memory_confidence=value,
        )
    with pytest.raises(ValueError, match="finite|between 0 and 1"):
        observation(parse_confidence=value)


def test_digest_tampering_and_invalid_statuses_are_rejected() -> None:
    report = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
        observation("event_alpha", "claim_alpha", "evidence_b"),
    )
    row = report.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(
            row,
            status=StringSubclass(row.status),
            derived_validation_digest="",
        )


def test_direct_rows_require_supported_canonical_reason_codes() -> None:
    row = scorecard_report(observation()).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            reason_codes=(*row.reason_codes, "unexpected_safe_reason"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            reason_codes=tuple(reversed(row.reason_codes)),
            derived_validation_digest="",
        )


def test_resigned_payload_recomputes_score_status_reasons_counts_rank_and_aggregates() -> None:
    module = api()
    report = scorecard_report(
        observation("event_pass", "claim_pass", "evidence_pass_a"),
        observation("event_pass", "claim_pass", "evidence_pass_b"),
        observation(
            "event_watch",
            "claim_watch",
            "evidence_watch_a",
            parse_confidence=d("0.500000"),
            memory_confidence=d("0.550000"),
        ),
        observation(
            "event_watch",
            "claim_watch",
            "evidence_watch_b",
            parse_confidence=d("0.500000"),
            memory_confidence=d("0.550000"),
        ),
        observation("event_block", "claim_block", "evidence_block_a"),
    )
    payload = report.payload

    score_mutation = copy.deepcopy(payload)
    score_mutation["rows"][0]["quorum_score"] = "0.100000"
    with pytest.raises(ValueError, match="quorum_score"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(score_mutation),
        )

    status_mutation = copy.deepcopy(payload)
    status_mutation["rows"][2]["status"] = "watch"
    status_mutation["rows"][2]["reason_codes"] = ["claim_memory_quorum_watch"]
    status_mutation["status"] = "block"
    status_mutation["pass_count"] = "0"
    status_mutation["watch_count"] = "2"
    status_mutation["reason_codes"] = [
        "claim_memory_quorum_scorecard_block",
        "claim_memory_quorum_block",
        "claim_memory_quorum_watch",
    ]
    with pytest.raises(ValueError, match="status|reason_codes"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(status_mutation),
        )

    count_mutation = copy.deepcopy(payload)
    count_mutation["pass_count"] = "9"
    with pytest.raises(ValueError, match="pass_count"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(count_mutation),
        )

    rank_mutation = copy.deepcopy(payload)
    rank_mutation["rows"][0]["rank"] = "2"
    rank_mutation["rows"][1]["rank"] = "1"
    with pytest.raises(ValueError, match="rank|rows"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(rank_mutation),
        )

    aggregate_mutation = copy.deepcopy(payload)
    aggregate_mutation["average_quorum_score"] = "0.100000"
    with pytest.raises(ValueError, match="average_quorum_score"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(aggregate_mutation),
        )


def test_resigned_payload_rejects_schema_drift_and_private_surfaces() -> None:
    module = api()
    payload = scorecard_report(
        observation("event_alpha", "claim_alpha", "evidence_a"),
        observation("event_alpha", "claim_alpha", "evidence_b"),
    ).payload

    extra_top_level = copy.deepcopy(payload)
    extra_top_level["unexpected_safe_key"] = "safe"
    with pytest.raises(ValueError, match="schema"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(extra_top_level),
        )

    extra_row_field = copy.deepcopy(payload)
    extra_row_field["rows"][0]["unexpected_safe_key"] = "safe"
    with pytest.raises(ValueError, match="schema"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(extra_row_field),
        )

    private_surface = copy.deepcopy(payload)
    private_surface["raw_url"] = "https://private.example/item"
    with pytest.raises(ValueError, match="schema|public payload"):
        module.research_event_source_claim_memory_quorum_scorecard_report_payload(
            resign_payload(private_surface),
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchEventSourceClaimMemoryQuorumConfig()
    sample = observation()
    report = scorecard_report(sample, observation(evidence_key="evidence_beta"))
    row = report.rows[0]

    for value in (config, sample, row, report):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(value, field.name) is True

    public_decimal_fields = {
        "min_agreeing_evidence_count",
        "min_memory_quorum_count",
        "min_memory_confidence",
        "watch_quorum_score",
        "pass_quorum_score",
        "rank",
        "observation_count",
        "agreeing_evidence_count",
        "memory_quorum_count",
        "support_ratio",
        "average_parse_confidence",
        "average_memory_confidence",
        "quorum_score",
        "event_claim_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_quorum_score",
    }
    for value in (config, sample, row, report):
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in public_decimal_fields:
                assert type(item) is Decimal
            assert type(item) is not float
            if type(item) is int:
                raise AssertionError(f"unexpected integer field {field.name}")

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchEventSourceClaimMemoryQuorumConfig(
            min_agreeing_evidence_count=2,
        )
    with pytest.raises(ValueError, match="Decimal"):
        observation(parse_confidence=0.8)
    with pytest.raises(ValueError, match="Decimal"):
        observation(memory_confidence=DecimalSubclass("0.8"))
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventSourceClaimMemoryQuorumConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
            key="review_scope",
            value="event_claim_memory_quorum",
            readonly=False,
        )


def test_public_payload_rejects_raw_leak_terms_and_unsafe_surfaces() -> None:
    module = api()
    forbidden = (
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "db",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )

    for word in forbidden:
        with pytest.raises(ValueError, match="public payload"):
            module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
                key=f"{word}_key",
                value="safe_scope",
            )
        with pytest.raises(ValueError, match="public payload"):
            module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
                key="review_scope",
                value=f"contains {word}",
            )

    for raw_value in (
        "https://private.example/raw-item",
        "postgres://private-dsn",
        "raw text must stay private",
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.ResearchEventSourceClaimMemoryQuorumPublicPayloadItem(
                key="review_scope",
                value=raw_value,
            )


def test_module_source_has_no_forbidden_runtime_surfaces() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_exact = {
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    }
    for word in forbidden_exact:
        assert word not in module_text
    for package_name in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite",
        "psycopg",
        "web3",
    ):
        assert package_name not in module_text
