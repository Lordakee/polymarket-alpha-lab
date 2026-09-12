"""Content-bound, as-of evaluation of existing market research runs.

Select the FIRST recorded attempt per team/model/protocol/condition BEFORE
examining status or outcome. This avoids best-revision and successful-retry
selection in the supplied history. No outcome fetching, model calls, fitting,
persistence or forecast promotion. Caller capture times are not authenticated.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re

from polymarket_alpha_lab.research_probability_scores import (
    BinaryResearchObservation, ResearchProbabilityDiagnostics, probability,
)
from polymarket_alpha_lab.team_research_agent_types import aware, hard_flags, identifier, snapshot_task, text
from polymarket_alpha_lab.team_research_intake import require_market_slug
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun

MAX_RECORDS = 10000
SCOPES = ("team_id", "model_id", "protocol_version")
REASONS = (
    "scored", "not_yet_recorded", "later_attempt", "intake_blocked",
    "research_blocked", "research_failed", "outcome_pending", "not_pre_outcome",
)


def _json_value(value):
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in (tuple, list):
        return [_json_value(item) for item in value]
    if type(value) is dict:
        return {key: _json_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool, int):
        return value
    raise ValueError("unsupported evaluation serialization type")


def _hash(value) -> str:
    return sha256(json.dumps(_json_value(value), sort_keys=True, ensure_ascii=True,
                             allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def _copy_run(run: MarketTeamResearchRun) -> MarketTeamResearchRun:
    if type(run) is not MarketTeamResearchRun:
        raise ValueError("expected exact MarketTeamResearchRun")
    run.__post_init__()
    intake = replace(run.intake,
        task=None if run.intake.task is None else snapshot_task(run.intake.task),
        source_receipts=tuple(replace(row) for row in run.intake.source_receipts))
    research = None if run.research is None else replace(run.research)
    if research is not None and research.status == "completed":
        probability(research.probability_yes)
        probability(research.confidence)
    return MarketTeamResearchRun(intake, research)


@dataclass(frozen=True, slots=True)
class ResearchEvaluationRecord:
    record_id: str
    model_id: str
    protocol_version: str
    recorded_at: datetime
    run: MarketTeamResearchRun = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("record_id", self.record_id)
        text("model_id", self.model_id, 128)
        identifier("protocol_version", self.protocol_version)
        aware("recorded_at", self.recorded_at)
        hard_flags(self)
        object.__setattr__(self, "run", _copy_run(self.run))
        if self.recorded_at < self.run.intake.as_of:
            raise ValueError("recorded_at must not precede the research data cutoff")

    @property
    def content_sha256(self) -> str:
        return _hash(asdict(self))

    @property
    def group_key(self) -> tuple[str, str, str]:
        return (self.run.intake.team_id, self.model_id, self.protocol_version)


@dataclass(frozen=True, slots=True)
class ResearchEvaluationOutcome:
    condition_id: str
    market_slug: str
    forecast_cutoff_at: datetime
    resolved_at: datetime
    recorded_at: datetime
    actual_yes: bool
    source_reference: str
    source_content_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        text("condition_id", self.condition_id)
        require_market_slug(self.market_slug)
        for name in ("forecast_cutoff_at", "resolved_at", "recorded_at"):
            aware(name, getattr(self, name))
        if not self.forecast_cutoff_at <= self.resolved_at <= self.recorded_at:
            raise ValueError("outcome timestamps must be chronological")
        if type(self.actual_yes) is not bool:
            raise ValueError("actual_yes must be an exact bool; unresolved/void is not NO")
        text("source_reference", self.source_reference, 1024)
        if (type(self.source_content_sha256) is not str
                or re.fullmatch(r"[0-9a-f]{64}", self.source_content_sha256) is None):
            raise ValueError("expected outcome source SHA256")
        hard_flags(self)

    @property
    def content_sha256(self) -> str:
        return _hash(asdict(self))


@dataclass(frozen=True, slots=True)
class ResearchEvaluationDecision:
    record_id: str
    team_id: str
    model_id: str
    protocol_version: str
    condition_id: str
    reason_code: str
    record_sha256: str
    outcome_sha256: str | None
    observation: BinaryResearchObservation | None


@dataclass(frozen=True, slots=True)
class ResearchEvaluationGroup:
    team_id: str
    model_id: str
    protocol_version: str
    attempted_count: int
    selected_count: int
    outcome_pending_count: int
    failed_or_blocked_count: int
    late_count: int
    scores: ResearchProbabilityDiagnostics


def _inputs(records, outcomes):
    if (type(records) is not tuple or type(outcomes) is not tuple
            or len(records) > MAX_RECORDS or len(outcomes) > MAX_RECORDS):
        raise ValueError("evaluation inputs must be bounded exact tuples")
    try:
        if any(type(row) is not ResearchEvaluationRecord for row in records):
            raise ValueError("invalid record")
        if any(type(row) is not ResearchEvaluationOutcome for row in outcomes):
            raise ValueError("invalid outcome")
        records = tuple(sorted((replace(row) for row in records), key=lambda row: row.record_id))
        outcomes = tuple(sorted((replace(row) for row in outcomes), key=lambda row: row.condition_id))
    except Exception:
        raise ValueError("invalid research evaluation input") from None
    if len({row.record_id for row in records}) != len(records):
        raise ValueError("duplicate evaluation record_id")
    if len({row.condition_id for row in outcomes}) != len(outcomes):
        raise ValueError("duplicate or conflicting outcome for condition_id")
    # Multiple captures of the same original task are not independent attempts.
    identities = [(row.group_key, row.run.intake.task_id) for row in records]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate research task within evaluation group")
    times = [(row.group_key, row.run.intake.condition_id, row.recorded_at) for row in records]
    if len(set(times)) != len(times):
        raise ValueError("ambiguous same-time attempts for a condition")
    slugs = {}
    for condition, slug in (
        *((row.run.intake.condition_id, row.run.intake.market_slug) for row in records),
        *((row.condition_id, row.market_slug) for row in outcomes),
    ):
        if condition in slugs and slugs[condition] != slug:
            raise ValueError("condition/market identity conflict")
        slugs[condition] = slug
    return records, outcomes


def _evaluate(records, outcomes, generated_at, bucket_count, min_sample_count, min_bin_count):
    first = {}
    for row in sorted(records, key=lambda item: (item.recorded_at, item.record_id)):
        if row.recorded_at <= generated_at:
            first.setdefault((*row.group_key, row.run.intake.condition_id), row.record_id)
    visible_outcomes = {row.condition_id: row for row in outcomes if row.recorded_at <= generated_at}
    decisions = []
    for row in records:
        intake, research = row.run.intake, row.run.research
        outcome = visible_outcomes.get(intake.condition_id)
        point, outcome_hash = None, None
        if row.recorded_at > generated_at:
            reason = "not_yet_recorded"
        elif first[(*row.group_key, intake.condition_id)] != row.record_id:
            reason = "later_attempt"
        elif intake.status == "blocked":
            reason = "intake_blocked"
        elif research.status != "completed":
            reason = "research_" + research.status
        elif outcome is None:
            reason = "outcome_pending"
        elif row.recorded_at >= outcome.forecast_cutoff_at:
            reason = "not_pre_outcome"
            outcome_hash = outcome.content_sha256
        else:
            reason = "scored"
            point = BinaryResearchObservation(research.probability_yes, outcome.actual_yes)
            outcome_hash = outcome.content_sha256
        decisions.append(ResearchEvaluationDecision(row.record_id, *row.group_key, intake.condition_id,
            reason, row.content_sha256, outcome_hash, point))
    groups = []
    # No pooled score: repeated conditions across teams/models are not new events.
    for key in sorted({row.group_key for row in records if row.recorded_at <= generated_at}):
        rows = [row for row in decisions if (row.team_id, row.model_id, row.protocol_version) == key
                and row.reason_code != "not_yet_recorded"]
        selected = [row for row in rows if row.reason_code != "later_attempt"]
        points = tuple(row.observation for row in selected if row.reason_code == "scored")
        groups.append(ResearchEvaluationGroup(*key, len(rows), len(selected),
            sum(row.reason_code == "outcome_pending" for row in selected),
            sum(row.reason_code in ("intake_blocked", "research_blocked", "research_failed") for row in selected),
            sum(row.reason_code == "not_pre_outcome" for row in selected),
            ResearchProbabilityDiagnostics(points, bucket_count, min_sample_count, min_bin_count)))
    return tuple(decisions), tuple(groups)


@dataclass(frozen=True, slots=True)
class ResearchEvaluationReport:
    records: tuple[ResearchEvaluationRecord, ...] = field(repr=False)
    outcomes: tuple[ResearchEvaluationOutcome, ...] = field(repr=False)
    generated_at: datetime
    bucket_count: int = 10
    min_sample_count: int = 30
    min_bin_count: int = 5
    input_sha256: str = field(init=False)
    decisions: tuple[ResearchEvaluationDecision, ...] = field(init=False)
    groups: tuple[ResearchEvaluationGroup, ...] = field(init=False)
    orphan_outcome_count: int = field(init=False)
    selection_rule: str = field(init=False, default="first_recorded_attempt")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        aware("generated_at", self.generated_at)
        # Validate scoring config even for empty inputs.
        ResearchProbabilityDiagnostics((), self.bucket_count, self.min_sample_count, self.min_bin_count)
        records, outcomes = _inputs(self.records, self.outcomes)
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "outcomes", outcomes)
        decisions, groups = _evaluate(records, outcomes, self.generated_at, self.bucket_count,
                                       self.min_sample_count, self.min_bin_count)
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(self, "groups", groups)
        visible_conditions = {row.run.intake.condition_id for row in records if row.recorded_at <= self.generated_at}
        object.__setattr__(self, "orphan_outcome_count", sum(
            row.condition_id not in visible_conditions for row in outcomes if row.recorded_at <= self.generated_at))
        object.__setattr__(self, "input_sha256", _hash({
            "version": "research-evaluation-v1", "generated_at": self.generated_at,
            "selection": self.selection_rule, "bucket_count": self.bucket_count,
            "min_sample_count": self.min_sample_count, "min_bin_count": self.min_bin_count,
            "records": [row.content_sha256 for row in records],
            "outcomes": [row.content_sha256 for row in outcomes],
        }))

    def to_dict(self) -> dict:
        """Recompute from inputs; export no evidence text, prompts or summaries."""
        report = replace(self)
        groups = []
        for group in report.groups:
            row = asdict(group)
            del row["scores"]["observations"]
            groups.append(row)
        return _json_value({
            "schema_version": "research-evaluation-v1", "generated_at": report.generated_at,
            "input_sha256": report.input_sha256, "selection_rule": report.selection_rule,
            "record_count": len(report.records), "outcome_count": len(report.outcomes),
            "orphan_outcome_count": report.orphan_outcome_count,
            "decisions": [asdict(row) for row in report.decisions], "groups": groups,
            "paper_only": True, "report_only": True, "readonly": True,
        })


__all__ = ("ResearchEvaluationRecord", "ResearchEvaluationOutcome", "ResearchEvaluationReport")
