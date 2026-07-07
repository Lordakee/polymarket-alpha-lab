from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_market_close_handoff_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 20, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 19, 55, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_market_close_handoff_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_TEAM_SPECIALIST_MARKET_CLOSE_HANDOFF_GATE_V2_CONFIG_VERSION
        ),
        "max_pass_source_freshness_minutes": d("15.000000"),
        "max_watch_source_freshness_minutes": d("45.000000"),
        "min_pass_official_source_coverage_ratio": d("1.000000"),
        "min_watch_official_source_coverage_ratio": d("0.750000"),
        "max_pass_unresolved_contradiction_count": d("0"),
        "max_watch_unresolved_contradiction_count": d("1"),
        "max_pass_queue_age_minutes": d("10.000000"),
        "max_watch_queue_age_minutes": d("30.000000"),
        "min_pass_handoff_completeness_ratio": d("1.000000"),
        "min_watch_handoff_completeness_ratio": d("0.800000"),
        "min_pass_available_reviewer_count": d("2"),
        "min_watch_available_reviewer_count": d("1"),
    }
    values.update(overrides)
    return module.TeamSpecialistMarketCloseHandoffGateV2Config(**values)


def handoff(**overrides: object) -> Any:
    module = api()
    values = {
        "handoff_reference": "handoff-alpha",
        "market_slug": "alpha-market",
        "specialist_team": "macro_close_team",
        "observed_at": OBSERVED_AT,
        "source_freshness_minutes": d("5.000000"),
        "official_source_coverage_ratio": d("1.000000"),
        "unresolved_contradiction_count": d("0"),
        "queue_age_minutes": d("5.000000"),
        "handoff_completeness_ratio": d("1.000000"),
        "available_reviewer_count": d("2"),
        "reason_codes": ("specialist_handoff_candidate",),
    }
    values.update(overrides)
    return module.TeamSpecialistMarketCloseHandoffGateV2Input(**values)


