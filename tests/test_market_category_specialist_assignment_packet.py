from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_category_specialist_assignment_packet"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "category_label": "finance.crypto.btc",
        "category_confidence": d("0.920000"),
        "keyword_confidence": d("0.650000"),
        "freshness_score": d("0.700000"),
        "observed_at": GENERATED_AT - timedelta(minutes=5),
    }
    values.update(overrides)
    return module.MarketCategorySpecialistAssignmentSignal(**values)


def packet(*signals: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_category_specialist_assignment_packet(
        signals,
        generated_at=generated_at,
    )


def assert_decimal_only_dataclass(value: object) -> None:
    for item in fields(value):
        field_value = getattr(value, item.name)
        if type(field_value) in (bool, str, datetime, tuple, dict) or field_value is None:
            continue
        assert type(field_value) is Decimal


def assert_no_json_numeric_values(value: object) -> None:
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise AssertionError(f"payload contains JSON numeric value {value!r}")
    if type(value) is dict:
        for key, item in value.items():
            assert type(key) is str
            assert_no_json_numeric_values(item)
    elif type(value) is list:
        for item in value:
            assert_no_json_numeric_values(item)


def test_assigns_primary_and_secondary_specialists_from_sanitized_category_signals() -> None:
    result = packet(
        signal(
            category_label="finance.crypto.btc",
            category_confidence=d("0.940000"),
            keyword_confidence=d("0.700000"),
            freshness_score=d("0.900000"),
        ),
        signal(
            category_label="politics",
            category_confidence=d("0.820000"),
            keyword_confidence=d("0.500000"),
            freshness_score=d("0.750000"),
        ),
        signal(
            category_label="finance.equity.indices",
            category_confidence=d("0.780000"),
            keyword_confidence=d("0.620000"),
            freshness_score=d("0.650000"),
        ),
        signal(
            category_label="finance.commodities.gold",
            category_confidence=d("0.700000"),
            keyword_confidence=d("0.600000"),
            freshness_score=d("0.700000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "market-category-specialist-assignment-packet-v1"
    assert result.assignment_status == "pass"
    assert result.primary_team_id == "crypto_btc"
    assert result.secondary_team_ids == ("politics", "equity_index", "commodities_gold")
    assert result.team_count == d("4")
    assert result.block_count == d("0")
    assert result.watch_count == d("0")
    assert result.pass_count == d("4")
    assert result.top_assignment_score == d("0.874000")
    assert result.reason_codes == ("primary_assignment_selected", "secondary_assignments_selected")
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.team_id for row in result.assignments) == (
        "crypto_btc",
        "politics",
        "equity_index",
        "commodities_gold",
    )
    primary = result.assignments[0]
    assert primary.rank == d("1")
    assert primary.category_label == "finance.crypto.btc"
    assert primary.assignment_score == d("0.874000")
    assert primary.assignment_status == "pass"
    assert primary.reason_codes == (
        "category_hint_crypto_btc",
        "category_signal_strong",
        "keyword_signal_watch",
        "fresh_signal",
        "primary_assignment",
    )

    assert result.assignments[1].assignment_score == d("0.729500")
    assert result.assignments[2].assignment_score == d("0.720500")
    assert result.assignments[3].assignment_score == d("0.675000")


def test_supports_medium_scale_taxonomy_and_safe_general_fallback() -> None:
    module = api()
    categories = {
        "politics": "politics",
        "finance.crypto.btc": "crypto_btc",
        "crypto.btc": "crypto_btc",
        "finance.equity.indices": "equity_index",
        "finance.equities": "equity_index",
        "equities.indices": "equity_index",
        "finance.commodities.gold": "commodities_gold",
        "commodities.gold": "commodities_gold",
        "sports.soccer": "soccer",
        "sports.football": "soccer",
        "sports.basketball": "basketball",
        "sports.tennis": "other_sports",
        "sports.other": "other_sports",
        "technology": "general",
    }

    for category_label, expected_team_id in categories.items():
        result = packet(signal(category_label=category_label))
        assert result.assignment_status == "pass"
        assert result.primary_team_id == expected_team_id
        assert result.secondary_team_ids == ()
        assert result.assignments[0].category_label == category_label
        assert result.assignments[0].team_id == expected_team_id

    no_general = module.MarketCategorySpecialistAssignmentConfig(
        available_team_ids=(
            "politics",
            "crypto_btc",
            "equity_index",
            "commodities_gold",
            "soccer",
            "basketball",
            "other_sports",
        ),
    )

    result = module.build_market_category_specialist_assignment_packet(
        (signal(category_label="technology"),),
        config=no_general,
        generated_at=GENERATED_AT,
    )

    assert result.assignment_status == "block"
    assert result.primary_team_id is None
    assert result.secondary_team_ids == ()
    assert result.team_count == d("1")
    assert result.block_count == d("1")
    assert result.watch_count == d("0")
    assert result.pass_count == d("0")
    assert result.top_assignment_score == d("0.000000")
    assert result.reason_codes == (
        "no_general_team_available",
        "assignment_block",
    )
    assert result.assignments[0].team_id == "general"
    assert result.assignments[0].assignment_status == "block"
    assert result.assignments[0].assignment_score == d("0.000000")
    assert result.assignments[0].reason_codes == (
        "category_hint_general",
        "no_general_team_available",
        "assignment_block",
    )


def test_empty_and_low_confidence_inputs_watch_without_misrouting() -> None:
    empty = packet()

    assert empty.assignment_status == "watch"
    assert empty.primary_team_id is None
    assert empty.secondary_team_ids == ()
    assert empty.team_count == d("0")
    assert empty.reason_codes == ("no_category_signals",)
    assert empty.assignments == ()

    low = packet(
        signal(
            category_label="sports.soccer",
            category_confidence=d("0.250000"),
            keyword_confidence=d("0.250000"),
            freshness_score=d("0.250000"),
        ),
    )

    assert low.assignment_status == "watch"
    assert low.primary_team_id is None
    assert low.secondary_team_ids == ()
    assert low.team_count == d("1")
    assert low.watch_count == d("1")
    assert low.block_count == d("0")
    assert low.pass_count == d("0")
    assert low.top_assignment_score == d("0.250000")
    assert low.reason_codes == ("assignment_confidence_watch",)
    assert low.assignments[0].team_id == "soccer"
    assert low.assignments[0].assignment_status == "watch"
    assert low.assignments[0].reason_codes == (
        "category_hint_soccer",
        "assignment_confidence_watch",
    )


def test_payload_serializes_decimal_strings_and_excludes_raw_market_surfaces() -> None:
    module = api()
    first = packet(
        signal(category_label="finance.crypto.btc", category_confidence=d("0.940000")),
        signal(category_label="politics", category_confidence=d("0.820000")),
    )
    second = packet(
        signal(category_label="politics", category_confidence=d("0.820000")),
        signal(category_label="finance.crypto.btc", category_confidence=d("0.940000")),
    )

    assert first.assignments == second.assignments
    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.market_category_specialist_assignment_packet_payload(first)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["primary_team_id"] == "crypto_btc"
    assert payload["secondary_team_ids"] == ["politics"]
    assert payload["team_count"] == "2"
    assert payload["pass_count"] == "2"
    assert payload["block_count"] == "0"
    assert "assigned_count" not in payload
    assert "blocked_count" not in payload
    assert payload["top_assignment_score"] == "0.831500"
    assert payload["assignments"][0]["assignment_score"] == "0.831500"
    assert payload["assignments"][0]["assignment_status"] == "pass"
    assert payload["assignments"][0]["category_label"] == "finance.crypto.btc"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert "market_id" not in json.dumps(payload, sort_keys=True)
    assert "slug" not in json.dumps(payload, sort_keys=True)
    assert "question" not in json.dumps(payload, sort_keys=True)
    assert "candidate" not in json.dumps(payload, sort_keys=True)
    assert_no_json_numeric_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["top_assignment_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.market_category_specialist_assignment_packet_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    item = signal()
    result = packet(item)
    row = result.assignments[0]

    for instance in (module.MarketCategorySpecialistAssignmentConfig(), item, row, result):
        assert is_dataclass(instance)
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        assert_decimal_only_dataclass(instance)
        with pytest.raises(FrozenInstanceError):
            instance.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, assignment_score=d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, team_count=d("999"))
    with pytest.raises(ValueError, match="payload must be"):
        module.market_category_specialist_assignment_packet_payload(object())


def test_validates_decimal_only_inputs_utc_available_teams_and_duplicates() -> None:
    module = api()
    eastern = timezone_minus_four()
    converted = module.build_market_category_specialist_assignment_packet(
        (
            signal(
                category_label="finance.crypto.btc",
                observed_at=datetime(2026, 7, 7, 7, 30, tzinfo=eastern),
            ),
        ),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=eastern),
    )
    assert converted.generated_at == GENERATED_AT
    assert converted.assignments[0].observed_at == datetime(2026, 7, 7, 11, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="category_confidence"):
        signal(category_confidence=0.9)
    with pytest.raises(ValueError, match="keyword_confidence"):
        signal(keyword_confidence=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="category_label"):
        signal(category_label=" finance.crypto.btc")
    with pytest.raises(ValueError, match="canonical category"):
        signal(category_label="arbitrary.safe.label")
    with pytest.raises(ValueError, match="canonical category"):
        signal(category_label="sports.custom")
    with pytest.raises(ValueError, match="between zero and one"):
        signal(freshness_score=d("1.000001"))

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        packet(signal(), generated_at=datetime(2026, 7, 7, 12, 0, tzinfo=MissingOffsetTz()))
    with pytest.raises(ValueError, match="inputs"):
        module.build_market_category_specialist_assignment_packet(
            "not-inputs",
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate"):
        packet(
            signal(category_label="finance.crypto.btc"),
            signal(category_label="crypto.btc"),
        )
    with pytest.raises(ValueError, match="available_team_ids"):
        module.MarketCategorySpecialistAssignmentConfig(available_team_ids=("politics",))
    with pytest.raises(ValueError, match="known strategy team"):
        module.MarketCategorySpecialistAssignmentConfig(
            available_team_ids=("politics", "not_a_team"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        packet(signal(observed_at=GENERATED_AT + timedelta(minutes=1)))


def timezone_minus_four() -> tzinfo:
    class FixedMinusFour(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta:
            return timedelta(hours=-4)

        def dst(self, dt: datetime | None) -> timedelta:
            return timedelta(0)

    return FixedMinusFour()


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "market-id",
        "https://example.test/market/123",
        "www.example.org/markets/123",
        "example.org/markets/123",
        "polymarket.com/event/example-market",
        "polymarket.com",
        "condition_id",
        "source_id",
        "token_id",
        "market_slug",
        "question_text",
        "candidate_id",
        "source_url",
        "source_text",
        "postgres_dsn",
        "table_name",
        "wallet_surface",
        "auth_surface",
        "order_surface",
        "trade_surface",
        "position_size",
        "buy_signal",
        "sell_signal",
        "recommendation",
    ),
)
def test_rejects_unsafe_public_payload_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        signal(category_label=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public"):
        module.market_category_specialist_assignment_packet_payload(
            {"note": unsafe_value, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.market_category_specialist_assignment_packet_payload(
            {unsafe_value: "redacted", "paper_only": True, "report_only": True, "readonly": True},
        )


def test_module_scope_has_no_external_io_execution_or_live_surfaces() -> None:
    module = api()
    source_text = inspect.getsource(module)
    lowered_source = source_text.lower()
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_MARKET_CATEGORY_SPECIALIST_ASSIGNMENT_PACKET_CONFIG_VERSION",
        "ASSIGNMENT_STATUSES",
        "PACKET_STATUSES",
        "MarketCategorySpecialistAssignmentConfig",
        "MarketCategorySpecialistAssignmentSignal",
        "MarketCategorySpecialistAssignmentRow",
        "MarketCategorySpecialistAssignmentPacket",
        "build_market_category_specialist_assignment_packet",
        "market_category_specialist_assignment_packet_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
        "polymarket_alpha_lab",
    }

    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "account",
        "wallet",
        "order",
        "trade",
        "trading",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "write_text",
        "write_bytes",
    )
    assert all(term not in lowered_source for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
