"""Node 4 offline row codec for team evaluation attempts (pure, paper-only).

Casts one complete Node 3 ``evaluation_scope_payload`` onto the immutable
``team_evaluation_attempts`` row: exact eight-key top-level allowlist, promoted
columns per the governing plan (``attempted_at`` from
``node2_result.result.evaluated_at``; ``hard_flag`` True only for a
blocked-level contradiction status), ``scope_key`` as the SHA-256 of the
canonical ``domain_context`` bytes, and ``payload_sha256`` over the canonical
complete payload, all encoded byte-identically to Node 3 canonical JSON
(``allow_nan=False, ensure_ascii=True, sort_keys=True`` compact separators).
No database, environment, filesystem, network, or clock operation; Phase 1
hard flags are literal True.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
import hashlib
import json
import re
from typing import Any

__all__ = (
    "TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS",
    "TEAM_EVALUATION_ATTEMPT_STATUS_VALUES",
    "TeamEvaluationAttemptDbRow",
    "team_evaluation_attempt_row_parameters",
    "team_evaluation_attempt_to_db_row",
)

TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS = (
    "scope_version", "domain_context", "provenance", "run_metadata",
    "evaluator_receipts", "node2_config", "node2_input", "node2_result",
)
TEAM_EVALUATION_ATTEMPT_STATUS_VALUES = ("blocked", "ready", "watch")
_STATUS_VALUES = frozenset(TEAM_EVALUATION_ATTEMPT_STATUS_VALUES)
_CONTRADICTION_STATUS_VALUES = frozenset(("blocked", "none", "watch"))
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_FRAGMENTS = (("node2_config", "config"), ("node2_input", "input"), ("node2_result", "result"))
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_TE_ID_PREFIXES = {"tea_id": "tea:v1:", "tfr_id": "tfr:v1:"}
_ZERO_OFFSET = timedelta(0)
_MISSING = object()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, allow_nan=False, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _normalize_json(path: str, value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float:
        raise ValueError(f"{path} must not contain float values")
    if type(value) is dict:
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} object keys must be strings")
            normalized[key] = _normalize_json(f"{path}.{key}", item)
        for flag in _HARD_FLAG_NAMES:
            if flag in normalized and normalized[flag] is not True:
                raise ValueError(f"{path}.{flag} must be True")
        return normalized
    if type(value) is list:
        return [_normalize_json(f"{path}[{index}]", item) for index, item in enumerate(value)]
    raise ValueError(f"{path} contains a non-JSON value")


def _require_explicit_hard_flags(node: object, path: str) -> None:
    if type(node) is not dict:
        raise ValueError(f"{path} must be a JSON object")
    for flag in _HARD_FLAG_NAMES:
        if node.get(flag, _MISSING) is not True:
            raise ValueError(f"{path}.{flag} must be explicitly True")


def _normalize_payload(value: object) -> dict[str, Any]:
    if type(payload := _normalize_json("evaluation_scope_payload", value)) is not dict:
        raise ValueError("evaluation_scope_payload must be a JSON object")
    if frozenset(payload) != frozenset(TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS):
        raise ValueError("evaluation_scope_payload top-level keys must be exactly the eight "
                         "allowed keys: " + ", ".join(TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS))
    if type(payload["domain_context"]) is not dict:
        raise ValueError("evaluation_scope_payload.domain_context must be a JSON object")
    _require_explicit_hard_flags(payload["run_metadata"], "run_metadata")
    if type(payload["evaluator_receipts"]) is not list:
        raise ValueError("evaluation_scope_payload.evaluator_receipts must be a list")
    for index, entry in enumerate(payload["evaluator_receipts"]):
        _require_explicit_hard_flags(entry, f"evaluator_receipts[{index}]")
    for fragment, section in _FRAGMENTS:
        node = payload[fragment].get(section, _MISSING) if type(payload[fragment]) is dict else None
        _require_explicit_hard_flags(node, f"{fragment}.{section}")
    return payload


def _result_section(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload["node2_result"].get("result", _MISSING)
    if type(result) is not dict:
        raise ValueError("node2_result.result must be a JSON object")
    return result


def _canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex string")
    return value


def _prefixed_digest_id(field_name: str, value: object) -> str:
    prefix = _TE_ID_PREFIXES[field_name]
    if type(value) is not str or not value.startswith(prefix):
        raise ValueError(f"{field_name} must be an exact {prefix} identifier")
    if _SHA256_PATTERN.fullmatch(value[len(prefix):]) is None:
        raise ValueError(f"{field_name} must be an exact {prefix} identifier")
    return value


def _nonnegative_int(field_name: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")
    return value


def _utc_text(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() != _ZERO_OFFSET:
        raise ValueError(f"{field_name} must be an aware UTC datetime")
    return value if value.tzinfo is UTC else value.astimezone(UTC)


def _payload_evaluated_at(result: dict[str, Any]) -> datetime:
    text = result.get("evaluated_at", _MISSING)
    try:
        parsed = _utc_datetime("evaluated_at", datetime.fromisoformat(text))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError("node2_result.result.evaluated_at must be a canonical UTC string") from None
    if type(text) is not str or _utc_text(parsed) != text:
        raise ValueError("node2_result.result.evaluated_at must be a canonical UTC string")
    return parsed


@dataclass(frozen=True)
class TeamEvaluationAttemptDbRow:
    """Immutable ``team_evaluation_attempts`` row; ``created_at`` is DB-assigned."""

    tea_id: str
    tfr_id: str
    attempted_at: datetime
    status: str
    hard_flag: bool
    scope_version: str
    scope_key: str
    config_version: str
    config_digest: str
    diagnostic_record_count: int
    arithmetic_record_count: int
    payload_sha256: str
    evaluation_scope_payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        payload = _normalize_payload(self.evaluation_scope_payload)
        object.__setattr__(self, "evaluation_scope_payload", payload)
        result = _result_section(payload)
        object.__setattr__(self, "tea_id", _prefixed_digest_id("tea_id", self.tea_id))
        object.__setattr__(self, "tfr_id", _prefixed_digest_id("tfr_id", self.tfr_id))
        object.__setattr__(self, "scope_version", _canonical_string("scope_version", self.scope_version))
        object.__setattr__(self, "attempted_at", _utc_datetime("attempted_at", self.attempted_at))
        if self.scope_version != payload["scope_version"]:
            raise ValueError("scope_version must match evaluation_scope_payload")
        if self.attempted_at != _payload_evaluated_at(result):
            raise ValueError("attempted_at must match node2_result.evaluated_at")
        if type(self.status) is not str or self.status not in _STATUS_VALUES:
            raise ValueError(f"status must be one of {TEAM_EVALUATION_ATTEMPT_STATUS_VALUES}")
        if self.status != result.get("status", _MISSING):
            raise ValueError("status must match evaluation_scope_payload")
        if type(self.hard_flag) is not bool:
            raise ValueError("hard_flag must be a bool")
        contra = result.get("contradiction", _MISSING)
        if type(contra) is not dict or contra.get("status", _MISSING) not in _CONTRADICTION_STATUS_VALUES:
            raise ValueError("node2_result.result.contradiction.status must be blocked, none, or watch")
        if self.hard_flag is not (contra["status"] == "blocked"):
            raise ValueError("hard_flag must match node2_result.contradiction")
        object.__setattr__(self, "config_version", _canonical_string("config_version", self.config_version))
        if self.config_version != result.get("config_version", _MISSING):
            raise ValueError("config_version must match evaluation_scope_payload")
        object.__setattr__(self, "config_digest", _hex_digest("config_digest", self.config_digest))
        if self.config_digest != result.get("config_digest", _MISSING):
            raise ValueError("config_digest must match evaluation_scope_payload")
        for field_name in ("diagnostic_record_count", "arithmetic_record_count"):
            object.__setattr__(self, field_name, _nonnegative_int(field_name, getattr(self, field_name)))
            if getattr(self, field_name) != result.get(field_name, _MISSING):
                raise ValueError(f"{field_name} must match evaluation_scope_payload")
        object.__setattr__(self, "scope_key", _hex_digest("scope_key", self.scope_key))
        if self.scope_key != hashlib.sha256(_canonical_bytes(payload["domain_context"])).hexdigest():
            raise ValueError("scope_key must be the sha256 of canonical domain_context")
        object.__setattr__(self, "payload_sha256", _hex_digest("payload_sha256", self.payload_sha256))
        if self.payload_sha256 != hashlib.sha256(_canonical_bytes(payload)).hexdigest():
            raise ValueError("payload_sha256 must match the canonical evaluation_scope_payload")
        for flag in _HARD_FLAG_NAMES:
            if getattr(self, flag) is not True:
                raise ValueError(f"{flag} must be True")


def team_evaluation_attempt_to_db_row(
    *, tea_id: str, tfr_id: str, evaluation_scope_payload: dict[str, object],
) -> TeamEvaluationAttemptDbRow:
    """Project a validated Node 3 payload onto the immutable attempt row."""
    payload = _normalize_payload(evaluation_scope_payload)
    result = _result_section(payload)
    return TeamEvaluationAttemptDbRow(
        tea_id=tea_id, tfr_id=tfr_id,
        attempted_at=_payload_evaluated_at(result), status=result["status"],
        hard_flag=result["contradiction"]["status"] == "blocked",
        scope_version=payload["scope_version"],
        scope_key=hashlib.sha256(_canonical_bytes(payload["domain_context"])).hexdigest(),
        config_version=result["config_version"], config_digest=result["config_digest"],
        diagnostic_record_count=result["diagnostic_record_count"],
        arithmetic_record_count=result["arithmetic_record_count"],
        payload_sha256=hashlib.sha256(_canonical_bytes(payload)).hexdigest(),
        evaluation_scope_payload=payload,
    )


def team_evaluation_attempt_row_parameters(
    row: TeamEvaluationAttemptDbRow,
) -> dict[str, Any]:
    """Return fresh JSON-safe insert parameters; ``created_at`` stays DB-assigned."""
    if type(row) is not TeamEvaluationAttemptDbRow:
        raise ValueError("row must be a TeamEvaluationAttemptDbRow")
    canonical = TeamEvaluationAttemptDbRow(
        **{field.name: getattr(row, field.name) for field in fields(row)}
    )
    return {
        "tea_id": canonical.tea_id, "tfr_id": canonical.tfr_id,
        "attempted_at": _utc_text(canonical.attempted_at), "status": canonical.status,
        "hard_flag": canonical.hard_flag, "scope_version": canonical.scope_version,
        "scope_key": canonical.scope_key, "config_version": canonical.config_version,
        "config_digest": canonical.config_digest,
        "diagnostic_record_count": canonical.diagnostic_record_count,
        "arithmetic_record_count": canonical.arithmetic_record_count,
        "payload_sha256": canonical.payload_sha256,
        "evaluation_scope_payload": _normalize_json(
            "evaluation_scope_payload", canonical.evaluation_scope_payload),
        "paper_only": True, "report_only": True, "readonly": True,
    }
