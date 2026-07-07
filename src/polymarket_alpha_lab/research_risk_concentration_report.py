"""Readonly research queue risk concentration report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION = (
    "research-risk-concentration-report-v0"
)

DIMENSIONS = ("domain", "source", "rule", "timeline")
DIMENSION_FIELDS = {
    "domain": "domain_key",
    "source": "source_family",
    "rule": "rule_family",
    "timeline": "timeline_bucket",
}
REPORT_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

PASS_REASON = "research_risk_concentration_passed"
REASON_CODES = (
    PASS_REASON,
    "research_risk_concentration_domain_watch",
    "research_risk_concentration_domain_block",
    "research_risk_concentration_source_watch",
    "research_risk_concentration_source_block",
    "research_risk_concentration_rule_watch",
    "research_risk_concentration_rule_block",
    "research_risk_concentration_timeline_watch",
    "research_risk_concentration_timeline_block",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


def _part(*pieces: str) -> str:
    return "".join(pieces)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _part("can", "didate", "_id"),
        _part("mar", "ket", "_id"),
        _part("mar", "ket", "_slug"),
        _part("ques", "tion"),
        _part("source", "_ref"),
        _part("source", "_url"),
        _part("source", "_text"),
        _part("http", "://"),
        _part("https", "://"),
        _part("ww", "w."),
        _part("ds", "n"),
        _part("ta", "ble"),
        _part("to", "ken"),
        _part("wal", "let"),
        _part("au", "th"),
        _part("ord", "er"),
        _part("tra", "de"),
        _part("pos", "ition"),
        _part("b", "uy"),
        _part("s", "ell"),
        _part("recom", "mend"),
    ),
)


@dataclass(frozen=True)
class ResearchRiskConcentrationConfig:
    config_version: str = DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION
    domain_watch_ratio: Decimal = Decimal("0.600000")
    domain_block_ratio: Decimal = Decimal("0.750000")
    source_watch_ratio: Decimal = Decimal("0.600000")
    source_block_ratio: Decimal = Decimal("0.750000")
    rule_watch_ratio: Decimal = Decimal("0.600000")
    rule_block_ratio: Decimal = Decimal("0.750000")
    timeline_watch_ratio: Decimal = Decimal("0.600000")
    timeline_block_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchRiskConcentrationConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for dimension in DIMENSIONS:
            watch_name = f"{dimension}_watch_ratio"
            block_name = f"{dimension}_block_ratio"
            watch_ratio = _require_ratio(watch_name, getattr(self, watch_name))
            block_ratio = _require_ratio(block_name, getattr(self, block_name))
            if block_ratio < watch_ratio:
                raise ValueError(f"{block_name} must be at least {watch_name}")
            object.__setattr__(self, watch_name, watch_ratio)
            object.__setattr__(self, block_name, block_ratio)
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchRiskConcentrationCandidate:
    candidate_id: str
    domain_key: str
    source_family: str
    rule_family: str
    timeline_bucket: str
    risk_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchRiskConcentrationCandidate does not support subclassing")

    def __post_init__(self) -> None:
        _require_private_identifier("candidate_id", self.candidate_id)
        for field_name in (
            "domain_key",
            "source_family",
            "rule_family",
            "timeline_bucket",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "risk_weight",
            _require_positive_decimal("risk_weight", self.risk_weight),
        )
        _require_flags("candidate", self)


@dataclass(frozen=True)
class ResearchRiskConcentrationDimension:
    dimension: str
    top_group_label: str
    top_group_item_count: Decimal
    top_group_item_ratio: Decimal
    top_group_risk_weight: Decimal
    top_group_risk_weight_ratio: Decimal
    dimension_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchRiskConcentrationDimension does not support subclassing")

    def __post_init__(self) -> None:
        _require_member("dimension", self.dimension, DIMENSIONS)
        object.__setattr__(
            self,
            "top_group_label",
            _require_public_string("top_group_label", self.top_group_label),
        )
        object.__setattr__(
            self,
            "top_group_item_count",
            _require_nonnegative_count(
                "top_group_item_count",
                self.top_group_item_count,
            ),
        )
        for field_name in ("top_group_item_ratio", "top_group_risk_weight_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_group_risk_weight",
            _require_nonnegative_decimal(
                "top_group_risk_weight",
                self.top_group_risk_weight,
            ),
        )
        _require_member("dimension_status", self.dimension_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("dimension", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _dimension_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_dimension(self)


@dataclass(frozen=True)
class ResearchRiskConcentrationReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    total_risk_weight: Decimal
    pass_dimension_count: Decimal
    watch_dimension_count: Decimal
    block_dimension_count: Decimal
    max_concentration_ratio: Decimal
    max_risk_weight_ratio: Decimal
    domain_watch_ratio: Decimal
    domain_block_ratio: Decimal
    source_watch_ratio: Decimal
    source_block_ratio: Decimal
    rule_watch_ratio: Decimal
    rule_block_ratio: Decimal
    timeline_watch_ratio: Decimal
    timeline_block_ratio: Decimal
    reason_codes: tuple[str, ...]
    dimensions: tuple[ResearchRiskConcentrationDimension, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchRiskConcentrationReport does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "item_count",
            "pass_dimension_count",
            "watch_dimension_count",
            "block_dimension_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_risk_weight",
            _require_nonnegative_decimal("total_risk_weight", self.total_risk_weight),
        )
        for field_name in ("max_concentration_ratio", "max_risk_weight_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for dimension in DIMENSIONS:
            for suffix in ("watch_ratio", "block_ratio"):
                field_name = f"{dimension}_{suffix}"
                object.__setattr__(
                    self,
                    field_name,
                    _require_ratio(field_name, getattr(self, field_name)),
                )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "dimensions", _normalize_dimensions(self.dimensions))
        _require_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)


def build_research_risk_concentration_report(
    candidates: list[ResearchRiskConcentrationCandidate]
    | tuple[ResearchRiskConcentrationCandidate, ...],
    *,
    config: ResearchRiskConcentrationConfig,
    generated_at: datetime,
) -> ResearchRiskConcentrationReport:
    if type(config) is not ResearchRiskConcentrationConfig:
        raise ValueError("config must be a ResearchRiskConcentrationConfig")
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    dimensions = tuple(
        _dimension_row(dimension, normalized_candidates, config=config)
        for dimension in DIMENSIONS
    )
    return ResearchRiskConcentrationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(dimensions),
        item_count=_count_decimal(len(normalized_candidates)),
        total_risk_weight=_sum_decimal(
            candidate.risk_weight for candidate in normalized_candidates
        ),
        pass_dimension_count=_dimension_status_count(dimensions, "pass"),
        watch_dimension_count=_dimension_status_count(dimensions, "watch"),
        block_dimension_count=_dimension_status_count(dimensions, "block"),
        max_concentration_ratio=max(
            (dimension.top_group_item_ratio for dimension in dimensions),
            default=ZERO,
        ),
        max_risk_weight_ratio=max(
            (dimension.top_group_risk_weight_ratio for dimension in dimensions),
            default=ZERO,
        ),
        domain_watch_ratio=config.domain_watch_ratio,
        domain_block_ratio=config.domain_block_ratio,
        source_watch_ratio=config.source_watch_ratio,
        source_block_ratio=config.source_block_ratio,
        rule_watch_ratio=config.rule_watch_ratio,
        rule_block_ratio=config.rule_block_ratio,
        timeline_watch_ratio=config.timeline_watch_ratio,
        timeline_block_ratio=config.timeline_block_ratio,
        reason_codes=_report_reason_codes(dimensions),
        dimensions=dimensions,
    )


def research_risk_concentration_report_payload(value: object) -> dict[str, Any]:
    if type(value) is ResearchRiskConcentrationReport:
        _validate_report(value)
        payload = _json_ready(value)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        validate_research_risk_concentration_public_payload(payload)
        return payload
    if type(value) is dict:
        validate_research_risk_concentration_public_payload(value)
        return dict(value)
    raise ValueError("value must be a ResearchRiskConcentrationReport or dict")


def validate_research_risk_concentration_public_payload(payload: dict[str, Any]) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    dimensions = payload.get("dimensions")
    if type(dimensions) is not list:
        raise ValueError("dimensions must be a list")
    for dimension_payload in dimensions:
        if type(dimension_payload) is not dict:
            raise ValueError("dimensions must contain dict values")
        _require_public_payload_flags(dimension_payload)
        digest = _payload_required_string(
            dimension_payload,
            "derived_validation_digest",
        )
        _require_digest("derived_validation_digest", digest)
        if digest != _public_dimension_digest(dimension_payload):
            raise ValueError("derived_validation_digest must match dimension payload")
    digest = _payload_required_string(payload, "derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    if digest != _public_report_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _dimension_row(
    dimension: str,
    candidates: tuple[ResearchRiskConcentrationCandidate, ...],
    *,
    config: ResearchRiskConcentrationConfig,
) -> ResearchRiskConcentrationDimension:
    field_name = DIMENSION_FIELDS[dimension]
    item_count = _count_decimal(len(candidates))
    total_weight = _sum_decimal(candidate.risk_weight for candidate in candidates)
    group_stats: dict[str, tuple[Decimal, Decimal]] = {}
    for candidate in candidates:
        group_label = getattr(candidate, field_name)
        current_count, current_weight = group_stats.get(group_label, (ZERO, ZERO))
        group_stats[group_label] = (
            current_count + ONE,
            _quantize(current_weight + candidate.risk_weight),
        )
    top_label, top_count, top_weight = _top_group(group_stats)
    top_item_ratio = _safe_ratio(top_count, item_count)
    top_weight_ratio = _safe_ratio(top_weight, total_weight)
    status = _dimension_status(
        dimension,
        max(top_item_ratio, top_weight_ratio),
        config=config,
    )
    return ResearchRiskConcentrationDimension(
        dimension=dimension,
        top_group_label=top_label,
        top_group_item_count=top_count,
        top_group_item_ratio=top_item_ratio,
        top_group_risk_weight=top_weight,
        top_group_risk_weight_ratio=top_weight_ratio,
        dimension_status=status,
        reason_codes=_dimension_reason_codes(dimension, status),
    )


def _top_group(group_stats: dict[str, tuple[Decimal, Decimal]]) -> tuple[str, Decimal, Decimal]:
    if not group_stats:
        return ("none", ZERO, ZERO)
    return sorted(
        (
            (group_label, item_count, risk_weight)
            for group_label, (item_count, risk_weight) in group_stats.items()
        ),
        key=lambda item: (-item[1], -item[2], item[0]),
    )[0]


def _dimension_status(
    dimension: str,
    concentration_ratio: Decimal,
    *,
    config: ResearchRiskConcentrationConfig,
) -> str:
    if concentration_ratio >= getattr(config, f"{dimension}_block_ratio"):
        return "block"
    if concentration_ratio >= getattr(config, f"{dimension}_watch_ratio"):
        return "watch"
    return "pass"


def _dimension_reason_codes(dimension: str, status: str) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    return (f"research_risk_concentration_{dimension}_{status}",)


def _report_status(
    dimensions: tuple[ResearchRiskConcentrationDimension, ...],
) -> str:
    if any(dimension.dimension_status == "block" for dimension in dimensions):
        return "block"
    if any(dimension.dimension_status == "watch" for dimension in dimensions):
        return "watch"
    return "pass"


def _report_reason_codes(
    dimensions: tuple[ResearchRiskConcentrationDimension, ...],
) -> tuple[str, ...]:
    found = frozenset(
        reason_code
        for dimension in dimensions
        for reason_code in dimension.reason_codes
        if reason_code != PASS_REASON
    )
    if not found:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in found)


def _dimension_status_count(
    dimensions: tuple[ResearchRiskConcentrationDimension, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for dimension in dimensions if dimension.dimension_status == status),
    )


def _normalize_candidates(
    value: object,
) -> tuple[ResearchRiskConcentrationCandidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    seen: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not ResearchRiskConcentrationCandidate:
            raise ValueError(
                "candidates must contain ResearchRiskConcentrationCandidate values",
            )
        _require_flags("candidate", candidate)
        if candidate.candidate_id in seen:
            raise ValueError("candidates must be unique by candidate_id")
        seen.add(candidate.candidate_id)
    return tuple(sorted(candidates, key=_candidate_sort_key))


def _candidate_sort_key(
    candidate: ResearchRiskConcentrationCandidate,
) -> tuple[str, str, str, str, str]:
    return (
        candidate.domain_key,
        candidate.source_family,
        candidate.rule_family,
        candidate.timeline_bucket,
        candidate.candidate_id,
    )


def _normalize_dimensions(value: object) -> tuple[ResearchRiskConcentrationDimension, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("dimensions must be a list or tuple")
    dimensions = tuple(value)
    seen: set[str] = set()
    for dimension in dimensions:
        if type(dimension) is not ResearchRiskConcentrationDimension:
            raise ValueError(
                "dimensions must contain ResearchRiskConcentrationDimension values",
            )
        _require_flags("dimension", dimension)
        if dimension.dimension in seen:
            raise ValueError("dimensions must be unique")
        seen.add(dimension.dimension)
    expected = tuple(
        dimension
        for dimension_name in DIMENSIONS
        for dimension in dimensions
        if dimension.dimension == dimension_name
    )
    if dimensions != expected:
        raise ValueError("dimensions must use deterministic sequence")
    return dimensions


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, REASON_CODES)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_dimension(dimension: ResearchRiskConcentrationDimension) -> None:
    if dimension.dimension_status == "pass" and dimension.reason_codes != (PASS_REASON,):
        raise ValueError("pass dimension must use pass reason")
    if dimension.dimension_status != "pass" and dimension.reason_codes != (
        f"research_risk_concentration_{dimension.dimension}_{dimension.dimension_status}",
    ):
        raise ValueError("dimension reason_codes must match dimension_status")
    if dimension.derived_validation_digest != _dimension_digest(dimension):
        raise ValueError("derived_validation_digest must match dimension payload")


def _validate_report(report: ResearchRiskConcentrationReport) -> None:
    expected_values = {
        "report_status": _report_status(report.dimensions),
        "pass_dimension_count": _dimension_status_count(report.dimensions, "pass"),
        "watch_dimension_count": _dimension_status_count(report.dimensions, "watch"),
        "block_dimension_count": _dimension_status_count(report.dimensions, "block"),
        "max_concentration_ratio": max(
            (dimension.top_group_item_ratio for dimension in report.dimensions),
            default=ZERO,
        ),
        "max_risk_weight_ratio": max(
            (dimension.top_group_risk_weight_ratio for dimension in report.dimensions),
            default=ZERO,
        ),
        "reason_codes": _report_reason_codes(report.dimensions),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match dimensions")
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match public payload")


def _dimension_digest(dimension: ResearchRiskConcentrationDimension) -> str:
    payload = _json_ready(asdict(dimension))
    if type(payload) is not dict:
        raise ValueError("dimension payload must be a JSON object")
    return _public_dimension_digest(payload)


def _report_digest(report: ResearchRiskConcentrationReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _public_report_digest(payload)


def _public_dimension_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    return _digest_payload(payload_without_digest)


def _public_report_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    return _digest_payload(payload_without_digest)


def _digest_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = _normalize_public_text(value)
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _normalize_public_text(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


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
        raise ValueError("JSON Decimal value must be an exact Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if isinstance(value, bool):
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
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


def _require_private_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_flags(label: str, value: object) -> None:
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


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


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


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be an exact Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


__all__ = (
    "DEFAULT_RESEARCH_RISK_CONCENTRATION_REPORT_CONFIG_VERSION",
    "ResearchRiskConcentrationCandidate",
    "ResearchRiskConcentrationConfig",
    "ResearchRiskConcentrationDimension",
    "ResearchRiskConcentrationReport",
    "build_research_risk_concentration_report",
    "research_risk_concentration_report_payload",
    "validate_research_risk_concentration_public_payload",
)
