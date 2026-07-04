from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest

from polymarket_alpha_lab.market_research_crypto_stablecoin_attestation_gap_digest import (
    DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION,
    StablecoinAttestationGapDigest,
    StablecoinAttestationGapDigestConfig,
    StablecoinAttestationGapReasonCodeCount,
    StablecoinAttestationGapRow,
    StablecoinReserveAttestationObservation,
    build_market_research_crypto_stablecoin_attestation_gap_digest,
    market_research_crypto_stablecoin_attestation_gap_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_crypto_stablecoin_attestation_gap_digest.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StablecoinAttestationGapDigestConfig:
    values = {
        "config_version": (
            DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION
        ),
        "watch_gap_ratio": d("0.010000"),
        "high_gap_ratio": d("0.050000"),
        "max_attestation_age_days": d("30.000000"),
        "max_source_age_seconds": d("900.000000"),
        "large_gap_usd": d("10000000.000000"),
        "high_confidence_threshold": d("0.800000"),
        "stale_confidence_cap": d("0.400000"),
    }
    values.update(overrides)
    return StablecoinAttestationGapDigestConfig(**values)


def observation(
    source_id: str,
    *,
    issuer_id: str = "issuer-a",
    asset_symbol: str = "USDA",
    event_slug: str = "will-usda-trade-below-99c-in-2026",
    outstanding_supply_usd: str = "500000000.000000",
    attested_reserves_usd: str = "492000000.000000",
    attestation_as_of: datetime = GENERATED_AT - timedelta(days=7),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    screening_confidence: str = "0.750000",
    upstream_reason_codes: tuple[str, ...] = ("stablecoin_attestation_reported",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StablecoinReserveAttestationObservation:
    return StablecoinReserveAttestationObservation(
        source_id=source_id,
        issuer_id=issuer_id,
        asset_symbol=asset_symbol,
        event_slug=event_slug,
        outstanding_supply_usd=d(outstanding_supply_usd),
        attested_reserves_usd=d(attested_reserves_usd),
        attestation_as_of=attestation_as_of,
        source_observed_at=source_observed_at,
        screening_confidence=d(screening_confidence),
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    *rows: StablecoinReserveAttestationObservation,
    cfg: StablecoinAttestationGapDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StablecoinAttestationGapDigest:
    return build_market_research_crypto_stablecoin_attestation_gap_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_digest_is_report_only_readonly_and_decimal_payload() -> None:
    report = digest()
    payload = market_research_crypto_stablecoin_attestation_gap_digest_payload(report)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.digest_status == "empty"
    assert report.reason_codes == ("stablecoin_attestation_gap_digest_empty",)
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.high_risk_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.low_risk_count == d("0.000000")
    assert report.total_reserve_gap_usd == d("0.000000")
    assert report.max_reserve_gap_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_or_int_paths(payload) == ()


def test_high_risk_attestation_gap_digest_sorts_caps_and_explains_rows() -> None:
    report = digest(
        observation(
            "source-zeta",
            issuer_id="issuer-z",
            asset_symbol="USDZ",
            event_slug="will-usdz-trade-below-98c-in-2026",
            outstanding_supply_usd="1000000000.000000",
            attested_reserves_usd="930000000.000000",
            attestation_as_of=GENERATED_AT - timedelta(days=45),
            source_observed_at=datetime(
                2026,
                7,
                4,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            screening_confidence="0.920000",
            upstream_reason_codes=(
                "stablecoin_supply_jump",
                "stablecoin_attestation_method_change",
            ),
        ),
        observation(
            "source-alpha",
            issuer_id="issuer-a",
            asset_symbol="USDA",
            outstanding_supply_usd="500000000.000000",
            attested_reserves_usd="492000000.000000",
            screening_confidence="0.750000",
        ),
        observation(
            "source-beta",
            issuer_id="issuer-b",
            asset_symbol="USDB",
            event_slug="will-usdb-trade-below-99c-in-2026",
            outstanding_supply_usd="300000000.000000",
            attested_reserves_usd="306000000.000000",
            screening_confidence="0.610000",
        ),
    )

    assert type(report) is StablecoinAttestationGapDigest
    assert report.generated_at == GENERATED_AT
    assert report.digest_status == "high_risk"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.high_risk_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.low_risk_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.stale_attestation_count == d("1.000000")
    assert report.total_reserve_gap_usd == d("78000000.000000")
    assert report.max_reserve_gap_usd == d("70000000.000000")
    assert report.max_reserve_gap_ratio == d("0.070000")
    assert tuple(row.source_id for row in report.rows) == (
        "source-zeta",
        "source-alpha",
        "source-beta",
    )

    high = report.rows[0]
    assert type(high) is StablecoinAttestationGapRow
    assert high.attestation_as_of == datetime(2026, 5, 20, 12, 0, tzinfo=UTC)
    assert high.source_observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert high.source_age_seconds == d("3600.000000")
    assert high.attestation_age_days == d("45.000000")
    assert high.reserve_gap_usd == d("70000000.000000")
    assert high.reserve_gap_ratio == d("0.070000")
    assert high.reserve_coverage_ratio == d("0.930000")
    assert high.confidence_cap == d("0.400000")
    assert high.capped_screening_confidence == d("0.400000")
    assert high.gap_status == "gap_risk_high"
    assert high.reason_codes == (
        "stablecoin_attestation_gap_high",
        "stablecoin_attestation_source_stale",
        "stablecoin_attestation_window_stale",
        "stablecoin_attestation_large_notional_gap",
        "stablecoin_attestation_high_confidence",
        "stablecoin_attestation_method_change",
        "stablecoin_supply_jump",
    )

    watch = report.rows[1]
    assert watch.gap_status == "gap_risk_watch"
    assert watch.reserve_gap_usd == d("8000000.000000")
    assert watch.reserve_gap_ratio == d("0.016000")
    assert watch.reason_codes == (
        "stablecoin_attestation_gap_watch",
        "stablecoin_attestation_source_fresh",
        "stablecoin_attestation_window_fresh",
    )

    low = report.rows[2]
    assert low.gap_status == "gap_risk_low"
    assert low.reserve_gap_usd == d("0.000000")
    assert low.reserve_gap_ratio == d("0.000000")
    assert low.reserve_coverage_ratio == d("1.020000")

    assert report.reason_codes == (
        "stablecoin_attestation_gap_high_present",
        "stablecoin_attestation_gap_watch_present",
        "stablecoin_attestation_source_stale_present",
        "stablecoin_attestation_window_stale_present",
        "stablecoin_attestation_large_notional_gap_present",
        "stablecoin_attestation_method_change_present",
        "stablecoin_supply_jump_present",
    )
    assert report.reason_code_counts == (
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_attestation_gap_high_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_attestation_gap_watch_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_attestation_source_stale_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_attestation_window_stale_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_attestation_large_notional_gap_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_attestation_method_change_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        StablecoinAttestationGapReasonCodeCount(
            reason_code="stablecoin_supply_jump_present",
            row_count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )


def test_digest_is_deterministic_for_input_permutation_and_reason_code_order() -> None:
    rows = (
        observation(
            "source-watch",
            outstanding_supply_usd="100000000.000000",
            attested_reserves_usd="98000000.000000",
            upstream_reason_codes=(
                "stablecoin_supply_jump",
                "stablecoin_attestation_reported",
                "stablecoin_supply_jump",
            ),
        ),
        observation(
            "source-high",
            issuer_id="issuer-h",
            asset_symbol="USDH",
            outstanding_supply_usd="100000000.000000",
            attested_reserves_usd="94000000.000000",
            screening_confidence="0.850000",
        ),
        observation(
            "source-low",
            issuer_id="issuer-l",
            asset_symbol="USDL",
            outstanding_supply_usd="100000000.000000",
            attested_reserves_usd="100000000.000000",
        ),
    )

    first = digest(*rows)
    second = digest(*tuple(reversed(rows)))

    assert first.rows == second.rows
    assert first.reason_codes == second.reason_codes
    assert first.rows[1].reason_codes == (
        "stablecoin_attestation_gap_watch",
        "stablecoin_attestation_source_fresh",
        "stablecoin_attestation_window_fresh",
        "stablecoin_supply_jump",
    )
    assert json.dumps(
        market_research_crypto_stablecoin_attestation_gap_digest_payload(first),
        sort_keys=True,
    ) == json.dumps(
        market_research_crypto_stablecoin_attestation_gap_digest_payload(second),
        sort_keys=True,
    )


def test_validates_inputs_datetimes_decimals_duplicates_and_hard_flags() -> None:
    with pytest.raises(ValueError, match="outstanding_supply_usd must be a Decimal"):
        StablecoinReserveAttestationObservation(
            source_id="bad-decimal",
            issuer_id="issuer-a",
            asset_symbol="USDA",
            event_slug="will-usda-trade-below-99c-in-2026",
            outstanding_supply_usd=100,  # type: ignore[arg-type]
            attested_reserves_usd=d("99.000000"),
            attestation_as_of=GENERATED_AT,
            source_observed_at=GENERATED_AT,
            screening_confidence=d("0.700000"),
            upstream_reason_codes=("stablecoin_attestation_reported",),
        )

    with pytest.raises(ValueError, match="attested_reserves_usd must be a Decimal"):
        observation("decimal-subclass", attested_reserves_usd="99.000000").__class__(
            source_id="decimal-subclass",
            issuer_id="issuer-a",
            asset_symbol="USDA",
            event_slug="will-usda-trade-below-99c-in-2026",
            outstanding_supply_usd=d("100.000000"),
            attested_reserves_usd=_DecimalSubclass("99.000000"),
            attestation_as_of=GENERATED_AT,
            source_observed_at=GENERATED_AT,
            screening_confidence=d("0.700000"),
            upstream_reason_codes=("stablecoin_attestation_reported",),
        )

    with pytest.raises(ValueError, match="source_observed_at must be UTC-aware"):
        observation("naive-time", source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="attestation_as_of must be a datetime"):
        observation(
            "datetime-subclass",
            attestation_as_of=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        digest(observation("future-source", source_observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="attestation_as_of must not be after generated_at"):
        digest(
            observation(
                "future-attestation",
                attestation_as_of=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest(observation("dupe"), observation("dupe", issuer_id="issuer-b"))

    with pytest.raises(ValueError, match="upstream_reason_codes must be supported"):
        observation("bad-reason", upstream_reason_codes=("not_supported",))

    with pytest.raises(ValueError, match="config must be a StablecoinAttestationGapDigestConfig"):
        build_market_research_crypto_stablecoin_attestation_gap_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_market_research_crypto_stablecoin_attestation_gap_digest(
            (),
            config=config(),
            generated_at="2026-07-04T12:00:00Z",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="watch_gap_ratio must not exceed high_gap_ratio"):
        config(watch_gap_ratio=d("0.060000"), high_gap_ratio=d("0.050000"))

    with pytest.raises(ValueError, match="paper_only"):
        observation("bad-flag", paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    report = digest(observation("frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]


def test_non_default_thresholds_change_screening_band_without_mutating_inputs() -> None:
    row = observation(
        "source-threshold",
        outstanding_supply_usd="200000000.000000",
        attested_reserves_usd="196000000.000000",
    )

    default_report = digest(row)
    strict_report = digest(
        row,
        cfg=config(watch_gap_ratio=d("0.005000"), high_gap_ratio=d("0.015000")),
    )

    assert default_report.digest_status == "watch"
    assert default_report.rows[0].gap_status == "gap_risk_watch"
    assert strict_report.digest_status == "high_risk"
    assert strict_report.rows[0].gap_status == "gap_risk_high"
    assert row.attested_reserves_usd == d("196000000.000000")


def test_static_surface_stays_pure_report_only_and_decimal_public_api() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "submit_order",
        "place_order",
        "cancel_order",
        "replace_order",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "cursor(",
        "execute(",
        "open(",
        "pathlib",
        "write_text",
        "write_bytes",
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
        "sqlalchemy",
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
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports

    for value in _walk_dataclasses(digest(observation("shape"))):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float_or_int(hint)
        for field in fields(value):
            if _is_public_numeric(field.name):
                field_value = getattr(value, field.name)
                assert type(field_value) is Decimal


def _walk_dataclasses(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if is_dataclass(value) and not isinstance(value, type):
        found.append(value)
        for field in fields(value):
            found.extend(_walk_dataclasses(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            found.extend(_walk_dataclasses(item))
    return tuple(found)


def _is_public_numeric(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_usd")
        or field_name.endswith("_seconds")
        or field_name.endswith("_days")
        or field_name.endswith("_confidence")
        or field_name in {"confidence_cap"}
    )


def _type_uses_float_or_int(hint: Any) -> bool:
    if hint in {float, int}:
        return True
    return any(_type_uses_float_or_int(arg) for arg in get_args(hint))


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, bool):
        return ()
    if isinstance(value, (float, int)):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
