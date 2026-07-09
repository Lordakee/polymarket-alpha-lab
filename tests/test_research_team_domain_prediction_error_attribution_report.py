from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256

import pytest

from polymarket_alpha_lab.research_team_domain_prediction_error_attribution_report import (
    DEFAULT_RESEARCH_TEAM_DOMAIN_PREDICTION_ERROR_ATTRIBUTION_CONFIG_VERSION,
    ResearchTeamDomainPredictionErrorAttributionConfig,
    ResearchTeamDomainPredictionErrorAttributionInputRow,
    ResearchTeamDomainPredictionErrorAttributionReasonCodeCount,
    ResearchTeamDomainPredictionErrorAttributionReport,
    ResearchTeamDomainPredictionErrorAttributionRow,
    build_research_team_domain_prediction_error_attribution_report,
    research_team_domain_prediction_error_attribution_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamDomainPredictionErrorAttributionConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_TEAM_DOMAIN_PREDICTION_ERROR_ATTRIBUTION_CONFIG_VERSION
        ),
        "material_error_watch_threshold": d("0.100000"),
        "material_error_block_threshold": d("0.350000"),
        "component_watch_threshold": d("0.200000"),
        "component_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return ResearchTeamDomainPredictionErrorAttributionConfig(**values)


def input_row(
    review_key: str = "domain.energy.pass",
    *,
    domain_team: str = "energy_research",
    prediction_family: str = "policy_supply",
    attribution_reference: str = "public-attribution-memo",
    prediction_made_at: datetime | None = None,
    resolved_at: datetime | None = None,
    review_started_at: datetime | None = None,
    review_completed_at: datetime | None = None,
    predicted_probability: Decimal = d("0.520000"),
    resolved_probability: Decimal = d("0.560000"),
    evidence_gap_score: Decimal = d("0.050000"),
    stale_memory_score: Decimal = d("0.050000"),
    source_conflict_handling_score: Decimal = d("0.050000"),
    cost_assumption_score: Decimal = d("0.050000"),
    resolution_ambiguity_score: Decimal = d("0.050000"),
    review_latency_score: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamDomainPredictionErrorAttributionInputRow:
    return ResearchTeamDomainPredictionErrorAttributionInputRow(
        review_key=review_key,
        domain_team=domain_team,
        prediction_family=prediction_family,
        attribution_reference=attribution_reference,
        prediction_made_at=prediction_made_at or GENERATED_AT - timedelta(days=3),
        resolved_at=resolved_at or GENERATED_AT - timedelta(hours=2),
        review_started_at=review_started_at or GENERATED_AT - timedelta(hours=5),
        review_completed_at=review_completed_at or GENERATED_AT - timedelta(hours=1),
        predicted_probability=predicted_probability,
        resolved_probability=resolved_probability,
        evidence_gap_score=evidence_gap_score,
        stale_memory_score=stale_memory_score,
        source_conflict_handling_score=source_conflict_handling_score,
        cost_assumption_score=cost_assumption_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        review_latency_score=review_latency_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchTeamDomainPredictionErrorAttributionInputRow, ...],
    *,
    cfg: ResearchTeamDomainPredictionErrorAttributionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamDomainPredictionErrorAttributionReport:
    return build_research_team_domain_prediction_error_attribution_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        nested: list[object] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def resign_payload(payload: dict[str, object]) -> None:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def test_domain_prediction_error_attribution_reduces_rows_and_redacts() -> None:
    summary = report(
        (
            input_row(
                "domain.energy.watch",
                attribution_reference="public-attribution-notice",
                predicted_probability=d("0.600000"),
                resolved_probability=d("0.450000"),
                evidence_gap_score=d("0.320000"),
                source_conflict_handling_score=d("0.250000"),
                cost_assumption_score=d("0.300000"),
                review_latency_score=d("0.210000"),
            ),
            input_row(
                "domain.energy.block",
                attribution_reference="https://private.example/evidence?token=hidden",
                predicted_probability=d("0.200000"),
                resolved_probability=d("0.900000"),
                stale_memory_score=d("0.610000"),
                cost_assumption_score=d("0.620000"),
                resolution_ambiguity_score=d("0.720000"),
                review_latency_score=d("0.650000"),
            ),
            input_row(),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_TEAM_DOMAIN_PREDICTION_ERROR_ATTRIBUTION_CONFIG_VERSION
    )
    assert summary.attribution_status == "block"
    assert summary.next_step == "block_report_only_domain_prediction_error_attribution"
    assert summary.prediction_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.material_prediction_error_count == d("2.000000")
    assert summary.evidence_gap_count == d("1.000000")
    assert summary.stale_memory_count == d("1.000000")
    assert summary.source_conflict_handling_count == d("1.000000")
    assert summary.cost_assumption_count == d("2.000000")
    assert summary.resolution_ambiguity_count == d("1.000000")
    assert summary.review_latency_count == d("2.000000")
    assert summary.average_prediction_error == d("0.296667")
    assert summary.max_prediction_error == d("0.700000")
    assert len(summary.derived_validation_digest) == 64
    assert all(ch in "0123456789abcdef" for ch in summary.derived_validation_digest)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.attribution_status, row.review_key) for row in summary.rows) == (
        ("block", "domain.energy.block"),
        ("watch", "domain.energy.watch"),
        ("pass", "domain.energy.pass"),
    )

    blocked = summary.rows[0]
    assert blocked.prediction_error == d("0.700000")
    assert blocked.prediction_age_seconds == d("252000.000000")
    assert blocked.review_latency_seconds == d("14400.000000")
    assert blocked.redacted_attribution_reference.startswith("sha256:")
    assert blocked.reason_codes == (
        "domain_prediction_error_attribution_material_prediction_error",
        "domain_prediction_error_attribution_stale_memory",
        "domain_prediction_error_attribution_cost_assumption",
        "domain_prediction_error_attribution_resolution_ambiguity",
        "domain_prediction_error_attribution_review_latency",
    )

    watched = summary.rows[1]
    assert watched.prediction_error == d("0.150000")
    assert watched.redacted_attribution_reference == "public-attribution-notice"
    assert watched.reason_codes == (
        "domain_prediction_error_attribution_material_prediction_error",
        "domain_prediction_error_attribution_evidence_gap",
        "domain_prediction_error_attribution_source_conflict_handling",
        "domain_prediction_error_attribution_cost_assumption",
        "domain_prediction_error_attribution_review_latency",
    )

    passed = summary.rows[2]
    assert passed.prediction_error == d("0.040000")
    assert passed.reason_codes == ("domain_prediction_error_attribution_pass",)

    public = json.dumps(
        research_team_domain_prediction_error_attribution_report_payload(summary),
        sort_keys=True,
    ).lower()
    for value in (
        "private.example",
        "https://",
        "token",
        "hidden",
    ):
        assert value not in public


