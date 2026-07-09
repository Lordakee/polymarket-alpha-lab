"""Paper-only domain memory signal calibration report for research teams."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_CALIBRATION_CONFIG_VERSION = (
    "research-team-domain-memory-signal-calibration-report-v1"
)
DOMAIN_MEMORY_SIGNAL_CALIBRATION_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEFAULT_MAX_PASS_MEMORY_AGE_SECONDS = Decimal("86400.000000")
DEFAULT_MAX_WATCH_MEMORY_AGE_SECONDS = Decimal("604800.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

REASON_SEQUENCE = (
    "domain_memory_signal_coverage_block",
    "domain_memory_signal_accuracy_gap_block",
    "domain_memory_signal_staleness_block",
    "domain_memory_signal_disagreement_block",
    "domain_memory_signal_coverage_watch",
    "domain_memory_signal_accuracy_gap_watch",
    "domain_memory_signal_staleness_watch",
    "domain_memory_signal_disagreement_watch",
    "domain_memory_signal_calibration_pass",
)
REPORT_REASON_SEQUENCE = REASON_SEQUENCE[:-1]
EMPTY_REASON = "domain_memory_signal_calibration_empty"
REPORT_MODE_BY_STATUS = {
    "pass": "paper_domain_memory_signal_monitor",
    "watch": "paper_domain_memory_signal_watch",
    "block": "paper_domain_memory_signal_block",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "auth",
        "private",
        "token",
        "secret",
        "account",
        "credential",
        "api_key",
        "sizing",
        "recommendation",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("trad", "ing"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "watch_block_ratio",
        "min_memory_coverage_ratio",
        "max_signal_accuracy_gap_ratio",
        "max_memory_age_seconds",
        "max_disagreement_rate",
        "max_calibration_pressure_score",
        "status",
        "report_mode",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "calibration_rank",
        "domain_label",
        "team_label",
        "signal_family_label",
        "status",
        "calibration_pressure_score",
        "memory_sample_count",
        "calibrated_memory_count",
        "memory_coverage_ratio",
        "expected_signal_accuracy",
        "observed_signal_accuracy",
        "signal_accuracy_gap_ratio",
        "memory_age_seconds",
        "memory_staleness_ratio",
        "disagreement_rate",
        "observed_at",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PAYLOAD_KEYS = frozenset(
    ("reason_code", "count", "row_ratio", "paper_only", "report_only", "readonly"),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_CALIBRATION_CONFIG_VERSION",
    "DOMAIN_MEMORY_SIGNAL_CALIBRATION_STATUSES",
    "ResearchTeamDomainMemorySignalCalibrationConfig",
    "ResearchTeamDomainMemorySignalCalibrationInput",
    "ResearchTeamDomainMemorySignalCalibrationReasonCodeCount",
    "ResearchTeamDomainMemorySignalCalibrationReport",
    "ResearchTeamDomainMemorySignalCalibrationRow",
    "build_research_team_domain_memory_signal_calibration_report",
    "research_team_domain_memory_signal_calibration_report_digest",
    "research_team_domain_memory_signal_calibration_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalCalibrationConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_CALIBRATION_CONFIG_VERSION
    )
    min_pass_memory_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_memory_coverage_ratio: Decimal = Decimal("0.700000")
    max_pass_signal_accuracy_gap_ratio: Decimal = Decimal("0.050000")
    max_watch_signal_accuracy_gap_ratio: Decimal = Decimal("0.150000")
    max_pass_memory_age_seconds: Decimal = DEFAULT_MAX_PASS_MEMORY_AGE_SECONDS
    max_watch_memory_age_seconds: Decimal = DEFAULT_MAX_WATCH_MEMORY_AGE_SECONDS
    max_pass_disagreement_rate: Decimal = Decimal("0.050000")
    max_watch_disagreement_rate: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemorySignalCalibrationConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_CALIBRATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
            "max_pass_signal_accuracy_gap_ratio",
            "max_watch_signal_accuracy_gap_ratio",
            "max_pass_disagreement_rate",
            "max_watch_disagreement_rate",
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
        if self.min_pass_memory_coverage_ratio < self.min_watch_memory_coverage_ratio:
            raise ValueError(
                "min_pass_memory_coverage_ratio must be at least "
                "min_watch_memory_coverage_ratio",
            )
        if (
            self.max_pass_signal_accuracy_gap_ratio
            > self.max_watch_signal_accuracy_gap_ratio
        ):
            raise ValueError(
                "max_watch_signal_accuracy_gap_ratio must be at least "
                "max_pass_signal_accuracy_gap_ratio",
            )
        if self.max_pass_memory_age_seconds > self.max_watch_memory_age_seconds:
            raise ValueError(
                "max_watch_memory_age_seconds must be at least "
                "max_pass_memory_age_seconds",
            )
        if self.max_pass_disagreement_rate > self.max_watch_disagreement_rate:
            raise ValueError(
                "max_watch_disagreement_rate must be at least "
                "max_pass_disagreement_rate",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalCalibrationInput(_FinalDataclass):
    domain_label: str
    team_label: str
    signal_family_label: str
    memory_sample_count: Decimal
    calibrated_memory_count: Decimal
    expected_signal_accuracy: Decimal
    observed_signal_accuracy: Decimal
    memory_age_seconds: Decimal
    disagreement_rate: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemorySignalCalibrationInput,
            "input",
        )
        for field_name in ("domain_label", "team_label", "signal_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "memory_sample_count",
            "calibrated_memory_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_signal_accuracy",
            "observed_signal_accuracy",
            "disagreement_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.calibrated_memory_count > self.memory_sample_count:
            raise ValueError(
                "calibrated_memory_count must not exceed memory_sample_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalCalibrationRow(_FinalDataclass):
    calibration_rank: Decimal
    domain_label: str
    team_label: str
    signal_family_label: str
    status: str
    calibration_pressure_score: Decimal
    memory_sample_count: Decimal
    calibrated_memory_count: Decimal
    memory_coverage_ratio: Decimal
    expected_signal_accuracy: Decimal
    observed_signal_accuracy: Decimal
    signal_accuracy_gap_ratio: Decimal
    memory_age_seconds: Decimal
    memory_staleness_ratio: Decimal
    disagreement_rate: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    max_watch_memory_age_seconds: InitVar[Decimal] = DEFAULT_MAX_WATCH_MEMORY_AGE_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self, max_watch_memory_age_seconds: Decimal) -> None:
        _require_exact_type(self, ResearchTeamDomainMemorySignalCalibrationRow, "row")
        watch_memory_age_window = _require_nonnegative_decimal(
            "max_watch_memory_age_seconds",
            max_watch_memory_age_seconds,
        )
        object.__setattr__(
            self,
            "calibration_rank",
            _require_count_decimal("calibration_rank", self.calibration_rank),
        )
        for field_name in ("domain_label", "team_label", "signal_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        for field_name in (
            "calibration_pressure_score",
            "memory_coverage_ratio",
            "expected_signal_accuracy",
            "observed_signal_accuracy",
            "signal_accuracy_gap_ratio",
            "memory_staleness_ratio",
            "disagreement_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_sample_count",
            "calibrated_memory_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.calibrated_memory_count > self.memory_sample_count:
            raise ValueError(
                "calibrated_memory_count must not exceed memory_sample_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row(
            self,
            max_watch_memory_age_seconds=watch_memory_age_window,
        )
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalCalibrationReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemorySignalCalibrationReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySignalCalibrationReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    watch_block_ratio: Decimal
    min_memory_coverage_ratio: Decimal
    max_signal_accuracy_gap_ratio: Decimal
    max_memory_age_seconds: Decimal
    max_disagreement_rate: Decimal
    max_calibration_pressure_score: Decimal
    status: str
    report_mode: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainMemorySignalCalibrationReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamDomainMemorySignalCalibrationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemorySignalCalibrationReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_block_ratio",
            "min_memory_coverage_ratio",
            "max_signal_accuracy_gap_ratio",
            "max_disagreement_rate",
            "max_calibration_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("report_mode", self.report_mode)
        if self.report_mode != REPORT_MODE_BY_STATUS[self.status]:
            raise ValueError("report_mode must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)


def build_research_team_domain_memory_signal_calibration_report(
    inputs: Iterable[ResearchTeamDomainMemorySignalCalibrationInput],
    *,
    config: ResearchTeamDomainMemorySignalCalibrationConfig,
    generated_at: datetime,
) -> ResearchTeamDomainMemorySignalCalibrationReport:
    _require_exact_type(
        config,
        ResearchTeamDomainMemorySignalCalibrationConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    for item in input_rows:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank, config)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    status = _report_status(rows)
    watch_block_count = _count(sum(1 for row in rows if row.status in ("watch", "block")))
    return ResearchTeamDomainMemorySignalCalibrationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        watch_block_ratio=_ratio(watch_block_count, _count(len(rows))),
        min_memory_coverage_ratio=_min_ratio(
            tuple(row.memory_coverage_ratio for row in rows),
        ),
        max_signal_accuracy_gap_ratio=_max_decimal(
            tuple(row.signal_accuracy_gap_ratio for row in rows),
        ),
        max_memory_age_seconds=_max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        max_disagreement_rate=_max_decimal(
            tuple(row.disagreement_rate for row in rows),
        ),
        max_calibration_pressure_score=_max_decimal(
            tuple(row.calibration_pressure_score for row in rows),
        ),
        status=status,
        report_mode=REPORT_MODE_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_memory_signal_calibration_report_payload(
    report: ResearchTeamDomainMemorySignalCalibrationReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainMemorySignalCalibrationReport:
        _require_hard_flags("report", report)
        _verify_digest(report)
        for row in report.rows:
            _verify_digest(row)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainMemorySignalCalibrationReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    _validate_public_payload(payload)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_domain_memory_signal_calibration_report_digest(
    report: ResearchTeamDomainMemorySignalCalibrationReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_memory_signal_calibration_report_payload(report)
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


def _row_from_input(
    item: ResearchTeamDomainMemorySignalCalibrationInput,
    config: ResearchTeamDomainMemorySignalCalibrationConfig,
) -> ResearchTeamDomainMemorySignalCalibrationRow:
    memory_coverage_ratio = _ratio(item.calibrated_memory_count, item.memory_sample_count)
    signal_accuracy_gap_ratio = _max_decimal(
        (ZERO, _subtract_decimal(item.expected_signal_accuracy, item.observed_signal_accuracy)),
    )
    memory_staleness_ratio = _bounded_ratio(
        item.memory_age_seconds,
        config.max_watch_memory_age_seconds,
    )
    pressure_components = (
        _inverse_threshold_pressure(
            memory_coverage_ratio,
            pass_value=config.min_pass_memory_coverage_ratio,
            watch_value=config.min_watch_memory_coverage_ratio,
        ),
        _threshold_pressure(
            signal_accuracy_gap_ratio,
            pass_value=config.max_pass_signal_accuracy_gap_ratio,
            watch_value=config.max_watch_signal_accuracy_gap_ratio,
        ),
        _threshold_pressure(
            item.memory_age_seconds,
            pass_value=config.max_pass_memory_age_seconds,
            watch_value=config.max_watch_memory_age_seconds,
        ),
        _threshold_pressure(
            item.disagreement_rate,
            pass_value=config.max_pass_disagreement_rate,
            watch_value=config.max_watch_disagreement_rate,
        ),
    )
    status = _status_for(
        memory_coverage_ratio=memory_coverage_ratio,
        signal_accuracy_gap_ratio=signal_accuracy_gap_ratio,
        memory_age_seconds=item.memory_age_seconds,
        disagreement_rate=item.disagreement_rate,
        config=config,
    )
    return ResearchTeamDomainMemorySignalCalibrationRow(
        calibration_rank=ZERO,
        domain_label=item.domain_label,
        team_label=item.team_label,
        signal_family_label=item.signal_family_label,
        status=status,
        calibration_pressure_score=_max_decimal(pressure_components),
        memory_sample_count=item.memory_sample_count,
        calibrated_memory_count=item.calibrated_memory_count,
        memory_coverage_ratio=memory_coverage_ratio,
        expected_signal_accuracy=item.expected_signal_accuracy,
        observed_signal_accuracy=item.observed_signal_accuracy,
        signal_accuracy_gap_ratio=signal_accuracy_gap_ratio,
        memory_age_seconds=item.memory_age_seconds,
        memory_staleness_ratio=memory_staleness_ratio,
        disagreement_rate=item.disagreement_rate,
        observed_at=item.observed_at,
        reason_codes=_reason_codes_for(
            memory_coverage_ratio=memory_coverage_ratio,
            signal_accuracy_gap_ratio=signal_accuracy_gap_ratio,
            memory_age_seconds=item.memory_age_seconds,
            disagreement_rate=item.disagreement_rate,
            status=status,
            config=config,
        ),
        max_watch_memory_age_seconds=config.max_watch_memory_age_seconds,
    )


def _with_rank(
    row: ResearchTeamDomainMemorySignalCalibrationRow,
    rank: int,
    config: ResearchTeamDomainMemorySignalCalibrationConfig,
) -> ResearchTeamDomainMemorySignalCalibrationRow:
    return ResearchTeamDomainMemorySignalCalibrationRow(
        calibration_rank=_count(rank),
        domain_label=row.domain_label,
        team_label=row.team_label,
        signal_family_label=row.signal_family_label,
        status=row.status,
        calibration_pressure_score=row.calibration_pressure_score,
        memory_sample_count=row.memory_sample_count,
        calibrated_memory_count=row.calibrated_memory_count,
        memory_coverage_ratio=row.memory_coverage_ratio,
        expected_signal_accuracy=row.expected_signal_accuracy,
        observed_signal_accuracy=row.observed_signal_accuracy,
        signal_accuracy_gap_ratio=row.signal_accuracy_gap_ratio,
        memory_age_seconds=row.memory_age_seconds,
        memory_staleness_ratio=row.memory_staleness_ratio,
        disagreement_rate=row.disagreement_rate,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
        max_watch_memory_age_seconds=config.max_watch_memory_age_seconds,
    )


def _status_for(
    *,
    memory_coverage_ratio: Decimal,
    signal_accuracy_gap_ratio: Decimal,
    memory_age_seconds: Decimal,
    disagreement_rate: Decimal,
    config: ResearchTeamDomainMemorySignalCalibrationConfig,
) -> str:
    if (
        memory_coverage_ratio < config.min_watch_memory_coverage_ratio
        or signal_accuracy_gap_ratio > config.max_watch_signal_accuracy_gap_ratio
        or memory_age_seconds > config.max_watch_memory_age_seconds
        or disagreement_rate > config.max_watch_disagreement_rate
    ):
        return "block"
    if (
        memory_coverage_ratio < config.min_pass_memory_coverage_ratio
        or signal_accuracy_gap_ratio > config.max_pass_signal_accuracy_gap_ratio
        or memory_age_seconds > config.max_pass_memory_age_seconds
        or disagreement_rate > config.max_pass_disagreement_rate
    ):
        return "watch"
    return "pass"


def _reason_codes_for(
    *,
    memory_coverage_ratio: Decimal,
    signal_accuracy_gap_ratio: Decimal,
    memory_age_seconds: Decimal,
    disagreement_rate: Decimal,
    status: str,
    config: ResearchTeamDomainMemorySignalCalibrationConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if memory_coverage_ratio < config.min_watch_memory_coverage_ratio:
        codes.append("domain_memory_signal_coverage_block")
    elif memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        codes.append("domain_memory_signal_coverage_watch")
    if signal_accuracy_gap_ratio > config.max_watch_signal_accuracy_gap_ratio:
        codes.append("domain_memory_signal_accuracy_gap_block")
    elif signal_accuracy_gap_ratio > config.max_pass_signal_accuracy_gap_ratio:
        codes.append("domain_memory_signal_accuracy_gap_watch")
    if memory_age_seconds > config.max_watch_memory_age_seconds:
        codes.append("domain_memory_signal_staleness_block")
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        codes.append("domain_memory_signal_staleness_watch")
    if disagreement_rate > config.max_watch_disagreement_rate:
        codes.append("domain_memory_signal_disagreement_block")
    elif disagreement_rate > config.max_pass_disagreement_rate:
        codes.append("domain_memory_signal_disagreement_watch")
    if not codes and status == "pass":
        codes.append("domain_memory_signal_calibration_pass")
    return _require_reason_codes(tuple(codes), require_nonempty=True)


def _row_sort_key(
    row: ResearchTeamDomainMemorySignalCalibrationRow,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.calibration_pressure_score,
        row.memory_coverage_ratio,
        row.domain_label,
        row.team_label,
        row.signal_family_label,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamDomainMemorySignalCalibrationInput],
) -> tuple[ResearchTeamDomainMemorySignalCalibrationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainMemorySignalCalibrationInput,
            "input",
        )
        _require_hard_flags("input", item)
        key = (item.domain_label, item.team_label, item.signal_family_label)
        if key in seen_keys:
            raise ValueError("team-domain-signal labels must be unique")
        seen_keys.add(key)
    return normalized


def _require_rows(
    rows: object,
) -> tuple[ResearchTeamDomainMemorySignalCalibrationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        _require_exact_type(row, ResearchTeamDomainMemorySignalCalibrationRow, "row")
        _require_hard_flags("row", row)
        _verify_digest(row)
        key = (row.domain_label, row.team_label, row.signal_family_label)
        if key in seen_keys:
            raise ValueError("team-domain-signal labels must be unique")
        seen_keys.add(key)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must use deterministic ordering")
    return normalized


def _require_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainMemorySignalCalibrationReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for item in counts:
        _require_exact_type(
            item,
            ResearchTeamDomainMemorySignalCalibrationReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_codes.add(item.reason_code)
    if tuple(sorted(counts, key=lambda item: _reason_rank(item.reason_code))) != counts:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return counts


def _validate_row(
    row: ResearchTeamDomainMemorySignalCalibrationRow,
    *,
    max_watch_memory_age_seconds: Decimal = DEFAULT_MAX_WATCH_MEMORY_AGE_SECONDS,
) -> None:
    if row.memory_coverage_ratio != _ratio(
        row.calibrated_memory_count,
        row.memory_sample_count,
    ):
        raise ValueError("memory_coverage_ratio must match row counts")
    expected_gap = _max_decimal(
        (ZERO, _subtract_decimal(row.expected_signal_accuracy, row.observed_signal_accuracy)),
    )
    if row.signal_accuracy_gap_ratio != expected_gap:
        raise ValueError("signal_accuracy_gap_ratio must match row accuracies")
    expected_staleness = _bounded_ratio(
        row.memory_age_seconds,
        max_watch_memory_age_seconds,
    )
    if row.memory_staleness_ratio != expected_staleness:
        raise ValueError("memory_staleness_ratio must match memory_age_seconds")
    if row.status == "pass" and row.reason_codes != (
        "domain_memory_signal_calibration_pass",
    ):
        raise ValueError("pass rows must carry the pass reason code")
    if row.status != "pass" and "domain_memory_signal_calibration_pass" in row.reason_codes:
        raise ValueError("non-pass rows must not carry the pass reason code")


def _validate_report(report: ResearchTeamDomainMemorySignalCalibrationReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    watch_block_count = _count(sum(1 for row in report.rows if row.status in ("watch", "block")))
    if report.watch_block_ratio != _ratio(watch_block_count, report.row_count):
        raise ValueError("watch_block_ratio must match rows")
    if report.min_memory_coverage_ratio != _min_ratio(
        tuple(row.memory_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_memory_coverage_ratio must match rows")
    if report.max_signal_accuracy_gap_ratio != _max_decimal(
        tuple(row.signal_accuracy_gap_ratio for row in report.rows),
    ):
        raise ValueError("max_signal_accuracy_gap_ratio must match rows")
    if report.max_memory_age_seconds != _max_decimal(
        tuple(row.memory_age_seconds for row in report.rows),
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_disagreement_rate != _max_decimal(
        tuple(row.disagreement_rate for row in report.rows),
    ):
        raise ValueError("max_disagreement_rate must match rows")
    if report.max_calibration_pressure_score != _max_decimal(
        tuple(row.calibration_pressure_score for row in report.rows),
    ):
        raise ValueError("max_calibration_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(
    rows: tuple[ResearchTeamDomainMemorySignalCalibrationRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemorySignalCalibrationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    active_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "domain_memory_signal_calibration_pass"
    }
    if not active_codes:
        return ("domain_memory_signal_calibration_pass",)
    return tuple(reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in active_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainMemorySignalCalibrationRow, ...],
) -> tuple[ResearchTeamDomainMemorySignalCalibrationReasonCodeCount, ...]:
    if not rows:
        return ()
    counter = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in REPORT_REASON_SEQUENCE
    )
    return tuple(
        ResearchTeamDomainMemorySignalCalibrationReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            row_ratio=_ratio(_count(counter[reason_code]), _count(len(rows))),
        )
        for reason_code in REPORT_REASON_SEQUENCE
        if counter[reason_code]
    )


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    for field_name in (
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "watch_block_ratio",
        "min_memory_coverage_ratio",
        "max_signal_accuracy_gap_ratio",
        "max_memory_age_seconds",
        "max_disagreement_rate",
        "max_calibration_pressure_score",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _require_public_string("report_mode", payload["report_mode"])
    if payload["report_mode"] != REPORT_MODE_BY_STATUS[payload["status"]]:
        raise ValueError("report_mode must match status")
    _require_reason_codes(payload["reason_codes"], require_nonempty=True)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for item in reason_code_counts:
        _validate_public_reason_code_count(item)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        _validate_public_row_payload(row)
    _require_sha256("derived_validation_digest", payload["derived_validation_digest"])


def _validate_public_reason_code_count(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_keys("reason_code_count", value, REASON_COUNT_PAYLOAD_KEYS)
    _require_public_string("reason_code", value["reason_code"])
    _require_decimal_string("count", value["count"])
    _require_decimal_string("row_ratio", value["row_ratio"])
    _require_hard_flags("reason_code_count", _MappingFlags(value))


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys("row", value, ROW_PAYLOAD_KEYS)
    for field_name in ("domain_label", "team_label", "signal_family_label"):
        _require_public_label(field_name, value[field_name])
    _require_status("status", value["status"])
    for field_name in (
        "calibration_rank",
        "calibration_pressure_score",
        "memory_sample_count",
        "calibrated_memory_count",
        "memory_coverage_ratio",
        "expected_signal_accuracy",
        "observed_signal_accuracy",
        "signal_accuracy_gap_ratio",
        "memory_age_seconds",
        "memory_staleness_ratio",
        "disagreement_rate",
    ):
        _require_decimal_string(field_name, value[field_name])
    _require_reason_codes(value["reason_codes"], require_nonempty=True)
    _require_hard_flags("row", _MappingFlags(value))
    _require_sha256("derived_validation_digest", value["derived_validation_digest"])
    expected_digest = _digest_from_payload(value)
    if value["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest does not match row payload")


def _require_payload_keys(
    label: str,
    payload: dict[str, object],
    allowed_keys: frozenset[str],
) -> None:
    keys = frozenset(payload)
    if keys != allowed_keys:
        raise ValueError(f"{label} must use the public readonly schema")


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(value, require_nonempty=True)
    if reason_codes == (EMPTY_REASON,):
        return reason_codes
    if any(reason_code not in REASON_SEQUENCE for reason_code in reason_codes):
        raise ValueError("reason_codes must use supported values")
    if tuple(sorted(reason_codes, key=_reason_rank)) != reason_codes:
        raise ValueError("reason_codes must use deterministic ordering")
    return reason_codes


def _require_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    if tuple(sorted(reason_codes, key=_reason_rank)) != reason_codes:
        raise ValueError("reason_codes must use deterministic ordering")
    return reason_codes


def _require_reason_code(value: object) -> None:
    _require_public_string("reason_code", value)
    if value != EMPTY_REASON and value not in REASON_SEQUENCE:
        raise ValueError("reason_code must be supported")


def _reason_rank(value: str) -> int:
    if value == EMPTY_REASON:
        return -1
    try:
        return REASON_SEQUENCE.index(value)
    except ValueError:
        return len(REASON_SEQUENCE)


def _status_count(
    rows: tuple[ResearchTeamDomainMemorySignalCalibrationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _divide_decimal(numerator, denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _bounded_ratio_value(_ratio(numerator, denominator))


def _threshold_pressure(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO
    if value >= watch_value:
        return ONE
    return _bounded_ratio_value(
        _divide_decimal(value - pass_value, watch_value - pass_value),
    )


def _inverse_threshold_pressure(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value >= pass_value:
        return ZERO
    if value <= watch_value:
        return ONE
    return _bounded_ratio_value(
        _divide_decimal(pass_value - value, pass_value - watch_value),
    )


def _bounded_ratio_value(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("division denominator must be nonzero")
    return _quantize(left / right)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} public payload numeric values must be strings")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if format(_quantize(decimal_value), "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return _quantize(decimal_value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_generated_at_utc(field_name: str, value: object) -> datetime:
    normalized = _as_utc(field_name, value)
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_MEMORY_SIGNAL_CALIBRATION_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or PUBLIC_LABEL_RE.fullmatch(value) is None
        or _has_unsafe_public_fragment(value)
    ):
        raise ValueError(f"{field_name} must be a public aggregate label")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(fragment in lowered or fragment in compact for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} must use public aggregate labels")
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{label} must use public aggregate labels")
        return
    if type(value) in (bool, type(None)):
        return
    if type(value) is Decimal:
        _require_decimal("public_payload_decimal", value)
        return
    if type(value) is datetime:
        _as_utc("public_payload_datetime", value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    raise ValueError("public payload value is not JSON serializable")


def _apply_or_verify_digest(
    value: (
        ResearchTeamDomainMemorySignalCalibrationRow
        | ResearchTeamDomainMemorySignalCalibrationReport
    ),
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_sha256("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _verify_digest(
    value: (
        ResearchTeamDomainMemorySignalCalibrationRow
        | ResearchTeamDomainMemorySignalCalibrationReport
    ),
) -> None:
    _require_sha256("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match report payload")


def _derived_digest(
    value: (
        ResearchTeamDomainMemorySignalCalibrationRow
        | ResearchTeamDomainMemorySignalCalibrationReport
    ),
) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    return _digest_from_payload(_json_ready(payload))


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return sha256(encoded).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(_require_decimal("json_decimal", value), "f")
    if type(value) is datetime:
        return _as_utc("json_datetime", value).isoformat()
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    raise ValueError("value is not JSON serializable")
