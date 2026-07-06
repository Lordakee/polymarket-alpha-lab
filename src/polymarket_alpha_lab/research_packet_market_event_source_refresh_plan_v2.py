from __future__ import annotations

import hashlib as _hashlib
import json as _json
from dataclasses import asdict as _asdict
from dataclasses import dataclass as _dataclass
from dataclasses import is_dataclass as _is_dataclass
from datetime import UTC as _UTC
from datetime import datetime as _datetime
from decimal import Decimal as _Decimal
from decimal import InvalidOperation as _InvalidOperation
from typing import Any as _Any


CONFIG_VERSION = "research-packet-market-event-source-refresh-plan-v2"
REQUIRED_SOURCE_FAMILIES = (
    "official_calendar",
    "resolution_rules",
    "news_context",
    "venue_status",
    "community_signal",
)

_QUANT = _Decimal("0.000001")
_ZERO = _Decimal("0.000000")
_ONE = _Decimal("1.000000")
_STALE_HOURS = _Decimal("72.000000")
_CRITICAL_STALE_HOURS = _Decimal("168.000000")
_LOW_CONFIDENCE = _Decimal("0.500000")
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@_dataclass(frozen=True)
class MarketEventSourceRefreshInput:
    event_slug: str
    source_family: str
    source_label: str
    source_age_hours: _Decimal
    confidence_score: _Decimal
    has_primary_reference: bool
    note: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("source input", self)
        _set_decimal(self, "source_age_hours", _normalize_decimal("source_age_hours", self.source_age_hours))
        _set_decimal(self, "confidence_score", _normalize_probability("confidence_score", self.confidence_score))
        if self.source_age_hours < _ZERO:
            raise ValueError("source_age_hours must not be negative")
        _require_known_family(self.source_family)
        _reject_unsafe_public_payload("source input", self)


@_dataclass(frozen=True)
class MarketEventSourceRefreshPlanRow:
    refresh_rank: _Decimal
    event_slug: str
    source_family: str
    source_label: str
    source_age_hours: _Decimal
    confidence_score: _Decimal
    staleness_score: _Decimal
    refresh_priority: str
    has_primary_reference: bool
    reason_codes: tuple[str, ...]
    note: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("plan row", self)
        _set_decimal(self, "refresh_rank", _normalize_decimal("refresh_rank", self.refresh_rank))
        _set_decimal(self, "source_age_hours", _normalize_decimal("source_age_hours", self.source_age_hours))
        _set_decimal(self, "confidence_score", _normalize_probability("confidence_score", self.confidence_score))
        _set_decimal(self, "staleness_score", _normalize_probability("staleness_score", self.staleness_score))
        _require_known_family(self.source_family)
        if type(self.reason_codes) is not tuple:
            object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        _reject_unsafe_public_payload("plan row", self)


@_dataclass(frozen=True)
class MarketEventSourceFamilyCoverageSummary:
    source_family: str
    source_count: _Decimal
    stale_source_count: _Decimal
    max_source_age_hours: _Decimal
    average_confidence_score: _Decimal
    coverage_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("family summary", self)
        _require_known_family(self.source_family)
        _set_decimal(self, "source_count", _normalize_decimal("source_count", self.source_count))
        _set_decimal(self, "stale_source_count", _normalize_decimal("stale_source_count", self.stale_source_count))
        _set_decimal(self, "max_source_age_hours", _normalize_decimal("max_source_age_hours", self.max_source_age_hours))
        _set_decimal(
            self,
            "average_confidence_score",
            _normalize_probability("average_confidence_score", self.average_confidence_score),
        )
        if self.coverage_status not in {"covered", "missing"}:
            raise ValueError("coverage_status must be covered or missing")
        if type(self.reason_codes) is not tuple:
            object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        _reject_unsafe_public_payload("family summary", self)


