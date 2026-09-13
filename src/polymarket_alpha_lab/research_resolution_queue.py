"""Read-only resolution worklist, derived from captured market/review history.

A forecast cutoff schedules a status check; it is NOT a resolution timestamp.
This view is not an execution lease, a probability score or a finality oracle.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from polymarket_alpha_lab.research_capture_psycopg import RegisteredResearchMarket
from polymarket_alpha_lab.research_resolution import MAX_REVIEW_AGE_SECONDS, assess_resolution, condition, utc
from polymarket_alpha_lab.research_resolution_store import StoredResolutionReview
from polymarket_alpha_lab.team_research_agent_types import hard_flags, integer

MAX_WORKLIST_MARKETS = 1000
MAX_WORKLIST_BYTES = 16777216
STATES = ("fetch_due", "waiting", "needs_confirmation", "blocked_review", "awaiting_cutoff", "unsupported_market")


@dataclass(frozen=True, slots=True)
class ResolutionWorkItem:
    market: RegisteredResearchMarket
    attempt_count: int = 0
    incomplete_claim_count: int = 0
    latest_review: StoredResolutionReview | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if type(self.market) is not RegisteredResearchMarket:
            raise ValueError("resolution_queue_market_invalid")
        object.__setattr__(self, "market", replace(self.market))
        integer("attempt_count", self.attempt_count, 0, 2**63 - 1)
        integer("incomplete_claim_count", self.incomplete_claim_count, 0, 2**63 - 1)
        if self.latest_review is not None:
            if type(self.latest_review) is not StoredResolutionReview:
                raise ValueError("resolution_queue_review_invalid")
            review = replace(self.latest_review)
            if (review.submission.condition_id != self.market.condition_id
                    or review.submission.snapshot.market_slug != self.market.market_slug
                    or review.recorded_at < self.market.registered_at
                    or review.outcome is not None
                    or assess_resolution(review.submission).status == "ready"):
                raise ValueError("resolution_queue_review_scope_invalid")
            object.__setattr__(self, "latest_review", review)

    def summary(self, at: datetime, recheck_after_seconds: int) -> dict:
        """Return bounded metadata only; never raw source/attestation text."""
        self.__post_init__()
        at = utc("generated_at", at)
        integer("recheck_after_seconds", recheck_after_seconds, 60, 86400)
        market, review = self.market, self.latest_review
        if market.registered_at > at or (review is not None and review.recorded_at > at):
            raise ValueError("resolution_queue_future_record")
        eligible = True
        try:
            condition(market.condition_id)
        except ValueError:
            eligible = False
        assessment = None if review is None else assess_resolution(review.submission)
        due_at = market.forecast_cutoff_at
        if not eligible:
            state = "unsupported_market"
        elif at < due_at:
            state = "awaiting_cutoff"
        elif assessment is None:
            state = "fetch_due"
        elif assessment.status == "blocked":
            state = "blocked_review"
            due_at = None
        elif assessment.status == "needs_confirmation":
            # Approval must bind to the exact snapshot, whose freshness expires
            # from fetched_at, not the later check/receipt time.
            expires = review.submission.snapshot.fetched_at + timedelta(seconds=MAX_REVIEW_AGE_SECONDS)
            state = "needs_confirmation" if at <= expires else "fetch_due"
            due_at = expires
        else:
            due_at = max(due_at, review.submission.checked_at + timedelta(seconds=recheck_after_seconds))
            state = "waiting" if at < due_at else "fetch_due"
        return {
            "condition_id": market.condition_id, "market_slug": market.market_slug,
            "forecast_cutoff_at": market.forecast_cutoff_at.isoformat(), "state": state,
            "next_check_at": None if due_at is None or not eligible else due_at.isoformat(),
            "attempt_count": self.attempt_count, "incomplete_claim_count": self.incomplete_claim_count,
            "latest_review_id": None if review is None else review.submission.review_id,
            "latest_checked_at": None if review is None else review.submission.checked_at.isoformat(),
            "latest_status": None if assessment is None else assessment.status,
            "latest_reason_code": None if assessment is None else assessment.reason_code,
            "candidate_yes": None if assessment is None else assessment.candidate_yes,
        }


@dataclass(frozen=True, slots=True)
class ResolutionWorklist:
    generated_at: datetime
    items: tuple[ResolutionWorkItem, ...] = field(repr=False)
    registered_market_count: int
    recheck_after_seconds: int = 300
    incomplete_execution_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        object.__setattr__(self, "generated_at", utc("generated_at", self.generated_at))
        integer("recheck_after_seconds", self.recheck_after_seconds, 60, 86400)
        integer("registered_market_count", self.registered_market_count, 0, 2**63 - 1)
        integer("incomplete_execution_count", self.incomplete_execution_count, 0, 2**63 - 1)
        if type(self.items) is not tuple or len(self.items) > MAX_WORKLIST_MARKETS:
            raise ValueError("resolution_queue_items_invalid")
        if any(type(item) is not ResolutionWorkItem for item in self.items):
            raise ValueError("resolution_queue_item_invalid")
        items = tuple(replace(item) for item in self.items)
        if (sum(item.incomplete_claim_count for item in items) > self.incomplete_execution_count
                or len(items) > self.registered_market_count
                or len({item.market.condition_id for item in items}) != len(items)):
            raise ValueError("resolution_queue_inventory_invalid")
        for item in items:
            item.summary(self.generated_at, self.recheck_after_seconds)
        object.__setattr__(self, "items", tuple(sorted(items,
            key=lambda item: (item.market.forecast_cutoff_at, item.market.condition_id))))

    def due_items(self) -> tuple[ResolutionWorkItem, ...]:
        self.__post_init__()
        return tuple(item for item in self.items
                     if item.summary(self.generated_at, self.recheck_after_seconds)["state"] == "fetch_due")

    def to_dict(self) -> dict:
        self.__post_init__()
        rows = [item.summary(self.generated_at, self.recheck_after_seconds) for item in self.items]
        return {
            "generated_at": self.generated_at.isoformat(), "registered_market_count": self.registered_market_count,
            "unresolved_market_count": len(rows), "settled_market_count": self.registered_market_count - len(rows),
            "state_counts": {state: sum(row["state"] == state for row in rows) for state in STATES},
            "recheck_after_seconds": self.recheck_after_seconds, "items": rows,
            "incomplete_execution_count": self.incomplete_execution_count,
            "evaluation_blocked_by_incomplete": self.incomplete_execution_count > 0,
            "paper_only": True, "report_only": True, "readonly": True,
            "outcome_confirmation_performed": False, "live_model_called": False,
        }


__all__ = ("ResolutionWorkItem", "ResolutionWorklist")
