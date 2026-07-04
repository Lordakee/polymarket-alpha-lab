from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 21, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_platoon_split_lineup_edge_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-baseball-platoon-split-lineup-edge-digest-v0",
        "max_source_age_minutes": d("20.000000"),
        "max_lineup_confirmation_age_minutes": d("30.000000"),
        "min_watch_platoon_edge_score": d("0.100000"),
        "min_blocked_platoon_edge_score": d("0.250000"),
        "min_favorable_batter_count": d("5.000000"),
        "min_confirmed_batter_count": d("9.000000"),
        "min_late_lineup_change_count": d("1.000000"),
        "min_source_disagreement_count": d("2.000000"),
    }
    values.update(overrides)
    return module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig(**values)


def row(
    market_slug: str,
    *,
    team: str = "nyy",
    opponent: str = "bos",
    pitcher_hand: str = "left",
    scheduled_first_pitch_at: datetime | None = None,
    lineup_confirmed_at: datetime | None = None,
    source_timestamp_at: datetime | None = None,
    platoon_edge_score: object = "0.040000",
    favorable_batter_count: object = "3.000000",
    confirmed_batter_count: object = "9.000000",
    late_lineup_change_count: object = "0.000000",
    source_disagreement_count: object = "0.000000",
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow(
        market_slug=market_slug,
        team=team,
        opponent=opponent,
        pitcher_hand=pitcher_hand,
        scheduled_first_pitch_at=scheduled_first_pitch_at
        or GENERATED_AT + timedelta(minutes=120),
        lineup_confirmed_at=lineup_confirmed_at or GENERATED_AT - timedelta(minutes=5),
        source_timestamp_at=source_timestamp_at or GENERATED_AT - timedelta(minutes=3),
        platoon_edge_score=d(platoon_edge_score)
        if type(platoon_edge_score) is str
        else platoon_edge_score,
        favorable_batter_count=d(favorable_batter_count)
        if type(favorable_batter_count) is str
        else favorable_batter_count,
        confirmed_batter_count=d(confirmed_batter_count)
        if type(confirmed_batter_count) is str
        else confirmed_batter_count,
        late_lineup_change_count=d(late_lineup_change_count)
        if type(late_lineup_change_count) is str
        else late_lineup_change_count,
        source_disagreement_count=d(source_disagreement_count)
        if type(source_disagreement_count) is str
        else source_disagreement_count,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_baseball_platoon_split_lineup_edge_digest(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_platoon_split_lineup_edge_digest_reduces_markets_deterministically() -> None:
    eastern_source_at = datetime(2026, 7, 4, 16, 58, tzinfo=timezone(timedelta(hours=-4)))

    report = digest(
        row(
            "clear-pass",
            team="ari",
            opponent="col",
        ),
        row(
            "zeta-stale",
            team="sea",
            opponent="tex",
            lineup_confirmed_at=GENERATED_AT - timedelta(minutes=40),
            source_timestamp_at=GENERATED_AT - timedelta(minutes=30),
            platoon_edge_score="0.060000",
            favorable_batter_count="4.000000",
        ),
        row(
            "alpha-edge",
            team="nyy",
            opponent="bos",
            scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=45),
            lineup_confirmed_at=GENERATED_AT - timedelta(minutes=15),
            source_timestamp_at=eastern_source_at,
            platoon_edge_score="0.320000",
            favorable_batter_count="6.000000",
            late_lineup_change_count="1.000000",
            source_disagreement_count="2.000000",
            upstream_reason_codes=("beat-writer-lineup-card", "club-card-confirmed"),
        ),
        row(
            "beta-watch",
            team="lad",
            opponent="sf",
            pitcher_hand="right",
            scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=80),
            platoon_edge_score="0.180000",
            favorable_batter_count="5.000000",
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    module = api()
    assert report == module.MarketResearchBaseballPlatoonSplitLineupEdgeDigest(
        generated_at=GENERATED_AT,
        config_version="market-research-baseball-platoon-split-lineup-edge-digest-v0",
        digest_status="blocked",
        market_count=d("4.000000"),
        input_row_count=d("4.000000"),
        pass_market_count=d("1.000000"),
        watch_market_count=d("1.000000"),
        blocked_market_count=d("2.000000"),
        platoon_edge_market_count=d("2.000000"),
        high_edge_market_count=d("1.000000"),
        stale_source_market_count=d("1.000000"),
        stale_lineup_market_count=d("1.000000"),
        thin_lineup_market_count=d("0.000000"),
        favorable_lineup_depth_market_count=d("2.000000"),
        late_lineup_change_market_count=d("1.000000"),
        source_disagreement_market_count=d("1.000000"),
        upstream_context_market_count=d("1.000000"),
        risk_score=d("0.470000"),
        max_platoon_edge_score=d("0.320000"),
        max_source_age_minutes=d("30.000000"),
        max_lineup_confirmation_age_minutes=d("40.000000"),
        rows=(
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow(
                market_slug="alpha-edge",
                team="nyy",
                opponent="bos",
                pitcher_hand="left",
                row_status="blocked",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=45),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=15),
                source_timestamp_at=datetime(2026, 7, 4, 20, 58, tzinfo=UTC),
                minutes_to_first_pitch=d("45.000000"),
                lineup_confirmation_age_minutes=d("15.000000"),
                source_age_minutes=d("2.000000"),
                platoon_edge_score=d("0.320000"),
                favorable_batter_count=d("6.000000"),
                confirmed_batter_count=d("9.000000"),
                favorable_batter_ratio=d("0.666667"),
                late_lineup_change_count=d("1.000000"),
                source_disagreement_count=d("2.000000"),
                upstream_reason_codes=("beat-writer-lineup-card", "club-card-confirmed"),
                row_risk_score=d("0.470000"),
                reason_codes=(
                    "baseball_platoon_split_lineup_edge_detected",
                    "baseball_platoon_split_lineup_edge_high",
                    "baseball_platoon_split_lineup_edge_favorable_lineup_depth",
                    "baseball_platoon_split_lineup_edge_late_lineup_change",
                    "baseball_platoon_split_lineup_edge_source_disagreement",
                    "baseball_platoon_split_lineup_edge_upstream_context",
                ),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow(
                market_slug="zeta-stale",
                team="sea",
                opponent="tex",
                pitcher_hand="left",
                row_status="blocked",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=120),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=40),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=30),
                minutes_to_first_pitch=d("120.000000"),
                lineup_confirmation_age_minutes=d("40.000000"),
                source_age_minutes=d("30.000000"),
                platoon_edge_score=d("0.060000"),
                favorable_batter_count=d("4.000000"),
                confirmed_batter_count=d("9.000000"),
                favorable_batter_ratio=d("0.444444"),
                late_lineup_change_count=d("0.000000"),
                source_disagreement_count=d("0.000000"),
                upstream_reason_codes=(),
                row_risk_score=d("0.460000"),
                reason_codes=(
                    "baseball_platoon_split_lineup_edge_stale_source",
                    "baseball_platoon_split_lineup_edge_stale_lineup_confirmation",
                ),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow(
                market_slug="beta-watch",
                team="lad",
                opponent="sf",
                pitcher_hand="right",
                row_status="watch",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=80),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=5),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=3),
                minutes_to_first_pitch=d("80.000000"),
                lineup_confirmation_age_minutes=d("5.000000"),
                source_age_minutes=d("3.000000"),
                platoon_edge_score=d("0.180000"),
                favorable_batter_count=d("5.000000"),
                confirmed_batter_count=d("9.000000"),
                favorable_batter_ratio=d("0.555556"),
                late_lineup_change_count=d("0.000000"),
                source_disagreement_count=d("0.000000"),
                upstream_reason_codes=(),
                row_risk_score=d("0.180000"),
                reason_codes=(
                    "baseball_platoon_split_lineup_edge_detected",
                    "baseball_platoon_split_lineup_edge_favorable_lineup_depth",
                ),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow(
                market_slug="clear-pass",
                team="ari",
                opponent="col",
                pitcher_hand="left",
                row_status="pass",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=120),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=5),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=3),
                minutes_to_first_pitch=d("120.000000"),
                lineup_confirmation_age_minutes=d("5.000000"),
                source_age_minutes=d("3.000000"),
                platoon_edge_score=d("0.040000"),
                favorable_batter_count=d("3.000000"),
                confirmed_batter_count=d("9.000000"),
                favorable_batter_ratio=d("0.333333"),
                late_lineup_change_count=d("0.000000"),
                source_disagreement_count=d("0.000000"),
                upstream_reason_codes=(),
                row_risk_score=d("0.040000"),
                reason_codes=("baseball_platoon_split_lineup_edge_clear",),
            ),
        ),
        reason_code_counts=(
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_detected",
                market_count=d("2.000000"),
                market_ratio=d("0.500000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_high",
                market_count=d("1.000000"),
                market_ratio=d("0.250000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_stale_source",
                market_count=d("1.000000"),
                market_ratio=d("0.250000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_stale_lineup_confirmation",
                market_count=d("1.000000"),
                market_ratio=d("0.250000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_favorable_lineup_depth",
                market_count=d("2.000000"),
                market_ratio=d("0.500000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_late_lineup_change",
                market_count=d("1.000000"),
                market_ratio=d("0.250000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_source_disagreement",
                market_count=d("1.000000"),
                market_ratio=d("0.250000"),
            ),
            module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
                reason_code="baseball_platoon_split_lineup_edge_upstream_context",
                market_count=d("1.000000"),
                market_ratio=d("0.250000"),
            ),
        ),
        reason_codes=(
            "baseball_platoon_split_lineup_edge_detected",
            "baseball_platoon_split_lineup_edge_high",
            "baseball_platoon_split_lineup_edge_stale_source",
            "baseball_platoon_split_lineup_edge_stale_lineup_confirmation",
            "baseball_platoon_split_lineup_edge_favorable_lineup_depth",
            "baseball_platoon_split_lineup_edge_late_lineup_change",
            "baseball_platoon_split_lineup_edge_source_disagreement",
            "baseball_platoon_split_lineup_edge_upstream_context",
        ),
    )
    assert report.generated_at.tzinfo is UTC
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_returns_blocked_report_only_zero_digest_and_payload_strings() -> None:
    module = api()
    report = digest()
    payload = module.market_research_baseball_platoon_split_lineup_edge_digest_payload(
        report,
    )

    assert report.digest_status == "blocked"
    assert report.market_count == d("0.000000")
    assert report.input_row_count == d("0.000000")
    assert report.rows == ()
    assert report.risk_score == d("0.000000")
    assert report.reason_codes == ("baseball_platoon_split_lineup_edge_rows_missing",)
    assert report.reason_code_counts == (
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount(
            reason_code="baseball_platoon_split_lineup_edge_rows_missing",
            market_count=d("0.000000"),
            market_ratio=d("0.000000"),
        ),
    )
    assert payload["generated_at"] == "2026-07-04T21:00:00+00:00"
    assert payload["market_count"] == "0.000000"
    assert payload["risk_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload, allow_nan=False, sort_keys=True)) == payload
    _assert_no_floats_or_ints(payload)


def test_payload_is_json_ready_decimal_only_and_utc_normalized() -> None:
    module = api()
    report = digest(
        row(
            "alpha-edge",
            scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=45),
            source_timestamp_at=datetime(2026, 7, 4, 16, 58, tzinfo=timezone(timedelta(hours=-4))),
            platoon_edge_score="0.320000",
            favorable_batter_count="6.000000",
            late_lineup_change_count="1.000000",
            source_disagreement_count="2.000000",
            upstream_reason_codes=("club-card-confirmed", "beat-writer-lineup-card"),
        ),
        generated_at=GENERATED_AT,
    )

    payload = module.market_research_baseball_platoon_split_lineup_edge_digest_payload(report)

    assert payload["generated_at"] == "2026-07-04T21:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["risk_score"] == "0.470000"
    assert payload["rows"][0]["source_timestamp_at"] == "2026-07-04T20:58:00+00:00"
    assert payload["rows"][0]["minutes_to_first_pitch"] == "45.000000"
    assert payload["rows"][0]["favorable_batter_ratio"] == "0.666667"
    assert payload["rows"][0]["upstream_reason_codes"] == [
        "beat-writer-lineup-card",
        "club-card-confirmed",
    ]
    assert payload["reason_code_counts"][0]["market_ratio"] == "1.000000"
    _assert_no_floats_or_ints(payload)


def test_validates_frozen_decimal_datetime_flags_duplicates_and_reason_contracts() -> None:
    module = api()
    cfg = config()
    input_row = row("alpha-edge")
    report = digest(input_row)

    for value in (cfg, input_row, report, report.rows[0], report.reason_code_counts[0]):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        input_row.market_slug = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_source_age_minutes"):
        config(max_source_age_minutes=20)
    with pytest.raises(ValueError, match="min_watch_platoon_edge_score"):
        config(min_watch_platoon_edge_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="platoon_edge_score"):
        row("bad-edge", platoon_edge_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        digest(generated_at=_DatetimeSubclass(2026, 7, 4, 21, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="scheduled_first_pitch_at"):
        row("naive-first-pitch", scheduled_first_pitch_at=datetime(2026, 7, 4, 22, 0))
    with pytest.raises(ValueError, match="paper_only"):
        row("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        row("bad-report-flag", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(cfg, readonly=False)
    with pytest.raises(ValueError, match="config"):
        digest(cfg=object())
    with pytest.raises(ValueError, match="source_timestamp_at"):
        digest(row("future-source", source_timestamp_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="lineup_confirmed_at"):
        digest(row("future-lineup", lineup_confirmed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="scheduled_first_pitch_at"):
        digest(row("already-started", scheduled_first_pitch_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        digest(row("duplicate"), row("duplicate"))
    with pytest.raises(ValueError, match="confirmed_batter_count"):
        digest(row("count-mismatch", favorable_batter_count="10.000000"))
    with pytest.raises(ValueError, match="row_status"):
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow(
            market_slug="manual",
            team="nyy",
            opponent="bos",
            pitcher_hand="left",
            row_status="pass",
            scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=45),
            lineup_confirmed_at=GENERATED_AT - timedelta(minutes=15),
            source_timestamp_at=GENERATED_AT - timedelta(minutes=2),
            minutes_to_first_pitch=d("45.000000"),
            lineup_confirmation_age_minutes=d("15.000000"),
            source_age_minutes=d("2.000000"),
            platoon_edge_score=d("0.320000"),
            favorable_batter_count=d("6.000000"),
            confirmed_batter_count=d("9.000000"),
            favorable_batter_ratio=d("0.666667"),
            late_lineup_change_count=d("1.000000"),
            source_disagreement_count=d("2.000000"),
            upstream_reason_codes=("beat-writer-lineup-card",),
            row_risk_score=d("0.470000"),
            reason_codes=(
                "baseball_platoon_split_lineup_edge_detected",
                "baseball_platoon_split_lineup_edge_high",
            ),
        )


def test_public_numeric_fields_are_decimal_only() -> None:
    module = api()
    public_classes = (
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig,
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow,
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow,
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount,
        module.MarketResearchBaseballPlatoonSplitLineupEdgeDigest,
    )
    numeric_name_fragments = (
        "count",
        "minutes",
        "ratio",
        "score",
    )

    for cls in public_classes:
        for field in fields(cls):
            if field.name == "reason_code_counts":
                continue
            if any(fragment in field.name for fragment in numeric_name_fragments):
                assert field.type in (Decimal, "Decimal")


def test_static_module_scope_is_pure_report_only_readonly_and_without_forbidden_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered = source.lower()

    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "pathlib",
        "environ",
        "fast",
    ):
        assert forbidden not in lowered

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
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"float", "open", "__import__"}
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    assert tuple(module.__all__) == (
        "DEFAULT_MARKET_RESEARCH_BASEBALL_PLATOON_SPLIT_LINEUP_EDGE_DIGEST_CONFIG_VERSION",
        "MarketResearchBaseballPlatoonSplitLineupEdgeDigest",
        "MarketResearchBaseballPlatoonSplitLineupEdgeDigestConfig",
        "MarketResearchBaseballPlatoonSplitLineupEdgeDigestInputRow",
        "MarketResearchBaseballPlatoonSplitLineupEdgeDigestReasonCodeCount",
        "MarketResearchBaseballPlatoonSplitLineupEdgeDigestRow",
        "build_market_research_baseball_platoon_split_lineup_edge_digest",
        "market_research_baseball_platoon_split_lineup_edge_digest_payload",
    )


def _assert_no_floats_or_ints(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        raise AssertionError("payload must serialize numerics as strings")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_floats_or_ints(nested)
    if isinstance(value, list):
        for nested in value:
            _assert_no_floats_or_ints(nested)
