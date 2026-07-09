from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_CONFIG_VERSION = (
    "research-team-specialist-source-quorum-memory-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_OBSERVATIONS_REASON = "source_quorum_memory_no_observations"
CLEAR_REASON = "source_quorum_memory_clear"
SOURCE_QUORUM_BLOCK_REASON = "source_quorum_block"
SOURCE_QUORUM_WATCH_REASON = "source_quorum_watch"
MEMORY_COVERAGE_BLOCK_REASON = "memory_coverage_block"
MEMORY_COVERAGE_WATCH_REASON = "memory_coverage_watch"
STALE_MEMORY_BLOCK_REASON = "stale_memory_block"
STALE_MEMORY_WATCH_REASON = "stale_memory_watch"

ROW_REASON_CODE_SEQUENCE = (
    SOURCE_QUORUM_BLOCK_REASON,
    SOURCE_QUORUM_WATCH_REASON,
    MEMORY_COVERAGE_BLOCK_REASON,
    MEMORY_COVERAGE_WATCH_REASON,
    STALE_MEMORY_BLOCK_REASON,
    STALE_MEMORY_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "source_quorum_memory_report_clear"
REPORT_BLOCK_PRESENT_REASON = "source_quorum_memory_block_present"
REPORT_WATCH_PRESENT_REASON = "source_quorum_memory_watch_present"
REPORT_SOURCE_QUORUM_GAP_REASON = "source_quorum_gap_present"
REPORT_MEMORY_COVERAGE_GAP_REASON = "memory_coverage_gap_present"
REPORT_STALE_MEMORY_GAP_REASON = "stale_memory_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_SOURCE_QUORUM_GAP_REASON,
    REPORT_MEMORY_COVERAGE_GAP_REASON,
    REPORT_STALE_MEMORY_GAP_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "use_quorum_memory_for_research_review",
    STATUS_WATCH: "review_quorum_memory_before_reuse",
    STATUS_BLOCK: "block_quorum_memory_until_review",
}

_BLOCKED_HEXES = (
    "63616e6469646174655f6964",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "64736e",
    "7461626c65",
    "746f6b656e",
    "77616c6c6574",
    "61757468",
    "6f72646572",
    "7472616465",
    "74726164696e67",
    "6c697665",
    "6461746162617365",
    "6e6574776f726b",
    "7265636f6d6d656e64",
    "73697a696e67",
    "736563726574",
    "63726564656e7469616c",
    "70726976617465",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
)
_BLOCKED_PARTS = tuple(bytes.fromhex(item).decode("ascii") for item in _BLOCKED_HEXES)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_STATUSES",
    "ResearchTeamSpecialistSourceQuorumMemoryConfig",
    "ResearchTeamSpecialistSourceQuorumMemoryObservation",
    "ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount",
    "ResearchTeamSpecialistSourceQuorumMemoryReport",
    "ResearchTeamSpecialistSourceQuorumMemoryRow",
    "build_research_team_specialist_source_quorum_memory_report",
    "research_team_specialist_source_quorum_memory_report_digest",
    "research_team_specialist_source_quorum_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQuorumMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_CONFIG_VERSION
    )
    min_pass_independent_family_count: Decimal = Decimal("3.000000")
    min_watch_independent_family_count: Decimal = Decimal("2.000000")
    min_pass_quorum_ratio: Decimal = Decimal("0.800000")
    min_watch_quorum_ratio: Decimal = Decimal("0.600000")
    min_pass_memory_coverage_ratio: Decimal = Decimal("0.750000")
    min_watch_memory_coverage_ratio: Decimal = Decimal("0.500000")
    max_pass_stale_memory_ratio: Decimal = Decimal("0.100000")
    max_watch_stale_memory_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQuorumMemoryConfig:
            raise TypeError(
                "ResearchTeamSpecialistSourceQuorumMemoryConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistSourceQuorumMemoryConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "min_pass_independent_family_count",
            "min_watch_independent_family_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_integral_decimal(name, getattr(self, name)),
            )
        for name in (
            "min_pass_quorum_ratio",
            "min_watch_quorum_ratio",
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
            "max_pass_stale_memory_ratio",
            "max_watch_stale_memory_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if (
            self.min_watch_independent_family_count
            > self.min_pass_independent_family_count
        ):
            raise ValueError("min_watch_independent_family_count must not exceed pass")
        if self.min_watch_quorum_ratio > self.min_pass_quorum_ratio:
            raise ValueError("min_watch_quorum_ratio must not exceed pass")
        if self.min_watch_memory_coverage_ratio > self.min_pass_memory_coverage_ratio:
            raise ValueError("min_watch_memory_coverage_ratio must not exceed pass")
        if self.max_pass_stale_memory_ratio > self.max_watch_stale_memory_ratio:
            raise ValueError("max_pass_stale_memory_ratio must not exceed watch")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQuorumMemoryObservation:
    team_label: str
    specialist_label: str
    evidence_family_label: str
    observed_at: datetime
    independent_family_count: Decimal
    quorum_confirmed_family_count: Decimal
    memory_check_count: Decimal
    memory_confirmed_count: Decimal
    stale_memory_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQuorumMemoryObservation:
            raise TypeError(
                "ResearchTeamSpecialistSourceQuorumMemoryObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistSourceQuorumMemoryObservation,
            "observation",
        )
        for name in ("team_label", "specialist_label", "evidence_family_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in ("independent_family_count", "memory_check_count"):
            object.__setattr__(
                self,
                name,
                _require_positive_integral_decimal(name, getattr(self, name)),
            )
        for name in (
            "quorum_confirmed_family_count",
            "memory_confirmed_count",
            "stale_memory_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_integral_decimal(name, getattr(self, name)),
            )
        _validate_count_bounds(self)
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQuorumMemoryRow:
    team_label: str
    specialist_label: str
    evidence_family_label: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    independent_family_count: Decimal
    quorum_confirmed_family_count: Decimal
    memory_check_count: Decimal
    memory_confirmed_count: Decimal
    stale_memory_count: Decimal
    quorum_ratio: Decimal
    memory_coverage_ratio: Decimal
    stale_memory_ratio: Decimal
    quorum_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQuorumMemoryRow:
            raise TypeError(
                "ResearchTeamSpecialistSourceQuorumMemoryRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistSourceQuorumMemoryRow, "row")
        for name in ("team_label", "specialist_label", "evidence_family_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal("snapshot_age_seconds", self.snapshot_age_seconds),
        )
        for name in ("independent_family_count", "memory_check_count"):
            object.__setattr__(
                self,
                name,
                _require_positive_integral_decimal(name, getattr(self, name)),
            )
        for name in (
            "quorum_confirmed_family_count",
            "memory_confirmed_count",
            "stale_memory_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_integral_decimal(name, getattr(self, name)),
            )
        for name in (
            "quorum_ratio",
            "memory_coverage_ratio",
            "stale_memory_ratio",
            "quorum_memory_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_count_bounds(self)
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_positive_integral_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQuorumMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    observation_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    evidence_family_count: Decimal
    independent_family_count: Decimal
    quorum_confirmed_family_count: Decimal
    memory_check_count: Decimal
    memory_confirmed_count: Decimal
    stale_memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    quorum_ratio: Decimal
    memory_coverage_ratio: Decimal
    stale_memory_ratio: Decimal
    quorum_memory_score: Decimal
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQuorumMemoryReport:
            raise TypeError(
                "ResearchTeamSpecialistSourceQuorumMemoryReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistSourceQuorumMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "next_review_step",
            _require_public_label("next_review_step", self.next_review_step),
        )
        for name in (
            "observation_count",
            "team_count",
            "specialist_count",
            "evidence_family_count",
            "independent_family_count",
            "quorum_confirmed_family_count",
            "memory_check_count",
            "memory_confirmed_count",
            "stale_memory_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_integral_decimal(name, getattr(self, name)),
            )
        for name in (
            "quorum_ratio",
            "memory_coverage_ratio",
            "stale_memory_ratio",
            "quorum_memory_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_specialist_source_quorum_memory_report_payload(self)


def build_research_team_specialist_source_quorum_memory_report(
    observations: Iterable[ResearchTeamSpecialistSourceQuorumMemoryObservation],
    *,
    config: ResearchTeamSpecialistSourceQuorumMemoryConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchTeamSpecialistSourceQuorumMemoryReport:
    cfg = config or ResearchTeamSpecialistSourceQuorumMemoryConfig()
    if type(cfg) is not ResearchTeamSpecialistSourceQuorumMemoryConfig:
        raise ValueError(
            "config must be exactly ResearchTeamSpecialistSourceQuorumMemoryConfig",
        )
    _require_hard_flags("config", cfg)
    _reject_unsafe_public_payload(cfg)
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable of observations")
    if generated_at is None:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    item,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for item in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    quorum_ratio = _aggregate_quorum_ratio(rows)
    memory_coverage_ratio = _aggregate_memory_coverage_ratio(rows)
    stale_memory_ratio = _aggregate_stale_memory_ratio(rows)
    quorum_memory_score = (
        ZERO
        if not rows
        else _quorum_memory_score(
            quorum_ratio=quorum_ratio,
            memory_coverage_ratio=memory_coverage_ratio,
            stale_memory_ratio=stale_memory_ratio,
        )
    )
    return ResearchTeamSpecialistSourceQuorumMemoryReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        observation_count=_count_decimal(len(normalized_observations)),
        team_count=_count_decimal(len({row.team_label for row in rows})),
        specialist_count=_count_decimal(
            len({(row.team_label, row.specialist_label) for row in rows}),
        ),
        evidence_family_count=_count_decimal(
            len({row.evidence_family_label for row in rows}),
        ),
        independent_family_count=_sum_decimal(row.independent_family_count for row in rows),
        quorum_confirmed_family_count=_sum_decimal(
            row.quorum_confirmed_family_count for row in rows
        ),
        memory_check_count=_sum_decimal(row.memory_check_count for row in rows),
        memory_confirmed_count=_sum_decimal(row.memory_confirmed_count for row in rows),
        stale_memory_count=_sum_decimal(row.stale_memory_count for row in rows),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        quorum_ratio=quorum_ratio,
        memory_coverage_ratio=memory_coverage_ratio,
        stale_memory_ratio=stale_memory_ratio,
        quorum_memory_score=quorum_memory_score,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(
            rows,
            observation_count=len(normalized_observations),
            quorum_ratio=quorum_ratio,
            memory_coverage_ratio=memory_coverage_ratio,
            stale_memory_ratio=stale_memory_ratio,
            config=cfg,
        ),
    )


def research_team_specialist_source_quorum_memory_report_payload(
    value: object,
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    return payload


def research_team_specialist_source_quorum_memory_report_digest(
    report: ResearchTeamSpecialistSourceQuorumMemoryReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistSourceQuorumMemoryReport:
        raise ValueError(
            "report must be exactly ResearchTeamSpecialistSourceQuorumMemoryReport",
        )
    return report.derived_validation_digest


def _row_from_observation(
    observation: ResearchTeamSpecialistSourceQuorumMemoryObservation,
    *,
    config: ResearchTeamSpecialistSourceQuorumMemoryConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistSourceQuorumMemoryRow:
    quorum_ratio = _safe_divide(
        observation.quorum_confirmed_family_count,
        observation.independent_family_count,
    )
    memory_coverage_ratio = _safe_divide(
        observation.memory_confirmed_count,
        observation.memory_check_count,
    )
    stale_memory_ratio = _safe_divide(
        observation.stale_memory_count,
        observation.memory_check_count,
    )
    reason_codes = _row_reason_codes(
        independent_family_count=observation.independent_family_count,
        quorum_ratio=quorum_ratio,
        memory_coverage_ratio=memory_coverage_ratio,
        stale_memory_ratio=stale_memory_ratio,
        config=config,
    )
    return ResearchTeamSpecialistSourceQuorumMemoryRow(
        team_label=observation.team_label,
        specialist_label=observation.specialist_label,
        evidence_family_label=observation.evidence_family_label,
        observed_at=observation.observed_at,
        snapshot_age_seconds=_age_seconds(generated_at, observation.observed_at),
        independent_family_count=observation.independent_family_count,
        quorum_confirmed_family_count=observation.quorum_confirmed_family_count,
        memory_check_count=observation.memory_check_count,
        memory_confirmed_count=observation.memory_confirmed_count,
        stale_memory_count=observation.stale_memory_count,
        quorum_ratio=quorum_ratio,
        memory_coverage_ratio=memory_coverage_ratio,
        stale_memory_ratio=stale_memory_ratio,
        quorum_memory_score=_quorum_memory_score(
            quorum_ratio=quorum_ratio,
            memory_coverage_ratio=memory_coverage_ratio,
            stale_memory_ratio=stale_memory_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    independent_family_count: Decimal,
    quorum_ratio: Decimal,
    memory_coverage_ratio: Decimal,
    stale_memory_ratio: Decimal,
    config: ResearchTeamSpecialistSourceQuorumMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        independent_family_count < config.min_watch_independent_family_count
        or quorum_ratio < config.min_watch_quorum_ratio
    ):
        reason_codes.append(SOURCE_QUORUM_BLOCK_REASON)
    elif (
        independent_family_count < config.min_pass_independent_family_count
        or quorum_ratio < config.min_pass_quorum_ratio
    ):
        reason_codes.append(SOURCE_QUORUM_WATCH_REASON)
    if memory_coverage_ratio < config.min_watch_memory_coverage_ratio:
        reason_codes.append(MEMORY_COVERAGE_BLOCK_REASON)
    elif memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        reason_codes.append(MEMORY_COVERAGE_WATCH_REASON)
    if stale_memory_ratio > config.max_watch_stale_memory_ratio:
        reason_codes.append(STALE_MEMORY_BLOCK_REASON)
    elif stale_memory_ratio > config.max_pass_stale_memory_ratio:
        reason_codes.append(STALE_MEMORY_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...],
    *,
    observation_count: int,
    quorum_ratio: Decimal,
    memory_coverage_ratio: Decimal,
    stale_memory_ratio: Decimal,
    config: ResearchTeamSpecialistSourceQuorumMemoryConfig,
) -> tuple[str, ...]:
    if observation_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if quorum_ratio < config.min_pass_quorum_ratio:
        reason_codes.append(REPORT_SOURCE_QUORUM_GAP_REASON)
    if memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        reason_codes.append(REPORT_MEMORY_COVERAGE_GAP_REASON)
    if stale_memory_ratio > config.max_pass_stale_memory_ratio:
        reason_codes.append(REPORT_STALE_MEMORY_GAP_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _report_status(rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(item.endswith("_block") for item in reason_codes):
        return STATUS_BLOCK
    if any(item.endswith("_watch") for item in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...],
) -> tuple[ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=_count_decimal(1),
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
            row_ratio=_safe_divide(_count_decimal(counter[reason_code]), row_count),
        )
        for reason_code in COUNT_REASON_CODE_SEQUENCE
        if counter.get(reason_code, 0) > 0
    )


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistSourceQuorumMemoryObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistSourceQuorumMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    normalized: list[ResearchTeamSpecialistSourceQuorumMemoryObservation] = []
    for item in observations:
        if type(item) is not ResearchTeamSpecialistSourceQuorumMemoryObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchTeamSpecialistSourceQuorumMemoryObservation",
            )
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        _require_hard_flags("observation", item)
        _reject_unsafe_public_payload(item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchTeamSpecialistSourceQuorumMemoryRow] = []
    for row in rows:
        if type(row) is not ResearchTeamSpecialistSourceQuorumMemoryRow:
            raise ValueError("rows must contain exactly ResearchTeamSpecialistSourceQuorumMemoryRow")
        normalized.append(row)
    return tuple(normalized)


def _normalize_reason_code_counts(
    items: object,
) -> tuple[ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount, ...]:
    if not isinstance(items, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount] = []
    for item in items:
        if type(item) is not ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchTeamSpecialistSourceQuorumMemoryReasonCodeCount",
            )
        normalized.append(item)
    return tuple(normalized)


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"{name} must be a non-empty tuple")
    normalized: list[str] = []
    for item in value:
        normalized.append(_require_member(name, item, allowed))
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(item for item in allowed if item in normalized)


def _row_sort_key(row: ResearchTeamSpecialistSourceQuorumMemoryRow) -> tuple[int, str, str, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.team_label,
        row.specialist_label,
        row.evidence_family_label,
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _aggregate_quorum_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.quorum_confirmed_family_count for row in rows),
        _sum_decimal(row.independent_family_count for row in rows),
    )


def _aggregate_memory_coverage_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.memory_confirmed_count for row in rows),
        _sum_decimal(row.memory_check_count for row in rows),
    )


def _aggregate_stale_memory_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQuorumMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.stale_memory_count for row in rows),
        _sum_decimal(row.memory_check_count for row in rows),
    )


