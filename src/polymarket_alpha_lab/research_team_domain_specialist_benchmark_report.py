"""Pure report-only benchmark for team-domain specialist quality."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import (
    Context,
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_HALF_EVEN,
    localcontext,
)
from hashlib import sha256
import json


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_BENCHMARK_CONFIG_VERSION",
    "ResearchTeamDomainSpecialistBenchmarkConfig",
    "ResearchTeamDomainSpecialistBenchmarkFact",
    "ResearchTeamDomainSpecialistBenchmarkReasonCodeCount",
    "ResearchTeamDomainSpecialistBenchmarkReport",
    "ResearchTeamDomainSpecialistBenchmarkRow",
    "build_research_team_domain_specialist_benchmark_report",
    "research_team_domain_specialist_benchmark_report_digest",
    "research_team_domain_specialist_benchmark_report_payload",
)


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_BENCHMARK_CONFIG_VERSION = (
    "research-team-domain-specialist-benchmark-report-v0"
)

NO_FACTS_REASON = "no_team_domain_specialist_benchmark_facts"
INSUFFICIENT_SAMPLE_REASON = "benchmark_forecast_sample_count_block"
CALIBRATION_BLOCK_REASON = "benchmark_calibration_accuracy_block"
CALIBRATION_WATCH_REASON = "benchmark_calibration_accuracy_watch"
MEMORY_BLOCK_REASON = "benchmark_memory_freshness_block"
MEMORY_WATCH_REASON = "benchmark_memory_freshness_watch"
WORKLOAD_BLOCK_REASON = "benchmark_workload_block"
WORKLOAD_WATCH_REASON = "benchmark_workload_watch"
SOURCE_COVERAGE_BLOCK_REASON = "benchmark_source_coverage_block"
SOURCE_COVERAGE_WATCH_REASON = "benchmark_source_coverage_watch"
CORRECTION_BLOCK_REASON = "benchmark_correction_followthrough_block"
CORRECTION_WATCH_REASON = "benchmark_correction_followthrough_watch"
BENCHMARK_BLOCK_REASON = "team_domain_specialist_benchmark_block"
BENCHMARK_WATCH_REASON = "team_domain_specialist_benchmark_watch"
BENCHMARK_PASS_REASON = "team_domain_specialist_benchmark_pass"

REASON_CODES = (
    NO_FACTS_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    CALIBRATION_BLOCK_REASON,
    MEMORY_BLOCK_REASON,
    WORKLOAD_BLOCK_REASON,
    SOURCE_COVERAGE_BLOCK_REASON,
    CORRECTION_BLOCK_REASON,
    CALIBRATION_WATCH_REASON,
    MEMORY_WATCH_REASON,
    WORKLOAD_WATCH_REASON,
    SOURCE_COVERAGE_WATCH_REASON,
    CORRECTION_WATCH_REASON,
    BENCHMARK_BLOCK_REASON,
    BENCHMARK_WATCH_REASON,
    BENCHMARK_PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (
    NO_FACTS_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    CALIBRATION_BLOCK_REASON,
    MEMORY_BLOCK_REASON,
    WORKLOAD_BLOCK_REASON,
    SOURCE_COVERAGE_BLOCK_REASON,
    CORRECTION_BLOCK_REASON,
    BENCHMARK_BLOCK_REASON,
)
WATCH_REASONS = (
    CALIBRATION_WATCH_REASON,
    MEMORY_WATCH_REASON,
    WORKLOAD_WATCH_REASON,
    SOURCE_COVERAGE_WATCH_REASON,
    CORRECTION_WATCH_REASON,
    BENCHMARK_WATCH_REASON,
)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {status: index for index, status in enumerate(STATUSES)}

ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE = Decimal("1.000000")
ONE_COUNT = Decimal("1")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
CALIBRATION_WEIGHT = Decimal("0.300000")
MEMORY_WEIGHT = Decimal("0.200000")
WORKLOAD_WEIGHT = Decimal("0.150000")
SOURCE_COVERAGE_WEIGHT = Decimal("0.200000")
CORRECTION_WEIGHT = Decimal("0.150000")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
SAFE_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_KEY_FRAGMENTS = (
    "candidate_" + "id",
    "condition_" + "id",
    "mar" + "ket_id",
    "mar" + "ket_slug",
    "ques" + "tion",
    "raw_candidate",
    "raw_mar" + "ket",
    "slug",
    "source_" + "url",
    "source_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "pri" + "vate",
    "wal" + "let",
    "account",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "reco" + "mmend",
    "siz" + "ing",
)
UNSAFE_TEXT_FRAGMENTS = (
    "http" + "://",
    "https" + "://",
    "://",
    "candidate_" + "id",
    "mar" + "ket_id",
    "mar" + "ket_slug",
    "source_" + "url",
    "source_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "bearer ",
    "pri" + "vate",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "reco" + "mmend",
    "siz" + "ing",
    "au" + "th",
    "li" + "ve",
    "data" + "base",
    "net" + "work",
)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistBenchmarkConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_BENCHMARK_CONFIG_VERSION
    )
    min_forecast_sample_count: Decimal = Decimal("10")
    min_pass_calibration_accuracy: Decimal = Decimal("0.850000")
    min_watch_calibration_accuracy: Decimal = Decimal("0.700000")
    min_pass_memory_freshness_ratio: Decimal = Decimal("0.800000")
    min_watch_memory_freshness_ratio: Decimal = Decimal("0.600000")
    max_pass_workload_open_item_count: Decimal = Decimal("8")
    max_watch_workload_open_item_count: Decimal = Decimal("16")
    min_pass_source_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_source_coverage_ratio: Decimal = Decimal("0.600000")
    min_pass_correction_followthrough_ratio: Decimal = Decimal("0.750000")
    min_watch_correction_followthrough_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistBenchmarkConfig:
            raise TypeError(
                "ResearchTeamDomainSpecialistBenchmarkConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistBenchmarkConfig:
            raise ValueError(
                "config must be exactly ResearchTeamDomainSpecialistBenchmarkConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_forecast_sample_count",
            _require_positive_whole_decimal(
                "min_forecast_sample_count",
                self.min_forecast_sample_count,
            ),
        )
        for field_name in (
            "min_pass_calibration_accuracy",
            "min_watch_calibration_accuracy",
            "min_pass_memory_freshness_ratio",
            "min_watch_memory_freshness_ratio",
            "min_pass_source_coverage_ratio",
            "min_watch_source_coverage_ratio",
            "min_pass_correction_followthrough_ratio",
            "min_watch_correction_followthrough_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_workload_open_item_count",
            "max_watch_workload_open_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_pass_above_watch(
            "calibration_accuracy",
            self.min_pass_calibration_accuracy,
            self.min_watch_calibration_accuracy,
        )
        _require_pass_above_watch(
            "memory_freshness_ratio",
            self.min_pass_memory_freshness_ratio,
            self.min_watch_memory_freshness_ratio,
        )
        _require_pass_above_watch(
            "source_coverage_ratio",
            self.min_pass_source_coverage_ratio,
            self.min_watch_source_coverage_ratio,
        )
        _require_pass_above_watch(
            "correction_followthrough_ratio",
            self.min_pass_correction_followthrough_ratio,
            self.min_watch_correction_followthrough_ratio,
        )
        if self.max_pass_workload_open_item_count >= self.max_watch_workload_open_item_count:
            raise ValueError("workload watch threshold must exceed pass threshold")
        for config_field in fields(self):
            if config_field.name in (
                "config_version",
                "paper_only",
                "report_only",
                "readonly",
            ):
                continue
            if getattr(self, config_field.name) != config_field.default:
                raise ValueError(f"{config_field.name} must use supported default")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistBenchmarkFact:
    team_key: str
    domain_key: str
    specialist_key: str
    forecast_sample_count: Decimal
    calibration_accuracy: Decimal
    memory_freshness_ratio: Decimal
    workload_open_item_count: Decimal
    source_coverage_ratio: Decimal
    correction_followthrough_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistBenchmarkFact:
            raise TypeError(
                "ResearchTeamDomainSpecialistBenchmarkFact "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistBenchmarkFact:
            raise ValueError(
                "fact must be exactly ResearchTeamDomainSpecialistBenchmarkFact",
            )
        for field_name in ("team_key", "domain_key", "specialist_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "calibration_accuracy",
            "memory_freshness_ratio",
            "source_coverage_ratio",
            "correction_followthrough_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "forecast_sample_count",
            _require_nonnegative_whole_decimal(
                "forecast_sample_count",
                self.forecast_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "workload_open_item_count",
            _require_nonnegative_whole_decimal(
                "workload_open_item_count",
                self.workload_open_item_count,
            ),
        )
        _require_hard_flags("fact", self)
        _reject_unsafe_public_payload("fact", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistBenchmarkRow:
    team_key: str
    domain_key: str
    specialist_count: Decimal
    forecast_sample_count: Decimal
    calibration_accuracy: Decimal
    memory_freshness_ratio: Decimal
    workload_open_item_count: Decimal
    workload_capacity_score: Decimal
    source_coverage_ratio: Decimal
    correction_followthrough_ratio: Decimal
    benchmark_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistBenchmarkRow:
            raise TypeError(
                "ResearchTeamDomainSpecialistBenchmarkRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistBenchmarkRow:
            raise ValueError(
                "row must be exactly ResearchTeamDomainSpecialistBenchmarkRow",
            )
        for field_name in ("team_key", "domain_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "specialist_count",
            _require_positive_whole_decimal(
                "specialist_count",
                self.specialist_count,
            ),
        )
        object.__setattr__(
            self,
            "forecast_sample_count",
            _require_nonnegative_whole_decimal(
                "forecast_sample_count",
                self.forecast_sample_count,
            ),
        )
        for field_name in (
            "calibration_accuracy",
            "memory_freshness_ratio",
            "workload_capacity_score",
            "source_coverage_ratio",
            "correction_followthrough_ratio",
            "benchmark_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "workload_open_item_count",
            _require_nonnegative_whole_decimal(
                "workload_open_item_count",
                self.workload_open_item_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistBenchmarkReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistBenchmarkReasonCodeCount:
            raise TypeError(
                "ResearchTeamDomainSpecialistBenchmarkReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistBenchmarkReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchTeamDomainSpecialistBenchmarkReasonCodeCount",
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
class ResearchTeamDomainSpecialistBenchmarkReport:
    generated_at: datetime
    config_version: str
    status: str
    team_domain_count: Decimal
    specialist_count: Decimal
    forecast_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_accuracy: Decimal | None
    average_memory_freshness_ratio: Decimal | None
    total_workload_open_item_count: Decimal
    average_source_coverage_ratio: Decimal | None
    average_correction_followthrough_ratio: Decimal | None
    average_benchmark_score: Decimal | None
    top_benchmark_score: Decimal | None
    bottom_benchmark_score: Decimal | None
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainSpecialistBenchmarkReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistBenchmarkReport:
            raise TypeError(
                "ResearchTeamDomainSpecialistBenchmarkReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistBenchmarkReport:
            raise ValueError(
                "report must be exactly ResearchTeamDomainSpecialistBenchmarkReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "team_domain_count",
            "specialist_count",
            "forecast_sample_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_workload_open_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_accuracy",
            "average_memory_freshness_ratio",
            "average_source_coverage_ratio",
            "average_correction_followthrough_ratio",
            "average_benchmark_score",
            "top_benchmark_score",
            "bottom_benchmark_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
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

    @property
    def payload(self) -> dict[str, object]:
        return research_team_domain_specialist_benchmark_report_payload(self)


def build_research_team_domain_specialist_benchmark_report(
    facts: Iterable[object],
    *,
    config: ResearchTeamDomainSpecialistBenchmarkConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistBenchmarkReport:
    with localcontext(DECIMAL_CONTEXT):
        return _build_research_team_domain_specialist_benchmark_report(
            facts,
            config=config,
            generated_at=generated_at,
        )


def _build_research_team_domain_specialist_benchmark_report(
    facts: Iterable[object],
    *,
    config: ResearchTeamDomainSpecialistBenchmarkConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistBenchmarkReport:
    if type(config) is not ResearchTeamDomainSpecialistBenchmarkConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainSpecialistBenchmarkConfig",
        )
    config = _revalidated_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_facts = _normalize_facts(facts)
    rows = tuple(
        sorted(
            (
                _row_from_group(group, config=config)
                for group in _facts_by_team_domain(normalized_facts)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": status,
        "team_domain_count": _decimal_count(len(rows)),
        "specialist_count": sum((row.specialist_count for row in rows), ZERO),
        "forecast_sample_count": sum((row.forecast_sample_count for row in rows), ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_calibration_accuracy": _weighted_row_average(
            rows,
            "calibration_accuracy",
        ),
        "average_memory_freshness_ratio": _weighted_row_average(
            rows,
            "memory_freshness_ratio",
        ),
        "total_workload_open_item_count": sum(
            (row.workload_open_item_count for row in rows),
            ZERO,
        ),
        "average_source_coverage_ratio": _weighted_row_average(
            rows,
            "source_coverage_ratio",
        ),
        "average_correction_followthrough_ratio": _weighted_row_average(
            rows,
            "correction_followthrough_ratio",
        ),
        "average_benchmark_score": _weighted_row_average(rows, "benchmark_score"),
        "top_benchmark_score": _max_row_decimal(rows, "benchmark_score"),
        "bottom_benchmark_score": _min_row_decimal(rows, "benchmark_score"),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainSpecialistBenchmarkReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_specialist_benchmark_report_payload(
    report: ResearchTeamDomainSpecialistBenchmarkReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSpecialistBenchmarkReport:
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = _json_payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSpecialistBenchmarkReport "
            "or exact JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    _require_payload_hard_flags("report payload", payload)
    _validate_public_payload_schema(payload)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    validated_report = _report_from_payload(payload)
    if _payload_value(asdict(validated_report)) != payload:
        raise ValueError("report payload must use canonical schema values")
    return payload


def research_team_domain_specialist_benchmark_report_digest(
    report: ResearchTeamDomainSpecialistBenchmarkReport | dict[str, object],
) -> str:
    payload = research_team_domain_specialist_benchmark_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _validate_public_payload_schema(payload: dict[str, object]) -> None:
    _require_exact_payload_keys(
        "report payload",
        payload,
        tuple(
            field.name
            for field in fields(ResearchTeamDomainSpecialistBenchmarkReport)
        ),
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("report payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("report payload rows must contain JSON objects")
        _require_exact_payload_keys(
            "report payload row",
            row,
            tuple(
                field.name
                for field in fields(ResearchTeamDomainSpecialistBenchmarkRow)
            ),
        )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("report payload reason_code_counts must be a list")
    for count in reason_code_counts:
        if type(count) is not dict:
            raise ValueError(
                "report payload reason_code_counts must contain JSON objects",
            )
        _require_exact_payload_keys(
            "report payload reason code count",
            count,
            tuple(
                field.name
                for field in fields(
                    ResearchTeamDomainSpecialistBenchmarkReasonCodeCount,
                )
            ),
        )


def _require_exact_payload_keys(
    label: str,
    payload: dict[str, object],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(payload) != expected_keys:
        raise ValueError(f"{label} must use exact schema")


def _report_from_payload(
    payload: dict[str, object],
) -> ResearchTeamDomainSpecialistBenchmarkReport:
    return ResearchTeamDomainSpecialistBenchmarkReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload(
            "config_version",
            payload["config_version"],
        ),
        status=_string_from_payload("status", payload["status"]),
        team_domain_count=_nonnegative_count_from_payload(
            "team_domain_count",
            payload["team_domain_count"],
        ),
        specialist_count=_nonnegative_count_from_payload(
            "specialist_count",
            payload["specialist_count"],
        ),
        forecast_sample_count=_nonnegative_count_from_payload(
            "forecast_sample_count",
            payload["forecast_sample_count"],
        ),
        pass_count=_nonnegative_count_from_payload(
            "pass_count",
            payload["pass_count"],
        ),
        watch_count=_nonnegative_count_from_payload(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_nonnegative_count_from_payload(
            "block_count",
            payload["block_count"],
        ),
        average_calibration_accuracy=_optional_probability_from_payload(
            "average_calibration_accuracy",
            payload["average_calibration_accuracy"],
        ),
        average_memory_freshness_ratio=_optional_probability_from_payload(
            "average_memory_freshness_ratio",
            payload["average_memory_freshness_ratio"],
        ),
        total_workload_open_item_count=_nonnegative_count_from_payload(
            "total_workload_open_item_count",
            payload["total_workload_open_item_count"],
        ),
        average_source_coverage_ratio=_optional_probability_from_payload(
            "average_source_coverage_ratio",
            payload["average_source_coverage_ratio"],
        ),
        average_correction_followthrough_ratio=_optional_probability_from_payload(
            "average_correction_followthrough_ratio",
            payload["average_correction_followthrough_ratio"],
        ),
        average_benchmark_score=_optional_probability_from_payload(
            "average_benchmark_score",
            payload["average_benchmark_score"],
        ),
        top_benchmark_score=_optional_probability_from_payload(
            "top_benchmark_score",
            payload["top_benchmark_score"],
        ),
        bottom_benchmark_score=_optional_probability_from_payload(
            "bottom_benchmark_score",
            payload["bottom_benchmark_score"],
        ),
        rows=tuple(
            _row_from_payload(row)
            for row in _list_from_payload("rows", payload["rows"])
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(count)
            for count in _list_from_payload(
                "reason_code_counts",
                payload["reason_code_counts"],
            )
        ),
        reason_codes=tuple(
            _string_from_payload("reason_codes", reason_code)
            for reason_code in _list_from_payload(
                "reason_codes",
                payload["reason_codes"],
            )
        ),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
) -> ResearchTeamDomainSpecialistBenchmarkRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    return ResearchTeamDomainSpecialistBenchmarkRow(
        team_key=_string_from_payload("team_key", value["team_key"]),
        domain_key=_string_from_payload("domain_key", value["domain_key"]),
        specialist_count=_positive_count_from_payload(
            "specialist_count",
            value["specialist_count"],
        ),
        forecast_sample_count=_nonnegative_count_from_payload(
            "forecast_sample_count",
            value["forecast_sample_count"],
        ),
        calibration_accuracy=_probability_from_payload(
            "calibration_accuracy",
            value["calibration_accuracy"],
        ),
        memory_freshness_ratio=_probability_from_payload(
            "memory_freshness_ratio",
            value["memory_freshness_ratio"],
        ),
        workload_open_item_count=_nonnegative_count_from_payload(
            "workload_open_item_count",
            value["workload_open_item_count"],
        ),
        workload_capacity_score=_probability_from_payload(
            "workload_capacity_score",
            value["workload_capacity_score"],
        ),
        source_coverage_ratio=_probability_from_payload(
            "source_coverage_ratio",
            value["source_coverage_ratio"],
        ),
        correction_followthrough_ratio=_probability_from_payload(
            "correction_followthrough_ratio",
            value["correction_followthrough_ratio"],
        ),
        benchmark_score=_probability_from_payload(
            "benchmark_score",
            value["benchmark_score"],
        ),
        status=_string_from_payload("status", value["status"]),
        reason_codes=tuple(
            _string_from_payload("reason_codes", reason_code)
            for reason_code in _list_from_payload(
                "reason_codes",
                value["reason_codes"],
            )
        ),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
) -> ResearchTeamDomainSpecialistBenchmarkReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    return ResearchTeamDomainSpecialistBenchmarkReasonCodeCount(
        reason_code=_string_from_payload("reason_code", value["reason_code"]),
        count=_positive_count_from_payload("count", value["count"]),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _list_from_payload(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _true_from_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    text = _string_from_payload(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{field_name} must use canonical UTC datetime text")
    return normalized


def _raw_decimal_from_payload(field_name: str, value: object) -> Decimal:
    text = _string_from_payload(field_name, value)
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return parsed


def _probability_from_payload(field_name: str, value: object) -> Decimal:
    text = _string_from_payload(field_name, value)
    normalized = _require_probability_decimal(
        field_name,
        _raw_decimal_from_payload(field_name, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{field_name} must use canonical Decimal text")
    return normalized


def _optional_probability_from_payload(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _probability_from_payload(field_name, value)


def _nonnegative_count_from_payload(field_name: str, value: object) -> Decimal:
    text = _string_from_payload(field_name, value)
    normalized = _require_nonnegative_whole_decimal(
        field_name,
        _raw_decimal_from_payload(field_name, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{field_name} must use canonical Decimal text")
    return normalized


def _positive_count_from_payload(field_name: str, value: object) -> Decimal:
    text = _string_from_payload(field_name, value)
    normalized = _require_positive_whole_decimal(
        field_name,
        _raw_decimal_from_payload(field_name, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{field_name} must use canonical Decimal text")
    return normalized


def _json_payload_value(value: object) -> object:
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_key("payload", key)
            payload[key] = _json_payload_value(item)
        return payload
    if type(value) is list:
        return [_json_payload_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        if type(value) is str and _has_unsafe_text(value):
            raise ValueError("payload contains unsafe public value")
        return value
    if type(value) in (Decimal, datetime, int, float):
        raise ValueError("payload numerics must use canonical Decimal strings")
    raise ValueError("payload must use JSON-compatible schema values")


def _row_from_group(
    facts: tuple[ResearchTeamDomainSpecialistBenchmarkFact, ...],
    *,
    config: ResearchTeamDomainSpecialistBenchmarkConfig,
) -> ResearchTeamDomainSpecialistBenchmarkRow:
    team_key = facts[0].team_key
    domain_key = facts[0].domain_key
    forecast_sample_count = sum((fact.forecast_sample_count for fact in facts), ZERO)
    workload_open_item_count = sum(
        (fact.workload_open_item_count for fact in facts),
        ZERO,
    )
    calibration_accuracy = _weighted_fact_average(facts, "calibration_accuracy")
    memory_freshness_ratio = _weighted_fact_average(facts, "memory_freshness_ratio")
    source_coverage_ratio = _weighted_fact_average(facts, "source_coverage_ratio")
    correction_followthrough_ratio = _weighted_fact_average(
        facts,
        "correction_followthrough_ratio",
    )
    workload_capacity_score = _workload_capacity_score(
        workload_open_item_count,
        config,
    )
    benchmark_score = _benchmark_score(
        calibration_accuracy=calibration_accuracy,
        memory_freshness_ratio=memory_freshness_ratio,
        workload_capacity_score=workload_capacity_score,
        source_coverage_ratio=source_coverage_ratio,
        correction_followthrough_ratio=correction_followthrough_ratio,
    )
    reason_codes = _row_reason_codes(
        forecast_sample_count=forecast_sample_count,
        calibration_accuracy=calibration_accuracy,
        memory_freshness_ratio=memory_freshness_ratio,
        workload_open_item_count=workload_open_item_count,
        source_coverage_ratio=source_coverage_ratio,
        correction_followthrough_ratio=correction_followthrough_ratio,
        config=config,
    )
    return ResearchTeamDomainSpecialistBenchmarkRow(
        team_key=team_key,
        domain_key=domain_key,
        specialist_count=_decimal_count(len({fact.specialist_key for fact in facts})),
        forecast_sample_count=forecast_sample_count,
        calibration_accuracy=calibration_accuracy,
        memory_freshness_ratio=memory_freshness_ratio,
        workload_open_item_count=workload_open_item_count,
        workload_capacity_score=workload_capacity_score,
        source_coverage_ratio=source_coverage_ratio,
        correction_followthrough_ratio=correction_followthrough_ratio,
        benchmark_score=benchmark_score,
        status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    forecast_sample_count: Decimal,
    calibration_accuracy: Decimal,
    memory_freshness_ratio: Decimal,
    workload_open_item_count: Decimal,
    source_coverage_ratio: Decimal,
    correction_followthrough_ratio: Decimal,
    config: ResearchTeamDomainSpecialistBenchmarkConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if forecast_sample_count < config.min_forecast_sample_count:
        reason_codes.append(INSUFFICIENT_SAMPLE_REASON)
    if calibration_accuracy < config.min_watch_calibration_accuracy:
        reason_codes.append(CALIBRATION_BLOCK_REASON)
    elif calibration_accuracy < config.min_pass_calibration_accuracy:
        reason_codes.append(CALIBRATION_WATCH_REASON)
    if memory_freshness_ratio < config.min_watch_memory_freshness_ratio:
        reason_codes.append(MEMORY_BLOCK_REASON)
    elif memory_freshness_ratio < config.min_pass_memory_freshness_ratio:
        reason_codes.append(MEMORY_WATCH_REASON)
    if workload_open_item_count > config.max_watch_workload_open_item_count:
        reason_codes.append(WORKLOAD_BLOCK_REASON)
    elif workload_open_item_count > config.max_pass_workload_open_item_count:
        reason_codes.append(WORKLOAD_WATCH_REASON)
    if source_coverage_ratio < config.min_watch_source_coverage_ratio:
        reason_codes.append(SOURCE_COVERAGE_BLOCK_REASON)
    elif source_coverage_ratio < config.min_pass_source_coverage_ratio:
        reason_codes.append(SOURCE_COVERAGE_WATCH_REASON)
    if correction_followthrough_ratio < config.min_watch_correction_followthrough_ratio:
        reason_codes.append(CORRECTION_BLOCK_REASON)
    elif correction_followthrough_ratio < config.min_pass_correction_followthrough_ratio:
        reason_codes.append(CORRECTION_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(BENCHMARK_PASS_REASON)
    else:
        status = _status_for_reason_codes(tuple(reason_codes))
        reason_codes.append(
            BENCHMARK_BLOCK_REASON if status == "block" else BENCHMARK_WATCH_REASON,
        )
    return _combined_reason_codes(tuple(reason_codes))


def _benchmark_score(
    *,
    calibration_accuracy: Decimal,
    memory_freshness_ratio: Decimal,
    workload_capacity_score: Decimal,
    source_coverage_ratio: Decimal,
    correction_followthrough_ratio: Decimal,
) -> Decimal:
    return _clamp_probability(
        _quantize_ratio(
            calibration_accuracy * CALIBRATION_WEIGHT
            + memory_freshness_ratio * MEMORY_WEIGHT
            + workload_capacity_score * WORKLOAD_WEIGHT
            + source_coverage_ratio * SOURCE_COVERAGE_WEIGHT
            + correction_followthrough_ratio * CORRECTION_WEIGHT,
        ),
    )


def _workload_capacity_score(
    workload_open_item_count: Decimal,
    config: ResearchTeamDomainSpecialistBenchmarkConfig,
) -> Decimal:
    return _clamp_probability(
        _quantize_ratio(
            ONE
            - _pressure_ratio(
                workload_open_item_count,
                config.max_watch_workload_open_item_count,
            ),
        ),
    )


def _normalize_facts(
    facts: Iterable[object],
) -> tuple[ResearchTeamDomainSpecialistBenchmarkFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        values = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    normalized: list[ResearchTeamDomainSpecialistBenchmarkFact] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for value in values:
        if type(value) is not ResearchTeamDomainSpecialistBenchmarkFact:
            raise ValueError(
                "facts must contain ResearchTeamDomainSpecialistBenchmarkFact items",
            )
        canonical_value = _revalidated_fact(value)
        key = (
            canonical_value.team_key,
            canonical_value.domain_key,
            canonical_value.specialist_key,
        )
        if key in seen_keys:
            raise ValueError("facts must not duplicate team/domain/specialist keys")
        seen_keys.add(key)
        normalized.append(canonical_value)
    return tuple(normalized)


def _revalidated_config(
    value: ResearchTeamDomainSpecialistBenchmarkConfig,
) -> ResearchTeamDomainSpecialistBenchmarkConfig:
    return ResearchTeamDomainSpecialistBenchmarkConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidated_fact(
    value: ResearchTeamDomainSpecialistBenchmarkFact,
) -> ResearchTeamDomainSpecialistBenchmarkFact:
    return ResearchTeamDomainSpecialistBenchmarkFact(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _facts_by_team_domain(
    facts: tuple[ResearchTeamDomainSpecialistBenchmarkFact, ...],
) -> tuple[tuple[ResearchTeamDomainSpecialistBenchmarkFact, ...], ...]:
    grouped: dict[
        tuple[str, str],
        list[ResearchTeamDomainSpecialistBenchmarkFact],
    ] = {}
    for fact in facts:
        grouped.setdefault((fact.team_key, fact.domain_key), []).append(fact)
    return tuple(
        tuple(grouped[key])
        for key in sorted(grouped, key=lambda item: (item[1], item[0]))
    )


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_FACTS_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != BENCHMARK_PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code
            for reason_code in reason_codes
            if reason_code != BENCHMARK_PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainSpecialistBenchmarkReasonCodeCount, ...]:
    if reason_codes == (NO_FACTS_REASON,):
        return (
            ResearchTeamDomainSpecialistBenchmarkReasonCodeCount(
                reason_code=NO_FACTS_REASON,
                count=ONE_COUNT,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchTeamDomainSpecialistBenchmarkReasonCodeCount(
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


def _validate_row(row: ResearchTeamDomainSpecialistBenchmarkRow) -> None:
    with localcontext(DECIMAL_CONTEXT):
        _validate_row_in_context(row)


def _validate_row_in_context(row: ResearchTeamDomainSpecialistBenchmarkRow) -> None:
    config = ResearchTeamDomainSpecialistBenchmarkConfig()
    expected_workload_capacity_score = _workload_capacity_score(
        row.workload_open_item_count,
        config,
    )
    if row.workload_capacity_score != expected_workload_capacity_score:
        raise ValueError(
            "workload_capacity_score must match workload_open_item_count "
            "and supported config",
        )
    expected_benchmark_score = _benchmark_score(
        calibration_accuracy=row.calibration_accuracy,
        memory_freshness_ratio=row.memory_freshness_ratio,
        workload_capacity_score=expected_workload_capacity_score,
        source_coverage_ratio=row.source_coverage_ratio,
        correction_followthrough_ratio=row.correction_followthrough_ratio,
    )
    if row.benchmark_score != expected_benchmark_score:
        raise ValueError(
            "benchmark_score must match source values and supported config",
        )
    expected_reason_codes = _row_reason_codes(
        forecast_sample_count=row.forecast_sample_count,
        calibration_accuracy=row.calibration_accuracy,
        memory_freshness_ratio=row.memory_freshness_ratio,
        workload_open_item_count=row.workload_open_item_count,
        source_coverage_ratio=row.source_coverage_ratio,
        correction_followthrough_ratio=row.correction_followthrough_ratio,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError(
            "reason_codes must match source values and supported config",
        )
    if row.status != _status_for_reason_codes(expected_reason_codes):
        raise ValueError("status must match source values and supported config")


def _validate_report(report: ResearchTeamDomainSpecialistBenchmarkReport) -> None:
    with localcontext(DECIMAL_CONTEXT):
        _validate_report_in_context(report)


def _validate_report_in_context(
    report: ResearchTeamDomainSpecialistBenchmarkReport,
) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.team_domain_count != _decimal_count(len(report.rows)):
        raise ValueError("team_domain_count must match rows")
    if report.specialist_count != sum((row.specialist_count for row in report.rows), ZERO):
        raise ValueError("specialist_count must match rows")
    if report.forecast_sample_count != sum(
        (row.forecast_sample_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("forecast_sample_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_calibration_accuracy != _weighted_row_average(
        report.rows,
        "calibration_accuracy",
    ):
        raise ValueError("average_calibration_accuracy must match rows")
    if report.average_memory_freshness_ratio != _weighted_row_average(
        report.rows,
        "memory_freshness_ratio",
    ):
        raise ValueError("average_memory_freshness_ratio must match rows")
    if report.total_workload_open_item_count != sum(
        (row.workload_open_item_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("total_workload_open_item_count must match rows")
    if report.average_source_coverage_ratio != _weighted_row_average(
        report.rows,
        "source_coverage_ratio",
    ):
        raise ValueError("average_source_coverage_ratio must match rows")
    if report.average_correction_followthrough_ratio != _weighted_row_average(
        report.rows,
        "correction_followthrough_ratio",
    ):
        raise ValueError("average_correction_followthrough_ratio must match rows")
    if report.average_benchmark_score != _weighted_row_average(
        report.rows,
        "benchmark_score",
    ):
        raise ValueError("average_benchmark_score must match rows")
    if report.top_benchmark_score != _max_row_decimal(report.rows, "benchmark_score"):
        raise ValueError("top_benchmark_score must match rows")
    if report.bottom_benchmark_score != _min_row_decimal(report.rows, "benchmark_score"):
        raise ValueError("bottom_benchmark_score must match rows")
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
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
) -> tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized_rows:
        if type(row) is not ResearchTeamDomainSpecialistBenchmarkRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainSpecialistBenchmarkRow",
            )
        _require_hard_flags("row", row)
        key = (row.team_key, row.domain_key)
        if key in seen_keys:
            raise ValueError("rows team/domain keys must be unique")
        seen_keys.add(key)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized_rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamDomainSpecialistBenchmarkReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainSpecialistBenchmarkReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not ResearchTeamDomainSpecialistBenchmarkReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainSpecialistBenchmarkReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized_counts != tuple(
        sorted(normalized_counts, key=lambda count: REASON_CODE_RANK[count.reason_code])
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized_counts


def _row_sort_key(row: ResearchTeamDomainSpecialistBenchmarkRow) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        row.benchmark_score.copy_negate(),
        row.domain_key,
        row.team_key,
    )


def _status_count(
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _weighted_fact_average(
    facts: tuple[ResearchTeamDomainSpecialistBenchmarkFact, ...],
    field_name: str,
) -> Decimal:
    total_weight = sum((fact.forecast_sample_count for fact in facts), ZERO)
    if total_weight == ZERO:
        return _average_decimal(tuple(getattr(fact, field_name) for fact in facts))
    weighted_total = sum(
        (
            getattr(fact, field_name) * fact.forecast_sample_count
            for fact in facts
        ),
        ZERO,
    )
    return _quantize_ratio(weighted_total / total_weight)


def _weighted_row_average(
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    total_weight = sum((row.forecast_sample_count for row in rows), ZERO)
    if total_weight == ZERO:
        return _average_decimal(tuple(getattr(row, field_name) for row in rows))
    weighted_total = sum(
        (
            getattr(row, field_name) * row.forecast_sample_count
            for row in rows
        ),
        ZERO,
    )
    return _quantize_ratio(weighted_total / total_weight)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _quantize_ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _max_row_decimal(
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchTeamDomainSpecialistBenchmarkRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return min(getattr(row, field_name) for row in rows)


def _decimal_count(value: int) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = Decimal(value).quantize(COUNT_QUANT)
    except DecimalException as exc:
        raise ValueError("count cannot be represented") from exc
    return ZERO if quantized.is_zero() else quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = value.quantize(RATIO_QUANT)
    except DecimalException as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    return ZERO_RATIO if quantized.is_zero() else quantized


def _pressure_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _clamp_probability(_quantize_ratio(value / denominator))


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO_RATIO
    if value > ONE:
        return ONE
    return _quantize_ratio(value)


def _require_pass_above_watch(
    metric_name: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold <= watch_threshold:
        raise ValueError(f"{metric_name} pass threshold must exceed watch threshold")


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
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if any(character not in SAFE_REASON_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    if value not in REASON_CODE_RANK:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(_require_reason_code(field_name, item) for item in reason_codes)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if normalized != tuple(sorted(normalized, key=lambda item: REASON_CODE_RANK[item])):
        raise ValueError(f"{field_name} must use deterministic sequence")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        return value.copy_abs()
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    quantized = _quantize_ratio(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            integral_value = value.to_integral_value()
            quantized = value.quantize(COUNT_QUANT)
    except DecimalException as exc:
        raise ValueError(f"{field_name} cannot be represented") from exc
    if value != integral_value:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return ZERO if quantized.is_zero() else quantized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        if value.utcoffset() is None:
            raise ValueError("timezone offset is unavailable")
        return value.astimezone(UTC)
    except Exception as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(
    label: str,
    value: Mapping[str, object],
) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 digest") from exc
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            _reject_key(label, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                field_value,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_key(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
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
        raise ValueError(f"{label} contains unsafe public value")


def _reject_key(label: str, key: str) -> None:
    normalized = key.lower()
    if any(fragment in normalized for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public key")


def _has_unsafe_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Mapping):
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_key("payload", key)
            payload[key] = _payload_value(item)
        return payload
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        if type(value) is str and _has_unsafe_text(value):
            raise ValueError("payload contains unsafe public value")
        return value
    if type(value) in (int, float):
        raise ValueError("payload numerics must use Decimal values")
    raise ValueError(f"payload contains unsupported value {type(value).__name__}")


def _report_values_without_digest(
    report: ResearchTeamDomainSpecialistBenchmarkReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("report values must build an object")
    payload.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(unsigned)


def _digest_from_unsigned_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()
