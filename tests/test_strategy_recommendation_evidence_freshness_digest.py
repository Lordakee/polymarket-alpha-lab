from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import json
from numbers import Number

import pytest

from polymarket_alpha_lab.strategy_recommendation_evidence_freshness_digest import (
    StrategyRecommendationEvidenceCandidate,
    StrategyRecommendationEvidenceFreshnessDigestConfig,
    StrategyRecommendationEvidenceFreshnessDigestReport,
    StrategyRecommendationEvidenceFreshnessDigestRollup,
    StrategyRecommendationEvidenceFreshnessDigestRow,
    StrategyRecommendationEvidenceSource,
    build_strategy_recommendation_evidence_freshness_digest,
    strategy_recommendation_evidence_freshness_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _config(**overrides) -> StrategyRecommendationEvidenceFreshnessDigestConfig:
    values = {
        "config_version": "strategy-recommendation-evidence-freshness-digest-v0",
        "required_source_families": (
            "market_snapshot",
            "probability_model",
            "resolution",
        ),
        "resolution_source_families": ("resolution",),
        "max_evidence_age_seconds": Decimal("300"),
        "max_resolution_evidence_age_seconds": Decimal("900"),
        "close_pressure_window_seconds": Decimal("600"),
    }
    values.update(overrides)
    return StrategyRecommendationEvidenceFreshnessDigestConfig(**values)


def _source(
    family: str,
    seconds_old: str | int,
    *,
    source_id: str | None = None,
    observed_at: datetime | None = None,
) -> StrategyRecommendationEvidenceSource:
    return StrategyRecommendationEvidenceSource(
        family=family,
        source_id=source_id if source_id is not None else f"{family}-source",
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=int(seconds_old))
        ),
    )


def _fresh_sources() -> tuple[StrategyRecommendationEvidenceSource, ...]:
    return (
        _source("market_snapshot", 10),
        _source("probability_model", 20),
        _source("resolution", 30),
    )


def _candidate(
    candidate_id: str = "candidate-1",
    market_slug: str = "alpha-market",
    *,
    evidence: tuple[StrategyRecommendationEvidenceSource, ...] | None = None,
    market_close_at: datetime | None = None,
) -> StrategyRecommendationEvidenceCandidate:
    return StrategyRecommendationEvidenceCandidate(
        candidate_id=candidate_id,
        market_slug=market_slug,
        market_close_at=(
            market_close_at
            if market_close_at is not None
            else GENERATED_AT + timedelta(seconds=3600)
        ),
        evidence=_fresh_sources() if evidence is None else evidence,
    )


