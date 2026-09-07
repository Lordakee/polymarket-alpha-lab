"""Deterministic, read-only reporting for a frozen settlement cohort."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .settlement_checkpoint import (
    P2_CHECKPOINT_SCHEMA_VERSION,
    P2CheckpointError,
    verify_p2_checkpoint_artifacts,
    validate_p2_checkpoint_document,
)
from .settlement_evaluation import (
    SettlementEvaluationReport,
    SettlementVerdict,
    evaluate_settlement_samples,
    load_samples_document,
)
from .settlement_export import EXPORT_SCHEMA_VERSION


CHECKPOINT_SCHEMA_VERSION = "p2a-settlement-checkpoint-v1"
REPORT_SCHEMA_VERSION = "p2a-settlement-report-v1"
REPORT_MANIFEST_SCHEMA_VERSION = "p2a-settlement-report-manifest-v1"
EVALUATOR_VERSION = "p2a-settlement-evaluator-v1"
HYPOTHESIS_LABEL = "zero_impact_market_control"
INDEPENDENT_HYPOTHESIS_STATUS = "not_implemented"
HARD_FLAGS = {"paper_only": True, "report_only": True, "readonly": True}
EXPECTED_TEAMS = (
    ("crypto_btc", "p1-crypto_btc-v1", "235"),
    ("crypto_eth", "p1-crypto_eth-v1", "39"),
)
EXPECTED_COHORTS = frozenset(
    f"{team_id}:{config_version}"
    for team_id, config_version, _ in EXPECTED_TEAMS
)
EXPECTED_SELECTION_RULE = (
    "earliest eligible forecast per (condition_id, team_id, config_version) "
    "generated before the forecast cutoff"
)
EXPECTED_MARKET_SELECTOR = {
    "active": True,
    "binary": True,
    "closed": False,
    "team_keyword_required": True,
}


class SettlementReportVerificationError(ValueError):
    """Raised when frozen export or checkpoint provenance does not agree."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _object(name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SettlementReportVerificationError(f"{name} must be a JSON object")
    return value


def _list(name: str, value: object) -> list[Any]:
    if not isinstance(value, list):
        raise SettlementReportVerificationError(f"{name} must be a JSON list")
    return value


