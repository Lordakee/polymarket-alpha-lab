from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.market_resolution_rule_clarity_report as api
from polymarket_alpha_lab.market_resolution_rule_clarity_report import (
    MarketResolutionRuleClarityInput,
    MarketResolutionRuleClarityReport,
    build_market_resolution_rule_clarity_report,
    market_resolution_rule_clarity_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def clarity_input(**overrides: object) -> MarketResolutionRuleClarityInput:
    values = {
        "rule_text_present": True,
        "official_resolution_source_present": True,
        "ambiguous_clause_count": d("0.000000"),
        "conflicting_rule_signal_count": d("0.000000"),
        "last_rule_check_age_seconds": d("300.000000"),
        "manual_review_required": False,
        "source_payload_redacted": True,
    }
    values.update(overrides)
    return MarketResolutionRuleClarityInput(**values)


def report(**overrides: object) -> MarketResolutionRuleClarityReport:
    return build_market_resolution_rule_clarity_report(clarity_input(**overrides))


def assert_decimal_only_public_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_public_numerics(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_decimal_only_public_numerics(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_decimal_only_public_numerics(item)


def walk_payload(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        out: list[object] = []
        for item in value.values():
            out.extend(walk_payload(item))
        return tuple(out)
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(walk_payload(item))
        return tuple(out)
    return (value,)


def test_clear_resolution_rules_are_ready_with_digest_backed_public_payload() -> None:
    ready = report()

    assert type(ready) is MarketResolutionRuleClarityReport
    assert ready.rule_clarity_ready is True
    assert ready.clarity_score == d("1.000000")
    assert ready.ready_ratio == d("1.000000")
    assert ready.blocked_reason_codes == ()
    assert ready.attention_reason_codes == ()
    assert ready.paper_only is True
    assert ready.report_only is True
    assert ready.readonly is True
    assert len(ready.digest) == 64

    payload = ready.public_payload
    assert payload == market_resolution_rule_clarity_report_payload(ready)
    assert payload["rule_clarity_ready"] is True
    assert payload["clarity_score"] == "1.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["blocked_reason_codes"] == []
    assert payload["attention_reason_codes"] == []
    assert payload["digest"] == ready.digest
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert not any(isinstance(item, (Decimal, float)) for item in walk_payload(payload))


def test_missing_sources_stale_checks_ambiguity_and_manual_review_block_readiness() -> None:
    blocked = report(
        rule_text_present=False,
        official_resolution_source_present=False,
        ambiguous_clause_count=d("2.000000"),
        conflicting_rule_signal_count=d("1.000000"),
        last_rule_check_age_seconds=d("90000.000000"),
        manual_review_required=True,
    )

    assert blocked.rule_clarity_ready is False
    assert blocked.clarity_score == d("0.000000")
    assert blocked.ready_ratio == d("0.000000")
    assert blocked.blocked_reason_codes == (
        "rule_text_missing",
        "official_resolution_source_missing",
        "ambiguous_clauses_present",
        "conflicting_rule_signals_present",
        "manual_review_required",
    )
    assert blocked.attention_reason_codes == ("rule_check_stale",)

    payload_text = json.dumps(blocked.public_payload, sort_keys=True)
    for unsafe_fragment in (
        "raw",
        "question",
        "source_url",
        "wallet",
        "auth",
        "order",
        "trade",
        "token",
        "private",
        "live",
    ):
        assert unsafe_fragment not in payload_text.lower()


def test_unredacted_source_payload_is_blocked_from_publication() -> None:
    unsafe = report(source_payload_redacted=False)

    assert unsafe.rule_clarity_ready is False
    assert "source_payload_not_redacted" in unsafe.blocked_reason_codes
    with pytest.raises(ValueError, match="redacted"):
        unsafe.public_payload
    with pytest.raises(ValueError, match="redacted"):
        market_resolution_rule_clarity_report_payload(unsafe)


def test_dataclasses_are_frozen_final_decimal_only_and_hard_flagged() -> None:
    sample_input = clarity_input()
    sample_report = build_market_resolution_rule_clarity_report(sample_input)

    for item in (sample_input, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_decimal_only_public_numerics(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(MarketResolutionRuleClarityInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(MarketResolutionRuleClarityReport):
            pass


def test_validation_rejects_non_decimal_negative_fractional_and_non_report_flags() -> None:
    with pytest.raises(ValueError, match="ambiguous_clause_count"):
        clarity_input(ambiguous_clause_count=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflicting_rule_signal_count"):
        clarity_input(conflicting_rule_signal_count=_DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="last_rule_check_age_seconds"):
        clarity_input(last_rule_check_age_seconds=d("-0.000001"))
    with pytest.raises(ValueError, match="integral"):
        clarity_input(ambiguous_clause_count=d("1.500000"))
    with pytest.raises(ValueError, match="manual_review_required"):
        clarity_input(manual_review_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        clarity_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        build_market_resolution_rule_clarity_report(clarity_input(report_only=False))
    with pytest.raises(ValueError, match="readonly"):
        build_market_resolution_rule_clarity_report(clarity_input(readonly=False))


def test_digest_revalidates_public_payload_and_tampered_reports() -> None:
    ready = report()
    payload = ready.public_payload

    tampered_payload = dict(payload)
    tampered_payload["clarity_score"] = "0.000000"
    with pytest.raises(ValueError, match="digest"):
        market_resolution_rule_clarity_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="digest"):
        market_resolution_rule_clarity_report_payload(
            {**payload, "digest": "0" * 64},
        )

    tampered_report = report()
    object.__setattr__(tampered_report, "clarity_score", d("0.000000"))
    with pytest.raises(ValueError, match="digest|clarity_score"):
        market_resolution_rule_clarity_report_payload(tampered_report)