def report(
    *handoffs: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_team_specialist_market_close_handoff_gate_v2(
        handoffs,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_gate_combines_phase1_handoff_dimensions_with_stable_reasons() -> None:
    result = report(
        handoff(
            handoff_reference="handoff-ready",
            market_slug="gamma-ready",
            source_freshness_minutes=d("5.000000"),
            official_source_coverage_ratio=d("1.000000"),
            unresolved_contradiction_count=d("0"),
            queue_age_minutes=d("5.000000"),
            handoff_completeness_ratio=d("1.000000"),
            available_reviewer_count=d("3"),
        ),
        handoff(
            handoff_reference="handoff-watch",
            market_slug="beta-watch",
            source_freshness_minutes=d("30.000000"),
            official_source_coverage_ratio=d("0.800000"),
            unresolved_contradiction_count=d("1"),
            queue_age_minutes=d("20.000000"),
            handoff_completeness_ratio=d("0.900000"),
            available_reviewer_count=d("1"),
        ),
        handoff(
            handoff_reference="secret-close-handoff",
            market_slug="alpha-blocked",
            source_freshness_minutes=d("90.000000"),
            official_source_coverage_ratio=d("0.500000"),
            unresolved_contradiction_count=d("2"),
            queue_age_minutes=d("60.000000"),
            handoff_completeness_ratio=d("0.500000"),
            available_reviewer_count=d("0"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "team-specialist-market-close-handoff-gate-v2"
    assert result.handoff_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.max_source_freshness_minutes == d("90.000000")
    assert result.min_official_source_coverage_ratio == d("0.500000")
    assert result.max_unresolved_contradiction_count == d("2")
    assert result.max_queue_age_minutes == d("60.000000")
    assert result.min_handoff_completeness_ratio == d("0.500000")
    assert result.min_available_reviewer_count == d("0")
    assert result.gate_status == "blocked"
    assert result.gate_digest.startswith("market_close_handoff_report_digest_")
    assert result.reason_codes == (
        "team_specialist_market_close_handoff_gate_blocked",
        "team_specialist_market_close_handoff_gate_watch",
        "team_specialist_market_close_handoff_gate_pass",
        "source_freshness_blocked",
        "source_freshness_watch",
        "source_freshness_pass",
        "official_source_coverage_blocked",
        "official_source_coverage_watch",
        "official_source_coverage_pass",
        "unresolved_contradictions_blocked",
        "unresolved_contradictions_watch",
        "unresolved_contradictions_pass",
        "queue_age_blocked",
        "queue_age_watch",
        "queue_age_pass",
        "handoff_completeness_blocked",
        "handoff_completeness_watch",
        "handoff_completeness_pass",
        "reviewer_availability_blocked",
        "reviewer_availability_watch",
        "reviewer_availability_pass",
        "specialist_handoff_candidate",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_slug for row in result.rows) == (
        "alpha-blocked",
        "beta-watch",
        "gamma-ready",
    )
    blocked, watched, passed = result.rows

    assert blocked.gate_status == "blocked"
    assert blocked.handoff_permitted is False
    assert blocked.handoff_digest.startswith("market_close_handoff_row_digest_")
    assert blocked.redacted_handoff_reference.startswith("handoff_ref_")
    assert "secret-close-handoff" not in repr(blocked)
    assert blocked.reason_codes == (
        "specialist_handoff_candidate",
        "team_specialist_market_close_handoff_gate_blocked",
        "source_freshness_blocked",
        "official_source_coverage_blocked",
        "unresolved_contradictions_blocked",
        "queue_age_blocked",
        "handoff_completeness_blocked",
        "reviewer_availability_blocked",
    )

    assert watched.gate_status == "watch"
    assert watched.handoff_permitted is False
    assert watched.reason_codes == (
        "specialist_handoff_candidate",
        "team_specialist_market_close_handoff_gate_watch",
        "source_freshness_watch",
        "official_source_coverage_watch",
        "unresolved_contradictions_watch",
        "queue_age_watch",
        "handoff_completeness_watch",
        "reviewer_availability_watch",
    )

    assert passed.gate_status == "pass"
    assert passed.handoff_permitted is True
    assert passed.reason_codes == (
        "specialist_handoff_candidate",
        "team_specialist_market_close_handoff_gate_pass",
        "source_freshness_pass",
        "official_source_coverage_pass",
        "unresolved_contradictions_pass",
        "queue_age_pass",
        "handoff_completeness_pass",
        "reviewer_availability_pass",
    )

    repeated = report(handoff(handoff_reference="handoff-ready", market_slug="gamma-ready"))
    repeated_again = report(
        handoff(handoff_reference="handoff-ready", market_slug="gamma-ready"),
    )
    assert repeated.gate_digest == repeated_again.gate_digest
    assert repeated.rows[0].handoff_digest == repeated_again.rows[0].handoff_digest


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.handoff_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.max_source_freshness_minutes == ZERO
    assert empty.min_official_source_coverage_ratio == ZERO
    assert empty.max_unresolved_contradiction_count == d("0")
    assert empty.max_queue_age_minutes == ZERO
    assert empty.min_handoff_completeness_ratio == ZERO
    assert empty.min_available_reviewer_count == d("0")
    assert empty.gate_status == "watch"
    assert empty.reason_codes == (
        "team_specialist_market_close_handoff_gate_v2_empty",
    )
    assert empty.rows == ()
    assert empty.gate_digest.startswith("market_close_handoff_report_digest_")
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_payload_redacts_references_and_uses_decimal_strings() -> None:
    module = api()
    result = report(
        handoff(
            handoff_reference="secret-close-handoff",
            market_slug="payload-market",
            observed_at=datetime(
                2026,
                7,
                7,
                12,
                55,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            source_freshness_minutes=d("30.000000"),
        ),
        generated_at=datetime(
            2026,
            7,
            7,
            13,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = module.team_specialist_market_close_handoff_gate_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T20:00:00+00:00"
    assert payload["handoff_count"] == "1"
    assert payload["max_source_freshness_minutes"] == "30.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-07T19:55:00+00:00"
    assert payload["rows"][0]["redacted_handoff_reference"].startswith("handoff_ref_")
    assert "secret-close-handoff" not in rendered
    assert_no_public_numeric_values(payload)

    unsafe_report = replace(result)
    object.__setattr__(unsafe_report, "extra_public_count", 1)
    with pytest.raises(ValueError, match="public payload numeric"):
        module.team_specialist_market_close_handoff_gate_v2_payload(unsafe_report)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_handoff = handoff()
    sample_report = report(sample_handoff)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_handoff, sample_row, sample_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="source_freshness_minutes must be a Decimal"):
        handoff(source_freshness_minutes=5)
    with pytest.raises(ValueError, match="source_freshness_minutes must be a Decimal"):
        handoff(source_freshness_minutes=_DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="available_reviewer_count must be a whole Decimal"):
        handoff(available_reviewer_count=d("1.500000"))
    with pytest.raises(ValueError, match="official_source_coverage_ratio"):
        handoff(official_source_coverage_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        handoff(observed_at=_DatetimeSubclass(2026, 7, 7, 19, 55, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(handoff(), generated_at=datetime(2026, 7, 7, 20, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            handoff(),
            generated_at=datetime(2026, 7, 7, 20, 0, tzinfo=_MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(handoff(observed_at=datetime(2026, 7, 7, 20, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate handoff_reference"):
        report(handoff(), handoff())
    with pytest.raises(ValueError, match="max_pass_source_freshness_minutes"):
        config(max_pass_source_freshness_minutes=d("46.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        handoff(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)


def test_report_and_row_consistency_are_validated() -> None:
    result = report(
        handoff(handoff_reference="handoff-ready", market_slug="alpha"),
        handoff(
            handoff_reference="handoff-blocked",
            market_slug="beta",
            source_freshness_minutes=d("90.000000"),
        ),
    )

    with pytest.raises(ValueError, match="pass_count"):
        replace(result, pass_count=d("0"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="gate_status"):
        replace(result.rows[0], gate_status="watch")
    with pytest.raises(ValueError, match="handoff_permitted"):
        replace(result.rows[1], handoff_permitted=True)
    with pytest.raises(ValueError, match="handoff_digest"):
        replace(result.rows[0], handoff_digest="market_close_handoff_row_digest_bad")
    with pytest.raises(ValueError, match="gate_digest"):
        replace(result, gate_digest="market_close_handoff_report_digest_bad")


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(handoff())

    with pytest.raises(ValueError, match="report must be"):
        module.team_specialist_market_close_handoff_gate_v2_payload(object())
    with pytest.raises(ValueError, match="report_only must be True"):
        module.team_specialist_market_close_handoff_gate_v2_payload(
            replace(result, report_only=False),
        )


def test_module_scope_has_no_io_persistence_or_non_decimal_numeric_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "psycopg",
        "supabase",
        "sqlite",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "private_key",
        "broker",
        "wallet",
        "order",
        "live",
        "trade",
    )
    for forbidden in forbidden_terms:
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported_names = [alias.name for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_names.append(node.module)
            for imported in imported_names:
                assert not any(term in imported.lower() for term in forbidden_terms)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "open",
                "connect",
                "execute",
                "fetch",
                "request",
                "submit",
            }
