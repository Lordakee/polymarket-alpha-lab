"""Phase 1 in-memory contradiction follow-up priority ranker."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any, Iterable


DEFAULT_RESEARCH_PACKET_CONTRADICTION_FOLLOWUP_PRIORITY_V2_CONFIG_VERSION = (
    "research-packet-contradiction-followup-priority-v2"
)

SCORE_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
HOURS_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_FAMILY_INDEPENDENCE_WEIGHT = Decimal("0.200000")
RECENCY_WEIGHT = Decimal("0.200000")
SEVERITY_WEIGHT = Decimal("0.250000")
RESOLUTION_RULE_SENSITIVITY_WEIGHT = Decimal("0.200000")
MARKET_CLOSE_URGENCY_WEIGHT = Decimal("0.150000")

STATUSES = ("empty", "clear", "watch", "blocked")
ROW_STATUSES = ("clear", "watch", "blocked")

SOURCE_FAMILY_INDEPENDENT_REASON = "source_family_independent_followup"
RECENT_CONTRADICTION_REASON = "recent_contradiction_followup"
SEVERE_CONTRADICTION_REASON = "severe_contradiction_followup"
RULE_SENSITIVE_REASON = "resolution_rule_sensitive_followup"
MARKET_CLOSE_URGENT_REASON = "market_close_urgent_followup"
CLEAR_REASON = "contradiction_followup_priority_clear"
WATCH_REASON = "contradiction_followup_priority_watch"
BLOCKED_REASON = "contradiction_followup_priority_blocked"
EMPTY_REASON = "contradiction_followup_priority_empty"

ROW_REASON_CODES = (
    SOURCE_FAMILY_INDEPENDENT_REASON,
    RECENT_CONTRADICTION_REASON,
    SEVERE_CONTRADICTION_REASON,
    RULE_SENSITIVE_REASON,
    MARKET_CLOSE_URGENT_REASON,
    CLEAR_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
)
REPORT_REASON_CODES = (
    SOURCE_FAMILY_INDEPENDENT_REASON,
    RECENT_CONTRADICTION_REASON,
    SEVERE_CONTRADICTION_REASON,
    RULE_SENSITIVE_REASON,
    MARKET_CLOSE_URGENT_REASON,
    CLEAR_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
    EMPTY_REASON,
)

ROW_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "priority_rank",
    "packet_id",
    "event_id",
    "market_id",
    "contradiction_id",
    "source_family",
    "source_family_count",
    "independent_source_family_count",
    "contradiction_observed_at",
    "evidence_age_hours",
    "recency_score",
    "contradiction_severity_score",
    "resolution_rule_sensitivity_score",
    "market_close_at",
    "seconds_until_market_close",
    "market_close_urgency_score",
    "source_family_independence_score",
    "followup_priority_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_FIELDS = (
    *ROW_PUBLIC_FIELDS_WITHOUT_DIGEST[:20],
    "derived_validation_digest",
    *ROW_PUBLIC_FIELDS_WITHOUT_DIGEST[20:],
)
REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "input_count",
    "priority_count",
    "blocked_count",
    "watch_count",
    "clear_count",
    "source_family_independence_count",
    "recent_contradiction_count",
    "severe_contradiction_count",
    "rule_sensitive_count",
    "market_close_urgent_count",
    "max_priority_score",
    "average_priority_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    *REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST[:17],
    "derived_validation_digest",
    *REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST[17:],
)

UNSAFE_PUBLIC_TERMS = (
    "au" + "th",
    "wal" + "let",
    "sec" + "ret",
    "priv" + "ate",
    "sign" + "ing",
    "mut" + "ation",
    "net" + "work",
    "data" + "base",
    "psy" + "copg",
    "sql" + "ite",
    "req" + "uests",
    "url" + "lib",
    "sock" + "et",
    "acc" + "ount",
    "bro" + "ker",
    "sub" + "mit",
    "can" + "cel",
    "tr" + "ade",
    "buy",
    "sell",
    "li" + "ve",
    "ord" + "er",
)


@dataclass(frozen=True)
class ResearchPacketContradictionFollowupPriorityV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_CONTRADICTION_FOLLOWUP_PRIORITY_V2_CONFIG_VERSION
    )
    recency_window_hours: Decimal = Decimal("24.000000")
    market_close_urgency_window_seconds: Decimal = Decimal("3600.000000")
    source_family_independence_watch_score: Decimal = Decimal("0.500000")
    recency_watch_score: Decimal = Decimal("0.500000")
    severity_watch_score: Decimal = Decimal("0.500000")
    resolution_rule_sensitivity_watch_score: Decimal = Decimal("0.500000")
    market_close_urgency_watch_score: Decimal = Decimal("0.500000")
    watch_priority_score: Decimal = Decimal("0.350000")
    blocked_priority_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketContradictionFollowupPriorityV2Config:
            raise TypeError(
                "ResearchPacketContradictionFollowupPriorityV2Config "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketContradictionFollowupPriorityV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "recency_window_hours",
            _normalize_positive_decimal(
                "recency_window_hours",
                self.recency_window_hours,
            ),
        )
        object.__setattr__(
            self,
            "market_close_urgency_window_seconds",
            _normalize_positive_decimal(
                "market_close_urgency_window_seconds",
                self.market_close_urgency_window_seconds,
            ),
        )
        for field_name in (
            "source_family_independence_watch_score",
            "recency_watch_score",
            "severity_watch_score",
            "resolution_rule_sensitivity_watch_score",
            "market_close_urgency_watch_score",
            "watch_priority_score",
            "blocked_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.blocked_priority_score < self.watch_priority_score:
            raise ValueError("blocked_priority_score must be >= watch_priority_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketContradictionFollowupPriorityV2Input:
    packet_id: str
    event_id: str
    market_id: str
    contradiction_id: str
    source_family: str
    source_family_count: Decimal
    independent_source_family_count: Decimal
    contradiction_observed_at: datetime
    contradiction_severity_score: Decimal
    resolution_rule_sensitivity_score: Decimal
    market_close_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketContradictionFollowupPriorityV2Input:
            raise TypeError(
                "ResearchPacketContradictionFollowupPriorityV2Input "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input_row",
            self,
            ResearchPacketContradictionFollowupPriorityV2Input,
        )
        for field_name in (
            "packet_id",
            "event_id",
            "market_id",
            "contradiction_id",
            "source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_family_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_family_count > self.source_family_count:
            raise ValueError(
                "independent_source_family_count must not exceed source_family_count",
            )
        object.__setattr__(
            self,
            "contradiction_observed_at",
            _as_utc("contradiction_observed_at", self.contradiction_observed_at),
        )
        for field_name in (
            "contradiction_severity_score",
            "resolution_rule_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        _require_hard_flags("input_row", self)
        _reject_unsafe_public_payload("input_row", self)


@dataclass(frozen=True)
class ResearchPacketContradictionFollowupPriorityV2Row:
    priority_rank: Decimal
    packet_id: str
    event_id: str
    market_id: str
    contradiction_id: str
    source_family: str
    source_family_count: Decimal
    independent_source_family_count: Decimal
    contradiction_observed_at: datetime
    evidence_age_hours: Decimal
    recency_score: Decimal
    contradiction_severity_score: Decimal
    resolution_rule_sensitivity_score: Decimal
    market_close_at: datetime
    seconds_until_market_close: Decimal
    market_close_urgency_score: Decimal
    source_family_independence_score: Decimal
    followup_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketContradictionFollowupPriorityV2Row:
            raise TypeError(
                "ResearchPacketContradictionFollowupPriorityV2Row "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketContradictionFollowupPriorityV2Row)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "packet_id",
            "event_id",
            "market_id",
            "contradiction_id",
            "source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_family_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_family_count > self.source_family_count:
            raise ValueError(
                "independent_source_family_count must not exceed source_family_count",
            )
        object.__setattr__(
            self,
            "contradiction_observed_at",
            _as_utc("contradiction_observed_at", self.contradiction_observed_at),
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        for field_name in (
            "evidence_age_hours",
            "seconds_until_market_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recency_score",
            "contradiction_severity_score",
            "resolution_rule_sensitivity_score",
            "market_close_urgency_score",
            "source_family_independence_score",
            "followup_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketContradictionFollowupPriorityV2Report:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    priority_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    source_family_independence_count: Decimal
    recent_contradiction_count: Decimal
    severe_contradiction_count: Decimal
    rule_sensitive_count: Decimal
    market_close_urgent_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketContradictionFollowupPriorityV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketContradictionFollowupPriorityV2Report:
            raise TypeError(
                "ResearchPacketContradictionFollowupPriorityV2Report "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchPacketContradictionFollowupPriorityV2Report,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "priority_count",
            "blocked_count",
            "watch_count",
            "clear_count",
            "source_family_independence_count",
            "recent_contradiction_count",
            "severe_contradiction_count",
            "rule_sensitive_count",
            "market_close_urgent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("max_priority_score", "average_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)


def build_research_packet_contradiction_followup_priority_v2_report(
    inputs: Iterable[ResearchPacketContradictionFollowupPriorityV2Input],
    *,
    config: ResearchPacketContradictionFollowupPriorityV2Config,
    generated_at: datetime,
) -> ResearchPacketContradictionFollowupPriorityV2Report:
    _require_exact_type(
        "config",
        config,
        ResearchPacketContradictionFollowupPriorityV2Config,
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(
        _priority_row(row, config=config, generated_at=generated_at_utc)
        for row in input_rows
    )
    rows = tuple(
        _with_rank(row, index)
        for index, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    return ResearchPacketContradictionFollowupPriorityV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count(len(rows)),
        priority_count=_count(sum(1 for row in rows if row.status != "clear")),
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        clear_count=_status_count(rows, "clear"),
        source_family_independence_count=_reason_count(
            rows,
            SOURCE_FAMILY_INDEPENDENT_REASON,
        ),
        recent_contradiction_count=_reason_count(rows, RECENT_CONTRADICTION_REASON),
        severe_contradiction_count=_reason_count(rows, SEVERE_CONTRADICTION_REASON),
        rule_sensitive_count=_reason_count(rows, RULE_SENSITIVE_REASON),
        market_close_urgent_count=_reason_count(rows, MARKET_CLOSE_URGENT_REASON),
        max_priority_score=_max_score(tuple(row.followup_priority_score for row in rows)),
        average_priority_score=_average_score(
            tuple(row.followup_priority_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_contradiction_followup_priority_v2_payload(
    report: ResearchPacketContradictionFollowupPriorityV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketContradictionFollowupPriorityV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report(report)
        return _report_public_payload(report)
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a ResearchPacketContradictionFollowupPriorityV2Report",
    )


def _priority_row(
    row: ResearchPacketContradictionFollowupPriorityV2Input,
    *,
    config: ResearchPacketContradictionFollowupPriorityV2Config,
    generated_at: datetime,
) -> ResearchPacketContradictionFollowupPriorityV2Row:
    if row.contradiction_observed_at > generated_at:
        raise ValueError("contradiction_observed_at must not be after generated_at")
    if row.market_close_at < generated_at:
        raise ValueError("market_close_at must not be before generated_at")
    evidence_age_hours = _hours_between(row.contradiction_observed_at, generated_at)
    seconds_until_market_close = _seconds_between(generated_at, row.market_close_at)
    source_family_independence_score = _ratio_capped(
        row.independent_source_family_count,
        row.source_family_count,
    )
    recency_score = _window_score(evidence_age_hours, config.recency_window_hours)
    market_close_urgency_score = _window_score(
        seconds_until_market_close,
        config.market_close_urgency_window_seconds,
    )
    followup_priority_score = _followup_priority_score(
        source_family_independence_score=source_family_independence_score,
        recency_score=recency_score,
        contradiction_severity_score=row.contradiction_severity_score,
        resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
        market_close_urgency_score=market_close_urgency_score,
    )
    status = _row_status(followup_priority_score, config)
    return ResearchPacketContradictionFollowupPriorityV2Row(
        priority_rank=_count(1),
        packet_id=row.packet_id,
        event_id=row.event_id,
        market_id=row.market_id,
        contradiction_id=row.contradiction_id,
        source_family=row.source_family,
        source_family_count=row.source_family_count,
        independent_source_family_count=row.independent_source_family_count,
        contradiction_observed_at=row.contradiction_observed_at,
        evidence_age_hours=evidence_age_hours,
        recency_score=recency_score,
        contradiction_severity_score=row.contradiction_severity_score,
        resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
        market_close_at=row.market_close_at,
        seconds_until_market_close=seconds_until_market_close,
        market_close_urgency_score=market_close_urgency_score,
        source_family_independence_score=source_family_independence_score,
        followup_priority_score=followup_priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            source_family_independence_score=source_family_independence_score,
            recency_score=recency_score,
            contradiction_severity_score=row.contradiction_severity_score,
            resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
            market_close_urgency_score=market_close_urgency_score,
            status=status,
            config=config,
        ),
    )


def _with_rank(
    row: ResearchPacketContradictionFollowupPriorityV2Row,
    index: int,
) -> ResearchPacketContradictionFollowupPriorityV2Row:
    return ResearchPacketContradictionFollowupPriorityV2Row(
        priority_rank=_count(index),
        packet_id=row.packet_id,
        event_id=row.event_id,
        market_id=row.market_id,
        contradiction_id=row.contradiction_id,
        source_family=row.source_family,
        source_family_count=row.source_family_count,
        independent_source_family_count=row.independent_source_family_count,
        contradiction_observed_at=row.contradiction_observed_at,
        evidence_age_hours=row.evidence_age_hours,
        recency_score=row.recency_score,
        contradiction_severity_score=row.contradiction_severity_score,
        resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
        market_close_at=row.market_close_at,
        seconds_until_market_close=row.seconds_until_market_close,
        market_close_urgency_score=row.market_close_urgency_score,
        source_family_independence_score=row.source_family_independence_score,
        followup_priority_score=row.followup_priority_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _followup_priority_score(
    *,
    source_family_independence_score: Decimal,
    recency_score: Decimal,
    contradiction_severity_score: Decimal,
    resolution_rule_sensitivity_score: Decimal,
    market_close_urgency_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            (source_family_independence_score * SOURCE_FAMILY_INDEPENDENCE_WEIGHT)
            + (recency_score * RECENCY_WEIGHT)
            + (contradiction_severity_score * SEVERITY_WEIGHT)
            + (resolution_rule_sensitivity_score * RESOLUTION_RULE_SENSITIVITY_WEIGHT)
            + (market_close_urgency_score * MARKET_CLOSE_URGENCY_WEIGHT),
        )


def _row_reason_codes(
    *,
    source_family_independence_score: Decimal,
    recency_score: Decimal,
    contradiction_severity_score: Decimal,
    resolution_rule_sensitivity_score: Decimal,
    market_close_urgency_score: Decimal,
    status: str,
    config: ResearchPacketContradictionFollowupPriorityV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_family_independence_score >= config.source_family_independence_watch_score:
        reason_codes.append(SOURCE_FAMILY_INDEPENDENT_REASON)
    if recency_score >= config.recency_watch_score:
        reason_codes.append(RECENT_CONTRADICTION_REASON)
    if contradiction_severity_score >= config.severity_watch_score:
        reason_codes.append(SEVERE_CONTRADICTION_REASON)
    if (
        resolution_rule_sensitivity_score
        >= config.resolution_rule_sensitivity_watch_score
    ):
        reason_codes.append(RULE_SENSITIVE_REASON)
    if market_close_urgency_score >= config.market_close_urgency_watch_score:
        reason_codes.append(MARKET_CLOSE_URGENT_REASON)
    reason_codes.append(
        {
            "clear": CLEAR_REASON,
            "watch": WATCH_REASON,
            "blocked": BLOCKED_REASON,
        }[status],
    )
    return tuple(reason for reason in ROW_REASON_CODES if reason in reason_codes)


def _row_status(
    followup_priority_score: Decimal,
    config: ResearchPacketContradictionFollowupPriorityV2Config,
) -> str:
    if followup_priority_score >= config.blocked_priority_score:
        return "blocked"
    if followup_priority_score >= config.watch_priority_score:
        return "watch"
    return "clear"


def _row_sort_key(
    row: ResearchPacketContradictionFollowupPriorityV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -row.followup_priority_score,
        -row.source_family_independence_score,
        -row.contradiction_severity_score,
        -row.resolution_rule_sensitivity_score,
        row.seconds_until_market_close,
        row.packet_id,
        row.contradiction_id,
    )


def _report_status(
    rows: tuple[ResearchPacketContradictionFollowupPriorityV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[ResearchPacketContradictionFollowupPriorityV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    if WATCH_REASON not in present and BLOCKED_REASON not in present:
        return (CLEAR_REASON,)
    return tuple(
        reason
        for reason in REPORT_REASON_CODES
        if reason in present and reason not in (CLEAR_REASON, EMPTY_REASON)
    )


def _normalize_inputs(
    value: Iterable[ResearchPacketContradictionFollowupPriorityV2Input],
) -> tuple[ResearchPacketContradictionFollowupPriorityV2Input, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketContradictionFollowupPriorityV2Input:
            raise ValueError(
                "inputs must contain ResearchPacketContradictionFollowupPriorityV2Input values",
            )
        _require_hard_flags("input_row", row)
        if row.contradiction_id in seen:
            raise ValueError("inputs must not contain duplicate contradiction_id")
        seen.add(row.contradiction_id)
    return rows


def _normalize_rows(
    value: Iterable[ResearchPacketContradictionFollowupPriorityV2Row],
) -> tuple[ResearchPacketContradictionFollowupPriorityV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketContradictionFollowupPriorityV2Row:
            raise ValueError("rows must contain priority row values")
        _require_hard_flags("row", row)
        if row.contradiction_id in seen:
            raise ValueError("rows must not contain duplicate contradiction_id")
        seen.add(row.contradiction_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _status_count(
    rows: tuple[ResearchPacketContradictionFollowupPriorityV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchPacketContradictionFollowupPriorityV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_score(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO)


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(sum(values, ZERO) / _count(len(values)))


def _hours_between(start: datetime, end: datetime) -> Decimal:
    seconds = _seconds_between(start, end)
    with localcontext(DECIMAL_CONTEXT):
        return (seconds / SECONDS_PER_HOUR).quantize(HOURS_QUANTUM)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(SECONDS_QUANTUM)


def _window_score(age_or_seconds: Decimal, window: Decimal) -> Decimal:
    if age_or_seconds >= window:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return ((window - age_or_seconds) / window).quantize(SCORE_QUANTUM)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
        if ratio >= ONE:
            return ONE
        return ratio.quantize(SCORE_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value)


def _q(value: Decimal) -> Decimal:
    try:
        return value.quantize(SCORE_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("score must use six decimal places") from exc


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_whole_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value.to_integral_value()


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(SCORE_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must use six decimal places") from exc


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or len(value) == 0:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_member(field_name, reason_code, allowed)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    deterministic = tuple(reason_code for reason_code in allowed if reason_code in seen)
    if value != deterministic:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload field in {label}")
            _reject_unsafe_public_payload(f"{label}.{key}", child)
        return
    if type(value) in (list, tuple):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", child)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"unsafe public payload value in {label}")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{label} must not use float values")
    raise ValueError(f"{label} is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _row_public_payload_without_digest(
    row: ResearchPacketContradictionFollowupPriorityV2Row,
) -> dict[str, object]:
    return {
        "priority_rank": _decimal_payload(row.priority_rank),
        "packet_id": row.packet_id,
        "event_id": row.event_id,
        "market_id": row.market_id,
        "contradiction_id": row.contradiction_id,
        "source_family": row.source_family,
        "source_family_count": _decimal_payload(row.source_family_count),
        "independent_source_family_count": _decimal_payload(
            row.independent_source_family_count,
        ),
        "contradiction_observed_at": _datetime_payload(row.contradiction_observed_at),
        "evidence_age_hours": _decimal_payload(row.evidence_age_hours),
        "recency_score": _decimal_payload(row.recency_score),
        "contradiction_severity_score": _decimal_payload(
            row.contradiction_severity_score,
        ),
        "resolution_rule_sensitivity_score": _decimal_payload(
            row.resolution_rule_sensitivity_score,
        ),
        "market_close_at": _datetime_payload(row.market_close_at),
        "seconds_until_market_close": _decimal_payload(row.seconds_until_market_close),
        "market_close_urgency_score": _decimal_payload(row.market_close_urgency_score),
        "source_family_independence_score": _decimal_payload(
            row.source_family_independence_score,
        ),
        "followup_priority_score": _decimal_payload(row.followup_priority_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(
    row: ResearchPacketContradictionFollowupPriorityV2Row,
) -> dict[str, object]:
    payload = _row_public_payload_without_digest(row)
    payload_with_digest: dict[str, object] = {}
    for field_name in ROW_PUBLIC_FIELDS:
        if field_name == "derived_validation_digest":
            payload_with_digest[field_name] = row.derived_validation_digest
        else:
            payload_with_digest[field_name] = payload[field_name]
    return payload_with_digest


def _report_public_payload_without_digest(
    report: ResearchPacketContradictionFollowupPriorityV2Report,
) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _decimal_payload(report.input_count),
        "priority_count": _decimal_payload(report.priority_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "watch_count": _decimal_payload(report.watch_count),
        "clear_count": _decimal_payload(report.clear_count),
        "source_family_independence_count": _decimal_payload(
            report.source_family_independence_count,
        ),
        "recent_contradiction_count": _decimal_payload(
            report.recent_contradiction_count,
        ),
        "severe_contradiction_count": _decimal_payload(
            report.severe_contradiction_count,
        ),
        "rule_sensitive_count": _decimal_payload(report.rule_sensitive_count),
        "market_close_urgent_count": _decimal_payload(
            report.market_close_urgent_count,
        ),
        "max_priority_score": _decimal_payload(report.max_priority_score),
        "average_priority_score": _decimal_payload(report.average_priority_score),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_public_payload(
    report: ResearchPacketContradictionFollowupPriorityV2Report,
) -> dict[str, object]:
    payload = _report_public_payload_without_digest(report)
    payload_with_digest: dict[str, object] = {}
    for field_name in REPORT_PUBLIC_FIELDS:
        if field_name == "derived_validation_digest":
            payload_with_digest[field_name] = report.derived_validation_digest
        else:
            payload_with_digest[field_name] = payload[field_name]
    return payload_with_digest


def _row_derived_validation_digest(
    row: ResearchPacketContradictionFollowupPriorityV2Row,
) -> str:
    payload = _row_public_payload_without_digest(row)
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in ROW_PUBLIC_FIELDS_WITHOUT_DIGEST
    )
    return _sha256(("row", *values))


def _report_derived_validation_digest(
    report: ResearchPacketContradictionFollowupPriorityV2Report,
) -> str:
    payload = _report_public_payload_without_digest(report)
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST
    )
    return _sha256(("report", *values))


def _sha256(parts: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x1f")
    return digest.hexdigest()


def _digest_payload_value(value: object) -> str:
    if type(value) is dict:
        return "{" + "|".join(
            f"{key}:{_digest_payload_value(child)}" for key, child in value.items()
        ) + "}"
    if type(value) is list:
        return "[" + ",".join(_digest_payload_value(child) for child in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    return str(value)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload value must be finite")
    return format(value, "f")


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    return value.lower()


def _validate_row(row: ResearchPacketContradictionFollowupPriorityV2Row) -> None:
    expected_independence = _ratio_capped(
        row.independent_source_family_count,
        row.source_family_count,
    )
    if row.source_family_independence_score != expected_independence:
        raise ValueError("source_family_independence_score must match source counts")
    expected_score = _followup_priority_score(
        source_family_independence_score=row.source_family_independence_score,
        recency_score=row.recency_score,
        contradiction_severity_score=row.contradiction_severity_score,
        resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
        market_close_urgency_score=row.market_close_urgency_score,
    )
    if row.followup_priority_score != expected_score:
        raise ValueError("followup_priority_score must match row scores")
    status_reasons = {
        "clear": CLEAR_REASON,
        "watch": WATCH_REASON,
        "blocked": BLOCKED_REASON,
    }
    if status_reasons[row.status] not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")
    if sum(1 for reason in status_reasons.values() if reason in row.reason_codes) != 1:
        raise ValueError("reason_codes must include exactly one status reason")


def _validate_report(report: ResearchPacketContradictionFollowupPriorityV2Report) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.priority_count != _count(sum(1 for row in rows if row.status != "clear")):
        raise ValueError("priority_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.clear_count != _status_count(rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.source_family_independence_count != _reason_count(
        rows,
        SOURCE_FAMILY_INDEPENDENT_REASON,
    ):
        raise ValueError("source_family_independence_count must match rows")
    if report.recent_contradiction_count != _reason_count(
        rows,
        RECENT_CONTRADICTION_REASON,
    ):
        raise ValueError("recent_contradiction_count must match rows")
    if report.severe_contradiction_count != _reason_count(
        rows,
        SEVERE_CONTRADICTION_REASON,
    ):
        raise ValueError("severe_contradiction_count must match rows")
    if report.rule_sensitive_count != _reason_count(rows, RULE_SENSITIVE_REASON):
        raise ValueError("rule_sensitive_count must match rows")
    if report.market_close_urgent_count != _reason_count(
        rows,
        MARKET_CLOSE_URGENT_REASON,
    ):
        raise ValueError("market_close_urgent_count must match rows")
    if report.max_priority_score != _max_score(
        tuple(row.followup_priority_score for row in rows),
    ):
        raise ValueError("max_priority_score must match rows")
    if report.average_priority_score != _average_score(
        tuple(row.followup_priority_score for row in rows),
    ):
        raise ValueError("average_priority_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_payload_fields("payload", payload, REPORT_PUBLIC_FIELDS)
    _require_canonical_datetime_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    _require_member("status", payload["status"], STATUSES)
    for field_name in (
        "input_count",
        "priority_count",
        "blocked_count",
        "watch_count",
        "clear_count",
        "source_family_independence_count",
        "recent_contradiction_count",
        "severe_contradiction_count",
        "rule_sensitive_count",
        "market_close_urgent_count",
        "max_priority_score",
        "average_priority_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    _validate_public_rows(payload["rows"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest")
    if provided_digest != _derived_validation_digest_from_payload(
        "report",
        without_digest,
        REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")
    _canonical_payload_value(payload)


def _validate_public_rows(rows_value: object) -> None:
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row in rows_value:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        _require_payload_fields("row", row, ROW_PUBLIC_FIELDS)
        for field_name in ROW_PUBLIC_FIELDS:
            value = row[field_name]
            if field_name in (
                "priority_rank",
                "source_family_count",
                "independent_source_family_count",
                "evidence_age_hours",
                "recency_score",
                "contradiction_severity_score",
                "resolution_rule_sensitivity_score",
                "seconds_until_market_close",
                "market_close_urgency_score",
                "source_family_independence_score",
                "followup_priority_score",
            ):
                _require_decimal_payload_string(field_name, value)
            elif field_name in ("contradiction_observed_at", "market_close_at"):
                _require_canonical_datetime_string(field_name, value)
            elif field_name == "status":
                _require_member(field_name, value, ROW_STATUSES)
            elif field_name == "reason_codes":
                _normalize_public_reason_codes(field_name, value, ROW_REASON_CODES)
            elif field_name == "derived_validation_digest":
                _normalize_sha256(field_name, value)
            elif field_name in ("paper_only", "report_only", "readonly"):
                continue
            else:
                _require_canonical_string(field_name, value)
        _require_hard_flags("row", _DictFlags(row))
        provided_digest = _normalize_sha256(
            "derived_validation_digest",
            row["derived_validation_digest"],
        )
        without_digest = dict(row)
        without_digest.pop("derived_validation_digest")
        if provided_digest != _derived_validation_digest_from_payload(
            "row",
            without_digest,
            ROW_PUBLIC_FIELDS_WITHOUT_DIGEST,
        ):
            raise ValueError("derived_validation_digest must match payload fields")


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    actual = tuple(payload)
    if actual != expected_fields:
        missing = [field for field in expected_fields if field not in payload]
        if missing:
            raise ValueError(f"{missing[0]} is required")
        extra = [field for field in actual if field not in expected_fields]
        if extra:
            raise ValueError(f"unexpected {label} field: {extra[0]}")
        raise ValueError(f"{label} fields must use deterministic sequence")


def _derived_validation_digest_from_payload(
    label: str,
    payload: dict[str, object],
    fields_without_digest: tuple[str, ...],
) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in fields_without_digest
    )
    return _sha256((label, *values))


def _normalize_public_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list or len(value) == 0:
        raise ValueError(f"{field_name} must be a non-empty list")
    values: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_member(field_name, item, allowed)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        values.append(item)
    deterministic = [reason for reason in allowed if reason in seen]
    if values != deterministic:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(values)


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_canonical_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC")


def _canonical_payload_value(value: Any) -> Any:
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_canonical_string("payload field", key)
            ready[key] = _canonical_payload_value(child)
        return ready
    if type(value) is list:
        return [_canonical_payload_value(child) for child in value]
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float, Decimal):
        raise ValueError("payload value must be a Decimal-derived string")
    raise ValueError("payload value is not JSON serializable")


class _DictFlags:
    def __init__(self, payload: dict[str, object]) -> None:
        self.paper_only = payload.get("paper_only")
        self.report_only = payload.get("report_only")
        self.readonly = payload.get("readonly")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_CONTRADICTION_FOLLOWUP_PRIORITY_V2_CONFIG_VERSION",
    "ResearchPacketContradictionFollowupPriorityV2Config",
    "ResearchPacketContradictionFollowupPriorityV2Input",
    "ResearchPacketContradictionFollowupPriorityV2Report",
    "ResearchPacketContradictionFollowupPriorityV2Row",
    "build_research_packet_contradiction_followup_priority_v2_report",
    "research_packet_contradiction_followup_priority_v2_payload",
)
