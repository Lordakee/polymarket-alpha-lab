from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_cpi_revision_digest import (
    DEFAULT_MARKET_RESEARCH_CPI_REVISION_DIGEST_CONFIG_VERSION,
    MarketResearchCpiRevisionDigestConfig,
    MarketResearchCpiRevisionDigestInputRow,
    MarketResearchCpiRevisionDigestReport,
    build_market_research_cpi_revision_digest,
    market_research_cpi_revision_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchCpiRevisionDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_CPI_REVISION_DIGEST_CONFIG_VERSION,
        "fresh_release_max_age_seconds": d("7200.000000"),
        "material_revision_threshold": d("0.100000"),
        "min_source_count": d("2.000000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchCpiRevisionDigestConfig(**values)


def input_row(
    research_key: str = "research.cpi.headline",
    *,
    condition_id: str = "condition_cpi_headline",
    cpi_series_key: str = "cpi.headline.yoy",
    cpi_release_reference: str = "public-bls-cpi-release",
    released_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    initial_value: Decimal = d("3.200000"),
    revised_value: Decimal = d("3.240000"),
    prior_value: Decimal = d("3.000000"),
    market_probability_before: Decimal = d("0.480000"),
    market_probability_after: Decimal = d("0.520000"),
) -> MarketResearchCpiRevisionDigestInputRow:
    return MarketResearchCpiRevisionDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        cpi_series_key=cpi_series_key,
        cpi_release_reference=cpi_release_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=(
            acknowledged_at
            if acknowledged_at is not None
            else GENERATED_AT - timedelta(minutes=20)
        ),
        source_count=source_count,
        initial_value=initial_value,
        revised_value=revised_value,
        prior_value=prior_value,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_cpi_revision_short_module_is_phase1_report_only_alias() -> None:
    summary = build_market_research_cpi_revision_digest(
        (
            input_row(
                "research.cpi.core",
                condition_id="condition_cpi_core",
                cpi_series_key="cpi.core.mom",
                cpi_release_reference="https://vendor.example/cpi?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=100),
                source_count=d("1.000000"),
                initial_value=d("0.200000"),
                revised_value=d("0.350000"),
                prior_value=d("0.100000"),
                market_probability_before=d("0.420000"),
                market_probability_after=d("0.610000"),
            ),
            input_row(),
        ),
        config=config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchCpiRevisionDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert summary.cpi_release_count == d("2.000000")
    assert all(row.paper_only and row.report_only and row.readonly for row in summary.rows)
    assert all(type(row.revision_abs) is Decimal for row in summary.rows)
    assert tuple(row.cpi_series_key for row in summary.rows) == (
        "cpi.core.mom",
        "cpi.headline.yoy",
    )
    assert summary.rows[0].redacted_cpi_release_reference.startswith("sha256:")

    with pytest.raises(FrozenInstanceError):
        summary.cpi_release_count = d("3.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        input_row(source_count=2)  # type: ignore[arg-type]

    payload = market_research_cpi_revision_digest_payload(summary)
    json.dumps(payload, sort_keys=True)
    assert payload == market_research_cpi_revision_digest_payload(summary)
    assert payload["cpi_release_count"] == "2.000000"
    assert payload["average_revision_abs"] == "0.095000"
    assert payload["max_release_age_seconds"] == "10800.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert all(row["paper_only"] is True for row in payload["rows"])
    assert all(row["report_only"] is True for row in payload["rows"])
    assert all(row["readonly"] is True for row in payload["rows"])
    assert all(item["paper_only"] is True for item in payload["reason_code_counts"])
    assert all(item["report_only"] is True for item in payload["reason_code_counts"])
    assert all(item["readonly"] is True for item in payload["reason_code_counts"])
    assert payload["rows"][0]["source_count"] == "1.000000"
    assert payload["rows"][0]["revision_abs"] == "0.150000"
    assert payload["rows"][0]["market_probability_after"] == "0.610000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["release_ratio"] == "0.500000"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert "'cpi_release_reference':" not in repr(payload)
    assert payload["rows"][0]["redacted_cpi_release_reference"].startswith("sha256:")
    assert "secret-123" not in repr(payload).lower()
    assert "token" not in repr(payload).lower()
    assert "wallet" not in repr(payload).lower()

    unsafe_report = replace(summary)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_cpi_revision_digest_payload(unsafe_report)
    with pytest.raises(ValueError, match="public identifier"):
        input_row(research_key="research.wallet.cpi")
    with pytest.raises(ValueError, match="public identifier"):
        input_row(condition_id="condition_private_cpi")
    with pytest.raises(ValueError, match="redacted"):
        replace(
            summary.rows[0],
            redacted_cpi_release_reference="https://vendor.example/cpi?token=secret-123",
        )


@pytest.mark.parametrize(
    "module_name",
    (
        "market_research_cpi_revision_digest.py",
        "market_research_macro_cpi_revision_digest.py",
    ),
)
def test_cpi_revision_short_module_has_no_live_or_durable_surface(
    module_name: str,
) -> None:
    module_path = (
        Path(__file__).resolve().parents[1] / "src" / "polymarket_alpha_lab" / module_name
    )
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "wallet",
        "private_key",
        "sqlite",
        "postgres",
        "redis",
    ):
        assert token not in source

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "web3",
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
