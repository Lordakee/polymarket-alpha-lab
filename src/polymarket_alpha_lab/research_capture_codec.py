"""Closed, versioned codec for local Supabase research capture, not file storage.

Reconstruct only the seven known research dataclasses. Never pickle, evaluate,
import payload-selected classes, coerce flags, or silently accept unknown fields.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re

from polymarket_alpha_lab.team_research_agent_types import (
    ResearchEvidence, TeamResearchResult, TeamResearchTask, aware, identifier, strict_json, text,
)
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord
from polymarket_alpha_lab.research_record_values import record_dict
from polymarket_alpha_lab.team_research_intake import ResearchSourceReceipt, TeamResearchIntake
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun

MAX_CAPTURE_BYTES = 2097152
VERSION = "research-capture-v1"


def _wire(value):
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("nonfinite capture number")
        return format(value, "f")
    if type(value) in (tuple, list):
        return [_wire(item) for item in value]
    if type(value) is dict:
        return {key: _wire(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("invalid capture value")


def _dump(value) -> str:
    result = json.dumps(_wire(value), sort_keys=True, separators=(",", ":"),
                        ensure_ascii=True, allow_nan=False)
    if len(result.encode("utf-8")) > MAX_CAPTURE_BYTES:
        raise ValueError("research capture payload too large")
    return result


def payload_sha256(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


def _time(value):
    text("capture timestamp", value, 64)
    if "T" not in value:
        raise ValueError("timestamp required")
    result = datetime.fromisoformat(value)
    aware("capture timestamp", result)
    return result.astimezone(UTC)


def _probability(value):
    if type(value) is not str or re.fullmatch(r"(?:0(?:\.[0-9]{1,6})?|1(?:\.0{1,6})?)", value) is None:
        raise ValueError("invalid canonical capture probability")
    return Decimal(value)


def _tuple(value):
    if type(value) is not list:
        raise ValueError("capture array required")
    return tuple(value)


def _object(cls, value):
    if type(value) is not dict or set(value) != {f.name for f in fields(cls)}:
        raise ValueError("capture object fields do not match schema")
    result = value.copy()
    for key in ("as_of", "fetched_at", "generated_at", "observed_at"):
        if key in result:
            result[key] = _time(result[key])
    for key in ("probability_yes", "confidence"):
        if key in result and result[key] is not None:
            result[key] = _probability(result[key])
    for key in ("source_ids", "tool_trace", "stale_source_ids", "future_source_ids"):
        if key in result:
            result[key] = _tuple(result[key])
    if cls is MarketTeamResearchRun:
        result["intake"] = _object(TeamResearchIntake, result["intake"])
        result["research"] = None if result["research"] is None else _object(TeamResearchResult, result["research"])
    elif cls is TeamResearchIntake:
        result["task"] = None if result["task"] is None else _object(TeamResearchTask, result["task"])
        result["source_receipts"] = tuple(_object(ResearchSourceReceipt, item) for item in _tuple(result["source_receipts"]))
    elif cls is TeamResearchTask:
        result["evidence"] = tuple(_object(ResearchEvidence, item) for item in _tuple(result["evidence"]))
    return cls(**result)


def encode_research_capture(*, record_id: str, model_id: str, protocol_version: str,
                            run: MarketTeamResearchRun) -> str:
    """Validate/copy a run before any DB activity; capture time is NOT an input."""
    try:
        if type(run) is not MarketTeamResearchRun:
            raise ValueError("exact market research run required")
        # Reuse the evaluator's deep-copy/validation boundary; its temporary
        # timestamp is not serialized or stored. The database assigns capture time.
        record = ResearchEvaluationRecord(record_id, model_id, protocol_version, run.intake.as_of, run)
        payload = _dump(dict(schema_version=VERSION, record_id=record.record_id,
                            model_id=record.model_id, protocol_version=record.protocol_version,
                            run=record_dict(record.run)))
        # Round trip now rather than committing a payload we cannot read later.
        decode_research_capture(payload, recorded_at=record.recorded_at,
                                expected_sha256=payload_sha256(payload))
        return payload
    except Exception:
        raise ValueError("invalid research capture input") from None


def decode_research_capture(payload: str, *, recorded_at: datetime,
                            expected_sha256: str) -> ResearchEvaluationRecord:
    """Revalidate persisted bytes, scope, evidence receipts and hard flags."""
    try:
        if type(payload) is not str or not 1 <= len(payload.encode("utf-8")) <= MAX_CAPTURE_BYTES:
            raise ValueError("invalid payload size")
        if type(expected_sha256) is not str or payload_sha256(payload) != expected_sha256:
            raise ValueError("payload digest mismatch")
        value = strict_json(payload)
        if type(value) is not dict or set(value) != {"schema_version", "record_id", "model_id", "protocol_version", "run"}:
            raise ValueError("invalid capture envelope")
        if value["schema_version"] != VERSION:
            raise ValueError("unsupported capture version")
        run = _object(MarketTeamResearchRun, value["run"])
        result = ResearchEvaluationRecord(value["record_id"], value["model_id"],
                                          value["protocol_version"], recorded_at, run)
        canonical = _dump(dict(schema_version=VERSION, record_id=result.record_id,
                              model_id=result.model_id, protocol_version=result.protocol_version,
                              run=record_dict(result.run)))
        if canonical != payload:
            raise ValueError("noncanonical capture payload")
        return result
    except Exception:
        raise ValueError("invalid stored research capture") from None


__all__ = ("encode_research_capture", "decode_research_capture")
