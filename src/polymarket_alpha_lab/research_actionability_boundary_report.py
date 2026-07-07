"""Pure research boundary report for manually screened inputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any, Iterable


DEFAULT_RESEARCH_ACTIONABILITY_BOUNDARY_CONFIG_VERSION = (
    "research-actionability-boundary-report-v0"
)
RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_BASE_REASON_CODE = "research_actionability_boundary"
_MANUAL_SCOPE_REASON_CODE = "manual_screening_only"

_UNSAFE_PARTS = (
    ("can", "didate", "_", "id"),
    ("raw", "_", "can", "didate"),
    ("mar", "ket", "_", "id"),
    ("mar", "ket", "_sl", "ug"),
    ("mar", "ket", "_q", "uest", "ion"),
    ("q", "uest", "ion"),
    ("sou", "rce", "_re", "f"),
    ("sou", "rce", "_u", "rl"),
    ("sou", "rce", "_te", "xt"),
    ("u", "rl"),
    ("ht", "tp"),
    (":", "/", "/"),
    ("d", "sn"),
    ("table", "_name"),
    ("to", "ken"),
    ("sec", "ret"),
    ("private", "_key"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tr", "ade"),
    ("pos", "ition"),
    ("b", "uy"),
    ("se", "ll"),
    ("reco", "mmend"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_PARTS)


@dataclass(frozen=True)
class ResearchActionabilityBoundaryConfig:
    config_version: str = DEFAULT_RESEARCH_ACTIONABILITY_BOUNDARY_CONFIG_VERSION
    min_pass_boundary_score: Decimal = Decimal("0.750000")
    min_watch_boundary_score: Decimal = Decimal("0.500000")
    max_pass_uncertainty_score: Decimal = Decimal("0.300000")
    max_watch_uncertainty_score: Decimal = Decimal("0.600000")
    max_pass_conflict_count: Decimal = Decimal("0")
    max_watch_conflict_count: Decimal = Decimal("1")
    max_pass_missing_check_count: Decimal = Decimal("0")
    max_watch_missing_check_count: Decimal = Decimal("2")
    research_score_weight: Decimal = Decimal("0.500000")
    support_score_weight: Decimal = Decimal("0.300000")
    freshness_score_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchActionabilityBoundaryConfig:
            raise ValueError("config must be a ResearchActionabilityBoundaryConfig")
        _require_safe_code("config_version", self.config_version)
        for field_name in (
            "min_pass_boundary_score",
            "min_watch_boundary_score",
            "max_pass_uncertainty_score",
            "max_watch_uncertainty_score",
            "research_score_weight",
            "support_score_weight",
            "freshness_score_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_conflict_count",
            "max_watch_conflict_count",
            "max_pass_missing_check_count",
            "max_watch_missing_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_boundary_score <= self.min_watch_boundary_score:
            raise ValueError("min_pass_boundary_score must exceed watch threshold")
        if self.max_pass_uncertainty_score > self.max_watch_uncertainty_score:
            raise ValueError("max_pass_uncertainty_score must not exceed watch threshold")
        if self.max_pass_conflict_count > self.max_watch_conflict_count:
            raise ValueError("max_pass_conflict_count must not exceed watch threshold")
        if self.max_pass_missing_check_count > self.max_watch_missing_check_count:
            raise ValueError("max_pass_missing_check_count must not exceed watch threshold")
        if _config_weight_sum(self) != ONE:
            raise ValueError("config weights must sum to 1")
        _require_report_flags("config", self)


@dataclass(frozen=True)
class ResearchActionabilityBoundaryInput:
    research_key: str
    research_score: Decimal
    support_score: Decimal
    freshness_score: Decimal
    uncertainty_score: Decimal
    conflict_count: Decimal
    missing_check_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchActionabilityBoundaryInput:
            raise ValueError("input_value must be a ResearchActionabilityBoundaryInput")
        _require_safe_code("research_key", self.research_key)
        for field_name in (
            "research_score",
            "support_score",
            "freshness_score",
            "uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("conflict_count", "missing_check_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_report_flags("input_value", self)


@dataclass(frozen=True)
class ResearchActionabilityBoundaryRow:
    research_key: str
    research_score: Decimal
    support_score: Decimal
    freshness_score: Decimal
    uncertainty_score: Decimal
    conflict_count: Decimal
    missing_check_count: Decimal
    boundary_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchActionabilityBoundaryRow:
            raise ValueError("row must be a ResearchActionabilityBoundaryRow")
        _require_safe_code("research_key", self.research_key)
        for field_name in (
            "research_score",
            "support_score",
            "freshness_score",
            "uncertainty_score",
            "boundary_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("conflict_count", "missing_check_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_report_flags("row", self)


@dataclass(frozen=True)
class ResearchActionabilityBoundaryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchActionabilityBoundaryReasonCodeCount:
            raise ValueError(
                "reason_code_count must be a ResearchActionabilityBoundaryReasonCodeCount",
            )
        _require_safe_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        _require_report_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchActionabilityBoundaryReport:
    config_version: str
    result_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchActionabilityBoundaryRow, ...]
    reason_code_counts: tuple[ResearchActionabilityBoundaryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchActionabilityBoundaryReport:
            raise ValueError("report must be a ResearchActionabilityBoundaryReport")
        _require_safe_code("config_version", self.config_version)
        for field_name in ("result_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_report_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_actionability_boundary_report_payload(self)


def build_research_actionability_boundary_report(
    rows: Iterable[object],
    *,
    config: ResearchActionabilityBoundaryConfig,
) -> ResearchActionabilityBoundaryReport:
    if type(config) is not ResearchActionabilityBoundaryConfig:
        raise ValueError("config must be a ResearchActionabilityBoundaryConfig")
    _require_report_flags("config", config)
    input_rows = _normalize_input_rows(rows)
    scored_rows = tuple(_row_from_input(value, config) for value in sorted(input_rows, key=lambda item: item.research_key))
    reason_codes = _report_reason_codes(scored_rows)
    return ResearchActionabilityBoundaryReport(
        config_version=config.config_version,
        result_count=_decimal_count(len(scored_rows)),
        pass_count=_decimal_count(_status_count(scored_rows, "pass")),
        watch_count=_decimal_count(_status_count(scored_rows, "watch")),
        block_count=_decimal_count(_status_count(scored_rows, "block")),
        status=_report_status(scored_rows),
        rows=scored_rows,
        reason_code_counts=_reason_code_counts(reason_codes, scored_rows),
        reason_codes=reason_codes,
    )


def research_actionability_boundary_report_payload(
    report: ResearchActionabilityBoundaryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchActionabilityBoundaryReport:
        raise ValueError("report must be a ResearchActionabilityBoundaryReport")
    _require_report_flags("report", report)
    _validate_report_consistency(report)
    payload = _public_json(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_actionability_boundary_public_payload(payload)
    return payload


def validate_research_actionability_boundary_public_payload(
    payload: dict[str, Any],
    *,
    require_flags: bool = True,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_entries(payload)
    _reject_numeric_public_values(payload)
    if require_flags:
        _require_public_payload_flags(payload)
    _require_public_status_values(payload)
    return True


def _row_from_input(
    input_value: ResearchActionabilityBoundaryInput,
    config: ResearchActionabilityBoundaryConfig,
) -> ResearchActionabilityBoundaryRow:
    boundary_score = _normalize_unit_decimal(
        "boundary_score",
        input_value.research_score * config.research_score_weight
        + input_value.support_score * config.support_score_weight
        + input_value.freshness_score * config.freshness_score_weight,
    )
    status = _row_status(input_value, boundary_score, config)
    return ResearchActionabilityBoundaryRow(
        research_key=input_value.research_key,
        research_score=input_value.research_score,
        support_score=input_value.support_score,
        freshness_score=input_value.freshness_score,
        uncertainty_score=input_value.uncertainty_score,
        conflict_count=input_value.conflict_count,
        missing_check_count=input_value.missing_check_count,
        boundary_score=boundary_score,
        status=status,
        reason_codes=_row_reason_codes(input_value, boundary_score, status, config),
    )


def _row_status(
    input_value: ResearchActionabilityBoundaryInput,
    boundary_score: Decimal,
    config: ResearchActionabilityBoundaryConfig,
) -> str:
    if (
        boundary_score < config.min_watch_boundary_score
        or input_value.uncertainty_score > config.max_watch_uncertainty_score
        or input_value.conflict_count > config.max_watch_conflict_count
        or input_value.missing_check_count > config.max_watch_missing_check_count
    ):
        return "block"
    if (
        boundary_score < config.min_pass_boundary_score
        or input_value.uncertainty_score > config.max_pass_uncertainty_score
        or input_value.conflict_count > config.max_pass_conflict_count
        or input_value.missing_check_count > config.max_pass_missing_check_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    input_value: ResearchActionabilityBoundaryInput,
    boundary_score: Decimal,
    status: str,
    config: ResearchActionabilityBoundaryConfig,
) -> tuple[str, ...]:
    values = {
        _MANUAL_SCOPE_REASON_CODE,
        f"{_BASE_REASON_CODE}_{status}",
        f"boundary_score_{_level_at_least(boundary_score, config.min_pass_boundary_score, config.min_watch_boundary_score)}",
        f"uncertainty_score_{_level_at_most(input_value.uncertainty_score, config.max_pass_uncertainty_score, config.max_watch_uncertainty_score)}",
        f"conflict_count_{_level_at_most(input_value.conflict_count, config.max_pass_conflict_count, config.max_watch_conflict_count)}",
        f"missing_check_count_{_level_at_most(input_value.missing_check_count, config.max_pass_missing_check_count, config.max_watch_missing_check_count)}",
    }
    for reason_code in input_value.reason_codes:
        values.add(f"input_{reason_code}")
    return tuple(sorted(values))


def _level_at_least(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value >= pass_threshold:
        return "pass"
    if value >= watch_threshold:
        return "watch"
    return "block"


def _level_at_most(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value <= pass_threshold:
        return "pass"
    if value <= watch_threshold:
        return "watch"
    return "block"


def _report_status(rows: tuple[ResearchActionabilityBoundaryRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchActionabilityBoundaryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            _MANUAL_SCOPE_REASON_CODE,
            "no_sanitized_research_results",
            f"{_BASE_REASON_CODE}_block",
        )
    values = {_MANUAL_SCOPE_REASON_CODE}
    for row in rows:
        values.update(row.reason_codes)
    return tuple(sorted(values))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchActionabilityBoundaryRow, ...],
) -> tuple[ResearchActionabilityBoundaryReasonCodeCount, ...]:
    counts = {reason_code: ZERO for reason_code in reason_codes}
    if not rows:
        for reason_code in reason_codes:
            counts[reason_code] = Decimal("1")
    else:
        for row in rows:
            for reason_code in row.reason_codes:
                counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
        counts[_MANUAL_SCOPE_REASON_CODE] = Decimal(len(rows))
    return tuple(
        ResearchActionabilityBoundaryReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in sorted(counts)
        if counts[reason_code] > ZERO
    )


def _normalize_input_rows(
    rows: Iterable[object],
) -> tuple[ResearchActionabilityBoundaryInput, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchActionabilityBoundaryInput:
            raise ValueError("rows must contain ResearchActionabilityBoundaryInput values")
        _require_report_flags("input_value", value)
    keys = tuple(value.research_key for value in values)
    if len(set(keys)) != len(keys):
        raise ValueError("research_key values must be unique")
    return values


def _normalize_rows(
    rows: object,
) -> tuple[ResearchActionabilityBoundaryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchActionabilityBoundaryRow:
            raise ValueError("rows must contain ResearchActionabilityBoundaryRow values")
        _require_report_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchActionabilityBoundaryReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchActionabilityBoundaryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchActionabilityBoundaryReasonCodeCount values",
            )
        _require_report_flags("reason_code_count", value)
    sorted_values = tuple(sorted(values, key=lambda value: value.reason_code))
    if values != sorted_values:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return values


def _validate_report_consistency(report: ResearchActionabilityBoundaryReport) -> None:
    if report.result_count != _decimal_count(len(report.rows)):
        raise ValueError("result_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(rows: tuple[ResearchActionabilityBoundaryRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _config_weight_sum(config: ResearchActionabilityBoundaryConfig) -> Decimal:
    return _normalize_decimal(
        "config_weight_sum",
        config.research_score_weight
        + config.support_score_weight
        + config.freshness_score_weight,
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_safe_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    integral = normalized.to_integral_value()
    if normalized != integral:
        raise ValueError(f"{field_name} must be a whole count")
    return integral


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_decimal(field_name, value)
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
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of {RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES!r}")


def _require_safe_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    for character in value:
        if not (
            "a" <= character <= "z"
            or "0" <= character <= "9"
            or character in {"_", "-"}
        ):
            raise ValueError(f"{field_name} must contain safe public characters")
    try:
        _reject_unsafe_public_entries(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} contains unsafe public text") from exc


def _require_report_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


def _require_public_status_values(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "status":
                _require_status("status", nested)
            _require_public_status_values(nested)
    elif isinstance(value, list):
        for nested in value:
            _require_public_status_values(nested)


def _reject_unsafe_public_entries(value: object) -> None:
    for item in _iter_public_strings(value):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError("unsafe public payload entry")


def _reject_numeric_public_values(value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, float):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_numeric_public_values(item)


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(nested))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, list):
        items = []
        for nested in value:
            items.extend(_iter_public_strings(nested))
        return tuple(items)
    return ()


def _public_json(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _public_json(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("public value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("public value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            converted[key] = _public_json(nested)
        return converted
    if isinstance(value, tuple):
        return [_public_json(nested) for nested in value]
    if isinstance(value, list):
        return [_public_json(nested) for nested in value]
    raise ValueError("public value must be scalar or container")


__all__ = (
    "DEFAULT_RESEARCH_ACTIONABILITY_BOUNDARY_CONFIG_VERSION",
    "RESEARCH_ACTIONABILITY_BOUNDARY_PUBLIC_STATUSES",
    "ResearchActionabilityBoundaryConfig",
    "ResearchActionabilityBoundaryInput",
    "ResearchActionabilityBoundaryRow",
    "ResearchActionabilityBoundaryReasonCodeCount",
    "ResearchActionabilityBoundaryReport",
    "build_research_actionability_boundary_report",
    "research_actionability_boundary_report_payload",
    "validate_research_actionability_boundary_public_payload",
)
