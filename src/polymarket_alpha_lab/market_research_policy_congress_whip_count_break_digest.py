"""Pure Phase 1 congress whip count break digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_CONGRESS_WHIP_COUNT_BREAK_DIGEST_CONFIG_VERSION = (
    "market-research-policy-congress-whip-count-break-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
WHIP_BREAK_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

CHAMBERS = ("house", "senate")
EXPECTED_OUTCOMES = (
    "passage_expected",
    "failure_expected",
    "confirmation_expected",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "private" + "_key",
    "wall" + "et",
    "au" + "th",
    "sec" + "ret",
    "tok" + "en",
)

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_congress_whip_count_break_screening",
    WATCH_STATUS: "monitor_report_only_congress_whip_count_break_screening",
    PASS_STATUS: "allow_report_only_congress_whip_count_break_screening",
}

__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_CONGRESS_WHIP_COUNT_BREAK_DIGEST_CONFIG_VERSION",
    "PolicyCongressWhipCountBreakDigestConfig",
    "PolicyCongressWhipCountBreakObservation",
    "PolicyCongressWhipCountBreakDigestRow",
    "PolicyCongressWhipCountBreakReasonCodeCount",
    "PolicyCongressWhipCountBreakDigestReport",
    "build_market_research_policy_congress_whip_count_break_digest",
    "market_research_policy_congress_whip_count_break_digest_payload",
)


@dataclass(frozen=True)
class PolicyCongressWhipCountBreakDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_CONGRESS_WHIP_COUNT_BREAK_DIGEST_CONFIG_VERSION
    )
    watch_margin_votes: Decimal = Decimal("5.000000")
    watch_public_break_count: Decimal = Decimal("2.000000")
    blocked_public_break_count: Decimal = Decimal("5.000000")
    watch_undecided_count: Decimal = Decimal("10.000000")
    blocked_undecided_count: Decimal = Decimal("20.000000")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCongressWhipCountBreakDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CONGRESS_WHIP_COUNT_BREAK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_margin_votes",
            "watch_public_break_count",
            "blocked_public_break_count",
            "watch_undecided_count",
            "blocked_undecided_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_public_break_count > self.blocked_public_break_count:
            raise ValueError(
                "watch_public_break_count must not exceed blocked_public_break_count",
            )
        if self.watch_undecided_count > self.blocked_undecided_count:
            raise ValueError(
                "watch_undecided_count must not exceed blocked_undecided_count",
            )
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class PolicyCongressWhipCountBreakObservation:
    source_id: str
    market_slug: str
    chamber: str
    vote_key: str
    caucus_key: str
    expected_outcome: str
    required_vote_count: Decimal
    committed_support_count: Decimal
    committed_opposition_count: Decimal
    undecided_count: Decimal
    public_break_count: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCongressWhipCountBreakObservation, "observation")
        for field_name in (
            "source_id",
            "market_slug",
            "vote_key",
            "caucus_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("chamber", self.chamber, CHAMBERS)
        _require_member("expected_outcome", self.expected_outcome, EXPECTED_OUTCOMES)
        object.__setattr__(
            self,
            "required_vote_count",
            _normalize_positive_decimal("required_vote_count", self.required_vote_count),
        )
        for field_name in (
            "committed_support_count",
            "committed_opposition_count",
            "undecided_count",
            "public_break_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class PolicyCongressWhipCountBreakDigestRow:
    source_id: str
    market_slug: str
    chamber: str
    vote_key: str
    caucus_key: str
    expected_outcome: str
    required_vote_count: Decimal
    committed_support_count: Decimal
    committed_opposition_count: Decimal
    undecided_count: Decimal
    public_break_count: Decimal
    support_gap_count: Decimal
    support_surplus_count: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    whip_break_risk_score: Decimal
    whip_break_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCongressWhipCountBreakDigestRow, "row")
        for field_name in (
            "source_id",
            "market_slug",
            "vote_key",
            "caucus_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("chamber", self.chamber, CHAMBERS)
        _require_member("expected_outcome", self.expected_outcome, EXPECTED_OUTCOMES)
        object.__setattr__(
            self,
            "required_vote_count",
            _normalize_positive_decimal("required_vote_count", self.required_vote_count),
        )
        for field_name in (
            "committed_support_count",
            "committed_opposition_count",
            "undecided_count",
            "public_break_count",
            "support_gap_count",
            "support_surplus_count",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "whip_break_risk_score",
            _normalize_probability("whip_break_risk_score", self.whip_break_risk_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("whip_break_status", self.whip_break_status, WHIP_BREAK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class PolicyCongressWhipCountBreakReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            PolicyCongressWhipCountBreakReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self, "reason_code_count")


@dataclass(frozen=True)
class PolicyCongressWhipCountBreakDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    support_gap_row_count: Decimal
    public_break_row_count: Decimal
    high_undecided_row_count: Decimal
    max_support_gap_count: Decimal
    max_public_break_count: Decimal
    average_whip_break_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PolicyCongressWhipCountBreakReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyCongressWhipCountBreakDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CONGRESS_WHIP_COUNT_BREAK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "support_gap_row_count",
            "public_break_row_count",
            "high_undecided_row_count",
            "max_support_gap_count",
            "max_public_break_count",
            "average_whip_break_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, WHIP_BREAK_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self, "report")


def build_market_research_policy_congress_whip_count_break_digest(
    observations: Iterable[PolicyCongressWhipCountBreakObservation],
    *,
    config: PolicyCongressWhipCountBreakDigestConfig,
    generated_at: datetime,
) -> PolicyCongressWhipCountBreakDigestReport:
    if type(config) is not PolicyCongressWhipCountBreakDigestConfig:
        raise ValueError(
            "config must be exactly PolicyCongressWhipCountBreakDigestConfig",
        )
    _require_hard_flags(config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return PolicyCongressWhipCountBreakDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "congress_whip_count_source_stale"),
        support_gap_row_count=_support_gap_row_count(rows),
        public_break_row_count=_public_break_row_count(rows),
        high_undecided_row_count=_high_undecided_row_count(rows),
        max_support_gap_count=_max_row_decimal(rows, "support_gap_count"),
        max_public_break_count=_max_row_decimal(rows, "public_break_count"),
        average_whip_break_risk_score=_ratio(
            _sum_decimal(row.whip_break_risk_score for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_policy_congress_whip_count_break_digest_payload(
    report: PolicyCongressWhipCountBreakDigestReport,
) -> dict[str, Any]:
    if type(report) is not PolicyCongressWhipCountBreakDigestReport:
        raise ValueError(
            "report must be exactly PolicyCongressWhipCountBreakDigestReport",
        )
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: PolicyCongressWhipCountBreakObservation,
    *,
    config: PolicyCongressWhipCountBreakDigestConfig,
    generated_at: datetime,
) -> PolicyCongressWhipCountBreakDigestRow:
    support_gap_count = _support_gap_count(
        value.required_vote_count,
        value.committed_support_count,
    )
    support_surplus_count = _support_surplus_count(
        value.required_vote_count,
        value.committed_support_count,
    )
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    whip_break_status = _whip_break_status(
        support_gap_count=support_gap_count,
        support_surplus_count=support_surplus_count,
        public_break_count=value.public_break_count,
        undecided_count=value.undecided_count,
        source_fresh=source_fresh,
        config=config,
    )
    return PolicyCongressWhipCountBreakDigestRow(
        source_id=value.source_id,
        market_slug=value.market_slug,
        chamber=value.chamber,
        vote_key=value.vote_key,
        caucus_key=value.caucus_key,
        expected_outcome=value.expected_outcome,
        required_vote_count=value.required_vote_count,
        committed_support_count=value.committed_support_count,
        committed_opposition_count=value.committed_opposition_count,
        undecided_count=value.undecided_count,
        public_break_count=value.public_break_count,
        support_gap_count=support_gap_count,
        support_surplus_count=support_surplus_count,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        whip_break_risk_score=_whip_break_risk_score(
            support_gap_count=support_gap_count,
            support_surplus_count=support_surplus_count,
            public_break_count=value.public_break_count,
            undecided_count=value.undecided_count,
            source_fresh=source_fresh,
            config=config,
        ),
        whip_break_status=whip_break_status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            whip_break_status=whip_break_status,
            source_fresh=source_fresh,
            support_gap_count=support_gap_count,
            support_surplus_count=support_surplus_count,
            public_break_count=value.public_break_count,
            undecided_count=value.undecided_count,
            config=config,
        ),
    )


def _whip_break_status(
    *,
    support_gap_count: Decimal,
    support_surplus_count: Decimal,
    public_break_count: Decimal,
    undecided_count: Decimal,
    source_fresh: bool,
    config: PolicyCongressWhipCountBreakDigestConfig,
) -> str:
    if (
        not source_fresh
        or support_gap_count > ZERO
        or public_break_count >= config.blocked_public_break_count
        or undecided_count >= config.blocked_undecided_count
    ):
        return BLOCKED_STATUS
    if (
        support_surplus_count <= config.watch_margin_votes
        or public_break_count >= config.watch_public_break_count
        or undecided_count >= config.watch_undecided_count
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _whip_break_risk_score(
    *,
    support_gap_count: Decimal,
    support_surplus_count: Decimal,
    public_break_count: Decimal,
    undecided_count: Decimal,
    source_fresh: bool,
    config: PolicyCongressWhipCountBreakDigestConfig,
) -> Decimal:
    if not source_fresh or support_gap_count > ZERO:
        return ONE
    return max(
        _margin_watch_risk_score(support_surplus_count, config.watch_margin_votes),
        _capped_ratio(public_break_count, config.blocked_public_break_count),
        _capped_ratio(undecided_count, config.blocked_undecided_count),
    )


def _margin_watch_risk_score(
    support_surplus_count: Decimal,
    watch_margin_votes: Decimal,
) -> Decimal:
    if support_surplus_count > watch_margin_votes:
        return ZERO
    return _ratio(watch_margin_votes - support_surplus_count, watch_margin_votes)


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    whip_break_status: str,
    source_fresh: bool,
    support_gap_count: Decimal,
    support_surplus_count: Decimal,
    public_break_count: Decimal,
    undecided_count: Decimal,
    config: PolicyCongressWhipCountBreakDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(
        {
            BLOCKED_STATUS: "congress_whip_count_break_blocked",
            WATCH_STATUS: "congress_whip_count_break_watch",
            PASS_STATUS: "congress_whip_count_break_below_threshold",
        }[whip_break_status],
    )
    reason_codes.append(
        "congress_whip_count_source_fresh"
        if source_fresh
        else "congress_whip_count_source_stale",
    )
    if support_gap_count > ZERO:
        reason_codes.append("congress_whip_count_support_gap_blocked")
    elif support_surplus_count <= config.watch_margin_votes:
        reason_codes.append("congress_whip_count_margin_watch")
    if public_break_count >= config.blocked_public_break_count:
        reason_codes.append("congress_whip_count_public_break_blocked")
    elif public_break_count >= config.watch_public_break_count:
        reason_codes.append("congress_whip_count_public_break_watch")
    if undecided_count >= config.blocked_undecided_count:
        reason_codes.append("congress_whip_count_undecided_blocked")
    elif undecided_count >= config.watch_undecided_count:
        reason_codes.append("congress_whip_count_undecided_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("congress_whip_count_break_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
) -> tuple[PolicyCongressWhipCountBreakReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("congress_whip_count_break_digest_empty",):
        return (
            PolicyCongressWhipCountBreakReasonCodeCount(
                reason_code="congress_whip_count_break_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        PolicyCongressWhipCountBreakReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[PolicyCongressWhipCountBreakObservation],
) -> tuple[PolicyCongressWhipCountBreakObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain PolicyCongressWhipCountBreakObservation",
        )
    normalized = tuple(observations)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyCongressWhipCountBreakObservation:
            raise ValueError(
                "observations must contain PolicyCongressWhipCountBreakObservation",
            )
        _require_hard_flags(value, "observation")
        if value.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[PolicyCongressWhipCountBreakDigestRow],
) -> tuple[PolicyCongressWhipCountBreakDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain PolicyCongressWhipCountBreakDigestRow")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not PolicyCongressWhipCountBreakDigestRow:
            raise ValueError("rows must contain PolicyCongressWhipCountBreakDigestRow")
        _require_hard_flags(row, "row")
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id")
        seen.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[PolicyCongressWhipCountBreakReasonCodeCount],
) -> tuple[PolicyCongressWhipCountBreakReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not PolicyCongressWhipCountBreakReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PolicyCongressWhipCountBreakReasonCodeCount",
            )
        _require_hard_flags(value, "reason_code_count")
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: PolicyCongressWhipCountBreakDigestRow) -> None:
    if row.support_gap_count != _support_gap_count(
        row.required_vote_count,
        row.committed_support_count,
    ):
        raise ValueError("support_gap_count must match required and support counts")
    if row.support_surplus_count != _support_surplus_count(
        row.required_vote_count,
        row.committed_support_count,
    ):
        raise ValueError("support_surplus_count must match required and support counts")
    expected_status_reason = {
        BLOCKED_STATUS: "congress_whip_count_break_blocked",
        WATCH_STATUS: "congress_whip_count_break_watch",
        PASS_STATUS: "congress_whip_count_break_below_threshold",
    }[row.whip_break_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("whip_break_status must match reason_codes")


def _validate_report(report: PolicyCongressWhipCountBreakDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "congress_whip_count_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.support_gap_row_count != _support_gap_row_count(report.rows):
        raise ValueError("support_gap_row_count must match rows")
    if report.public_break_row_count != _public_break_row_count(report.rows):
        raise ValueError("public_break_row_count must match rows")
    if report.high_undecided_row_count != _high_undecided_row_count(report.rows):
        raise ValueError("high_undecided_row_count must match rows")
    if report.max_support_gap_count != _max_row_decimal(report.rows, "support_gap_count"):
        raise ValueError("max_support_gap_count must match rows")
    if report.max_public_break_count != _max_row_decimal(report.rows, "public_break_count"):
        raise ValueError("max_public_break_count must match rows")
    if report.average_whip_break_risk_score != _ratio(
        _sum_decimal(row.whip_break_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_whip_break_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _digest_status(rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.whip_break_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.whip_break_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _row_sort_key(
    row: PolicyCongressWhipCountBreakDigestRow,
) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.whip_break_status],
        -row.whip_break_risk_score,
        row.chamber,
        row.vote_key,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.whip_break_status == status))


def _support_gap_row_count(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.support_gap_count > ZERO))


def _public_break_row_count(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                "congress_whip_count_public_break_blocked" in row.reason_codes
                or "congress_whip_count_public_break_watch" in row.reason_codes
            )
        ),
    )


def _high_undecided_row_count(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                "congress_whip_count_undecided_blocked" in row.reason_codes
                or "congress_whip_count_undecided_watch" in row.reason_codes
            )
        ),
    )


def _reason_count(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[PolicyCongressWhipCountBreakDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _support_gap_count(required_vote_count: Decimal, committed_support_count: Decimal) -> Decimal:
    if committed_support_count >= required_vote_count:
        return ZERO
    return _quantize_decimal(required_vote_count - committed_support_count)


def _support_surplus_count(
    required_vote_count: Decimal,
    committed_support_count: Decimal,
) -> Decimal:
    if committed_support_count <= required_vote_count:
        return ZERO
    return _quantize_decimal(committed_support_count - required_vote_count)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return min(ONE, _ratio(numerator, denominator))


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_text_fragment(value):
        raise ValueError(f"unsafe public text in {field_name}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object, label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
