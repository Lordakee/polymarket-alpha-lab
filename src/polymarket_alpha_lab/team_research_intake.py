"""Pure Gamma context/evidence intake for report-only team research.

Market descriptions define the question, never independent research evidence.
Raw public JSON stays in the caller's in-memory snapshot; nothing is persisted.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import re

from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, ResearchEvidence, TeamResearchTask, aware, hard_flags,
    identifier, integer, snapshot_task, strict_json, text,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id

GAMMA_MARKET_PREFIX = "https://gamma-api.polymarket.com/markets/slug/"
MAX_GAMMA_RESPONSE_BYTES = 1048576
INTAKE_REASONS = (
    "research_intake_prepared", "invalid_market_payload", "market_identity_mismatch",
    "market_not_open", "unsupported_market_outcomes", "missing_resolution_criteria",
    "invalid_market_time", "market_context_stale", "market_context_from_future",
    "market_already_ended", "no_eligible_evidence",
)


def require_market_slug(value: object) -> str:
    if (type(value) is not str or len(value) > 200
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is None):
        raise ValueError("invalid canonical market slug")
    return value


def _digest(value: object) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("invalid SHA256 digest")


@dataclass(frozen=True, slots=True)
class GammaMarketSnapshot:
    market_slug: str
    fetched_at: datetime
    raw_json: bytes = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_market_slug(self.market_slug)
        aware("fetched_at", self.fetched_at)
        if type(self.raw_json) is not bytes or not 1 <= len(self.raw_json) <= MAX_GAMMA_RESPONSE_BYTES:
            raise ValueError("invalid Gamma snapshot size or type")
        hard_flags(self)

    @property
    def source_reference(self) -> str:
        return GAMMA_MARKET_PREFIX + self.market_slug

    @property
    def content_sha256(self) -> str:
        return sha256(self.raw_json).hexdigest()


def evidence_content_sha256(evidence: ResearchEvidence) -> str:
    """Bind the full canonical evidence record, not just its source label."""
    if type(evidence) is not ResearchEvidence:
        raise ValueError("expected exact ResearchEvidence")
    evidence = replace(evidence)
    payload = asdict(evidence)
    payload["observed_at"] = evidence.observed_at.astimezone(UTC).isoformat()
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ResearchSourceReceipt:
    source_id: str
    content_sha256: str
    reference: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("source_id", self.source_id)
        _digest(self.content_sha256)
        text("reference", self.reference, 1024)
        aware("observed_at", self.observed_at)
        hard_flags(self)


def _receipt(evidence: ResearchEvidence) -> ResearchSourceReceipt:
    return ResearchSourceReceipt(evidence.source_id, evidence_content_sha256(evidence),
                                 evidence.reference, evidence.observed_at)


@dataclass(frozen=True, slots=True)
class TeamResearchIntake:
    task_id: str
    team_id: str
    condition_id: str
    market_slug: str
    as_of: datetime
    fetched_at: datetime
    market_content_sha256: str
    status: str
    reason_code: str
    task: TeamResearchTask | None = field(default=None, repr=False)
    source_receipts: tuple[ResearchSourceReceipt, ...] = ()
    stale_source_ids: tuple[str, ...] = ()
    future_source_ids: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("task_id", self.task_id)
        require_team_id("team_id", self.team_id)
        text("condition_id", self.condition_id)
        require_market_slug(self.market_slug)
        aware("as_of", self.as_of)
        aware("fetched_at", self.fetched_at)
        _digest(self.market_content_sha256)
        hard_flags(self)
        if type(self.status) is not str or self.status not in ("prepared", "blocked"):
            raise ValueError("invalid intake status")
        if type(self.reason_code) is not str or self.reason_code not in INTAKE_REASONS:
            raise ValueError("invalid intake reason")
        for ids in (self.stale_source_ids, self.future_source_ids):
            if type(ids) is not tuple or len(ids) > 100:
                raise ValueError("invalid excluded source IDs")
            for source_id in ids:
                identifier("source_id", source_id)
            if len(set(ids)) != len(ids):
                raise ValueError("duplicate excluded source ID")
        if set(self.stale_source_ids).intersection(self.future_source_ids):
            raise ValueError("excluded source sets must not overlap")
        if type(self.source_receipts) is not tuple:
            raise ValueError("source receipts must be an exact tuple")
        if self.status == "blocked":
            if self.task is not None or self.source_receipts or self.reason_code == "research_intake_prepared":
                raise ValueError("blocked intake must suppress task and source receipts")
            return
        if self.reason_code != "research_intake_prepared":
            raise ValueError("prepared intake must use prepared reason")
        task = snapshot_task(self.task)
        if not task.evidence:
            raise ValueError("market context alone is not research evidence")
        for name in ("task_id", "team_id", "condition_id", "market_slug", "as_of"):
            if getattr(task, name) != getattr(self, name):
                raise ValueError("intake task scope mismatch")
        for receipt in self.source_receipts:
            if type(receipt) is not ResearchSourceReceipt:
                raise ValueError("expected exact source receipt")
            receipt.__post_init__()
        if self.source_receipts != tuple(_receipt(item) for item in task.evidence):
            raise ValueError("source receipts must bind the prepared evidence")
        included = {item.source_id for item in task.evidence}
        if included.intersection((*self.stale_source_ids, *self.future_source_ids)):
            raise ValueError("included source cannot be excluded")


class _ContextRejected(ValueError):
    pass


def _timestamp(value: object) -> datetime:
    try:
        text("market timestamp", value, 64)
        # Require a timestamp rather than accepting date-only ISO forms.
        if "T" not in value:
            raise ValueError("timestamp required")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        aware("market timestamp", parsed)
        return parsed.astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        raise _ContextRejected("invalid_market_time") from None


def _market_context(snapshot: GammaMarketSnapshot, condition_id: str,
                    as_of: datetime, max_age: int) -> tuple[str, str]:
    if snapshot.fetched_at > as_of:
        raise _ContextRejected("market_context_from_future")
    if as_of - snapshot.fetched_at > timedelta(seconds=max_age):
        raise _ContextRejected("market_context_stale")
    try:
        payload = strict_json(snapshot.raw_json.decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError):
        raise _ContextRejected("invalid_market_payload") from None
    if type(payload) is not dict:
        raise _ContextRejected("invalid_market_payload")
    if payload.get("slug") != snapshot.market_slug or payload.get("conditionId") != condition_id:
        raise _ContextRejected("market_identity_mismatch")
    if (payload.get("active") is not True or payload.get("closed") is not False
            or ("archived" in payload and payload["archived"] is not False)):
        raise _ContextRejected("market_not_open")
    try:
        outcomes = payload.get("outcomes")
        if type(outcomes) is str:
            outcomes = strict_json(outcomes)
        if (type(outcomes) is not list or len(outcomes) != 2
                or any(type(item) is not str for item in outcomes)
                or {item.casefold() for item in outcomes} != {"yes", "no"}):
            raise ValueError("not canonical binary outcomes")
    except (ValueError, RecursionError):
        raise _ContextRejected("unsupported_market_outcomes") from None
    try:
        question = payload.get("question")
        text("question", question, 2000)
    except ValueError:
        raise _ContextRejected("invalid_market_payload") from None
    try:
        description = payload.get("description")
        text("resolution criteria", description, 4000)
    except ValueError:
        raise _ContextRejected("missing_resolution_criteria") from None
    end_at = _timestamp(payload.get("endDate"))
    if end_at <= as_of:
        raise _ContextRejected("market_already_ended")
    updated_at = payload.get("updatedAt")
    if updated_at is not None and _timestamp(updated_at) > snapshot.fetched_at:
        raise _ContextRejected("invalid_market_time")
    # Do not use prices, nested event fields, or a URL from resolutionSource as evidence.
    return question, description


def prepare_team_research_from_gamma(
    snapshot: GammaMarketSnapshot, *, task_id: str, team_id: str, condition_id: str,
    as_of: datetime, evidence: tuple[ResearchEvidence, ...],
    limits: ResearchAgentLimits = ResearchAgentLimits(), max_context_age_seconds: int = 300,
) -> TeamResearchIntake:
    """Build a scoped task or a fixed-code blocked report; perform no I/O.

    Caller contract violations raise before model construction. Source-content
    or market-eligibility failures return blocked. Descriptions are not promoted
    into evidence. Historical replay requires a genuine as-of snapshot: a newly
    fetched response cannot be backdated via as_of.
    """
    if type(snapshot) is not GammaMarketSnapshot or type(limits) is not ResearchAgentLimits:
        raise ValueError("expected exact snapshot and limits")
    snapshot, limits = replace(snapshot), replace(limits)
    integer("max_context_age_seconds", max_context_age_seconds, 0, 86400)
    # Existing task validation enforces exact evidence types, unique IDs and scope.
    request = snapshot_task(TeamResearchTask(
        task_id, team_id, condition_id, snapshot.market_slug, "Intake preflight",
        "Intake preflight", as_of, evidence,
    ))
    stale, future, eligible = [], [], []
    for item in request.evidence:
        age = as_of - item.observed_at
        if age < timedelta(0):
            future.append(item.source_id)
        elif age > timedelta(seconds=limits.max_evidence_age_seconds):
            stale.append(item.source_id)
        else:
            eligible.append(item)
    task = None
    reason = "research_intake_prepared"
    try:
        question, criteria = _market_context(snapshot, condition_id, as_of, max_context_age_seconds)
        if not eligible:
            raise _ContextRejected("no_eligible_evidence")
        task = replace(request, question=question, resolution_criteria=criteria, evidence=tuple(eligible))
    except _ContextRejected as error:
        reason = str(error)
    return TeamResearchIntake(
        task_id, team_id, condition_id, snapshot.market_slug, as_of, snapshot.fetched_at,
        snapshot.content_sha256, "prepared" if task is not None else "blocked", reason,
        task, tuple(_receipt(item) for item in task.evidence) if task is not None else (),
        tuple(stale), tuple(future),
    )


__all__ = (
    "GammaMarketSnapshot", "ResearchSourceReceipt", "TeamResearchIntake",
    "evidence_content_sha256", "prepare_team_research_from_gamma",
)
