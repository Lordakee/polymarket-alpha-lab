"""Pure report reducer for research team queue load balance."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_REPORT_CONFIG_VERSION = (
    "research-team-queue-load-balancer-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_team_queue_load_balancer_report_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
PENDING_BLOCK_REASON = f"{REASON_PREFIX}pending_review_block"
PENDING_PRESSURE_REASON = f"{REASON_PREFIX}pending_review_pressure"
URGENCY_BLOCK_REASON = f"{REASON_PREFIX}urgency_block"
URGENCY_WATCH_REASON = f"{REASON_PREFIX}urgency_watch"
EVIDENCE_GAP_BLOCK_REASON = f"{REASON_PREFIX}evidence_gap_block"
EVIDENCE_GAP_REASON = f"{REASON_PREFIX}evidence_gap"
DOMAIN_EXPERTISE_BLOCK_REASON = f"{REASON_PREFIX}domain_expertise_block"
DOMAIN_EXPERTISE_GAP_REASON = f"{REASON_PREFIX}domain_expertise_gap"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    PENDING_BLOCK_REASON,
    URGENCY_BLOCK_REASON,
    EVIDENCE_GAP_BLOCK_REASON,
    DOMAIN_EXPERTISE_BLOCK_REASON,
    PENDING_PRESSURE_REASON,
    URGENCY_WATCH_REASON,
    EVIDENCE_GAP_REASON,
    DOMAIN_EXPERTISE_GAP_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    PENDING_BLOCK_REASON,
    URGENCY_BLOCK_REASON,
    EVIDENCE_GAP_BLOCK_REASON,
    DOMAIN_EXPERTISE_BLOCK_REASON,
    PENDING_PRESSURE_REASON,
    URGENCY_WATCH_REASON,
    EVIDENCE_GAP_REASON,
    DOMAIN_EXPERTISE_GAP_REASON,
    PASS_REASON,
)
BLOCKING_REASON_CODES = (
    PENDING_BLOCK_REASON,
    URGENCY_BLOCK_REASON,
    EVIDENCE_GAP_BLOCK_REASON,
    DOMAIN_EXPERTISE_BLOCK_REASON,
)
NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_research_team_queue_load_balancer",
    STATUS_WATCH: "watch_report_only_research_team_queue_load_balancer",
    STATUS_BLOCK: "block_report_only_research_team_queue_load_balancer",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("live", "_", "trading"),
        _join_parts("wa", "llet"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("sign", "ing"),
        _join_parts("ad", "vice"),
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("se", "cret"),
        _join_parts("po", "sition"),
        _join_parts("tr", "ade"),
        _join_parts("b", "et"),
        _join_parts("sta", "ke"),
        _join_parts("cli", "ent"),
        _join_parts("re", "quests"),
        _join_parts("h", "ttp"),
        _join_parts("so", "cket"),
        _join_parts("sub", "process"),
        _join_parts("path", "lib"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("dur", "able"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("recom", "mend"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_REPORT_CONFIG_VERSION",
    "ResearchTeamQueueLoadBalancerConfig",
    "ResearchTeamQueueLoadBalancerInputRow",
    "ResearchTeamQueueLoadBalancerReasonCodeCount",
    "ResearchTeamQueueLoadBalancerReport",
    "ResearchTeamQueueLoadBalancerReportRow",
    "build_research_team_queue_load_balancer_report",
    "research_team_queue_load_balancer_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_REPORT_CONFIG_VERSION
    max_pass_pending_review_count: Decimal = Decimal("5.000000")
    max_watch_pending_review_count: Decimal = Decimal("12.000000")
    urgency_watch_threshold: Decimal = Decimal("0.700000")
    urgency_block_threshold: Decimal = Decimal("0.900000")
    max_pass_evidence_gap_count: Decimal = Decimal("0.000000")
    max_watch_evidence_gap_count: Decimal = Decimal("2.000000")
    min_pass_domain_expertise_match_score: Decimal = Decimal("0.750000")
    min_block_domain_expertise_match_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerConfig:
            raise TypeError(
                "ResearchTeamQueueLoadBalancerConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerConfig:
            raise ValueError(
                "config must be exactly ResearchTeamQueueLoadBalancerConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "max_pass_pending_review_count",
            "max_watch_pending_review_count",
            "max_pass_evidence_gap_count",
            "max_watch_evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "urgency_watch_threshold",
            "urgency_block_threshold",
            "min_pass_domain_expertise_match_score",
            "min_block_domain_expertise_match_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_pending_review_count > self.max_watch_pending_review_count:
            raise ValueError(
                "max_watch_pending_review_count must be at least "
                "max_pass_pending_review_count",
            )
        if self.urgency_watch_threshold > self.urgency_block_threshold:
            raise ValueError(
                "urgency_block_threshold must be at least urgency_watch_threshold",
            )
        if self.max_pass_evidence_gap_count > self.max_watch_evidence_gap_count:
            raise ValueError(
                "max_watch_evidence_gap_count must be at least "
                "max_pass_evidence_gap_count",
            )
        if (
            self.min_block_domain_expertise_match_score
            > self.min_pass_domain_expertise_match_score
        ):
            raise ValueError(
                "min_pass_domain_expertise_match_score must be at least "
                "min_block_domain_expertise_match_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerInputRow:
    team_key: str
    team_domain: str
    observed_at: datetime
    pending_review_count: Decimal
    urgency_score: Decimal
    evidence_gap_count: Decimal
    domain_expertise_match_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerInputRow:
            raise TypeError(
                "ResearchTeamQueueLoadBalancerInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerInputRow:
            raise ValueError(
                "input row must be exactly ResearchTeamQueueLoadBalancerInputRow",
            )
        _require_public_identifier("team_key", self.team_key)
        _require_public_identifier("team_domain", self.team_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "pending_review_count",
            _require_nonnegative_count_decimal(
                "pending_review_count",
                self.pending_review_count,
            ),
        )
        object.__setattr__(
            self,
            "urgency_score",
            _require_ratio_decimal("urgency_score", self.urgency_score),
        )
        object.__setattr__(
            self,
            "evidence_gap_count",
            _require_nonnegative_count_decimal(
                "evidence_gap_count",
                self.evidence_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "domain_expertise_match_score",
            _require_ratio_decimal(
                "domain_expertise_match_score",
                self.domain_expertise_match_score,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerReportRow:
    team_key: str
    team_domain: str
    team_status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    pending_review_count: Decimal
    urgency_score: Decimal
    evidence_gap_count: Decimal
    domain_expertise_match_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchTeamQueueLoadBalancerConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerReportRow:
            raise TypeError(
                "ResearchTeamQueueLoadBalancerReportRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchTeamQueueLoadBalancerConfig | None,
    ) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerReportRow:
            raise ValueError("row must be exactly ResearchTeamQueueLoadBalancerReportRow")
        _require_public_identifier("team_key", self.team_key)
        _require_public_identifier("team_domain", self.team_domain)
        _require_status("team_status", self.team_status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in ("pending_review_count", "evidence_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("urgency_score", "domain_expertise_match_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerReasonCodeCount:
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerReasonCodeCount:
            raise TypeError(
                "ResearchTeamQueueLoadBalancerReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchTeamQueueLoadBalancerReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerReport:
    generated_at: datetime
    config_version: str
    load_status: str
    next_step: str
    team_count: Decimal
    pass_team_count: Decimal
    watch_team_count: Decimal
    block_team_count: Decimal
    total_pending_review_count: Decimal
    pending_pressure_team_count: Decimal
    urgent_team_count: Decimal
    evidence_gap_team_count: Decimal
    domain_expertise_gap_team_count: Decimal
    average_urgency_score: Decimal
    average_domain_expertise_match_score: Decimal
    max_pending_review_count: Decimal
    max_evidence_gap_count: Decimal
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...]
    reason_code_counts: tuple[ResearchTeamQueueLoadBalancerReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerReport:
            raise TypeError(
                "ResearchTeamQueueLoadBalancerReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerReport:
            raise ValueError("report must be exactly ResearchTeamQueueLoadBalancerReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_status("load_status", self.load_status)
        _require_public_identifier("next_step", self.next_step)
        for field_name in (
            "team_count",
            "pass_team_count",
            "watch_team_count",
            "block_team_count",
            "total_pending_review_count",
            "pending_pressure_team_count",
            "urgent_team_count",
            "evidence_gap_team_count",
            "domain_expertise_gap_team_count",
            "max_pending_review_count",
            "max_evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_urgency_score",
            "average_domain_expertise_match_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_team_queue_load_balancer_report(
    input_rows: list[ResearchTeamQueueLoadBalancerInputRow]
    | tuple[ResearchTeamQueueLoadBalancerInputRow, ...],
    *,
    config: ResearchTeamQueueLoadBalancerConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamQueueLoadBalancerReport:
    cfg = config or ResearchTeamQueueLoadBalancerConfig()
    if type(cfg) is not ResearchTeamQueueLoadBalancerConfig:
        raise ValueError("config must be exactly ResearchTeamQueueLoadBalancerConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    rows = tuple(
        _build_row(input_row, config=cfg, generated_at=generated_at_utc)
        for input_row in normalized_rows
    )
    ranked_rows = _ranked_rows(rows)
    team_count = _count(len(ranked_rows))
    load_status = _report_status(ranked_rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchTeamQueueLoadBalancerReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    return ResearchTeamQueueLoadBalancerReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        load_status=load_status,
        next_step=NEXT_STEPS[load_status],
        team_count=team_count,
        pass_team_count=_status_count(ranked_rows, STATUS_PASS),
        watch_team_count=_status_count(ranked_rows, STATUS_WATCH),
        block_team_count=_status_count(ranked_rows, STATUS_BLOCK),
        total_pending_review_count=_sum_decimal(
            row.pending_review_count for row in ranked_rows
        ),
        pending_pressure_team_count=_reason_team_count(
            ranked_rows,
            PENDING_PRESSURE_REASON,
            PENDING_BLOCK_REASON,
        ),
        urgent_team_count=_reason_team_count(
            ranked_rows,
            URGENCY_WATCH_REASON,
            URGENCY_BLOCK_REASON,
        ),
        evidence_gap_team_count=_reason_team_count(
            ranked_rows,
            EVIDENCE_GAP_REASON,
            EVIDENCE_GAP_BLOCK_REASON,
        ),
        domain_expertise_gap_team_count=_reason_team_count(
            ranked_rows,
            DOMAIN_EXPERTISE_GAP_REASON,
            DOMAIN_EXPERTISE_BLOCK_REASON,
        ),
        average_urgency_score=_ratio(
            _sum_decimal(row.urgency_score for row in ranked_rows),
            team_count,
        ),
        average_domain_expertise_match_score=_ratio(
            _sum_decimal(row.domain_expertise_match_score for row in ranked_rows),
            team_count,
        ),
        max_pending_review_count=max(
            (row.pending_review_count for row in ranked_rows),
            default=ZERO,
        ),
        max_evidence_gap_count=max(
            (row.evidence_gap_count for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_queue_load_balancer_report_payload(
    report: ResearchTeamQueueLoadBalancerReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamQueueLoadBalancerReport:
        raise ValueError("report must be exactly ResearchTeamQueueLoadBalancerReport")
    _require_hard_flags("report", report)
    payload = {
        "payload_kind": "research_team_queue_load_balancer_report",
        **_json_ready(report),
    }
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_payload(payload)
    return payload


def _build_row(
    row: ResearchTeamQueueLoadBalancerInputRow,
    *,
    config: ResearchTeamQueueLoadBalancerConfig,
    generated_at: datetime,
) -> ResearchTeamQueueLoadBalancerReportRow:
    observation_age_seconds = _datetime_delta_seconds(generated_at, row.observed_at)
    reason_codes = _row_reason_codes(
        pending_review_count=row.pending_review_count,
        urgency_score=row.urgency_score,
        evidence_gap_count=row.evidence_gap_count,
        domain_expertise_match_score=row.domain_expertise_match_score,
        config=config,
    )
    return ResearchTeamQueueLoadBalancerReportRow(
        team_key=row.team_key,
        team_domain=row.team_domain,
        team_status=_row_status(reason_codes),
        generated_at=generated_at,
        observed_at=row.observed_at,
        observation_age_seconds=observation_age_seconds,
        pending_review_count=row.pending_review_count,
        urgency_score=row.urgency_score,
        evidence_gap_count=row.evidence_gap_count,
        domain_expertise_match_score=row.domain_expertise_match_score,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchTeamQueueLoadBalancerInputRow]
    | tuple[ResearchTeamQueueLoadBalancerInputRow, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamQueueLoadBalancerInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamQueueLoadBalancerInputRow:
            raise ValueError(
                "input rows must contain ResearchTeamQueueLoadBalancerInputRow",
            )
        _require_hard_flags("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if row.team_key in seen:
            raise ValueError("input rows must not contain duplicate team_key values")
        seen.add(row.team_key)
    return normalized


def _row_reason_codes(
    *,
    pending_review_count: Decimal,
    urgency_score: Decimal,
    evidence_gap_count: Decimal,
    domain_expertise_match_score: Decimal,
    config: ResearchTeamQueueLoadBalancerConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if pending_review_count > config.max_watch_pending_review_count:
        reason_codes.append(PENDING_BLOCK_REASON)
    elif pending_review_count > config.max_pass_pending_review_count:
        reason_codes.append(PENDING_PRESSURE_REASON)
    if urgency_score >= config.urgency_block_threshold:
        reason_codes.append(URGENCY_BLOCK_REASON)
    elif urgency_score >= config.urgency_watch_threshold:
        reason_codes.append(URGENCY_WATCH_REASON)
    if evidence_gap_count > config.max_watch_evidence_gap_count:
        reason_codes.append(EVIDENCE_GAP_BLOCK_REASON)
    elif evidence_gap_count > config.max_pass_evidence_gap_count:
        reason_codes.append(EVIDENCE_GAP_REASON)
    if domain_expertise_match_score < config.min_block_domain_expertise_match_score:
        reason_codes.append(DOMAIN_EXPERTISE_BLOCK_REASON)
    elif domain_expertise_match_score < config.min_pass_domain_expertise_match_score:
        reason_codes.append(DOMAIN_EXPERTISE_GAP_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if any(reason_code in reason_codes for reason_code in BLOCKING_REASON_CODES):
        return STATUS_BLOCK
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.team_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.team_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerReportRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.team_status),
                -_row_severity(row),
                -row.urgency_score,
                -row.pending_review_count,
                row.team_domain,
                row.team_key,
            ),
        ),
    )


def _status_rank(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ZERO
    if status == STATUS_WATCH:
        return ONE
    return TWO


def _row_severity(row: ResearchTeamQueueLoadBalancerReportRow) -> Decimal:
    return _count(sum(reason_code != PASS_REASON for reason_code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.team_status == status for row in rows))


def _reason_team_count(
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...],
    *reason_codes: str,
) -> Decimal:
    return _count(
        sum(any(reason_code in row.reason_codes for reason_code in reason_codes) for row in rows),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            team_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchTeamQueueLoadBalancerReportRow,
    *,
    config: ResearchTeamQueueLoadBalancerConfig | None,
) -> None:
    cfg = config or ResearchTeamQueueLoadBalancerConfig()
    if type(cfg) is not ResearchTeamQueueLoadBalancerConfig:
        raise ValueError("validation_config must be ResearchTeamQueueLoadBalancerConfig")
    if row.observed_at > row.generated_at:
        raise ValueError("observed_at must be on or before generated_at")
    if row.observation_age_seconds != _datetime_delta_seconds(
        row.generated_at,
        row.observed_at,
    ):
        raise ValueError("observation_age_seconds must match generated_at and observed_at")
    expected_reasons = _row_reason_codes(
        pending_review_count=row.pending_review_count,
        urgency_score=row.urgency_score,
        evidence_gap_count=row.evidence_gap_count,
        domain_expertise_match_score=row.domain_expertise_match_score,
        config=cfg,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row inputs")
    if row.team_status != _row_status(row.reason_codes):
        raise ValueError("team_status must match reason_codes")


def _validate_report(report: ResearchTeamQueueLoadBalancerReport) -> None:
    rows = report.rows
    if report.next_step != NEXT_STEPS[report.load_status]:
        raise ValueError("next_step must match load_status")
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    if report.team_count != _count(len(rows)):
        raise ValueError("team_count must match rows")
    if report.pass_team_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_team_count must match rows")
    if report.watch_team_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_team_count must match rows")
    if report.block_team_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_team_count must match rows")
    if report.total_pending_review_count != _sum_decimal(
        row.pending_review_count for row in rows
    ):
        raise ValueError("total_pending_review_count must match rows")
    if report.pending_pressure_team_count != _reason_team_count(
        rows,
        PENDING_PRESSURE_REASON,
        PENDING_BLOCK_REASON,
    ):
        raise ValueError("pending_pressure_team_count must match rows")
    if report.urgent_team_count != _reason_team_count(
        rows,
        URGENCY_WATCH_REASON,
        URGENCY_BLOCK_REASON,
    ):
        raise ValueError("urgent_team_count must match rows")
    if report.evidence_gap_team_count != _reason_team_count(
        rows,
        EVIDENCE_GAP_REASON,
        EVIDENCE_GAP_BLOCK_REASON,
    ):
        raise ValueError("evidence_gap_team_count must match rows")
    if report.domain_expertise_gap_team_count != _reason_team_count(
        rows,
        DOMAIN_EXPERTISE_GAP_REASON,
        DOMAIN_EXPERTISE_BLOCK_REASON,
    ):
        raise ValueError("domain_expertise_gap_team_count must match rows")
    if report.average_urgency_score != _ratio(
        _sum_decimal(row.urgency_score for row in rows),
        report.team_count,
    ):
        raise ValueError("average_urgency_score must match rows")
    if report.average_domain_expertise_match_score != _ratio(
        _sum_decimal(row.domain_expertise_match_score for row in rows),
        report.team_count,
    ):
        raise ValueError("average_domain_expertise_match_score must match rows")
    if report.max_pending_review_count != max(
        (row.pending_review_count for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_pending_review_count must match rows")
    if report.max_evidence_gap_count != max(
        (row.evidence_gap_count for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_gap_count must match rows")
    expected_counts = _reason_code_counts(rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not rows:
        expected_counts = (
            ResearchTeamQueueLoadBalancerReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.load_status != _report_status(rows):
        raise ValueError("load_status must match rows")


def _normalize_rows(
    rows: tuple[ResearchTeamQueueLoadBalancerReportRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamQueueLoadBalancerReportRow:
            raise ValueError("rows must contain ResearchTeamQueueLoadBalancerReportRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchTeamQueueLoadBalancerReasonCodeCount, ...],
) -> tuple[ResearchTeamQueueLoadBalancerReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamQueueLoadBalancerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamQueueLoadBalancerReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return rows


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, sequence)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if sequence is ROW_REASON_CODE_SEQUENCE and PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with review reasons")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    sequence: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in sequence:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty public identifier")
    if not all(
        character.isascii()
        and (character.isalnum() or character in ("_", "-", "."))
        for character in value
    ):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_text(field_name, value)
    return value


def _reject_unsafe_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if "://" in lowered:
        raise ValueError(f"{field_name} must not include external references")
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} must not include unsafe text")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name) or getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be from zero to one")
    return decimal_value


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(micros / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if type(numerator) is not Decimal or type(denominator) is not Decimal:
        raise ValueError("ratio values must be Decimal")
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("payload values must not be float")
    if isinstance(value, bool) or isinstance(value, str):
        return value
    if isinstance(value, int):
        raise ValueError("payload values must not be int")
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not supported")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_identifier("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text("payload value", value)
        return
    if isinstance(value, Decimal):
        raise ValueError("payload must serialize Decimal values")
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("payload must not contain integer values")
