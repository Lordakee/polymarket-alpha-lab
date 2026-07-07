from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.candidate_portfolio_exposure_throttle import (
    BOUNDARY_STATEMENT,
    CandidatePortfolioExposureBucket,
    CandidatePortfolioExposureCandidate,
    CandidatePortfolioExposureSnapshot,
    CandidatePortfolioExposureThrottleConfig,
    CandidatePortfolioExposureThrottleReport,
    CandidatePortfolioExposureThrottleRow,
    build_candidate_portfolio_exposure_throttle_report,
    candidate_portfolio_exposure_throttle_payload,
)


STAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def _config(**overrides: object) -> CandidatePortfolioExposureThrottleConfig:
    values: dict[str, object] = {
        "team_watch_ratio": Decimal("0.300000"),
        "team_block_ratio": Decimal("0.500000"),
        "event_watch_ratio": Decimal("0.200000"),
        "event_block_ratio": Decimal("0.350000"),
        "side_watch_ratio": Decimal("0.600000"),
        "side_block_ratio": Decimal("0.800000"),
        "minimum_cash_buffer_ratio": Decimal("0.100000"),
        "long_cash_lockup_days": Decimal("14.000000"),
        "block_cash_lockup_days": Decimal("45.000000"),
    }
    values.update(overrides)
    return CandidatePortfolioExposureThrottleConfig(**values)


def _snapshot(
    *,
    total_paper_equity: Decimal = Decimal("100.000000"),
    available_cash: Decimal = Decimal("80.000000"),
    exposures: tuple[CandidatePortfolioExposureBucket, ...] = (),
) -> CandidatePortfolioExposureSnapshot:
    return CandidatePortfolioExposureSnapshot(
        total_paper_equity=total_paper_equity,
        available_cash=available_cash,
        exposures=exposures,
    )


def _bucket(
    bucket_type: str,
    bucket_value: str,
    current_notional: Decimal,
) -> CandidatePortfolioExposureBucket:
    return CandidatePortfolioExposureBucket(
        bucket_type=bucket_type,
        bucket_value=bucket_value,
        current_notional=current_notional,
    )


def _candidate(**overrides: object) -> CandidatePortfolioExposureCandidate:
    values: dict[str, object] = {
        "candidate_reference": "candidate-alpha",
        "event_reference": "event-alpha",
        "team_id": "sports",
        "side": "yes",
        "candidate_notional": Decimal("5.000000"),
        "cash_lockup_days": Decimal("2.000000"),
        "hard_safety_flags": (),
    }
    values.update(overrides)
    return CandidatePortfolioExposureCandidate(**values)


def test_report_returns_pass_watch_block_counts_and_aggregate_ratios() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-pass",
                event_reference="event-alpha",
                team_id="sports",
                side="no",
                candidate_notional=Decimal("5.000000"),
            ),
            _candidate(
                candidate_reference="candidate-block",
                event_reference="event-beta",
                team_id="sports",
                side="no",
                candidate_notional=Decimal("10.000000"),
            ),
            _candidate(
                candidate_reference="candidate-watch",
                event_reference="event-gamma",
                team_id="crypto",
                side="yes",
                candidate_notional=Decimal("10.000000"),
            ),
        ),
        snapshot=_snapshot(
            exposures=(
                _bucket("event", "event-beta", Decimal("30.000000")),
                _bucket("team", "crypto", Decimal("25.000000")),
                _bucket("side", "yes", Decimal("20.000000")),
                _bucket("team", "sports", Decimal("5.000000")),
                _bucket("event", "event-alpha", Decimal("5.000000")),
                _bucket("side", "no", Decimal("5.000000")),
            ),
        ),
        config=_config(),
        generated_at=STAMP,
    )

    assert isinstance(report, CandidatePortfolioExposureThrottleReport)
    assert report.generated_at == STAMP
    assert report.boundary_statement == BOUNDARY_STATEMENT
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.status == "block"
    assert report.candidate_count == Decimal("3")
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert report.total_candidate_notional == Decimal("25.000000")
    assert report.aggregate_candidate_notional_to_equity_ratio == Decimal("0.250000")
    assert report.max_projected_team_exposure_ratio == Decimal("0.350000")
    assert report.max_projected_event_exposure_ratio == Decimal("0.400000")
    assert report.max_projected_side_exposure_ratio == Decimal("0.300000")
    assert report.min_projected_cash_buffer_ratio == Decimal("0.700000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert "event_exposure_block" in report.rows[0].reason_codes
    assert "team_exposure_watch" in report.rows[1].reason_codes
    assert report.rows[2].reason_codes == ("candidate_exposure_pass",)
    assert all(row.redacted_candidate_reference.startswith("candidate_ref_") for row in report.rows)
    assert all(row.redacted_event_reference.startswith("event_ref_") for row in report.rows)


def test_same_team_concentration_watches_candidate() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-team",
                event_reference="event-team",
                team_id="crypto",
                side="yes",
                candidate_notional=Decimal("10.000000"),
            ),
        ),
        snapshot=_snapshot(
            exposures=(
                _bucket("team", "crypto", Decimal("25.000000")),
                _bucket("event", "event-team", Decimal("1.000000")),
                _bucket("side", "yes", Decimal("1.000000")),
            ),
        ),
        config=_config(),
        generated_at=STAMP,
    )

    assert report.status == "watch"
    assert report.watch_count == Decimal("1")
    assert report.rows[0].projected_team_exposure_ratio == Decimal("0.350000")
    assert report.rows[0].reason_codes == (
        "candidate_exposure_watch",
        "team_exposure_watch",
    )


