"""Phase 1 report-only research consensus gap penalty snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_STRATEGY_CANDIDATE_RESEARCH_CONSENSUS_GAP_PENALTY_V2_CONFIG_VERSION = (
    "strategy-candidate-research-consensus-gap-penalty-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
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
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "research_consensus_gap_penalty",
    "weak_quorum_penalty",
    "independent_source_boost",
    "consensus_score_watch",
    "consensus_score_blocked",
    "research_consensus_gap_pass",
)


@dataclass(frozen=True)
class StrategyCandidateResearchConsensusGapPenaltyConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_RESEARCH_CONSENSUS_GAP_PENALTY_V2_CONFIG_VERSION
    )
    min_observation_count: Decimal = Decimal("2.000000")
    min_consensus_score: Decimal = Decimal("0.650000")
    min_block_score: Decimal = Decimal("0.350000")
    consensus_gap_penalty_multiplier: Decimal = Decimal("1.000000")
    weak_quorum_penalty_per_missing_observation: Decimal = Decimal("0.200000")
    independent_source_boost_per_source: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateResearchConsensusGapPenaltyConfig:
            raise TypeError(
                "StrategyCandidateResearchConsensusGapPenaltyConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResearchConsensusGapPenaltyConfig:
            raise ValueError(
                "config must be exactly "
                "StrategyCandidateResearchConsensusGapPenaltyConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_RESEARCH_CONSENSUS_GAP_PENALTY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_observation_count",
            _require_positive_count_decimal(
                "min_observation_count",
                self.min_observation_count,
            ),
        )
        for field_name in (
            "min_consensus_score",
            "min_block_score",
            "consensus_gap_penalty_multiplier",
            "weak_quorum_penalty_per_missing_observation",
            "independent_source_boost_per_source",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_block_score > self.min_consensus_score:
            raise ValueError("min_block_score must not exceed min_consensus_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyCandidateResearchConsensusObservation:
    candidate_id: str
    observation_id: str
    source_id: str
    observed_at: datetime
    candidate_probability: Decimal
    research_probability: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateResearchConsensusObservation:
            raise TypeError(
                "StrategyCandidateResearchConsensusObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResearchConsensusObservation:
            raise ValueError(
                "observation must be exactly "
                "StrategyCandidateResearchConsensusObservation",
            )
        for field_name in ("candidate_id", "observation_id", "source_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "candidate_probability",
            "research_probability",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class StrategyCandidateResearchConsensusPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateResearchConsensusPublicPayloadItem:
            raise TypeError(
                "StrategyCandidateResearchConsensusPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResearchConsensusPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "StrategyCandidateResearchConsensusPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class StrategyCandidateResearchConsensusGapPenaltyRow:
    candidate_id: str
    observation_count: Decimal
    independent_source_count: Decimal
    candidate_probability: Decimal
    research_consensus_probability: Decimal
    consensus_gap: Decimal
    average_confidence_score: Decimal
    consensus_gap_penalty: Decimal
    weak_quorum_penalty: Decimal
    independent_source_boost: Decimal
    consensus_score: Decimal
    penalty_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateResearchConsensusGapPenaltyRow:
            raise TypeError(
                "StrategyCandidateResearchConsensusGapPenaltyRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResearchConsensusGapPenaltyRow:
            raise ValueError(
                "row must be exactly StrategyCandidateResearchConsensusGapPenaltyRow",
            )
        _require_public_identifier("candidate_id", self.candidate_id)
        for field_name in ("observation_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "candidate_probability",
            "research_consensus_probability",
            "consensus_gap",
            "average_confidence_score",
            "consensus_gap_penalty",
            "weak_quorum_penalty",
            "independent_source_boost",
            "consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("penalty_status", self.penalty_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyCandidateResearchConsensusGapPenaltyReport:
    generated_at: datetime
    config_version: str
    penalty_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_consensus_gap: Decimal
    max_consensus_gap_penalty: Decimal
    max_weak_quorum_penalty: Decimal
    rows: tuple[StrategyCandidateResearchConsensusGapPenaltyRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[StrategyCandidateResearchConsensusPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateResearchConsensusGapPenaltyReport:
            raise TypeError(
                "StrategyCandidateResearchConsensusGapPenaltyReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResearchConsensusGapPenaltyReport:
            raise ValueError(
                "report must be exactly "
                "StrategyCandidateResearchConsensusGapPenaltyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_RESEARCH_CONSENSUS_GAP_PENALTY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("penalty_status", self.penalty_status)
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_consensus_gap",
            "max_consensus_gap_penalty",
            "max_weak_quorum_penalty",
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
            "StrategyCandidateResearchConsensusGapPenaltyReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_candidate_research_consensus_gap_penalty_v2_report(
    observations: Sequence[StrategyCandidateResearchConsensusObservation],
    *,
    generated_at: datetime,
    config: StrategyCandidateResearchConsensusGapPenaltyConfig | None = None,
    public_payload: Sequence[StrategyCandidateResearchConsensusPublicPayloadItem] = (),
) -> StrategyCandidateResearchConsensusGapPenaltyReport:
    """Build a local paper-only consensus-gap penalty report."""

    if config is None:
        config = StrategyCandidateResearchConsensusGapPenaltyConfig()
    if type(config) is not StrategyCandidateResearchConsensusGapPenaltyConfig:
        raise ValueError(
            "config must be a StrategyCandidateResearchConsensusGapPenaltyConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "penalty_status": _report_status(rows),
        "candidate_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "average_consensus_gap": _average(
            tuple(row.consensus_gap for row in rows),
        ),
        "max_consensus_gap_penalty": max(
            (row.consensus_gap_penalty for row in rows),
            default=_ZERO,
        ),
        "max_weak_quorum_penalty": max(
            (row.weak_quorum_penalty for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyCandidateResearchConsensusGapPenaltyReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[StrategyCandidateResearchConsensusObservation, ...],
    config: StrategyCandidateResearchConsensusGapPenaltyConfig,
) -> tuple[StrategyCandidateResearchConsensusGapPenaltyRow, ...]:
    grouped: dict[str, list[StrategyCandidateResearchConsensusObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.candidate_id, []).append(observation)
    rows = [
        _row_for_candidate(candidate_id, tuple(items), config)
        for candidate_id, items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_candidate(
    candidate_id: str,
    observations: tuple[StrategyCandidateResearchConsensusObservation, ...],
    config: StrategyCandidateResearchConsensusGapPenaltyConfig,
) -> StrategyCandidateResearchConsensusGapPenaltyRow:
    observation_count = _decimal_count(len(observations))
    independent_source_count = _decimal_count(
        len({observation.source_id for observation in observations}),
    )
    candidate_probability = _average(
        tuple(observation.candidate_probability for observation in observations),
    )
    research_consensus_probability = _average(
        tuple(observation.research_probability for observation in observations),
    )
    average_confidence = _average(
        tuple(observation.confidence_score for observation in observations),
    )
    consensus_gap = _abs_decimal(candidate_probability - research_consensus_probability)
    gap_penalty = _clamp_ratio(consensus_gap * config.consensus_gap_penalty_multiplier)
    missing_observation_count = max(config.min_observation_count - observation_count, _ZERO)
    weak_quorum_penalty = _clamp_ratio(
        missing_observation_count * config.weak_quorum_penalty_per_missing_observation,
    )
    independent_source_boost = _clamp_ratio(
        max(independent_source_count - _ONE, _ZERO)
        * config.independent_source_boost_per_source,
    )
    consensus_score = _clamp_ratio(
        average_confidence - gap_penalty - weak_quorum_penalty + independent_source_boost,
    )
    return StrategyCandidateResearchConsensusGapPenaltyRow(
        candidate_id=candidate_id,
        observation_count=observation_count,
        independent_source_count=independent_source_count,
        candidate_probability=candidate_probability,
        research_consensus_probability=research_consensus_probability,
        consensus_gap=consensus_gap,
        average_confidence_score=average_confidence,
        consensus_gap_penalty=gap_penalty,
        weak_quorum_penalty=weak_quorum_penalty,
        independent_source_boost=independent_source_boost,
        consensus_score=consensus_score,
        penalty_status=_row_status(consensus_score, config),
        reason_codes=_row_reason_codes(
            consensus_gap_penalty=gap_penalty,
            weak_quorum_penalty=weak_quorum_penalty,
            independent_source_boost=independent_source_boost,
            consensus_score=consensus_score,
            config=config,
        ),
    )


def _row_reason_codes(
    *,
    consensus_gap_penalty: Decimal,
    weak_quorum_penalty: Decimal,
    independent_source_boost: Decimal,
    consensus_score: Decimal,
    config: StrategyCandidateResearchConsensusGapPenaltyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if consensus_gap_penalty > _ZERO:
        reason_codes.append("research_consensus_gap_penalty")
    if weak_quorum_penalty > _ZERO:
        reason_codes.append("weak_quorum_penalty")
    if independent_source_boost > _ZERO:
        reason_codes.append("independent_source_boost")
    if consensus_score < config.min_block_score:
        reason_codes.append("consensus_score_blocked")
    elif consensus_score < config.min_consensus_score:
        reason_codes.append("consensus_score_watch")
    else:
        reason_codes.append("research_consensus_gap_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    consensus_score: Decimal,
    config: StrategyCandidateResearchConsensusGapPenaltyConfig,
) -> str:
    if consensus_score < config.min_block_score:
        return "blocked"
    if consensus_score < config.min_consensus_score:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[StrategyCandidateResearchConsensusGapPenaltyRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.penalty_status == "blocked" for row in rows):
        return "blocked"
    if any(row.penalty_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateResearchConsensusGapPenaltyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[StrategyCandidateResearchConsensusGapPenaltyRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.penalty_status == status))


def _validate_row_consistency(
    row: StrategyCandidateResearchConsensusGapPenaltyRow,
) -> None:
    if row.independent_source_count > row.observation_count:
        raise ValueError("independent_source_count must not exceed observation_count")
    if row.penalty_status == "pass" and "research_consensus_gap_pass" not in row.reason_codes:
        raise ValueError("pass rows must include research_consensus_gap_pass")
    if row.penalty_status == "watch" and "consensus_score_watch" not in row.reason_codes:
        raise ValueError("watch rows must include consensus_score_watch")
    if row.penalty_status == "blocked" and "consensus_score_blocked" not in row.reason_codes:
        raise ValueError("blocked rows must include consensus_score_blocked")


def _validate_report_consistency(
    report: StrategyCandidateResearchConsensusGapPenaltyReport,
) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.average_consensus_gap != _average(
        tuple(row.consensus_gap for row in report.rows),
    ):
        raise ValueError("average_consensus_gap must match rows")
    if report.max_consensus_gap_penalty != max(
        (row.consensus_gap_penalty for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_consensus_gap_penalty must match rows")
    if report.max_weak_quorum_penalty != max(
        (row.weak_quorum_penalty for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_weak_quorum_penalty must match rows")
    if report.penalty_status != _report_status(report.rows):
        raise ValueError("penalty_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[StrategyCandidateResearchConsensusObservation],
) -> tuple[StrategyCandidateResearchConsensusObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[StrategyCandidateResearchConsensusObservation] = []
    seen: set[str] = set()
    for observation in observations:
        if type(observation) is not StrategyCandidateResearchConsensusObservation:
            raise ValueError(
                "observations must contain "
                "StrategyCandidateResearchConsensusObservation",
            )
        key = f"{observation.candidate_id}\0{observation.observation_id}"
        if key in seen:
            raise ValueError("duplicate observation_id for candidate_id")
        seen.add(key)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.candidate_id,
                item.observed_at,
                item.observation_id,
                item.source_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[StrategyCandidateResearchConsensusGapPenaltyRow],
) -> tuple[StrategyCandidateResearchConsensusGapPenaltyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[StrategyCandidateResearchConsensusGapPenaltyRow] = []
    for row in rows:
        if type(row) is not StrategyCandidateResearchConsensusGapPenaltyRow:
            raise ValueError(
                "rows must contain StrategyCandidateResearchConsensusGapPenaltyRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.candidate_id))


def _normalize_public_payload(
    public_payload: Sequence[StrategyCandidateResearchConsensusPublicPayloadItem],
) -> tuple[StrategyCandidateResearchConsensusPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[StrategyCandidateResearchConsensusPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not StrategyCandidateResearchConsensusPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "StrategyCandidateResearchConsensusPublicPayloadItem",
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


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


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


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(abs(value))


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


def _report_values_without_digest(
    report: StrategyCandidateResearchConsensusGapPenaltyReport,
) -> dict[str, object]:
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_CONSENSUS_GAP_PENALTY_V2_CONFIG_VERSION",
    "StrategyCandidateResearchConsensusGapPenaltyConfig",
    "StrategyCandidateResearchConsensusGapPenaltyReport",
    "StrategyCandidateResearchConsensusGapPenaltyRow",
    "StrategyCandidateResearchConsensusObservation",
    "StrategyCandidateResearchConsensusPublicPayloadItem",
    "build_strategy_candidate_research_consensus_gap_penalty_v2_report",
)
