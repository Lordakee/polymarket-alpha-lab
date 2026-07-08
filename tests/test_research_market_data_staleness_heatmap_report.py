from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_data_staleness_heatmap_report import (
    DEFAULT_RESEARCH_MARKET_DATA_STALENESS_HEATMAP_CONFIG_VERSION,
    ResearchMarketDataStalenessHeatmapConfig,
    ResearchMarketDataStalenessHeatmapDigest,
    ResearchMarketDataStalenessHeatmapInput,
    ResearchMarketDataStalenessHeatmapReasonCodeCount,
    ResearchMarketDataStalenessHeatmapReport,
    ResearchMarketDataStalenessHeatmapRow,
    build_research_market_data_staleness_heatmap_report,
    research_market_data_staleness_heatmap_digest,
    research_market_data_staleness_heatmap_report_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_data_staleness_heatmap_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketDataStalenessHeatmapConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_DATA_STALENESS_HEATMAP_CONFIG_VERSION,
        "watch_age_seconds": d("3600.000000"),
        "block_age_seconds": d("7200.000000"),
        "minimum_source_family_count": d("2.000000"),
    }
    values.update(overrides)
    return ResearchMarketDataStalenessHeatmapConfig(**values)


def observation(
    event_category: str = "macro",
    source_family: str = "official",
    research_team: str = "rates",
    *,
    latest_observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    source_family_count: Decimal = d("2.000000"),
    reason_codes: tuple[str, ...] = ("freshness_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketDataStalenessHeatmapInput:
    return ResearchMarketDataStalenessHeatmapInput(
        event_category=event_category,
        source_family=source_family,
        research_team=research_team,
        latest_observed_at=latest_observed_at,
        source_family_count=source_family_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketDataStalenessHeatmapInput,
    cfg: ResearchMarketDataStalenessHeatmapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketDataStalenessHeatmapReport:
    return build_research_market_data_staleness_heatmap_report(
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


def test_pass_watch_and_block_heatmap_statuses_roll_up_publicly() -> None:
    digest = report(
        observation(
            "macro",
            "official",
            "rates",
            latest_observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        observation(
            "elections",
            "newswire",
            "policy",
            latest_observed_at=GENERATED_AT - timedelta(minutes=90),
        ),
        observation(
            "weather",
            "specialist",
            "climate",
            latest_observed_at=GENERATED_AT - timedelta(hours=3),
            source_family_count=d("1.000000"),
        ),
    )

    assert digest.status == "block"
    assert digest.cell_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.stale_watch_count == d("1.000000")
    assert digest.stale_block_count == d("1.000000")
    assert digest.source_family_gap_count == d("1.000000")
    assert digest.max_staleness_age_seconds == d("10800.000000")
    assert digest.reason_codes == (
        "market_data_staleness_heatmap_block",
        "source_family_gap_block",
        "staleness_block",
        "staleness_watch",
    )

    assert tuple(
        (row.event_category, row.source_family, row.research_team, row.status)
        for row in digest.heatmap_rows
    ) == (
        ("weather", "specialist", "climate", "block"),
        ("elections", "newswire", "policy", "watch"),
        ("macro", "official", "rates", "pass"),
    )
    assert digest.heatmap_rows[0].reason_codes == (
        "freshness_input_available",
        "source_family_gap_block",
        "staleness_block",
    )
    assert digest.heatmap_rows[1].reason_codes == (
        "freshness_input_available",
        "staleness_watch",
    )
    assert digest.heatmap_rows[2].reason_codes == (
        "freshness_clear",
        "freshness_input_available",
    )


def test_empty_inputs_block_without_private_surface() -> None:
    digest = report()

    assert digest.status == "block"
    assert digest.cell_count == ZERO
    assert digest.reason_codes == ("market_data_staleness_heatmap_no_inputs",)
    assert digest.reason_code_counts == (
        ResearchMarketDataStalenessHeatmapReasonCodeCount(
            reason_code="market_data_staleness_heatmap_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest.heatmap_rows == ()


def test_payload_is_deterministic_decimal_string_only_and_json_ready() -> None:
    digest_a = report(
        observation(
            "weather",
            "specialist",
            "climate",
            latest_observed_at=GENERATED_AT - timedelta(hours=3),
            source_family_count=d("1.000000"),
        ),
        observation(
            "macro",
            "official",
            "rates",
            latest_observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        observation(
            "elections",
            "newswire",
            "policy",
            latest_observed_at=GENERATED_AT - timedelta(minutes=90),
        ),
    )
    digest_b = report(
        observation(
            "elections",
            "newswire",
            "policy",
            latest_observed_at=GENERATED_AT - timedelta(minutes=90),
        ),
        observation(
            "macro",
            "official",
            "rates",
            latest_observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        observation(
            "weather",
            "specialist",
            "climate",
            latest_observed_at=GENERATED_AT - timedelta(hours=3),
            source_family_count=d("1.000000"),
        ),
    )

    payload_a = research_market_data_staleness_heatmap_report_payload(digest_a)
    payload_b = research_market_data_staleness_heatmap_report_payload(digest_b)

    assert payload_a == payload_b
    assert payload_a["cell_count"] == "3.000000"
    assert payload_a["generated_at"] == GENERATED_AT.isoformat()
    assert payload_a["heatmap_rows"][0]["staleness_age_seconds"] == "10800.000000"
    assert payload_a["paper_only"] is True
    assert payload_a["report_only"] is True
    assert payload_a["readonly"] is True
    assert_no_float(payload_a)
    json.dumps(payload_a, sort_keys=True)


def test_digest_summary_matches_report_and_payload() -> None:
    digest = report(
        observation(
            "macro",
            "official",
            "rates",
            latest_observed_at=GENERATED_AT - timedelta(minutes=90),
        ),
    )

    summary = research_market_data_staleness_heatmap_digest(digest)
    payload = research_market_data_staleness_heatmap_report_payload(digest)

    assert type(summary) is ResearchMarketDataStalenessHeatmapDigest
    assert summary.generated_at == digest.generated_at
    assert summary.config_version == digest.config_version
    assert summary.status == digest.status == payload["status"]
    assert summary.cell_count == digest.cell_count
    assert summary.pass_count == digest.pass_count
    assert summary.watch_count == digest.watch_count
    assert summary.block_count == digest.block_count
    assert summary.reason_codes == digest.reason_codes
    assert summary.reason_code_counts == digest.reason_code_counts
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_decimal_and_type_rejection_at_public_boundaries() -> None:
    with pytest.raises(ValueError, match="watch_age_seconds"):
        config(watch_age_seconds=d("-0.000001"))
    with pytest.raises(ValueError, match="watch_age_seconds"):
        config(
            watch_age_seconds=d("7200.000000"),
            block_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="block_age_seconds"):
        config(block_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="event_category"):
        observation(event_category=" macro")
    with pytest.raises(ValueError, match="source_family_count"):
        observation(source_family_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_count"):
        observation(source_family_count=d("-1.000000"))
    with pytest.raises(ValueError, match="latest_observed_at"):
        observation(latest_observed_at=datetime(2026, 7, 4, 11, 0))
    with pytest.raises(ValueError, match="latest_observed_at"):
        observation(
            latest_observed_at=datetime(
                2026,
                7,
                4,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation("aware-time"),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="latest_observed_at"):
        report(observation(latest_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("staleness_watch", "freshness_input_available"))


def test_public_leak_rejection_blocks_private_identifiers_and_targets() -> None:
    for field_name, value in (
        ("event_category", "raw_candidate_alpha"),
        ("event_category", "market_id_123"),
        ("event_category", "slug_alpha"),
        ("source_family", "https://example.invalid/source"),
        ("source_family", "dsn_primary"),
        ("source_family", "table_alpha"),
        ("research_team", "wallet_ops"),
        ("research_team", "order_flow"),
        ("research_team", "buy_signal"),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            observation(**{field_name: value})

    digest = report(observation("safe-category"))
    with pytest.raises(ValueError, match="unsafe"):
        research_market_data_staleness_heatmap_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "status": "pass",
                "source_url": "redacted",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        object.__setattr__(digest.heatmap_rows[0], "source_family", "source_text")
        research_market_data_staleness_heatmap_report_payload(digest)


def test_hard_flags_frozen_dataclasses_and_decimal_public_numbers() -> None:
    digest = report(observation("frozen-category"))

    assert is_dataclass(ResearchMarketDataStalenessHeatmapConfig)
    assert is_dataclass(ResearchMarketDataStalenessHeatmapInput)
    assert is_dataclass(ResearchMarketDataStalenessHeatmapRow)
    assert is_dataclass(ResearchMarketDataStalenessHeatmapReasonCodeCount)
    assert is_dataclass(ResearchMarketDataStalenessHeatmapDigest)
    assert is_dataclass(ResearchMarketDataStalenessHeatmapReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.heatmap_rows[0].staleness_age_seconds = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(digest, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest.heatmap_rows[0], readonly=False)

    for item in (
        digest,
        *digest.heatmap_rows,
        *digest.reason_code_counts,
        research_market_data_staleness_heatmap_digest(digest),
    ):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    for field_name in (
        "cell_count",
        "pass_count",
        "watch_count",
        "block_count",
        "stale_watch_count",
        "stale_block_count",
        "source_family_gap_count",
        "mean_staleness_age_seconds",
        "max_staleness_age_seconds",
    ):
        assert type(getattr(digest, field_name)) is Decimal


def test_report_constructors_revalidate_consistency_and_tampering() -> None:
    digest = report(
        observation(
            "watch-category",
            latest_observed_at=GENERATED_AT - timedelta(minutes=90),
        ),
    )

    with pytest.raises(ValueError, match="cell_count"):
        replace(digest, cell_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="pass")
    with pytest.raises(ValueError, match="mean_staleness_age_seconds"):
        replace(digest, mean_staleness_age_seconds=d("2.000000"))
    with pytest.raises(ValueError, match="heatmap_rows"):
        replace(digest, heatmap_rows=(digest.heatmap_rows[0], digest.heatmap_rows[0]))
    with pytest.raises(ValueError, match="count"):
        ResearchMarketDataStalenessHeatmapReasonCodeCount(
            reason_code="manual_zero",
            count=ZERO,
        )
    with pytest.raises(ValueError, match="six decimal"):
        object.__setattr__(
            digest.heatmap_rows[0],
            "staleness_age_seconds",
            d("5400.0000000"),
        )
        research_market_data_staleness_heatmap_report_payload(digest)


def test_public_dataclasses_reject_subclassing_and_subclass_instances() -> None:
    digest = report(observation("exact-type"))
    public_values = (
        config(),
        observation("exact-input"),
        digest.heatmap_rows[0],
        digest.reason_code_counts[0],
        research_market_data_staleness_heatmap_digest(digest),
        digest,
    )

    for value in public_values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(value)}

        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.research_market_data_staleness_heatmap_report as digest

    assert digest.__all__ == (
        "DEFAULT_RESEARCH_MARKET_DATA_STALENESS_HEATMAP_CONFIG_VERSION",
        "ResearchMarketDataStalenessHeatmapConfig",
        "ResearchMarketDataStalenessHeatmapDigest",
        "ResearchMarketDataStalenessHeatmapInput",
        "ResearchMarketDataStalenessHeatmapReasonCodeCount",
        "ResearchMarketDataStalenessHeatmapReport",
        "ResearchMarketDataStalenessHeatmapRow",
        "build_research_market_data_staleness_heatmap_report",
        "research_market_data_staleness_heatmap_digest",
        "research_market_data_staleness_heatmap_report_payload",
    )


def test_static_forbidden_surface_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "position",
        "buy",
        "sell",
        "recommend",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "token",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_dataclass_helpers = {"asdict"}
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
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", *forbidden_dataclass_helpers}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(
                alias.name not in forbidden_dataclass_helpers
                for alias in node.names
            )


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]
