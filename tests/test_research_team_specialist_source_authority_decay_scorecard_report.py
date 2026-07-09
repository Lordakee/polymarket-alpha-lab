from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_team_specialist_source_authority_decay_scorecard_report as api
from polymarket_alpha_lab.research_team_specialist_source_authority_decay_scorecard_report import (
    ResearchTeamSpecialistSourceAuthorityDecayObservation,
    ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
    ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
    build_research_team_specialist_source_authority_decay_scorecard_report,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    team_key: str = "macro_team",
    specialist_key: str = "calendar_specialist",
    authority_family: str = "official_calendar",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=1800),
    authority_score: Decimal = d("0.950000"),
    source_decay_half_life_seconds: Decimal = d("7200.000000"),
    corroboration_score: Decimal = d("0.900000"),
    conflict_score: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistSourceAuthorityDecayObservation:
    return ResearchTeamSpecialistSourceAuthorityDecayObservation(
        team_key=team_key,
        specialist_key=specialist_key,
        authority_family=authority_family,
        observed_at=observed_at,
        authority_score=authority_score,
        source_decay_half_life_seconds=source_decay_half_life_seconds,
        corroboration_score=corroboration_score,
        conflict_score=conflict_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: ResearchTeamSpecialistSourceAuthorityDecayObservation,
    config: ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig | None = None,
) -> ResearchTeamSpecialistSourceAuthorityDecayScorecardReport:
    return build_research_team_specialist_source_authority_decay_scorecard_report(
        observations,
        generated_at=GENERATED_AT,
        config=config,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_scorecard_aggregates_pass_watch_and_block_rows() -> None:
    result = report(
        observation(
            team_key="macro_team",
            specialist_key="calendar_specialist",
            authority_family="official_calendar",
        ),
        observation(
            team_key="geo_team",
            specialist_key="regional_specialist",
            authority_family="regional_notice",
            observed_at=GENERATED_AT - timedelta(seconds=3600),
            authority_score=d("1.000000"),
            source_decay_half_life_seconds=d("7200.000000"),
            corroboration_score=d("0.800000"),
            conflict_score=d("0.250000"),
        ),
        observation(
            team_key="sports_team",
            specialist_key="injury_specialist",
            authority_family="league_report",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            authority_score=d("0.700000"),
            source_decay_half_life_seconds=d("10000.000000"),
            corroboration_score=d("0.400000"),
            conflict_score=d("0.600000"),
        ),
    )

    assert result.status == "block"
    assert result.row_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.team_count == d("3.000000")
    assert result.specialist_count == d("3.000000")
    assert result.authority_family_count == d("3.000000")
    assert result.average_specialist_authority_score == d("0.515417")
    assert result.lowest_decay_adjusted_authority_score == d("0.070000")
    assert result.highest_authority_decay_risk_score == d("0.825000")
    assert result.oldest_source_age_seconds == d("9000.000000")
    assert result.reason_codes == (
        "authority_decay_score_block",
        "authority_conflict_block",
        "authority_decay_score_watch",
        "authority_age_watch",
        "authority_conflict_watch",
        "authority_decay_pass",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.team_key for row in result.rows) == (
        "sports_team",
        "geo_team",
        "macro_team",
    )

    blocked = result.rows[0]
    assert blocked.source_age_seconds == d("9000.000000")
    assert blocked.freshness_decay_score == d("0.100000")
    assert blocked.decay_adjusted_authority_score == d("0.070000")
    assert blocked.specialist_authority_score == d("0.175000")
    assert blocked.authority_decay_risk_score == d("0.825000")
    assert blocked.reason_codes == (
        "authority_decay_score_block",
        "authority_conflict_block",
    )

    watched = result.rows[1]
    assert watched.source_age_seconds == d("3600.000000")
    assert watched.freshness_decay_score == d("0.500000")
    assert watched.decay_adjusted_authority_score == d("0.500000")
    assert watched.specialist_authority_score == d("0.585000")
    assert watched.authority_decay_risk_score == d("0.415000")
    assert watched.reason_codes == (
        "authority_decay_score_watch",
        "authority_age_watch",
        "authority_conflict_watch",
    )

    passed = result.rows[2]
    assert passed.freshness_decay_score == d("0.750000")
    assert passed.decay_adjusted_authority_score == d("0.712500")
    assert passed.specialist_authority_score == d("0.786250")
    assert passed.authority_decay_risk_score == d("0.213750")
    assert passed.reason_codes == ("authority_decay_pass",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_empty_report_is_pass_report_only_and_decimal_payload() -> None:
    result = report()

    assert result.status == "pass"
    assert result.reason_codes == ("authority_decay_empty",)
    assert result.row_count == d("0.000000")
    assert result.rows == ()
    assert result.reason_code_counts == (
        api.ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount(
            reason_code="authority_decay_empty",
            count=d("1.000000"),
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = api.research_team_specialist_source_authority_decay_scorecard_report_payload(
        result,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["status"] == "pass"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    assert_no_decimal_objects(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_public_payload_digest_is_deterministic_and_tamper_checked() -> None:
    pass_row = observation(
        team_key="macro_team",
        specialist_key="calendar_specialist",
        authority_family="official_calendar",
    )
    block_row = observation(
        team_key="sports_team",
        specialist_key="injury_specialist",
        authority_family="league_report",
        observed_at=GENERATED_AT - timedelta(seconds=9000),
        authority_score=d("0.700000"),
        source_decay_half_life_seconds=d("10000.000000"),
        corroboration_score=d("0.400000"),
        conflict_score=d("0.600000"),
    )
    report_a = report(pass_row, block_row)
    report_b = report(block_row, pass_row)

    payload_a = api.research_team_specialist_source_authority_decay_scorecard_report_payload(
        report_a,
    )
    payload_b = api.research_team_specialist_source_authority_decay_scorecard_report_payload(
        report_b,
    )
    digest_a = api.research_team_specialist_source_authority_decay_scorecard_report_digest(
        report_a,
    )

    assert payload_a == payload_b
    assert digest_a == api.research_team_specialist_source_authority_decay_scorecard_report_digest(
        report_b,
    )
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert_payload_has_no_raw_private_values(payload_a)
    api.validate_research_team_specialist_source_authority_decay_scorecard_report_digest(
        report_a,
    )
    api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
        payload_a,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload_a)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            tampered_payload,
        )

    tampered_digest = dict(payload_a)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            tampered_digest,
        )


def test_signed_public_payload_requires_canonical_report_shape_and_types() -> None:
    payload = api.research_team_specialist_source_authority_decay_scorecard_report_payload(
        report(observation()),
    )

    invalid_status = dict(payload)
    invalid_status["status"] = "ready"
    with pytest.raises(ValueError, match="status"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            resign_payload(invalid_status),
        )

    invalid_row_status = json.loads(json.dumps(payload))
    invalid_row_status["rows"][0]["status"] = "ready"
    with pytest.raises(ValueError, match="status"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            resign_payload(invalid_row_status),
        )

    false_hard_flag = dict(payload)
    false_hard_flag["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            resign_payload(false_hard_flag),
        )

    raw_numeric = dict(payload)
    raw_numeric["row_count"] = 1
    with pytest.raises(ValueError, match="row_count"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            resign_payload(raw_numeric),
        )

    extra_field = dict(payload)
    extra_field["safe_extra"] = "value"
    with pytest.raises(ValueError, match="report fields"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            resign_payload(extra_field),
        )

    unsupported_config = dict(payload)
    unsupported_config["config_version"] = "unsupported"
    with pytest.raises(ValueError, match="supported config version"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            resign_payload(unsupported_config),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("team_key", "123456"),
        ("specialist_key", "0x1234567890abcdef1234567890abcdef12345678"),
        ("authority_family", "will-btc-hit-100k"),
    ),
)
def test_public_aggregate_identifiers_reject_opaque_and_slug_shaped_values(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=f"{field_name} must be a public-safe aggregate identifier",
    ):
        observation(**{field_name: value})


def test_duplicate_aggregate_observation_identities_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="team_key, specialist_key, and authority_family triples must be unique",
    ):
        report(observation(), observation())


def test_dataclasses_are_frozen_decimal_only_and_status_limited() -> None:
    result = report(observation())

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(result.rows[0], status="blocked")

    assert set(api.RESEARCH_TEAM_SPECIALIST_SOURCE_AUTHORITY_DECAY_STATUSES) == {
        "pass",
        "watch",
        "block",
    }
    assert_no_non_decimal_public_numbers(result)

    for cls in (
        ResearchTeamSpecialistSourceAuthorityDecayScorecardConfig,
        ResearchTeamSpecialistSourceAuthorityDecayObservation,
        api.ResearchTeamSpecialistSourceAuthorityDecayScorecardRow,
        api.ResearchTeamSpecialistSourceAuthorityDecayReasonCodeCount,
        ResearchTeamSpecialistSourceAuthorityDecayScorecardReport,
    ):
        for field in fields(cls):
            assert field.name not in {"candidate", "url", "text", "dsn", "table", "token"}


def test_rejects_unsafe_public_values_and_keeps_module_report_only() -> None:
    unsafe_values = (
        "candidate_alpha",
        "market_alpha",
        "source_url_value",
        "source_text_value",
        "https://example.invalid/item",
        "raw_text",
        "dsn_value",
        "table_value",
        "token_value",
    )
    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            observation(team_key=unsafe_value)

    payload = api.research_team_specialist_source_authority_decay_scorecard_report_payload(
        report(observation()),
    )
    payload["raw_candidate"] = "candidate_alpha"
    with pytest.raises(ValueError, match="unsafe public"):
        api.validate_research_team_specialist_source_authority_decay_scorecard_public_payload(
            payload,
        )

    module_source = inspect.getsource(api).lower()
    for forbidden_text in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "wallet",
        "private_key",
        "network",
        "live trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden_text not in module_source
        assert not hasattr(api, forbidden_text)

    module_path = Path(api.__file__)
    assert module_path.name == (
        "research_team_specialist_source_authority_decay_scorecard_report.py"
    )


def assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_objects(item)


def assert_no_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None or isinstance(value, str):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public payload contains a non-string number: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_no_non_decimal_public_numbers(item)


def assert_payload_has_no_raw_private_values(payload: object) -> None:
    forbidden_terms = (
        "candidate",
        "market",
        "source_url",
        "source_text",
        "raw_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
    )

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                lowered_key = key.lower()
                assert not any(term in lowered_key for term in forbidden_terms)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            lowered_value = value.lower()
            assert not any(term in lowered_value for term in forbidden_terms)

    walk(payload)
