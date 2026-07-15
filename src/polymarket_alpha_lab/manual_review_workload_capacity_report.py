"""Read-only workload capacity report for manual review queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_MANUAL_REVIEW_WORKLOAD_CAPACITY_REPORT_CONFIG_VERSION = (
    "manual-review-workload-capacity-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_REVIEWER_CAPACITY_WINDOW_MINUTES = Decimal("30.000000")
_NEAR_RESOLUTION_SECONDS = Decimal("21600.000000")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "available_reviewer_count",
    "ready_candidate_count",
    "watch_candidate_count",
    "blocked_candidate_count",
    "average_review_minutes",
    "time_to_nearest_resolution_seconds",
    "high_priority_candidate_count",
    "source_freshness_attention_count",
    "capacity_ready",
    "review_capacity_score",
    "estimated_backlog_minutes",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "public_digest",
)
_DECIMAL_PAYLOAD_KEYS = (
    "available_reviewer_count",
    "ready_candidate_count",
    "watch_candidate_count",
    "blocked_candidate_count",
    "average_review_minutes",
    "time_to_nearest_resolution_seconds",
    "high_priority_candidate_count",
    "source_freshness_attention_count",
    "review_capacity_score",
    "estimated_backlog_minutes",
    "ready_ratio",
)
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "execution",
    "network",
    "database",
    "persist",
    "mutation",
    "trade",
    "trading",
    "buy",
    "sell",
    "position",
    "private_key",
    "secret",
    "token",
    "password",
    "api_key",
    "dsn",
    "postgres://",
    "postgresql://",
    "http://",
    "https://",
)

__all__ = (
    "DEFAULT_MANUAL_REVIEW_WORKLOAD_CAPACITY_REPORT_CONFIG_VERSION",
    "ManualReviewWorkloadCapacityInputs",
    "ManualReviewWorkloadCapacityReport",
    "build_manual_review_workload_capacity_report",
    "format_manual_review_workload_capacity_digest",
    "manual_review_workload_capacity_public_payload",
)


@dataclass(frozen=True)
class ManualReviewWorkloadCapacityInputs:
    available_reviewer_count: Decimal
    ready_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_review_minutes: Decimal
    time_to_nearest_resolution_seconds: Decimal
    high_priority_candidate_count: Decimal
    source_freshness_attention_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ManualReviewWorkloadCapacityInputs:
            raise ValueError("inputs must be exactly ManualReviewWorkloadCapacityInputs")
        _normalize_input_decimals(self)
        _require_hard_flags("inputs", self)
        _reject_unsafe_public_payload("inputs", self)


@dataclass(frozen=True)
class ManualReviewWorkloadCapacityReport:
    generated_at: datetime
    config_version: str
    available_reviewer_count: Decimal
    ready_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_review_minutes: Decimal
    time_to_nearest_resolution_seconds: Decimal
    high_priority_candidate_count: Decimal
    source_freshness_attention_count: Decimal
    capacity_ready: bool
    review_capacity_score: Decimal
    estimated_backlog_minutes: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    public_digest: str = ""

    def __post_init__(self) -> None:
        if type(self) is not ManualReviewWorkloadCapacityReport:
            raise ValueError("report must be exactly ManualReviewWorkloadCapacityReport")
        object.__setattr__(self, "generated_at", _require_utc_datetime(self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        _normalize_input_decimals(self)
        object.__setattr__(
            self,
            "review_capacity_score",
            _require_ratio_decimal("review_capacity_score", self.review_capacity_score),
        )
        object.__setattr__(
            self,
            "estimated_backlog_minutes",
            _require_nonnegative_decimal(
                "estimated_backlog_minutes",
                self.estimated_backlog_minutes,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _require_reason_codes("blocked_reason_codes", self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _require_reason_codes("attention_reason_codes", self.attention_reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        digest = self.public_digest or _public_digest_for_report(self)
        if not _DIGEST_RE.fullmatch(digest):
            raise ValueError("public_digest must be sha256-prefixed lowercase hex")
        object.__setattr__(self, "public_digest", digest)
        if self.public_digest != _public_digest_for_report(self):
            raise ValueError("public_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return manual_review_workload_capacity_public_payload(self)

    @property
    def digest(self) -> str:
        return format_manual_review_workload_capacity_digest(self)


def build_manual_review_workload_capacity_report(
    inputs: ManualReviewWorkloadCapacityInputs | None = None,
    *,
    available_reviewer_count: Decimal | None = None,
    ready_candidate_count: Decimal | None = None,
    watch_candidate_count: Decimal | None = None,
    blocked_candidate_count: Decimal | None = None,
    average_review_minutes: Decimal | None = None,
    time_to_nearest_resolution_seconds: Decimal | None = None,
    high_priority_candidate_count: Decimal | None = None,
    source_freshness_attention_count: Decimal | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
    generated_at: datetime | None = None,
    config_version: str = DEFAULT_MANUAL_REVIEW_WORKLOAD_CAPACITY_REPORT_CONFIG_VERSION,
) -> ManualReviewWorkloadCapacityReport:
    if inputs is not None:
        if type(inputs) is not ManualReviewWorkloadCapacityInputs:
            raise ValueError("inputs must be exactly ManualReviewWorkloadCapacityInputs")
        if any(
            value is not None
            for value in (
                available_reviewer_count,
                ready_candidate_count,
                watch_candidate_count,
                blocked_candidate_count,
                average_review_minutes,
                time_to_nearest_resolution_seconds,
                high_priority_candidate_count,
                source_freshness_attention_count,
            )
        ):
            raise ValueError("inputs cannot be combined with explicit metric values")
        available_reviewer_count = inputs.available_reviewer_count
        ready_candidate_count = inputs.ready_candidate_count
        watch_candidate_count = inputs.watch_candidate_count
        blocked_candidate_count = inputs.blocked_candidate_count
        average_review_minutes = inputs.average_review_minutes
        time_to_nearest_resolution_seconds = inputs.time_to_nearest_resolution_seconds
        high_priority_candidate_count = inputs.high_priority_candidate_count
        source_freshness_attention_count = inputs.source_freshness_attention_count
        paper_only = inputs.paper_only
        report_only = inputs.report_only
        readonly = inputs.readonly

    missing = tuple(
        name
        for name, value in (
            ("available_reviewer_count", available_reviewer_count),
            ("ready_candidate_count", ready_candidate_count),
            ("watch_candidate_count", watch_candidate_count),
            ("blocked_candidate_count", blocked_candidate_count),
            ("average_review_minutes", average_review_minutes),
            ("time_to_nearest_resolution_seconds", time_to_nearest_resolution_seconds),
            ("high_priority_candidate_count", high_priority_candidate_count),
            ("source_freshness_attention_count", source_freshness_attention_count),
        )
        if value is None
    )
    if missing:
        raise ValueError(f"missing workload capacity inputs: {', '.join(missing)}")

    normalized = ManualReviewWorkloadCapacityInputs(
        available_reviewer_count=available_reviewer_count,
        ready_candidate_count=ready_candidate_count,
        watch_candidate_count=watch_candidate_count,
        blocked_candidate_count=blocked_candidate_count,
        average_review_minutes=average_review_minutes,
        time_to_nearest_resolution_seconds=time_to_nearest_resolution_seconds,
        high_priority_candidate_count=high_priority_candidate_count,
        source_freshness_attention_count=source_freshness_attention_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    generated = _require_utc_datetime(generated_at or datetime.now(UTC))
    capacity_minutes = (
        normalized.available_reviewer_count * _REVIEWER_CAPACITY_WINDOW_MINUTES
    )
    estimated_backlog_minutes = _quantize(
        normalized.ready_candidate_count * normalized.average_review_minutes,
    )
    if normalized.ready_candidate_count == _ZERO:
        review_capacity_score = _ONE
    else:
        review_capacity_score = _ratio(
            capacity_minutes,
            estimated_backlog_minutes,
            cap_at_one=True,
        )
    total_candidates = (
        normalized.ready_candidate_count
        + normalized.watch_candidate_count
        + normalized.blocked_candidate_count
    )
    ready_ratio = _ratio(normalized.ready_candidate_count, total_candidates, cap_at_one=True)
    blocked_reason_codes = _blocked_reason_codes(
        normalized,
        review_capacity_score=review_capacity_score,
    )
    attention_reason_codes = _attention_reason_codes(normalized)

    return ManualReviewWorkloadCapacityReport(
        generated_at=generated,
        config_version=config_version,
        available_reviewer_count=normalized.available_reviewer_count,
        ready_candidate_count=normalized.ready_candidate_count,
        watch_candidate_count=normalized.watch_candidate_count,
        blocked_candidate_count=normalized.blocked_candidate_count,
        average_review_minutes=normalized.average_review_minutes,
        time_to_nearest_resolution_seconds=normalized.time_to_nearest_resolution_seconds,
        high_priority_candidate_count=normalized.high_priority_candidate_count,
        source_freshness_attention_count=normalized.source_freshness_attention_count,
        capacity_ready=not blocked_reason_codes,
        review_capacity_score=review_capacity_score,
        estimated_backlog_minutes=estimated_backlog_minutes,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=ready_ratio,
        paper_only=normalized.paper_only,
        report_only=normalized.report_only,
        readonly=normalized.readonly,
    )


def manual_review_workload_capacity_public_payload(
    value: ManualReviewWorkloadCapacityReport | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(value, dict):
        payload = dict(value)
        _validate_payload(payload)
        return payload
    if type(value) is not ManualReviewWorkloadCapacityReport:
        raise TypeError("value must be ManualReviewWorkloadCapacityReport or payload dict")
    _require_hard_flags("report", value)
    _reject_unsafe_public_payload("report", value)
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    _validate_payload(payload)
    return payload


def format_manual_review_workload_capacity_digest(
    report: ManualReviewWorkloadCapacityReport,
) -> str:
    if type(report) is not ManualReviewWorkloadCapacityReport:
        raise TypeError("report must be ManualReviewWorkloadCapacityReport")
    return (
        "manual_review_workload_capacity_report("
        f"generated_at={report.generated_at.isoformat()}, "
        f"capacity_ready={str(report.capacity_ready).lower()}, "
        f"score={report.review_capacity_score}, "
        f"ready_ratio={report.ready_ratio}, "
        f"backlog_minutes={report.estimated_backlog_minutes}, "
        f"blocked_reason_codes={','.join(report.blocked_reason_codes) or 'none'}, "
        f"attention_reason_codes={','.join(report.attention_reason_codes) or 'none'}, "
        f"public_digest={report.public_digest})"
    )


def _blocked_reason_codes(
    inputs: ManualReviewWorkloadCapacityInputs,
    *,
    review_capacity_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.available_reviewer_count == _ZERO and inputs.ready_candidate_count > _ZERO:
        reasons.append("no_available_reviewers")
    if review_capacity_score < _ONE:
        reasons.append("review_capacity_score_below_ready")
    return tuple(reasons)


def _attention_reason_codes(inputs: ManualReviewWorkloadCapacityInputs) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.high_priority_candidate_count > _ZERO:
        reasons.append("high_priority_candidates_present")
    if inputs.source_freshness_attention_count > _ZERO:
        reasons.append("source_freshness_attention_present")
    if inputs.time_to_nearest_resolution_seconds < _NEAR_RESOLUTION_SECONDS:
        reasons.append("nearest_resolution_under_review_window")
    if inputs.watch_candidate_count > _ZERO:
        reasons.append("watch_candidates_present")
    if inputs.blocked_candidate_count > _ZERO:
        reasons.append("blocked_candidates_present")
    return tuple(reasons)


def _normalize_input_decimals(value: object) -> None:
    for field_name in (
        "available_reviewer_count",
        "ready_candidate_count",
        "watch_candidate_count",
        "blocked_candidate_count",
        "time_to_nearest_resolution_seconds",
        "high_priority_candidate_count",
        "source_freshness_attention_count",
    ):
        object.__setattr__(
            value,
            field_name,
            _require_nonnegative_decimal(field_name, getattr(value, field_name)),
        )
    object.__setattr__(
        value,
        "average_review_minutes",
        _require_positive_decimal("average_review_minutes", getattr(value, "average_review_minutes")),
    )


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    if type(value) is not Decimal:
        raise TypeError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    number = _require_decimal(name, value)
    if number < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return number


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    number = _require_decimal(name, value)
    if number <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return number


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    number = _require_nonnegative_decimal(name, value)
    if number > _ONE:
        raise ValueError(f"{name} must be no greater than 1.000000")
    return number


def _require_supported_config_version(value: str) -> str:
    if type(value) is not str:
        raise TypeError("config_version must be str")
    if value != DEFAULT_MANUAL_REVIEW_WORKLOAD_CAPACITY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return value


def _require_utc_datetime(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError("generated_at must be datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _require_reason_codes(name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be tuple")
    for code in value:
        if type(code) is not str:
            raise TypeError(f"{name} entries must be str")
        if not code or not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", code):
            raise ValueError(f"{name} entries must be public reason codes")
    return value


def _require_hard_flags(context: str, value: object) -> None:
    for flag_name in _FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{context} {flag_name} must be True")


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    text = json.dumps(_json_ready(value), sort_keys=True).lower()
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in text:
            raise ValueError(
                f"{context} must remain read-only/report-only/paper-only and avoid "
                "live trading/auth/wallet/order execution/database/network fields",
            )


def _ratio(numerator: Decimal, denominator: Decimal, *, cap_at_one: bool) -> Decimal:
    if denominator == _ZERO:
        return _ONE
    with localcontext() as context:
        context.prec = 28
        value = numerator / denominator
    if cap_at_one and value > _ONE:
        value = _ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value


def _payload_without_digest(report: ManualReviewWorkloadCapacityReport) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("public_digest", None)
    return {key: payload[key] for key in _PUBLIC_PAYLOAD_KEYS if key in payload}


def _public_digest_for_report(report: ManualReviewWorkloadCapacityReport) -> str:
    payload = _payload_without_digest(report)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{sha256(blob.encode('utf-8')).hexdigest()}"


def _validate_payload(payload: dict[str, Any]) -> None:
    if tuple(payload.keys()) != _PUBLIC_PAYLOAD_KEYS:
        raise ValueError("public_payload keys must match the workload capacity schema")
    for key in _DECIMAL_PAYLOAD_KEYS:
        if type(payload[key]) is not str:
            raise TypeError(f"{key} must be rendered as a string")
        _require_decimal(key, Decimal(payload[key]))
    for flag_name in _FLAG_NAMES:
        if payload[flag_name] is not True:
            raise ValueError(f"public_payload {flag_name} must be True")
    if type(payload["capacity_ready"]) is not bool:
        raise TypeError("capacity_ready must be bool")
    for key in ("blocked_reason_codes", "attention_reason_codes"):
        if type(payload[key]) is not list:
            raise TypeError(f"{key} must be list")
        _require_reason_codes(key, tuple(payload[key]))
    if not _DIGEST_RE.fullmatch(payload["public_digest"]):
        raise ValueError("public_digest must be sha256-prefixed lowercase hex")
    digest_payload = dict(payload)
    supplied_digest = digest_payload.pop("public_digest")
    blob = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    expected_digest = f"sha256:{sha256(blob.encode('utf-8')).hexdigest()}"
    if supplied_digest != expected_digest:
        raise ValueError("public_digest must match report payload")
    _reject_unsafe_public_payload("public_payload", payload)
