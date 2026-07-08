"""Pure report-only summary for public resolution evidence quality variance."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ResearchResolutionEvidenceQualityVarianceConfig",
    "ResearchResolutionEvidenceQualityVarianceInput",
    "ResearchResolutionEvidenceQualityVarianceReasonCodeCount",
    "ResearchResolutionEvidenceQualityVarianceReport",
    "ResearchResolutionEvidenceQualityVarianceRow",
    "build_research_resolution_evidence_quality_variance_report",
    "research_resolution_evidence_quality_variance_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-evidence-quality-variance-v0"
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_STATUSES = ("pass", "watch", "block")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_BUCKET_ID_UNSAFE_TERMS = (
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
    "raw_url",
    "raw_text",
    "raw_ref",
    "market_slug",
    "market_id",
    "market_identifier",
    "condition_id",
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
class ResearchResolutionEvidenceQualityVarianceConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    oracle_lag_fresh_seconds: Decimal = Decimal("3600")
    oracle_lag_stale_seconds: Decimal = Decimal("86400")
    watch_variance_threshold: Decimal = Decimal("0.350000")
    block_variance_threshold: Decimal = Decimal("0.700000")
    source_reliability_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    rule_clarity_weight: Decimal = Decimal("0.150000")
    oracle_lag_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceQualityVarianceConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("oracle_lag_fresh_seconds", "oracle_lag_stale_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.oracle_lag_stale_seconds <= self.oracle_lag_fresh_seconds:
            raise ValueError("oracle_lag_stale_seconds must exceed oracle_lag_fresh_seconds")
        for field_name in (
            "watch_variance_threshold",
            "block_variance_threshold",
            "source_reliability_weight",
            "freshness_weight",
            "contradiction_pressure_weight",
            "rule_clarity_weight",
            "oracle_lag_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_variance_threshold <= self.watch_variance_threshold:
            raise ValueError("block_variance_threshold must exceed watch_variance_threshold")
        weight_sum = _quantize(
            self.source_reliability_weight
            + self.freshness_weight
            + self.contradiction_pressure_weight
            + self.rule_clarity_weight
            + self.oracle_lag_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "source_reliability_weight, freshness_weight, "
                "contradiction_pressure_weight, rule_clarity_weight, "
                "and oracle_lag_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceQualityVarianceInput:
    public_bucket_id: str
    evidence_group_count: Decimal
    aggregate_source_reliability: Decimal
    aggregate_freshness: Decimal
    contradiction_pressure: Decimal
    rule_clarity: Decimal
    oracle_lag_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceQualityVarianceInput,
            "quality variance input",
        )
        _require_public_bucket_id("public_bucket_id", self.public_bucket_id)
        object.__setattr__(
            self,
            "evidence_group_count",
            _require_positive_whole_decimal(
                "evidence_group_count",
                self.evidence_group_count,
            ),
        )
        for field_name in (
            "aggregate_source_reliability",
            "aggregate_freshness",
            "contradiction_pressure",
            "rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oracle_lag_seconds",
            _require_nonnegative_decimal("oracle_lag_seconds", self.oracle_lag_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("quality variance input", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceQualityVarianceRow:
    public_bucket_id: str
    evidence_group_count: Decimal
    aggregate_source_reliability: Decimal
    source_reliability_gap: Decimal
    aggregate_freshness: Decimal
    freshness_gap: Decimal
    contradiction_pressure: Decimal
    rule_clarity: Decimal
    rule_clarity_gap: Decimal
    oracle_lag_seconds: Decimal
    oracle_lag_pressure: Decimal
    quality_variance_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceQualityVarianceRow,
            "row",
        )
        _require_public_bucket_id("public_bucket_id", self.public_bucket_id)
        object.__setattr__(
            self,
            "evidence_group_count",
            _require_positive_whole_decimal(
                "evidence_group_count",
                self.evidence_group_count,
            ),
        )
        for field_name in (
            "aggregate_source_reliability",
            "source_reliability_gap",
            "aggregate_freshness",
            "freshness_gap",
            "contradiction_pressure",
            "rule_clarity",
            "rule_clarity_gap",
            "oracle_lag_pressure",
            "quality_variance_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oracle_lag_seconds",
            _require_nonnegative_decimal("oracle_lag_seconds", self.oracle_lag_seconds),
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
class ResearchResolutionEvidenceQualityVarianceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceQualityVarianceReasonCodeCount,
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
class ResearchResolutionEvidenceQualityVarianceReport:
    generated_at: datetime
    config_version: str
    bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quality_variance_pressure: Decimal | None
    max_oracle_lag_seconds: Decimal
    status: str
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...]
    reason_code_counts: tuple[
        ResearchResolutionEvidenceQualityVarianceReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceQualityVarianceReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("bucket_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quality_variance_pressure",
            _require_optional_probability_decimal(
                "average_quality_variance_pressure",
                self.average_quality_variance_pressure,
            ),
        )
        object.__setattr__(
            self,
            "max_oracle_lag_seconds",
            _require_nonnegative_decimal(
                "max_oracle_lag_seconds",
                self.max_oracle_lag_seconds,
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


def build_research_resolution_evidence_quality_variance_report(
    quality_items: Iterable[object],
    *,
    config: ResearchResolutionEvidenceQualityVarianceConfig,
    generated_at: datetime,
) -> ResearchResolutionEvidenceQualityVarianceReport:
    if type(config) is not ResearchResolutionEvidenceQualityVarianceConfig:
        raise ValueError(
            "config must be a ResearchResolutionEvidenceQualityVarianceConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_quality_items(quality_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_bucket_id)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "bucket_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_quality_variance_pressure": _average_quality_variance_pressure(rows),
        "max_oracle_lag_seconds": max(
            (row.oracle_lag_seconds for row in rows),
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
    return ResearchResolutionEvidenceQualityVarianceReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_resolution_evidence_quality_variance_report_payload(
    report: ResearchResolutionEvidenceQualityVarianceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionEvidenceQualityVarianceReport:
        raise ValueError(
            "report must be a ResearchResolutionEvidenceQualityVarianceReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchResolutionEvidenceQualityVarianceInput,
    *,
    config: ResearchResolutionEvidenceQualityVarianceConfig,
) -> ResearchResolutionEvidenceQualityVarianceRow:
    source_reliability_gap = _quantize(_ONE - item.aggregate_source_reliability)
    freshness_gap = _quantize(_ONE - item.aggregate_freshness)
    rule_clarity_gap = _quantize(_ONE - item.rule_clarity)
    oracle_lag_pressure = _oracle_lag_pressure(item.oracle_lag_seconds, config=config)
    quality_variance_pressure = _quantize(
        (source_reliability_gap * config.source_reliability_weight)
        + (freshness_gap * config.freshness_weight)
        + (item.contradiction_pressure * config.contradiction_pressure_weight)
        + (rule_clarity_gap * config.rule_clarity_weight)
        + (oracle_lag_pressure * config.oracle_lag_weight),
    )
    status = _row_status(quality_variance_pressure, config=config)
    return ResearchResolutionEvidenceQualityVarianceRow(
        public_bucket_id=item.public_bucket_id,
        evidence_group_count=item.evidence_group_count,
        aggregate_source_reliability=item.aggregate_source_reliability,
        source_reliability_gap=source_reliability_gap,
        aggregate_freshness=item.aggregate_freshness,
        freshness_gap=freshness_gap,
        contradiction_pressure=item.contradiction_pressure,
        rule_clarity=item.rule_clarity,
        rule_clarity_gap=rule_clarity_gap,
        oracle_lag_seconds=item.oracle_lag_seconds,
        oracle_lag_pressure=oracle_lag_pressure,
        quality_variance_pressure=quality_variance_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            aggregate_source_reliability=item.aggregate_source_reliability,
            aggregate_freshness=item.aggregate_freshness,
            contradiction_pressure=item.contradiction_pressure,
            rule_clarity=item.rule_clarity,
            oracle_lag_pressure=oracle_lag_pressure,
            input_reason_codes=item.reason_codes,
        ),
    )


def _normalize_quality_items(
    quality_items: Iterable[object],
) -> tuple[ResearchResolutionEvidenceQualityVarianceInput, ...]:
    if isinstance(quality_items, (str, bytes)):
        raise ValueError("quality_items must be an iterable")
    try:
        values = tuple(quality_items)
    except TypeError as exc:
        raise ValueError("quality_items must be an iterable") from exc
    return tuple(_coerce_quality_item(value) for value in values)


def _coerce_quality_item(
    value: object,
) -> ResearchResolutionEvidenceQualityVarianceInput:
    if type(value) is ResearchResolutionEvidenceQualityVarianceInput:
        _require_hard_flags("quality variance input", value)
        return value
    _require_hard_flags("quality variance input", value)
    return ResearchResolutionEvidenceQualityVarianceInput(
        public_bucket_id=_field_value(value, "public_bucket_id"),
        evidence_group_count=_field_value(value, "evidence_group_count"),
        aggregate_source_reliability=_field_value(
            value,
            "aggregate_source_reliability",
        ),
        aggregate_freshness=_field_value(value, "aggregate_freshness"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        rule_clarity=_field_value(value, "rule_clarity"),
        oracle_lag_seconds=_field_value(value, "oracle_lag_seconds"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _oracle_lag_pressure(
    lag_seconds: Decimal,
    *,
    config: ResearchResolutionEvidenceQualityVarianceConfig,
) -> Decimal:
    if lag_seconds <= config.oracle_lag_fresh_seconds:
        return _ZERO
    if lag_seconds >= config.oracle_lag_stale_seconds:
        return _ONE
    return _quantize(lag_seconds / config.oracle_lag_stale_seconds)


def _row_status(
    quality_variance_pressure: Decimal,
    *,
    config: ResearchResolutionEvidenceQualityVarianceConfig,
) -> str:
    if quality_variance_pressure >= config.block_variance_threshold:
        return "block"
    if quality_variance_pressure >= config.watch_variance_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_source_reliability: Decimal,
    aggregate_freshness: Decimal,
    contradiction_pressure: Decimal,
    rule_clarity: Decimal,
    oracle_lag_pressure: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_evidence_quality_variance_{status}"}
    if aggregate_source_reliability < Decimal("0.500000"):
        codes.add("source_reliability_low")
    elif aggregate_source_reliability < Decimal("0.800000"):
        codes.add("source_reliability_mixed")
    else:
        codes.add("source_reliability_strong")
    if aggregate_freshness < Decimal("0.500000"):
        codes.add("aggregate_freshness_low")
    elif aggregate_freshness < Decimal("0.800000"):
        codes.add("aggregate_freshness_mixed")
    else:
        codes.add("aggregate_freshness_strong")
    if contradiction_pressure >= Decimal("0.500000"):
        codes.add("contradiction_pressure_high")
    elif contradiction_pressure >= Decimal("0.250000"):
        codes.add("contradiction_pressure_watch")
    if rule_clarity < Decimal("0.500000"):
        codes.add("rule_clarity_low")
    elif rule_clarity < Decimal("0.800000"):
        codes.add("rule_clarity_mixed")
    else:
        codes.add("rule_clarity_sufficient")
    if oracle_lag_pressure == _ZERO:
        codes.add("oracle_lag_fresh")
    elif oracle_lag_pressure == _ONE:
        codes.add("oracle_lag_stale")
    else:
        codes.add("oracle_lag_aging")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_quality_variance_items",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_evidence_quality_variance_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionEvidenceQualityVarianceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionEvidenceQualityVarianceReasonCodeCount(
                reason_code=reason_codes[0],
                count=Decimal("1"),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionEvidenceQualityVarianceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_quality_variance_pressure(
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.quality_variance_pressure for row in rows), _ZERO)
        / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchResolutionEvidenceQualityVarianceRow, ...],
) -> tuple[ResearchResolutionEvidenceQualityVarianceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionEvidenceQualityVarianceRow:
            raise ValueError(
                "rows must contain ResearchResolutionEvidenceQualityVarianceRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_bucket_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_bucket_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionEvidenceQualityVarianceReasonCodeCount, ...],
) -> tuple[ResearchResolutionEvidenceQualityVarianceReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionEvidenceQualityVarianceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionEvidenceQualityVarianceReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchResolutionEvidenceQualityVarianceRow,
) -> None:
    if row.source_reliability_gap != _quantize(_ONE - row.aggregate_source_reliability):
        raise ValueError("source_reliability_gap must match aggregate_source_reliability")
    if row.freshness_gap != _quantize(_ONE - row.aggregate_freshness):
        raise ValueError("freshness_gap must match aggregate_freshness")
    if row.rule_clarity_gap != _quantize(_ONE - row.rule_clarity):
        raise ValueError("rule_clarity_gap must match rule_clarity")
    if row.status == "pass" and row.quality_variance_pressure >= Decimal("0.350000"):
        raise ValueError("quality_variance_pressure must support pass status")
    if row.status == "watch" and (
        row.quality_variance_pressure < Decimal("0.350000")
        or row.quality_variance_pressure >= Decimal("0.700000")
    ):
        raise ValueError("quality_variance_pressure must support watch status")
    if row.status == "block" and row.quality_variance_pressure < Decimal("0.700000"):
        raise ValueError("quality_variance_pressure must support block status")


def _validate_report_consistency(
    report: ResearchResolutionEvidenceQualityVarianceReport,
) -> None:
    if report.bucket_count != _decimal_count(len(report.rows)):
        raise ValueError("bucket_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_quality_variance_pressure != _average_quality_variance_pressure(
        report.rows,
    ):
        raise ValueError("average_quality_variance_pressure must match rows")
    if report.max_oracle_lag_seconds != max(
        (row.oracle_lag_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_oracle_lag_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchResolutionEvidenceQualityVarianceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    _reject_public_payload("report digest payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


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


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


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
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


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
    return value.quantize(_QUANT)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public identifier")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_bucket_id(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    lowered = value.lower()
    if any(term in lowered for term in _BUCKET_ID_UNSAFE_TERMS):
        raise ValueError(f"{field_name} must not contain unsafe public terms")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or _REASON_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must contain public snake_case reason codes")


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
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of {_STATUSES}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be true")


def _reject_public_payload(label: str, payload: object) -> None:
    encoded = json.dumps(_json_ready(payload), sort_keys=True).lower()
    for fragment in _PAYLOAD_UNSAFE_FRAGMENTS + _ACTION_TERMS:
        if fragment in encoded:
            raise ValueError(f"{label} contains unsafe public payload content")
