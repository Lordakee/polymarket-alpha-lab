"""Pure Phase 1 breaking-news source triage report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any


DEFAULT_RESEARCH_PACKET_BREAKING_NEWS_SOURCE_TRIAGE_V2_CONFIG_VERSION = (
    "research-packet-breaking-news-source-triage-v2-v0"
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

UNOFFICIAL_SOURCE_WEIGHT = Decimal("0.200000")
SOURCE_AGE_WEIGHT = Decimal("0.150000")
CORROBORATION_WEIGHT = Decimal("0.150000")
CONTRADICTION_WEIGHT = Decimal("0.200000")
MARKET_MOVE_WEIGHT = Decimal("0.150000")
CLOSE_URGENCY_WEIGHT = Decimal("0.150000")

SOURCE_KINDS = ("official", "unofficial")
STATUSES = ("pass", "watch", "blocked")
FOLLOW_UP_PRIORITIES = {
    "pass": "routine",
    "watch": "elevated",
    "blocked": "immediate",
}
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

NO_INPUTS_REASON = "breaking_news_source_triage_no_inputs"
PASS_STATUS_REASON = "breaking_news_source_triage_status_pass"
WATCH_STATUS_REASON = "breaking_news_source_triage_status_watch"
BLOCKED_STATUS_REASON = "breaking_news_source_triage_status_blocked"
UNOFFICIAL_SOURCE_REASON = "breaking_news_source_unofficial"
STALE_SOURCE_REASON = "breaking_news_source_stale"
WEAK_CORROBORATION_REASON = "breaking_news_corroboration_weak"
CONTRADICTION_ELEVATED_REASON = "breaking_news_contradiction_elevated"
CONTRADICTION_HIGH_REASON = "breaking_news_contradiction_high"
MARKET_PROBABILITY_MOVE_LARGE_REASON = (
    "breaking_news_market_probability_move_large"
)
MARKET_CLOSE_URGENT_REASON = "breaking_news_market_close_urgent"

REASON_CODES = (
    NO_INPUTS_REASON,
    PASS_STATUS_REASON,
    WATCH_STATUS_REASON,
    BLOCKED_STATUS_REASON,
    UNOFFICIAL_SOURCE_REASON,
    STALE_SOURCE_REASON,
    WEAK_CORROBORATION_REASON,
    CONTRADICTION_ELEVATED_REASON,
    CONTRADICTION_HIGH_REASON,
    MARKET_PROBABILITY_MOVE_LARGE_REASON,
    MARKET_CLOSE_URGENT_REASON,
)
TRIAGE_REASON_SEQUENCE = REASON_CODES[4:]


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("per", "sist"),
    _join_parts("sign", "ing"),
    _join_parts("muta", "tion"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("tra", "de"),
)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_BREAKING_NEWS_SOURCE_TRIAGE_V2_CONFIG_VERSION",
    "FOLLOW_UP_PRIORITIES",
    "REASON_CODES",
    "ResearchPacketBreakingNewsSourceTriageV2Config",
    "ResearchPacketBreakingNewsSourceTriageV2Input",
    "ResearchPacketBreakingNewsSourceTriageV2Report",
    "ResearchPacketBreakingNewsSourceTriageV2Row",
    "SOURCE_KINDS",
    "STATUSES",
    "build_research_packet_breaking_news_source_triage_v2_report",
    "research_packet_breaking_news_source_triage_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketBreakingNewsSourceTriageV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_BREAKING_NEWS_SOURCE_TRIAGE_V2_CONFIG_VERSION
    )
    fresh_source_age_seconds: Decimal = Decimal("1800.000000")
    stale_source_age_seconds: Decimal = Decimal("7200.000000")
    min_corroboration_count: Decimal = Decimal("2.000000")
    high_contradiction_threshold: Decimal = Decimal("0.750000")
    large_market_probability_move_threshold: Decimal = Decimal("0.050000")
    urgent_market_close_horizon_seconds: Decimal = Decimal("3600.000000")
    safe_market_close_horizon_seconds: Decimal = Decimal("86400.000000")
    blocked_priority_score: Decimal = Decimal("0.650000")
    watch_priority_score: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketBreakingNewsSourceTriageV2Config:
            raise ValueError(
                "config must be a ResearchPacketBreakingNewsSourceTriageV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_BREAKING_NEWS_SOURCE_TRIAGE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
            "urgent_market_close_horizon_seconds",
            "safe_market_close_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_corroboration_count",
            _normalize_positive_count(
                "min_corroboration_count",
                self.min_corroboration_count,
            ),
        )
        for field_name in (
            "high_contradiction_threshold",
            "large_market_probability_move_threshold",
            "blocked_priority_score",
            "watch_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.fresh_source_age_seconds >= self.stale_source_age_seconds:
            raise ValueError("fresh_source_age_seconds must be below stale_source_age_seconds")
        if (
            self.urgent_market_close_horizon_seconds
            >= self.safe_market_close_horizon_seconds
        ):
            raise ValueError(
                "urgent_market_close_horizon_seconds must be below "
                "safe_market_close_horizon_seconds",
            )
        if self.large_market_probability_move_threshold == ZERO:
            raise ValueError("large_market_probability_move_threshold must be positive")
        if self.watch_priority_score >= self.blocked_priority_score:
            raise ValueError("watch_priority_score must be below blocked_priority_score")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchPacketBreakingNewsSourceTriageV2Input:
    packet_ref: str
    question_ref: str
    source_ref: str
    source_kind: str
    source_age_seconds: Decimal
    corroboration_count: Decimal
    contradiction_risk_score: Decimal
    market_probability_move_abs: Decimal
    market_close_horizon_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketBreakingNewsSourceTriageV2Input:
            raise ValueError(
                "subject must be a ResearchPacketBreakingNewsSourceTriageV2Input",
            )
        for field_name in ("packet_ref", "question_ref", "source_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        _require_choice("source_kind", self.source_kind, SOURCE_KINDS)
        for field_name in ("source_age_seconds", "market_close_horizon_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _normalize_nonnegative_count(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        for field_name in ("contradiction_risk_score", "market_probability_move_abs"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("breaking news source triage input", asdict(self))


@dataclass(frozen=True)
class ResearchPacketBreakingNewsSourceTriageV2Row:
    packet_ref: str
    question_ref: str
    source_ref: str
    source_kind: str
    priority_rank: Decimal
    priority_score: Decimal
    unofficial_source_score: Decimal
    source_age_score: Decimal
    corroboration_gap_score: Decimal
    contradiction_risk_score: Decimal
    market_probability_move_score: Decimal
    close_urgency_score: Decimal
    source_age_seconds: Decimal
    corroboration_count: Decimal
    market_probability_move_abs: Decimal
    market_close_horizon_seconds: Decimal
    triage_status: str
    recommended_follow_up_priority: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketBreakingNewsSourceTriageV2Row:
            raise ValueError("row must be a ResearchPacketBreakingNewsSourceTriageV2Row")
        for field_name in ("packet_ref", "question_ref", "source_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        _require_choice("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "priority_score",
            "unofficial_source_score",
            "source_age_score",
            "corroboration_gap_score",
            "contradiction_risk_score",
            "market_probability_move_score",
            "close_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_seconds",
            "market_probability_move_abs",
            "market_close_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _normalize_nonnegative_count("corroboration_count", self.corroboration_count),
        )
        _require_choice("triage_status", self.triage_status, STATUSES)
        _require_choice(
            "recommended_follow_up_priority",
            self.recommended_follow_up_priority,
            tuple(FOLLOW_UP_PRIORITIES.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("breaking news source triage row", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(self.derived_validation_digest),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketBreakingNewsSourceTriageV2Report:
    config_version: str
    report_status: str
    recommended_follow_up_priority: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    official_source_count: Decimal
    unofficial_source_count: Decimal
    stale_source_count: Decimal
    weak_corroboration_count: Decimal
    contradiction_risk_count: Decimal
    high_contradiction_risk_count: Decimal
    large_market_probability_move_count: Decimal
    market_close_urgent_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketBreakingNewsSourceTriageV2Report:
            raise ValueError(
                "report must be a ResearchPacketBreakingNewsSourceTriageV2Report",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_BREAKING_NEWS_SOURCE_TRIAGE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_choice("report_status", self.report_status, STATUSES)
        _require_choice(
            "recommended_follow_up_priority",
            self.recommended_follow_up_priority,
            tuple(FOLLOW_UP_PRIORITIES.values()),
        )
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "official_source_count",
            "unofficial_source_count",
            "stale_source_count",
            "weak_corroboration_count",
            "contradiction_risk_count",
            "high_contradiction_risk_count",
            "large_market_probability_move_count",
            "market_close_urgent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_probability("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("breaking news source triage report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(self.derived_validation_digest),
            )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("breaking news source triage payload", payload)
        if type(payload) is not dict:
            raise ValueError("breaking news source triage payload must be an object")
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> ResearchPacketBreakingNewsSourceTriageV2Report:
        _reject_unsafe_public_payload("breaking news source triage payload", payload)
        payload_dict = _payload_dict("breaking news source triage payload", payload)
        _require_payload_fields(payload_dict, _REPORT_PAYLOAD_FIELDS)
        rows_value = payload_dict["rows"]
        if not isinstance(rows_value, list):
            raise ValueError("rows must be a list")
        rows = tuple(_row_from_payload(item) for item in rows_value)
        return cls(
            config_version=_payload_string("config_version", payload_dict["config_version"]),
            report_status=_payload_string("report_status", payload_dict["report_status"]),
            recommended_follow_up_priority=_payload_string(
                "recommended_follow_up_priority",
                payload_dict["recommended_follow_up_priority"],
            ),
            input_count=_decimal_from_payload("input_count", payload_dict["input_count"]),
            blocked_count=_decimal_from_payload(
                "blocked_count",
                payload_dict["blocked_count"],
            ),
            watch_count=_decimal_from_payload("watch_count", payload_dict["watch_count"]),
            pass_count=_decimal_from_payload("pass_count", payload_dict["pass_count"]),
            official_source_count=_decimal_from_payload(
                "official_source_count",
                payload_dict["official_source_count"],
            ),
            unofficial_source_count=_decimal_from_payload(
                "unofficial_source_count",
                payload_dict["unofficial_source_count"],
            ),
            stale_source_count=_decimal_from_payload(
                "stale_source_count",
                payload_dict["stale_source_count"],
            ),
            weak_corroboration_count=_decimal_from_payload(
                "weak_corroboration_count",
                payload_dict["weak_corroboration_count"],
            ),
            contradiction_risk_count=_decimal_from_payload(
                "contradiction_risk_count",
                payload_dict["contradiction_risk_count"],
            ),
            high_contradiction_risk_count=_decimal_from_payload(
                "high_contradiction_risk_count",
                payload_dict["high_contradiction_risk_count"],
            ),
            large_market_probability_move_count=_decimal_from_payload(
                "large_market_probability_move_count",
                payload_dict["large_market_probability_move_count"],
            ),
            market_close_urgent_count=_decimal_from_payload(
                "market_close_urgent_count",
                payload_dict["market_close_urgent_count"],
            ),
            highest_priority_score=_decimal_from_payload(
                "highest_priority_score",
                payload_dict["highest_priority_score"],
            ),
            rows=rows,
            reason_codes=_string_tuple_from_payload(
                "reason_codes",
                payload_dict["reason_codes"],
            ),
            derived_validation_digest=_payload_string(
                "derived_validation_digest",
                payload_dict["derived_validation_digest"],
            ),
            paper_only=_payload_bool("paper_only", payload_dict["paper_only"]),
            report_only=_payload_bool("report_only", payload_dict["report_only"]),
            readonly=_payload_bool("readonly", payload_dict["readonly"]),
        )


_REPORT_PAYLOAD_FIELDS = (
    "config_version",
    "report_status",
    "recommended_follow_up_priority",
    "input_count",
    "blocked_count",
    "watch_count",
    "pass_count",
    "official_source_count",
    "unofficial_source_count",
    "stale_source_count",
    "weak_corroboration_count",
    "contradiction_risk_count",
    "high_contradiction_risk_count",
    "large_market_probability_move_count",
    "market_close_urgent_count",
    "highest_priority_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "source_ref",
    "source_kind",
    "priority_rank",
    "priority_score",
    "unofficial_source_score",
    "source_age_score",
    "corroboration_gap_score",
    "contradiction_risk_score",
    "market_probability_move_score",
    "close_urgency_score",
    "source_age_seconds",
    "corroboration_count",
    "market_probability_move_abs",
    "market_close_horizon_seconds",
    "triage_status",
    "recommended_follow_up_priority",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def build_research_packet_breaking_news_source_triage_v2_report(
    rows: object,
    *,
    config: ResearchPacketBreakingNewsSourceTriageV2Config | None = None,
) -> ResearchPacketBreakingNewsSourceTriageV2Report:
    if config is None:
        config = ResearchPacketBreakingNewsSourceTriageV2Config()
    if type(config) is not ResearchPacketBreakingNewsSourceTriageV2Config:
        raise ValueError(
            "config must be a ResearchPacketBreakingNewsSourceTriageV2Config",
        )
    _require_hard_flags(config)
    source_rows = _normalize_input_rows(rows)
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, row in enumerate(
            sorted(
                (_unranked_row(item, config=config) for item in source_rows),
                key=_row_sort_key,
            ),
        )
    )
    report_status = _report_status(ranked_rows)
    return ResearchPacketBreakingNewsSourceTriageV2Report(
        config_version=config.config_version,
        report_status=report_status,
        recommended_follow_up_priority=FOLLOW_UP_PRIORITIES[report_status],
        input_count=_count(len(source_rows)),
        blocked_count=_status_count(ranked_rows, "blocked"),
        watch_count=_status_count(ranked_rows, "watch"),
        pass_count=_status_count(ranked_rows, "pass"),
        official_source_count=_source_kind_count(ranked_rows, "official"),
        unofficial_source_count=_source_kind_count(ranked_rows, "unofficial"),
        stale_source_count=_reason_count(ranked_rows, STALE_SOURCE_REASON),
        weak_corroboration_count=_reason_count(
            ranked_rows,
            WEAK_CORROBORATION_REASON,
        ),
        contradiction_risk_count=_count(
            sum(1 for row in ranked_rows if row.contradiction_risk_score > ZERO),
        ),
        high_contradiction_risk_count=_reason_count(
            ranked_rows,
            CONTRADICTION_HIGH_REASON,
        ),
        large_market_probability_move_count=_reason_count(
            ranked_rows,
            MARKET_PROBABILITY_MOVE_LARGE_REASON,
        ),
        market_close_urgent_count=_reason_count(
            ranked_rows,
            MARKET_CLOSE_URGENT_REASON,
        ),
        highest_priority_score=_max_priority_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_packet_breaking_news_source_triage_v2_payload(
    report: ResearchPacketBreakingNewsSourceTriageV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketBreakingNewsSourceTriageV2Report:
        raise ValueError("report must be a ResearchPacketBreakingNewsSourceTriageV2Report")
    _require_hard_flags(report)
    _validate_report(report)
    return report.payload


def _unranked_row(
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
    *,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> ResearchPacketBreakingNewsSourceTriageV2Row:
    unofficial_source_score = _unofficial_source_score(subject)
    source_age_score = _source_age_score(subject, config)
    corroboration_gap_score = _corroboration_gap_score(subject, config)
    market_probability_move_score = _market_probability_move_score(subject, config)
    close_urgency_score = _close_urgency_score(subject, config)
    priority_score = _priority_score(
        unofficial_source_score=unofficial_source_score,
        source_age_score=source_age_score,
        corroboration_gap_score=corroboration_gap_score,
        contradiction_risk_score=subject.contradiction_risk_score,
        market_probability_move_score=market_probability_move_score,
        close_urgency_score=close_urgency_score,
    )
    triage_status = _triage_status(priority_score, config)
    return ResearchPacketBreakingNewsSourceTriageV2Row(
        packet_ref=subject.packet_ref,
        question_ref=subject.question_ref,
        source_ref=subject.source_ref,
        source_kind=subject.source_kind,
        priority_rank=ONE,
        priority_score=priority_score,
        unofficial_source_score=unofficial_source_score,
        source_age_score=source_age_score,
        corroboration_gap_score=corroboration_gap_score,
        contradiction_risk_score=subject.contradiction_risk_score,
        market_probability_move_score=market_probability_move_score,
        close_urgency_score=close_urgency_score,
        source_age_seconds=subject.source_age_seconds,
        corroboration_count=subject.corroboration_count,
        market_probability_move_abs=subject.market_probability_move_abs,
        market_close_horizon_seconds=subject.market_close_horizon_seconds,
        triage_status=triage_status,
        recommended_follow_up_priority=FOLLOW_UP_PRIORITIES[triage_status],
        reason_codes=_row_reason_codes(subject=subject, config=config),
    )


def _ranked_row(
    row: ResearchPacketBreakingNewsSourceTriageV2Row,
    *,
    rank: int,
) -> ResearchPacketBreakingNewsSourceTriageV2Row:
    return replace(row, priority_rank=_count(rank), derived_validation_digest="")


def _row_sort_key(
    row: ResearchPacketBreakingNewsSourceTriageV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.triage_status],
        -row.priority_score,
        row.packet_ref,
        row.question_ref,
        row.source_ref,
    )


def _unofficial_source_score(
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
) -> Decimal:
    if subject.source_kind == "unofficial":
        return ONE
    return ZERO


def _source_age_score(
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> Decimal:
    if subject.source_age_seconds <= config.fresh_source_age_seconds:
        return ZERO
    if subject.source_age_seconds >= config.stale_source_age_seconds:
        return ONE
    elapsed = subject.source_age_seconds - config.fresh_source_age_seconds
    span = config.stale_source_age_seconds - config.fresh_source_age_seconds
    return _clamp_probability(_safe_ratio(elapsed, span))


def _corroboration_gap_score(
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> Decimal:
    if subject.corroboration_count >= config.min_corroboration_count:
        return ZERO
    gap = config.min_corroboration_count - subject.corroboration_count
    return _clamp_probability(_safe_ratio(gap, config.min_corroboration_count))


def _market_probability_move_score(
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> Decimal:
    return _clamp_probability(
        _safe_ratio(
            subject.market_probability_move_abs,
            config.large_market_probability_move_threshold,
        ),
    )


def _close_urgency_score(
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> Decimal:
    if subject.market_close_horizon_seconds <= config.urgent_market_close_horizon_seconds:
        return ONE
    if subject.market_close_horizon_seconds >= config.safe_market_close_horizon_seconds:
        return ZERO
    remaining = (
        config.safe_market_close_horizon_seconds
        - subject.market_close_horizon_seconds
    )
    span = (
        config.safe_market_close_horizon_seconds
        - config.urgent_market_close_horizon_seconds
    )
    return _clamp_probability(_safe_ratio(remaining, span))


def _priority_score(
    *,
    unofficial_source_score: Decimal,
    source_age_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_risk_score: Decimal,
    market_probability_move_score: Decimal,
    close_urgency_score: Decimal,
) -> Decimal:
    return _clamp_probability(
        (unofficial_source_score * UNOFFICIAL_SOURCE_WEIGHT)
        + (source_age_score * SOURCE_AGE_WEIGHT)
        + (corroboration_gap_score * CORROBORATION_WEIGHT)
        + (contradiction_risk_score * CONTRADICTION_WEIGHT)
        + (market_probability_move_score * MARKET_MOVE_WEIGHT)
        + (close_urgency_score * CLOSE_URGENCY_WEIGHT),
    )


def _triage_status(
    priority_score: Decimal,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> str:
    if priority_score >= config.blocked_priority_score:
        return "blocked"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    subject: ResearchPacketBreakingNewsSourceTriageV2Input,
    config: ResearchPacketBreakingNewsSourceTriageV2Config,
) -> tuple[str, ...]:
    priority_score = _priority_score(
        unofficial_source_score=_unofficial_source_score(subject),
        source_age_score=_source_age_score(subject, config),
        corroboration_gap_score=_corroboration_gap_score(subject, config),
        contradiction_risk_score=subject.contradiction_risk_score,
        market_probability_move_score=_market_probability_move_score(subject, config),
        close_urgency_score=_close_urgency_score(subject, config),
    )
    triage_status = _triage_status(priority_score, config)
    codes = [f"breaking_news_source_triage_status_{triage_status}"]
    if subject.source_kind == "unofficial":
        codes.append(UNOFFICIAL_SOURCE_REASON)
    if subject.source_age_seconds > config.fresh_source_age_seconds:
        codes.append(STALE_SOURCE_REASON)
    if subject.corroboration_count < config.min_corroboration_count:
        codes.append(WEAK_CORROBORATION_REASON)
    if subject.contradiction_risk_score >= config.high_contradiction_threshold:
        codes.append(CONTRADICTION_HIGH_REASON)
    elif subject.contradiction_risk_score > ZERO:
        codes.append(CONTRADICTION_ELEVATED_REASON)
    if (
        subject.market_probability_move_abs
        >= config.large_market_probability_move_threshold
    ):
        codes.append(MARKET_PROBABILITY_MOVE_LARGE_REASON)
    if subject.market_close_horizon_seconds <= config.urgent_market_close_horizon_seconds:
        codes.append(MARKET_CLOSE_URGENT_REASON)
    return tuple(codes)


def _row_reason_codes_from_row(
    row: ResearchPacketBreakingNewsSourceTriageV2Row,
) -> tuple[str, ...]:
    codes = [f"breaking_news_source_triage_status_{row.triage_status}"]
    if row.source_kind == "unofficial":
        codes.append(UNOFFICIAL_SOURCE_REASON)
    if row.source_age_score > ZERO:
        codes.append(STALE_SOURCE_REASON)
    if row.corroboration_gap_score > ZERO:
        codes.append(WEAK_CORROBORATION_REASON)
    if row.contradiction_risk_score >= Decimal("0.750000"):
        codes.append(CONTRADICTION_HIGH_REASON)
    elif row.contradiction_risk_score > ZERO:
        codes.append(CONTRADICTION_ELEVATED_REASON)
    if row.market_probability_move_score >= ONE:
        codes.append(MARKET_PROBABILITY_MOVE_LARGE_REASON)
    if row.close_urgency_score >= ONE:
        codes.append(MARKET_CLOSE_URGENT_REASON)
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _report_status(rows)
    codes = [f"breaking_news_source_triage_status_{status}"]
    present = {code for row in rows for code in row.reason_codes}
    for code in TRIAGE_REASON_SEQUENCE:
        if code in present:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.triage_status == "blocked" for row in rows):
        return "blocked"
    if any(row.triage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.triage_status == status))


def _source_kind_count(
    rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...],
    source_kind: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.source_kind == source_kind))


def _reason_count(
    rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_priority_score(
    rows: tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _validate_row(row: ResearchPacketBreakingNewsSourceTriageV2Row) -> None:
    expected_priority_score = _priority_score(
        unofficial_source_score=row.unofficial_source_score,
        source_age_score=row.source_age_score,
        corroboration_gap_score=row.corroboration_gap_score,
        contradiction_risk_score=row.contradiction_risk_score,
        market_probability_move_score=row.market_probability_move_score,
        close_urgency_score=row.close_urgency_score,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match breaking news source drivers")
    if row.triage_status == "blocked":
        expected_status = "blocked"
    elif row.triage_status == "watch":
        expected_status = "watch"
    else:
        expected_status = "pass"
    if row.triage_status != expected_status:
        raise ValueError("triage_status must match priority_score")
    if row.recommended_follow_up_priority != FOLLOW_UP_PRIORITIES[row.triage_status]:
        raise ValueError("recommended_follow_up_priority must match triage_status")
    if row.reason_codes != _row_reason_codes_from_row(row):
        raise ValueError("reason_codes must match breaking news source drivers")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchPacketBreakingNewsSourceTriageV2Report) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if (
        report.recommended_follow_up_priority
        != FOLLOW_UP_PRIORITIES[report.report_status]
    ):
        raise ValueError("recommended_follow_up_priority must match report_status")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.official_source_count != _source_kind_count(report.rows, "official"):
        raise ValueError("official_source_count must match rows")
    if report.unofficial_source_count != _source_kind_count(report.rows, "unofficial"):
        raise ValueError("unofficial_source_count must match rows")
    if (
        report.official_source_count + report.unofficial_source_count
        != report.input_count
    ):
        raise ValueError("source kind counts must match input_count")
    if report.stale_source_count != _reason_count(report.rows, STALE_SOURCE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.weak_corroboration_count != _reason_count(
        report.rows,
        WEAK_CORROBORATION_REASON,
    ):
        raise ValueError("weak_corroboration_count must match rows")
    if report.contradiction_risk_count != _count(
        sum(1 for row in report.rows if row.contradiction_risk_score > ZERO),
    ):
        raise ValueError("contradiction_risk_count must match rows")
    if report.high_contradiction_risk_count != _reason_count(
        report.rows,
        CONTRADICTION_HIGH_REASON,
    ):
        raise ValueError("high_contradiction_risk_count must match rows")
    if report.large_market_probability_move_count != _reason_count(
        report.rows,
        MARKET_PROBABILITY_MOVE_LARGE_REASON,
    ):
        raise ValueError("large_market_probability_move_count must match rows")
    if report.market_close_urgent_count != _reason_count(
        report.rows,
        MARKET_CLOSE_URGENT_REASON,
    ):
        raise ValueError("market_close_urgent_count must match rows")
    if report.highest_priority_score != _max_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchPacketBreakingNewsSourceTriageV2Input, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError(
            "rows must be an iterable of ResearchPacketBreakingNewsSourceTriageV2Input",
        )
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketBreakingNewsSourceTriageV2Input:
            raise ValueError(
                "rows must be ResearchPacketBreakingNewsSourceTriageV2Input values",
            )
        _require_hard_flags(row)
        key = (row.packet_ref, row.question_ref, row.source_ref)
        if key in seen:
            raise ValueError("rows must be unique by packet_ref, question_ref, source_ref")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketBreakingNewsSourceTriageV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError(
            "rows must be an iterable of ResearchPacketBreakingNewsSourceTriageV2Row",
        )
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketBreakingNewsSourceTriageV2Row:
            raise ValueError(
                "rows must be ResearchPacketBreakingNewsSourceTriageV2Row values",
            )
        _require_hard_flags(row)
        key = (row.packet_ref, row.question_ref, row.source_ref)
        if key in seen:
            raise ValueError("rows must be unique by packet_ref, question_ref, source_ref")
        seen.add(key)
    expected_ranks = tuple(_count(index + 1) for index in range(len(normalized)))
    actual_ranks = tuple(row.priority_rank for row in normalized)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must match row sequence")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < SCORE_QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _q(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_derived_validation_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest") from exc
    return value


def _normalize_reason_codes(values: object, *, allow_empty: bool) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise ValueError("reason_codes must contain supported reason codes")
    reason_codes = tuple(values)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for code in reason_codes:
        _require_choice("reason_codes", code, REASON_CODES)
    expected = tuple(code for code in REASON_CODES if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _count(value: int) -> Decimal:
    return _q(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(numerator / denominator)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _q(value)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _mentions_unsafe_public_term(value):
        raise ValueError(f"unsafe public payload value in {field_name}: {value}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if hasattr(payload, "__dataclass_fields__") and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _mentions_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str and _mentions_unsafe_public_term(payload):
        raise ValueError(f"unsafe public payload value in {label}: {payload}")
    if type(payload) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")


def _mentions_unsafe_public_term(value: str) -> bool:
    tokens = _public_tokens(value.lower())
    return any(term in tokens for term in UNSAFE_PUBLIC_TERMS)


def _public_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _payload_value(value: Any) -> Any:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        return str(_q(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        _reject_unsafe_public_payload("breaking news source triage payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _payload_dict(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    return value


def _require_payload_fields(payload: dict[str, object], fields: tuple[str, ...]) -> None:
    if tuple(payload.keys()) != fields:
        raise ValueError("payload fields must match public contract")


def _row_from_payload(value: object) -> ResearchPacketBreakingNewsSourceTriageV2Row:
    payload = _payload_dict("row", value)
    _require_payload_fields(payload, _ROW_PAYLOAD_FIELDS)
    return ResearchPacketBreakingNewsSourceTriageV2Row(
        packet_ref=_payload_string("packet_ref", payload["packet_ref"]),
        question_ref=_payload_string("question_ref", payload["question_ref"]),
        source_ref=_payload_string("source_ref", payload["source_ref"]),
        source_kind=_payload_string("source_kind", payload["source_kind"]),
        priority_rank=_decimal_from_payload("priority_rank", payload["priority_rank"]),
        priority_score=_decimal_from_payload("priority_score", payload["priority_score"]),
        unofficial_source_score=_decimal_from_payload(
            "unofficial_source_score",
            payload["unofficial_source_score"],
        ),
        source_age_score=_decimal_from_payload(
            "source_age_score",
            payload["source_age_score"],
        ),
        corroboration_gap_score=_decimal_from_payload(
            "corroboration_gap_score",
            payload["corroboration_gap_score"],
        ),
        contradiction_risk_score=_decimal_from_payload(
            "contradiction_risk_score",
            payload["contradiction_risk_score"],
        ),
        market_probability_move_score=_decimal_from_payload(
            "market_probability_move_score",
            payload["market_probability_move_score"],
        ),
        close_urgency_score=_decimal_from_payload(
            "close_urgency_score",
            payload["close_urgency_score"],
        ),
        source_age_seconds=_decimal_from_payload(
            "source_age_seconds",
            payload["source_age_seconds"],
        ),
        corroboration_count=_decimal_from_payload(
            "corroboration_count",
            payload["corroboration_count"],
        ),
        market_probability_move_abs=_decimal_from_payload(
            "market_probability_move_abs",
            payload["market_probability_move_abs"],
        ),
        market_close_horizon_seconds=_decimal_from_payload(
            "market_close_horizon_seconds",
            payload["market_close_horizon_seconds"],
        ),
        triage_status=_payload_string("triage_status", payload["triage_status"]),
        recommended_follow_up_priority=_payload_string(
            "recommended_follow_up_priority",
            payload["recommended_follow_up_priority"],
        ),
        reason_codes=_string_tuple_from_payload("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal strings")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal strings") from exc
    return _normalize_decimal(field_name, decimal_value)


def _row_derived_validation_digest(
    row: ResearchPacketBreakingNewsSourceTriageV2Row,
) -> str:
    values = asdict(row)
    values.pop("derived_validation_digest", None)
    return hashlib.sha256(_canonical_payload(values).encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchPacketBreakingNewsSourceTriageV2Report,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return hashlib.sha256(_canonical_payload(values).encode("utf-8")).hexdigest()


def _canonical_payload(value: object) -> str:
    if type(value) is Decimal:
        return f"decimal:{_q(value)}"
    if type(value) is str:
        return f"string:{len(value)}:{value}"
    if type(value) is bool:
        return f"bool:{value}"
    if value is None:
        return "none"
    if isinstance(value, tuple):
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if isinstance(value, list):
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("canonical payload keys must be strings")
            parts.append(f"{_canonical_payload(key)}:{_canonical_payload(value[key])}")
        return "{" + ",".join(parts) + "}"
    raise ValueError("canonical payload value is not supported")
