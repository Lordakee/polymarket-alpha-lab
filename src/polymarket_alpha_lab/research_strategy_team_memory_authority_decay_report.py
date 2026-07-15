"""Pure report-only team memory authority decay aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Iterable, Sequence, final


DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_CONFIG_VERSION = (
    "research-strategy-team-memory-authority-decay-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_STATUS_VALUES = frozenset(RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_STATUSES)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DECIMAL_PAYLOAD_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "network",
    "database",
    "order",
    "buy",
    "sell",
    "trade",
    "position",
    "recommend",
    "sizing",
    "live",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = _UNSAFE_PUBLIC_FRAGMENTS + ("://", "www.")
_REASON_CODE_SEQUENCE = (
    "authority_decay_score_watch",
    "authority_decay_score_block",
    "memory_age_watch",
    "memory_age_block",
    "stale_memory_ratio_watch",
    "stale_memory_ratio_block",
    "unresolved_conflict_ratio_watch",
    "unresolved_conflict_ratio_block",
    "team_confidence_score_watch",
    "team_confidence_score_block",
    "team_memory_authority_decay_watch",
    "team_memory_authority_decay_block",
    "team_memory_authority_decay_passed",
)
_CONFIG_PAYLOAD_KEYS = (
    "config_version",
    "watch_authority_decay_score",
    "block_authority_decay_score",
    "watch_memory_age_seconds",
    "block_memory_age_seconds",
    "watch_stale_memory_ratio",
    "block_stale_memory_ratio",
    "watch_unresolved_conflict_ratio",
    "block_unresolved_conflict_ratio",
    "min_pass_team_confidence_score",
    "min_watch_team_confidence_score",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "config",
    "status",
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_memory_age_seconds",
    "max_stale_memory_ratio",
    "max_authority_decay_score",
    "max_decay_pressure_score",
    "min_team_confidence_score",
    "total_evidence_reuse_count",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
_ROW_PAYLOAD_KEYS = (
    "authority_decay_rank",
    "team_sequence",
    "authority_family_sequence",
    "observed_at",
    "memory_age_seconds",
    "stale_memory_ratio",
    "authority_decay_score",
    "unresolved_conflict_ratio",
    "team_confidence_score",
    "evidence_reuse_count",
    "decay_pressure_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_memory_age_seconds",
    "max_stale_memory_ratio",
    "max_authority_decay_score",
    "max_decay_pressure_score",
    "min_team_confidence_score",
    "total_evidence_reuse_count",
)
_ROW_DECIMAL_PAYLOAD_FIELDS = (
    "authority_decay_rank",
    "team_sequence",
    "authority_family_sequence",
    "memory_age_seconds",
    "stale_memory_ratio",
    "authority_decay_score",
    "unresolved_conflict_ratio",
    "team_confidence_score",
    "evidence_reuse_count",
    "decay_pressure_score",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamMemoryAuthorityDecayConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_CONFIG_VERSION
    watch_authority_decay_score: Decimal = Decimal("0.350000")
    block_authority_decay_score: Decimal = Decimal("0.700000")
    watch_memory_age_seconds: Decimal = Decimal("86400.000000")
    block_memory_age_seconds: Decimal = Decimal("259200.000000")
    watch_stale_memory_ratio: Decimal = Decimal("0.400000")
    block_stale_memory_ratio: Decimal = Decimal("0.700000")
    watch_unresolved_conflict_ratio: Decimal = Decimal("0.300000")
    block_unresolved_conflict_ratio: Decimal = Decimal("0.600000")
    min_pass_team_confidence_score: Decimal = Decimal("0.750000")
    min_watch_team_confidence_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyTeamMemoryAuthorityDecayConfig, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyTeamMemoryAuthorityDecayConfig:
            raise TypeError(
                "ResearchStrategyTeamMemoryAuthorityDecayConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryAuthorityDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyTeamMemoryAuthorityDecayConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_authority_decay_score",
            "block_authority_decay_score",
            "watch_stale_memory_ratio",
            "block_stale_memory_ratio",
            "watch_unresolved_conflict_ratio",
            "block_unresolved_conflict_ratio",
            "min_pass_team_confidence_score",
            "min_watch_team_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_memory_age_seconds", "block_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "block_authority_decay_score",
            self.watch_authority_decay_score,
            self.block_authority_decay_score,
        )
        _require_threshold_pair(
            "block_memory_age_seconds",
            self.watch_memory_age_seconds,
            self.block_memory_age_seconds,
        )
        _require_threshold_pair(
            "block_stale_memory_ratio",
            self.watch_stale_memory_ratio,
            self.block_stale_memory_ratio,
        )
        _require_threshold_pair(
            "block_unresolved_conflict_ratio",
            self.watch_unresolved_conflict_ratio,
            self.block_unresolved_conflict_ratio,
        )
        if self.min_pass_team_confidence_score <= self.min_watch_team_confidence_score:
            raise ValueError(
                "min_pass_team_confidence_score must exceed "
                "min_watch_team_confidence_score",
            )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamMemoryAuthorityDecayObservation:
    team_key: str
    authority_family_key: str
    observed_at: datetime
    memory_age_seconds: Decimal
    stale_memory_ratio: Decimal
    authority_decay_score: Decimal
    unresolved_conflict_ratio: Decimal
    team_confidence_score: Decimal
    evidence_reuse_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(
            ResearchStrategyTeamMemoryAuthorityDecayObservation,
            cls,
        ).__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamMemoryAuthorityDecayObservation:
            raise TypeError(
                "ResearchStrategyTeamMemoryAuthorityDecayObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryAuthorityDecayObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategyTeamMemoryAuthorityDecayObservation",
            )
        for field_name in ("team_key", "authority_family_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "stale_memory_ratio",
            "authority_decay_score",
            "unresolved_conflict_ratio",
            "team_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_reuse_count",
            _require_nonnegative_whole_decimal(
                "evidence_reuse_count",
                self.evidence_reuse_count,
            ),
        )
        _require_hard_flags("observation", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamMemoryAuthorityDecayRow:
    authority_decay_rank: Decimal
    team_sequence: Decimal
    authority_family_sequence: Decimal
    observed_at: datetime
    memory_age_seconds: Decimal
    stale_memory_ratio: Decimal
    authority_decay_score: Decimal
    unresolved_conflict_ratio: Decimal
    team_confidence_score: Decimal
    evidence_reuse_count: Decimal
    decay_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyTeamMemoryAuthorityDecayRow, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyTeamMemoryAuthorityDecayRow:
            raise TypeError(
                "ResearchStrategyTeamMemoryAuthorityDecayRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryAuthorityDecayRow:
            raise ValueError(
                "row must be exactly ResearchStrategyTeamMemoryAuthorityDecayRow",
            )
        for field_name in (
            "authority_decay_rank",
            "team_sequence",
            "authority_family_sequence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "stale_memory_ratio",
            "authority_decay_score",
            "unresolved_conflict_ratio",
            "team_confidence_score",
            "decay_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_reuse_count",
            _require_nonnegative_whole_decimal(
                "evidence_reuse_count",
                self.evidence_reuse_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamMemoryAuthorityDecayReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_memory_age_seconds: Decimal
    max_stale_memory_ratio: Decimal
    max_authority_decay_score: Decimal
    max_decay_pressure_score: Decimal
    min_team_confidence_score: Decimal
    total_evidence_reuse_count: Decimal
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyTeamMemoryAuthorityDecayReport, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyTeamMemoryAuthorityDecayReport:
            raise TypeError(
                "ResearchStrategyTeamMemoryAuthorityDecayReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamMemoryAuthorityDecayReport:
            raise ValueError(
                "report must be exactly ResearchStrategyTeamMemoryAuthorityDecayReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if type(self.config) is not ResearchStrategyTeamMemoryAuthorityDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyTeamMemoryAuthorityDecayConfig",
            )
        _require_hard_flags("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_evidence_reuse_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        for field_name in (
            "max_stale_memory_ratio",
            "max_authority_decay_score",
            "max_decay_pressure_score",
            "min_team_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_team_memory_authority_decay_report_payload(self)


def build_research_strategy_team_memory_authority_decay_report(
    observations: Iterable[ResearchStrategyTeamMemoryAuthorityDecayObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig | None = None,
) -> ResearchStrategyTeamMemoryAuthorityDecayReport:
    """Build a deterministic local report-only team memory decay report."""

    if config is None:
        config = ResearchStrategyTeamMemoryAuthorityDecayConfig()
    if type(config) is not ResearchStrategyTeamMemoryAuthorityDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamMemoryAuthorityDecayConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "config": config,
        "status": _report_status(rows),
        "observation_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(_status_count(rows, PASS_STATUS)),
        "watch_count": _count_decimal(_status_count(rows, WATCH_STATUS)),
        "block_count": _count_decimal(_status_count(rows, BLOCK_STATUS)),
        "max_memory_age_seconds": _max_decimal(row.memory_age_seconds for row in rows),
        "max_stale_memory_ratio": _max_decimal(row.stale_memory_ratio for row in rows),
        "max_authority_decay_score": _max_decimal(
            row.authority_decay_score for row in rows
        ),
        "max_decay_pressure_score": _max_decimal(
            row.decay_pressure_score for row in rows
        ),
        "min_team_confidence_score": _min_decimal(
            row.team_confidence_score for row in rows
        ),
        "total_evidence_reuse_count": _sum_decimal(
            row.evidence_reuse_count for row in rows
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamMemoryAuthorityDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_team_memory_authority_decay_report_payload(
    report: ResearchStrategyTeamMemoryAuthorityDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamMemoryAuthorityDecayReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyTeamMemoryAuthorityDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_strategy_team_memory_authority_decay_public_payload(payload)
    return payload


def validate_research_strategy_team_memory_authority_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _validate_public_payload_schema(payload)


def research_strategy_team_memory_authority_decay_report_digest(
    report: ResearchStrategyTeamMemoryAuthorityDecayReport,
) -> str:
    if type(report) is not ResearchStrategyTeamMemoryAuthorityDecayReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamMemoryAuthorityDecayReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    research_strategy_team_memory_authority_decay_report_payload(report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def _build_rows(
    observations: tuple[ResearchStrategyTeamMemoryAuthorityDecayObservation, ...],
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig,
) -> tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]:
    team_sequences = _sequence_map(observation.team_key for observation in observations)
    authority_family_sequences = _sequence_map(
        observation.authority_family_key for observation in observations
    )
    rows = tuple(
        _row_from_observation(
            observation,
            config,
            team_sequence=team_sequences[observation.team_key],
            authority_family_sequence=authority_family_sequences[
                observation.authority_family_key
            ],
        )
        for observation in observations
    )
    return _canonicalize_row_sequences(_rank_rows(rows))


def _sequence_map(values: Iterable[str]) -> dict[str, Decimal]:
    return {
        value: _count_decimal(index)
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _canonicalize_row_sequences(
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...],
) -> tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]:
    sequence_maps: dict[str, dict[Decimal, Decimal]] = {
        "team_sequence": {},
        "authority_family_sequence": {},
    }
    normalized: list[ResearchStrategyTeamMemoryAuthorityDecayRow] = []
    for row in rows:
        replacements: dict[str, Decimal] = {}
        for field_name, sequence_map in sequence_maps.items():
            current = getattr(row, field_name)
            if current not in sequence_map:
                sequence_map[current] = _count_decimal(len(sequence_map) + 1)
            replacements[field_name] = sequence_map[current]
        normalized.append(replace(row, **replacements))
    return tuple(normalized)


def _rank_rows(
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...],
) -> tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]:
    ordered = tuple(sorted(rows, key=_row_sort_key))
    return tuple(
        replace(row, authority_decay_rank=_count_decimal(index))
        for index, row in enumerate(ordered, start=1)
    )


def _row_from_observation(
    observation: ResearchStrategyTeamMemoryAuthorityDecayObservation,
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig,
    *,
    team_sequence: Decimal,
    authority_family_sequence: Decimal,
) -> ResearchStrategyTeamMemoryAuthorityDecayRow:
    return _row_from_values(
        authority_decay_rank=_ONE,
        team_sequence=team_sequence,
        authority_family_sequence=authority_family_sequence,
        observed_at=observation.observed_at,
        memory_age_seconds=observation.memory_age_seconds,
        stale_memory_ratio=observation.stale_memory_ratio,
        authority_decay_score=observation.authority_decay_score,
        unresolved_conflict_ratio=observation.unresolved_conflict_ratio,
        team_confidence_score=observation.team_confidence_score,
        evidence_reuse_count=observation.evidence_reuse_count,
        config=config,
    )


def _row_from_values(
    *,
    authority_decay_rank: Decimal,
    team_sequence: Decimal,
    authority_family_sequence: Decimal,
    observed_at: datetime,
    memory_age_seconds: Decimal,
    stale_memory_ratio: Decimal,
    authority_decay_score: Decimal,
    unresolved_conflict_ratio: Decimal,
    team_confidence_score: Decimal,
    evidence_reuse_count: Decimal,
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig,
) -> ResearchStrategyTeamMemoryAuthorityDecayRow:
    authority_level = _threshold_level(
        authority_decay_score,
        config.watch_authority_decay_score,
        config.block_authority_decay_score,
    )
    memory_level = _threshold_level(
        memory_age_seconds,
        config.watch_memory_age_seconds,
        config.block_memory_age_seconds,
    )
    stale_level = _threshold_level(
        stale_memory_ratio,
        config.watch_stale_memory_ratio,
        config.block_stale_memory_ratio,
    )
    conflict_level = _threshold_level(
        unresolved_conflict_ratio,
        config.watch_unresolved_conflict_ratio,
        config.block_unresolved_conflict_ratio,
    )
    confidence_level = _confidence_level(team_confidence_score, config)
    levels = (
        authority_level,
        memory_level,
        stale_level,
        conflict_level,
        confidence_level,
    )
    status = _row_status(levels)
    return ResearchStrategyTeamMemoryAuthorityDecayRow(
        authority_decay_rank=authority_decay_rank,
        team_sequence=team_sequence,
        authority_family_sequence=authority_family_sequence,
        observed_at=observed_at,
        memory_age_seconds=memory_age_seconds,
        stale_memory_ratio=stale_memory_ratio,
        authority_decay_score=authority_decay_score,
        unresolved_conflict_ratio=unresolved_conflict_ratio,
        team_confidence_score=team_confidence_score,
        evidence_reuse_count=evidence_reuse_count,
        decay_pressure_score=_decay_pressure_score(
            memory_age_seconds=memory_age_seconds,
            stale_memory_ratio=stale_memory_ratio,
            authority_decay_score=authority_decay_score,
            unresolved_conflict_ratio=unresolved_conflict_ratio,
            team_confidence_score=team_confidence_score,
            config=config,
            status=status,
        ),
        status=status,
        reason_codes=_row_reason_codes(
            authority_level=authority_level,
            memory_level=memory_level,
            stale_level=stale_level,
            conflict_level=conflict_level,
            confidence_level=confidence_level,
            status=status,
        ),
    )


def _threshold_level(value: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str | None:
    if value >= block_threshold:
        return BLOCK_STATUS
    if value >= watch_threshold:
        return WATCH_STATUS
    return None


def _confidence_level(
    value: Decimal,
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig,
) -> str | None:
    if value < config.min_watch_team_confidence_score:
        return BLOCK_STATUS
    if value < config.min_pass_team_confidence_score:
        return WATCH_STATUS
    return None


def _row_status(levels: tuple[str | None, ...]) -> str:
    if any(level == BLOCK_STATUS for level in levels):
        return BLOCK_STATUS
    if any(level == WATCH_STATUS for level in levels):
        return WATCH_STATUS
    return PASS_STATUS


def _decay_pressure_score(
    *,
    memory_age_seconds: Decimal,
    stale_memory_ratio: Decimal,
    authority_decay_score: Decimal,
    unresolved_conflict_ratio: Decimal,
    team_confidence_score: Decimal,
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig,
    status: str,
) -> Decimal:
    if status == PASS_STATUS:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        pressure = _base_decay_pressure_score(
            stale_memory_ratio=stale_memory_ratio,
            authority_decay_score=authority_decay_score,
            unresolved_conflict_ratio=unresolved_conflict_ratio,
        )
        if status == BLOCK_STATUS:
            pressure += (
                (_ONE - team_confidence_score) * Decimal("0.325000")
                + _ratio(
                    memory_age_seconds,
                    config.block_memory_age_seconds,
                )
                * Decimal("0.200000")
            )
        return _require_ratio_decimal("decay_pressure_score", min(_ONE, pressure))


def _base_decay_pressure_score(
    *,
    stale_memory_ratio: Decimal,
    authority_decay_score: Decimal,
    unresolved_conflict_ratio: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (
            authority_decay_score * Decimal("0.400000")
            + stale_memory_ratio * Decimal("0.100000")
            + unresolved_conflict_ratio * Decimal("0.100000")
        )


def _row_reason_codes(
    *,
    authority_level: str | None,
    memory_level: str | None,
    stale_level: str | None,
    conflict_level: str | None,
    confidence_level: str | None,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_level_code(reason_codes, "authority_decay_score", authority_level)
    _append_level_code(reason_codes, "memory_age", memory_level)
    _append_level_code(reason_codes, "stale_memory_ratio", stale_level)
    _append_level_code(reason_codes, "unresolved_conflict_ratio", conflict_level)
    _append_level_code(reason_codes, "team_confidence_score", confidence_level)
    if status == BLOCK_STATUS:
        reason_codes.append("team_memory_authority_decay_block")
    elif status == WATCH_STATUS:
        reason_codes.append("team_memory_authority_decay_watch")
    else:
        reason_codes.append("team_memory_authority_decay_passed")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_level_code(
    reason_codes: list[str],
    prefix: str,
    level: str | None,
) -> None:
    if level is not None:
        reason_codes.append(f"{prefix}_{level}")


def _row_sort_key(
    row: ResearchStrategyTeamMemoryAuthorityDecayRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        _negative_decimal(row.decay_pressure_score),
        _negative_decimal(row.authority_decay_score),
        _negative_decimal(row.memory_age_seconds),
        _negative_decimal(row.stale_memory_ratio),
        _negative_decimal(row.unresolved_conflict_ratio),
        row.team_confidence_score,
        _negative_decimal(row.evidence_reuse_count),
        row.team_sequence,
        row.authority_family_sequence,
        row.observed_at,
    )


def _report_status(rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]) -> str:
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_memory_authority_decay_passed",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(row: ResearchStrategyTeamMemoryAuthorityDecayRow) -> None:
    terminal_codes = {
        PASS_STATUS: "team_memory_authority_decay_passed",
        WATCH_STATUS: "team_memory_authority_decay_watch",
        BLOCK_STATUS: "team_memory_authority_decay_block",
    }
    expected_terminal_code = terminal_codes[row.status]
    actual_terminal_codes = tuple(
        code for code in row.reason_codes if code in terminal_codes.values()
    )
    if actual_terminal_codes != (expected_terminal_code,):
        raise ValueError("reason_codes must match derived values")

    metric_codes = tuple(
        code for code in row.reason_codes if code not in terminal_codes.values()
    )
    if row.status == PASS_STATUS:
        expected_codes = ("team_memory_authority_decay_passed",)
        if row.decay_pressure_score != _ZERO:
            raise ValueError("pass rows must have zero decay_pressure_score")
    elif row.status == WATCH_STATUS:
        if not metric_codes or any(code.endswith(BLOCK_STATUS) for code in metric_codes):
            raise ValueError("reason_codes must match derived values")
        expected_pressure = _require_ratio_decimal(
            "decay_pressure_score",
            min(
                _ONE,
                _base_decay_pressure_score(
                    stale_memory_ratio=row.stale_memory_ratio,
                    authority_decay_score=row.authority_decay_score,
                    unresolved_conflict_ratio=row.unresolved_conflict_ratio,
                ),
            ),
        )
        if row.decay_pressure_score != expected_pressure:
            raise ValueError("decay_pressure_score must match derived values")
        expected_codes = row.reason_codes
    else:
        if not any(code.endswith(BLOCK_STATUS) for code in metric_codes):
            raise ValueError("reason_codes must match derived values")
        expected_codes = row.reason_codes
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes must match derived values")


def _validate_report_consistency(
    report: ResearchStrategyTeamMemoryAuthorityDecayReport,
) -> None:
    _require_canonical_utc_datetime("generated_at", report.generated_at)
    for row in report.rows:
        _require_canonical_utc_datetime("observed_at", row.observed_at)
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
    expected_rows = _rederive_rows(report.rows, report.config)
    for actual, expected in zip(report.rows, expected_rows, strict=True):
        if actual.authority_decay_rank != expected.authority_decay_rank:
            raise ValueError("authority_decay_rank must match derived values")
        if actual.team_sequence != expected.team_sequence:
            raise ValueError("team_sequence must match derived values")
        if actual.authority_family_sequence != expected.authority_family_sequence:
            raise ValueError("authority_family_sequence must match derived values")
        if actual.status != expected.status or actual.reason_codes != expected.reason_codes:
            raise ValueError("row status and reason_codes must match derived values")
        if actual.decay_pressure_score != expected.decay_pressure_score:
            raise ValueError("decay_pressure_score must match derived values")
        if actual != expected:
            raise ValueError("rows must match derived values")
    _validate_consecutive_sequences(report.rows, "team_sequence")
    _validate_consecutive_sequences(report.rows, "authority_family_sequence")
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    for field_name, status in (
        ("pass_count", PASS_STATUS),
        ("watch_count", WATCH_STATUS),
        ("block_count", BLOCK_STATUS),
    ):
        if getattr(report, field_name) != _count_decimal(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if _sum_decimal(
        (report.pass_count, report.watch_count, report.block_count),
    ) != report.observation_count:
        raise ValueError("status counts must match observation_count")
    if report.max_memory_age_seconds != _max_decimal(
        row.memory_age_seconds for row in report.rows
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_stale_memory_ratio != _max_decimal(
        row.stale_memory_ratio for row in report.rows
    ):
        raise ValueError("max_stale_memory_ratio must match rows")
    if report.max_authority_decay_score != _max_decimal(
        row.authority_decay_score for row in report.rows
    ):
        raise ValueError("max_authority_decay_score must match rows")
    if report.max_decay_pressure_score != _max_decimal(
        row.decay_pressure_score for row in report.rows
    ):
        raise ValueError("max_decay_pressure_score must match rows")
    if report.min_team_confidence_score != _min_decimal(
        row.team_confidence_score for row in report.rows
    ):
        raise ValueError("min_team_confidence_score must match rows")
    if report.total_evidence_reuse_count != _sum_decimal(
        row.evidence_reuse_count for row in report.rows
    ):
        raise ValueError("total_evidence_reuse_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _rederive_rows(
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...],
    config: ResearchStrategyTeamMemoryAuthorityDecayConfig,
) -> tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]:
    derived = tuple(
        _row_from_values(
            authority_decay_rank=_ONE,
            team_sequence=row.team_sequence,
            authority_family_sequence=row.authority_family_sequence,
            observed_at=row.observed_at,
            memory_age_seconds=row.memory_age_seconds,
            stale_memory_ratio=row.stale_memory_ratio,
            authority_decay_score=row.authority_decay_score,
            unresolved_conflict_ratio=row.unresolved_conflict_ratio,
            team_confidence_score=row.team_confidence_score,
            evidence_reuse_count=row.evidence_reuse_count,
            config=config,
        )
        for row in rows
    )
    return _canonicalize_row_sequences(
        _rank_rows(_canonicalize_row_sequences(derived)),
    )


def _validate_consecutive_sequences(
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...],
    field_name: str,
) -> None:
    values = tuple(sorted({getattr(row, field_name) for row in rows}))
    expected = tuple(_count_decimal(index) for index in range(1, len(values) + 1))
    if values != expected:
        raise ValueError(f"{field_name} values must be consecutive")


def _normalize_observations(
    observations: Iterable[ResearchStrategyTeamMemoryAuthorityDecayObservation],
) -> tuple[ResearchStrategyTeamMemoryAuthorityDecayObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchStrategyTeamMemoryAuthorityDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyTeamMemoryAuthorityDecayObservation",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyTeamMemoryAuthorityDecayRow],
) -> tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyTeamMemoryAuthorityDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamMemoryAuthorityDecayRow",
            )
    return rows


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
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize(raw)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        integral_value = raw.to_integral_value()
    if raw != integral_value:
        raise ValueError(f"{field_name} must be whole")
    return _quantize(raw)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw)


def _require_threshold_pair(
    block_field_name: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed the watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if isinstance(value, datetime) and type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    normalized = value.astimezone(UTC)
    return datetime(
        normalized.year,
        normalized.month,
        normalized.day,
        normalized.hour,
        normalized.minute,
        normalized.second,
        normalized.microsecond,
        tzinfo=UTC,
    )


def _require_canonical_utc_datetime(field_name: str, value: object) -> datetime:
    normalized = _as_utc(field_name, value)
    if value != normalized or value.tzinfo is not UTC or value.fold != normalized.fold:
        raise ValueError(f"{field_name} must be canonical UTC datetime")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return min(_ONE, _quantize(numerator / denominator))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total += value
        return _quantize(total)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(max(tuple(values), default=_ZERO))


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(min(tuple(values), default=_ZERO))


def _status_count(
    rows: tuple[ResearchStrategyTeamMemoryAuthorityDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_rank(status: str) -> int:
    if status == BLOCK_STATUS:
        return 0
    if status == WATCH_STATUS:
        return 1
    return 2


def _negative_decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return -value


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _report_values_without_digest(
    report: ResearchStrategyTeamMemoryAuthorityDecayReport,
) -> dict[str, object]:
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: object) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not be signed zero")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float) or type(value) is int:
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


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys("public payload", payload, _REPORT_PAYLOAD_KEYS)
    generated_at = _require_datetime_payload_string(
        "generated_at",
        payload["generated_at"],
    )
    config_version = _require_public_identifier(
        "config_version",
        payload["config_version"],
    )
    if (
        config_version
        != DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    config = _validate_public_config_payload(payload["config"])
    if config_version != config.config_version:
        raise ValueError("config_version must match config")
    decimal_values: dict[str, Decimal] = {}
    for field_name in _REPORT_DECIMAL_PAYLOAD_FIELDS:
        parsed = _require_decimal_payload_string(field_name, payload[field_name])
        if field_name in {
            "max_stale_memory_ratio",
            "max_authority_decay_score",
            "max_decay_pressure_score",
            "min_team_confidence_score",
        }:
            decimal_values[field_name] = _require_ratio_decimal(field_name, parsed)
        elif field_name in {
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_evidence_reuse_count",
        }:
            decimal_values[field_name] = _require_nonnegative_whole_decimal(
                field_name,
                parsed,
            )
        else:
            decimal_values[field_name] = _require_nonnegative_decimal(
                field_name,
                parsed,
            )
    reason_codes = _require_reason_codes_payload(
        "reason_codes",
        payload["reason_codes"],
    )
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(
        _validate_public_row_payload(row)
        for row in payload["rows"]
    )
    ResearchStrategyTeamMemoryAuthorityDecayReport(
        generated_at=generated_at,
        config_version=config_version,
        config=config,
        status=_require_status("status", payload["status"]),
        observation_count=decimal_values["observation_count"],
        pass_count=decimal_values["pass_count"],
        watch_count=decimal_values["watch_count"],
        block_count=decimal_values["block_count"],
        max_memory_age_seconds=decimal_values["max_memory_age_seconds"],
        max_stale_memory_ratio=decimal_values["max_stale_memory_ratio"],
        max_authority_decay_score=decimal_values["max_authority_decay_score"],
        max_decay_pressure_score=decimal_values["max_decay_pressure_score"],
        min_team_confidence_score=decimal_values["min_team_confidence_score"],
        total_evidence_reuse_count=decimal_values["total_evidence_reuse_count"],
        rows=rows,
        reason_codes=reason_codes,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        derived_validation_digest=_require_sha256_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
    )


def _validate_public_config_payload(
    value: object,
) -> ResearchStrategyTeamMemoryAuthorityDecayConfig:
    if type(value) is not dict:
        raise ValueError("config must be a JSON object")
    _require_payload_keys("config payload", value, _CONFIG_PAYLOAD_KEYS)
    return ResearchStrategyTeamMemoryAuthorityDecayConfig(
        config_version=_require_public_identifier(
            "config_version",
            value["config_version"],
        ),
        watch_authority_decay_score=_require_decimal_payload_string(
            "watch_authority_decay_score",
            value["watch_authority_decay_score"],
        ),
        block_authority_decay_score=_require_decimal_payload_string(
            "block_authority_decay_score",
            value["block_authority_decay_score"],
        ),
        watch_memory_age_seconds=_require_decimal_payload_string(
            "watch_memory_age_seconds",
            value["watch_memory_age_seconds"],
        ),
        block_memory_age_seconds=_require_decimal_payload_string(
            "block_memory_age_seconds",
            value["block_memory_age_seconds"],
        ),
        watch_stale_memory_ratio=_require_decimal_payload_string(
            "watch_stale_memory_ratio",
            value["watch_stale_memory_ratio"],
        ),
        block_stale_memory_ratio=_require_decimal_payload_string(
            "block_stale_memory_ratio",
            value["block_stale_memory_ratio"],
        ),
        watch_unresolved_conflict_ratio=_require_decimal_payload_string(
            "watch_unresolved_conflict_ratio",
            value["watch_unresolved_conflict_ratio"],
        ),
        block_unresolved_conflict_ratio=_require_decimal_payload_string(
            "block_unresolved_conflict_ratio",
            value["block_unresolved_conflict_ratio"],
        ),
        min_pass_team_confidence_score=_require_decimal_payload_string(
            "min_pass_team_confidence_score",
            value["min_pass_team_confidence_score"],
        ),
        min_watch_team_confidence_score=_require_decimal_payload_string(
            "min_watch_team_confidence_score",
            value["min_watch_team_confidence_score"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _validate_public_row_payload(
    value: object,
) -> ResearchStrategyTeamMemoryAuthorityDecayRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys("row payload", value, _ROW_PAYLOAD_KEYS)
    observed_at = _require_datetime_payload_string("observed_at", value["observed_at"])
    decimal_values: dict[str, Decimal] = {}
    for field_name in _ROW_DECIMAL_PAYLOAD_FIELDS:
        parsed = _require_decimal_payload_string(field_name, value[field_name])
        if field_name in {
            "authority_decay_rank",
            "team_sequence",
            "authority_family_sequence",
        }:
            decimal_values[field_name] = _require_positive_whole_decimal(
                field_name,
                parsed,
            )
        elif field_name == "evidence_reuse_count":
            decimal_values[field_name] = _require_nonnegative_whole_decimal(
                field_name,
                parsed,
            )
        elif field_name == "memory_age_seconds":
            decimal_values[field_name] = _require_nonnegative_decimal(
                field_name,
                parsed,
            )
        else:
            decimal_values[field_name] = _require_ratio_decimal(field_name, parsed)
    status = _require_status("status", value["status"])
    reason_codes = _require_reason_codes_payload(
        "row reason_codes",
        value["reason_codes"],
    )
    return ResearchStrategyTeamMemoryAuthorityDecayRow(
        authority_decay_rank=decimal_values["authority_decay_rank"],
        team_sequence=decimal_values["team_sequence"],
        authority_family_sequence=decimal_values["authority_family_sequence"],
        observed_at=observed_at,
        memory_age_seconds=decimal_values["memory_age_seconds"],
        stale_memory_ratio=decimal_values["stale_memory_ratio"],
        authority_decay_score=decimal_values["authority_decay_score"],
        unresolved_conflict_ratio=decimal_values["unresolved_conflict_ratio"],
        team_confidence_score=decimal_values["team_confidence_score"],
        evidence_reuse_count=decimal_values["evidence_reuse_count"],
        decay_pressure_score=decimal_values["decay_pressure_score"],
        status=status,
        reason_codes=reason_codes,
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_reason_codes_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(value)
    if tuple(value) != normalized:
        raise ValueError(f"{field_name} must be normalized")
    return normalized


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    actual_keys = tuple(payload)
    keys = set(actual_keys)
    expected = set(expected_keys)
    if keys != expected:
        unknown = keys - expected
        missing = expected - keys
        if unknown:
            raise ValueError(f"{label} has unsupported field: {sorted(unknown)[0]}")
        raise ValueError(f"{label} is missing field: {sorted(missing)[0]}")
    if actual_keys != expected_keys:
        raise ValueError(f"{label} fields must use canonical order")


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not _DECIMAL_PAYLOAD_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    parsed = Decimal(value)
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if str(_quantize(parsed)) != value:
        raise ValueError(f"{field_name} must be quantized to six decimals")
    return parsed

def _reject_public_numerics(value: object) -> None:
    if type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if allow_json_containers or value is None or type(value) in (bool, Decimal, datetime):
        return
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_key(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public field in {label}: {value}")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_STATUSES",
    "ResearchStrategyTeamMemoryAuthorityDecayConfig",
    "ResearchStrategyTeamMemoryAuthorityDecayObservation",
    "ResearchStrategyTeamMemoryAuthorityDecayRow",
    "ResearchStrategyTeamMemoryAuthorityDecayReport",
    "build_research_strategy_team_memory_authority_decay_report",
    "research_strategy_team_memory_authority_decay_report_payload",
    "research_strategy_team_memory_authority_decay_report_digest",
    "validate_research_strategy_team_memory_authority_decay_public_payload",
)
