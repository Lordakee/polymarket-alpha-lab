from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_crypto_onchain_signal_readiness_report import (
    ResearchCryptoOnchainSignalReadinessConfig,
    ResearchCryptoOnchainSignalReadinessReasonCodeCount,
    ResearchCryptoOnchainSignalReadinessReport,
    ResearchCryptoOnchainSignalReadinessRow,
    ResearchCryptoOnchainSignalReadinessSignal,
    build_research_crypto_onchain_signal_readiness_report,
    research_crypto_onchain_signal_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
REFRESHED_AT = datetime(2026, 7, 6, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCryptoOnchainSignalReadinessConfig:
    values = {
        "config_version": "research-crypto-onchain-signal-readiness-report-v0",
        "pass_readiness_score": d("0.800000"),
        "watch_readiness_score": d("0.550000"),
        "min_independent_family_count": d("2.000000"),
        "min_independence_score": d("0.700000"),
        "block_independence_score": d("0.400000"),
        "min_metric_stability_score": d("0.700000"),
        "block_metric_stability_score": d("0.400000"),
        "min_rebuttal_check_count": d("1.000000"),
        "watch_rebuttal_strength": d("0.300000"),
        "block_rebuttal_strength": d("0.600000"),
        "max_refresh_age_seconds": d("7200.000000"),
        "data_latency_weight": d("0.250000"),
        "independence_weight": d("0.250000"),
        "metric_stability_weight": d("0.250000"),
        "rebuttal_weight": d("0.150000"),
        "refresh_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchCryptoOnchainSignalReadinessConfig(**values)


def signal(
    index: int,
    *,
    internal_signal_key: str | None = None,
    asset_group: str = "btc",
    indicator_family: str = "exchange_flow",
    observed_at: datetime = OBSERVED_AT,
    refreshed_at: datetime | None = REFRESHED_AT,
    data_latency_seconds: Decimal = d("900.000000"),
    max_allowed_latency_seconds: Decimal = d("1800.000000"),
    independent_family_count: Decimal = d("3.000000"),
    independence_score: Decimal = d("0.900000"),
    metric_stability_score: Decimal = d("0.900000"),
    rebuttal_check_count: Decimal = d("2.000000"),
    rebuttal_strength: Decimal = d("0.100000"),
    refresh_required_within_seconds: Decimal = d("3600.000000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchCryptoOnchainSignalReadinessSignal:
    return ResearchCryptoOnchainSignalReadinessSignal(
        internal_signal_key=internal_signal_key or f"internal-signal-{index:03d}",
        asset_group=asset_group,
        indicator_family=indicator_family,
        observed_at=observed_at,
        refreshed_at=refreshed_at,
        data_latency_seconds=data_latency_seconds,
        max_allowed_latency_seconds=max_allowed_latency_seconds,
        independent_family_count=independent_family_count,
        independence_score=independence_score,
        metric_stability_score=metric_stability_score,
        rebuttal_check_count=rebuttal_check_count,
        rebuttal_strength=rebuttal_strength,
        refresh_required_within_seconds=refresh_required_within_seconds,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchCryptoOnchainSignalReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCryptoOnchainSignalReadinessReport:
    return build_research_crypto_onchain_signal_readiness_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_without_rows() -> None:
    readiness_report = report(())

    assert type(readiness_report) is ResearchCryptoOnchainSignalReadinessReport
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.signal_count == d("0.000000")
    assert readiness_report.pass_count == d("0.000000")
    assert readiness_report.watch_count == d("0.000000")
    assert readiness_report.block_count == d("0.000000")
    assert readiness_report.refresh_due_count == d("0.000000")
    assert readiness_report.contrary_count == d("0.000000")
    assert readiness_report.average_readiness_score is None
    assert readiness_report.max_data_latency_seconds is None
    assert readiness_report.minimum_independence_score is None
    assert readiness_report.minimum_stability_score is None
    assert readiness_report.status == "block"
    assert readiness_report.rows == ()
    assert readiness_report.reason_codes == ("no_signals_to_assess",)
    assert readiness_report.reason_code_counts == (
        ResearchCryptoOnchainSignalReadinessReasonCodeCount(
            reason_code="no_signals_to_assess",
            count=d("1.000000"),
            signal_ratio=d("1.000000"),
        ),
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_fresh_independent_stable_signal_passes() -> None:
    readiness_report = report((signal(1),))

    assert readiness_report.status == "pass"
    assert readiness_report.signal_count == d("1.000000")
    assert readiness_report.pass_count == d("1.000000")
    assert readiness_report.watch_count == d("0.000000")
    assert readiness_report.block_count == d("0.000000")
    assert readiness_report.refresh_due_count == d("0.000000")
    assert readiness_report.contrary_count == d("0.000000")
    assert readiness_report.average_readiness_score == d("0.950000")
    assert readiness_report.max_data_latency_seconds == d("900.000000")
    assert readiness_report.minimum_independence_score == d("0.900000")
    assert readiness_report.minimum_stability_score == d("0.900000")
    assert readiness_report.reason_codes == ("onchain_signal_pass",)

    row = readiness_report.rows[0]
    assert type(row) is ResearchCryptoOnchainSignalReadinessRow
    assert row.signal_index == d("1.000000")
    assert row.asset_group == "btc"
    assert row.indicator_family == "exchange_flow"
    assert row.observed_at == OBSERVED_AT
    assert row.refresh_age_seconds == d("1800.000000")
    assert row.data_latency_seconds == d("900.000000")
    assert row.data_latency_score == d("1.000000")
    assert row.independence_score == d("0.900000")
    assert row.metric_stability_score == d("0.900000")
    assert row.rebuttal_score == d("1.000000")
    assert row.refresh_score == d("1.000000")
    assert row.readiness_score == d("0.950000")
    assert row.status == "pass"
    assert row.refresh_action == "keep_cadence"
    assert row.reason_codes == (
        "data_latency_within_sla",
        "independence_pass",
        "metric_stability_pass",
        "onchain_signal_pass",
        "rebuttal_clear",
        "refresh_current",
    )


def test_degraded_independence_stability_latency_and_refresh_are_watch() -> None:
    readiness_report = report(
        (
            signal(
                1,
                asset_group="crypto",
                indicator_family="chain_activity",
                refreshed_at=datetime(2026, 7, 6, 10, 30, tzinfo=UTC),
                data_latency_seconds=d("3000.000000"),
                max_allowed_latency_seconds=d("1800.000000"),
                independent_family_count=d("2.000000"),
                independence_score=d("0.650000"),
                metric_stability_score=d("0.650000"),
                rebuttal_strength=d("0.350000"),
                refresh_required_within_seconds=d("1800.000000"),
                reason_codes=("manual_reviewed",),
            ),
        ),
    )

    assert readiness_report.status == "watch"
    assert readiness_report.watch_count == d("1.000000")
    assert readiness_report.refresh_due_count == d("1.000000")
    assert readiness_report.contrary_count == d("1.000000")
    assert readiness_report.average_readiness_score == d("0.575000")

    row = readiness_report.rows[0]
    assert row.status == "watch"
    assert row.refresh_action == "refresh_before_use"
    assert row.data_latency_score == d("0.500000")
    assert row.independence_score == d("0.650000")
    assert row.metric_stability_score == d("0.650000")
    assert row.rebuttal_score == d("0.500000")
    assert row.refresh_score == d("0.500000")
    assert row.readiness_score == d("0.575000")
    assert row.reason_codes == (
        "data_latency_watch",
        "independence_watch",
        "input_manual_reviewed",
        "metric_stability_watch",
        "onchain_signal_watch",
        "rebuttal_watch",
        "refresh_watch",
    )


def test_latency_contrary_evidence_and_missing_refresh_block_readiness() -> None:
    readiness_report = report(
        (
            signal(
                1,
                refreshed_at=None,
                data_latency_seconds=d("5000.000000"),
                max_allowed_latency_seconds=d("1800.000000"),
                independent_family_count=d("1.000000"),
                independence_score=d("0.600000"),
                metric_stability_score=d("0.300000"),
                rebuttal_check_count=d("1.000000"),
                rebuttal_strength=d("0.700000"),
            ),
        ),
    )

    row = readiness_report.rows[0]
    assert readiness_report.status == "block"
    assert readiness_report.block_count == d("1.000000")
    assert readiness_report.refresh_due_count == d("1.000000")
    assert readiness_report.contrary_count == d("1.000000")
    assert readiness_report.average_readiness_score == d("0.150000")
    assert row.status == "block"
    assert row.refresh_age_seconds is None
    assert row.data_latency_score == d("0.000000")
    assert row.independence_score == d("0.300000")
    assert row.metric_stability_score == d("0.300000")
    assert row.rebuttal_score == d("0.000000")
    assert row.refresh_score == d("0.000000")
    assert row.refresh_action == "manual_review_before_use"
    assert row.reason_codes == (
        "data_latency_block",
        "independence_block",
        "metric_stability_block",
        "onchain_signal_block",
        "rebuttal_block",
        "refresh_due",
    )


def test_rows_are_sorted_and_payload_uses_decimal_strings_without_private_material() -> None:
    internal_locator = (
        "https://btc.example/wallet/address?token=abc&table=raw_market&dsn=hidden"
    )
    readiness_report = report(
        (
            signal(2, internal_signal_key="z-internal"),
            signal(
                1,
                internal_signal_key=internal_locator,
                indicator_family="miner_activity",
            ),
        ),
    )
    payload = research_crypto_onchain_signal_readiness_report_payload(readiness_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert readiness_report.payload == payload
    assert tuple(row.signal_index for row in readiness_report.rows) == (
        d("1.000000"),
        d("2.000000"),
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["signal_count"] == "2.000000"
    assert payload["average_readiness_score"] == "0.950000"
    assert payload["rows"][0]["indicator_family"] == "miner_activity"
    assert payload["rows"][0]["readiness_score"] == "0.950000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert internal_locator.lower() not in encoded
    for unsafe_fragment in (
        "wallet",
        "address",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "raw_market",
        "condition_id",
        "slug",
        "https://",
    ):
        assert unsafe_fragment not in encoded

    with pytest.raises(ValueError, match="unsafe public material"):
        signal(3, reason_codes=("token_found",))
    with pytest.raises(ValueError, match="unsafe public material"):
        signal(4, reason_codes=("raw_market_seen",))


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    numeric_fields = {
        "pass_readiness_score",
        "watch_readiness_score",
        "min_independent_family_count",
        "min_independence_score",
        "block_independence_score",
        "min_metric_stability_score",
        "block_metric_stability_score",
        "min_rebuttal_check_count",
        "watch_rebuttal_strength",
        "block_rebuttal_strength",
        "max_refresh_age_seconds",
        "data_latency_weight",
        "independence_weight",
        "metric_stability_weight",
        "rebuttal_weight",
        "refresh_weight",
        "data_latency_seconds",
        "max_allowed_latency_seconds",
        "independent_family_count",
        "independence_score",
        "metric_stability_score",
        "rebuttal_check_count",
        "rebuttal_strength",
        "refresh_required_within_seconds",
        "signal_index",
        "data_latency_score",
        "rebuttal_score",
        "refresh_score",
        "readiness_score",
        "count",
        "signal_ratio",
        "signal_count",
        "pass_count",
        "watch_count",
        "block_count",
        "refresh_due_count",
        "contrary_count",
    }

    for cls in (
        ResearchCryptoOnchainSignalReadinessConfig,
        ResearchCryptoOnchainSignalReadinessSignal,
        ResearchCryptoOnchainSignalReadinessRow,
        ResearchCryptoOnchainSignalReadinessReasonCodeCount,
        ResearchCryptoOnchainSignalReadinessReport,
    ):
        hints = get_type_hints(cls)
        for item_name, item_hint in hints.items():
            if item_name in numeric_fields:
                assert item_hint is Decimal


def test_validation_rejects_bad_types_ranges_duplicates_flags_and_manual_inconsistency() -> None:
    with pytest.raises(ValueError, match="data_latency_weight"):
        config(data_latency_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_readiness_score"):
        config(pass_readiness_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="refresh_weight"):
        config(refresh_weight=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-crypto-onchain-signal-readiness-report-v0"))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (signal(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="signals"):
        report(("not-a-signal",))
    with pytest.raises(ValueError, match="unique"):
        report((signal(1, internal_signal_key="dup"), signal(2, internal_signal_key="dup")))
    with pytest.raises(ValueError, match="asset_group"):
        signal(1, asset_group="equities")
    with pytest.raises(ValueError, match="indicator_family"):
        signal(1, indicator_family="unknown")
    with pytest.raises(ValueError, match="data_latency_seconds"):
        signal(1, data_latency_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="data_latency_seconds"):
        signal(1, data_latency_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_family_count"):
        signal(1, independent_family_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        signal(1, reason_codes=("manual_reviewed", "manual_reviewed"))
    with pytest.raises(ValueError, match="refreshed_at"):
        report(
            (
                signal(
                    1,
                    refreshed_at=datetime(2026, 7, 6, 9, 0, tzinfo=UTC),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal(1), paper_only=False)

    readiness_report = report((signal(1),))
    with pytest.raises(FrozenInstanceError):
        readiness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].readiness_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="pass_count"):
        replace(readiness_report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="signal_index"):
        replace(readiness_report, rows=(readiness_report.rows[0], readiness_report.rows[0]))
    with pytest.raises(ValueError, match="signal_index"):
        replace(readiness_report.rows[0], signal_index=d("1.500000"))


def test_owned_module_has_no_external_mutation_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_crypto_onchain_signal_readiness_report.py"
    )
    module_code = module_path.read_text(encoding="utf-8")
    lowered = module_code.lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        ".get(",
        ".post(",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "supabase",
        "execute(",
        "insert ",
        "update ",
        "delete ",
    )

    assert all(term not in lowered for term in forbidden_terms)
    tree = ast.parse(module_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
