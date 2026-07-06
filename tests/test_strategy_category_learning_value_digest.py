from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_category_learning_value_digest"
GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 14, 30, tzinfo=UTC)
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


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CATEGORY_LEARNING_VALUE_DIGEST_CONFIG_VERSION
        ),
        "target_resolved_sample_count": d("10"),
        "min_resolved_sample_count": d("3"),
        "target_forecast_error_reduction": d("0.050000"),
        "target_source_reliability_improvement": d("0.100000"),
        "min_event_archetype_coverage_ratio": d("0.500000"),
        "max_calibration_backlog": d("5"),
        "min_capital_efficiency": d("0.100000"),
        "pass_learning_value_score": d("0.700000"),
        "watch_learning_value_score": d("0.400000"),
    }
    values.update(overrides)
    return module.StrategyCategoryLearningValueDigestConfig(**values)


def category(**overrides: object) -> Any:
    module = api()
    values = {
        "category": "macro",
        "sample_observed_at": OBSERVED_AT,
        "resolved_sample_count": d("8"),
        "previous_forecast_error": d("0.150000"),
        "current_forecast_error": d("0.130000"),
        "previous_source_reliability": d("0.500000"),
        "current_source_reliability": d("0.560000"),
        "covered_event_archetype_count": d("3"),
        "required_event_archetype_count": d("5"),
        "calibration_backlog": d("2"),
        "capital_efficiency": d("0.500000"),
        "learning_reference": "plain-ticket",
    }
    values.update(overrides)
    return module.StrategyCategoryLearningValueInput(**values)


