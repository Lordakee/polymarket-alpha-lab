from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 30, tzinfo=UTC)
CONFIG_VERSION = "market-research-policy-shutdown-risk-digest-test-v0"
MODULE_NAME = "polymarket_alpha_lab.market_research_policy_shutdown_risk_digest"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_policy_shutdown_risk_digest.py",
)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


@dataclass(frozen=True)
class _UnknownPayloadRecord:
    value: Decimal


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # noqa: ANN001, ANN201
        return None

    def dst(self, dt):  # noqa: ANN001, ANN201
        return None


def module():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "elevated_shutdown_probability_threshold": d("0.500000"),
        "material_impact_threshold": d("0.400000"),
        "fresh_signal_max_age_seconds": d("7200.000000"),
        "min_independent_source_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchPolicyShutdownRiskDigestConfig(**values)


def signal(
    market_research_key: str = "condition_alpha",
    policy_jurisdiction: str = "us_federal",
    policy_surface: str = "appropriations",
    source_ref: str = "official_budget_calendar",
    source_family: str = "official",
    *,
    observed_at: datetime = OBSERVED_AT,
    shutdown_probability: Decimal = d("0.200000"),
    impact_score: Decimal = d("0.300000"),
    source_confidence: Decimal = d("0.800000"),
    signal_config_version: str = "policy-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchPolicyShutdownRiskDigestSignal(
        market_research_key=market_research_key,
        policy_jurisdiction=policy_jurisdiction,
        policy_surface=policy_surface,
        source_ref=source_ref,
        source_family=source_family,
        observed_at=observed_at,
        shutdown_probability=shutdown_probability,
        impact_score=impact_score,
        source_confidence=source_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals, **overrides):
    digest = module()
    values = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_policy_shutdown_risk_digest(**values)


def test_policy_shutdown_digest_summarizes_blocked_watch_and_clear_rows() -> None:
    report = build_report(
        signal(
            "condition_beta",
            "us_federal",
            "appropriations",
            "beta_budget_office",
            "official",
            shutdown_probability=d("0.720000"),
            impact_score=d("0.650000"),
            source_confidence=d("0.900000"),
        ),
        signal(
            "condition_beta",
            "us_federal",
            "appropriations",
            "beta_house_calendar",
            "calendar",
            shutdown_probability=d("0.620000"),
            impact_score=d("0.500000"),
            source_confidence=d("0.700000"),
        ),
        signal(
            "condition_gamma",
            "us_state",
            "budget_timing",
            "gamma_state_calendar",
            "calendar",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            shutdown_probability=d("0.250000"),
            impact_score=d("0.200000"),
            source_confidence=d("0.600000"),
        ),
        signal(
            "condition_alpha",
            "us_federal",
            "appropriations",
            "alpha_budget_office",
            "official",
        ),
        signal(
            "condition_alpha",
            "us_federal",
            "appropriations",
            "alpha_public_calendar",
            "calendar",
            shutdown_probability=d("0.100000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_policy_shutdown_risk_digest"
    )
    assert report.policy_surface_count == d("3.000000")
    assert report.blocked_surface_count == d("1.000000")
    assert report.watch_surface_count == d("1.000000")
    assert report.clear_surface_count == d("1.000000")
    assert report.signal_count == d("5.000000")
    assert report.elevated_surface_count == d("1.000000")
    assert report.stale_signal_surface_count == d("1.000000")
    assert report.thin_source_surface_count == d("1.000000")
    assert report.shutdown_risk_surface_ratio == d("0.333333")
    assert report.max_signal_age_seconds == d("9000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_research_key for row in report.rows) == (
        "condition_beta",
        "condition_gamma",
        "condition_alpha",
    )

    beta = report.rows[0]
    assert beta.risk_status == "blocked"
    assert beta.signal_count == d("2.000000")
    assert beta.independent_source_count == d("2.000000")
    assert beta.max_shutdown_probability == d("0.720000")
    assert beta.average_shutdown_probability == d("0.670000")
    assert beta.max_impact_score == d("0.650000")
    assert beta.average_source_confidence == d("0.800000")
    assert beta.reason_codes == (
        "market_research_policy_shutdown_risk_digest_elevated_probability",
        "market_research_policy_shutdown_risk_digest_material_impact",
    )

    gamma = report.rows[1]
    assert gamma.risk_status == "watch"
    assert gamma.stale_signal_count == d("1.000000")
    assert gamma.reason_codes == (
        "market_research_policy_shutdown_risk_digest_stale_signal",
        "market_research_policy_shutdown_risk_digest_thin_source_coverage",
    )

    alpha = report.rows[2]
    assert alpha.risk_status == "clear"
    assert alpha.reason_codes == (
        "market_research_policy_shutdown_risk_digest_clear",
    )

    assert report.reason_codes == (
        "market_research_policy_shutdown_risk_digest_elevated_probability",
        "market_research_policy_shutdown_risk_digest_material_impact",
        "market_research_policy_shutdown_risk_digest_stale_signal",
        "market_research_policy_shutdown_risk_digest_thin_source_coverage",
    )


def test_policy_shutdown_digest_handles_empty_inputs_with_decimal_counts() -> None:
    report = build_report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_policy_shutdown_risk_digest"
    )
    assert report.policy_surface_count == d("0.000000")
    assert report.signal_count == d("0.000000")
    assert report.shutdown_risk_surface_ratio == d("0.000000")
    assert report.max_signal_age_seconds is None
    assert report.rows == ()
    assert report.reason_code_counts == (
        module().MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
            reason_code="market_research_policy_shutdown_risk_digest_empty",
            count=d("1.000000"),
            surface_ratio=d("0.000000"),
        ),
    )
    assert report.reason_codes == (
        "market_research_policy_shutdown_risk_digest_empty",
    )
    assert all(
        field.type in {"Decimal", "Decimal | None"}
        for field in fields(type(report))
        if ("count" in field.name or "ratio" in field.name)
        and field.name != "reason_code_counts"
    )


