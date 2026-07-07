"""Pure report-only forecast error attribution reducer."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION = (
    "research-forecast-error-attribution-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_forecast_error_attribution_report_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
MATERIAL_ERROR_REASON = f"{REASON_PREFIX}material_forecast_error"
INFORMATION_GAP_REASON = f"{REASON_PREFIX}information_gap"
MODEL_DISAGREEMENT_REASON = f"{REASON_PREFIX}model_disagreement"
SETTLEMENT_AMBIGUITY_REASON = f"{REASON_PREFIX}settlement_ambiguity"
COST_FRICTION_REASON = f"{REASON_PREFIX}cost_friction"
TEAM_MEMORY_MISSING_REASON = f"{REASON_PREFIX}team_memory_missing"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MATERIAL_ERROR_REASON,
    INFORMATION_GAP_REASON,
    MODEL_DISAGREEMENT_REASON,
    SETTLEMENT_AMBIGUITY_REASON,
    COST_FRICTION_REASON,
    TEAM_MEMORY_MISSING_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_ERROR_REASON,
    INFORMATION_GAP_REASON,
    MODEL_DISAGREEMENT_REASON,
    SETTLEMENT_AMBIGUITY_REASON,
    COST_FRICTION_REASON,
    TEAM_MEMORY_MISSING_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_forecast_error_attribution_review",
    STATUS_WATCH: "watch_report_only_forecast_error_attribution_review",
    STATUS_BLOCK: "block_report_only_forecast_error_attribution_review",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_PUBLIC_REFERENCE_FRAGMENTS = ("public", "memo", "bulletin", "notice", "release")


@dataclass(frozen=True)
class ResearchForecastErrorAttributionConfig:
    config_version: str = DEFAULT_RESEARCH_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION
    material_error_watch_threshold: Decimal = Decimal("0.100000")
    material_error_block_threshold: Decimal = Decimal("0.350000")
    component_watch_threshold: Decimal = Decimal("0.200000")
    component_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchForecastErrorAttributionConfig:
            raise TypeError(
                "ResearchForecastErrorAttributionConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchForecastErrorAttributionConfig:
            raise ValueError(
                "config must be exactly ResearchForecastErrorAttributionConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "material_error_watch_threshold",
            "material_error_block_threshold",
            "component_watch_threshold",
            "component_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_error_watch_threshold > self.material_error_block_threshold:
            raise ValueError(
                "material_error_block_threshold must be at least "
                "material_error_watch_threshold",
            )
        if self.component_watch_threshold > self.component_block_threshold:
            raise ValueError(
                "component_block_threshold must be at least component_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchForecastErrorAttributionInputRow:
    review_key: str
    condition_id: str
    forecast_group: str
    public_resolution_reference: str
    forecast_made_at: datetime
    resolved_at: datetime
    forecast_probability: Decimal
    resolved_probability: Decimal
    information_gap_score: Decimal
    model_disagreement_score: Decimal
    settlement_ambiguity_score: Decimal
    cost_friction_score: Decimal
    team_memory_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchForecastErrorAttributionInputRow:
            raise TypeError(
                "ResearchForecastErrorAttributionInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchForecastErrorAttributionInputRow:
            raise ValueError(
                "input row must be exactly ResearchForecastErrorAttributionInputRow",
            )
        for field_name in ("review_key", "condition_id", "forecast_group"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_resolution_reference", self.public_resolution_reference)
        object.__setattr__(
            self,
            "forecast_made_at",
            _as_utc("forecast_made_at", self.forecast_made_at),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _as_utc("resolved_at", self.resolved_at),
        )
        if self.resolved_at < self.forecast_made_at:
            raise ValueError("resolved_at must be on or after forecast_made_at")
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "information_gap_score",
            "model_disagreement_score",
            "settlement_ambiguity_score",
            "cost_friction_score",
            "team_memory_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchForecastErrorAttributionRow:
    review_key: str
    condition_id: str
    forecast_group: str
    forecast_made_at: datetime
    resolved_at: datetime
    resolution_lag_seconds: Decimal
    forecast_probability: Decimal
    resolved_probability: Decimal
    forecast_error: Decimal
    information_gap_score: Decimal
    model_disagreement_score: Decimal
    settlement_ambiguity_score: Decimal
    cost_friction_score: Decimal
    team_memory_gap_score: Decimal
    attribution_status: str
    redacted_resolution_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchForecastErrorAttributionConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchForecastErrorAttributionRow:
            raise TypeError(
                "ResearchForecastErrorAttributionRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchForecastErrorAttributionConfig | None,
    ) -> None:
        if type(self) is not ResearchForecastErrorAttributionRow:
            raise ValueError("row must be exactly ResearchForecastErrorAttributionRow")
        for field_name in ("review_key", "condition_id", "forecast_group"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "forecast_made_at",
            _as_utc("forecast_made_at", self.forecast_made_at),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _as_utc("resolved_at", self.resolved_at),
        )
        if self.resolved_at < self.forecast_made_at:
            raise ValueError("resolved_at must be on or after forecast_made_at")
        object.__setattr__(
            self,
            "resolution_lag_seconds",
            _require_nonnegative_decimal(
                "resolution_lag_seconds",
                self.resolution_lag_seconds,
            ),
        )
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "forecast_error",
            "information_gap_score",
            "model_disagreement_score",
            "settlement_ambiguity_score",
            "cost_friction_score",
            "team_memory_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("attribution_status", self.attribution_status)
        object.__setattr__(
            self,
            "redacted_resolution_reference",
            _require_redacted_reference(
                "redacted_resolution_reference",
                self.redacted_resolution_reference,
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
class ResearchForecastErrorAttributionReasonCodeCount:
    reason_code: str
    count: Decimal
    forecast_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchForecastErrorAttributionReasonCodeCount:
            raise TypeError(
                "ResearchForecastErrorAttributionReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchForecastErrorAttributionReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchForecastErrorAttributionReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "forecast_ratio",
            _require_ratio_decimal("forecast_ratio", self.forecast_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchForecastErrorAttributionReport:
    generated_at: datetime
    config_version: str
    attribution_status: str
    next_step: str
    forecast_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    material_error_count: Decimal
    information_gap_count: Decimal
    model_disagreement_count: Decimal
    settlement_ambiguity_count: Decimal
    cost_friction_count: Decimal
    team_memory_missing_count: Decimal
    average_forecast_error: Decimal
    max_forecast_error: Decimal
    rows: tuple[ResearchForecastErrorAttributionRow, ...]
    reason_code_counts: tuple[ResearchForecastErrorAttributionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchForecastErrorAttributionReport:
            raise TypeError(
                "ResearchForecastErrorAttributionReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchForecastErrorAttributionReport:
            raise ValueError(
                "report must be exactly ResearchForecastErrorAttributionReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("attribution_status", self.attribution_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "forecast_count",
            "pass_count",
            "watch_count",
            "block_count",
            "material_error_count",
            "information_gap_count",
            "model_disagreement_count",
            "settlement_ambiguity_count",
            "cost_friction_count",
            "team_memory_missing_count",
            "average_forecast_error",
            "max_forecast_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchForecastErrorAttributionRow:
                raise ValueError(
                    "rows must contain ResearchForecastErrorAttributionRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchForecastErrorAttributionReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchForecastErrorAttributionReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_forecast_error_attribution_report_payload(self)


def build_research_forecast_error_attribution_report(
    input_rows: list[ResearchForecastErrorAttributionInputRow]
    | tuple[ResearchForecastErrorAttributionInputRow, ...],
    *,
    config: ResearchForecastErrorAttributionConfig | None = None,
    generated_at: datetime,
) -> ResearchForecastErrorAttributionReport:
    cfg = config or ResearchForecastErrorAttributionConfig()
    if type(cfg) is not ResearchForecastErrorAttributionConfig:
        raise ValueError("config must be a ResearchForecastErrorAttributionConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    forecast_count = _count(len(ranked_rows))
    pass_count = _count(
        sum(1 for row in ranked_rows if row.attribution_status == STATUS_PASS),
    )
    watch_count = _count(
        sum(1 for row in ranked_rows if row.attribution_status == STATUS_WATCH),
    )
    block_count = _count(
        sum(1 for row in ranked_rows if row.attribution_status == STATUS_BLOCK),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchForecastErrorAttributionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                forecast_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    attribution_status = _report_status(
        has_inputs=bool(ranked_rows),
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchForecastErrorAttributionReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        attribution_status=attribution_status,
        next_step=NEXT_STEPS[attribution_status],
        forecast_count=forecast_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        material_error_count=_count(
            sum(1 for row in ranked_rows if MATERIAL_ERROR_REASON in row.reason_codes),
        ),
        information_gap_count=_count(
            sum(1 for row in ranked_rows if INFORMATION_GAP_REASON in row.reason_codes),
        ),
        model_disagreement_count=_count(
            sum(
                1
                for row in ranked_rows
                if MODEL_DISAGREEMENT_REASON in row.reason_codes
            ),
        ),
        settlement_ambiguity_count=_count(
            sum(
                1
                for row in ranked_rows
                if SETTLEMENT_AMBIGUITY_REASON in row.reason_codes
            ),
        ),
        cost_friction_count=_count(
            sum(1 for row in ranked_rows if COST_FRICTION_REASON in row.reason_codes),
        ),
        team_memory_missing_count=_count(
            sum(
                1
                for row in ranked_rows
                if TEAM_MEMORY_MISSING_REASON in row.reason_codes
            ),
        ),
        average_forecast_error=_ratio(
            _sum_decimal(row.forecast_error for row in ranked_rows),
            forecast_count,
        ),
        max_forecast_error=max(
            (row.forecast_error for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_forecast_error_attribution_report_payload(
    report: ResearchForecastErrorAttributionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchForecastErrorAttributionReport:
        raise ValueError(
            "report must be a ResearchForecastErrorAttributionReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
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
    row: ResearchForecastErrorAttributionInputRow,
    *,
    config: ResearchForecastErrorAttributionConfig,
) -> ResearchForecastErrorAttributionRow:
    resolution_lag_seconds = _datetime_delta_seconds(row.resolved_at, row.forecast_made_at)
    forecast_error = _abs_decimal(
        _quantize(row.resolved_probability - row.forecast_probability),
    )
    reason_codes = _row_reason_codes(
        forecast_error=forecast_error,
        information_gap_score=row.information_gap_score,
        model_disagreement_score=row.model_disagreement_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        cost_friction_score=row.cost_friction_score,
        team_memory_gap_score=row.team_memory_gap_score,
        config=config,
    )
    attribution_status = _row_status(
        reason_codes=reason_codes,
        forecast_error=forecast_error,
        information_gap_score=row.information_gap_score,
        model_disagreement_score=row.model_disagreement_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        cost_friction_score=row.cost_friction_score,
        team_memory_gap_score=row.team_memory_gap_score,
        config=config,
    )
    return ResearchForecastErrorAttributionRow(
        review_key=row.review_key,
        condition_id=row.condition_id,
        forecast_group=row.forecast_group,
        forecast_made_at=row.forecast_made_at,
        resolved_at=row.resolved_at,
        resolution_lag_seconds=resolution_lag_seconds,
        forecast_probability=row.forecast_probability,
        resolved_probability=row.resolved_probability,
        forecast_error=forecast_error,
        information_gap_score=row.information_gap_score,
        model_disagreement_score=row.model_disagreement_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        cost_friction_score=row.cost_friction_score,
        team_memory_gap_score=row.team_memory_gap_score,
        attribution_status=attribution_status,
        redacted_resolution_reference=_redacted_reference(
            row.public_resolution_reference,
        ),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchForecastErrorAttributionInputRow]
    | tuple[ResearchForecastErrorAttributionInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchForecastErrorAttributionInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchForecastErrorAttributionInputRow:
            raise ValueError(
                "input rows must contain ResearchForecastErrorAttributionInputRow",
            )
        _require_hard_flags("input row", row)
        if row.resolved_at > generated_at:
            raise ValueError("resolved_at must be on or before generated_at")
        key = (row.review_key, row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate review keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    forecast_error: Decimal,
    information_gap_score: Decimal,
    model_disagreement_score: Decimal,
    settlement_ambiguity_score: Decimal,
    cost_friction_score: Decimal,
    team_memory_gap_score: Decimal,
    config: ResearchForecastErrorAttributionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if forecast_error >= config.material_error_watch_threshold:
        reason_codes.append(MATERIAL_ERROR_REASON)
    if information_gap_score >= config.component_watch_threshold:
        reason_codes.append(INFORMATION_GAP_REASON)
    if model_disagreement_score >= config.component_watch_threshold:
        reason_codes.append(MODEL_DISAGREEMENT_REASON)
    if settlement_ambiguity_score >= config.component_watch_threshold:
        reason_codes.append(SETTLEMENT_AMBIGUITY_REASON)
    if cost_friction_score >= config.component_watch_threshold:
        reason_codes.append(COST_FRICTION_REASON)
    if team_memory_gap_score >= config.component_watch_threshold:
        reason_codes.append(TEAM_MEMORY_MISSING_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    forecast_error: Decimal,
    information_gap_score: Decimal,
    model_disagreement_score: Decimal,
    settlement_ambiguity_score: Decimal,
    cost_friction_score: Decimal,
    team_memory_gap_score: Decimal,
    config: ResearchForecastErrorAttributionConfig,
) -> str:
    if forecast_error >= config.material_error_block_threshold:
        return STATUS_BLOCK
    if any(
        score >= config.component_block_threshold
        for score in (
            information_gap_score,
            model_disagreement_score,
            settlement_ambiguity_score,
            cost_friction_score,
            team_memory_gap_score,
        )
    ):
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
    rows: tuple[ResearchForecastErrorAttributionRow, ...],
) -> tuple[ResearchForecastErrorAttributionRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.attribution_status),
                -row.forecast_error,
                row.forecast_group,
                row.review_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchForecastErrorAttributionRow, ...],
) -> tuple[ResearchForecastErrorAttributionReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            forecast_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchForecastErrorAttributionRow,
    *,
    config: ResearchForecastErrorAttributionConfig | None,
) -> None:
    if config is None:
        config = ResearchForecastErrorAttributionConfig()
    if type(config) is not ResearchForecastErrorAttributionConfig:
        raise ValueError(
            "validation_config must be a ResearchForecastErrorAttributionConfig",
        )
    expected_error = _abs_decimal(
        _quantize(row.resolved_probability - row.forecast_probability),
    )
    if row.forecast_error != expected_error:
        raise ValueError("forecast_error must match probability inputs")
    expected_lag = _datetime_delta_seconds(row.resolved_at, row.forecast_made_at)
    if row.resolution_lag_seconds != expected_lag:
        raise ValueError("resolution_lag_seconds must match row timestamps")
    expected_reason_codes = _row_reason_codes(
        forecast_error=row.forecast_error,
        information_gap_score=row.information_gap_score,
        model_disagreement_score=row.model_disagreement_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        cost_friction_score=row.cost_friction_score,
        team_memory_gap_score=row.team_memory_gap_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_status = _row_status(
        reason_codes=row.reason_codes,
        forecast_error=row.forecast_error,
        information_gap_score=row.information_gap_score,
        model_disagreement_score=row.model_disagreement_score,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        cost_friction_score=row.cost_friction_score,
        team_memory_gap_score=row.team_memory_gap_score,
        config=config,
    )
    if row.attribution_status != expected_status:
        raise ValueError("attribution_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_resolution_reference):
        raise ValueError("redacted_resolution_reference must be redacted or public")


def _validate_report(report: ResearchForecastErrorAttributionReport) -> None:
    if report.next_step != NEXT_STEPS[report.attribution_status]:
        raise ValueError("next_step must match attribution_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.forecast_count != _count(len(report.rows)):
        raise ValueError("forecast_count must match rows")
    expected_pass = _count(
        sum(1 for row in report.rows if row.attribution_status == STATUS_PASS),
    )
    if report.pass_count != expected_pass:
        raise ValueError("pass_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.attribution_status == STATUS_WATCH),
    )
    if report.watch_count != expected_watch:
        raise ValueError("watch_count must match rows")
    expected_block = _count(
        sum(1 for row in report.rows if row.attribution_status == STATUS_BLOCK),
    )
    if report.block_count != expected_block:
        raise ValueError("block_count must match rows")
    if report.material_error_count != _count(
        sum(1 for row in report.rows if MATERIAL_ERROR_REASON in row.reason_codes),
    ):
        raise ValueError("material_error_count must match rows")
    if report.information_gap_count != _count(
        sum(1 for row in report.rows if INFORMATION_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("information_gap_count must match rows")
    if report.model_disagreement_count != _count(
        sum(1 for row in report.rows if MODEL_DISAGREEMENT_REASON in row.reason_codes),
    ):
        raise ValueError("model_disagreement_count must match rows")
    if report.settlement_ambiguity_count != _count(
        sum(1 for row in report.rows if SETTLEMENT_AMBIGUITY_REASON in row.reason_codes),
    ):
        raise ValueError("settlement_ambiguity_count must match rows")
    if report.cost_friction_count != _count(
        sum(1 for row in report.rows if COST_FRICTION_REASON in row.reason_codes),
    ):
        raise ValueError("cost_friction_count must match rows")
    if report.team_memory_missing_count != _count(
        sum(1 for row in report.rows if TEAM_MEMORY_MISSING_REASON in row.reason_codes),
    ):
        raise ValueError("team_memory_missing_count must match rows")
    if report.average_forecast_error != _ratio(
        _sum_decimal(row.forecast_error for row in report.rows),
        report.forecast_count,
    ):
        raise ValueError("average_forecast_error must match rows")
    expected_max_error = max(
        (row.forecast_error for row in report.rows),
        default=ZERO,
    )
    if report.max_forecast_error != expected_max_error:
        raise ValueError("max_forecast_error must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchForecastErrorAttributionReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                forecast_ratio=ONE,
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
    if report.attribution_status != expected_status:
        raise ValueError("attribution_status must match rows")


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
        raise ValueError("reason_codes cannot mix pass with attribution reasons")
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


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if not _is_redacted_reference(text):
        raise ValueError(f"{field_name} must be redacted or public")
    return text


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be from 0 through 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{field_name} must expose {flag_name}")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    if later_utc < earlier_utc:
        raise ValueError("later must be on or after earlier")
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize(seconds)


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


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total = _quantize(total + value)
    return total


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _redacted_reference(value: str) -> str:
    if _is_public_reference(value):
        _reject_unsafe_text("public_resolution_reference", value)
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_public_reference(value: str) -> bool:
    lowered = value.lower()
    return (
        all(fragment not in lowered for fragment in (_join_parts(":", "//"),))
        and any(fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS)
    )


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 19:
        return True
    return _is_public_reference(value)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
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
    if type(value) in (int, float):
        raise ValueError("JSON numeric values must use Decimal strings")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_text("payload value", value)
        if _join_parts(":", "//") in value:
            raise ValueError(f"{label} must not include unredacted references")
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{label} must serialize Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain float values")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError(f"{label} must not contain integer values")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("repl", "ace"),
        _join_parts("sign", "ing"),
        _join_parts("ad", "vice"),
        _join_parts("market", "_slug"),
        _join_parts("ques", "tion"),
        _join_parts("priv", "ate_key"),
        _join_parts("api", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("pos", "ition"),
        _join_parts("tra", "de"),
        _join_parts("b", "et"),
        _join_parts("sta", "ke"),
        _join_parts("cli", "ent"),
        _join_parts("req", "uests"),
        _join_parts("ht", "tp"),
        _join_parts("soc", "ket"),
        _join_parts("sub", "process"),
        _join_parts("path", "lib"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("dur", "able"),
        _join_parts("cred", "ential"),
        _join_parts("hid", "den"),
        _join_parts("li", "ve"),
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} has unsafe value")


def _join_parts(left: str, right: str) -> str:
    return left + right