def test_long_cash_lockup_horizon_watches_without_blocking() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-long-lock",
                event_reference="event-long-lock",
                cash_lockup_days=Decimal("21.000000"),
            ),
        ),
        snapshot=_snapshot(),
        config=_config(),
        generated_at=STAMP,
    )

    assert report.status == "watch"
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == (
        "candidate_exposure_watch",
        "long_cash_lockup_horizon",
    )


def test_insufficient_cash_buffer_blocks_candidate() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-cash-buffer",
                event_reference="event-cash-buffer",
                candidate_notional=Decimal("8.000000"),
            ),
        ),
        snapshot=_snapshot(available_cash=Decimal("12.000000")),
        config=_config(),
        generated_at=STAMP,
    )

    assert report.status == "block"
    assert report.rows[0].projected_cash_buffer == Decimal("4.000000")
    assert report.rows[0].projected_cash_buffer_ratio == Decimal("0.040000")
    assert report.rows[0].reason_codes == (
        "candidate_exposure_block",
        "cash_buffer_below_minimum",
    )


def test_dataclasses_are_frozen_decimal_only_and_reject_float_inputs() -> None:
    candidate = _candidate()
    report = build_candidate_portfolio_exposure_throttle_report(
        (candidate,),
        snapshot=_snapshot(),
        config=_config(),
        generated_at=STAMP,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "allow"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="candidate_notional must be a finite Decimal"):
        replace(candidate, candidate_notional=1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_watch_ratio must be a finite Decimal"):
        _config(team_watch_ratio=0.3)
    with pytest.raises(ValueError, match="current_notional must be a finite Decimal"):
        _bucket("team", "crypto", 1.0)  # type: ignore[arg-type]
    for public_record in (
        _config(),
        candidate,
        _snapshot(),
        report,
        *report.rows,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        _assert_no_float_or_int(public_record)


def test_hard_flags_block_candidate_and_stay_visible_as_safe_codes() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-hard-flag",
                event_reference="event-hard-flag",
                hard_safety_flags=("manual_review",),
            ),
        ),
        snapshot=_snapshot(),
        config=_config(),
        generated_at=STAMP,
    )

    assert report.status == "block"
    assert report.block_count == Decimal("1")
    assert report.hard_flag_count == Decimal("1")
    assert report.rows[0].hard_safety_flags == ("manual_review",)
    assert report.rows[0].reason_codes == (
        "candidate_exposure_block",
        "hard_safety_flag_present",
        "hard_safety_flag_manual_review",
    )


def test_public_dataclasses_reject_subclassing() -> None:
    for public_class in (
        CandidatePortfolioExposureThrottleConfig,
        CandidatePortfolioExposureBucket,
        CandidatePortfolioExposureSnapshot,
        CandidatePortfolioExposureCandidate,
        CandidatePortfolioExposureThrottleRow,
        CandidatePortfolioExposureThrottleReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_class.__name__}Child", (public_class,), {})


