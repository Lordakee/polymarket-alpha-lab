import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_information_edge_score_v10"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_STRATEGY_INFORMATION_EDGE_SCORE_V10_CONFIG_VERSION,
        "max_source_freshness_hours": d("24.000000"),
        "min_source_reliability": d("0.700000"),
        "min_coverage_quorum_ratio": d("0.800000"),
        "target_forecast_dispersion": d("0.150000"),
        "target_market_staleness_hours": d("6.000000"),
        "max_resolution_ambiguity": d("0.250000"),
        "high_edge_score": d("0.750000"),
        "medium_edge_score": d("0.500000"),
        "freshness_weight": d("0.200000"),
        "reliability_weight": d("0.200000"),
        "coverage_quorum_weight": d("0.150000"),
        "forecast_dispersion_weight": d("0.150000"),
        "market_staleness_weight": d("0.200000"),
        "resolution_clarity_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyInformationEdgeScoreV10Config(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "market_slug": "fed-july-rate-above-four",
        "event_slug": "fed-july-policy-path",
        "source_observed_at": OBSERVED_AT,
        "source_freshness_hours": d("1.500000"),
        "source_reliability": d("0.920000"),
        "coverage_source_count": d("5"),
        "required_coverage_source_count": d("5"),
        "forecast_dispersion": d("0.180000"),
        "market_staleness_hours": d("9.000000"),
        "resolution_ambiguity": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyInformationEdgeScoreV10Input(**values)


