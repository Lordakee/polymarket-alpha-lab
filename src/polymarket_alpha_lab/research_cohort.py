"""Pure cohort selection for recurring research-cycle collection.

The filter is frozen before outcome inspection: binary, active, not
closed, team-keyword match, ranked by liquidity then condition id.
Changing this rule starts a new config cohort; it never inspects
outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any, Mapping, Sequence


TEAM_KEYWORD_PATTERNS: dict[str, re.Pattern[str]] = {
    "crypto_btc": re.compile(r"(?i)\b(btc|bitcoin)\b"),
    "crypto_eth": re.compile(r"(?i)\b(eth|ethereum)\b"),
}


@dataclass(frozen=True)
class CohortCandidate:
    condition_id: str
    market_slug: str
    question: str
    is_binary: bool
    is_active: bool
    is_closed: bool
    keyword_match: bool
    liquidity: Decimal | None

    def __post_init__(self) -> None:
        for name in ("condition_id", "market_slug", "question"):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        for name in ("is_binary", "is_active", "is_closed", "keyword_match"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a bool")
        if self.liquidity is not None and not isinstance(self.liquidity, Decimal):
            raise ValueError("liquidity must be a Decimal or None")


def candidate_from_metadata(metadata_value: Mapping[str, Any], team_id: str) -> CohortCandidate:
    if team_id not in TEAM_KEYWORD_PATTERNS:
        raise ValueError(f"no cohort keyword pattern for team {team_id!r}")
    tokens = metadata_value.get("clob_token_ids")
    outcomes = metadata_value.get("outcomes")
    text = " ".join(
        part
        for part in (metadata_value.get("slug"), metadata_value.get("question"))
        if isinstance(part, str)
    )
    liquidity = metadata_value.get("liquidity")
    return CohortCandidate(
        condition_id=metadata_value.get("condition_id") or "",
        market_slug=metadata_value.get("slug") or "",
        question=metadata_value.get("question") or "",
        is_binary=(
            isinstance(tokens, list)
            and len(tokens) == 2
            and isinstance(outcomes, list)
            and len(outcomes) == 2
        ),
        is_active=metadata_value.get("active") is True,
        is_closed=metadata_value.get("closed") is True,
        keyword_match=bool(TEAM_KEYWORD_PATTERNS[team_id].search(text)),
        liquidity=liquidity if isinstance(liquidity, Decimal) else None,
    )


def select_cohort(
    candidates: Sequence[CohortCandidate],
    *,
    limit: int,
) -> tuple[CohortCandidate, ...]:
    """Eligible candidates ranked by liquidity desc, condition id asc."""

    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive int")
    eligible = [
        candidate
        for candidate in candidates
        if candidate.is_binary
        and candidate.is_active
        and not candidate.is_closed
        and candidate.keyword_match
        and candidate.condition_id
        and candidate.market_slug
    ]
    ranked = sorted(
        eligible,
        key=lambda item: (
            -(item.liquidity if item.liquidity is not None else Decimal(0)),
            item.condition_id,
        ),
    )
    return tuple(ranked[:limit])


__all__ = (
    "CohortCandidate",
    "TEAM_KEYWORD_PATTERNS",
    "candidate_from_metadata",
    "select_cohort",
)
