from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-baseball-bullpen-back-to-back-digest-test-v0"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_baseball_bullpen_back_to_back_digest.py"
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_bullpen_back_to_back_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "max_observation_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_confirmation_ratio": d("0.666667"),
        "max_back_to_back_rest_hours": d("24.000000"),
        "watch_bullpen_innings_last_game": d("3.000000"),
        "high_bullpen_innings_last_game": d("4.500000"),
        "high_bullpen_innings_last_2_days": d("7.000000"),
        "watch_high_leverage_pitch_count": d("35.000000"),
        "high_high_leverage_pitch_count": d("55.000000"),
        "watch_reliever_back_to_back_count": d("2.000000"),
        "watch_unavailable_reliever_count": d("1.000000"),
        "confidence_decay_per_stale_observation": d("0.150000"),
        "confidence_decay_per_source_gap": d("0.100000"),
        "confidence_decay_per_source_diversity_gap": d("0.080000"),
        "confidence_decay_per_confirmation_gap": d("0.100000"),
        "confidence_decay_per_conflicting_sources": d("0.120000"),
        "confidence_decay_per_back_to_back_game": d("0.050000"),
        "confidence_decay_per_heavy_bullpen_workload": d("0.100000"),
        "confidence_decay_per_leverage_pitch_spike": d("0.080000"),
        "confidence_decay_per_reliever_reuse_pressure": d("0.070000"),
        "confidence_decay_per_bullpen_availability_gap": d("0.100000"),
    }
    values.update(overrides)
    return module.MarketResearchBaseballBullpenBackToBackDigestConfig(**values)


