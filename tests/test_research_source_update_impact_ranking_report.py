from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Context, Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_update_impact_ranking_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_update_impact_ranking_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
REPORT_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "max_update_age_seconds",
    "component_watch_threshold",
    "component_block_threshold",
    "impact_watch_threshold",
    "impact_block_threshold",
    "freshness_weight",
    "authority_weight",
    "independence_weight",
    "contradiction_weight",
    "domain_relevance_weight",
    "resolution_rule_connection_weight",
    "generated_at",
    "status",
    "update_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_probability_review_impact_score",
    "max_probability_review_impact_score",
    "max_contradiction_severity",
    "average_freshness_score",
    "average_authority_score",
    "average_independence_score",
    "average_domain_relevance_score",
    "average_resolution_rule_connection_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "priority_rank",
    "update_label",
    "source_family_label",
    "domain_bucket",
    "observed_at",
    "update_age_seconds",
    "freshness_score",
    "authority_score",
    "independent_source_count",
    "expected_independent_source_count",
    "independence_score",
    "contradiction_severity",
    "domain_relevance_score",
    "resolution_rule_connection_score",
    "probability_review_impact_score",
    "impact_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(
    label: str,
    payload: dict[str, Any],
    field_names: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {field_name: payload[field_name] for field_name in field_names},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def resign_row(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_digest(
        "research_source_update_impact_ranking_report_row",
        payload,
        tuple(field_name for field_name in ROW_FIELDS_WITHOUT_DIGEST if field_name in payload),
    )


def resign_report(payload: dict[str, Any]) -> dict[str, Any]:
    for row_payload in payload["rows"]:
        resign_row(row_payload)
    payload["derived_validation_digest"] = canonical_digest(
        "research_source_update_impact_ranking_report",
        payload,
        tuple(
            field_name
            for field_name in REPORT_FIELDS_WITHOUT_DIGEST
            if field_name in payload
        ),
    )
    return payload


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "research-source-update-impact-ranking-report-test-v0",
        "max_update_age_seconds": d("7200.000000"),
        "component_watch_threshold": d("0.500000"),
        "component_block_threshold": d("0.800000"),
        "impact_watch_threshold": d("0.350000"),
        "impact_block_threshold": d("0.700000"),
        "freshness_weight": d("0.150000"),
        "authority_weight": d("0.200000"),
        "independence_weight": d("0.150000"),
        "contradiction_weight": d("0.200000"),
        "domain_relevance_weight": d("0.150000"),
        "resolution_rule_connection_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceUpdateImpactRankingConfig(**values)


def observation(
    update_label: str,
    *,
    source_family_label: str = "official_reporting",
    domain_bucket: str = "macro_policy",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    authority_score: Decimal = d("0.600000"),
    independent_source_count: Decimal = d("1.000000"),
    expected_independent_source_count: Decimal = d("2.000000"),
    contradiction_severity: Decimal = d("0.400000"),
    domain_relevance_score: Decimal = d("0.500000"),
    resolution_rule_connection_score: Decimal = d("0.600000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceUpdateImpactObservation(
        update_label=update_label,
        source_family_label=source_family_label,
        domain_bucket=domain_bucket,
        observed_at=observed_at,
        authority_score=authority_score,
        independent_source_count=independent_source_count,
        expected_independent_source_count=expected_independent_source_count,
        contradiction_severity=contradiction_severity,
        domain_relevance_score=domain_relevance_score,
        resolution_rule_connection_score=resolution_rule_connection_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def sample_observations() -> tuple[Any, ...]:
    return (
        observation(
            "update-watch",
            source_family_label="specialist_notes",
            domain_bucket="sports_roster",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            authority_score=d("0.600000"),
            independent_source_count=d("1.000000"),
            expected_independent_source_count=d("2.000000"),
            contradiction_severity=d("0.500000"),
            domain_relevance_score=d("0.500000"),
            resolution_rule_connection_score=d("0.600000"),
        ),
        observation(
            "update-pass",
            source_family_label="social_summary",
            domain_bucket="general_context",
            observed_at=GENERATED_AT - timedelta(minutes=90),
            authority_score=d("0.200000"),
            independent_source_count=d("0.000000"),
            expected_independent_source_count=d("2.000000"),
            contradiction_severity=d("0.050000"),
            domain_relevance_score=d("0.200000"),
            resolution_rule_connection_score=d("0.100000"),
        ),
        observation(
            "update-block",
            source_family_label="official_reporting",
            domain_bucket="macro_policy",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            authority_score=d("0.950000"),
            independent_source_count=d("3.000000"),
            expected_independent_source_count=d("3.000000"),
            contradiction_severity=d("0.800000"),
            domain_relevance_score=d("0.900000"),
            resolution_rule_connection_score=d("0.950000"),
        ),
    )


def report(
    observations: tuple[Any, ...] | None = None,
    *,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_source_update_impact_ranking_report(
        sample_observations() if observations is None else observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_number_or_datetime_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_number_or_datetime_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_number_or_datetime_payload_values(item)
        return
    assert type(value) not in (Decimal, float, int, datetime)


def assert_no_raw_identifier_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "condition_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "market_id",
        "question",
        "source_text",
        "wallet",
        "order",
        "trade",
        "token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_raw_identifier_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_raw_identifier_surface(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_ranks_updates_by_probability_review_impact_components() -> None:
    built = report()

    assert is_dataclass(built)
    assert built.status == "block"
    assert built.update_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_probability_review_impact_score == d("0.542083")
    assert built.max_probability_review_impact_score == d("0.921250")
    assert built.max_contradiction_severity == d("0.800000")
    assert built.average_freshness_score == d("0.652778")
    assert built.average_authority_score == d("0.583333")
    assert built.average_independence_score == d("0.500000")
    assert built.average_domain_relevance_score == d("0.533333")
    assert built.average_resolution_rule_connection_score == d("0.550000")
    assert built.reason_codes == (
        "freshness_watch",
        "freshness_block",
        "authority_watch",
        "authority_block",
        "independence_watch",
        "independence_block",
        "contradiction_watch",
        "contradiction_block",
        "domain_relevance_watch",
        "domain_relevance_block",
        "resolution_rule_connection_watch",
        "resolution_rule_connection_block",
        "probability_review_impact_watch",
        "probability_review_impact_block",
        "source_update_impact_ranking_pass",
    )

    assert tuple(row.update_label for row in built.rows) == (
        "update-block",
        "update-watch",
        "update-pass",
    )
    assert tuple(row.priority_rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.impact_status for row in built.rows) == ("block", "watch", "pass")

    blocked, watched, passed = built.rows
    assert blocked.update_age_seconds == d("300.000000")
    assert blocked.freshness_score == d("0.958333")
    assert blocked.independence_score == d("1.000000")
    assert blocked.probability_review_impact_score == d("0.921250")
    assert blocked.reason_codes == (
        "freshness_block",
        "authority_block",
        "independence_block",
        "contradiction_block",
        "domain_relevance_block",
        "resolution_rule_connection_block",
        "probability_review_impact_block",
    )
    assert watched.freshness_score == d("0.750000")
    assert watched.independence_score == d("0.500000")
    assert watched.probability_review_impact_score == d("0.572500")
    assert watched.reason_codes == (
        "freshness_watch",
        "authority_watch",
        "independence_watch",
        "contradiction_watch",
        "domain_relevance_watch",
        "resolution_rule_connection_watch",
        "probability_review_impact_watch",
    )
    assert passed.probability_review_impact_score == d("0.132500")
    assert passed.reason_codes == ("source_update_impact_ranking_pass",)


def test_payload_is_deterministic_public_safe_json_ready_and_digest_validated() -> None:
    module = api()
    first = report()
    second = report(tuple(reversed(sample_observations())))

    payload = module.research_source_update_impact_ranking_report_payload(first)
    reversed_payload = module.research_source_update_impact_ranking_report_payload(second)

    assert payload == reversed_payload
    assert json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["config_version"] == "research-source-update-impact-ranking-report-test-v0"
    assert payload["status"] == "block"
    assert payload["max_update_age_seconds"] == "7200.000000"
    assert payload["impact_block_threshold"] == "0.700000"
    assert payload["contradiction_weight"] == "0.200000"
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["probability_review_impact_score"] == "0.921250"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_source_update_impact_ranking_report_digest(first) == (
        first.derived_validation_digest
    )
    assert module.validate_research_source_update_impact_ranking_public_payload(payload)
    assert_no_number_or_datetime_payload_values(payload)
    assert_no_raw_identifier_surface(payload)
    assert module.research_source_update_impact_ranking_report_payload(payload) == payload
    assert set(payload) == {
        *REPORT_FIELDS_WITHOUT_DIGEST,
        "derived_validation_digest",
    }
    assert set(payload["rows"][0]) == {
        *ROW_FIELDS_WITHOUT_DIGEST,
        "derived_validation_digest",
    }
    assert payload["rows"][0]["derived_validation_digest"] == canonical_digest(
        "research_source_update_impact_ranking_report_row",
        payload["rows"][0],
        ROW_FIELDS_WITHOUT_DIGEST,
    )
    assert payload["derived_validation_digest"] == canonical_digest(
        "research_source_update_impact_ranking_report",
        payload,
        REPORT_FIELDS_WITHOUT_DIGEST,
    )

    tampered = dict(payload)
    tampered["average_probability_review_impact_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_update_impact_ranking_report_payload(tampered)
    assert not module.validate_research_source_update_impact_ranking_public_payload(tampered)

    unsafe = dict(payload)
    unsafe["wallet_surface"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_update_impact_ranking_report_payload(unsafe)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    built = report()

    public_classes = (
        module.ResearchSourceUpdateImpactRankingConfig,
        module.ResearchSourceUpdateImpactObservation,
        module.ResearchSourceUpdateImpactRankingRow,
        module.ResearchSourceUpdateImpactRankingReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True
        with pytest.raises(TypeError):
            type(f"Bad{public_class.__name__}", (public_class,), {})

    for instance in (cfg(), sample_observations()[0], built, *built.rows):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        built.rows[0].impact_status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceUpdateImpactRankingReport):
            pass

    with pytest.raises(ValueError, match="authority_score must be exactly Decimal"):
        observation("update-float", authority_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_count must be exactly Decimal"):
        observation(
            "update-decimal-subclass",
            independent_source_count=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="whole"):
        observation("update-fractional", independent_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="expected_independent_source_count"):
        observation(
            "update-overcount",
            independent_source_count=d("3.000000"),
            expected_independent_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_observations()[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation("update-naive", observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            "update-offset",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report((observation("update-future", observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="unsafe"):
        observation("https://example.invalid/raw-market")


def test_public_dataclasses_are_frozen_slotted_final_and_exact() -> None:
    module = api()
    instances = (
        cfg(),
        sample_observations()[0],
        report(),
        report().rows[0],
    )
    public_classes = tuple(type(instance) for instance in instances)

    for public_class, instance in zip(public_classes, instances):
        assert getattr(public_class, "__final__", False) is True
        assert public_class.__dataclass_params__.frozen is True
        assert tuple(public_class.__slots__) == tuple(
            field.name for field in fields(instance)
        )
        assert not hasattr(instance, "__dict__")
        assert type(instance) is public_class

    assert public_classes == (
        module.ResearchSourceUpdateImpactRankingConfig,
        module.ResearchSourceUpdateImpactObservation,
        module.ResearchSourceUpdateImpactRankingReport,
        module.ResearchSourceUpdateImpactRankingRow,
    )


def test_public_export_revalidates_resigned_direct_instance_tampering() -> None:
    module = api()
    built = report()
    original_payload = json.loads(
        json.dumps(module.research_source_update_impact_ranking_report_payload(built)),
    )

    object.__setattr__(built.rows[0], "authority_score", d("0.000000"))
    tampered_payload = json.loads(json.dumps(original_payload))
    tampered_payload["rows"][0]["authority_score"] = "0.000000"
    resign_report(tampered_payload)
    object.__setattr__(
        built.rows[0],
        "derived_validation_digest",
        tampered_payload["rows"][0]["derived_validation_digest"],
    )
    object.__setattr__(built, "derived_validation_digest", tampered_payload["derived_validation_digest"])

    with pytest.raises(ValueError, match="probability_review_impact_score.*components"):
        module.research_source_update_impact_ranking_report_payload(built)


def test_public_export_revalidates_direct_report_field_types() -> None:
    module = api()
    built = report()
    object.__setattr__(built, "generated_at", datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="generated_at.*timezone"):
        module.research_source_update_impact_ranking_report_payload(built)


def test_build_revalidates_tampered_config_and_observation_instances() -> None:
    module = api()
    tampered_config = cfg()
    object.__setattr__(tampered_config, "max_update_age_seconds", 7200.0)
    with pytest.raises(ValueError, match="max_update_age_seconds.*Decimal"):
        module.build_research_source_update_impact_ranking_report(
            sample_observations(),
            generated_at=GENERATED_AT,
            config=tampered_config,
        )

    tampered_observation = observation("tampered-input")
    object.__setattr__(
        tampered_observation,
        "observed_at",
        datetime(2026, 7, 8, 11, 30),
    )
    with pytest.raises(ValueError, match="observed_at.*timezone"):
        module.build_research_source_update_impact_ranking_report(
            (tampered_observation,),
            generated_at=GENERATED_AT,
            config=cfg(),
        )


def test_decimal_context_raw_bounds_signed_zero_and_non_finite_are_hardened() -> None:
    module = api()
    baseline = module.research_source_update_impact_ranking_report_payload(report())

    hostile_context = Context(prec=6, rounding=ROUND_DOWN)
    hostile_context.traps[InvalidOperation] = True
    with localcontext(hostile_context):
        rebuilt = module.research_source_update_impact_ranking_report_payload(report())
    assert rebuilt == baseline

    with pytest.raises(ValueError, match="authority_score must be between 0 and 1"):
        observation("negative-bound", authority_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="authority_score must be between 0 and 1"):
        observation("above-one-bound", authority_score=d("1.0000004"))
    with pytest.raises(ValueError, match="max_update_age_seconds must be positive"):
        cfg(max_update_age_seconds=d("-0.0000004"))
    with pytest.raises(ValueError, match="signed zero"):
        observation("signed-zero", authority_score=d("-0"))
    with pytest.raises(ValueError, match="finite"):
        observation("not-finite", authority_score=d("NaN"))
    with pytest.raises(ValueError, match="finite"):
        cfg(max_update_age_seconds=d("Infinity"))

    signed_zero_payload = json.loads(json.dumps(baseline))
    signed_zero_payload["rows"][0]["authority_score"] = "-0.000000"
    with pytest.raises(ValueError, match="signed zero|canonical Decimal"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(signed_zero_payload),
        )


@pytest.mark.parametrize(
    "source_family_label",
    (
        "private_discord_room",
        "secret_source_room",
        "internal_research_desk",
        "restricted_feed",
    ),
)
def test_private_source_family_is_redacted_before_public_ranking(
    source_family_label: str,
) -> None:
    built = report(
        (
            observation(
                "private-update",
                source_family_label=source_family_label,
            ),
        ),
    )

    assert built.rows[0].source_family_label == "private_source_redacted"
    payload_text = json.dumps(built.payload).lower()
    assert source_family_label.lower() not in payload_text


def test_custom_config_is_canonical_self_contained_and_revalidated() -> None:
    module = api()
    custom_config = cfg(
        max_update_age_seconds=d("3600.000000"),
        freshness_weight=d("0.100000"),
        authority_weight=d("0.250000"),
    )
    built = report(config=custom_config)
    payload = module.research_source_update_impact_ranking_report_payload(built)

    assert payload["max_update_age_seconds"] == "3600.000000"
    assert payload["freshness_weight"] == "0.100000"
    assert payload["authority_weight"] == "0.250000"
    assert module.validate_research_source_update_impact_ranking_public_payload(payload)

    tampered = json.loads(json.dumps(payload))
    tampered["freshness_weight"] = "0.150000"
    tampered["authority_weight"] = "0.200000"
    with pytest.raises(ValueError, match="probability_review_impact_score.*components"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(tampered),
        )


def test_stable_sorting_uses_complete_public_tie_break() -> None:
    module = api()
    observations = (
        observation("same-update", source_family_label="zeta_family"),
        observation("same-update", source_family_label="alpha_family"),
    )
    built = report(tuple(reversed(observations)))
    assert tuple(row.source_family_label for row in built.rows) == (
        "alpha_family",
        "zeta_family",
    )

    payload = json.loads(
        json.dumps(
            module.research_source_update_impact_ranking_report_payload(built),
        ),
    )
    payload["rows"].reverse()
    for rank, row_payload in enumerate(payload["rows"], start=1):
        row_payload["priority_rank"] = f"{rank}.000000"

    with pytest.raises(ValueError, match="sorted deterministically"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(payload),
        )


def test_resigned_payload_recomputes_all_row_and_report_invariants() -> None:
    module = api()
    original = module.research_source_update_impact_ranking_report_payload(report())

    def clone_payload() -> dict[str, Any]:
        return json.loads(json.dumps(original))

    extra_report_field = clone_payload()
    extra_report_field["extra_field"] = "ok"
    with pytest.raises(ValueError, match="unexpected report payload field"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(extra_report_field),
        )

    missing_report_field = clone_payload()
    missing_report_field.pop("status")
    with pytest.raises(ValueError, match="status is required"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(missing_report_field),
        )

    extra_row_field = clone_payload()
    extra_row_field["rows"][0]["extra_field"] = "ok"
    with pytest.raises(ValueError, match="unexpected row payload field"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(extra_row_field),
        )

    row_score = clone_payload()
    row_score["rows"][0]["probability_review_impact_score"] = "0.000000"
    with pytest.raises(ValueError, match="probability_review_impact_score.*components"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(row_score),
        )

    row_status = clone_payload()
    row_status["rows"][0]["impact_status"] = "pass"
    row_status["rows"][0]["reason_codes"] = [
        "source_update_impact_ranking_pass",
    ]
    with pytest.raises(ValueError, match="impact_status.*metrics"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(row_status),
        )

    row_reasons = clone_payload()
    row_reasons["rows"][0]["reason_codes"] = ["authority_watch"]
    with pytest.raises(ValueError, match="reason_codes.*metrics"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(row_reasons),
        )

    report_count = clone_payload()
    report_count["update_count"] = "99.000000"
    with pytest.raises(ValueError, match="update_count must match rows"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(report_count),
        )

    status_count = clone_payload()
    status_count["block_count"] = "99.000000"
    with pytest.raises(ValueError, match="block_count must match rows"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(status_count),
        )

    row_rank = clone_payload()
    row_rank["rows"][0]["priority_rank"] = "9.000000"
    with pytest.raises(ValueError, match="priority_rank values must match row order"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(row_rank),
        )

    report_status = clone_payload()
    report_status["status"] = "pass"
    with pytest.raises(ValueError, match="status must match rows"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(report_status),
        )

    report_reasons = clone_payload()
    report_reasons["reason_codes"] = ["source_update_impact_ranking_pass"]
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(report_reasons),
        )

    report_aggregate = clone_payload()
    report_aggregate["average_probability_review_impact_score"] = "0.000000"
    with pytest.raises(
        ValueError,
        match="average_probability_review_impact_score must match rows",
    ):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(report_aggregate),
        )

    max_aggregate = clone_payload()
    max_aggregate["max_probability_review_impact_score"] = "0.000000"
    with pytest.raises(
        ValueError,
        match="max_probability_review_impact_score must match rows",
    ):
        module.research_source_update_impact_ranking_report_payload(
            resign_report(max_aggregate),
        )


def test_empty_report_is_pass_and_public_exports_have_no_live_surfaces() -> None:
    module = api()
    empty = report(())

    assert module.IMPACT_STATUSES == ("pass", "watch", "block")
    assert empty.status == "pass"
    assert empty.update_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("source_update_impact_ranking_pass",)
    assert module.validate_research_source_update_impact_ranking_public_payload(empty.payload)

    unsafe_public_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "raw_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
    )
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in unsafe_public_terms)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "http",
        "requests",
        "httpx",
        "os",
        "pathlib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "scrapling",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    forbidden_name_calls = {"eval", "exec", "input", "open", "print"}
    forbidden_attribute_calls = {
        "authenticate",
        "buy",
        "commit",
        "connect",
        "execute",
        "place_order",
        "post",
        "request",
        "sell",
        "send",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_name_calls
        if isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attribute_calls

    public_names = set(dir(module))
    assert "client" not in public_names
    assert "wallet" not in public_names
    assert "order" not in public_names
    assert "trade" not in public_names