@_dataclass(frozen=True)
class ResearchPacketMarketEventSourceRefreshPlanV2Report:
    generated_at: _datetime
    config_version: str
    reviewed_source_count: _Decimal
    stale_source_count: _Decimal
    high_refresh_priority_count: _Decimal
    source_family_count: _Decimal
    coverage_status: str
    rows: tuple[MarketEventSourceRefreshPlanRow, ...]
    family_summaries: tuple[MarketEventSourceFamilyCoverageSummary, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __post_init__(self) -> None:
        _require_hard_flags("report", self)
        _require_datetime("generated_at", self.generated_at)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version is not supported")
        for field_name in (
            "reviewed_source_count",
            "stale_source_count",
            "high_refresh_priority_count",
            "source_family_count",
        ):
            _set_decimal(self, field_name, _normalize_decimal(field_name, getattr(self, field_name)))
        if self.coverage_status not in {"coverage_complete", "coverage_gap"}:
            raise ValueError("coverage_status must be coverage_complete or coverage_gap")
        if type(self.rows) is not tuple:
            object.__setattr__(self, "rows", tuple(self.rows))
        if type(self.family_summaries) is not tuple:
            object.__setattr__(self, "family_summaries", tuple(self.family_summaries))
        if type(self.reason_codes) is not tuple:
            object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        _reject_unsafe_public_payload("report", self)
        expected_digest = _derived_validation_digest(_json_ready_without_digest(self))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)


