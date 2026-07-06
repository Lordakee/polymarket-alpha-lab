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


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ANCHOR_AT = datetime(2026, 7, 6, 11, 50, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_NAME = "polymarket_alpha_lab.strategy_source_verified_edge_gate_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_source_verified_edge_gate_v2.py"
)


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
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_STRATEGY_SOURCE_VERIFIED_EDGE_GATE_V2_CONFIG_VERSION,
        "max_official_anchor_age_seconds": d("900.000000"),
        "min_official_anchor_count": d("1.000000"),
        "min_independent_source_family_count": d("3.000000"),
        "min_specialist_quorum_count": d("2.000000"),
        "min_resolution_rule_clarity_score": d("0.800000"),
        "min_forecast_edge_probability": d("0.020000"),
    }
    values.update(overrides)
    return module.StrategySourceVerifiedEdgeGateV2Config(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "market_slug": "verified-edge-market",
        "condition_id": "condition-verified-edge",
        "outcome": "yes",
        "forecast_probability": d("0.580000"),
        "market_probability": d("0.530000"),
        "official_anchor_observed_at": ANCHOR_AT,
        "official_anchor_count": d("1.000000"),
        "source_families": (
            "official_federal",
            "independent_media",
            "market_rules",
        ),
        "contradiction_review_status": "reviewed_no_material_contradiction",
        "resolution_rule_clarity_score": d("0.900000"),
        "specialist_quorum_count": d("2.000000"),
        "source_config_version": "paper-source-review-v0",
    }
    values.update(overrides)
    return module.StrategySourceVerifiedEdgeGateV2Candidate(**values)


