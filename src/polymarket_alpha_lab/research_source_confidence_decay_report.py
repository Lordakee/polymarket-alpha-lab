"""Pure source confidence decay report for caller supplied evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from json import dumps
from typing import Any


__all__ = (
    "ResearchSourceConfidenceDecayBucketRow",
    "ResearchSourceConfidenceDecayConfig",
    "ResearchSourceConfidenceDecayEvidence",
    "ResearchSourceConfidenceDecayReasonCodeCount",
    "ResearchSourceConfidenceDecayReport",
    "build_research_source_confidence_decay_report",
    "research_source_confidence_decay_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-confidence-decay-report-v0"
STATUSES = ("pass", "watch", "block")
AGE_BUCKETS = ("fresh", "aging", "stale")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
REDACTED_SOURCE_LOCATOR = "[redacted_source_locator]"
REDACTED_EVIDENCE_EXCERPT = "[redacted_evidence_excerpt]"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("candidate", "_", "id"),
        ("market", "_", "id"),
        ("market", "_", "slug"),
        ("ques", "tion"),
        ("source", "_", "url"),
        ("source", "_", "text"),
        ("source", "_", "loc", "ator"),
        ("evidence", "_", "excerpt"),
        ("d", "s", "n"),
        ("ta", "ble"),
        ("private",),
        ("to", "ken"),
        ("sec", "ret"),
        ("api", "_", "key"),
        ("sess", "ion"),
        ("raw",),
        ("li", "ve"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("wal", "let"),
        ("bro", "ker"),
        ("or", "der"),
        ("can", "cel"),
        ("re", "place"),
        ("ex", "change"),
        ("mut", "ation"),
        ("sign", "ing"),
        ("au", "th"),
        ("tra", "de"),
        ("ad", "vice"),
        ("creden", "tial"),
        ("private", "_", "key"),
    )
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceConfidenceDecayConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    pass_decayed_confidence_score: Decimal = Decimal("0.700000")
    block_decayed_confidence_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceConfidenceDecayConfig:
            raise ValueError("config must be exactly ResearchSourceConfidenceDecayConfig")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "pass_decayed_confidence_score",
            "block_decayed_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_decayed_confidence_score <= self.block_decayed_confidence_score:
            raise ValueError(
                "pass_decayed_confidence_score must be greater than "
                "block_decayed_confidence_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceConfidenceDecayEvidence:
    evidence_key: str
    source_class: str
    source_confidence: Decimal
    observed_at: datetime
    source_locator: str = ""
    evidence_excerpt: str = ""
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceConfidenceDecayEvidence:
            raise ValueError(
                "evidence must be exactly ResearchSourceConfidenceDecayEvidence",
            )
        _require_canonical_string("evidence_key", self.evidence_key)
        _require_safe_public_string("source_class", self.source_class)
        object.__setattr__(
            self,
            "source_confidence",
            _require_probability_decimal("source_confidence", self.source_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.source_locator) is not str:
            raise ValueError("source_locator must be a string")
        if type(self.evidence_excerpt) is not str:
            raise ValueError("evidence_excerpt must be a string")
        object.__setattr__(self, "source_locator", REDACTED_SOURCE_LOCATOR)
        object.__setattr__(self, "evidence_excerpt", REDACTED_EVIDENCE_EXCERPT)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceConfidenceDecayBucketRow:
    source_class: str
    age_bucket: str
    evidence_count: Decimal
    average_source_confidence: Decimal
    average_age_seconds: Decimal
    average_age_decay_factor: Decimal
    average_decayed_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceConfidenceDecayBucketRow:
            raise ValueError("row must be exactly ResearchSourceConfidenceDecayBucketRow")
        _require_safe_public_string("source_class", self.source_class)
        _require_member("age_bucket", self.age_bucket, AGE_BUCKETS)
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_whole_decimal("evidence_count", self.evidence_count),
        )
        for field_name in (
            "average_source_confidence",
            "average_age_decay_factor",
            "average_decayed_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_age_seconds",
            _require_nonnegative_decimal(
                "average_age_seconds",
                self.average_age_seconds,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _validate_derived_validation_digest(
                "row",
                self,
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchSourceConfidenceDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceConfidenceDecayReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchSourceConfidenceDecayReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceConfidenceDecayReport:
    generated_at: datetime
    config_version: str
    evidence_count: Decimal
    bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decayed_confidence_score: Decimal | None
    status: str
    rows: tuple[ResearchSourceConfidenceDecayBucketRow, ...]
    reason_code_counts: tuple[ResearchSourceConfidenceDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceConfidenceDecayReport:
            raise ValueError("report must be exactly ResearchSourceConfidenceDecayReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_count",
            "bucket_count",
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
            "average_decayed_confidence_score",
            _require_optional_probability_decimal(
                "average_decayed_confidence_score",
                self.average_decayed_confidence_score,
            ),
        )
        _require_member("status", self.status, STATUSES)
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
        object.__setattr__(
            self,
            "derived_validation_digest",
            _validate_derived_validation_digest(
                "report",
                self,
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _payload_value(self))


def build_research_source_confidence_decay_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchSourceConfidenceDecayConfig,
    generated_at: datetime,
) -> ResearchSourceConfidenceDecayReport:
    if type(config) is not ResearchSourceConfidenceDecayConfig:
        raise ValueError("config must be a ResearchSourceConfidenceDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        _reject_future_observed_at(item, generated_at_utc)

    grouped: dict[tuple[str, str], list[tuple[ResearchSourceConfidenceDecayEvidence, Decimal]]] = {}
    for item in evidence_items:
        age_seconds = _age_seconds(generated_at_utc, item.observed_at)
        bucket = _age_bucket(age_seconds, config=config)
        grouped.setdefault((item.source_class, bucket), []).append((item, age_seconds))

    rows = tuple(
        _bucket_row(
            source_class=source_class,
            age_bucket=age_bucket,
            evidence_rows=tuple(grouped[(source_class, age_bucket)]),
            config=config,
        )
        for source_class, age_bucket in sorted(
            grouped,
            key=lambda key: (key[0], key[1]),
        )
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceConfidenceDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        evidence_count=_decimal_count(len(evidence_items)),
        bucket_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_decayed_confidence_score=_average_report_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_confidence_decay_report_payload(
    report: ResearchSourceConfidenceDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceConfidenceDecayReport:
        _require_hard_flags("report", report)
        payload = _payload_value(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("report", payload)
        _validate_payload_digests(payload, require_current=True)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_values("payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        _validate_payload_digests(report, require_current=True)
        return report
    raise ValueError("report must be a ResearchSourceConfidenceDecayReport")


def _bucket_row(
    *,
    source_class: str,
    age_bucket: str,
    evidence_rows: tuple[tuple[ResearchSourceConfidenceDecayEvidence, Decimal], ...],
    config: ResearchSourceConfidenceDecayConfig,
) -> ResearchSourceConfidenceDecayBucketRow:
    if not evidence_rows:
        raise ValueError("evidence_rows must be nonempty")
    confidences = tuple(item.source_confidence for item, _ in evidence_rows)
    ages = tuple(age_seconds for _, age_seconds in evidence_rows)
    factors = tuple(_age_decay_factor(age_seconds, config=config) for age_seconds in ages)
    decayed_scores = tuple(
        _quantize(item.source_confidence * factor)
        for (item, _), factor in zip(evidence_rows, factors, strict=True)
    )
    average_decayed_score = _average_decimal(decayed_scores)
    status = _row_status(average_decayed_score, config=config)

    return ResearchSourceConfidenceDecayBucketRow(
        source_class=source_class,
        age_bucket=age_bucket,
        evidence_count=_decimal_count(len(evidence_rows)),
        average_source_confidence=_average_decimal(confidences),
        average_age_seconds=_average_age_seconds(ages),
        average_age_decay_factor=_average_decimal(factors),
        average_decayed_confidence_score=average_decayed_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            age_bucket=age_bucket,
            input_reason_codes=tuple(
                reason_code for item, _ in evidence_rows for reason_code in item.reason_codes
            ),
        ),
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchSourceConfidenceDecayEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_evidence_row(value) for value in values)


def _coerce_evidence_row(value: object) -> ResearchSourceConfidenceDecayEvidence:
    if type(value) is ResearchSourceConfidenceDecayEvidence:
        _require_hard_flags("evidence", value)
        return value
    _require_hard_flags("evidence", value)
    return ResearchSourceConfidenceDecayEvidence(
        evidence_key=_field_value(value, "evidence_key"),
        source_class=_field_value(value, "source_class"),
        source_confidence=_field_value(value, "source_confidence"),
        observed_at=_field_value(value, "observed_at"),
        source_locator=_field_value(value, "source_locator", default=""),
        evidence_excerpt=_field_value(value, "evidence_excerpt", default=""),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _age_bucket(
    age_seconds: Decimal,
    *,
    config: ResearchSourceConfidenceDecayConfig,
) -> str:
    if age_seconds <= config.fresh_age_seconds:
        return "fresh"
    if age_seconds >= config.stale_age_seconds:
        return "stale"
    return "aging"


def _age_decay_factor(
    age_seconds: Decimal,
    *,
    config: ResearchSourceConfidenceDecayConfig,
) -> Decimal:
    if age_seconds <= config.fresh_age_seconds:
        return ONE
    if age_seconds >= config.stale_age_seconds:
        return ZERO
    return _quantize(ONE - (age_seconds / config.stale_age_seconds))


def _row_status(
    decayed_confidence_score: Decimal,
    *,
    config: ResearchSourceConfidenceDecayConfig,
) -> str:
    if decayed_confidence_score <= config.block_decayed_confidence_score:
        return "block"
    if decayed_confidence_score < config.pass_decayed_confidence_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    age_bucket: str,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {
        f"source_confidence_decay_{status}",
        f"source_age_bucket_{age_bucket}",
    }
    if age_bucket != "fresh":
        reason_codes.add("confidence_age_decay_applied")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchSourceConfidenceDecayBucketRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_source_confidence_evidence",)
    if all(row.status == "pass" for row in rows):
        return ("source_confidence_decay_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_source_confidence_evidence",):
        return "block"
    if "source_confidence_decay_block" in reason_codes:
        return "block"
    if "source_confidence_decay_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSourceConfidenceDecayBucketRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceConfidenceDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceConfidenceDecayReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceConfidenceDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_report_score(
    rows: tuple[ResearchSourceConfidenceDecayBucketRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    weighted_total = sum(
        (
            row.average_decayed_confidence_score * row.evidence_count
            for row in rows
        ),
        ZERO,
    )
    evidence_total = sum((row.evidence_count for row in rows), ZERO)
    return _quantize(weighted_total / evidence_total)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _average_age_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    average = sum(values, ZERO) / Decimal(len(values))
    return average.quantize(Decimal("0.000001")) if average % ONE else +average


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _reject_future_observed_at(
    item: ResearchSourceConfidenceDecayEvidence,
    generated_at: datetime,
) -> None:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _status_count(
    rows: tuple[ResearchSourceConfidenceDecayBucketRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceConfidenceDecayBucketRow, ...],
) -> tuple[ResearchSourceConfidenceDecayBucketRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceConfidenceDecayBucketRow:
            raise ValueError(
                "rows must contain ResearchSourceConfidenceDecayBucketRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.source_class, row.age_bucket)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by source_class and age_bucket")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceConfidenceDecayReasonCodeCount, ...],
) -> tuple[ResearchSourceConfidenceDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceConfidenceDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceConfidenceDecayReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_report_consistency(report: ResearchSourceConfidenceDecayReport) -> None:
    if report.bucket_count != _decimal_count(len(report.rows)):
        raise ValueError("bucket_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_decayed_confidence_score != _average_report_score(report.rows):
        raise ValueError("average_decayed_confidence_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_derived_validation_digest(
    label: str,
    value: object,
    supplied_digest: object,
) -> str:
    expected_digest = _derived_validation_digest(value)
    if supplied_digest == "":
        return expected_digest
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, supplied_digest)
    if supplied_digest != expected_digest:
        raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} must match {label} fields")
    return supplied_digest


def _derived_validation_digest(value: object) -> str:
    digest_payload = _digest_ready(value)
    encoded = dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, tuple):
        return [_digest_ready(item) for item in value]
    if isinstance(value, list):
        return [_digest_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _digest_ready(item)
            for key, item in value.items()
            if key != DERIVED_VALIDATION_DIGEST_FIELD
        }
    return value


def _validate_payload_digests(
    value: object,
    *,
    require_current: bool = False,
) -> None:
    if type(value) is dict:
        if require_current and DERIVED_VALIDATION_DIGEST_FIELD not in value:
            raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} is required")
        if DERIVED_VALIDATION_DIGEST_FIELD in value:
            supplied_digest = value[DERIVED_VALIDATION_DIGEST_FIELD]
            _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, supplied_digest)
            expected_digest = _derived_validation_digest(value)
            if supplied_digest != expected_digest:
                raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} must match payload")
        for item in value.values():
            _validate_payload_digests(item)
        return
    if type(value) is list:
        for item in value:
            _validate_payload_digests(item)


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) in (float, int):
        raise ValueError("value must use Decimal-string serialization")
    return value


def _validate_public_payload_values(label: str, value: object, path: str = "") -> None:
    location = path or label
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError(f"{location} must use Decimal strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{location} keys must be strings")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key if not path else path + '.' + key} must be True")
            item_path = key if not path else f"{path}.{key}"
            _validate_public_payload_values(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _validate_public_payload_values(label, item, item_path)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    location = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{location} keys must be strings")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"{location} has unsafe key")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError(f"{location} has unsafe value")


def _contains_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


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
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_safe_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


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


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    allowed = "0123456789abcdef"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


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


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


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
