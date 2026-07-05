from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 5, 15, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_policy_poll_sample_drift_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "us-senate-alpha-dem-wins",
    pollster_id: str = "pollster-alpha",
    contest_key: str = "us-senate-alpha",
    sample_frame_key: str = "likely-voters",
    party_sample_drift_share: str | Decimal = "0.010000",
    demographic_sample_drift_share: str | Decimal = "0.020000",
    sample_size_drop_share: str | Decimal = "0.050000",
    days_until_event: str | Decimal = "60.000000",
    evidence_confidence: str | Decimal = "0.820000",
    observed_at: datetime = datetime(2026, 7, 5, 14, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_poll_sample_release",),
):
    module = digest()
    return module.PolicyPollSampleDriftObservation(
        source_id=source_id,
        market_slug=market_slug,
        pollster_id=pollster_id,
        contest_key=contest_key,
        sample_frame_key=sample_frame_key,
        party_sample_drift_share=(
            party_sample_drift_share
            if isinstance(party_sample_drift_share, Decimal)
            else d(party_sample_drift_share)
        ),
        demographic_sample_drift_share=(
            demographic_sample_drift_share
            if isinstance(demographic_sample_drift_share, Decimal)
            else d(demographic_sample_drift_share)
        ),
        sample_size_drop_share=(
            sample_size_drop_share
            if isinstance(sample_size_drop_share, Decimal)
            else d(sample_size_drop_share)
        ),
        days_until_event=(
            days_until_event
            if isinstance(days_until_event, Decimal)
            else d(days_until_event)
        ),
        evidence_confidence=(
            evidence_confidence
            if isinstance(evidence_confidence, Decimal)
            else d(evidence_confidence)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    if cfg is None:
        cfg = module.PolicyPollSampleDriftDigestConfig()
    return module.build_market_research_policy_poll_sample_drift_digest(
        rows,
        config=cfg,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.PolicyPollSampleDriftDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-policy-poll-sample-drift-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_poll_sample_drift_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.party_drift_row_count == d("0.000000")
    assert digest_report.demographic_drift_row_count == d("0.000000")
    assert digest_report.sample_size_drop_row_count == d("0.000000")
    assert digest_report.near_event_count == d("0.000000")
    assert digest_report.max_sample_drift_risk_score == d("0.000000")
    assert digest_report.average_sample_drift_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("poll_sample_drift_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.PolicyPollSampleDriftReasonCodeCount(
            reason_code="poll_sample_drift_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_sample_composition_drift_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            market_slug="us-senate-alpha-dem-wins",
            pollster_id="pollster-alpha",
            party_sample_drift_share="0.130000",
            demographic_sample_drift_share="0.200000",
            sample_size_drop_share="0.500000",
            days_until_event="7.000000",
            evidence_confidence="0.940000",
            observed_at=datetime(
                2026,
                7,
                5,
                10,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-watch",
            market_slug="us-governor-beta-dem-wins",
            pollster_id="pollster-beta",
            contest_key="us-governor-beta",
            party_sample_drift_share="0.060000",
            demographic_sample_drift_share="0.080000",
            sample_size_drop_share="0.100000",
            days_until_event="30.000000",
            observed_at=datetime(
                2026,
                7,
                5,
                10,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-pass",
            market_slug="us-house-gamma-dem-wins",
            pollster_id="pollster-gamma",
            contest_key="us-house-gamma",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_poll_sample_drift_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.party_drift_row_count == d("2.000000")
    assert digest_report.demographic_drift_row_count == d("2.000000")
    assert digest_report.sample_size_drop_row_count == d("1.000000")
    assert digest_report.near_event_count == d("1.000000")
    assert digest_report.max_sample_drift_risk_score == d("1.000000")
    assert digest_report.average_sample_drift_risk_score == d("0.499306")
    assert digest_report.reason_codes == (
        "official_poll_sample_release",
        "poll_sample_drift_below_threshold",
        "poll_sample_drift_blocked",
        "poll_sample_drift_demographic_mix_high",
        "poll_sample_drift_demographic_mix_material",
        "poll_sample_drift_near_event",
        "poll_sample_drift_party_mix_high",
        "poll_sample_drift_party_mix_material",
        "poll_sample_drift_sample_size_drop_high",
        "poll_sample_drift_sample_size_drop_material",
        "poll_sample_drift_source_fresh",
        "poll_sample_drift_watch",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "us-senate-alpha-dem-wins",
        "us-governor-beta-dem-wins",
        "us-house-gamma-dem-wins",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.drift_status == "blocked"
    assert blocked.sample_drift_risk_score == d("1.000000")
    assert blocked.observed_at == datetime(2026, 7, 5, 14, 0, tzinfo=UTC)
    assert blocked.source_age_seconds == d("5400.000000")
    assert blocked.reason_codes == (
        "official_poll_sample_release",
        "poll_sample_drift_blocked",
        "poll_sample_drift_demographic_mix_high",
        "poll_sample_drift_demographic_mix_material",
        "poll_sample_drift_near_event",
        "poll_sample_drift_party_mix_high",
        "poll_sample_drift_party_mix_material",
        "poll_sample_drift_sample_size_drop_high",
        "poll_sample_drift_sample_size_drop_material",
        "poll_sample_drift_source_fresh",
    )
    assert blocked.capped_confidence == d("0.940000")
    assert watched.drift_status == "watch"
    assert watched.sample_drift_risk_score == d("0.397500")
    assert watched.source_age_seconds == d("2700.000000")
    assert watched.reason_codes == (
        "official_poll_sample_release",
        "poll_sample_drift_demographic_mix_material",
        "poll_sample_drift_party_mix_material",
        "poll_sample_drift_source_fresh",
        "poll_sample_drift_watch",
    )
    assert passed.drift_status == "pass"
    assert passed.sample_drift_risk_score == d("0.100417")
    assert passed.confidence_cap == d("0.650000")
    assert passed.capped_confidence == d("0.650000")
    assert passed.reason_codes == (
        "official_poll_sample_release",
        "poll_sample_drift_below_threshold",
        "poll_sample_drift_source_fresh",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        party_sample_drift_share="0.060000",
        demographic_sample_drift_share="0.080000",
        sample_size_drop_share="0.100000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        party_sample_drift_share="0.130000",
        demographic_sample_drift_share="0.200000",
        sample_size_drop_share="0.500000",
        days_until_event="7.000000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        party_sample_drift_share="0.060000",
        demographic_sample_drift_share="0.080000",
        sample_size_drop_share="0.100000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        forward.reason_codes
    )


def test_validation_rejects_bad_inputs_and_noncanonical_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="party_sample_drift_share must be a Decimal"):
        observation(party_sample_drift_share=_DecimalSubclass("0.050000"))
    with pytest.raises(
        ValueError,
        match="party_sample_drift_share must be between 0 and 1",
    ):
        observation(party_sample_drift_share="1.100000")
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 5, 14, 0))
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(
            observed_at=datetime(2026, 7, 5, 14, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="upstream_reason_codes must be sorted"):
        observation(upstream_reason_codes=("z_reason", "a_reason"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_poll_sample_drift_digest(
            (),
            config=module.PolicyPollSampleDriftDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 15, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.build_market_research_policy_poll_sample_drift_digest(
            (observation("source-future"),),
            config=module.PolicyPollSampleDriftDigestConfig(),
            generated_at=datetime(2026, 7, 5, 13, 0, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="material_party_drift_share must not exceed high_party_drift_share",
    ):
        module.PolicyPollSampleDriftDigestConfig(
            material_party_drift_share=d("0.200000"),
            high_party_drift_share=d("0.100000"),
        )

    digest_report = report(
        observation(
            "source-blocked",
            market_slug="alpha-blocked",
            party_sample_drift_share="0.130000",
            demographic_sample_drift_share="0.200000",
            sample_size_drop_share="0.500000",
            days_until_event="7.000000",
        ),
        observation(
            "source-watch",
            market_slug="beta-watch",
            party_sample_drift_share="0.060000",
            demographic_sample_drift_share="0.080000",
            sample_size_drop_share="0.100000",
        ),
    )
    with pytest.raises(ValueError, match="sample_drift_risk_score must match row factors"):
        replace(digest_report.rows[0], sample_drift_risk_score=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match row factors"):
        replace(
            digest_report.rows[0],
            reason_codes=(
                "official_poll_sample_release",
                "poll_sample_drift_blocked",
                "poll_sample_drift_source_fresh",
            ),
        )
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(digest_report, rows=tuple(reversed(digest_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        replace(digest_report, reason_codes=tuple(reversed(digest_report.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(
            digest_report,
            reason_code_counts=tuple(reversed(digest_report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="count must be positive"):
        module.PolicyPollSampleDriftReasonCodeCount(
            reason_code="manual_reason",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadObservation(module.PolicyPollSampleDriftObservation):
            pass

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.PolicyPollSampleDriftDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason_code_count paper_only must be True"):
        replace(digest_report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_non_default_thresholds_can_downgrade_moderate_sample_drift_risk() -> None:
    module = digest()
    cfg = module.PolicyPollSampleDriftDigestConfig(
        watch_sample_drift_risk_score=d("0.500000"),
        blocked_sample_drift_risk_score=d("0.900000"),
        material_party_drift_share=d("0.100000"),
        high_party_drift_share=d("0.200000"),
        material_demographic_drift_share=d("0.120000"),
        high_demographic_drift_share=d("0.250000"),
        material_sample_size_drop_share=d("0.250000"),
        high_sample_size_drop_share=d("0.500000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            party_sample_drift_share="0.060000",
            demographic_sample_drift_share="0.080000",
            sample_size_drop_share="0.100000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_poll_sample_drift_screening"
    )
    assert digest_report.rows[0].drift_status == "pass"
    assert digest_report.rows[0].sample_drift_risk_score == d("0.251000")
    assert digest_report.rows[0].reason_codes == (
        "official_poll_sample_release",
        "poll_sample_drift_below_threshold",
        "poll_sample_drift_source_fresh",
    )
    assert digest_report.party_drift_row_count == d("0.000000")
    assert digest_report.demographic_drift_row_count == d("0.000000")
    assert digest_report.sample_size_drop_row_count == d("0.000000")


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_policy_poll_sample_drift_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["party_sample_drift_share"] == "0.010000"
    assert payload["rows"][0]["sample_drift_risk_score"] == "0.100417"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T14:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, Decimal | datetime | float)

    walk_payload(payload)

    for public_record in (
        module.PolicyPollSampleDriftDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_policy_poll_sample_drift_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "pathlib",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (called_names & {"open", "read_text", "write_text", "connect", "execute"})
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
    ):
        assert forbidden not in source.lower()


def test_payload_revalidates_nested_public_records_before_serialization() -> None:
    module = digest()

    for field_name in ("paper_only", "report_only", "readonly"):
        digest_report = report(observation(f"source-report-{field_name}"))
        object.__setattr__(digest_report, field_name, False)
        with pytest.raises(ValueError, match=f"report {field_name} must be True"):
            module.market_research_policy_poll_sample_drift_digest_payload(
                digest_report,
            )

    for field_name in ("paper_only", "report_only", "readonly"):
        digest_report = report(observation(f"source-row-{field_name}"))
        object.__setattr__(digest_report.rows[0], field_name, False)
        with pytest.raises(ValueError, match=f"row {field_name} must be True"):
            module.market_research_policy_poll_sample_drift_digest_payload(
                digest_report,
            )

    for field_name in ("paper_only", "report_only", "readonly"):
        digest_report = report(observation(f"source-count-{field_name}"))
        object.__setattr__(digest_report.reason_code_counts[0], field_name, False)
        with pytest.raises(
            ValueError,
            match=f"reason_code_count {field_name} must be True",
        ):
            module.market_research_policy_poll_sample_drift_digest_payload(
                digest_report,
            )

    digest_report = report(observation("source-non-six-decimal"))
    object.__setattr__(
        digest_report.rows[0],
        "party_sample_drift_share",
        d("0.0100000"),
    )
    with pytest.raises(
        ValueError,
        match="party_sample_drift_share must have exactly six decimal places",
    ):
        module.market_research_policy_poll_sample_drift_digest_payload(
            digest_report,
        )

    digest_report = report(observation("source-noncanonical-row"))
    object.__setattr__(digest_report.rows[0], "pollster_id", " pollster-alpha")
    with pytest.raises(
        ValueError,
        match="pollster_id must be a canonical nonblank string",
    ):
        module.market_research_policy_poll_sample_drift_digest_payload(
            digest_report,
        )

    digest_report = report(observation("source-duplicate-row-reason"))
    object.__setattr__(
        digest_report.rows[0],
        "reason_codes",
        digest_report.rows[0].reason_codes + ("official_poll_sample_release",),
    )
    with pytest.raises(
        ValueError,
        match="reason_codes must contain unique reason codes",
    ):
        module.market_research_policy_poll_sample_drift_digest_payload(
            digest_report,
        )

    digest_report = report(observation("source-noncanonical-count"))
    object.__setattr__(
        digest_report.reason_code_counts[0],
        "reason_code",
        " official_poll_sample_release",
    )
    with pytest.raises(
        ValueError,
        match="reason_code must be a canonical nonblank string",
    ):
        module.market_research_policy_poll_sample_drift_digest_payload(
            digest_report,
        )

    digest_report = report(observation("source-nested-type"))
    object.__setattr__(digest_report, "rows", (object(),))
    with pytest.raises(
        ValueError,
        match="rows must contain PolicyPollSampleDriftDigestRow",
    ):
        module.market_research_policy_poll_sample_drift_digest_payload(
            digest_report,
        )


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
