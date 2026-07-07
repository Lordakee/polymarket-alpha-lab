from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_news_freshness_edge_gate_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_news_freshness_edge_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 11, 50, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"module missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION
        ),
        "max_pass_latest_source_age_seconds": d("1800.000000"),
        "max_watch_latest_source_age_seconds": d("7200.000000"),
        "min_pass_official_update_count": d("1.000000"),
        "min_watch_official_update_count": d("0.000000"),
        "min_pass_independent_confirmation_count": d("2.000000"),
        "min_watch_independent_confirmation_count": d("1.000000"),
        "max_pass_probability_move_velocity_per_hour": d("0.050000"),
        "max_watch_probability_move_velocity_per_hour": d("0.120000"),
        "min_pass_edge_margin_probability": d("0.030000"),
        "min_watch_edge_margin_probability": d("0.010000"),
        "max_pass_cost_drag_probability": d("0.010000"),
        "max_watch_cost_drag_probability": d("0.030000"),
        "min_pass_news_freshness_edge_score": d("0.700000"),
        "min_watch_news_freshness_edge_score": d("0.350000"),
        "source_age_weight": d("0.250000"),
        "official_update_weight": d("0.150000"),
        "independent_confirmation_weight": d("0.150000"),
        "probability_move_velocity_weight": d("0.150000"),
        "edge_margin_weight": d("0.200000"),
        "cost_drag_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyCandidateNewsFreshnessEdgeGateV2Config(**values)


def snapshot(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "candidate-fresh",
        "market_slug": "fresh-news-market",
        "observed_at": OBSERVED_AT,
        "latest_source_age_seconds": d("600.000000"),
        "official_update_count": d("1.000000"),
        "independent_confirmation_count": d("3.000000"),
        "probability_move_velocity_per_hour": d("0.020000"),
        "edge_margin_probability": d("0.060000"),
        "cost_drag_probability": d("0.005000"),
        "source_config_version": "news-freshness-source-v0",
    }
    values.update(overrides)
    return module.StrategyCandidateNewsFreshnessEdgeGateV2Snapshot(**values)


