"""Strict validation and artifact binding for P2 prospective checkpoints.

A P2 checkpoint is only trustworthy if it is a complete frozen document:
the frozen cohort constants, the exact prospective forecast identities with
their lineage, and the exact-byte hashes of the inventory and collection
artifacts produced before any outcome refresh. A minimal JSON object that
merely lists a database hash can never satisfy this contract, so a
checkpoint written after outcomes are known cannot silently replace the
frozen selection.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


P2_CHECKPOINT_SCHEMA_VERSION = "p2-settlement-checkpoint-v1"
HYPOTHESIS_LABEL = "zero_impact_market_control"
INDEPENDENT_HYPOTHESIS_STATUS = "not_implemented"
MINIMUM_LEAD_SECONDS = 1800
EXPECTED_TEAMS = (
    ("crypto_btc", "p1-crypto_btc-v1", "235"),
    ("crypto_eth", "p1-crypto_eth-v1", "39"),
)
EXPECTED_COHORTS = frozenset(
    f"{team_id}:{config_version}" for team_id, config_version, _ in EXPECTED_TEAMS
)
EXPECTED_CONFIG_BY_TEAM = {team_id: config_version for team_id, config_version, _ in EXPECTED_TEAMS}
EXPECTED_GAMMA_QUERY = {"closed": False, "limit": 100, "offset": 0}
EXPECTED_MARKET_SELECTOR = {
    "active": True,
    "binary": True,
    "closed": False,
    "team_keyword_required": True,
}
EXPECTED_SELECTION_RULE = (
    "earliest eligible forecast per (condition_id, team_id, config_version) "
    "generated before the forecast cutoff"
)
HARD_FLAGS = {"paper_only": True, "report_only": True, "readonly": True}
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_ARTIFACT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class P2CheckpointError(ValueError):
    """A P2 checkpoint document or its artifact binding is invalid."""


def _canonical_string(name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise P2CheckpointError(f"{name} must be a canonical nonblank string")
    return value


def _sha256_hex(name: str, value: object) -> str:
    text = _canonical_string(name, value)
    if _HEX64_RE.fullmatch(text) is None:
        raise P2CheckpointError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _timestamp(name: str, value: object) -> datetime:
    text = _canonical_string(name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise P2CheckpointError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise P2CheckpointError(f"{name} must be timezone-aware")
    return parsed


def _require_equal(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise P2CheckpointError(f"{name} mismatch: expected {expected!r}, got {actual!r}")


def _require_str_list(name: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise P2CheckpointError(f"{name} must be a JSON list")
    return [_canonical_string(f"{name}[{index}]", item) for index, item in enumerate(value)]


def validate_p2_checkpoint_document(checkpoint: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate the complete frozen document and return records by payload hash."""

    if not isinstance(checkpoint, Mapping):
        raise P2CheckpointError("checkpoint must be a JSON object")
    _require_equal(
        "checkpoint.schema_version",
        checkpoint.get("schema_version"),
        P2_CHECKPOINT_SCHEMA_VERSION,
    )
    _canonical_string("checkpoint.cohort_id", checkpoint.get("cohort_id"))
    _require_equal("checkpoint.hypothesis_label", checkpoint.get("hypothesis_label"), HYPOTHESIS_LABEL)
    _require_equal(
        "checkpoint.independent_hypothesis_status",
        checkpoint.get("independent_hypothesis_status"),
        INDEPENDENT_HYPOTHESIS_STATUS,
    )
    _require_equal("checkpoint.flags", checkpoint.get("flags"), HARD_FLAGS)
    _require_equal("checkpoint.outcome_refresh", checkpoint.get("outcome_refresh"), "not_performed")

    teams = checkpoint.get("teams")
    if not isinstance(teams, list):
        raise P2CheckpointError("checkpoint.teams must be a JSON list")
    normalized_teams = []
    for index, raw in enumerate(teams):
        if not isinstance(raw, Mapping):
            raise P2CheckpointError(f"checkpoint.teams[{index}] must be a JSON object")
        normalized_teams.append(
            (
                _canonical_string(f"checkpoint.teams[{index}].team_id", raw.get("team_id")),
                _canonical_string(
                    f"checkpoint.teams[{index}].config_version", raw.get("config_version")
                ),
                _canonical_string("checkpoint.teams[].tag_id", str(raw.get("tag_id"))),
            )
        )
    _require_equal("checkpoint.teams", tuple(sorted(normalized_teams)), EXPECTED_TEAMS)
    _require_equal("checkpoint.gamma_query", checkpoint.get("gamma_query"), EXPECTED_GAMMA_QUERY)
    _require_equal("checkpoint.market_selector", checkpoint.get("market_selector"), EXPECTED_MARKET_SELECTOR)
    _require_equal(
        "checkpoint.forecast_selection_rule",
        checkpoint.get("forecast_selection_rule"),
        EXPECTED_SELECTION_RULE,
    )
    _require_equal(
        "checkpoint.minimum_lead_seconds",
        checkpoint.get("minimum_lead_seconds"),
        MINIMUM_LEAD_SECONDS,
    )
    cohort_horizon = _timestamp("checkpoint.cohort_horizon", checkpoint.get("cohort_horizon"))
    cutoff = _timestamp("checkpoint.as_of_evaluation_cutoff", checkpoint.get("as_of_evaluation_cutoff"))
    generated_at = _timestamp("checkpoint.generated_at", checkpoint.get("generated_at"))
    reassessment_at = _timestamp("checkpoint.reassessment_at", checkpoint.get("reassessment_at"))
    if reassessment_at < cutoff:
        raise P2CheckpointError("checkpoint.reassessment_at must not precede as_of_evaluation_cutoff")
    if generated_at < cutoff:
        raise P2CheckpointError("checkpoint.generated_at must not precede as_of_evaluation_cutoff")

    forecast_ids = _require_str_list("checkpoint.selected_forecast_ids", checkpoint.get("selected_forecast_ids"))
    hashes_raw = checkpoint.get("selected_forecast_payload_sha256")
    if not isinstance(hashes_raw, list):
        raise P2CheckpointError("checkpoint.selected_forecast_payload_sha256 must be a JSON list")
    hashes = [
        _sha256_hex(f"checkpoint.selected_forecast_payload_sha256[{index}]", item)
        for index, item in enumerate(hashes_raw)
    ]
    event_ids_raw = checkpoint.get("selected_forecast_event_ids")
    if not isinstance(event_ids_raw, list):
        raise P2CheckpointError("checkpoint.selected_forecast_event_ids must be a JSON list")
    event_ids: list[str | None] = []
    for index, item in enumerate(event_ids_raw):
        if item is None:
            event_ids.append(None)
        else:
            event_ids.append(
                _canonical_string(f"checkpoint.selected_forecast_event_ids[{index}]", item)
            )
    if not forecast_ids or len(forecast_ids) != len(hashes) or len(forecast_ids) != len(event_ids):
        raise P2CheckpointError("checkpoint forecast identity arrays must be nonempty and aligned")
    if len(set(forecast_ids)) != len(forecast_ids) or len(set(hashes)) != len(hashes):
        raise P2CheckpointError("checkpoint forecast identities must be unique")

    records_raw = checkpoint.get("selected_forecasts")
    if not isinstance(records_raw, list) or len(records_raw) != len(forecast_ids):
        raise P2CheckpointError("checkpoint.selected_forecasts must align with the identity arrays")
    records_by_hash: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(records_raw):
        if not isinstance(raw, Mapping):
            raise P2CheckpointError(f"checkpoint.selected_forecasts[{index}] must be a JSON object")
        prefix = f"checkpoint.selected_forecasts[{index}]"
        record = {
            "forecast_id": _canonical_string(f"{prefix}.forecast_id", raw.get("forecast_id")),
            "forecast_payload_sha256": _sha256_hex(
                f"{prefix}.forecast_payload_sha256", raw.get("forecast_payload_sha256")
            ),
            "condition_id": _canonical_string(f"{prefix}.condition_id", raw.get("condition_id")),
            "team_id": _canonical_string(f"{prefix}.team_id", raw.get("team_id")),
            "config_version": _canonical_string(f"{prefix}.config_version", raw.get("config_version")),
            "event_id": raw.get("event_id"),
            "event_slug": _canonical_string(f"{prefix}.event_slug", raw.get("event_slug"))
            if raw.get("event_id") is not None
            else None,
            "generated_at": _timestamp(f"{prefix}.generated_at", raw.get("generated_at")),
            "market_end_at": _timestamp(f"{prefix}.market_end_at", raw.get("market_end_at")),
            "metadata_observed_at": _timestamp(
                f"{prefix}.metadata_observed_at", raw.get("metadata_observed_at")
            ),
            "metadata_payload_sha256": _sha256_hex(
                f"{prefix}.metadata_payload_sha256", raw.get("metadata_payload_sha256")
            ),
        }
        _require_equal(f"{prefix}.forecast_id", record["forecast_id"], forecast_ids[index])
        _require_equal(
            f"{prefix}.forecast_payload_sha256",
            record["forecast_payload_sha256"],
            hashes[index],
        )
        _require_equal(f"{prefix}.event_id", record["event_id"], event_ids[index])
        if record["team_id"] not in EXPECTED_CONFIG_BY_TEAM:
            raise P2CheckpointError(f"{prefix}.team_id is not a frozen P2 team")
        _require_equal(
            f"{prefix}.config_version",
            record["config_version"],
            EXPECTED_CONFIG_BY_TEAM[record["team_id"]],
        )
        if record["generated_at"] > cutoff:
            raise P2CheckpointError(f"{prefix}.generated_at must not follow the cutoff")
        if record["market_end_at"] > cohort_horizon:
            raise P2CheckpointError(f"{prefix}.market_end_at must not follow the cohort horizon")
        lead_seconds = int(
            (record["market_end_at"] - record["generated_at"]).total_seconds()
        )
        if lead_seconds < MINIMUM_LEAD_SECONDS:
            raise P2CheckpointError(f"{prefix} must retain the minimum lead")
        stored_lead = raw.get("lead_seconds")
        if type(stored_lead) is not int or stored_lead != lead_seconds:
            raise P2CheckpointError(f"{prefix}.lead_seconds must equal the recomputed lead")
        if record["metadata_observed_at"] > cutoff:
            raise P2CheckpointError(
                f"{prefix}.metadata_observed_at must not follow the cutoff"
            )
        records_by_hash[record["forecast_payload_sha256"]] = record

    selected_event_ids = _require_str_list(
        "checkpoint.selected_event_ids", checkpoint.get("selected_event_ids")
    )
    _require_equal(
        "checkpoint.selected_event_ids",
        selected_event_ids,
        sorted({event_id for event_id in event_ids if event_id is not None}),
    )
    selected_cohorts = _require_str_list(
        "checkpoint.selected_cohorts", checkpoint.get("selected_cohorts")
    )
    _require_equal(
        "checkpoint.selected_cohorts",
        selected_cohorts,
        sorted(
            {f"{record['team_id']}:{record['config_version']}" for record in records_by_hash.values()}
        ),
    )
    if not set(selected_cohorts).issubset(EXPECTED_COHORTS):
        raise P2CheckpointError("checkpoint.selected_cohorts must be a subset of the frozen cohorts")
    unknown_count = checkpoint.get("unknown_event_lineage_count")
    if type(unknown_count) is not int or unknown_count < 0:
        raise P2CheckpointError("checkpoint.unknown_event_lineage_count must be a nonnegative int")
    _require_equal(
        "checkpoint.unknown_event_lineage_count",
        unknown_count,
        sum(record["event_id"] is None for record in records_by_hash.values()),
    )

    for artifact_field, hash_field in (
        ("inventory_artifact", "inventory_sha256"),
        ("collection_artifact", "collection_sha256"),
    ):
        name = _canonical_string(f"checkpoint.{artifact_field}", checkpoint.get(artifact_field))
        if "/" in name or "\\" in name or _ARTIFACT_NAME_RE.fullmatch(name) is None:
            raise P2CheckpointError(f"checkpoint.{artifact_field} must be a sibling file name")
        _sha256_hex(f"checkpoint.{hash_field}", checkpoint.get(hash_field))
    return records_by_hash