def test_config_version_is_fixed_and_hard_flags_sort_deterministically() -> None:
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="candidate-portfolio-exposure-risk-v999")

    candidate = _candidate(hard_safety_flags=("z_review", "a_review", "z_review"))

    assert candidate.hard_safety_flags == ("a_review", "z_review")


def test_unsafe_public_values_are_rejected_and_payload_uses_redacted_refs() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-public-alpha",
                event_reference="event-public-alpha",
            ),
        ),
        snapshot=_snapshot(),
        config=_config(),
        generated_at=STAMP,
    )

    payload = candidate_portfolio_exposure_throttle_payload(report)
    payload_text = repr(payload)
    assert payload["generated_at"] == "2026-01-02T03:04:05+00:00"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith("candidate_ref_")
    assert payload["rows"][0]["redacted_event_reference"].startswith("event_ref_")
    assert "candidate-public-alpha" not in payload_text
    assert "event-public-alpha" not in payload_text
    assert "candidate_exposure_pass" in payload_text
    assert "candidate_exposure_allow" not in payload_text
    assert "candidate_exposure_throttle" not in payload_text
    assert _json_contains_no_float(payload)

    with pytest.raises(ValueError, match="unsafe public value"):
        _candidate(candidate_reference="candidate-wallet-alpha")
    with pytest.raises(ValueError, match="unredacted reference"):
        candidate_portfolio_exposure_throttle_payload(
            {
                **payload,
                "candidate_reference": "candidate-public-alpha",
            },
        )
    with pytest.raises(ValueError, match="unredacted reference"):
        candidate_portfolio_exposure_throttle_payload(
            {
                **payload,
                "rows": [
                    {
                        **payload["rows"][0],
                        "event_reference": "event-public-alpha",
                    },
                ],
            },
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        candidate_portfolio_exposure_throttle_payload(
            {
                **payload,
                "rows": [
                    {
                        **payload["rows"][0],
                        "redacted_candidate_reference": "candidate_ref_wallet",
                    },
                ],
            },
        )


def test_payload_is_decision_support_view_without_position_sizing() -> None:
    report = build_candidate_portfolio_exposure_throttle_report(
        (
            _candidate(
                candidate_reference="candidate-sized-alpha",
                event_reference="event-sized-alpha",
                candidate_notional=Decimal("5.000000"),
            ),
            _candidate(
                candidate_reference="candidate-sized-beta",
                event_reference="event-sized-beta",
                candidate_notional=Decimal("10.000000"),
            ),
        ),
        snapshot=_snapshot(
            exposures=(
                _bucket("team", "sports", Decimal("25.000000")),
                _bucket("event", "event-sized-beta", Decimal("30.000000")),
                _bucket("side", "yes", Decimal("20.000000")),
            ),
        ),
        config=_config(),
        generated_at=STAMP,
    )

    payload = candidate_portfolio_exposure_throttle_payload(report)
    payload_text = repr(payload)

    assert set(payload) == {
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "hard_flag_count",
        "status",
        "reason_codes",
        "rows",
        "boundary_statement",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["rows"][0]) == {
        "redacted_candidate_reference",
        "redacted_event_reference",
        "status",
        "reason_codes",
        "hard_safety_flags",
        "boundary_statement",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert "candidate-sized-alpha" not in payload_text
    assert "event-sized-beta" not in payload_text
    for sizing_value in (
        "5.000000",
        "10.000000",
        "20.000000",
        "25.000000",
        "30.000000",
        "0.150000",
        "0.300000",
        "0.350000",
        "0.400000",
        "0.700000",
    ):
        assert sizing_value not in payload_text


def test_payload_rejects_position_sizing_fields_sensitive_refs_and_action_language() -> None:
    payload = candidate_portfolio_exposure_throttle_payload(
        build_candidate_portfolio_exposure_throttle_report(
            (_candidate(),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        ),
    )

    for unsafe_payload in (
        {**payload, "candidate_notional": "5.000000"},
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "projected_cash_buffer_ratio": "0.700000",
                },
            ],
        },
    ):
        with pytest.raises(ValueError, match="position sizing"):
            candidate_portfolio_exposure_throttle_payload(unsafe_payload)

    for unsafe_payload in (
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "redacted_candidate_reference": "candidate_ref_internal_alpha",
                },
            ],
        },
        {**payload, "market_slug": "election-outcome"},
        {**payload, "source_url": "redacted"},
        {**payload, "database_dsn": "redacted"},
        {**payload, "table_name": "portfolio_candidates"},
        {**payload, "note": "buy candidate now"},
        {**payload, "note": "sell candidate now"},
        {**payload, "note": "recommended candidate"},
    ):
        with pytest.raises(ValueError, match="unsafe|redacted"):
            candidate_portfolio_exposure_throttle_payload(unsafe_payload)


