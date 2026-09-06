from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

from polymarket_alpha_lab.settlement_export import (
    EXCLUSION_BASELINE_HINT,
    EXCLUSION_FORECAST_AFTER_CUTOFF,
    EXCLUSION_INVALID_ROW,
    EXCLUSION_NOT_EARLIEST,
    ForecastRowView,
    SettledOutcomeView,
    build_settlement_export,
)
from polymarket_alpha_lab.settlement_evaluation import load_samples_document


CUTOFF = datetime(2026, 10, 1, tzinfo=UTC)


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

    result = build_settlement_export([], [], as_of_evaluation_cutoff=CUTOFF)
    manifest = json.loads(result.manifest)
    assert result.document.endswith("\n")
    assert result.export_id == hashlib.sha256(result.document.encode()).hexdigest()
    assert manifest["export_id"] == result.export_id


def test_outcome_revision_uses_latest_observation() -> None:
    older = outcome(outcome="no", observed=datetime(2026, 9, 18, tzinfo=UTC))
    newer = outcome(outcome="yes", observed=datetime(2026, 9, 21, tzinfo=UTC))
    result = build_settlement_export(
        [forecast()], [older, newer], as_of_evaluation_cutoff=CUTOFF,
    )
    assert json.loads(result.document)["samples"][0]["actual_outcome"] == "yes"
    assert json.loads(result.document)["samples"][0]["settled_at"].startswith("2026-09-21")


def test_exported_document_loads_in_the_evaluator() -> None:
    rows = [forecast(condition=f"0x{i}", p="0.7", market="0.5") for i in range(3)]
    rows.append(forecast(condition="0xpend"))
    outcomes = [outcome(condition=f"0x{i}", outcome="yes") for i in range(3)]
    result = build_settlement_export(rows, outcomes, as_of_evaluation_cutoff=CUTOFF)
    parsed_rows, config = load_samples_document(result.document)
    assert len(parsed_rows) == 3 and config.pending_count == 1

    from polymarket_alpha_lab.settlement_evaluation import evaluate_settlement_samples

    report = evaluate_settlement_samples(parsed_rows, config)
    assert report.included_count == 3
    assert report.pending_count == 1