def score(
    item: Any | None = None,
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.score_strategy_information_edge_v10(
        item or signal(),
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_no_runtime_numeric_or_datetime(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, (Decimal, datetime))
    if isinstance(value, dict):
        for child in value.values():
            assert_no_runtime_numeric_or_datetime(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_runtime_numeric_or_datetime(child)


def payload_with_matching_digest(
    payload: dict[str, Any],
    **overrides: object,
) -> dict[str, Any]:
    tampered = {**payload, **overrides}
    digest_values = {
        key: value
        for key, value in tampered.items()
        if key != "derived_validation_digest"
    }
    tampered["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            digest_values,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return tampered


def test_scores_high_information_edge_from_fresh_reliable_quorum_inputs() -> None:
    module = api()

    result = score(
        signal(
            source_observed_at=datetime(
                2026,
                7,
                6,
                7,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(result, module.StrategyInformationEdgeScoreV10Report)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.config_version == "strategy-information-edge-score-v10"
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.source_observed_at == OBSERVED_AT
    assert result.source_observed_at.tzinfo is UTC
    assert result.source_freshness_score == d("0.937500")
    assert result.source_reliability_score == d("0.920000")
    assert result.coverage_quorum_ratio == d("1.000000")
    assert result.coverage_quorum_score == d("1.000000")
    assert result.forecast_dispersion_score == d("1.000000")
    assert result.market_staleness_score == d("1.000000")
    assert result.resolution_clarity_score == d("0.900000")
    assert result.edge_score == d("0.961500")
    assert result.edge_tier == "high"
    assert result.research_priority == "urgent"
    assert result.reason_codes == (
        "coverage_quorum_met",
        "forecast_dispersion_material",
        "information_edge_high",
        "market_stale",
        "resolution_clear",
        "source_fresh",
        "source_reliable",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_blocks_score_when_quorum_reliability_and_resolution_are_weak() -> None:
    result = score(
        signal(
            source_freshness_hours=d("36.000000"),
            source_reliability=d("0.450000"),
            coverage_source_count=d("1"),
            required_coverage_source_count=d("5"),
            forecast_dispersion=d("0.020000"),
            market_staleness_hours=d("0.500000"),
            resolution_ambiguity=d("0.550000"),
        ),
    )

    assert result.edge_tier == "blocked"
    assert result.research_priority == "blocked"
    assert result.edge_score == d("0.201667")
    assert result.reason_codes == (
        "coverage_quorum_missed",
        "forecast_dispersion_thin",
        "information_edge_blocked",
        "market_recent",
        "resolution_ambiguity_high",
        "source_aging",
        "source_reliability_low",
    )


def test_source_freshness_threshold_is_aging_boundary() -> None:
    result = score(signal(source_freshness_hours=d("24.000000")))

    assert result.source_freshness_score == d("0.000000")
    assert "source_aging" in result.reason_codes
    assert "source_fresh" not in result.reason_codes


def test_payload_is_json_ready_decimal_only_and_dict_path_is_guarded() -> None:
    module = api()
    result = score()

    payload = module.strategy_information_edge_score_v10_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["source_observed_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["edge_score"] == "0.961500"
    assert payload["coverage_source_count"] == "5"
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert not any(character.isdigit() for character in result.research_priority)
    assert not any(fragment in encoded.lower() for fragment in ("api_key=secret", "token=secret"))
    assert_no_runtime_numeric_or_datetime(payload)
    assert module.strategy_information_edge_score_v10_payload(payload) == payload

    with pytest.raises(ValueError, match="payload fields must match"):
        module.strategy_information_edge_score_v10_payload(
            {key: value for key, value in payload.items() if key != "edge_score"},
        )
    with pytest.raises(ValueError, match="payload fields must match"):
        module.strategy_information_edge_score_v10_payload({**payload, "public_note": "ok"})
    with pytest.raises(ValueError, match="payload derived validation failed"):
        module.strategy_information_edge_score_v10_payload(
            {**payload, "edge_score": "0.950000"},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_information_edge_score_v10_payload({**payload, "readonly": False})
    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_information_edge_score_v10_payload({**payload, "edge_score": 1})
    with pytest.raises(ValueError, match="float"):
        module.strategy_information_edge_score_v10_payload({**payload, "edge_score": 0.5})
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_information_edge_score_v10_payload({**payload, "auth": "off"})
    with pytest.raises(ValueError, match="sensitive|unsafe"):
        module.strategy_information_edge_score_v10_payload(
            {**payload, "market_slug": "https://example.test/feed?token=secret"},
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.strategy_information_edge_score_v10_payload(
            {**payload, "generated_at": datetime(2026, 7, 6, 12, 0)},
        )


def test_payload_rejects_live_auth_wallet_order_network_database_persist_surfaces() -> None:
    module = api()
    payload = module.strategy_information_edge_score_v10_payload(score())

    for field_name in (
        "live_mode",
        "auth_context",
        "wallet_address",
        "order_id",
        "network_endpoint",
        "database_url",
        "persist_path",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_information_edge_score_v10_payload(
                {**payload, field_name: "redacted"},
            )

    for unsafe_value in (
        "enable live mode",
        "auth context attached",
        "wallet address attached",
        "order submission attached",
        "network endpoint attached",
        "database path attached",
        "persist report output",
    ):
        with pytest.raises(ValueError, match="sensitive|unsafe"):
            module.strategy_information_edge_score_v10_payload(
                {**payload, "market_slug": unsafe_value},
            )


def test_payload_decimal_fields_must_remain_decimal_strings_even_with_valid_digest() -> None:
    module = api()
    payload = module.strategy_information_edge_score_v10_payload(score())

    with pytest.raises(ValueError, match="Decimal-string"):
        module.strategy_information_edge_score_v10_payload(
            {**payload, "edge_score": d("0.961500")},
        )

    for field_name, unsafe_value in (
        ("edge_score", "not-a-decimal"),
        ("edge_score", "0.9615000"),
        ("coverage_source_count", "5.500000"),
    ):
        with pytest.raises(ValueError, match="Decimal-string|precision|count"):
            module.strategy_information_edge_score_v10_payload(
                payload_with_matching_digest(payload, **{field_name: unsafe_value}),
            )


def test_inputs_config_and_report_validate_decimal_time_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        signal(source_reliability=1)
    with pytest.raises(ValueError, match="source_reliability must be exactly Decimal"):
        signal(source_reliability=_DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="source_reliability must be between zero and one"):
        signal(source_reliability=d("1.100000"))
    with pytest.raises(ValueError, match="coverage_source_count must be nonnegative"):
        signal(coverage_source_count=d("-1"))
    with pytest.raises(ValueError, match="required_coverage_source_count must be above zero"):
        signal(required_coverage_source_count=d("0"))
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        signal(source_observed_at=datetime(2026, 7, 6, 11, 30))
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        signal(source_observed_at=datetime(2026, 7, 6, 11, 30, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="config weights must sum to 1.000000"):
        config(freshness_weight=d("0.300000"))
    with pytest.raises(ValueError, match="high_edge_score must be at least medium_edge_score"):
        config(high_edge_score=d("0.400000"))
    with pytest.raises(ValueError, match="input paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        score(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))

    result = score()
    with pytest.raises(FrozenInstanceError):
        result.edge_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="report reason_codes must match"):
        module.StrategyInformationEdgeScoreV10Report(
            **{**result.__dict__, "reason_codes": ("source_fresh",)},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyInformationEdgeScoreV10Report(
            **{**result.__dict__, "edge_score": d("0.950000")},
        )
    with pytest.raises(ValueError, match="report derived validation failed"):
        module.StrategyInformationEdgeScoreV10Report(
            **{**result.__dict__, "coverage_quorum_score": d("0.900000")},
        )
    with pytest.raises(ValueError, match="report readonly must be True"):
        module.StrategyInformationEdgeScoreV10Report(
            **{**result.__dict__, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyInformationEdgeScoreV10Report(
            **{**result.__dict__, "edge_score": d("0.950000"), "derived_validation_digest": ""},
        )


def test_module_is_readonly_paper_report_only_with_no_io_or_execution_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_information_edge_score_v10.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "open",
        "connect",
        "cancel",
        "replace",
        "wallet",
        "order",
        "create_order",
        "place_order",
        "submit_order",
        "trade",
        "auth",
        "login",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "trade",
        "execute",
        "database",
        "durable file",
        "supabase",
        "live",
        "network",
        "persist",
        "requests",
        "httpx",
        "socket",
        "subprocess",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
