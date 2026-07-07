"""Pure report-only coverage checks for research market categories.

The module is deterministic and side-effect free. Callers provide typed category
coverage rows; the policy returns pass/watch/blocked status rows and a public
payload with Decimal values serialized as strings.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchMarketCategoryCoverageConfig",
    "ResearchMarketCategoryCoverageInputRow",
    "ResearchMarketCategoryCoverageReasonCodeCount",
    "ResearchMarketCategoryCoverageReport",
    "ResearchMarketCategoryCoverageScoreRow",
    "build_research_market_category_coverage_report",
    "research_market_category_coverage_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-category-coverage-v0"
DEFAULT_TARGET_CATEGORIES = (
    "basketball",
    "btc",
    "equity_index",
    "gold",
    "politics",
    "soccer",
)
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_COVERAGE_SCORE = Decimal("0.750000")
DEFAULT_WATCH_COVERAGE_SCORE = Decimal("0.400000")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketCategoryCoverageConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    target_categories: tuple[str, ...] = DEFAULT_TARGET_CATEGORIES
    min_candidate_count: Decimal = Decimal("3")
    min_source_family_count: Decimal = Decimal("3")
    min_team_count: Decimal = Decimal("2")
    pass_coverage_score: Decimal = DEFAULT_PASS_COVERAGE_SCORE
    watch_coverage_score: Decimal = DEFAULT_WATCH_COVERAGE_SCORE
    candidate_weight: Decimal = Decimal("0.400000")
    source_weight: Decimal = Decimal("0.350000")
    team_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "target_categories",
            _normalize_string_tuple(
                "target_categories",
                self.target_categories,
                allow_empty=False,
                require_sorted=True,
            ),
        )
        for field_name in (
            "min_candidate_count",
            "min_source_family_count",
            "min_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_coverage_score",
            "watch_coverage_score",
            "candidate_weight",
            "source_weight",
            "team_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_coverage_score <= self.watch_coverage_score:
            raise ValueError("pass_coverage_score must be greater than watch_coverage_score")
        weight_sum = _quantize(
            self.candidate_weight + self.source_weight + self.team_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "candidate_weight, source_weight, and team_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketCategoryCoverageInputRow:
    category: str
    candidate_id: str
    source_families: tuple[str, ...]
    team_names: tuple[str, ...]
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("category", self.category)
        _require_identifier("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "source_families",
            _normalize_string_tuple(
                "source_families",
                self.source_families,
                allow_empty=True,
                require_sorted=False,
            ),
        )
        object.__setattr__(
            self,
            "team_names",
            _normalize_string_tuple(
                "team_names",
                self.team_names,
                allow_empty=True,
                require_sorted=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input_row", self)


@dataclass(frozen=True)
class ResearchMarketCategoryCoverageScoreRow:
    category: str
    input_row_count: Decimal
    candidate_count: Decimal
    source_family_count: Decimal
    team_count: Decimal
    candidate_coverage_score: Decimal
    source_coverage_score: Decimal
    team_coverage_score: Decimal
    coverage_score: Decimal
    candidate_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    team_names: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("category", self.category)
        for field_name in (
            "input_row_count",
            "candidate_count",
            "source_family_count",
            "team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "candidate_coverage_score",
            "source_coverage_score",
            "team_coverage_score",
            "coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("candidate_ids", "source_families", "team_names"):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=True,
                    require_sorted=True,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("score_row", self)
        _validate_score_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketCategoryCoverageReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketCategoryCoverageReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_coverage_score: Decimal
    status: str
    rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...]
    reason_code_counts: tuple[ResearchMarketCategoryCoverageReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "category_count",
            "input_row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_coverage_score",
            _require_probability_decimal(
                "average_coverage_score",
                self.average_coverage_score,
            ),
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
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_category_coverage_report(
    input_rows: Iterable[object],
    *,
    config: ResearchMarketCategoryCoverageConfig,
    generated_at: datetime,
) -> ResearchMarketCategoryCoverageReport:
    if type(config) is not ResearchMarketCategoryCoverageConfig:
        raise ValueError("config must be a ResearchMarketCategoryCoverageConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_input_rows(input_rows)
    target_categories = frozenset(config.target_categories)
    unknown_categories = tuple(
        sorted({item.category for item in input_items if item.category not in target_categories}),
    )
    if unknown_categories:
        raise ValueError("input row category must be present in target_categories")

    grouped: dict[str, list[ResearchMarketCategoryCoverageInputRow]] = {
        category: [] for category in config.target_categories
    }
    for item in input_items:
        grouped[item.category].append(item)

    rows = tuple(
        _score_row_from_category(
            category=category,
            input_rows=tuple(grouped[category]),
            config=config,
        )
        for category in config.target_categories
    )
    reason_codes = _summary_reason_codes(rows, input_items)

    return ResearchMarketCategoryCoverageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_decimal_count(len(rows)),
        input_row_count=_decimal_count(len(input_items)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_coverage_score=_average_coverage_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_market_category_coverage_report_payload(
    report: ResearchMarketCategoryCoverageReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketCategoryCoverageReport:
        raise ValueError("report must be a ResearchMarketCategoryCoverageReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _score_row_from_category(
    *,
    category: str,
    input_rows: tuple[ResearchMarketCategoryCoverageInputRow, ...],
    config: ResearchMarketCategoryCoverageConfig,
) -> ResearchMarketCategoryCoverageScoreRow:
    sorted_rows = tuple(
        sorted(
            input_rows,
            key=lambda item: (
                item.candidate_id,
                item.category,
                item.source_families,
                item.team_names,
            ),
        ),
    )
    candidate_ids = tuple(sorted({item.candidate_id for item in sorted_rows}))
    source_families = tuple(
        sorted({source for item in sorted_rows for source in item.source_families}),
    )
    team_names = tuple(sorted({team for item in sorted_rows for team in item.team_names}))
    candidate_score = _coverage_ratio(
        len(candidate_ids),
        config.min_candidate_count,
    )
    source_score = _coverage_ratio(
        len(source_families),
        config.min_source_family_count,
    )
    team_score = _coverage_ratio(
        len(team_names),
        config.min_team_count,
    )
    coverage_score = _quantize(
        (candidate_score * config.candidate_weight)
        + (source_score * config.source_weight)
        + (team_score * config.team_weight),
    )
    status = _row_status(
        candidate_count=len(candidate_ids),
        source_family_count=len(source_families),
        team_count=len(team_names),
        coverage_score=coverage_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        input_row_count=len(sorted_rows),
        candidate_count=len(candidate_ids),
        source_family_count=len(source_families),
        team_count=len(team_names),
        config=config,
        input_reason_codes=tuple(
            reason_code for item in sorted_rows for reason_code in item.reason_codes
        ),
    )

    return ResearchMarketCategoryCoverageScoreRow(
        category=category,
        input_row_count=_decimal_count(len(sorted_rows)),
        candidate_count=_decimal_count(len(candidate_ids)),
        source_family_count=_decimal_count(len(source_families)),
        team_count=_decimal_count(len(team_names)),
        candidate_coverage_score=candidate_score,
        source_coverage_score=source_score,
        team_coverage_score=team_score,
        coverage_score=coverage_score,
        candidate_ids=candidate_ids,
        source_families=source_families,
        team_names=team_names,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    input_rows: Iterable[object],
) -> tuple[ResearchMarketCategoryCoverageInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable")
    try:
        values = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable") from exc
    return tuple(_coerce_input_row(value) for value in values)


def _coerce_input_row(value: object) -> ResearchMarketCategoryCoverageInputRow:
    if type(value) is ResearchMarketCategoryCoverageInputRow:
        _require_hard_flags("input_row", value)
        return value
    _require_hard_flags("input_row", value)
    return ResearchMarketCategoryCoverageInputRow(
        category=_field_value(value, "category"),
        candidate_id=_field_value(value, "candidate_id"),
        source_families=_field_value(value, "source_families"),
        team_names=_field_value(value, "team_names"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _coverage_ratio(count: int, minimum: Decimal) -> Decimal:
    return _quantize(min(ONE, Decimal(count) / minimum))


def _row_status(
    *,
    candidate_count: int,
    source_family_count: int,
    team_count: int,
    coverage_score: Decimal,
    config: ResearchMarketCategoryCoverageConfig,
) -> str:
    if candidate_count == 0 or source_family_count == 0 or team_count == 0:
        return "blocked"
    if coverage_score < config.watch_coverage_score:
        return "blocked"
    if coverage_score < config.pass_coverage_score:
        return "watch"
    if (
        Decimal(candidate_count) < config.min_candidate_count
        or Decimal(source_family_count) < config.min_source_family_count
        or Decimal(team_count) < config.min_team_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    input_row_count: int,
    candidate_count: int,
    source_family_count: int,
    team_count: int,
    config: ResearchMarketCategoryCoverageConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"research_market_category_coverage_{status}"}
    if input_row_count == 0:
        reason_codes.add("no_category_coverage")
    reason_codes.add(
        _coverage_reason(
            count=candidate_count,
            minimum=config.min_candidate_count,
            none_code="no_candidates",
            low_code="not_enough_candidates",
            met_code="candidate_coverage_met",
        ),
    )
    reason_codes.add(
        _coverage_reason(
            count=source_family_count,
            minimum=config.min_source_family_count,
            none_code="no_source_family_coverage",
            low_code="not_enough_source_families",
            met_code="source_family_coverage_met",
        ),
    )
    reason_codes.add(
        _coverage_reason(
            count=team_count,
            minimum=config.min_team_count,
            none_code="no_team_coverage",
            low_code="not_enough_team_coverage",
            met_code="team_coverage_met",
        ),
    )
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _coverage_reason(
    *,
    count: int,
    minimum: Decimal,
    none_code: str,
    low_code: str,
    met_code: str,
) -> str:
    if count == 0:
        return none_code
    if Decimal(count) < minimum:
        return low_code
    return met_code


def _summary_reason_codes(
    rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...],
    input_rows: tuple[ResearchMarketCategoryCoverageInputRow, ...],
) -> tuple[str, ...]:
    if not input_rows:
        return ("no_category_coverage",)
    if all(row.status == "pass" for row in rows):
        return ("research_market_category_coverage_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...],
) -> tuple[ResearchMarketCategoryCoverageReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketCategoryCoverageReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_coverage_score(
    rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(sum((row.coverage_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchMarketCategoryCoverageScoreRow, ...],
) -> tuple[ResearchMarketCategoryCoverageScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketCategoryCoverageScoreRow:
            raise ValueError(
                "rows must contain ResearchMarketCategoryCoverageScoreRow values",
            )
        _require_hard_flags("score_row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.category))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by category")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketCategoryCoverageReasonCodeCount, ...],
) -> tuple[ResearchMarketCategoryCoverageReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketCategoryCoverageReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCategoryCoverageReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_score_row_consistency(
    row: ResearchMarketCategoryCoverageScoreRow,
) -> None:
    if row.candidate_count > row.input_row_count:
        raise ValueError("candidate_count must not exceed input_row_count")
    if row.candidate_count != _decimal_count(len(row.candidate_ids)):
        raise ValueError("candidate_ids must match candidate_count")
    if row.source_family_count != _decimal_count(len(row.source_families)):
        raise ValueError("source_families must match source_family_count")
    if row.team_count != _decimal_count(len(row.team_names)):
        raise ValueError("team_names must match team_count")
    if row.status == "pass" and row.coverage_score < DEFAULT_PASS_COVERAGE_SCORE:
        raise ValueError("coverage_score must support pass status")
    if row.status == "blocked" and (
        row.candidate_count > ZERO
        and row.source_family_count > ZERO
        and row.team_count > ZERO
        and row.coverage_score >= DEFAULT_WATCH_COVERAGE_SCORE
    ):
        raise ValueError("coverage_score must support blocked status")


def _validate_report_consistency(report: ResearchMarketCategoryCoverageReport) -> None:
    if report.category_count != _decimal_count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.input_row_count != sum((row.input_row_count for row in report.rows), ZERO):
        raise ValueError("input_row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_coverage_score != _average_coverage_score(report.rows):
        raise ValueError("average_coverage_score must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = (
        ("no_category_coverage",)
        if report.input_row_count == ZERO
        else tuple(sorted({code for row in report.rows for code in row.reason_codes}))
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
    require_sorted: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_identifier(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    deduped = tuple(sorted(set(normalized)))
    if require_sorted and tuple(normalized) != deduped:
        raise ValueError(f"{field_name} must be sorted and unique")
    return deduped


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_identifier(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    allowed = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_-.")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use public identifier characters")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