def build_research_packet_market_event_source_refresh_plan_v2(
    *,
    sources: tuple[MarketEventSourceRefreshInput, ...],
    generated_at: _datetime,
) -> ResearchPacketMarketEventSourceRefreshPlanV2Report:
    _require_datetime("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    ranked_rows = _rank_rows(normalized_sources)
    family_summaries = _family_summaries(ranked_rows)
    stale_source_count = _decimal_count(
        row for row in ranked_rows if "stale_source_escalation" in row.reason_codes
    )
    high_refresh_priority_count = _decimal_count(
        row for row in ranked_rows if row.refresh_priority in {"urgent_refresh", "high_refresh"}
    )
    covered_family_count = _decimal_count(
        summary for summary in family_summaries if summary.coverage_status == "covered"
    )
    coverage_status = (
        "coverage_complete"
        if covered_family_count == _decimal_count(REQUIRED_SOURCE_FAMILIES)
        else "coverage_gap"
    )
    reason_codes = _report_reason_codes(
        coverage_status=coverage_status,
        stale_source_count=stale_source_count,
        high_refresh_priority_count=high_refresh_priority_count,
    )
    return ResearchPacketMarketEventSourceRefreshPlanV2Report(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        reviewed_source_count=_decimal_count(ranked_rows),
        stale_source_count=stale_source_count,
        high_refresh_priority_count=high_refresh_priority_count,
        source_family_count=covered_family_count,
        coverage_status=coverage_status,
        rows=ranked_rows,
        family_summaries=family_summaries,
        reason_codes=reason_codes,
    )


def research_packet_market_event_source_refresh_plan_v2_payload(
    report: ResearchPacketMarketEventSourceRefreshPlanV2Report | dict[str, _Any],
) -> dict[str, _Any]:
    if type(report) is ResearchPacketMarketEventSourceRefreshPlanV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchPacketMarketEventSourceRefreshPlanV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


@_dataclass(frozen=True)
class _DictFlags:
    value: dict[str, _Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_sources(
    sources: tuple[MarketEventSourceRefreshInput, ...],
) -> tuple[MarketEventSourceRefreshInput, ...]:
    if type(sources) is not tuple:
        raise ValueError("sources must be a tuple")
    normalized: list[MarketEventSourceRefreshInput] = []
    for source in sources:
        if type(source) is not MarketEventSourceRefreshInput:
            raise ValueError("sources must contain MarketEventSourceRefreshInput values")
        normalized.append(source)
    return tuple(normalized)


def _rank_rows(
    sources: tuple[MarketEventSourceRefreshInput, ...],
) -> tuple[MarketEventSourceRefreshPlanRow, ...]:
    unranked = [_unranked_row(source) for source in sources]
    sorted_rows = sorted(
        unranked,
        key=lambda item: (
            _priority_weight(item["refresh_priority"]),
            item["refresh_score"],
            item["source_age_hours"],
            item["source_family"],
            item["source_label"],
        ),
        reverse=True,
    )
    rows: list[MarketEventSourceRefreshPlanRow] = []
    for index, item in enumerate(sorted_rows, start=1):
        rows.append(
            MarketEventSourceRefreshPlanRow(
                refresh_rank=_decimal_count(range(index)),
                event_slug=item["event_slug"],
                source_family=item["source_family"],
                source_label=item["source_label"],
                source_age_hours=item["source_age_hours"],
                confidence_score=item["confidence_score"],
                staleness_score=item["staleness_score"],
                refresh_priority=item["refresh_priority"],
                has_primary_reference=item["has_primary_reference"],
                reason_codes=item["reason_codes"],
                note=item["note"],
            ),
        )
    return tuple(rows)


def _unranked_row(source: MarketEventSourceRefreshInput) -> dict[str, _Any]:
    staleness_score = _ratio_capped(source.source_age_hours, _STALE_HOURS)
    confidence_gap = _ONE - source.confidence_score
    reasons: list[str] = []
    if source.source_age_hours >= _STALE_HOURS:
        reasons.append("stale_source_escalation")
    if source.source_age_hours >= _CRITICAL_STALE_HOURS:
        reasons.append("critical_source_refresh")
    if source.confidence_score <= _LOW_CONFIDENCE:
        reasons.append("low_confidence_refresh")
    if not source.has_primary_reference:
        reasons.append("missing_primary_reference")

    if source.source_age_hours >= _CRITICAL_STALE_HOURS:
        refresh_priority = "urgent_refresh"
    elif source.source_age_hours >= _STALE_HOURS:
        refresh_priority = "high_refresh"
    elif source.confidence_score <= _LOW_CONFIDENCE or not source.has_primary_reference:
        refresh_priority = "high_refresh"
    elif source.source_age_hours >= _Decimal("24.000000"):
        refresh_priority = "medium_refresh"
    else:
        refresh_priority = "low_watch"
        reasons.append("fresh_source_watch")

    refresh_score = (staleness_score + confidence_gap).quantize(_QUANT)
    return {
        "event_slug": source.event_slug,
        "source_family": source.source_family,
        "source_label": source.source_label,
        "source_age_hours": source.source_age_hours,
        "confidence_score": source.confidence_score,
        "staleness_score": staleness_score,
        "refresh_priority": refresh_priority,
        "refresh_score": refresh_score,
        "has_primary_reference": source.has_primary_reference,
        "reason_codes": tuple(reasons),
        "note": source.note,
    }


def _family_summaries(
    rows: tuple[MarketEventSourceRefreshPlanRow, ...],
) -> tuple[MarketEventSourceFamilyCoverageSummary, ...]:
    summaries: list[MarketEventSourceFamilyCoverageSummary] = []
    for source_family in REQUIRED_SOURCE_FAMILIES:
        family_rows = tuple(row for row in rows if row.source_family == source_family)
        if family_rows:
            stale_count = _decimal_count(
                row for row in family_rows if "stale_source_escalation" in row.reason_codes
            )
            max_age = max(row.source_age_hours for row in family_rows)
            average_confidence = _average(row.confidence_score for row in family_rows)
            summaries.append(
                MarketEventSourceFamilyCoverageSummary(
                    source_family=source_family,
                    source_count=_decimal_count(family_rows),
                    stale_source_count=stale_count,
                    max_source_age_hours=max_age,
                    average_confidence_score=average_confidence,
                    coverage_status="covered",
                    reason_codes=("family_covered",),
                ),
            )
        else:
            summaries.append(
                MarketEventSourceFamilyCoverageSummary(
                    source_family=source_family,
                    source_count=_ZERO,
                    stale_source_count=_ZERO,
                    max_source_age_hours=_ZERO,
                    average_confidence_score=_ZERO,
                    coverage_status="missing",
                    reason_codes=("family_missing",),
                ),
            )
    return tuple(summaries)


def _report_reason_codes(
    *,
    coverage_status: str,
    stale_source_count: _Decimal,
    high_refresh_priority_count: _Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if coverage_status == "coverage_gap":
        reasons.append("coverage_gap")
    if stale_source_count > _ZERO:
        reasons.append("stale_source_escalation")
    if high_refresh_priority_count > _ZERO:
        reasons.append("refresh_priority_review")
    if not reasons:
        reasons.append("source_refresh_current")
    return tuple(reasons)


def _validate_report_consistency(
    report: ResearchPacketMarketEventSourceRefreshPlanV2Report,
) -> None:
    if report.reviewed_source_count != _decimal_count(report.rows):
        raise ValueError("reviewed_source_count does not match rows")
    stale_count = _decimal_count(
        row for row in report.rows if "stale_source_escalation" in row.reason_codes
    )
    if report.stale_source_count != stale_count:
        raise ValueError("stale_source_count does not match rows")
    high_count = _decimal_count(
        row for row in report.rows if row.refresh_priority in {"urgent_refresh", "high_refresh"}
    )
    if report.high_refresh_priority_count != high_count:
        raise ValueError("high_refresh_priority_count does not match rows")
    covered_family_count = _decimal_count(
        summary
        for summary in report.family_summaries
        if summary.coverage_status == "covered"
    )
    if report.source_family_count != covered_family_count:
        raise ValueError("source_family_count does not match family summaries")
    expected_coverage = (
        "coverage_complete"
        if covered_family_count == _decimal_count(REQUIRED_SOURCE_FAMILIES)
        else "coverage_gap"
    )
    if report.coverage_status != expected_coverage:
        raise ValueError("coverage_status does not match family summaries")


def _validate_payload_digest(payload: dict[str, _Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    expected = _derived_validation_digest(
        {key: value for key, value in payload.items() if key != "derived_validation_digest"},
    )
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _json_ready_without_digest(
    report: ResearchPacketMarketEventSourceRefreshPlanV2Report,
) -> dict[str, _Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> object:
    if isinstance(value, _Decimal):
        if type(value) is not _Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(_QUANT))
    if isinstance(value, _datetime):
        _require_datetime("JSON datetime value", value)
        return value.astimezone(_UTC).isoformat()
    if _is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, _Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _derived_validation_digest(payload_without_digest: dict[str, _Any]) -> str:
    canonical_payload = _json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if _is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _asdict(value), path)
        return
    if isinstance(value, _Decimal):
        if type(value) is not _Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, _datetime):
        _require_datetime(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is str:
        lowered = value.lower()
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe value")
        if "://" in lowered or "?" in lowered:
            raise ValueError(f"{current_path} has unsafe value")
        if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"{current_path} has unsafe value")
        return
    if type(value) is tuple or type(value) is list:
        for index, item in enumerate(value):
            nested_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is dict:
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(term in lowered_key for term in _UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"{key} has unsafe field")
            nested_path = key if not path else f"{path}.{key}"
            if key in _FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_known_family(source_family: str) -> None:
    if type(source_family) is not str:
        raise ValueError("source_family must be a string")
    if source_family not in REQUIRED_SOURCE_FAMILIES:
        raise ValueError("source_family is not supported")


def _require_datetime(field_name: str, value: object) -> None:
    if type(value) is not _datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _normalize_decimal(field_name: str, value: object) -> _Decimal:
    if type(value) is not _Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(_QUANT)
    except _InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_probability(field_name: str, value: object) -> _Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _set_decimal(target: object, field_name: str, value: _Decimal) -> None:
    if getattr(target, field_name) != value:
        object.__setattr__(target, field_name, value)


def _decimal_count(values: object) -> _Decimal:
    return _Decimal(len(tuple(values))).quantize(_QUANT)


def _average(values: object) -> _Decimal:
    decimals = tuple(values)
    if not decimals:
        return _ZERO
    return (sum(decimals, _ZERO) / _Decimal(len(decimals))).quantize(_QUANT)


def _ratio_capped(numerator: _Decimal, denominator: _Decimal) -> _Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    ratio = (numerator / denominator).quantize(_QUANT)
    if ratio > _ONE:
        return _ONE
    if ratio < _ZERO:
        return _ZERO
    return ratio


def _priority_weight(refresh_priority: str) -> _Decimal:
    if refresh_priority == "urgent_refresh":
        return _Decimal("4.000000")
    if refresh_priority == "high_refresh":
        return _Decimal("3.000000")
    if refresh_priority == "medium_refresh":
        return _Decimal("2.000000")
    if refresh_priority == "low_watch":
        return _Decimal("1.000000")
    raise ValueError("refresh_priority is not supported")
