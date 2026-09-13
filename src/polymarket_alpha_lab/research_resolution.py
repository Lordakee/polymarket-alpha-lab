"""Official-market resolution hints plus an explicit independent attestation.

A price, closed flag or Gamma timestamp alone is NEVER a confirmed outcome.
This pure gate does not fetch, authenticate a source, run a model, or persist.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import re
from urllib.parse import urlsplit

from polymarket_alpha_lab.team_research_agent_types import (
    aware, hard_flags, identifier, strict_json, text,
)
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, require_market_slug

MAX_REVIEW_AGE_SECONDS = 600


def condition(value: object) -> None:
    if type(value) is not str or re.fullmatch(r"0x[0-9a-f]{64}", value) is None:
        raise ValueError("resolution_condition_id_invalid")


def digest(value: object) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("resolution_digest_invalid")


def utc(name: str, value: object) -> datetime:
    aware(name, value)
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class IndependentResolutionConfirmation:
    """Operator assertion of independent review, NOT an authenticated proof.

    source_text is public, approved evidence retained for audit. This module does
    not fetch its reference or prove that its text supports the asserted outcome.
    gamma_content_sha256 prevents reusing approval for a different snapshot.
    """
    condition_id: str
    market_slug: str
    actual_yes: bool
    resolved_at: datetime
    confirmed_at: datetime
    gamma_content_sha256: str
    reviewer_id: str
    source_reference: str
    source_text: str = field(repr=False)
    independently_verified: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        condition(self.condition_id)
        require_market_slug(self.market_slug)
        if type(self.actual_yes) is not bool or self.independently_verified is not True:
            raise ValueError("resolution_independent_confirmation_required")
        hard_flags(self)
        digest(self.gamma_content_sha256)
        identifier("reviewer_id", self.reviewer_id)
        text("source_reference", self.source_reference, 1024)
        text("source_text", self.source_text, 32000)
        # References are labels only, never destinations for an automatic fetch.
        url = urlsplit(self.source_reference)
        host = (url.hostname or "").lower()
        if (url.scheme != "https" or not host or url.username is not None
                or url.password is not None or url.fragment or url.port not in (None, 443)
                or host.rstrip(".") == "polymarket.com"
                or host.rstrip(".").endswith(".polymarket.com")
                or any(char.isspace() or ord(char) < 32 for char in self.source_reference)):
            raise ValueError("resolution_independent_reference_required")
        for name in ("resolved_at", "confirmed_at"):
            object.__setattr__(self, name, utc(name, getattr(self, name)))
        if self.resolved_at > self.confirmed_at:
            raise ValueError("resolution_confirmation_time_invalid")

    @property
    def source_content_sha256(self) -> str:
        return sha256(self.source_text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ResolutionSubmission:
    review_id: str
    condition_id: str
    snapshot: GammaMarketSnapshot = field(repr=False)
    checked_at: datetime
    confirmation: IndependentResolutionConfirmation | None = field(default=None, repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier("review_id", self.review_id)
        condition(self.condition_id)
        hard_flags(self)
        object.__setattr__(self, "checked_at", utc("checked_at", self.checked_at))
        if type(self.snapshot) is not GammaMarketSnapshot:
            raise ValueError("resolution_snapshot_invalid")
        object.__setattr__(self, "snapshot", replace(self.snapshot,
            fetched_at=utc("fetched_at", self.snapshot.fetched_at)))
        if self.confirmation is not None:
            if type(self.confirmation) is not IndependentResolutionConfirmation:
                raise ValueError("resolution_confirmation_invalid")
            object.__setattr__(self, "confirmation", replace(self.confirmation))


@dataclass(frozen=True, slots=True)
class ResolutionAssessment:
    status: str
    reason_code: str
    candidate_yes: bool | None = None


class _Rejected(ValueError):
    pass


def _array(value: object) -> list:
    if type(value) is str:
        value = strict_json(value)
    if type(value) is not list or len(value) != 2:
        raise _Rejected("unsupported_outcomes")
    return value


def _price(value: object) -> Decimal:
    if type(value) not in (str, int, Decimal):
        raise _Rejected("invalid_payload")
    token = str(value)
    if re.fullmatch(r"(?:0(?:\.[0-9]{1,18})?|1(?:\.0{1,18})?)", token) is None:
        raise _Rejected("invalid_payload")
    return Decimal(token)


def assess_resolution(submission: ResolutionSubmission) -> ResolutionAssessment:
    """Return candidate/blocked/pending/ready, keeping unknown distinct from NO.

    'ready' means operator-confirmed with agreeing Gamma finality hints, not
    oracle verification, truth authentication or financial execution approval.
    """
    if type(submission) is not ResolutionSubmission:
        raise ValueError("resolution_submission_invalid")
    item = replace(submission)
    snap = item.snapshot
    age = item.checked_at - snap.fetched_at
    if age < timedelta(0):
        return ResolutionAssessment("blocked", "snapshot_from_future")
    if age > timedelta(seconds=MAX_REVIEW_AGE_SECONDS):
        return ResolutionAssessment("blocked", "snapshot_stale")
    try:
        data = strict_json(snap.raw_json.decode("utf-8"))
        if type(data) is not dict:
            raise _Rejected("invalid_payload")
        if data.get("conditionId") != item.condition_id or data.get("slug") != snap.market_slug:
            raise _Rejected("market_identity_mismatch")
        labels = _array(data.get("outcomes"))
        if any(type(label) is not str for label in labels):
            raise _Rejected("unsupported_outcomes")
        labels = [label.lower() for label in labels]
        if set(labels) != {"yes", "no"}:
            raise _Rejected("unsupported_outcomes")
        if type(data.get("closed")) is not bool:
            raise _Rejected("invalid_payload")
        if data["closed"] is False:
            return ResolutionAssessment("pending", "market_not_closed")
        if data.get("acceptingOrders") is not False:
            raise _Rejected("order_state_not_final")
        # A conservative supported finality hint, not a guarantee of oracle truth.
        if data.get("umaResolutionStatus") != "resolved":
            return ResolutionAssessment("pending", "resolution_not_final")
        prices = [_price(value) for value in _array(data.get("outcomePrices"))]
        if sorted(prices) != [Decimal(0), Decimal(1)]:
            return ResolutionAssessment("blocked", "non_binary_payout")
        candidate = labels[prices.index(Decimal(1))] == "yes"
    except _Rejected as error:
        return ResolutionAssessment("blocked", str(error))
    except Exception:
        return ResolutionAssessment("blocked", "invalid_payload")
    proof = item.confirmation
    if proof is None:
        return ResolutionAssessment("needs_confirmation", "independent_confirmation_required", candidate)
    if (proof.condition_id != item.condition_id or proof.market_slug != snap.market_slug
            or proof.gamma_content_sha256 != snap.content_sha256):
        return ResolutionAssessment("blocked", "confirmation_scope_mismatch")
    if not proof.resolved_at <= snap.fetched_at <= proof.confirmed_at <= item.checked_at:
        return ResolutionAssessment("blocked", "confirmation_time_invalid")
    if proof.actual_yes is not candidate:
        return ResolutionAssessment("blocked", "confirmation_disagrees")
    return ResolutionAssessment("ready", "operator_confirmed", candidate)


__all__ = ("IndependentResolutionConfirmation", "ResolutionSubmission",
           "ResolutionAssessment", "assess_resolution")
