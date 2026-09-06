from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.settlement_evaluation_report import (
    CHECKPOINT_SCHEMA_VERSION,
    REPORT_MANIFEST_SCHEMA_VERSION,
    SettlementReportVerificationError,
)
from polymarket_alpha_lab.settlement_export import (
    ForecastRowView,
    SettledOutcomeView,
    build_settlement_export,
)


FORECAST_CUTOFF = datetime(2026, 9, 7, 1, tzinfo=UTC)
OUTCOME_CUTOFF = datetime(2026, 9, 8, tzinfo=UTC)
GENERATED_AT = datetime(2026, 9, 7, 2, tzinfo=UTC)
REASSESSMENT_AT = datetime(2026, 10, 7, tzinfo=UTC)


def _export(count: int = 2, *, winning: bool = True):
    forecasts = []
    outcomes = []
    for index in range(count):
        condition = f"condition-{index:03d}"
        team = "crypto_btc" if index % 2 == 0 else "crypto_eth"
        config_version = f"p1-{team}-v1"
        forecasts.append(
            ForecastRowView(
                forecast_id=f"forecast-{index:03d}",
                condition_id=condition,
                team_id=team,
                config_version=config_version,
                forecast_p_yes=Decimal("0.9" if winning else "0.1"),
                market_implied_p_yes=Decimal("0.5" if winning else "0.9"),
                generated_at=FORECAST_CUTOFF - timedelta(hours=1),
                payload_sha256=f"{index + 1:064x}",
                event_id="event-shared" if index < 2 else f"event-{index:03d}",
            )
        )
        outcomes.append(
            SettledOutcomeView(
                condition_id=condition,
                outcome="yes",
                observed_at=OUTCOME_CUTOFF - timedelta(hours=1),
            )
        )
    return build_settlement_export(
        forecasts,
        outcomes,
        as_of_evaluation_cutoff=FORECAST_CUTOFF,
        as_of_outcome_cutoff=OUTCOME_CUTOFF,
    )


def _checkpoint(manifest: dict, *, generated_at=GENERATED_AT, reassessment_at=REASSESSMENT_AT):
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "cohort_id": "p2-crypto-control-20260907",
        "hypothesis_label": "zero_impact_market_control",
        "independent_hypothesis_status": "not_implemented",
        "teams": [
            {
                "team_id": "crypto_btc",
                "config_version": "p1-crypto_btc-v1",
                "tag_id": "235",
            },
            {
                "team_id": "crypto_eth",
                "config_version": "p1-crypto_eth-v1",
                "tag_id": "39",
            },
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
        "cohort_horizon": "2026-10-07T00:00:00+00:00",
        "as_of_evaluation_cutoff": FORECAST_CUTOFF.isoformat(),
        "selected_forecast_ids": manifest["selected_forecast_ids"],
        "selected_forecast_payload_sha256": manifest[
            "selected_forecast_payload_sha256"
        ],
        "selected_forecast_event_ids": manifest["selected_forecast_event_ids"],
        "selected_event_ids": manifest["selected_event_ids"],
        "unknown_event_lineage_count": manifest["unknown_event_lineage_count"],
        "selected_cohorts": manifest["selected_cohorts"],
        "generated_at": generated_at.isoformat(),
        "reassessment_at": reassessment_at.isoformat(),
        "flags": {"paper_only": True, "report_only": True, "readonly": True},
    }


def _write_inputs(tmp_path, result, checkpoint):
    samples = tmp_path / "samples.json"
    manifest = tmp_path / "samples.manifest.json"
    checkpoint_path = tmp_path / "checkpoint.json"
    samples.write_text(result.document, encoding="utf-8")
    manifest.write_text(result.manifest, encoding="utf-8")
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    return samples, manifest, checkpoint_path


def _run(tmp_path, result, checkpoint):
    samples, manifest, checkpoint_path = _write_inputs(tmp_path, result, checkpoint)
    prefix = tmp_path / "report"
    exit_code = main(
        [
            "evaluate-settlement-cohort",
            "--samples",
            str(samples),
            "--manifest",
            str(manifest),
            "--checkpoint",
            str(checkpoint_path),
            "--out",
            str(prefix),
        ]
    )
    return exit_code, prefix


def test_command_writes_deterministic_hashed_reports(tmp_path) -> None:
    result = _export()
    checkpoint = _checkpoint(json.loads(result.manifest))
    exit_code, prefix = _run(tmp_path, result, checkpoint)
    assert exit_code == 0

    report_bytes = (tmp_path / "report.json").read_bytes()
    markdown_bytes = (tmp_path / "report.md").read_bytes()
    report = json.loads(report_bytes)
    report_manifest = json.loads((tmp_path / "report.manifest.json").read_bytes())
    assert report["generated_at"] == GENERATED_AT.isoformat()
    assert report["verdict"] == "insufficient_sample"
    assert report["disposition"] == "continue_bounded_collection"
    assert report["evaluation"]["market_log_loss"] is not None
    assert len(report["evaluation"]["hand_check_rows"]) == 2
    assert report_manifest["schema_version"] == REPORT_MANIFEST_SCHEMA_VERSION
    assert report_manifest["report_json_sha256"] == hashlib.sha256(report_bytes).hexdigest()
    assert report_manifest["report_markdown_sha256"] == hashlib.sha256(markdown_bytes).hexdigest()
    assert report_manifest["sample_manifest_sha256"] == hashlib.sha256(
        result.manifest.encode()
    ).hexdigest()
    assert report_manifest["paper_only"] is True

    first = {suffix: (tmp_path / f"report{suffix}").read_bytes() for suffix in (".json", ".md", ".manifest.json")}
    assert _run(tmp_path, result, checkpoint)[0] == 0
    second = {suffix: (tmp_path / f"report{suffix}").read_bytes() for suffix in first}
    assert first == second


