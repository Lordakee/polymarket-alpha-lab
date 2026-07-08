"""Pure report for human research decision readiness exceptions."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_DECISION_READINESS_EXCEPTION_CONFIG_VERSION = (
    "research-decision-readiness-exception-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

EXCEPTION_MISSING_EVIDENCE = "missing_evidence"
EXCEPTION_COST_ANOMALY = "cost_anomaly"
EXCEPTION_SETTLEMENT_AMBIGUITY = "settlement_ambiguity"
EXCEPTION_TEAM_DISAGREEMENT = "team_disagreement"
EXCEPTION_SAFETY_BLOCK = "safety_block"

EXCEPTION_TYPES = (
    EXCEPTION_MISSING_EVIDENCE,
    EXCEPTION_COST_ANOMALY,
    EXCEPTION_SETTLEMENT_AMBIGUITY,
    EXCEPTION_TEAM_DISAGREEMENT,
    EXCEPTION_SAFETY_BLOCK,
)

REASON_PREFIX = "research_decision_readiness_exception_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
MISSING_EVIDENCE_REASON = f"{REASON_PREFIX}missing_evidence"
COST_ANOMALY_WATCH_REASON = f"{REASON_PREFIX}cost_anomaly_watch"
COST_ANOMALY_BLOCK_REASON = f"{REASON_PREFIX}cost_anomaly_block"
SETTLEMENT_AMBIGUITY_WATCH_REASON = f"{REASON_PREFIX}settlement_ambiguity_watch"
SETTLEMENT_AMBIGUITY_BLOCK_REASON = f"{REASON_PREFIX}settlement_ambiguity_block"
TEAM_DISAGREEMENT_WATCH_REASON = f"{REASON_PREFIX}team_disagreement_watch"
TEAM_DISAGREEMENT_BLOCK_REASON = f"{REASON_PREFIX}team_disagreement_block"
SAFETY_BLOCK_REASON = f"{REASON_PREFIX}safety_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    SAFETY_BLOCK_REASON,
    MISSING_EVIDENCE_REASON,
    COST_ANOMALY_BLOCK_REASON,
    SETTLEMENT_AMBIGUITY_BLOCK_REASON,
    TEAM_DISAGREEMENT_BLOCK_REASON,
    COST_ANOMALY_WATCH_REASON,
    SETTLEMENT_AMBIGUITY_WATCH_REASON,
    TEAM_DISAGREEMENT_WATCH_REASON,
    PASS_REASON,
)

ROW_REASON_CODE_SEQUENCE = (
    SAFETY_BLOCK_REASON,
    MISSING_EVIDENCE_REASON,
    COST_ANOMALY_BLOCK_REASON,
    SETTLEMENT_AMBIGUITY_BLOCK_REASON,
    TEAM_DISAGREEMENT_BLOCK_REASON,
    COST_ANOMALY_WATCH_REASON,
    SETTLEMENT_AMBIGUITY_WATCH_REASON,
    TEAM_DISAGREEMENT_WATCH_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_research_decision_readiness_exception_report",
    STATUS_WATCH: "watch_report_only_research_decision_readiness_exception_report",
    STATUS_BLOCK: "block_report_only_research_decision_readiness_exception_report",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_PUBLIC_REFERENCE_FRAGMENTS = ("public", "memo", "notice", "filing", "release")
_UNSAFE_TEXT_FRAGMENTS = (
    "conf" + "idential",
    "cred" + "ential",
    "priv" + "ate",
    "sec" + "ret",
    "tok" + "en",
    "api" + "_key",
    "au" + "th",
    "wa" + "llet",
    "br" + "oker",
    "li" + "ve",
    "ord" + "er",
    "pos" + "ition",
    "tra" + "de",
    "b" + "uy",
    "s" + "ell",
    "b" + "et",
    "st" + "ake",
    "recom" + "mend",
)


@dataclass(frozen=True)
class ResearchDecisionReadinessExceptionConfig:
    config_version: str = DEFAULT_RESEARCH_DECISION_READINESS_EXCEPTION_CONFIG_VERSION
    missing_evidence_block_threshold: Decimal = Decimal("1")
    cost_anomaly_watch_threshold: Decimal = Decimal("0.150000")
    cost_anomaly_block_threshold: Decimal = Decimal("0.350000")
    settlement_ambiguity_watch_threshold: Decimal = Decimal("0.200000")
    settlement_ambiguity_block_threshold: Decimal = Decimal("0.500000")
    team_disagreement_watch_threshold: Decimal = Decimal("0.250000")
    team_disagreement_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionReadinessExceptionConfig:
            raise TypeError(
                "ResearchDecisionReadinessExceptionConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionReadinessExceptionConfig:
            raise ValueError(
                "config must be exactly ResearchDecisionReadinessExceptionConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "missing_evidence_block_threshold",
            _require_positive_count_decimal(
                "missing_evidence_block_threshold",
                self.missing_evidence_block_threshold,
            ),
        )
        _normalize_threshold_pair(
            self,
            "cost_anomaly_watch_threshold",
            "cost_anomaly_block_threshold",
        )
        _normalize_threshold_pair(
            self,
            "settlement_ambiguity_watch_threshold",
            "settlement_ambiguity_block_threshold",
        )
        _normalize_threshold_pair(
            self,
            "team_disagreement_watch_threshold",
            "team_disagreement_block_threshold",
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDecisionReadinessExceptionInputRow:
    packet_id: str
    exception_id: str
    exception_type: str
    observed_at: datetime
    public_reference: str
    severity_score: Decimal
    missing_evidence_count: Decimal
    cost_anomaly_score: Decimal
    settlement_ambiguity_score: Decimal
    team_disagreement_score: Decimal
    safety_blocked: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionReadinessExceptionInputRow:
            raise TypeError(
                "ResearchDecisionReadinessExceptionInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionReadinessExceptionInputRow:
            raise ValueError(
                "input row must be exactly ResearchDecisionReadinessExceptionInputRow",
            )
        _require_public_string("packet_id", self.packet_id)
        _require_public_string("exception_id", self.exception_id)
        _require_exception_type("exception_type", self.exception_type)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_reference("public_reference", self.public_reference)
        object.__setattr__(
            self,
            "severity_score",
            _require_ratio_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "missing_evidence_count",
            _require_nonnegative_count_decimal(
                "missing_evidence_count",
                self.missing_evidence_count,
            ),
        )
        for field_name in (
            "cost_anomaly_score",
            "settlement_ambiguity_score",
            "team_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "safety_blocked",
            _require_bool("safety_blocked", self.safety_blocked),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDecisionReadinessExceptionRow:
    packet_id: str
    exception_id: str
    exception_type: str
    observed_at: datetime
    exception_age_seconds: Decimal
    severity_score: Decimal
    missing_evidence_count: Decimal
    cost_anomaly_score: Decimal
    settlement_ambiguity_score: Decimal
    team_disagreement_score: Decimal
    safety_blocked: bool
    status: str
    redacted_public_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchDecisionReadinessExceptionConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionReadinessExceptionRow:
            raise TypeError(
                "ResearchDecisionReadinessExceptionRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchDecisionReadinessExceptionConfig | None,
    ) -> None:
        if type(self) is not ResearchDecisionReadinessExceptionRow:
            raise ValueError("row must be exactly ResearchDecisionReadinessExceptionRow")
        _require_public_string("packet_id", self.packet_id)
        _require_public_string("exception_id", self.exception_id)
        _require_exception_type("exception_type", self.exception_type)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "exception_age_seconds",
            _require_nonnegative_decimal(
                "exception_age_seconds",
                self.exception_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "severity_score",
            _require_ratio_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "missing_evidence_count",
            _require_nonnegative_count_decimal(
                "missing_evidence_count",
                self.missing_evidence_count,
            ),
        )
        for field_name in (
            "cost_anomaly_score",
            "settlement_ambiguity_score",
            "team_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "safety_blocked",
            _require_bool("safety_blocked", self.safety_blocked),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "redacted_public_reference",
            _require_redacted_reference(
                "redacted_public_reference",
                self.redacted_public_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDecisionReadinessExceptionReasonCodeCount:
    reason_code: str
    count: Decimal
    exception_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionReadinessExceptionReasonCodeCount:
            raise TypeError(
                "ResearchDecisionReadinessExceptionReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionReadinessExceptionReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDecisionReadinessExceptionReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "exception_ratio",
            _require_ratio_decimal("exception_ratio", self.exception_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDecisionReadinessExceptionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    exception_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_evidence_count: Decimal
    cost_anomaly_count: Decimal
    settlement_ambiguity_count: Decimal
    team_disagreement_count: Decimal
    safety_block_count: Decimal
    average_severity_score: Decimal
    max_exception_age_seconds: Decimal
    rows: tuple[ResearchDecisionReadinessExceptionRow, ...]
    reason_code_counts: tuple[ResearchDecisionReadinessExceptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionReadinessExceptionReport:
            raise TypeError(
                "ResearchDecisionReadinessExceptionReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionReadinessExceptionReport:
            raise ValueError(
                "report must be exactly ResearchDecisionReadinessExceptionReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "exception_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_evidence_count",
            "cost_anomaly_count",
            "settlement_ambiguity_count",
            "team_disagreement_count",
            "safety_block_count",
            "average_severity_score",
            "max_exception_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchDecisionReadinessExceptionRow:
                raise ValueError(
                    "rows must contain ResearchDecisionReadinessExceptionRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchDecisionReadinessExceptionReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchDecisionReadinessExceptionReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_decision_readiness_exception_report(
    input_rows: list[ResearchDecisionReadinessExceptionInputRow]
    | tuple[ResearchDecisionReadinessExceptionInputRow, ...],
    *,
    config: ResearchDecisionReadinessExceptionConfig | None = None,
    generated_at: datetime,
) -> ResearchDecisionReadinessExceptionReport:
    cfg = config or ResearchDecisionReadinessExceptionConfig()
    if type(cfg) is not ResearchDecisionReadinessExceptionConfig:
        raise ValueError("config must be a ResearchDecisionReadinessExceptionConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    exception_count = _count(len(ranked_rows))
    pass_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchDecisionReadinessExceptionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                exception_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    report_status = _report_status(
        has_inputs=bool(ranked_rows),
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchDecisionReadinessExceptionReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        exception_count=exception_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        missing_evidence_count=_count(
            sum(1 for row in ranked_rows if MISSING_EVIDENCE_REASON in row.reason_codes),
        ),
        cost_anomaly_count=_count(
            sum(
                1
                for row in ranked_rows
                if COST_ANOMALY_BLOCK_REASON in row.reason_codes
                or COST_ANOMALY_WATCH_REASON in row.reason_codes
            ),
        ),
        settlement_ambiguity_count=_count(
            sum(
                1
                for row in ranked_rows
                if SETTLEMENT_AMBIGUITY_BLOCK_REASON in row.reason_codes
                or SETTLEMENT_AMBIGUITY_WATCH_REASON in row.reason_codes
            ),
        ),
        team_disagreement_count=_count(
            sum(
                1
                for row in ranked_rows
                if TEAM_DISAGREEMENT_BLOCK_REASON in row.reason_codes
                or TEAM_DISAGREEMENT_WATCH_REASON in row.reason_codes
            ),
        ),
        safety_block_count=_count(
            sum(1 for row in ranked_rows if SAFETY_BLOCK_REASON in row.reason_codes),
        ),
        average_severity_score=_ratio(
            _sum_decimal(row.severity_score for row in ranked_rows),
            exception_count,
        ),
        max_exception_age_seconds=max(
            (row.exception_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_decision_readiness_exception_report_payload(
    report: ResearchDecisionReadinessExceptionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDecisionReadinessExceptionReport:
        raise ValueError("report must be a ResearchDecisionReadinessExceptionReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _build_row(
    row: ResearchDecisionReadinessExceptionInputRow,
    *,
    config: ResearchDecisionReadinessExceptionConfig,
    generated_at: datetime,
) -> ResearchDecisionReadinessExceptionRow:
    exception_age_seconds = _datetime_delta_seconds(generated_at, row.observed_at)
    reason_codes = _row_reason_codes(
        missing_evidence_count=row.missing_evidence_count,
        cost_anomaly_score=row.cost_anomaly_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        team_disagreement_score=row.team_disagreement_score,
        safety_blocked=row.safety_blocked,
        config=config,
    )
    return ResearchDecisionReadinessExceptionRow(
        packet_id=row.packet_id,
        exception_id=row.exception_id,
        exception_type=row.exception_type,
        observed_at=row.observed_at,
        exception_age_seconds=exception_age_seconds,
        severity_score=row.severity_score,
        missing_evidence_count=row.missing_evidence_count,
        cost_anomaly_score=row.cost_anomaly_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        team_disagreement_score=row.team_disagreement_score,
        safety_blocked=row.safety_blocked,
        status=_row_status(reason_codes),
        redacted_public_reference=_redacted_reference(row.public_reference),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchDecisionReadinessExceptionInputRow]
    | tuple[ResearchDecisionReadinessExceptionInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchDecisionReadinessExceptionInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDecisionReadinessExceptionInputRow:
            raise ValueError(
                "input rows must contain ResearchDecisionReadinessExceptionInputRow",
            )
        _require_hard_flags("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        key = (row.packet_id, row.exception_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate exceptions")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    missing_evidence_count: Decimal,
    cost_anomaly_score: Decimal,
    settlement_ambiguity_score: Decimal,
    team_disagreement_score: Decimal,
    safety_blocked: bool,
    config: ResearchDecisionReadinessExceptionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if safety_blocked:
        reason_codes.append(SAFETY_BLOCK_REASON)
    if missing_evidence_count >= config.missing_evidence_block_threshold:
        reason_codes.append(MISSING_EVIDENCE_REASON)
    if cost_anomaly_score >= config.cost_anomaly_block_threshold:
        reason_codes.append(COST_ANOMALY_BLOCK_REASON)
    elif cost_anomaly_score >= config.cost_anomaly_watch_threshold:
        reason_codes.append(COST_ANOMALY_WATCH_REASON)
    if settlement_ambiguity_score >= config.settlement_ambiguity_block_threshold:
        reason_codes.append(SETTLEMENT_AMBIGUITY_BLOCK_REASON)
    elif settlement_ambiguity_score >= config.settlement_ambiguity_watch_threshold:
        reason_codes.append(SETTLEMENT_AMBIGUITY_WATCH_REASON)
    if team_disagreement_score >= config.team_disagreement_block_threshold:
        reason_codes.append(TEAM_DISAGREEMENT_BLOCK_REASON)
    elif team_disagreement_score >= config.team_disagreement_watch_threshold:
        reason_codes.append(TEAM_DISAGREEMENT_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    block_reasons = (
        SAFETY_BLOCK_REASON,
        MISSING_EVIDENCE_REASON,
        COST_ANOMALY_BLOCK_REASON,
        SETTLEMENT_AMBIGUITY_BLOCK_REASON,
        TEAM_DISAGREEMENT_BLOCK_REASON,
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


def _ranked_rows(
    rows: tuple[ResearchDecisionReadinessExceptionRow, ...],
) -> tuple[ResearchDecisionReadinessExceptionRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                -row.severity_score,
                row.exception_type,
                row.packet_id,
                row.exception_id,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchDecisionReadinessExceptionRow, ...],
) -> tuple[ResearchDecisionReadinessExceptionReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            exception_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchDecisionReadinessExceptionRow,
    *,
    config: ResearchDecisionReadinessExceptionConfig | None,
) -> None:
    if config is None:
        config = ResearchDecisionReadinessExceptionConfig()
    if type(config) is not ResearchDecisionReadinessExceptionConfig:
        raise ValueError(
            "validation_config must be a ResearchDecisionReadinessExceptionConfig",
        )
    expected_reason_codes = _row_reason_codes(
        missing_evidence_count=row.missing_evidence_count,
        cost_anomaly_score=row.cost_anomaly_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        team_disagreement_score=row.team_disagreement_score,
        safety_blocked=row.safety_blocked,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if not _is_redacted_reference(row.redacted_public_reference):
        raise ValueError("redacted_public_reference must be redacted or public")


def _validate_report(report: ResearchDecisionReadinessExceptionReport) -> None:
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step must match report_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.exception_count != _count(len(report.rows)):
        raise ValueError("exception_count must match rows")
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
    if report.missing_evidence_count != _count(
        sum(1 for row in report.rows if MISSING_EVIDENCE_REASON in row.reason_codes),
    ):
        raise ValueError("missing_evidence_count must match rows")
    if report.cost_anomaly_count != _count(
        sum(
            1
            for row in report.rows
            if COST_ANOMALY_BLOCK_REASON in row.reason_codes
            or COST_ANOMALY_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("cost_anomaly_count must match rows")
    if report.settlement_ambiguity_count != _count(
        sum(
            1
            for row in report.rows
            if SETTLEMENT_AMBIGUITY_BLOCK_REASON in row.reason_codes
            or SETTLEMENT_AMBIGUITY_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("settlement_ambiguity_count must match rows")
    if report.team_disagreement_count != _count(
        sum(
            1
            for row in report.rows
            if TEAM_DISAGREEMENT_BLOCK_REASON in row.reason_codes
            or TEAM_DISAGREEMENT_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("team_disagreement_count must match rows")
    if report.safety_block_count != _count(
        sum(1 for row in report.rows if SAFETY_BLOCK_REASON in row.reason_codes),
    ):
        raise ValueError("safety_block_count must match rows")
    if report.average_severity_score != _ratio(
        _sum_decimal(row.severity_score for row in report.rows),
        report.exception_count,
    ):
        raise ValueError("average_severity_score must match rows")
    if report.max_exception_age_seconds != max(
        (row.exception_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_exception_age_seconds must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchDecisionReadinessExceptionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                exception_ratio=ONE,
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
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")


def _normalize_threshold_pair(
    config: ResearchDecisionReadinessExceptionConfig,
    watch_field_name: str,
    block_field_name: str,
) -> None:
    watch_value = _require_ratio_decimal(watch_field_name, getattr(config, watch_field_name))
    block_value = _require_ratio_decimal(block_field_name, getattr(config, block_field_name))
    if watch_value > block_value:
        raise ValueError(f"{block_field_name} must be at least {watch_field_name}")
    object.__setattr__(config, watch_field_name, watch_value)
    object.__setattr__(config, block_field_name, block_value)


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
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with exception reasons")
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
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_exception_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXCEPTION_TYPES:
        raise ValueError(f"{field_name} must be a supported exception type")


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


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or any(item not in "0123456789abcdef" for item in digest):
            raise ValueError(f"{field_name} must be a short sha256 digest")
        return value
    _reject_unsafe_text(field_name, value)
    if not _is_public_reference(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        return len(digest) == 12 and all(item in "0123456789abcdef" for item in digest)
    return _is_public_reference(value)


def _is_public_reference(value: str) -> bool:
    lowered = value.lower()
    if _contains_unsafe_text(value):
        return False
    return any(fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS)


def _redacted_reference(value: str) -> str:
    if _is_public_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return _quantize(value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be in range 0 to 1")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("later datetime must be on or after earlier datetime")
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    subseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + subseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        return str(_require_decimal("JSON Decimal value", value))
    if type(value) is datetime:
        return _as_utc("JSON datetime value", value).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must use Decimal strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(field_name: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} keys must be strings")
            _reject_unsafe_text(f"{field_name} key", key)
            _reject_unsafe_payload(field_name, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_payload(field_name, item)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{field_name} numeric values must use Decimal strings")
    if type(value) is str:
        _reject_unsafe_text(f"{field_name} value", value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must be public-safe")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS)
