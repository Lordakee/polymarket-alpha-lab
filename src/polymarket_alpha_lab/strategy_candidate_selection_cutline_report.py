"""Read-only cutline report for batch strategy candidate selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_SELECTION_CUTLINE_REPORT_CONFIG_VERSION = (
    "strategy-candidate-selection-cutline-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HALF = Decimal("0.500000")
_SELECT_MIN_QUALITY = Decimal("0.800000")
_ATTENTION_MIN_QUALITY = Decimal("0.600000")
_SELECT_MIN_EDGE = Decimal("0.070000")
_ATTENTION_MIN_EDGE = Decimal("0.030000")
_SELECT_MIN_SOURCE_RELIABILITY = Decimal("0.750000")
_ATTENTION_MIN_SOURCE_RELIABILITY = Decimal("0.600000")
_SELECT_MIN_MEMORY_QUALITY = Decimal("0.700000")
_ATTENTION_MIN_MEMORY_QUALITY = Decimal("0.600000")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_READY_GATE_NAMES = (
    "liquidity_exit_ready",
    "operator_safety_ready",
    "manual_review_capacity_ready",
)
_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "quality_index_score",
    "edge_to_threshold_probability",
    "source_reliability_score",
    "memory_quality_score",
    "liquidity_exit_ready",
    "operator_safety_ready",
    "manual_review_capacity_ready",
    "selection_cutline_ready",
    "cutline_band",
    "selected_candidate_count",
    "deferred_candidate_count",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "public_digest",
)
_DECIMAL_PAYLOAD_KEYS = (
    "candidate_count",
    "quality_index_score",
    "edge_to_threshold_probability",
    "source_reliability_score",
    "memory_quality_score",
    "selected_candidate_count",
    "deferred_candidate_count",
    "ready_ratio",
)
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "account",
    "broker",
    "order",
    "submit",
    "cancel",
    "sign",
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
    "DEFAULT_STRATEGY_CANDIDATE_SELECTION_CUTLINE_REPORT_CONFIG_VERSION",
    "StrategyCandidateSelectionCutlineInputs",
    "StrategyCandidateSelectionCutlineReport",
    "build_strategy_candidate_selection_cutline_report",
    "format_strategy_candidate_selection_cutline_digest",
    "strategy_candidate_selection_cutline_public_payload",
)


@dataclass(frozen=True)
class StrategyCandidateSelectionCutlineInputs:
    candidate_count: Decimal
    quality_index_score: Decimal
    edge_to_threshold_probability: Decimal
    source_reliability_score: Decimal
    memory_quality_score: Decimal
    liquidity_exit_ready: bool
    operator_safety_ready: bool
    manual_review_capacity_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSelectionCutlineInputs:
            raise ValueError("inputs must be exactly StrategyCandidateSelectionCutlineInputs")
        _normalize_input_values(self)
        _require_hard_flags("inputs", self)
        _reject_unsafe_public_payload("inputs", self)


@dataclass(frozen=True)
class StrategyCandidateSelectionCutlineReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    quality_index_score: Decimal
    edge_to_threshold_probability: Decimal
    source_reliability_score: Decimal
    memory_quality_score: Decimal
    liquidity_exit_ready: bool
    operator_safety_ready: bool
    manual_review_capacity_ready: bool
    selection_cutline_ready: bool
    cutline_band: str
    selected_candidate_count: Decimal
    deferred_candidate_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    public_digest: str = ""

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSelectionCutlineReport:
            raise ValueError("report must be exactly StrategyCandidateSelectionCutlineReport")
        object.__setattr__(self, "generated_at", _require_utc_datetime(self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        _normalize_input_values(self)
        for field_name in (
            "selection_cutline_ready",
            "liquidity_exit_ready",
            "operator_safety_ready",
            "manual_review_capacity_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "cutline_band",
            _require_cutline_band(self.cutline_band),
        )
        object.__setattr__(
            self,
            "selected_candidate_count",
            _require_nonnegative_decimal(
                "selected_candidate_count",
                self.selected_candidate_count,
            ),
        )
        object.__setattr__(
            self,
            "deferred_candidate_count",
            _require_nonnegative_decimal(
                "deferred_candidate_count",
                self.deferred_candidate_count,
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
        _validate_report_consistency(self)
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
        return strategy_candidate_selection_cutline_public_payload(self)

    @property
    def digest(self) -> str:
        return format_strategy_candidate_selection_cutline_digest(self)


def build_strategy_candidate_selection_cutline_report(
    inputs: StrategyCandidateSelectionCutlineInputs | None = None,
    *,
    candidate_count: Decimal | None = None,
    quality_index_score: Decimal | None = None,
    edge_to_threshold_probability: Decimal | None = None,
    source_reliability_score: Decimal | None = None,
    memory_quality_score: Decimal | None = None,
    liquidity_exit_ready: bool | None = None,
    operator_safety_ready: bool | None = None,
    manual_review_capacity_ready: bool | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
    generated_at: datetime | None = None,
    config_version: str = DEFAULT_STRATEGY_CANDIDATE_SELECTION_CUTLINE_REPORT_CONFIG_VERSION,
) -> StrategyCandidateSelectionCutlineReport:
    if inputs is not None:
        if type(inputs) is not StrategyCandidateSelectionCutlineInputs:
            raise ValueError("inputs must be exactly StrategyCandidateSelectionCutlineInputs")
        if any(
            value is not None
            for value in (
                candidate_count,
                quality_index_score,
                edge_to_threshold_probability,
                source_reliability_score,
                memory_quality_score,
                liquidity_exit_ready,
                operator_safety_ready,
                manual_review_capacity_ready,
            )
        ):
            raise ValueError("inputs cannot be combined with explicit cutline values")
        candidate_count = inputs.candidate_count
        quality_index_score = inputs.quality_index_score
        edge_to_threshold_probability = inputs.edge_to_threshold_probability
        source_reliability_score = inputs.source_reliability_score
        memory_quality_score = inputs.memory_quality_score
        liquidity_exit_ready = inputs.liquidity_exit_ready
        operator_safety_ready = inputs.operator_safety_ready
        manual_review_capacity_ready = inputs.manual_review_capacity_ready
        paper_only = inputs.paper_only
        report_only = inputs.report_only
        readonly = inputs.readonly

    missing = tuple(
        name
        for name, value in (
            ("candidate_count", candidate_count),
            ("quality_index_score", quality_index_score),
            ("edge_to_threshold_probability", edge_to_threshold_probability),
            ("source_reliability_score", source_reliability_score),
            ("memory_quality_score", memory_quality_score),
            ("liquidity_exit_ready", liquidity_exit_ready),
            ("operator_safety_ready", operator_safety_ready),
            ("manual_review_capacity_ready", manual_review_capacity_ready),
        )
        if value is None
    )
    if missing:
        raise ValueError(f"missing candidate selection cutline inputs: {', '.join(missing)}")

    normalized = StrategyCandidateSelectionCutlineInputs(
        candidate_count=candidate_count,
        quality_index_score=quality_index_score,
        edge_to_threshold_probability=edge_to_threshold_probability,
        source_reliability_score=source_reliability_score,
        memory_quality_score=memory_quality_score,
        liquidity_exit_ready=liquidity_exit_ready,
        operator_safety_ready=operator_safety_ready,
        manual_review_capacity_ready=manual_review_capacity_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    blocked_reason_codes = _blocked_reason_codes(normalized)
    attention_reason_codes = _attention_reason_codes(normalized)
    cutline_band = _cutline_band(
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    )
    selected_candidate_count = _selected_candidate_count(
        normalized.candidate_count,
        cutline_band=cutline_band,
    )
    deferred_candidate_count = _quantize(
        normalized.candidate_count - selected_candidate_count,
    )
    ready_ratio = _ratio(
        selected_candidate_count,
        normalized.candidate_count,
        zero_default=_ONE,
    )

    return StrategyCandidateSelectionCutlineReport(
        generated_at=_require_utc_datetime(generated_at or datetime.now(UTC)),
        config_version=config_version,
        candidate_count=normalized.candidate_count,
        quality_index_score=normalized.quality_index_score,
        edge_to_threshold_probability=normalized.edge_to_threshold_probability,
        source_reliability_score=normalized.source_reliability_score,
        memory_quality_score=normalized.memory_quality_score,
        liquidity_exit_ready=normalized.liquidity_exit_ready,
        operator_safety_ready=normalized.operator_safety_ready,
        manual_review_capacity_ready=normalized.manual_review_capacity_ready,
        selection_cutline_ready=not blocked_reason_codes,
        cutline_band=cutline_band,
        selected_candidate_count=selected_candidate_count,
        deferred_candidate_count=deferred_candidate_count,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=ready_ratio,
        paper_only=normalized.paper_only,
        report_only=normalized.report_only,
        readonly=normalized.readonly,
    )


def strategy_candidate_selection_cutline_public_payload(
    value: StrategyCandidateSelectionCutlineReport | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(value, dict):
        payload = dict(value)
        _validate_payload(payload)
        return payload
    if type(value) is not StrategyCandidateSelectionCutlineReport:
        raise TypeError(
            "value must be StrategyCandidateSelectionCutlineReport or payload dict",
        )
    _require_hard_flags("report", value)
    _reject_unsafe_public_payload("report", value)
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    _validate_payload(payload)
    return payload


def format_strategy_candidate_selection_cutline_digest(
    report: StrategyCandidateSelectionCutlineReport,
) -> str:
    if type(report) is not StrategyCandidateSelectionCutlineReport:
        raise TypeError("report must be StrategyCandidateSelectionCutlineReport")
    return (
        "strategy_candidate_selection_cutline_report("
        f"generated_at={report.generated_at.isoformat()}, "
        f"selection_cutline_ready={str(report.selection_cutline_ready).lower()}, "
        f"cutline_band={report.cutline_band}, "
        f"selected_candidate_count={report.selected_candidate_count}, "
        f"deferred_candidate_count={report.deferred_candidate_count}, "
        f"ready_ratio={report.ready_ratio}, "
        f"blocked_reason_codes={','.join(report.blocked_reason_codes) or 'none'}, "
        f"attention_reason_codes={','.join(report.attention_reason_codes) or 'none'}, "
        f"public_digest={report.public_digest})"
    )


def _blocked_reason_codes(
    inputs: StrategyCandidateSelectionCutlineInputs,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.quality_index_score < _ATTENTION_MIN_QUALITY:
        reasons.append("quality_index_score_below_cutline")
    if inputs.edge_to_threshold_probability < _ATTENTION_MIN_EDGE:
        reasons.append("edge_to_threshold_probability_below_cutline")
    if inputs.source_reliability_score < _ATTENTION_MIN_SOURCE_RELIABILITY:
        reasons.append("source_reliability_score_below_cutline")
    if inputs.memory_quality_score < _ATTENTION_MIN_MEMORY_QUALITY:
        reasons.append("memory_quality_score_below_cutline")
    if inputs.liquidity_exit_ready is False:
        reasons.append("liquidity_exit_not_ready")
    if inputs.manual_review_capacity_ready is False:
        reasons.append("manual_review_capacity_not_ready")
    if inputs.operator_safety_ready is False:
        reasons.append("operator_safety_not_ready")
    return tuple(sorted(reasons))


def _attention_reason_codes(
    inputs: StrategyCandidateSelectionCutlineInputs,
) -> tuple[str, ...]:
    if _blocked_reason_codes(inputs):
        return ()
    reasons: list[str] = []
    if inputs.quality_index_score < _SELECT_MIN_QUALITY:
        reasons.append("quality_index_score_attention")
    if inputs.edge_to_threshold_probability < _SELECT_MIN_EDGE:
        reasons.append("edge_to_threshold_probability_attention")
    if inputs.source_reliability_score < _SELECT_MIN_SOURCE_RELIABILITY:
        reasons.append("source_reliability_score_attention")
    if inputs.memory_quality_score < _SELECT_MIN_MEMORY_QUALITY:
        reasons.append("memory_quality_score_attention")
    return tuple(sorted(reasons))


def _cutline_band(
    *,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "attention"
    return "select"


def _selected_candidate_count(candidate_count: Decimal, *, cutline_band: str) -> Decimal:
    if cutline_band == "blocked":
        return _ZERO
    if cutline_band == "attention":
        return _quantize(candidate_count * _HALF)
    return candidate_count


def _normalize_input_values(value: object) -> None:
    object.__setattr__(
        value,
        "candidate_count",
        _require_nonnegative_decimal("candidate_count", getattr(value, "candidate_count")),
    )
    for field_name in (
        "quality_index_score",
        "source_reliability_score",
        "memory_quality_score",
    ):
        object.__setattr__(
            value,
            field_name,
            _require_ratio_decimal(field_name, getattr(value, field_name)),
        )
    object.__setattr__(
        value,
        "edge_to_threshold_probability",
        _require_decimal(
            "edge_to_threshold_probability",
            getattr(value, "edge_to_threshold_probability"),
        ),
    )
    for field_name in _READY_GATE_NAMES:
        _require_bool(field_name, getattr(value, field_name))


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


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    number = _require_nonnegative_decimal(name, value)
    if number > _ONE:
        raise ValueError(f"{name} must be no greater than 1.000000")
    return number


def _require_bool(name: str, value: bool) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool")
    return value


def _require_cutline_band(value: str) -> str:
    if value not in {"select", "attention", "blocked"}:
        raise ValueError("cutline_band must be select, attention, or blocked")
    return value


def _require_supported_config_version(value: str) -> str:
    if type(value) is not str:
        raise TypeError("config_version must be str")
    if value != DEFAULT_STRATEGY_CANDIDATE_SELECTION_CUTLINE_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return value


def _require_utc_datetime(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError("generated_at must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _require_reason_codes(name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be tuple")
    normalized = tuple(sorted(value))
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} entries must be unique")
    for code in normalized:
        if type(code) is not str:
            raise TypeError(f"{name} entries must be str")
        if not code or not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", code):
            raise ValueError(f"{name} entries must be public reason codes")
    return normalized


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


def _validate_report_consistency(report: StrategyCandidateSelectionCutlineReport) -> None:
    blocked_reason_codes = _blocked_reason_codes(
        StrategyCandidateSelectionCutlineInputs(
            candidate_count=report.candidate_count,
            quality_index_score=report.quality_index_score,
            edge_to_threshold_probability=report.edge_to_threshold_probability,
            source_reliability_score=report.source_reliability_score,
            memory_quality_score=report.memory_quality_score,
            liquidity_exit_ready=report.liquidity_exit_ready,
            operator_safety_ready=report.operator_safety_ready,
            manual_review_capacity_ready=report.manual_review_capacity_ready,
        ),
    )
    attention_reason_codes = _attention_reason_codes(
        StrategyCandidateSelectionCutlineInputs(
            candidate_count=report.candidate_count,
            quality_index_score=report.quality_index_score,
            edge_to_threshold_probability=report.edge_to_threshold_probability,
            source_reliability_score=report.source_reliability_score,
            memory_quality_score=report.memory_quality_score,
            liquidity_exit_ready=report.liquidity_exit_ready,
            operator_safety_ready=report.operator_safety_ready,
            manual_review_capacity_ready=report.manual_review_capacity_ready,
        ),
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match cutline inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match cutline inputs")
    if report.cutline_band != _cutline_band(
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    ):
        raise ValueError("cutline_band must match cutline inputs")
    if report.selection_cutline_ready is not (not blocked_reason_codes):
        raise ValueError("selection_cutline_ready must match blocked_reason_codes")
    if report.selected_candidate_count != _selected_candidate_count(
        report.candidate_count,
        cutline_band=report.cutline_band,
    ):
        raise ValueError("selected_candidate_count must match cutline_band")
    if report.deferred_candidate_count != _quantize(
        report.candidate_count - report.selected_candidate_count,
    ):
        raise ValueError("deferred_candidate_count must match candidate_count")
    if report.ready_ratio != _ratio(
        report.selected_candidate_count,
        report.candidate_count,
        zero_default=_ONE,
    ):
        raise ValueError("ready_ratio must match selected_candidate_count")


def _ratio(numerator: Decimal, denominator: Decimal, *, zero_default: Decimal) -> Decimal:
    if denominator == _ZERO:
        return zero_default
    with localcontext() as context:
        context.prec = 28
        value = numerator / denominator
    if value > _ONE:
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


def _payload_without_digest(
    report: StrategyCandidateSelectionCutlineReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("public_digest", None)
    return {key: payload[key] for key in _PUBLIC_PAYLOAD_KEYS if key in payload}


def _public_digest_for_report(report: StrategyCandidateSelectionCutlineReport) -> str:
    payload = _payload_without_digest(report)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{sha256(blob.encode('utf-8')).hexdigest()}"


def _validate_payload(payload: dict[str, Any]) -> None:
    if tuple(payload.keys()) != _PUBLIC_PAYLOAD_KEYS:
        raise ValueError("public_payload keys must match the candidate selection cutline schema")
    for key in _DECIMAL_PAYLOAD_KEYS:
        if type(payload[key]) is not str:
            raise TypeError(f"{key} must be rendered as a string")
        _require_decimal(key, Decimal(payload[key]))
    for flag_name in _FLAG_NAMES:
        if payload[flag_name] is not True:
            raise ValueError(f"public_payload {flag_name} must be True")
    for key in (
        "liquidity_exit_ready",
        "operator_safety_ready",
        "manual_review_capacity_ready",
        "selection_cutline_ready",
    ):
        if type(payload[key]) is not bool:
            raise TypeError(f"{key} must be bool")
    _require_cutline_band(payload["cutline_band"])
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


REPORT_DECIMAL_FIELDS = tuple(
    field.name
    for field in fields(StrategyCandidateSelectionCutlineReport)
    if field.name.endswith(("_count", "_score", "_probability", "_ratio"))
)