def digest(*rows: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_category_learning_value_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_ranks_categories_by_paper_learning_value() -> None:
    result = digest(
        category(
            category="crypto",
            resolved_sample_count=d("2"),
            previous_forecast_error=d("0.100000"),
            current_forecast_error=d("0.140000"),
            previous_source_reliability=d("0.700000"),
            current_source_reliability=d("0.650000"),
            covered_event_archetype_count=d("1"),
            required_event_archetype_count=d("4"),
            calibration_backlog=d("7"),
            capital_efficiency=d("0.050000"),
            learning_reference="wallet://private-key",
        ),
        category(
            category="sports",
            resolved_sample_count=d("12"),
            previous_forecast_error=d("0.180000"),
            current_forecast_error=d("0.110000"),
            previous_source_reliability=d("0.500000"),
            current_source_reliability=d("0.650000"),
            covered_event_archetype_count=d("5"),
            required_event_archetype_count=d("5"),
            calibration_backlog=d("1"),
            capital_efficiency=d("0.900000"),
            learning_reference="https://example.test/feed?token=secret",
        ),
        category(),
    )

    assert is_dataclass(result)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-category-learning-value-digest-v0"
    assert result.category_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.top_category == "sports"
    assert result.max_learning_value_score == d("0.970000")
    assert result.min_learning_value_score == d("0.082500")
    assert result.average_learning_value_score == d("0.544167")
    assert result.digest_status == "watch"
    assert result.reason_codes == (
        "calibration_backlog_high",
        "capital_efficiency_low",
        "event_archetype_coverage_low",
        "forecast_error_reduction_low",
        "learning_value_blocked",
        "learning_value_pass",
        "learning_value_watch",
        "resolved_sample_count_low",
        "source_reliability_improvement_low",
    )
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.category for row in result.rows) == ("sports", "macro", "crypto")
    top = result.rows[0]
    assert top.rank == d("1")
    assert top.resolved_sample_score == d("1.000000")
    assert top.forecast_error_reduction == d("0.070000")
    assert top.forecast_error_reduction_score == d("1.000000")
    assert top.source_reliability_improvement == d("0.150000")
    assert top.source_reliability_improvement_score == d("1.000000")
    assert top.event_archetype_coverage_ratio == d("1.000000")
    assert top.calibration_backlog_score == d("0.800000")
    assert top.capital_efficiency == d("0.900000")
    assert top.learning_value_score == d("0.970000")
    assert top.learning_value_status == "pass"
    assert top.redacted_learning_reference == "<redacted>"
    assert top.reason_codes == ("learning_value_pass",)

    middle = result.rows[1]
    assert middle.rank == d("2")
    assert middle.category == "macro"
    assert middle.learning_value_score == d("0.580000")
    assert middle.learning_value_status == "watch"
    assert middle.redacted_learning_reference == "plain-ticket"
    assert middle.reason_codes == (
        "forecast_error_reduction_low",
        "learning_value_watch",
        "resolved_sample_count_low",
        "source_reliability_improvement_low",
    )

    blocked = result.rows[2]
    assert blocked.rank == d("3")
    assert blocked.category == "crypto"
    assert blocked.forecast_error_reduction == ZERO
    assert blocked.source_reliability_improvement == ZERO
    assert blocked.event_archetype_coverage_ratio == d("0.250000")
    assert blocked.calibration_backlog_score == ZERO
    assert blocked.learning_value_score == d("0.082500")
    assert blocked.learning_value_status == "blocked"
    assert blocked.reason_codes == (
        "calibration_backlog_high",
        "capital_efficiency_low",
        "event_archetype_coverage_low",
        "forecast_error_reduction_low",
        "learning_value_blocked",
        "resolved_sample_count_low",
        "source_reliability_improvement_low",
    )


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    result = digest()

    assert result.category_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.top_category is None
    assert result.max_learning_value_score == ZERO
    assert result.min_learning_value_score == ZERO
    assert result.average_learning_value_score == ZERO
    assert result.digest_status == "blocked"
    assert result.reason_codes == ("strategy_category_learning_value_digest_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_payload_is_json_ready_decimal_stringed_and_redacted() -> None:
    module = api()
    result = digest(
        category(learning_reference="https://example.test/private?api_key=secret"),
        generated_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_category_learning_value_digest_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["category_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["learning_value_score"] == "0.580000"
    assert payload["rows"][0]["redacted_learning_reference"] == "<redacted>"
    assert "api_key=secret" not in encoded
    assert "learning_reference" not in payload["rows"][0]
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_values(payload)


def test_payload_dict_path_enforces_phase1_boundaries() -> None:
    module = api()
    payload = module.strategy_category_learning_value_digest_payload(
        digest(category(learning_reference="plain-ticket")),
    )

    assert module.strategy_category_learning_value_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_category_learning_value_digest_payload({**payload, "readonly": False})

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_category_learning_value_digest_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="unsafe|sensitive"):
        module.strategy_category_learning_value_digest_payload(
            {**payload, "learning_reference": "https://example.test/feed?token=secret"},
        )

    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_category_learning_value_digest_payload({**payload, "category_count": 1})

    with pytest.raises(ValueError, match="float"):
        module.strategy_category_learning_value_digest_payload(
            {**payload, "average_learning_value_score": 0.58},
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        module.strategy_category_learning_value_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 3, 15, 0)},
        )

    with pytest.raises(ValueError, match="JSON object keys"):
        module.strategy_category_learning_value_digest_payload({1: "x", **payload})