def observation(
    research_key: str = "research.mlb.mets.bullpen",
    *,
    condition_id: str = "condition.mlb.mets.braves.bullpen",
    game_id: str = "mlb.mets.braves.20260704",
    team_key: str = "mets",
    market_id: str = "mets-braves-moneyline",
    public_source_reference: str = "mlb-official-bullpen-usage-report",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    source_count: object = "3.000000",
    independent_source_count: object = "3.000000",
    confirming_source_count: object = "3.000000",
    conflicting_source_count: object = "0.000000",
    rest_hours_since_last_game: object = "48.000000",
    bullpen_innings_last_game: object = "1.200000",
    bullpen_innings_last_2_days: object = "2.400000",
    high_leverage_pitch_count_last_game: object = "12.000000",
    reliever_back_to_back_count: object = "0.000000",
    unavailable_reliever_count: object = "0.000000",
    base_confidence_score: object = "0.840000",
    source_config_version: str = "baseball-bullpen-usage-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchBaseballBullpenBackToBackDigestObservation(
        research_key=research_key,
        condition_id=condition_id,
        game_id=game_id,
        team_key=team_key,
        market_id=market_id,
        public_source_reference=public_source_reference,
        observed_at=observed_at,
        source_count=_maybe_decimal(source_count),
        independent_source_count=_maybe_decimal(independent_source_count),
        confirming_source_count=_maybe_decimal(confirming_source_count),
        conflicting_source_count=_maybe_decimal(conflicting_source_count),
        rest_hours_since_last_game=_maybe_decimal(rest_hours_since_last_game),
        bullpen_innings_last_game=_maybe_decimal(bullpen_innings_last_game),
        bullpen_innings_last_2_days=_maybe_decimal(bullpen_innings_last_2_days),
        high_leverage_pitch_count_last_game=_maybe_decimal(
            high_leverage_pitch_count_last_game,
        ),
        reliever_back_to_back_count=_maybe_decimal(reliever_back_to_back_count),
        unavailable_reliever_count=_maybe_decimal(unavailable_reliever_count),
        base_confidence_score=_maybe_decimal(base_confidence_score),
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_baseball_bullpen_back_to_back_digest(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def _maybe_decimal(value: object) -> object:
    if type(value) is str:
        return d(value)
    return value


def test_digest_flags_bullpen_back_to_back_fatigue_risk_for_screening() -> None:
    raw_reference = "bullpen-feed://primary?api_key=secret-token"
    report = build_report(
        observation(
            "research.mlb.redsox.bullpen",
            condition_id="condition.mlb.redsox.yankees.bullpen",
            game_id="mlb.redsox.yankees.20260704",
            team_key="redsox",
            market_id="red-sox-yankees-moneyline",
            public_source_reference=raw_reference,
            observed_at=GENERATED_AT - timedelta(minutes=20),
            rest_hours_since_last_game="19.000000",
            bullpen_innings_last_game="5.100000",
            bullpen_innings_last_2_days="8.200000",
            high_leverage_pitch_count_last_game="64.000000",
            reliever_back_to_back_count="3.000000",
            unavailable_reliever_count="2.000000",
            base_confidence_score="0.900000",
            source_config_version="bullpen-usage-feed-v1",
        ),
        observation(
            "research.mlb.dodgers.bullpen",
            condition_id="condition.mlb.dodgers.giants.bullpen",
            game_id="mlb.dodgers.giants.20260704",
            team_key="dodgers",
            market_id="dodgers-giants-moneyline",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            rest_hours_since_last_game="22.000000",
            bullpen_innings_last_game="3.300000",
            bullpen_innings_last_2_days="5.500000",
            high_leverage_pitch_count_last_game="38.000000",
            base_confidence_score="0.760000",
        ),
        observation(
            observed_at=datetime(
                2026,
                7,
                4,
                13,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    module = api()
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_baseball_bullpen_back_to_back_digest"
    )
    assert report.observation_count == d("3.000000")
    assert report.clear_observation_count == d("1.000000")
    assert report.watch_observation_count == d("1.000000")
    assert report.high_risk_observation_count == d("1.000000")
    assert report.blocked_observation_count == d("0.000000")
    assert report.back_to_back_game_count == d("2.000000")
    assert report.heavy_bullpen_workload_count == d("2.000000")
    assert report.leverage_pitch_spike_count == d("2.000000")
    assert report.reliever_reuse_pressure_count == d("1.000000")
    assert report.bullpen_availability_gap_count == d("1.000000")
    assert report.average_confidence_score == d("0.623333")
    assert report.max_observation_age_seconds == d("2700.000000")
    assert report.min_rest_hours_since_last_game == d("19.000000")
    assert report.max_bullpen_innings_last_2_days == d("8.200000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.fatigue_status, row.game_id, row.team_key) for row in report.rows) == (
        ("high_risk", "mlb.redsox.yankees.20260704", "redsox"),
        ("watch", "mlb.dodgers.giants.20260704", "dodgers"),
        ("clear", "mlb.mets.braves.20260704", "mets"),
    )

    high_risk = report.rows[0]
    assert high_risk.observation_age_seconds == d("1200.000000")
    assert high_risk.source_confirmation_ratio == d("1.000000")
    assert high_risk.source_diversity_ratio == d("1.000000")
    assert high_risk.back_to_back_game_flag is True
    assert high_risk.heavy_bullpen_workload_flag is True
    assert high_risk.confidence_decay_score == d("0.400000")
    assert high_risk.confidence_score == d("0.500000")
    assert high_risk.redacted_public_source_reference == (
        "sha256:" + sha256(raw_reference.encode()).hexdigest()[:12]
    )
    assert high_risk.reason_codes == (
        "market_research_baseball_bullpen_back_to_back_digest_back_to_back_game",
        "market_research_baseball_bullpen_back_to_back_digest_bullpen_availability_gap",
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_high_risk",
        "market_research_baseball_bullpen_back_to_back_digest_heavy_bullpen_workload",
        "market_research_baseball_bullpen_back_to_back_digest_leverage_pitch_spike",
        "market_research_baseball_bullpen_back_to_back_digest_reliever_reuse_pressure",
    )

    watched = report.rows[1]
    assert watched.fatigue_status == "watch"
    assert watched.confidence_score == d("0.530000")
    assert watched.reason_codes == (
        "market_research_baseball_bullpen_back_to_back_digest_back_to_back_game",
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_watch",
        "market_research_baseball_bullpen_back_to_back_digest_heavy_bullpen_workload",
        "market_research_baseball_bullpen_back_to_back_digest_leverage_pitch_spike",
    )

    clear = report.rows[2]
    assert clear.fatigue_status == "clear"
    assert clear.observed_at == datetime(2026, 7, 4, 17, 45, tzinfo=UTC)
    assert clear.confidence_score == d("0.840000")
    assert clear.reason_codes == (
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_clear",
    )

    assert report.reason_codes == (
        "market_research_baseball_bullpen_back_to_back_digest_back_to_back_game",
        "market_research_baseball_bullpen_back_to_back_digest_bullpen_availability_gap",
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_clear",
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_high_risk",
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_watch",
        "market_research_baseball_bullpen_back_to_back_digest_heavy_bullpen_workload",
        "market_research_baseball_bullpen_back_to_back_digest_leverage_pitch_spike",
        "market_research_baseball_bullpen_back_to_back_digest_reliever_reuse_pressure",
    )
    assert report.reason_code_counts[0] == (
        module.MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount(
            reason_code=(
                "market_research_baseball_bullpen_back_to_back_digest_back_to_back_game"
            ),
            observation_count=d("2.000000"),
            observation_ratio=d("0.666667"),
        )
    )
    assert report.source_config_versions == (
        ("dodgers", "baseball-bullpen-usage-source-v0"),
        ("mets", "baseball-bullpen-usage-source-v0"),
        ("redsox", "bullpen-usage-feed-v1"),
    )


def test_empty_input_returns_pure_report_only_zero_payload() -> None:
    module = api()
    report = build_report()
    payload = module.market_research_baseball_bullpen_back_to_back_digest_payload(report)

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_baseball_bullpen_back_to_back_digest"
    )
    assert report.reason_codes == (
        "market_research_baseball_bullpen_back_to_back_digest_no_inputs",
    )
    assert report.observation_count == d("0.000000")
    assert report.clear_observation_count == d("0.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.high_risk_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("0.000000")
    assert report.max_observation_age_seconds == d("0.000000")
    assert report.min_rest_hours_since_last_game == d("0.000000")
    assert report.max_bullpen_innings_last_2_days == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == (
        module.MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount(
            reason_code="market_research_baseball_bullpen_back_to_back_digest_no_inputs",
            observation_count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["observation_count"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_or_int_paths(payload) == ()


def test_deterministic_output_and_non_default_thresholds_reclassify_risk() -> None:
    module = api()
    strict_cfg = config(
        high_bullpen_innings_last_game=d("6.000000"),
        high_bullpen_innings_last_2_days=d("9.000000"),
        watch_high_leverage_pitch_count=d("45.000000"),
        high_high_leverage_pitch_count=d("70.000000"),
        watch_reliever_back_to_back_count=d("4.000000"),
        watch_unavailable_reliever_count=d("3.000000"),
    )
    rows = (
        observation(
            "research.mlb.redsox.bullpen",
            condition_id="condition.mlb.redsox.yankees.bullpen",
            game_id="mlb.redsox.yankees.20260704",
            team_key="redsox",
            market_id="red-sox-yankees-moneyline",
            rest_hours_since_last_game="19.000000",
            bullpen_innings_last_game="5.100000",
            bullpen_innings_last_2_days="8.200000",
            high_leverage_pitch_count_last_game="64.000000",
            reliever_back_to_back_count="3.000000",
            unavailable_reliever_count="2.000000",
        ),
        observation(),
    )

    first = build_report(*rows, cfg=strict_cfg)
    second = build_report(*reversed(rows), cfg=strict_cfg)

    assert first == second
    assert module.market_research_baseball_bullpen_back_to_back_digest_payload(
        first,
    ) == module.market_research_baseball_bullpen_back_to_back_digest_payload(second)
    assert first.digest_status == "watch"
    assert first.high_risk_observation_count == d("0.000000")
    assert first.watch_observation_count == d("1.000000")
    assert tuple(row.fatigue_status for row in first.rows) == ("watch", "clear")
    assert first.rows[0].reason_codes == (
        "market_research_baseball_bullpen_back_to_back_digest_back_to_back_game",
        "market_research_baseball_bullpen_back_to_back_digest_fatigue_watch",
        "market_research_baseball_bullpen_back_to_back_digest_heavy_bullpen_workload",
        "market_research_baseball_bullpen_back_to_back_digest_leverage_pitch_spike",
    )


def test_validation_frozen_dataclasses_utc_decimals_and_hard_flags() -> None:
    cfg = config()
    with pytest.raises(FrozenInstanceError):
        cfg.max_back_to_back_rest_hours = d("25.000000")  # type: ignore[misc]

    for kwargs, message in (
        ({"max_observation_age_seconds": 3600}, "max_observation_age_seconds"),
        ({"min_source_count": d("0.500000")}, "min_source_count"),
        (
            {"watch_bullpen_innings_last_game": _DecimalSubclass("3.000000")},
            "watch_bullpen_innings_last_game",
        ),
        ({"confidence_decay_per_source_gap": d("1.100000")}, "source_gap"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ):
        with pytest.raises(ValueError, match=message):
            config(**kwargs)

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=3)
    with pytest.raises(ValueError, match="bullpen_innings_last_game must be a Decimal"):
        observation(bullpen_innings_last_game=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="base_confidence_score must be a Decimal"):
        observation(base_confidence_score=d("NaN"))
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="confirming_source_count must not exceed source_count"):
        observation(
            source_count="2.000000",
            independent_source_count="2.000000",
            confirming_source_count="3.000000",
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate research_key"):
        build_report(observation(), observation(game_id="other-game"))
    with pytest.raises(ValueError, match="config must be a"):
        build_report(observation(), cfg=object())
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].team_key = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_static_module_scope_is_report_only_readonly_and_decimal_public_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "live_trading",
        "wallet",
        "broker",
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
        "socket",
        "subprocess",
        "open(",
        "pathlib",
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

    for name in module.__all__:
        value = getattr(module, name)
        if is_dataclass(value):
            assert value.__dataclass_params__.frozen is True

    report = build_report(observation())
    for value in _walk_dataclasses(report):
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float_or_int(hint)
        for field in fields(value):
            if _is_public_numeric(field.name):
                assert type(getattr(value, field.name)) is Decimal


def test_payload_is_deterministic_json_ready_and_does_not_leak_sensitive_references() -> None:
    module = api()
    raw_reference = "bullpen-feed://primary?api_key=secret-token"
    report = build_report(
        observation(
            "research.mlb.redsox.bullpen",
            condition_id="condition.mlb.redsox.yankees.bullpen",
            game_id="mlb.redsox.yankees.20260704",
            team_key="redsox",
            market_id="red-sox-yankees-moneyline",
            public_source_reference=raw_reference,
            rest_hours_since_last_game="19.000000",
            bullpen_innings_last_game="5.100000",
            bullpen_innings_last_2_days="8.200000",
            high_leverage_pitch_count_last_game="64.000000",
            reliever_back_to_back_count="3.000000",
            unavailable_reliever_count="2.000000",
        ),
    )

    payload = module.market_research_baseball_bullpen_back_to_back_digest_payload(report)

    assert payload == module.market_research_baseball_bullpen_back_to_back_digest_payload(
        report,
    )
    assert payload["rows"][0]["public_source_reference"] == (
        "sha256:" + sha256(raw_reference.encode()).hexdigest()[:12]
    )
    assert payload["rows"][0]["confidence_score"] == "0.440000"
    assert _float_or_int_paths(payload) == ()
    json.dumps(payload, allow_nan=False, sort_keys=True)

    payload_text = repr(payload).lower()
    for unsafe_fragment in (
        "api_key",
        "secret",
        "token",
        "wallet",
        "private",
        "place_order",
        "cancel_order",
        "trade",
        "buy",
        "sell",
    ):
        assert unsafe_fragment not in payload_text


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
        or field_name.endswith("_hours")
        or field_name.endswith("_innings")
        or field_name.endswith("_seconds")
        or field_name.endswith("_score")
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
