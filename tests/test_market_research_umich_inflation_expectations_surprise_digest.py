from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 5, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_umich_inflation_expectations_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-umich-inflation-expectations-surprise-digest-v0"
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.250000"),
        "max_revision_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "stale_confidence_decay": d("0.200000"),
        "thin_source_confidence_decay": d("0.150000"),
        "revision_confidence_decay": d("0.100000"),
        "confirmation_confidence_decay": d("0.200000"),
    }
    values.update(overrides)
    return module.MarketResearchUmichInflationExpectationsSurpriseDigestConfig(
        **values,
    )


def signal(
    research_id: str = "research.umich_inflation_expectations.one_year",
    *,
    condition_id: str = "condition_umich_inflation_expectations",
    release_id: str = "umich.inflation_expectations.one_year.prelim",
    expectation_horizon: str = "one_year",
    public_signal_reference: str = "umich-public-inflation-expectations-release",
    observed_at: datetime | None = None,
    expected_inflation_expectation: Decimal = d("3.000000"),
    actual_inflation_expectation: Decimal = d("3.100000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.020000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "umich-inflation-expectations-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchUmichInflationExpectationsSurpriseDigestSignal(
        condition_id=condition_id,
        research_id=research_id,
        release_id=release_id,
        expectation_horizon=expectation_horizon,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=45),
        expected_inflation_expectation=expected_inflation_expectation,
        actual_inflation_expectation=actual_inflation_expectation,
        source_count=source_count,
        revision_ratio=revision_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    signals: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_umich_inflation_expectations_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk_public_values(value: object, path: str = "value") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _walk_public_values(getattr(value, field.name), f"{path}.{field.name}")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _walk_public_values(item, f"{path}[{index}]")
        return
    if isinstance(value, bool):
        return
    assert type(value) is not int, path
    assert type(value) is not float, path


def _assert_payload_has_no_live_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_payload_has_no_live_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_payload_has_no_live_values(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, datetime, float, int))


def _assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def test_umich_inflation_expectations_surprise_digest_builds_report_only_screening_summary() -> None:
    module = api()
    report = digest(
        (
            signal(
                "research.umich_inflation_expectations.ready",
                condition_id="condition_ready",
                release_id="z.ready.umich.inflation_expectations",
                observed_at=(GENERATED_AT - timedelta(minutes=45)).astimezone(
                    timezone(timedelta(hours=2)),
                ),
            ),
            signal(
                "research.umich_inflation_expectations.watch",
                condition_id="condition_watch",
                release_id="m.watch.umich.inflation_expectations",
                expected_inflation_expectation=d("3.000000"),
                actual_inflation_expectation=d("3.450000"),
                revision_ratio=d("0.350000"),
                base_confidence=d("0.850000"),
                signal_config_version="umich-inflation-expectations-watch-v0",
            ),
            signal(
                "research.umich_inflation_expectations.blocked",
                condition_id="condition_blocked",
                release_id="a.blocked.umich.inflation_expectations",
                observed_at=GENERATED_AT - timedelta(hours=5),
                expected_inflation_expectation=d("3.000000"),
                actual_inflation_expectation=d("3.800000"),
                source_count=d("1.000000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.700000"),
                signal_config_version="umich-inflation-expectations-blocked-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(
        report,
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReport,
    )
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-umich-inflation-expectations-surprise-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_umich_inflation_expectations_"
        "surprise_digest"
    )
    assert report.signal_count == d("3.000000")
    assert report.ready_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.stale_signal_count == d("1.000000")
    assert report.material_surprise_count == d("2.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.high_revision_count == d("1.000000")
    assert report.confirmation_gap_count == d("1.000000")
    assert report.average_abs_surprise_delta == d("0.450000")
    assert report.average_final_confidence == d("0.600000")
    assert report.max_observed_signal_age_seconds == d("18000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.digest_status, row.release_id) for row in report.rows) == (
        ("blocked", "a.blocked.umich.inflation_expectations"),
        ("watch", "m.watch.umich.inflation_expectations"),
        ("ready", "z.ready.umich.inflation_expectations"),
    )

    blocked = report.rows[0]
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=5)
    assert blocked.signal_age_seconds == d("18000.000000")
    assert blocked.surprise_delta == d("0.800000")
    assert blocked.abs_surprise_delta == d("0.800000")
    assert blocked.surprise_direction == "higher"
    assert blocked.confidence_decay_factor == d("0.550000")
    assert blocked.final_confidence == d("0.150000")
    assert blocked.reason_codes == (
        "market_research_umich_inflation_expectations_surprise_digest_"
        "confirmation_gap",
        "market_research_umich_inflation_expectations_surprise_digest_"
        "material_surprise",
        "market_research_umich_inflation_expectations_surprise_digest_"
        "stale_signal",
        "market_research_umich_inflation_expectations_surprise_digest_"
        "thin_sources",
    )

    watched = report.rows[1]
    assert watched.surprise_delta == d("0.450000")
    assert watched.abs_surprise_delta == d("0.450000")
    assert watched.surprise_direction == "higher"
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.750000")
    assert watched.public_signal_reference == (
        "umich-public-inflation-expectations-release"
    )
    assert watched.reason_codes == (
        "market_research_umich_inflation_expectations_surprise_digest_"
        "high_revision",
        "market_research_umich_inflation_expectations_surprise_digest_"
        "material_surprise",
    )

    ready = report.rows[2]
    assert ready.surprise_delta == d("0.100000")
    assert ready.surprise_direction == "higher"
    assert ready.reason_codes == (
        "market_research_umich_inflation_expectations_surprise_digest_ready",
    )
    assert ready.final_confidence == d("0.900000")

    assert report.reason_code_counts == (
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_"
                "material_surprise"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_"
                "confirmation_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_"
                "high_revision"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_"
                "stale_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_"
                "thin_sources"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_ready"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == tuple(
        item.reason_code for item in report.reason_code_counts
    )
    _walk_public_values(config(), "config")
    _walk_public_values(signal(), "signal")
    _walk_public_values(report, "report")


def test_umich_inflation_expectations_surprise_empty_inputs_block_as_missing_evidence() -> None:
    module = api()
    report = digest(())

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_umich_inflation_expectations_surprise_digest"
    )
    assert report.signal_count == d("0.000000")
    assert report.ready_signal_count == d("0.000000")
    assert report.watch_signal_count == d("0.000000")
    assert report.blocked_signal_count == d("0.000000")
    assert report.average_abs_surprise_delta == d("0.000000")
    assert report.average_final_confidence == d("0.000000")
    assert report.max_observed_signal_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_umich_inflation_expectations_surprise_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_no_inputs"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_umich_inflation_expectations_surprise_frozen_decimal_payload_and_guardrails() -> None:
    module = api()
    report = digest((signal(),))

    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "watch"  # type: ignore[misc]

    payload = module.market_research_umich_inflation_expectations_surprise_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["average_final_confidence"] == "0.900000"
    assert payload["rows"][0]["actual_inflation_expectation"] == "3.100000"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T13:15:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    _assert_payload_has_no_live_values(payload)
    _assert_six_decimal_string(payload["signal_count"])
    _assert_six_decimal_string(payload["rows"][0]["surprise_delta"])

    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="row paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="reason code count report_only"):
        replace(report.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="aware datetime"):
        signal(observed_at=datetime(2026, 7, 5, 13, 0))
    with pytest.raises(ValueError, match="aware datetime"):
        signal(observed_at=datetime(2026, 7, 5, 13, 0, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 5, 13, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="exact Decimal"):
        signal(expected_inflation_expectation=_DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="source_count must be a whole-count Decimal"):
        signal(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="public_signal_reference"):
        signal(public_signal_reference="https://example.invalid/umich?token=x")
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        digest((signal(observed_at=GENERATED_AT + timedelta(microseconds=1)),))

    for type_ in (
        module.MarketResearchUmichInflationExpectationsSurpriseDigestConfig,
        module.MarketResearchUmichInflationExpectationsSurpriseDigestSignal,
        module.MarketResearchUmichInflationExpectationsSurpriseDigestRow,
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount,
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReport,
    ):
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type

        with pytest.raises(TypeError, match="subclassing"):
            type(f"{type_.__name__}Subclass", (type_,), {})

    with pytest.raises(ValueError, match="count"):
        module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_umich_inflation_expectations_surprise_digest_no_inputs"
            ),
            count=d("0.000000"),
            signal_ratio=d("0.000000"),
        )

    with pytest.raises(
        ValueError,
        match=(
            "report must be a "
            "MarketResearchUmichInflationExpectationsSurpriseDigestReport"
        ),
    ):
        module.market_research_umich_inflation_expectations_surprise_digest_payload(
            object(),
        )