def test_only_explicit_public_references_are_exposed() -> None:
    internal_reference = "internal-public-attribution-memo-account-42"
    summary = report(
        (
            input_row(
                attribution_reference=internal_reference,
            ),
        ),
    )

    assert summary.rows[0].redacted_attribution_reference.startswith("sha256:")
    assert internal_reference not in json.dumps(summary.payload, sort_keys=True)


def test_empty_report_is_blocked_report_only_and_decimal_zeroed() -> None:
    summary = report(())

    assert summary.attribution_status == "block"
    assert summary.next_step == "block_report_only_domain_prediction_error_attribution"
    assert summary.prediction_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_prediction_error == ZERO
    assert summary.max_prediction_error == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchTeamDomainPredictionErrorAttributionReasonCodeCount(
            reason_code="domain_prediction_error_attribution_no_inputs",
            count=d("1.000000"),
            prediction_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("domain_prediction_error_attribution_no_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_is_deterministic_decimal_string_only_and_digest_validated() -> None:
    first = report((input_row(),))
    second = report((input_row(),))
    payload = research_team_domain_prediction_error_attribution_report_payload(first)
    repeat_payload = research_team_domain_prediction_error_attribution_report_payload(
        second,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["prediction_count"] == "1.000000"
    assert payload["average_prediction_error"] == "0.040000"
    assert payload["rows"][0]["predicted_probability"] == "0.520000"
    assert payload["rows"][0]["prediction_error"] == "0.040000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert not any(type(value) in (float, int) for value in walk_values(payload))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["prediction_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_domain_prediction_error_attribution_report_payload(tampered)


def test_public_payload_rejects_raw_identifiers_text_urls_and_live_surfaces() -> None:
    payload = research_team_domain_prediction_error_attribution_report_payload(
        report((input_row(),)),
    )
    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate",
        "market_id",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "https://",
        "private.example",
    ):
        assert forbidden not in rendered

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "dsn",
        "table_name",
        "wallet_address",
        "order_ref",
        "trade_ref",
        "live_surface",
    ):
        unsafe = dict(payload)
        unsafe[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_team_domain_prediction_error_attribution_report_payload(unsafe)


def test_public_payload_enforces_exact_schema_canonical_values_and_nested_flags() -> None:
    payload = research_team_domain_prediction_error_attribution_report_payload(
        report((input_row(),)),
    )

    extra_field = dict(payload)
    extra_field["safe_note"] = "redacted"
    resign_payload(extra_field)
    with pytest.raises(ValueError, match="exact schema"):
        research_team_domain_prediction_error_attribution_report_payload(extra_field)

    missing_field = dict(payload)
    missing_field.pop("next_step")
    resign_payload(missing_field)
    with pytest.raises(ValueError, match="exact schema"):
        research_team_domain_prediction_error_attribution_report_payload(missing_field)

    noncanonical_count = json.loads(json.dumps(payload))
    noncanonical_count["prediction_count"] = "1"
    resign_payload(noncanonical_count)
    with pytest.raises(ValueError, match="prediction_count"):
        research_team_domain_prediction_error_attribution_report_payload(
            noncanonical_count,
        )

    downgraded_row = json.loads(json.dumps(payload))
    downgraded_row["rows"][0]["report_only"] = False
    resign_payload(downgraded_row)
    with pytest.raises(ValueError, match="report_only"):
        research_team_domain_prediction_error_attribution_report_payload(
            downgraded_row,
        )

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["safe_note"] = "redacted"
    resign_payload(extra_row_field)
    with pytest.raises(ValueError, match="exact schema"):
        research_team_domain_prediction_error_attribution_report_payload(
            extra_row_field,
        )

    downgraded_reason_count = json.loads(json.dumps(payload))
    downgraded_reason_count["reason_code_counts"][0]["readonly"] = False
    resign_payload(downgraded_reason_count)
    with pytest.raises(ValueError, match="readonly"):
        research_team_domain_prediction_error_attribution_report_payload(
            downgraded_reason_count,
        )


def test_public_payload_rejects_resigned_semantic_drift() -> None:
    payload = research_team_domain_prediction_error_attribution_report_payload(
        report((input_row(),)),
    )

    forged_count = json.loads(json.dumps(payload))
    forged_count["prediction_count"] = "2.000000"
    resign_payload(forged_count)
    with pytest.raises(ValueError, match="prediction_count"):
        research_team_domain_prediction_error_attribution_report_payload(forged_count)

    forged_row_error = json.loads(json.dumps(payload))
    forged_row_error["rows"][0]["prediction_error"] = "0.500000"
    resign_payload(forged_row_error)
    with pytest.raises(ValueError, match="prediction_error"):
        research_team_domain_prediction_error_attribution_report_payload(
            forged_row_error,
        )

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "2.000000"
    resign_payload(forged_reason_count)
    with pytest.raises(ValueError, match="reason_code_counts"):
        research_team_domain_prediction_error_attribution_report_payload(
            forged_reason_count,
        )

    forged_generated_at = json.loads(json.dumps(payload))
    forged_generated_at["generated_at"] = "2026-07-01T18:00:00+00:00"
    resign_payload(forged_generated_at)
    with pytest.raises(ValueError, match="generated_at"):
        research_team_domain_prediction_error_attribution_report_payload(
            forged_generated_at,
        )


def test_validation_enforces_frozen_exact_decimal_and_hard_flags() -> None:
    assert is_dataclass(ResearchTeamDomainPredictionErrorAttributionConfig)
    assert is_dataclass(ResearchTeamDomainPredictionErrorAttributionInputRow)
    assert is_dataclass(ResearchTeamDomainPredictionErrorAttributionRow)
    assert is_dataclass(ResearchTeamDomainPredictionErrorAttributionReasonCodeCount)
    assert is_dataclass(ResearchTeamDomainPredictionErrorAttributionReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.predicted_probability = d("0.400000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].prediction_error = d("0.400000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("domain-attribution-v0"))
    with pytest.raises(ValueError, match="material_error_watch_threshold"):
        config(material_error_watch_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="material_error_block_threshold"):
        config(
            material_error_watch_threshold=d("0.800000"),
            material_error_block_threshold=d("0.700000"),
        )
    with pytest.raises(ValueError, match="component_watch_threshold"):
        config(component_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="component_block_threshold"):
        config(
            component_watch_threshold=d("0.700000"),
            component_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="review_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="domain_team"):
        input_row(domain_team="")
    with pytest.raises(ValueError, match="prediction_family"):
        input_row(prediction_family="policy_live_surface")
    with pytest.raises(ValueError, match="prediction_made_at"):
        input_row(prediction_made_at=datetime(2026, 7, 5, 12, 0))
    with pytest.raises(ValueError, match="resolved_at"):
        input_row(resolved_at=_DateTimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="review_completed_at"):
        input_row(review_completed_at=GENERATED_AT - timedelta(days=4))
    with pytest.raises(ValueError, match="predicted_probability"):
        input_row(predicted_probability=0.520000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolved_probability"):
        input_row(resolved_probability=d("1.000001"))
    with pytest.raises(ValueError, match="evidence_gap_score"):
        input_row(evidence_gap_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="stale_memory_score"):
        input_row(stale_memory_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="source_conflict_handling_score"):
        input_row(source_conflict_handling_score=d("-0.000001"))
    with pytest.raises(ValueError, match="cost_assumption_score"):
        input_row(cost_assumption_score=d("1.000001"))
    with pytest.raises(ValueError, match="resolution_ambiguity_score"):
        input_row(resolution_ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="review_latency_score"):
        input_row(review_latency_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_team_domain_prediction_error_attribution_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_domain_prediction_error_attribution_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))  # type: ignore[arg-type]


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    passed = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=(
                "domain_prediction_error_attribution_pass",
                "domain_prediction_error_attribution_evidence_gap",
            ),
        )
    with pytest.raises(ValueError, match="attribution_status"):
        replace(passed, attribution_status="block")
    with pytest.raises(ValueError, match="prediction_error"):
        replace(passed, prediction_error=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_attribution_reference"):
        replace(passed, redacted_attribution_reference="https://host/token")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report((input_row(),)), pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("domain.energy.z", prediction_family="zeta_rules"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_all_public_numeric_fields_are_exact_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    for value in (
        source_row.predicted_probability,
        source_row.evidence_gap_score,
        summary.prediction_count,
        summary.average_prediction_error,
        summary.rows[0].prediction_error,
        summary.reason_code_counts[0].prediction_ratio,
    ):
        assert type(value) is Decimal
