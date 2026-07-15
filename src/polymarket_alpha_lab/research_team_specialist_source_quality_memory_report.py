from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_CONFIG_VERSION = (
    "research-team-specialist-source-quality-memory-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_OBSERVATIONS_REASON = "source_quality_memory_no_observations"
CLEAR_REASON = "source_quality_memory_clear"
SOURCE_QUALITY_BLOCK_REASON = "source_quality_block"
SOURCE_QUALITY_WATCH_REASON = "source_quality_watch"
MEMORY_RECALL_BLOCK_REASON = "memory_recall_block"
MEMORY_RECALL_WATCH_REASON = "memory_recall_watch"
STALE_MEMORY_BLOCK_REASON = "stale_memory_block"
STALE_MEMORY_WATCH_REASON = "stale_memory_watch"
QUALITY_MEMORY_ALIGNMENT_BLOCK_REASON = "quality_memory_alignment_block"
QUALITY_MEMORY_ALIGNMENT_WATCH_REASON = "quality_memory_alignment_watch"

ROW_REASON_CODE_SEQUENCE = (
    SOURCE_QUALITY_BLOCK_REASON,
    SOURCE_QUALITY_WATCH_REASON,
    MEMORY_RECALL_BLOCK_REASON,
    MEMORY_RECALL_WATCH_REASON,
    STALE_MEMORY_BLOCK_REASON,
    STALE_MEMORY_WATCH_REASON,
    QUALITY_MEMORY_ALIGNMENT_BLOCK_REASON,
    QUALITY_MEMORY_ALIGNMENT_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "source_quality_memory_report_clear"
REPORT_BLOCK_PRESENT_REASON = "source_quality_memory_block_present"
REPORT_WATCH_PRESENT_REASON = "source_quality_memory_watch_present"
REPORT_SOURCE_QUALITY_GAP_REASON = "source_quality_gap_present"
REPORT_MEMORY_RECALL_GAP_REASON = "memory_recall_gap_present"
REPORT_STALE_MEMORY_GAP_REASON = "stale_memory_gap_present"
REPORT_ALIGNMENT_GAP_REASON = "quality_memory_alignment_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_SOURCE_QUALITY_GAP_REASON,
    REPORT_MEMORY_RECALL_GAP_REASON,
    REPORT_STALE_MEMORY_GAP_REASON,
    REPORT_ALIGNMENT_GAP_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "reuse_source_quality_memory_for_research",
    STATUS_WATCH: "review_source_quality_memory_before_reuse",
    STATUS_BLOCK: "block_source_quality_memory_reuse_until_review",
}

_BLOCKED_HEXES = (
    "63616e6469646174655f6964",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "736c7567",
    "7175657374696f6e",
    "75726c",
    "736f757263655f74657874",
    "736f757263655f75726c",
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
    "7261775f6964",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
)
_BLOCKED_PARTS = tuple(bytes.fromhex(item).decode("ascii") for item in _BLOCKED_HEXES)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_STATUSES",
    "ResearchTeamSpecialistSourceQualityMemoryConfig",
    "ResearchTeamSpecialistSourceQualityMemoryObservation",
    "ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount",
    "ResearchTeamSpecialistSourceQualityMemoryReport",
    "ResearchTeamSpecialistSourceQualityMemoryRow",
    "build_research_team_specialist_source_quality_memory_report",
    "research_team_specialist_source_quality_memory_report_digest",
    "research_team_specialist_source_quality_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQualityMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_CONFIG_VERSION
    )
    min_pass_source_quality_ratio: Decimal = Decimal("0.800000")
    min_watch_source_quality_ratio: Decimal = Decimal("0.600000")
    min_pass_memory_recall_ratio: Decimal = Decimal("0.750000")
    min_watch_memory_recall_ratio: Decimal = Decimal("0.500000")
    max_pass_stale_memory_ratio: Decimal = Decimal("0.100000")
    max_watch_stale_memory_ratio: Decimal = Decimal("0.250000")
    min_pass_quality_memory_alignment_ratio: Decimal = Decimal("0.700000")
    min_watch_quality_memory_alignment_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQualityMemoryConfig:
            raise TypeError(
                "ResearchTeamSpecialistSourceQualityMemoryConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistSourceQualityMemoryConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        ratio_names = (
            "min_pass_source_quality_ratio",
            "min_watch_source_quality_ratio",
            "min_pass_memory_recall_ratio",
            "min_watch_memory_recall_ratio",
            "max_pass_stale_memory_ratio",
            "max_watch_stale_memory_ratio",
            "min_pass_quality_memory_alignment_ratio",
            "min_watch_quality_memory_alignment_ratio",
        )
        raw_ratios = {
            name: _require_decimal(name, getattr(self, name))
            for name in ratio_names
        }
        for name in ratio_names:
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if (
            raw_ratios["min_watch_source_quality_ratio"]
            > raw_ratios["min_pass_source_quality_ratio"]
        ):
            raise ValueError("min_watch_source_quality_ratio must not exceed pass")
        if (
            raw_ratios["min_watch_memory_recall_ratio"]
            > raw_ratios["min_pass_memory_recall_ratio"]
        ):
            raise ValueError("min_watch_memory_recall_ratio must not exceed pass")
        if (
            raw_ratios["max_pass_stale_memory_ratio"]
            > raw_ratios["max_watch_stale_memory_ratio"]
        ):
            raise ValueError("max_pass_stale_memory_ratio must not exceed watch")
        if (
            raw_ratios["min_watch_quality_memory_alignment_ratio"]
            > raw_ratios["min_pass_quality_memory_alignment_ratio"]
        ):
            raise ValueError(
                "min_watch_quality_memory_alignment_ratio must not exceed pass",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQualityMemoryObservation:
    team_ref: str
    specialist_ref: str
    observed_at: datetime
    source_quality_check_count: Decimal
    source_quality_pass_count: Decimal
    memory_recall_check_count: Decimal
    memory_recall_pass_count: Decimal
    memory_item_count: Decimal
    stale_memory_item_count: Decimal
    quality_memory_link_count: Decimal
    validated_quality_memory_link_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQualityMemoryObservation:
            raise TypeError(
                "ResearchTeamSpecialistSourceQualityMemoryObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistSourceQualityMemoryObservation,
            "observation",
        )
        for name in ("team_ref", "specialist_ref"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _validate_count_domains(self)
        _validate_count_bounds(self)
        for name in (
            "source_quality_check_count",
            "memory_recall_check_count",
            "memory_item_count",
            "quality_memory_link_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "source_quality_pass_count",
            "memory_recall_pass_count",
            "stale_memory_item_count",
            "validated_quality_memory_link_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQualityMemoryRow:
    team_ref: str
    specialist_ref: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    source_quality_check_count: Decimal
    source_quality_pass_count: Decimal
    memory_recall_check_count: Decimal
    memory_recall_pass_count: Decimal
    memory_item_count: Decimal
    stale_memory_item_count: Decimal
    quality_memory_link_count: Decimal
    validated_quality_memory_link_count: Decimal
    source_quality_ratio: Decimal
    memory_recall_ratio: Decimal
    stale_memory_ratio: Decimal
    quality_memory_alignment_ratio: Decimal
    source_quality_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamSpecialistSourceQualityMemoryConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQualityMemoryRow:
            raise TypeError(
                "ResearchTeamSpecialistSourceQualityMemoryRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchTeamSpecialistSourceQualityMemoryConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchTeamSpecialistSourceQualityMemoryRow, "row")
        config = _require_validation_config(validation_config)
        for name in ("team_ref", "specialist_ref"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal("snapshot_age_seconds", self.snapshot_age_seconds),
        )
        _validate_count_domains(self)
        _validate_count_bounds(self)
        for name in (
            "source_quality_check_count",
            "memory_recall_check_count",
            "memory_item_count",
            "quality_memory_link_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "source_quality_pass_count",
            "memory_recall_pass_count",
            "stale_memory_item_count",
            "validated_quality_memory_link_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "source_quality_ratio",
            "memory_recall_ratio",
            "stale_memory_ratio",
            "quality_memory_alignment_ratio",
            "source_quality_memory_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self, config=config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(self)
        object.__setattr__(self, "_validation_config", config)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistSourceQualityMemoryReport:
    generated_at: datetime
    config_version: str
    min_pass_source_quality_ratio: Decimal
    min_watch_source_quality_ratio: Decimal
    min_pass_memory_recall_ratio: Decimal
    min_watch_memory_recall_ratio: Decimal
    max_pass_stale_memory_ratio: Decimal
    max_watch_stale_memory_ratio: Decimal
    min_pass_quality_memory_alignment_ratio: Decimal
    min_watch_quality_memory_alignment_ratio: Decimal
    status: str
    next_review_step: str
    observation_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    source_quality_check_count: Decimal
    source_quality_pass_count: Decimal
    memory_recall_check_count: Decimal
    memory_recall_pass_count: Decimal
    memory_item_count: Decimal
    stale_memory_item_count: Decimal
    quality_memory_link_count: Decimal
    validated_quality_memory_link_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    source_quality_ratio: Decimal
    memory_recall_ratio: Decimal
    stale_memory_ratio: Decimal
    quality_memory_alignment_ratio: Decimal
    source_quality_memory_score: Decimal
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamSpecialistSourceQualityMemoryConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistSourceQualityMemoryReport:
            raise TypeError(
                "ResearchTeamSpecialistSourceQualityMemoryReport does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchTeamSpecialistSourceQualityMemoryConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchTeamSpecialistSourceQualityMemoryReport, "report")
        config = _require_validation_config(validation_config)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        if self.config_version != config.config_version:
            raise ValueError("config_version must match validation_config")
        for name in (
            "min_pass_source_quality_ratio",
            "min_watch_source_quality_ratio",
            "min_pass_memory_recall_ratio",
            "min_watch_memory_recall_ratio",
            "max_pass_stale_memory_ratio",
            "max_watch_stale_memory_ratio",
            "min_pass_quality_memory_alignment_ratio",
            "min_watch_quality_memory_alignment_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
            if getattr(self, name) != getattr(config, name):
                raise ValueError(f"{name} must match validation_config")
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
            "source_quality_check_count",
            "source_quality_pass_count",
            "memory_recall_check_count",
            "memory_recall_pass_count",
            "memory_item_count",
            "stale_memory_item_count",
            "quality_memory_link_count",
            "validated_quality_memory_link_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "source_quality_ratio",
            "memory_recall_ratio",
            "stale_memory_ratio",
            "quality_memory_alignment_ratio",
            "source_quality_memory_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows, config=config))
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
        _validate_report(self, config=config)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(self)
        object.__setattr__(self, "_validation_config", config)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_specialist_source_quality_memory_report_payload(self)


def build_research_team_specialist_source_quality_memory_report(
    observations: Iterable[ResearchTeamSpecialistSourceQualityMemoryObservation],
    *,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistSourceQualityMemoryReport:
    cfg = _revalidate_config(
        config
        if config is not None
        else ResearchTeamSpecialistSourceQualityMemoryConfig(),
        "config",
    )
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
    return ResearchTeamSpecialistSourceQualityMemoryReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        min_pass_source_quality_ratio=cfg.min_pass_source_quality_ratio,
        min_watch_source_quality_ratio=cfg.min_watch_source_quality_ratio,
        min_pass_memory_recall_ratio=cfg.min_pass_memory_recall_ratio,
        min_watch_memory_recall_ratio=cfg.min_watch_memory_recall_ratio,
        max_pass_stale_memory_ratio=cfg.max_pass_stale_memory_ratio,
        max_watch_stale_memory_ratio=cfg.max_watch_stale_memory_ratio,
        min_pass_quality_memory_alignment_ratio=(
            cfg.min_pass_quality_memory_alignment_ratio
        ),
        min_watch_quality_memory_alignment_ratio=(
            cfg.min_watch_quality_memory_alignment_ratio
        ),
        status=status,
        next_review_step=NEXT_REVIEW_STEPS[status],
        observation_count=_count_decimal(len(normalized_observations)),
        team_count=_count_decimal(len({row.team_ref for row in rows})),
        specialist_count=_count_decimal(
            len({(row.team_ref, row.specialist_ref) for row in rows}),
        ),
        source_quality_check_count=_sum_decimal(
            row.source_quality_check_count for row in rows
        ),
        source_quality_pass_count=_sum_decimal(row.source_quality_pass_count for row in rows),
        memory_recall_check_count=_sum_decimal(row.memory_recall_check_count for row in rows),
        memory_recall_pass_count=_sum_decimal(row.memory_recall_pass_count for row in rows),
        memory_item_count=_sum_decimal(row.memory_item_count for row in rows),
        stale_memory_item_count=_sum_decimal(row.stale_memory_item_count for row in rows),
        quality_memory_link_count=_sum_decimal(row.quality_memory_link_count for row in rows),
        validated_quality_memory_link_count=_sum_decimal(
            row.validated_quality_memory_link_count for row in rows
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        source_quality_ratio=_aggregate_source_quality_ratio(rows),
        memory_recall_ratio=_aggregate_memory_recall_ratio(rows),
        stale_memory_ratio=_aggregate_stale_memory_ratio(rows),
        quality_memory_alignment_ratio=_aggregate_quality_memory_alignment_ratio(rows),
        source_quality_memory_score=_aggregate_source_quality_memory_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows, len(normalized_observations)),
        validation_config=cfg,
    )


def research_team_specialist_source_quality_memory_report_payload(
    value: object,
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    if type(value) is ResearchTeamSpecialistSourceQualityMemoryReport:
        rebuilt_report = _revalidate_report(value)
        payload = _payload_value(rebuilt_report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _validate_payload_flags(payload, "payload")
        _reject_unsafe_public_payload(payload)
        return payload

    payload = _require_public_payload_object(
        value,
        "payload",
        _public_payload_fields(ResearchTeamSpecialistSourceQualityMemoryReport),
    )
    _validate_payload_digest(payload)
    rebuilt_report = _report_from_public_payload(payload)
    canonical_payload = _payload_value(rebuilt_report)
    if type(canonical_payload) is not dict:
        raise ValueError("payload must be a dict")
    if canonical_payload != payload:
        raise ValueError("payload must use canonical public values and sequence")
    return canonical_payload


def research_team_specialist_source_quality_memory_report_digest(
    report: ResearchTeamSpecialistSourceQualityMemoryReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistSourceQualityMemoryReport:
        raise ValueError(
            "report must be exactly ResearchTeamSpecialistSourceQualityMemoryReport",
        )
    return _revalidate_report(report).derived_validation_digest


def _row_from_observation(
    observation: ResearchTeamSpecialistSourceQualityMemoryObservation,
    *,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistSourceQualityMemoryRow:
    source_quality_ratio = _safe_divide(
        observation.source_quality_pass_count,
        observation.source_quality_check_count,
    )
    memory_recall_ratio = _safe_divide(
        observation.memory_recall_pass_count,
        observation.memory_recall_check_count,
    )
    stale_memory_ratio = _safe_divide(
        observation.stale_memory_item_count,
        observation.memory_item_count,
    )
    quality_memory_alignment_ratio = _safe_divide(
        observation.validated_quality_memory_link_count,
        observation.quality_memory_link_count,
    )
    reason_codes = _row_reason_codes(
        source_quality_ratio=source_quality_ratio,
        memory_recall_ratio=memory_recall_ratio,
        stale_memory_ratio=stale_memory_ratio,
        quality_memory_alignment_ratio=quality_memory_alignment_ratio,
        config=config,
    )
    return ResearchTeamSpecialistSourceQualityMemoryRow(
        team_ref=observation.team_ref,
        specialist_ref=observation.specialist_ref,
        observed_at=observation.observed_at,
        snapshot_age_seconds=_age_seconds(generated_at, observation.observed_at),
        source_quality_check_count=observation.source_quality_check_count,
        source_quality_pass_count=observation.source_quality_pass_count,
        memory_recall_check_count=observation.memory_recall_check_count,
        memory_recall_pass_count=observation.memory_recall_pass_count,
        memory_item_count=observation.memory_item_count,
        stale_memory_item_count=observation.stale_memory_item_count,
        quality_memory_link_count=observation.quality_memory_link_count,
        validated_quality_memory_link_count=observation.validated_quality_memory_link_count,
        source_quality_ratio=source_quality_ratio,
        memory_recall_ratio=memory_recall_ratio,
        stale_memory_ratio=stale_memory_ratio,
        quality_memory_alignment_ratio=quality_memory_alignment_ratio,
        source_quality_memory_score=_source_quality_memory_score(
            source_quality_ratio=source_quality_ratio,
            memory_recall_ratio=memory_recall_ratio,
            stale_memory_ratio=stale_memory_ratio,
            quality_memory_alignment_ratio=quality_memory_alignment_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    source_quality_ratio: Decimal,
    memory_recall_ratio: Decimal,
    stale_memory_ratio: Decimal,
    quality_memory_alignment_ratio: Decimal,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_quality_ratio < config.min_watch_source_quality_ratio:
        reason_codes.append(SOURCE_QUALITY_BLOCK_REASON)
    elif source_quality_ratio < config.min_pass_source_quality_ratio:
        reason_codes.append(SOURCE_QUALITY_WATCH_REASON)
    if memory_recall_ratio < config.min_watch_memory_recall_ratio:
        reason_codes.append(MEMORY_RECALL_BLOCK_REASON)
    elif memory_recall_ratio < config.min_pass_memory_recall_ratio:
        reason_codes.append(MEMORY_RECALL_WATCH_REASON)
    if stale_memory_ratio > config.max_watch_stale_memory_ratio:
        reason_codes.append(STALE_MEMORY_BLOCK_REASON)
    elif stale_memory_ratio > config.max_pass_stale_memory_ratio:
        reason_codes.append(STALE_MEMORY_WATCH_REASON)
    if quality_memory_alignment_ratio < config.min_watch_quality_memory_alignment_ratio:
        reason_codes.append(QUALITY_MEMORY_ALIGNMENT_BLOCK_REASON)
    elif quality_memory_alignment_ratio < config.min_pass_quality_memory_alignment_ratio:
        reason_codes.append(QUALITY_MEMORY_ALIGNMENT_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
    observation_count: int,
) -> tuple[str, ...]:
    if observation_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if _row_reason_count(rows, (SOURCE_QUALITY_BLOCK_REASON, SOURCE_QUALITY_WATCH_REASON)):
        reason_codes.append(REPORT_SOURCE_QUALITY_GAP_REASON)
    if _row_reason_count(rows, (MEMORY_RECALL_BLOCK_REASON, MEMORY_RECALL_WATCH_REASON)):
        reason_codes.append(REPORT_MEMORY_RECALL_GAP_REASON)
    if _row_reason_count(rows, (STALE_MEMORY_BLOCK_REASON, STALE_MEMORY_WATCH_REASON)):
        reason_codes.append(REPORT_STALE_MEMORY_GAP_REASON)
    if _row_reason_count(
        rows,
        (
            QUALITY_MEMORY_ALIGNMENT_BLOCK_REASON,
            QUALITY_MEMORY_ALIGNMENT_WATCH_REASON,
        ),
    ):
        reason_codes.append(REPORT_ALIGNMENT_GAP_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _report_status(rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...]) -> str:
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
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
) -> tuple[ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount(
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
        ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
            row_ratio=_safe_divide(_count_decimal(counter[reason_code]), row_count),
        )
        for reason_code in COUNT_REASON_CODE_SEQUENCE
        if counter.get(reason_code, 0) > 0
    )


def _row_reason_count(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> int:
    return sum(1 for row in rows if any(item in row.reason_codes for item in reason_codes))


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistSourceQualityMemoryObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistSourceQualityMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    normalized: list[ResearchTeamSpecialistSourceQualityMemoryObservation] = []
    for item in observations:
        if type(item) is not ResearchTeamSpecialistSourceQualityMemoryObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchTeamSpecialistSourceQualityMemoryObservation",
            )
        rebuilt = ResearchTeamSpecialistSourceQualityMemoryObservation(
            **{field.name: getattr(item, field.name) for field in fields(item)},
        )
        if rebuilt.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        normalized.append(rebuilt)
    pairs = [(item.team_ref, item.specialist_ref) for item in normalized]
    if len(set(pairs)) != len(pairs):
        raise ValueError("team_ref and specialist_ref pairs must be unique")
    return tuple(sorted(normalized, key=lambda item: (item.team_ref, item.specialist_ref)))


def _normalize_rows(
    rows: object,
    *,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
) -> tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchTeamSpecialistSourceQualityMemoryRow] = []
    for row in rows:
        if type(row) is not ResearchTeamSpecialistSourceQualityMemoryRow:
            raise ValueError(
                "rows must contain exactly ResearchTeamSpecialistSourceQualityMemoryRow",
            )
        normalized.append(
            ResearchTeamSpecialistSourceQualityMemoryRow(
                **{field.name: getattr(row, field.name) for field in fields(row)},
                validation_config=config,
            ),
        )
    pairs = [(row.team_ref, row.specialist_ref) for row in normalized]
    if len(set(pairs)) != len(pairs):
        raise ValueError("team_ref and specialist_ref pairs must be unique")
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount] = []
    for value in values:
        if type(value) is not ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount",
            )
        normalized.append(
            ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount(
                **{field.name: getattr(value, field.name) for field in fields(value)},
            ),
        )
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                COUNT_REASON_CODE_SEQUENCE.index(item.reason_code),
                item.reason_code,
            ),
        ),
    )


def _normalize_reason_codes(
    name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_member(name, value, allowed_values))
    if not normalized:
        raise ValueError(f"{name} must be nonempty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _row_sort_key(
    row: ResearchTeamSpecialistSourceQualityMemoryRow,
) -> tuple[object, ...]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.source_quality_memory_score,
        row.source_quality_ratio,
        row.memory_recall_ratio,
        -row.stale_memory_ratio,
        row.quality_memory_alignment_ratio,
        -row.snapshot_age_seconds,
        row.team_ref,
        row.specialist_ref,
    )


def _validate_count_bounds(value: object) -> None:
    source_quality_pass_count = _require_decimal(
        "source_quality_pass_count",
        value.source_quality_pass_count,
    )
    source_quality_check_count = _require_decimal(
        "source_quality_check_count",
        value.source_quality_check_count,
    )
    memory_recall_pass_count = _require_decimal(
        "memory_recall_pass_count",
        value.memory_recall_pass_count,
    )
    memory_recall_check_count = _require_decimal(
        "memory_recall_check_count",
        value.memory_recall_check_count,
    )
    stale_memory_item_count = _require_decimal(
        "stale_memory_item_count",
        value.stale_memory_item_count,
    )
    memory_item_count = _require_decimal("memory_item_count", value.memory_item_count)
    validated_quality_memory_link_count = _require_decimal(
        "validated_quality_memory_link_count",
        value.validated_quality_memory_link_count,
    )
    quality_memory_link_count = _require_decimal(
        "quality_memory_link_count",
        value.quality_memory_link_count,
    )
    if source_quality_pass_count > source_quality_check_count:
        raise ValueError("source_quality_pass_count must not exceed check count")
    if memory_recall_pass_count > memory_recall_check_count:
        raise ValueError("memory_recall_pass_count must not exceed check count")
    if stale_memory_item_count > memory_item_count:
        raise ValueError("stale_memory_item_count must not exceed memory_item_count")
    if validated_quality_memory_link_count > quality_memory_link_count:
        raise ValueError(
            "validated_quality_memory_link_count must not exceed quality_memory_link_count",
        )


def _validate_count_domains(value: object) -> None:
    for name in (
        "source_quality_check_count",
        "memory_recall_check_count",
        "memory_item_count",
        "quality_memory_link_count",
    ):
        _require_positive_decimal(name, getattr(value, name))
    for name in (
        "source_quality_pass_count",
        "memory_recall_pass_count",
        "stale_memory_item_count",
        "validated_quality_memory_link_count",
    ):
        _require_nonnegative_decimal(name, getattr(value, name))


def _validate_row(
    row: ResearchTeamSpecialistSourceQualityMemoryRow,
    *,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
) -> None:
    if row.source_quality_ratio != _safe_divide(
        row.source_quality_pass_count,
        row.source_quality_check_count,
    ):
        raise ValueError("source_quality_ratio must match row counts")
    if row.memory_recall_ratio != _safe_divide(
        row.memory_recall_pass_count,
        row.memory_recall_check_count,
    ):
        raise ValueError("memory_recall_ratio must match row counts")
    if row.stale_memory_ratio != _safe_divide(
        row.stale_memory_item_count,
        row.memory_item_count,
    ):
        raise ValueError("stale_memory_ratio must match row counts")
    if row.quality_memory_alignment_ratio != _safe_divide(
        row.validated_quality_memory_link_count,
        row.quality_memory_link_count,
    ):
        raise ValueError("quality_memory_alignment_ratio must match row counts")
    expected_score = _source_quality_memory_score(
        source_quality_ratio=row.source_quality_ratio,
        memory_recall_ratio=row.memory_recall_ratio,
        stale_memory_ratio=row.stale_memory_ratio,
        quality_memory_alignment_ratio=row.quality_memory_alignment_ratio,
    )
    if row.source_quality_memory_score != expected_score:
        raise ValueError("source_quality_memory_score must match row ratios")
    expected_reason_codes = _row_reason_codes(
        source_quality_ratio=row.source_quality_ratio,
        memory_recall_ratio=row.memory_recall_ratio,
        stale_memory_ratio=row.stale_memory_ratio,
        quality_memory_alignment_ratio=row.quality_memory_alignment_ratio,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row ratios and validation_config")
    if row.status != _status_from_reason_codes(expected_reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchTeamSpecialistSourceQualityMemoryReport,
    *,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
) -> None:
    for row in report.rows:
        _validate_row(row, config=config)
        if row.snapshot_age_seconds != _age_seconds(report.generated_at, row.observed_at):
            raise ValueError("snapshot_age_seconds must match report timestamps")
    row_count = _count_decimal(len(report.rows))
    if report.observation_count != row_count:
        raise ValueError("observation_count must match rows")
    if report.team_count != _count_decimal(len({row.team_ref for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _count_decimal(
        len({(row.team_ref, row.specialist_ref) for row in report.rows}),
    ):
        raise ValueError("specialist_count must match rows")
    expected_totals = {
        "source_quality_check_count": _sum_decimal(
            row.source_quality_check_count for row in report.rows
        ),
        "source_quality_pass_count": _sum_decimal(
            row.source_quality_pass_count for row in report.rows
        ),
        "memory_recall_check_count": _sum_decimal(
            row.memory_recall_check_count for row in report.rows
        ),
        "memory_recall_pass_count": _sum_decimal(
            row.memory_recall_pass_count for row in report.rows
        ),
        "memory_item_count": _sum_decimal(row.memory_item_count for row in report.rows),
        "stale_memory_item_count": _sum_decimal(
            row.stale_memory_item_count for row in report.rows
        ),
        "quality_memory_link_count": _sum_decimal(
            row.quality_memory_link_count for row in report.rows
        ),
        "validated_quality_memory_link_count": _sum_decimal(
            row.validated_quality_memory_link_count for row in report.rows
        ),
    }
    for name, expected_value in expected_totals.items():
        if getattr(report, name) != expected_value:
            raise ValueError(f"{name} must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")
    expected_ratios = {
        "source_quality_ratio": _aggregate_source_quality_ratio(report.rows),
        "memory_recall_ratio": _aggregate_memory_recall_ratio(report.rows),
        "stale_memory_ratio": _aggregate_stale_memory_ratio(report.rows),
        "quality_memory_alignment_ratio": _aggregate_quality_memory_alignment_ratio(
            report.rows,
        ),
        "source_quality_memory_score": _aggregate_source_quality_memory_score(report.rows),
    }
    for name, expected_value in expected_ratios.items():
        if getattr(report, name) != expected_value:
            raise ValueError(f"{name} must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.observation_count)):
        raise ValueError("reason_codes must match rows")
    if (
        report.observation_count
        != report.pass_count + report.watch_count + report.block_count
    ):
        raise ValueError("status counts must sum to observation_count")


def _aggregate_source_quality_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.source_quality_pass_count for row in rows),
        _sum_decimal(row.source_quality_check_count for row in rows),
    )


def _aggregate_memory_recall_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.memory_recall_pass_count for row in rows),
        _sum_decimal(row.memory_recall_check_count for row in rows),
    )


def _aggregate_stale_memory_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.stale_memory_item_count for row in rows),
        _sum_decimal(row.memory_item_count for row in rows),
    )


def _aggregate_quality_memory_alignment_ratio(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.validated_quality_memory_link_count for row in rows),
        _sum_decimal(row.quality_memory_link_count for row in rows),
    )


def _aggregate_source_quality_memory_score(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    source_pass = _sum_decimal(row.source_quality_pass_count for row in rows)
    source_check = _sum_decimal(row.source_quality_check_count for row in rows)
    memory_pass = _sum_decimal(row.memory_recall_pass_count for row in rows)
    memory_check = _sum_decimal(row.memory_recall_check_count for row in rows)
    stale_memory = _sum_decimal(row.stale_memory_item_count for row in rows)
    memory_items = _sum_decimal(row.memory_item_count for row in rows)
    aligned = _sum_decimal(row.validated_quality_memory_link_count for row in rows)
    links = _sum_decimal(row.quality_memory_link_count for row in rows)
    if source_check == ZERO or memory_check == ZERO or memory_items == ZERO or links == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = (
            (source_pass / source_check)
            + (memory_pass / memory_check)
            + (ONE - (stale_memory / memory_items))
            + (aligned / links)
        ) / FOUR
    return _six(score)


def _source_quality_memory_score(
    *,
    source_quality_ratio: Decimal,
    memory_recall_ratio: Decimal,
    stale_memory_ratio: Decimal,
    quality_memory_alignment_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            source_quality_ratio
            + memory_recall_ratio
            + (ONE - stale_memory_ratio)
            + quality_memory_alignment_ratio
        ) / FOUR
    return _six(value)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return _six(total)


def _status_count(
    rows: tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _six(Decimal(value))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds) + (
            Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        )
    return _six(seconds)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    quantized = _six(normalized)
    if quantized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return quantized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _six(normalized)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_decimal(name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _six(raw_value)


def _six(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = (+value).quantize(DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonempty public label")
    _reject_unsafe_public_payload(value)
    return value


def _require_config_version(value: object) -> str:
    config_version = _require_public_label("config_version", value)
    if (
        config_version
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    return config_version


def _require_validation_config(
    value: ResearchTeamSpecialistSourceQualityMemoryConfig | None,
) -> ResearchTeamSpecialistSourceQualityMemoryConfig:
    return _revalidate_config(
        value
        if value is not None
        else ResearchTeamSpecialistSourceQualityMemoryConfig(),
        "validation_config",
    )


def _revalidate_config(
    value: object,
    name: str,
) -> ResearchTeamSpecialistSourceQualityMemoryConfig:
    if type(value) is not ResearchTeamSpecialistSourceQualityMemoryConfig:
        raise ValueError(
            f"{name} must be exactly "
            "ResearchTeamSpecialistSourceQualityMemoryConfig",
        )
    return ResearchTeamSpecialistSourceQualityMemoryConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_report(
    value: object,
) -> ResearchTeamSpecialistSourceQualityMemoryReport:
    _require_exact_type(
        value,
        ResearchTeamSpecialistSourceQualityMemoryReport,
        "report",
    )
    config = _require_validation_config(
        getattr(value, "_validation_config", None),
    )
    return ResearchTeamSpecialistSourceQualityMemoryReport(
        **{field.name: getattr(value, field.name) for field in fields(value)},
        validation_config=config,
    )


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed_values:
        joined = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of {joined}")
    return value


def _require_status(name: str, value: object) -> str:
    return _require_member(name, value, RESEARCH_TEAM_SPECIALIST_SOURCE_QUALITY_MEMORY_STATUSES)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {name}")


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    return value


def _require_supported_payload_input(value: object) -> None:
    if type(value) not in (ResearchTeamSpecialistSourceQualityMemoryReport, dict):
        raise ValueError(
            "value must be exactly ResearchTeamSpecialistSourceQualityMemoryReport or dict",
        )


def _report_from_public_payload(
    value: object,
) -> ResearchTeamSpecialistSourceQualityMemoryReport:
    payload = _require_public_payload_object(
        value,
        "payload",
        _public_payload_fields(ResearchTeamSpecialistSourceQualityMemoryReport),
    )
    config_version = _require_config_version(payload["config_version"])
    config_ratio_names = (
        "min_pass_source_quality_ratio",
        "min_watch_source_quality_ratio",
        "min_pass_memory_recall_ratio",
        "min_watch_memory_recall_ratio",
        "max_pass_stale_memory_ratio",
        "max_watch_stale_memory_ratio",
        "min_pass_quality_memory_alignment_ratio",
        "min_watch_quality_memory_alignment_ratio",
    )
    config_values = {
        name: _public_ratio_decimal(name, payload[name])
        for name in config_ratio_names
    }
    config = ResearchTeamSpecialistSourceQualityMemoryConfig(
        config_version=config_version,
        **config_values,
    )
    count_names = (
        "observation_count",
        "team_count",
        "specialist_count",
        "source_quality_check_count",
        "source_quality_pass_count",
        "memory_recall_check_count",
        "memory_recall_pass_count",
        "memory_item_count",
        "stale_memory_item_count",
        "quality_memory_link_count",
        "validated_quality_memory_link_count",
        "pass_count",
        "watch_count",
        "block_count",
    )
    ratio_names = (
        "source_quality_ratio",
        "memory_recall_ratio",
        "stale_memory_ratio",
        "quality_memory_alignment_ratio",
        "source_quality_memory_score",
    )
    numeric_values = {
        name: _public_nonnegative_decimal(name, payload[name])
        for name in count_names
    }
    numeric_values.update(
        {
            name: _public_ratio_decimal(name, payload[name])
            for name in ratio_names
        },
    )
    return ResearchTeamSpecialistSourceQualityMemoryReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=config_version,
        **config_values,
        status=_require_status("status", payload["status"]),
        next_review_step=_require_public_label(
            "next_review_step",
            payload["next_review_step"],
        ),
        rows=_public_rows(payload["rows"], config=config),
        reason_code_counts=_public_reason_code_counts(
            payload["reason_code_counts"],
        ),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODE_SEQUENCE,
        ),
        derived_validation_digest=_require_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=config,
        **numeric_values,
    )


def _public_rows(
    value: object,
    *,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
) -> tuple[ResearchTeamSpecialistSourceQualityMemoryRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a plain public list")
    rows = tuple(
        _public_row(item, index=index, config=config)
        for index, item in enumerate(value)
    )
    normalized = _normalize_rows(rows, config=config)
    if rows != normalized:
        raise ValueError("rows must use canonical deterministic sequence")
    return rows


def _public_row(
    value: object,
    *,
    index: int,
    config: ResearchTeamSpecialistSourceQualityMemoryConfig,
) -> ResearchTeamSpecialistSourceQualityMemoryRow:
    path = f"rows[{index}]"
    payload = _require_public_payload_object(
        value,
        path,
        _public_payload_fields(ResearchTeamSpecialistSourceQualityMemoryRow),
    )
    positive_count_names = (
        "source_quality_check_count",
        "memory_recall_check_count",
        "memory_item_count",
        "quality_memory_link_count",
    )
    nonnegative_count_names = (
        "snapshot_age_seconds",
        "source_quality_pass_count",
        "memory_recall_pass_count",
        "stale_memory_item_count",
        "validated_quality_memory_link_count",
    )
    ratio_names = (
        "source_quality_ratio",
        "memory_recall_ratio",
        "stale_memory_ratio",
        "quality_memory_alignment_ratio",
        "source_quality_memory_score",
    )
    numeric_values = {
        name: _public_positive_decimal(f"{path}.{name}", payload[name])
        for name in positive_count_names
    }
    numeric_values.update(
        {
            name: _public_nonnegative_decimal(f"{path}.{name}", payload[name])
            for name in nonnegative_count_names
        },
    )
    numeric_values.update(
        {
            name: _public_ratio_decimal(f"{path}.{name}", payload[name])
            for name in ratio_names
        },
    )
    return ResearchTeamSpecialistSourceQualityMemoryRow(
        team_ref=_require_public_label(f"{path}.team_ref", payload["team_ref"]),
        specialist_ref=_require_public_label(
            f"{path}.specialist_ref",
            payload["specialist_ref"],
        ),
        observed_at=_public_datetime(f"{path}.observed_at", payload["observed_at"]),
        status=_require_status(f"{path}.status", payload["status"]),
        reason_codes=_public_reason_codes(
            f"{path}.reason_codes",
            payload["reason_codes"],
            ROW_REASON_CODE_SEQUENCE,
        ),
        paper_only=_public_true_flag(f"{path}.paper_only", payload["paper_only"]),
        report_only=_public_true_flag(f"{path}.report_only", payload["report_only"]),
        readonly=_public_true_flag(f"{path}.readonly", payload["readonly"]),
        validation_config=config,
        **numeric_values,
    )


def _public_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a plain public list")
    values = tuple(
        _public_reason_code_count(item, index=index)
        for index, item in enumerate(value)
    )
    normalized = _normalize_reason_code_counts(values)
    if values != normalized:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _public_reason_code_count(
    value: object,
    *,
    index: int,
) -> ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount:
    path = f"reason_code_counts[{index}]"
    payload = _require_public_payload_object(
        value,
        path,
        _public_payload_fields(
            ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount,
        ),
    )
    return ResearchTeamSpecialistSourceQualityMemoryReasonCodeCount(
        reason_code=_require_member(
            f"{path}.reason_code",
            payload["reason_code"],
            COUNT_REASON_CODE_SEQUENCE,
        ),
        count=_public_positive_decimal(f"{path}.count", payload["count"]),
        row_ratio=_public_ratio_decimal(f"{path}.row_ratio", payload["row_ratio"]),
        paper_only=_public_true_flag(f"{path}.paper_only", payload["paper_only"]),
        report_only=_public_true_flag(f"{path}.report_only", payload["report_only"]),
        readonly=_public_true_flag(f"{path}.readonly", payload["readonly"]),
    )


def _public_payload_fields(dataclass_type: type[object]) -> tuple[str, ...]:
    return tuple(item.name for item in fields(dataclass_type))


def _require_public_payload_object(
    value: object,
    path: str,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{path} must be a plain public object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{path} keys must be strings")
    for field_name in expected_fields:
        if field_name not in value:
            raise ValueError(f"{path}.{field_name} is required")
    expected = frozenset(expected_fields)
    for field_name in value:
        if field_name not in expected:
            raise ValueError(f"{path}.{field_name} is unexpected")
    if tuple(value) != expected_fields:
        raise ValueError(f"{path} must use canonical key sequence")
    return value


def _public_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical Decimal-derived string")
    try:
        with localcontext(DECIMAL_CONTEXT):
            decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a canonical Decimal-derived string") from exc
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    try:
        normalized = _six(decimal_value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a canonical Decimal-derived string") from exc
    if not decimal_value.is_finite() or value != str(normalized):
        raise ValueError(f"{name} must be a canonical Decimal-derived string")
    return normalized


def _public_positive_decimal(name: str, value: object) -> Decimal:
    return _require_positive_decimal(name, _public_decimal(name, value))


def _public_nonnegative_decimal(name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(name, _public_decimal(name, value))


def _public_ratio_decimal(name: str, value: object) -> Decimal:
    return _require_ratio_decimal(name, _public_decimal(name, value))


def _public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _public_reason_codes(
    name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a plain public list")
    raw_values = tuple(
        _require_member(name, item, allowed_values)
        for item in value
    )
    normalized = _normalize_reason_codes(name, raw_values, allowed_values)
    if raw_values != normalized:
        raise ValueError(f"{name} must use canonical sequence without duplicates")
    return normalized


def _public_true_flag(name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{name} must be True")
    return True


def _validate_payload_flags(payload: object, label: str) -> None:
    if type(payload) is dict:
        if payload.get("paper_only") is not True:
            raise ValueError(f"paper_only must be True for {label}")
        if payload.get("report_only") is not True:
            raise ValueError(f"report_only must be True for {label}")
        if payload.get("readonly") is not True:
            raise ValueError(f"readonly must be True for {label}")
        for item in payload.values():
            _validate_payload_flags(item, label)
    elif type(payload) is list:
        for item in payload:
            _validate_payload_flags(item, label)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(
    report: ResearchTeamSpecialistSourceQualityMemoryReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _canonical_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return str(_six(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime value must be exactly datetime")
        return _as_utc("payload datetime", value).isoformat()
    if isinstance(value, (bool, str)) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not payload serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(part in lowered for part in _BLOCKED_PARTS):
            raise ValueError("unsafe public payload")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if any(part in key.lower() for part in _BLOCKED_PARTS):
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(item)
