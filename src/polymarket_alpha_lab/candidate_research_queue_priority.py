"""Pure manual research queue priority aggregation for sanitized summaries."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any, Iterable


CONFIG_VERSION = "candidate-research-queue-priority-v0"
PASS_WATCH_BLOCK_STATUSES = frozenset(("pass", "watch", "block"))
PRIORITY_TIERS = frozenset(("low", "watch", "high"))
DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "config_version",
        "summary_count",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "top_priority_tier",
        "max_research_priority_score",
        "reason_codes",
        "research_priority_explanation",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "summary_ref",
        "status",
        "priority_tier",
        "research_priority_score",
        "score",
        "risk_score",
        "uncertainty_score",
        "impact_score",
        "reason_codes",
    ),
)
_DECIMAL_REPORT_FIELDS = frozenset(
    (
        "summary_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_research_priority_score",
    ),
)
_DECIMAL_ROW_FIELDS = frozenset(
    (
        "research_priority_score",
        "score",
        "risk_score",
        "uncertainty_score",
        "impact_score",
    ),
)
_FIELD_DENY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "bu" + "y",
        "se" + "ll",
        "rec" + "ommend",
    ),
)
_VALUE_DENY_FRAGMENTS = frozenset(
    (
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table:",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "bu" + "y",
        "se" + "ll",
        "rec" + "ommend",
    ),
)
_RESEARCH_PRIORITY_EXPLANATION = (
    "block summaries are reviewed first for manual research only",
    "watch summaries are sorted by risk uncertainty impact and score",
    "pass summaries remain available after higher priority review",
)


@dataclass(frozen=True)
class CandidateResearchQueuePriorityConfig:
    config_version: str
    watch_priority_threshold: Decimal
    high_priority_threshold: Decimal
    block_risk_threshold: Decimal

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_priority_threshold",
            "high_priority_threshold",
            "block_risk_threshold",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        if self.watch_priority_threshold > self.high_priority_threshold:
            raise ValueError("watch_priority_threshold must be <= high_priority_threshold")


@dataclass(frozen=True)
class CandidateResearchQueuePrioritySummary:
    summary_ref: str
    status: str
    score: Decimal
    risk_score: Decimal
    uncertainty_score: Decimal
    impact_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("summary", self)
        _require_public_string("summary_ref", self.summary_ref)
        _require_status("status", self.status)
        for field_name in (
            "score",
            "risk_score",
            "uncertainty_score",
            "impact_score",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_reason_codes("reason_codes", self.reason_codes)
        _reject_unsafe_public_surface("summary", self)


@dataclass(frozen=True)
class CandidateResearchQueuePriorityRow:
    summary_ref: str
    status: str
    priority_tier: str
    research_priority_score: Decimal
    score: Decimal
    risk_score: Decimal
    uncertainty_score: Decimal
    impact_score: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_public_string("summary_ref", self.summary_ref)
        _require_status("status", self.status)
        _require_member("priority_tier", self.priority_tier, PRIORITY_TIERS)
        for field_name in _DECIMAL_ROW_FIELDS:
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_reason_codes("reason_codes", self.reason_codes)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class CandidateResearchQueuePriorityReport:
    config_version: str
    summary_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    top_priority_tier: str
    max_research_priority_score: Decimal
    reason_codes: tuple[str, ...]
    research_priority_explanation: tuple[str, ...]
    rows: tuple[CandidateResearchQueuePriorityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("report", self)
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in _DECIMAL_REPORT_FIELDS:
            _require_non_negative_decimal(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        _require_member("top_priority_tier", self.top_priority_tier, PRIORITY_TIERS)
        _require_reason_codes("reason_codes", self.reason_codes)
        _require_public_string_tuple(
            "research_priority_explanation",
            self.research_priority_explanation,
        )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not CandidateResearchQueuePriorityRow:
                raise ValueError("rows must contain CandidateResearchQueuePriorityRow")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report values")


def build_candidate_research_queue_priority(
    summaries: Iterable[CandidateResearchQueuePrioritySummary],
    *,
    config: CandidateResearchQueuePriorityConfig,
) -> CandidateResearchQueuePriorityReport:
    if type(config) is not CandidateResearchQueuePriorityConfig:
        raise ValueError("config must be a CandidateResearchQueuePriorityConfig")
    normalized = _normalize_summaries(summaries)
    rows = tuple(_row_from_summary(summary, config) for summary in normalized)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))

    pass_count = _count_decimal(row.status == "pass" for row in sorted_rows)
    watch_count = _count_decimal(row.status == "watch" for row in sorted_rows)
    block_count = _count_decimal(row.status == "block" for row in sorted_rows)
    max_score = max((row.research_priority_score for row in sorted_rows), default=ZERO)
    top_priority_tier = _tier_for_priority(
        max_score,
        watch_threshold=config.watch_priority_threshold,
        high_threshold=config.high_priority_threshold,
    )
    report_status = _report_status(block_count=block_count, watch_count=watch_count)
    reason_codes = _report_reason_codes(sorted_rows, report_status, top_priority_tier)

    values = {
        "config_version": config.config_version,
        "summary_count": _count_decimal(True for _ in sorted_rows),
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "status": report_status,
        "top_priority_tier": top_priority_tier,
        "max_research_priority_score": max_score,
        "reason_codes": reason_codes,
        "research_priority_explanation": _RESEARCH_PRIORITY_EXPLANATION,
        "rows": sorted_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _digest_payload(_json_ready(values))
    return CandidateResearchQueuePriorityReport(
        **values,
        derived_validation_digest=digest,
    )


def candidate_research_queue_priority_payload(
    report: CandidateResearchQueuePriorityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is CandidateResearchQueuePriorityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a CandidateResearchQueuePriorityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
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


def _normalize_summaries(
    summaries: Iterable[CandidateResearchQueuePrioritySummary],
) -> tuple[CandidateResearchQueuePrioritySummary, ...]:
    if isinstance(summaries, (str, bytes)) or not isinstance(summaries, Iterable):
        raise ValueError("summaries must be an iterable")
    normalized: list[CandidateResearchQueuePrioritySummary] = []
    for summary in summaries:
        if type(summary) is not CandidateResearchQueuePrioritySummary:
            raise ValueError("summaries must contain CandidateResearchQueuePrioritySummary")
        _require_hard_flags("summary", summary)
        _reject_unsafe_public_surface("summary", summary)
        normalized.append(summary)
    return tuple(sorted(normalized, key=lambda item: item.summary_ref))


def _row_from_summary(
    summary: CandidateResearchQueuePrioritySummary,
    config: CandidateResearchQueuePriorityConfig,
) -> CandidateResearchQueuePriorityRow:
    risk_blocked = summary.risk_score >= config.block_risk_threshold
    row_status = "block" if risk_blocked else summary.status
    priority_score = _priority_score(summary, row_status)
    priority_tier = _tier_for_priority(
        priority_score,
        watch_threshold=config.watch_priority_threshold,
        high_threshold=config.high_priority_threshold,
    )
    reason_codes = _row_reason_codes(
        summary.reason_codes,
        row_status=row_status,
        priority_tier=priority_tier,
        risk_blocked=risk_blocked,
    )
    return CandidateResearchQueuePriorityRow(
        summary_ref=summary.summary_ref,
        status=row_status,
        priority_tier=priority_tier,
        research_priority_score=priority_score,
        score=summary.score,
        risk_score=summary.risk_score,
        uncertainty_score=summary.uncertainty_score,
        impact_score=summary.impact_score,
        reason_codes=reason_codes,
    )


def _priority_score(
    summary: CandidateResearchQueuePrioritySummary,
    row_status: str,
) -> Decimal:
    if row_status == "pass":
        value = (
            summary.score * Decimal("0.100000")
            + summary.risk_score * Decimal("0.400000")
            + summary.uncertainty_score * Decimal("0.300000")
            + summary.impact_score * Decimal("0.250000")
        )
        return _quantize_decimal(value)
    value = (
        summary.score
        + summary.uncertainty_score * Decimal("0.100000")
        + summary.impact_score * Decimal("0.050000")
    )
    if row_status == "block":
        risk_weighted = (
            summary.score * Decimal("0.500000")
            + summary.risk_score * Decimal("0.400000")
            + summary.uncertainty_score * Decimal("0.200000")
            + summary.impact_score * Decimal("0.100000")
        )
        value = max(value, risk_weighted)
    return _quantize_decimal(min(value, ONE))


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    row_status: str,
    priority_tier: str,
    risk_blocked: bool,
) -> tuple[str, ...]:
    tier_code = f"{priority_tier}_manual_research_priority"
    if risk_blocked:
        return _unique_reason_codes(
            (*input_reason_codes, tier_code, "risk_limit_block"),
        )
    reason_codes = (tier_code, *input_reason_codes)
    if row_status == "watch":
        reason_codes = (*reason_codes, "watch_summary")
    return _unique_reason_codes(reason_codes)


def _report_status(*, block_count: Decimal, watch_count: Decimal) -> str:
    if block_count > ZERO:
        return "block"
    if watch_count > ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateResearchQueuePriorityRow, ...],
    report_status: str,
    top_priority_tier: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if report_status == "block":
        reason_codes.append("block_summary_present")
    if top_priority_tier == "high":
        reason_codes.append("high_manual_research_priority_present")
    if any("risk_limit_block" in row.reason_codes for row in rows):
        reason_codes.append("risk_limit_block_present")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("watch_summary_present")
    if not reason_codes:
        reason_codes.append("queue_priority_clear")
    return tuple(reason_codes)


def _row_sort_key(row: CandidateResearchQueuePriorityRow) -> tuple[int, Decimal, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}[row.status]
    return (status_rank, -row.research_priority_score, row.summary_ref)


def _tier_for_priority(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    high_threshold: Decimal,
) -> str:
    if value >= high_threshold:
        return "high"
    if value >= watch_threshold:
        return "watch"
    return "low"


def _count_decimal(values: Iterable[bool]) -> Decimal:
    return Decimal(sum(1 for value in values if value)).quantize(DECIMAL_QUANT)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_non_negative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if field_name.endswith("summary_ref"):
        normalized_value = value.lower()
        if normalized_value.startswith(("candidate-", "candidate_", "market-", "market_")):
            raise ValueError(f"unsafe public value in {field_name}")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_public_string(field_name, item)
    return value


def _require_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_public_string(field_name, item)
    if tuple(dict.fromkeys(value)) != value:
        raise ValueError(f"{field_name} must be unique")
    return value


def _unique_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(reason_codes))


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, PASS_WATCH_BLOCK_STATUSES)


def _require_member(field_name: str, value: object, allowed_values: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


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
        raise ValueError("JSON Decimal value must be a Decimal")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str) or type(value) is bool:
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


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_public_string("config_version", payload["config_version"])
    if payload["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in _DECIMAL_REPORT_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _require_member("top_priority_tier", payload["top_priority_tier"], PRIORITY_TIERS)
    _validate_public_string_list("reason_codes", payload["reason_codes"])
    _validate_public_string_list(
        "research_priority_explanation",
        payload["research_priority_explanation"],
    )
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(payload["rows"]):
        _validate_public_row_payload(f"rows[{index}]", row)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if payload["derived_validation_digest"] != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_row_payload(label: str, row: object) -> None:
    if type(row) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _reject_unknown_keys(label, row, _ROW_PAYLOAD_KEYS)
    _require_public_string(f"{label}.summary_ref", row["summary_ref"])
    _require_status(f"{label}.status", row["status"])
    _require_member(f"{label}.priority_tier", row["priority_tier"], PRIORITY_TIERS)
    for field_name in _DECIMAL_ROW_FIELDS:
        _require_decimal_string(f"{label}.{field_name}", row[field_name])
    _validate_public_string_list(f"{label}.reason_codes", row["reason_codes"])


def _validate_public_string_list(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_public_string(field_name, item)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite() or decimal_value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-place Decimal-derived string")
    return decimal_value


def _reject_unknown_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    for key in payload:
        if key not in allowed_keys:
            raise ValueError(f"unknown public field in {label}: {key}")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in _FIELD_DENY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in _VALUE_DENY_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _report_derived_validation_digest(
    report: CandidateResearchQueuePriorityReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


__all__ = (
    "CONFIG_VERSION",
    "CandidateResearchQueuePriorityConfig",
    "CandidateResearchQueuePriorityReport",
    "CandidateResearchQueuePriorityRow",
    "CandidateResearchQueuePrioritySummary",
    "PASS_WATCH_BLOCK_STATUSES",
    "build_candidate_research_queue_priority",
    "candidate_research_queue_priority_payload",
)
