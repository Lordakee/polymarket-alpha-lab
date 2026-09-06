from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.settlement_evaluation import (
    SettlementEvaluationConfig,
    SettlementVerdict,
    SettledForecastSample,
    evaluate_settlement_samples,
    load_samples_document,
)


CUTOFF = datetime(2026, 10, 1, tzinfo=UTC)
GENERATED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
SETTLED = datetime(2026, 9, 20, tzinfo=UTC)


def sample(
    *,
    forecast="0.6",
    market="0.5",
    outcome="yes",
    team="crypto_btc",
    generated=GENERATED,
    settled=SETTLED,
    condition="0x1",
    event=None,
) -> SettledForecastSample:
    return SettledForecastSample(
        condition_id=condition,
        team_id=team,
        event_id=event,
        forecast_p_yes=Decimal(forecast),
        market_implied_p_yes=Decimal(market),
        actual_outcome=outcome,
        generated_at=generated,
        settled_at=settled,
    )


def config(**overrides) -> SettlementEvaluationConfig:
    values = dict(as_of_evaluation_cutoff=CUTOFF)
    values.update(overrides)
    return SettlementEvaluationConfig(**values)


def test_brier_logloss_and_paired_baseline_are_hand_verifiable() -> None:
    samples = [
        sample(forecast="0.8", market="0.5", outcome="yes", condition="0xa"),
        sample(forecast="0.8", market="0.5", outcome="no", condition="0xb"),
    ]
    report = evaluate_settlement_samples(samples, config())
    # Team: (0.8-1)^2 and (0.8-0)^2 -> mean (0.04+0.64)/2 = 0.34.
    assert report.team_brier == Decimal("0.34")
    # Market: 0.5 -> error 0.25 each -> mean 0.25.
    assert report.market_brier == Decimal("0.25")
    # Log loss: -ln(0.8) and -ln(0.2), averaged.
    import math

    expected = (Decimal(str(-math.log(0.8))) + Decimal(str(-math.log(0.2)))) / 2
    assert abs(report.team_log_loss - expected) < Decimal("0.000001")
    assert report.market_log_loss is not None
    assert abs(report.market_log_loss - Decimal(str(-math.log(0.5)))) < Decimal("0.000001")
    assert report.verdict is SettlementVerdict.INSUFFICIENT_SAMPLE  # N=2 < 30


def test_log_loss_clipping_prevents_infinite_loss() -> None:
    near_one = [sample(forecast="0.9999999", outcome="no", condition=f"0x{i}") for i in range(2)]
    report = evaluate_settlement_samples(near_one, config())
    # Clipped to 1-eps=0.999 -> reference 0.001 -> loss capped at -ln(0.001).
    assert report.team_log_loss is not None and report.team_log_loss.is_finite()
    assert abs(report.team_log_loss - Decimal("6.907755")) < Decimal("0.0001")


def test_market_log_loss_clips_yes_and_no_edges_with_same_epsilon() -> None:
    rows = [
        sample(forecast="0.5", market="0.0000001", outcome="yes", condition="yes"),
        sample(forecast="0.5", market="0.9999999", outcome="no", condition="no"),
    ]
    report = evaluate_settlement_samples(rows, config())
    assert report.market_log_loss is not None
    assert abs(report.market_log_loss - Decimal("6.907755")) < Decimal("0.0001")
    assert all(
        abs(row.market_log_loss - Decimal("6.907755")) < Decimal("0.0001")
        for row in report.hand_check_rows
    )


def test_condition_event_concentration_lags_and_bounded_hand_checks() -> None:
    rows = [
        sample(condition="c6", event=None, settled=GENERATED + timedelta(seconds=6)),
        sample(condition="c2", event="event-a", settled=GENERATED + timedelta(seconds=2)),
        sample(condition="c4", event="event-b", settled=GENERATED + timedelta(seconds=4)),
        sample(condition="c1", event="event-a", settled=GENERATED + timedelta(seconds=1)),
        sample(condition="c5", event=None, settled=GENERATED + timedelta(seconds=5)),
        sample(condition="c3", event="event-a", settled=GENERATED + timedelta(seconds=3)),
    ]
    report = evaluate_settlement_samples(rows, config())
    assert report.unique_condition_count == 6
    assert report.verified_unique_event_count == 2
    assert report.unknown_event_row_count == 2
    assert report.event_counts == (("event-a", 3), ("event-b", 1))
    assert report.max_verified_event_concentration == Decimal("0.75")
    assert report.settlement_lag_min_seconds == Decimal(1)
    assert report.settlement_lag_median_seconds == Decimal("3.5")
    assert report.settlement_lag_max_seconds == Decimal(6)
    assert [row.condition_id for row in report.hand_check_rows] == ["c1", "c2", "c3", "c4", "c5"]
    assert all(row.team_squared_error == Decimal("0.16") for row in report.hand_check_rows)


