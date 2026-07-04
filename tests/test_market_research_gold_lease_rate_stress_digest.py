from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_gold_lease_rate_stress_digest import (
    DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION,
    MarketResearchGoldLeaseRateStressDigestConfig,
    MarketResearchGoldLeaseRateStressDigestObservation,
    MarketResearchGoldLeaseRateStressDigestReasonCodeCount,
    MarketResearchGoldLeaseRateStressDigestReport,
    build_market_research_gold_lease_rate_stress_digest,
    market_research_gold_lease_rate_stress_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=1))
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchGoldLeaseRateStressDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION
        ),
        "severe_lease_rate_threshold_bps": d("80.000000"),
        "elevated_lease_rate_threshold_bps": d("40.000000"),
        "lease_rate_spike_threshold_bps": d("25.000000"),
        "backwardation_threshold_bps": d("10.000000"),
        "max_observation_age_seconds": d("86400.000000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return MarketResearchGoldLeaseRateStressDigestConfig(**values)


def observation(
    tenor_key: str,
    *,
    market_slug: str | None = None,
    observed_at: datetime | None = None,
    lease_rate_bps: Decimal = d("18.000000"),
    baseline_lease_rate_bps: Decimal = d("12.000000"),
    futures_basis_bps: Decimal = d("4.000000"),
    source_count: Decimal = d("2.000000"),
    source_reference: str = "public-lbma-gold-lease-release",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchGoldLeaseRateStressDigestObservation:
    return MarketResearchGoldLeaseRateStressDigestObservation(
        tenor_key=tenor_key,
        market_slug=market_slug or f"gold-lease-rate-stress-{tenor_key}",
        observed_at=observed_at if observed_at is not None else GENERATED_AT,
        lease_rate_bps=lease_rate_bps,
        baseline_lease_rate_bps=baseline_lease_rate_bps,
        futures_basis_bps=futures_basis_bps,
        source_count=source_count,
        source_reference=source_reference,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchGoldLeaseRateStressDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchGoldLeaseRateStressDigestReport:
    return build_market_research_gold_lease_rate_stress_digest(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_gold_lease_rate_stress_digest_reduces_inputs_deterministically() -> None:
    summary = report(
        (
            observation(
                "three-month",
                observed_at=GENERATED_AT - timedelta(hours=30),
                lease_rate_bps=d("55.000000"),
                baseline_lease_rate_bps=d("22.000000"),
                futures_basis_bps=d("-16.000000"),
                source_count=d("1.000000"),
                source_reference="restricted-bullion-bank-sheet",
            ),
            observation(
                "one-month",
                observed_at=GENERATED_AT - timedelta(hours=3),
                lease_rate_bps=d("95.000000"),
                baseline_lease_rate_bps=d("50.000000"),
                futures_basis_bps=d("-18.000000"),
                source_reference="https://vendor.example/gold-lease?token=secret-123",
            ),
            observation(
                "six-month",
                observed_at=GENERATED_AT.astimezone(SOURCE_TZ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(SOURCE_TZ),
    )

    assert isinstance(summary, MarketResearchGoldLeaseRateStressDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_gold_lease_rate_stress_digest"
    )
    assert tuple(row.tenor_key for row in summary.observations) == (
        "one-month",
        "six-month",
        "three-month",
    )
    assert all(row.observed_at.tzinfo is UTC for row in summary.observations)
    assert summary.observation_count == d("3.000000")
    assert summary.severe_lease_rate_count == d("1.000000")
    assert summary.elevated_lease_rate_count == d("1.000000")
    assert summary.lease_rate_spike_count == d("2.000000")
    assert summary.backwardation_pressure_count == d("2.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.max_lease_rate_bps == d("95.000000")
    assert summary.average_lease_rate_bps == d("56.000000")
    assert summary.average_lease_rate_delta_bps == d("28.000000")
    assert summary.average_source_count == d("1.666667")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert summary.reason_codes == (
        "market_research_gold_lease_rate_stress_digest_severe_lease_rate",
        "market_research_gold_lease_rate_stress_digest_elevated_lease_rate",
        "market_research_gold_lease_rate_stress_digest_lease_rate_spike",
        "market_research_gold_lease_rate_stress_digest_backwardation_pressure",
        "market_research_gold_lease_rate_stress_digest_stale_observation",
        "market_research_gold_lease_rate_stress_digest_thin_sources",
        "market_research_gold_lease_rate_stress_digest_blocked",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_lease_rate_stress_digest_severe_lease_rate"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_lease_rate_stress_digest_elevated_lease_rate"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code="market_research_gold_lease_rate_stress_digest_lease_rate_spike",
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_lease_rate_stress_digest_backwardation_pressure"
            ),
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_lease_rate_stress_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code="market_research_gold_lease_rate_stress_digest_thin_sources",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code="market_research_gold_lease_rate_stress_digest_blocked",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )

    severe, ready, elevated = summary.observations
    assert severe.digest_status == "blocked"
    assert severe.observation_age_seconds == d("10800.000000")
    assert severe.lease_rate_delta_bps == d("45.000000")
    assert severe.redacted_source_reference.startswith("sha256:")
    assert severe.reason_codes == (
        "market_research_gold_lease_rate_stress_digest_severe_lease_rate",
        "market_research_gold_lease_rate_stress_digest_lease_rate_spike",
        "market_research_gold_lease_rate_stress_digest_backwardation_pressure",
        "market_research_gold_lease_rate_stress_digest_blocked",
    )
    assert ready.digest_status == "ready"
    assert ready.observation_age_seconds == ZERO
    assert ready.lease_rate_delta_bps == d("6.000000")
    assert ready.redacted_source_reference == "public-lbma-gold-lease-release"
    assert ready.reason_codes == (
        "market_research_gold_lease_rate_stress_digest_no_stress",
    )
    assert elevated.digest_status == "watch"
    assert elevated.observation_age_seconds == d("108000.000000")
    assert elevated.lease_rate_delta_bps == d("33.000000")
    assert elevated.redacted_source_reference.startswith("sha256:")
    assert elevated.reason_codes == (
        "market_research_gold_lease_rate_stress_digest_elevated_lease_rate",
        "market_research_gold_lease_rate_stress_digest_lease_rate_spike",
        "market_research_gold_lease_rate_stress_digest_backwardation_pressure",
        "market_research_gold_lease_rate_stress_digest_stale_observation",
        "market_research_gold_lease_rate_stress_digest_thin_sources",
    )

    serialized = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "restricted-bullion-bank-sheet",
        "auth",
        "wallet",
        "token",
        "private",
    ):
        assert token not in serialized


def test_gold_lease_rate_stress_digest_ready_when_clear() -> None:
    summary = report(
        (
            observation(
                "six-month",
                lease_rate_bps=d("18.000000"),
                baseline_lease_rate_bps=d("14.000000"),
                futures_basis_bps=d("3.000000"),
            ),
        ),
    )

    assert summary.digest_status == "ready"
    assert summary.recommended_next_step == (
        "allow_report_only_gold_lease_rate_stress_digest"
    )
    assert summary.reason_codes == (
        "market_research_gold_lease_rate_stress_digest_no_stress",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code="market_research_gold_lease_rate_stress_digest_no_stress",
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )


def test_empty_gold_lease_rate_stress_digest_is_blocked_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_gold_lease_rate_stress_digest"
    )
    assert summary.observation_count == ZERO
    assert summary.severe_lease_rate_count == ZERO
    assert summary.elevated_lease_rate_count == ZERO
    assert summary.lease_rate_spike_count == ZERO
    assert summary.backwardation_pressure_count == ZERO
    assert summary.stale_observation_count == ZERO
    assert summary.thin_source_count == ZERO
    assert summary.max_lease_rate_bps == ZERO
    assert summary.average_lease_rate_bps == ZERO
    assert summary.average_lease_rate_delta_bps == ZERO
    assert summary.average_source_count == ZERO
    assert summary.observations == ()
    assert summary.reason_codes == (
        "market_research_gold_lease_rate_stress_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code="market_research_gold_lease_rate_stress_digest_no_inputs",
            count=ZERO,
            observation_ratio=ZERO,
        ),
    )

    public_values = asdict(summary)
    numeric_or_countish = ("count", "ratio", "bps", "seconds", "threshold")
    for name, value in public_values.items():
        if name != "generated_at" and any(fragment in name for fragment in numeric_or_countish):
            if isinstance(value, (dict, list, tuple)):
                continue
            assert isinstance(value, Decimal), (name, value)


def test_gold_lease_rate_stress_dataclasses_are_frozen_and_validate_surface() -> None:
    obs = observation(
        "one-month",
        lease_rate_bps=d("95.000000"),
        baseline_lease_rate_bps=d("50.000000"),
        futures_basis_bps=d("-18.000000"),
    )
    summary = report((obs,))

    with pytest.raises(FrozenInstanceError):
        obs.tenor_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadObservation",
            (MarketResearchGoldLeaseRateStressDigestObservation,),
            {},
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            "bad-time",
            observed_at=datetime(2026, 7, 4, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((obs,), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="Decimal"):
        observation("bad-count", source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation("bad-decimal", lease_rate_bps=_DecimalSubclass("2.0"))
    with pytest.raises(ValueError, match="public identifier"):
        observation("gold-wallet-risk")
    with pytest.raises(ValueError, match="source_reference"):
        observation("bad-source", source_reference="")
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        observation("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="severe_lease_rate_threshold_bps"):
        config(severe_lease_rate_threshold_bps=d("40.000000"))
    with pytest.raises(ValueError, match="observed_at cannot be after generated_at"):
        report((observation("future", observed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_gold_lease_rate_stress_payload_is_json_safe_and_guarded() -> None:
    summary = report(
        (
            observation(
                "one-month",
                lease_rate_bps=d("95.000000"),
                baseline_lease_rate_bps=d("50.000000"),
                futures_basis_bps=d("-18.000000"),
                source_reference="https://vendor.example/gold-lease?token=secret-123",
            ),
        ),
    )

    payload = market_research_gold_lease_rate_stress_digest_payload(summary)

    assert payload == market_research_gold_lease_rate_stress_digest_payload(summary)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["max_lease_rate_bps"] == "95.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["observations"][0]["lease_rate_bps"] == "95.000000"
    assert payload["observations"][0]["futures_basis_bps"] == "-18.000000"
    assert payload["observations"][0]["redacted_source_reference"].startswith("sha256:")
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert "secret-123" not in repr(payload).lower()
    assert "token" not in repr(payload).lower()

    unsafe_report = replace(summary)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_gold_lease_rate_stress_digest_payload(unsafe_report)
    with pytest.raises(ValueError, match="Decimal-derived"):
        market_research_gold_lease_rate_stress_digest_payload(
            {**payload, "observation_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        market_research_gold_lease_rate_stress_digest_payload(
            {**payload, "average_lease_rate_bps": 1.0},
        )
    with pytest.raises(ValueError, match="unsafe"):
        market_research_gold_lease_rate_stress_digest_payload(
            {
                **payload,
                "observations": [
                    {
                        **payload["observations"][0],
                        "operator_token": "redacted",
                    },
                ],
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        market_research_gold_lease_rate_stress_digest_payload(
            {
                **payload,
                "observations": [
                    {
                        **payload["observations"][0],
                        "redacted_source_reference": "https://vendor.example/feed",
                    },
                ],
            },
        )


def test_gold_lease_rate_stress_source_has_no_live_or_durable_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_gold_lease_rate_stress_digest.py"
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
        "subprocess",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
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


def test_gold_lease_rate_stress_import_surface_stays_minimal() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_gold_lease_rate_stress_digest.py"
    )
    tree = ast.parse(module_path.read_text())

    allowed_import_roots = {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] in allowed_import_roots


def test_gold_lease_rate_stress_public_decimal_annotations() -> None:
    numeric_fragments = ("count", "ratio", "bps", "seconds", "threshold")
    for cls in (
        MarketResearchGoldLeaseRateStressDigestConfig,
        MarketResearchGoldLeaseRateStressDigestObservation,
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount,
        MarketResearchGoldLeaseRateStressDigestReport,
    ):
        offenders = [
            (field.name, field.type)
            for field in fields(cls)
            if any(fragment in field.name for fragment in numeric_fragments)
            and field.name != "reason_code_counts"
            and field.type != "Decimal"
            and field.type is not Decimal
        ]
        assert all(
            field.type == "Decimal" or field.type is Decimal
            for field in fields(cls)
            if any(fragment in field.name for fragment in numeric_fragments)
            and field.name != "reason_code_counts"
        ), offenders
