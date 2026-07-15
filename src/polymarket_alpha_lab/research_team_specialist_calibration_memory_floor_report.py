"""Public-safe calibration memory floor report for research team specialists."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION = (
    "research-team-specialist-calibration-memory-floor-report-v1"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
CALIBRATION_MEMORY_FLOOR_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

NO_INPUTS_REASON = "team_specialist_calibration_memory_floor_no_inputs"
PASS_REASON = "team_specialist_calibration_memory_floor_pass"
FLOOR_BLOCK_REASON = "team_specialist_calibration_memory_floor_below_watch"
FLOOR_WATCH_REASON = "team_specialist_calibration_memory_floor_between_watch_and_pass"
CALIBRATION_BLOCK_REASON = "team_specialist_calibration_score_below_watch"
CALIBRATION_WATCH_REASON = "team_specialist_calibration_score_watch"
MEMORY_RECALL_BLOCK_REASON = "team_specialist_memory_recall_below_watch"
MEMORY_RECALL_WATCH_REASON = "team_specialist_memory_recall_watch"
MEMORY_AGE_BLOCK_REASON = "team_specialist_memory_age_above_watch"
MEMORY_AGE_WATCH_REASON = "team_specialist_memory_age_watch"
UNCALIBRATED_RATIO_BLOCK_REASON = (
    "team_specialist_uncalibrated_ratio_above_watch"
)
UNCALIBRATED_RATIO_WATCH_REASON = "team_specialist_uncalibrated_ratio_watch"

REASON_CODE_SEQUENCE = (
    FLOOR_BLOCK_REASON,
    CALIBRATION_BLOCK_REASON,
    MEMORY_RECALL_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    UNCALIBRATED_RATIO_BLOCK_REASON,
    FLOOR_WATCH_REASON,
    CALIBRATION_WATCH_REASON,
    MEMORY_RECALL_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    UNCALIBRATED_RATIO_WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
BLOCK_REASONS = (
    FLOOR_BLOCK_REASON,
    CALIBRATION_BLOCK_REASON,
    MEMORY_RECALL_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    UNCALIBRATED_RATIO_BLOCK_REASON,
)
NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_team_specialist_calibration_memory_floor",
    STATUS_WATCH: "watch_report_only_team_specialist_calibration_memory_floor",
    STATUS_BLOCK: "block_report_only_team_specialist_calibration_memory_floor",
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]{0,56})\.[0-9]{6}$")
HEX_CHARS = frozenset("0123456789abcdef")

REPORT_PAYLOAD_SCHEMA = (
    "generated_at",
    "config_version",
    "status",
    "next_step",
    "team_specialist_count",
    "pass_count",
    "watch_count",
    "block_count",
    "floor_breach_count",
    "floor_breach_ratio",
    "average_calibration_memory_floor_score",
    "lowest_calibration_memory_floor_score",
    "max_memory_age_seconds",
    "max_uncalibrated_specialist_ratio",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_SCHEMA = (
    "floor_rank",
    "team_label",
    "specialist_label",
    "observed_at",
    "calibration_score",
    "memory_recall_score",
    "memory_age_seconds",
    "memory_recency_score",
    "uncalibrated_specialist_ratio",
    "calibration_memory_floor_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_SCHEMA = (
    "reason_code",
    "count",
    "team_specialist_ratio",
    "paper_only",
    "report_only",
    "readonly",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_LABEL_FRAGMENTS = frozenset(
    (
        _join_parts("raw"),
        _join_parts("cand", "idate"),
        _join_parts("mar", "ket"),
        _join_parts("slug"),
        _join_parts("ques", "tion"),
        _join_parts("sour", "ce"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("au", "th"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
        _join_parts("pos", "ition"),
        _join_parts("li", "ve"),
        _join_parts("trad", "ing"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION",
    "CALIBRATION_MEMORY_FLOOR_STATUSES",
    "ResearchTeamSpecialistCalibrationMemoryFloorConfig",
    "ResearchTeamSpecialistCalibrationMemoryFloorObservation",
    "ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount",
    "ResearchTeamSpecialistCalibrationMemoryFloorReport",
    "ResearchTeamSpecialistCalibrationMemoryFloorRow",
    "build_research_team_specialist_calibration_memory_floor_report",
    "research_team_specialist_calibration_memory_floor_report_digest",
    "research_team_specialist_calibration_memory_floor_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationMemoryFloorConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION
    )
    min_pass_calibration_memory_floor_score: Decimal = Decimal("0.750000")
    min_watch_calibration_memory_floor_score: Decimal = Decimal("0.500000")
    min_pass_calibration_score: Decimal = Decimal("0.750000")
    min_watch_calibration_score: Decimal = Decimal("0.500000")
    min_pass_memory_recall_score: Decimal = Decimal("0.750000")
    min_watch_memory_recall_score: Decimal = Decimal("0.500000")
    max_pass_memory_age_seconds: Decimal = Decimal("604800.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("2592000.000000")
    max_pass_uncalibrated_specialist_ratio: Decimal = Decimal("0.200000")
    max_watch_uncalibrated_specialist_ratio: Decimal = Decimal("0.500000")
    calibration_score_weight: Decimal = Decimal("0.400000")
    memory_recall_weight: Decimal = Decimal("0.400000")
    memory_recency_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationMemoryFloorConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_calibration_memory_floor_score",
            "min_watch_calibration_memory_floor_score",
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "min_pass_memory_recall_score",
            "min_watch_memory_recall_score",
            "max_pass_uncalibrated_specialist_ratio",
            "max_watch_uncalibrated_specialist_ratio",
            "calibration_score_weight",
            "memory_recall_weight",
            "memory_recency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_calibration_memory_floor_score
            <= self.min_watch_calibration_memory_floor_score
        ):
            raise ValueError(
                "min_pass_calibration_memory_floor_score must be greater than "
                "min_watch_calibration_memory_floor_score",
            )
        _require_pass_at_least_watch(
            "min_pass_calibration_score",
            self.min_pass_calibration_score,
            "min_watch_calibration_score",
            self.min_watch_calibration_score,
        )
        _require_pass_at_least_watch(
            "min_pass_memory_recall_score",
            self.min_pass_memory_recall_score,
            "min_watch_memory_recall_score",
            self.min_watch_memory_recall_score,
        )
        _require_watch_at_least_pass(
            "max_watch_memory_age_seconds",
            self.max_watch_memory_age_seconds,
            "max_pass_memory_age_seconds",
            self.max_pass_memory_age_seconds,
        )
        _require_watch_at_least_pass(
            "max_watch_uncalibrated_specialist_ratio",
            self.max_watch_uncalibrated_specialist_ratio,
            "max_pass_uncalibrated_specialist_ratio",
            self.max_pass_uncalibrated_specialist_ratio,
        )
        if self.max_watch_memory_age_seconds <= ZERO:
            raise ValueError("max_watch_memory_age_seconds must be positive")
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = _quantize_decimal(
                self.calibration_score_weight
                + self.memory_recall_weight
                + self.memory_recency_weight,
            )
        if weight_sum != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationMemoryFloorObservation(_FinalDataclass):
    team_label: str
    specialist_label: str
    calibration_score: Decimal
    memory_recall_score: Decimal
    memory_age_seconds: Decimal
    uncalibrated_specialist_ratio: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationMemoryFloorObservation,
            "observation",
        )
        _require_public_label("team_label", self.team_label)
        _require_public_label("specialist_label", self.specialist_label)
        for field_name in (
            "calibration_score",
            "memory_recall_score",
            "uncalibrated_specialist_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc_exact("observed_at", self.observed_at),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationMemoryFloorRow(_FinalDataclass):
    floor_rank: Decimal
    team_label: str
    specialist_label: str
    observed_at: datetime
    calibration_score: Decimal
    memory_recall_score: Decimal
    memory_age_seconds: Decimal
    memory_recency_score: Decimal
    uncalibrated_specialist_ratio: Decimal
    calibration_memory_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamSpecialistCalibrationMemoryFloorConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchTeamSpecialistCalibrationMemoryFloorConfig | None,
    ) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationMemoryFloorRow,
            "row",
        )
        object.__setattr__(
            self,
            "floor_rank",
            _require_count_decimal("floor_rank", self.floor_rank),
        )
        _require_public_label("team_label", self.team_label)
        _require_public_label("specialist_label", self.specialist_label)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc_exact("observed_at", self.observed_at),
        )
        for field_name in (
            "calibration_score",
            "memory_recall_score",
            "memory_recency_score",
            "uncalibrated_specialist_ratio",
            "calibration_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _validate_row(self, validation_config)
        object.__setattr__(
            self,
            "_validation_config",
            validation_config or ResearchTeamSpecialistCalibrationMemoryFloorConfig(),
        )
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    team_specialist_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "team_specialist_ratio",
            _require_ratio_decimal(
                "team_specialist_ratio",
                self.team_specialist_ratio,
            ),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationMemoryFloorReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    status: str
    next_step: str
    team_specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    floor_breach_count: Decimal
    floor_breach_ratio: Decimal
    average_calibration_memory_floor_score: Decimal | None
    lowest_calibration_memory_floor_score: Decimal | None
    max_memory_age_seconds: Decimal | None
    max_uncalibrated_specialist_ratio: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationMemoryFloorReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc_exact("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_MEMORY_FLOOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_public_string("next_step", self.next_step)
        if self.next_step != NEXT_STEPS[self.status]:
            raise ValueError("next_step must match status")
        for field_name in (
            "team_specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "floor_breach_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "floor_breach_ratio",
            _require_ratio_decimal("floor_breach_ratio", self.floor_breach_ratio),
        )
        for field_name in (
            "average_calibration_memory_floor_score",
            "lowest_calibration_memory_floor_score",
            "max_uncalibrated_specialist_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_optional_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_specialist_calibration_memory_floor_report(
    observations: Iterable[ResearchTeamSpecialistCalibrationMemoryFloorObservation],
    *,
    config: ResearchTeamSpecialistCalibrationMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistCalibrationMemoryFloorReport:
    _require_exact_type(
        config,
        ResearchTeamSpecialistCalibrationMemoryFloorConfig,
        "config",
    )
    config.__post_init__()
    generated_at_utc = _as_utc_exact("generated_at", generated_at)
    items = _normalize_observations(observations, generated_at_utc)
    built_rows = tuple(_row_from_observation(item, config) for item in items)
    rows = _ranked_rows(built_rows)
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": status,
        "next_step": NEXT_STEPS[status],
        "team_specialist_count": _count(len(rows)),
        "pass_count": _count(_status_count(rows, STATUS_PASS)),
        "watch_count": _count(_status_count(rows, STATUS_WATCH)),
        "block_count": _count(_status_count(rows, STATUS_BLOCK)),
        "floor_breach_count": _count(
            sum(1 for row in rows if row.status in (STATUS_WATCH, STATUS_BLOCK)),
        ),
        "floor_breach_ratio": _ratio(
            _count(sum(1 for row in rows if row.status in (STATUS_WATCH, STATUS_BLOCK))),
            _count(len(rows)),
        ),
        "average_calibration_memory_floor_score": _average_or_none(
            row.calibration_memory_floor_score for row in rows
        ),
        "lowest_calibration_memory_floor_score": min(
            (row.calibration_memory_floor_score for row in rows),
            default=None,
        ),
        "max_memory_age_seconds": max(
            (row.memory_age_seconds for row in rows),
            default=None,
        ),
        "max_uncalibrated_specialist_ratio": max(
            (row.uncalibrated_specialist_ratio for row in rows),
            default=None,
        ),
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistCalibrationMemoryFloorReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_specialist_calibration_memory_floor_report_payload(
    report: ResearchTeamSpecialistCalibrationMemoryFloorReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamSpecialistCalibrationMemoryFloorReport:
        report.__post_init__()
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _payload_from_public_mapping(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistCalibrationMemoryFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_specialist_calibration_memory_floor_report_digest(
    report: ResearchTeamSpecialistCalibrationMemoryFloorReport | Mapping[str, object],
) -> str:
    payload = research_team_specialist_calibration_memory_floor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _payload_from_public_mapping(report: dict[str, object]) -> dict[str, object]:
    _reject_unsafe_public_payload(
        "report payload",
        report,
        allow_json_containers=True,
    )
    _require_mapping_schema("report payload", report, REPORT_PAYLOAD_SCHEMA)
    _require_sha256(
        "derived_validation_digest",
        report["derived_validation_digest"],  # type: ignore[arg-type]
    )
    if report["derived_validation_digest"] != _digest_from_payload(report):
        raise ValueError("derived_validation_digest does not match report payload")

    rows_value = _require_public_list("rows", report["rows"])
    rows = tuple(
        _row_from_public_mapping(item, index)
        for index, item in enumerate(rows_value)
    )
    counts_value = _require_public_list(
        "reason_code_counts",
        report["reason_code_counts"],
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_mapping(item, index)
        for index, item in enumerate(counts_value)
    )
    reconstructed = ResearchTeamSpecialistCalibrationMemoryFloorReport(
        generated_at=_public_datetime("generated_at", report["generated_at"]),
        config_version=_public_string("config_version", report["config_version"]),
        status=_public_string("status", report["status"]),
        next_step=_public_string("next_step", report["next_step"]),
        team_specialist_count=_public_decimal(
            "team_specialist_count",
            report["team_specialist_count"],
        ),
        pass_count=_public_decimal("pass_count", report["pass_count"]),
        watch_count=_public_decimal("watch_count", report["watch_count"]),
        block_count=_public_decimal("block_count", report["block_count"]),
        floor_breach_count=_public_decimal(
            "floor_breach_count",
            report["floor_breach_count"],
        ),
        floor_breach_ratio=_public_decimal(
            "floor_breach_ratio",
            report["floor_breach_ratio"],
        ),
        average_calibration_memory_floor_score=_public_optional_decimal(
            "average_calibration_memory_floor_score",
            report["average_calibration_memory_floor_score"],
        ),
        lowest_calibration_memory_floor_score=_public_optional_decimal(
            "lowest_calibration_memory_floor_score",
            report["lowest_calibration_memory_floor_score"],
        ),
        max_memory_age_seconds=_public_optional_decimal(
            "max_memory_age_seconds",
            report["max_memory_age_seconds"],
        ),
        max_uncalibrated_specialist_ratio=_public_optional_decimal(
            "max_uncalibrated_specialist_ratio",
            report["max_uncalibrated_specialist_ratio"],
        ),
        reason_codes=_public_reason_codes("reason_codes", report["reason_codes"]),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=report["derived_validation_digest"],  # type: ignore[arg-type]
        paper_only=_public_true("paper_only", report["paper_only"]),
        report_only=_public_true("report_only", report["report_only"]),
        readonly=_public_true("readonly", report["readonly"]),
    )
    payload = _json_ready(asdict(reconstructed))
    if type(payload) is not dict or payload != report:
        raise ValueError("report payload must use the canonical schema and values")
    return payload


def _row_from_public_mapping(
    value: object,
    index: int,
) -> ResearchTeamSpecialistCalibrationMemoryFloorRow:
    path = f"rows[{index}]"
    row = _require_public_mapping(path, value)
    _require_mapping_schema(path, row, ROW_PAYLOAD_SCHEMA)
    return ResearchTeamSpecialistCalibrationMemoryFloorRow(
        floor_rank=_public_decimal(f"{path}.floor_rank", row["floor_rank"]),
        team_label=_public_string(f"{path}.team_label", row["team_label"]),
        specialist_label=_public_string(
            f"{path}.specialist_label",
            row["specialist_label"],
        ),
        observed_at=_public_datetime(f"{path}.observed_at", row["observed_at"]),
        calibration_score=_public_decimal(
            f"{path}.calibration_score",
            row["calibration_score"],
        ),
        memory_recall_score=_public_decimal(
            f"{path}.memory_recall_score",
            row["memory_recall_score"],
        ),
        memory_age_seconds=_public_decimal(
            f"{path}.memory_age_seconds",
            row["memory_age_seconds"],
        ),
        memory_recency_score=_public_decimal(
            f"{path}.memory_recency_score",
            row["memory_recency_score"],
        ),
        uncalibrated_specialist_ratio=_public_decimal(
            f"{path}.uncalibrated_specialist_ratio",
            row["uncalibrated_specialist_ratio"],
        ),
        calibration_memory_floor_score=_public_decimal(
            f"{path}.calibration_memory_floor_score",
            row["calibration_memory_floor_score"],
        ),
        status=_public_string(f"{path}.status", row["status"]),
        reason_codes=_public_reason_codes(
            f"{path}.reason_codes",
            row["reason_codes"],
        ),
        paper_only=_public_true(f"{path}.paper_only", row["paper_only"]),
        report_only=_public_true(f"{path}.report_only", row["report_only"]),
        readonly=_public_true(f"{path}.readonly", row["readonly"]),
    )


def _reason_code_count_from_public_mapping(
    value: object,
    index: int,
) -> ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount:
    path = f"reason_code_counts[{index}]"
    item = _require_public_mapping(path, value)
    _require_mapping_schema(path, item, REASON_CODE_COUNT_PAYLOAD_SCHEMA)
    return ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount(
        reason_code=_public_string(f"{path}.reason_code", item["reason_code"]),
        count=_public_decimal(f"{path}.count", item["count"]),
        team_specialist_ratio=_public_decimal(
            f"{path}.team_specialist_ratio",
            item["team_specialist_ratio"],
        ),
        paper_only=_public_true(f"{path}.paper_only", item["paper_only"]),
        report_only=_public_true(f"{path}.report_only", item["report_only"]),
        readonly=_public_true(f"{path}.readonly", item["readonly"]),
    )


def _require_mapping_schema(
    path: str,
    value: dict[str, object],
    schema: tuple[str, ...],
) -> None:
    if tuple(value.keys()) != schema:
        raise ValueError(f"{path} must use the exact canonical schema and key order")


def _require_public_mapping(path: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{path} must be a JSON object")
    return value


def _require_public_list(path: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a JSON list")
    return value


def _public_string(path: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be a string")
    return value


def _public_decimal(path: str, value: object) -> Decimal:
    if type(value) is not str or not PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{path} must be a canonical finite Decimal string")
    return Decimal(value)


def _public_optional_decimal(path: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _public_decimal(path, value)


def _public_datetime(path: str, value: object) -> datetime:
    text = _public_string(path, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical UTC datetime") from exc
    if type(parsed) is not datetime or parsed.tzinfo is not UTC or parsed.isoformat() != text:
        raise ValueError(f"{path} must be a canonical UTC datetime")
    return parsed


def _public_reason_codes(path: str, value: object) -> tuple[str, ...]:
    items = _require_public_list(path, value)
    if any(type(item) is not str for item in items):
        raise ValueError(f"{path} must contain strings")
    return tuple(items)  # type: ignore[arg-type]


def _public_true(path: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _row_from_observation(
    item: ResearchTeamSpecialistCalibrationMemoryFloorObservation,
    config: ResearchTeamSpecialistCalibrationMemoryFloorConfig,
) -> ResearchTeamSpecialistCalibrationMemoryFloorRow:
    memory_recency_score = _memory_recency_score(item.memory_age_seconds, config)
    floor_score = _calibration_memory_floor_score(
        calibration_score=item.calibration_score,
        memory_recall_score=item.memory_recall_score,
        memory_recency_score=memory_recency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        calibration_score=item.calibration_score,
        memory_recall_score=item.memory_recall_score,
        memory_age_seconds=item.memory_age_seconds,
        uncalibrated_specialist_ratio=item.uncalibrated_specialist_ratio,
        calibration_memory_floor_score=floor_score,
        config=config,
    )
    return ResearchTeamSpecialistCalibrationMemoryFloorRow(
        floor_rank=ONE,
        team_label=item.team_label,
        specialist_label=item.specialist_label,
        observed_at=item.observed_at,
        calibration_score=item.calibration_score,
        memory_recall_score=item.memory_recall_score,
        memory_age_seconds=item.memory_age_seconds,
        memory_recency_score=memory_recency_score,
        uncalibrated_specialist_ratio=item.uncalibrated_specialist_ratio,
        calibration_memory_floor_score=floor_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _with_rank(
    row: ResearchTeamSpecialistCalibrationMemoryFloorRow,
    rank: int,
) -> ResearchTeamSpecialistCalibrationMemoryFloorRow:
    return ResearchTeamSpecialistCalibrationMemoryFloorRow(
        floor_rank=_count(rank),
        team_label=row.team_label,
        specialist_label=row.specialist_label,
        observed_at=row.observed_at,
        calibration_score=row.calibration_score,
        memory_recall_score=row.memory_recall_score,
        memory_age_seconds=row.memory_age_seconds,
        memory_recency_score=row.memory_recency_score,
        uncalibrated_specialist_ratio=row.uncalibrated_specialist_ratio,
        calibration_memory_floor_score=row.calibration_memory_floor_score,
        status=row.status,
        reason_codes=row.reason_codes,
        validation_config=getattr(row, "_validation_config", None),
    )


def _row_reason_codes(
    *,
    calibration_score: Decimal,
    memory_recall_score: Decimal,
    memory_age_seconds: Decimal,
    uncalibrated_specialist_ratio: Decimal,
    calibration_memory_floor_score: Decimal,
    config: ResearchTeamSpecialistCalibrationMemoryFloorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if calibration_memory_floor_score < config.min_watch_calibration_memory_floor_score:
        reason_codes.append(FLOOR_BLOCK_REASON)
    elif calibration_memory_floor_score < config.min_pass_calibration_memory_floor_score:
        reason_codes.append(FLOOR_WATCH_REASON)
    if calibration_score < config.min_watch_calibration_score:
        reason_codes.append(CALIBRATION_BLOCK_REASON)
    elif calibration_score < config.min_pass_calibration_score:
        reason_codes.append(CALIBRATION_WATCH_REASON)
    if memory_recall_score < config.min_watch_memory_recall_score:
        reason_codes.append(MEMORY_RECALL_BLOCK_REASON)
    elif memory_recall_score < config.min_pass_memory_recall_score:
        reason_codes.append(MEMORY_RECALL_WATCH_REASON)
    if memory_age_seconds > config.max_watch_memory_age_seconds:
        reason_codes.append(MEMORY_AGE_BLOCK_REASON)
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        reason_codes.append(MEMORY_AGE_WATCH_REASON)
    if (
        uncalibrated_specialist_ratio
        > config.max_watch_uncalibrated_specialist_ratio
    ):
        reason_codes.append(UNCALIBRATED_RATIO_BLOCK_REASON)
    elif (
        uncalibrated_specialist_ratio
        > config.max_pass_uncalibrated_specialist_ratio
    ):
        reason_codes.append(UNCALIBRATED_RATIO_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...]:
    return tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(
    row: ResearchTeamSpecialistCalibrationMemoryFloorRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        row.calibration_memory_floor_score,
        row.calibration_score,
        row.memory_recall_score,
        -row.memory_age_seconds,
        -row.uncalibrated_specialist_ratio,
        row.observed_at,
        row.team_label,
        row.specialist_label,
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_specialist_ratio=ONE,
            ),
        )
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            team_specialist_ratio=_ratio(_count(counter[reason_code]), total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _memory_recency_score(
    memory_age_seconds: Decimal,
    config: ResearchTeamSpecialistCalibrationMemoryFloorConfig,
) -> Decimal:
    if memory_age_seconds >= config.max_watch_memory_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = ONE - _ratio(memory_age_seconds, config.max_watch_memory_age_seconds)
    return _clamp_ratio(value)


def _calibration_memory_floor_score(
    *,
    calibration_score: Decimal,
    memory_recall_score: Decimal,
    memory_recency_score: Decimal,
    config: ResearchTeamSpecialistCalibrationMemoryFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            calibration_score * config.calibration_score_weight
            + memory_recall_score * config.memory_recall_weight
            + memory_recency_score * config.memory_recency_weight
        )
        value = _quantize_decimal(value)
    return _require_ratio_decimal("calibration_memory_floor_score", value)


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistCalibrationMemoryFloorObservation],
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistCalibrationMemoryFloorObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    items = tuple(observations)
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistCalibrationMemoryFloorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamSpecialistCalibrationMemoryFloorObservation",
            )
        item.__post_init__()
        if item.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        key = (item.team_label, item.specialist_label)
        if key in seen:
            raise ValueError("team and specialist labels must be unique")
        seen.add(key)
    return items


def _validate_row(
    row: ResearchTeamSpecialistCalibrationMemoryFloorRow,
    config: ResearchTeamSpecialistCalibrationMemoryFloorConfig | None,
) -> None:
    cfg = config or ResearchTeamSpecialistCalibrationMemoryFloorConfig()
    _require_exact_type(
        cfg,
        ResearchTeamSpecialistCalibrationMemoryFloorConfig,
        "validation_config",
    )
    cfg.__post_init__()
    expected_recency = _memory_recency_score(row.memory_age_seconds, cfg)
    if row.memory_recency_score != expected_recency:
        raise ValueError("memory_recency_score must match row inputs")
    expected_floor = _calibration_memory_floor_score(
        calibration_score=row.calibration_score,
        memory_recall_score=row.memory_recall_score,
        memory_recency_score=row.memory_recency_score,
        config=cfg,
    )
    if row.calibration_memory_floor_score != expected_floor:
        raise ValueError("calibration_memory_floor_score must match row inputs")
    expected_reason_codes = _row_reason_codes(
        calibration_score=row.calibration_score,
        memory_recall_score=row.memory_recall_score,
        memory_age_seconds=row.memory_age_seconds,
        uncalibrated_specialist_ratio=row.uncalibrated_specialist_ratio,
        calibration_memory_floor_score=row.calibration_memory_floor_score,
        config=cfg,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(expected_reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchTeamSpecialistCalibrationMemoryFloorReport,
) -> None:
    rows = report.rows
    identities = tuple((row.team_label, row.specialist_label) for row in rows)
    if len(set(identities)) != len(identities):
        raise ValueError("team and specialist labels must be unique")
    if any(row.observed_at > report.generated_at for row in rows):
        raise ValueError("observed_at must be on or before generated_at")
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be ranked deterministically")
    if report.team_specialist_count != _count(len(rows)):
        raise ValueError("team_specialist_count must match rows")
    if report.pass_count != _count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    breach_count = _count(
        sum(1 for row in rows if row.status in (STATUS_WATCH, STATUS_BLOCK)),
    )
    if report.floor_breach_count != breach_count:
        raise ValueError("floor_breach_count must match rows")
    if report.floor_breach_ratio != _ratio(breach_count, _count(len(rows))):
        raise ValueError("floor_breach_ratio must match rows")
    if report.average_calibration_memory_floor_score != _average_or_none(
        row.calibration_memory_floor_score for row in rows
    ):
        raise ValueError("average_calibration_memory_floor_score must match rows")
    if report.lowest_calibration_memory_floor_score != min(
        (row.calibration_memory_floor_score for row in rows),
        default=None,
    ):
        raise ValueError("lowest_calibration_memory_floor_score must match rows")
    if report.max_memory_age_seconds != max(
        (row.memory_age_seconds for row in rows),
        default=None,
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_uncalibrated_specialist_ratio != max(
        (row.uncalibrated_specialist_ratio for row in rows),
        default=None,
    ):
        raise ValueError("max_uncalibrated_specialist_ratio must match rows")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reasons = tuple(item.reason_code for item in expected_counts)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match reason_code_counts")


def _require_rows(
    rows: tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecialistCalibrationMemoryFloorRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistCalibrationMemoryFloorRow",
            )
        row.__post_init__(getattr(row, "_validation_config", None))
    return rows


def _require_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistCalibrationMemoryFloorReasonCodeCount",
            )
        item.__post_init__()
    return counts


def _require_reason_codes(
    values: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not values:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_public_string("reason_code", value)
        if value not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code is not supported")
        if value not in normalized:
            normalized.append(value)
    ordered = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if ordered != values:
        raise ValueError("reason_codes must be deterministically ordered")
    return ordered


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in CALIBRATION_MEMORY_FLOOR_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if _contains_unsafe_public_label(value):
        raise ValueError(f"{field_name} must be a public aggregate label")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a nonblank trimmed public string")


def _contains_unsafe_public_label(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be a {expected_type.__name__}")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_pass_at_least_watch(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be at least {watch_name}")


def _require_watch_at_least_pass(
    watch_name: str,
    watch_value: Decimal,
    pass_name: str,
    pass_value: Decimal,
) -> None:
    if watch_value < pass_value:
        raise ValueError(f"{watch_name} must be at least {pass_name}")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = _quantize_decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be within supported Decimal bounds") from exc
    if value != normalized:
        raise ValueError(f"{field_name} precision is too granular")
    return ZERO if normalized.is_zero() else normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is Decimal and value.is_finite() and value < Decimal(0):
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _require_decimal(field_name, value)
    return normalized


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is Decimal and value.is_finite() and not (Decimal(0) <= value <= Decimal(1)):
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    normalized = _require_decimal(field_name, value)
    return normalized


def _require_optional_ratio_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _as_utc_exact(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _status_count(
    rows: tuple[ResearchTeamSpecialistCalibrationMemoryFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = _quantize_decimal(numerator / denominator)
    return _require_ratio_decimal("ratio", value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _average_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for item in items:
            total += item
    return _ratio(total, _count(len(items)))


def _report_values_without_digest(
    report: ResearchTeamSpecialistCalibrationMemoryFloorReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_values(unsigned)


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported JSON payload value {type(value).__name__}")


def _reject_unsafe_public_payload(
    context: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            context,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str or _contains_unsafe_public_label(key):
                raise ValueError(f"{context} must use public aggregate labels")
            _reject_unsafe_public_payload(
                context,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{context} must be a public aggregate payload")
        for item in value:
            _reject_unsafe_public_payload(
                context,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if _contains_unsafe_public_label(value):
            raise ValueError(f"{context} must use public aggregate labels")
        return
    if type(value) in (bool, Decimal) or value is None or type(value) is datetime:
        return
    raise ValueError(f"{context} contains unsupported public payload value")
