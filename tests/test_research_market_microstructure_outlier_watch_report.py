from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_microstructure_outlier_watch_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_microstructure_outlier_watch_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 58, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "research-market-microstructure-outlier-watch-report-v1",
        "watch_spread_outlier_score": d("0.350000"),
        "block_spread_outlier_score": d("0.700000"),
        "watch_depth_imbalance_score": d("0.300000"),
        "block_depth_imbalance_score": d("0.650000"),
        "watch_quote_age_seconds": d("60.000000"),
        "block_quote_age_seconds": d("300.000000"),
        "watch_unexplained_book_movement_score": d("0.300000"),
        "block_unexplained_book_movement_score": d("0.650000"),
        "watch_fee_friction_score": d("0.250000"),
        "block_fee_friction_score": d("0.500000"),
        "watch_manual_review_urgency_score": d("0.350000"),
        "block_manual_review_urgency_score": d("0.700000"),
        "block_signal_count_threshold": d("3"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketMicrostructureOutlierWatchConfig(**values)


def observation(
    *,
    observed_at: datetime = OBSERVED_AT,
    spread_outlier_score: Decimal = d("0.050000"),
    depth_imbalance_score: Decimal = d("0.100000"),
    quote_age_seconds: Decimal = d("20.000000"),
    book_movement_score: Decimal = d("0.100000"),
    book_movement_explained: bool = True,
    fee_friction_score: Decimal = d("0.050000"),
    manual_review_urgency_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketMicrostructureOutlierObservation(
        observed_at=observed_at,
        spread_outlier_score=spread_outlier_score,
        depth_imbalance_score=depth_imbalance_score,
        quote_age_seconds=quote_age_seconds,
        book_movement_score=book_movement_score,
        book_movement_explained=book_movement_explained,
        fee_friction_score=fee_friction_score,
        manual_review_urgency_score=manual_review_urgency_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*observations: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_market_microstructure_outlier_watch_report(
        observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "raw",
        "market_id",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "candidate",
        "dsn",
        "table",
        "token",
        "private",
        "auth",
        "wallet",
        "network",
        "database",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        for fragment in forbidden_fragments:
            assert fragment not in lowered, value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_codes"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "seconds",
                "age",
                "urgency",
                "imbalance",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def test_empty_input_returns_pass_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-market-microstructure-outlier-watch-report-v1"
    )
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("microstructure_outlier_watch_passed",)
    assert empty_report.observation_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_spread_outlier_score == d("0.000000")
    assert empty_report.max_depth_imbalance_score == d("0.000000")
    assert empty_report.max_quote_age_seconds == d("0.000000")
    assert empty_report.max_unexplained_book_movement_score == d("0.000000")
    assert empty_report.max_fee_friction_score == d("0.000000")
    assert empty_report.max_manual_review_urgency_score == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_fields(empty_report)

    payload = module.research_market_microstructure_outlier_watch_report_payload(
        empty_report,
    )
    digest_value = module.research_market_microstructure_outlier_watch_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "pass"
    assert payload["observation_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64


def test_report_scores_spread_depth_stale_movement_fee_and_manual_urgency() -> None:
    watched = observation(
        observed_at=GENERATED_AT - timedelta(seconds=120),
        spread_outlier_score=d("0.450000"),
    )
    blocked = observation(
        observed_at=GENERATED_AT - timedelta(seconds=10),
        spread_outlier_score=d("0.800000"),
        depth_imbalance_score=d("0.700000"),
        quote_age_seconds=d("360.000000"),
        book_movement_score=d("0.750000"),
        book_movement_explained=False,
        fee_friction_score=d("0.550000"),
        manual_review_urgency_score=d("0.900000"),
    )
    passed = observation(observed_at=GENERATED_AT - timedelta(seconds=30))

    built = report(passed, watched, blocked)

    assert built.status == "block"
    assert built.observation_count == d("3")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.spread_outlier_count == d("2")
    assert built.depth_imbalance_count == d("1")
    assert built.stale_quote_count == d("1")
    assert built.unexplained_book_movement_count == d("1")
    assert built.fee_friction_count == d("1")
    assert built.manual_review_urgent_count == d("1")
    assert built.max_spread_outlier_score == d("0.800000")
    assert built.max_depth_imbalance_score == d("0.700000")
    assert built.max_quote_age_seconds == d("360.000000")
    assert built.max_unexplained_book_movement_score == d("0.750000")
    assert built.max_fee_friction_score == d("0.550000")
    assert built.max_manual_review_urgency_score == d("0.900000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    blocked_row, watched_row, passed_row = built.rows
    assert blocked_row.outlier_signal_count == d("6")
    assert blocked_row.status == "block"
    assert blocked_row.spread_outlier is True
    assert blocked_row.depth_imbalance is True
    assert blocked_row.stale_quote is True
    assert blocked_row.unexplained_book_movement is True
    assert blocked_row.fee_friction is True
    assert blocked_row.manual_review_urgent is True
    assert blocked_row.reason_codes == (
        "spread_outlier_score_block",
        "depth_imbalance_block",
        "stale_quote_age_block",
        "unexplained_book_movement_block",
        "fee_friction_block",
        "manual_review_urgency_block",
        "microstructure_outlier_watch_block",
    )

    assert watched_row.outlier_signal_count == d("1")
    assert watched_row.status == "watch"
    assert watched_row.reason_codes == (
        "spread_outlier_score_watch",
        "microstructure_outlier_watch_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("microstructure_outlier_watch_passed",)


def test_payload_is_decimal_string_sanitized_deterministic_and_digest_checked() -> None:
    module = api()
    observations = (
        observation(spread_outlier_score=d("0.450000")),
        observation(
            observed_at=GENERATED_AT - timedelta(seconds=30),
            depth_imbalance_score=d("0.700000"),
            quote_age_seconds=d("360.000000"),
            manual_review_urgency_score=d("0.800000"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["status"] == "block"
    assert payload["rows"][0]["depth_imbalance_score"] == "0.700000"
    assert payload["rows"][1]["spread_outlier_score"] == "0.450000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_microstructure_outlier_watch_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_fields(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_microstructure_outlier_watch_public_payload(
            tampered,
        )


def test_dataclasses_are_frozen_and_reject_subclassing_and_bad_flags() -> None:
    module = api()
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketMicrostructureOutlierWatchConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)


def test_strict_types_unsafe_inputs_and_live_surfaces_are_rejected() -> None:
    module = api()
    with pytest.raises(ValueError, match="spread_outlier_score must be exactly Decimal"):
        observation(spread_outlier_score=_DecimalSubclass("0.400000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="depth_imbalance_score must be a Decimal"):
        observation(depth_imbalance_score=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="book_movement_explained must be a bool"):
        observation(book_movement_explained=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 58))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 8, 11, 58, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="block_spread_outlier_score"):
        cfg(block_spread_outlier_score=d("0.300000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    for cls in (
        module.ResearchMarketMicrostructureOutlierWatchConfig,
        module.ResearchMarketMicrostructureOutlierObservation,
        module.ResearchMarketMicrostructureOutlierWatchRow,
        module.ResearchMarketMicrostructureOutlierWatchReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "market_id" not in lowered
            assert "slug" not in lowered
            assert "question" not in lowered
            assert "source" not in lowered
            assert "url" not in lowered
            assert "candidate" not in lowered
            assert "dsn" not in lowered
            assert "table" not in lowered
            assert "token" not in lowered

    public_names = set(module.__all__)
    forbidden_public_name_fragments = {
        "client",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    }
    for name in public_names:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)
