"""Pure research report for model/team/market probability disagreement.

The module is deterministic and side-effect free. Callers provide typed
probability rows; the policy returns report-only disagreement metrics, statuses,
and reason codes without trading, persistence, or network behavior.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_DISAGREEMENT_TRACKER_CONFIG_VERSION",
    "ResearchProbabilityDisagreementConfig",
    "ResearchProbabilityDisagreementInput",
    "ResearchProbabilityDisagreementReport",
    "ResearchProbabilityDisagreementRow",
    "build_research_probability_disagreement_report",
    "research_probability_disagreement_report_payload",
)


DEFAULT_RESEARCH_PROBABILITY_DISAGREEMENT_TRACKER_CONFIG_VERSION = (
    "research-probability-disagreement-tracker-v0"
)
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
THREE = Decimal("3")
QUANTUM = Decimal("0.000001")
STATUS_SEVERITY = {"block": 2, "watch": 1, "pass": 0}
SENSITIVE_PUBLIC_TOKENS = (
    "auth",
    "api_key",
    "private",
    "secret",
    "token",
    "wallet",
)
ADVICE_PUBLIC_PHRASES = (
    "buy yes",
    "buy no",
    "sell yes",
    "sell no",
    "place order",
    "submit order",
    "trade this",
)


@dataclass(frozen=True)
class ResearchProbabilityDisagreementConfig:
    config_version: str = DEFAULT_RESEARCH_PROBABILITY_DISAGREEMENT_TRACKER_CONFIG_VERSION
    watch_disagreement_threshold: Decimal = Decimal("0.050000")
    block_disagreement_threshold: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_disagreement_threshold",
            _require_probability_decimal(
                "watch_disagreement_threshold",
                self.watch_disagreement_threshold,
            ),
        )
        object.__setattr__(
            self,
            "block_disagreement_threshold",
            _require_probability_decimal(
                "block_disagreement_threshold",
                self.block_disagreement_threshold,
            ),
        )
        if self.watch_disagreement_threshold <= ZERO:
            raise ValueError("watch_disagreement_threshold must be greater than 0")
        if self.block_disagreement_threshold <= self.watch_disagreement_threshold:
            raise ValueError(
                "block_disagreement_threshold must be greater than watch_disagreement_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchProbabilityDisagreementInput:
    market_slug: str
    model_probability: Decimal
    team_probability: Decimal
    market_implied_probability: Decimal
    observed_at: datetime
    public_notes: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "model_probability",
            "team_probability",
            "market_implied_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_canonical_string("public_notes", self.public_notes)
        _reject_unsafe_public_text("public_notes", self.public_notes)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchProbabilityDisagreementRow:
    market_slug: str
    observed_at: datetime
    model_probability: Decimal
    team_probability: Decimal
    market_implied_probability: Decimal
    model_team_abs_disagreement: Decimal
    model_market_abs_disagreement: Decimal
    team_market_abs_disagreement: Decimal
    max_abs_disagreement: Decimal
    average_abs_disagreement: Decimal
    status: str
    reason_codes: tuple[str, ...]
    public_notes: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "team_probability",
            "market_implied_probability",
            "model_team_abs_disagreement",
            "model_market_abs_disagreement",
            "team_market_abs_disagreement",
            "max_abs_disagreement",
            "average_abs_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_canonical_string("public_notes", self.public_notes)
        _reject_unsafe_public_text("public_notes", self.public_notes)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchProbabilityDisagreementReport:
    generated_at: datetime
    config_version: str
    status: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    largest_abs_disagreement: Decimal
    average_max_abs_disagreement: Decimal
    rows: tuple[ResearchProbabilityDisagreementRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "largest_abs_disagreement",
            "average_max_abs_disagreement",
        ):
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_probability_disagreement_report(
    rows: Iterable[object],
    *,
    config: ResearchProbabilityDisagreementConfig,
    generated_at: datetime,
) -> ResearchProbabilityDisagreementReport:
    if type(config) is not ResearchProbabilityDisagreementConfig:
        raise ValueError("config must be a ResearchProbabilityDisagreementConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    for row in input_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("rows observed_at must not be after generated_at")

    report_rows = tuple(
        sorted(
            (
                _build_row(
                    row,
                    watch_threshold=config.watch_disagreement_threshold,
                    block_threshold=config.block_disagreement_threshold,
                )
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    return ResearchProbabilityDisagreementReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_summary_status(reason_codes),
        market_count=_decimal_count(len(report_rows)),
        pass_count=_decimal_count(_status_count(report_rows, "pass")),
        watch_count=_decimal_count(_status_count(report_rows, "watch")),
        block_count=_decimal_count(_status_count(report_rows, "block")),
        largest_abs_disagreement=_largest_abs_disagreement(report_rows),
        average_max_abs_disagreement=_average_max_abs_disagreement(report_rows),
        rows=report_rows,
        reason_code_counts=_row_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_probability_disagreement_report_payload(
    report: ResearchProbabilityDisagreementReport,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilityDisagreementReport:
        raise ValueError("report must be a ResearchProbabilityDisagreementReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _build_row(
    row: ResearchProbabilityDisagreementInput,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> ResearchProbabilityDisagreementRow:
    model_team = _quantize(abs(row.model_probability - row.team_probability))
    model_market = _quantize(abs(row.model_probability - row.market_implied_probability))
    team_market = _quantize(abs(row.team_probability - row.market_implied_probability))
    max_disagreement = max(model_team, model_market, team_market)
    average_disagreement = _quantize((model_team + model_market + team_market) / THREE)
    status = _row_status(max_disagreement, watch_threshold=watch_threshold, block_threshold=block_threshold)
    reason_codes = _row_reason_codes(
        status=status,
        model_team=model_team,
        model_market=model_market,
        team_market=team_market,
        watch_threshold=watch_threshold,
    )
    return ResearchProbabilityDisagreementRow(
        market_slug=row.market_slug,
        observed_at=row.observed_at,
        model_probability=row.model_probability,
        team_probability=row.team_probability,
        market_implied_probability=row.market_implied_probability,
        model_team_abs_disagreement=model_team,
        model_market_abs_disagreement=model_market,
        team_market_abs_disagreement=team_market,
        max_abs_disagreement=max_disagreement,
        average_abs_disagreement=average_disagreement,
        status=status,
        reason_codes=reason_codes,
        public_notes=row.public_notes,
    )


def _row_status(
    max_disagreement: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if max_disagreement >= block_threshold:
        return "block"
    if max_disagreement >= watch_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    model_team: Decimal,
    model_market: Decimal,
    team_market: Decimal,
    watch_threshold: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = [f"probability_disagreement_{status}"]
    if model_market >= watch_threshold:
        codes.append("probability_disagreement_model_market")
    if model_team >= watch_threshold:
        codes.append("probability_disagreement_model_team")
    if team_market >= watch_threshold:
        codes.append("probability_disagreement_team_market")
    return tuple(sorted(codes))


def _report_reason_codes(rows: tuple[ResearchProbabilityDisagreementRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("probability_disagreement_missing_inputs",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if "probability_disagreement_missing_inputs" in reason_codes:
        return "block"
    if "probability_disagreement_block" in reason_codes:
        return "block"
    if "probability_disagreement_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(reason_codes: tuple[str, ...]) -> tuple[tuple[str, Decimal], ...]:
    counts = Counter(reason_codes)
    return tuple((reason_code, _decimal_count(counts[reason_code])) for reason_code in sorted(counts))


def _row_reason_code_counts(
    rows: tuple[ResearchProbabilityDisagreementRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return _reason_code_counts(report_reason_codes)
    return _reason_code_counts(tuple(code for row in rows for code in row.reason_codes))


def _status_count(rows: tuple[ResearchProbabilityDisagreementRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _largest_abs_disagreement(rows: tuple[ResearchProbabilityDisagreementRow, ...]) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return max(row.max_abs_disagreement for row in rows)


def _average_max_abs_disagreement(rows: tuple[ResearchProbabilityDisagreementRow, ...]) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return _quantize(sum((row.max_abs_disagreement for row in rows), ZERO) / _decimal_count(len(rows)))


def _row_sort_key(row: ResearchProbabilityDisagreementRow) -> tuple[int, Decimal, str]:
    return (-STATUS_SEVERITY[row.status], -row.max_abs_disagreement, row.market_slug)


def _normalize_input_rows(
    value: Iterable[object],
) -> tuple[ResearchProbabilityDisagreementInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityDisagreementInput:
            raise ValueError("rows must contain ResearchProbabilityDisagreementInput values")
        _require_hard_flags("rows", row)
        if row.market_slug in seen:
            raise ValueError("rows must contain unique market_slug values")
        seen.add(row.market_slug)
    return rows


def _normalize_rows(
    value: Iterable[ResearchProbabilityDisagreementRow],
) -> tuple[ResearchProbabilityDisagreementRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchProbabilityDisagreementRow:
            raise ValueError("rows must contain ResearchProbabilityDisagreementRow values")
        _require_hard_flags("rows", row)
        if row.market_slug in seen:
            raise ValueError("rows must contain unique market_slug values")
        seen.add(row.market_slug)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, disagreement, and market_slug")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[tuple[str, Decimal]],
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    normalized: list[tuple[str, Decimal]] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = row
        _require_canonical_string("reason_code_counts reason_code", reason_code)
        normalized.append(
            (
                reason_code,
                _require_positive_whole_decimal("reason_code_counts count", count),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result, key=lambda item: item[0])):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return result


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return reason_codes


def _validate_row_consistency(row: ResearchProbabilityDisagreementRow) -> None:
    model_team = _quantize(abs(row.model_probability - row.team_probability))
    model_market = _quantize(abs(row.model_probability - row.market_implied_probability))
    team_market = _quantize(abs(row.team_probability - row.market_implied_probability))
    if row.model_team_abs_disagreement != model_team:
        raise ValueError("model_team_abs_disagreement must match probabilities")
    if row.model_market_abs_disagreement != model_market:
        raise ValueError("model_market_abs_disagreement must match probabilities")
    if row.team_market_abs_disagreement != team_market:
        raise ValueError("team_market_abs_disagreement must match probabilities")
    if row.max_abs_disagreement != max(model_team, model_market, team_market):
        raise ValueError("max_abs_disagreement must match pairwise disagreements")
    expected_average = _quantize((model_team + model_market + team_market) / THREE)
    if row.average_abs_disagreement != expected_average:
        raise ValueError("average_abs_disagreement must match pairwise disagreements")


def _validate_report_consistency(report: ResearchProbabilityDisagreementReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.largest_abs_disagreement != _largest_abs_disagreement(report.rows):
        raise ValueError("largest_abs_disagreement must match rows")
    if report.average_max_abs_disagreement != _average_max_abs_disagreement(report.rows):
        raise ValueError("average_max_abs_disagreement must match rows")
    expected_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_counts = _row_reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in SENSITIVE_PUBLIC_TOKENS):
        raise ValueError(f"{field_name} contains sensitive public payload text")
    if any(phrase in lowered for phrase in ADVICE_PUBLIC_PHRASES):
        raise ValueError(f"{field_name} contains trading or investment advice")


def _json_ready(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value, key if not path else f"{path}.{key}")
            for key, nested_value in asdict(value).items()
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) is str:
        _reject_unsafe_public_text(path or "value", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    probability = _require_nonnegative_decimal(field_name, value)
    if probability > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return probability


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return number


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    number = _require_nonnegative_decimal(field_name, value)
    if number <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if number != number.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return number


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be a single-line string")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
