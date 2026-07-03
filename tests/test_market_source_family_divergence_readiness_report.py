from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_source_family_divergence_readiness_report"
SOURCE = Path("src/polymarket_alpha_lab/market_source_family_divergence_readiness_report.py")
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _input_row(
    market_id: str,
    source_family: str,
    *,
    probability_delta: Decimal = Decimal("0.100000"),
    evidence_count: Decimal = Decimal("1.000000"),
    observed_at: datetime | None = None,
    conflict_acknowledged_at: datetime | None = None,
) -> object:
    api = _api()
    return api.MarketSourceFamilyDivergenceReadinessInputRow(
        market_id=market_id,
        source_family=source_family,
        probability_delta=probability_delta,
        evidence_count=evidence_count,
        observed_at=observed_at or _at(minutes=15),
        conflict_acknowledged_at=conflict_acknowledged_at,
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_READINESS_REPORT_CONFIG_VERSION
        ),
        "required_source_family_count": d("3.000000"),
        "required_divergence_evidence_count": d("2.000000"),
        "conflict_acknowledgement_stale_after_seconds": d("3600.000000"),
        "source_family_stale_after_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return api.MarketSourceFamilyDivergenceReadinessConfig(**values)


def _report(*rows: object, **config_overrides: object) -> object:
    api = _api()
    return api.build_market_source_family_divergence_readiness_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_report_rolls_up_independent_family_evidence_ack_freshness_and_buckets() -> None:
    report = _report(
        _input_row(
            "market-ready",
            "official",
            probability_delta=d("0.180000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=30),
            conflict_acknowledged_at=_at(minutes=20),
        ),
        _input_row(
            "market-ready",
            "primary",
            probability_delta=d("0.160000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=25),
            conflict_acknowledged_at=_at(minutes=18),
        ),
        _input_row(
            "market-ready",
            "proxy",
            probability_delta=d("0.120000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=15),
            conflict_acknowledged_at=_at(minutes=12),
        ),
        _input_row(
            "market-stale-ack",
            "official",
            probability_delta=d("0.150000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=30),
            conflict_acknowledged_at=_at(hours=2),
        ),
        _input_row(
            "market-stale-ack",
            "primary",
            probability_delta=d("0.120000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=28),
            conflict_acknowledged_at=_at(hours=2),
        ),
        _input_row(
            "market-stale-ack",
            "proxy",
            probability_delta=d("0.100000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=27),
            conflict_acknowledged_at=_at(hours=2),
        ),
        _input_row(
            "market-missing-family",
            "official",
            probability_delta=d("0.130000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=20),
            conflict_acknowledged_at=_at(minutes=15),
        ),
        _input_row(
            "market-missing-family",
            "primary",
            probability_delta=d("0.110000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=18),
            conflict_acknowledged_at=_at(minutes=15),
        ),
        _input_row(
            "market-stale-family",
            "official",
            probability_delta=d("0.140000"),
            evidence_count=d("1.000000"),
            observed_at=_at(hours=3),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-stale-family",
            "primary",
            probability_delta=d("0.120000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=18),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-stale-family",
            "proxy",
            probability_delta=d("0.100000"),
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=16),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-no-evidence",
            "official",
            probability_delta=d("0.000000"),
            evidence_count=d("0.000000"),
            observed_at=_at(minutes=15),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-no-evidence",
            "primary",
            probability_delta=d("0.010000"),
            evidence_count=d("0.000000"),
            observed_at=_at(minutes=14),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-no-evidence",
            "proxy",
            probability_delta=d("0.020000"),
            evidence_count=d("0.000000"),
            observed_at=_at(minutes=13),
            conflict_acknowledged_at=_at(minutes=10),
        ),
    )

    assert type(report) is _api().MarketSourceFamilyDivergenceReadinessReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.report_status == "blocked"
    assert report.market_count == d("5.000000")
    assert report.ready_market_count == d("1.000000")
    assert report.watch_market_count == d("2.000000")
    assert report.blocked_market_count == d("2.000000")
    assert report.readiness_ratio == d("0.200000")
    assert report.divergence_evidence_market_count == d("4.000000")
    assert report.conflict_acknowledged_market_count == d("5.000000")
    assert report.fresh_acknowledgement_market_count == d("4.000000")
    assert report.missing_family_market_count == d("1.000000")
    assert report.stale_family_market_count == d("1.000000")
    assert report.max_probability_delta == d("0.180000")
    assert report.max_acknowledgement_age_seconds == d("7200.000000")
    assert report.max_source_family_age_seconds == d("10800.000000")
    assert report.reason_codes == (
        "market_source_family_divergence_readiness_blocked",
        "market_source_family_divergence_acknowledgement_stale",
        "market_source_family_divergence_family_missing",
        "market_source_family_divergence_family_stale",
        "market_source_family_divergence_evidence_missing",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_id for row in report.rows) == (
        "market-missing-family",
        "market-no-evidence",
        "market-stale-ack",
        "market-stale-family",
        "market-ready",
    )
    missing = report.rows[0]
    assert missing.readiness_status == "blocked"
    assert missing.source_family_count == d("2.000000")
    assert missing.missing_family_count == d("1.000000")
    assert missing.stale_family_count == d("0.000000")
    assert missing.divergence_evidence_present is True
    assert missing.conflict_acknowledgement_status == "fresh"
    assert missing.reason_codes == (
        "market_source_family_divergence_family_missing",
    )

    stale_ack = report.rows[2]
    assert stale_ack.readiness_status == "watch"
    assert stale_ack.conflict_acknowledgement_status == "stale"
    assert stale_ack.conflict_acknowledgement_age_seconds == d("7200.000000")
    assert stale_ack.reason_codes == (
        "market_source_family_divergence_acknowledgement_stale",
    )

    ready = report.rows[-1]
    assert ready.readiness_status == "ready"
    assert ready.readiness_ratio == d("1.000000")
    assert ready.reason_codes == (
        "market_source_family_divergence_readiness_ready",
    )


def test_empty_report_is_deterministic_readonly_and_decimal_zeroed() -> None:
    report = _report()

    assert report.report_status == "clear"
    assert report.reason_codes == (
        "market_source_family_divergence_readiness_clear",
    )
    assert report.market_count == d("0.000000")
    assert report.ready_market_count == d("0.000000")
    assert report.watch_market_count == d("0.000000")
    assert report.blocked_market_count == d("0.000000")
    assert report.readiness_ratio == d("0.000000")
    assert report.divergence_evidence_market_count == d("0.000000")
    assert report.conflict_acknowledged_market_count == d("0.000000")
    assert report.fresh_acknowledgement_market_count == d("0.000000")
    assert report.missing_family_market_count == d("0.000000")
    assert report.stale_family_market_count == d("0.000000")
    assert report.max_probability_delta == d("0.000000")
    assert report.max_acknowledgement_age_seconds == d("0.000000")
    assert report.max_source_family_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_json_ready_decimal_stringed_utc_and_has_no_float_or_live_surface() -> None:
    api = _api()
    report = _report(
        _input_row(
            "market-ready",
            "official",
            probability_delta=d("0.120000"),
            observed_at=_at(minutes=45).astimezone(timezone(timedelta(hours=-4))),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-ready",
            "primary",
            probability_delta=d("0.100000"),
            observed_at=_at(minutes=35),
            conflict_acknowledged_at=_at(minutes=10),
        ),
        _input_row(
            "market-ready",
            "proxy",
            probability_delta=d("0.090000"),
            observed_at=_at(minutes=25),
            conflict_acknowledged_at=_at(minutes=10),
        ),
    )

    payload = api.market_source_family_divergence_readiness_payload(report)
    json.dumps(payload)
    payload_text = repr(payload).lower()

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["rows"][0]["source_family_count"] == "3.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-02T11:35:00+00:00"
    assert payload["rows"][0]["conflict_acknowledged_at"] == "2026-07-02T11:50:00+00:00"
    assert ".0," not in payload_text
    assert "wallet" not in payload_text
    assert "account" not in payload_text
    assert "order" not in payload_text
    assert "recommend" not in payload_text
    assert "advice" not in payload_text
    assert "action" not in payload_text


def test_dataclasses_reject_floats_naive_time_false_flags_subclasses_and_mutation() -> None:
    api = _api()

    with pytest.raises(ValueError, match="probability_delta must be a Decimal"):
        api.MarketSourceFamilyDivergenceReadinessInputRow(
            market_id="market-alpha",
            source_family="official",
            probability_delta=0.1,
            evidence_count=d("1.000000"),
            observed_at=_at(minutes=10),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _input_row(
            "market-alpha",
            "official",
            observed_at=datetime(2026, 7, 2, 11, 0),
        )

    with pytest.raises(ValueError, match="datetime values must not be after generated_at"):
        api.build_market_source_family_divergence_readiness_report(
            (
                _input_row(
                    "market-alpha",
                    "official",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    row = _input_row("market-alpha", "official")
    with pytest.raises(FrozenInstanceError):
        row.market_id = "market-beta"

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="config must be a MarketSourceFamilyDivergenceReadinessConfig"):
        api.build_market_source_family_divergence_readiness_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    class ConfigSubclass(api.MarketSourceFamilyDivergenceReadinessConfig):
        pass

    with pytest.raises(ValueError, match="config must be a MarketSourceFamilyDivergenceReadinessConfig"):
        api.build_market_source_family_divergence_readiness_report(
            (),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )

    class InputSubclass(api.MarketSourceFamilyDivergenceReadinessInputRow):
        pass

    with pytest.raises(ValueError, match="rows must contain MarketSourceFamilyDivergenceReadinessInputRow values"):
        api.build_market_source_family_divergence_readiness_report(
            (
                InputSubclass(
                    market_id="market-alpha",
                    source_family="official",
                    probability_delta=d("0.100000"),
                    evidence_count=d("1.000000"),
                    observed_at=_at(minutes=5),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_public_numeric_annotations_are_decimal_and_module_scope_is_side_effect_free() -> None:
    api = _api()
    numeric_fragments = (
        "count",
        "ratio",
        "amount",
        "seconds",
        "delta",
        "age",
    )

    for cls_name in (
        "MarketSourceFamilyDivergenceReadinessConfig",
        "MarketSourceFamilyDivergenceReadinessInputRow",
        "MarketSourceFamilyDivergenceReadinessMarketRow",
        "MarketSourceFamilyDivergenceReadinessReport",
    ):
        cls = getattr(api, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if any(fragment in field.name for fragment in numeric_fragments):
                assert hints[field.name] is Decimal, (cls_name, field.name, hints[field.name])

    text = SOURCE.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden_text = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "private_key",
        "wallet",
        "account",
        "recommend",
        "advice",
        "action",
        "open(",
        "print(",
    )
    for token in forbidden_text:
        assert token not in lowered, token

    allowed_import_prefixes = (
        "from __future__",
        "from dataclasses",
        "from datetime",
        "from decimal",
        "from typing",
        "from polymarket_alpha_lab.team_paper_guard",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert any(
                stripped.startswith(prefix) for prefix in allowed_import_prefixes
            ), stripped

    tree = ast.parse(text)
    forbidden_calls = {"open", "print", "exec", "eval", "compile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    assert importlib.util.find_spec(MODULE_NAME) is not None
    for name, value in inspect.getmembers(api):
        if name.startswith("_"):
            continue
        if isinstance(value, float):
            raise AssertionError(name)
