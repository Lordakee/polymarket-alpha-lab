"""Pure in-memory research packet source reliability playbook."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json


DEFAULT_RESEARCH_PACKET_SOURCE_RELIABILITY_PLAYBOOK_CONFIG_VERSION = (
    "research-packet-source-reliability-playbook-v2"
)

PASSED_REASON = "source_reliability_playbook_passed"
EMPTY_REASON = "source_reliability_playbook_empty"
LOW_RELIABILITY_REASON = "source_reliability_playbook_low_reliability"
STALE_SOURCE_FAMILY_REASON = "source_reliability_playbook_stale_source_family"
LOW_OFFICIALNESS_REASON = "source_reliability_playbook_low_officialness"
LOW_INDEPENDENCE_REASON = "source_reliability_playbook_low_independence"
SLOW_SOURCE_FAMILY_REASON = "source_reliability_playbook_slow_source_family"
HIGH_CONTRADICTION_RATE_REASON = (
    "source_reliability_playbook_high_contradiction_rate"
)
LOW_RESOLUTION_USEFULNESS_REASON = (
    "source_reliability_playbook_low_resolution_usefulness"
)

REASON_CODES = (
    PASSED_REASON,
    EMPTY_REASON,
    LOW_RELIABILITY_REASON,
    STALE_SOURCE_FAMILY_REASON,
    LOW_OFFICIALNESS_REASON,
    LOW_INDEPENDENCE_REASON,
    SLOW_SOURCE_FAMILY_REASON,
    HIGH_CONTRADICTION_RATE_REASON,
    LOW_RESOLUTION_USEFULNESS_REASON,
)
REPORT_REASON_SEQUENCE = (
    LOW_RELIABILITY_REASON,
    STALE_SOURCE_FAMILY_REASON,
    LOW_OFFICIALNESS_REASON,
    LOW_INDEPENDENCE_REASON,
    SLOW_SOURCE_FAMILY_REASON,
    HIGH_CONTRADICTION_RATE_REASON,
    LOW_RESOLUTION_USEFULNESS_REASON,
)
PLAYBOOK_STATUSES = ("pass", "watch")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(chr(code) for code in codes)
    for codes in (
        (108, 105, 118, 101),
        (97, 117, 116, 104),
        (119, 97, 108, 108, 101, 116),
        (111, 114, 100, 101, 114),
        (110, 101, 116, 119, 111, 114, 107),
        (100, 97, 116, 97, 98, 97, 115, 101),
        (112, 101, 114, 115, 105, 115, 116),
        (115, 105, 103, 110, 105, 110, 103),
        (109, 117, 116, 97, 116, 105, 111, 110),
        (98, 117, 121),
        (115, 101, 108, 108),
        (116, 114, 97, 100, 101),
    )
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_DAY = Decimal("86400")

__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_RELIABILITY_PLAYBOOK_CONFIG_VERSION",
    "ResearchPacketSourceReliabilityPlaybookConfig",
    "ResearchPacketSourceReliabilityPlaybookObservation",
    "ResearchPacketSourceReliabilityPlaybookRow",
    "ResearchPacketSourceReliabilityPlaybookReasonCount",
    "ResearchPacketSourceReliabilityPlaybookReport",
    "build_research_packet_source_reliability_playbook_report",
    "research_packet_source_reliability_playbook_report_payload",
)


@dataclass(frozen=True)
class ResearchPacketSourceReliabilityPlaybookConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_RELIABILITY_PLAYBOOK_CONFIG_VERSION
    max_freshness_age_seconds: Decimal = Decimal("86400")
    max_latency_seconds: Decimal = Decimal("3600")
    min_historical_reliability_score: Decimal = Decimal("0.700000")
    min_freshness_score: Decimal = Decimal("0.500000")
    min_officialness_score: Decimal = Decimal("0.500000")
    min_independence_score: Decimal = Decimal("0.500000")
    min_latency_score: Decimal = Decimal("0.500000")
    max_contradiction_rate: Decimal = Decimal("0.200000")
    min_resolution_usefulness_score: Decimal = Decimal("0.500000")
    reliability_weight: Decimal = Decimal("1.000000")
    freshness_weight: Decimal = Decimal("1.000000")
    officialness_weight: Decimal = Decimal("1.000000")
    independence_weight: Decimal = Decimal("1.000000")
    latency_weight: Decimal = Decimal("1.000000")
    contradiction_weight: Decimal = Decimal("1.000000")
    resolution_usefulness_weight: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _reject_public_text("config_version", self.config_version)
        for field_name in (
            "max_freshness_age_seconds",
            "max_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_historical_reliability_score",
            "min_freshness_score",
            "min_officialness_score",
            "min_independence_score",
            "min_latency_score",
            "max_contradiction_rate",
            "min_resolution_usefulness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_weight",
            "freshness_weight",
            "officialness_weight",
            "independence_weight",
            "latency_weight",
            "contradiction_weight",
            "resolution_usefulness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchPacketSourceReliabilityPlaybookObservation:
    team_id: str
    source_family_id: str
    source_family_label: str
    source_family_updated_at: datetime
    historical_reliability_score: Decimal
    officialness_score: Decimal
    independence_score: Decimal
    median_latency_seconds: Decimal
    contradiction_rate: Decimal
    resolution_usefulness_score: Decimal
    evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("source_family_id", self.source_family_id)
        _require_public_string("source_family_label", self.source_family_label)
        object.__setattr__(
            self,
            "source_family_updated_at",
            _as_utc("source_family_updated_at", self.source_family_updated_at),
        )
        for field_name in (
            "historical_reliability_score",
            "officialness_score",
            "independence_score",
            "contradiction_rate",
            "resolution_usefulness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "median_latency_seconds",
            _require_nonnegative_decimal(
                "median_latency_seconds",
                self.median_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_count("evidence_count", self.evidence_count),
        )
        _require_hard_flags("observation", self)
        _reject_public_payload("observation", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchPacketSourceReliabilityPlaybookRow:
    team_id: str
    rank: Decimal
    source_family_id: str
    source_family_label: str
    source_family_updated_at: datetime
    source_family_age_seconds: Decimal
    historical_reliability_score: Decimal
    freshness_score: Decimal
    officialness_score: Decimal
    independence_score: Decimal
    latency_score: Decimal
    contradiction_rate: Decimal
    contradiction_score: Decimal
    resolution_usefulness_score: Decimal
    composite_reliability_score: Decimal
    evidence_count: Decimal
    playbook_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        object.__setattr__(self, "rank", _require_positive_count("rank", self.rank))
        _require_public_string("source_family_id", self.source_family_id)
        _require_public_string("source_family_label", self.source_family_label)
        object.__setattr__(
            self,
            "source_family_updated_at",
            _as_utc("source_family_updated_at", self.source_family_updated_at),
        )
        object.__setattr__(
            self,
            "source_family_age_seconds",
            _require_nonnegative_decimal(
                "source_family_age_seconds",
                self.source_family_age_seconds,
            ),
        )
        for field_name in (
            "historical_reliability_score",
            "freshness_score",
            "officialness_score",
            "independence_score",
            "latency_score",
            "contradiction_rate",
            "contradiction_score",
            "resolution_usefulness_score",
            "composite_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_count("evidence_count", self.evidence_count),
        )
        _require_playbook_status("playbook_status", self.playbook_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_public_payload("row", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchPacketSourceReliabilityPlaybookReasonCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count("count", self.count),
        )
        _require_hard_flags("reason count", self)
        _reject_public_payload("reason count", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchPacketSourceReliabilityPlaybookReport:
    generated_at: datetime
    config_version: str
    playbook_status: str
    team_count: Decimal
    source_family_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    top_source_family_count: Decimal
    rows: tuple[ResearchPacketSourceReliabilityPlaybookRow, ...]
    reason_code_counts: tuple[ResearchPacketSourceReliabilityPlaybookReasonCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _reject_public_text("config_version", self.config_version)
        _require_playbook_status("playbook_status", self.playbook_status)
        for field_name in (
            "team_count",
            "source_family_count",
            "row_count",
            "pass_count",
            "watch_count",
            "top_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_public_payload("report", _payload_value(asdict(self)))
        _validate_report_consistency(self)


def build_research_packet_source_reliability_playbook_report(
    *,
    observations: object,
    config: ResearchPacketSourceReliabilityPlaybookConfig,
    generated_at: datetime,
) -> ResearchPacketSourceReliabilityPlaybookReport:
    if type(config) is not ResearchPacketSourceReliabilityPlaybookConfig:
        raise ValueError("config must be a ResearchPacketSourceReliabilityPlaybookConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = _ranked_rows(
        normalized_observations,
        config=config,
        generated_at=generated_at_utc,
    )
    reason_code_counts = _reason_code_counts(rows)
    report_reason_codes = _report_reason_codes(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "playbook_status": _report_status(rows),
        "team_count": _count_from_int(len({row.team_id for row in rows})),
        "source_family_count": _count_from_int(len(rows)),
        "row_count": _count_from_int(len(rows)),
        "pass_count": _count_from_int(_status_count(rows, "pass")),
        "watch_count": _count_from_int(_status_count(rows, "watch")),
        "top_source_family_count": _count_from_int(
            sum(1 for row in rows if row.rank == ONE),
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": report_reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchPacketSourceReliabilityPlaybookReport(**values)


def research_packet_source_reliability_playbook_report_payload(
    report: ResearchPacketSourceReliabilityPlaybookReport,
) -> dict[str, object]:
    if type(report) is not ResearchPacketSourceReliabilityPlaybookReport:
        raise ValueError("report must be a ResearchPacketSourceReliabilityPlaybookReport")
    payload = _payload_value(report)
    _reject_public_payload("report payload", payload)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    return payload


def _normalize_observations(
    observations: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceReliabilityPlaybookObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_keys: set[tuple[str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchPacketSourceReliabilityPlaybookObservation:
            raise ValueError(
                "observations must contain ResearchPacketSourceReliabilityPlaybookObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_family_updated_at > generated_at:
            raise ValueError("source_family_updated_at must not be in the future")
        key = (observation.team_id, observation.source_family_id)
        if key in seen_keys:
            raise ValueError("observations must be unique by team and source family")
        seen_keys.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.source_family_id)))


def _ranked_rows(
    observations: tuple[ResearchPacketSourceReliabilityPlaybookObservation, ...],
    *,
    config: ResearchPacketSourceReliabilityPlaybookConfig,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceReliabilityPlaybookRow, ...]:
    unranked = tuple(
        _row_from_observation(
            observation,
            config=config,
            generated_at=generated_at,
            rank=ONE,
        )
        for observation in observations
    )
    ranked_rows: list[ResearchPacketSourceReliabilityPlaybookRow] = []
    team_ids = tuple(dict.fromkeys(row.team_id for row in unranked))
    for team_id in team_ids:
        team_rows = sorted(
            (row for row in unranked if row.team_id == team_id),
            key=lambda row: (
                -row.composite_reliability_score,
                -row.historical_reliability_score,
                -row.freshness_score,
                row.source_family_id,
            ),
        )
        for index, row in enumerate(team_rows, start=1):
            ranked_rows.append(
                ResearchPacketSourceReliabilityPlaybookRow(
                    team_id=row.team_id,
                    rank=_count_from_int(index),
                    source_family_id=row.source_family_id,
                    source_family_label=row.source_family_label,
                    source_family_updated_at=row.source_family_updated_at,
                    source_family_age_seconds=row.source_family_age_seconds,
                    historical_reliability_score=row.historical_reliability_score,
                    freshness_score=row.freshness_score,
                    officialness_score=row.officialness_score,
                    independence_score=row.independence_score,
                    latency_score=row.latency_score,
                    contradiction_rate=row.contradiction_rate,
                    contradiction_score=row.contradiction_score,
                    resolution_usefulness_score=row.resolution_usefulness_score,
                    composite_reliability_score=row.composite_reliability_score,
                    evidence_count=row.evidence_count,
                    playbook_status=row.playbook_status,
                    reason_codes=row.reason_codes,
                )
            )
    return tuple(ranked_rows)


def _row_from_observation(
    observation: ResearchPacketSourceReliabilityPlaybookObservation,
    *,
    config: ResearchPacketSourceReliabilityPlaybookConfig,
    generated_at: datetime,
    rank: Decimal,
) -> ResearchPacketSourceReliabilityPlaybookRow:
    age_seconds = _age_seconds(
        "source_family_updated_at",
        generated_at,
        observation.source_family_updated_at,
    )
    freshness_score = _bounded_ratio(ONE - _ratio(age_seconds, config.max_freshness_age_seconds))
    latency_score = _bounded_ratio(
        ONE - _ratio(observation.median_latency_seconds, config.max_latency_seconds),
    )
    contradiction_score = _bounded_ratio(ONE - observation.contradiction_rate)
    composite_reliability_score = _weighted_score(
        (
            (observation.historical_reliability_score, config.reliability_weight),
            (freshness_score, config.freshness_weight),
            (observation.officialness_score, config.officialness_weight),
            (observation.independence_score, config.independence_weight),
            (latency_score, config.latency_weight),
            (contradiction_score, config.contradiction_weight),
            (
                observation.resolution_usefulness_score,
                config.resolution_usefulness_weight,
            ),
        )
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        freshness_score=freshness_score,
        latency_score=latency_score,
        config=config,
    )
    return ResearchPacketSourceReliabilityPlaybookRow(
        team_id=observation.team_id,
        rank=rank,
        source_family_id=observation.source_family_id,
        source_family_label=observation.source_family_label,
        source_family_updated_at=observation.source_family_updated_at,
        source_family_age_seconds=age_seconds,
        historical_reliability_score=observation.historical_reliability_score,
        freshness_score=freshness_score,
        officialness_score=observation.officialness_score,
        independence_score=observation.independence_score,
        latency_score=latency_score,
        contradiction_rate=observation.contradiction_rate,
        contradiction_score=contradiction_score,
        resolution_usefulness_score=observation.resolution_usefulness_score,
        composite_reliability_score=composite_reliability_score,
        evidence_count=observation.evidence_count,
        playbook_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: ResearchPacketSourceReliabilityPlaybookObservation,
    freshness_score: Decimal,
    latency_score: Decimal,
    config: ResearchPacketSourceReliabilityPlaybookConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.historical_reliability_score < config.min_historical_reliability_score:
        reasons.append(LOW_RELIABILITY_REASON)
    if freshness_score < config.min_freshness_score:
        reasons.append(STALE_SOURCE_FAMILY_REASON)
    if observation.officialness_score < config.min_officialness_score:
        reasons.append(LOW_OFFICIALNESS_REASON)
    if observation.independence_score < config.min_independence_score:
        reasons.append(LOW_INDEPENDENCE_REASON)
    if latency_score < config.min_latency_score:
        reasons.append(SLOW_SOURCE_FAMILY_REASON)
    if observation.contradiction_rate > config.max_contradiction_rate:
        reasons.append(HIGH_CONTRADICTION_RATE_REASON)
    if observation.resolution_usefulness_score < config.min_resolution_usefulness_score:
        reasons.append(LOW_RESOLUTION_USEFULNESS_REASON)
    return tuple(reasons or (PASSED_REASON,))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    return "pass" if reason_codes == (PASSED_REASON,) else "watch"


def _report_status(
    rows: tuple[ResearchPacketSourceReliabilityPlaybookRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.playbook_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceReliabilityPlaybookRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )
    return reason_codes or (PASSED_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchPacketSourceReliabilityPlaybookRow, ...],
) -> tuple[ResearchPacketSourceReliabilityPlaybookReasonCount, ...]:
    return tuple(
        ResearchPacketSourceReliabilityPlaybookReasonCount(
            reason_code=reason_code,
            count=_count_from_int(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in REPORT_REASON_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )


def _status_count(
    rows: tuple[ResearchPacketSourceReliabilityPlaybookRow, ...],
    playbook_status: str,
) -> int:
    return sum(1 for row in rows if row.playbook_status == playbook_status)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketSourceReliabilityPlaybookRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    previous_team = ""
    previous_rank = ZERO
    for row in normalized:
        if type(row) is not ResearchPacketSourceReliabilityPlaybookRow:
            raise ValueError("rows must contain ResearchPacketSourceReliabilityPlaybookRow")
        _require_hard_flags("row", row)
        key = (row.team_id, row.source_family_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and source family")
        seen_keys.add(key)
        if row.team_id != previous_team:
            previous_team = row.team_id
            previous_rank = ZERO
        if row.rank != previous_rank + ONE:
            raise ValueError("rows must use stable rank sequence")
        previous_rank = row.rank
    return normalized


def _normalize_reason_counts(
    counts: object,
) -> tuple[ResearchPacketSourceReliabilityPlaybookReasonCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchPacketSourceReliabilityPlaybookReasonCount:
            raise ValueError(
                "reason_code_counts must contain ResearchPacketSourceReliabilityPlaybookReasonCount",
            )
        _require_hard_flags("reason count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in seen
    )
    if tuple(item.reason_code for item in normalized) != expected:
        raise ValueError("reason_code_counts must use deterministic reason sequence")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized == (PASSED_REASON,) or normalized == (EMPTY_REASON,):
        return normalized
    expected = tuple(reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in normalized)
    if normalized != expected:
        raise ValueError(f"{field_name} must use deterministic reason sequence")
    return normalized


def _validate_row_consistency(row: ResearchPacketSourceReliabilityPlaybookRow) -> None:
    if row.contradiction_score != _bounded_ratio(ONE - row.contradiction_rate):
        raise ValueError("contradiction_score must match contradiction_rate")
    if row.playbook_status != _row_status(row.reason_codes):
        raise ValueError("playbook_status must match reason_codes")
    if PASSED_REASON in row.reason_codes and row.reason_codes != (PASSED_REASON,):
        raise ValueError("passed reason must stand alone")


def _validate_report_consistency(
    report: ResearchPacketSourceReliabilityPlaybookReport,
) -> None:
    if report.row_count != _count_from_int(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _count_from_int(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.source_family_count != report.row_count:
        raise ValueError("source_family_count must match rows")
    if report.pass_count != _count_from_int(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_from_int(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.top_source_family_count != _count_from_int(
        sum(1 for row in report.rows if row.rank == ONE),
    ):
        raise ValueError("top_source_family_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.playbook_status != _report_status(report.rows):
        raise ValueError("playbook_status must match rows")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _weighted_score(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    numerator = ZERO
    denominator = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for score, weight in values:
            numerator += score * weight
            denominator += weight
        return _bounded_ratio(numerator / denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _bounded_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return _quantize(ZERO)
    if normalized > ONE:
        return _quantize(ONE)
    return normalized


def _age_seconds(field_name: str, later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError(f"{field_name} must not be in the future")
    delta = later - earlier
    return _quantize(
        (Decimal(delta.days) * SECONDS_PER_DAY)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_public_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_playbook_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in PLAYBOOK_STATUSES:
        raise ValueError(f"{field_name} must be pass or watch")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _count_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat().replace("+00:00", "Z")
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value")


def _reject_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_public_text(f"{label} key", key)
            _reject_public_payload(label, item)
        return
    if type(payload) in (list, tuple):
        for item in payload:
            _reject_public_payload(label, item)
        return
    if type(payload) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(payload) is str:
        _reject_public_text(label, payload)


def _reject_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
