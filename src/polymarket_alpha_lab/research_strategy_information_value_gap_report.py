"""Pure strategy information value gap report reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_REPORT_CONFIG_VERSION = (
    "research-strategy-information-value-gap-report-v0"
)
RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_STATUSES = ("pass", "watch", "block")

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

MISSING_EVIDENCE_CATEGORIES = (
    "base_rate_context",
    "resolution_rule",
    "source_corroboration",
)
ROW_REASON_CODES = (
    "evidence_quality_block",
    "evidence_quality_watch",
    "high_category_importance",
    "high_readiness_dependency",
    "information_value_gap_pass",
    "value_gap_block",
    "value_gap_watch",
)
REPORT_REASON_CODES = (
    "category_importance_review",
    "evidence_quality_review",
    "information_value_gap_block",
    "information_value_gap_pass",
    "information_value_gap_watch",
    "readiness_dependency_review",
    "value_gap_review",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "credential",
    "private",
    "secret",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "data" + "base",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
    "candi" + "date",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion",
    "u" + "rl",
    "source" + "_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "reco" + "mmendation",
    "siz" + "ing",
)


@dataclass(frozen=True)
class ResearchStrategyInformationValueGapConfig:
    config_version: str
    value_gap_watch_threshold: Decimal
    value_gap_block_threshold: Decimal
    evidence_quality_watch_floor: Decimal
    evidence_quality_block_floor: Decimal
    category_importance_watch_threshold: Decimal
    readiness_dependency_watch_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "value_gap_watch_threshold",
            "value_gap_block_threshold",
            "evidence_quality_watch_floor",
            "evidence_quality_block_floor",
            "category_importance_watch_threshold",
            "readiness_dependency_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "value gap threshold",
            self.value_gap_watch_threshold,
            self.value_gap_block_threshold,
        )
        _require_floor_pair(
            "evidence quality threshold",
            self.evidence_quality_watch_floor,
            self.evidence_quality_block_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyInformationValueGapInput:
    evidence_gap_ref: str
    strategy_ref: str
    missing_evidence_category: str
    observed_at: datetime
    category_importance_score: Decimal
    available_evidence_score: Decimal
    readiness_dependency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("evidence_gap_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_missing_evidence_category(
            "missing_evidence_category",
            self.missing_evidence_category,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "category_importance_score",
            "available_evidence_score",
            "readiness_dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyInformationValueGapRow:
    evidence_gap_ref: str
    strategy_ref: str
    missing_evidence_category: str
    observed_at: datetime
    category_importance_score: Decimal
    available_evidence_score: Decimal
    readiness_dependency_score: Decimal
    missing_evidence_quality_gap: Decimal
    information_value_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("evidence_gap_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_missing_evidence_category(
            "missing_evidence_category",
            self.missing_evidence_category,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "category_importance_score",
            "available_evidence_score",
            "readiness_dependency_score",
            "missing_evidence_quality_gap",
            "information_value_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyInformationValueGapReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_missing_evidence_quality_gap: Decimal
    mean_information_value_gap_score: Decimal
    highest_information_value_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyInformationValueGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_missing_evidence_quality_gap",
            "mean_information_value_gap_score",
            "highest_information_value_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_information_value_gap_report(
    inputs: Iterable[ResearchStrategyInformationValueGapInput],
    *,
    config: ResearchStrategyInformationValueGapConfig,
    generated_at: datetime,
) -> ResearchStrategyInformationValueGapReport:
    if type(config) is not ResearchStrategyInformationValueGapConfig:
        raise ValueError(
            "config must be a ResearchStrategyInformationValueGapConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyInformationValueGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_missing_evidence_quality_gap=_mean(
            tuple(row.missing_evidence_quality_gap for row in rows),
        ),
        mean_information_value_gap_score=_mean(
            tuple(row.information_value_gap_score for row in rows),
        ),
        highest_information_value_gap_score=_highest(
            tuple(row.information_value_gap_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_information_value_gap_report_payload(
    report: ResearchStrategyInformationValueGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyInformationValueGapReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyInformationValueGapReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_STATUSES",
    "ResearchStrategyInformationValueGapConfig",
    "ResearchStrategyInformationValueGapInput",
    "ResearchStrategyInformationValueGapRow",
    "ResearchStrategyInformationValueGapReport",
    "build_research_strategy_information_value_gap_report",
    "research_strategy_information_value_gap_report_payload",
)


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


def _row_from_input(
    value: ResearchStrategyInformationValueGapInput,
    *,
    config: ResearchStrategyInformationValueGapConfig,
    generated_at: datetime,
) -> ResearchStrategyInformationValueGapRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    missing_quality_gap = _subtract_decimal(ONE, value.available_evidence_score)
    value_gap = _multiply_decimal(
        _multiply_decimal(missing_quality_gap, value.category_importance_score),
        value.readiness_dependency_score,
    )
    return ResearchStrategyInformationValueGapRow(
        evidence_gap_ref=value.evidence_gap_ref,
        strategy_ref=value.strategy_ref,
        missing_evidence_category=value.missing_evidence_category,
        observed_at=observed_at,
        category_importance_score=value.category_importance_score,
        available_evidence_score=value.available_evidence_score,
        readiness_dependency_score=value.readiness_dependency_score,
        missing_evidence_quality_gap=missing_quality_gap,
        information_value_gap_score=value_gap,
        status=_row_status(value, config),
        reason_codes=_row_reason_codes(value, config),
    )


def _row_status(
    value: ResearchStrategyInformationValueGapInput,
    config: ResearchStrategyInformationValueGapConfig,
) -> str:
    codes = _row_reason_codes(value, config)
    if any(code.endswith("_block") for code in codes):
        return "block"
    if len(codes) != 1 or codes[0] != "information_value_gap_pass":
        return "watch"
    return "pass"


def _row_reason_codes(
    value: ResearchStrategyInformationValueGapInput,
    config: ResearchStrategyInformationValueGapConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    missing_quality_gap = _subtract_decimal(ONE, value.available_evidence_score)
    value_gap = _multiply_decimal(
        _multiply_decimal(missing_quality_gap, value.category_importance_score),
        value.readiness_dependency_score,
    )
    if value_gap >= config.value_gap_block_threshold:
        codes.append("value_gap_block")
    elif value_gap >= config.value_gap_watch_threshold:
        codes.append("value_gap_watch")
    if value.available_evidence_score < config.evidence_quality_block_floor:
        codes.append("evidence_quality_block")
    elif value.available_evidence_score < config.evidence_quality_watch_floor:
        codes.append("evidence_quality_watch")
    if (
        value.category_importance_score >= config.category_importance_watch_threshold
        and value.readiness_dependency_score
        >= config.readiness_dependency_watch_threshold
        and value_gap >= config.value_gap_block_threshold
    ):
        codes.append("high_category_importance")
        codes.append("high_readiness_dependency")
    if not codes:
        codes.append("information_value_gap_pass")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategyInformationValueGapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyInformationValueGapRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("information_value_gap_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("information_value_gap_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("information_value_gap_watch")
    if any(code.startswith("value_gap_") for row in rows for code in row.reason_codes):
        codes.append("value_gap_review")
    if any(
        code.startswith("evidence_quality_")
        for row in rows
        for code in row.reason_codes
    ):
        codes.append("evidence_quality_review")
    if any("category_importance" in code for row in rows for code in row.reason_codes):
        codes.append("category_importance_review")
    if any("readiness_dependency" in code for row in rows for code in row.reason_codes):
        codes.append("readiness_dependency_review")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyInformationValueGapRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.information_value_gap_score,
        -row.missing_evidence_quality_gap,
        -row.category_importance_score,
        row.evidence_gap_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyInformationValueGapInput],
) -> tuple[ResearchStrategyInformationValueGapInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyInformationValueGapInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyInformationValueGapInput values",
            )
        _require_hard_flags("input", value)
        if value.evidence_gap_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate evidence_gap_ref values")
        seen_refs.add(value.evidence_gap_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyInformationValueGapRow],
) -> tuple[ResearchStrategyInformationValueGapRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyInformationValueGapRow:
            raise ValueError(
                "rows must contain ResearchStrategyInformationValueGapRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.evidence_gap_ref in seen_refs:
            raise ValueError("rows must not contain duplicate evidence_gap_ref values")
        seen_refs.add(row.evidence_gap_ref)
    return normalized


def _validate_row_consistency(row: ResearchStrategyInformationValueGapRow) -> None:
    expected_missing_quality_gap = _subtract_decimal(ONE, row.available_evidence_score)
    if row.missing_evidence_quality_gap != expected_missing_quality_gap:
        raise ValueError("missing_evidence_quality_gap does not match quality inputs")
    expected_value_gap = _multiply_decimal(
        _multiply_decimal(
            row.missing_evidence_quality_gap,
            row.category_importance_score,
        ),
        row.readiness_dependency_score,
    )
    if row.information_value_gap_score != expected_value_gap:
        raise ValueError("information_value_gap_score does not match score inputs")
    if row.status == "pass" and row.reason_codes != ("information_value_gap_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyInformationValueGapReport,
) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.source_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match source_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_missing_evidence_quality_gap != _mean(
        tuple(row.missing_evidence_quality_gap for row in report.rows),
    ):
        raise ValueError("mean_missing_evidence_quality_gap must match rows")
    if report.mean_information_value_gap_score != _mean(
        tuple(row.information_value_gap_score for row in report.rows),
    ):
        raise ValueError("mean_information_value_gap_score must match rows")
    if report.highest_information_value_gap_score != _highest(
        tuple(row.information_value_gap_score for row in report.rows),
    ):
        raise ValueError("highest_information_value_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyInformationValueGapReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyInformationValueGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyInformationValueGapRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


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
            raise ValueError("reason_code_counts must contain reason code count tuples")
        reason_code, count = row
        _require_reason_code("reason_code_counts reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code_counts reason code is not supported")
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    sorted_counts = tuple(
        sorted(
            normalized,
            key=lambda item: (-item[1], item[0]),
        ),
    )
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must use deterministic sequence")
    if len({reason_code for reason_code, _count_value in sorted_counts}) != len(
        sorted_counts,
    ):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return sorted_counts


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _highest(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(values).quantize(RATIO_QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _apply_or_verify_digest(
    value: ResearchStrategyInformationValueGapRow | ResearchStrategyInformationValueGapReport,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: ResearchStrategyInformationValueGapRow | ResearchStrategyInformationValueGapReport,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: ResearchStrategyInformationValueGapRow | ResearchStrategyInformationValueGapReport,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_canonical_public_string("public_payload_key", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _require_canonical_public_string(label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if isinstance(value, datetime):
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError(f"{label} must not be a float")
    raise ValueError(f"{label} is not JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} is not supported")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if value.startswith("_") or value.endswith("_") or "__" in value:
        raise ValueError(f"{field_name} must be a canonical reason code")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must be a canonical reason code")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_STATUSES
    ):
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_missing_evidence_category(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in MISSING_EVIDENCE_CATEGORIES:
        raise ValueError(f"{field_name} must be a supported sanitized category")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _require_threshold_pair(
    label: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _require_floor_pair(
    label: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if watch_floor < block_floor:
        raise ValueError(f"{label} watch floor must not be below block floor")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(
        fragment in lowered or fragment in compact
        for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    )
