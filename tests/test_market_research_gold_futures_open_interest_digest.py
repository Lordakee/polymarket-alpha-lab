from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_research_gold_futures_open_interest_digest"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_gold_futures_open_interest_digest.py",
)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"{MODULE_NAME} is not implemented: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("7200.000000"),
        "min_open_interest_contracts": d("10000.000000"),
        "min_volume_contracts": d("2500.000000"),
        "max_open_interest_change_abs": d("0.200000"),
        "min_source_count": d("2.000000"),
        "max_concentration_ratio": d("0.650000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confidence": d("0.650000"),
    }
    values.update(overrides)
    return module.MarketResearchGoldFuturesOpenInterestDigestConfig(**values)


def snapshot(
    open_interest_key: str = "gold.futures.oi.ready",
    *,
    condition_id: str = "condition_gold_futures_oi_ready",
    contract_bucket: str = "front_month",
    observed_at: datetime | None = None,
    open_interest_contracts: Decimal = d("18000.000000"),
    open_interest_change_ratio: Decimal = d("0.060000"),
    volume_contracts: Decimal = d("4800.000000"),
    volume_to_open_interest_ratio: Decimal = d("0.266667"),
    position_concentration_ratio: Decimal = d("0.420000"),
    source_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.050000"),
    confidence: Decimal = d("0.840000"),
    source_config_version: str = "gold-futures-oi-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchGoldFuturesOpenInterestSnapshot(
        condition_id=condition_id,
        open_interest_key=open_interest_key,
        contract_bucket=contract_bucket,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=45),
        open_interest_contracts=open_interest_contracts,
        open_interest_change_ratio=open_interest_change_ratio,
        volume_contracts=volume_contracts,
        volume_to_open_interest_ratio=volume_to_open_interest_ratio,
        position_concentration_ratio=position_concentration_ratio,
        source_count=source_count,
        stale_source_ratio=stale_source_ratio,
        confidence=confidence,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    snapshots: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_market_research_gold_futures_open_interest_digest(
        snapshots,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        pytest.fail(f"found public numeric that is not a Decimal string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, tuple):
        for item in value:
            assert_no_public_float_or_int(item)


def test_gold_futures_open_interest_digest_reduces_snapshots_and_sorts() -> None:
    module = api()

    summary = report(
        (
            snapshot(
                "gold.futures.oi.blocked",
                condition_id="condition_gold_futures_oi_blocked",
                contract_bucket="front_month",
                observed_at=GENERATED_AT - timedelta(hours=3),
                open_interest_contracts=d("7500.000000"),
                open_interest_change_ratio=d("-0.310000"),
                volume_contracts=d("1200.000000"),
                volume_to_open_interest_ratio=d("0.160000"),
                position_concentration_ratio=d("0.720000"),
                source_count=d("1.000000"),
                stale_source_ratio=d("0.400000"),
                confidence=d("0.520000"),
            ),
            snapshot(
                "gold.futures.oi.watch",
                condition_id="condition_gold_futures_oi_watch",
                contract_bucket="deferred_quarter",
                source_count=d("1.000000"),
                stale_source_ratio=d("0.100000"),
                confidence=d("0.760000"),
            ),
            snapshot("gold.futures.oi.ready"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.MarketResearchGoldFuturesOpenInterestDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_futures_open_interest_digest"
    )
    assert summary.snapshot_count == d("3.000000")
    assert summary.ready_snapshot_count == d("1.000000")
    assert summary.watch_snapshot_count == d("1.000000")
    assert summary.blocked_snapshot_count == d("1.000000")
    assert summary.stale_snapshot_count == d("1.000000")
    assert summary.thin_source_snapshot_count == d("2.000000")
    assert summary.low_open_interest_snapshot_count == d("1.000000")
    assert summary.low_volume_snapshot_count == d("1.000000")
    assert summary.open_interest_shock_snapshot_count == d("1.000000")
    assert summary.concentration_pressure_snapshot_count == d("1.000000")
    assert summary.stale_source_snapshot_count == d("1.000000")
    assert summary.confidence_gap_snapshot_count == d("1.000000")
    assert summary.average_open_interest_contracts == d("14500.000000")
    assert summary.average_volume_contracts == d("3600.000000")
    assert summary.average_open_interest_change_ratio == d("-0.063333")
    assert summary.average_volume_to_open_interest_ratio == d("0.231111")
    assert summary.average_position_concentration_ratio == d("0.520000")
    assert summary.max_observed_snapshot_age_seconds == d("10800.000000")
    assert summary.ready_snapshot_ratio == d("0.333333")

    assert tuple(row.open_interest_key for row in summary.rows) == (
        "gold.futures.oi.blocked",
        "gold.futures.oi.watch",
        "gold.futures.oi.ready",
    )
    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.snapshot_age_seconds == d("10800.000000")
    assert blocked.open_interest_change_abs == d("0.310000")
    assert blocked.reason_codes == (
        "market_research_gold_futures_open_interest_digest_stale_snapshot",
        "market_research_gold_futures_open_interest_digest_thin_source_count",
        "market_research_gold_futures_open_interest_digest_low_open_interest",
        "market_research_gold_futures_open_interest_digest_low_volume",
        "market_research_gold_futures_open_interest_digest_open_interest_shock",
        "market_research_gold_futures_open_interest_digest_concentration_pressure",
        "market_research_gold_futures_open_interest_digest_stale_source_ratio",
        "market_research_gold_futures_open_interest_digest_confidence_gap",
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.source_config_versions == (
        ("gold.futures.oi.blocked", "gold-futures-oi-source-v0"),
        ("gold.futures.oi.ready", "gold-futures-oi-source-v0"),
        ("gold.futures.oi.watch", "gold-futures-oi-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_gold_futures_open_interest_empty_inputs_are_report_only_blocked() -> None:
    module = api()

    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_futures_open_interest_digest"
    )
    assert summary.snapshot_count == ZERO
    assert summary.ready_snapshot_count == ZERO
    assert summary.watch_snapshot_count == ZERO
    assert summary.blocked_snapshot_count == ZERO
    assert summary.average_open_interest_contracts == ZERO
    assert summary.average_volume_contracts == ZERO
    assert summary.average_open_interest_change_ratio == ZERO
    assert summary.average_volume_to_open_interest_ratio == ZERO
    assert summary.average_position_concentration_ratio == ZERO
    assert summary.max_observed_snapshot_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.source_config_versions == ()
    assert summary.reason_code_counts == (
        module.MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_futures_open_interest_digest_no_inputs"
            ),
            count=d("1.000000"),
            snapshot_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_gold_futures_open_interest_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_gold_futures_open_interest_validates_contracts_payload_and_no_io() -> None:
    module = api()

    assert module.MarketResearchGoldFuturesOpenInterestDigestConfig.__dataclass_params__.frozen
    assert module.MarketResearchGoldFuturesOpenInterestSnapshot.__dataclass_params__.frozen
    assert module.MarketResearchGoldFuturesOpenInterestDigestRow.__dataclass_params__.frozen
    assert (
        module.MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert module.MarketResearchGoldFuturesOpenInterestDigestReport.__dataclass_params__.frozen

    frozen_summary = report((snapshot(),))
    with pytest.raises(FrozenInstanceError):
        config().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        snapshot().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_summary.rows[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_summary.reason_code_counts[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_summary.paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("gold-futures-oi-v0"))
    with pytest.raises(ValueError, match="max_snapshot_age_seconds"):
        config(max_snapshot_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="open_interest_key"):
        snapshot(_StringSubclass("gold.futures.oi.bad"))
    with pytest.raises(ValueError, match="condition_id"):
        snapshot(condition_id="condition gold futures oi bad")
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 4, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (snapshot(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="open_interest_contracts"):
        snapshot(open_interest_contracts=Decimal("NaN"))
    with pytest.raises(ValueError, match="source_count"):
        snapshot(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="position_concentration_ratio"):
        snapshot(position_concentration_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(TypeError, match="does not support subclassing"):
        type("BadConfig", (module.MarketResearchGoldFuturesOpenInterestDigestConfig,), {})

    base = snapshot()
    with pytest.raises(ValueError, match="duplicate open_interest_key"):
        module.build_market_research_gold_futures_open_interest_digest(
            (base, base),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_gold_futures_open_interest_digest(
            (base,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        report((snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="report"):
        module.market_research_gold_futures_open_interest_digest_payload(object())

    payload = module.market_research_gold_futures_open_interest_digest_payload(
        report((base,)),
    )
    assert payload["generated_at"] == "2026-07-04T14:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["rows"][0]["open_interest_change_ratio"] == "0.060000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["confidence"] = "0.000000"  # type: ignore[index]

    public = repr(payload).lower()
    assert "datetime." not in public
    assert "decimal(" not in public
    for token in (
        "market_slug",
        "question",
        "wallet",
        "broker",
        "signing",
        "submit",
        "account",
        "private",
    ):
        assert token not in public

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for token in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "private_key",
        "secret",
        "token",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "psycopg",
        "supabase",
        "web3",
    ):
        assert token not in lowered_source

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {"open", "connect", "request", "urlopen", "run", "Popen"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls


def test_gold_futures_open_interest_public_numeric_fields_are_decimal_only() -> None:
    summary = report((snapshot(),))

    for row in summary.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_contracts")
                or field.name.endswith("_abs")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
    for field in fields(summary):
        value = getattr(summary, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_contracts")
        ):
            assert type(value) is Decimal
    for reason_count in summary.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal


def test_gold_futures_open_interest_rejects_false_phase1_flags_explicitly() -> None:
    summary = report((snapshot(),))
    ready_row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    cases = (
        (lambda: config(paper_only=False), "paper_only"),
        (lambda: config(report_only=False), "report_only"),
        (lambda: config(readonly=False), "readonly"),
        (lambda: snapshot(paper_only=False), "paper_only"),
        (lambda: snapshot(report_only=False), "report_only"),
        (lambda: snapshot(readonly=False), "readonly"),
        (lambda: replace(ready_row, paper_only=False), "paper_only"),
        (lambda: replace(ready_row, report_only=False), "report_only"),
        (lambda: replace(ready_row, readonly=False), "readonly"),
        (lambda: replace(reason_count, paper_only=False), "paper_only"),
        (lambda: replace(reason_count, report_only=False), "report_only"),
        (lambda: replace(reason_count, readonly=False), "readonly"),
        (lambda: replace(summary, paper_only=False), "paper_only"),
        (lambda: replace(summary, report_only=False), "report_only"),
        (lambda: replace(summary, readonly=False), "readonly"),
    )
    for factory, flag_name in cases:
        with pytest.raises(ValueError, match=flag_name):
            factory()


def test_gold_futures_open_interest_rejects_falsey_non_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_market_research_gold_futures_open_interest_digest(
            (snapshot(),),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_gold_futures_open_interest_validates_direct_source_config_versions() -> None:
    summary = report((snapshot(),))

    with pytest.raises(ValueError, match="source_config_versions"):
        replace(summary, source_config_versions=())
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(
            summary,
            source_config_versions=(
                ("gold.futures.oi.other", "gold-futures-oi-source-v0"),
            ),
        )


def test_gold_futures_open_interest_validates_direct_report_consistency() -> None:
    summary = report((snapshot(),))

    with pytest.raises(ValueError, match="ready_snapshot_count"):
        replace(summary, ready_snapshot_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=())
    with pytest.raises(ValueError, match="snapshot_count"):
        replace(summary, snapshot_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