@pytest.mark.parametrize(
    ("count", "winning", "reassessment_at", "expected"),
    [
        (2, True, OUTCOME_CUTOFF, "reassess_extension_or_stop"),
        (30, False, REASSESSMENT_AT, "stop_or_new_reviewed_hypothesis"),
        (30, True, REASSESSMENT_AT, "continue_prospective_comparison"),
        (100, True, REASSESSMENT_AT, "proceed_to_applicable_p5_evidence"),
    ],
)
def test_every_fixed_disposition_branch(tmp_path, count, winning, reassessment_at, expected) -> None:
    result = _export(count, winning=winning)
    checkpoint = _checkpoint(json.loads(result.manifest), reassessment_at=reassessment_at)
    _, prefix = _run(tmp_path, result, checkpoint)
    assert json.loads(prefix.with_suffix(".json").read_text())["disposition"] == expected


def test_zero_samples_render_explicit_undefined(tmp_path) -> None:
    result = _export(0)
    manifest = json.loads(result.manifest)
    manifest["config_versions"] = []
    result = type(result)(
        document=result.document,
        manifest=json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        included_count=0,
        pending_count=0,
        exclusion_reasons=(),
    )
    _, prefix = _run(tmp_path, result, _checkpoint(manifest))
    report = json.loads(prefix.with_suffix(".json").read_text())
    assert report["evaluation"]["coverage"] is None
    assert report["evaluation"]["team_brier"] is None
    assert report["evaluation"]["market_log_loss"] is None
    assert report["evaluation"]["hand_check_rows"] == []
    markdown = prefix.with_suffix(".md").read_text()
    assert "Coverage: undefined" in markdown
    assert "Market clipped log loss: undefined" in markdown


@pytest.mark.parametrize(
    ("target", "field", "replacement", "message"),
    [
        ("manifest", "included_count", 999, "manifest.included_count mismatch"),
        ("manifest", "forecast_cutoff", "2026-09-01T00:00:00+00:00", "manifest.forecast_cutoff mismatch"),
        ("manifest", "selected_outcome_ids", [], "selected outcome count mismatch"),
        ("manifest", "config_versions", ["p1-crypto_btc-v1"], "manifest.config_versions mismatch"),
        ("checkpoint", "cohort_id", "", "checkpoint.cohort_id"),
        ("checkpoint", "as_of_evaluation_cutoff", "2026-09-06T00:00:00+00:00", "checkpoint.as_of_evaluation_cutoff mismatch"),
        ("checkpoint", "generated_at", "2026-09-09T00:00:00+00:00", "checkpoint.generated_at must not follow manifest.outcome_cutoff"),
    ],
)
def test_command_fails_closed_on_provenance_mismatch(
    tmp_path, target, field, replacement, message
) -> None:
    result = _export()
    manifest = json.loads(result.manifest)
    checkpoint = _checkpoint(manifest)
    if target == "manifest":
        manifest[field] = replacement
        result = type(result)(
            document=result.document,
            manifest=json.dumps(manifest),
            included_count=result.included_count,
            pending_count=result.pending_count,
            exclusion_reasons=result.exclusion_reasons,
        )
    else:
        checkpoint[field] = replacement
    exit_code, _ = _run(tmp_path, result, checkpoint)
    assert exit_code == 2
    assert not (tmp_path / "report.json").exists()


def test_command_rejects_exact_byte_hash_change(tmp_path) -> None:
    result = _export()
    manifest = json.loads(result.manifest)
    checkpoint = _checkpoint(manifest)
    samples, manifest_path, checkpoint_path = _write_inputs(tmp_path, result, checkpoint)
    samples.write_bytes(samples.read_bytes() + b" ")
    assert main(
        [
            "evaluate-settlement-cohort",
            "--samples",
            str(samples),
            "--manifest",
            str(manifest_path),
            "--checkpoint",
            str(checkpoint_path),
            "--out",
            str(tmp_path / "report"),
        ]
    ) == 2
    assert not (tmp_path / "report.json").exists()


def test_multi_file_publish_restores_previous_bundle_on_failure(
    monkeypatch, tmp_path
) -> None:
    from polymarket_alpha_lab import settlement_evaluation_report as report_module

    result = _export()
    checkpoint = _checkpoint(json.loads(result.manifest))
    prefix = tmp_path / "report"
    previous = {
        suffix: f"previous-{suffix}".encode()
        for suffix in (".json", ".md", ".manifest.json")
    }
    for suffix, payload in previous.items():
        (tmp_path / f"report{suffix}").write_bytes(payload)

    real_replace = report_module.os.replace
    publish_calls = 0

    def fail_second_publish(source, destination):
        nonlocal publish_calls
        if str(source).startswith(str(tmp_path / ".report")):
            publish_calls += 1
            if publish_calls == 2:
                raise OSError("injected publish failure")
        return real_replace(source, destination)

    monkeypatch.setattr(report_module.os, "replace", fail_second_publish)
    samples, manifest_path, checkpoint_path = _write_inputs(
        tmp_path, result, checkpoint
    )
    with pytest.raises(OSError, match="injected publish failure"):
        report_module.run_evaluate_settlement_cohort_command(
            samples_path=str(samples),
            manifest_path=str(manifest_path),
            checkpoint_path=str(checkpoint_path),
            out_prefix=str(prefix),
        )
    for suffix, payload in previous.items():
        assert (tmp_path / f"report{suffix}").read_bytes() == payload
