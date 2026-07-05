from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 50, tzinfo=UTC)
CONFIG_VERSION = "market-research-crypto-validator-exit-digest-test-v0"


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt):  # noqa: ANN001
        return None

    def dst(self, dt):  # noqa: ANN001
        return None


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_validator_exit_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    market_id: str = "eth_validator_exit_market",
    chain_id: str = "ethereum",
    validator_id: str = "validator_alpha",
    source_ref: str = "beaconscan_report",
    *,
    observed_at: datetime = OBSERVED_AT,
    exit_status: str = "not_seen",
    source_confidence: Decimal = d("0.800000"),
    source_config_version: str = "validator-source-config-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchCryptoValidatorExitDigestSource(
        market_id=market_id,
        chain_id=chain_id,
        validator_id=validator_id,
        source_ref=source_ref,
        observed_at=observed_at,
        exit_status=exit_status,
        source_confidence=source_confidence,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "min_validator_source_count": d("2.000000"),
        "min_confirmed_exit_ratio": d("0.600000"),
        "max_unconfirmed_exit_age_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchCryptoValidatorExitDigestConfig(**values)


def build_report(*sources, **overrides):
    digest = module()
    values = {
        "sources": sources,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_crypto_validator_exit_digest(**values)


def test_validator_exit_digest_summarizes_blocked_watch_and_clear_rows() -> None:
    report = build_report(
        source(
            "eth_validator_exit_beta",
            "ethereum",
            "validator_beta",
            "beta_beacon_primary",
            exit_status="confirmed",
            source_confidence=d("0.900000"),
        ),
        source(
            "eth_validator_exit_beta",
            "ethereum",
            "validator_beta",
            "beta_beacon_secondary",
            exit_status="confirmed",
            source_confidence=d("0.850000"),
        ),
        source(
            "eth_validator_exit_beta",
            "ethereum",
            "validator_beta",
            "beta_indexer_crosscheck",
            exit_status="not_seen",
            source_confidence=d("0.700000"),
        ),
        source(
            "eth_validator_exit_gamma",
            "ethereum",
            "validator_gamma",
            "gamma_beacon_pending",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            exit_status="pending",
            source_confidence=d("0.650000"),
        ),
        source(
            "eth_validator_exit_alpha",
            "ethereum",
            "validator_alpha",
            "alpha_beacon_primary",
            exit_status="not_seen",
            source_confidence=d("0.950000"),
        ),
        source(
            "eth_validator_exit_alpha",
            "ethereum",
            "validator_alpha",
            "alpha_beacon_secondary",
            exit_status="not_seen",
            source_confidence=d("0.900000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.summary_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_validator_exit"
    )
    assert report.validator_count == d("3.000000")
    assert report.clear_validator_count == d("1.000000")
    assert report.watch_validator_count == d("1.000000")
    assert report.blocked_validator_count == d("1.000000")
    assert report.source_count == d("6.000000")
    assert report.confirmed_validator_count == d("1.000000")
    assert report.confirmed_validator_ratio == d("0.333333")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(
        (row.row_status, row.market_id, row.validator_id) for row in report.rows
    ) == (
        ("blocked", "eth_validator_exit_beta", "validator_beta"),
        ("watch", "eth_validator_exit_gamma", "validator_gamma"),
        ("clear", "eth_validator_exit_alpha", "validator_alpha"),
    )

    beta = report.rows[0]
    assert beta.source_count == d("3.000000")
    assert beta.confirming_source_count == d("2.000000")
    assert beta.not_seen_source_count == d("1.000000")
    assert beta.confirmed_exit_ratio == d("0.666667")
    assert beta.reason_codes == (
        "market_research_crypto_validator_exit_confirmed",
        "market_research_crypto_validator_exit_status_conflict",
    )

    gamma = report.rows[1]
    assert gamma.row_status == "watch"
    assert gamma.max_source_age_seconds == d("7200.000000")
    assert gamma.reason_codes == (
        "market_research_crypto_validator_exit_pending_stale",
        "market_research_crypto_validator_exit_source_gap",
    )

    alpha = report.rows[2]
    assert alpha.row_status == "clear"
    assert alpha.reason_codes == ("market_research_crypto_validator_exit_clear",)
    assert report.reason_codes == (
        "market_research_crypto_validator_exit_confirmed",
        "market_research_crypto_validator_exit_status_conflict",
        "market_research_crypto_validator_exit_pending_stale",
        "market_research_crypto_validator_exit_source_gap",
    )


def test_empty_validator_exit_digest_is_report_only_with_decimal_zeroes() -> None:
    digest = module()
    report = build_report()

    assert report.summary_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_validator_exit"
    )
    assert report.validator_count == d("0.000000")
    assert report.source_count == d("0.000000")
    assert report.confirmed_validator_count == d("0.000000")
    assert report.confirmed_validator_ratio is None
    assert report.max_observed_source_age_seconds is None
    assert report.rows == ()
    assert report.reason_codes == ("market_research_crypto_validator_exit_empty",)
    assert report.reason_code_counts == (
        digest.MarketResearchCryptoValidatorExitDigestReasonCodeCount(
            reason_code="market_research_crypto_validator_exit_empty",
            count=d("1.000000"),
            validator_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_validator_exit_digest_normalizes_timezones_and_rollups() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 13, 55, tzinfo=timezone(timedelta(hours=2)))
    report = build_report(
        source(
            "eth_validator_exit_delta",
            "ethereum",
            "validator_delta",
            "delta_beacon_pending",
            observed_at=observed_at,
            exit_status="pending",
            source_confidence=d("0.700000"),
        ),
        source(
            "eth_validator_exit_delta",
            "ethereum",
            "validator_delta",
            "delta_beacon_unknown",
            exit_status="unknown",
            source_confidence=d("0.600000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].latest_observed_at == datetime(2026, 7, 4, 11, 55, tzinfo=UTC)
    assert report.rows[0].max_source_age_seconds == d("600.000000")
    assert report.max_observed_source_age_seconds == d("600.000000")
    assert report.reason_code_counts == (
        module().MarketResearchCryptoValidatorExitDigestReasonCodeCount(
            reason_code="market_research_crypto_validator_exit_unknown_status",
            count=d("1.000000"),
            validator_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("delta_beacon_pending", "validator-source-config-v0"),
        ("delta_beacon_unknown", "validator-source-config-v0"),
    )


def test_validator_exit_digest_payload_is_json_ready_without_public_float_or_int_numbers() -> None:
    digest = module()
    report = build_report(
        source(
            "eth_validator_exit_payload",
            "ethereum",
            "validator_payload",
            "payload_beacon_confirmed",
            exit_status="confirmed",
            source_confidence=d("0.900000"),
        ),
        source(
            "eth_validator_exit_payload",
            "ethereum",
            "validator_payload",
            "payload_beacon_not_seen",
            exit_status="not_seen",
            source_confidence=d("0.700000"),
        ),
    )

    payload = digest.market_research_crypto_validator_exit_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["validator_count"] == "1.000000"
    assert payload["rows"][0]["confirmed_exit_ratio"] == "0.500000"
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["source_config_versions"] == (
        ("payload_beacon_confirmed", "validator-source-config-v0"),
        ("payload_beacon_not_seen", "validator-source-config-v0"),
    )
    assert not any(type(value) in (float, int) for value in _walk_values(payload))
    for forbidden in ("wallet", "account", "token", "secret", "private_key", "0xabc"):
        assert forbidden not in encoded.lower()


def test_validator_exit_digest_payload_rejects_tampered_nested_public_values() -> None:
    digest = module()
    report = build_report(source(), source(source_ref="secondary_ref"))

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        digest.market_research_crypto_validator_exit_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        digest.market_research_crypto_validator_exit_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "source_count", d("2.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        digest.market_research_crypto_validator_exit_digest_payload(report)


def test_validator_exit_digest_validates_public_dataclasses_and_exact_types() -> None:
    digest = module()

    assert digest.__all__ == (
        "MarketResearchCryptoValidatorExitDigestConfig",
        "MarketResearchCryptoValidatorExitDigestReport",
        "MarketResearchCryptoValidatorExitDigestReasonCodeCount",
        "MarketResearchCryptoValidatorExitDigestRow",
        "MarketResearchCryptoValidatorExitDigestSource",
        "build_market_research_crypto_validator_exit_digest",
        "market_research_crypto_validator_exit_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            with pytest.raises(TypeError, match="subclassing"):
                type(f"{exported_name}Subclass", (value,), {})

    with pytest.raises(FrozenInstanceError):
        replace(config(), config_version=CONFIG_VERSION).paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="market_id"):
        source(market_id=_StringSubclass("eth_validator_exit_market"))
    with pytest.raises(ValueError, match="source_confidence"):
        source(source_confidence=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_confidence"):
        source(source_confidence=Decimal("NaN"))
    with pytest.raises(ValueError, match="min_confirmed_exit_ratio"):
        config(min_confirmed_exit_ratio=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            source(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_report(config=False)
    with pytest.raises(ValueError, match="timezone aware"):
        source(observed_at=datetime(2026, 7, 4, 11, 50))
    with pytest.raises(ValueError, match="timezone aware"):
        source(observed_at=datetime(2026, 7, 4, 11, 50, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="future"):
        build_report(source(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        source(source_ref="wallet_0xabc")
    with pytest.raises(ValueError, match="paper_only"):
        source(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(source(), readonly=False)


def test_validator_exit_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    digest = module()

    with pytest.raises(ValueError, match="unique"):
        build_report(
            source(source_ref="duplicate_ref"),
            source(source_ref="duplicate_ref"),
        )

    row = digest.MarketResearchCryptoValidatorExitDigestRow(
        market_id="eth_validator_exit_alpha",
        chain_id="ethereum",
        validator_id="validator_alpha",
        row_status="clear",
        source_count=d("2.000000"),
        confirming_source_count=d("0.000000"),
        pending_source_count=d("0.000000"),
        not_seen_source_count=d("2.000000"),
        unknown_source_count=d("0.000000"),
        confirmed_exit_ratio=d("0.000000"),
        latest_observed_at=OBSERVED_AT,
        max_source_age_seconds=d("600.000000"),
        reason_codes=("market_research_crypto_validator_exit_clear",),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        summary_status="clear",
        recommended_next_step="allow_report_only_market_research_crypto_validator_exit",
        validator_count=d("1.000000"),
        clear_validator_count=d("1.000000"),
        watch_validator_count=d("0.000000"),
        blocked_validator_count=d("0.000000"),
        source_count=d("2.000000"),
        min_validator_source_count=d("2.000000"),
        min_confirmed_exit_ratio=d("0.600000"),
        max_unconfirmed_exit_age_seconds=d("3600.000000"),
        confirmed_validator_count=d("0.000000"),
        confirmed_validator_ratio=d("0.000000"),
        max_observed_source_age_seconds=d("600.000000"),
        rows=(row,),
        source_config_versions=(
            ("alpha_beacon_primary", "validator-source-config-v0"),
            ("alpha_beacon_secondary", "validator-source-config-v0"),
        ),
        reason_code_counts=(
            digest.MarketResearchCryptoValidatorExitDigestReasonCodeCount(
                reason_code="market_research_crypto_validator_exit_clear",
                count=d("1.000000"),
                validator_ratio=d("1.000000"),
            ),
        ),
        reason_codes=("market_research_crypto_validator_exit_clear",),
    )

    assert digest.MarketResearchCryptoValidatorExitDigestReport(**kwargs).summary_status == "clear"

    with pytest.raises(ValueError, match="reason_codes"):
        digest.MarketResearchCryptoValidatorExitDigestRow(
            **{
                **row.__dict__,
                "row_status": "watch",
                "reason_codes": (
                    "market_research_crypto_validator_exit_source_gap",
                    "market_research_crypto_validator_exit_pending_stale",
                ),
            },
        )
    with pytest.raises(ValueError, match="count"):
        digest.MarketResearchCryptoValidatorExitDigestReasonCodeCount(
            reason_code="market_research_crypto_validator_exit_clear",
            count=d("0.000000"),
            validator_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        digest.MarketResearchCryptoValidatorExitDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    digest.MarketResearchCryptoValidatorExitDigestReasonCodeCount(
                        reason_code="market_research_crypto_validator_exit_clear",
                        count=d("1.000000"),
                        validator_ratio=d("1.000000"),
                    ),
                    digest.MarketResearchCryptoValidatorExitDigestReasonCodeCount(
                        reason_code="market_research_crypto_validator_exit_status_conflict",
                        count=d("1.000000"),
                        validator_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="validator_count"):
        digest.MarketResearchCryptoValidatorExitDigestReport(
            **{**kwargs, "validator_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="summary_status"):
        digest.MarketResearchCryptoValidatorExitDigestReport(
            **{**kwargs, "summary_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        digest.MarketResearchCryptoValidatorExitDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    digest.MarketResearchCryptoValidatorExitDigestReasonCodeCount(
                        reason_code="market_research_crypto_validator_exit_clear",
                        count=d("2.000000"),
                        validator_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_validator_exit_digest_module_scope_excludes_execution_io_and_sensitive_terms() -> None:
    digest = module()
    source_text = digest.__loader__.get_source(digest.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "signing",
        "order",
        "submit",
        "cancel",
        "replace",
        "exchange",
        "account",
        "advice",
        "network",
        "database",
        "persist",
        "supabase",
        "pathlib",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            callee = node.func.id if isinstance(node.func, ast.Name) else None
            assert callee not in {"open", "print", "exec", "eval"}

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "io",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value
