from datetime import UTC, datetime, timedelta
import hashlib
import json

import pytest

from polymarket_alpha_lab.settlement_checkpoint import (
    P2_CHECKPOINT_SCHEMA_VERSION,
    P2CheckpointError,
    load_p2_checkpoint,
    validate_p2_checkpoint_document,
    verify_p2_checkpoint_artifacts,
)


CUTOFF = datetime(2026, 9, 8, tzinfo=UTC)
HORIZON = datetime(2026, 10, 7, tzinfo=UTC)
MARKET_END = datetime(2026, 9, 9, tzinfo=UTC)
GENERATED_AT = datetime(2026, 9, 7, 12, tzinfo=UTC)


def _record(**overrides):
    record = {
        "forecast_id": "forecast-1",
        "forecast_payload_sha256": "a" * 64,
        "condition_id": "0xabc",
        "team_id": "crypto_btc",
        "config_version": "p1-crypto_btc-v1",
        "event_id": "event-1",
        "event_slug": "event-one",
        "generated_at": GENERATED_AT.isoformat(),
        "market_end_at": MARKET_END.isoformat(),
        "lead_seconds": int((MARKET_END - GENERATED_AT).total_seconds()),
        "metadata_observed_at": GENERATED_AT.isoformat(),
        "metadata_payload_sha256": "f" * 64,
    }
    record.update(overrides)
    return record


def _document(records=None, **overrides):
    records = [_record()] if records is None else records
    document = {
        "schema_version": P2_CHECKPOINT_SCHEMA_VERSION,
        "cohort_id": "p2-test-cohort",
        "hypothesis_label": "zero_impact_market_control",
        "independent_hypothesis_status": "not_implemented",
        "teams": [
            {"team_id": "crypto_btc", "config_version": "p1-crypto_btc-v1", "tag_id": "235"},
            {"team_id": "crypto_eth", "config_version": "p1-crypto_eth-v1", "tag_id": "39"},
        ],
        "gamma_query": {"closed": False, "limit": 100, "offset": 0},
        "market_selector": {
            "active": True,
            "binary": True,
            "closed": False,
            "team_keyword_required": True,
        },
        "forecast_selection_rule": (
            "earliest eligible forecast per (condition_id, team_id, config_version) "
            "generated before the forecast cutoff"
        ),
        "minimum_lead_seconds": 1800,
        "cohort_horizon": HORIZON.isoformat(),
        "as_of_evaluation_cutoff": CUTOFF.isoformat(),
        "selected_forecast_ids": [record["forecast_id"] for record in records],
        "selected_forecast_payload_sha256": [
            record["forecast_payload_sha256"] for record in records
        ],
        "selected_forecast_event_ids": [record["event_id"] for record in records],
        "selected_event_ids": sorted(
            {record["event_id"] for record in records if record["event_id"] is not None}
        ),
        "unknown_event_lineage_count": sum(
            record["event_id"] is None for record in records
        ),
        "selected_cohorts": sorted(
            {f"{record['team_id']}:{record['config_version']}" for record in records}
        ),
        "selected_forecasts": records,
        "inventory_artifact": "inventory-test.json",
        "inventory_sha256": hashlib.sha256(b"inventory").hexdigest(),
        "collection_artifact": "collection-test.json",
        "collection_sha256": hashlib.sha256(b"collection").hexdigest(),
        "generated_at": CUTOFF.isoformat(),
        "reassessment_at": HORIZON.isoformat(),
        "outcome_refresh": "not_performed",
        "flags": {"paper_only": True, "report_only": True, "readonly": True},
    }
    document.update(overrides)
    return document


def test_valid_document_passes_and_returns_records() -> None:
    records = validate_p2_checkpoint_document(_document())
    assert set(records) == {"a" * 64}
    assert records["a" * 64]["condition_id"] == "0xabc"


