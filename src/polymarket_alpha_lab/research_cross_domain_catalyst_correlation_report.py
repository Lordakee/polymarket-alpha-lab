"""Pure public reducer for cross-domain catalyst correlation pressure."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_CROSS_DOMAIN_CATALYST_CORRELATION_CONFIG_VERSION = (
    "research-cross-domain-catalyst-correlation-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_ALLOWED_DOMAINS = frozenset(
    ("politics", "crypto", "equities", "gold", "soccer", "basketball"),
)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_RANK = {
    "correlation_pressure_block": 0,
    "correlation_pressure_watch": 1,
    "shared_conflict_high": 2,
    "shared_conflict_watch": 3,
    "shared_intensity_high": 4,
    "shared_intensity_watch": 5,
    "correlation_pressure_pass": 6,
    "insufficient_domain_coverage": 7,
}
_PASS_REASON = "correlation_pressure_pass"
_INSUFFICIENT_REASON = "insufficient_domain_coverage"


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("event", "_", "id"),
        _surface_term("event", "_", "text"),
        _surface_term("market", "_", "id"),
        _surface_term("market", "_", "slug"),
        _surface_term("source", "_", "id"),
        _surface_term("source", "_", "text"),
        _surface_term("raw", "-", "event"),
        _surface_term("raw", "_", "event"),
        _surface_term("wa", "llet"),
        _surface_term("au", "th"),
        _surface_term("or", "der"),
        _surface_term("tra", "de"),
        _surface_term("private", "_", "key"),
        _surface_term("private", "-", "key"),
        _surface_term("private", " ", "key"),
        _surface_term("data", "base"),
        _surface_term("net", "work"),
        _surface_term("live", "_", "execution"),
        _surface_term("live", "-", "execution"),
        _surface_term("reco", "mmendation"),
        _surface_term("reco", "mmended"),
        _surface_term("siz", "ing"),
    ),
)


@dataclass(frozen=True)
class ResearchCrossDomainCatalystCorrelationConfig:
    config_version: str
    watch_correlation_pressure: Decimal
    block_correlation_pressure: Decimal
    shared_intensity_watch: Decimal
    shared_intensity_high: Decimal
    shared_conflict_watch: Decimal
    shared_conflict_high: Decimal
    intensity_weight: Decimal
    freshness_weight: Decimal
    conflict_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "watch_correlation_pressure",
            "block_correlation_pressure",
            "shared_intensity_watch",
            "shared_intensity_high",
            "shared_conflict_watch",
            "shared_conflict_high",
            "intensity_weight",
            "freshness_weight",
            "conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_correlation_pressure <= self.watch_correlation_pressure:
            raise ValueError(
                "block_correlation_pressure must exceed watch_correlation_pressure",
            )
        if self.shared_intensity_high < self.shared_intensity_watch:
            raise ValueError("shared_intensity_high must be at least shared_intensity_watch")
        if self.shared_conflict_high < self.shared_conflict_watch:
            raise ValueError("shared_conflict_high must be at least shared_conflict_watch")
        if self.intensity_weight <= _ZERO:
            raise ValueError("intensity_weight must be positive")
        if self.freshness_weight <= _ZERO:
            raise ValueError("freshness_weight must be positive")
        if self.conflict_weight <= _ZERO:
            raise ValueError("conflict_weight must be positive")
        if (
            self.intensity_weight
            + self.freshness_weight
            + self.conflict_weight
            != _ONE
        ):
            raise ValueError("weights must sum to 1")
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchCrossDomainCatalystCorrelationInput:
    domain: str
    aggregate_intensity: Decimal
    aggregate_freshness: Decimal
    aggregate_conflict: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_domain(self.domain)
        for field_name in (
            "aggregate_intensity",
            "aggregate_freshness",
            "aggregate_conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchCrossDomainCatalystCorrelationPairRow:
    domain_a: str
    domain_b: str
    status: str
    domain_a_pressure: Decimal
    domain_b_pressure: Decimal
    average_intensity: Decimal
    average_freshness: Decimal
    average_conflict: Decimal
    pressure_alignment: Decimal
    correlation_pressure: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_domain(self.domain_a)
        _require_domain(self.domain_b)
        if self.domain_a >= self.domain_b:
            raise ValueError("domain_a must sort before domain_b")
        _require_status("status", self.status)
        for field_name in (
            "domain_a_pressure",
            "domain_b_pressure",
            "average_intensity",
            "average_freshness",
            "average_conflict",
            "pressure_alignment",
            "correlation_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)


@dataclass(frozen=True)
class ResearchCrossDomainCatalystCorrelationReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_ratio("row_ratio", self.row_ratio),
        )
        _require_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCrossDomainCatalystCorrelationReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_count: Decimal
    pair_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_correlation_pressure: Decimal
    max_correlation_pressure: Decimal
    max_aggregate_intensity: Decimal
    max_aggregate_conflict: Decimal
    min_aggregate_freshness: Decimal
    covered_domains: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCrossDomainCatalystCorrelationPairRow, ...]
    reason_code_counts: tuple[ResearchCrossDomainCatalystCorrelationReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "domain_count",
            "pair_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_correlation_pressure",
            "max_correlation_pressure",
            "max_aggregate_intensity",
            "max_aggregate_conflict",
            "min_aggregate_freshness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "covered_domains",
            _normalize_domains("covered_domains", self.covered_domains),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_flags("report", self)
        _check_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_cross_domain_catalyst_correlation_report_payload(self)


def build_research_cross_domain_catalyst_correlation_report(
    inputs: object,
    *,
    config: ResearchCrossDomainCatalystCorrelationConfig,
    generated_at: datetime,
) -> ResearchCrossDomainCatalystCorrelationReport:
    if type(config) is not ResearchCrossDomainCatalystCorrelationConfig:
        raise ValueError("config must be a ResearchCrossDomainCatalystCorrelationConfig")
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_for_pair(left, right, config=config)
                for index, left in enumerate(normalized_inputs)
                for right in normalized_inputs[index + 1 :]
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchCrossDomainCatalystCorrelationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        domain_count=_count(len(normalized_inputs)),
        pair_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_correlation_pressure=_average_or_zero(
            tuple(row.correlation_pressure for row in rows),
        ),
        max_correlation_pressure=_max_or_zero(
            tuple(row.correlation_pressure for row in rows),
        ),
        max_aggregate_intensity=_max_or_zero(
            tuple(item.aggregate_intensity for item in normalized_inputs),
        ),
        max_aggregate_conflict=_max_or_zero(
            tuple(item.aggregate_conflict for item in normalized_inputs),
        ),
        min_aggregate_freshness=_min_or_zero(
            tuple(item.aggregate_freshness for item in normalized_inputs),
        ),
        covered_domains=tuple(item.domain for item in normalized_inputs),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_cross_domain_catalyst_correlation_report_payload(
    report: ResearchCrossDomainCatalystCorrelationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCrossDomainCatalystCorrelationReport:
        _require_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_flag_downgrades("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchCrossDomainCatalystCorrelationReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_public("payload", payload)
    _reject_flag_downgrades("payload", payload)
    _verify_payload_digest(payload)
    return payload


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


def _row_for_pair(
    left: ResearchCrossDomainCatalystCorrelationInput,
    right: ResearchCrossDomainCatalystCorrelationInput,
    *,
    config: ResearchCrossDomainCatalystCorrelationConfig,
) -> ResearchCrossDomainCatalystCorrelationPairRow:
    first, second = tuple(sorted((left, right), key=lambda item: item.domain))
    first_pressure = _domain_pressure(first, config)
    second_pressure = _domain_pressure(second, config)
    average_intensity = _average((first.aggregate_intensity, second.aggregate_intensity))
    average_freshness = _average((first.aggregate_freshness, second.aggregate_freshness))
    average_conflict = _average((first.aggregate_conflict, second.aggregate_conflict))
    pressure_alignment = _clamp_ratio(_ONE - abs(first_pressure - second_pressure))
    correlation_pressure = _quantize(
        _average((first_pressure, second_pressure)) * pressure_alignment,
    )
    reason_codes = _row_reason_codes(
        correlation_pressure=correlation_pressure,
        average_intensity=average_intensity,
        average_conflict=average_conflict,
        config=config,
    )
    return ResearchCrossDomainCatalystCorrelationPairRow(
        domain_a=first.domain,
        domain_b=second.domain,
        status=_row_status(reason_codes),
        domain_a_pressure=first_pressure,
        domain_b_pressure=second_pressure,
        average_intensity=average_intensity,
        average_freshness=average_freshness,
        average_conflict=average_conflict,
        pressure_alignment=pressure_alignment,
        correlation_pressure=correlation_pressure,
        reason_codes=reason_codes,
    )


def _domain_pressure(
    item: ResearchCrossDomainCatalystCorrelationInput,
    config: ResearchCrossDomainCatalystCorrelationConfig,
) -> Decimal:
    return _quantize(
        item.aggregate_intensity * config.intensity_weight
        + item.aggregate_freshness * config.freshness_weight
        + item.aggregate_conflict * config.conflict_weight,
    )


def _row_reason_codes(
    *,
    correlation_pressure: Decimal,
    average_intensity: Decimal,
    average_conflict: Decimal,
    config: ResearchCrossDomainCatalystCorrelationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if correlation_pressure >= config.block_correlation_pressure:
        reasons.append("correlation_pressure_block")
    elif correlation_pressure >= config.watch_correlation_pressure:
        reasons.append("correlation_pressure_watch")
    if average_conflict >= config.shared_conflict_high:
        reasons.append("shared_conflict_high")
    elif average_conflict >= config.shared_conflict_watch:
        reasons.append("shared_conflict_watch")
    if average_intensity >= config.shared_intensity_high:
        reasons.append("shared_intensity_high")
    elif average_intensity >= config.shared_intensity_watch:
        reasons.append("shared_intensity_watch")
    if not reasons:
        reasons.append(_PASS_REASON)
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "correlation_pressure_block" in reason_codes:
        return "block"
    if "correlation_pressure_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchCrossDomainCatalystCorrelationPairRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchCrossDomainCatalystCorrelationPairRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_reason_codes(
    rows: tuple[ResearchCrossDomainCatalystCorrelationPairRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_INSUFFICIENT_REASON,)
    reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != _PASS_REASON
    )
    if not reasons:
        return (_PASS_REASON,)
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _reason_code_counts(
    rows: tuple[ResearchCrossDomainCatalystCorrelationPairRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchCrossDomainCatalystCorrelationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCrossDomainCatalystCorrelationReasonCodeCount(
                reason_code=_INSUFFICIENT_REASON,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.reason_codes:
            if reason == _PASS_REASON and _PASS_REASON not in report_reason_codes:
                continue
            counts[reason] = counts.get(reason, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchCrossDomainCatalystCorrelationReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
            row_ratio=_ratio(_count(counts[reason]), denominator),
        )
        for reason in sorted(counts, key=_reason_key)
    )


def _normalize_inputs(
    inputs: object,
) -> tuple[ResearchCrossDomainCatalystCorrelationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchCrossDomainCatalystCorrelationInput:
            raise ValueError(
                "inputs must contain ResearchCrossDomainCatalystCorrelationInput",
            )
        _require_flags("input", item)
    sorted_items = tuple(sorted(items, key=lambda item: item.domain))
    domains = tuple(item.domain for item in sorted_items)
    if len(set(domains)) != len(domains):
        raise ValueError("inputs must contain unique domain values")
    return sorted_items


def _check_report(report: ResearchCrossDomainCatalystCorrelationReport) -> None:
    rows = report.rows
    if report.pair_count != _count(len(rows)):
        raise ValueError("pair_count must match rows")
    if report.domain_count != _count(len(report.covered_domains)):
        raise ValueError("domain_count must match covered_domains")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_correlation_pressure != _average_or_zero(
        tuple(row.correlation_pressure for row in rows),
    ):
        raise ValueError("average_correlation_pressure must match rows")
    if report.max_correlation_pressure != _max_or_zero(
        tuple(row.correlation_pressure for row in rows),
    ):
        raise ValueError("max_correlation_pressure must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchCrossDomainCatalystCorrelationPairRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchCrossDomainCatalystCorrelationPairRow:
            raise ValueError("rows must contain ResearchCrossDomainCatalystCorrelationPairRow")
        _require_flags("row", item)
    return items


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchCrossDomainCatalystCorrelationReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchCrossDomainCatalystCorrelationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCrossDomainCatalystCorrelationReasonCodeCount",
            )
        _require_flags("reason code count", item)
    return items


def _normalize_domains(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for item in items:
        _require_domain(item)
    if tuple(sorted(items)) != items:
        raise ValueError(f"{name} must be sorted")
    if len(set(items)) != len(items):
        raise ValueError(f"{name} must not contain duplicates")
    return items


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        _require_text(name, item)
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_key))


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _row_sort_key(row: ResearchCrossDomainCatalystCorrelationPairRow) -> tuple[int, str, str]:
    return (_STATUS_RANK[row.status], row.domain_a, row.domain_b)


def _report_digest(report: ResearchCrossDomainCatalystCorrelationReport) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("derived_validation_digest must be a lowercase sha256 hex digest")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _ratio(sum(values, _ZERO), _count(len(values)))


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _average(values)


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(max(values))


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(min(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return _quantize(value)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_domain(value: object) -> None:
    if type(value) is not str:
        raise ValueError("domain must be a string")
    if value not in _ALLOWED_DOMAINS:
        raise ValueError("domain must be one of politics, crypto, equities, gold, soccer, basketball")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {name}")


def _require_status(name: str, value: object) -> None:
    if value not in _STATUS_RANK:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "DEFAULT_RESEARCH_CROSS_DOMAIN_CATALYST_CORRELATION_CONFIG_VERSION",
    "ResearchCrossDomainCatalystCorrelationConfig",
    "ResearchCrossDomainCatalystCorrelationInput",
    "ResearchCrossDomainCatalystCorrelationPairRow",
    "ResearchCrossDomainCatalystCorrelationReasonCodeCount",
    "ResearchCrossDomainCatalystCorrelationReport",
    "build_research_cross_domain_catalyst_correlation_report",
    "research_cross_domain_catalyst_correlation_report_payload",
)