def _quorum_memory_score(
    *,
    quorum_ratio: Decimal,
    memory_coverage_ratio: Decimal,
    stale_memory_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            "quorum_memory_score",
            (quorum_ratio + memory_coverage_ratio + (ONE - stale_memory_ratio)) / THREE,
        )


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal("ratio", numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        raise ValueError("observed_at must not be after generated_at")
    seconds = (
        Decimal(str(delta.days * 86400 + delta.seconds))
        + (Decimal(str(delta.microseconds)) / MICROSECONDS_PER_SECOND)
    )
    return _quantize_decimal("snapshot_age_seconds", seconds)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        with localcontext(DECIMAL_CONTEXT):
            total = _quantize_decimal("total", total + value)
    return total


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(str(value)))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{name} must be a non-empty string")
    if stripped != value:
        raise ValueError(f"{name} must be canonical")
    _reject_unsafe_public_text(name, value)
    return value


def _require_status(name: str, value: object) -> str:
    return _require_member(name, value, RESEARCH_TEAM_SPECIALIST_SOURCE_QUORUM_MEMORY_STATUSES)


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed!r}")
    return value


def _require_exact_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize_decimal(name, value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_exact_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be >= 0.000000")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be <= 1.000000")
    return normalized


def _require_positive_integral_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_integral_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be > 0.000000")
    return normalized


