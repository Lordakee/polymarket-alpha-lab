from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ALLOWED_STATUSES = {"pass", "watch", "block"}


class DerivedDecimal(Decimal):
    pass


class DerivedDatetime(datetime):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None

    def dst(self, value: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_claim_memory_decay_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "claim-memory-decay-scorecard-test",
        "half_life_seconds": d("2592000"),
        "review_gap_watch_seconds": d("604800"),
        "review_gap_block_seconds": d("1209600"),
        "min_confirmation_count": d("2"),
        "max_contradiction_count": d("1"),
        "min_pass_score": d("0.700000"),
        "min_watch_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainClaimMemoryDecayScorecardConfig(**values)


def claim(**overrides: object):
    module = api()
    values = {
        "domain_id": "macro_rates",
        "team_id": "rates_research_team",
        "claim_id": "private-alpha-claim-line",
        "memory_strength": d("0.950000"),
        "claim_age_seconds": d("86400"),
        "confirmation_count": d("3"),
        "contradiction_count": d("0"),
        "review_gap_seconds": d("7200"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainClaimMemoryDecayScorecardClaim(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_claim_memory_decay_scorecard_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_signed_decimal_zero(value: object) -> None:
    if type(value) is Decimal:
        assert not (value.is_zero() and value.is_signed())
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_no_signed_decimal_zero(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_no_signed_decimal_zero(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_signed_decimal_zero(item)


def assert_payload_omits_private_material(payload: dict[str, Any], private_value: str) -> None:
    encoded = json.dumps(payload, sort_keys=True)
    assert private_value not in encoded
    blocked_fragments = (
        "can" + "didate",
        "mar" + "ket",
        "sou" + "rce",
        "u" + "rl",
        "d" + "sn",
        "ta" + "ble",
        "to" + "ken",
    )
    lowered = encoded.lower()
    for fragment in blocked_fragments:
        assert fragment not in lowered


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    digest_values = dict(resigned)
    digest_values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    resigned["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return resigned


def test_decay_scorecard_sorts_and_summarizes_claim_rows() -> None:
    report = build_report(
        claim(claim_id="pass-private-claim"),
        claim(
            claim_id="watch-private-claim",
            memory_strength=d("0.650000"),
            claim_age_seconds=d("1296000"),
            confirmation_count=d("1"),
        ),
        claim(
            claim_id="block-private-claim",
            memory_strength=d("0.400000"),
            claim_age_seconds=d("3024000"),
            confirmation_count=d("0"),
            contradiction_count=d("2"),
            review_gap_seconds=d("1296000"),
        ),
    )

    assert report.report_status == "block"
    assert report.assessed_claim_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_claim_memory_decay_score == d("0.507407")
    assert report.lowest_claim_memory_decay_score == d("0.000000")
    assert tuple(row.row_status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.claim_memory_decay_score for row in report.rows) == (
        d("0.000000"),
        d("0.550000"),
        d("0.972222"),
    )
    assert report.reason_codes == (
        "claim_memory_decay_block_present",
        "claim_memory_decay_watch_present",
    )
    assert {report.report_status, *(row.row_status for row in report.rows)} <= ALLOWED_STATUSES


def test_public_payload_is_deterministic_and_validates_digest() -> None:
    module = api()
    first = build_report(
        claim(claim_id="beta-private-claim"),
        claim(claim_id="alpha-private-claim"),
    )
    second = build_report(
        claim(claim_id="alpha-private-claim"),
        claim(claim_id="beta-private-claim"),
    )

    first_payload = module.research_team_domain_claim_memory_decay_scorecard_payload(first)
    second_payload = module.research_team_domain_claim_memory_decay_scorecard_payload(second)

    assert first_payload == second_payload
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["assessed_claim_count"] == "2"
    assert first_payload["rows"][0]["claim_memory_decay_score"] == "0.972222"
    assert isinstance(first_payload["derived_validation_digest"], str)
    assert len(first_payload["derived_validation_digest"]) == 64
    assert_no_float_values(first_payload)

    assert module.research_team_domain_claim_memory_decay_scorecard_payload(
        first_payload,
    ) == first_payload

    tampered = dict(first_payload)
    tampered["average_claim_memory_decay_score"] = "0.000001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_claim = claim()
    sample_report = build_report(sample_claim)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_claim, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        claim(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(claim(readonly=False))


def test_all_module_dataclasses_are_non_subclassable_and_reject_derived_scalars() -> None:
    module = api()
    dataclass_types = tuple(
        value
        for value in vars(module).values()
        if isinstance(value, type) and is_dataclass(value)
    )

    assert dataclass_types
    for dataclass_type in dataclass_types:
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Unsafe{dataclass_type.__name__}", (dataclass_type,), {})

    with pytest.raises(ValueError, match="Decimal"):
        config(min_pass_score=DerivedDecimal("0.700000"))
    with pytest.raises(ValueError, match="Decimal"):
        claim(claim_age_seconds=DerivedDecimal("86400"))
    with pytest.raises(ValueError, match="datetime"):
        build_report(
            claim(),
            generated_at=DerivedDatetime(2026, 7, 9, 12, 0, tzinfo=UTC),
        )


def test_decimal_arithmetic_uses_a_fixed_context_and_emits_canonical_zero() -> None:
    def context_sensitive_report():
        return build_report(
            claim(
                claim_id="context-pass-private-claim",
                memory_strength=d("0.950000"),
                claim_age_seconds=d("86400"),
                confirmation_count=d("3"),
            ),
            claim(
                claim_id="context-watch-private-claim",
                memory_strength=d("0.650000"),
                claim_age_seconds=d("1296000"),
                confirmation_count=d("1"),
            ),
            claim(
                claim_id="context-block-private-claim",
                memory_strength=d("0.400000"),
                claim_age_seconds=d("3024000"),
                confirmation_count=d("0"),
                contradiction_count=d("2"),
                review_gap_seconds=d("1296000"),
            ),
        )

    expected = context_sensitive_report()
    with localcontext() as ambient:
        ambient.prec = 2
        ambient.rounding = ROUND_DOWN
        ambient.Emin = -2
        ambient.Emax = 2
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        actual = context_sensitive_report()

    assert actual == expected
    assert actual.payload == expected.payload
    assert_no_signed_decimal_zero(actual)


def test_utc_normalization_rejects_naive_and_none_offset_datetimes() -> None:
    shifted = GENERATED_AT.astimezone(timezone(-timedelta(hours=7)))
    shifted_report = build_report(claim(), generated_at=shifted)

    assert shifted_report.generated_at == GENERATED_AT
    assert shifted_report.generated_at.tzinfo is UTC
    with pytest.raises(ValueError, match="timezone-aware|UTC-aware"):
        build_report(claim(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware|UTC-aware"):
        build_report(
            claim(),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=NoneOffsetTimezone(),
            ),
        )


@pytest.mark.parametrize("field_name", ("claim_age_seconds", "review_gap_seconds"))
def test_negative_age_boundaries_reject_future_claim_data(field_name: str) -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        claim(**{field_name: d("-0.000001")})


def test_public_payload_omits_raw_claim_material() -> None:
    module = api()
    private_claim = "sensitive-private-claim-material"
    report = build_report(claim(claim_id=private_claim))
    payload = module.research_team_domain_claim_memory_decay_scorecard_payload(report)

    assert "claim_id" not in payload["rows"][0]
    assert payload["rows"][0]["claim_digest"] != private_claim
    assert len(payload["rows"][0]["claim_digest"]) == 64
    assert_payload_omits_private_material(payload, private_claim)


def test_public_payload_rejects_extra_raw_identifier_keys_even_with_matching_digest() -> None:
    module = api()
    payload = module.research_team_domain_claim_memory_decay_scorecard_payload(
        build_report(claim()),
    )
    tampered = dict(payload)
    tampered["claim_id"] = "raw-private-claim-id"
    digest_values = dict(tampered)
    digest_values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    tampered["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()

    with pytest.raises(ValueError, match="payload keys"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(tampered)


def test_validation_rejects_non_decimal_inputs_and_invalid_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        config(half_life_seconds=2592000)
    with pytest.raises(ValueError, match="Decimal"):
        claim(memory_strength=0.95)
    with pytest.raises(ValueError, match="threshold"):
        config(min_pass_score=d("0.400000"), min_watch_score=d("0.500000"))

    row_values = {field.name: getattr(build_report(claim()).rows[0], field.name) for field in fields(build_report(claim()).rows[0])}
    row_values["row_status"] = "blocked"
    with pytest.raises(ValueError, match="status"):
        module.ResearchTeamDomainClaimMemoryDecayScorecardRow(**row_values)


def test_public_payload_rejects_forged_resigned_derived_logic() -> None:
    module = api()
    payload = module.research_team_domain_claim_memory_decay_scorecard_payload(
        build_report(
            claim(claim_id="pass-private-claim"),
            claim(
                claim_id="block-private-claim",
                memory_strength=d("0.400000"),
                claim_age_seconds=d("3024000"),
                confirmation_count=d("0"),
                contradiction_count=d("2"),
                review_gap_seconds=d("1296000"),
            ),
        ),
    )

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["claim_memory_decay_score"] = "0.100000"
    forged_score["average_claim_memory_decay_score"] = "0.536111"
    forged_score["lowest_claim_memory_decay_score"] = "0.100000"
    with pytest.raises(ValueError, match="claim_memory_decay_score"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_score),
        )

    forged_row_reason = json.loads(json.dumps(payload))
    forged_row_reason["rows"][0]["reason_codes"] = ["claim_memory_current"]
    with pytest.raises(ValueError, match="reason_codes"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_row_reason),
        )

    forged_count = dict(payload)
    forged_count["assessed_claim_count"] = "3"
    with pytest.raises(ValueError, match="assessed_claim_count"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_count),
        )

    forged_report_status = dict(payload)
    forged_report_status["report_status"] = "pass"
    forged_report_status["reason_codes"] = ["claim_memory_decay_scorecard_ready"]
    with pytest.raises(ValueError, match="report_status|reason_codes"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_report_status),
        )

    forged_row_status = json.loads(json.dumps(payload))
    forged_row_status["rows"][1]["row_status"] = "watch"
    forged_row_status["rows"][1]["reason_codes"] = ["claim_memory_watch"]
    forged_row_status["pass_count"] = "0"
    forged_row_status["watch_count"] = "1"
    forged_row_status["reason_codes"] = [
        "claim_memory_decay_block_present",
        "claim_memory_decay_watch_present",
    ]
    with pytest.raises(ValueError, match="row_status"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_row_status),
        )

    forged_component = json.loads(json.dumps(payload))
    forged_component["rows"][1]["freshness_component"] = "0.500000"
    forged_component["rows"][1]["claim_memory_decay_score"] = "0.816667"
    forged_component["average_claim_memory_decay_score"] = "0.408334"
    with pytest.raises(ValueError, match="freshness_component"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_component),
        )

    contradiction_payload = module.research_team_domain_claim_memory_decay_scorecard_payload(
        build_report(claim(contradiction_count=d("2"))),
    )
    forged_excess = json.loads(json.dumps(contradiction_payload))
    forged_excess["rows"][0]["contradiction_excess_count"] = "0"
    forged_excess["rows"][0]["claim_memory_decay_score"] = "0.972222"
    forged_excess["rows"][0]["reason_codes"] = ["claim_memory_current"]
    forged_excess["contradiction_excess_count"] = "0"
    forged_excess["average_claim_memory_decay_score"] = "0.972222"
    forged_excess["lowest_claim_memory_decay_score"] = "0.972222"
    with pytest.raises(ValueError, match="contradiction_excess_count"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(forged_excess),
        )


def test_direct_dataclasses_reject_forged_derived_logic() -> None:
    module = api()
    report = build_report(claim())
    row = report.rows[0]

    with pytest.raises(ValueError, match="claim_memory_decay_score"):
        replace(row, claim_memory_decay_score=d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("claim_memory_watch",))
    with pytest.raises(ValueError, match="contradiction_excess_count"):
        replace(row, contradiction_excess_count=d("1"))
    with pytest.raises(ValueError, match="review_gap"):
        replace(row, review_gap_watch=False, review_gap_block=True)

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["report_status"] = "watch"
    values["reason_codes"] = ("claim_memory_decay_watch_present",)
    digest_values = dict(values)
    digest_values.pop("derived_validation_digest")
    values["derived_validation_digest"] = module._report_digest_from_values(
        digest_values,
    )
    with pytest.raises(ValueError, match="report_status|reason_codes"):
        module.ResearchTeamDomainClaimMemoryDecayScorecardReport(**values)

    forged_row = replace(
        row,
        row_status="watch",
        reason_codes=("claim_memory_watch",),
    )
    forged_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    forged_values["rows"] = (forged_row,)
    forged_values["pass_count"] = d("0")
    forged_values["watch_count"] = d("1")
    forged_values["report_status"] = "watch"
    forged_values["reason_codes"] = ("claim_memory_decay_watch_present",)
    forged_digest_values = dict(forged_values)
    forged_digest_values.pop("derived_validation_digest")
    forged_values["derived_validation_digest"] = module._report_digest_from_values(
        forged_digest_values,
    )
    with pytest.raises(ValueError, match="row_status"):
        module.ResearchTeamDomainClaimMemoryDecayScorecardReport(**forged_values)


def test_direct_payload_property_revalidates_digest_and_derived_fields() -> None:
    module = api()

    digest_tampered = build_report(claim())
    object.__setattr__(digest_tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _ = digest_tampered.payload

    count_tampered = build_report(claim())
    object.__setattr__(count_tampered, "assessed_claim_count", d("2"))
    object.__setattr__(
        count_tampered,
        "derived_validation_digest",
        module._report_digest_from_values(
            module._report_values_without_digest(count_tampered),
        ),
    )
    with pytest.raises(ValueError, match="assessed_claim_count"):
        _ = count_tampered.payload

    row_tampered = build_report(claim())
    object.__setattr__(row_tampered.rows[0], "freshness_component", d("0.500000"))
    object.__setattr__(
        row_tampered,
        "derived_validation_digest",
        module._report_digest_from_values(
            module._report_values_without_digest(row_tampered),
        ),
    )
    with pytest.raises(ValueError, match="freshness_component"):
        _ = row_tampered.payload

    signed_zero_tampered = build_report()
    object.__setattr__(
        signed_zero_tampered,
        "average_claim_memory_decay_score",
        d("-0.000000"),
    )
    object.__setattr__(
        signed_zero_tampered,
        "derived_validation_digest",
        module._report_digest_from_values(
            module._report_values_without_digest(signed_zero_tampered),
        ),
    )
    with pytest.raises(ValueError, match="signed zero"):
        _ = signed_zero_tampered.payload

    malformed_digest_tampered = build_report(claim())
    object.__setattr__(malformed_digest_tampered.rows[0], "claim_digest", "x")
    object.__setattr__(
        malformed_digest_tampered,
        "derived_validation_digest",
        module._report_digest_from_values(
            module._report_values_without_digest(malformed_digest_tampered),
        ),
    )
    with pytest.raises(ValueError, match="claim_digest"):
        _ = malformed_digest_tampered.payload


def test_direct_payload_property_rejects_noncanonical_utc_tampering() -> None:
    report = build_report(claim())
    shifted = GENERATED_AT.astimezone(timezone(timedelta(hours=9)))

    object.__setattr__(report, "generated_at", shifted)
    with pytest.raises(ValueError, match="generated_at.*canonical UTC"):
        _ = report.payload


def test_private_claim_material_is_hashed_while_public_identifiers_are_screened() -> None:
    module = api()
    private_claim = (
        "https://private.invalid/raw?" + "au" + "th=" + "to" + "ken-wallet-order"
    )
    payload = module.research_team_domain_claim_memory_decay_scorecard_payload(
        build_report(claim(claim_id=private_claim)),
    )

    assert_payload_omits_private_material(payload, private_claim)
    with pytest.raises(ValueError, match="unsafe public payload"):
        claim(domain_id="domain-" + "wall" + "et")
    with pytest.raises(ValueError, match="unsafe public payload"):
        claim(team_id="team-" + "net" + "work")
    with pytest.raises(ValueError, match="unsafe public payload"):
        config(config_version="config-" + "cre" + "dential")

    for unsafe_public_value in (
        "config-" + "api" + "_key",
        "config-" + "access" + "_key",
        "config-" + "pass" + "word",
        "config-" + "sec" + "ret",
        "config-" + "http" + "_endpoint",
        "config-" + "storage" + "_bucket",
        "config-" + "post" + "gres",
        "config-" + "sql" + "ite",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            config(config_version=unsafe_public_value)

    nested_raw_key = json.loads(json.dumps(payload))
    nested_raw_key["rows"][0]["claim_id"] = private_claim
    with pytest.raises(ValueError, match="payload row keys|unsafe public payload"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(nested_raw_key),
        )


@pytest.mark.parametrize(
    ("factory", "field_name", "value"),
    (
        (config, "min_watch_score", d("-0.0000004")),
        (config, "min_pass_score", d("1.0000004")),
        (claim, "memory_strength", d("-0.0000004")),
        (claim, "memory_strength", d("1.0000004")),
        (claim, "memory_strength", d("-0.000000")),
        (claim, "claim_age_seconds", d("-0")),
        (claim, "confirmation_count", d("-0")),
    ),
)
def test_decimal_validation_uses_raw_bounds_and_rejects_signed_zero(
    factory,
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match="between 0 and 1|signed zero|nonnegative"):
        factory(**{field_name: value})


def test_public_payload_requires_exact_json_scalar_and_container_types() -> None:
    module = api()
    payload = module.research_team_domain_claim_memory_decay_scorecard_payload(
        build_report(claim()),
    )

    decimal_count = dict(payload)
    decimal_count["assessed_claim_count"] = d("1")
    decimal_values = dict(decimal_count)
    decimal_values.pop("derived_validation_digest")
    decimal_count["derived_validation_digest"] = module._report_digest_from_values(
        decimal_values,
    )
    with pytest.raises(ValueError, match="assessed_claim_count|Decimal-derived"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            decimal_count,
        )

    noncanonical_count = dict(payload)
    noncanonical_count["assessed_claim_count"] = "1.0"
    with pytest.raises(ValueError, match="assessed_claim_count"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            resign_payload(noncanonical_count),
        )

    tuple_rows = dict(payload)
    tuple_rows["rows"] = tuple(payload["rows"])
    tuple_values = dict(tuple_rows)
    tuple_values.pop("derived_validation_digest")
    tuple_rows["derived_validation_digest"] = module._report_digest_from_values(
        tuple_values,
    )
    with pytest.raises(ValueError, match="rows"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(tuple_rows)

    datetime_value = dict(payload)
    datetime_value["generated_at"] = GENERATED_AT
    datetime_values = dict(datetime_value)
    datetime_values.pop("derived_validation_digest")
    datetime_value["derived_validation_digest"] = module._report_digest_from_values(
        datetime_values,
    )
    with pytest.raises(ValueError, match="generated_at"):
        module.research_team_domain_claim_memory_decay_scorecard_payload(
            datetime_value,
        )


def test_public_schemas_and_exports_are_exact() -> None:
    module = api()
    report = build_report(claim())
    payload = module.research_team_domain_claim_memory_decay_scorecard_payload(report)

    assert tuple(field.name for field in fields(module.ResearchTeamDomainClaimMemoryDecayScorecardConfig)) == (
        "config_version",
        "half_life_seconds",
        "review_gap_watch_seconds",
        "review_gap_block_seconds",
        "min_confirmation_count",
        "max_contradiction_count",
        "min_pass_score",
        "min_watch_score",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(module.ResearchTeamDomainClaimMemoryDecayScorecardClaim)) == (
        "domain_id",
        "team_id",
        "claim_id",
        "memory_strength",
        "claim_age_seconds",
        "confirmation_count",
        "contradiction_count",
        "review_gap_seconds",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(module.ResearchTeamDomainClaimMemoryDecayScorecardRow)) == (
        "domain_id",
        "team_id",
        "claim_digest",
        "memory_strength",
        "claim_age_seconds",
        "freshness_component",
        "confirmation_component",
        "confirmation_count",
        "contradiction_count",
        "contradiction_excess_count",
        "review_gap_seconds",
        "review_gap_watch",
        "review_gap_block",
        "claim_memory_decay_score",
        "row_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(module.ResearchTeamDomainClaimMemoryDecayScorecardReport)) == (
        "generated_at",
        "config_version",
        "half_life_seconds",
        "review_gap_watch_seconds",
        "review_gap_block_seconds",
        "min_confirmation_count",
        "max_contradiction_count",
        "min_pass_score",
        "min_watch_score",
        "report_status",
        "assessed_claim_count",
        "pass_count",
        "watch_count",
        "block_count",
        "review_gap_watch_count",
        "review_gap_block_count",
        "contradiction_excess_count",
        "average_claim_memory_decay_score",
        "lowest_claim_memory_decay_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert set(payload) == module.PUBLIC_PAYLOAD_KEYS == {
        "assessed_claim_count",
        "average_claim_memory_decay_score",
        "block_count",
        "config_version",
        "contradiction_excess_count",
        "derived_validation_digest",
        "generated_at",
        "half_life_seconds",
        "lowest_claim_memory_decay_score",
        "max_contradiction_count",
        "min_confirmation_count",
        "min_pass_score",
        "min_watch_score",
        "paper_only",
        "pass_count",
        "readonly",
        "reason_codes",
        "report_only",
        "report_status",
        "review_gap_block_count",
        "review_gap_block_seconds",
        "review_gap_watch_count",
        "review_gap_watch_seconds",
        "rows",
        "watch_count",
    }
    assert set(payload["rows"][0]) == module.PUBLIC_ROW_PAYLOAD_KEYS
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_CLAIM_MEMORY_DECAY_SCORECARD_CONFIG_VERSION",
        "CLAIM_MEMORY_DECAY_STATUSES",
        "ResearchTeamDomainClaimMemoryDecayScorecardClaim",
        "ResearchTeamDomainClaimMemoryDecayScorecardConfig",
        "ResearchTeamDomainClaimMemoryDecayScorecardReport",
        "ResearchTeamDomainClaimMemoryDecayScorecardRow",
        "build_research_team_domain_claim_memory_decay_scorecard_report",
        "research_team_domain_claim_memory_decay_scorecard_payload",
    )


def test_module_is_phase_one_pure_report_only_paper_only_readonly() -> None:
    module_path = Path(api().__file__)
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "builtins",
        "dbm",
        "requests.",
        "httpx",
        "io.",
        "os.",
        "pathlib",
        "pickle",
        "shelve",
        "shutil",
        "tempfile",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "open(",
        "getenv",
        "environ",
        "postgres",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
            imported_modules.add(node.module)
            if node.module.startswith("polymarket_alpha_lab"):
                assert node.module == "polymarket_alpha_lab.team_paper_guard"
                assert tuple(alias.name for alias in node.names) == (
                    "require_paper_only_flags",
                )
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "__import__",
                "call",
                "check_call",
                "check_output",
                "compile",
                "connect",
                "dump",
                "eval",
                "exec",
                "execute",
                "executemany",
                "load",
                "makedirs",
                "mkdir",
                "open",
                "popen",
                "read",
                "read_bytes",
                "read_text",
                "remove",
                "rename",
                "replace",
                "request",
                "rmdir",
                "run",
                "send",
                "spawnl",
                "spawnle",
                "spawnlp",
                "spawnlpe",
                "spawnv",
                "spawnve",
                "spawnvp",
                "spawnvpe",
                "system",
                "unlink",
                "urlopen",
                "write",
                "write_bytes",
                "write_text",
                "post",
                "put",
                "patch",
                "place_order",
                "submit_order",
                "cancel_order",
            }

    assert imported_roots == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "polymarket_alpha_lab",
        "typing",
    }
    assert imported_modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "polymarket_alpha_lab.team_paper_guard",
        "typing",
    }
