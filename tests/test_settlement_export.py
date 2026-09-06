from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

from polymarket_alpha_lab.settlement_export import (
    EXCLUSION_BASELINE_HINT,
    EXCLUSION_FORECAST_AFTER_CUTOFF,
    EXCLUSION_INVALID_ROW,
    EXCLUSION_NOT_EARLIEST,
    EXCLUSION_OUTCOME_AFTER_CUTOFF,
    EXCLUSION_OUTCOME_BEFORE_FORECAST,
    ForecastRowView,
    SettledOutcomeView,
    build_settlement_export,
)
from polymarket_alpha_lab.settlement_evaluation import load_samples_document


CUTOFF = datetime(2026, 10, 1, tzinfo=UTC)
OUTCOME_CUTOFF = datetime(2026, 10, 2, tzinfo=UTC)


def forecast(condition="0x1", team="crypto_btc", config="p1-crypto_btc-v1",
             p="0.6", market="0.5", generated=datetime(2026, 9, 5, 12, tzinfo=UTC),
             forecast_id=None) -> ForecastRowView:
    return ForecastRowView(
        forecast_id=forecast_id or f"{condition}:{team}:1",
        condition_id=condition,
        team_id=team,
        config_version=config,
        forecast_p_yes=Decimal(p),
        market_implied_p_yes=Decimal(market),
        generated_at=generated,
    )


def outcome(condition="0x1", outcome="yes", observed=datetime(2026, 9, 20, tzinfo=UTC),
            dispute=False) -> SettledOutcomeView:
    return SettledOutcomeView(
        condition_id=condition,
        outcome=outcome,
        observed_at=observed,
        dispute_flag=dispute,
    )


