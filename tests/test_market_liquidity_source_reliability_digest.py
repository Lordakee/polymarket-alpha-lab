from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import inspect

import pytest

import polymarket_alpha_lab.market_liquidity_source_reliability_digest as digest_module
from polymarket_alpha_lab.market_liquidity_source_reliability_digest import (
    MarketLiquiditySourceReliabilityDigestConfig,
    MarketLiquiditySourceReliabilityDigestObservation,
    MarketLiquiditySourceReliabilityDigestReport,
    MarketLiquiditySourceReliabilityDigestRow,
    build_market_liquidity_source_reliability_digest,
    market_liquidity_source_reliability_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def config(**overrides: object) -> MarketLiquiditySourceReliabilityDigestConfig:
    values: dict[str, object] = {
        "config_version": "market-liquidity-source-reliability-digest-v1",
        "max_source_age_seconds": Decimal("60.000000"),
        "max_depth_disagreement_ratio": Decimal("0.250000"),
        "max_spread_disagreement_ratio": Decimal("0.200000"),
        "min_source_family_count": Decimal("2.000000"),
    }
    values.update(overrides)
    return MarketLiquiditySourceReliabilityDigestConfig(**values)


def observation(
    market_slug: str = "alpha-market",
    *,
    outcome_name: str = "Yes",
    source_family: str = "clob",
    source_name: str = "clob-book",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=12),
    bid_depth: Decimal = Decimal("100.000000"),
    ask_depth: Decimal = Decimal("120.000000"),
    spread: Decimal = Decimal("0.040000"),
    reference: str = "public/clob/book",
    reason_codes: tuple[str, ...] = ("source_snapshot_ok",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketLiquiditySourceReliabilityDigestObservation:
    return MarketLiquiditySourceReliabilityDigestObservation(
        market_slug=market_slug,
        outcome_name=outcome_name,
        source_family=source_family,
        source_name=source_name,
        observed_at=observed_at,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        spread=spread,
        reference=reference,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    observations: tuple[MarketLiquiditySourceReliabilityDigestObservation, ...],
    *,
    cfg: MarketLiquiditySourceReliabilityDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketLiquiditySourceReliabilityDigestReport:
    return build_market_liquidity_source_reliability_digest(
        observations,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def decimal_public_field_names(type_: type[object]) -> set[str]:
    return {
        field.name
        for field in fields(type_)
        if "Decimal" in str(field.type) or field.type is Decimal
    }


def test_empty_input_returns_report_only_rollup() -> None:
    report = digest(())

    assert report.generated_at == GENERATED_AT
    assert report.observation_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.stale_source_family_count == Decimal("0.000000")
    assert report.depth_disagreement_count == Decimal("0.000000")
    assert report.spread_disagreement_count == Decimal("0.000000")
    assert report.missing_redundancy_count == Decimal("0.000000")
    assert report.max_source_age_seconds_observed == Decimal("0.000000")
    assert report.max_depth_disagreement_ratio_observed == Decimal("0.000000")
    assert report.max_spread_disagreement_ratio_observed == Decimal("0.000000")
    assert report.reason_codes == ("no_liquidity_observations",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reliable_redundant_sources_pass_and_redact_references() -> None:
    report = digest(
        (
            observation(
                source_family="gamma",
                source_name="gamma-market",
                bid_depth=Decimal("99.000000"),
                ask_depth=Decimal("121.000000"),
                spread=Decimal("0.041000"),
                reference="https://example.test/markets?api_key=secret",
            ),
            observation(),
        ),
    )

    assert report.observation_count == Decimal("2.000000")
    assert report.row_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.reason_codes == (
        "depth_agreement_pass",
        "source_redundancy_pass",
        "source_snapshot_ok",
        "source_timeliness_pass",
        "spread_agreement_pass",
    )

    row = report.rows[0]
    assert row.market_slug == "alpha-market"
    assert row.outcome_name == "Yes"
    assert row.reliability_status == "pass"
    assert row.source_family_count == Decimal("2.000000")
    assert row.observation_count == Decimal("2.000000")
    assert row.stale_source_family_count == Decimal("0.000000")
    assert row.missing_redundancy is False
    assert row.depth_disagreement_ratio == Decimal("0.010050")
    assert row.spread_disagreement_ratio == Decimal("0.024691")
    assert row.observation_references == (
        "clob-book:public/clob/book",
        "gamma-market:https://example.test/markets?<redacted>",
    )
    assert row.reason_codes == report.reason_codes


def test_nonblocking_source_warning_sets_watch_status() -> None:
    report = digest(
        (
            observation(reason_codes=("source_latency_warning",)),
            observation(source_family="gamma", reason_codes=("source_snapshot_ok",)),
        ),
    )

    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.rows[0].reliability_status == "watch"
    assert "source_latency_warning" in report.rows[0].reason_codes


def test_flags_stale_source_family_depth_spread_and_missing_redundancy() -> None:
    captured_at = datetime(2026, 7, 2, 4, 58, 30, tzinfo=timezone(timedelta(hours=-7)))
    report = digest(
        (
            observation(
                source_family="clob",
                source_name="clob-book",
                observed_at=captured_at,
                bid_depth=Decimal("40.000000"),
                ask_depth=Decimal("60.000000"),
                spread=Decimal("0.090000"),
                reason_codes=("primary_feed_delayed",),
            ),
            observation(
                source_family="clob",
                source_name="clob-depth",
                observed_at=GENERATED_AT - timedelta(seconds=20),
                bid_depth=Decimal("120.000000"),
                ask_depth=Decimal("140.000000"),
                spread=Decimal("0.030000"),
                reason_codes=("depth_crosscheck_ok",),
            ),
        ),
    )

    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("1.000000")
    assert report.stale_source_family_count == Decimal("1.000000")
    assert report.depth_disagreement_count == Decimal("1.000000")
    assert report.spread_disagreement_count == Decimal("1.000000")
    assert report.missing_redundancy_count == Decimal("1.000000")

    row = report.rows[0]
    assert row.reliability_status == "blocked"
    assert row.latest_observed_at == GENERATED_AT - timedelta(seconds=20)
    assert row.oldest_observed_at == datetime(2026, 7, 2, 11, 58, 30, tzinfo=UTC)
    assert row.max_source_age_seconds == Decimal("90.000000")
    assert row.source_family_count == Decimal("1.000000")
    assert row.stale_source_family_count == Decimal("1.000000")
    assert row.depth_disagreement_ratio == Decimal("1.000000")
    assert row.spread_disagreement_ratio == Decimal("1.000000")
    assert row.missing_redundancy is True
    assert row.reason_codes == (
        "depth_crosscheck_ok",
        "depth_disagreement",
        "missing_source_redundancy",
        "primary_feed_delayed",
        "source_family_stale",
        "spread_disagreement",
    )


def test_multiple_markets_sort_deterministically() -> None:
    report = digest(
        (
            observation("zeta-market", source_family="gamma", source_name="gamma-zeta"),
            observation("alpha-market", outcome_name="No", source_family="gamma"),
            observation("zeta-market"),
            observation("alpha-market", outcome_name="No", source_family="clob"),
        ),
    )

    assert [(row.market_slug, row.outcome_name) for row in report.rows] == [
        ("alpha-market", "No"),
        ("zeta-market", "Yes"),
    ]


def test_rejects_non_decimal_numeric_fields_and_float_inputs() -> None:
    with pytest.raises(ValueError, match="bid_depth"):
        observation(bid_depth=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="spread"):
        observation(spread=0.04)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=_DecimalSubclass("60.000000"))


def test_config_requires_positive_operating_thresholds() -> None:
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=Decimal("0.000000"))

    with pytest.raises(ValueError, match="min_source_family_count"):
        config(min_source_family_count=Decimal("0.000000"))

    assert config(max_depth_disagreement_ratio=Decimal("0.000000")).paper_only is True


def test_rejects_nonfinite_decimal_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        observation(bid_depth=Decimal("NaN"))

    with pytest.raises(ValueError, match="finite"):
        config(max_spread_disagreement_ratio=Decimal("Infinity"))


def test_rejects_naive_datetime_and_datetime_subclass() -> None:
    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC))


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    report = digest((observation(), observation(source_family="gamma"),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        MarketLiquiditySourceReliabilityDigestRow(
            market_slug="alpha-market",
            outcome_name="Yes",
            reliability_status="pass",
            source_family_count=Decimal("2.000000"),
            observation_count=Decimal("2.000000"),
            stale_source_family_count=Decimal("0.000000"),
            max_source_age_seconds=Decimal("12.000000"),
            min_bid_depth=Decimal("99.000000"),
            max_bid_depth=Decimal("100.000000"),
            min_ask_depth=Decimal("120.000000"),
            max_ask_depth=Decimal("121.000000"),
            depth_disagreement_ratio=Decimal("0.018182"),
            min_spread=Decimal("0.040000"),
            max_spread=Decimal("0.041000"),
            spread_disagreement_ratio=Decimal("0.024691"),
            missing_redundancy=False,
            latest_observed_at=GENERATED_AT,
            oldest_observed_at=GENERATED_AT - timedelta(seconds=12),
            observation_references=(),
            reason_codes=("source_redundancy_pass",),
            readonly=False,
        )


def test_public_count_and_ratio_fields_are_decimal_only() -> None:
    assert "source_family_count" in decimal_public_field_names(
        MarketLiquiditySourceReliabilityDigestRow,
    )
    assert "depth_disagreement_ratio" in decimal_public_field_names(
        MarketLiquiditySourceReliabilityDigestRow,
    )
    assert "observation_count" in decimal_public_field_names(
        MarketLiquiditySourceReliabilityDigestReport,
    )
    assert all(
        "int" not in str(field.type) and field.type is not int
        for type_ in (
            MarketLiquiditySourceReliabilityDigestConfig,
            MarketLiquiditySourceReliabilityDigestObservation,
            MarketLiquiditySourceReliabilityDigestRow,
            MarketLiquiditySourceReliabilityDigestReport,
        )
        for field in fields(type_)
    )


def test_payload_uses_strings_for_decimals_and_contains_no_floats() -> None:
    report = digest((observation(), observation(source_family="gamma"),))
    payload = market_liquidity_source_reliability_digest_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["depth_disagreement_ratio"] == "0.000000"
    assert_no_floats(payload)


def test_derived_validation_digest_revalidates_report_rows_and_public_payload() -> None:
    report = digest((observation(), observation(source_family="gamma"),))

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    payload = market_liquidity_source_reliability_digest_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert market_liquidity_source_reliability_digest_payload(dict(payload)) == payload

    tampered_report = digest(
        (
            observation(source_name="tamper-a"),
            observation(source_family="gamma", source_name="tamper-b"),
        ),
    )
    object.__setattr__(tampered_report, "observation_count", Decimal("3.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest|observation_count"):
        market_liquidity_source_reliability_digest_payload(tampered_report)

    tampered_row_report = digest(
        (
            observation(source_name="row-tamper-a"),
            observation(source_family="gamma", source_name="row-tamper-b"),
        ),
    )
    object.__setattr__(
        tampered_row_report.rows[0],
        "depth_disagreement_ratio",
        Decimal("0.990000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_liquidity_source_reliability_digest_payload(tampered_row_report)

    tampered_payload = dict(payload)
    tampered_payload["blocked_count"] = "1.000000"
    with pytest.raises(ValueError, match="derived_validation_digest|status counts"):
        market_liquidity_source_reliability_digest_payload(tampered_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_liquidity_source_reliability_digest_payload(missing_digest)


def test_payload_rejects_unexpected_public_ints_and_floats() -> None:
    with pytest.raises(ValueError, match="public float or int"):
        market_liquidity_source_reliability_digest_payload(1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="public float or int"):
        market_liquidity_source_reliability_digest_payload(0.1)  # type: ignore[arg-type]


def test_public_payload_rejects_unsafe_live_auth_wallet_order_network_database_persist_surface() -> None:
    report = digest((observation(), observation(source_family="gamma"),))
    payload = market_liquidity_source_reliability_digest_payload(report)

    unsafe_keys = (
        "li" + "ve_mode",
        "a" + "uth_token",
        "wal" + "let_address",
        "or" + "der_id",
        "net" + "work_client",
        "data" + "base_url",
        "per" + "sist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            market_liquidity_source_reliability_digest_payload(unsafe_payload)

    unsafe_values = (
        "li" + "ve mode enabled",
        "a" + "uth token configured",
        "wal" + "let transfer configured",
        "submit " + "or" + "der configured",
        "net" + "work request configured",
        "data" + "base writer configured",
        "per" + "sist report configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["config_version"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            market_liquidity_source_reliability_digest_payload(unsafe_payload)

    with pytest.raises(ValueError, match="unsafe"):
        observation(market_slug="wal" + "let-private-source")
    with pytest.raises(ValueError, match="unsafe"):
        observation(reason_codes=("net" + "work_probe",))

    tampered_report = digest((observation(), observation(source_family="gamma"),))
    object.__setattr__(tampered_report, "wal" + "let_address", "0xunsafe")
    with pytest.raises(ValueError, match="unsafe"):
        market_liquidity_source_reliability_digest_payload(tampered_report)


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(MarketLiquiditySourceReliabilityDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(MarketLiquiditySourceReliabilityDigestObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(MarketLiquiditySourceReliabilityDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(MarketLiquiditySourceReliabilityDigestReport):
            pass


def test_module_has_no_live_auth_wallet_order_network_database_or_persistence_surface() -> None:
    source = inspect.getsource(digest_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "io",
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
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert forbidden_import_roots.isdisjoint(imports)

    forbidden_identifiers = (
        "a" + "uth",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
    )
    public_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    public_names.update(
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    )
    public_names.update(getattr(digest_module, "__all__", ()))

    assert all(
        forbidden not in name.lower()
        for name in public_names
        for forbidden in forbidden_identifiers
    )


def test_manual_rows_reject_secret_references_and_inconsistent_status() -> None:
    with pytest.raises(ValueError, match="secrets"):
        MarketLiquiditySourceReliabilityDigestRow(
            market_slug="alpha-market",
            outcome_name="Yes",
            reliability_status="pass",
            source_family_count=Decimal("2.000000"),
            observation_count=Decimal("2.000000"),
            stale_source_family_count=Decimal("0.000000"),
            max_source_age_seconds=Decimal("12.000000"),
            min_bid_depth=Decimal("99.000000"),
            max_bid_depth=Decimal("100.000000"),
            min_ask_depth=Decimal("120.000000"),
            max_ask_depth=Decimal("121.000000"),
            depth_disagreement_ratio=Decimal("0.018182"),
            min_spread=Decimal("0.040000"),
            max_spread=Decimal("0.041000"),
            spread_disagreement_ratio=Decimal("0.024691"),
            missing_redundancy=False,
            latest_observed_at=GENERATED_AT,
            oldest_observed_at=GENERATED_AT - timedelta(seconds=12),
            observation_references=("clob-book:https://example.test?api_key=secret",),
            reason_codes=(
                "depth_agreement_pass",
                "source_redundancy_pass",
                "source_snapshot_ok",
                "source_timeliness_pass",
                "spread_agreement_pass",
            ),
        )

    with pytest.raises(ValueError, match="reliability_status"):
        MarketLiquiditySourceReliabilityDigestRow(
            market_slug="alpha-market",
            outcome_name="Yes",
            reliability_status="pass",
            source_family_count=Decimal("2.000000"),
            observation_count=Decimal("2.000000"),
            stale_source_family_count=Decimal("0.000000"),
            max_source_age_seconds=Decimal("12.000000"),
            min_bid_depth=Decimal("99.000000"),
            max_bid_depth=Decimal("100.000000"),
            min_ask_depth=Decimal("120.000000"),
            max_ask_depth=Decimal("121.000000"),
            depth_disagreement_ratio=Decimal("0.018182"),
            min_spread=Decimal("0.040000"),
            max_spread=Decimal("0.041000"),
            spread_disagreement_ratio=Decimal("0.024691"),
            missing_redundancy=False,
            latest_observed_at=GENERATED_AT,
            oldest_observed_at=GENERATED_AT - timedelta(seconds=12),
            observation_references=("clob-book:public/clob/book",),
            reason_codes=(
                "depth_agreement_pass",
                "source_latency_warning",
                "source_redundancy_pass",
                "source_timeliness_pass",
                "spread_agreement_pass",
            ),
        )


def test_direct_report_consistency_validation() -> None:
    with pytest.raises(ValueError, match="status counts"):
        MarketLiquiditySourceReliabilityDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-liquidity-source-reliability-digest-v1",
            observation_count=Decimal("1.000000"),
            row_count=Decimal("0.000000"),
            pass_count=Decimal("2.000000"),
            watch_count=Decimal("0.000000"),
            blocked_count=Decimal("0.000000"),
            stale_source_family_count=Decimal("0.000000"),
            depth_disagreement_count=Decimal("0.000000"),
            spread_disagreement_count=Decimal("0.000000"),
            missing_redundancy_count=Decimal("0.000000"),
            max_source_age_seconds_observed=Decimal("0.000000"),
            max_depth_disagreement_ratio_observed=Decimal("0.000000"),
            max_spread_disagreement_ratio_observed=Decimal("0.000000"),
            reason_codes=("source_redundancy_pass",),
            rows=(),
        )