def _require_nonnegative_integral_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integral Decimal")
    return normalized


def _quantize_decimal(name: str, value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_count_bounds(value: object) -> None:
    independent_family_count = getattr(value, "independent_family_count")
    quorum_confirmed_family_count = getattr(value, "quorum_confirmed_family_count")
    memory_check_count = getattr(value, "memory_check_count")
    memory_confirmed_count = getattr(value, "memory_confirmed_count")
    stale_memory_count = getattr(value, "stale_memory_count")
    if quorum_confirmed_family_count > independent_family_count:
        raise ValueError("quorum_confirmed_family_count must not exceed independent_family_count")
    if memory_confirmed_count > memory_check_count:
        raise ValueError("memory_confirmed_count must not exceed memory_check_count")
    if stale_memory_count > memory_check_count:
        raise ValueError("stale_memory_count must not exceed memory_check_count")


def _validate_row(row: ResearchTeamSpecialistSourceQuorumMemoryRow) -> None:
    if row.quorum_ratio != _safe_divide(
        row.quorum_confirmed_family_count,
        row.independent_family_count,
    ):
        raise ValueError("quorum_ratio must match row counts")
    if row.memory_coverage_ratio != _safe_divide(
        row.memory_confirmed_count,
        row.memory_check_count,
    ):
        raise ValueError("memory_coverage_ratio must match row counts")
    if row.stale_memory_ratio != _safe_divide(row.stale_memory_count, row.memory_check_count):
        raise ValueError("stale_memory_ratio must match row counts")
    expected_score = _quorum_memory_score(
        quorum_ratio=row.quorum_ratio,
        memory_coverage_ratio=row.memory_coverage_ratio,
        stale_memory_ratio=row.stale_memory_ratio,
    )
    if row.quorum_memory_score != expected_score:
        raise ValueError("quorum_memory_score must match row ratios")


def _validate_report(report: ResearchTeamSpecialistSourceQuorumMemoryReport) -> None:
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.team_count != _count_decimal(len({row.team_label for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _count_decimal(
        len({(row.team_label, row.specialist_label) for row in report.rows}),
    ):
        raise ValueError("specialist_count must match rows")
    if report.evidence_family_count != _count_decimal(
        len({row.evidence_family_label for row in report.rows}),
    ):
        raise ValueError("evidence_family_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    expected_score = (
        ZERO
        if not report.rows
        else _quorum_memory_score(
            quorum_ratio=report.quorum_ratio,
            memory_coverage_ratio=report.memory_coverage_ratio,
            stale_memory_ratio=report.stale_memory_ratio,
        )
    )
    if report.quorum_memory_score != expected_score:
        raise ValueError("quorum_memory_score must match report ratios")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a 64-character digest")
    allowed = set("0123456789abcdef")
    if any(item not in allowed for item in value):
        raise ValueError(f"{name} must be lowercase hex")
    return value


def _require_supported_payload_input(value: object) -> None:
    if type(value) is not ResearchTeamSpecialistSourceQuorumMemoryReport and type(value) is not dict:
        raise ValueError(
            "value must be a ResearchTeamSpecialistSourceQuorumMemoryReport or dict",
        )


def _payload_value(value: Any) -> Any:
    return _json_ready(asdict(value) if is_dataclass(value) and not isinstance(value, type) else value)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must be Decimal-backed string")
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


def _derived_validation_digest(
    report: ResearchTeamSpecialistSourceQuorumMemoryReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = sha256(encoded.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _validate_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_text("public payload", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text("public payload", value)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(part in lowered for part in _BLOCKED_PARTS):
        raise ValueError(f"unsafe public payload in {label}")
