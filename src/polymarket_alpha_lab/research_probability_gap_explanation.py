"""Read-only audit explanations for redacted research probability gaps."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_PROBABILITY_GAP_EXPLANATION_CONFIG_VERSION = (
    "research-probability-gap-explanation-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
PROBABILITY_GAP_DIRECTIONS = ("below_reference", "at_reference", "above_reference")

ROW_EXPLANATION_CODES = (
    "probability_gap_pass",
    "probability_gap_watch",
    "probability_gap_block",
    "evidence_quality_pass",
    "evidence_quality_watch",
    "evidence_quality_block",
    "base_rate_drift_pass",
    "base_rate_drift_watch",
    "base_rate_drift_block",
    "source_conflict_pass",
    "source_conflict_watch",
    "source_conflict_block",
)
REPORT_EXPLANATION_CODES = (
    "probability_gap_explanation_clear",
    "probability_gap_watch",
    "probability_gap_block",
    "evidence_quality_watch",
    "evidence_quality_block",
    "base_rate_drift_watch",
    "base_rate_drift_block",
    "source_conflict_watch",
    "source_conflict_block",
)

RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PUBLIC_KEY_BLOCKLIST = (
    "raw",
    "candidate_id",
    "market",
    "slug",
    "question",
    "source_ref",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
)
PUBLIC_VALUE_BLOCKLIST = (
    "raw",
    "market",
    "slug",
    "question",
    "source_ref",
    "http",
    "https",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
)


__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_GAP_EXPLANATION_CONFIG_VERSION",
    "ResearchProbabilityGapExplanationConfig",
    "ResearchProbabilityGapExplanationInput",
    "ResearchProbabilityGapExplanationReport",
    "ResearchProbabilityGapExplanationRow",
    "build_research_probability_gap_explanation_report",
    "research_probability_gap_explanation_digest",
    "research_probability_gap_explanation_payload",
)


@dataclass(frozen=True)
class ResearchProbabilityGapExplanationConfig:
    config_version: str = DEFAULT_RESEARCH_PROBABILITY_GAP_EXPLANATION_CONFIG_VERSION
    watch_probability_gap: Decimal = Decimal("0.030000")
    block_probability_gap: Decimal = Decimal("0.100000")
    watch_min_evidence_quality_score: Decimal = Decimal("0.600000")
    block_min_evidence_quality_score: Decimal = Decimal("0.300000")
    watch_base_rate_drift: Decimal = Decimal("0.040000")
    block_base_rate_drift: Decimal = Decimal("0.120000")
    watch_source_conflict_score: Decimal = Decimal("0.250000")
    block_source_conflict_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityGapExplanationConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityGapExplanationConfig:
            raise ValueError(
                "config must be exactly ResearchProbabilityGapExplanationConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_probability_gap",
            "block_probability_gap",
            "watch_min_evidence_quality_score",
            "block_min_evidence_quality_score",
            "watch_base_rate_drift",
            "block_base_rate_drift",
            "watch_source_conflict_score",
            "block_source_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchProbabilityGapExplanationInput:
    redacted_candidate_ref: str
    probability_gap: Decimal
    evidence_quality_score: Decimal
    base_rate_drift: Decimal
    source_conflict_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityGapExplanationInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityGapExplanationInput:
            raise ValueError(
                "input must be exactly ResearchProbabilityGapExplanationInput",
            )
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        object.__setattr__(
            self,
            "probability_gap",
            _normalize_probability_gap("probability_gap", self.probability_gap),
        )
        for field_name in (
            "evidence_quality_score",
            "base_rate_drift",
            "source_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchProbabilityGapExplanationRow:
    redacted_candidate_ref: str
    probability_gap: Decimal
    absolute_probability_gap: Decimal
    probability_gap_direction: str
    evidence_quality_score: Decimal
    base_rate_drift: Decimal
    source_conflict_score: Decimal
    status: str
    explanation_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityGapExplanationRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityGapExplanationRow:
            raise ValueError("row must be exactly ResearchProbabilityGapExplanationRow")
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        object.__setattr__(
            self,
            "probability_gap",
            _normalize_probability_gap("probability_gap", self.probability_gap),
        )
        object.__setattr__(
            self,
            "absolute_probability_gap",
            _normalize_probability(
                "absolute_probability_gap",
                self.absolute_probability_gap,
            ),
        )
        _require_member(
            "probability_gap_direction",
            self.probability_gap_direction,
            PROBABILITY_GAP_DIRECTIONS,
        )
        for field_name in (
            "evidence_quality_score",
            "base_rate_drift",
            "source_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "explanation_codes",
            _normalize_explanation_codes(
                "explanation_codes",
                self.explanation_codes,
                ROW_EXPLANATION_CODES,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchProbabilityGapExplanationReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    explanation_codes: tuple[str, ...]
    rows: tuple[ResearchProbabilityGapExplanationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchProbabilityGapExplanationReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchProbabilityGapExplanationReport:
            raise ValueError(
                "report must be exactly ResearchProbabilityGapExplanationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "explanation_codes",
            _normalize_explanation_codes(
                "explanation_codes",
                self.explanation_codes,
                REPORT_EXPLANATION_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_probability_gap_explanation_report(
    rows: list[ResearchProbabilityGapExplanationInput]
    | tuple[ResearchProbabilityGapExplanationInput, ...],
    *,
    config: ResearchProbabilityGapExplanationConfig,
    generated_at: datetime,
) -> ResearchProbabilityGapExplanationReport:
    """Build a deterministic audit explanation report without live-action fields."""

    if type(config) is not ResearchProbabilityGapExplanationConfig:
        raise ValueError("config must be a ResearchProbabilityGapExplanationConfig")
    _require_hard_flags("config", config)
    input_rows = _normalize_inputs(rows)
    explanation_rows = tuple(
        sorted(
            (_row_from_input(row, config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchProbabilityGapExplanationReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_count(len(input_rows)),
        pass_count=_count(_status_count(explanation_rows, "pass")),
        watch_count=_count(_status_count(explanation_rows, "watch")),
        block_count=_count(_status_count(explanation_rows, "block")),
        status=_report_status(explanation_rows),
        explanation_codes=_report_explanation_codes(explanation_rows),
        rows=explanation_rows,
    )


def research_probability_gap_explanation_payload(
    report: ResearchProbabilityGapExplanationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchProbabilityGapExplanationReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchProbabilityGapExplanationReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("research probability gap explanation payload", payload)
    return payload


def research_probability_gap_explanation_digest(
    report: ResearchProbabilityGapExplanationReport | dict[str, Any],
) -> str:
    payload = research_probability_gap_explanation_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


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


def _normalize_inputs(
    rows: list[ResearchProbabilityGapExplanationInput]
    | tuple[ResearchProbabilityGapExplanationInput, ...],
) -> tuple[ResearchProbabilityGapExplanationInput, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchProbabilityGapExplanationInput:
            raise ValueError(
                "rows must contain ResearchProbabilityGapExplanationInput values",
            )
        _require_hard_flags("input", row)
        if row.redacted_candidate_ref in seen:
            raise ValueError("rows must not contain duplicate redacted_candidate_ref values")
        seen.add(row.redacted_candidate_ref)
    return normalized


def _row_from_input(
    row: ResearchProbabilityGapExplanationInput,
    config: ResearchProbabilityGapExplanationConfig,
) -> ResearchProbabilityGapExplanationRow:
    status = _row_status(row, config)
    return ResearchProbabilityGapExplanationRow(
        redacted_candidate_ref=row.redacted_candidate_ref,
        probability_gap=row.probability_gap,
        absolute_probability_gap=_abs_decimal(row.probability_gap),
        probability_gap_direction=_probability_gap_direction(row.probability_gap),
        evidence_quality_score=row.evidence_quality_score,
        base_rate_drift=row.base_rate_drift,
        source_conflict_score=row.source_conflict_score,
        status=status,
        explanation_codes=_row_explanation_codes(row, config, status),
    )


def _row_status(
    row: ResearchProbabilityGapExplanationInput,
    config: ResearchProbabilityGapExplanationConfig,
) -> str:
    absolute_gap = _abs_decimal(row.probability_gap)
    if (
        absolute_gap >= config.block_probability_gap
        or row.evidence_quality_score <= config.block_min_evidence_quality_score
        or row.base_rate_drift >= config.block_base_rate_drift
        or row.source_conflict_score >= config.block_source_conflict_score
    ):
        return "block"
    if (
        absolute_gap >= config.watch_probability_gap
        or row.evidence_quality_score <= config.watch_min_evidence_quality_score
        or row.base_rate_drift >= config.watch_base_rate_drift
        or row.source_conflict_score >= config.watch_source_conflict_score
    ):
        return "watch"
    return "pass"


def _row_explanation_codes(
    row: ResearchProbabilityGapExplanationInput,
    config: ResearchProbabilityGapExplanationConfig,
    status: str,
) -> tuple[str, ...]:
    absolute_gap = _abs_decimal(row.probability_gap)
    return (
        f"probability_gap_{_band_for_high_signal(absolute_gap, config.watch_probability_gap, config.block_probability_gap)}",
        f"evidence_quality_{_band_for_low_signal(row.evidence_quality_score, config.watch_min_evidence_quality_score, config.block_min_evidence_quality_score)}",
        f"base_rate_drift_{_band_for_high_signal(row.base_rate_drift, config.watch_base_rate_drift, config.block_base_rate_drift)}",
        f"source_conflict_{_band_for_high_signal(row.source_conflict_score, config.watch_source_conflict_score, config.block_source_conflict_score)}",
    )


def _band_for_high_signal(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str:
    if value >= block_threshold:
        return "block"
    if value >= watch_threshold:
        return "watch"
    return "pass"


def _band_for_low_signal(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str:
    if value <= block_threshold:
        return "block"
    if value <= watch_threshold:
        return "watch"
    return "pass"


def _probability_gap_direction(value: Decimal) -> str:
    if value < ZERO:
        return "below_reference"
    if value > ZERO:
        return "above_reference"
    return "at_reference"


def _report_status(rows: tuple[ResearchProbabilityGapExplanationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_explanation_codes(
    rows: tuple[ResearchProbabilityGapExplanationRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("probability_gap_explanation_clear",)
    codes: list[str] = []
    for prefix in (
        "probability_gap",
        "evidence_quality",
        "base_rate_drift",
        "source_conflict",
    ):
        for status in ("block", "watch"):
            code = f"{prefix}_{status}"
            if any(code in row.explanation_codes for row in rows):
                codes.append(code)
    return tuple(codes)


def _row_sort_key(
    row: ResearchProbabilityGapExplanationRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.absolute_probability_gap,
        -row.source_conflict_score,
        -row.base_rate_drift,
        row.evidence_quality_score,
        row.redacted_candidate_ref,
    )


def _status_count(rows: tuple[ResearchProbabilityGapExplanationRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_config(config: ResearchProbabilityGapExplanationConfig) -> None:
    if config.watch_probability_gap > config.block_probability_gap:
        raise ValueError("watch_probability_gap must not exceed block_probability_gap")
    if config.watch_min_evidence_quality_score < config.block_min_evidence_quality_score:
        raise ValueError(
            "watch_min_evidence_quality_score must be at least "
            "block_min_evidence_quality_score",
        )
    if config.watch_base_rate_drift > config.block_base_rate_drift:
        raise ValueError("watch_base_rate_drift must not exceed block_base_rate_drift")
    if config.watch_source_conflict_score > config.block_source_conflict_score:
        raise ValueError(
            "watch_source_conflict_score must not exceed block_source_conflict_score",
        )


def _validate_row(row: ResearchProbabilityGapExplanationRow) -> None:
    if row.absolute_probability_gap != _abs_decimal(row.probability_gap):
        raise ValueError("absolute_probability_gap must match probability_gap")
    if row.probability_gap_direction != _probability_gap_direction(row.probability_gap):
        raise ValueError("probability_gap_direction must match probability_gap")
    row_statuses = tuple(code.rsplit("_", maxsplit=1)[1] for code in row.explanation_codes)
    if row.status == "pass" and any(status != "pass" for status in row_statuses):
        raise ValueError("pass rows must contain only pass explanation codes")
    if row.status == "watch" and "block" in row_statuses:
        raise ValueError("watch rows must not contain block explanation codes")
    if row.status == "watch" and "watch" not in row_statuses:
        raise ValueError("watch rows must contain watch explanation codes")
    if row.status == "block" and "block" not in row_statuses:
        raise ValueError("block rows must contain block explanation codes")


def _validate_report(report: ResearchProbabilityGapExplanationReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.explanation_codes != _report_explanation_codes(report.rows):
        raise ValueError("explanation_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    refs = tuple(row.redacted_candidate_ref for row in report.rows)
    if len(set(refs)) != len(refs):
        raise ValueError("rows must contain unique redacted_candidate_ref values")


def _normalize_rows(value: object) -> tuple[ResearchProbabilityGapExplanationRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not ResearchProbabilityGapExplanationRow:
            raise ValueError(
                "rows must contain ResearchProbabilityGapExplanationRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_explanation_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        if _contains_blocked_fragment(key, PUBLIC_KEY_BLOCKLIST):
            raise ValueError(f"unsafe public field in {label}: {key}")
    _reject_unsafe_public_strings(label, value)


def _reject_unsafe_public_strings(label: str, value: object) -> None:
    if type(value) is str:
        if _contains_blocked_fragment(value, PUBLIC_VALUE_BLOCKLIST):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_strings(label, item)
        return


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _require_redacted_candidate_ref(value: object) -> None:
    _require_canonical_string("redacted_candidate_ref", value)
    assert type(value) is str
    if not value.startswith("candidate_ref_"):
        raise ValueError("redacted_candidate_ref must be redacted")
    suffix = value.removeprefix("candidate_ref_")
    if not suffix:
        raise ValueError("redacted_candidate_ref must be redacted")
    if _contains_blocked_fragment(suffix, PUBLIC_VALUE_BLOCKLIST):
        raise ValueError("redacted_candidate_ref must not leak sensitive identifiers")
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_" for char in value):
        raise ValueError("redacted_candidate_ref must be canonical")


def _contains_blocked_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    lowered = value.lower()
    tokens = _tokens(lowered)
    for fragment in fragments:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        part
        for part in "".join(char if char.isalnum() else "_" for char in value).split("_")
        if part
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_probability_gap(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(RATIO_QUANTUM)
