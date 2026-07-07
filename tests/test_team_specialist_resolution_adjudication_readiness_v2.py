from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_resolution_adjudication_readiness_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(**overrides: object):
    module = api()
    values = {
        "team_id": "politics",
        "category_id": "politics",
        "specialist_id": "resolver_alpha",
        "adjudication_case_id": "case_presidential_nominee",
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "rule_familiarity_score": d("0.920000"),
        "official_source_coverage_score": d("0.900000"),
        "contradiction_handling_score": d("0.880000"),
        "seconds_until_close": d("7200.000000"),
        "prior_error_rate": d("0.010000"),
        "open_review_count": d("1"),
    }
    values.update(overrides)
    return module.TeamSpecialistResolutionAdjudicationReadinessInput(**values)


def report(input_row, *, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_resolution_adjudication_readiness_v2_report(
        input_row,
        config=cfg or module.TeamSpecialistResolutionAdjudicationReadinessConfig(),
        generated_at=generated_at,
    )


def assert_no_int_or_float(value: Any) -> None:
    assert type(value) is not int
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float(item)


def signed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    ready = dict(payload)
    payload_without_digest = {
        key: value for key, value in ready.items() if key != "derived_validation_digest"
    }
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    ready["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return ready


def test_clear_readiness_report_passes_with_decimal_payload_and_digest() -> None:
    module = api()
    readiness = report(readiness_input())

    assert is_dataclass(readiness)
    assert readiness.generated_at == GENERATED_AT
    assert readiness.config_version == (
        module.DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_VERSION
    )
    assert readiness.team_id == "politics"
    assert readiness.category_id == "politics"
    assert readiness.specialist_id == "resolver_alpha"
    assert readiness.adjudication_case_id == "case_presidential_nominee"
    assert readiness.readiness_status == "pass"
    assert readiness.reason_codes == ("resolution_adjudication_readiness_clear",)
    assert readiness.ready_dimension_count == d("6")
    assert readiness.blocked_dimension_count == d("0")
    assert readiness.rule_familiarity_score == d("0.920000")
    assert readiness.official_source_coverage_score == d("0.900000")
    assert readiness.contradiction_handling_score == d("0.880000")
    assert readiness.seconds_until_close == d("7200.000000")
    assert readiness.prior_error_rate == d("0.010000")
    assert readiness.open_review_count == d("1")
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True
    assert len(readiness.derived_validation_digest) == 64

    assert tuple(row.dimension_id for row in readiness.dimension_rows) == (
        "rule_familiarity",
        "official_source_coverage",
        "contradiction_handling",
        "close_urgency",
        "prior_error_rate",
        "reviewer_load",
    )
    assert all(row.dimension_status == "pass" for row in readiness.dimension_rows)
    assert readiness.dimension_rows[0].observed_value == d("0.920000")
    assert readiness.dimension_rows[3].threshold_value == d("3600.000000")
    assert readiness.dimension_rows[5].observed_value == d("1")

    payload = module.team_specialist_resolution_adjudication_readiness_v2_payload(
        readiness,
    )
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["ready_dimension_count"] == "6"
    assert payload["rule_familiarity_score"] == "0.920000"
    assert payload["dimension_rows"][3]["threshold_value"] == "3600.000000"
    assert payload["derived_validation_digest"] == readiness.derived_validation_digest
    assert (
        module.validate_team_specialist_resolution_adjudication_readiness_v2_payload(
            payload,
        )
        == payload
    )
    assert_no_int_or_float(payload)


def test_validate_payload_rejects_self_digested_malformed_report_payloads() -> None:
    module = api()
    payload = module.team_specialist_resolution_adjudication_readiness_v2_payload(
        report(readiness_input()),
    )

    missing_report_field = dict(payload)
    missing_report_field.pop("dimension_rows")

    extra_report_field = dict(payload)
    extra_report_field["extra_report_note"] = "paper"

    missing_row_field = dict(payload)
    row_payloads = [dict(row) for row in payload["dimension_rows"]]
    row_payloads[0].pop("threshold_value")
    missing_row_field["dimension_rows"] = row_payloads

    inconsistent_count = dict(payload)
    inconsistent_count["ready_dimension_count"] = "5"

    cases = (
        (missing_report_field, "payload fields must match readiness report"),
        (extra_report_field, "payload fields must match readiness report"),
        (missing_row_field, "dimension row fields must match readiness dimension row"),
        (inconsistent_count, "ready_dimension_count must match dimension_rows"),
    )

    for malformed_payload, message in cases:
        with pytest.raises(ValueError, match=message):
            module.validate_team_specialist_resolution_adjudication_readiness_v2_payload(
                signed_payload(malformed_payload),
            )


def test_blocks_all_readiness_dimensions_with_deterministic_reasons() -> None:
    readiness = report(
        readiness_input(
            rule_familiarity_score=d("0.700000"),
            official_source_coverage_score=d("0.600000"),
            contradiction_handling_score=d("0.790000"),
            seconds_until_close=d("300.000000"),
            prior_error_rate=d("0.200000"),
            open_review_count=d("4"),
        ),
    )

    assert readiness.readiness_status == "blocked"
    assert readiness.ready_dimension_count == d("0")
    assert readiness.blocked_dimension_count == d("6")
    assert readiness.reason_codes == (
        "rule_familiarity_below_threshold",
        "official_source_coverage_below_threshold",
        "contradiction_handling_below_threshold",
        "close_urgency_window_too_short",
        "prior_error_rate_above_threshold",
        "reviewer_load_above_threshold",
    )
    assert tuple(row.dimension_status for row in readiness.dimension_rows) == (
        "blocked",
        "blocked",
        "blocked",
        "blocked",
        "blocked",
        "blocked",
    )
    assert tuple(row.reason_codes[0] for row in readiness.dimension_rows) == (
        "rule_familiarity_below_threshold",
        "official_source_coverage_below_threshold",
        "contradiction_handling_below_threshold",
        "close_urgency_window_too_short",
        "prior_error_rate_above_threshold",
        "reviewer_load_above_threshold",
    )


def test_custom_thresholds_and_equal_edges_are_ready() -> None:
    module = api()
    cfg = module.TeamSpecialistResolutionAdjudicationReadinessConfig(
        min_rule_familiarity_score=d("0.920000"),
        min_official_source_coverage_score=d("0.900000"),
        min_contradiction_handling_score=d("0.880000"),
        min_seconds_until_close=d("7200.000000"),
        max_prior_error_rate=d("0.010000"),
        max_open_review_count=d("1"),
    )

    readiness = report(readiness_input(), cfg=cfg)

    assert readiness.readiness_status == "pass"
    assert readiness.reason_codes == ("resolution_adjudication_readiness_clear",)
    assert tuple(row.threshold_value for row in readiness.dimension_rows) == (
        d("0.920000"),
        d("0.900000"),
        d("0.880000"),
        d("7200.000000"),
        d("0.010000"),
        d("1"),
    )


def test_frozen_flags_digest_and_payload_tamper_are_rejected() -> None:
    module = api()
    readiness = report(readiness_input())

    with pytest.raises(FrozenInstanceError):
        readiness.readiness_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(readiness, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(readiness, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="ready_dimension_count"):
        replace(readiness, ready_dimension_count=d("5"))

    payload = module.team_specialist_resolution_adjudication_readiness_v2_payload(
        readiness,
    )
    tampered_payload = dict(payload)
    tampered_payload["open_review_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_team_specialist_resolution_adjudication_readiness_v2_payload(
            tampered_payload,
        )

    unsafe_flag_payload = dict(payload)
    unsafe_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        module.validate_team_specialist_resolution_adjudication_readiness_v2_payload(
            unsafe_flag_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wa" "llet_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_team_specialist_resolution_adjudication_readiness_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["specialist_id"] = "paper-" "tra" "de"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_team_specialist_resolution_adjudication_readiness_v2_payload(
            unsafe_value_payload,
        )


def test_validates_decimal_only_datetimes_flags_and_exact_types() -> None:
    module = api()

    with pytest.raises(ValueError, match="rule_familiarity_score must be a Decimal"):
        readiness_input(rule_familiarity_score=0.9)

    with pytest.raises(ValueError, match="open_review_count must be integral"):
        readiness_input(open_review_count=d("1.5"))

    with pytest.raises(ValueError, match="seconds_until_close must be nonnegative"):
        readiness_input(seconds_until_close=d("-1.000000"))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        readiness_input(observed_at=datetime(2026, 7, 7, 11, 55))

    class _DateTimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            readiness_input(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        report(
            readiness_input(observed_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(ValueError, match="config must be"):
        module.build_team_specialist_resolution_adjudication_readiness_v2_report(
            readiness_input(),
            config=object(),
            generated_at=GENERATED_AT,
        )

    class InputSubclass(module.TeamSpecialistResolutionAdjudicationReadinessInput):
        pass

    with pytest.raises(ValueError, match="input_row must be"):
        module.build_team_specialist_resolution_adjudication_readiness_v2_report(
            InputSubclass(
                team_id="politics",
                category_id="politics",
                specialist_id="resolver_alpha",
                adjudication_case_id="case_presidential_nominee",
                observed_at=GENERATED_AT,
                rule_familiarity_score=d("0.920000"),
                official_source_coverage_score=d("0.900000"),
                contradiction_handling_score=d("0.880000"),
                seconds_until_close=d("7200.000000"),
                prior_error_rate=d("0.010000"),
                open_review_count=d("1"),
            ),
            config=module.TeamSpecialistResolutionAdjudicationReadinessConfig(),
            generated_at=GENERATED_AT,
        )


def test_module_scope_is_phase1_report_only_without_side_effect_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_resolution_adjudication_readiness_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for token in (
        "li" "ve_trading",
        "au" "th",
        "wa" "llet",
        "or" "der",
        "net" "work",
        "data" "base",
        "sqlite",
        "sqlalchemy",
        "requests",
        "socket",
        "urllib",
        "web3",
        "open(",
        ".write(",
        ".read(",
    ):
        assert token not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
        if isinstance(node, ast.Import):
            imported = tuple(alias.name.split(".")[0] for alias in node.names)
            assert "requests" not in imported
            assert "socket" not in imported
            assert "urllib" not in imported
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".")[0]
            assert root not in {"requests", "socket", "urllib", "sqlite3"}