def test_payload_rejects_extra_public_fields_even_when_values_are_safe() -> None:
    payload = candidate_portfolio_exposure_throttle_payload(
        build_candidate_portfolio_exposure_throttle_report(
            (_candidate(),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        ),
    )

    for unsafe_payload in (
        {**payload, "note": "paper only diagnostic"},
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "note": "paper only diagnostic",
                },
            ],
        },
    ):
        with pytest.raises(ValueError, match="unexpected public field"):
            candidate_portfolio_exposure_throttle_payload(unsafe_payload)


def test_payload_rejects_blocked_status_vocabulary_in_public_dicts() -> None:
    payload = candidate_portfolio_exposure_throttle_payload(
        build_candidate_portfolio_exposure_throttle_report(
            (_candidate(),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        ),
    )

    for unsafe_payload in (
        {**payload, "status": "blocked"},
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "status": "blocked",
                },
            ],
        },
    ):
        with pytest.raises(ValueError, match="status"):
            candidate_portfolio_exposure_throttle_payload(unsafe_payload)


def test_payload_rejects_position_sizing_language_in_public_values() -> None:
    payload = candidate_portfolio_exposure_throttle_payload(
        build_candidate_portfolio_exposure_throttle_report(
            (_candidate(),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        ),
    )

    for unsafe_payload in (
        {**payload, "reason_codes": [*payload["reason_codes"], "notional_review"]},
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "hard_safety_flags": ["position_size_review"],
                },
            ],
        },
    ):
        with pytest.raises(ValueError, match="position sizing"):
            candidate_portfolio_exposure_throttle_payload(unsafe_payload)

    with pytest.raises(ValueError, match="position sizing"):
        report = build_candidate_portfolio_exposure_throttle_report(
            (_candidate(hard_safety_flags=("position_size_review",)),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        )
        candidate_portfolio_exposure_throttle_payload(report)


def test_payload_rejects_stake_allocation_and_amount_language_in_public_codes() -> None:
    payload = candidate_portfolio_exposure_throttle_payload(
        build_candidate_portfolio_exposure_throttle_report(
            (_candidate(),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        ),
    )

    for unsafe_payload in (
        {
            **payload,
            "reason_codes": [
                *payload["reason_codes"],
                "hard_safety_flag_stake_review",
            ],
        },
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "hard_safety_flags": ["allocation_amount_review"],
                },
            ],
        },
    ):
        with pytest.raises(ValueError, match="position sizing"):
            candidate_portfolio_exposure_throttle_payload(unsafe_payload)

    with pytest.raises(ValueError, match="position sizing"):
        report = build_candidate_portfolio_exposure_throttle_report(
            (_candidate(hard_safety_flags=("stake_review",)),),
            snapshot=_snapshot(),
            config=_config(),
            generated_at=STAMP,
        )
        candidate_portfolio_exposure_throttle_payload(report)


def test_module_stays_pure_report_only_boundary() -> None:
    source = Path("src/polymarket_alpha_lab/candidate_portfolio_exposure_throttle.py").read_text()
    lowered_source = source.lower()

    forbidden_terms = (
        "api",
        "auth",
        "client",
        "wallet",
        "order",
        "account",
        "trade",
        "private_key",
        "sign",
        "cancel",
        "replace",
        "exchange_mutation",
        "subprocess",
        "socket",
        "requests",
        "http",
        "supabase",
        "postgres",
        "os.environ",
        "open(",
        "pathlib",
        "argparse",
        "click",
        "typer",
    )
    for term in forbidden_terms:
        assert term not in lowered_source

    assert "paper_only: bool = True" in source
    assert "report_only: bool = True" in source
    assert "readonly: bool = True" in source


def _assert_no_float_or_int(value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_float_or_int(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, int)
    assert not isinstance(value, float)


def _json_contains_no_float(value: Any) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, dict):
        return all(_json_contains_no_float(item) for item in value.values())
    if isinstance(value, list):
        return all(_json_contains_no_float(item) for item in value)
    return True
