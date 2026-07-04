from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_court_oral_argument_signal_digest.py",
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_policy_court_oral_argument_signal_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def signal(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "case_key": "scotus-policy-case-alpha",
        "court_key": "scotus",
        "docket_key": "24-101",
        "source_ref": "oral-argument-transcript",
        "observed_at": GENERATED_AT - timedelta(hours=3),
        "skeptical_prompt_count": d("6.000000"),
        "supportive_prompt_count": d("1.000000"),
        "uncertainty_prompt_count": d("3.000000"),
        "cited_precedent_count": d("4.000000"),
        "outcome_alignment_confidence": d("0.820000"),
        "oral_argument_signal_active": True,
    }
    values.update(overrides)
    return module.MarketResearchPolicyCourtOralArgumentSignalDigestSignal(**values)


def report(*signals: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_research_policy_court_oral_argument_signal_digest(
        signals,
        config=module.MarketResearchPolicyCourtOralArgumentSignalDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in JSON payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            assert_no_floats(item)


def assert_no_public_int_payload_numerics(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        raise AssertionError(f"int found in public payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_int_payload_numerics(child)
    if isinstance(value, list):
        for child in value:
            assert_no_public_int_payload_numerics(child)


def test_empty_input_returns_report_only_pass_digest() -> None:
    digest = report()

    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "market-research-policy-court-oral-argument-signal-digest-v0"
    )
    assert digest.research_scope == (
        "policy court oral argument signal research digest only"
    )
    assert digest.digest_status == "pass"
    assert digest.recommended_next_step == (
        "continue_report_only_policy_court_oral_argument_signal_monitoring"
    )
    assert digest.case_count == d("0.000000")
    assert digest.signal_count == d("0.000000")
    assert digest.clear_case_count == d("0.000000")
    assert digest.watch_case_count == d("0.000000")
    assert digest.high_score_case_count == d("0.000000")
    assert digest.high_skepticism_case_count == d("0.000000")
    assert digest.high_uncertainty_case_count == d("0.000000")
    assert digest.high_precedent_pressure_case_count == d("0.000000")
    assert digest.high_confidence_case_count == d("0.000000")
    assert digest.active_signal_case_count == d("0.000000")
    assert digest.stale_signal_case_count == d("0.000000")
    assert digest.max_oral_argument_signal_score == d("0.000000")
    assert digest.max_signal_age_seconds == d("0.000000")
    assert digest.average_outcome_alignment_confidence == d("0.000000")
    assert digest.rows == ()
    assert digest.reason_code_counts == ()
    assert digest.reason_codes == ("policy_court_oral_argument_signal_empty",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_active_oral_argument_signal_builds_watch_row_with_decimal_metrics() -> None:
    digest = report(signal())

    assert digest.digest_status == "watch"
    assert digest.recommended_next_step == (
        "review_report_only_policy_court_oral_argument_signals"
    )
    assert digest.case_count == d("1.000000")
    assert digest.signal_count == d("1.000000")
    assert digest.clear_case_count == d("0.000000")
    assert digest.watch_case_count == d("1.000000")
    assert digest.high_score_case_count == d("1.000000")
    assert digest.high_skepticism_case_count == d("1.000000")
    assert digest.high_uncertainty_case_count == d("1.000000")
    assert digest.high_precedent_pressure_case_count == d("1.000000")
    assert digest.high_confidence_case_count == d("1.000000")
    assert digest.active_signal_case_count == d("1.000000")
    assert digest.stale_signal_case_count == d("1.000000")
    assert digest.max_oral_argument_signal_score == d("1.000000")
    assert digest.max_signal_age_seconds == d("10800.000000")
    assert digest.average_outcome_alignment_confidence == d("0.820000")
    assert digest.reason_codes == (
        "policy_court_oral_argument_signal_score_high",
        "policy_court_oral_argument_skepticism_high",
        "policy_court_oral_argument_uncertainty_high",
        "policy_court_oral_argument_precedent_pressure_high",
        "policy_court_oral_argument_confidence_high",
        "policy_court_oral_argument_signal_active",
        "policy_court_oral_argument_signal_stale",
    )

    row = digest.rows[0]
    assert row.case_key == "scotus-policy-case-alpha"
    assert row.court_key == "scotus"
    assert row.docket_key == "24-101"
    assert row.signal_count == d("1.000000")
    assert row.observed_at_latest == GENERATED_AT - timedelta(hours=3)
    assert row.skeptical_prompt_count_max == d("6.000000")
    assert row.supportive_prompt_count_max == d("1.000000")
    assert row.uncertainty_prompt_count_max == d("3.000000")
    assert row.cited_precedent_count_max == d("4.000000")
    assert row.outcome_alignment_confidence_max == d("0.820000")
    assert row.oral_argument_signal_score == d("1.000000")
    assert row.signal_age_seconds == d("10800.000000")
    assert row.digest_status == "watch"
    assert row.reason_codes == digest.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_rows_and_reason_code_counts_sort_deterministically() -> None:
    digest = report(
        signal(
            case_key="z-case",
            docket_key="z-docket",
            source_ref="z-source",
            oral_argument_signal_active=False,
            skeptical_prompt_count=d("1.000000"),
            supportive_prompt_count=d("3.000000"),
            uncertainty_prompt_count=d("0.000000"),
            cited_precedent_count=d("0.000000"),
            outcome_alignment_confidence=d("0.500000"),
            observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        signal(
            case_key="a-case",
            docket_key="a-docket",
            source_ref="a-source",
            oral_argument_signal_active=False,
            skeptical_prompt_count=d("5.000000"),
            supportive_prompt_count=d("1.000000"),
            uncertainty_prompt_count=d("0.000000"),
            cited_precedent_count=d("0.000000"),
            outcome_alignment_confidence=d("0.660000"),
            observed_at=GENERATED_AT - timedelta(hours=1),
        ),
        signal(
            case_key="m-case",
            docket_key="m-docket",
            source_ref="m-source",
            oral_argument_signal_active=False,
            skeptical_prompt_count=d("0.000000"),
            supportive_prompt_count=d("1.000000"),
            uncertainty_prompt_count=d("3.000000"),
            cited_precedent_count=d("0.000000"),
            outcome_alignment_confidence=d("0.720000"),
            observed_at=GENERATED_AT - timedelta(hours=2),
        ),
    )

    assert tuple(row.case_key for row in digest.rows) == ("m-case", "a-case", "z-case")
    assert tuple((item.reason_code, item.case_count) for item in digest.reason_code_counts) == (
        ("policy_court_oral_argument_signal_score_high", d("2.000000")),
        ("policy_court_oral_argument_skepticism_high", d("1.000000")),
        ("policy_court_oral_argument_uncertainty_high", d("1.000000")),
        ("policy_court_oral_argument_confidence_high", d("1.000000")),
    )


def test_offset_datetimes_normalize_to_utc_and_naive_datetimes_are_rejected() -> None:
    digest = report(
        signal(
            observed_at=datetime(
                2026,
                7,
                4,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(2026, 7, 4, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    row = digest.rows[0]
    assert digest.generated_at == GENERATED_AT
    assert row.observed_at_latest == datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
    assert row.signal_age_seconds == d("10800.000000")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(signal(), generated_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC))


def test_payload_uses_six_decimal_strings_iso_datetimes_and_no_public_ints() -> None:
    payload = api().market_research_policy_court_oral_argument_signal_digest_payload(
        report(signal()),
    )

    json.dumps(payload, sort_keys=True)
    assert_no_floats(payload)
    assert_no_public_int_payload_numerics(payload)
    assert payload["generated_at"] == "2026-07-04T18:00:00Z"
    assert payload["case_count"] == "1.000000"
    assert payload["signal_count"] == "1.000000"
    assert payload["max_oral_argument_signal_score"] == "1.000000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-04T15:00:00Z"
    assert payload["rows"][0]["skeptical_prompt_count_max"] == "6.000000"
    assert payload["reason_code_counts"][0]["case_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_validation_rejects_bad_values_flags_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="skeptical_prompt_count must be a Decimal"):
        signal(skeptical_prompt_count=_DecimalSubclass("6.000000"))
    with pytest.raises(ValueError, match="skeptical_prompt_count must be nonnegative"):
        signal(skeptical_prompt_count=d("-1.000000"))
    with pytest.raises(ValueError, match="outcome_alignment_confidence must be at most 1"):
        signal(outcome_alignment_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="oral_argument_signal_active must be a bool"):
        signal(oral_argument_signal_active="true")
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.MarketResearchPolicyCourtOralArgumentSignalDigestRow(
            case_key="case",
            court_key="scotus",
            docket_key="docket",
            signal_count=d("1.000000"),
            observed_at_latest=GENERATED_AT,
            skeptical_prompt_count_max=d("0.000000"),
            supportive_prompt_count_max=d("0.000000"),
            uncertainty_prompt_count_max=d("0.000000"),
            cited_precedent_count_max=d("0.000000"),
            outcome_alignment_confidence_max=d("0.000000"),
            oral_argument_signal_score=d("0.000000"),
            signal_age_seconds=d("0.000000"),
            digest_status="clear",
            reason_codes=(
                "policy_court_oral_argument_signal_clear",
                "policy_court_oral_argument_signal_clear",
            ),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        module.MarketResearchPolicyCourtOralArgumentSignalDigestConfig(report_only=False)
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        report(signal(), signal())

    digest = report(signal())
    with pytest.raises(ValueError, match="case_count must match rows"):
        replace(digest, case_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(digest, reason_code_counts=tuple(reversed(digest.reason_code_counts)))
    with pytest.raises(ValueError, match="clear rows must use the clear reason"):
        replace(digest.rows[0], digest_status="clear")
    with pytest.raises(
        ValueError,
        match="report must be exactly "
        "MarketResearchPolicyCourtOralArgumentSignalDigestReport",
    ):
        module.market_research_policy_court_oral_argument_signal_digest_payload(
            report="bad",
        )


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_POLICY_COURT_ORAL_ARGUMENT_SIGNAL_DIGEST_CONFIG_VERSION",
        "POLICY_COURT_ORAL_ARGUMENT_SIGNAL_RESEARCH_SCOPE",
        "MarketResearchPolicyCourtOralArgumentSignalDigestConfig",
        "MarketResearchPolicyCourtOralArgumentSignalDigestSignal",
        "MarketResearchPolicyCourtOralArgumentSignalDigestReasonCodeCount",
        "MarketResearchPolicyCourtOralArgumentSignalDigestRow",
        "MarketResearchPolicyCourtOralArgumentSignalDigestReport",
        "build_market_research_policy_court_oral_argument_signal_digest",
        "market_research_policy_court_oral_argument_signal_digest_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    digest = report(signal())
    with pytest.raises(FrozenInstanceError):
        digest.digest_status = "pass"
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].digest_status = "clear"

    for value in (
        module.MarketResearchPolicyCourtOralArgumentSignalDigestConfig(),
        signal(),
        digest,
        digest.rows[0],
        digest.reason_code_counts[0],
    ):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            public_value = getattr(value, field.name)
            if field.name.endswith(
                (
                    "_count",
                    "_score",
                    "_threshold",
                    "_seconds",
                    "_confidence",
                ),
            ):
                assert type(public_value) is Decimal


def test_static_forbidden_surface_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange_mutation",
        "private_key",
        "api_key",
        "secret",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "sqlite",
        "postgres",
        "supabase",
        "write_text",
        "write_bytes",
        "fast_mode",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "int", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
