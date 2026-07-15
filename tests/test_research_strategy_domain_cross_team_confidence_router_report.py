from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_domain_cross_team_confidence_router_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api():
    return import_module(
        "polymarket_alpha_lab."
        "research_strategy_domain_cross_team_confidence_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(assessment_label: str = "alpha-private-candidate", **overrides: object):
    module = api()
    values = {
        "domain_key": "macro",
        "team_key": "forecast",
        "assessment_label": assessment_label,
        "observed_at": GENERATED_AT - timedelta(seconds=1800),
        "local_confidence_score": d("0.880000"),
        "cross_team_agreement_score": d("0.840000"),
        "evidence_support_score": d("0.800000"),
        "handoff_completeness_score": d("0.900000"),
        "conflict_pressure_score": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainCrossTeamConfidenceRouterInput(**values)


def report(*values: object, config: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_domain_cross_team_confidence_router_report(
        values,
        config=config or module.ResearchStrategyDomainCrossTeamConfidenceRouterConfig(),
        generated_at=generated_at,
    )


def assert_public_numeric_payload(value: Any) -> None:
    assert not isinstance(value, float)
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for item_value in value.values():
            assert_public_numeric_payload(item_value)
    elif isinstance(value, list):
        for item_value in value:
            assert_public_numeric_payload(item_value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("public_payload_sha256", None)
    return hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def test_router_report_rolls_up_cross_team_confidence_without_raw_identifiers() -> None:
    module = api()
    passing = signal()
    watched = signal(
        "watched-private-candidate",
        domain_key="sports",
        team_key="review",
        observed_at=GENERATED_AT - timedelta(seconds=9000),
        local_confidence_score=d("0.640000"),
        cross_team_agreement_score=d("0.620000"),
        evidence_support_score=d("0.600000"),
        handoff_completeness_score=d("0.580000"),
        conflict_pressure_score=d("0.300000"),
    )
    blocked = signal(
        "blocked-private-candidate",
        domain_key="crypto",
        team_key="challenge",
        observed_at=GENERATED_AT - timedelta(seconds=30000),
        local_confidence_score=d("0.450000"),
        cross_team_agreement_score=d("0.420000"),
        evidence_support_score=d("0.400000"),
        handoff_completeness_score=d("0.350000"),
        conflict_pressure_score=d("0.820000"),
    )

    routed = report(passing, watched, blocked)
    rebuilt = report(blocked, passing, watched)
    changed = report(
        passing,
        watched,
        signal(
            "blocked-private-candidate",
            domain_key="crypto",
            team_key="challenge",
            observed_at=GENERATED_AT - timedelta(seconds=30000),
            local_confidence_score=d("0.500000"),
            cross_team_agreement_score=d("0.420000"),
            evidence_support_score=d("0.400000"),
            handoff_completeness_score=d("0.350000"),
            conflict_pressure_score=d("0.820000"),
        ),
    )

    assert is_dataclass(routed)
    assert routed.generated_at == GENERATED_AT
    assert routed.config_version == (
        "research-strategy-domain-cross-team-confidence-router-report-v0"
    )
    assert routed.signal_count == d("3.000000")
    assert routed.domain_count == d("3.000000")
    assert routed.team_count == d("3.000000")
    assert routed.pass_count == d("1.000000")
    assert routed.watch_count == d("1.000000")
    assert routed.block_count == d("1.000000")
    assert routed.status == "block"
    assert routed.average_router_confidence_score == d("0.624667")
    assert routed.average_conflict_pressure_score == d("0.390000")
    assert routed.highest_conflict_pressure_score == d("0.820000")
    assert routed.oldest_assessment_age_seconds == d("30000.000000")
    assert routed.reason_codes == (
        "domain_cross_team_confidence_router_report_block",
        "router_confidence_score_block",
        "router_confidence_score_watch",
        "local_confidence_score_block",
        "local_confidence_score_watch",
        "cross_team_agreement_score_block",
        "cross_team_agreement_score_watch",
        "evidence_support_score_block",
        "evidence_support_score_watch",
        "handoff_completeness_score_block",
        "handoff_completeness_score_watch",
        "conflict_pressure_score_block",
        "conflict_pressure_score_watch",
    )
    assert routed.paper_only is True
    assert routed.report_only is True
    assert routed.readonly is True

    assert tuple(row.status for row in routed.rows) == ("block", "watch", "pass")
    blocked_row, watched_row, passing_row = routed.rows
    assert blocked_row.rank == d("1.000000")
    assert blocked_row.domain_key == "crypto"
    assert blocked_row.team_key == "challenge"
    assert blocked_row.assessment_digest == hashlib.sha256(
        b"blocked-private-candidate",
    ).hexdigest()
    assert blocked_row.router_confidence_score == d("0.389000")
    assert blocked_row.assessment_age_seconds == d("30000.000000")
    assert blocked_row.reason_codes == (
        "router_confidence_score_block",
        "local_confidence_score_block",
        "cross_team_agreement_score_block",
        "evidence_support_score_block",
        "handoff_completeness_score_block",
        "conflict_pressure_score_block",
    )
    assert watched_row.router_confidence_score == d("0.623000")
    assert watched_row.reason_codes == (
        "router_confidence_score_watch",
        "local_confidence_score_watch",
        "cross_team_agreement_score_watch",
        "evidence_support_score_watch",
        "handoff_completeness_score_watch",
        "conflict_pressure_score_watch",
    )
    assert passing_row.reason_codes == ("router_confidence_score_pass",)
    assert tuple(row.human_review_required for row in routed.rows) == (
        True,
        True,
        False,
    )
    assert tuple(row.human_review_route for row in routed.rows) == (
        "priority_review",
        "standard_review",
        "no_review",
    )
    assert routed.human_review_required_count == d("2.000000")
    assert routed.priority_review_count == d("1.000000")
    assert routed.standard_review_count == d("1.000000")

    payload = module.research_strategy_domain_cross_team_confidence_router_report_payload(
        routed,
    )
    assert payload["public_payload_sha256"] == routed.public_payload_sha256
    assert len(payload["public_payload_sha256"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["public_payload_sha256"])
    assert payload == (
        module.research_strategy_domain_cross_team_confidence_router_report_payload(
            rebuilt,
        )
    )
    assert routed.public_payload_sha256 != changed.public_payload_sha256
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "alpha-private-candidate",
        "watched-private-candidate",
        "blocked-private-candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in encoded.lower()
    assert_public_numeric_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_inputs_block_at_report_only_boundary() -> None:
    module = api()
    routed = report()

    assert routed.status == "block"
    assert routed.signal_count == d("0.000000")
    assert routed.domain_count == d("0.000000")
    assert routed.team_count == d("0.000000")
    assert routed.pass_count == d("0.000000")
    assert routed.watch_count == d("0.000000")
    assert routed.block_count == d("0.000000")
    assert routed.rows == ()
    assert routed.reason_codes == ("empty_domain_cross_team_confidence_router_inputs",)
    assert routed.reason_code_counts == (
        module.ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
            reason_code="empty_domain_cross_team_confidence_router_inputs",
            count=d("1.000000"),
        ),
    )
    assert routed.paper_only is True
    assert routed.report_only is True
    assert routed.readonly is True


def test_public_payload_serializes_decimal_strings_and_validates_sha256_digest() -> None:
    module = api()
    routed = report(signal())

    payload = module.research_strategy_domain_cross_team_confidence_router_report_payload(
        routed,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["local_confidence_score"] == "0.880000"
    assert payload["rows"][0]["assessment_age_seconds"] == "1800.000000"
    assert payload["rows"][0]["assessment_digest"] == hashlib.sha256(
        b"alpha-private-candidate",
    ).hexdigest()

    with pytest.raises(ValueError, match="public_payload_sha256"):
        replace(routed, public_payload_sha256="0" * 64)

    tampered = replace(routed)
    object.__setattr__(tampered, "public_payload_sha256", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_sha256"):
        module.research_strategy_domain_cross_team_confidence_router_report_payload(
            tampered,
        )


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values() -> None:
    shifted = report(
        signal(
            observed_at=datetime(2026, 7, 9, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        generated_at=GENERATED_AT,
    )

    assert shifted.rows[0].observed_at == datetime(2026, 7, 9, 11, 0, tzinfo=UTC)
    assert shifted.rows[0].assessment_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal(), generated_at=datetime(2026, 7, 9, 12, 0))


def test_report_is_frozen_decimal_only_flagged_safe_and_revalidated() -> None:
    module = api()
    routed = report(signal())

    assert module.RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_STATUSES",
        "ResearchStrategyDomainCrossTeamConfidenceRouterConfig",
        "ResearchStrategyDomainCrossTeamConfidenceRouterInput",
        "ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount",
        "ResearchStrategyDomainCrossTeamConfidenceRouterReport",
        "ResearchStrategyDomainCrossTeamConfidenceRouterRow",
        "build_research_strategy_domain_cross_team_confidence_router_report",
        "research_strategy_domain_cross_team_confidence_router_report_payload",
        "validate_research_strategy_domain_cross_team_confidence_router_public_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        routed.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        routed.rows[0].local_confidence_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(module.ResearchStrategyDomainCrossTeamConfidenceRouterConfig(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(routed, readonly=False)
    with pytest.raises(ValueError, match="signal_count"):
        replace(routed, signal_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(routed, status="watch")
    with pytest.raises(ValueError, match="local_confidence_score"):
        signal(local_confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_support_score"):
        signal(evidence_support_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="restricted"):
        signal(domain_key="market_slug_raw")
    with pytest.raises(ValueError, match="assessment_label"):
        signal(assessment_label="https://example.invalid/item")

    object.__setattr__(routed.rows[0], "assessment_digest", "source_url:https")
    with pytest.raises(ValueError, match="assessment_digest"):
        module.research_strategy_domain_cross_team_confidence_router_report_payload(
            routed,
        )


def test_public_dataclasses_are_slotted_without_instance_dicts() -> None:
    module = api()
    values = (
        module.ResearchStrategyDomainCrossTeamConfidenceRouterConfig(),
        signal(),
        module.ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
            reason_code="empty_domain_cross_team_confidence_router_inputs",
            count=d("1.000000"),
        ),
        report(signal()).rows[0],
        report(signal()),
    )

    for value in values:
        assert hasattr(type(value), "__slots__")
        assert not hasattr(value, "__dict__")


def test_build_revalidates_mutated_input_before_hashing_or_reduction() -> None:
    mutated = signal()
    object.__setattr__(mutated, "assessment_label", "https://example.invalid/unsafe")

    with pytest.raises(ValueError, match="assessment_label|restricted|unsafe"):
        report(mutated)

    object.__setattr__(mutated, "assessment_label", "safe-public-label")
    object.__setattr__(mutated, "observed_at", datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at|timezone"):
        report(mutated)


def test_build_revalidates_mutated_config_before_scoring() -> None:
    module = api()
    mutated = module.ResearchStrategyDomainCrossTeamConfidenceRouterConfig()
    object.__setattr__(mutated, "pass_threshold", d("NaN"))

    with pytest.raises(ValueError, match="pass_threshold|finite"):
        report(signal(), config=mutated)


def test_public_validator_rejects_non_exact_string_schema_keys_after_resigning() -> None:
    module = api()
    payload = module.research_strategy_domain_cross_team_confidence_router_report_payload(
        report(signal()),
    )
    subclass_key_payload = {
        _StringSubclass(key): value for key, value in payload.items()
    }
    subclass_key_payload["public_payload_sha256"] = canonical_digest(
        subclass_key_payload,
    )

    with pytest.raises(ValueError, match="canonical schema|field sequence"):
        module.validate_research_strategy_domain_cross_team_confidence_router_public_payload(
            subclass_key_payload,
        )


def test_large_finite_measure_values_use_value_error_boundary() -> None:
    with pytest.raises(ValueError, match="oldest_assessment_age_seconds"):
        replace(report(signal()), oldest_assessment_age_seconds=d("1e1000"))


def test_decimal_context_raw_bounds_signed_zero_and_non_finite_are_hardened() -> None:
    baseline = report(
        signal(
            local_confidence_score=d("0.999999"),
            cross_team_agreement_score=d("0.888888"),
            evidence_support_score=d("0.777777"),
            handoff_completeness_score=d("0.666666"),
            conflict_pressure_score=d("0.111111"),
        ),
        signal(
            "second-private-candidate",
            domain_key="politics",
            team_key="challenge",
            local_confidence_score=d("0.123456"),
            cross_team_agreement_score=d("0.234567"),
            evidence_support_score=d("0.345678"),
            handoff_completeness_score=d("0.456789"),
            conflict_pressure_score=d("0.654321"),
        ),
    )
    baseline_payload = api().research_strategy_domain_cross_team_confidence_router_report_payload(
        baseline,
    )

    with localcontext(Context(prec=6, rounding=ROUND_DOWN)):
        constrained = report(
            signal(
                local_confidence_score=d("0.999999"),
                cross_team_agreement_score=d("0.888888"),
                evidence_support_score=d("0.777777"),
                handoff_completeness_score=d("0.666666"),
                conflict_pressure_score=d("0.111111"),
            ),
            signal(
                "second-private-candidate",
                domain_key="politics",
                team_key="challenge",
                local_confidence_score=d("0.123456"),
                cross_team_agreement_score=d("0.234567"),
                evidence_support_score=d("0.345678"),
                handoff_completeness_score=d("0.456789"),
                conflict_pressure_score=d("0.654321"),
            ),
        )
        constrained_payload = (
            api().research_strategy_domain_cross_team_confidence_router_report_payload(
                constrained,
            )
        )
    assert constrained_payload == baseline_payload

    with pytest.raises(ValueError, match="between zero and one"):
        signal(local_confidence_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="between zero and one"):
        signal(conflict_pressure_score=d("1.0000004"))
    with pytest.raises(ValueError, match="nonnegative"):
        replace(report(signal()), oldest_assessment_age_seconds=d("-0.0000004"))
    for non_finite in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            signal(evidence_support_score=d(non_finite))
    for signed_zero in ("-0", "-0.000000"):
        with pytest.raises(ValueError, match="signed zero"):
            signal(handoff_completeness_score=d(signed_zero))


def test_public_dataclasses_are_frozen_exact_and_non_subclassable() -> None:
    module = api()
    dataclass_types = (
        module.ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
        module.ResearchStrategyDomainCrossTeamConfidenceRouterInput,
        module.ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount,
        module.ResearchStrategyDomainCrossTeamConfidenceRouterRow,
        module.ResearchStrategyDomainCrossTeamConfidenceRouterReport,
    )

    for dataclass_type in dataclass_types:
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Invalid{dataclass_type.__name__}", (dataclass_type,), {})


def test_payload_uses_exact_canonical_schema_and_stable_tie_breaks() -> None:
    module = api()
    tied = (
        signal(
            "zeta-private-candidate",
            domain_key="politics",
            team_key="zeta",
        ),
        signal(
            "beta-private-candidate",
            domain_key="macro",
            team_key="beta",
        ),
        signal(
            "alpha-private-candidate",
            domain_key="macro",
            team_key="alpha",
        ),
    )

    routed = report(*reversed(tied))
    payload = module.research_strategy_domain_cross_team_confidence_router_report_payload(
        routed,
    )

    assert tuple((row.domain_key, row.team_key) for row in routed.rows) == (
        ("macro", "alpha"),
        ("macro", "beta"),
        ("politics", "zeta"),
    )
    assert tuple(payload) == tuple(field.name for field in fields(routed))
    assert tuple(payload["rows"][0]) == tuple(
        field.name for field in fields(routed.rows[0])
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name for field in fields(routed.reason_code_counts[0])
    )

    reordered_report = dict(reversed(tuple(payload.items())))
    reordered_report["public_payload_sha256"] = canonical_digest(reordered_report)
    with pytest.raises(ValueError, match="canonical field sequence"):
        module.validate_research_strategy_domain_cross_team_confidence_router_public_payload(
            reordered_report,
        )

    reordered_row = json.loads(json.dumps(payload))
    reordered_row["rows"][0] = dict(reversed(tuple(reordered_row["rows"][0].items())))
    reordered_row["public_payload_sha256"] = canonical_digest(reordered_row)
    with pytest.raises(ValueError, match="canonical field sequence"):
        module.validate_research_strategy_domain_cross_team_confidence_router_public_payload(
            reordered_row,
        )


def test_private_team_and_source_identifiers_are_redacted() -> None:
    for domain_key, team_key in (
        ("macro", "internal_rates"),
        ("internal_source", "forecast"),
        ("macro", "confidential_rates"),
        ("proprietary_source", "forecast"),
        ("macro", "private_forecast"),
        ("macro", "prіvate_forecast"),
    ):
        with pytest.raises(ValueError, match="restricted|public"):
            signal(domain_key=domain_key, team_key=team_key)

    routed = report(signal("private-source-record"))
    encoded = json.dumps(
        api().research_strategy_domain_cross_team_confidence_router_report_payload(
            routed,
        ),
        sort_keys=True,
    )
    assert "private-source-record" not in encoded


def test_public_validator_recomputes_all_derived_fields_after_resigning() -> None:
    module = api()
    routed = report(
        signal(
            local_confidence_score=d("0.640000"),
            cross_team_agreement_score=d("0.620000"),
            evidence_support_score=d("0.600000"),
            handoff_completeness_score=d("0.580000"),
            conflict_pressure_score=d("0.300000"),
        ),
    )
    payload = module.research_strategy_domain_cross_team_confidence_router_report_payload(
        routed,
    )

    assert module.validate_research_strategy_domain_cross_team_confidence_router_public_payload(
        payload,
    )

    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["status"] = "pass"
    forged["rows"][0]["human_review_required"] = False
    forged["rows"][0]["human_review_route"] = "no_review"
    forged["rows"][0]["reason_codes"] = ["router_confidence_score_pass"]
    forged["status"] = "pass"
    forged["pass_count"] = "1.000000"
    forged["watch_count"] = "0.000000"
    forged["human_review_required_count"] = "0.000000"
    forged["standard_review_count"] = "0.000000"
    forged["reason_codes"] = [
        "domain_cross_team_confidence_router_report_pass",
        "router_confidence_score_pass",
    ]
    forged["reason_code_counts"] = [
        {
            "reason_code": "router_confidence_score_pass",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    forged["public_payload_sha256"] = canonical_digest(forged)

    with pytest.raises(ValueError, match="status|reason_codes|human_review"):
        module.validate_research_strategy_domain_cross_team_confidence_router_public_payload(
            forged,
        )


def test_rejects_trade_and_execution_public_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="domain_key"):
        signal(domain_key="trade-router")
    with pytest.raises(ValueError, match="team_key"):
        signal(team_key="execution")
    with pytest.raises(ValueError, match="assessment_label"):
        signal(assessment_label="execute-router-note")

    routed = report(signal())
    object.__setattr__(routed.rows[0], "domain_key", "trade-router")
    with pytest.raises(ValueError, match="domain_key"):
        module.research_strategy_domain_cross_team_confidence_router_report_payload(
            routed,
        )


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"__import__", "float", "open", "request", "write"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in {
                    "connect",
                    "execute",
                    "write",
                    "write_bytes",
                    "write_text",
                }

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
