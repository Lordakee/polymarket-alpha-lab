"""Report-only research signal source diversity assessment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SIGNAL_SOURCE_DIVERSITY_CONFIG_VERSION = (
    "research-signal-source-diversity-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_STANCES = frozenset(("supports", "counters", "neutral"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "url",
    "source_ref",
    "source_text",
    "source_table",
    "dsn",
    "token",
    "market_id",
    "candidate_id",
    "raw_market",
    "raw_candidate",
    "auth",
    "wallet",
    "trade",
    "order",
    "buy",
    "sell",
    "database",
    "network",
    "socket",
    "persist",
    "mutation",
)
_UNSAFE_PUBLIC_KEY_TERMS = (
    "url",
    "ref",
    "text",
    "table",
    "dsn",
    "token",
    "market_id",
    "candidate_id",
    "raw_market",
    "raw_candidate",
    "auth",
    "wallet",
    "trade",
    "order",
    "buy",
    "sell",
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "single_source_family_block",
    "single_independent_source_block",
    "insufficient_source_family_diversity_watch",
    "insufficient_independent_source_watch",
    "source_concentration_block",
    "counterevidence_coverage_watch",
    "diversity_score_watch",
    "source_diversity_pass",
)


@dataclass(frozen=True)
class ResearchSignalSourceDiversityConfig:
    config_version: str = DEFAULT_RESEARCH_SIGNAL_SOURCE_DIVERSITY_CONFIG_VERSION
    min_source_family_count: Decimal = Decimal("3.000000")
    min_independent_source_count: Decimal = Decimal("3.000000")
    max_source_concentration_ratio: Decimal = Decimal("0.500000")
    min_counterevidence_coverage_ratio: Decimal = Decimal("0.200000")
    pass_diversity_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalSourceDiversityConfig:
            raise TypeError(
                "ResearchSignalSourceDiversityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalSourceDiversityConfig:
            raise ValueError(
                "config must be exactly ResearchSignalSourceDiversityConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SIGNAL_SOURCE_DIVERSITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_source_family_count", "min_independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_source_concentration_ratio",
            "min_counterevidence_coverage_ratio",
            "pass_diversity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSignalSourceDiversityObservation:
    signal_key: str
    observation_key: str
    source_family: str
    source_cluster: str
    stance: str
    observed_at: datetime
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalSourceDiversityObservation:
            raise TypeError(
                "ResearchSignalSourceDiversityObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalSourceDiversityObservation:
            raise ValueError(
                "observation must be exactly ResearchSignalSourceDiversityObservation",
            )
        for field_name in (
            "signal_key",
            "observation_key",
            "source_family",
            "source_cluster",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("stance", self.stance, _STANCES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSignalSourceDiversityPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalSourceDiversityPublicPayloadItem:
            raise TypeError(
                "ResearchSignalSourceDiversityPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalSourceDiversityPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSignalSourceDiversityPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_value("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSignalSourceDiversityRow:
    signal_key: str
    observation_count: Decimal
    supporting_observation_count: Decimal
    counter_observation_count: Decimal
    source_family_count: Decimal
    independent_source_count: Decimal
    source_concentration_ratio: Decimal
    counterevidence_coverage_ratio: Decimal
    average_confidence_score: Decimal
    diversity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalSourceDiversityRow:
            raise TypeError(
                "ResearchSignalSourceDiversityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalSourceDiversityRow:
            raise ValueError("row must be exactly ResearchSignalSourceDiversityRow")
        _require_public_identifier("signal_key", self.signal_key)
        for field_name in (
            "observation_count",
            "supporting_observation_count",
            "counter_observation_count",
            "source_family_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_concentration_ratio",
            "counterevidence_coverage_ratio",
            "average_confidence_score",
            "diversity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSignalSourceDiversityReport:
    generated_at: datetime
    config_version: str
    status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_diversity_score: Decimal
    max_source_concentration_ratio: Decimal
    rows: tuple[ResearchSignalSourceDiversityRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSignalSourceDiversityPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSignalSourceDiversityReport:
            raise TypeError(
                "ResearchSignalSourceDiversityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSignalSourceDiversityReport:
            raise ValueError("report must be exactly ResearchSignalSourceDiversityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SIGNAL_SOURCE_DIVERSITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_diversity_score",
            "max_source_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSignalSourceDiversityReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_signal_source_diversity_report(
    observations: Sequence[ResearchSignalSourceDiversityObservation],
    *,
    generated_at: datetime,
    config: ResearchSignalSourceDiversityConfig | None = None,
    public_payload: Sequence[ResearchSignalSourceDiversityPublicPayloadItem] = (),
) -> ResearchSignalSourceDiversityReport:
    """Build a local report-only source diversity assessment."""

    if config is None:
        config = ResearchSignalSourceDiversityConfig()
    if type(config) is not ResearchSignalSourceDiversityConfig:
        raise ValueError("config must be a ResearchSignalSourceDiversityConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "signal_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_diversity_score": _average(
            tuple(row.diversity_score for row in rows),
        ),
        "max_source_concentration_ratio": max(
            (row.source_concentration_ratio for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSignalSourceDiversityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchSignalSourceDiversityObservation, ...],
    config: ResearchSignalSourceDiversityConfig,
) -> tuple[ResearchSignalSourceDiversityRow, ...]:
    grouped: dict[str, list[ResearchSignalSourceDiversityObservation]] = {}
    for item in observations:
        grouped.setdefault(item.signal_key, []).append(item)
    rows = [
        _row_for_signal(signal_key, tuple(items), config)
        for signal_key, items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_signal(
    signal_key: str,
    observations: tuple[ResearchSignalSourceDiversityObservation, ...],
    config: ResearchSignalSourceDiversityConfig,
) -> ResearchSignalSourceDiversityRow:
    observation_count = _decimal_count(len(observations))
    supporting_count = _decimal_count(
        sum(1 for item in observations if item.stance == "supports"),
    )
    counter_count = _decimal_count(
        sum(1 for item in observations if item.stance == "counters"),
    )
    family_count = _decimal_count(len({item.source_family for item in observations}))
    independent_count = _decimal_count(len({item.source_cluster for item in observations}))
    concentration_ratio = _source_concentration_ratio(observations)
    counter_ratio = _safe_ratio(counter_count, observation_count)
    average_confidence = _average(tuple(item.confidence_score for item in observations))
    diversity_score = _diversity_score(
        family_count=family_count,
        independent_count=independent_count,
        concentration_ratio=concentration_ratio,
        counterevidence_ratio=counter_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        family_count=family_count,
        independent_count=independent_count,
        concentration_ratio=concentration_ratio,
        counterevidence_ratio=counter_ratio,
        diversity_score=diversity_score,
        config=config,
    )
    return ResearchSignalSourceDiversityRow(
        signal_key=signal_key,
        observation_count=observation_count,
        supporting_observation_count=supporting_count,
        counter_observation_count=counter_count,
        source_family_count=family_count,
        independent_source_count=independent_count,
        source_concentration_ratio=concentration_ratio,
        counterevidence_coverage_ratio=counter_ratio,
        average_confidence_score=average_confidence,
        diversity_score=diversity_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _source_concentration_ratio(
    observations: tuple[ResearchSignalSourceDiversityObservation, ...],
) -> Decimal:
    if not observations:
        return _ZERO
    counts: dict[str, int] = {}
    for item in observations:
        counts[item.source_family] = counts.get(item.source_family, 0) + 1
    return _safe_ratio(_decimal_count(max(counts.values())), _decimal_count(len(observations)))


def _diversity_score(
    *,
    family_count: Decimal,
    independent_count: Decimal,
    concentration_ratio: Decimal,
    counterevidence_ratio: Decimal,
    config: ResearchSignalSourceDiversityConfig,
) -> Decimal:
    family_score = _clamp_ratio(family_count / config.min_source_family_count)
    independent_score = _clamp_ratio(
        independent_count / config.min_independent_source_count,
    )
    concentration_score = (
        _ONE
        if concentration_ratio <= config.max_source_concentration_ratio
        else _clamp_ratio(config.max_source_concentration_ratio / concentration_ratio)
    )
    counter_score = _clamp_ratio(
        counterevidence_ratio / config.min_counterevidence_coverage_ratio,
    )
    return _average((family_score, independent_score, concentration_score, counter_score))


def _row_reason_codes(
    *,
    family_count: Decimal,
    independent_count: Decimal,
    concentration_ratio: Decimal,
    counterevidence_ratio: Decimal,
    diversity_score: Decimal,
    config: ResearchSignalSourceDiversityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if family_count <= _ONE:
        reason_codes.append("single_source_family_block")
    elif family_count < config.min_source_family_count:
        reason_codes.append("insufficient_source_family_diversity_watch")
    if independent_count <= _ONE:
        reason_codes.append("single_independent_source_block")
    elif independent_count < config.min_independent_source_count:
        reason_codes.append("insufficient_independent_source_watch")
    if concentration_ratio > config.max_source_concentration_ratio:
        reason_codes.append("source_concentration_block")
    if counterevidence_ratio < config.min_counterevidence_coverage_ratio:
        reason_codes.append("counterevidence_coverage_watch")
    if diversity_score < config.pass_diversity_score:
        reason_codes.append("diversity_score_watch")
    if not reason_codes:
        reason_codes.append("source_diversity_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("source_diversity_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSignalSourceDiversityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSignalSourceDiversityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[ResearchSignalSourceDiversityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchSignalSourceDiversityRow) -> None:
    if row.supporting_observation_count + row.counter_observation_count > row.observation_count:
        raise ValueError(
            "supporting_observation_count plus counter_observation_count must not "
            "exceed observation_count",
        )
    if row.source_family_count > row.observation_count:
        raise ValueError("source_family_count must not exceed observation_count")
    if row.independent_source_count > row.observation_count:
        raise ValueError("independent_source_count must not exceed observation_count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("source_diversity_pass",):
        raise ValueError("pass rows must include only source_diversity_pass")


def _validate_report_consistency(report: ResearchSignalSourceDiversityReport) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_diversity_score != _average(
        tuple(row.diversity_score for row in report.rows),
    ):
        raise ValueError("average_diversity_score must match rows")
    expected_max_concentration = max(
        (row.source_concentration_ratio for row in report.rows),
        default=_ZERO,
    )
    if report.max_source_concentration_ratio != expected_max_concentration:
        raise ValueError("max_source_concentration_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchSignalSourceDiversityObservation],
) -> tuple[ResearchSignalSourceDiversityObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSignalSourceDiversityObservation] = []
    for item in observations:
        if type(item) is not ResearchSignalSourceDiversityObservation:
            raise ValueError(
                "observations items must be ResearchSignalSourceDiversityObservation",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.signal_key,
                item.observed_at,
                item.observation_key,
                item.source_family,
                item.source_cluster,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSignalSourceDiversityRow],
) -> tuple[ResearchSignalSourceDiversityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSignalSourceDiversityRow] = []
    for row in rows:
        if type(row) is not ResearchSignalSourceDiversityRow:
            raise ValueError("rows must contain ResearchSignalSourceDiversityRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.signal_key))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSignalSourceDiversityPublicPayloadItem],
) -> tuple[ResearchSignalSourceDiversityPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSignalSourceDiversityPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchSignalSourceDiversityPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchSignalSourceDiversityPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_value(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(report: ResearchSignalSourceDiversityReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_KEY_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_SIGNAL_SOURCE_DIVERSITY_CONFIG_VERSION",
    "ResearchSignalSourceDiversityConfig",
    "ResearchSignalSourceDiversityObservation",
    "ResearchSignalSourceDiversityPublicPayloadItem",
    "ResearchSignalSourceDiversityReport",
    "ResearchSignalSourceDiversityRow",
    "build_research_signal_source_diversity_report",
)
