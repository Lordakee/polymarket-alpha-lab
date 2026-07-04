from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_crypto_bridge_governance_pause_digest"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_crypto_bridge_governance_pause_digest.py"
)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "max_observation_age_seconds": d("1800.000000"),
        "watch_active_pause_signal_count": d("1.000000"),
        "blocked_enactable_pause_action_count": d("1.000000"),
        "max_pause_window_seconds": d("7200.000000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoBridgeGovernancePauseDigestConfig(**values)


def observation(
    condition_id: str = "condition_alpha",
    bridge_pause_id: str = "arb_eth_governance_pause",
    *,
    bridge_name: str = "Arbitrum",
    chain_family: str = "ethereum_l2",
    observed_at: datetime = GENERATED_AT,
    active_pause_signal_count: Decimal = d("0.000000"),
    enactable_pause_action_count: Decimal = d("0.000000"),
    paused_critical_function_count: Decimal = d("0.000000"),
    total_critical_function_count: Decimal = d("4.000000"),
    pause_window_seconds: Decimal = d("1800.000000"),
    governance_delay_seconds: Decimal = d("7200.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "bridge-pause-source-v0",
):
    module = api()
    return module.MarketResearchCryptoBridgeGovernancePauseObservation(
        condition_id=condition_id,
        bridge_pause_id=bridge_pause_id,
        bridge_name=bridge_name,
        chain_family=chain_family,
        observed_at=observed_at,
        active_pause_signal_count=active_pause_signal_count,
        enactable_pause_action_count=enactable_pause_action_count,
        paused_critical_function_count=paused_critical_function_count,
        total_critical_function_count=total_critical_function_count,
        pause_window_seconds=pause_window_seconds,
        governance_delay_seconds=governance_delay_seconds,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def build_digest(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_market_research_crypto_bridge_governance_pause_digest(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_governance_pause_digest_reduces_pause_pressure_and_confidence() -> None:
    report = build_digest(
        observation(
            "condition_beta",
            "op_usdc_governance_pause",
            bridge_name="Optimism",
            chain_family="ethereum_l2",
            observed_at=GENERATED_AT - timedelta(seconds=2_400),
            active_pause_signal_count=d("2.000000"),
            enactable_pause_action_count=d("1.000000"),
            paused_critical_function_count=d("2.000000"),
            total_critical_function_count=d("4.000000"),
            pause_window_seconds=d("14400.000000"),
            governance_delay_seconds=d("7200.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        observation(
            "condition_alpha",
            "arb_eth_governance_pause",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    module = api()
    assert type(report) is module.MarketResearchCryptoBridgeGovernancePauseDigestReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-bridge-governance-pause-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_bridge_governance_pause_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.pause_signal_observation_count == d("1.000000")
    assert report.pause_action_enactable_observation_count == d("1.000000")
    assert report.critical_function_paused_observation_count == d("1.000000")
    assert report.pause_window_pressure_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_active_pause_signal_count == d("1.000000")
    assert report.average_enactable_pause_action_count == d("0.500000")
    assert report.average_critical_pause_ratio == d("0.250000")
    assert report.average_pause_window_pressure_ratio == d("1.125000")
    assert report.max_observation_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.bridge_pause_id) for row in report.rows) == (
        ("condition_beta", "op_usdc_governance_pause"),
        ("condition_alpha", "arb_eth_governance_pause"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.observation_age_seconds == d("2400.000000")
    assert beta.critical_pause_ratio == d("0.500000")
    assert beta.pause_window_pressure_ratio == d("2.000000")
    assert beta.reason_codes == (
        "market_research_crypto_bridge_governance_pause_digest_pause_signal",
        "market_research_crypto_bridge_governance_pause_digest_pause_action_enactable",
        "market_research_crypto_bridge_governance_pause_digest_critical_function_paused",
        "market_research_crypto_bridge_governance_pause_digest_pause_window_pressure",
        "market_research_crypto_bridge_governance_pause_digest_source_diversity_gap",
        "market_research_crypto_bridge_governance_pause_digest_stale_observation",
        "market_research_crypto_bridge_governance_pause_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_governance_pause_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = build_digest(
        observation(
            "condition_gamma",
            "base_eth_governance_pause",
            bridge_name="Base",
            observed_at=observed_at,
            source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    module = api()
    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        module.MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_bridge_governance_pause_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        module.MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_bridge_governance_pause_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("base_eth_governance_pause", "bridge-pause-source-v0"),
    )


def test_governance_pause_digest_empty_input_is_watch_and_sorted_deterministically() -> None:
    empty = build_digest()
    assert empty.digest_status == "watch"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_bridge_governance_pause_digest_no_inputs",
    )

    first = build_digest(
        observation("condition_b", "source_b"),
        observation("condition_a", "source_a"),
    )
    second = build_digest(
        observation("condition_a", "source_a"),
        observation("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.bridge_pause_id for row in first.rows) == ("source_a", "source_b")


def test_governance_pause_digest_validates_exact_types_flags_and_freezing() -> None:
    module = api()
    contract_classes = (
        module.MarketResearchCryptoBridgeGovernancePauseDigestConfig,
        module.MarketResearchCryptoBridgeGovernancePauseObservation,
        module.MarketResearchCryptoBridgeGovernancePauseDigestRow,
        module.MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount,
        module.MarketResearchCryptoBridgeGovernancePauseDigestReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for hint in get_type_hints(contract_class).values():
            assert not _type_uses_float(hint)

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("pause-v0"))
    with pytest.raises(ValueError, match="watch_active_pause_signal_count"):
        config(watch_active_pause_signal_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        observation(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        build_digest(
            observation(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_digest(
            observation(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        build_digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        observation().paper_only = False  # type: ignore[misc]


def test_governance_pause_digest_public_numeric_fields_are_decimal_only() -> None:
    report = build_digest(observation())

    for value in _decimal_public_values(report):
        assert type(value) is Decimal

    with pytest.raises(ValueError, match="observation_count"):
        replace(report, observation_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.rows[0],
            reason_codes=(
                "market_research_crypto_bridge_governance_pause_digest_no_inputs",
            ),
        )


def test_governance_pause_digest_payload_is_immutable_and_uses_six_decimal_strings() -> None:
    module = api()
    payload = module.market_research_crypto_bridge_governance_pause_digest_payload(
        build_digest(
            observation(
                "condition_redacted",
                "arb_eth_governance_pause_redacted",
                bridge_name="Arbitrum",
            ),
        ),
    )
    payload_text = repr(payload).lower()

    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "order",
        "auth",
        "token",
        "private",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_pause_window_pressure_ratio"] == "0.250000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["active_pause_signal_count"] == "0.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["active_pause_signal_count"] = "1.000000"  # type: ignore[index]


def test_governance_pause_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    module = api()
    with pytest.raises(ValueError, match="unique"):
        build_digest(
            observation(bridge_pause_id="duplicate"),
            observation(bridge_pause_id="duplicate"),
        )

    valid = build_digest(observation())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(module.MarketResearchCryptoBridgeGovernancePauseDigestReport)
    }
    assert (
        module.MarketResearchCryptoBridgeGovernancePauseDigestReport(**kwargs).digest_status
        == "ready"
    )

    with pytest.raises(ValueError, match="observation_count"):
        module.MarketResearchCryptoBridgeGovernancePauseDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        module.MarketResearchCryptoBridgeGovernancePauseDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.MarketResearchCryptoBridgeGovernancePauseDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    module.MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_bridge_governance_pause_digest_ready"
                        ),
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )

    multi = build_digest(
        observation("condition_b", "source_b"),
        observation("condition_a", "source_a"),
    )
    multi_kwargs = {
        field.name: getattr(multi, field.name)
        for field in fields(module.MarketResearchCryptoBridgeGovernancePauseDigestReport)
    }
    with pytest.raises(ValueError, match="rows"):
        module.MarketResearchCryptoBridgeGovernancePauseDigestReport(
            **{**multi_kwargs, "rows": tuple(reversed(multi.rows))},
        )


def test_governance_pause_digest_module_scope_excludes_execution_io_and_persistence() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "live_trading",
        "wallet",
        "broker",
        "order",
        "signing",
        "advice",
        "private_key",
        "api_key",
        "secret",
        "credential",
        "database",
        "network",
        "requests",
        "socket",
        "subprocess",
        "http",
        "open(",
        "pathlib",
        "psycopg",
        "supabase",
        "cancel",
        "replace",
        "exchange",
        "mutation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
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


def _decimal_public_values(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name == "confidence"
            ):
                found.append(field_value)
            found.extend(_decimal_public_values(field_value))
        return tuple(found)
    if isinstance(value, tuple):
        for item in value:
            found.extend(_decimal_public_values(item))
    return tuple(found)


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))
