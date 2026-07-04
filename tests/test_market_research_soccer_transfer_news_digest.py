from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_soccer_transfer_news_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_transfer_news_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    source_id: str = "source-alpha",
    *,
    player_ref: str = "player-alpha",
    club_ref: str = "club-alpha",
    market_slug: str = "player-alpha-to-club-alpha",
    headline_ref: str = "headline-alpha",
    transfer_probability: str | Decimal = "0.720000",
    confidence_score: str | Decimal = "0.850000",
    source_age_seconds: str | Decimal = "120.000000",
    mention_count: str | Decimal = "3",
    published_at: datetime = datetime(2026, 7, 4, 11, 58, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("transfer_news_probability_high",),
):
    module = api()
    return module.SoccerTransferNewsItem(
        source_id=source_id,
        player_ref=player_ref,
        club_ref=club_ref,
        market_slug=market_slug,
        headline_ref=headline_ref,
        transfer_probability=(
            transfer_probability
            if isinstance(transfer_probability, Decimal)
            else d(transfer_probability)
        ),
        confidence_score=(
            confidence_score
            if isinstance(confidence_score, Decimal)
            else d(confidence_score)
        ),
        source_age_seconds=(
            source_age_seconds
            if isinstance(source_age_seconds, Decimal)
            else d(source_age_seconds)
        ),
        mention_count=mention_count if isinstance(mention_count, Decimal) else d(mention_count),
        published_at=published_at,
        reason_codes=reason_codes,
    )


def build(*items: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_research_soccer_transfer_news_digest(
        items,
        config=module.SoccerTransferNewsDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in JSON payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_floats(child)
    if isinstance(value, list):
        for child in value:
            assert_no_floats(child)


def test_soccer_transfer_news_digest_reduces_news_deterministically() -> None:
    module = api()

    report = build(
        item(
            "source-watch",
            player_ref="player-beta",
            club_ref="club-beta",
            market_slug="player-beta-to-club-beta",
            headline_ref="headline-beta",
            transfer_probability="0.540000",
            confidence_score="0.640000",
            source_age_seconds="900.000000",
            mention_count="2",
            published_at=datetime(2026, 7, 4, 12, 30, tzinfo=timezone(timedelta(hours=1))),
            reason_codes=("transfer_news_probability_watch",),
        ),
        item(
            "source-blocked",
            player_ref="player-gamma",
            club_ref="club-gamma",
            market_slug="player-gamma-to-club-gamma",
            headline_ref="headline-gamma",
            transfer_probability="0.840000",
            confidence_score="0.910000",
            source_age_seconds="60.000000",
            mention_count="5",
            published_at=datetime(2026, 7, 4, 11, 59, tzinfo=UTC),
            reason_codes=("transfer_news_probability_high",),
        ),
        item(
            "source-inline",
            player_ref="player-alpha",
            club_ref="club-alpha",
            market_slug="player-alpha-to-club-alpha",
            headline_ref="headline-alpha",
            transfer_probability="0.310000",
            confidence_score="0.420000",
            source_age_seconds="1500.000000",
            mention_count="1",
            published_at=datetime(2026, 7, 4, 7, 35, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=("transfer_news_probability_inline",),
        ),
    )

    assert isinstance(report, module.SoccerTransferNewsDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "market-research-soccer-transfer-news-digest-v0"
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_soccer_transfer_news_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.high_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.inline_signal_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.max_transfer_probability == d("0.840000")
    assert report.average_confidence_score == d("0.656667")
    assert report.reason_codes == (
        "soccer_transfer_news_high_signal_present",
        "soccer_transfer_news_watch_signal_present",
        "soccer_transfer_news_stale_source_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.rows) == (
        "player-gamma-to-club-gamma",
        "player-beta-to-club-beta",
        "player-alpha-to-club-alpha",
    )
    high, watch, inline = report.rows
    assert high.signal_status == "blocked"
    assert high.signal_bucket == "high_signal"
    assert high.published_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert high.reason_codes == (
        "soccer_transfer_news_high_signal",
        "soccer_transfer_news_source_fresh",
    )
    assert watch.signal_status == "watch"
    assert watch.reason_codes == (
        "soccer_transfer_news_watch_signal",
        "soccer_transfer_news_source_fresh",
    )
    assert inline.signal_status == "pass"
    assert inline.reason_codes == (
        "soccer_transfer_news_inline_signal",
        "soccer_transfer_news_source_stale",
    )


def test_empty_digest_is_report_only_blocked_and_decimal_zeroed() -> None:
    module = api()

    report = build()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_soccer_transfer_news_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.high_signal_count == d("0.000000")
    assert report.watch_signal_count == d("0.000000")
    assert report.inline_signal_count == d("0.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.max_transfer_probability == d("0.000000")
    assert report.average_confidence_score == d("0.000000")
    assert report.reason_codes == ("soccer_transfer_news_digest_empty",)
    assert report.rows == ()
    assert report.reason_code_counts == (
        module.SoccerTransferNewsReasonCodeCount(
            reason_code="soccer_transfer_news_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_validates_decimal_datetime_flags_duplicates_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="transfer_probability must be a Decimal"):
        item(transfer_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="confidence_score must be between zero and one"):
        item(confidence_score="1.100000")
    with pytest.raises(ValueError, match="published_at must be timezone-aware"):
        item(published_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_soccer_transfer_news_digest(
            (),
            config=module.SoccerTransferNewsDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes must match transfer_probability"):
        item(
            transfer_probability="0.840000",
            reason_codes=("transfer_news_probability_inline",),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate source_id"):
        build(item("source-dupe"), item("source-dupe"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item(), paper_only=False)
    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.SoccerTransferNewsDigestConfig(paper_only=False)

    frozen = item("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.transfer_probability = d("0.900000")  # type: ignore[misc]


def test_payload_uses_decimal_strings_and_has_no_live_or_secret_surface() -> None:
    module = api()
    report = build(item("source-json"))

    payload = module.market_research_soccer_transfer_news_digest_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["transfer_probability"] == "0.720000"
    assert payload["rows"][0]["published_at"] == "2026-07-04T11:58:00+00:00"
    assert_no_floats(payload)

    for value in (
        module.SoccerTransferNewsDigestConfig(),
        item("source-decimal"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if _public_numeric(field.name):
                assert type(getattr(value, field.name)) is Decimal, field.name

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
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
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "auth",
        "secret",
        "database",
        "network",
    ):
        assert forbidden not in source.lower()


def _public_numeric(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
        or field_name.endswith("_probability")
        or field_name.endswith("_seconds")
    )
