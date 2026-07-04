from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_validator_client_bug_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoValidatorClientBugDigestConfig,
    MarketResearchCryptoValidatorClientBugDigestReasonCodeCount,
    MarketResearchCryptoValidatorClientBugDigestReport,
    MarketResearchCryptoValidatorClientBugDigestRow,
    MarketResearchCryptoValidatorClientBugSnapshot,
    build_market_research_crypto_validator_client_bug_digest,
    market_research_crypto_validator_client_bug_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_crypto_validator_client_bug_digest.py",
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


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCryptoValidatorClientBugDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "max_affected_validator_ratio": d("0.100000"),
        "max_incident_count": d("0.000000"),
        "max_unpatched_ratio": d("0.050000"),
        "max_client_supermajority_ratio": d("0.660000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoValidatorClientBugDigestConfig(**values)


def _snapshot(
    cluster_id: str = "cluster_alpha",
    client_family: str = "geth",
    *,
    network: str = "ethereum",
    observed_at: datetime = GENERATED_AT,
    affected_validator_count: Decimal = d("10.000000"),
    total_validator_count: Decimal = d("1000.000000"),
    incident_count: Decimal = d("0.000000"),
    unpatched_validator_count: Decimal = d("20.000000"),
    client_share: Decimal = d("0.420000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.840000"),
    source_config_version: str = "validator-client-bug-source-v0",
) -> MarketResearchCryptoValidatorClientBugSnapshot:
    return MarketResearchCryptoValidatorClientBugSnapshot(
        cluster_id=cluster_id,
        client_family=client_family,
        network=network,
        observed_at=observed_at,
        affected_validator_count=affected_validator_count,
        total_validator_count=total_validator_count,
        incident_count=incident_count,
        unpatched_validator_count=unpatched_validator_count,
        client_share=client_share,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoValidatorClientBugSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoValidatorClientBugDigestConfig | None = None,
) -> MarketResearchCryptoValidatorClientBugDigestReport:
    return build_market_research_crypto_validator_client_bug_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def test_validator_client_bug_digest_models_bug_exposure_and_patch_risk() -> None:
    report = _report(
        _snapshot(
            "cluster_beta",
            "nethermind",
            network="ethereum",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            affected_validator_count=d("180.000000"),
            total_validator_count=d("1000.000000"),
            incident_count=d("2.000000"),
            unpatched_validator_count=d("150.000000"),
            client_share=d("0.710000"),
            source_count=d("2.000000"),
            confidence=d("0.640000"),
        ),
        _snapshot("cluster_alpha", "geth"),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_validator_client_bug_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.affected_validator_exposure_count == d("1.000000")
    assert report.active_incident_snapshot_count == d("1.000000")
    assert report.unpatched_validator_risk_count == d("1.000000")
    assert report.client_supermajority_risk_count == d("1.000000")
    assert report.source_diversity_gap_snapshot_count == d("1.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_affected_validator_ratio == d("0.095000")
    assert report.average_unpatched_validator_ratio == d("0.085000")
    assert report.average_client_share == d("0.565000")
    assert report.max_snapshot_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.cluster_id, row.client_family) for row in report.rows) == (
        ("cluster_beta", "nethermind"),
        ("cluster_alpha", "geth"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("2400.000000")
    assert beta.affected_validator_ratio == d("0.180000")
    assert beta.unpatched_validator_ratio == d("0.150000")
    assert beta.reason_codes == (
        "market_research_crypto_validator_client_bug_digest_affected_validator_exposure",
        "market_research_crypto_validator_client_bug_digest_active_incident",
        "market_research_crypto_validator_client_bug_digest_unpatched_validator_risk",
        "market_research_crypto_validator_client_bug_digest_client_supermajority_risk",
        "market_research_crypto_validator_client_bug_digest_source_diversity_gap",
        "market_research_crypto_validator_client_bug_digest_stale_snapshot",
        "market_research_crypto_validator_client_bug_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_validator_client_bug_digest_normalizes_timezones_and_reason_counts() -> None:
    generated_at = datetime(2026, 7, 4, 11, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 15, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "cluster_gamma",
            "prysm",
            network="ethereum",
            observed_at=observed_at,
            affected_validator_count=d("0.000000"),
            total_validator_count=d("200.000000"),
            incident_count=d("0.000000"),
            unpatched_validator_count=d("25.000000"),
            client_share=d("0.720000"),
            source_count=d("2.000000"),
            confidence=d("0.740000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoValidatorClientBugDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_validator_client_bug_digest_unpatched_validator_risk"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoValidatorClientBugDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_validator_client_bug_digest_client_supermajority_risk"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoValidatorClientBugDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_validator_client_bug_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoValidatorClientBugDigestReasonCodeCount(
            reason_code="market_research_crypto_validator_client_bug_digest_stale_snapshot",
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("prysm", "validator-client-bug-source-v0"),
    )


def test_validator_client_bug_digest_empty_input_and_sorting_are_deterministic() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_validator_client_bug_digest_no_inputs",
    )

    first = _report(
        _snapshot("cluster_b", "client_b"),
        _snapshot("cluster_a", "client_a"),
    )
    second = _report(
        _snapshot("cluster_a", "client_a"),
        _snapshot("cluster_b", "client_b"),
    )

    assert first == second
    assert tuple(row.client_family for row in first.rows) == ("client_a", "client_b")


def test_validator_client_bug_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoValidatorClientBugDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoValidatorClientBugSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoValidatorClientBugDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoValidatorClientBugDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("validator-client-bug-v0"))
    with pytest.raises(ValueError, match="max_affected_validator_ratio"):
        _config(max_affected_validator_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)
    with pytest.raises(ValueError, match="cluster_id"):
        _snapshot(cluster_id=_StringSubclass("cluster_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _snapshot(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 4, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 4, 15, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="total_validator_count"):
        _snapshot(total_validator_count=d("0.000000"))
    with pytest.raises(ValueError, match="affected_validator_count"):
        _snapshot(affected_validator_count=d("1001.000000"))
    with pytest.raises(ValueError, match="unpatched_validator_count"):
        _snapshot(unpatched_validator_count=d("1001.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_validator_client_bug_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_snapshot())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_ratio")
                or field.name.endswith("_share")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_share")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoValidatorClientBugDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_validator_client_bug_digest"
            ),
            snapshot_count=1,  # type: ignore[arg-type]
            ready_snapshot_count=d("1.000000"),
            watch_snapshot_count=d("0.000000"),
            blocked_snapshot_count=d("0.000000"),
            affected_validator_exposure_count=d("0.000000"),
            active_incident_snapshot_count=d("0.000000"),
            unpatched_validator_risk_count=d("0.000000"),
            client_supermajority_risk_count=d("0.000000"),
            source_diversity_gap_snapshot_count=d("0.000000"),
            stale_snapshot_count=d("0.000000"),
            confidence_gap_snapshot_count=d("0.000000"),
            average_affected_validator_ratio=d("0.010000"),
            average_unpatched_validator_ratio=d("0.020000"),
            average_client_share=d("0.420000"),
            max_snapshot_age_seconds=d("0.000000"),
            max_allowed_snapshot_age_seconds=d("1800.000000"),
            max_allowed_affected_validator_ratio=d("0.100000"),
            max_allowed_incident_count=d("0.000000"),
            max_allowed_unpatched_ratio=d("0.050000"),
            max_allowed_client_supermajority_ratio=d("0.660000"),
            min_source_count=d("3.000000"),
            min_confidence=d("0.700000"),
            rows=report.rows,
            source_config_versions=(("geth", "validator-client-bug-source-v0"),),
            reason_code_counts=report.reason_code_counts,
            reason_codes=(
                "market_research_crypto_validator_client_bug_digest_ready",
            ),
        )


def test_validator_client_bug_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_validator_client_bug_digest_payload(
        _report(_snapshot("cluster_redacted", "geth_redacted")),
    )
    payload_text = repr(payload).lower()

    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "order",
        "token",
        "secret",
        "private",
        "0x",
    ):
        assert forbidden not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_kind"] == (
        "market_research_crypto_validator_client_bug_digest"
    )
    assert_no_floats(payload)
    assert payload["snapshot_count"] == "1.000000"
    assert payload["rows"][0]["client_family"] == "geth_redacted"
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "2.000000"  # type: ignore[index]


def test_validator_client_bug_digest_static_source_is_pure_and_safe() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "token",
        "secret",
        "private",
        "0x",
        "auth",
        "account",
        "balance",
        "cancel",
        "replace",
        "exchange_mutation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_calls = {
        "open",
        "__import__",
        "connect",
        "request",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            assert not isinstance(node.value, int) or isinstance(node.value, bool)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "int", "open", "__import__"}
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def test_validator_client_bug_digest_module_stays_unwired() -> None:
    root = MODULE_PATH.parent
    needle = "market_research_crypto_validator_client_bug_digest"
    references: list[str] = []
    for path in root.glob("*.py"):
        if path == MODULE_PATH:
            continue
        if needle in path.read_text():
            references.append(str(path))

    assert references == []


def test_validator_client_bug_digest_import_surface_is_explicit() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_validator_client_bug_digest",
    )

    assert set(module.__all__) == {
        "DEFAULT_MARKET_RESEARCH_CRYPTO_VALIDATOR_CLIENT_BUG_DIGEST_CONFIG_VERSION",
        "MarketResearchCryptoValidatorClientBugDigestConfig",
        "MarketResearchCryptoValidatorClientBugDigestReasonCodeCount",
        "MarketResearchCryptoValidatorClientBugDigestReport",
        "MarketResearchCryptoValidatorClientBugDigestRow",
        "MarketResearchCryptoValidatorClientBugSnapshot",
        "build_market_research_crypto_validator_client_bug_digest",
        "market_research_crypto_validator_client_bug_digest_payload",
    }