def report(*values: object, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_candidate_news_freshness_edge_gate_v2_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(key)
            strings.extend(walk_strings(item))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(walk_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def test_gate_scores_candidate_edge_support_from_fresh_news_with_stable_digest() -> None:
    pass_snapshot = snapshot(candidate_id="z-pass", market_slug="z-pass-market")
    watch_snapshot = snapshot(
        candidate_id="m-watch",
        market_slug="m-watch-market",
        latest_source_age_seconds=d("3600.000000"),
        official_update_count=d("0.000000"),
        independent_confirmation_count=d("1.000000"),
        probability_move_velocity_per_hour=d("0.080000"),
        edge_margin_probability=d("0.020000"),
        cost_drag_probability=d("0.020000"),
    )
    blocked_snapshot = snapshot(
        candidate_id="a-blocked",
        market_slug="a-blocked-market",
        latest_source_age_seconds=d("9000.000000"),
        official_update_count=d("0.000000"),
        independent_confirmation_count=d("0.000000"),
        probability_move_velocity_per_hour=d("0.150000"),
        edge_margin_probability=d("0.005000"),
        cost_drag_probability=d("0.040000"),
    )

    result = report(pass_snapshot, watch_snapshot, blocked_snapshot)
    same_result = report(blocked_snapshot, pass_snapshot, watch_snapshot)

    assert result == same_result
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-news-freshness-edge-gate-v2"
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.max_latest_source_age_seconds == d("9000.000000")
    assert result.max_probability_move_velocity_per_hour == d("0.150000")
    assert result.min_news_freshness_edge_score == d("0.033333")
    assert result.gate_status == "blocked"
    assert result.recommended_next_step == "block_candidate_until_fresh_news_supports_edge"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    int(result.derived_validation_digest, 16)

    assert tuple(row.candidate_id for row in result.rows) == (
        "a-blocked",
        "m-watch",
        "z-pass",
    )
    blocked_row, watch_row, pass_row = result.rows

    assert blocked_row.gate_status == "blocked"
    assert blocked_row.source_age_score == d("0.000000")
    assert blocked_row.official_update_presence_score == d("0.000000")
    assert blocked_row.independent_confirmation_score == d("0.000000")
    assert blocked_row.probability_move_velocity_score == d("0.000000")
    assert blocked_row.edge_margin_score == d("0.166667")
    assert blocked_row.cost_drag_score == d("0.000000")
    assert blocked_row.news_freshness_edge_score == d("0.033333")
    assert blocked_row.reason_codes == (
        "latest_source_age_above_watch_limit",
        "official_update_below_pass_minimum",
        "independent_confirmations_below_watch_minimum",
        "probability_move_velocity_above_watch_limit",
        "edge_margin_below_watch_minimum",
        "cost_drag_above_watch_limit",
        "news_freshness_edge_score_below_watch_minimum",
    )

    assert watch_row.gate_status == "watch"
    assert watch_row.source_age_score == d("0.500000")
    assert watch_row.official_update_presence_score == d("0.000000")
    assert watch_row.independent_confirmation_score == d("0.500000")
    assert watch_row.probability_move_velocity_score == d("0.333333")
    assert watch_row.edge_margin_score == d("0.666667")
    assert watch_row.cost_drag_score == d("0.333333")
    assert watch_row.news_freshness_edge_score == d("0.416667")
    assert watch_row.reason_codes == (
        "latest_source_age_above_pass_limit",
        "official_update_below_pass_minimum",
        "independent_confirmations_below_pass_minimum",
        "probability_move_velocity_above_pass_limit",
        "edge_margin_below_pass_minimum",
        "cost_drag_above_pass_limit",
        "news_freshness_edge_score_below_pass_minimum",
    )

    assert pass_row.gate_status == "pass"
    assert pass_row.news_freshness_edge_score == d("0.937500")
    assert pass_row.reason_codes == ("news_freshness_edge_supported",)
    assert len({row.derived_validation_digest for row in result.rows}) == 3


def test_public_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        snapshot(
            candidate_id="payload-candidate",
            market_slug="payload-market",
            latest_source_age_seconds=d("9000.000000"),
            official_update_count=d("0.000000"),
            independent_confirmation_count=d("0.000000"),
            probability_move_velocity_per_hour=d("0.150000"),
            edge_margin_probability=d("0.005000"),
            cost_drag_probability=d("0.040000"),
        ),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_candidate_news_freshness_edge_gate_v2_public_payload(result)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["blocked_count"] == "1.000000"
    assert payload["max_latest_source_age_seconds"] == "9000.000000"
    assert payload["min_news_freshness_edge_score"] == "0.033333"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["news_freshness_edge_score"] == "0.033333"
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "candidate_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(
            numeric_payload,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(
            missing_digest,
        )

    tampered = {**payload, "blocked_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(
            tampered,
        )

    tampered_report = replace(result)
    object.__setattr__(tampered_report, "blocked_count", d("99.000000"))
    with pytest.raises(ValueError, match="blocked_count|derived_validation_digest"):
        module.strategy_candidate_news_freshness_edge_gate_v2_public_payload(
            tampered_report,
        )


def test_empty_report_is_blocked_report_only_and_digest_bound() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.StrategyCandidateNewsFreshnessEdgeGateV2Report
    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.max_latest_source_age_seconds == ZERO
    assert empty.max_probability_move_velocity_per_hour == ZERO
    assert empty.min_news_freshness_edge_score == ZERO
    assert empty.gate_status == "blocked"
    assert empty.recommended_next_step == "block_candidate_until_fresh_news_supports_edge"
    assert empty.reason_codes == ("news_freshness_edge_gate_empty",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    for public_value in (config(), snapshot(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True


def test_validation_rejects_bad_types_flags_duplicates_time_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_news_freshness_edge_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 7, 11, 50))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 7, 11, 50, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="after generated_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate news freshness snapshot"):
        report(
            snapshot(candidate_id="dup", market_slug="dup-market"),
            snapshot(candidate_id="dup", market_slug="dup-market"),
        )
    with pytest.raises(ValueError, match="latest_source_age_seconds"):
        snapshot(latest_source_age_seconds=1)
    with pytest.raises(ValueError, match="edge_margin_probability"):
        snapshot(edge_margin_probability=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="cost_drag_probability"):
        snapshot(cost_drag_probability=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="weights"):
        config(cost_drag_weight=d("0.200000"))

    clear_report = report(snapshot(candidate_id="consistent", market_slug="consistent-market"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(clear_report, pass_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        clear_report.gate_status = "blocked"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("key", "value"),
    (
        (unsafe_text("li", "ve", "_enabled"), "not allowed"),
        (unsafe_text("au", "th", "_token"), "not allowed"),
        (unsafe_text("wal", "let", "_address"), "not allowed"),
        (unsafe_text("ord", "er", "_id"), "not allowed"),
        (unsafe_text("net", "work", "_url"), "not allowed"),
        (unsafe_text("data", "base", "_dsn"), "not allowed"),
        (unsafe_text("per", "sist", "_path"), "not allowed"),
        (unsafe_text("sig", "ning", "_key"), "not allowed"),
        (unsafe_text("mu", "tation", "_path"), "not allowed"),
        (unsafe_text("bu", "y", "_flag"), "not allowed"),
        (unsafe_text("sel", "l", "_flag"), "not allowed"),
        (unsafe_text("tra", "de", "_id"), "not allowed"),
        ("operator_note", unsafe_text("configured ", "li", "ve", " surface")),
        ("operator_note", unsafe_text("configured ", "au", "th", " surface")),
        ("operator_note", unsafe_text("configured ", "wal", "let", " surface")),
        ("operator_note", unsafe_text("configured ", "ord", "er", " surface")),
        ("operator_note", unsafe_text("configured ", "net", "work", " surface")),
        ("operator_note", unsafe_text("configured ", "data", "base", " surface")),
        ("operator_note", unsafe_text("configured ", "per", "sist", " surface")),
        ("operator_note", unsafe_text("configured ", "sig", "ning", " surface")),
        ("operator_note", unsafe_text("configured ", "mu", "tation", " surface")),
        ("operator_note", unsafe_text("configured ", "bu", "y", " surface")),
        ("operator_note", unsafe_text("configured ", "sel", "l", " surface")),
        ("operator_note", unsafe_text("configured ", "tra", "de", " surface")),
    ),
)
def test_public_payload_rejects_unsafe_public_keys_and_values(key: str, value: str) -> None:
    module = api()
    payload = module.strategy_candidate_news_freshness_edge_gate_v2_public_payload(
        report(snapshot(candidate_id="unsafe-check", market_slug="unsafe-market")),
    )

    unsafe_payload = {**payload, key: value}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload(
            unsafe_payload,
        )


def test_export_contract_decimal_fields_and_static_no_external_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_NEWS_FRESHNESS_EDGE_GATE_V2_CONFIG_VERSION",
        "StrategyCandidateNewsFreshnessEdgeGateV2Config",
        "StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount",
        "StrategyCandidateNewsFreshnessEdgeGateV2Report",
        "StrategyCandidateNewsFreshnessEdgeGateV2Row",
        "StrategyCandidateNewsFreshnessEdgeGateV2Snapshot",
        "build_strategy_candidate_news_freshness_edge_gate_v2_report",
        "strategy_candidate_news_freshness_edge_gate_v2_public_payload",
        "validate_strategy_candidate_news_freshness_edge_gate_v2_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    sample_report = report(snapshot())
    for instance in (
        config(),
        snapshot(),
        *sample_report.rows,
        sample_report,
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_seconds",
                    "_per_hour",
                    "_probability",
                    "_score",
                    "_weight",
                ),
            ):
                assert value is None or type(value) is Decimal

    payload = module.strategy_candidate_news_freshness_edge_gate_v2_public_payload(
        sample_report,
    )
    unsafe_fragments = (
        unsafe_text("li", "ve"),
        unsafe_text("au", "th"),
        unsafe_text("wal", "let"),
        unsafe_text("ord", "er"),
        unsafe_text("net", "work"),
        unsafe_text("data", "base"),
        unsafe_text("per", "sist"),
        unsafe_text("sig", "ning"),
        unsafe_text("mu", "tation"),
        unsafe_text("bu", "y"),
        unsafe_text("sel", "l"),
        unsafe_text("tra", "de"),
    )
    public_names = set(module.__all__)
    for dataclass_type in (
        module.StrategyCandidateNewsFreshnessEdgeGateV2Config,
        module.StrategyCandidateNewsFreshnessEdgeGateV2Snapshot,
        module.StrategyCandidateNewsFreshnessEdgeGateV2ReasonCodeCount,
        module.StrategyCandidateNewsFreshnessEdgeGateV2Row,
        module.StrategyCandidateNewsFreshnessEdgeGateV2Report,
    ):
        public_names.update(field.name for field in fields(dataclass_type))
    public_names.update(walk_strings(payload))
    for name in public_names:
        lowered = name.lower()
        assert all(fragment not in lowered for fragment in unsafe_fragments)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "httpx",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        ".write(",
        ".read(",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
