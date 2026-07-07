"""Pure planning report for research strategy backtest readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_BACKTEST_READINESS_PLAN_CONFIG_VERSION = (
    "research-strategy-backtest-readiness-plan-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
AREA_ORDER = (
    "historical_samples",
    "settlement_labels",
    "fee_assumptions",
    "probability_calibration",
    "team_memory",
)
ALLOWED_LOCAL_SUPABASE_POSTGRES_REQUIREMENTS = frozenset(
    (
        "load_closed_prediction_snapshots",
        "collect_final_resolution_labels",
        "snapshot_fee_schedule_assumptions",
        "bucket_forecast_probabilities",
        "snapshot_team_memory_references",
        "compute_readiness_gaps_locally",
    ),
)
PUBLIC_IDENTIFIER_FRAGMENTS = frozenset(("dsn", "table", "token", "source", "market"))
TRADING_ADVICE_FRAGMENTS = frozenset(
    ("buy", "sell", "bet", "stake", "position", "entry", "exit", "contract")
)


@dataclass(frozen=True)
class ResearchStrategyBacktestReadinessPlanConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_BACKTEST_READINESS_PLAN_CONFIG_VERSION
    min_historical_sample_count: Decimal = Decimal("100.000000")
    min_settlement_label_coverage_ratio: Decimal = Decimal("0.950000")
    min_fee_assumption_count: Decimal = Decimal("2.000000")
    min_calibration_bucket_count: Decimal = Decimal("5.000000")
    max_probability_calibration_error: Decimal = Decimal("0.030000")
    min_team_memory_reference_count: Decimal = Decimal("3.000000")
    min_team_memory_coverage_ratio: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyBacktestReadinessPlanConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_historical_sample_count",
            "min_fee_assumption_count",
            "min_calibration_bucket_count",
            "min_team_memory_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_settlement_label_coverage_ratio",
            "max_probability_calibration_error",
            "min_team_memory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_positive_threshold(
            "min_historical_sample_count",
            self.min_historical_sample_count,
        )
        _require_positive_threshold(
            "min_fee_assumption_count",
            self.min_fee_assumption_count,
        )
        _require_positive_threshold(
            "min_calibration_bucket_count",
            self.min_calibration_bucket_count,
        )
        _require_positive_threshold(
            "min_team_memory_reference_count",
            self.min_team_memory_reference_count,
        )
        require_paper_only_flags("research strategy backtest readiness plan config", self)


@dataclass(frozen=True)
class ResearchStrategyBacktestReadinessPlanInput:
    strategy_family: str
    historical_sample_count: Decimal
    settled_label_count: Decimal
    unresolved_label_count: Decimal
    ambiguous_label_count: Decimal
    fee_assumption_count: Decimal
    fee_model_documented: bool
    calibration_bucket_count: Decimal
    mean_absolute_calibration_error: Decimal
    team_memory_reference_count: Decimal
    team_memory_coverage_ratio: Decimal
    local_supabase_postgres_plan: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyBacktestReadinessPlanInput:
            raise ValueError("input must be exact")
        _require_canonical_string("strategy_family", self.strategy_family)
        for field_name in (
            "historical_sample_count",
            "fee_assumption_count",
            "calibration_bucket_count",
            "team_memory_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settled_label_count",
            "unresolved_label_count",
            "ambiguous_label_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_absolute_calibration_error",
            _normalize_probability(
                "mean_absolute_calibration_error",
                self.mean_absolute_calibration_error,
            ),
        )
        object.__setattr__(
            self,
            "team_memory_coverage_ratio",
            _normalize_probability(
                "team_memory_coverage_ratio",
                self.team_memory_coverage_ratio,
            ),
        )
        if type(self.fee_model_documented) is not bool:
            raise ValueError("fee_model_documented must be a bool")
        object.__setattr__(
            self,
            "local_supabase_postgres_plan",
            _normalize_local_requirements(
                "local_supabase_postgres_plan",
                self.local_supabase_postgres_plan,
            ),
        )
        _validate_input(self)
        require_paper_only_flags("research strategy backtest readiness plan input", self)


@dataclass(frozen=True)
class ResearchStrategyBacktestReadinessPlanRow:
    area: str
    status: str
    observed_value: Decimal
    required_value: Decimal
    coverage_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyBacktestReadinessPlanRow:
            raise ValueError("row must be exact")
        _require_member("area", self.area, frozenset(AREA_ORDER))
        _require_member("status", self.status, STATUSES)
        for field_name in ("observed_value", "required_value"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_probability("coverage_ratio", self.coverage_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("research strategy backtest readiness plan row", self)


@dataclass(frozen=True)
class ResearchStrategyBacktestReadinessPlanReport:
    generated_at: datetime
    config_version: str
    area_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyBacktestReadinessPlanRow, ...]
    local_supabase_postgres_requirements: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyBacktestReadinessPlanReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("area_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "local_supabase_postgres_requirements",
            _normalize_local_requirements(
                "local_supabase_postgres_requirements",
                self.local_supabase_postgres_requirements,
            ),
        )
        _validate_report(self)
        require_paper_only_flags("research strategy backtest readiness plan report", self)
        reject_unsafe_surface_fields("research strategy backtest readiness plan report", self)
        _reject_public_identifiers("research strategy backtest readiness plan report", self)
        _reject_trading_advice("research strategy backtest readiness plan report", self)
        _set_or_validate_derived_validation_digest(self)


def build_research_strategy_backtest_readiness_plan(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
    *,
    config: ResearchStrategyBacktestReadinessPlanConfig,
    generated_at: datetime,
) -> ResearchStrategyBacktestReadinessPlanReport:
    if type(config) is not ResearchStrategyBacktestReadinessPlanConfig:
        raise ValueError("config must be a ResearchStrategyBacktestReadinessPlanConfig")
    if type(readiness_input) is not ResearchStrategyBacktestReadinessPlanInput:
        raise ValueError("readiness_input must be a ResearchStrategyBacktestReadinessPlanInput")
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("research strategy backtest readiness plan config", config)
    require_paper_only_flags(
        "research strategy backtest readiness plan input",
        readiness_input,
    )
    rows = (
        _historical_samples_row(readiness_input, config),
        _settlement_labels_row(readiness_input, config),
        _fee_assumptions_row(readiness_input, config),
        _probability_calibration_row(readiness_input, config),
        _team_memory_row(readiness_input, config),
    )
    return ResearchStrategyBacktestReadinessPlanReport(
        generated_at=generated_at,
        config_version=config.config_version,
        area_count=Decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        local_supabase_postgres_requirements=_report_requirements(readiness_input),
    )


def research_strategy_backtest_readiness_plan_payload(
    report: ResearchStrategyBacktestReadinessPlanReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyBacktestReadinessPlanReport:
        raise ValueError("report must be a ResearchStrategyBacktestReadinessPlanReport")
    require_paper_only_flags("research strategy backtest readiness plan report", report)
    reject_unsafe_surface_fields("research strategy backtest readiness plan report", report)
    _reject_public_identifiers("research strategy backtest readiness plan report", report)
    _reject_trading_advice("research strategy backtest readiness plan report", report)
    payload = json_ready_no_floats(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("research strategy backtest readiness plan payload", payload)
    _reject_public_identifiers("research strategy backtest readiness plan payload", payload)
    _reject_trading_advice("research strategy backtest readiness plan payload", payload)
    return payload


def _historical_samples_row(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
    config: ResearchStrategyBacktestReadinessPlanConfig,
) -> ResearchStrategyBacktestReadinessPlanRow:
    observed = readiness_input.historical_sample_count
    required = config.min_historical_sample_count
    if observed == ZERO:
        status = "block"
        reason_codes = ("historical_sample_count_block",)
    elif observed < required:
        status = "watch"
        reason_codes = ("historical_sample_count_watch",)
    else:
        status = "pass"
        reason_codes = ("historical_sample_count_pass",)
    return ResearchStrategyBacktestReadinessPlanRow(
        area="historical_samples",
        status=status,
        observed_value=observed,
        required_value=required,
        coverage_ratio=_coverage_ratio(observed, required),
        reason_codes=reason_codes,
    )


def _settlement_labels_row(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
    config: ResearchStrategyBacktestReadinessPlanConfig,
) -> ResearchStrategyBacktestReadinessPlanRow:
    total = (
        readiness_input.settled_label_count
        + readiness_input.unresolved_label_count
        + readiness_input.ambiguous_label_count
    )
    coverage = _coverage_ratio(readiness_input.settled_label_count, total)
    required = _decimal_product(total, config.min_settlement_label_coverage_ratio)
    reason_codes: list[str] = []
    status = "pass"
    if readiness_input.ambiguous_label_count > ZERO:
        reason_codes.append("ambiguous_settlement_labels_present")
        status = "block"
    if readiness_input.settled_label_count == ZERO:
        reason_codes.append("settlement_label_count_block")
        status = "block"
    if coverage < config.min_settlement_label_coverage_ratio:
        reason_codes.append("settlement_label_coverage_watch")
        if status != "block":
            status = "watch"
    if not reason_codes:
        reason_codes.append("settlement_label_coverage_pass")
    return ResearchStrategyBacktestReadinessPlanRow(
        area="settlement_labels",
        status=status,
        observed_value=readiness_input.settled_label_count,
        required_value=required,
        coverage_ratio=coverage,
        reason_codes=tuple(reason_codes),
    )


def _fee_assumptions_row(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
    config: ResearchStrategyBacktestReadinessPlanConfig,
) -> ResearchStrategyBacktestReadinessPlanRow:
    observed = readiness_input.fee_assumption_count
    required = config.min_fee_assumption_count
    reason_codes: list[str] = []
    status = "pass"
    if observed == ZERO:
        reason_codes.append("fee_assumption_count_block")
        status = "block"
    elif observed < required:
        reason_codes.append("fee_assumption_count_watch")
        status = "watch"
    if not readiness_input.fee_model_documented:
        reason_codes.append("fee_model_not_documented")
        status = "block"
    if not reason_codes:
        reason_codes.append("fee_assumption_plan_pass")
    return ResearchStrategyBacktestReadinessPlanRow(
        area="fee_assumptions",
        status=status,
        observed_value=observed,
        required_value=required,
        coverage_ratio=_coverage_ratio(observed, required),
        reason_codes=tuple(reason_codes),
    )


def _probability_calibration_row(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
    config: ResearchStrategyBacktestReadinessPlanConfig,
) -> ResearchStrategyBacktestReadinessPlanRow:
    observed = readiness_input.calibration_bucket_count
    required = config.min_calibration_bucket_count
    reason_codes: list[str] = []
    status = "pass"
    if observed == ZERO:
        reason_codes.append("calibration_bucket_count_block")
        status = "block"
    elif observed < required:
        reason_codes.append("calibration_bucket_count_watch")
        status = "watch"
    if readiness_input.mean_absolute_calibration_error > config.max_probability_calibration_error:
        reason_codes.append("calibration_error_watch")
        if status != "block":
            status = "watch"
    if not reason_codes:
        reason_codes.append("probability_calibration_plan_pass")
    return ResearchStrategyBacktestReadinessPlanRow(
        area="probability_calibration",
        status=status,
        observed_value=observed,
        required_value=required,
        coverage_ratio=_coverage_ratio(observed, required),
        reason_codes=tuple(reason_codes),
    )


def _team_memory_row(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
    config: ResearchStrategyBacktestReadinessPlanConfig,
) -> ResearchStrategyBacktestReadinessPlanRow:
    observed = readiness_input.team_memory_reference_count
    required = config.min_team_memory_reference_count
    reason_codes: list[str] = []
    status = "pass"
    if observed == ZERO:
        reason_codes.append("team_memory_reference_count_block")
        status = "block"
    elif observed < required:
        reason_codes.append("team_memory_reference_count_watch")
        status = "watch"
    elif readiness_input.team_memory_coverage_ratio < config.min_team_memory_coverage_ratio:
        reason_codes.append("team_memory_coverage_watch")
        status = "watch"
    if not reason_codes:
        reason_codes.append("team_memory_plan_pass")
    return ResearchStrategyBacktestReadinessPlanRow(
        area="team_memory",
        status=status,
        observed_value=observed,
        required_value=required,
        coverage_ratio=readiness_input.team_memory_coverage_ratio,
        reason_codes=tuple(reason_codes),
    )


def _report_requirements(
    readiness_input: ResearchStrategyBacktestReadinessPlanInput,
) -> tuple[str, ...]:
    requirements = list(readiness_input.local_supabase_postgres_plan)
    if "compute_readiness_gaps_locally" not in requirements:
        requirements.append("compute_readiness_gaps_locally")
    return tuple(requirements)


def _status_count(
    rows: tuple[ResearchStrategyBacktestReadinessPlanRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status))


def _report_status(rows: tuple[ResearchStrategyBacktestReadinessPlanRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyBacktestReadinessPlanRow, ...],
) -> tuple[str, ...]:
    has_block = any(row.status == "block" for row in rows)
    has_watch = any(row.status == "watch" for row in rows)
    if has_block and has_watch:
        return ("blocked_backtest_readiness_area", "watch_backtest_readiness_area")
    if has_block:
        return ("blocked_backtest_readiness_area",)
    if has_watch:
        return ("watch_backtest_readiness_area",)
    return ("research_strategy_backtest_readiness_plan_pass",)


def _coverage_ratio(observed: Decimal, required: Decimal) -> Decimal:
    if required <= ZERO:
        return ONE if observed > ZERO else ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = observed / required
    if ratio > ONE:
        return ONE
    if ratio < ZERO:
        return ZERO
    return _quantize_decimal(ratio)


def _decimal_product(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left * right)


def _validate_input(readiness_input: ResearchStrategyBacktestReadinessPlanInput) -> None:
    label_counts = (
        readiness_input.settled_label_count,
        readiness_input.unresolved_label_count,
        readiness_input.ambiguous_label_count,
    )
    if any(value < ZERO for value in label_counts):
        raise ValueError("settlement label counts must be nonnegative")


def _validate_report(report: ResearchStrategyBacktestReadinessPlanReport) -> None:
    rows = report.rows
    if tuple(row.area for row in rows) != AREA_ORDER:
        raise ValueError("rows must match readiness area order")
    expected_area_count = Decimal(len(rows))
    expected_pass_count = _status_count(rows, "pass")
    expected_watch_count = _status_count(rows, "watch")
    expected_block_count = _status_count(rows, "block")
    if report.area_count != expected_area_count:
        raise ValueError("area_count must match rows")
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match rows")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row statuses")


def _normalize_rows(value: object) -> tuple[ResearchStrategyBacktestReadinessPlanRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple of rows")
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple of rows")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyBacktestReadinessPlanRow:
            raise ValueError("rows must contain ResearchStrategyBacktestReadinessPlanRow values")
    return rows


def _normalize_local_requirements(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple of strings")
    requirements = tuple(value)
    if not requirements:
        raise ValueError(f"{field_name} must contain at least one requirement")
    if len(set(requirements)) != len(requirements):
        raise ValueError(f"{field_name} must not contain duplicates")
    for requirement in requirements:
        _require_canonical_string(field_name, requirement)
        if any(fragment in requirement for fragment in PUBLIC_IDENTIFIER_FRAGMENTS):
            raise ValueError(f"{field_name} contains public identifier")
        if requirement not in ALLOWED_LOCAL_SUPABASE_POSTGRES_REQUIREMENTS:
            raise ValueError(f"{field_name} contains unsupported requirement")
    return requirements


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple of strings")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _require_positive_threshold(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-.")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(sorted(allowed))}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _set_or_validate_derived_validation_digest(
    report: ResearchStrategyBacktestReadinessPlanReport,
) -> None:
    current = report.derived_validation_digest
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if current != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _derived_validation_digest(report: ResearchStrategyBacktestReadinessPlanReport) -> str:
    material = asdict(report)
    material["derived_validation_digest"] = ""
    ready = json_ready_no_floats(material)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reject_public_identifiers(label: str, value: object) -> None:
    for text in _iter_string_values(value):
        normalized = text.lower()
        if any(fragment in normalized for fragment in PUBLIC_IDENTIFIER_FRAGMENTS):
            raise ValueError(f"public identifier is not allowed in {label}")


def _reject_trading_advice(label: str, value: object) -> None:
    for text in _iter_string_values(value):
        normalized = text.lower()
        if any(fragment in normalized for fragment in TRADING_ADVICE_FRAGMENTS):
            raise ValueError(f"trading advice is not allowed in {label}")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_string_values(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            items.append(key)
            items.extend(_iter_string_values(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_string_values(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_BACKTEST_READINESS_PLAN_CONFIG_VERSION",
    "PUBLIC_IDENTIFIER_FRAGMENTS",
    "ResearchStrategyBacktestReadinessPlanConfig",
    "ResearchStrategyBacktestReadinessPlanInput",
    "ResearchStrategyBacktestReadinessPlanReport",
    "ResearchStrategyBacktestReadinessPlanRow",
    "build_research_strategy_backtest_readiness_plan",
    "research_strategy_backtest_readiness_plan_payload",
)