def test_odd_lag_median_and_n_zero_render_undefined() -> None:
    odd = evaluate_settlement_samples(
        [
            sample(condition="a", settled=GENERATED + timedelta(seconds=1)),
            sample(condition="b", settled=GENERATED + timedelta(seconds=9)),
            sample(condition="c", settled=GENERATED + timedelta(seconds=4)),
        ],
        config(),
    )
    assert odd.settlement_lag_median_seconds == Decimal(4)

    empty = evaluate_settlement_samples([], config(pending_count=3))
    assert empty.hand_check_rows == ()
    assert empty.coverage is None
    assert empty.market_log_loss is None
    assert empty.max_verified_event_concentration is None
    rendered = empty.render()
    assert "team_brier: undefined" in rendered
    assert "market_log_loss: undefined" in rendered
    assert "coverage_settled_ratio: undefined" in rendered
    assert "settlement_lag_median_seconds: undefined" in rendered


def test_verdict_branches() -> None:
    winning = [
        sample(forecast="0.9", market="0.5", outcome="yes", condition=f"w{i}")
        for i in range(35)
    ]
    report = evaluate_settlement_samples(winning, config())
    assert report.verdict is SettlementVerdict.INDICATIVE_EDGE
    winning_large = winning + [
        sample(forecast="0.9", market="0.5", outcome="yes", condition=f"x{i}")
        for i in range(70)
    ]
    report = evaluate_settlement_samples(winning_large, config())
    assert report.verdict is SettlementVerdict.COMPARATIVE_EDGE
    losing = [
        sample(forecast="0.1", market="0.9", outcome="yes", condition=f"l{i}")
        for i in range(40)
    ]
    report = evaluate_settlement_samples(losing, config())
    assert report.verdict is SettlementVerdict.NO_CONSISTENT_EDGE
    assert report.team_brier > report.market_brier


def test_lookahead_and_contract_exclusions_are_reason_coded() -> None:
    future = sample(
        generated=CUTOFF + timedelta(days=1),
        settled=CUTOFF + timedelta(days=2),
        condition="0xf",
    )
    report = evaluate_settlement_samples([future, sample()], config())
    assert report.included_count == 1
    assert report.exclusion_reasons == (("forecast_after_evaluation_cutoff", 1),)
    with pytest.raises(ValueError):
        sample(forecast="1.5")
    with pytest.raises(ValueError):
        sample(outcome="maybe")
    with pytest.raises(ValueError):
        sample(settled=GENERATED - timedelta(days=1))
    bad_rows = [{"condition_id": "0xz"}]
    report = evaluate_settlement_samples(bad_rows, config())
    assert report.exclusion_reasons == (("invalid_sample_contract", 1),)


def test_calibration_buckets_render_empty_and_counts() -> None:
    samples = [
        sample(forecast="0.05", outcome="yes", condition="0xp"),
        sample(forecast="0.95", outcome="no", condition="0xq"),
    ]
    report = evaluate_settlement_samples(samples, config())
    rendered = report.render()
    assert "[0.0, 0.1): n=1 mean_p=0.05 yes=1" in rendered
    assert "[0.9, 1.0): n=1 mean_p=0.95 yes=0" in rendered
    assert "[0.2, 0.3): empty" in rendered
    assert len(report.calibration_buckets) == 10


def test_team_concentration_coverage_and_limitations() -> None:
    samples = [sample(team="crypto_btc", condition=f"b{i}") for i in range(3)]
    samples += [sample(team="crypto_eth", condition=f"e{i}") for i in range(2)]
    report = evaluate_settlement_samples(samples, config(pending_count=4))
    assert report.team_counts == (("crypto_btc", 3), ("crypto_eth", 2))
    assert report.pending_count == 4
    assert report.coverage == Decimal(5) / Decimal(9)
    rendered = report.render()
    assert "pending_unsettled: 4" in rendered
    assert "coverage_settled_ratio:" in rendered
    assert "cost-adjusted paper results" in rendered
    assert "cost-adjusted paper results (fee/slippage/fill sensitivity) arm activates" in rendered
    assert "revision history not tracked" in rendered
    assert "https://" not in rendered


def test_document_loader_and_cli_end_to_end(tmp_path, capsys) -> None:
    document = {
        "as_of_evaluation_cutoff": CUTOFF.isoformat(),
        "pending_count": 1,
        "samples": [
            {
                "condition_id": "0xcli",
                "team_id": "crypto_btc",
                "forecast_p_yes": "0.7",
                "market_implied_p_yes": "0.5",
                "actual_outcome": "yes",
                "generated_at": GENERATED.isoformat(),
                "settled_at": SETTLED.isoformat(),
            }
        ],
    }
    path = tmp_path / "samples.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    rows, loaded = load_samples_document(path.read_text(encoding="utf-8"))
    report = evaluate_settlement_samples(rows, loaded)
    assert report.included_count == 1
    assert report.verdict is SettlementVerdict.INSUFFICIENT_SAMPLE

    from polymarket_alpha_lab.cli import main

    exit_code = main(["settlement-evaluation", "--samples", str(path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "verdict: insufficient_sample" in out
    assert "team_brier:" in out


def test_determinism() -> None:
    samples = [sample(forecast="0.55", condition=f"d{i}") for i in range(4)]
    first = evaluate_settlement_samples(samples, config())
    second = evaluate_settlement_samples(samples, config())
    assert first == second
    assert first.render() == second.render()