def test_unknown_lineage_records_are_counted() -> None:
    unknown = _record(
        forecast_id="forecast-2",
        forecast_payload_sha256="b" * 64,
        condition_id="0xdef",
        team_id="crypto_eth",
        config_version="p1-crypto_eth-v1",
        event_id=None,
        event_slug=None,
    )
    document = _document([_record(), unknown])
    records = validate_p2_checkpoint_document(document)
    assert len(records) == 2
    assert document["unknown_event_lineage_count"] == 1
    assert document["selected_event_ids"] == ["event-1"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda document: document.update({"schema_version": "p2a-settlement-checkpoint-v1"}),
        lambda document: document.update({"flags": {"paper_only": False, "report_only": True, "readonly": True}}),
        lambda document: document.update({"outcome_refresh": "performed"}),
        lambda document: document.update({"minimum_lead_seconds": 60}),
        lambda document: document.update({"selected_forecast_payload_sha256": ["not-a-hash"]}),
        lambda document: document.update({"selected_forecast_ids": []}),
        lambda document: document.update(
            {
                "selected_forecast_ids": ["forecast-1", "forecast-1"],
                "selected_forecast_payload_sha256": ["a" * 64, "a" * 64],
                "selected_forecast_event_ids": ["event-1", "event-1"],
                "selected_forecasts": [_record(), _record()],
            }
        ),
        lambda document: document.update({"unknown_event_lineage_count": 5}),
        lambda document: document.update({"selected_event_ids": ["event-other"]}),
        lambda document: document.update({"selected_cohorts": ["crypto_btc:p1-crypto_btc-v2"]}),
        lambda document: document.update({"inventory_artifact": "../escape.json"}),
        lambda document: document.update({"collection_sha256": "z" * 64}),
    ],
)
def test_invalid_documents_fail_closed(mutation) -> None:
    document = _document()
    mutation(document)
    with pytest.raises(P2CheckpointError):
        validate_p2_checkpoint_document(document)


@pytest.mark.parametrize(
    "overrides",
    [
        {"team_id": "crypto_eth"},
        {"config_version": "p1-crypto_btc-v2"},
        {"generated_at": (CUTOFF + timedelta(seconds=1)).isoformat()},
        {"market_end_at": (GENERATED_AT + timedelta(seconds=60)).isoformat()},
        {"market_end_at": (HORIZON + timedelta(seconds=1)).isoformat()},
        {"metadata_observed_at": (CUTOFF + timedelta(seconds=1)).isoformat()},
        {"lead_seconds": 1},
        {"event_id": "event-other"},
    ],
)
def test_invalid_selected_forecast_records_fail_closed(overrides) -> None:
    record = _record(**overrides)
    if "event_id" in overrides:
        record["event_slug"] = None
    document = _document([record])
    with pytest.raises(P2CheckpointError):
        validate_p2_checkpoint_document(document)


def test_record_and_array_identity_mismatch_fails_closed() -> None:
    document = _document()
    document["selected_forecasts"][0]["forecast_payload_sha256"] = "b" * 64
    with pytest.raises(P2CheckpointError):
        validate_p2_checkpoint_document(document)


def test_minimal_fabricated_document_is_rejected() -> None:
    with pytest.raises(P2CheckpointError):
        validate_p2_checkpoint_document(
            {
                "as_of_evaluation_cutoff": CUTOFF.isoformat(),
                "selected_forecast_ids": ["forecast-1"],
                "selected_forecast_payload_sha256": ["a" * 64],
            }
        )


def test_load_rejects_unreadable_checkpoint(tmp_path) -> None:
    with pytest.raises(P2CheckpointError):
        load_p2_checkpoint(tmp_path / "missing.json", verify_artifacts=True)


def test_load_verifies_sibling_artifact_hashes(tmp_path) -> None:
    document = _document()
    (tmp_path / "inventory-test.json").write_bytes(b"inventory")
    (tmp_path / "collection-test.json").write_bytes(b"collection")
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")

    loaded, records = load_p2_checkpoint(checkpoint, verify_artifacts=True)
    assert loaded["cohort_id"] == "p2-test-cohort"
    assert set(records) == {"a" * 64}

    (tmp_path / "inventory-test.json").write_bytes(b"tampered")
    with pytest.raises(P2CheckpointError):
        verify_p2_checkpoint_artifacts(document, tmp_path)

    (tmp_path / "inventory-test.json").unlink()
    with pytest.raises(P2CheckpointError):
        load_p2_checkpoint(checkpoint, verify_artifacts=True)
