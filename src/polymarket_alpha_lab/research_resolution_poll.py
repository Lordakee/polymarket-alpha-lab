"""Explicit one-shot Gamma candidate collection; NEVER confirms an outcome.

No scheduler, worker daemon, model, source attestation or transaction across HTTP.
This reuses existing append-only resolution storage, without another database.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from hashlib import sha256

from polymarket_alpha_lab.research_resolution import ResolutionSubmission, assess_resolution
from polymarket_alpha_lab.research_resolution_queue import MAX_WORKLIST_MARKETS, ResolutionWorkItem, ResolutionWorklist
from polymarket_alpha_lab.research_resolution_queue_store import load_resolution_worklist_with_psycopg
from polymarket_alpha_lab.research_resolution_store import StoredResolutionReview, record_resolution_review_with_psycopg
from polymarket_alpha_lab.team_research_agent_types import integer
from polymarket_alpha_lab.team_research_gamma import GammaResearchReader
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class ResolutionPollAttempt:
    item: ResolutionWorkItem = field(repr=False)
    status: str
    submission: ResolutionSubmission | None = field(default=None, repr=False)
    receipt: StoredResolutionReview | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if type(self.item) is not ResolutionWorkItem or self.status not in ("recorded", "fetch_failed", "capture_failed"):
            raise ValueError("resolution_poll_result_invalid")
        object.__setattr__(self, "item", replace(self.item))
        if self.status == "fetch_failed":
            if self.submission is not None or self.receipt is not None:
                raise ValueError("resolution_poll_result_invalid")
            return
        if type(self.submission) is not ResolutionSubmission:
            raise ValueError("resolution_poll_submission_invalid")
        item = replace(self.submission)
        object.__setattr__(self, "submission", item)
        if (item.confirmation is not None or item.condition_id != self.item.market.condition_id
                or item.snapshot.market_slug != self.item.market.market_slug
                or assess_resolution(item).status == "ready"):
            raise ValueError("resolution_poll_confirmation_forbidden")
        if self.status == "recorded":
            if type(self.receipt) is not StoredResolutionReview:
                raise ValueError("resolution_poll_receipt_invalid")
            receipt = replace(self.receipt)
            object.__setattr__(self, "receipt", receipt)
            if receipt.submission != item or receipt.outcome is not None:
                raise ValueError("resolution_poll_receipt_invalid")
        elif self.receipt is not None:
            raise ValueError("resolution_poll_receipt_invalid")

    def to_dict(self) -> dict:
        self.__post_init__()
        assessment = None if self.submission is None else assess_resolution(self.submission)
        return {
            "condition_id": self.item.market.condition_id, "market_slug": self.item.market.market_slug,
            "status": self.status,
            "reason_code": {"recorded": "unconfirmed_review_recorded", "fetch_failed": "resolution_candidate_fetch_failed",
                            "capture_failed": "resolution_candidate_capture_failed"}[self.status],
            "review_id": None if self.submission is None else self.submission.review_id,
            "assessment": None if assessment is None else {
                "status": assessment.status, "reason_code": assessment.reason_code, "candidate_yes": assessment.candidate_yes},
            "snapshot_sha256": None if self.submission is None else self.submission.snapshot.content_sha256,
            "recorded_at": None if self.receipt is None else self.receipt.recorded_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ResolutionPollReport:
    worklist: ResolutionWorklist = field(repr=False)
    attempts: tuple[ResolutionPollAttempt, ...] = field(repr=False)
    max_requests: int

    def __post_init__(self) -> None:
        integer("max_requests", self.max_requests, 1, 20)
        if type(self.worklist) is not ResolutionWorklist or type(self.attempts) is not tuple:
            raise ValueError("resolution_poll_report_invalid")
        worklist = replace(self.worklist)
        attempts = tuple(replace(attempt) for attempt in self.attempts
                         if type(attempt) is ResolutionPollAttempt)
        expected = worklist.due_items()[:self.max_requests]
        if len(attempts) != len(self.attempts) or tuple(attempt.item for attempt in attempts) != expected:
            raise ValueError("resolution_poll_report_incomplete")
        object.__setattr__(self, "worklist", worklist)
        object.__setattr__(self, "attempts", attempts)

    def to_dict(self) -> dict:
        self.__post_init__()
        return {
            "generated_at": self.worklist.generated_at.isoformat(), "max_requests": self.max_requests,
            "due_at_selection": len(self.worklist.due_items()), "fetch_attempts": len(self.attempts),
            "unprocessed_due_count": len(self.worklist.due_items()) - len(self.attempts),
            "recorded_count": sum(item.status == "recorded" for item in self.attempts),
            "failed_count": sum(item.status != "recorded" for item in self.attempts),
            "results": [item.to_dict() for item in self.attempts],
            "incomplete_execution_count": self.worklist.incomplete_execution_count,
            "confirmed_outcomes_created": 0, "independent_confirmation_performed": False,
            "live_model_called": False, "paper_only": True, "report_only": True, "readonly": True,
        }


def collect_resolution_candidates_with_psycopg(
    dsn: str, *, allow_public_fetch: bool = False, max_requests: int = 10,
    max_markets: int = MAX_WORKLIST_MARKETS, recheck_after_seconds: int = 300,
) -> ResolutionPollReport:
    """Fetch one bounded batch, capture each unconfirmed snapshot, then return.

    Opt-in is checked before DB access. Each attempted HTTP call consumes one
    allowance including failures; no retries or background work. Candidate YES/NO
    is not actual_yes. No independent confirmation parameter is exposed.

    The selection is an as-of snapshot, not a lease. Concurrent processes may
    fetch the same market or record an extra unconfirmed review after another
    operator settles it; neither can create/replace an outcome here. Transport
    failures have no invented snapshot and are returned, not durably fabricated.
    A capture failure retains the immutable submission IN MEMORY for an explicit
    same-submission record_resolution retry; commit success may be uncertain.
    """
    if type(allow_public_fetch) is not bool or not allow_public_fetch:
        raise ValueError("resolution_collection_requires_public_fetch_opt_in")
    integer("max_requests", max_requests, 1, 20)
    worklist = load_resolution_worklist_with_psycopg(dsn,
        max_markets=max_markets, recheck_after_seconds=recheck_after_seconds)
    reader = GammaResearchReader(allow_public_fetch=True)
    attempts = []
    for item in worklist.due_items()[:max_requests]:
        try:
            snapshot = reader.fetch(market_slug=item.market.market_slug)
            if type(snapshot) is not GammaMarketSnapshot or snapshot.market_slug != item.market.market_slug:
                raise ValueError("resolution_snapshot_scope_invalid")
            snapshot = replace(snapshot)
            checked = _now()
            # Bind the identifier to this exact immutable observation/check, not
            # just market ID. Explicit persistence retries retain the same object.
            rid = "poll-" + sha256((item.market.condition_id + "\n" + snapshot.market_slug + "\n"
                + snapshot.fetched_at.isoformat() + "\n" + checked.isoformat() + "\n"
                + snapshot.content_sha256).encode("utf-8")).hexdigest()
            submission = ResolutionSubmission(rid, item.market.condition_id, snapshot, checked)
        except Exception:
            attempts.append(ResolutionPollAttempt(item, "fetch_failed"))
            continue
        try:
            receipt = record_resolution_review_with_psycopg(dsn, submission=submission)
            attempt = ResolutionPollAttempt(item, "recorded", submission, receipt)
        except Exception:
            attempt = ResolutionPollAttempt(item, "capture_failed", submission)
        attempts.append(attempt)
    return ResolutionPollReport(worklist, tuple(attempts), max_requests)


__all__ = ("ResolutionPollAttempt", "ResolutionPollReport", "collect_resolution_candidates_with_psycopg")
