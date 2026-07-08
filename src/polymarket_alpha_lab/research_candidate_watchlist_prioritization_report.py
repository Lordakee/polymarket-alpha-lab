"""Pure report reducer for candidate watchlist research priority."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_CANDIDATE_WATCHLIST_PRIORITIZATION_CONFIG_VERSION = (
    "research-candidate-watchlist-prioritization-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_candidate_watchlist_prioritization_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
INFORMATION_GAP_BLOCK_REASON = f"{REASON_PREFIX}information_gap_block"
CALIBRATION_DRIFT_BLOCK_REASON = f"{REASON_PREFIX}calibration_drift_block"
LIQUIDITY_COST_BLOCK_REASON = f"{REASON_PREFIX}liquidity_cost_block"
TEAM_COVERAGE_BLOCK_REASON = f"{REASON_PREFIX}team_coverage_block"
INFORMATION_GAP_WATCH_REASON = f"{REASON_PREFIX}information_gap_watch"
CALIBRATION_DRIFT_WATCH_REASON = f"{REASON_PREFIX}calibration_drift_watch"
LIQUIDITY_COST_WATCH_REASON = f"{REASON_PREFIX}liquidity_cost_watch"
TEAM_COVERAGE_WATCH_REASON = f"{REASON_PREFIX}team_coverage_watch"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    INFORMATION_GAP_BLOCK_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
    LIQUIDITY_COST_BLOCK_REASON,
    TEAM_COVERAGE_BLOCK_REASON,
    INFORMATION_GAP_WATCH_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    LIQUIDITY_COST_WATCH_REASON,
    TEAM_COVERAGE_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    INFORMATION_GAP_BLOCK_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
    LIQUIDITY_COST_BLOCK_REASON,
    TEAM_COVERAGE_BLOCK_REASON,
    INFORMATION_GAP_WATCH_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    LIQUIDITY_COST_WATCH_REASON,
    TEAM_COVERAGE_WATCH_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_research_candidate_watchlist_prioritization",
    STATUS_WATCH: "watch_report_only_research_candidate_watchlist_prioritization",
    STATUS_BLOCK: "block_report_only_research_candidate_watchlist_prioritization",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class ResearchCandidateWatchlistPrioritizationConfig:
    config_version: str = DEFAULT_RESEARCH_CANDIDATE_WATCHLIST_PRIORITIZATION_CONFIG_VERSION
    information_gap_watch_threshold: Decimal = Decimal("0.350000")
    information_gap_block_threshold: Decimal = Decimal("0.750000")
    calibration_drift_watch_threshold: Decimal = Decimal("0.100000")
    calibration_drift_block_threshold: Decimal = Decimal("0.250000")
    liquidity_cost_watch_threshold: Decimal = Decimal("0.030000")
    liquidity_cost_block_threshold: Decimal = Decimal("0.120000")
    min_team_coverage_count: Decimal = Decimal("2")
    information_gap_weight: Decimal = Decimal("0.400000")
    calibration_drift_weight: Decimal = Decimal("0.250000")
    liquidity_cost_weight: Decimal = Decimal("0.200000")
    team_coverage_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateWatchlistPrioritizationConfig:
            raise TypeError(
                "ResearchCandidateWatchlistPrioritizationConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateWatchlistPrioritizationConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchCandidateWatchlistPrioritizationConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "information_gap_watch_threshold",
            "information_gap_block_threshold",
            "calibration_drift_watch_threshold",
            "calibration_drift_block_threshold",
            "liquidity_cost_watch_threshold",
            "liquidity_cost_block_threshold",
            "information_gap_weight",
            "calibration_drift_weight",
            "liquidity_cost_weight",
            "team_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_team_coverage_count",
            _require_positive_count_decimal(
                "min_team_coverage_count",
                self.min_team_coverage_count,
            ),
        )
        _require_threshold_pair(
            "information_gap",
            self.information_gap_watch_threshold,
            self.information_gap_block_threshold,
        )
        _require_threshold_pair(
            "calibration_drift",
            self.calibration_drift_watch_threshold,
            self.calibration_drift_block_threshold,
        )
        _require_threshold_pair(
            "liquidity_cost",
            self.liquidity_cost_watch_threshold,
            self.liquidity_cost_block_threshold,
        )
        weight_sum = _quantize(
            self.information_gap_weight
            + self.calibration_drift_weight
            + self.liquidity_cost_weight
            + self.team_coverage_weight,
        )
        if weight_sum != ONE:
            raise ValueError("priority weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateWatchlistPrioritizationInputRow:
    private_candidate_reference: str
    public_research_bucket: str
    information_gap_score: Decimal
    calibration_drift_score: Decimal
    liquidity_cost_score: Decimal
    team_coverage_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateWatchlistPrioritizationInputRow:
            raise TypeError(
                "ResearchCandidateWatchlistPrioritizationInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateWatchlistPrioritizationInputRow:
            raise ValueError(
                "input row must be exactly "
                "ResearchCandidateWatchlistPrioritizationInputRow",
            )
        _require_private_candidate_reference(
            "private_candidate_reference",
            self.private_candidate_reference,
        )
        _require_public_string("public_research_bucket", self.public_research_bucket)
        for field_name in (
            "information_gap_score",
            "calibration_drift_score",
            "liquidity_cost_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_coverage_count",
            _require_nonnegative_count_decimal(
                "team_coverage_count",
                self.team_coverage_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchCandidateWatchlistPrioritizationRow:
    public_candidate_ref: str
    public_research_bucket: str
    observed_at: datetime
    information_gap_score: Decimal
    calibration_drift_score: Decimal
    liquidity_cost_score: Decimal
    team_coverage_count: Decimal
    team_coverage_gap_score: Decimal
    priority_score: Decimal
    priority_rank: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchCandidateWatchlistPrioritizationConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateWatchlistPrioritizationRow:
            raise TypeError(
                "ResearchCandidateWatchlistPrioritizationRow does not support "
                "subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchCandidateWatchlistPrioritizationConfig | None,
    ) -> None:
        if type(self) is not ResearchCandidateWatchlistPrioritizationRow:
            raise ValueError(
                "row must be exactly ResearchCandidateWatchlistPrioritizationRow",
            )
        _require_public_candidate_ref("public_candidate_ref", self.public_candidate_ref)
        _require_public_string("public_research_bucket", self.public_research_bucket)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "information_gap_score",
            "calibration_drift_score",
            "liquidity_cost_score",
            "team_coverage_gap_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("team_coverage_count", "priority_rank"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.priority_rank <= ZERO:
            raise ValueError("priority_rank must be positive")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchCandidateWatchlistPrioritizationReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateWatchlistPrioritizationReasonCodeCount:
            raise TypeError(
                "ResearchCandidateWatchlistPrioritizationReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateWatchlistPrioritizationReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchCandidateWatchlistPrioritizationReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _require_ratio_decimal("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCandidateWatchlistPrioritizationReport:
    generated_at: datetime
    config_version: str
    status: str
    next_step: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_priority_score: Decimal
    max_priority_score: Decimal
    rows: tuple[ResearchCandidateWatchlistPrioritizationRow, ...]
    reason_code_counts: tuple[ResearchCandidateWatchlistPrioritizationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateWatchlistPrioritizationReport:
            raise TypeError(
                "ResearchCandidateWatchlistPrioritizationReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateWatchlistPrioritizationReport:
            raise ValueError(
                "report must be exactly ResearchCandidateWatchlistPrioritizationReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_priority_score",
            "max_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchCandidateWatchlistPrioritizationRow:
                raise ValueError(
                    "rows must contain ResearchCandidateWatchlistPrioritizationRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchCandidateWatchlistPrioritizationReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchCandidateWatchlistPrioritizationReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_candidate_watchlist_prioritization_report(
    input_rows: list[ResearchCandidateWatchlistPrioritizationInputRow]
    | tuple[ResearchCandidateWatchlistPrioritizationInputRow, ...],
    *,
    config: ResearchCandidateWatchlistPrioritizationConfig,
    generated_at: datetime,
) -> ResearchCandidateWatchlistPrioritizationReport:
    if type(config) is not ResearchCandidateWatchlistPrioritizationConfig:
        raise ValueError(
            "config must be a ResearchCandidateWatchlistPrioritizationConfig",
        )
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=report_time)
    ranked_rows = _build_ranked_rows(rows, config=config)
    candidate_count = _count(len(ranked_rows))
    pass_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchCandidateWatchlistPrioritizationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                candidate_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    status = _report_status(
        has_inputs=bool(ranked_rows),
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchCandidateWatchlistPrioritizationReport(
        generated_at=report_time,
        config_version=config.config_version,
        status=status,
        next_step=NEXT_STEPS[status],
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_priority_score=_ratio(
            _sum_decimal(row.priority_score for row in ranked_rows),
            candidate_count,
        ),
        max_priority_score=max(
            (row.priority_score for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_candidate_watchlist_prioritization_report_payload(
    report: ResearchCandidateWatchlistPrioritizationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCandidateWatchlistPrioritizationReport:
        raise ValueError(
            "report must be a ResearchCandidateWatchlistPrioritizationReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload("payload", payload)
    return payload


def research_candidate_watchlist_prioritization_digest_payload(
    report: ResearchCandidateWatchlistPrioritizationReport,
) -> dict[str, Any]:
    payload = research_candidate_watchlist_prioritization_report_payload(report)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    digest_rows = [
        {
            "priority_rank": row["priority_rank"],
            "public_candidate_ref": row["public_candidate_ref"],
            "public_research_bucket": row["public_research_bucket"],
            "priority_score": row["priority_score"],
            "status": row["status"],
            "reason_codes": row["reason_codes"],
        }
        for row in rows
    ]
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "status": payload["status"],
        "next_step": payload["next_step"],
        "candidate_count": payload["candidate_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "average_priority_score": payload["average_priority_score"],
        "max_priority_score": payload["max_priority_score"],
        "reason_codes": payload["reason_codes"],
        "rows": digest_rows,
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    _reject_unsafe_payload("digest", digest)
    return digest


@dataclass(frozen=True)
class _CandidateMetrics:
    public_candidate_ref: str
    public_research_bucket: str
    observed_at: datetime
    information_gap_score: Decimal
    calibration_drift_score: Decimal
    liquidity_cost_score: Decimal
    team_coverage_count: Decimal
    team_coverage_gap_score: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _build_ranked_rows(
    rows: tuple[ResearchCandidateWatchlistPrioritizationInputRow, ...],
    *,
    config: ResearchCandidateWatchlistPrioritizationConfig,
) -> tuple[ResearchCandidateWatchlistPrioritizationRow, ...]:
    metrics = tuple(_build_metrics(row, config=config) for row in rows)
    ranked_metrics = tuple(sorted(metrics, key=_metrics_sort_key))
    return tuple(
        ResearchCandidateWatchlistPrioritizationRow(
            public_candidate_ref=item.public_candidate_ref,
            public_research_bucket=item.public_research_bucket,
            observed_at=item.observed_at,
            information_gap_score=item.information_gap_score,
            calibration_drift_score=item.calibration_drift_score,
            liquidity_cost_score=item.liquidity_cost_score,
            team_coverage_count=item.team_coverage_count,
            team_coverage_gap_score=item.team_coverage_gap_score,
            priority_score=item.priority_score,
            priority_rank=_count(index),
            status=item.status,
            reason_codes=item.reason_codes,
            validation_config=config,
        )
        for index, item in enumerate(ranked_metrics, start=1)
    )


def _build_metrics(
    row: ResearchCandidateWatchlistPrioritizationInputRow,
    *,
    config: ResearchCandidateWatchlistPrioritizationConfig,
) -> _CandidateMetrics:
    team_coverage_gap_score = _team_coverage_gap_score(
        row.team_coverage_count,
        min_team_coverage_count=config.min_team_coverage_count,
    )
    priority_score = _priority_score(
        information_gap_score=row.information_gap_score,
        calibration_drift_score=row.calibration_drift_score,
        liquidity_cost_score=row.liquidity_cost_score,
        team_coverage_gap_score=team_coverage_gap_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        information_gap_score=row.information_gap_score,
        calibration_drift_score=row.calibration_drift_score,
        liquidity_cost_score=row.liquidity_cost_score,
        team_coverage_count=row.team_coverage_count,
        config=config,
    )
    return _CandidateMetrics(
        public_candidate_ref=_public_candidate_ref(row.private_candidate_reference),
        public_research_bucket=row.public_research_bucket,
        observed_at=row.observed_at,
        information_gap_score=row.information_gap_score,
        calibration_drift_score=row.calibration_drift_score,
        liquidity_cost_score=row.liquidity_cost_score,
        team_coverage_count=row.team_coverage_count,
        team_coverage_gap_score=team_coverage_gap_score,
        priority_score=priority_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    rows: list[ResearchCandidateWatchlistPrioritizationInputRow]
    | tuple[ResearchCandidateWatchlistPrioritizationInputRow, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchCandidateWatchlistPrioritizationInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchCandidateWatchlistPrioritizationInputRow:
            raise ValueError(
                "input rows must contain "
                "ResearchCandidateWatchlistPrioritizationInputRow",
            )
        _require_hard_flags("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        public_candidate_ref = _public_candidate_ref(row.private_candidate_reference)
        if public_candidate_ref in seen:
            raise ValueError("input rows must not contain duplicate candidates")
        seen.add(public_candidate_ref)
    return normalized


def _row_reason_codes(
    *,
    information_gap_score: Decimal,
    calibration_drift_score: Decimal,
    liquidity_cost_score: Decimal,
    team_coverage_count: Decimal,
    config: ResearchCandidateWatchlistPrioritizationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if information_gap_score >= config.information_gap_block_threshold:
        reason_codes.append(INFORMATION_GAP_BLOCK_REASON)
    elif information_gap_score >= config.information_gap_watch_threshold:
        reason_codes.append(INFORMATION_GAP_WATCH_REASON)
    if calibration_drift_score >= config.calibration_drift_block_threshold:
        reason_codes.append(CALIBRATION_DRIFT_BLOCK_REASON)
    elif calibration_drift_score >= config.calibration_drift_watch_threshold:
        reason_codes.append(CALIBRATION_DRIFT_WATCH_REASON)
    if liquidity_cost_score >= config.liquidity_cost_block_threshold:
        reason_codes.append(LIQUIDITY_COST_BLOCK_REASON)
    elif liquidity_cost_score >= config.liquidity_cost_watch_threshold:
        reason_codes.append(LIQUIDITY_COST_WATCH_REASON)
    if team_coverage_count == ZERO:
        reason_codes.append(TEAM_COVERAGE_BLOCK_REASON)
    elif team_coverage_count < config.min_team_coverage_count:
        reason_codes.append(TEAM_COVERAGE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    block_reasons = (
        INFORMATION_GAP_BLOCK_REASON,
        CALIBRATION_DRIFT_BLOCK_REASON,
        LIQUIDITY_COST_BLOCK_REASON,
        TEAM_COVERAGE_BLOCK_REASON,
    )
    if any(reason_code in reason_codes for reason_code in block_reasons):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_inputs or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _metrics_sort_key(item: _CandidateMetrics) -> tuple[object, ...]:
    return (
        _status_rank(item.status),
        -item.priority_score,
        -item.information_gap_score,
        -item.calibration_drift_score,
        -item.liquidity_cost_score,
        item.team_coverage_count,
        item.public_research_bucket,
        item.public_candidate_ref,
    )


def _row_sort_key(
    row: ResearchCandidateWatchlistPrioritizationRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        -row.priority_score,
        -row.information_gap_score,
        -row.calibration_drift_score,
        -row.liquidity_cost_score,
        row.team_coverage_count,
        row.public_research_bucket,
        row.public_candidate_ref,
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _team_coverage_gap_score(
    team_coverage_count: Decimal,
    *,
    min_team_coverage_count: Decimal,
) -> Decimal:
    if team_coverage_count >= min_team_coverage_count:
        return ZERO
    return _ratio(min_team_coverage_count - team_coverage_count, min_team_coverage_count)


def _priority_score(
    *,
    information_gap_score: Decimal,
    calibration_drift_score: Decimal,
    liquidity_cost_score: Decimal,
    team_coverage_gap_score: Decimal,
    config: ResearchCandidateWatchlistPrioritizationConfig,
) -> Decimal:
    return _quantize(
        information_gap_score * config.information_gap_weight
        + calibration_drift_score * config.calibration_drift_weight
        + liquidity_cost_score * config.liquidity_cost_weight
        + team_coverage_gap_score * config.team_coverage_weight,
    )


def _reason_code_counts(
    rows: tuple[ResearchCandidateWatchlistPrioritizationRow, ...],
) -> tuple[ResearchCandidateWatchlistPrioritizationReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            candidate_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchCandidateWatchlistPrioritizationRow,
    *,
    config: ResearchCandidateWatchlistPrioritizationConfig | None,
) -> None:
    if config is None:
        config = ResearchCandidateWatchlistPrioritizationConfig()
    if type(config) is not ResearchCandidateWatchlistPrioritizationConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchCandidateWatchlistPrioritizationConfig",
        )
    expected_team_gap = _team_coverage_gap_score(
        row.team_coverage_count,
        min_team_coverage_count=config.min_team_coverage_count,
    )
    if row.team_coverage_gap_score != expected_team_gap:
        raise ValueError("team_coverage_gap_score must match team coverage inputs")
    expected_score = _priority_score(
        information_gap_score=row.information_gap_score,
        calibration_drift_score=row.calibration_drift_score,
        liquidity_cost_score=row.liquidity_cost_score,
        team_coverage_gap_score=row.team_coverage_gap_score,
        config=config,
    )
    if row.priority_score != expected_score:
        raise ValueError("priority_score must match row inputs")
    expected_reason_codes = _row_reason_codes(
        information_gap_score=row.information_gap_score,
        calibration_drift_score=row.calibration_drift_score,
        liquidity_cost_score=row.liquidity_cost_score,
        team_coverage_count=row.team_coverage_count,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchCandidateWatchlistPrioritizationReport) -> None:
    if report.next_step != NEXT_STEPS[report.status]:
        raise ValueError("next_step must match status")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted deterministically")
    expected_ranks = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.priority_rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must have sequential priority_rank values")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.status == STATUS_PASS),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.status == STATUS_WATCH),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.status == STATUS_BLOCK),
    ):
        raise ValueError("block_count must match rows")
    if report.average_priority_score != _ratio(
        _sum_decimal(row.priority_score for row in report.rows),
        report.candidate_count,
    ):
        raise ValueError("average_priority_score must match rows")
    if report.max_priority_score != max(
        (row.priority_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchCandidateWatchlistPrioritizationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                candidate_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        block_count=report.block_count,
        watch_count=report.watch_count,
    )
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_threshold_pair(
    prefix: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{prefix}_block_threshold must be at least watch threshold")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_private_candidate_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_public_candidate_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not _is_public_candidate_ref(value):
        raise ValueError(f"{field_name} must be redacted")
    _reject_unsafe_text(field_name, value)
    return value


def _is_public_candidate_ref(value: str) -> bool:
    if not value.startswith("sha256:") or len(value) != 19:
        return False
    suffix = value.removeprefix("sha256:")
    return all(character in "0123456789abcdef" for character in suffix)


def _public_candidate_ref(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    if type(value) is Decimal:
        return _quantize(value)
    raise ValueError("count value must be an int or Decimal")


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _reject_unsafe_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_text(nested_path, key)
            _reject_unsafe_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        _join_parts("raw", "-", "candidate", "-", "id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", " ", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("market", " ", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("source", "_", "ref"),
        _join_parts("source", " ", "ref"),
        _join_parts("source", "_", "url"),
        _join_parts("source", " ", "url"),
        _join_parts("source", "_", "text"),
        _join_parts("source", " ", "text"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wall", "et"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("pos", "ition"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("reco", "mmend"),
        _join_parts("au", "th"),
        _join_parts("live", "_", "trading"),
        "://",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} has unsafe value")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_WATCHLIST_PRIORITIZATION_CONFIG_VERSION",
    "ResearchCandidateWatchlistPrioritizationConfig",
    "ResearchCandidateWatchlistPrioritizationInputRow",
    "ResearchCandidateWatchlistPrioritizationReasonCodeCount",
    "ResearchCandidateWatchlistPrioritizationReport",
    "ResearchCandidateWatchlistPrioritizationRow",
    "build_research_candidate_watchlist_prioritization_report",
    "research_candidate_watchlist_prioritization_digest_payload",
    "research_candidate_watchlist_prioritization_report_payload",
)
