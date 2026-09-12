"""Immutable, report-only contracts for bounded evidence research agents.

No provider, network, environment or persistence imports. Model estimates are
uncalibrated research candidates, never publication or execution permission.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.team_taxonomy import require_team_id

FLAGS = ("paper_only", "report_only", "readonly")
TOOL_NAMES = ("search_evidence", "read_evidence", "finish_research")
REASONS = (
    "research_completed", "no_eligible_evidence", "model_failed", "invalid_model_action",
    "model_call_limit", "tool_call_limit", "token_limit", "context_limit",
    "invalid_citations", "model_factory_failed",
)


def text(name: str, value: object, limit: int = 512) -> None:
    if (type(value) is not str or not value or value.strip() != value
            or len(value) > limit or "\x00" in value):
        raise ValueError(f"invalid {name}")


def identifier(name: str, value: object) -> None:
    text(name, value, 128)
    if re.fullmatch(r"[A-Za-z0-9_.:-]+", value) is None:
        raise ValueError(f"invalid {name}")


def aware(name: str, value: object) -> None:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be an aware datetime")


def integer(name: str, value: object, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"invalid {name}")


def hard_flags(value: object) -> None:
    if any(getattr(value, name, None) is not True for name in FLAGS):
        raise ValueError("paper_only, report_only and readonly must be exact True")


def strict_json(value: str) -> object:
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = item
        return result

    def constant(_):
        raise ValueError("nonfinite JSON number")

    return json.loads(value, parse_float=Decimal, parse_constant=constant, object_pairs_hook=pairs)


@dataclass(frozen=True, slots=True)
class ResearchEvidence:
    source_id: str
    team_id: str
    condition_id: str
    title: str
    text: str = field(repr=False)
    reference: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("source_id", self.source_id)
        require_team_id("team_id", self.team_id)
        text("condition_id", self.condition_id)
        text("title", self.title, 256)
        text("evidence text", self.text, 12000)
        text("reference", self.reference, 1024)
        aware("observed_at", self.observed_at)
        hard_flags(self)


@dataclass(frozen=True, slots=True)
class TeamResearchTask:
    task_id: str
    team_id: str
    condition_id: str
    market_slug: str
    question: str
    resolution_criteria: str
    as_of: datetime
    evidence: tuple[ResearchEvidence, ...] = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("task_id", self.task_id)
        require_team_id("team_id", self.team_id)
        for name in ("condition_id", "market_slug"):
            text(name, getattr(self, name))
        text("question", self.question, 2000)
        text("resolution_criteria", self.resolution_criteria, 4000)
        aware("as_of", self.as_of)
        hard_flags(self)
        if type(self.evidence) is not tuple or len(self.evidence) > 100:
            raise ValueError("evidence must be a tuple of at most 100 sources")
        ids = []
        for item in self.evidence:
            if type(item) is not ResearchEvidence:
                raise ValueError("evidence must contain exact ResearchEvidence values")
            item.__post_init__()
            if item.team_id != self.team_id or item.condition_id != self.condition_id:
                raise ValueError("evidence scope does not match task")
            ids.append(item.source_id)
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate evidence source_id")


@dataclass(frozen=True, slots=True)
class ResearchAgentLimits:
    max_model_calls: int = 6
    max_tool_calls: int = 12
    max_total_tokens: int = 12000
    max_output_tokens: int = 1024
    max_context_chars: int = 100000
    max_evidence_age_seconds: int = 86400

    def __post_init__(self) -> None:
        for name, maximum in (("max_model_calls", 32), ("max_tool_calls", 64),
                              ("max_total_tokens", 1000000), ("max_output_tokens", 8192),
                              ("max_context_chars", 500000)):
            integer(name, getattr(self, name), 1, maximum)
        integer("max_evidence_age_seconds", self.max_evidence_age_seconds, 0, 31536000)
        if self.max_output_tokens > self.max_total_tokens:
            raise ValueError("output token limit exceeds total token limit")


@dataclass(frozen=True, slots=True)
class ResearchToolCall:
    call_id: str
    name: str
    arguments_json: str = field(repr=False)

    def __post_init__(self) -> None:
        identifier("call_id", self.call_id)
        identifier("tool name", self.name)
        text("tool arguments", self.arguments_json, 8192)


@dataclass(frozen=True, slots=True)
class ResearchModelReply:
    calls: tuple[ResearchToolCall, ...]
    total_tokens: int
    finish_reason: str = "tool_calls"

    def __post_init__(self) -> None:
        if type(self.calls) is not tuple or not 1 <= len(self.calls) <= 8:
            raise ValueError("reply must contain one to eight tool calls")
        for call in self.calls:
            if type(call) is not ResearchToolCall:
                raise ValueError("invalid tool call type")
            call.__post_init__()
        integer("total_tokens", self.total_tokens, 1, 1000000)
        if type(self.finish_reason) is not str or self.finish_reason != "tool_calls":
            raise ValueError("reply must finish with tool_calls")


@dataclass(frozen=True, slots=True)
class TeamResearchResult:
    task_id: str
    team_id: str
    condition_id: str
    market_slug: str
    as_of: datetime
    status: str
    reason_code: str
    probability_yes: Decimal | None = None
    confidence: Decimal | None = None
    summary: str = field(default="", repr=False)
    source_ids: tuple[str, ...] = ()
    model_calls: int = 0
    tool_calls: int = 0
    total_tokens: int = 0
    tool_trace: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("task_id", self.task_id)
        require_team_id("team_id", self.team_id)
        text("condition_id", self.condition_id)
        text("market_slug", self.market_slug)
        aware("as_of", self.as_of)
        hard_flags(self)
        if type(self.status) is not str or self.status not in ("completed", "blocked", "failed"):
            raise ValueError("invalid research status")
        if type(self.reason_code) is not str or self.reason_code not in REASONS:
            raise ValueError("invalid research reason")
        for name in ("model_calls", "tool_calls", "total_tokens"):
            integer(name, getattr(self, name), 0, 32000000)
        if (type(self.tool_trace) is not tuple or len(self.tool_trace) != self.tool_calls
                or any(type(item) is not str or item not in TOOL_NAMES for item in self.tool_trace)):
            raise ValueError("invalid tool trace")
        if type(self.source_ids) is not tuple:
            raise ValueError("source_ids must be a tuple")
        if self.status == "completed":
            if self.reason_code != "research_completed" or not 1 <= len(self.source_ids) <= 20:
                raise ValueError("completed research requires citations")
            if len(set(self.source_ids)) != len(self.source_ids):
                raise ValueError("duplicate citations")
            for source_id in self.source_ids:
                identifier("source_id", source_id)
            for value in (self.probability_yes, self.confidence):
                if type(value) is not Decimal or not value.is_finite() or not 0 <= value <= 1:
                    raise ValueError("invalid research probability")
            text("summary", self.summary, 2000)
        elif (self.probability_yes is not None or self.confidence is not None
              or self.summary != "" or self.source_ids):
            raise ValueError("unsuccessful research must suppress estimates and text")
        elif self.reason_code == "research_completed":
            raise ValueError("unsuccessful research cannot claim completion")


def snapshot_task(task: TeamResearchTask) -> TeamResearchTask:
    if type(task) is not TeamResearchTask:
        raise ValueError("task must be exactly TeamResearchTask")
    try:
        task.__post_init__()
        return replace(task, evidence=tuple(replace(item) for item in task.evidence))
    except Exception:
        raise ValueError("invalid research task") from None
