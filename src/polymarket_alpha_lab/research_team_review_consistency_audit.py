"""Pure report-only audit for cross-team research review consistency.

The module is deterministic and side-effect free. Callers provide immutable
team review inputs; the audit returns public-safe consistency rows, summary
status, and reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_RESEARCH_TEAM_REVIEW_CONSISTENCY_CONFIG_VERSION = (
    "research-team-review-consistency-audit-v0"
)
STATUSES = ("pass", "watch", "block")
NEXT_STEPS = {
    "pass": "archive_consistent_research_reviews",
    "watch": "review_research_review_consistency_watches",
    "block": "resolve_research_review_consistency_blocks",
}
ZERO = Decimal("0")
ONE = Decimal("1")
UNSAFE_FIELD_FRAGMENTS = frozenset(
    (
        "account",
        "api_key",
        "auth",
        "balance",
        "cancel",
        "credential",
        "dsn",
        "exchange_mutation",
        "key",
        "live_trading",
        "network",
        "order",
        "password",
        "persistence",
        "private",
        "replace",
        "secret",
        "sign",
        "token",
        "wallet",
    ),
)
UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "api_key=",
        "authorization=",
        "credential=",
        "database_url=",
        "dsn=",
        "password=",
        "postgres://",
        "postgresql://",
        "private_key=",
        "secret=",
        "token=",
    ),
)
TRADE_INSTRUCTION_FRAGMENTS = frozenset(
    (
        "buy",
        "close position",
        "execute trade",
        "investment recommendation",
        "limit order",
        "market order",
        "open position",
        "place order",
        "position sizing",
        "position_sizing",
        "sell",
        "submit order",
        "trade recommendation",
    ),
)


@dataclass(frozen=True)
class ResearchTeamReviewConsistencyConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_REVIEW_CONSISTENCY_CONFIG_VERSION
    min_team_review_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewConsistencyConfig:
            raise TypeError("ResearchTeamReviewConsistencyConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewConsistencyConfig:
            raise ValueError("config must be exactly ResearchTeamReviewConsistencyConfig")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_team_review_count",
            _require_positive_whole_decimal("min_team_review_count", self.min_team_review_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewConsistencyInput:
    research_item_id: str
    team_id: str
    review_status: str
    reviewed_at: datetime
    reason_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...]
    escalation_required: bool
    public_notes: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewConsistencyInput:
            raise TypeError("ResearchTeamReviewConsistencyInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewConsistencyInput:
            raise ValueError("input row must be exactly ResearchTeamReviewConsistencyInput")
        for field_name in ("research_item_id", "team_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("review_status", self.review_status)
        object.__setattr__(self, "reviewed_at", _as_utc("reviewed_at", self.reviewed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_code_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_code_tuple(
                "evidence_gap_codes",
                self.evidence_gap_codes,
                allow_empty=True,
            ),
        )
        if type(self.escalation_required) is not bool:
            raise ValueError("escalation_required must be a bool")
        _require_public_text("public_notes", self.public_notes)
        _reject_trade_or_investment_instructions("public_notes", self.public_notes)
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamReviewConsistencyAuditRow:
    research_item_id: str
    audit_status: str
    team_count: Decimal
    reviewed_team_ids: tuple[str, ...]
    latest_reviewed_at: datetime
    status_values: tuple[str, ...]
    reason_code_values: tuple[str, ...]
    evidence_gap_code_values: tuple[str, ...]
    status_divergence_count: Decimal
    reason_code_divergence_count: Decimal
    evidence_gap_divergence_count: Decimal
    escalation_required_count: Decimal
    min_team_review_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewConsistencyAuditRow:
            raise TypeError("ResearchTeamReviewConsistencyAuditRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewConsistencyAuditRow:
            raise ValueError("row must be exactly ResearchTeamReviewConsistencyAuditRow")
        _require_canonical_string("research_item_id", self.research_item_id)
        _require_status("audit_status", self.audit_status)
        object.__setattr__(self, "team_count", _require_positive_whole_decimal("team_count", self.team_count))
        object.__setattr__(
            self,
            "reviewed_team_ids",
            _normalize_code_tuple("reviewed_team_ids", self.reviewed_team_ids, allow_empty=False),
        )
        object.__setattr__(
            self,
            "latest_reviewed_at",
            _as_utc("latest_reviewed_at", self.latest_reviewed_at),
        )
        object.__setattr__(
            self,
            "status_values",
            _normalize_status_values(self.status_values),
        )
        object.__setattr__(
            self,
            "reason_code_values",
            _normalize_code_tuple(
                "reason_code_values",
                self.reason_code_values,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "evidence_gap_code_values",
            _normalize_code_tuple(
                "evidence_gap_code_values",
                self.evidence_gap_code_values,
                allow_empty=True,
            ),
        )
        for field_name in (
            "status_divergence_count",
            "reason_code_divergence_count",
            "evidence_gap_divergence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_binary_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "escalation_required_count",
            _require_nonnegative_whole_decimal(
                "escalation_required_count",
                self.escalation_required_count,
            ),
        )
        object.__setattr__(
            self,
            "min_team_review_count",
            _require_positive_whole_decimal("min_team_review_count", self.min_team_review_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_code_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamReviewConsistencyReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewConsistencyReasonCodeCount:
            raise TypeError(
                "ResearchTeamReviewConsistencyReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewConsistencyReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly ResearchTeamReviewConsistencyReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamReviewConsistencyAuditReport:
    generated_at: datetime
    config_version: str
    audit_status: str
    next_step: str
    review_item_count: Decimal
    team_review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status_divergence_count: Decimal
    reason_code_divergence_count: Decimal
    evidence_gap_divergence_count: Decimal
    escalation_required_count: Decimal
    rows: tuple[ResearchTeamReviewConsistencyAuditRow, ...]
    reason_code_counts: tuple[ResearchTeamReviewConsistencyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewConsistencyAuditReport:
            raise TypeError(
                "ResearchTeamReviewConsistencyAuditReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewConsistencyAuditReport:
            raise ValueError("report must be exactly ResearchTeamReviewConsistencyAuditReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("audit_status", self.audit_status)
        _require_canonical_string("next_step", self.next_step)
        for field_name in (
            "review_item_count",
            "team_review_count",
            "pass_count",
            "watch_count",
            "block_count",
            "status_divergence_count",
            "reason_code_divergence_count",
            "evidence_gap_divergence_count",
            "escalation_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_code_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_team_review_consistency_audit(
    reviews: Iterable[ResearchTeamReviewConsistencyInput],
    *,
    config: ResearchTeamReviewConsistencyConfig,
    generated_at: datetime,
) -> ResearchTeamReviewConsistencyAuditReport:
    if type(config) is not ResearchTeamReviewConsistencyConfig:
        raise ValueError("config must be a ResearchTeamReviewConsistencyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    review_rows = _normalize_inputs(reviews)
    for review in review_rows:
        if review.reviewed_at > generated_at_utc:
            raise ValueError("reviewed_at must not be after generated_at")

    grouped: dict[str, list[ResearchTeamReviewConsistencyInput]] = {}
    seen_pairs: set[tuple[str, str]] = set()
    for review in review_rows:
        key = (review.research_item_id, review.team_id)
        if key in seen_pairs:
            raise ValueError("reviews must contain at most one team review per research item")
        seen_pairs.add(key)
        grouped.setdefault(review.research_item_id, []).append(review)

    rows = tuple(
        _audit_row_from_reviews(
            research_item_id=research_item_id,
            reviews=tuple(grouped[research_item_id]),
            config=config,
        )
        for research_item_id in sorted(grouped)
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(count.reason_code for count in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchTeamReviewConsistencyReasonCodeCount(
                reason_code="no_research_team_reviews",
                count=ONE,
            ),
        )
        reason_codes = ("no_research_team_reviews",)
    audit_status = _report_status(rows)
    return ResearchTeamReviewConsistencyAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        audit_status=audit_status,
        next_step=NEXT_STEPS[audit_status],
        review_item_count=_count_decimal(len(rows)),
        team_review_count=sum((row.team_count for row in rows), ZERO),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status_divergence_count=sum((row.status_divergence_count for row in rows), ZERO),
        reason_code_divergence_count=sum(
            (row.reason_code_divergence_count for row in rows),
            ZERO,
        ),
        evidence_gap_divergence_count=sum(
            (row.evidence_gap_divergence_count for row in rows),
            ZERO,
        ),
        escalation_required_count=sum((row.escalation_required_count for row in rows), ZERO),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_review_consistency_audit_payload(
    report: ResearchTeamReviewConsistencyAuditReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamReviewConsistencyAuditReport:
        raise ValueError("report must be a ResearchTeamReviewConsistencyAuditReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("research team review consistency audit payload", payload)
    _reject_trade_or_investment_instructions(
        "research team review consistency audit payload",
        payload,
    )
    return payload


def _audit_row_from_reviews(
    *,
    research_item_id: str,
    reviews: tuple[ResearchTeamReviewConsistencyInput, ...],
    config: ResearchTeamReviewConsistencyConfig,
) -> ResearchTeamReviewConsistencyAuditRow:
    sorted_reviews = tuple(sorted(reviews, key=lambda review: review.team_id))
    reviewed_team_ids = tuple(review.team_id for review in sorted_reviews)
    status_values = _status_values(tuple(review.review_status for review in sorted_reviews))
    reason_code_sets = tuple(review.reason_codes for review in sorted_reviews)
    evidence_gap_sets = tuple(review.evidence_gap_codes for review in sorted_reviews)
    status_divergence_count = _count_decimal(1 if len(status_values) > 1 else 0)
    reason_code_divergence_count = _count_decimal(1 if len(set(reason_code_sets)) > 1 else 0)
    evidence_gap_divergence_count = _count_decimal(1 if len(set(evidence_gap_sets)) > 1 else 0)
    escalation_required_count = _count_decimal(
        sum(1 for review in sorted_reviews if review.escalation_required),
    )
    team_count = _count_decimal(len(sorted_reviews))
    audit_status = _row_status(
        team_count=team_count,
        min_team_review_count=config.min_team_review_count,
        status_divergence_count=status_divergence_count,
        reason_code_divergence_count=reason_code_divergence_count,
        evidence_gap_divergence_count=evidence_gap_divergence_count,
        escalation_required_count=escalation_required_count,
    )
    reason_codes = _row_reason_codes(
        audit_status=audit_status,
        team_count=team_count,
        min_team_review_count=config.min_team_review_count,
        status_divergence_count=status_divergence_count,
        reason_code_divergence_count=reason_code_divergence_count,
        evidence_gap_divergence_count=evidence_gap_divergence_count,
        escalation_required_count=escalation_required_count,
    )
    return ResearchTeamReviewConsistencyAuditRow(
        research_item_id=research_item_id,
        audit_status=audit_status,
        team_count=team_count,
        reviewed_team_ids=reviewed_team_ids,
        latest_reviewed_at=max(review.reviewed_at for review in sorted_reviews),
        status_values=status_values,
        reason_code_values=tuple(
            sorted({reason_code for review in sorted_reviews for reason_code in review.reason_codes}),
        ),
        evidence_gap_code_values=tuple(
            sorted(
                {
                    evidence_gap_code
                    for review in sorted_reviews
                    for evidence_gap_code in review.evidence_gap_codes
                },
            ),
        ),
        status_divergence_count=status_divergence_count,
        reason_code_divergence_count=reason_code_divergence_count,
        evidence_gap_divergence_count=evidence_gap_divergence_count,
        escalation_required_count=escalation_required_count,
        min_team_review_count=config.min_team_review_count,
        reason_codes=reason_codes,
    )


def _normalize_inputs(
    reviews: Iterable[ResearchTeamReviewConsistencyInput],
) -> tuple[ResearchTeamReviewConsistencyInput, ...]:
    if isinstance(reviews, (str, bytes)):
        raise ValueError("reviews must be an iterable")
    try:
        normalized = tuple(reviews)
    except TypeError as exc:
        raise ValueError("reviews must be an iterable") from exc
    for review in normalized:
        if type(review) is not ResearchTeamReviewConsistencyInput:
            raise ValueError("reviews must contain ResearchTeamReviewConsistencyInput values")
        _require_hard_flags("input row", review)
    return normalized


def _row_status(
    *,
    team_count: Decimal,
    min_team_review_count: Decimal,
    status_divergence_count: Decimal,
    reason_code_divergence_count: Decimal,
    evidence_gap_divergence_count: Decimal,
    escalation_required_count: Decimal,
) -> str:
    if (
        team_count < min_team_review_count
        or status_divergence_count > ZERO
        or escalation_required_count > ZERO
    ):
        return "block"
    if reason_code_divergence_count > ZERO or evidence_gap_divergence_count > ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    audit_status: str,
    team_count: Decimal,
    min_team_review_count: Decimal,
    status_divergence_count: Decimal,
    reason_code_divergence_count: Decimal,
    evidence_gap_divergence_count: Decimal,
    escalation_required_count: Decimal,
) -> tuple[str, ...]:
    reason_codes = {f"research_team_review_consistency_{audit_status}"}
    if team_count < min_team_review_count:
        reason_codes.add("insufficient_team_reviews")
    if status_divergence_count > ZERO:
        reason_codes.add("status_divergence")
    if escalation_required_count > ZERO:
        reason_codes.add("escalation_required")
    has_hard_block_reason = any(
        reason_code in reason_codes
        for reason_code in (
            "insufficient_team_reviews",
            "status_divergence",
            "escalation_required",
        )
    )
    if not has_hard_block_reason:
        if reason_code_divergence_count > ZERO:
            reason_codes.add("reason_code_divergence")
        if evidence_gap_divergence_count > ZERO:
            reason_codes.add("evidence_gap_divergence")
    if reason_codes == {"research_team_review_consistency_pass"}:
        reason_codes.add("review_consensus_clear")
    return tuple(sorted(reason_codes))


def _report_status(rows: tuple[ResearchTeamReviewConsistencyAuditRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.audit_status == "block" for row in rows):
        return "block"
    if any(row.audit_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(rows: tuple[ResearchTeamReviewConsistencyAuditRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.audit_status == status))


def _reason_code_counts(
    rows: tuple[ResearchTeamReviewConsistencyAuditRow, ...],
) -> tuple[ResearchTeamReviewConsistencyReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamReviewConsistencyReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_rows(
    rows: tuple[ResearchTeamReviewConsistencyAuditRow, ...],
) -> tuple[ResearchTeamReviewConsistencyAuditRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamReviewConsistencyAuditRow:
            raise ValueError("rows must contain ResearchTeamReviewConsistencyAuditRow values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.research_item_id)):
        raise ValueError("rows must be sorted by research_item_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamReviewConsistencyReasonCodeCount, ...],
) -> tuple[ResearchTeamReviewConsistencyReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamReviewConsistencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTeamReviewConsistencyReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchTeamReviewConsistencyAuditRow) -> None:
    if row.team_count != _count_decimal(len(row.reviewed_team_ids)):
        raise ValueError("team_count must match reviewed_team_ids")
    if row.escalation_required_count > row.team_count:
        raise ValueError("escalation_required_count must not exceed team_count")
    expected_status = _row_status(
        team_count=row.team_count,
        min_team_review_count=row.min_team_review_count,
        status_divergence_count=row.status_divergence_count,
        reason_code_divergence_count=row.reason_code_divergence_count,
        evidence_gap_divergence_count=row.evidence_gap_divergence_count,
        escalation_required_count=row.escalation_required_count,
    )
    if row.audit_status != expected_status:
        raise ValueError("audit_status must match divergence counts")
    expected_reason_codes = _row_reason_codes(
        audit_status=row.audit_status,
        team_count=row.team_count,
        min_team_review_count=row.min_team_review_count,
        status_divergence_count=row.status_divergence_count,
        reason_code_divergence_count=row.reason_code_divergence_count,
        evidence_gap_divergence_count=row.evidence_gap_divergence_count,
        escalation_required_count=row.escalation_required_count,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row consistency")


def _validate_report_consistency(report: ResearchTeamReviewConsistencyAuditReport) -> None:
    if report.review_item_count != _count_decimal(len(report.rows)):
        raise ValueError("review_item_count must match rows")
    if report.team_review_count != sum((row.team_count for row in report.rows), ZERO):
        raise ValueError("team_review_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status_divergence_count != sum(
        (row.status_divergence_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("status_divergence_count must match rows")
    if report.reason_code_divergence_count != sum(
        (row.reason_code_divergence_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("reason_code_divergence_count must match rows")
    if report.evidence_gap_divergence_count != sum(
        (row.evidence_gap_divergence_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("evidence_gap_divergence_count must match rows")
    if report.escalation_required_count != sum(
        (row.escalation_required_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("escalation_required_count must match rows")
    if report.audit_status != _report_status(report.rows):
        raise ValueError("audit_status must match rows")
    if report.next_step != NEXT_STEPS[report.audit_status]:
        raise ValueError("next_step must match audit_status")
    if report.reason_code_counts != _expected_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(count.reason_code for count in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _expected_reason_code_counts(
    rows: tuple[ResearchTeamReviewConsistencyAuditRow, ...],
) -> tuple[ResearchTeamReviewConsistencyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamReviewConsistencyReasonCodeCount(
                reason_code="no_research_team_reviews",
                count=ONE,
            ),
        )
    return _reason_code_counts(rows)


def _json_ready(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) in (str,):
        _require_public_text(path or label, value)
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must not be numeric")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_key(key):
                raise ValueError(f"unsafe field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]" if path else label)
        return
    raise ValueError(f"{path or label} is not public JSON")


def _reject_trade_or_investment_instructions(label: str, value: object) -> None:
    for text in _iter_public_strings(value):
        normalized = text.lower()
        if any(fragment in normalized for fragment in TRADE_INSTRUCTION_FRAGMENTS):
            raise ValueError(f"{label} must not contain trade or investment instruction")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        strings: list[str] = []
        for field in fields(value):
            strings.extend(_iter_public_strings(getattr(value, field.name)))
        return tuple(strings)
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_binary_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _status_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(status for status in STATUSES if status in values)


def _normalize_status_values(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("status_values must be a tuple")
    for value in values:
        _require_status("status_values", value)
    normalized = _status_values(values)
    if not normalized:
        raise ValueError("status_values must be nonempty")
    if values != normalized:
        raise ValueError("status_values must be unique and sorted")
    return normalized


def _normalize_code_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        if value not in normalized:
            normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(normalized))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789_:-")
    if any(char not in allowed_chars for char in value):
        raise ValueError(f"{field_name} must contain public reason-code tokens")
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if _is_unsafe_key(value):
        raise ValueError(f"{field_name} has unsafe value")


def _is_unsafe_key(key: str) -> bool:
    normalized = key.lower()
    return any(fragment in normalized for fragment in UNSAFE_FIELD_FRAGMENTS)


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_CONSISTENCY_CONFIG_VERSION",
    "ResearchTeamReviewConsistencyAuditReport",
    "ResearchTeamReviewConsistencyAuditRow",
    "ResearchTeamReviewConsistencyConfig",
    "ResearchTeamReviewConsistencyInput",
    "ResearchTeamReviewConsistencyReasonCodeCount",
    "build_research_team_review_consistency_audit",
    "research_team_review_consistency_audit_payload",
)
