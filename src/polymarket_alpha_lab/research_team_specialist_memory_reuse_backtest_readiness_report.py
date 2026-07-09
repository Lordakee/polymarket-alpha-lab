"""Report-only specialist memory reuse backtest readiness reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_STATUSES",
    "ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig",
    "ResearchTeamSpecialistMemoryReuseBacktestReadinessInput",
    "ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount",
    "ResearchTeamSpecialistMemoryReuseBacktestReadinessReport",
    "ResearchTeamSpecialistMemoryReuseBacktestReadinessRow",
    "build_research_team_specialist_memory_reuse_backtest_readiness_report",
    "research_team_specialist_memory_reuse_backtest_readiness_report_payload",
)


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-reuse-backtest-readiness-report-v0"
)
RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_STATUSES = (
    "pass",
    "watch",
    "block",
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

EMPTY_REPORT_REASON_CODE = "empty_specialist_memory_reuse_backtest_readiness_inputs"
REPORT_PASS_REASON_CODE = "specialist_memory_reuse_backtest_readiness_report_pass"
REPORT_WATCH_REASON_CODE = "specialist_memory_reuse_backtest_readiness_report_watch"
REPORT_BLOCK_REASON_CODE = "specialist_memory_reuse_backtest_readiness_report_block"
ROW_PASS_REASON_CODE = "specialist_memory_reuse_backtest_ready"
ROW_REASON_CODES = (
    "readiness_score_block",
    "readiness_score_watch",
    ROW_PASS_REASON_CODE,
    "prior_reuse_hit_rate_block",
    "prior_reuse_hit_rate_watch",
    "signal_similarity_score_block",
    "signal_similarity_score_watch",
    "backtest_sample_depth_block",
    "backtest_sample_depth_watch",
    "backtest_success_rate_block",
    "backtest_success_rate_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "calibration_drift_pressure_block",
    "calibration_drift_pressure_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REPORT_REASON_CODE,
)
ROW_REASON_SEQUENCE = (
    ("readiness_score_block", "readiness_score_watch", ROW_PASS_REASON_CODE),
    ("prior_reuse_hit_rate_block", "prior_reuse_hit_rate_watch"),
    ("signal_similarity_score_block", "signal_similarity_score_watch"),
    ("backtest_sample_depth_block", "backtest_sample_depth_watch"),
    ("backtest_success_rate_block", "backtest_success_rate_watch"),
    ("contradiction_pressure_block", "contradiction_pressure_watch"),
    ("calibration_drift_pressure_block", "calibration_drift_pressure_watch"),
)
UNSAFE_VALUE_FRAGMENTS = (
    "cand" + "idate_id",
    "raw_" + "cand" + "idate",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "u" + "rl",
    "://",
    "d" + "sn",
    "tab" + "le_name",
    "tok" + "en",
    "wa" + "llet",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "rec" + "ommendation",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_REPORT_CONFIG_VERSION
    )
    prior_reuse_hit_rate_weight: Decimal = Decimal("0.152679")
    signal_similarity_score_weight: Decimal = Decimal("0.076786")
    backtest_sample_depth_weight: Decimal = Decimal("0.150000")
    backtest_success_rate_weight: Decimal = Decimal("0.409821")
    contradiction_reserve_weight: Decimal = Decimal("0.110714")
    calibration_stability_weight: Decimal = Decimal("0.100000")
    pass_threshold: Decimal = Decimal("0.750000")
    watch_threshold: Decimal = Decimal("0.550000")
    backtest_sample_target_count: Decimal = Decimal("20")
    min_pass_prior_reuse_hit_rate: Decimal = Decimal("0.750000")
    min_watch_prior_reuse_hit_rate: Decimal = Decimal("0.500000")
    min_pass_signal_similarity_score: Decimal = Decimal("0.750000")
    min_watch_signal_similarity_score: Decimal = Decimal("0.500000")
    min_pass_backtest_sample_depth_score: Decimal = Decimal("0.750000")
    min_watch_backtest_sample_depth_score: Decimal = Decimal("0.250000")
    min_pass_backtest_success_rate: Decimal = Decimal("0.750000")
    min_watch_backtest_success_rate: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.250000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.700000")
    max_pass_calibration_drift_pressure: Decimal = Decimal("0.250000")
    max_watch_calibration_drift_pressure: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "prior_reuse_hit_rate_weight",
            "signal_similarity_score_weight",
            "backtest_sample_depth_weight",
            "backtest_success_rate_weight",
            "contradiction_reserve_weight",
            "calibration_stability_weight",
            "pass_threshold",
            "watch_threshold",
            "min_pass_prior_reuse_hit_rate",
            "min_watch_prior_reuse_hit_rate",
            "min_pass_signal_similarity_score",
            "min_watch_signal_similarity_score",
            "min_pass_backtest_sample_depth_score",
            "min_watch_backtest_sample_depth_score",
            "min_pass_backtest_success_rate",
            "min_watch_backtest_success_rate",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "max_pass_calibration_drift_pressure",
            "max_watch_calibration_drift_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "backtest_sample_target_count",
            _normalize_positive_count(
                "backtest_sample_target_count",
                self.backtest_sample_target_count,
            ),
        )
        _require_descending_threshold(
            "threshold",
            self.pass_threshold,
            self.watch_threshold,
        )
        _require_descending_threshold(
            "prior_reuse_hit_rate",
            self.min_pass_prior_reuse_hit_rate,
            self.min_watch_prior_reuse_hit_rate,
        )
        _require_descending_threshold(
            "signal_similarity_score",
            self.min_pass_signal_similarity_score,
            self.min_watch_signal_similarity_score,
        )
        _require_descending_threshold(
            "backtest_sample_depth_score",
            self.min_pass_backtest_sample_depth_score,
            self.min_watch_backtest_sample_depth_score,
        )
        _require_descending_threshold(
            "backtest_success_rate",
            self.min_pass_backtest_success_rate,
            self.min_watch_backtest_success_rate,
        )
        _require_ascending_threshold(
            "contradiction_pressure",
            self.max_pass_contradiction_pressure,
            self.max_watch_contradiction_pressure,
        )
        _require_ascending_threshold(
            "calibration_drift_pressure",
            self.max_pass_calibration_drift_pressure,
            self.max_watch_calibration_drift_pressure,
        )
        _require_weight_total(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryReuseBacktestReadinessInput:
    specialist_key: str
    memory_reference: str
    observed_at: datetime
    prior_reuse_hit_rate: Decimal
    signal_similarity_score: Decimal
    backtest_sample_count: Decimal
    backtest_success_rate: Decimal
    contradiction_pressure: Decimal
    calibration_drift_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryReuseBacktestReadinessInput,
        )
        object.__setattr__(
            self,
            "specialist_key",
            _require_safe_label("specialist_key", self.specialist_key),
        )
        object.__setattr__(
            self,
            "memory_reference",
            _require_memory_reference("memory_reference", self.memory_reference),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_reuse_hit_rate",
            "signal_similarity_score",
            "backtest_success_rate",
            "contradiction_pressure",
            "calibration_drift_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "backtest_sample_count",
            _normalize_nonnegative_count(
                "backtest_sample_count",
                self.backtest_sample_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryReuseBacktestReadinessRow:
    rank: Decimal
    specialist_key: str
    memory_digest: str
    status: str
    observed_at: datetime
    memory_age_seconds: Decimal
    prior_reuse_hit_rate: Decimal
    signal_similarity_score: Decimal
    backtest_sample_count: Decimal
    backtest_sample_depth_score: Decimal
    backtest_success_rate: Decimal
    contradiction_pressure: Decimal
    calibration_drift_pressure: Decimal
    memory_reuse_backtest_readiness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryReuseBacktestReadinessRow,
        )
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "specialist_key",
            _require_safe_label("specialist_key", self.specialist_key),
        )
        object.__setattr__(
            self,
            "memory_digest",
            _normalize_sha256("memory_digest", self.memory_digest),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_STATUSES,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_measure(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        for field_name in (
            "prior_reuse_hit_rate",
            "signal_similarity_score",
            "backtest_sample_depth_score",
            "backtest_success_rate",
            "contradiction_pressure",
            "calibration_drift_pressure",
            "memory_reuse_backtest_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "backtest_sample_count",
            _normalize_nonnegative_count(
                "backtest_sample_count",
                self.backtest_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount,
        )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(self, "count", _normalize_nonnegative_count("count", self.count))
        if self.count <= ZERO_COUNT:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryReuseBacktestReadinessReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    lowest_backtest_sample_count: Decimal
    highest_contradiction_pressure: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount,
        ...
    ]
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...]
    public_payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryReuseBacktestReadinessReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "highest_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_backtest_sample_count",
            "oldest_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_SPECIALIST_MEMORY_REUSE_BACKTEST_READINESS_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_report_reason_code_sequence(self.reason_codes)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_sha256 = _report_public_payload_sha256(self)
        if self.public_payload_sha256:
            object.__setattr__(
                self,
                "public_payload_sha256",
                _normalize_sha256("public_payload_sha256", self.public_payload_sha256),
            )
            if self.public_payload_sha256 != expected_sha256:
                raise ValueError("public_payload_sha256 must match report fields")
        else:
            object.__setattr__(self, "public_payload_sha256", expected_sha256)


def build_research_team_specialist_memory_reuse_backtest_readiness_report(
    signals: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessInput, ...]
    | list[ResearchTeamSpecialistMemoryReuseBacktestReadinessInput],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
) -> ResearchTeamSpecialistMemoryReuseBacktestReadinessReport:
    if type(config) is not ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig:
        raise ValueError(
            "config must be a "
            "ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(signals, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(item, generated_at=generated_at_utc, config=config) for item in inputs),
    )
    return ResearchTeamSpecialistMemoryReuseBacktestReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_readiness_score=_average_field(
            rows,
            "memory_reuse_backtest_readiness_score",
        ),
        lowest_backtest_sample_count=_min_measure_field(rows, "backtest_sample_count"),
        highest_contradiction_pressure=_max_ratio_field(rows, "contradiction_pressure"),
        oldest_memory_age_seconds=_max_measure_field(rows, "memory_age_seconds"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_memory_reuse_backtest_readiness_report_payload(
    report: ResearchTeamSpecialistMemoryReuseBacktestReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSpecialistMemoryReuseBacktestReadinessReport:
        raise ValueError(
            "report must be a "
            "ResearchTeamSpecialistMemoryReuseBacktestReadinessReport",
        )
    _require_hard_flags("report", report)
    _validate_report_public_payload_sha256(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


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


def _build_row(
    item: ResearchTeamSpecialistMemoryReuseBacktestReadinessInput,
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
) -> ResearchTeamSpecialistMemoryReuseBacktestReadinessRow:
    memory_age_seconds = _age_seconds(item.observed_at, generated_at)
    backtest_sample_depth_score = _backtest_sample_depth_score(item, config=config)
    readiness_score = _memory_reuse_backtest_readiness_score(
        item,
        backtest_sample_depth_score=backtest_sample_depth_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        prior_reuse_hit_rate=item.prior_reuse_hit_rate,
        signal_similarity_score=item.signal_similarity_score,
        backtest_sample_depth_score=backtest_sample_depth_score,
        backtest_success_rate=item.backtest_success_rate,
        contradiction_pressure=item.contradiction_pressure,
        calibration_drift_pressure=item.calibration_drift_pressure,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchTeamSpecialistMemoryReuseBacktestReadinessRow(
        rank=COUNT_QUANTUM,
        specialist_key=item.specialist_key,
        memory_digest=_memory_digest(item.memory_reference),
        status=_status_from_reason_codes(reason_codes),
        observed_at=item.observed_at,
        memory_age_seconds=memory_age_seconds,
        prior_reuse_hit_rate=item.prior_reuse_hit_rate,
        signal_similarity_score=item.signal_similarity_score,
        backtest_sample_count=item.backtest_sample_count,
        backtest_sample_depth_score=backtest_sample_depth_score,
        backtest_success_rate=item.backtest_success_rate,
        contradiction_pressure=item.contradiction_pressure,
        calibration_drift_pressure=item.calibration_drift_pressure,
        memory_reuse_backtest_readiness_score=readiness_score,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...]:
    return tuple(
        ResearchTeamSpecialistMemoryReuseBacktestReadinessRow(
            rank=_count(index),
            specialist_key=row.specialist_key,
            memory_digest=row.memory_digest,
            status=row.status,
            observed_at=row.observed_at,
            memory_age_seconds=row.memory_age_seconds,
            prior_reuse_hit_rate=row.prior_reuse_hit_rate,
            signal_similarity_score=row.signal_similarity_score,
            backtest_sample_count=row.backtest_sample_count,
            backtest_sample_depth_score=row.backtest_sample_depth_score,
            backtest_success_rate=row.backtest_success_rate,
            contradiction_pressure=row.contradiction_pressure,
            calibration_drift_pressure=row.calibration_drift_pressure,
            memory_reuse_backtest_readiness_score=(
                row.memory_reuse_backtest_readiness_score
            ),
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    prior_reuse_hit_rate: Decimal,
    signal_similarity_score: Decimal,
    backtest_sample_depth_score: Decimal,
    backtest_success_rate: Decimal,
    contradiction_pressure: Decimal,
    calibration_drift_pressure: Decimal,
    readiness_score: Decimal,
    config: ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
) -> tuple[str, ...]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    if readiness_score < config.watch_threshold:
        block_codes.append("readiness_score_block")
    elif readiness_score < config.pass_threshold:
        watch_codes.append("readiness_score_watch")
    if prior_reuse_hit_rate < config.min_watch_prior_reuse_hit_rate:
        block_codes.append("prior_reuse_hit_rate_block")
    elif prior_reuse_hit_rate < config.min_pass_prior_reuse_hit_rate:
        watch_codes.append("prior_reuse_hit_rate_watch")
    if signal_similarity_score < config.min_watch_signal_similarity_score:
        block_codes.append("signal_similarity_score_block")
    elif signal_similarity_score < config.min_pass_signal_similarity_score:
        watch_codes.append("signal_similarity_score_watch")
    if backtest_sample_depth_score < config.min_watch_backtest_sample_depth_score:
        block_codes.append("backtest_sample_depth_block")
    elif backtest_sample_depth_score < config.min_pass_backtest_sample_depth_score:
        watch_codes.append("backtest_sample_depth_watch")
    if backtest_success_rate < config.min_watch_backtest_success_rate:
        block_codes.append("backtest_success_rate_block")
    elif backtest_success_rate < config.min_pass_backtest_success_rate:
        watch_codes.append("backtest_success_rate_watch")
    if contradiction_pressure >= config.max_watch_contradiction_pressure:
        block_codes.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.max_pass_contradiction_pressure:
        watch_codes.append("contradiction_pressure_watch")
    if calibration_drift_pressure >= config.max_watch_calibration_drift_pressure:
        block_codes.append("calibration_drift_pressure_block")
    elif calibration_drift_pressure >= config.max_pass_calibration_drift_pressure:
        watch_codes.append("calibration_drift_pressure_watch")
    if block_codes:
        return _normalize_reason_codes("reason_codes", tuple(block_codes), ROW_REASON_CODES)
    if watch_codes:
        return _normalize_reason_codes("reason_codes", tuple(watch_codes), ROW_REASON_CODES)
    return (ROW_PASS_REASON_CODE,)


def _memory_reuse_backtest_readiness_score(
    item: ResearchTeamSpecialistMemoryReuseBacktestReadinessInput,
    *,
    backtest_sample_depth_score: Decimal,
    config: ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "memory_reuse_backtest_readiness_score",
            item.prior_reuse_hit_rate * config.prior_reuse_hit_rate_weight
            + item.signal_similarity_score * config.signal_similarity_score_weight
            + backtest_sample_depth_score * config.backtest_sample_depth_weight
            + item.backtest_success_rate * config.backtest_success_rate_weight
            + (ONE_RATIO - item.contradiction_pressure)
            * config.contradiction_reserve_weight
            + (ONE_RATIO - item.calibration_drift_pressure)
            * config.calibration_stability_weight,
        )


def _backtest_sample_depth_score(
    item: ResearchTeamSpecialistMemoryReuseBacktestReadinessInput,
    *,
    config: ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
) -> Decimal:
    if item.backtest_sample_count >= config.backtest_sample_target_count:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "backtest_sample_depth_score",
            item.backtest_sample_count / config.backtest_sample_target_count,
        )


def _normalize_inputs(
    value: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessInput, ...]
    | list[ResearchTeamSpecialistMemoryReuseBacktestReadinessInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryReuseBacktestReadinessInput:
            raise ValueError(
                "signals must contain "
                "ResearchTeamSpecialistMemoryReuseBacktestReadinessInput values",
            )
        _require_hard_flags("signal", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return rows


def _normalize_rows(
    value: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryReuseBacktestReadinessRow:
            raise ValueError("rows must contain readiness row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    expected = tuple(sorted(rows, key=lambda row: _row_reason_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamSpecialistMemoryReuseBacktestReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counter
    )


def _validate_report(
    report: ResearchTeamSpecialistMemoryReuseBacktestReadinessReport,
) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average_field(
        rows,
        "memory_reuse_backtest_readiness_score",
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.lowest_backtest_sample_count != _min_measure_field(
        rows,
        "backtest_sample_count",
    ):
        raise ValueError("lowest_backtest_sample_count must match rows")
    if report.highest_contradiction_pressure != _max_ratio_field(
        rows,
        "contradiction_pressure",
    ):
        raise ValueError("highest_contradiction_pressure must match rows")
    if report.oldest_memory_age_seconds != _max_measure_field(rows, "memory_age_seconds"):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if report.status != _status_rollup(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_public_payload_sha256(
    report: ResearchTeamSpecialistMemoryReuseBacktestReadinessReport,
) -> None:
    _normalize_sha256("public_payload_sha256", report.public_payload_sha256)
    if report.public_payload_sha256 != _report_public_payload_sha256(report):
        raise ValueError("public_payload_sha256 must match report fields")


def _report_public_payload_sha256(
    report: ResearchTeamSpecialistMemoryReuseBacktestReadinessReport,
) -> str:
    payload = asdict(report)
    payload.pop("public_payload_sha256", None)
    ready = _json_ready(payload)
    _reject_unsafe_public_payload("digest_payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _memory_digest(memory_reference: str) -> str:
    _require_memory_reference("memory_reference", memory_reference)
    return hashlib.sha256(memory_reference.encode("utf-8")).hexdigest()


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            field_name,
            sum((getattr(row, field_name) for row in rows), ZERO_RATIO)
            / Decimal(len(rows)),
        )


def _max_ratio_field(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(getattr(row, field_name) for row in rows)


def _max_measure_field(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(getattr(row, field_name) for row in rows)


def _min_measure_field(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(getattr(row, field_name) for row in rows)


def _status_rollup(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryReuseBacktestReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _status_rollup(rows)
    codes = [_report_status_reason_code(status)]
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status_reason_code(status: str) -> str:
    if status == BLOCK_STATUS:
        return REPORT_BLOCK_REASON_CODE
    if status == WATCH_STATUS:
        return REPORT_WATCH_REASON_CODE
    return REPORT_PASS_REASON_CODE


def _row_sort_key(
    row: ResearchTeamSpecialistMemoryReuseBacktestReadinessRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.contradiction_pressure,
        -row.memory_age_seconds,
        -row.memory_reuse_backtest_readiness_score,
        row.specialist_key,
        row.memory_digest,
    )


def _row_reason_rank(reason_code: str) -> int:
    return ROW_REASON_CODES.index(reason_code)


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    expected = tuple(
        reason_code
        for group in ROW_REASON_SEQUENCE
        for reason_code in group
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    score_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code
        in (
            "readiness_score_block",
            "readiness_score_watch",
            ROW_PASS_REASON_CODE,
        )
    )
    if len(score_reasons) != 1:
        raise ValueError("reason_codes must include exactly one readiness reason")
    if any(reason_code.endswith("_block") for reason_code in reason_codes) and any(
        reason_code.endswith("_watch") for reason_code in reason_codes
    ):
        raise ValueError("reason_codes must not mix block and watch detail")


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(value)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    for code in codes:
        _require_member(name, code, allowed)
    return codes


def _age_seconds(older_at: datetime, newer_at: datetime) -> Decimal:
    older = _as_utc("observed_at", older_at)
    newer = _as_utc("generated_at", newer_at)
    if older > newer:
        raise ValueError("observed_at must not be after generated_at")
    delta = newer - older
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _normalize_nonnegative_measure("memory_age_seconds", seconds)


def _require_weight_total(
    config: ResearchTeamSpecialistMemoryReuseBacktestReadinessConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = _quantize(
            config.prior_reuse_hit_rate_weight
            + config.signal_similarity_score_weight
            + config.backtest_sample_depth_weight
            + config.backtest_success_rate_weight
            + config.contradiction_reserve_weight
            + config.calibration_stability_weight,
            RATIO_QUANTUM,
        )
    if total != ONE_RATIO:
        raise ValueError("weights must total one")


def _require_descending_threshold(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value < watch_value:
        raise ValueError(f"pass_{name} must not be below watch_{name}")


def _require_ascending_threshold(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"pass_{name} must not exceed watch_{name}")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{expected_type.__name__} subclasses are not supported")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonblank trimmed string")


def _require_safe_label(name: str, value: object) -> str:
    _require_public_string(name, value)
    if _contains_restricted_public_content(value):
        raise ValueError(f"{name} must not expose restricted references")
    return value


def _require_memory_reference(name: str, value: object) -> str:
    _require_public_string(name, value)
    if _contains_restricted_public_content(value):
        raise ValueError(f"{name} must not expose restricted references")
    return value


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO or decimal > ONE_RATIO:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_measure(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO_RATIO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    with localcontext(DECIMAL_CONTEXT):
        if decimal < ZERO_COUNT:
            raise ValueError(f"{name} must be nonnegative")
        if decimal != decimal.to_integral_value():
            raise ValueError(f"{name} must be a whole count")
        return decimal.quantize(COUNT_QUANTUM)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(name, value)
    if count <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return count


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value), COUNT_QUANTUM)


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(name: str, payload: object) -> None:
    for value in _public_strings(_json_ready(payload)):
        if _contains_restricted_public_content(value):
            raise ValueError(f"{name} contains restricted public payload content")


def _contains_restricted_public_content(value: str) -> bool:
    lowered = value.casefold()
    compact = "".join(character for character in lowered if character.isalnum())
    for fragment in UNSAFE_VALUE_FRAGMENTS:
        if fragment in lowered:
            return True
        compact_fragment = "".join(
            character for character in fragment if character.isalnum()
        )
        if compact_fragment and compact_fragment in compact:
            return True
    return False


def _public_strings(value: object) -> tuple[str, ...]:
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_public_strings(item))
        return tuple(strings)
    return ()
