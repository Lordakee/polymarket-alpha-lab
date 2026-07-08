from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_depth_anomaly_digest import (
    DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION,
    ResearchMarketDepthAnomalyDigestConfig,
    ResearchMarketDepthAnomalyDigestReasonCodeCount,
    ResearchMarketDepthAnomalyDigestReport,
    ResearchMarketDepthAnomalyDigestRow,
    ResearchMarketDepthAnomalyObservation,
    build_research_market_depth_anomaly_digest_report,
    research_market_depth_anomaly_digest_payload,
    research_market_depth_anomaly_public_digest,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_market_depth_anomaly_digest.py")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketDepthAnomalyDigestConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION,
        "depth_shortfall_watch": d("0.400000"),
        "depth_shortfall_block": d("0.750000"),
        "imbalance_watch": d("0.600000"),
        "imbalance_block": d("0.850000"),
        "spread_width_watch": d("0.080000"),
        "spread_width_block": d("0.150000"),
        "stale_snapshot_age_seconds": d("900.000000"),
    }
    values.update(overrides)
    return ResearchMarketDepthAnomalyDigestConfig(**values)


def observation(
    segment: str = "macro-liquidity",
    *,
    best_bid_depth: Decimal = d("20.000000"),
    best_ask_depth: Decimal = d("20.000000"),
    top_bid_depth: Decimal = d("55.000000"),
    top_ask_depth: Decimal = d("45.000000"),
    baseline_depth: Decimal = d("100.000000"),
    spread_width: Decimal = d("0.020000"),
    snapshot_at: datetime = GENERATED_AT - timedelta(minutes=5),
    reason_codes: tuple[str, ...] = ("depth_snapshot_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketDepthAnomalyObservation:
    return ResearchMarketDepthAnomalyObservation(
        segment=segment,
        best_bid_depth=best_bid_depth,
        best_ask_depth=best_ask_depth,
        top_bid_depth=top_bid_depth,
        top_ask_depth=top_ask_depth,
        baseline_depth=baseline_depth,
        spread_width=spread_width,
        snapshot_at=snapshot_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketDepthAnomalyObservation,
    cfg: ResearchMarketDepthAnomalyDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketDepthAnomalyDigestReport:
    return build_research_market_depth_anomaly_digest_report(
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


def test_pass_report_payload_and_public_digest_are_review_only() -> None:
    digest_report = report(observation("macro-clear"))

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.config_version == (
        DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION
    )
    assert digest_report.observation_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.watch_count == ZERO
    assert digest_report.block_count == ZERO
    assert digest_report.status == "pass"
    assert digest_report.reason_codes == ("market_depth_anomaly_digest_clear",)
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    row = digest_report.market_depth_anomaly_rows[0]
    assert row.review_label == "depth-anomaly-001"
    assert row.segment == "macro-clear"
    assert row.status == "pass"
    assert row.total_depth == d("100.000000")
    assert row.depth_ratio == d("1.000000")
    assert row.depth_shortfall_ratio == ZERO
    assert row.absolute_imbalance_ratio == d("0.100000")
    assert row.snapshot_age_seconds == d("300.000000")
    assert row.anomaly_score == d("0.120000")
    assert row.reason_codes == ("depth_snapshot_available", "market_depth_clear")

    payload = research_market_depth_anomaly_digest_payload(digest_report)
    public_digest = research_market_depth_anomaly_public_digest(digest_report)
    assert payload["status"] == "pass"
    assert payload["observation_count"] == "1.000000"
    assert payload["market_depth_anomaly_rows"][0]["anomaly_score"] == "0.120000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert public_digest["status"] == payload["status"]
    assert public_digest["observation_count"] == payload["observation_count"]
    assert public_digest["review_rows"][0]["review_label"] == row.review_label
    assert public_digest["review_rows"][0]["status"] == row.status
    assert public_digest["review_rows"][0]["anomaly_score"] == "0.120000"
    assert public_digest["paper_only"] is True
    assert public_digest["report_only"] is True
    assert public_digest["readonly"] is True
    assert_no_float(payload)
    assert_no_float(public_digest)
    json.dumps(payload, sort_keys=True)
    json.dumps(public_digest, sort_keys=True)


def test_watch_and_block_statuses_roll_up_with_reason_counts() -> None:
    digest_report = report(
        observation(
            "macro-watch",
            top_bid_depth=d("20.000000"),
            top_ask_depth=d("30.000000"),
            spread_width=d("0.090000"),
            snapshot_at=GENERATED_AT - timedelta(minutes=20),
        ),
        observation(
            "macro-block",
            best_bid_depth=d("1.000000"),
            best_ask_depth=d("2.000000"),
            top_bid_depth=d("2.000000"),
            top_ask_depth=d("8.000000"),
            spread_width=d("0.160000"),
        ),
        observation("macro-pass"),
    )

    assert digest_report.status == "block"
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.block_count == d("1.000000")
    assert digest_report.depth_shortfall_count == d("2.000000")
    assert digest_report.spread_width_count == d("2.000000")
    assert digest_report.stale_snapshot_count == d("1.000000")
    assert digest_report.reason_codes == (
        "market_depth_anomaly_digest_block",
        "depth_imbalance_watch",
        "depth_shortfall_block",
        "depth_shortfall_watch",
        "snapshot_stale_watch",
        "spread_width_block",
        "spread_width_watch",
    )
    assert tuple(row.segment for row in digest_report.market_depth_anomaly_rows) == (
        "macro-block",
        "macro-watch",
        "macro-pass",
    )
    assert tuple(row.status for row in digest_report.market_depth_anomaly_rows) == (
        "block",
        "watch",
        "pass",
    )
    assert digest_report.market_depth_anomaly_rows[0].reason_codes == (
        "depth_imbalance_watch",
        "depth_shortfall_block",
        "depth_snapshot_available",
        "spread_width_block",
    )
    assert digest_report.market_depth_anomaly_rows[1].reason_codes == (
        "depth_shortfall_watch",
        "depth_snapshot_available",
        "snapshot_stale_watch",
        "spread_width_watch",
    )
    assert digest_report.reason_code_counts[0] == (
        ResearchMarketDepthAnomalyDigestReasonCodeCount(
            reason_code="depth_snapshot_available",
            count=d("3.000000"),
        )
    )


def test_empty_inputs_block_without_public_identifiers() -> None:
    digest_report = report()

    assert digest_report.status == "block"
    assert digest_report.observation_count == ZERO
    assert digest_report.pass_count == ZERO
    assert digest_report.watch_count == ZERO
    assert digest_report.block_count == ZERO
    assert digest_report.mean_anomaly_score == ZERO
    assert digest_report.max_anomaly_score == ZERO
    assert digest_report.reason_codes == ("market_depth_anomaly_digest_no_inputs",)
    assert digest_report.reason_code_counts == (
        ResearchMarketDepthAnomalyDigestReasonCodeCount(
            reason_code="market_depth_anomaly_digest_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest_report.market_depth_anomaly_rows == ()
    assert research_market_depth_anomaly_public_digest(digest_report)["review_rows"] == []


def test_utc_normalization_and_datetime_type_rejection() -> None:
    digest_report = report(
        observation(
            snapshot_at=datetime(
                2026,
                7,
                4,
                7,
                55,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.market_depth_anomaly_rows[0].snapshot_at == datetime(
        2026,
        7,
        4,
        11,
        55,
        tzinfo=UTC,
    )
    assert digest_report.market_depth_anomaly_rows[0].snapshot_age_seconds == d("300.000000")

    with pytest.raises(ValueError, match="snapshot_at"):
        observation(snapshot_at=datetime(2026, 7, 4, 11, 55))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation("aware"), generated_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="snapshot_at"):
        observation(snapshot_at=datetime(2026, 7, 4, 11, 55, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation("aware-subclass"),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )


def test_decimal_only_type_rejection_and_config_thresholds() -> None:
    with pytest.raises(ValueError, match="best_bid_depth"):
        observation(best_bid_depth=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="top_ask_depth"):
        observation(top_ask_depth=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_width"):
        observation(spread_width=_DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="baseline_depth"):
        observation(baseline_depth=ZERO)
    with pytest.raises(ValueError, match="top_bid_depth"):
        observation(top_bid_depth=d("-0.000001"))
    with pytest.raises(ValueError, match="depth_shortfall_watch"):
        config(depth_shortfall_watch=d("0.760000"), depth_shortfall_block=d("0.750000"))
    with pytest.raises(ValueError, match="imbalance_block"):
        config(imbalance_block=d("1.000001"))


def test_public_leak_terms_are_rejected_from_public_values() -> None:
    for leaked_value in (
        "raw_candidate_abc",
        "candidate_id_abc",
        "market_id_abc",
        "market_slug_abc",
        "market_question_abc",
        "source_ref_abc",
        "source_url_abc",
        "source_text_abc",
        "postgres_dsn",
        "orders_table",
        "secret_token",
        "wallet_alpha",
        "buy_now",
        "sell_now",
        "recommend_yes",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            observation(segment=leaked_value)

    digest_report = report(observation("tamper-safe"))
    object.__setattr__(digest_report.market_depth_anomaly_rows[0], "segment", "market_slug_abc")
    with pytest.raises(ValueError, match="unsafe"):
        research_market_depth_anomaly_digest_payload(digest_report)
    with pytest.raises(ValueError, match="unsafe"):
        research_market_depth_anomaly_public_digest(digest_report)


def test_hard_flags_frozen_dataclasses_and_public_status_domain() -> None:
    digest_report = report(observation("frozen"))

    assert is_dataclass(ResearchMarketDepthAnomalyDigestConfig)
    assert is_dataclass(ResearchMarketDepthAnomalyObservation)
    assert is_dataclass(ResearchMarketDepthAnomalyDigestRow)
    assert is_dataclass(ResearchMarketDepthAnomalyDigestReasonCodeCount)
    assert is_dataclass(ResearchMarketDepthAnomalyDigestReport)
    with pytest.raises(FrozenInstanceError):
        digest_report.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest_report.market_depth_anomaly_rows[0].anomaly_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest_report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(digest_report.market_depth_anomaly_rows[0], status="blocked")

    for public_status in (digest_report.status, digest_report.market_depth_anomaly_rows[0].status):
        assert public_status in {"pass", "watch", "block"}

    for item in (
        digest_report,
        *digest_report.market_depth_anomaly_rows,
        *digest_report.reason_code_counts,
    ):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_dataclasses_reject_subclassing_and_subclass_instances() -> None:
    digest_report = report(observation("exact-type"))
    public_values = (
        config(),
        observation("exact-observation"),
        digest_report.market_depth_anomaly_rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )

    for value in public_values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(value)}

        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)


def test_deterministic_payload_and_digest_match_across_input_order() -> None:
    inputs = (
        observation(
            "zeta-watch",
            top_bid_depth=d("20.000000"),
            top_ask_depth=d("30.000000"),
            spread_width=d("0.090000"),
        ),
        observation(
            "beta-block",
            top_bid_depth=d("2.000000"),
            top_ask_depth=d("8.000000"),
            spread_width=d("0.160000"),
        ),
        observation("alpha-pass"),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    first_payload = research_market_depth_anomaly_digest_payload(first)
    second_payload = research_market_depth_anomaly_digest_payload(second)
    first_digest = research_market_depth_anomaly_public_digest(first)
    second_digest = research_market_depth_anomaly_public_digest(second)

    assert first_payload == second_payload
    assert first_digest == second_digest
    assert tuple(row.review_label for row in first.market_depth_anomaly_rows) == (
        "depth-anomaly-001",
        "depth-anomaly-002",
        "depth-anomaly-003",
    )
    assert tuple(row.segment for row in first.market_depth_anomaly_rows) == (
        "beta-block",
        "zeta-watch",
        "alpha-pass",
    )
    assert first_digest["status"] == first_payload["status"]
    assert first_digest["reason_codes"] == first_payload["reason_codes"]
    assert first_digest["block_count"] == first_payload["block_count"]
    assert first_digest["watch_count"] == first_payload["watch_count"]
    assert first_digest["pass_count"] == first_payload["pass_count"]
    assert first_digest["max_anomaly_score"] == first_payload["max_anomaly_score"]
    assert first_digest["review_rows"] == [
        {
            "review_label": row["review_label"],
            "segment": row["segment"],
            "status": row["status"],
            "anomaly_score": row["anomaly_score"],
            "reason_codes": row["reason_codes"],
        }
        for row in first_payload["market_depth_anomaly_rows"]
    ]
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_report_payload_revalidates_after_tampering() -> None:
    digest_report = report(observation("tampered-row-shape"))
    row_payload = research_market_depth_anomaly_digest_payload(digest_report)[
        "market_depth_anomaly_rows"
    ][0]
    object.__setattr__(digest_report, "market_depth_anomaly_rows", (row_payload,))
    with pytest.raises(ValueError, match="market_depth_anomaly_rows"):
        research_market_depth_anomaly_digest_payload(digest_report)

    digest_report = report(observation("tampered-row-decimal"))
    object.__setattr__(
        digest_report.market_depth_anomaly_rows[0],
        "anomaly_score",
        d("0.1200000"),
    )
    with pytest.raises(ValueError, match="six decimal"):
        research_market_depth_anomaly_digest_payload(digest_report)

    digest_report = report(observation("tampered-row-time"))
    object.__setattr__(
        digest_report.market_depth_anomaly_rows[0],
        "snapshot_at",
        datetime(2026, 7, 4, 7, 55, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC"):
        research_market_depth_anomaly_digest_payload(digest_report)

    digest_report = report(observation("tampered-count"))
    object.__setattr__(digest_report.reason_code_counts[0], "count", ZERO)
    with pytest.raises(ValueError, match="count"):
        research_market_depth_anomaly_digest_payload(digest_report)


def test_validation_errors_cover_consistency_sequences_and_exports() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("market_depth_clear", "depth_snapshot_available"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("duplicate", "duplicate"))

    digest_report = report(observation("consistent-alpha"), observation("consistent-beta"))
    with pytest.raises(ValueError, match="observation_count"):
        replace(digest_report, observation_count=d("3.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest_report, status="block")
    with pytest.raises(ValueError, match="mean_anomaly_score"):
        replace(digest_report, mean_anomaly_score=d("2.000000"))
    with pytest.raises(ValueError, match="market_depth_anomaly_rows"):
        replace(digest_report, market_depth_anomaly_rows=tuple(reversed(digest_report.market_depth_anomaly_rows)))
    with pytest.raises(ValueError, match="ResearchMarketDepthAnomalyDigestReport"):
        research_market_depth_anomaly_digest_payload(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ResearchMarketDepthAnomalyDigestReport"):
        research_market_depth_anomaly_public_digest(object())  # type: ignore[arg-type]

    import polymarket_alpha_lab.research_market_depth_anomaly_digest as digest

    assert digest.__all__ == (
        "DEFAULT_RESEARCH_MARKET_DEPTH_ANOMALY_DIGEST_CONFIG_VERSION",
        "ResearchMarketDepthAnomalyDigestConfig",
        "ResearchMarketDepthAnomalyObservation",
        "ResearchMarketDepthAnomalyDigestReasonCodeCount",
        "ResearchMarketDepthAnomalyDigestReport",
        "ResearchMarketDepthAnomalyDigestRow",
        "build_research_market_depth_anomaly_digest_report",
        "research_market_depth_anomaly_digest_payload",
        "research_market_depth_anomaly_public_digest",
    )


def test_static_forbidden_surface_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret",
        "position",
        "buy",
        "sell",
        "recommend",
        "source_ref",
        "source_url",
        "source_text",
        "market_id",
        "market_slug",
        "market_question",
        "candidate_id",
        "dsn",
        "table",
        "token",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "asdict",
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
        "write_bytes",
        "write_text",
        "float",
        "__import__",
        "asdict",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


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
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[method-assign]