def test_earliest_eligible_selection_and_deterministic_export() -> None:
    rows = [
        forecast(generated=datetime(2026, 9, 6, tzinfo=UTC), forecast_id="0x1:crypto_btc:2"),
        forecast(generated=datetime(2026, 9, 5, tzinfo=UTC), forecast_id="0x1:crypto_btc:1"),
        forecast(condition="0x0", team="crypto_eth", config="p1-crypto_eth-v1", market="0.4"),
    ]
    result = build_settlement_export(
        rows, [outcome(), outcome(condition="0x0", outcome="no")],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    document = json.loads(result.document)
    assert len(document["samples"]) == 2
    first = document["samples"][0]
    assert first["condition_id"] == "0x0" and first["team_id"] == "crypto_eth"
    assert first["forecast_p_yes"] == "0.6" and first["market_implied_p_yes"] == "0.4"
    assert first["actual_outcome"] == "no"
    assert document["samples"][1]["generated_at"].startswith("2026-09-05")
    replay = build_settlement_export(
        list(reversed(rows)), [outcome(), outcome(condition="0x0", outcome="no")],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    assert replay.document == result.document
    assert replay.export_id == result.export_id
    assert dict(result.exclusion_reasons) == {EXCLUSION_NOT_EARLIEST: 1}
    manifest = json.loads(result.manifest)
    assert manifest["selected_forecast_ids"] == [
        "0x0:crypto_eth:1",
        "0x1:crypto_btc:1",
    ]


def test_pending_disputed_and_exclusions_are_reason_coded() -> None:
    rows = [
        forecast(condition="0xpend"),
        forecast(condition="0xdisputed"),
        forecast(condition="0xold", config="m5-crypto_btc-v1"),
        forecast(condition="0xfuture", generated=CUTOFF + timedelta(days=1)),
    ]
    outcomes = [
        outcome(condition="0xdisputed", dispute=True),
    ]
    result = build_settlement_export(
        rows,
        outcomes,
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
        invalid_forecast_row_count=2,
    )
    document = json.loads(result.document)
    assert document["samples"] == []
    assert document["pending_count"] == 2  # unresolved + disputed
    assert result.exclusion_reasons == (
        (EXCLUSION_BASELINE_HINT, 1),
        (EXCLUSION_FORECAST_AFTER_CUTOFF, 1),
        (EXCLUSION_INVALID_ROW, 2),
    )
    manifest = json.loads(result.manifest)
    assert manifest["included_count"] == 0 and manifest["pending_count"] == 2
    assert manifest["disputed_pending"] == 1
    assert manifest["input_forecast_rows"] == 6


def test_export_id_hashes_exact_document_bytes() -> None:
    import hashlib

    result = build_settlement_export(
        [], [],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    manifest = json.loads(result.manifest)
    assert result.document.endswith("\n")
    assert result.export_id == hashlib.sha256(result.document.encode()).hexdigest()
    assert manifest["export_id"] == result.export_id


def test_outcome_revision_uses_latest_observation() -> None:
    older = outcome(outcome="no", observed=datetime(2026, 9, 18, tzinfo=UTC))
    newer = outcome(outcome="yes", observed=datetime(2026, 9, 21, tzinfo=UTC))
    result = build_settlement_export(
        [forecast()], [older, newer],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    assert json.loads(result.document)["samples"][0]["actual_outcome"] == "yes"
    assert json.loads(result.document)["samples"][0]["settled_at"].startswith("2026-09-21")


def test_exported_document_loads_in_the_evaluator() -> None:
    rows = [forecast(condition=f"0x{i}", p="0.7", market="0.5") for i in range(3)]
    rows.append(forecast(condition="0xpend"))
    outcomes = [outcome(condition=f"0x{i}", outcome="yes") for i in range(3)]
    result = build_settlement_export(
        rows, outcomes,
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    parsed_rows, config = load_samples_document(result.document)
    assert len(parsed_rows) == 3 and config.pending_count == 1

    from polymarket_alpha_lab.settlement_evaluation import evaluate_settlement_samples

    report = evaluate_settlement_samples(parsed_rows, config)
    assert report.included_count == 3
    assert report.pending_count == 1


def test_outcome_cutoff_and_pre_forecast_observations_are_reason_coded() -> None:
    generated = datetime(2026, 9, 10, tzinfo=UTC)
    rows = [
        forecast(condition="0xfuture", generated=generated),
        forecast(condition="0xbefore", generated=generated),
    ]
    outcomes = [
        outcome(
            condition="0xfuture",
            observed=OUTCOME_CUTOFF + timedelta(seconds=1),
        ),
        outcome(
            condition="0xbefore",
            observed=generated - timedelta(seconds=1),
        ),
    ]
    result = build_settlement_export(
        rows,
        outcomes,
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
        invalid_outcome_row_count=2,
    )
    assert result.included_count == 0
    assert result.pending_count == 1
    assert dict(result.exclusion_reasons) == {
        "invalid_outcome_row": 2,
        EXCLUSION_OUTCOME_AFTER_CUTOFF: 1,
        EXCLUSION_OUTCOME_BEFORE_FORECAST: 1,
    }


def test_latest_disputed_revision_is_pending_and_correction_is_linked() -> None:
    payload_hash = "a" * 64
    prior_export_id = "b" * 64
    result = build_settlement_export(
        [forecast()],
        [
            outcome(outcome="yes", observed=datetime(2026, 9, 20, tzinfo=UTC)),
            SettledOutcomeView(
                condition_id="0x1",
                outcome="no",
                observed_at=datetime(2026, 9, 21, tzinfo=UTC),
                dispute_flag=True,
                payload_sha256=payload_hash,
            ),
        ],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
        prior_export_id=prior_export_id,
    )
    manifest = json.loads(result.manifest)
    assert result.pending_count == 1
    assert result.included_count == 0
    assert manifest["disputed_pending"] == 1
    assert manifest["prior_export_id"] == prior_export_id


def test_selected_outcome_identity_and_payload_hash_are_deterministic() -> None:
    payload_hash = "c" * 64
    selected = SettledOutcomeView(
        condition_id="0x1",
        outcome="yes",
        observed_at=datetime(2026, 9, 20, tzinfo=UTC),
        payload_sha256=payload_hash,
    )
    result = build_settlement_export(
        [forecast()],
        [selected],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    manifest = json.loads(result.manifest)
    assert manifest["selected_outcome_ids"] == [selected.outcome_id]
    assert manifest["selected_outcome_payload_sha256"] == [payload_hash]


def test_outcome_cutoff_cannot_precede_forecast_cutoff() -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="as_of_outcome_cutoff must not precede as_of_evaluation_cutoff",
    ):
        build_settlement_export(
            [],
            [],
            as_of_evaluation_cutoff=CUTOFF,
            as_of_outcome_cutoff=CUTOFF - timedelta(seconds=1),
        )


def test_config_cohorts_remain_separate_and_unknown_lineage_is_counted() -> None:
    rows = [
        forecast(config="p1-crypto_btc-v1", forecast_id="forecast-v1"),
        forecast(config="p1-crypto_btc-v2", forecast_id="forecast-v2"),
    ]
    result = build_settlement_export(
        rows,
        [outcome()],
        as_of_evaluation_cutoff=CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )
    manifest = json.loads(result.manifest)
    assert result.included_count == 2
    assert manifest["config_versions"] == ["p1-crypto_btc-v1", "p1-crypto_btc-v2"]
    assert manifest["selected_cohorts"] == [
        "crypto_btc:p1-crypto_btc-v1",
        "crypto_btc:p1-crypto_btc-v2",
    ]
    assert manifest["unknown_event_lineage_count"] == 2
    assert manifest["selected_event_ids"] == []
