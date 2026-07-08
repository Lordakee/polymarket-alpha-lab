"""Pure report-only backlog builder for stale resolution evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "ResearchResolutionEvidenceStalenessBacklogConfig",
    "ResearchResolutionEvidenceStalenessBacklogInput",
    "ResearchResolutionEvidenceStalenessBacklogReasonCodeCount",
    "ResearchResolutionEvidenceStalenessBacklogReport",
    "ResearchResolutionEvidenceStalenessBacklogRow",
    "build_research_resolution_evidence_staleness_backlog_report",
    "research_resolution_evidence_staleness_backlog_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-evidence-staleness-backlog-v0"
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_STATUSES = frozenset(("pass", "watch", "block"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID_UNSAFE_TERMS = (
    "http",
    "url",
    "market",
    "condition",
    "slug",
    "source",
    "ref",
    "text",
)
_PAYLOAD_UNSAFE_FRAGMENTS = (
    "http://",
    "https://",
    "source_url",
    "source_text",
    "source_ref",
    "source_reference",
    "market_slug",
    "market_id",
    "condition_id",
    "raw_url",
    "raw_text",
    "raw_ref",
)
_ACTION_TERMS = (
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "recomm" + "endation",
    "siz" + "ing",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchResolutionEvidenceStalenessBacklogConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    watch_pressure_threshold: Decimal = Decimal("0.350000")
    block_pressure_threshold: Decimal = Decimal("0.700000")
    aggregate_age_weight: Decimal = Decimal("0.300000")
    source_class_reliability_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    deadline_proximity_weight: Decimal = Decimal("0.150000")
    rule_clarity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceStalenessBacklogConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "aggregate_age_weight",
            "source_class_reliability_weight",
            "contradiction_pressure_weight",
            "deadline_proximity_weight",
            "rule_clarity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_pressure_threshold <= self.watch_pressure_threshold:
            raise ValueError("block_pressure_threshold must exceed watch_pressure_threshold")
        weight_sum = _quantize(
            self.aggregate_age_weight
            + self.source_class_reliability_weight
            + self.contradiction_pressure_weight
            + self.deadline_proximity_weight
            + self.rule_clarity_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "aggregate_age_weight, source_class_reliability_weight, "
                "contradiction_pressure_weight, deadline_proximity_weight, "
                "and rule_clarity_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceStalenessBacklogInput:
    public_case_id: str
    evidence_bundle_count: Decimal
    aggregate_evidence_age_seconds: Decimal
    source_class_reliability: Decimal
    contradiction_pressure: Decimal
    deadline_proximity: Decimal
    rule_clarity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceStalenessBacklogInput,
            "backlog input",
        )
        _require_public_case_id("public_case_id", self.public_case_id)
        object.__setattr__(
            self,
            "evidence_bundle_count",
            _require_positive_whole_decimal(
                "evidence_bundle_count",
                self.evidence_bundle_count,
            ),
        )
        object.__setattr__(
            self,
            "aggregate_evidence_age_seconds",
            _require_nonnegative_decimal(
                "aggregate_evidence_age_seconds",
                self.aggregate_evidence_age_seconds,
            ),
        )
        for field_name in (
            "source_class_reliability",
            "contradiction_pressure",
            "deadline_proximity",
            "rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("backlog input", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceStalenessBacklogRow:
    public_case_id: str
    evidence_bundle_count: Decimal
    aggregate_evidence_age_seconds: Decimal
    aggregate_age_pressure: Decimal
    source_class_reliability: Decimal
    source_class_reliability_gap: Decimal
    contradiction_pressure: Decimal
    deadline_proximity: Decimal
    rule_clarity: Decimal
    rule_clarity_gap: Decimal
    backlog_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceStalenessBacklogRow,
            "row",
        )
        _require_public_case_id("public_case_id", self.public_case_id)
        object.__setattr__(
            self,
            "evidence_bundle_count",
            _require_positive_whole_decimal(
                "evidence_bundle_count",
                self.evidence_bundle_count,
            ),
        )
        object.__setattr__(
            self,
            "aggregate_evidence_age_seconds",
            _require_nonnegative_decimal(
                "aggregate_evidence_age_seconds",
                self.aggregate_evidence_age_seconds,
            ),
        )
        for field_name in (
            "aggregate_age_pressure",
            "source_class_reliability",
            "source_class_reliability_gap",
            "contradiction_pressure",
            "deadline_proximity",
            "rule_clarity",
            "rule_clarity_gap",
            "backlog_pressure",
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
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceStalenessBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceStalenessBacklogReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceStalenessBacklogReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_backlog_pressure: Decimal | None
    max_aggregate_evidence_age_seconds: Decimal
    status: str
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...]
    reason_code_counts: tuple[ResearchResolutionEvidenceStalenessBacklogReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceStalenessBacklogReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_backlog_pressure",
            _require_optional_probability_decimal(
                "average_backlog_pressure",
                self.average_backlog_pressure,
            ),
        )
        object.__setattr__(
            self,
            "max_aggregate_evidence_age_seconds",
            _require_nonnegative_decimal(
                "max_aggregate_evidence_age_seconds",
                self.max_aggregate_evidence_age_seconds,
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
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_resolution_evidence_staleness_backlog_report(
    backlog_items: Iterable[object],
    *,
    config: ResearchResolutionEvidenceStalenessBacklogConfig,
    generated_at: datetime,
) -> ResearchResolutionEvidenceStalenessBacklogReport:
    if type(config) is not ResearchResolutionEvidenceStalenessBacklogConfig:
        raise ValueError(
            "config must be a ResearchResolutionEvidenceStalenessBacklogConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_backlog_items(backlog_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_case_id)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_backlog_pressure": _average_backlog_pressure(rows),
        "max_aggregate_evidence_age_seconds": max(
            (row.aggregate_evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchResolutionEvidenceStalenessBacklogReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_resolution_evidence_staleness_backlog_report_payload(
    report: ResearchResolutionEvidenceStalenessBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionEvidenceStalenessBacklogReport:
        raise ValueError(
            "report must be a ResearchResolutionEvidenceStalenessBacklogReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchResolutionEvidenceStalenessBacklogInput,
    *,
    config: ResearchResolutionEvidenceStalenessBacklogConfig,
) -> ResearchResolutionEvidenceStalenessBacklogRow:
    aggregate_age_pressure = _aggregate_age_pressure(
        item.aggregate_evidence_age_seconds,
        config=config,
    )
    reliability_gap = _quantize(_ONE - item.source_class_reliability)
    rule_clarity_gap = _quantize(_ONE - item.rule_clarity)
    backlog_pressure = _quantize(
        (aggregate_age_pressure * config.aggregate_age_weight)
        + (reliability_gap * config.source_class_reliability_weight)
        + (item.contradiction_pressure * config.contradiction_pressure_weight)
        + (item.deadline_proximity * config.deadline_proximity_weight)
        + (rule_clarity_gap * config.rule_clarity_weight),
    )
    status = _row_status(backlog_pressure, config=config)
    return ResearchResolutionEvidenceStalenessBacklogRow(
        public_case_id=item.public_case_id,
        evidence_bundle_count=item.evidence_bundle_count,
        aggregate_evidence_age_seconds=item.aggregate_evidence_age_seconds,
        aggregate_age_pressure=aggregate_age_pressure,
        source_class_reliability=item.source_class_reliability,
        source_class_reliability_gap=reliability_gap,
        contradiction_pressure=item.contradiction_pressure,
        deadline_proximity=item.deadline_proximity,
        rule_clarity=item.rule_clarity,
        rule_clarity_gap=rule_clarity_gap,
        backlog_pressure=backlog_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            aggregate_age_pressure=aggregate_age_pressure,
            source_class_reliability=item.source_class_reliability,
            contradiction_pressure=item.contradiction_pressure,
            deadline_proximity=item.deadline_proximity,
            rule_clarity=item.rule_clarity,
            input_reason_codes=item.reason_codes,
        ),
    )


def _normalize_backlog_items(
    backlog_items: Iterable[object],
) -> tuple[ResearchResolutionEvidenceStalenessBacklogInput, ...]:
    if isinstance(backlog_items, (str, bytes)):
        raise ValueError("backlog_items must be an iterable")
    try:
        values = tuple(backlog_items)
    except TypeError as exc:
        raise ValueError("backlog_items must be an iterable") from exc
    return tuple(_coerce_backlog_item(value) for value in values)


def _coerce_backlog_item(
    value: object,
) -> ResearchResolutionEvidenceStalenessBacklogInput:
    if type(value) is ResearchResolutionEvidenceStalenessBacklogInput:
        _require_hard_flags("backlog input", value)
        return value
    _require_hard_flags("backlog input", value)
    return ResearchResolutionEvidenceStalenessBacklogInput(
        public_case_id=_field_value(value, "public_case_id"),
        evidence_bundle_count=_field_value(value, "evidence_bundle_count"),
        aggregate_evidence_age_seconds=_field_value(
            value,
            "aggregate_evidence_age_seconds",
        ),
        source_class_reliability=_field_value(value, "source_class_reliability"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        deadline_proximity=_field_value(value, "deadline_proximity"),
        rule_clarity=_field_value(value, "rule_clarity"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _aggregate_age_pressure(
    age_seconds: Decimal,
    *,
    config: ResearchResolutionEvidenceStalenessBacklogConfig,
) -> Decimal:
    if age_seconds <= config.fresh_age_seconds:
        return _ZERO
    if age_seconds >= config.stale_age_seconds:
        return _ONE
    return _quantize(age_seconds / config.stale_age_seconds)


def _row_status(
    backlog_pressure: Decimal,
    *,
    config: ResearchResolutionEvidenceStalenessBacklogConfig,
) -> str:
    if backlog_pressure >= config.block_pressure_threshold:
        return "block"
    if backlog_pressure >= config.watch_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_age_pressure: Decimal,
    source_class_reliability: Decimal,
    contradiction_pressure: Decimal,
    deadline_proximity: Decimal,
    rule_clarity: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_evidence_staleness_{status}"}
    if aggregate_age_pressure == _ZERO:
        codes.add("aggregate_evidence_fresh")
    elif aggregate_age_pressure == _ONE:
        codes.add("aggregate_evidence_stale")
    else:
        codes.add("aggregate_evidence_aging")
    if source_class_reliability < Decimal("0.500000"):
        codes.add("source_class_reliability_low")
    elif source_class_reliability < Decimal("0.800000"):
        codes.add("source_class_reliability_mixed")
    else:
        codes.add("source_class_reliability_strong")
    if contradiction_pressure >= Decimal("0.500000"):
        codes.add("contradiction_pressure_high")
    elif contradiction_pressure >= Decimal("0.250000"):
        codes.add("contradiction_pressure_watch")
    if deadline_proximity >= Decimal("0.750000"):
        codes.add("deadline_proximity_high")
    elif deadline_proximity >= Decimal("0.350000"):
        codes.add("deadline_proximity_watch")
    if rule_clarity < Decimal("0.500000"):
        codes.add("rule_clarity_low")
    elif rule_clarity < Decimal("0.800000"):
        codes.add("rule_clarity_mixed")
    else:
        codes.add("rule_clarity_sufficient")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_staleness_backlog_items",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_evidence_staleness_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionEvidenceStalenessBacklogReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionEvidenceStalenessBacklogReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionEvidenceStalenessBacklogReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_backlog_pressure(
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.backlog_pressure for row in rows), _ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...],
) -> tuple[ResearchResolutionEvidenceStalenessBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionEvidenceStalenessBacklogRow:
            raise ValueError(
                "rows must contain ResearchResolutionEvidenceStalenessBacklogRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_case_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_case_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionEvidenceStalenessBacklogReasonCodeCount, ...],
) -> tuple[ResearchResolutionEvidenceStalenessBacklogReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionEvidenceStalenessBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionEvidenceStalenessBacklogReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchResolutionEvidenceStalenessBacklogRow,
) -> None:
    if row.source_class_reliability_gap != _quantize(_ONE - row.source_class_reliability):
        raise ValueError("source_class_reliability_gap must match source_class_reliability")
    if row.rule_clarity_gap != _quantize(_ONE - row.rule_clarity):
        raise ValueError("rule_clarity_gap must match rule_clarity")
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"resolution_evidence_staleness_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(
    report: ResearchResolutionEvidenceStalenessBacklogReport,
) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_backlog_pressure != _average_backlog_pressure(report.rows):
        raise ValueError("average_backlog_pressure must match rows")
    expected_max_age = max(
        (row.aggregate_evidence_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_aggregate_evidence_age_seconds != expected_max_age:
        raise ValueError("max_aggregate_evidence_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchResolutionEvidenceStalenessBacklogReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON value must use exact Decimal values")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        _reject_text_value("JSON string value", value)
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _field_value(value: object, name: str, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if any(field.name == name for field in fields(value)):
            return getattr(value, name)
    elif isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{name} is required")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_text_value(name, value)
    return value


def _require_public_case_id(name: str, value: str) -> str:
    _require_public_identifier(name, value)
    normalized = value.lower()
    if any(term in normalized for term in _CASE_ID_UNSAFE_TERMS):
        raise ValueError(f"{name} must not expose market or evidence surface identifiers")
    return value


def _require_reason_code(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase reason code")
    _reject_text_value(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be nonempty")
    normalized = tuple(_require_reason_code(name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(sorted(normalized))


def _require_status(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(result)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(result)


def _require_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_positive_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_probability_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO or result > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(result)


def _require_optional_probability_decimal(
    name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(name, value)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_text_value(label, key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_text_value(label, value)


def _reject_text_value(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _PAYLOAD_UNSAFE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface text")
    if any(term in normalized for term in _ACTION_TERMS):
        raise ValueError(f"{label} contains unsafe action text")
