"""Pure report-only counter-thesis matrix for caller-supplied research.

The module is deterministic and side-effect free. Callers provide typed
counter-thesis evidence; the builder returns public matrix rows, status
rollups, and reason codes without exposing raw source references or source
text.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchCounterThesisConfig",
    "ResearchCounterThesisEvidence",
    "ResearchCounterThesisMatrixReport",
    "ResearchCounterThesisMatrixRow",
    "ResearchCounterThesisReasonCodeCount",
    "build_research_counter_thesis_matrix_report",
    "research_counter_thesis_matrix_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-counter-thesis-matrix-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_WATCH_SCORE_THRESHOLD = Decimal("0.350000")
DEFAULT_BLOCK_SCORE_THRESHOLD = Decimal("0.750000")
_PUBLIC_ONLY_FLAGS = ("paper_only", "report_only", "readonly")
_SENSITIVE_PUBLIC_FIELD_FRAGMENTS = (
    "source_ref",
    "source_url",
    "source_text",
    "source_id",
    "url",
    "raw",
    "condition_id",
    "token_id",
    "market_slug",
    "market_url",
)
_SENSITIVE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "polymarket",
    "condition_id",
    "token_id",
    "market_slug",
    "market_url",
    "market-",
)


@dataclass(frozen=True)
class ResearchCounterThesisConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_score_threshold: Decimal = DEFAULT_WATCH_SCORE_THRESHOLD
    block_score_threshold: Decimal = DEFAULT_BLOCK_SCORE_THRESHOLD
    min_independent_source_families: Decimal = Decimal("2")
    strong_counter_evidence_threshold: Decimal = Decimal("0.700000")
    unresolved_conflict_threshold: Decimal = Decimal("0.500000")
    counter_evidence_strength_weight: Decimal = Decimal("0.500000")
    source_independence_weight: Decimal = Decimal("0.300000")
    unresolved_conflict_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCounterThesisConfig:
            raise TypeError("ResearchCounterThesisConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCounterThesisConfig:
            raise ValueError("config must be exactly ResearchCounterThesisConfig")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "watch_score_threshold",
            "block_score_threshold",
            "strong_counter_evidence_threshold",
            "unresolved_conflict_threshold",
            "counter_evidence_strength_weight",
            "source_independence_weight",
            "unresolved_conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold >= self.block_score_threshold:
            raise ValueError("watch_score_threshold must be less than block_score_threshold")
        object.__setattr__(
            self,
            "min_independent_source_families",
            _require_positive_whole_decimal(
                "min_independent_source_families",
                self.min_independent_source_families,
            ),
        )
        weight_sum = _quantize(
            self.counter_evidence_strength_weight
            + self.source_independence_weight
            + self.unresolved_conflict_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "counter_evidence_strength_weight, source_independence_weight, "
                "and unresolved_conflict_weight must sum to 1",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchCounterThesisEvidence:
    candidate_key: str
    counter_thesis_code: str
    evidence_key: str
    source_family: str
    counter_evidence_strength: Decimal
    source_independence: Decimal
    unresolved_conflict: Decimal
    source_ref: str
    source_url: str | None = None
    source_text: str | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCounterThesisEvidence:
            raise TypeError("ResearchCounterThesisEvidence does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCounterThesisEvidence:
            raise ValueError("evidence must be exactly ResearchCounterThesisEvidence")
        _require_public_candidate_key("candidate_key", self.candidate_key)
        _require_reason_code("counter_thesis_code", self.counter_thesis_code)
        _require_public_identifier("evidence_key", self.evidence_key)
        _require_public_identifier("source_family", self.source_family)
        for field_name in (
            "counter_evidence_strength",
            "source_independence",
            "unresolved_conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_private_text("source_ref", self.source_ref)
        object.__setattr__(
            self,
            "source_url",
            _normalize_optional_private_text("source_url", self.source_url),
        )
        object.__setattr__(
            self,
            "source_text",
            _normalize_optional_private_text("source_text", self.source_text),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchCounterThesisMatrixRow:
    candidate_key: str
    counter_thesis_code: str
    evidence_count: Decimal
    source_family_count: Decimal
    average_counter_evidence_strength: Decimal
    source_independence_score: Decimal
    unresolved_conflict_score: Decimal
    counter_thesis_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCounterThesisMatrixRow:
            raise TypeError("ResearchCounterThesisMatrixRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCounterThesisMatrixRow:
            raise ValueError("row must be exactly ResearchCounterThesisMatrixRow")
        _require_public_candidate_key("candidate_key", self.candidate_key)
        _require_reason_code("counter_thesis_code", self.counter_thesis_code)
        for field_name in ("evidence_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_counter_evidence_strength",
            "source_independence_score",
            "unresolved_conflict_score",
            "counter_thesis_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCounterThesisReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCounterThesisReasonCodeCount:
            raise TypeError(
                "ResearchCounterThesisReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCounterThesisReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly ResearchCounterThesisReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchCounterThesisMatrixReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    matrix_row_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_counter_thesis_score: Decimal | None
    status: str
    rows: tuple[ResearchCounterThesisMatrixRow, ...]
    reason_code_counts: tuple[ResearchCounterThesisReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCounterThesisMatrixReport:
            raise TypeError(
                "ResearchCounterThesisMatrixReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCounterThesisMatrixReport:
            raise ValueError("report must be exactly ResearchCounterThesisMatrixReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "matrix_row_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_counter_thesis_score",
            _require_optional_ratio_decimal(
                "average_counter_thesis_score",
                self.average_counter_thesis_score,
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
        _reject_unsafe_public_payload("report", self)


def build_research_counter_thesis_matrix_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchCounterThesisConfig,
    generated_at: datetime,
) -> ResearchCounterThesisMatrixReport:
    if type(config) is not ResearchCounterThesisConfig:
        raise ValueError("config must be a ResearchCounterThesisConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)

    grouped: dict[tuple[str, str], list[ResearchCounterThesisEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault((item.candidate_key, item.counter_thesis_code), []).append(item)

    rows = tuple(
        _matrix_row_from_group(
            candidate_key=candidate_key,
            counter_thesis_code=counter_thesis_code,
            evidence_rows=tuple(grouped[(candidate_key, counter_thesis_code)]),
            config=config,
        )
        for candidate_key, counter_thesis_code in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchCounterThesisMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_count(len({item.candidate_key for item in evidence_items})),
        matrix_row_count=_decimal_count(len(rows)),
        evidence_count=_decimal_count(len(evidence_items)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_counter_thesis_score=_average_counter_thesis_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_counter_thesis_matrix_report_payload(
    report: ResearchCounterThesisMatrixReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCounterThesisMatrixReport:
        raise ValueError("report must be a ResearchCounterThesisMatrixReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _matrix_row_from_group(
    *,
    candidate_key: str,
    counter_thesis_code: str,
    evidence_rows: tuple[ResearchCounterThesisEvidence, ...],
    config: ResearchCounterThesisConfig,
) -> ResearchCounterThesisMatrixRow:
    sorted_rows = tuple(
        sorted(
            evidence_rows,
            key=lambda item: (item.evidence_key, item.source_family, item.source_ref),
        ),
    )
    source_families = tuple(sorted({item.source_family for item in sorted_rows}))
    average_strength = _average_decimal(
        tuple(item.counter_evidence_strength for item in sorted_rows),
    )
    independence_score = _source_independence_score(
        tuple(item.source_independence for item in sorted_rows),
        source_family_count=len(source_families),
        config=config,
    )
    unresolved_score = _average_decimal(
        tuple(item.unresolved_conflict for item in sorted_rows),
    )
    counter_thesis_score = _counter_thesis_score(
        average_counter_evidence_strength=average_strength,
        source_independence_score=independence_score,
        unresolved_conflict_score=unresolved_score,
        config=config,
    )
    status = _row_status(counter_thesis_score, config)
    reason_codes = _row_reason_codes(
        status=status,
        average_counter_evidence_strength=average_strength,
        source_family_count=len(source_families),
        unresolved_conflict_score=unresolved_score,
        input_reason_codes=tuple(
            reason_code for item in sorted_rows for reason_code in item.reason_codes
        ),
        config=config,
    )

    return ResearchCounterThesisMatrixRow(
        candidate_key=candidate_key,
        counter_thesis_code=counter_thesis_code,
        evidence_count=_decimal_count(len(sorted_rows)),
        source_family_count=_decimal_count(len(source_families)),
        average_counter_evidence_strength=average_strength,
        source_independence_score=independence_score,
        unresolved_conflict_score=unresolved_score,
        counter_thesis_score=counter_thesis_score,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchCounterThesisEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_evidence_row(value) for value in values)


def _coerce_evidence_row(value: object) -> ResearchCounterThesisEvidence:
    if type(value) is ResearchCounterThesisEvidence:
        return value
    return ResearchCounterThesisEvidence(
        candidate_key=_get_required(value, "candidate_key"),
        counter_thesis_code=_get_required(value, "counter_thesis_code"),
        evidence_key=_get_required(value, "evidence_key"),
        source_family=_get_required(value, "source_family"),
        counter_evidence_strength=_get_required(value, "counter_evidence_strength"),
        source_independence=_get_required(value, "source_independence"),
        unresolved_conflict=_get_required(value, "unresolved_conflict"),
        source_ref=_get_required(value, "source_ref"),
        source_url=_get_optional(value, "source_url"),
        source_text=_get_optional(value, "source_text"),
        reason_codes=_get_optional(value, "reason_codes", default=()),
        paper_only=_get_required(value, "paper_only"),
        report_only=_get_required(value, "report_only"),
        readonly=_get_required(value, "readonly"),
    )


def _get_required(value: object, field_name: str) -> Any:
    sentinel = object()
    found = _get_optional(value, field_name, default=sentinel)
    if found is sentinel:
        raise ValueError(f"{field_name} is required")
    return found


def _get_optional(value: object, field_name: str, *, default: object = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _counter_thesis_score(
    *,
    average_counter_evidence_strength: Decimal,
    source_independence_score: Decimal,
    unresolved_conflict_score: Decimal,
    config: ResearchCounterThesisConfig,
) -> Decimal:
    return _quantize(
        average_counter_evidence_strength * config.counter_evidence_strength_weight
        + source_independence_score * config.source_independence_weight
        + unresolved_conflict_score * config.unresolved_conflict_weight,
    )


def _source_independence_score(
    values: tuple[Decimal, ...],
    *,
    source_family_count: int,
    config: ResearchCounterThesisConfig,
) -> Decimal:
    diversity_ratio = min(
        ONE,
        Decimal(source_family_count) / config.min_independent_source_families,
    )
    return _quantize(_average_decimal(values) * diversity_ratio)


def _row_status(score: Decimal, config: ResearchCounterThesisConfig) -> str:
    if score >= config.block_score_threshold:
        return "block"
    if score >= config.watch_score_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    average_counter_evidence_strength: Decimal,
    source_family_count: int,
    unresolved_conflict_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchCounterThesisConfig,
) -> tuple[str, ...]:
    reason_codes = [f"counter_thesis_{status}"]
    if average_counter_evidence_strength >= config.strong_counter_evidence_threshold:
        reason_codes.append("strong_counter_evidence")
    else:
        reason_codes.append("weak_counter_evidence")
    if Decimal(source_family_count) >= config.min_independent_source_families:
        reason_codes.append("independent_sources")
    else:
        reason_codes.append("limited_source_independence")
    if unresolved_conflict_score >= config.unresolved_conflict_threshold:
        reason_codes.append("unresolved_conflicts_present")
    else:
        reason_codes.append("conflicts_resolved_or_low")
    reason_codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _summary_reason_codes(
    rows: tuple[ResearchCounterThesisMatrixRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_counter_thesis_evidence",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchCounterThesisMatrixRow, ...]) -> str:
    statuses = {row.status for row in rows}
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchCounterThesisMatrixRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCounterThesisReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCounterThesisReasonCodeCount(
                reason_code="no_counter_thesis_evidence",
                count=Decimal("1"),
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchCounterThesisReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
        if counts[reason_code] > 0
    )


def _average_counter_thesis_score(
    rows: tuple[ResearchCounterThesisMatrixRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.counter_thesis_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _status_count(rows: tuple[ResearchCounterThesisMatrixRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(rows: object) -> tuple[ResearchCounterThesisMatrixRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchCounterThesisMatrixRow] = []
    seen: set[tuple[str, str]] = set()
    previous_key: tuple[str, str] | None = None
    for row in rows:
        if type(row) is not ResearchCounterThesisMatrixRow:
            raise ValueError("rows must contain ResearchCounterThesisMatrixRow values")
        key = (row.candidate_key, row.counter_thesis_code)
        if key in seen:
            raise ValueError("rows must not contain duplicate matrix keys")
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be sorted by candidate_key and counter_thesis_code")
        seen.add(key)
        previous_key = key
        normalized.append(row)
    return tuple(normalized)


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchCounterThesisReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchCounterThesisReasonCodeCount] = []
    seen: set[str] = set()
    previous_reason_code: str | None = None
    for item in reason_code_counts:
        if type(item) is not ResearchCounterThesisReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchCounterThesisReasonCodeCount values",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        if previous_reason_code is not None and item.reason_code <= previous_reason_code:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        seen.add(item.reason_code)
        previous_reason_code = item.reason_code
        normalized.append(item)
    return tuple(normalized)


def _validate_row_consistency(row: ResearchCounterThesisMatrixRow) -> None:
    expected_status_code = f"counter_thesis_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("reason_codes must include the row status reason code")
    if row.status == "block" and row.counter_thesis_score < DEFAULT_BLOCK_SCORE_THRESHOLD:
        raise ValueError("counter_thesis_score is inconsistent with block status")
    if row.status == "watch" and (
        row.counter_thesis_score < DEFAULT_WATCH_SCORE_THRESHOLD
        or row.counter_thesis_score >= DEFAULT_BLOCK_SCORE_THRESHOLD
    ):
        raise ValueError("counter_thesis_score is inconsistent with watch status")
    if row.status == "pass" and row.counter_thesis_score >= DEFAULT_WATCH_SCORE_THRESHOLD:
        raise ValueError("counter_thesis_score is inconsistent with pass status")


def _validate_report_consistency(report: ResearchCounterThesisMatrixReport) -> None:
    rows = report.rows
    if report.matrix_row_count != _decimal_count(len(rows)):
        raise ValueError("matrix_row_count must equal row count")
    if report.candidate_count != _decimal_count(len({row.candidate_key for row in rows})):
        raise ValueError("candidate_count must equal unique candidate count")
    if report.evidence_count != sum((row.evidence_count for row in rows), ZERO):
        raise ValueError("evidence_count must equal row evidence counts")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must equal block rows")
    if report.average_counter_thesis_score != _average_counter_thesis_score(rows):
        raise ValueError("average_counter_thesis_score must equal row average")
    if report.status != _summary_status(rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must summarize rows")
    expected_counts = _reason_code_counts(rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must summarize rows")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is str:
        if _has_unsafe_public_value(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is int or type(value) is float:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_field(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in _PUBLIC_ONLY_FLAGS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_field(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _SENSITIVE_PUBLIC_FIELD_FRAGMENTS)


def _has_unsafe_public_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _SENSITIVE_PUBLIC_VALUE_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if not _is_safe_identifier_text(value):
        raise ValueError(f"{field_name} must use safe identifier characters")
    if _has_unsafe_public_value(value):
        raise ValueError(f"{field_name} contains an unsafe public value")


def _require_public_candidate_key(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if not _is_safe_identifier_text(value):
        raise ValueError(f"{field_name} must use reason-code characters")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")


def _is_safe_identifier_text(value: str) -> bool:
    return all(
        ("a" <= char <= "z")
        or ("0" <= char <= "9")
        or char in {"_", "-"}
        for char in value
    )


def _require_private_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _normalize_optional_private_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    return value


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
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PUBLIC_ONLY_FLAGS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
