from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def m() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_core_ppi_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = m()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_CORE_PPI_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.050000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchCorePpiSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_core_ppi",
    *,
    research_key: str = "research.core_ppi.monthly",
    release_key: str = "core_ppi.monthly.latest",
    ppi_measure: str = "core_ppi_monthly",
    public_signal_reference: str = "public-core-ppi-release",
    observed_at: datetime | None = None,
    expected_core_ppi_change: Decimal = d("0.200000"),
    actual_core_ppi_change: Decimal = d("0.350000"),
    surprise_score: Decimal = d("0.060000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.850000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "core-ppi-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = m()
    return module.MarketResearchCorePpiSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        ppi_measure=ppi_measure,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        expected_core_ppi_change=expected_core_ppi_change,
        actual_core_ppi_change=actual_core_ppi_change,
        surprise_score=surprise_score,
        source_count=source_count,
        revision_ratio=revision_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...] = (),
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = m()
    return module.build_market_research_core_ppi_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_fields_are_decimal(value: object) -> None:
    numeric_tokens = (
        "age",
        "average",
        "change",
        "confidence",
        "count",
        "delta",
        "max_",
        "min_",
        "ratio",
        "score",
        "surprise",
        "threshold",
    )
    non_numeric_fields = {"config_version"}
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, tuple):
                assert_public_numeric_fields_are_decimal(item)
                continue
            if field.name not in non_numeric_fields and any(
                token in field.name for token in numeric_tokens
            ):
                assert type(item) is Decimal, field.name
                assert item.as_tuple().exponent == -6, field.name
            assert_public_numeric_fields_are_decimal(item)
    elif isinstance(value, tuple):
        for item in value:
            assert_public_numeric_fields_are_decimal(item)


def assert_serialized_numerics_are_six_decimal_strings(value: object) -> None:
    numeric_tokens = (
        "age",
        "average",
        "change",
        "confidence",
        "count",
        "delta",
        "max_",
        "min_",
        "ratio",
        "score",
        "surprise",
        "threshold",
    )
    non_numeric_fields = {"config_version"}
    if isinstance(value, dict):
        for key, item in value.items():
            if (
                key not in non_numeric_fields
                and not isinstance(item, dict | list)
                and any(token in key for token in numeric_tokens)
            ):
                assert type(item) is str, key
                Decimal(item)
                assert len(item.rsplit(".", maxsplit=1)[-1]) == 6, key
            assert_serialized_numerics_are_six_decimal_strings(item)
    elif isinstance(value, list):
        for item in value:
            assert_serialized_numerics_are_six_decimal_strings(item)