def _build(
    candidates: tuple[StrategyRecommendationEvidenceCandidate, ...],
    *,
    config: StrategyRecommendationEvidenceFreshnessDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationEvidenceFreshnessDigestReport:
    return build_strategy_recommendation_evidence_freshness_digest(
        candidates,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_empty_input_is_blocked_readonly_report() -> None:
    report = _build(())

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.status == "blocked"
    assert report.reason_codes == ("no_recommendation_candidates",)
    assert report.candidate_count == Decimal("0")
    assert report.pass_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.blocked_count == Decimal("0")
    assert report.missing_family_count == Decimal("0")
    assert report.stale_resolution_candidate_count == Decimal("0")
    assert report.close_pressure_candidate_count == Decimal("0")
    assert report.rows == ()
    assert report.rollups == ()


def test_fresh_candidates_summarize_newest_and_oldest_required_ages() -> None:
    report = _build(
        (
            _candidate("candidate-2", "beta-market"),
            _candidate(
                "candidate-1",
                "alpha-market",
                evidence=(
                    _source("market_snapshot", 10),
                    _source("probability_model", 20),
                    _source("resolution", 30),
                ),
            ),
        ),
    )

    assert report.status == "pass"
    assert report.reason_codes == ("evidence_fresh",)
    assert report.candidate_count == Decimal("2")
    assert report.pass_count == Decimal("2")
    assert tuple(row.market_slug for row in report.rows) == (
        "alpha-market",
        "beta-market",
    )
    row = report.rows[0]
    assert isinstance(row, StrategyRecommendationEvidenceFreshnessDigestRow)
    assert row.newest_evidence_at == GENERATED_AT - timedelta(seconds=10)
    assert row.newest_evidence_age_seconds == Decimal("10")
    assert row.oldest_required_source_age_seconds == Decimal("30")
    assert row.missing_evidence_families == ()
    assert row.stale_resolution_evidence_families == ()
    assert row.market_close_pressure == "none"
    assert row.seconds_until_market_close == Decimal("3600")
    assert row.evidence_count == Decimal("3")
    assert row.evidence_family_count == Decimal("3")
    assert row.required_family_count == Decimal("3")
    assert row.missing_family_count == Decimal("0")
    assert tuple(rollup.family for rollup in report.rollups) == (
        "market_snapshot",
        "probability_model",
        "resolution",
    )
    assert all(
        isinstance(rollup, StrategyRecommendationEvidenceFreshnessDigestRollup)
        for rollup in report.rollups
    )
    assert tuple(rollup.present_count for rollup in report.rollups) == (
        Decimal("2"),
        Decimal("2"),
        Decimal("2"),
    )


def test_stale_required_evidence_watches_candidate() -> None:
    report = _build(
        (
            _candidate(
                evidence=(
                    _source("market_snapshot", 301),
                    _source("probability_model", 20),
                    _source("resolution", 30),
                ),
            ),
        ),
    )

    assert report.status == "watch"
    assert report.reason_codes == ("stale_required_evidence",)
    assert report.watch_count == Decimal("1")
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == ("stale_required_evidence",)
    assert report.rows[0].oldest_required_source_age_seconds == Decimal("301")


def test_missing_required_families_block_candidate_and_rollup() -> None:
    report = _build(
        (
            _candidate(
                evidence=(
                    _source("market_snapshot", 10),
                    _source("probability_model", 20),
                ),
            ),
        ),
    )

    assert report.status == "blocked"
    assert report.reason_codes == ("missing_evidence_family",)
    assert report.blocked_count == Decimal("1")
    assert report.missing_family_count == Decimal("1")
    assert report.rows[0].missing_evidence_families == ("resolution",)
    assert report.rows[0].missing_family_count == Decimal("1")
    assert report.rows[0].status == "blocked"
    resolution_rollup = report.rollups[0]
    assert resolution_rollup.family == "resolution"
    assert resolution_rollup.status == "blocked"
    assert resolution_rollup.reason_codes == ("missing_evidence_family",)
    assert resolution_rollup.missing_count == Decimal("1")


def test_stale_resolution_evidence_is_reported_separately() -> None:
    report = _build(
        (
            _candidate(
                evidence=(
                    _source("market_snapshot", 100),
                    _source("probability_model", 200),
                    _source("resolution", 901),
                ),
            ),
        ),
        config=_config(max_evidence_age_seconds=Decimal("1200")),
    )

    assert report.status == "watch"
    assert report.reason_codes == ("stale_resolution_evidence",)
    assert report.stale_resolution_candidate_count == Decimal("1")
    assert report.rows[0].stale_resolution_evidence_families == ("resolution",)
    assert report.rows[0].stale_resolution_family_count == Decimal("1")
    assert report.rows[0].reason_codes == ("stale_resolution_evidence",)
    assert report.rollups[0].family == "resolution"
    assert report.rollups[0].stale_resolution_count == Decimal("1")


def test_market_close_pressure_and_closed_markets_are_summarized() -> None:
    report = _build(
        (
            _candidate(
                "soon",
                "soon-market",
                market_close_at=GENERATED_AT + timedelta(seconds=300),
            ),
            _candidate(
                "closed",
                "closed-market",
                market_close_at=GENERATED_AT - timedelta(seconds=1),
            ),
        ),
    )

    assert report.status == "blocked"
    assert report.reason_codes == ("market_already_closed", "market_close_pressure")
    assert report.close_pressure_candidate_count == Decimal("2")
    assert tuple(row.market_slug for row in report.rows) == (
        "closed-market",
        "soon-market",
    )
    assert report.rows[0].market_close_pressure == "closed"
    assert report.rows[0].seconds_until_market_close == Decimal("-1")
    assert report.rows[0].status == "blocked"
    assert report.rows[1].market_close_pressure == "watch"
    assert report.rows[1].seconds_until_market_close == Decimal("300")
    assert report.rows[1].status == "watch"


def test_rows_rollups_and_reason_codes_are_sorted_stably() -> None:
    report = _build(
        (
            _candidate("z-pass", "zeta-market"),
            _candidate(
                "m-watch",
                "middle-market",
                evidence=(
                    _source("market_snapshot", 301),
                    _source("probability_model", 20),
                    _source("resolution", 30),
                ),
            ),
            _candidate(
                "a-blocked",
                "alpha-market",
                evidence=(
                    _source("market_snapshot", 10),
                    _source("probability_model", 20),
                ),
            ),
        ),
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "a-blocked",
        "m-watch",
        "z-pass",
    )
    assert tuple(row.status for row in report.rows) == ("blocked", "watch", "pass")
    assert report.reason_codes == (
        "missing_evidence_family",
        "stale_required_evidence",
    )
    assert tuple(rollup.family for rollup in report.rollups) == (
        "resolution",
        "market_snapshot",
        "probability_model",
    )
    assert tuple(rollup.status for rollup in report.rollups) == (
        "blocked",
        "watch",
        "pass",
    )


def test_payload_helper_uses_decimal_strings_and_no_float_values() -> None:
    report = _build((_candidate(),))

    payload = strategy_recommendation_evidence_freshness_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["newest_evidence_age_seconds"] == "10"
    assert payload["rows"][0]["oldest_required_source_age_seconds"] == "30"
    assert payload["rows"][0]["newest_evidence_at"] == "2026-07-02T11:59:50+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_decimal_values(payload)


def test_payload_helper_requires_report_hard_flags() -> None:
    report = _build((_candidate(),))

    with pytest.raises(ValueError, match="paper_only"):
        strategy_recommendation_evidence_freshness_digest_payload(
            replace(report, paper_only=False),
        )
    with pytest.raises(ValueError, match="report_only"):
        strategy_recommendation_evidence_freshness_digest_payload(
            replace(report, report_only=False),
        )
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_evidence_freshness_digest_payload(
            replace(report, readonly=False),
        )


def test_validation_rejects_bad_types_and_unsafe_inputs() -> None:
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("bad"))
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        _config(max_evidence_age_seconds=300)
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        _config(max_evidence_age_seconds=Decimal("-1"))
    with pytest.raises(ValueError, match="required_source_families"):
        _config(required_source_families=("market_snapshot", "market_snapshot"))
    with pytest.raises(ValueError, match="generated_at"):
        _build((_candidate(),), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        _build(
            (_candidate(),),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _build(
            (
                _candidate(
                    evidence=(
                        _source("market_snapshot", 10),
                        _source("probability_model", 20),
                        _source(
                            "resolution",
                            0,
                            observed_at=GENERATED_AT + timedelta(seconds=1),
                        ),
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError, match="family"):
        StrategyRecommendationEvidenceSource(
            family=_StringSubclass("market_snapshot"),
            source_id="source",
            observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at"):
        StrategyRecommendationEvidenceSource(
            family="market_snapshot",
            source_id="source",
            observed_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
        )
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        _config(max_evidence_age_seconds=_DecimalSubclass("300"))


def test_sorting_is_stable_when_row_sort_keys_match() -> None:
    report = _build(
        (
            _candidate(
                "candidate-z",
                "same-market",
                evidence=(
                    _source("market_snapshot", 301, source_id="z-snapshot"),
                    _source("probability_model", 20, source_id="z-model"),
                    _source("resolution", 30, source_id="z-resolution"),
                ),
            ),
            _candidate(
                "candidate-a",
                "same-market",
                evidence=(
                    _source("market_snapshot", 301, source_id="a-snapshot"),
                    _source("probability_model", 20, source_id="a-model"),
                    _source("resolution", 30, source_id="a-resolution"),
                ),
            ),
        ),
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-z",
        "candidate-a",
    )


def test_public_numeric_fields_are_decimal_only() -> None:
    report = _build((_candidate(),))
    instances = (
        _config(),
        report.rows[0],
        report.rollups[0],
        report,
    )

    for instance in instances:
        for field in fields(instance):
            value = getattr(instance, field.name)
            if _is_public_numeric_field(field.name):
                assert value is None or type(value) is Decimal


def test_dataclasses_are_frozen_and_hard_flags_are_true() -> None:
    report = _build((_candidate(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rollups[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_source("market_snapshot", 1), readonly=False)


def test_module_has_no_forbidden_runtime_surface_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "strategy_recommendation_evidence_freshness_digest.py",
    ).read_text()
    lowered = source.lower()

    for forbidden in (
        "api_key",
        "auth",
        "broker",
        "connect(",
        "httpx",
        "open(",
        "private_key",
        "psycopg",
        "requests",
        "secret",
        "sign",
        "socket",
        "sqlite",
        "subprocess",
        "token",
        "trade",
        "urllib",
        "wallet",
    ):
        assert forbidden not in lowered


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_ratio")
        or field_name.startswith("max_")
        or field_name.startswith("min_")
        or field_name == "close_pressure_window_seconds"
    )


def _assert_no_float_or_decimal_values(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_or_decimal_values(child)
        return
    if isinstance(value, list):
        for child in value:
            _assert_no_float_or_decimal_values(child)
        return
    if isinstance(value, Number) and not isinstance(value, bool):
        assert not isinstance(value, (float, Decimal))