def _canonical_string(name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise SettlementReportVerificationError(f"{name} must be a canonical nonblank string")
    return value


def _timestamp(name: str, value: object) -> datetime:
    text = _canonical_string(name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SettlementReportVerificationError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SettlementReportVerificationError(f"{name} must be timezone-aware")
    return parsed


def _require_equal(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise SettlementReportVerificationError(
            f"{name} mismatch: expected {expected!r}, got {actual!r}"
        )


def _load_json(name: str, payload: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SettlementReportVerificationError(f"{name} must be valid UTF-8 JSON") from exc
    return _object(name, parsed)


def _validate_flags(name: str, value: object) -> None:
    _require_equal(name, value, HARD_FLAGS)


def _validate_checkpoint(checkpoint: dict[str, Any]) -> None:
    schema_version = checkpoint.get("schema_version")
    if schema_version == P2_CHECKPOINT_SCHEMA_VERSION:
        try:
            validate_p2_checkpoint_document(checkpoint)
        except P2CheckpointError as exc:
            raise SettlementReportVerificationError(str(exc)) from exc
        return
    _require_equal("checkpoint.schema_version", schema_version, CHECKPOINT_SCHEMA_VERSION)
    _canonical_string("checkpoint.cohort_id", checkpoint.get("cohort_id"))
    _require_equal("checkpoint.hypothesis_label", checkpoint.get("hypothesis_label"), HYPOTHESIS_LABEL)
    _require_equal(
        "checkpoint.independent_hypothesis_status",
        checkpoint.get("independent_hypothesis_status"),
        INDEPENDENT_HYPOTHESIS_STATUS,
    )
    _validate_flags("checkpoint.flags", checkpoint.get("flags"))

    teams = _list("checkpoint.teams", checkpoint.get("teams"))
    normalized_teams = []
    for index, raw in enumerate(teams):
        team = _object(f"checkpoint.teams[{index}]", raw)
        normalized_teams.append(
            (
                _canonical_string("team_id", team.get("team_id")),
                _canonical_string("config_version", team.get("config_version")),
                _canonical_string("tag_id", str(team.get("tag_id"))),
            )
        )
    _require_equal("checkpoint.teams", tuple(sorted(normalized_teams)), EXPECTED_TEAMS)

    query = _object("checkpoint.gamma_query", checkpoint.get("gamma_query"))
    _require_equal(
        "checkpoint.gamma_query",
        query,
        {"closed": False, "limit": 100, "offset": 0},
    )
    _require_equal(
        "checkpoint.market_selector",
        checkpoint.get("market_selector"),
        EXPECTED_MARKET_SELECTOR,
    )
    _require_equal(
        "checkpoint.forecast_selection_rule",
        checkpoint.get("forecast_selection_rule"),
        EXPECTED_SELECTION_RULE,
    )
    _require_equal("checkpoint.minimum_lead_seconds", checkpoint.get("minimum_lead_seconds"), 1800)
    _timestamp("checkpoint.cohort_horizon", checkpoint.get("cohort_horizon"))
    forecast_cutoff = _timestamp(
        "checkpoint.as_of_evaluation_cutoff", checkpoint.get("as_of_evaluation_cutoff")
    )
    generated_at = _timestamp("checkpoint.generated_at", checkpoint.get("generated_at"))
    reassessment_at = _timestamp("checkpoint.reassessment_at", checkpoint.get("reassessment_at"))
    if reassessment_at < forecast_cutoff:
        raise SettlementReportVerificationError(
            "checkpoint.reassessment_at must not precede as_of_evaluation_cutoff"
        )
    if generated_at < forecast_cutoff:
        raise SettlementReportVerificationError(
            "checkpoint.generated_at must not precede as_of_evaluation_cutoff"
        )
    for field in (
        "selected_forecast_ids",
        "selected_event_ids",
        "selected_cohorts",
    ):
        values = _list(f"checkpoint.{field}", checkpoint.get(field))
        if any(type(item) is not str or not item for item in values) or len(values) != len(set(values)):
            raise SettlementReportVerificationError(
                f"checkpoint.{field} must contain unique nonblank strings"
            )
    hashes = _list(
        "checkpoint.selected_forecast_payload_sha256",
        checkpoint.get("selected_forecast_payload_sha256"),
    )
    if any(
        type(item) is not str
        or len(item) != 64
        or any(char not in "0123456789abcdef" for char in item)
        for item in hashes
    ):
        raise SettlementReportVerificationError(
            "checkpoint.selected_forecast_payload_sha256 must contain lowercase SHA-256 digests"
        )
    if len(hashes) != len(checkpoint["selected_forecast_ids"]):
        raise SettlementReportVerificationError(
            "checkpoint forecast IDs and payload hashes must have equal lengths"
        )
    event_ids = _list(
        "checkpoint.selected_forecast_event_ids",
        checkpoint.get("selected_forecast_event_ids"),
    )
    if any(
        item is not None
        and (type(item) is not str or not item or item.strip() != item)
        for item in event_ids
    ) or len(event_ids) != len(checkpoint["selected_forecast_ids"]):
        raise SettlementReportVerificationError(
            "checkpoint forecast IDs and event IDs must have equal valid entries"
        )
    unknown_count = checkpoint.get("unknown_event_lineage_count")
    if type(unknown_count) is not int or unknown_count < 0:
        raise SettlementReportVerificationError(
            "checkpoint.unknown_event_lineage_count must be a nonnegative int"
        )


def _verify_inputs(
    samples_bytes: bytes,
    samples: dict[str, Any],
    manifest: dict[str, Any],
    checkpoint: dict[str, Any],
) -> None:
    _validate_checkpoint(checkpoint)
    _require_equal("manifest.schema_version", manifest.get("schema_version"), EXPORT_SCHEMA_VERSION)
    _require_equal("manifest.selection_rule", manifest.get("selection_rule"), EXPECTED_SELECTION_RULE)
    _require_equal("manifest.export_id", manifest.get("export_id"), _sha256(samples_bytes))
    rows = _list("samples.samples", samples.get("samples"))
    _require_equal("manifest.included_count", manifest.get("included_count"), len(rows))
    _require_equal("manifest.pending_count", manifest.get("pending_count"), samples.get("pending_count"))
    _require_equal(
        "manifest.forecast_cutoff",
        manifest.get("forecast_cutoff"),
        samples.get("as_of_evaluation_cutoff"),
    )
    _require_equal(
        "manifest.outcome_cutoff", manifest.get("outcome_cutoff"), samples.get("as_of_outcome_cutoff")
    )
    outcome_cutoff = _timestamp("manifest.outcome_cutoff", manifest.get("outcome_cutoff"))
    forecast_cutoff = _timestamp("manifest.forecast_cutoff", manifest.get("forecast_cutoff"))
    if outcome_cutoff < forecast_cutoff:
        raise SettlementReportVerificationError(
            "manifest.outcome_cutoff must not precede forecast_cutoff"
        )
    checkpoint_generated_at = _timestamp(
        "checkpoint.generated_at", checkpoint.get("generated_at")
    )
    if checkpoint_generated_at > outcome_cutoff:
        raise SettlementReportVerificationError(
            "checkpoint.generated_at must not follow manifest.outcome_cutoff"
        )
    _require_equal(
        "checkpoint.as_of_evaluation_cutoff",
        checkpoint.get("as_of_evaluation_cutoff"),
        manifest.get("forecast_cutoff"),
    )
    manifest_configs = _list("manifest.config_versions", manifest.get("config_versions"))
    manifest_cohorts = _list("manifest.selected_cohorts", manifest.get("selected_cohorts"))
    if not set(manifest_cohorts).issubset(EXPECTED_COHORTS):
        raise SettlementReportVerificationError(
            "manifest.selected_cohorts must be a subset of the frozen cohorts"
        )
    _require_equal(
        "manifest.config_versions",
        manifest_configs,
        sorted(cohort.split(":", 1)[1] for cohort in manifest_cohorts),
    )
    for field in (
        "selected_forecast_ids",
        "selected_forecast_payload_sha256",
        "selected_forecast_event_ids",
        "selected_event_ids",
        "selected_cohorts",
    ):
        manifest_values = _list(f"manifest.{field}", manifest.get(field))
        _require_equal(f"checkpoint.{field}", checkpoint.get(field), manifest_values)
    _require_equal(
        "checkpoint.unknown_event_lineage_count",
        checkpoint.get("unknown_event_lineage_count"),
        manifest.get("unknown_event_lineage_count"),
    )
    selected_outcome_ids = _list("manifest.selected_outcome_ids", manifest.get("selected_outcome_ids"))
    _require_equal("selected outcome count", len(selected_outcome_ids), len(rows))
    sample_forecast_ids: list[str] = []
    sample_outcome_ids: list[str] = []
    sample_cohorts: set[str] = set()
    checkpoint_forecasts = {
        forecast_id: (payload_hash, event_id)
        for forecast_id, payload_hash, event_id in zip(
            checkpoint["selected_forecast_ids"],
            checkpoint["selected_forecast_payload_sha256"],
            checkpoint["selected_forecast_event_ids"],
        )
    }
    outcome_payload_hashes = _list(
        "manifest.selected_outcome_payload_sha256",
        manifest.get("selected_outcome_payload_sha256"),
    )
    _require_equal(
        "selected outcome payload hash count",
        len(outcome_payload_hashes),
        len(rows),
    )
    for index, raw_row in enumerate(rows):
        row = _object(f"samples.samples[{index}]", raw_row)
        forecast_id = _canonical_string(
            f"samples.samples[{index}].forecast_id", row.get("forecast_id")
        )
        outcome_id = _canonical_string(
            f"samples.samples[{index}].outcome_id", row.get("outcome_id")
        )
        sample_forecast_ids.append(forecast_id)
        sample_outcome_ids.append(outcome_id)
        if forecast_id not in checkpoint_forecasts:
            raise SettlementReportVerificationError(
                "sample forecast IDs must be present in checkpoint.selected_forecast_ids"
            )
        expected_forecast_hash, expected_event_id = checkpoint_forecasts[forecast_id]
        _require_equal(
            f"samples.samples[{index}].forecast_payload_sha256",
            row.get("forecast_payload_sha256"),
            expected_forecast_hash,
        )
        _require_equal(
            f"samples.samples[{index}].event_id",
            row.get("event_id"),
            expected_event_id,
        )
        _require_equal(
            f"samples.samples[{index}].outcome_payload_sha256",
            row.get("outcome_payload_sha256"),
            outcome_payload_hashes[index],
        )
        expected_outcome_id = _sha256(
            (
                f"{row.get('condition_id')}|{row.get('settled_at')}|"
                f"{row.get('actual_outcome')}|{row.get('outcome_payload_sha256') or 'unknown'}"
            ).encode("utf-8")
        )
        _require_equal(
            f"samples.samples[{index}].outcome_id",
            outcome_id,
            expected_outcome_id,
        )
        sample_cohorts.add(
            f"{_canonical_string('sample.team_id', row.get('team_id'))}:"
            f"{_canonical_string('sample.config_version', row.get('config_version'))}"
        )
    if len(sample_forecast_ids) != len(set(sample_forecast_ids)):
        raise SettlementReportVerificationError("sample forecast IDs must be unique")
    if not set(sample_forecast_ids).issubset(set(checkpoint["selected_forecast_ids"])):
        raise SettlementReportVerificationError(
            "sample forecast IDs must be present in checkpoint.selected_forecast_ids"
        )
    _require_equal("sample outcome IDs", sample_outcome_ids, selected_outcome_ids)
    if not sample_cohorts.issubset(set(manifest_cohorts)):
        raise SettlementReportVerificationError(
            "sample cohorts must be present in manifest.selected_cohorts"
        )
    selected_event_ids = _list("manifest.selected_event_ids", manifest.get("selected_event_ids"))
    expected_event_ids = sorted(
        {
            row.get("event_id")
            for row in rows
            if isinstance(row, Mapping) and row.get("event_id") is not None
        }
    )
    if not set(expected_event_ids).issubset(set(selected_event_ids)):
        raise SettlementReportVerificationError(
            "sample event IDs must be present in manifest.selected_event_ids"
        )


def _decimal(value: Decimal | None) -> str | None:
    return format(value, "f") if value is not None else None


def _evaluation_payload(report: SettlementEvaluationReport) -> dict[str, Any]:
    return {
        "verdict": report.verdict.value,
        "included_count": report.included_count,
        "excluded_count": report.excluded_count,
        "exclusion_reasons": dict(report.exclusion_reasons),
        "pending_count": report.pending_count,
        "coverage": _decimal(report.coverage),
        "team_brier": _decimal(report.team_brier),
        "market_brier": _decimal(report.market_brier),
        "team_log_loss": _decimal(report.team_log_loss),
        "market_log_loss": _decimal(report.market_log_loss),
        "team_counts": dict(report.team_counts),
        "unique_condition_count": report.unique_condition_count,
        "verified_unique_event_count": report.verified_unique_event_count,
        "unknown_event_row_count": report.unknown_event_row_count,
        "per_event_counts": dict(report.event_counts),
        "max_verified_event_concentration": _decimal(report.max_verified_event_concentration),
        "settlement_lag_seconds": {
            "min": _decimal(report.settlement_lag_min_seconds),
            "median": _decimal(report.settlement_lag_median_seconds),
            "max": _decimal(report.settlement_lag_max_seconds),
        },
        "calibration_buckets": [
            {
                "lower": _decimal(bucket.lower),
                "upper": _decimal(bucket.upper),
                "count": bucket.count,
                "mean_forecast": _decimal(bucket.mean_forecast),
                "actual_yes_count": bucket.actual_yes_count,
            }
            for bucket in report.calibration_buckets
        ],
        "hand_check_rows": [
            {
                "condition_id": row.condition_id,
                "team_id": row.team_id,
                "generated_at": row.generated_at.isoformat(),
                "event_id": row.event_id,
                "forecast_p_yes": _decimal(row.forecast_p_yes),
                "market_implied_p_yes": _decimal(row.market_implied_p_yes),
                "actual_outcome": row.actual_outcome,
                "team_squared_error": _decimal(row.team_squared_error),
                "market_squared_error": _decimal(row.market_squared_error),
                "team_log_loss": _decimal(row.team_log_loss),
                "market_log_loss": _decimal(row.market_log_loss),
            }
            for row in report.hand_check_rows
        ],
        "limitations": list(report.limitations),
    }


def _disposition(
    report: SettlementEvaluationReport,
    checkpoint: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> str:
    if report.verdict is SettlementVerdict.INSUFFICIENT_SAMPLE:
        outcome_cutoff = _timestamp("manifest.outcome_cutoff", manifest["outcome_cutoff"])
        reassessment_at = _timestamp("checkpoint.reassessment_at", checkpoint["reassessment_at"])
        return (
            "continue_bounded_collection"
            if outcome_cutoff < reassessment_at
            else "reassess_extension_or_stop"
        )
    return {
        SettlementVerdict.NO_CONSISTENT_EDGE: "stop_or_new_reviewed_hypothesis",
        SettlementVerdict.INDICATIVE_EDGE: "continue_prospective_comparison",
        SettlementVerdict.COMPARATIVE_EDGE: "proceed_to_applicable_p5_evidence",
    }[report.verdict]


def _markdown(payload: Mapping[str, Any]) -> str:
    evaluation = payload["evaluation"]
    value = lambda item: "undefined" if item is None else str(item)
    lines = [
        "# Settlement Cohort Evaluation",
        "",
        f"- Cohort: `{payload['cohort_id']}`",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Verdict: `{payload['verdict']}`",
        f"- Disposition: `{payload['disposition']}`",
        "",
        "## Engineering Acceptance",
        "",
        "Input bytes, schema, cutoffs, counts, selected identities, configurations, and checkpoint identity verified.",
        "",
        "## Control Behavior",
        "",
        f"- Included samples: {evaluation['included_count']}",
        f"- Pending samples: {evaluation['pending_count']}",
        f"- Coverage: {value(evaluation['coverage'])}",
        f"- Team Brier: {value(evaluation['team_brier'])}",
        f"- Market Brier: {value(evaluation['market_brier'])}",
        f"- Team clipped log loss: {value(evaluation['team_log_loss'])}",
        f"- Market clipped log loss: {value(evaluation['market_log_loss'])}",
        f"- Unique conditions: {evaluation['unique_condition_count']}",
        f"- Verified unique events: {evaluation['verified_unique_event_count']}",
        f"- Unknown event rows: {evaluation['unknown_event_row_count']}",
        f"- Maximum verified event concentration: {value(evaluation['max_verified_event_concentration'])}",
        f"- Settlement lag minimum seconds: {value(evaluation['settlement_lag_seconds']['min'])}",
        f"- Settlement lag median seconds: {value(evaluation['settlement_lag_seconds']['median'])}",
        f"- Settlement lag maximum seconds: {value(evaluation['settlement_lag_seconds']['max'])}",
        "",
        "## Independent Hypothesis Evidence",
        "",
        f"Status: `{payload['independent_hypothesis_status']}`. No independent predictive hypothesis is evaluated.",
        "",
        "## Hand Check Rows",
        "",
    ]
    rows = evaluation["hand_check_rows"]
    if not rows:
        lines.append("None.")
    else:
        lines.append("| condition | team | forecast | market | outcome | team SE | market SE | team LL | market LL |")
        lines.append("| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |")
        for row in rows:
            lines.append(
                f"| {row['condition_id']} | {row['team_id']} | {row['forecast_p_yes']} | "
                f"{row['market_implied_p_yes']} | {row['actual_outcome']} | "
                f"{row['team_squared_error']} | {row['market_squared_error']} | "
                f"{row['team_log_loss']} | {row['market_log_loss']} |"
            )
    lines.extend(("", "Paper-only, report-only, readonly.", ""))
    return "\n".join(lines)


def _write_temporary(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def _atomic_write_many(outputs: Mapping[Path, bytes]) -> None:
    temporary: dict[Path, Path] = {}
    previous = {
        path: path.read_bytes() if path.exists() else None
        for path in outputs
    }
    published: list[Path] = []
    try:
        temporary = {
            path: _write_temporary(path, payload)
            for path, payload in outputs.items()
        }
        for path, temporary_path in temporary.items():
            os.replace(temporary_path, path)
            published.append(path)
    except BaseException:
        for path in reversed(published):
            old_payload = previous[path]
            if old_payload is None:
                path.unlink(missing_ok=True)
            else:
                restoration = _write_temporary(path, old_payload)
                try:
                    os.replace(restoration, path)
                finally:
                    restoration.unlink(missing_ok=True)
        raise
    finally:
        for temporary_path in temporary.values():
            temporary_path.unlink(missing_ok=True)


def run_evaluate_settlement_cohort_command(
    *, samples_path: str, manifest_path: str, checkpoint_path: str, out_prefix: str
) -> int:
    samples_bytes = Path(samples_path).read_bytes()
    manifest_bytes = Path(manifest_path).read_bytes()
    checkpoint_bytes = Path(checkpoint_path).read_bytes()
    samples = _load_json("samples", samples_bytes)
    manifest = _load_json("manifest", manifest_bytes)
    checkpoint = _load_json("checkpoint", checkpoint_bytes)
    _verify_inputs(samples_bytes, samples, manifest, checkpoint)
    if checkpoint.get("schema_version") == P2_CHECKPOINT_SCHEMA_VERSION:
        try:
            verify_p2_checkpoint_artifacts(checkpoint, Path(checkpoint_path).parent)
        except P2CheckpointError as exc:
            raise SettlementReportVerificationError(str(exc)) from exc

    rows, config = load_samples_document(samples_bytes.decode("utf-8"))
    report = evaluate_settlement_samples(rows, config)
    disposition = _disposition(report, checkpoint, manifest)
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "cohort_id": checkpoint["cohort_id"],
        "sample_export_id": manifest["export_id"],
        "evaluator_version": EVALUATOR_VERSION,
        "generated_at": checkpoint["generated_at"],
        "hypothesis_label": HYPOTHESIS_LABEL,
        "independent_hypothesis_status": INDEPENDENT_HYPOTHESIS_STATUS,
        "verdict": report.verdict.value,
        "disposition": disposition,
        "engineering_acceptance": "verified",
        "control_behavior": "evaluated" if report.included_count else "undefined_no_settled_samples",
        "independent_hypothesis_evidence": "none_not_implemented",
        "evaluation": _evaluation_payload(report),
        **HARD_FLAGS,
    }
    report_json = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    report_markdown = _markdown(payload).encode("utf-8")
    report_manifest = (
        json.dumps(
            {
                "schema_version": REPORT_MANIFEST_SCHEMA_VERSION,
                "cohort_id": checkpoint["cohort_id"],
                "sample_export_id": manifest["export_id"],
                "evaluator_version": EVALUATOR_VERSION,
                "verdict": report.verdict.value,
                "disposition": disposition,
                "hypothesis_label": HYPOTHESIS_LABEL,
                "independent_hypothesis_status": INDEPENDENT_HYPOTHESIS_STATUS,
                "generated_at": checkpoint["generated_at"],
                "sample_manifest_sha256": _sha256(manifest_bytes),
                "checkpoint_sha256": _sha256(checkpoint_bytes),
                "report_json_sha256": _sha256(report_json),
                "report_markdown_sha256": _sha256(report_markdown),
                **HARD_FLAGS,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    prefix = Path(out_prefix)
    _atomic_write_many(
        {
            Path(f"{prefix}.json"): report_json,
            Path(f"{prefix}.md"): report_markdown,
            Path(f"{prefix}.manifest.json"): report_manifest,
        }
    )
    return 0


__all__ = (
    "CHECKPOINT_SCHEMA_VERSION",
    "EVALUATOR_VERSION",
    "REPORT_MANIFEST_SCHEMA_VERSION",
    "REPORT_SCHEMA_VERSION",
    "SettlementReportVerificationError",
    "run_evaluate_settlement_cohort_command",
)