def load_p2_checkpoint(
    checkpoint_path: str | Path,
    *,
    verify_artifacts: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Read, validate, and optionally artifact-bind a P2 checkpoint document."""

    path = Path(checkpoint_path)
    try:
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise P2CheckpointError("checkpoint must be readable UTF-8 JSON") from exc
    if not isinstance(checkpoint, dict):
        raise P2CheckpointError("checkpoint must be a JSON object")
    records = validate_p2_checkpoint_document(checkpoint)
    if verify_artifacts:
        _verify_artifact_hashes(checkpoint, path.parent)
    return checkpoint, records


def verify_p2_checkpoint_artifacts(
    checkpoint: Mapping[str, Any],
    directory: str | Path,
) -> None:
    """Re-hash the sibling inventory/collection artifacts of a P2 checkpoint."""

    _verify_artifact_hashes(checkpoint, Path(directory))


def _verify_artifact_hashes(checkpoint: Mapping[str, Any], directory: Path) -> None:
    for artifact_field, hash_field in (
        ("inventory_artifact", "inventory_sha256"),
        ("collection_artifact", "collection_sha256"),
    ):
        artifact_path = directory / str(checkpoint[artifact_field])
        try:
            payload = artifact_path.read_bytes()
        except OSError as exc:
            raise P2CheckpointError(
                f"checkpoint.{artifact_field} must be readable next to the checkpoint"
            ) from exc
        _require_equal(
            f"checkpoint.{hash_field}",
            hashlib.sha256(payload).hexdigest(),
            checkpoint[hash_field],
        )


__all__ = (
    "HYPOTHESIS_LABEL",
    "INDEPENDENT_HYPOTHESIS_STATUS",
    "MINIMUM_LEAD_SECONDS",
    "P2_CHECKPOINT_SCHEMA_VERSION",
    "P2CheckpointError",
    "EXPECTED_COHORTS",
    "EXPECTED_TEAMS",
    "load_p2_checkpoint",
    "validate_p2_checkpoint_document",
    "verify_p2_checkpoint_artifacts",
)
