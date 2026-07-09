from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_liquidity_fee_confidence_decay_report import (
    DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION,
    ResearchMarketLiquidityFeeConfidenceDecayConfig,
    ResearchMarketLiquidityFeeConfidenceDecayObservation,
    ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount,
    ResearchMarketLiquidityFeeConfidenceDecayReport,
    ResearchMarketLiquidityFeeConfidenceDecayRow,
    build_research_market_liquidity_fee_confidence_decay_report,
    research_market_liquidity_fee_confidence_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_liquidity_fee_confidence_decay_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchMarketLiquidityFeeConfidenceDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
        ),
        "spread_watch_bps": d("20.000000"),
        "spread_block_bps": d("50.000000"),
        "fee_watch_bps": d("8.000000"),
        "fee_block_bps": d("18.000000"),
        "total_cost_watch_bps": d("30.000000"),
        "total_cost_block_bps": d("60.000000"),
        "depth_pass_floor": d("0.650000"),
        "depth_watch_floor": d("0.350000"),
        "confidence_pass_floor": d("0.700000"),
        "confidence_watch_floor": d("0.400000"),
        "confidence_decay_window_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityFeeConfidenceDecayConfig(**values)


def observation(
    observation_id: str = "alpha-observation",
    *,
    spread_bps: Decimal = d("5.000000"),
    fee_bps: Decimal = d("2.000000"),
    depth_score: Decimal = d("0.800000"),
    confidence_score: Decimal = d("0.900000"),
    observed_at: datetime = GENERATED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketLiquidityFeeConfidenceDecayObservation:
    return ResearchMarketLiquidityFeeConfidenceDecayObservation(
        observation_id=observation_id,
        spread_bps=spread_bps,
        fee_bps=fee_bps,
        depth_score=depth_score,
        confidence_score=confidence_score,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketLiquidityFeeConfidenceDecayObservation,
    cfg: ResearchMarketLiquidityFeeConfidenceDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketLiquidityFeeConfidenceDecayReport:
    return build_research_market_liquidity_fee_confidence_decay_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    signed = dict(payload)
    payload_without_digest = dict(signed)
    payload_without_digest.pop("derived_validation_digest", None)
    signed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            payload_without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return signed


def test_report_rolls_up_pass_watch_block_and_payload_digest() -> None:
    digest = report(
        observation("pass-row"),
        observation(
            "watch-row",
            spread_bps=d("25.000000"),
            fee_bps=d("4.000000"),
            depth_score=d("0.600000"),
            confidence_score=d("0.800000"),
        ),
        observation(
            "block-row",
            spread_bps=d("55.000000"),
            fee_bps=d("20.000000"),
            depth_score=d("0.250000"),
            confidence_score=d("0.700000"),
            observed_at=GENERATED_AT - timedelta(days=2),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
    )
    assert digest.status == "block"
    assert digest.observation_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.max_total_cost_bps == d("75.000000")
    assert digest.mean_total_cost_bps == d("37.000000")
    assert digest.min_adjusted_confidence_score == d("0.233333")
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.status for row in digest.rows) == ("block", "watch", "pass")
    assert digest.rows[0].observation_digest == hashlib.sha256(
        b"block-row",
    ).hexdigest()
    assert digest.rows[0].reason_codes == (
        "confidence_decay_block",
        "depth_score_block",
        "fee_cost_block",
        "spread_cost_block",
        "total_cost_block",
    )
    assert digest.rows[1].reason_codes == (
        "depth_score_watch",
        "spread_cost_watch",
    )
    assert digest.rows[2].reason_codes == (
        "liquidity_fee_confidence_decay_clear",
    )
    assert digest.reason_codes == (
        "research_market_liquidity_fee_confidence_decay_block",
        "confidence_decay_block",
        "depth_score_block",
        "depth_score_watch",
        "fee_cost_block",
        "spread_cost_block",
        "spread_cost_watch",
        "total_cost_block",
    )

    payload = research_market_liquidity_fee_confidence_decay_report_payload(digest)
    assert payload["observation_count"] == "3.000000"
    assert payload["rows"][0]["adjusted_confidence_score"] == "0.233333"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)

    payload_without_digest = dict(payload)
    derived_validation_digest = payload_without_digest.pop("derived_validation_digest")
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert derived_validation_digest == hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    json.dumps(payload, sort_keys=True)


def test_empty_observations_block_with_no_inputs_reason_count() -> None:
    digest = report()

    assert digest.status == "block"
    assert digest.observation_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.mean_total_cost_bps == ZERO
    assert digest.max_total_cost_bps == ZERO
    assert digest.mean_adjusted_confidence_score == ZERO
    assert digest.min_adjusted_confidence_score == ZERO
    assert digest.reason_codes == (
        "research_market_liquidity_fee_confidence_decay_no_inputs",
    )
    assert digest.reason_code_counts == (
        ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount(
            reason_code="research_market_liquidity_fee_confidence_decay_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest.rows == ()


def test_time_normalization_and_future_observations_are_rejected() -> None:
    digest = report(
        observation(
            observed_at=datetime(
                2026,
                7,
                9,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            9,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.rows[0].observed_at == datetime(2026, 7, 9, 11, 0, tzinfo=UTC)
    assert digest.rows[0].age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            observed_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_frozen_flags_decimal_only_and_exact_status_vocabulary() -> None:
    digest = report(observation("frozen-row"))

    assert is_dataclass(ResearchMarketLiquidityFeeConfidenceDecayConfig)
    assert is_dataclass(ResearchMarketLiquidityFeeConfidenceDecayObservation)
    assert is_dataclass(ResearchMarketLiquidityFeeConfidenceDecayRow)
    assert is_dataclass(ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount)
    assert is_dataclass(ResearchMarketLiquidityFeeConfidenceDecayReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].total_cost_bps = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(digest, report_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(digest.rows[0], status="blocked")

    public_values = (digest, *digest.rows, *digest.reason_code_counts)
    for item in public_values:
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name

    for field_name in (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_total_cost_bps",
        "max_total_cost_bps",
        "mean_adjusted_confidence_score",
        "min_adjusted_confidence_score",
    ):
        assert type(getattr(digest, field_name)) is Decimal
    assert {row.status for row in digest.rows} <= {"pass", "watch", "block"}


def test_validation_rejects_bad_decimals_subclasses_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="spread_watch_bps"):
        config(spread_watch_bps=d("-0.000001"))
    with pytest.raises(ValueError, match="spread_watch_bps"):
        config(spread_watch_bps=d("60.000000"), spread_block_bps=d("50.000000"))
    with pytest.raises(ValueError, match="confidence_decay_window_seconds"):
        config(confidence_decay_window_seconds=ZERO)
    with pytest.raises(ValueError, match="observation_id"):
        observation(observation_id=" token ")
    with pytest.raises(ValueError, match="spread_bps"):
        observation(spread_bps=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_bps"):
        observation(fee_bps=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="depth_score"):
        observation(depth_score=d("1.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )

    digest = report(observation("tamper-row"))
    with pytest.raises(ValueError, match="observation_count"):
        replace(digest, observation_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="watch")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(digest, reason_code_counts=())

    object.__setattr__(digest.rows[0], "total_cost_bps", d("7.0000000"))
    with pytest.raises(ValueError, match="six decimal"):
        research_market_liquidity_fee_confidence_decay_report_payload(digest)

    digest = report(observation("payload-tamper"))
    payload = research_market_liquidity_fee_confidence_decay_report_payload(digest)
    payload["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_liquidity_fee_confidence_decay_report_payload(payload)


def test_public_payload_rejects_schema_drift_even_with_matching_digest() -> None:
    digest = report(observation("schema-drift-row"))
    payload = research_market_liquidity_fee_confidence_decay_report_payload(digest)

    extra_top_level_field = resign_payload(
        {
            **payload,
            "extra_public_metric": "1.000000",
        },
    )
    with pytest.raises(ValueError, match="schema"):
        research_market_liquidity_fee_confidence_decay_report_payload(
            extra_top_level_field,
        )

    invalid_status = resign_payload({**payload, "status": "hold"})
    with pytest.raises(ValueError, match="status"):
        research_market_liquidity_fee_confidence_decay_report_payload(invalid_status)

    noncanonical_decimal = resign_payload({**payload, "observation_count": "1.0"})
    with pytest.raises(ValueError, match="observation_count"):
        research_market_liquidity_fee_confidence_decay_report_payload(
            noncanonical_decimal,
        )


def test_public_payload_dict_requires_exact_json_types_before_normalization() -> None:
    payload = research_market_liquidity_fee_confidence_decay_report_payload(
        report(observation("exact-json-row")),
    )

    subclass_key_payload = dict(payload)
    readonly = subclass_key_payload.pop("readonly")
    subclass_key_payload[_StringSubclass("readonly")] = readonly
    with pytest.raises(ValueError, match="keys must be strings"):
        research_market_liquidity_fee_confidence_decay_report_payload(
            subclass_key_payload,
        )

    decimal_payload = dict(payload)
    decimal_payload["observation_count"] = d("1.000000")
    with pytest.raises(ValueError, match="Decimal-derived string"):
        research_market_liquidity_fee_confidence_decay_report_payload(
            decimal_payload,
        )


def test_public_payload_rejects_resigned_adjusted_confidence_drift() -> None:
    payload = research_market_liquidity_fee_confidence_decay_report_payload(
        report(observation("adjusted-confidence-drift-row")),
    )
    row = dict(payload["rows"][0])
    row["adjusted_confidence_score"] = "0.800000"
    tampered = resign_payload(
        {
            **payload,
            "mean_adjusted_confidence_score": "0.800000",
            "min_adjusted_confidence_score": "0.800000",
            "rows": [row],
        },
    )

    with pytest.raises(ValueError, match="adjusted_confidence_score"):
        research_market_liquidity_fee_confidence_decay_report_payload(tampered)


def test_public_payload_rejects_resigned_age_drift() -> None:
    payload = research_market_liquidity_fee_confidence_decay_report_payload(
        report(observation("age-drift-row")),
    )
    row = dict(payload["rows"][0])
    row["age_seconds"] = "1.000000"
    tampered = resign_payload({**payload, "rows": [row]})

    with pytest.raises(ValueError, match="age_seconds"):
        research_market_liquidity_fee_confidence_decay_report_payload(tampered)


def test_public_payload_rejects_resigned_freeform_reason_code() -> None:
    payload = research_market_liquidity_fee_confidence_decay_report_payload(
        report(observation("freeform-reason-row")),
    )
    row = dict(payload["rows"][0])
    row["reason_codes"] = ["freeform_note"]
    tampered = resign_payload(
        {
            **payload,
            "rows": [row],
            "reason_code_counts": [
                {
                    "reason_code": "freeform_note",
                    "count": "1.000000",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ],
        },
    )

    with pytest.raises(ValueError, match="reason_codes"):
        research_market_liquidity_fee_confidence_decay_report_payload(tampered)


def test_public_payload_does_not_expose_raw_identifiers_or_unsafe_fields() -> None:
    private_identifier = "private-alpha-observation"
    digest = report(observation(private_identifier))
    payload = research_market_liquidity_fee_confidence_decay_report_payload(digest)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert private_identifier not in encoded
    assert "observation_id" not in encoded
    assert "candidate" not in encoded
    assert "source" not in encoded
    assert "url" not in encoded
    assert "text" not in encoded
    assert "dsn" not in encoded
    assert "table" not in encoded
    assert "token" not in encoded


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.research_market_liquidity_fee_confidence_decay_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION",
        "ResearchMarketLiquidityFeeConfidenceDecayConfig",
        "ResearchMarketLiquidityFeeConfidenceDecayObservation",
        "ResearchMarketLiquidityFeeConfidenceDecayReasonCodeCount",
        "ResearchMarketLiquidityFeeConfidenceDecayReport",
        "ResearchMarketLiquidityFeeConfidenceDecayRow",
        "build_research_market_liquidity_fee_confidence_decay_report",
        "research_market_liquidity_fee_confidence_decay_report_payload",
    )


def test_static_forbidden_surfaces_and_external_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "db",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "candidate",
        "url",
        "dsn",
        "table",
        "token",
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
        "total_seconds",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
