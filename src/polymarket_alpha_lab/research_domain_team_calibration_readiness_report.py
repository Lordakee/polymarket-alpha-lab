"""Pure report-only domain-team calibration readiness analytics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_READINESS_CONFIG_VERSION",
    "ResearchDomainTeamCalibrationReadinessConfig",
    "ResearchDomainTeamCalibrationReadinessObservation",
    "ResearchDomainTeamCalibrationReadinessReasonCodeCount",
    "ResearchDomainTeamCalibrationReadinessReport",
    "ResearchDomainTeamCalibrationReadinessRow",
    "build_research_domain_team_calibration_readiness_report",
    "research_domain_team_calibration_readiness_report_digest",
    "research_domain_team_calibration_readiness_report_payload",
)


DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_READINESS_CONFIG_VERSION = (
    "research-domain-team-calibration-readiness-report-v0"
)

NO_OBSERVATIONS_REASON = "domain_team_calibration_no_observations"
INSUFFICIENT_SETTLED_BLOCK_REASON = (
    "domain_team_calibration_insufficient_settled_count_block"
)
BRIER_SCORE_BLOCK_REASON = "domain_team_calibration_brier_score_block"
CALIBRATION_ERROR_BLOCK_REASON = "domain_team_calibration_error_block"
MEMORY_COVERAGE_BLOCK_REASON = "domain_team_calibration_memory_coverage_block"
INSUFFICIENT_SETTLED_WATCH_REASON = (
    "domain_team_calibration_insufficient_settled_count_watch"
)
BRIER_SCORE_WATCH_REASON = "domain_team_calibration_brier_score_watch"
CALIBRATION_ERROR_WATCH_REASON = "domain_team_calibration_error_watch"
MEMORY_COVERAGE_WATCH_REASON = "domain_team_calibration_memory_coverage_watch"
BLOCK_REASON = "domain_team_calibration_block"
WATCH_REASON = "domain_team_calibration_watch"
READY_REASON = "domain_team_calibration_ready"

REASON_CODES = (
    NO_OBSERVATIONS_REASON,
    INSUFFICIENT_SETTLED_BLOCK_REASON,
    BRIER_SCORE_BLOCK_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    MEMORY_COVERAGE_BLOCK_REASON,
    INSUFFICIENT_SETTLED_WATCH_REASON,
    BRIER_SCORE_WATCH_REASON,
    CALIBRATION_ERROR_WATCH_REASON,
    MEMORY_COVERAGE_WATCH_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    READY_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (
    NO_OBSERVATIONS_REASON,
    INSUFFICIENT_SETTLED_BLOCK_REASON,
    BRIER_SCORE_BLOCK_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    MEMORY_COVERAGE_BLOCK_REASON,
    BLOCK_REASON,
)
WATCH_REASONS = (
    INSUFFICIENT_SETTLED_WATCH_REASON,
    BRIER_SCORE_WATCH_REASON,
    CALIBRATION_ERROR_WATCH_REASON,
    MEMORY_COVERAGE_WATCH_REASON,
    WATCH_REASON,
)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {status: index for index, status in enumerate(STATUSES)}
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
SAFE_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_KEY_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "question",
    "raw_candidate",
    "raw_market",
    "slug",
    "source_text",
    "source_url",
    "dsn",
    "table",
    "token",
    "private",
    "wallet",
    "account",
    "auth",
    "order",
    "recommendation",
    "sizing",
)
UNSAFE_TEXT_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "candidate_id",
    "market_id",
    "market_slug",
    "dsn",
    "token",
    "bearer ",
    "private",
    "wallet",
    "order",
    "recommendation",
    "sizing",
)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationReadinessConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_READINESS_CONFIG_VERSION
    min_pass_settled_count: Decimal = Decimal("20")
    min_watch_settled_count: Decimal = Decimal("8")
    max_pass_brier_score: Decimal = Decimal("0.160000")
    max_watch_brier_score: Decimal = Decimal("0.240000")
    max_pass_calibration_error: Decimal = Decimal("0.060000")
    max_watch_calibration_error: Decimal = Decimal("0.120000")
    min_pass_memory_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_memory_coverage_ratio: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainTeamCalibrationReadinessConfig:
            raise TypeError(
                "ResearchDomainTeamCalibrationReadinessConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainTeamCalibrationReadinessConfig:
            raise ValueError(
                "config must be exactly ResearchDomainTeamCalibrationReadinessConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in ("min_pass_settled_count", "min_watch_settled_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_brier_score",
            "max_watch_brier_score",
            "max_pass_calibration_error",
            "max_watch_calibration_error",
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_settled_count > self.min_pass_settled_count:
            raise ValueError("min_watch_settled_count must not exceed pass threshold")
        if self.max_pass_brier_score > self.max_watch_brier_score:
            raise ValueError("max_pass_brier_score must not exceed watch threshold")
        if self.max_pass_calibration_error > self.max_watch_calibration_error:
            raise ValueError(
                "max_pass_calibration_error must not exceed watch threshold",
            )
        if self.min_pass_memory_coverage_ratio < self.min_watch_memory_coverage_ratio:
            raise ValueError(
                "min_pass_memory_coverage_ratio must not be below watch threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationReadinessObservation:
    domain_label: str
    team_key: str
    settled_count: Decimal
    brier_score: Decimal
    calibration_error: Decimal
    memory_coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainTeamCalibrationReadinessObservation:
            raise TypeError(
                "ResearchDomainTeamCalibrationReadinessObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainTeamCalibrationReadinessObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchDomainTeamCalibrationReadinessObservation",
            )
        _require_public_identifier("domain_label", self.domain_label)
        _require_public_identifier("team_key", self.team_key)
        object.__setattr__(
            self,
            "settled_count",
            _require_nonnegative_whole_decimal("settled_count", self.settled_count),
        )
        for field_name in (
            "brier_score",
            "calibration_error",
            "memory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationReadinessRow:
    domain_label: str
    team_key: str
    settled_count: Decimal
    brier_score: Decimal
    calibration_error: Decimal
    memory_coverage_ratio: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainTeamCalibrationReadinessRow:
            raise TypeError(
                "ResearchDomainTeamCalibrationReadinessRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainTeamCalibrationReadinessRow:
            raise ValueError("row must be exactly ResearchDomainTeamCalibrationReadinessRow")
        _require_public_identifier("domain_label", self.domain_label)
        _require_public_identifier("team_key", self.team_key)
        object.__setattr__(
            self,
            "settled_count",
            _require_nonnegative_whole_decimal("settled_count", self.settled_count),
        )
        for field_name in (
            "brier_score",
            "calibration_error",
            "memory_coverage_ratio",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainTeamCalibrationReadinessReasonCodeCount:
            raise TypeError(
                "ResearchDomainTeamCalibrationReadinessReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainTeamCalibrationReadinessReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDomainTeamCalibrationReadinessReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationReadinessReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_team_count: Decimal
    settled_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_brier_score: Decimal | None
    average_calibration_error: Decimal | None
    average_memory_coverage_ratio: Decimal | None
    lowest_memory_coverage_ratio: Decimal | None
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...]
    reason_code_counts: tuple[ResearchDomainTeamCalibrationReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainTeamCalibrationReadinessReport:
            raise TypeError(
                "ResearchDomainTeamCalibrationReadinessReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainTeamCalibrationReadinessReport:
            raise ValueError(
                "report must be exactly ResearchDomainTeamCalibrationReadinessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "domain_team_count",
            "settled_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_brier_score",
            "average_calibration_error",
            "average_memory_coverage_ratio",
            "lowest_memory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_domain_team_calibration_readiness_report(
    observations: Iterable[object],
    *,
    config: ResearchDomainTeamCalibrationReadinessConfig,
    generated_at: datetime,
) -> ResearchDomainTeamCalibrationReadinessReport:
    if type(config) is not ResearchDomainTeamCalibrationReadinessConfig:
        raise ValueError("config must be a ResearchDomainTeamCalibrationReadinessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(item, config=config) for item in normalized_observations),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _status_for_reason_codes(reason_codes),
        "domain_team_count": _decimal_count(len(rows)),
        "settled_count": sum((row.settled_count for row in rows), ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_brier_score": _weighted_row_average(rows, "brier_score"),
        "average_calibration_error": _weighted_row_average(rows, "calibration_error"),
        "average_memory_coverage_ratio": _weighted_row_average(
            rows,
            "memory_coverage_ratio",
        ),
        "lowest_memory_coverage_ratio": _min_row_decimal(
            rows,
            "memory_coverage_ratio",
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainTeamCalibrationReadinessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_domain_team_calibration_readiness_report_payload(
    report: ResearchDomainTeamCalibrationReadinessReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchDomainTeamCalibrationReadinessReport:
        _require_hard_flags("report", report)
        payload = _payload_value(asdict(report))
    elif isinstance(report, Mapping):
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchDomainTeamCalibrationReadinessReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    _require_hard_flags("report payload", _MappingFlags(payload))
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_domain_team_calibration_readiness_report_digest(
    report: ResearchDomainTeamCalibrationReadinessReport | Mapping[str, object],
) -> str:
    payload = research_domain_team_calibration_readiness_report_payload(report)
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


def _row_from_observation(
    observation: ResearchDomainTeamCalibrationReadinessObservation,
    *,
    config: ResearchDomainTeamCalibrationReadinessConfig,
) -> ResearchDomainTeamCalibrationReadinessRow:
    reason_codes = _row_reason_codes(observation, config=config)
    return ResearchDomainTeamCalibrationReadinessRow(
        domain_label=observation.domain_label,
        team_key=observation.team_key,
        settled_count=observation.settled_count,
        brier_score=observation.brier_score,
        calibration_error=observation.calibration_error,
        memory_coverage_ratio=observation.memory_coverage_ratio,
        readiness_score=_readiness_score(observation, config=config),
        status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchDomainTeamCalibrationReadinessObservation,
    *,
    config: ResearchDomainTeamCalibrationReadinessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.settled_count < config.min_watch_settled_count:
        reason_codes.append(INSUFFICIENT_SETTLED_BLOCK_REASON)
    elif observation.settled_count < config.min_pass_settled_count:
        reason_codes.append(INSUFFICIENT_SETTLED_WATCH_REASON)
    if observation.brier_score > config.max_watch_brier_score:
        reason_codes.append(BRIER_SCORE_BLOCK_REASON)
    elif observation.brier_score > config.max_pass_brier_score:
        reason_codes.append(BRIER_SCORE_WATCH_REASON)
    if observation.calibration_error > config.max_watch_calibration_error:
        reason_codes.append(CALIBRATION_ERROR_BLOCK_REASON)
    elif observation.calibration_error > config.max_pass_calibration_error:
        reason_codes.append(CALIBRATION_ERROR_WATCH_REASON)
    if observation.memory_coverage_ratio < config.min_watch_memory_coverage_ratio:
        reason_codes.append(MEMORY_COVERAGE_BLOCK_REASON)
    elif observation.memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        reason_codes.append(MEMORY_COVERAGE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    else:
        status = _status_for_reason_codes(tuple(reason_codes))
        reason_codes.append(BLOCK_REASON if status == "block" else WATCH_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _readiness_score(
    observation: ResearchDomainTeamCalibrationReadinessObservation,
    *,
    config: ResearchDomainTeamCalibrationReadinessConfig,
) -> Decimal:
    settled_component = _clamp_ratio(
        observation.settled_count / config.min_pass_settled_count,
    )
    brier_component = ONE - observation.brier_score
    calibration_component = ONE - observation.calibration_error
    return _quantize_ratio(
        (
            settled_component
            + brier_component
            + calibration_component
            + observation.memory_coverage_ratio
        )
        / Decimal("4"),
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchDomainTeamCalibrationReadinessObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchDomainTeamCalibrationReadinessObservation] = []
    seen_pairs: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not ResearchDomainTeamCalibrationReadinessObservation:
            raise ValueError(
                "observations must contain "
                "ResearchDomainTeamCalibrationReadinessObservation items",
            )
        _require_hard_flags("observation", value)
        pair = (value.domain_label, value.team_key)
        if pair in seen_pairs:
            raise ValueError("domain_label/team_key pairs must be unique")
        seen_pairs.add(pair)
        normalized.append(value)
    return tuple(normalized)


def _report_reason_codes(
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != READY_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != READY_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchDomainTeamCalibrationReadinessReasonCodeCount, ...]:
    if reason_codes == (NO_OBSERVATIONS_REASON,):
        return (
            ResearchDomainTeamCalibrationReadinessReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchDomainTeamCalibrationReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_report(report: ResearchDomainTeamCalibrationReadinessReport) -> None:
    if report.domain_team_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_team_count must match rows")
    if report.settled_count != sum((row.settled_count for row in report.rows), ZERO):
        raise ValueError("settled_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_brier_score != _weighted_row_average(report.rows, "brier_score"):
        raise ValueError("average_brier_score must match rows")
    if report.average_calibration_error != _weighted_row_average(
        report.rows,
        "calibration_error",
    ):
        raise ValueError("average_calibration_error must match rows")
    if report.average_memory_coverage_ratio != _weighted_row_average(
        report.rows,
        "memory_coverage_ratio",
    ):
        raise ValueError("average_memory_coverage_ratio must match rows")
    if report.lowest_memory_coverage_ratio != _min_row_decimal(
        report.rows,
        "memory_coverage_ratio",
    ):
        raise ValueError("lowest_memory_coverage_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...],
) -> tuple[ResearchDomainTeamCalibrationReadinessRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_pairs: set[tuple[str, str]] = set()
    for row in normalized_rows:
        if type(row) is not ResearchDomainTeamCalibrationReadinessRow:
            raise ValueError(
                "rows must contain ResearchDomainTeamCalibrationReadinessRow",
            )
        _require_hard_flags("row", row)
        pair = (row.domain_label, row.team_key)
        if pair in seen_pairs:
            raise ValueError("rows domain_label/team_key pairs must be unique")
        seen_pairs.add(pair)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized_rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchDomainTeamCalibrationReadinessReasonCodeCount, ...],
) -> tuple[ResearchDomainTeamCalibrationReadinessReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not ResearchDomainTeamCalibrationReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainTeamCalibrationReadinessReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    expected = tuple(
        sorted(normalized_counts, key=lambda count: REASON_CODE_RANK[count.reason_code])
    )
    if normalized_counts != expected:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized_counts


def _row_sort_key(row: ResearchDomainTeamCalibrationReadinessRow) -> tuple[int, str, str]:
    return (STATUS_RANK[row.status], row.domain_label, row.team_key)


def _status_count(
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _weighted_row_average(
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...],
    field_name: str,
) -> Decimal | None:
    return _average_decimal(tuple(getattr(row, field_name) for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _min_row_decimal(
    rows: tuple[ResearchDomainTeamCalibrationReadinessRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return min(getattr(row, field_name) for row in rows)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = value.lower()
    if normalized != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_RANK:
        raise ValueError(f"{field_name} must be a known reason code")
    if any(character not in SAFE_REASON_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    stable_codes = tuple(
        reason_code for reason_code in REASON_CODES if reason_code in reason_codes
    )
    if stable_codes != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value.quantize(COUNT_QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != _ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


_ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchDomainTeamCalibrationReadinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload(
        "digest payload",
        payload,
        allow_json_containers=True,
    )
    return _digest_from_unsigned_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(unsigned)


def _digest_from_unsigned_payload(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return _payload_mapping(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_mapping(value: Mapping[Any, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        payload[key] = _payload_value(item)
    return payload


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_unsafe_key(key):
                raise ValueError(f"unsafe field in {label}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple) or (allow_json_containers and isinstance(value, list)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_text(value):
        raise ValueError(f"{label} has unsafe value")


def _has_unsafe_key(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_KEY_FRAGMENTS)


def _has_unsafe_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)
