"""Immutable requests/receipts for explicit local captured research execution.

No I/O, provider selection, credentials or automatic outcome inference. A claim
binds the entire prepared intake and limits, not just the market/task label.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime

from polymarket_alpha_lab.research_capture_codec import (
    MAX_CAPTURE_BYTES, _dump, _object, _time, decode_research_capture,
    encode_research_capture, payload_sha256,
)
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, aware, hard_flags, identifier, integer, strict_json, text,
)
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord
from polymarket_alpha_lab.team_research_intake import TeamResearchIntake
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun

VERSION = "research-execution-v1"


@dataclass(frozen=True, slots=True)
class CapturedResearchRequest:
    record_id: str
    model_id: str
    protocol_version: str
    forecast_cutoff_at: datetime
    intake: TeamResearchIntake = field(repr=False)
    limits: ResearchAgentLimits = ResearchAgentLimits()
    required_source_ids: tuple[str, ...] = ()
    max_start_delay_seconds: int = 300
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("record_id", self.record_id)
        text("model_id", self.model_id, 128)
        identifier("protocol_version", self.protocol_version)
        aware("forecast_cutoff_at", self.forecast_cutoff_at)
        object.__setattr__(self, "forecast_cutoff_at", self.forecast_cutoff_at.astimezone(UTC))
        hard_flags(self)
        integer("max_start_delay_seconds", self.max_start_delay_seconds, 1, 3600)
        if type(self.intake) is not TeamResearchIntake or type(self.limits) is not ResearchAgentLimits:
            raise ValueError("expected exact intake and limits")
        self.intake.__post_init__()
        # Reuse the existing closed codec to copy nested sources and normalize
        # all clocks to UTC, including repeated local hours on DST transitions.
        copied = _object(TeamResearchIntake, strict_json(_dump(asdict(self.intake))))
        object.__setattr__(self, "intake", copied)
        object.__setattr__(self, "limits", replace(self.limits))
        if copied.as_of >= self.forecast_cutoff_at:
            raise ValueError("research data cutoff must precede registered forecast cutoff")
        ids = self.required_source_ids
        available = {row.source_id for row in copied.source_receipts}
        if (type(ids) is not tuple or len(ids) > 20 or any(type(x) is not str for x in ids)
                or len(set(ids)) != len(ids) or not set(ids).issubset(available)):
            raise ValueError("required sources must be unique eligible source IDs")
        object.__setattr__(self, "required_source_ids", tuple(sorted(ids)))

    @property
    def payload(self) -> str:
        return _dump(dict(schema_version=VERSION, **asdict(self)))

    @property
    def content_sha256(self) -> str:
        return payload_sha256(self.payload)


def copy_request(request: CapturedResearchRequest) -> CapturedResearchRequest:
    try:
        if type(request) is not CapturedResearchRequest:
            raise ValueError("exact request required")
        request = replace(request)
        # Apply the same maximum to the stored request and run codec.
        request.payload
        return request
    except Exception:
        raise ValueError("invalid captured research request") from None


def decode_execution_request(payload: str, expected_sha256: str) -> CapturedResearchRequest:
    try:
        if (type(payload) is not str or not 1 <= len(payload.encode("utf-8")) <= MAX_CAPTURE_BYTES
                or type(expected_sha256) is not str or payload_sha256(payload) != expected_sha256):
            raise ValueError("invalid request digest/size")
        data = strict_json(payload)
        if type(data) is not dict or data.pop("schema_version", None) != VERSION:
            raise ValueError("unknown request version")
        data["forecast_cutoff_at"] = _time(data["forecast_cutoff_at"])
        data["intake"] = _object(TeamResearchIntake, data["intake"])
        limits = data["limits"]
        if type(limits) is not dict or set(limits) != set(asdict(ResearchAgentLimits())):
            raise ValueError("invalid limits schema")
        data["limits"] = ResearchAgentLimits(**limits)
        if type(data["required_source_ids"]) is not list:
            raise ValueError("source array required")
        data["required_source_ids"] = tuple(data["required_source_ids"])
        request = CapturedResearchRequest(**data)
        if request.payload != payload:
            raise ValueError("noncanonical execution request")
        return request
    except Exception:
        raise ValueError("invalid stored research execution request") from None


def bind_execution_run(request: CapturedResearchRequest, run: MarketTeamResearchRun) -> MarketTeamResearchRun:
    """Validate an original result for capture-only recovery; never rerun a model."""
    body = encode_research_capture(record_id=request.record_id, model_id=request.model_id,
                                  protocol_version=request.protocol_version, run=run)
    result = decode_research_capture(body, recorded_at=run.intake.as_of,
                                    expected_sha256=payload_sha256(body)).run
    if result.intake != request.intake:
        raise ValueError("research result does not match the claimed intake")
    if (result.research is not None and result.research.status == "completed"
            and not set(request.required_source_ids).issubset(result.research.source_ids)):
        raise ValueError("research result omits required sources")
    return result


@dataclass(frozen=True, slots=True)
class CapturedResearchExecution:
    request: CapturedResearchRequest = field(repr=False)
    claimed_at: datetime
    status: str
    record: ResearchEvaluationRecord | None = field(default=None, repr=False)
    pending_run: MarketTeamResearchRun | None = field(default=None, repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", copy_request(self.request))
        aware("claimed_at", self.claimed_at)
        object.__setattr__(self, "claimed_at", self.claimed_at.astimezone(UTC))
        hard_flags(self)
        request = self.request
        if not request.intake.as_of <= self.claimed_at < request.forecast_cutoff_at:
            raise ValueError("invalid execution claim time")
        if (self.claimed_at - request.intake.as_of).total_seconds() > request.max_start_delay_seconds:
            raise ValueError("claim is too old for its data cutoff")
        if type(self.status) is not str or self.status not in ("captured", "already_captured", "incomplete", "capture_failed"):
            raise ValueError("invalid execution status")
        if self.status in ("captured", "already_captured"):
            if type(self.record) is not ResearchEvaluationRecord or self.pending_run is not None:
                raise ValueError("captured execution requires a committed record only")
            record = replace(self.record)
            bind_execution_run(request, record.run)
            if ((record.record_id, record.model_id, record.protocol_version) !=
                    (request.record_id, request.model_id, request.protocol_version)
                    or record.recorded_at < self.claimed_at):
                raise ValueError("execution record identity or time mismatch")
            object.__setattr__(self, "record", record)
        elif self.record is not None:
            raise ValueError("uncaptured execution cannot claim a stored record")
        elif self.status == "capture_failed":
            object.__setattr__(self, "pending_run", bind_execution_run(request, self.pending_run))
        elif self.pending_run is not None:
            raise ValueError("incomplete execution has no claimed result")

    def to_dict(self) -> dict:
        row = replace(self)
        record = row.record
        return dict(schema_version=VERSION, record_id=row.request.record_id,
                    task_id=row.request.intake.task_id, status=row.status,
                    request_sha256=row.request.content_sha256, claimed_at=row.claimed_at.isoformat(),
                    recorded_at=None if record is None else record.recorded_at.isoformat(),
                    record_sha256=None if record is None else record.content_sha256,
                    research_status=None if record is None or record.run.research is None else record.run.research.status,
                    paper_only=True, report_only=True, readonly=True)


__all__ = ("CapturedResearchRequest", "CapturedResearchExecution")