def test_policy_shutdown_digest_normalizes_timezones_and_rollups() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = build_report(
        signal(
            "condition_delta",
            "us_federal",
            "funding_deadline",
            "delta_calendar",
            "calendar",
            observed_at=observed_at,
            shutdown_probability=d("0.550000"),
            impact_score=d("0.250000"),
            source_confidence=d("0.600000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.max_signal_age_seconds == d("3600.000000")
    assert report.reason_code_counts == (
        module().MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
            reason_code=(
                "market_research_policy_shutdown_risk_digest_elevated_probability"
            ),
            count=d("1.000000"),
            surface_ratio=d("1.000000"),
        ),
        module().MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
            reason_code="market_research_policy_shutdown_risk_digest_thin_source_coverage",
            count=d("1.000000"),
            surface_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("delta_calendar", "policy-signal-v0"),
    )


def test_policy_shutdown_payload_uses_decimal_strings_and_redacted_references() -> None:
    digest = module()
    report = build_report(
        signal(
            "condition_payload",
            "us_federal",
            "appropriations",
            "payload_official_source",
            "official",
            shutdown_probability=d("0.600000"),
            impact_score=d("0.500000"),
            source_confidence=d("0.900000"),
        ),
        signal(
            "condition_payload",
            "us_federal",
            "appropriations",
            "payload_calendar_source",
            "calendar",
            shutdown_probability=d("0.400000"),
            impact_score=d("0.300000"),
            source_confidence=d("0.700000"),
        ),
    )

    payload = digest.market_research_policy_shutdown_risk_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["policy_surface_count"] == "1.000000"
    assert payload["rows"][0]["average_shutdown_probability"] == "0.500000"
    assert not any(
        type(value) in {float, int}
        for value in _walk_values(payload)
        if type(value) is not bool
    )
    for forbidden in ("wallet", "account", "token", "secret", "private_key", "0xabc"):
        assert forbidden not in encoded.lower()


def test_policy_shutdown_payload_revalidates_tampered_public_records() -> None:
    digest = module()

    tampered_flag_report = build_report(
        signal(
            "condition_nested_flag",
            "us_federal",
            "appropriations",
            "nested_flag_source",
            "official",
        ),
    )
    object.__setattr__(tampered_flag_report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        digest.market_research_policy_shutdown_risk_digest_payload(tampered_flag_report)

    tampered_decimal_report = build_report(
        signal(
            "condition_decimal_scale",
            "us_federal",
            "appropriations",
            "decimal_scale_source",
            "official",
        ),
    )
    object.__setattr__(
        tampered_decimal_report.rows[0],
        "signal_count",
        Decimal("1.0000000"),
    )
    with pytest.raises(ValueError, match="signal_count must be a six-decimal Decimal"):
        digest.market_research_policy_shutdown_risk_digest_payload(tampered_decimal_report)

    tampered_nested_type_report = build_report(
        signal(
            "condition_nested_type",
            "us_federal",
            "appropriations",
            "nested_type_source",
            "official",
        ),
    )
    object.__setattr__(
        tampered_nested_type_report,
        "reason_code_counts",
        (("market_research_policy_shutdown_risk_digest_thin_source_coverage",),),
    )
    with pytest.raises(ValueError, match="reason_code_counts must contain"):
        digest.market_research_policy_shutdown_risk_digest_payload(
            tampered_nested_type_report,
        )


def test_policy_shutdown_payload_helpers_reject_unvalidated_public_values() -> None:
    digest = module()

    with pytest.raises(ValueError, match="unsupported public dataclass"):
        digest._to_payload(_UnknownPayloadRecord(d("1.000000")))

    with pytest.raises(ValueError, match="UTC-aware"):
        digest._to_payload(datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))))

    with pytest.raises(ValueError, match="six-decimal Decimal"):
        digest._to_payload(Decimal("1.0000000"))

    for raw_container in (
        [d("1.000000")],
        {"value": d("1.000000")},
        {d("1.000000")},
    ):
        with pytest.raises(ValueError, match="unsupported public value"):
            digest._to_payload(raw_container)