def test_umich_inflation_expectations_surprise_public_constructors_reject_noncanonical_ordering() -> None:
    module = api()
    report = digest(
        (
            signal(
                "research.umich_inflation_expectations.ready",
                condition_id="condition_ready",
                release_id="z.ready.umich.inflation_expectations",
            ),
            signal(
                "research.umich_inflation_expectations.watch",
                condition_id="condition_watch",
                release_id="m.watch.umich.inflation_expectations",
                actual_inflation_expectation=d("3.450000"),
                revision_ratio=d("0.300000"),
            ),
            signal(
                "research.umich_inflation_expectations.blocked",
                condition_id="condition_blocked",
                release_id="a.blocked.umich.inflation_expectations",
                source_count=d("1.000000"),
                confirmation_ratio=d("0.400000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(report.rows[1], reason_codes=tuple(reversed(report.rows[1].reason_codes)))
    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must use deterministic ordering"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(report, reason_codes=tuple(reversed(report.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(
            report,
            reason_code_counts=(
                module.MarketResearchUmichInflationExpectationsSurpriseDigestReasonCodeCount(
                    reason_code=(
                        "market_research_umich_inflation_expectations_surprise_digest_"
                        "no_inputs"
                    ),
                    count=d("1.000000"),
                    signal_ratio=d("0.000000"),
                ),
            ),
            reason_codes=(
                "market_research_umich_inflation_expectations_surprise_digest_no_inputs",
            ),
        )
    with pytest.raises(ValueError, match="signals must contain unique release_id"):
        digest(
            (
                signal(release_id="duplicate.umich.inflation_expectations"),
                signal(
                    research_id="research.umich_inflation_expectations.duplicate",
                    condition_id="condition_duplicate",
                    release_id="duplicate.umich.inflation_expectations",
                ),
            ),
        )


def test_umich_inflation_expectations_surprise_module_scope_is_pure_report_only() -> None:
    module = api()
    source = inspect.getsource(module).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "submit_order",
        "api_key",
        "exchange",
        "live trading",
        "fast",
    ):
        assert forbidden not in source

    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_umich_inflation_expectations_surprise_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            function_name = ""
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            assert function_name not in {
                "open",
                "connect",
                "execute",
                "request",
                "urlopen",
                "trade",
                "submit",
                "cancel",
                "sign",
            }
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "pathlib",
        "sqlite3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
