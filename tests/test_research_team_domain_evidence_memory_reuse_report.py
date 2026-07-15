from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import (
    Context,
    Decimal,
    ROUND_DOWN,
    localcontext,
)
import hashlib
import inspect
import json
import socket
import urllib.request

import pytest

import polymarket_alpha_lab.research_team_domain_evidence_memory_reuse_report as api
from polymarket_alpha_lab.research_team_domain_evidence_memory_reuse_report import (
    ResearchTeamDomainEvidenceMemoryReuseConfig,
    ResearchTeamDomainEvidenceMemoryReuseObservation,
    ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount,
    ResearchTeamDomainEvidenceMemoryReuseReport,
    ResearchTeamDomainEvidenceMemoryReuseRow,
    build_research_team_domain_evidence_memory_reuse_report,
    research_team_domain_evidence_memory_reuse_report_payload,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class StringSubclass(str):
    pass


class DictSubclass(dict):
    pass


class ListSubclass(list):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object) -> ResearchTeamDomainEvidenceMemoryReuseObservation:
    values: dict[str, object] = {
        "team_key": "macro",
        "domain_key": "rates",
        "internal_reference": "candidate-123 market_slug https://example.invalid/path",
        "captured_at": NOW - timedelta(days=10),
        "reused_at": NOW - timedelta(hours=1),
        "source_observed_at": NOW - timedelta(hours=2),
        "relevant_precedent_score": d("0.900000"),
        "source_freshness_score": d("0.850000"),
        "calibration_value": d("0.800000"),
        "cross_domain_conflict_count": d("0.000000"),
        "conflict_handling_score": d("1.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchTeamDomainEvidenceMemoryReuseObservation(**values)


def report(
    observations: tuple[ResearchTeamDomainEvidenceMemoryReuseObservation, ...],
    *,
    config: ResearchTeamDomainEvidenceMemoryReuseConfig | None = None,
) -> ResearchTeamDomainEvidenceMemoryReuseReport:
    return build_research_team_domain_evidence_memory_reuse_report(
        observations,
        generated_at=NOW,
        config=config,
    )


def test_fresh_relevant_calibrated_memory_reuse_passes() -> None:
    built = report(
        (
            observation(internal_reference="ref-a"),
            observation(
                internal_reference="ref-b",
                relevant_precedent_score=d("0.800000"),
                source_freshness_score=d("0.750000"),
                calibration_value=d("0.700000"),
            ),
        ),
    )

    row = built.rows[0]
    assert built.report_status == "pass"
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert row.reuse_status == "pass"
    assert row.observation_count == d("2.000000")
    assert row.relevant_precedent_count == d("2.000000")
    assert row.relevant_precedent_coverage == d("1.000000")
    assert row.stale_memory_count == d("0.000000")
    assert row.stale_source_count == d("0.000000")
    assert row.average_source_freshness_score == d("0.800000")
    assert row.average_calibration_value == d("0.750000")
    assert row.productive_reuse_score == d("0.850000")
    assert row.reason_codes == ("productive_domain_evidence_memory_reuse_passed",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_stale_freshness_calibration_and_conflict_paths_are_reported() -> None:
    config = ResearchTeamDomainEvidenceMemoryReuseConfig(
        min_relevant_precedent_score=d("0.600000"),
        min_relevant_precedent_coverage=d("0.600000"),
        stale_memory_age_seconds=d("1209600.000000"),
        stale_source_age_seconds=d("86400.000000"),
        min_productive_reuse_score=d("0.650000"),
        min_calibration_value=d("0.550000"),
        min_conflict_handling_score=d("0.600000"),
    )

    built = report(
        (
            observation(
                team_key="macro",
                domain_key="rates",
                internal_reference="watch-a",
                captured_at=NOW - timedelta(days=30),
                source_observed_at=NOW - timedelta(days=3),
                relevant_precedent_score=d("0.700000"),
                source_freshness_score=d("0.400000"),
                calibration_value=d("0.500000"),
                cross_domain_conflict_count=d("1.000000"),
                conflict_handling_score=d("0.900000"),
            ),
            observation(
                team_key="sports",
                domain_key="tennis",
                internal_reference="block-a",
                relevant_precedent_score=d("0.300000"),
                source_freshness_score=d("0.700000"),
                calibration_value=d("0.600000"),
                cross_domain_conflict_count=d("1.000000"),
                conflict_handling_score=d("0.200000"),
            ),
        ),
        config=config,
    )

    watch_row, block_row = built.rows
    assert built.report_status == "block"
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")

    assert watch_row.reuse_status == "watch"
    assert watch_row.stale_memory_count == d("1.000000")
    assert watch_row.stale_source_count == d("1.000000")
    assert watch_row.stale_memory_penalty == d("0.250000")
    assert watch_row.average_calibration_value == d("0.500000")
    assert watch_row.cross_domain_conflict_count == d("1.000000")
    assert "stale_memory_penalty_applied" in watch_row.reason_codes
    assert "source_freshness_watch" in watch_row.reason_codes
    assert "calibration_value_watch" in watch_row.reason_codes
    assert "cross_domain_conflict_handled" in watch_row.reason_codes

    assert block_row.reuse_status == "block"
    assert block_row.relevant_precedent_coverage == d("0.000000")
    assert "insufficient_relevant_precedent_coverage" in block_row.reason_codes
    assert "cross_domain_conflict_unresolved" in block_row.reason_codes


def test_payload_is_deterministic_decimal_stringified_and_redacted() -> None:
    private_references = (
        (
            "candidate-999 market-alpha_slug question text "
            "https://example.invalid?token=secret"
        ),
        "dsn://warehouse/table-name wallet order trade live",
    )
    built = report(
        (
            observation(
                internal_reference=private_references[0],
            ),
            observation(
                internal_reference=private_references[1],
                source_freshness_score=d("0.750000"),
            ),
        ),
    )

    payload = research_team_domain_evidence_memory_reuse_report_payload(built)
    assert payload == built.payload
    json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["productive_reuse_score"] == "0.875000"
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["rows"][0]["memory_reference_digests"] == sorted(
        "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
        for value in private_references
    )

    serialized = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate-999",
        "market-alpha_slug",
        "question text",
        "https://example.invalid",
        "dsn://warehouse",
        "table-name",
        "token=secret",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in serialized
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(built)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_frozen_decimal_only_hard_flags_and_public_surface_guards() -> None:
    built = report((observation(),))

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_freshness_score"):
        observation(source_freshness_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cross_domain_conflict_count"):
        observation(cross_domain_conflict_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchTeamDomainEvidenceMemoryReuseConfig(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    for public_name in api.__all__:
        _assert_public_name(public_name)
    public_dataclasses = (
        ResearchTeamDomainEvidenceMemoryReuseConfig,
        ResearchTeamDomainEvidenceMemoryReuseObservation,
        type(built.rows[0]),
        type(built.reason_code_counts[0]),
        ResearchTeamDomainEvidenceMemoryReuseReport,
    )
    for cls in public_dataclasses:
        with pytest.raises(TypeError, match="subclass"):
            type(f"Invalid{cls.__name__}", (cls,), {})
        for field in fields(cls):
            _assert_public_name(field.name)
    with pytest.raises(ValueError, match="unsafe public"):
        observation(team_key="market-team")


@pytest.mark.parametrize(
    "unsafe_identifier",
    (
        "auth-team",
        "api_key-team",
        "credential-team",
        "password-team",
        "private-team",
        "secret-team",
    ),
)
def test_sensitive_identifiers_are_private_reference_only(
    unsafe_identifier: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        observation(team_key=unsafe_identifier)

    private = observation(internal_reference=unsafe_identifier)
    serialized = json.dumps(report((private,)).payload, sort_keys=True)
    assert unsafe_identifier not in serialized


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload.update(
            report_status="watch",
            next_review_step="review_domain_memory_reuse_inputs",
        ),
        lambda payload: payload.update(row_count="2.000000"),
        lambda payload: payload.update(average_productive_reuse_score="0.100000"),
        lambda payload: payload.update(
            reason_codes=["productive_reuse_score_watch"],
        ),
    ),
)
def test_rejects_forged_resigned_report_derivations(
    mutate: object,
) -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    mutate(payload)  # type: ignore[operator]
    _resign(payload)

    with pytest.raises(ValueError):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


@pytest.mark.parametrize(
    "mutate",
    (
        lambda row: row.update(productive_reuse_score="0.100000"),
        lambda row: row.update(
            reuse_status="watch",
            reason_codes=["stale_memory_penalty_applied"],
        ),
        lambda row: row.update(relevant_precedent_count="2.000000"),
    ),
)
def test_rejects_forged_resigned_row_derivations(
    mutate: object,
) -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    mutate(payload["rows"][0])  # type: ignore[index,operator]
    _resign(payload)

    with pytest.raises(ValueError):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


@pytest.mark.parametrize(
    ("location", "change"),
    (
        ("report", "extra"),
        ("report", "missing"),
        ("row", "extra"),
        ("row", "missing"),
        ("reason_count", "extra"),
        ("reason_count", "missing"),
    ),
)
def test_public_payload_requires_exact_nested_schemas(
    location: str,
    change: str,
) -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    target: dict[str, object]
    required_key: str
    if location == "report":
        target = payload
        required_key = "row_count"
    elif location == "row":
        target = payload["rows"][0]
        required_key = "observation_count"
    else:
        target = payload["reason_code_counts"][0]
        required_key = "count"

    if change == "extra":
        target["unexpected"] = "value"
    else:
        target.pop(required_key)
    _resign(payload)

    with pytest.raises(ValueError, match="exact schema"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


@pytest.mark.parametrize(
    "invalid_value",
    (
        1,
        1.0,
        "1",
        "1.0",
        "1.0000000",
        "-0.000000",
        "NaN",
        "Infinity",
    ),
)
def test_public_payload_requires_canonical_decimal_strings(
    invalid_value: object,
) -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    payload["row_count"] = invalid_value
    if type(invalid_value) is str:
        _resign(payload)

    with pytest.raises(ValueError, match="Decimal|decimal"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload.update(rows=tuple(payload["rows"])),
        lambda payload: payload.update(row_count=d("1.000000")),
        lambda payload: payload.update(generated_at=NOW),
        lambda payload: payload["rows"].__setitem__(
            0,
            DictSubclass(payload["rows"][0]),
        ),
        lambda payload: payload.update(
            reason_codes=ListSubclass(payload["reason_codes"]),
        ),
    ),
)
def test_public_payload_rejects_noncanonical_json_types_before_normalization(
    mutate: object,
) -> None:
    payload = copy.deepcopy(report((observation(),)).payload)
    mutate(payload)  # type: ignore[operator]
    _resign(payload)

    with pytest.raises(ValueError, match="exact JSON"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_public_payload_rejects_cyclic_json_containers() -> None:
    payload = copy.deepcopy(report((observation(),)).payload)
    cycle: list[object] = []
    cycle.append(cycle)
    payload["reason_codes"] = cycle

    with pytest.raises(ValueError, match="cyclic"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_public_payload_rejects_excessive_json_nesting() -> None:
    payload = copy.deepcopy(report((observation(),)).payload)
    nested: object = "unexpected"
    for _ in range(128):
        nested = [nested]
    payload["reason_codes"] = nested

    with pytest.raises(ValueError, match="nesting"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


@pytest.mark.parametrize(
    ("factory", "field_name"),
    (
        (
            lambda: ResearchTeamDomainEvidenceMemoryReuseConfig(
                stale_memory_penalty_per_item=d("-0.000000"),
            ),
            "stale_memory_penalty_per_item",
        ),
        (lambda: observation(relevant_precedent_score=d("-0")), "relevant_precedent_score"),
        (
            lambda: observation(cross_domain_conflict_count=d("-0.000000")),
            "cross_domain_conflict_count",
        ),
    ),
)
def test_signed_zero_is_canonicalized_before_derivation(
    factory: object,
    field_name: str,
) -> None:
    value = getattr(factory(), field_name)  # type: ignore[operator]

    assert value == d("0.000000")
    assert value.as_tuple().exponent == -6
    assert value.is_signed() is False


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("relevant_precedent_score", d("-0.0000001")),
        ("source_freshness_score", d("1.0000004")),
        ("cross_domain_conflict_count", d("1.0000001")),
    ),
)
def test_raw_decimal_bounds_are_checked_before_quantization(
    field_name: str,
    invalid_value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        observation(**{field_name: invalid_value})


def test_source_observed_at_must_not_be_after_reused_at() -> None:
    with pytest.raises(ValueError, match="source_observed_at.*reused_at"):
        observation(
            reused_at=NOW - timedelta(hours=2),
            source_observed_at=NOW - timedelta(hours=1),
        )


def test_utc_and_generated_at_boundaries_reject_future_data() -> None:
    offset = timezone(timedelta(hours=5, minutes=30))
    item = observation(
        captured_at=(NOW - timedelta(days=1)).astimezone(offset),
        reused_at=NOW.astimezone(offset),
        source_observed_at=(NOW - timedelta(hours=1)).astimezone(offset),
    )

    assert item.captured_at.tzinfo is UTC
    assert item.reused_at.tzinfo is UTC
    assert item.source_observed_at.tzinfo is UTC
    assert report((item,)).observation_count == d("1.000000")

    future = observation(
        captured_at=NOW + timedelta(microseconds=1),
        reused_at=NOW + timedelta(microseconds=1),
        source_observed_at=NOW + timedelta(microseconds=1),
    )
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report((future,))


def test_staleness_thresholds_are_strict_at_microsecond_precision() -> None:
    config = ResearchTeamDomainEvidenceMemoryReuseConfig(
        stale_memory_age_seconds=d("10.000000"),
        stale_source_age_seconds=d("10.000000"),
    )
    boundary = report(
        (
            observation(
                captured_at=NOW - timedelta(seconds=10),
                reused_at=NOW,
                source_observed_at=NOW - timedelta(seconds=10),
            ),
        ),
        config=config,
    ).rows[0]
    stale = report(
        (
            observation(
                captured_at=NOW - timedelta(seconds=10, microseconds=1),
                reused_at=NOW,
                source_observed_at=NOW - timedelta(seconds=10, microseconds=1),
            ),
        ),
        config=config,
    ).rows[0]

    assert boundary.stale_memory_count == d("0.000000")
    assert boundary.stale_source_count == d("0.000000")
    assert stale.stale_memory_count == d("1.000000")
    assert stale.stale_source_count == d("1.000000")


@pytest.mark.parametrize(
    "invalid_value",
    (
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_non_finite_decimals_are_rejected(invalid_value: Decimal) -> None:
    with pytest.raises(ValueError, match="finite"):
        observation(relevant_precedent_score=invalid_value)


def test_decimal_and_datetime_subclasses_are_rejected() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        observation(relevant_precedent_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="datetime"):
        observation(
            captured_at=DatetimeSubclass(2025, 12, 1, tzinfo=UTC),
        )


def test_string_and_public_container_subclasses_are_rejected() -> None:
    with pytest.raises(ValueError, match="team_key"):
        observation(team_key=StringSubclass("macro"))
    with pytest.raises(ValueError, match="internal_reference"):
        observation(internal_reference=StringSubclass("private-reference"))

    payload = report((observation(),)).payload
    with pytest.raises(ValueError, match="JSON object"):
        research_team_domain_evidence_memory_reuse_report_payload(
            DictSubclass(payload),
        )


def test_report_math_is_independent_of_global_decimal_context() -> None:
    observations = (
        observation(internal_reference="context-a"),
        observation(
            internal_reference="context-b",
            relevant_precedent_score=d("0.700000"),
            source_freshness_score=d("0.650000"),
            calibration_value=d("0.600000"),
            cross_domain_conflict_count=d("1.000000"),
            conflict_handling_score=d("0.700000"),
        ),
    )
    baseline = report(observations)

    hostile = Context(prec=2, rounding=ROUND_DOWN, Emin=-2, Emax=2)
    for signal in tuple(hostile.traps):
        hostile.traps[signal] = True
    with localcontext(hostile):
        rebuilt = report(observations)
        rebuilt_from_payload = research_team_domain_evidence_memory_reuse_report_payload(
            copy.deepcopy(baseline.payload),
        )

    assert rebuilt == baseline
    assert rebuilt.payload == baseline.payload
    assert rebuilt_from_payload == baseline.payload
    assert rebuilt.derived_validation_digest == baseline.derived_validation_digest


def test_observation_normalization_uses_a_complete_tie_break() -> None:
    earlier = observation(
        internal_reference="same-reference",
        captured_at=NOW - timedelta(days=20),
        reused_at=NOW - timedelta(hours=1),
        source_observed_at=NOW - timedelta(days=2),
        relevant_precedent_score=d("0.700000"),
        source_freshness_score=d("0.650000"),
        calibration_value=d("0.600000"),
        cross_domain_conflict_count=d("1.000000"),
        conflict_handling_score=d("0.700000"),
    )
    later = observation(
        internal_reference="same-reference",
        captured_at=NOW - timedelta(days=5),
        reused_at=NOW - timedelta(hours=1),
        source_observed_at=NOW - timedelta(hours=2),
        relevant_precedent_score=d("0.900000"),
        source_freshness_score=d("0.850000"),
        calibration_value=d("0.800000"),
        cross_domain_conflict_count=d("0.000000"),
        conflict_handling_score=d("1.000000"),
    )

    assert api._normalize_observations(
        (later, earlier),
        generated_at=NOW,
    ) == (earlier, later)
    assert report((later, earlier)).payload == report((earlier, later)).payload


def test_payload_snapshots_config_for_resigned_reason_validation() -> None:
    config = ResearchTeamDomainEvidenceMemoryReuseConfig(
        min_source_freshness_score=d("0.900000"),
    )
    built = report(
        (observation(source_freshness_score=d("0.850000")),),
        config=config,
    )
    payload = copy.deepcopy(built.payload)

    assert payload["min_source_freshness_score"] == "0.900000"
    assert payload["stale_memory_penalty_per_item"] == "0.250000"
    assert research_team_domain_evidence_memory_reuse_report_payload(payload) == payload

    payload["min_source_freshness_score"] = "0.800000"
    _resign(payload)
    with pytest.raises(ValueError, match="reason_codes|reuse_status"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_rejects_resigned_stale_penalty_and_score_forgery() -> None:
    built = report(
        (
            observation(
                captured_at=NOW - timedelta(days=40),
                internal_reference="stale-reference",
            ),
        ),
    )
    payload = copy.deepcopy(built.payload)
    row = payload["rows"][0]
    row["stale_memory_penalty"] = "0.000000"
    row["productive_reuse_score"] = "0.887500"
    row["reason_codes"] = ["stale_memory_penalty_applied"]
    payload["average_productive_reuse_score"] = "0.887500"
    payload["reason_codes"] = ["stale_memory_penalty_applied"]
    payload["reason_code_counts"] = [
        {
            "reason_code": "stale_memory_penalty_applied",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    _resign(payload)

    with pytest.raises(ValueError, match="stale_memory_penalty"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_rejects_resigned_freshness_and_calibration_reason_forgery() -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    row = payload["rows"][0]
    row["average_source_freshness_score"] = "0.500000"
    row["average_calibration_value"] = "0.500000"
    row["productive_reuse_score"] = "0.725000"
    payload["average_productive_reuse_score"] = "0.725000"
    _resign(payload)

    with pytest.raises(ValueError, match="reason_codes|reuse_status"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_rejects_resigned_no_conflict_average_forgery() -> None:
    payload = copy.deepcopy(report((observation(),)).payload)
    payload["rows"][0]["average_conflict_handling_score"] = "0.500000"
    _resign(payload)

    with pytest.raises(ValueError, match="average_conflict_handling_score"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_rejects_resigned_empty_memory_reference_digests() -> None:
    payload = copy.deepcopy(report((observation(),)).payload)
    payload["rows"][0]["memory_reference_digests"] = []
    _resign(payload)

    with pytest.raises(ValueError, match="memory_reference_digests"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


@pytest.mark.parametrize(
    ("relevant_score", "forged_average", "forged_productive_score"),
    (
        ("0.900000", "0.500000", "0.787500"),
        ("0.500000", "0.900000", "0.637500"),
    ),
)
def test_rejects_resigned_precedent_count_average_contradictions(
    relevant_score: str,
    forged_average: str,
    forged_productive_score: str,
) -> None:
    payload = copy.deepcopy(
        report(
            (
                observation(
                    relevant_precedent_score=d(relevant_score),
                ),
            ),
        ).payload,
    )
    payload["rows"][0]["average_relevant_precedent_score"] = forged_average
    payload["rows"][0]["productive_reuse_score"] = forged_productive_score
    payload["average_productive_reuse_score"] = forged_productive_score
    _resign(payload)

    with pytest.raises(ValueError, match="average_relevant_precedent_score"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_rejects_resigned_duplicate_team_domain_rows() -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    payload["rows"].append(copy.deepcopy(payload["rows"][0]))
    payload["observation_count"] = "2.000000"
    payload["row_count"] = "2.000000"
    payload["pass_count"] = "2.000000"
    payload["reason_code_counts"][0]["count"] = "2.000000"
    _resign(payload)

    with pytest.raises(ValueError, match="unique"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_all_public_dataclasses_are_frozen() -> None:
    built = report((observation(),))
    values = (
        ResearchTeamDomainEvidenceMemoryReuseConfig(),
        observation(),
        built.rows[0],
        built.reason_code_counts[0],
        built,
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]


def test_phase_one_report_build_and_payload_are_side_effect_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Phase 1 report code attempted an external side effect")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    built = report((observation(internal_reference="private-ref"),))
    payload = research_team_domain_evidence_memory_reuse_report_payload(built)
    _assert_phase_one_flags(payload)

    for public_name in api.__all__:
        lowered = public_name.lower()
        for forbidden_term in (
            "auth",
            "wallet",
            "order",
            "execution",
            "recommendation",
            "sizing",
            "network",
            "persistence",
            "database",
        ):
            assert forbidden_term not in lowered


def test_module_source_is_pure_report_only_code() -> None:
    tree = ast.parse(inspect.getsource(api))
    imported_roots: set[str] = set()
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("report module must not contain float literals")

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }


def test_payload_property_revalidates_frozen_report_integrity() -> None:
    built = report((observation(),))
    object.__setattr__(built, "row_count", d("2.000000"))

    with pytest.raises(ValueError, match="row_count"):
        _ = built.payload


@pytest.mark.parametrize(
    "tamper",
    (
        lambda built: object.__setattr__(built, "rows", list(built.rows)),
        lambda built: object.__setattr__(
            built.rows[0],
            "memory_reference_digests",
            list(built.rows[0].memory_reference_digests),
        ),
    ),
)
def test_payload_property_rejects_object_tampered_container_types(
    tamper: object,
) -> None:
    built = report((observation(),))
    tamper(built)  # type: ignore[operator]

    with pytest.raises(ValueError, match="constructor-normalized"):
        _ = built.payload


def test_build_revalidates_tampered_frozen_config_and_observation() -> None:
    config = ResearchTeamDomainEvidenceMemoryReuseConfig()
    object.__setattr__(config, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        report((observation(),), config=config)

    item = observation()
    object.__setattr__(item, "internal_reference", "")
    with pytest.raises(ValueError, match="internal_reference"):
        report((item,))


def test_report_constructor_revalidates_nested_rows_by_reconstruction() -> None:
    built = report((observation(),))
    tampered_row = built.rows[0]
    object.__setattr__(
        tampered_row,
        "memory_reference_digests",
        ("sha256:" + "g" * 64,),
    )

    values = {field.name: getattr(built, field.name) for field in fields(built)}
    values["rows"] = (tampered_row,)
    unsigned = dict(values)
    unsigned.pop("derived_validation_digest")
    values["derived_validation_digest"] = api._report_digest_from_values(unsigned)

    with pytest.raises(ValueError, match="memory_reference_digests"):
        ResearchTeamDomainEvidenceMemoryReuseReport(**values)


@pytest.mark.parametrize("location", ("report", "row", "reason_count"))
def test_public_payload_requires_canonical_field_order(location: str) -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)

    if location == "report":
        payload = dict(reversed(tuple(payload.items())))
    elif location == "row":
        payload["rows"][0] = dict(reversed(tuple(payload["rows"][0].items())))
    else:
        payload["reason_code_counts"][0] = dict(
            reversed(tuple(payload["reason_code_counts"][0].items())),
        )
    _resign(payload)

    with pytest.raises(ValueError, match="schema|order|canonical"):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_payload_uses_exact_canonical_schema_order_and_hash() -> None:
    built = report((observation(),))
    payload = built.payload

    assert tuple(payload) == tuple(field.name for field in fields(built))
    assert tuple(payload["rows"][0]) == tuple(field.name for field in fields(built.rows[0]))
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name for field in fields(built.reason_code_counts[0])
    )

    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert built.derived_validation_digest == hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()


def test_public_exports_and_dataclass_schemas_are_exact() -> None:
    assert api.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_REUSE_CONFIG_VERSION",
        "ResearchTeamDomainEvidenceMemoryReuseConfig",
        "ResearchTeamDomainEvidenceMemoryReuseObservation",
        "ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount",
        "ResearchTeamDomainEvidenceMemoryReuseReport",
        "ResearchTeamDomainEvidenceMemoryReuseRow",
        "build_research_team_domain_evidence_memory_reuse_report",
        "research_team_domain_evidence_memory_reuse_report_payload",
    )
    expected_fields = {
        ResearchTeamDomainEvidenceMemoryReuseConfig: (
            "config_version",
            "min_relevant_precedent_score",
            "min_relevant_precedent_coverage",
            "stale_memory_age_seconds",
            "stale_source_age_seconds",
            "stale_memory_penalty_per_item",
            "min_source_freshness_score",
            "min_calibration_value",
            "min_conflict_handling_score",
            "min_productive_reuse_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainEvidenceMemoryReuseObservation: (
            "team_key",
            "domain_key",
            "internal_reference",
            "captured_at",
            "reused_at",
            "source_observed_at",
            "relevant_precedent_score",
            "source_freshness_score",
            "calibration_value",
            "cross_domain_conflict_count",
            "conflict_handling_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainEvidenceMemoryReuseRow: (
            "team_key",
            "domain_key",
            "reuse_status",
            "observation_count",
            "relevant_precedent_count",
            "relevant_precedent_coverage",
            "stale_memory_count",
            "stale_source_count",
            "stale_memory_penalty",
            "average_relevant_precedent_score",
            "average_source_freshness_score",
            "average_calibration_value",
            "cross_domain_conflict_count",
            "average_conflict_handling_score",
            "productive_reuse_score",
            "memory_reference_digests",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainEvidenceMemoryReuseReasonCodeCount: (
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchTeamDomainEvidenceMemoryReuseReport: (
            "generated_at",
            "config_version",
            "min_relevant_precedent_score",
            "min_relevant_precedent_coverage",
            "stale_memory_age_seconds",
            "stale_source_age_seconds",
            "stale_memory_penalty_per_item",
            "min_source_freshness_score",
            "min_calibration_value",
            "min_conflict_handling_score",
            "min_productive_reuse_score",
            "report_status",
            "next_review_step",
            "observation_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "stale_source_count",
            "cross_domain_conflict_count",
            "average_productive_reuse_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    built = report((observation(),))

    for dataclass_type, schema in expected_fields.items():
        assert dataclass_type.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(dataclass_type)) == schema
    assert tuple(built.payload) == expected_fields[type(built)]
    assert tuple(built.payload["rows"][0]) == expected_fields[type(built.rows[0])]
    assert tuple(built.payload["reason_code_counts"][0]) == expected_fields[
        type(built.reason_code_counts[0])
    ]


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("observation_count", "2.000000"),
        ("pass_count", "2.000000"),
        ("watch_count", "1.000000"),
        ("block_count", "1.000000"),
        ("stale_memory_count", "1.000000"),
        ("stale_source_count", "1.000000"),
        ("cross_domain_conflict_count", "1.000000"),
    ),
)
def test_payload_rebuild_recomputes_all_report_aggregates(
    field_name: str,
    forged_value: str,
) -> None:
    built = report((observation(),))
    payload = copy.deepcopy(built.payload)
    payload[field_name] = forged_value
    _resign(payload)

    with pytest.raises(ValueError, match=field_name):
        research_team_domain_evidence_memory_reuse_report_payload(payload)


def test_observation_sort_key_is_a_complete_stable_tie_break() -> None:
    item = observation()

    assert len(api._observation_sort_key(item)) == len(
        fields(ResearchTeamDomainEvidenceMemoryReuseObservation),
    )


def _resign(payload: dict[str, object]) -> None:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = api._report_digest_from_values(unsigned)


def _assert_phase_one_flags(value: object) -> None:
    if isinstance(value, dict):
        flag_names = {"paper_only", "report_only", "readonly"}
        present_flags = flag_names.intersection(value)
        if present_flags:
            assert present_flags == flag_names
            assert all(value[field_name] is True for field_name in flag_names)
        for item in value.values():
            _assert_phase_one_flags(item)
    elif isinstance(value, list):
        for item in value:
            _assert_phase_one_flags(item)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            if field.name == "internal_reference":
                continue
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_public_name(value: str) -> None:
    lowered = value.lower()
    for forbidden in (
        "api_key",
        "auth",
        "candidate",
        "credential",
        "market",
        "password",
        "private",
        "secret",
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
    ):
        assert forbidden not in lowered