def test_payload_exposes_and_revalidates_tamper_evident_derived_digests() -> None:
    module = api()
    result = digest(category(learning_reference="plain-ticket"))

    assert re.fullmatch(r"[0-9a-f]{64}", result.validation_digest)
    assert re.fullmatch(r"[0-9a-f]{64}", result.rows[0].validation_digest)
    payload = module.strategy_category_learning_value_digest_payload(result)
    assert payload["validation_digest"] == result.validation_digest
    assert payload["rows"][0]["validation_digest"] == result.rows[0].validation_digest

    tampered_row_report = digest(category(learning_reference="plain-ticket"))
    object.__setattr__(
        tampered_row_report.rows[0],
        "redacted_learning_reference",
        "plain-ticket-tampered",
    )
    with pytest.raises(ValueError, match="validation_digest must match row"):
        module.strategy_category_learning_value_digest_payload(tampered_row_report)

    tampered_report = digest(category(learning_reference="plain-ticket"))
    object.__setattr__(tampered_report, "validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="validation_digest must match report"):
        module.strategy_category_learning_value_digest_payload(tampered_report)


def test_payload_dict_path_rejects_missing_or_tampered_validation_digests() -> None:
    module = api()
    payload = module.strategy_category_learning_value_digest_payload(
        digest(category(learning_reference="plain-ticket")),
    )

    missing_report_digest = dict(payload)
    del missing_report_digest["validation_digest"]
    with pytest.raises(ValueError, match="validation_digest"):
        module.strategy_category_learning_value_digest_payload(missing_report_digest)

    missing_row_digest = {
        **payload,
        "rows": [dict(payload["rows"][0])],
    }
    del missing_row_digest["rows"][0]["validation_digest"]
    with pytest.raises(ValueError, match="validation_digest"):
        module.strategy_category_learning_value_digest_payload(missing_row_digest)

    tampered_count = {**payload, "category_count": "2"}
    with pytest.raises(ValueError, match="validation_digest must match payload"):
        module.strategy_category_learning_value_digest_payload(tampered_count)

    tampered_row = {
        **payload,
        "rows": [{**payload["rows"][0], "redacted_learning_reference": "other-ticket"}],
    }
    with pytest.raises(ValueError, match="validation_digest must match payload row"):
        module.strategy_category_learning_value_digest_payload(tampered_row)

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_category_learning_value_digest_payload(
            {**payload, "api_key": "public"},
        )


def test_inputs_and_config_reject_non_decimal_subclasses_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="resolved_sample_count must be a Decimal"):
        category(resolved_sample_count=8)
    with pytest.raises(ValueError, match="resolved_sample_count must be exactly Decimal"):
        category(resolved_sample_count=_DecimalSubclass("8"))
    with pytest.raises(ValueError, match="category must be a nonblank trimmed string"):
        category(category=_StringSubclass("macro"))
    with pytest.raises(ValueError, match="required_event_archetype_count must be above zero"):
        category(required_event_archetype_count=ZERO)
    with pytest.raises(ValueError, match="capital_efficiency must be between zero and one"):
        category(capital_efficiency=d("1.100000"))
    with pytest.raises(ValueError, match="sample_observed_at must be timezone-aware"):
        category(sample_observed_at=datetime(2026, 7, 3, 14, 30))
    with pytest.raises(ValueError, match="sample_observed_at must be timezone-aware"):
        category(
            sample_observed_at=datetime(
                2026,
                7,
                3,
                14,
                30,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        category(paper_only=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_category_learning_value_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_dataclasses_are_frozen_and_datetimes_normalize_to_utc() -> None:
    result = digest(
        category(sample_observed_at=datetime(2026, 7, 3, 10, 30, tzinfo=timezone(timedelta(hours=-4)))),
        generated_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.rows[0].sample_observed_at == OBSERVED_AT
    assert result.rows[0].sample_observed_at.tzinfo is UTC
    assert result.rows[0].paper_only is True
    assert result.rows[0].report_only is True
    assert result.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        result.rows[0].rank = d("99")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest(category(), generated_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="digest report must contain exact rows"):
        replace(result, rows=(object(),))


def test_module_is_pure_report_only_and_contains_no_io_or_trading_behavior() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_category_learning_value_digest.py")
    tree = ast.parse(path.read_text())

    banned_imports = {
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "psycopg",
    }
    banned_names = {
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
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_names


def test_static_forbidden_surface_terms_are_absent_from_digest_source() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_category_learning_value_digest.py",
    ).read_text(encoding="utf-8").lower()

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
        "supabase",
    )

    assert [term for term in forbidden_terms if term in source] == []
