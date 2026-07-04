from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_repo_specialness_squeeze_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-rates-repo-specialness-squeeze-digest-v0",
        "max_signal_age_seconds": d("7200.000000"),
        "min_specialness_bps": d("25.000000"),
        "min_fails_to_deliver_ratio": d("0.350000"),
        "min_dealer_shortage_ratio": d("0.600000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return module.MarketResearchRatesRepoSpecialnessSqueezeDigestConfig(**values)


def repo_signal(
    condition_id: str = "condition.special.alpha",
    *,
    repo_market_key: str = "ust.on-the-run.10y.repo",
    collateral_bucket: str = "on-the-run-10y",
    public_signal_reference: str = "nyfed.soma.repo.specialness",
    observed_at: datetime | None = None,
    signal_age_seconds: Decimal = d("900.000000"),
    general_collateral_rate_pct: Decimal = d("5.300000"),
    specific_collateral_rate_pct: Decimal = d("4.800000"),
    fails_to_deliver_ratio: Decimal = d("0.420000"),
    dealer_shortage_ratio: Decimal = d("0.720000"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.850000"),
    signal_config_version: str = "repo-specialness-squeeze-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchRatesRepoSpecialnessSqueezeSignal(
        condition_id=condition_id,
        repo_market_key=repo_market_key,
        collateral_bucket=collateral_bucket,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        signal_age_seconds=signal_age_seconds,
        general_collateral_rate_pct=general_collateral_rate_pct,
        specific_collateral_rate_pct=specific_collateral_rate_pct,
        fails_to_deliver_ratio=fails_to_deliver_ratio,
        dealer_shortage_ratio=dealer_shortage_ratio,
        source_family_count=source_family_count,
        stale_source_ratio=stale_source_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_rates_repo_specialness_squeeze_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("public payload must not contain floats")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_floats(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_no_floats(child)


def test_repo_specialness_squeeze_digest_reduces_signals_with_utc_decimal_sorting_and_reasons() -> None:
    summary = report(
        (
            repo_signal(
                "condition.watch",
                repo_market_key="ust.repo.watch",
                collateral_bucket="otr-2y",
                public_signal_reference="repo-watch-public",
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            repo_signal(
                "condition.ready",
                repo_market_key="ust.repo.ready",
                collateral_bucket="otr-5y",
                public_signal_reference="repo-ready-public",
                general_collateral_rate_pct=d("5.250000"),
                specific_collateral_rate_pct=d("4.900000"),
                fails_to_deliver_ratio=d("0.380000"),
                dealer_shortage_ratio=d("0.700000"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.840000"),
                base_confidence=d("0.880000"),
            ),
            repo_signal(
                "condition.blocked",
                repo_market_key="ust.repo.blocked",
                collateral_bucket="otr-30y",
                public_signal_reference="credential-repo-reference",
                observed_at=GENERATED_AT - timedelta(hours=3),
                signal_age_seconds=d("10800.000000"),
                general_collateral_rate_pct=d("5.320000"),
                specific_collateral_rate_pct=d("5.180000"),
                fails_to_deliver_ratio=d("0.120000"),
                dealer_shortage_ratio=d("0.420000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.350000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    module = api()
    assert isinstance(
        summary,
        module.MarketResearchRatesRepoSpecialnessSqueezeDigestReport,
    )
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        "market-research-rates-repo-specialness-squeeze-digest-v0"
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_repo_specialness_squeeze_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.weak_specialness_signal_count == d("1.000000")
    assert summary.fails_pressure_gap_signal_count == d("1.000000")
    assert summary.dealer_shortage_gap_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.800000")
    assert summary.average_final_confidence == d("0.580000")
    assert summary.max_specialness_bps == d("50.000000")
    assert summary.average_specialness_bps == d("33.000000")
    assert summary.average_fails_to_deliver_ratio == d("0.306667")
    assert summary.average_dealer_shortage_ratio == d("0.613333")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.repo_market_key for row in summary.rows) == (
        "ust.repo.blocked",
        "ust.repo.watch",
        "ust.repo.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=3)
    assert blocked.specialness_bps == d("14.000000")
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.confidence_decay_factor == d("0.700000")
    assert blocked.final_confidence == d("0.200000")
    assert blocked.redacted_public_signal_reference == "sha256:5dfb0ffaa06f"
    assert blocked.reason_codes == (
        "market_research_rates_repo_specialness_squeeze_digest_stale_signal",
        "market_research_rates_repo_specialness_squeeze_digest_weak_specialness",
        "market_research_rates_repo_specialness_squeeze_digest_fails_pressure_gap",
        "market_research_rates_repo_specialness_squeeze_digest_dealer_shortage_gap",
        "market_research_rates_repo_specialness_squeeze_digest_source_family_gap",
        "market_research_rates_repo_specialness_squeeze_digest_stale_source_ratio",
        "market_research_rates_repo_specialness_squeeze_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.specialness_bps == d("50.000000")
    assert watch.confidence_decay_factor == d("0.100000")
    assert watch.final_confidence == d("0.660000")
    assert watch.reason_codes == (
        "market_research_rates_repo_specialness_squeeze_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.specialness_bps == d("35.000000")
    assert ready.final_confidence == d("0.880000")
    assert ready.reason_codes == (
        "market_research_rates_repo_specialness_squeeze_digest_ready",
    )

    assert summary.reason_codes == (
        "market_research_rates_repo_specialness_squeeze_digest_confirmation_gap",
        "market_research_rates_repo_specialness_squeeze_digest_stale_signal",
        "market_research_rates_repo_specialness_squeeze_digest_weak_specialness",
        "market_research_rates_repo_specialness_squeeze_digest_fails_pressure_gap",
        "market_research_rates_repo_specialness_squeeze_digest_dealer_shortage_gap",
        "market_research_rates_repo_specialness_squeeze_digest_source_family_gap",
        "market_research_rates_repo_specialness_squeeze_digest_stale_source_ratio",
    )
    assert tuple(item.reason_code for item in summary.reason_code_counts) == (
        "market_research_rates_repo_specialness_squeeze_digest_confirmation_gap",
        "market_research_rates_repo_specialness_squeeze_digest_stale_signal",
        "market_research_rates_repo_specialness_squeeze_digest_weak_specialness",
        "market_research_rates_repo_specialness_squeeze_digest_fails_pressure_gap",
        "market_research_rates_repo_specialness_squeeze_digest_dealer_shortage_gap",
        "market_research_rates_repo_specialness_squeeze_digest_source_family_gap",
        "market_research_rates_repo_specialness_squeeze_digest_stale_source_ratio",
    )
    assert summary.reason_code_counts[0].count == d("2.000000")
    assert summary.reason_code_counts[0].signal_ratio == d("0.666667")
    assert all(row.paper_only and row.report_only and row.readonly for row in summary.rows)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_inputs_block_with_decimal_zeroes_and_no_rows() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_repo_specialness_squeeze_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.stale_signal_count == ZERO
    assert summary.weak_specialness_signal_count == ZERO
    assert summary.fails_pressure_gap_signal_count == ZERO
    assert summary.dealer_shortage_gap_signal_count == ZERO
    assert summary.source_family_gap_signal_count == ZERO
    assert summary.stale_source_signal_count == ZERO
    assert summary.confirmation_gap_signal_count == ZERO
    assert summary.total_confidence_decay == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.max_specialness_bps == ZERO
    assert summary.average_specialness_bps == ZERO
    assert summary.average_fails_to_deliver_ratio == ZERO
    assert summary.average_dealer_shortage_ratio == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == ()
    assert summary.reason_codes == (
        "market_research_rates_repo_specialness_squeeze_digest_no_inputs",
    )


def test_public_numerics_are_decimal_only_payload_uses_six_decimal_strings_and_dataclasses_are_frozen() -> None:
    module = api()
    summary = report((repo_signal(),))

    for value in (
        config(),
        repo_signal(),
        *summary.rows,
        *summary.reason_code_counts,
        summary,
    ):
        assert value.__dataclass_params__.frozen is True
        for field in fields(value):
            public_value = getattr(value, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_confidence")
                or field.name.endswith("_decay")
                or field.name.endswith("_factor")
                or field.name.endswith("_bps")
                or field.name.endswith("_pct")
            ):
                assert type(public_value) is Decimal, field.name

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].repo_market_key = "changed"  # type: ignore[misc]

    payload = module.market_research_rates_repo_specialness_squeeze_digest_payload(
        summary,
    )

    json.dumps(payload, sort_keys=True)
    assert_no_floats(payload)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == (
        GENERATED_AT - timedelta(minutes=15)
    ).isoformat()
    assert payload["rows"][0]["specialness_bps"] == "50.000000"
    assert payload["rows"][0]["general_collateral_rate_pct"] == "5.300000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_rejects_bad_types_inconsistent_inputs_duplicate_keys_and_false_hard_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "market-research-rates-repo-specialness-squeeze-digest-v0",
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 4, 14, 0))
    with pytest.raises(ValueError, match="signals"):
        report((object(),))
    with pytest.raises(ValueError, match="general_collateral_rate_pct"):
        repo_signal(general_collateral_rate_pct=_DecimalSubclass("5.300000"))
    with pytest.raises(ValueError, match="fails_to_deliver_ratio"):
        repo_signal(fails_to_deliver_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        repo_signal(observed_at=datetime(2026, 7, 4, 14, 0))
    with pytest.raises(ValueError, match="signal_age_seconds"):
        report(
            (
                repo_signal(
                    observed_at=GENERATED_AT - timedelta(minutes=15),
                    signal_age_seconds=d("600.000000"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="condition_id"):
        report(
            (
                repo_signal("condition.dupe"),
                repo_signal("condition.dupe"),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(repo_signal(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="rows"):
        replace(
            report((repo_signal(),)),
            rows=(
                replace(report((repo_signal(),)).rows[0], digest_status="watch"),
                report((repo_signal(),)).rows[0],
            ),
        )

    with pytest.raises(ValueError, match="redacted_public_signal_reference"):
        module.MarketResearchRatesRepoSpecialnessSqueezeDigestRow(
            condition_id="condition.secret",
            repo_market_key="ust.repo.secret",
            collateral_bucket="otr-10y",
            observed_at=GENERATED_AT,
            signal_age_seconds=ZERO,
            general_collateral_rate_pct=d("5.300000"),
            specific_collateral_rate_pct=d("4.800000"),
            specialness_bps=d("50.000000"),
            fails_to_deliver_ratio=d("0.420000"),
            dealer_shortage_ratio=d("0.720000"),
            source_family_count=d("3.000000"),
            stale_source_ratio=d("0.100000"),
            confirmation_ratio=d("0.800000"),
            base_confidence=d("0.850000"),
            confidence_decay_factor=ZERO,
            final_confidence=d("0.850000"),
            digest_status="ready",
            redacted_public_signal_reference="https://token-secret.example/repo",
            signal_config_version="repo-specialness-squeeze-v0",
            reason_codes=(
                "market_research_rates_repo_specialness_squeeze_digest_ready",
            ),
        )


def test_module_scope_is_pure_report_only_without_io_network_db_or_live_mutation_surface() -> None:
    source = inspect.getsource(api())
    tree = ast.parse(source)
    lowered_source = source.lower()

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
        "private_key",
        "api_key",
        "wallet",
        "place_order",
        "cancel_order",
        "replace_order",
        "submit_order",
        "auth",
    ):
        assert forbidden not in lowered_source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def test_public_exports_are_exact() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_RATES_REPO_SPECIALNESS_SQUEEZE_DIGEST_CONFIG_VERSION",
        "MarketResearchRatesRepoSpecialnessSqueezeDigestConfig",
        "MarketResearchRatesRepoSpecialnessSqueezeSignal",
        "MarketResearchRatesRepoSpecialnessSqueezeDigestRow",
        "MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount",
        "MarketResearchRatesRepoSpecialnessSqueezeDigestReport",
        "build_market_research_rates_repo_specialness_squeeze_digest",
        "market_research_rates_repo_specialness_squeeze_digest_payload",
    )