def test_core_ppi_surprise_digest_reduces_report_only_rows_deterministically() -> None:
    leaked_reference = "https://source.example/core-ppi?token=secret-123"
    summary = report(
        (
            signal(
                "condition_ready",
                research_key="research.core_ppi.ready",
                release_key="core_ppi.ready",
                ppi_measure="core_ppi_ex_food_energy_ready",
                observed_at=GENERATED_AT - timedelta(minutes=25),
                expected_core_ppi_change=d("0.300000"),
                actual_core_ppi_change=d("0.250000"),
                surprise_score=d("0.010000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.920000"),
            ),
            signal(
                "condition_blocked",
                research_key="research.core_ppi.blocked",
                release_key="core_ppi.blocked",
                ppi_measure="core_ppi_ex_food_energy_blocked",
                public_signal_reference=leaked_reference,
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_core_ppi_change=d("0.200000"),
                actual_core_ppi_change=d("0.500000"),
                surprise_score=d("0.090000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.350000"),
                confirmation_ratio=d("0.420000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_watch",
                research_key="research.core_ppi.watch",
                release_key="core_ppi.watch",
                ppi_measure="core_ppi_ex_food_energy_watch",
                observed_at=GENERATED_AT - timedelta(hours=1),
                expected_core_ppi_change=d("0.200000"),
                actual_core_ppi_change=d("0.450000"),
                surprise_score=d("0.070000"),
                source_count=d("2.000000"),
                revision_ratio=d("0.120000"),
                confirmation_ratio=d("0.600000"),
                base_confidence=d("0.850000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    module = m()
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_CORE_PPI_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_core_ppi_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("2.000000")
    assert summary.average_surprise_score == d("0.056667")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.condition_id for row in summary.rows) == (
        "condition_blocked",
        "condition_watch",
        "condition_ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.surprise_delta == d("0.300000")
    assert blocked.surprise_ratio == d("1.500000")
    assert blocked.confidence_decay_factor == d("0.400000")
    assert blocked.final_confidence == d("0.352000")
    assert blocked.redacted_public_signal_reference == (
        f"sha256:{sha256(leaked_reference.encode('utf-8')).hexdigest()[:12]}"
    )
    assert blocked.reason_codes == (
        "market_research_core_ppi_surprise_digest_stale_signal",
        "market_research_core_ppi_surprise_digest_material_surprise",
        "market_research_core_ppi_surprise_digest_thin_sources",
        "market_research_core_ppi_surprise_digest_high_revision",
        "market_research_core_ppi_surprise_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.signal_age_seconds == d("3600.000000")
    assert watch.surprise_delta == d("0.250000")
    assert watch.surprise_ratio == d("1.250000")
    assert watch.confidence_decay_factor == d("0.800000")
    assert watch.final_confidence == d("0.680000")
    assert watch.reason_codes == (
        "market_research_core_ppi_surprise_digest_material_surprise",
        "market_research_core_ppi_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.signal_age_seconds == d("1500.000000")
    assert ready.surprise_delta == d("-0.050000")
    assert ready.surprise_ratio == d("-0.166667")
    assert ready.confidence_decay_factor == d("1.000000")
    assert ready.final_confidence == d("0.920000")
    assert ready.reason_codes == (
        "market_research_core_ppi_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "source.example",
        "https://",
        "token=",
        "wallet",
        "private",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert token not in public


def test_empty_core_ppi_digest_blocks_with_missing_evidence_count_one() -> None:
    summary = report(())
    module = m()

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_core_ppi_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.rows == ()
    assert summary.average_surprise_score == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.reason_code_counts == (
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_core_ppi_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_core_ppi_dataclasses_are_frozen_exact_decimal_and_utc_only() -> None:
    cfg = config()
    source = signal(
        observed_at=datetime(2026, 7, 3, 9, 30, tzinfo=timezone(timedelta(hours=-4))),
    )
    summary = report((source,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = d("0.500000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    assert source.observed_at == GENERATED_AT - timedelta(minutes=30)
    assert source.observed_at.tzinfo is UTC
    assert summary.rows[0].observed_at.tzinfo is UTC
    assert summary.generated_at.tzinfo is UTC
    assert_public_numeric_fields_are_decimal(cfg)
    assert_public_numeric_fields_are_decimal(source)
    assert_public_numeric_fields_are_decimal(summary)

    fractional = report(
        (
            signal(
                observed_at=GENERATED_AT - timedelta(seconds=1, microseconds=250000),
            ),
        ),
    )
    assert fractional.rows[0].signal_age_seconds == d("1.250000")


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (lambda: config(paper_only=False), "paper_only"),
        (lambda: config(report_only=False), "report_only"),
        (lambda: config(readonly=False), "readonly"),
        (lambda: signal(paper_only=False), "paper_only"),
        (lambda: signal(report_only=False), "report_only"),
        (lambda: signal(readonly=False), "readonly"),
        (lambda: config(min_source_count=2), "Decimal"),
        (lambda: signal(source_count=d("-1.000000")), "source_count"),
        (lambda: signal(source_count=d("1.500000")), "source_count"),
        (lambda: signal(surprise_score=d("1.500000")), "surprise_score"),
        (lambda: signal(public_signal_reference="wallet source"), "public_signal_reference"),
        (lambda: signal(condition_id="condition-order-flow"), "condition_id"),
        (lambda: signal(research_key="research.trade.intent"), "research_key"),
        (lambda: signal(release_key="release.submit.intent"), "release_key"),
        (lambda: signal(ppi_measure="private_ppi_measure"), "ppi_measure"),
        (lambda: signal(signal_config_version=_StringSubclass("config-v0")), "signal_config_version"),
        (lambda: signal(signal_config_version="core-ppi-secret-config"), "signal_config_version"),
        (lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC)), "observed_at"),
        (lambda: signal(observed_at=datetime(2026, 7, 3, 10, 30)), "observed_at"),
        (
            lambda: signal(
                observed_at=datetime(
                    2026,
                    7,
                    3,
                    10,
                    30,
                    tzinfo=_NoneOffsetTimezone(),
                ),
            ),
            "observed_at",
        ),
        (
            lambda: report(
                (signal(observed_at=GENERATED_AT + timedelta(microseconds=1)),),
            ),
            "observed_at",
        ),
        (lambda: signal(expected_core_ppi_change=_DecimalSubclass("0.200000")), "Decimal"),
        (lambda: signal(actual_core_ppi_change=1), "Decimal"),
        (lambda: signal(base_confidence=0.7), "Decimal"),
        (lambda: report((object(),)), "signals"),
        (lambda: report((signal(),), cfg=object()), "config"),
    ),
)
def test_core_ppi_digest_validates_inputs_and_explicit_false_flags(
    factory: object,
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_core_ppi_digest_rejects_subclasses_and_noncanonical_public_records() -> None:
    module = m()

    with pytest.raises(TypeError, match="subclassing"):
        class ConfigSubclass(module.MarketResearchCorePpiSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class SignalSubclass(module.MarketResearchCorePpiSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class RowSubclass(module.MarketResearchCorePpiSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReasonCountSubclass(
            module.MarketResearchCorePpiSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReportSubclass(module.MarketResearchCorePpiSurpriseDigestReport):
            pass

    summary = report(
        (
            signal("condition.blocked", observed_at=GENERATED_AT - timedelta(hours=3)),
            signal("condition.watch", confirmation_ratio=d("0.500000")),
            signal("condition.ready", surprise_score=d("0.010000")),
        ),
    )
    row = summary.rows[1]

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(
            row,
            reason_codes=(
                "market_research_core_ppi_surprise_digest_confirmation_gap",
                "market_research_core_ppi_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(
            row,
            reason_codes=(
                "market_research_core_ppi_surprise_digest_material_surprise",
                "market_research_core_ppi_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must use deterministic ordering"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))
    with pytest.raises(ValueError, match="count"):
        module.MarketResearchCorePpiSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_ppi_surprise_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )
    with pytest.raises(ValueError, match="config_version"):
        replace(
            summary,
            config_version="market-research-core-ppi-surprise-digest-v1",
        )
    with pytest.raises(ValueError, match="surprise_delta"):
        replace(summary.rows[0], surprise_delta=d("99.000000"))
    with pytest.raises(ValueError, match="final_confidence"):
        replace(summary.rows[0], final_confidence=d("0.123456"))


def test_core_ppi_payload_serializes_six_decimal_strings_and_rejects_unsafe_values() -> None:
    module = m()
    summary = report((signal("condition_b"), signal("condition_a")))

    payload = module.market_research_core_ppi_surprise_digest_payload(summary)

    assert payload == module.market_research_core_ppi_surprise_digest_payload(summary)
    assert payload["generated_at"] == "2026-07-03T14:00:00+00:00"
    assert payload["signal_count"] == "2.000000"
    assert [row["condition_id"] for row in payload["rows"]] == [
        "condition_a",
        "condition_b",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert_serialized_numerics_are_six_decimal_strings(payload)

    assert module.market_research_core_ppi_surprise_digest_payload(
        {"signal_count": d("1")},
    ) == {"signal_count": "1.000000"}
    with pytest.raises(TypeError, match="Decimal"):
        module.market_research_core_ppi_surprise_digest_payload({"signal_count": 1})
    with pytest.raises(TypeError, match="Decimal"):
        module.market_research_core_ppi_surprise_digest_payload(
            {"rows": [{"surprise_score": 0.1}]},
        )
    with pytest.raises(TypeError, match="Decimal"):
        module.market_research_core_ppi_surprise_digest_payload(
            {"signal_count": _DecimalSubclass("1.000000")},
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_core_ppi_surprise_digest_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="public"):
        module.market_research_core_ppi_surprise_digest_payload(
            {"wallet_reference": "redacted-reference"},
        )
    with pytest.raises(ValueError, match="public"):
        module.market_research_core_ppi_surprise_digest_payload(
            {"redacted_public_signal_reference": "token=secret-123"},
        )
    with pytest.raises(ValueError, match="report"):
        module.market_research_core_ppi_surprise_digest_payload(object())


def test_core_ppi_digest_module_has_no_io_network_store_auth_or_trading_surface() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/market_research_core_ppi_surprise_digest.py",
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported_modules <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }

    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "socket",
        "urllib",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "mnemonic",
        "signature",
        "wallet",
        "live_trading",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "fast",
        "open(",
        ".write(",
        ".read(",
    ):
        assert forbidden not in lowered

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
