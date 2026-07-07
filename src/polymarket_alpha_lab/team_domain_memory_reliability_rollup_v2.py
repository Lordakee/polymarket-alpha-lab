"""Phase 1 readonly team-domain memory reliability rollup."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_TEAM_DOMAIN_MEMORY_RELIABILITY_ROLLUP_V2_CONFIG_VERSION = (
    "team-domain-memory-reliability-rollup-v2"
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_ROW_STATUSES = ("block", "watch", "pass")
_REPORT_STATUSES = ("empty", "block", "watch", "pass")
_ROW_REASON_CODE_SEQUENCE = (
    "domain_memory_reliability_pass",
    "domain_memory_reliability_watch",
    "domain_memory_reliability_block",
    "memory_current",
    "stale_memory",
    "resolved_forecast_depth_full",
    "resolved_forecast_depth_watch",
    "resolved_forecast_depth_thin",
    "calibration_coverage_full",
    "calibration_coverage_watch",
    "calibration_coverage_low",
    "brier_quality_strong",
    "brier_quality_watch",
    "brier_quality_weak",
    "source_reliability_strong",
    "source_reliability_watch",
    "source_reliability_low",
    "low_reliability_score",
)
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

__all__ = (
    "DEFAULT_TEAM_DOMAIN_MEMORY_RELIABILITY_ROLLUP_V2_CONFIG_VERSION",
    "TeamDomainMemoryReliabilityRollupV2Config",
    "TeamDomainMemoryReliabilityRollupV2Input",
    "TeamDomainMemoryReliabilityRollupV2ReasonCodeCount",
    "TeamDomainMemoryReliabilityRollupV2Row",
    "TeamDomainMemoryReliabilityRollupV2Report",
    "build_team_domain_memory_reliability_rollup_v2",
    "team_domain_memory_reliability_rollup_v2_payload",
)


@dataclass(frozen=True)
class TeamDomainMemoryReliabilityRollupV2Config:
    config_version: str = DEFAULT_TEAM_DOMAIN_MEMORY_RELIABILITY_ROLLUP_V2_CONFIG_VERSION
    stale_memory_after_seconds: Decimal = Decimal("2592000.000000")
    full_resolved_forecast_count: Decimal = Decimal("20.000000")
    max_brier_score: Decimal = Decimal("0.250000")
    source_reliability_weight: Decimal = Decimal("0.450000")
    brier_quality_weight: Decimal = Decimal("0.300000")
    calibration_coverage_weight: Decimal = Decimal("0.150000")
    forecast_depth_weight: Decimal = Decimal("0.100000")
    stale_memory_penalty: Decimal = Decimal("0.150000")
    pass_reliability_floor: Decimal = Decimal("0.700000")
    watch_reliability_floor: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainMemoryReliabilityRollupV2Config:
            raise ValueError(
                "config must be exactly TeamDomainMemoryReliabilityRollupV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "stale_memory_after_seconds",
            "full_resolved_forecast_count",
            "max_brier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability_weight",
            "brier_quality_weight",
            "calibration_coverage_weight",
            "forecast_depth_weight",
            "stale_memory_penalty",
            "pass_reliability_floor",
            "watch_reliability_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamDomainMemoryReliabilityRollupV2Input:
    team_id: str
    domain: str
    resolved_forecast_count: Decimal
    calibrated_forecast_count: Decimal
    brier_score: Decimal
    source_reliability_score: Decimal
    latest_memory_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainMemoryReliabilityRollupV2Input:
            raise ValueError(
                "memory must be exactly TeamDomainMemoryReliabilityRollupV2Input",
            )
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain", self.domain)
        object.__setattr__(
            self,
            "resolved_forecast_count",
            _require_nonnegative_count_decimal(
                "resolved_forecast_count",
                self.resolved_forecast_count,
            ),
        )
        object.__setattr__(
            self,
            "calibrated_forecast_count",
            _require_nonnegative_count_decimal(
                "calibrated_forecast_count",
                self.calibrated_forecast_count,
            ),
        )
        if self.calibrated_forecast_count > self.resolved_forecast_count:
            raise ValueError(
                "calibrated_forecast_count must not exceed resolved_forecast_count",
            )
        object.__setattr__(
            self,
            "brier_score",
            _require_ratio_decimal("brier_score", self.brier_score),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _require_ratio_decimal(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "latest_memory_at",
            _as_utc("latest_memory_at", self.latest_memory_at),
        )
        _require_hard_flags("memory", self)
        _reject_unsafe_public_payload("memory", self)


@dataclass(frozen=True)
class TeamDomainMemoryReliabilityRollupV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainMemoryReliabilityRollupV2ReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "TeamDomainMemoryReliabilityRollupV2ReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class TeamDomainMemoryReliabilityRollupV2Row:
    team_id: str
    domain: str
    resolved_forecast_count: Decimal
    calibrated_forecast_count: Decimal
    brier_score: Decimal
    source_reliability_score: Decimal
    latest_memory_at: datetime
    memory_age_seconds: Decimal
    reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainMemoryReliabilityRollupV2Row:
            raise ValueError("row must be exactly TeamDomainMemoryReliabilityRollupV2Row")
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain", self.domain)
        for field_name in ("resolved_forecast_count", "calibrated_forecast_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.calibrated_forecast_count > self.resolved_forecast_count:
            raise ValueError(
                "calibrated_forecast_count must not exceed resolved_forecast_count",
            )
        for field_name in (
            "brier_score",
            "source_reliability_score",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_at",
            _as_utc("latest_memory_at", self.latest_memory_at),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamDomainMemoryReliabilityRollupV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    low_reliability_count: Decimal
    min_reliability_score: Decimal
    reason_code_counts: tuple[TeamDomainMemoryReliabilityRollupV2ReasonCodeCount, ...]
    rows: tuple[TeamDomainMemoryReliabilityRollupV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainMemoryReliabilityRollupV2Report:
            raise ValueError(
                "report must be exactly TeamDomainMemoryReliabilityRollupV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "low_reliability_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reliability_score",
            _require_ratio_decimal(
                "min_reliability_score",
                self.min_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_team_domain_memory_reliability_rollup_v2(
    memories: Sequence[TeamDomainMemoryReliabilityRollupV2Input],
    *,
    generated_at: datetime,
    config: TeamDomainMemoryReliabilityRollupV2Config | None = None,
) -> TeamDomainMemoryReliabilityRollupV2Report:
    if config is None:
        config = TeamDomainMemoryReliabilityRollupV2Config()
    if type(config) is not TeamDomainMemoryReliabilityRollupV2Config:
        raise ValueError(
            "config must be a TeamDomainMemoryReliabilityRollupV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_memories = _normalize_memories(memories)
    rows = tuple(
        sorted(
            (
                _row_for_memory(
                    memory,
                    generated_at=generated_at,
                    config=config,
                )
                for memory in normalized_memories
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "team_domain_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "stale_memory_count": _decimal_count(_reason_count(rows, "stale_memory")),
        "low_reliability_count": _decimal_count(
            _reason_count(rows, "low_reliability_score"),
        ),
        "min_reliability_score": _min_reliability_score(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamDomainMemoryReliabilityRollupV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_domain_memory_reliability_rollup_v2_payload(
    report: TeamDomainMemoryReliabilityRollupV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamDomainMemoryReliabilityRollupV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a TeamDomainMemoryReliabilityRollupV2Report or payload",
    )


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


def _row_for_memory(
    memory: TeamDomainMemoryReliabilityRollupV2Input,
    *,
    generated_at: datetime,
    config: TeamDomainMemoryReliabilityRollupV2Config,
) -> TeamDomainMemoryReliabilityRollupV2Row:
    memory_age_seconds = _age_seconds(memory.latest_memory_at, generated_at)
    stale = memory_age_seconds > config.stale_memory_after_seconds
    reliability_score = _reliability_score(memory, stale=stale, config=config)
    status = _row_status(reliability_score, stale=stale, config=config)
    return TeamDomainMemoryReliabilityRollupV2Row(
        team_id=memory.team_id,
        domain=memory.domain,
        resolved_forecast_count=memory.resolved_forecast_count,
        calibrated_forecast_count=memory.calibrated_forecast_count,
        brier_score=memory.brier_score,
        source_reliability_score=memory.source_reliability_score,
        latest_memory_at=memory.latest_memory_at,
        memory_age_seconds=memory_age_seconds,
        reliability_score=reliability_score,
        status=status,
        reason_codes=_row_reason_codes(
            memory,
            stale=stale,
            reliability_score=reliability_score,
            status=status,
            config=config,
        ),
    )


def _reliability_score(
    memory: TeamDomainMemoryReliabilityRollupV2Input,
    *,
    stale: bool,
    config: TeamDomainMemoryReliabilityRollupV2Config,
) -> Decimal:
    score = (
        memory.source_reliability_score * config.source_reliability_weight
        + _brier_quality_score(memory.brier_score, config) * config.brier_quality_weight
        + _calibration_coverage_score(memory) * config.calibration_coverage_weight
        + _forecast_depth_score(memory.resolved_forecast_count, config)
        * config.forecast_depth_weight
    )
    if stale:
        score -= config.stale_memory_penalty
    return _clamp_ratio(score)


def _brier_quality_score(
    brier_score: Decimal,
    config: TeamDomainMemoryReliabilityRollupV2Config,
) -> Decimal:
    return _clamp_ratio(_ONE - brier_score / config.max_brier_score)


def _calibration_coverage_score(
    memory: TeamDomainMemoryReliabilityRollupV2Input,
) -> Decimal:
    if memory.resolved_forecast_count == _ZERO:
        return _ZERO
    return _clamp_ratio(
        memory.calibrated_forecast_count / memory.resolved_forecast_count,
    )


def _forecast_depth_score(
    resolved_forecast_count: Decimal,
    config: TeamDomainMemoryReliabilityRollupV2Config,
) -> Decimal:
    return _clamp_ratio(resolved_forecast_count / config.full_resolved_forecast_count)


def _row_status(
    reliability_score: Decimal,
    *,
    stale: bool,
    config: TeamDomainMemoryReliabilityRollupV2Config,
) -> str:
    if not stale and reliability_score >= config.pass_reliability_floor:
        return "pass"
    if reliability_score >= config.watch_reliability_floor:
        return "watch"
    return "block"


def _row_reason_codes(
    memory: TeamDomainMemoryReliabilityRollupV2Input,
    *,
    stale: bool,
    reliability_score: Decimal,
    status: str,
    config: TeamDomainMemoryReliabilityRollupV2Config,
) -> tuple[str, ...]:
    codes = [
        f"domain_memory_reliability_{status}",
        "stale_memory" if stale else "memory_current",
        _depth_reason(_forecast_depth_score(memory.resolved_forecast_count, config)),
        _coverage_reason(_calibration_coverage_score(memory)),
        _brier_quality_reason(_brier_quality_score(memory.brier_score, config)),
        _source_reliability_reason(memory.source_reliability_score),
    ]
    if reliability_score < config.watch_reliability_floor:
        codes.append("low_reliability_score")
    return _normalize_reason_codes(tuple(codes))


def _depth_reason(value: Decimal) -> str:
    if value >= _ONE:
        return "resolved_forecast_depth_full"
    if value >= Decimal("0.500000"):
        return "resolved_forecast_depth_watch"
    return "resolved_forecast_depth_thin"


def _coverage_reason(value: Decimal) -> str:
    if value >= Decimal("0.800000"):
        return "calibration_coverage_full"
    if value >= Decimal("0.500000"):
        return "calibration_coverage_watch"
    return "calibration_coverage_low"


def _brier_quality_reason(value: Decimal) -> str:
    if value >= Decimal("0.800000"):
        return "brier_quality_strong"
    if value >= Decimal("0.500000"):
        return "brier_quality_watch"
    return "brier_quality_weak"


def _source_reliability_reason(value: Decimal) -> str:
    if value >= Decimal("0.800000"):
        return "source_reliability_strong"
    if value >= Decimal("0.500000"):
        return "source_reliability_watch"
    return "source_reliability_low"


def _report_status(rows: tuple[TeamDomainMemoryReliabilityRollupV2Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: TeamDomainMemoryReliabilityRollupV2Row,
) -> tuple[int, Decimal, str, str]:
    return (
        _ROW_STATUSES.index(row.status),
        row.reliability_score,
        row.team_id,
        row.domain,
    )


def _status_count(
    rows: tuple[TeamDomainMemoryReliabilityRollupV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[TeamDomainMemoryReliabilityRollupV2Row, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _reason_code_counts(
    rows: tuple[TeamDomainMemoryReliabilityRollupV2Row, ...],
) -> tuple[TeamDomainMemoryReliabilityRollupV2ReasonCodeCount, ...]:
    return tuple(
        TeamDomainMemoryReliabilityRollupV2ReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(_reason_count(rows, reason_code)),
        )
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > 0
    )


def _min_reliability_score(
    rows: tuple[TeamDomainMemoryReliabilityRollupV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.reliability_score for row in rows)


def _normalize_memories(
    memories: Sequence[TeamDomainMemoryReliabilityRollupV2Input],
) -> tuple[TeamDomainMemoryReliabilityRollupV2Input, ...]:
    if isinstance(memories, (str, bytes)) or not isinstance(memories, Sequence):
        raise ValueError("memories must be a sequence")
    normalized: list[TeamDomainMemoryReliabilityRollupV2Input] = []
    seen_keys: set[tuple[str, str]] = set()
    for memory in memories:
        if type(memory) is not TeamDomainMemoryReliabilityRollupV2Input:
            raise ValueError(
                "memories must contain TeamDomainMemoryReliabilityRollupV2Input",
            )
        _require_hard_flags("memory", memory)
        key = (memory.team_id, memory.domain)
        if key in seen_keys:
            raise ValueError("duplicate team/domain memory")
        seen_keys.add(key)
        normalized.append(memory)
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.domain)))


def _normalize_rows(
    rows: Sequence[TeamDomainMemoryReliabilityRollupV2Row],
) -> tuple[TeamDomainMemoryReliabilityRollupV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamDomainMemoryReliabilityRollupV2Row] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamDomainMemoryReliabilityRollupV2Row:
            raise ValueError("rows must contain TeamDomainMemoryReliabilityRollupV2Row")
        _require_hard_flags("row", row)
        key = (row.team_id, row.domain)
        if key in seen_keys:
            raise ValueError("duplicate team/domain row")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: Sequence[TeamDomainMemoryReliabilityRollupV2ReasonCodeCount],
) -> tuple[TeamDomainMemoryReliabilityRollupV2ReasonCodeCount, ...]:
    if (
        isinstance(reason_code_counts, (str, bytes))
        or not isinstance(reason_code_counts, Sequence)
    ):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[TeamDomainMemoryReliabilityRollupV2ReasonCodeCount] = []
    seen_codes: set[str] = set()
    for item in reason_code_counts:
        if type(item) is not TeamDomainMemoryReliabilityRollupV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamDomainMemoryReliabilityRollupV2ReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_codes:
            raise ValueError("duplicate reason_code_counts reason_code")
        seen_codes.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _ROW_REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in normalized)


def _validate_config(config: TeamDomainMemoryReliabilityRollupV2Config) -> None:
    weight_total = _quantize(
        config.source_reliability_weight
        + config.brier_quality_weight
        + config.calibration_coverage_weight
        + config.forecast_depth_weight,
    )
    if weight_total != _ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_reliability_floor > config.pass_reliability_floor:
        raise ValueError("watch_reliability_floor must not exceed pass_reliability_floor")


def _validate_row(row: TeamDomainMemoryReliabilityRollupV2Row) -> None:
    expected_status_code = f"domain_memory_reliability_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("row status must match reason_codes")
    if "stale_memory" in row.reason_codes and "memory_current" in row.reason_codes:
        raise ValueError("row cannot be stale and current")
    if row.status == "block" and "low_reliability_score" not in row.reason_codes:
        raise ValueError("block rows must include low_reliability_score")


def _validate_report(report: TeamDomainMemoryReliabilityRollupV2Report) -> None:
    rows = report.rows
    if report.team_domain_count != _decimal_count(len(rows)):
        raise ValueError("team_domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.stale_memory_count != _decimal_count(_reason_count(rows, "stale_memory")):
        raise ValueError("stale_memory_count must match rows")
    if report.low_reliability_count != _decimal_count(
        _reason_count(rows, "low_reliability_score"),
    ):
        raise ValueError("low_reliability_count must match rows")
    if report.min_reliability_score != _min_reliability_score(rows):
        raise ValueError("min_reliability_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_for_json_payload(payload):
        raise ValueError("derived_validation_digest must match report contents")


def _report_values_without_digest(
    report: TeamDomainMemoryReliabilityRollupV2Report,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_for_json_payload(_json_ready(values))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value >= generated_at:
        return _ZERO
    delta = generated_at - value
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000")
    )
    return _quantize(seconds)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _ROW_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_row_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known row status")
    return value


def _require_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known report status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized.quantize(_COUNT_QUANT) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key, path or label)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
