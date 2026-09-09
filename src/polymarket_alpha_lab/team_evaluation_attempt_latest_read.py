"""Node 8 read-only report for the latest team-evaluation attempt.

Delegates exactly one latest-row read to the reviewed Node 5 interfaces
(``load_latest_team_evaluation_attempt`` and its ``_with_psycopg`` wrapper);
ordering (``attempted_at DESC, tea_id DESC``), filtering, DSN validation,
connection lifecycle, and every DB error stay owned by Node 5, and neither
reader catches or rewrites DB errors or falls back to an older attempt.

The projection is fail-closed. A ``None`` row yields one explicit empty
report (``attempt_present=False``, ``absence_reason="no_matching_attempt"``).
A row is revalidated read-only through its ``evaluation_scope_payload``:
exact eight-key outer payload, canonical Node 2 result schema, row/payload
status and hard-flag agreement, required hard flags, canonical reason codes
and publication gate, and a canonical fixed-six audit probability. Injected
packet-shaped keys are rejected, never trusted. ``audit_packet_selected_side``
is always ``None`` because the row schema never persists packets, and the
audit probability is an audit-only canonical P(YES), never a side
recommendation. Phase 1 hard flags are literal True.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg import (
    load_latest_team_evaluation_attempt_with_psycopg,
)
from polymarket_alpha_lab.team_evidence_aggregation_attempt_store import (
    load_latest_team_evaluation_attempt,
)
from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow,
)

__all__ = (
    "TeamEvaluationAttemptLatestReadReport",
    "read_latest_team_evaluation_attempt_report",
    "read_latest_team_evaluation_attempt_report_with_psycopg",
)

_DEFAULT_TABLE_NAME = "team_evaluation_attempts"
_ABSENCE_REASON = "no_matching_attempt"
_PAYLOAD_KEYS = frozenset((
    "scope_version", "domain_context", "provenance", "run_metadata",
    "evaluator_receipts", "node2_config", "node2_input", "node2_result"))
_RESULT_FRAGMENT_KEYS = frozenset(("schema_version", "result"))
_NODE2_RESULT_SCHEMA = "pal.team_evidence_aggregation.result.v1"
_STATUS_VALUES = frozenset(("ready", "watch", "blocked"))
_CONTRADICTION_STATUS_VALUES = frozenset(("blocked", "none", "watch"))
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_GATE_PAYLOAD_KEY = "external_publication_gate"
_GATE_FIELD_KEYS = frozenset((
    "status", "reason_codes", "paper_only", "report_only", "readonly"))
_PACKET_SHAPED_KEYS = frozenset((
    "legacy_forecast_packet", "selected_side", "forecast_probability"))
_PACKET_PRESENCE_VALUES = frozenset(("projected", "suppressed"))
_ASCII_DIGITS = frozenset("0123456789")
_IDENTIFIER_EDGE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789")
_IDENTIFIER_MIDDLE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._:-")
_ZERO_OFFSET = timedelta(0)


def _canonical_identifier(path: str, value: object) -> str:
    if type(value) is not str or not value or len(value.encode("utf-8")) > 160:
        raise ValueError(f"{path} must be a canonical identifier")
    if (value[0] not in _IDENTIFIER_EDGE_CHARS
            or value[-1] not in _IDENTIFIER_EDGE_CHARS):
        raise ValueError(f"{path} must be a canonical identifier")
    for char in value[1:-1]:
        if char not in _IDENTIFIER_MIDDLE_CHARS:
            raise ValueError(f"{path} must be a canonical identifier")
    return value


def _canonical_reason_codes(path: str, value: object) -> tuple[str, ...]:
    """Recheck a sorted duplicate-free canonical JSON list; return a tuple."""
    if type(value) is not list:
        raise ValueError(f"{path} must be a canonical JSON list")
    codes = tuple(_canonical_identifier(f"{path}[{index}]", item)
                  for index, item in enumerate(value))
    if len(set(codes)) != len(codes) or tuple(sorted(codes)) != codes:
        raise ValueError(f"{path} must be sorted and duplicate-free")
    return codes


def _require_hard_flags(node: dict[str, Any], path: str) -> None:
    for flag in _HARD_FLAG_NAMES:
        if node.get(flag) is not True:
            raise ValueError(f"{path}.{flag} must be literally True")


def _utc_text(value: datetime) -> str:
    return (f"{value.year:04d}-{value.month:02d}-{value.day:02d}T"
            f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}."
            f"{value.microsecond:06d}+00:00")


def _payload_evaluated_at(path: str, result: dict[str, Any]) -> datetime:
    text = result.get("evaluated_at")
    if type(text) is not str:
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{path} must be a canonical UTC string") from None
    if (parsed.tzinfo is None or parsed.utcoffset() != _ZERO_OFFSET
            or _utc_text(parsed) != text):
        raise ValueError(f"{path} must be a canonical UTC string")
    return parsed


def _fixed_six_decimal(path: str, value: object) -> Decimal:
    """Parse only an unsigned canonical fixed-six (d.dddddd) string."""
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical fixed-six Decimal string")
    whole, separator, fraction = value.partition(".")
    if (not separator or not whole or len(fraction) != 6
            or not _ASCII_DIGITS.issuperset(whole)
            or not _ASCII_DIGITS.issuperset(fraction)
            or (len(whole) > 1 and whole[0] == "0")):
        raise ValueError(f"{path} must be a canonical fixed-six Decimal string")
    return Decimal(value)


def _reject_packet_shaped_keys(value: object, path: str) -> None:
    """Reject injected packet keys anywhere in the canonical payload."""
    if type(value) is dict:
        for key, item in value.items():
            if key in _PACKET_SHAPED_KEYS:
                raise ValueError(f"{path}.{key} is a forbidden packet-shaped key")
            _reject_packet_shaped_keys(item, f"{path}.{key}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_packet_shaped_keys(item, f"{path}[{index}]")


def _node2_result_section(payload: dict[str, Any]) -> dict[str, Any]:
    fragment = payload["node2_result"]
    if (type(fragment) is not dict
            or frozenset(fragment) != _RESULT_FRAGMENT_KEYS
            or fragment["schema_version"] != _NODE2_RESULT_SCHEMA):
        raise ValueError(
            "evaluation_scope_payload.node2_result must be the canonical "
            f"Node 2 result payload with schema {_NODE2_RESULT_SCHEMA}")
    result = fragment["result"]
    if type(result) is not dict:
        raise ValueError("node2_result.result must be a JSON object")
    return result


def _publication_gate(
        run_metadata: dict[str, Any]) -> tuple[bool, str | None, tuple[str, ...]]:
    """Read the gate only when present; exact five-field canonical map."""
    if _GATE_PAYLOAD_KEY not in run_metadata:
        return False, None, ()
    gate = run_metadata[_GATE_PAYLOAD_KEY]
    if type(gate) is not dict or frozenset(gate) != _GATE_FIELD_KEYS:
        raise ValueError(
            "run_metadata.external_publication_gate must be an exact "
            "five-field map")
    status = gate["status"]
    if type(status) is not str or status not in _STATUS_VALUES:
        raise ValueError("run_metadata.external_publication_gate.status must "
                         "be ready, watch, or blocked")
    codes = _canonical_reason_codes(
        "run_metadata.external_publication_gate.reason_codes",
        gate["reason_codes"])
    _require_hard_flags(gate, "run_metadata.external_publication_gate")
    return True, status, codes


def _audit_probability(
        result: dict[str, Any], packet_presence: str | None) -> Decimal | None:
    """Audit-only canonical P(YES); suppressed or absent packets stay None."""
    if packet_presence != "projected":
        return None
    value = result.get("publishable_probability_yes")
    if value is None:
        return None
    return _fixed_six_decimal(
        "node2_result.result.publishable_probability_yes", value)


@dataclass(frozen=True, slots=True)
class TeamEvaluationAttemptLatestReadReport:
    """Immutable latest-attempt read report (Phase 1 flags literal True)."""

    attempt_present: bool
    absence_reason: str | None
    tea_id: str | None
    tfr_id: str | None
    attempted_at: datetime | None
    scope_version: str | None
    scope_key: str | None
    status: str | None
    hard_flag: bool | None
    publication_gate_present: bool | None
    publication_gate_status: str | None
    reason_codes: tuple[str, ...]
    publication_gate_reason_codes: tuple[str, ...]
    packet_presence: str | None
    audit_packet_selected_side: str | None
    audit_packet_forecast_probability_yes: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for flag in _HARD_FLAG_NAMES:
            if getattr(self, flag) is not True:
                raise ValueError(f"{flag} must be True")
        if self.absence_reason not in (None, _ABSENCE_REASON):
            raise ValueError(f"absence_reason must be {_ABSENCE_REASON!r} or None")
        if self.status is not None and self.status not in _STATUS_VALUES:
            raise ValueError("status must be ready, watch, blocked, or None")
        if (self.packet_presence is not None
                and self.packet_presence not in _PACKET_PRESENCE_VALUES):
            raise ValueError("packet_presence must be projected, suppressed, or None")
        if self.audit_packet_selected_side is not None:
            raise ValueError("audit_packet_selected_side is always None")


def _empty_report() -> TeamEvaluationAttemptLatestReadReport:
    return TeamEvaluationAttemptLatestReadReport(
        attempt_present=False, absence_reason=_ABSENCE_REASON, tea_id=None,
        tfr_id=None, attempted_at=None, scope_version=None, scope_key=None,
        status=None, hard_flag=None, publication_gate_present=None,
        publication_gate_status=None, reason_codes=(),
        publication_gate_reason_codes=(), packet_presence=None,
        audit_packet_selected_side=None,
        audit_packet_forecast_probability_yes=None)


def _project_row(row: object) -> TeamEvaluationAttemptLatestReadReport:
    """Fail-closed read-only projection of one validated latest row."""
    if type(row) is not TeamEvaluationAttemptDbRow:
        raise ValueError("row must be a TeamEvaluationAttemptDbRow")
    payload = row.evaluation_scope_payload
    if type(payload) is not dict or frozenset(payload) != _PAYLOAD_KEYS:
        raise ValueError("evaluation_scope_payload top-level keys must be "
                         "exactly the eight allowed keys")
    _reject_packet_shaped_keys(payload, "evaluation_scope_payload")
    run_metadata = payload["run_metadata"]
    if type(run_metadata) is not dict:
        raise ValueError("run_metadata must be a JSON object")
    _require_hard_flags(run_metadata, "run_metadata")
    if payload["scope_version"] != row.scope_version:
        raise ValueError("scope_version must match evaluation_scope_payload")
    result = _node2_result_section(payload)
    status = result.get("status")
    if (type(status) is not str or status not in _STATUS_VALUES
            or status != row.status):
        raise ValueError("status must match evaluation_scope_payload")
    contradiction = result.get("contradiction")
    if (type(contradiction) is not dict
            or contradiction.get("status") not in _CONTRADICTION_STATUS_VALUES):
        raise ValueError("node2_result.result.contradiction.status must be "
                         "blocked, none, or watch")
    if type(row.hard_flag) is not bool or row.hard_flag is not (
            contradiction["status"] == "blocked"):
        raise ValueError("hard_flag must match node2_result.contradiction")
    attempted_at = row.attempted_at
    if (type(attempted_at) is not datetime or attempted_at.tzinfo is None
            or attempted_at.utcoffset() != _ZERO_OFFSET
            or attempted_at != _payload_evaluated_at(
                "node2_result.result.evaluated_at", result)):
        raise ValueError("attempted_at must match node2_result.evaluated_at")
    reason_codes = _canonical_reason_codes(
        "node2_result.result.reason_codes", result.get("reason_codes"))
    gate_present, gate_status, gate_codes = _publication_gate(run_metadata)
    # Node 3 contract: projected only when Node 2 is ready and the gate is
    # absent or ready; any watch/blocked Node 2 or gate status suppresses.
    if status == "ready" and (not gate_present or gate_status == "ready"):
        packet_presence = "projected"
    else:
        packet_presence = "suppressed"
    return TeamEvaluationAttemptLatestReadReport(
        attempt_present=True, absence_reason=None, tea_id=row.tea_id,
        tfr_id=row.tfr_id, attempted_at=attempted_at,
        scope_version=row.scope_version, scope_key=row.scope_key, status=status,
        hard_flag=row.hard_flag, publication_gate_present=gate_present,
        publication_gate_status=gate_status, reason_codes=reason_codes,
        publication_gate_reason_codes=gate_codes,
        packet_presence=packet_presence, audit_packet_selected_side=None,
        audit_packet_forecast_probability_yes=_audit_probability(
            result, packet_presence))


def read_latest_team_evaluation_attempt_report(
        connection: Any, *, tfr_id: str | None = None,
        scope_version: str | None = None, scope_key: str | None = None,
        table_name: str = _DEFAULT_TABLE_NAME,
) -> TeamEvaluationAttemptLatestReadReport:
    """Read the latest attempt through the Node 5 DB-API store loader."""
    row = load_latest_team_evaluation_attempt(
        connection, tfr_id=tfr_id, scope_version=scope_version,
        scope_key=scope_key, table_name=table_name)
    return _empty_report() if row is None else _project_row(row)


def read_latest_team_evaluation_attempt_report_with_psycopg(
        dsn: str, *, tfr_id: str | None = None,
        scope_version: str | None = None, scope_key: str | None = None,
        table_name: str = _DEFAULT_TABLE_NAME,
) -> TeamEvaluationAttemptLatestReadReport:
    """Read the latest attempt through the Node 5 psycopg adapter."""
    row = load_latest_team_evaluation_attempt_with_psycopg(
        dsn, tfr_id=tfr_id, scope_version=scope_version, scope_key=scope_key,
        table_name=table_name)
    return _empty_report() if row is None else _project_row(row)