def test_policy_shutdown_digest_validates_exact_public_types_and_flags() -> None:
    digest = module()

    assert digest.__all__ == (
        "MarketResearchPolicyShutdownRiskDigestConfig",
        "MarketResearchPolicyShutdownRiskDigestReasonCodeCount",
        "MarketResearchPolicyShutdownRiskDigestReport",
        "MarketResearchPolicyShutdownRiskDigestRow",
        "MarketResearchPolicyShutdownRiskDigestSignal",
        "build_market_research_policy_shutdown_risk_digest",
        "market_research_policy_shutdown_risk_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        replace(config(), config_version=CONFIG_VERSION).paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="market_research_key"):
        signal(market_research_key=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="shutdown_probability"):
        signal(shutdown_probability=0.6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="impact_score"):
        signal(impact_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="material_impact_threshold"):
        config(material_impact_threshold=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            signal(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone"):
        signal(observed_at=datetime(2026, 7, 4, 11, 0))
    with pytest.raises(ValueError, match="timezone"):
        signal(observed_at=datetime(2026, 7, 4, 11, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        signal(source_ref="wallet_0xabc")
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(signal(), readonly=False)


def test_policy_shutdown_digest_public_dataclasses_reject_subclassing() -> None:
    digest = module()

    for name in (
        "MarketResearchPolicyShutdownRiskDigestConfig",
        "MarketResearchPolicyShutdownRiskDigestSignal",
        "MarketResearchPolicyShutdownRiskDigestRow",
        "MarketResearchPolicyShutdownRiskDigestReasonCodeCount",
        "MarketResearchPolicyShutdownRiskDigestReport",
    ):
        public_type = getattr(digest, name)
        assert "__init_subclass__" in public_type.__dict__
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{name}Subclass", (public_type,), {})


def test_policy_shutdown_digest_rejects_duplicates_and_bad_consistency() -> None:
    digest = module()

    with pytest.raises(ValueError, match="unique"):
        build_report(
            signal(source_ref="duplicate_ref"),
            signal(source_ref="duplicate_ref"),
        )

    row = digest.MarketResearchPolicyShutdownRiskDigestRow(
        market_research_key="condition_alpha",
        policy_jurisdiction="us_federal",
        policy_surface="appropriations",
        risk_status="clear",
        signal_count=d("2.000000"),
        independent_source_count=d("2.000000"),
        stale_signal_count=d("0.000000"),
        max_shutdown_probability=d("0.200000"),
        average_shutdown_probability=d("0.150000"),
        max_impact_score=d("0.300000"),
        average_source_confidence=d("0.800000"),
        reason_codes=("market_research_policy_shutdown_risk_digest_clear",),
    )
    reason_count = digest.MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
        reason_code="market_research_policy_shutdown_risk_digest_clear",
        count=d("1.000000"),
        surface_ratio=d("1.000000"),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        digest_status="clear",
        recommended_next_step=(
            "allow_report_only_market_research_policy_shutdown_risk_digest"
        ),
        policy_surface_count=d("1.000000"),
        clear_surface_count=d("1.000000"),
        watch_surface_count=d("0.000000"),
        blocked_surface_count=d("0.000000"),
        signal_count=d("2.000000"),
        elevated_surface_count=d("0.000000"),
        stale_signal_surface_count=d("0.000000"),
        thin_source_surface_count=d("0.000000"),
        shutdown_risk_surface_ratio=d("0.000000"),
        max_signal_age_seconds=d("1800.000000"),
        elevated_shutdown_probability_threshold=d("0.500000"),
        material_impact_threshold=d("0.400000"),
        fresh_signal_max_age_seconds=d("7200.000000"),
        min_independent_source_count=d("2.000000"),
        rows=(row,),
        source_config_versions=(
            ("alpha_budget_office", "policy-signal-v0"),
            ("alpha_public_calendar", "policy-signal-v0"),
        ),
        reason_code_counts=(reason_count,),
        reason_codes=("market_research_policy_shutdown_risk_digest_clear",),
    )

    assert digest.MarketResearchPolicyShutdownRiskDigestReport(**kwargs).digest_status == "clear"

    with pytest.raises(ValueError, match="policy_surface_count"):
        digest.MarketResearchPolicyShutdownRiskDigestReport(
            **{**kwargs, "policy_surface_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        digest.MarketResearchPolicyShutdownRiskDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        digest.MarketResearchPolicyShutdownRiskDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    digest.MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
                        reason_code="market_research_policy_shutdown_risk_digest_clear",
                        count=d("2.000000"),
                        surface_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="count"):
        digest.MarketResearchPolicyShutdownRiskDigestReasonCodeCount(
            reason_code="market_research_policy_shutdown_risk_digest_clear",
            count=d("0.000000"),
            surface_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        digest.MarketResearchPolicyShutdownRiskDigestReport(
            **{**kwargs, "paper_only": False},
        )

    ordered_report = build_report(
        signal(
            "condition_alpha",
            "us_federal",
            "appropriations",
            "ordered_alpha_source",
            "official",
        ),
        signal(
            "condition_beta",
            "us_federal",
            "appropriations",
            "ordered_beta_source",
            "official",
            shutdown_probability=d("0.700000"),
            impact_score=d("0.600000"),
        ),
    )
    with pytest.raises(ValueError, match="rows must be deterministic"):
        replace(ordered_report, rows=tuple(reversed(ordered_report.rows)))


def test_policy_shutdown_digest_source_excludes_execution_io_and_sensitive_terms() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange_mutation",
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