def report(*values: object, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_source_verified_edge_gate_v2_report(
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


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_verified_sources_allow_edge_and_unverified_sources_zero_edge() -> None:
    result = report(
        candidate(
            market_slug="z-verified",
            condition_id="condition-verified",
            forecast_probability=d("0.580000"),
            market_probability=d("0.530000"),
            official_anchor_observed_at=GENERATED_AT - timedelta(seconds=600),
            source_families=(
                "official_federal",
                "independent_media",
                "market_rules",
            ),
        ),
        candidate(
            market_slug="a-stale",
            condition_id="condition-stale",
            forecast_probability=d("0.610000"),
            market_probability=d("0.560000"),
            official_anchor_observed_at=GENERATED_AT - timedelta(seconds=901),
            source_families=(
                "official_federal",
                "independent_media",
                "market_rules",
            ),
        ),
        candidate(
            market_slug="m-unclear",
            condition_id="condition-unclear",
            forecast_probability=d("0.570000"),
            market_probability=d("0.560000"),
            resolution_rule_clarity_score=d("0.700000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-source-verified-edge-gate-v2"
    assert result.market_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.candidate_edge_count == d("2.000000")
    assert result.eligible_edge_count == d("1.000000")
    assert result.total_candidate_edge_probability == d("0.110000")
    assert result.total_eligible_edge_probability == d("0.050000")
    assert result.max_anchor_age_seconds == d("901.000000")
    assert result.min_resolution_rule_clarity_score == d("0.700000")
    assert result.gate_status == "blocked"
    assert result.recommended_next_step == "block_report_only_source_verified_edge"
    assert result.reason_codes == (
        "forecast_edge_below_minimum",
        "fresh_official_anchor_missing",
        "resolution_rule_clarity_below_minimum",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    stale, unclear, verified = result.rows
    assert tuple(row.market_slug for row in result.rows) == (
        "a-stale",
        "m-unclear",
        "z-verified",
    )
    assert stale.candidate_edge_probability == d("0.050000")
    assert stale.eligible_edge_probability == ZERO
    assert stale.gate_status == "blocked"
    assert stale.reason_codes == ("fresh_official_anchor_missing",)
    assert unclear.candidate_edge_probability == d("0.010000")
    assert unclear.eligible_edge_probability == ZERO
    assert unclear.gate_status == "watch"
    assert unclear.reason_codes == (
        "forecast_edge_below_minimum",
        "resolution_rule_clarity_below_minimum",
    )
    assert verified.candidate_edge_probability == d("0.050000")
    assert verified.eligible_edge_probability == d("0.050000")
    assert verified.gate_status == "pass"
    assert verified.reason_codes == ("source_verified_edge_gate_passed",)
    assert len({row.derived_validation_digest for row in result.rows}) == 3


def test_empty_report_is_readonly_zeroed_and_digest_bound() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.StrategySourceVerifiedEdgeGateV2Report
    assert empty.market_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.candidate_edge_count == ZERO
    assert empty.eligible_edge_count == ZERO
    assert empty.total_candidate_edge_probability == ZERO
    assert empty.total_eligible_edge_probability == ZERO
    assert empty.max_anchor_age_seconds == ZERO
    assert empty.min_resolution_rule_clarity_score == ZERO
    assert empty.gate_status == "pass"
    assert empty.recommended_next_step == "continue_report_only_source_verified_edge"
    assert empty.reason_codes == ("source_verified_edge_gate_empty",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    for public_value in (config(), candidate(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True


def test_public_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        candidate(
            market_slug="payload-market",
            condition_id="condition-payload",
            forecast_probability=d("0.620000"),
            market_probability=d("0.550000"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_source_verified_edge_gate_v2_public_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["total_eligible_edge_probability"] == "0.070000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["official_anchor_observed_at"] == "2026-07-06T11:50:00+00:00"
    assert payload["rows"][0]["candidate_edge_probability"] == "0.070000"
    assert payload["rows"][0]["eligible_edge_probability"] == "0.070000"
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_strategy_source_verified_edge_gate_v2_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "market_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_strategy_source_verified_edge_gate_v2_public_payload(
            numeric_payload,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_source_verified_edge_gate_v2_public_payload(
            missing_digest,
        )

    tampered = {**payload, "eligible_edge_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_source_verified_edge_gate_v2_public_payload(tampered)

    tampered_report = replace(result)
    object.__setattr__(tampered_report, "eligible_edge_count", d("99.000000"))
    with pytest.raises(ValueError, match="eligible_edge_count|derived_validation_digest"):
        module.strategy_source_verified_edge_gate_v2_public_payload(tampered_report)


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
def test_public_payload_rejects_unsafe_public_keys_and_values(
    key: str,
    value: str,
) -> None:
    module = api()
    payload = module.strategy_source_verified_edge_gate_v2_public_payload(
        report(candidate(market_slug="unsafe-check", condition_id="condition-unsafe")),
    )

    unsafe_payload = {**payload, key: value}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_strategy_source_verified_edge_gate_v2_public_payload(
            unsafe_payload,
        )


def test_validation_rejects_bad_types_flags_duplicates_time_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_source_verified_edge_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="official_anchor_observed_at"):
        candidate(official_anchor_observed_at=datetime(2026, 7, 6, 11, 50))
    with pytest.raises(ValueError, match="official_anchor_observed_at"):
        candidate(
            official_anchor_observed_at=datetime(
                2026,
                7,
                6,
                11,
                50,
                tzinfo=_NoneOffsetTz(),
            ),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        report(candidate(official_anchor_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate source verified candidate"):
        report(
            candidate(market_slug="dup", condition_id="condition-dup"),
            candidate(market_slug="dup", condition_id="condition-dup"),
        )
    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=d("0.500000"), market_probability=d("0.510000"))
    with pytest.raises(ValueError, match="official_anchor_count"):
        candidate(official_anchor_count=1)
    with pytest.raises(ValueError, match="specialist_quorum_count"):
        candidate(specialist_quorum_count=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="source_families"):
        candidate(source_families=("official_federal", "official_federal"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    clear_report = report(candidate(market_slug="consistent", condition_id="condition-consistent"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="eligible_edge_count"):
        replace(clear_report, eligible_edge_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        clear_report.gate_status = "blocked"  # type: ignore[misc]


def test_export_contract_and_static_no_external_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_SOURCE_VERIFIED_EDGE_GATE_V2_CONFIG_VERSION",
        "StrategySourceVerifiedEdgeGateV2Candidate",
        "StrategySourceVerifiedEdgeGateV2Config",
        "StrategySourceVerifiedEdgeGateV2ReasonCodeCount",
        "StrategySourceVerifiedEdgeGateV2Report",
        "StrategySourceVerifiedEdgeGateV2Row",
        "build_strategy_source_verified_edge_gate_v2_report",
        "strategy_source_verified_edge_gate_v2_public_payload",
        "validate_strategy_source_verified_edge_gate_v2_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for instance in (
        config(),
        candidate(),
        *report(candidate()).rows,
        report(candidate()),
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_score",
                    "_seconds",
                ),
            ):
                assert value is None or type(value) is Decimal

    source = MODULE_PATH.read_text()
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
        "private_key",
        "api_key",
        unsafe_text("au", "th", "_token"),
        unsafe_text("wal", "let"),
        unsafe_text("net", "work", "_client"),
        unsafe_text("data", "base", "_url"),
        unsafe_text("per", "sist", "_path"),
        "place_" + unsafe_text("ord", "er"),
        "create_" + unsafe_text("ord", "er"),
        "cancel_" + unsafe_text("ord", "er"),
        "submit_" + unsafe_text("ord", "er"),
        unsafe_text("li", "ve", "_trading"),
        unsafe_text("tra", "de", "_executor"),
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "read",
        "write",
    }
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_source_fragments
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_source_fragments
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names
