from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_bank_deposit_outflow_digest"
GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_MARKET_RESEARCH_BANK_DEPOSIT_OUTFLOW_DIGEST_CONFIG_VERSION,
        "fresh_observation_max_age_seconds": d("7200.000000"),
        "material_deposit_drop_ratio": d("0.030000"),
        "elevated_outflow_ratio": d("0.050000"),
        "min_source_count": d("2"),
        "probability_repricing_threshold": d("0.050000"),
    }
    values.update(overrides)
    return module.MarketResearchBankDepositOutflowDigestConfig(**values)


def input_row(
    research_key: str = "research.bank.deposit.regional.alpha",
    *,
    condition_id: str = "condition_bank_deposit_outflow",
    bank_key: str = "regional_alpha",
    deposit_source_reference: str = "https://bank.example/regional_alpha?api_key=secret-123",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3"),
    deposit_balance: Decimal = d("970.000000"),
    prior_deposit_balance: Decimal = d("1000.000000"),
    net_deposit_flow: Decimal = d("-30.000000"),
    uninsured_deposit_ratio: Decimal = d("0.420000"),
    market_probability_before: Decimal = d("0.390000"),
    market_probability_after: Decimal = d("0.430000"),
) -> Any:
    module = api()
    return module.MarketResearchBankDepositOutflowDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        bank_key=bank_key,
        deposit_source_reference=deposit_source_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        source_count=source_count,
        deposit_balance=deposit_balance,
        prior_deposit_balance=prior_deposit_balance,
        net_deposit_flow=net_deposit_flow,
        uninsured_deposit_ratio=uninsured_deposit_ratio,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
    )


def digest(
    *rows: object,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_market_research_bank_deposit_outflow_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_bank_deposit_outflow_digest_flags_pressure_and_sorts_rows() -> None:
    module = api()
    report = digest(
        input_row(),
        input_row(
            "research.bank.deposit.regional.beta",
            condition_id="condition_bank_beta",
            bank_key="regional_beta",
            observed_at=GENERATED_AT - timedelta(hours=3),
            source_count=d("1"),
            deposit_balance=d("880.000000"),
            prior_deposit_balance=d("1000.000000"),
            net_deposit_flow=d("-120.000000"),
            uninsured_deposit_ratio=d("0.610000"),
            market_probability_before=d("0.300000"),
            market_probability_after=d("0.390000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, module.MarketResearchBankDepositOutflowDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("0.000000")
    assert report.watch_observation_count == d("1.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.material_deposit_drop_count == d("2.000000")
    assert report.elevated_outflow_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.probability_repricing_count == d("1.000000")
    assert report.average_deposit_drop_ratio == d("0.075000")
    assert report.max_observation_age_seconds == d("10800.000000")
    assert tuple(row.bank_key for row in report.rows) == (
        "regional_beta",
        "regional_alpha",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.rows[0].deposit_drop_ratio == d("0.120000")
    assert report.rows[0].net_deposit_flow == d("-120.000000")
    assert report.rows[0].redacted_deposit_source_reference.startswith("sha256:")
    assert report.reason_codes == (
        "market_research_bank_deposit_outflow_digest_material_deposit_drop",
        "market_research_bank_deposit_outflow_digest_stale_observation",
        "market_research_bank_deposit_outflow_digest_probability_repricing",
        "market_research_bank_deposit_outflow_digest_elevated_outflow",
        "market_research_bank_deposit_outflow_digest_thin_source",
    )

    with pytest.raises(FrozenInstanceError):
        report.observation_count = d("3.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        input_row(source_count=2)  # type: ignore[arg-type]


def test_payload_is_json_ready_redacted_and_decimal_string_only() -> None:
    module = api()
    report = digest(input_row())

    payload = module.market_research_bank_deposit_outflow_digest_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload == module.market_research_bank_deposit_outflow_digest_payload(report)
    assert payload["observation_count"] == "1.000000"
    assert payload["average_deposit_drop_ratio"] == "0.030000"
    assert payload["max_observation_age_seconds"] == "1800.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["deposit_balance"] == "970.000000"
    assert payload["rows"][0]["prior_deposit_balance"] == "1000.000000"
    assert payload["rows"][0]["net_deposit_flow"] == "-30.000000"
    assert payload["rows"][0]["deposit_drop_ratio"] == "0.030000"
    assert payload["rows"][0]["redacted_deposit_source_reference"].startswith("sha256:")
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert "secret-123" not in repr(payload).lower()
    assert "api_key" not in repr(payload).lower()
    assert "wallet" not in repr(payload).lower()

    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_bank_deposit_outflow_digest_payload(unsafe_report)
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.market_research_bank_deposit_outflow_digest_payload(
            {**payload, "observation_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        module.market_research_bank_deposit_outflow_digest_payload(
            {**payload, "average_deposit_drop_ratio": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.market_research_bank_deposit_outflow_digest_payload(
            {**payload, "operator_token": "redacted"},
        )

    raw_payload = module.market_research_bank_deposit_outflow_digest_payload(
        {
            "observation_count": Decimal("1"),
            "average_deposit_drop_ratio": Decimal("0.1"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    assert raw_payload["observation_count"] == "1.000000"
    assert raw_payload["average_deposit_drop_ratio"] == "0.100000"


def test_source_references_with_key_material_are_redacted() -> None:
    module = api()
    report = digest(
        input_row(
            deposit_source_reference="api_key=abc123",
        ),
    )

    row = report.rows[0]
    payload = module.market_research_bank_deposit_outflow_digest_payload(report)

    assert row.redacted_deposit_source_reference.startswith("sha256:")
    assert payload["rows"][0]["redacted_deposit_source_reference"].startswith("sha256:")
    assert "api_key" not in repr(report).lower()
    assert "api_key" not in repr(payload).lower()
    assert "abc123" not in repr(report).lower()
    assert "abc123" not in repr(payload).lower()


def test_empty_input_and_datetime_validation_are_strict() -> None:
    module = api()

    report = digest()
    assert report.digest_status == "watch"
    assert report.observation_count == d("0.000000")
    assert report.average_deposit_drop_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_bank_deposit_outflow_digest_no_inputs",
    )

    class DerivedDateTime(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at"):
        digest(input_row(), generated_at=DerivedDateTime(2026, 7, 4, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 4, 14, 30))
    with pytest.raises(ValueError, match="public identifier"):
        input_row(research_key="research.wallet.bank")
    with pytest.raises(ValueError, match="observed_at cannot be after generated_at"):
        digest(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique research condition bank keys"):
        digest(input_row(), input_row())
    with pytest.raises(ValueError, match="redacted"):
        replace(
            digest(input_row()).rows[0],
            redacted_deposit_source_reference=(
                "https://bank.example/regional_alpha?api_key=secret-123"
            ),
        )


def test_module_has_no_live_durable_or_forbidden_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / (
        "src/polymarket_alpha_lab/market_research_bank_deposit_outflow_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
        "live trading",
        "wallet",
        "private_key",
        "sqlite",
        "postgres",
        "redis",
    ):
        assert token not in lowered

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
