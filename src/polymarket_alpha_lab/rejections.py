"""Rejected-candidate audit logs for paper-only risk gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite
from pathlib import Path
from typing import Any, Iterable

from polymarket_alpha_lab.research import ResearchPacket
from polymarket_alpha_lab.risk import RiskGateDecision, RiskGateReason


@dataclass(frozen=True)
class RejectedCandidateRecord:
    rejected_at: datetime
    packet_id: str
    packet_created_at: datetime
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    source_score: str
    market_raw_archive_path: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    gate_config_version: str
    reasons: tuple[RiskGateReason, ...]
    evidence_summary: str
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rejected_at", _as_utc(self.rejected_at))
        object.__setattr__(self, "packet_created_at", _as_utc(self.packet_created_at))
        object.__setattr__(self, "risk_tags", _normalize_string_tuple("risk_tags", self.risk_tags))
        object.__setattr__(self, "reasons", _normalize_reasons(self.reasons))
        _require_nonblank_string("packet_id", self.packet_id)
        _require_nonblank_string("condition_id", self.condition_id)
        _require_nonblank_string("token_id", self.token_id)
        _require_nonblank_string("market_slug", self.market_slug)
        _require_string("market_url", self.market_url)
        _require_nonblank_string("question", self.question)
        _require_string("outcome_name", self.outcome_name)
        _require_string("strategy_type", self.strategy_type)
        _require_nonblank_string("source_score", self.source_score)
        _require_nonblank_string("market_raw_archive_path", self.market_raw_archive_path)
        _require_nonblank_string("rule_text_hash", self.rule_text_hash)
        _require_nonblank_string("resolution_source", self.resolution_source)
        _require_nonblank_string("gate_config_version", self.gate_config_version)
        if not isinstance(self.evidence_summary, str) or not self.evidence_summary.strip():
            raise ValueError("evidence_summary is required")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")

    @classmethod
    def from_packet_and_decision(
        cls,
        *,
        packet: ResearchPacket,
        decision: RiskGateDecision,
        rejected_at: datetime,
        evidence_summary: str,
    ) -> "RejectedCandidateRecord":
        if not isinstance(packet, ResearchPacket):
            raise ValueError("packet must be a ResearchPacket")
        if not isinstance(decision, RiskGateDecision):
            raise ValueError("decision must be a RiskGateDecision")
        if decision.accepted:
            raise ValueError("accepted decisions cannot be logged as rejected candidates")
        if not decision.reasons:
            raise ValueError("rejected decisions must include at least one reason")
        if not isinstance(evidence_summary, str) or not evidence_summary.strip():
            raise ValueError("evidence_summary is required")

        return cls(
            rejected_at=_as_utc(rejected_at),
            packet_id=packet.packet_id,
            packet_created_at=_as_utc(packet.created_at),
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            market_url=packet.market_url,
            question=packet.question,
            outcome_name=packet.outcome_name,
            strategy_type=packet.strategy_type,
            source_score=packet.source_score,
            market_raw_archive_path=packet.raw_archive_path,
            risk_tags=packet.risk_tags,
            rule_text_hash=packet.rule_text_hash,
            resolution_source=packet.resolution_source,
            gate_config_version=decision.config_version,
            reasons=tuple(decision.reasons),
            evidence_summary=evidence_summary,
        )


@dataclass(frozen=True)
class RejectedCandidateLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, record: RejectedCandidateRecord) -> None:
        if not isinstance(record, RejectedCandidateRecord):
            raise ValueError("record must be a RejectedCandidateRecord")
        line = json.dumps(_json_ready(asdict(record)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime values are required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_reasons(value: Iterable[RiskGateReason]) -> tuple[RiskGateReason, ...]:
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError("reasons must be a sequence of RiskGateReason values") from exc
    if not reasons:
        raise ValueError("reasons must include at least one RiskGateReason")
    for reason in reasons:
        if not isinstance(reason, RiskGateReason):
            raise ValueError("reasons must contain RiskGateReason values")
    return reasons


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain nonblank strings")
    return items


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _require_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")


def _require_nonblank_string(field_name: str, value: str) -> None:
    _require_string(field_name, value)
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("rejection log Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("rejection log float values must be finite")
        return value
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("rejection log object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("rejection log values must be JSON serializable")
