"""Pure public report for liquidity and information-quality divergence."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Sequence


DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION = (
    "research-event-liquidity-information-divergence-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_DEPTH_BLOCK = "liquidity_depth_block"
REASON_SPREAD_BLOCK = "spread_pressure_block"
REASON_FRESHNESS_BLOCK = "evidence_freshness_block"
REASON_RELIABILITY_BLOCK = "source_reliability_block"
REASON_CATALYST_BLOCK = "catalyst_pressure_block"
REASON_DIVERGENCE_BLOCK = "divergence_score_block"
REASON_DEPTH_WATCH = "liquidity_depth_watch"
REASON_SPREAD_WATCH = "spread_pressure_watch"
REASON_FRESHNESS_WATCH = "evidence_freshness_watch"
REASON_RELIABILITY_WATCH = "source_reliability_watch"
REASON_CATALYST_WATCH = "catalyst_pressure_watch"
REASON_DIVERGENCE_WATCH = "divergence_score_watch"
REASON_ALIGNMENT_PASS = "liquidity_information_alignment_pass"

REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_DEPTH_BLOCK,
    REASON_SPREAD_BLOCK,
    REASON_FRESHNESS_BLOCK,
    REASON_RELIABILITY_BLOCK,
    REASON_CATALYST_BLOCK,
    REASON_DIVERGENCE_BLOCK,
    REASON_DEPTH_WATCH,
    REASON_SPREAD_WATCH,
    REASON_FRESHNESS_WATCH,
    REASON_RELIABILITY_WATCH,
    REASON_CATALYST_WATCH,
    REASON_DIVERGENCE_WATCH,
    REASON_ALIGNMENT_PASS,
)
ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code != REASON_EMPTY_INPUT
)
BLOCK_REASON_CODES = frozenset(
    (
        REASON_DEPTH_BLOCK,
        REASON_SPREAD_BLOCK,
        REASON_FRESHNESS_BLOCK,
        REASON_RELIABILITY_BLOCK,
        REASON_CATALYST_BLOCK,
        REASON_DIVERGENCE_BLOCK,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_FIELD = "derived_validation_digest"
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchEventLiquidityInformationDivergenceConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION
    )
    pass_depth_units: Decimal = Decimal("100.000000")
    block_depth_units: Decimal = Decimal("25.000000")
    spread_pressure_watch_threshold: Decimal = Decimal("0.350000")
    spread_pressure_block_threshold: Decimal = Decimal("0.700000")
    evidence_age_watch_hours: Decimal = Decimal("24.000000")
    evidence_age_block_hours: Decimal = Decimal("72.000000")
    source_reliability_watch_threshold: Decimal = Decimal("0.700000")
    source_reliability_block_threshold: Decimal = Decimal("0.400000")
    catalyst_pressure_watch_threshold: Decimal = Decimal("0.400000")
    catalyst_pressure_block_threshold: Decimal = Decimal("0.750000")
    divergence_watch_threshold: Decimal = Decimal("0.400000")
    divergence_block_threshold: Decimal = Decimal("0.700000")
    depth_weight: Decimal = Decimal("0.250000")
    spread_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.200000")
    reliability_weight: Decimal = Decimal("0.200000")
    catalyst_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventLiquidityInformationDivergenceConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("pass_depth_units", "block_depth_units"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_pressure_watch_threshold",
            "spread_pressure_block_threshold",
            "source_reliability_watch_threshold",
            "source_reliability_block_threshold",
            "catalyst_pressure_watch_threshold",
            "catalyst_pressure_block_threshold",
            "divergence_watch_threshold",
            "divergence_block_threshold",
            "depth_weight",
            "spread_weight",
            "freshness_weight",
            "reliability_weight",
            "catalyst_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_watch_hours", "evidence_age_block_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventLiquidityInformationDivergenceInput(_FinalPublicDataclass):
    analysis_key: str
    aggregate_depth_units: Decimal
    spread_pressure_score: Decimal
    evidence_age_hours: Decimal
    source_reliability_score: Decimal
    catalyst_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventLiquidityInformationDivergenceInput, "input")
        object.__setattr__(
            self,
            "analysis_key",
            _require_input_key("analysis_key", self.analysis_key),
        )
        object.__setattr__(
            self,
            "aggregate_depth_units",
            _require_nonnegative_decimal(
                "aggregate_depth_units",
                self.aggregate_depth_units,
            ),
        )
        for field_name in (
            "spread_pressure_score",
            "source_reliability_score",
            "catalyst_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _require_nonnegative_decimal("evidence_age_hours", self.evidence_age_hours),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventLiquidityInformationDivergenceRow(_FinalPublicDataclass):
    analysis_digest: str
    aggregate_depth_units: Decimal
    spread_pressure_score: Decimal
    evidence_age_hours: Decimal
    source_reliability_score: Decimal
    catalyst_pressure_score: Decimal
    depth_gap_score: Decimal
    freshness_gap_score: Decimal
    reliability_gap_score: Decimal
    divergence_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchEventLiquidityInformationDivergenceConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchEventLiquidityInformationDivergenceConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchEventLiquidityInformationDivergenceRow, "row")
        object.__setattr__(
            self,
            "analysis_digest",
            _require_public_digest("analysis_digest", self.analysis_digest),
        )
        object.__setattr__(
            self,
            "aggregate_depth_units",
            _require_nonnegative_decimal(
                "aggregate_depth_units",
                self.aggregate_depth_units,
            ),
        )
        for field_name in (
            "spread_pressure_score",
            "source_reliability_score",
            "catalyst_pressure_score",
            "depth_gap_score",
            "freshness_gap_score",
            "reliability_gap_score",
            "divergence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _require_nonnegative_decimal("evidence_age_hours", self.evidence_age_hours),
        )
        _require_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventLiquidityInformationDivergenceReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventLiquidityInformationDivergenceReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchEventLiquidityInformationDivergenceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_divergence_score: Decimal
    max_divergence_score: Decimal
    average_depth_units: Decimal
    max_spread_pressure_score: Decimal
    max_evidence_age_hours: Decimal
    min_source_reliability_score: Decimal
    max_catalyst_pressure_score: Decimal
    rows: tuple[ResearchEventLiquidityInformationDivergenceRow, ...]
    reason_code_counts: tuple[
        ResearchEventLiquidityInformationDivergenceReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventLiquidityInformationDivergenceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("public_status", self.public_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_divergence_score",
            "max_divergence_score",
            "max_spread_pressure_score",
            "min_source_reliability_score",
            "max_catalyst_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_depth_units", "max_evidence_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_event_liquidity_information_divergence_payload(self)


def build_research_event_liquidity_information_divergence_report(
    inputs: Sequence[ResearchEventLiquidityInformationDivergenceInput],
    *,
    generated_at: datetime,
    config: ResearchEventLiquidityInformationDivergenceConfig | None = None,
) -> ResearchEventLiquidityInformationDivergenceReport:
    cfg = config or ResearchEventLiquidityInformationDivergenceConfig()
    if type(cfg) is not ResearchEventLiquidityInformationDivergenceConfig:
        raise ValueError(
            "config must be a ResearchEventLiquidityInformationDivergenceConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in _normalize_inputs(inputs)),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchEventLiquidityInformationDivergenceReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "public_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_divergence_score": _average_decimal(
            tuple(row.divergence_score for row in rows),
        ),
        "max_divergence_score": max(
            (row.divergence_score for row in rows),
            default=ZERO,
        ),
        "average_depth_units": _average_decimal(
            tuple(row.aggregate_depth_units for row in rows),
        ),
        "max_spread_pressure_score": max(
            (row.spread_pressure_score for row in rows),
            default=ZERO,
        ),
        "max_evidence_age_hours": max(
            (row.evidence_age_hours for row in rows),
            default=ZERO,
        ),
        "min_source_reliability_score": min(
            (row.source_reliability_score for row in rows),
            default=ZERO,
        ),
        "max_catalyst_pressure_score": max(
            (row.catalyst_pressure_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventLiquidityInformationDivergenceReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_liquidity_information_divergence_payload(
    value: ResearchEventLiquidityInformationDivergenceReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchEventLiquidityInformationDivergenceReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchEventLiquidityInformationDivergenceReport or dict",
        )
    _reject_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchEventLiquidityInformationDivergenceInput,
    config: ResearchEventLiquidityInformationDivergenceConfig,
) -> ResearchEventLiquidityInformationDivergenceRow:
    depth_gap_score = _depth_gap_score(row.aggregate_depth_units, config)
    freshness_gap_score = _freshness_gap_score(row.evidence_age_hours, config)
    reliability_gap_score = _inverse_ratio(row.source_reliability_score)
    divergence_score = _divergence_score(
        depth_gap_score=depth_gap_score,
        spread_pressure_score=row.spread_pressure_score,
        freshness_gap_score=freshness_gap_score,
        reliability_gap_score=reliability_gap_score,
        catalyst_pressure_score=row.catalyst_pressure_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        aggregate_depth_units=row.aggregate_depth_units,
        spread_pressure_score=row.spread_pressure_score,
        evidence_age_hours=row.evidence_age_hours,
        source_reliability_score=row.source_reliability_score,
        catalyst_pressure_score=row.catalyst_pressure_score,
        divergence_score=divergence_score,
        config=config,
    )
    return ResearchEventLiquidityInformationDivergenceRow(
        analysis_digest=_analysis_digest(row.analysis_key),
        aggregate_depth_units=row.aggregate_depth_units,
        spread_pressure_score=row.spread_pressure_score,
        evidence_age_hours=row.evidence_age_hours,
        source_reliability_score=row.source_reliability_score,
        catalyst_pressure_score=row.catalyst_pressure_score,
        depth_gap_score=depth_gap_score,
        freshness_gap_score=freshness_gap_score,
        reliability_gap_score=reliability_gap_score,
        divergence_score=divergence_score,
        public_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    aggregate_depth_units: Decimal,
    spread_pressure_score: Decimal,
    evidence_age_hours: Decimal,
    source_reliability_score: Decimal,
    catalyst_pressure_score: Decimal,
    divergence_score: Decimal,
    config: ResearchEventLiquidityInformationDivergenceConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if aggregate_depth_units <= config.block_depth_units:
        reason_codes.append(REASON_DEPTH_BLOCK)
    elif aggregate_depth_units < config.pass_depth_units:
        reason_codes.append(REASON_DEPTH_WATCH)
    if spread_pressure_score >= config.spread_pressure_block_threshold:
        reason_codes.append(REASON_SPREAD_BLOCK)
    elif spread_pressure_score >= config.spread_pressure_watch_threshold:
        reason_codes.append(REASON_SPREAD_WATCH)
    if evidence_age_hours >= config.evidence_age_block_hours:
        reason_codes.append(REASON_FRESHNESS_BLOCK)
    elif evidence_age_hours > config.evidence_age_watch_hours:
        reason_codes.append(REASON_FRESHNESS_WATCH)
    if source_reliability_score <= config.source_reliability_block_threshold:
        reason_codes.append(REASON_RELIABILITY_BLOCK)
    elif source_reliability_score < config.source_reliability_watch_threshold:
        reason_codes.append(REASON_RELIABILITY_WATCH)
    if catalyst_pressure_score >= config.catalyst_pressure_block_threshold:
        reason_codes.append(REASON_CATALYST_BLOCK)
    elif catalyst_pressure_score >= config.catalyst_pressure_watch_threshold:
        reason_codes.append(REASON_CATALYST_WATCH)
    if divergence_score >= config.divergence_block_threshold:
        reason_codes.append(REASON_DIVERGENCE_BLOCK)
    elif divergence_score >= config.divergence_watch_threshold:
        reason_codes.append(REASON_DIVERGENCE_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_ALIGNMENT_PASS)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_ALIGNMENT_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchEventLiquidityInformationDivergenceRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchEventLiquidityInformationDivergenceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _row_sort_key(
    row: ResearchEventLiquidityInformationDivergenceRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.public_status), -row.divergence_score, row.analysis_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchEventLiquidityInformationDivergenceRow, ...],
) -> tuple[ResearchEventLiquidityInformationDivergenceReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _depth_gap_score(
    aggregate_depth_units: Decimal,
    config: ResearchEventLiquidityInformationDivergenceConfig,
) -> Decimal:
    if aggregate_depth_units <= config.block_depth_units:
        return ONE
    if aggregate_depth_units >= config.pass_depth_units:
        return ZERO
    return _clamp_ratio((config.pass_depth_units - aggregate_depth_units) / config.pass_depth_units)


def _freshness_gap_score(
    evidence_age_hours: Decimal,
    config: ResearchEventLiquidityInformationDivergenceConfig,
) -> Decimal:
    if evidence_age_hours >= config.evidence_age_block_hours:
        return ONE
    return _clamp_ratio(evidence_age_hours / config.evidence_age_block_hours)


def _divergence_score(
    *,
    depth_gap_score: Decimal,
    spread_pressure_score: Decimal,
    freshness_gap_score: Decimal,
    reliability_gap_score: Decimal,
    catalyst_pressure_score: Decimal,
    config: ResearchEventLiquidityInformationDivergenceConfig,
) -> Decimal:
    return _clamp_ratio(
        depth_gap_score * config.depth_weight
        + spread_pressure_score * config.spread_weight
        + freshness_gap_score * config.freshness_weight
        + reliability_gap_score * config.reliability_weight
        + catalyst_pressure_score * config.catalyst_weight,
    )


def _validate_config(
    config: ResearchEventLiquidityInformationDivergenceConfig,
) -> None:
    if config.block_depth_units >= config.pass_depth_units:
        raise ValueError("block_depth_units must be less than pass_depth_units")
    if config.spread_pressure_watch_threshold > config.spread_pressure_block_threshold:
        raise ValueError(
            "spread_pressure_watch_threshold must not exceed "
            "spread_pressure_block_threshold",
        )
    if config.evidence_age_watch_hours > config.evidence_age_block_hours:
        raise ValueError(
            "evidence_age_watch_hours must not exceed evidence_age_block_hours",
        )
    if (
        config.source_reliability_block_threshold
        > config.source_reliability_watch_threshold
    ):
        raise ValueError(
            "source_reliability_block_threshold must not exceed "
            "source_reliability_watch_threshold",
        )
    if config.catalyst_pressure_watch_threshold > config.catalyst_pressure_block_threshold:
        raise ValueError(
            "catalyst_pressure_watch_threshold must not exceed "
            "catalyst_pressure_block_threshold",
        )
    if config.divergence_watch_threshold > config.divergence_block_threshold:
        raise ValueError(
            "divergence_watch_threshold must not exceed divergence_block_threshold",
        )
    weight_sum = _quantize(
        config.depth_weight
        + config.spread_weight
        + config.freshness_weight
        + config.reliability_weight
        + config.catalyst_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(
    row: ResearchEventLiquidityInformationDivergenceRow,
    config: ResearchEventLiquidityInformationDivergenceConfig | None,
) -> None:
    cfg = config or ResearchEventLiquidityInformationDivergenceConfig()
    if type(cfg) is not ResearchEventLiquidityInformationDivergenceConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchEventLiquidityInformationDivergenceConfig",
        )
    expected_depth_gap_score = _depth_gap_score(row.aggregate_depth_units, cfg)
    if row.depth_gap_score != expected_depth_gap_score:
        raise ValueError("depth_gap_score must match row inputs")
    expected_freshness_gap_score = _freshness_gap_score(row.evidence_age_hours, cfg)
    if row.freshness_gap_score != expected_freshness_gap_score:
        raise ValueError("freshness_gap_score must match row inputs")
    expected_reliability_gap_score = _inverse_ratio(row.source_reliability_score)
    if row.reliability_gap_score != expected_reliability_gap_score:
        raise ValueError("reliability_gap_score must match row inputs")
    expected_divergence_score = _divergence_score(
        depth_gap_score=row.depth_gap_score,
        spread_pressure_score=row.spread_pressure_score,
        freshness_gap_score=row.freshness_gap_score,
        reliability_gap_score=row.reliability_gap_score,
        catalyst_pressure_score=row.catalyst_pressure_score,
        config=cfg,
    )
    if row.divergence_score != expected_divergence_score:
        raise ValueError("divergence_score must match row inputs")
    expected_reason_codes = _row_reason_codes(
        aggregate_depth_units=row.aggregate_depth_units,
        spread_pressure_score=row.spread_pressure_score,
        evidence_age_hours=row.evidence_age_hours,
        source_reliability_score=row.source_reliability_score,
        catalyst_pressure_score=row.catalyst_pressure_score,
        divergence_score=row.divergence_score,
        config=cfg,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.public_status != _row_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")


def _validate_report(report: ResearchEventLiquidityInformationDivergenceReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_divergence_score != _average_decimal(
        tuple(row.divergence_score for row in report.rows),
    ):
        raise ValueError("average_divergence_score must match rows")
    if report.max_divergence_score != max(
        (row.divergence_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_divergence_score must match rows")
    if report.average_depth_units != _average_decimal(
        tuple(row.aggregate_depth_units for row in report.rows),
    ):
        raise ValueError("average_depth_units must match rows")
    if report.max_spread_pressure_score != max(
        (row.spread_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_pressure_score must match rows")
    if report.max_evidence_age_hours != max(
        (row.evidence_age_hours for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_age_hours must match rows")
    if report.min_source_reliability_score != min(
        (row.source_reliability_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_source_reliability_score must match rows")
    if report.max_catalyst_pressure_score != max(
        (row.catalyst_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_catalyst_pressure_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchEventLiquidityInformationDivergenceReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")


def _normalize_inputs(
    rows: Sequence[ResearchEventLiquidityInformationDivergenceInput],
) -> tuple[ResearchEventLiquidityInformationDivergenceInput, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventLiquidityInformationDivergenceInput:
            raise ValueError(
                "input rows must contain "
                "ResearchEventLiquidityInformationDivergenceInput",
            )
        _require_hard_flags("input", row)
        digest = _analysis_digest(row.analysis_key)
        if digest in seen:
            raise ValueError("input rows must not contain duplicate analysis keys")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventLiquidityInformationDivergenceRow, ...],
) -> tuple[ResearchEventLiquidityInformationDivergenceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventLiquidityInformationDivergenceRow:
            raise ValueError(
                "rows must contain ResearchEventLiquidityInformationDivergenceRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchEventLiquidityInformationDivergenceReasonCodeCount, ...],
) -> tuple[ResearchEventLiquidityInformationDivergenceReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventLiquidityInformationDivergenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventLiquidityInformationDivergenceReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    return rows


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
    if REASON_ALIGNMENT_PASS in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with divergence reasons")
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


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be pass, watch, or block")


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
    return value


def _require_input_key(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a public sha256 digest")
    _require_digest(field_name, value[7:])
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
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


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return _quantize(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    decimal_value = _quantize(value)
    if decimal_value < ZERO:
        return ZERO
    if decimal_value > ONE:
        return ONE
    return decimal_value


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(ONE - value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _decimal_count(len(values)))


def _analysis_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _report_digest(report: ResearchEventLiquidityInformationDivergenceReport) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _report_digest_from_values(values: dict[str, object]) -> str:
    ready = _json_ready(values)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_digest(ready)


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _report_payload(
    report: ResearchEventLiquidityInformationDivergenceReport,
    *,
    include_digest: bool = True,
) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if not include_digest:
        payload.pop(DIGEST_FIELD, None)
    return payload


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(DIGEST_FIELD)
    _require_digest(DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(DIGEST_FIELD, None)
    if digest != _payload_digest(payload_without_digest):
        raise ValueError("derived_validation_digest mismatch")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


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


def _reject_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if type(value) is str:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{label} must use finite Decimal values")
        return
    if isinstance(value, datetime):
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("public payload must not contain floats")
    if type(value) is int:
        raise ValueError("public payload numeric values must use Decimal strings")
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError("public payload containers must be explicit")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key == "analysis_key":
                raise ValueError("public payload must not contain analysis_key")
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_public_payload(key, item, allow_json_containers=True)
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError("public payload containers must be explicit")
        for item in value:
            _reject_public_payload(label, item, allow_json_containers=True)
        return
    raise ValueError("public payload contains an unsupported value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION",
    "ResearchEventLiquidityInformationDivergenceConfig",
    "ResearchEventLiquidityInformationDivergenceInput",
    "ResearchEventLiquidityInformationDivergenceReasonCodeCount",
    "ResearchEventLiquidityInformationDivergenceReport",
    "ResearchEventLiquidityInformationDivergenceRow",
    "build_research_event_liquidity_information_divergence_report",
    "research_event_liquidity_information_divergence_payload",
)
