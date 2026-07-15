"""Report-only domain edge memory calibration reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_STATUSES",
    "ResearchStrategyDomainEdgeMemoryCalibrationConfig",
    "ResearchStrategyDomainEdgeMemoryCalibrationInput",
    "ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount",
    "ResearchStrategyDomainEdgeMemoryCalibrationReport",
    "ResearchStrategyDomainEdgeMemoryCalibrationRow",
    "build_research_strategy_domain_edge_memory_calibration_report",
    "research_strategy_domain_edge_memory_calibration_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-edge-memory-calibration-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_STATUSES = (
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
HEX_CHARS = frozenset("0123456789abcdef")

EMPTY_REPORT_REASON_CODE = "empty_domain_edge_memory_calibration_input"
ROW_PASS_REASON_CODE = "domain_edge_memory_calibration_pass"
ROW_REASON_CODES = (
    "edge_memory_calibration_score_block",
    "edge_memory_calibration_score_watch",
    ROW_PASS_REASON_CODE,
    "historical_hit_rate_block",
    "historical_hit_rate_watch",
    "calibration_alignment_score_block",
    "calibration_alignment_score_watch",
    "domain_transfer_score_block",
    "domain_transfer_score_watch",
    "recency_score_block",
    "recency_score_watch",
    "sample_support_score_block",
    "sample_support_score_watch",
    "error_rate_block",
    "error_rate_watch",
)
REPORT_REASON_CODES = (
    EMPTY_REPORT_REASON_CODE,
    *ROW_REASON_CODES,
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_edge_memory_calibration_score",
    "average_error_rate",
    "oldest_memory_age_seconds",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "rank",
    "domain_key",
    "edge_memory_digest",
    "status",
    "observed_at",
    "memory_age_seconds",
    "historical_hit_rate",
    "calibration_alignment_score",
    "domain_transfer_score",
    "recency_score",
    "sample_support_score",
    "error_rate",
    "edge_memory_calibration_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_REASON_SEQUENCE = (
    (
        "edge_memory_calibration_score_block",
        "edge_memory_calibration_score_watch",
        ROW_PASS_REASON_CODE,
    ),
    ("historical_hit_rate_block", "historical_hit_rate_watch"),
    ("calibration_alignment_score_block", "calibration_alignment_score_watch"),
    ("domain_transfer_score_block", "domain_transfer_score_watch"),
    ("recency_score_block", "recency_score_watch"),
    ("sample_support_score_block", "sample_support_score_watch"),
    ("error_rate_block", "error_rate_watch"),
)
UNSAFE_KEY_FRAGMENTS = (
    "cand" + "idate_id",
    "cand" + "idate_sl" + "ug",
    "mar" + "ket_id",
    "mar" + "ket_sl" + "ug",
    "mar" + "ket_ques" + "tion",
    "sou" + "rce_u" + "rl",
    "sou" + "rce_tex" + "t",
    "dsn",
    "tab" + "le_name",
    "tok" + "en",
    "wa" + "llet",
    "ord" + "er",
    "tra" + "de",
    "au" + "th",
)
UNSAFE_VALUE_FRAGMENTS = (
    *UNSAFE_KEY_FRAGMENTS,
    "cand" + "idate",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion:",
    "sou" + "rce",
    "://",
    "dsn=",
    "tok" + "en=",
    "buy",
    "sell",
    "li" + "ve",
    "si" + "zing",
    "rec" + "ommend",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEdgeMemoryCalibrationConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_REPORT_CONFIG_VERSION
    )
    historical_hit_rate_weight: Decimal = Decimal("0.244375")
    calibration_alignment_score_weight: Decimal = Decimal("0.212500")
    domain_transfer_score_weight: Decimal = Decimal("0.200000")
    recency_score_weight: Decimal = Decimal("0.132500")
    sample_support_score_weight: Decimal = Decimal("0.100000")
    error_reserve_weight: Decimal = Decimal("0.110625")
    pass_threshold: Decimal = Decimal("0.750000")
    watch_threshold: Decimal = Decimal("0.550000")
    min_pass_historical_hit_rate: Decimal = Decimal("0.750000")
    min_watch_historical_hit_rate: Decimal = Decimal("0.500000")
    min_pass_calibration_alignment_score: Decimal = Decimal("0.750000")
    min_watch_calibration_alignment_score: Decimal = Decimal("0.550000")
    min_pass_domain_transfer_score: Decimal = Decimal("0.700000")
    min_watch_domain_transfer_score: Decimal = Decimal("0.500000")
    min_pass_recency_score: Decimal = Decimal("0.750000")
    min_watch_recency_score: Decimal = Decimal("0.500000")
    min_pass_sample_support_score: Decimal = Decimal("0.700000")
    min_watch_sample_support_score: Decimal = Decimal("0.500000")
    max_pass_error_rate: Decimal = Decimal("0.200000")
    max_watch_error_rate: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEdgeMemoryCalibrationConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "historical_hit_rate_weight",
            "calibration_alignment_score_weight",
            "domain_transfer_score_weight",
            "recency_score_weight",
            "sample_support_score_weight",
            "error_reserve_weight",
            "pass_threshold",
            "watch_threshold",
            "min_pass_historical_hit_rate",
            "min_watch_historical_hit_rate",
            "min_pass_calibration_alignment_score",
            "min_watch_calibration_alignment_score",
            "min_pass_domain_transfer_score",
            "min_watch_domain_transfer_score",
            "min_pass_recency_score",
            "min_watch_recency_score",
            "min_pass_sample_support_score",
            "min_watch_sample_support_score",
            "max_pass_error_rate",
            "max_watch_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_descending_threshold(
            "pass_threshold",
            self.pass_threshold,
            self.watch_threshold,
        )
        _require_descending_threshold(
            "historical_hit_rate",
            self.min_pass_historical_hit_rate,
            self.min_watch_historical_hit_rate,
        )
        _require_descending_threshold(
            "calibration_alignment_score",
            self.min_pass_calibration_alignment_score,
            self.min_watch_calibration_alignment_score,
        )
        _require_descending_threshold(
            "domain_transfer_score",
            self.min_pass_domain_transfer_score,
            self.min_watch_domain_transfer_score,
        )
        _require_descending_threshold(
            "recency_score",
            self.min_pass_recency_score,
            self.min_watch_recency_score,
        )
        _require_descending_threshold(
            "sample_support_score",
            self.min_pass_sample_support_score,
            self.min_watch_sample_support_score,
        )
        _require_ascending_threshold(
            "error_rate",
            self.max_pass_error_rate,
            self.max_watch_error_rate,
        )
        _require_weight_total(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEdgeMemoryCalibrationInput(_FinalPublicDataclass):
    domain_key: str
    edge_memory_ref: str
    observed_at: datetime
    historical_hit_rate: Decimal
    calibration_alignment_score: Decimal
    domain_transfer_score: Decimal
    recency_score: Decimal
    sample_support_score: Decimal
    error_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEdgeMemoryCalibrationInput)
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_label("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "edge_memory_ref",
            _require_private_ref("edge_memory_ref", self.edge_memory_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "historical_hit_rate",
            "calibration_alignment_score",
            "domain_transfer_score",
            "recency_score",
            "sample_support_score",
            "error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEdgeMemoryCalibrationRow(_FinalPublicDataclass):
    rank: Decimal
    domain_key: str
    edge_memory_digest: str
    status: str
    observed_at: datetime
    memory_age_seconds: Decimal
    historical_hit_rate: Decimal
    calibration_alignment_score: Decimal
    domain_transfer_score: Decimal
    recency_score: Decimal
    sample_support_score: Decimal
    error_rate: Decimal
    edge_memory_calibration_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEdgeMemoryCalibrationRow)
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_label("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "edge_memory_digest",
            _normalize_sha256("edge_memory_digest", self.edge_memory_digest),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_STATUSES,
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
            "historical_hit_rate",
            "calibration_alignment_score",
            "domain_transfer_score",
            "recency_score",
            "sample_support_score",
            "error_rate",
            "edge_memory_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount)
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        if self.count <= ZERO_COUNT:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEdgeMemoryCalibrationReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_edge_memory_calibration_score: Decimal
    average_error_rate: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEdgeMemoryCalibrationReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_edge_memory_calibration_score",
            "average_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_memory_age_seconds",
            _normalize_nonnegative_measure(
                "oldest_memory_age_seconds",
                self.oldest_memory_age_seconds,
            ),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
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
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_domain_edge_memory_calibration_report_payload(self)


def build_research_strategy_domain_edge_memory_calibration_report(
    items: Sequence[ResearchStrategyDomainEdgeMemoryCalibrationInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainEdgeMemoryCalibrationConfig | None = None,
) -> ResearchStrategyDomainEdgeMemoryCalibrationReport:
    cfg = config or ResearchStrategyDomainEdgeMemoryCalibrationConfig()
    if type(cfg) is not ResearchStrategyDomainEdgeMemoryCalibrationConfig:
        raise ValueError("config must be a ResearchStrategyDomainEdgeMemoryCalibrationConfig")
    cfg = _revalidate_config(cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(items, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(item, generated_at=generated_at_utc, config=cfg) for item in inputs),
    )
    return ResearchStrategyDomainEdgeMemoryCalibrationReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        item_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_edge_memory_calibration_score=_average_field(
            rows,
            "edge_memory_calibration_score",
        ),
        average_error_rate=_average_field(rows, "error_rate"),
        oldest_memory_age_seconds=_max_measure_field(rows, "memory_age_seconds"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_domain_edge_memory_calibration_report_payload(
    report: ResearchStrategyDomainEdgeMemoryCalibrationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyDomainEdgeMemoryCalibrationReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainEdgeMemoryCalibrationReport",
        )
    _require_hard_flags("report", report)
    _validate_report_derived_validation_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_schema(payload)
    return payload


@dataclass(frozen=True, slots=True)
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


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    rows = tuple(
        _payload_row(row_payload)
        for row_payload in _payload_object_list("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _payload_reason_code_count(item)
        for item in _payload_object_list(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    report = ResearchStrategyDomainEdgeMemoryCalibrationReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        item_count=_payload_decimal("item_count", payload["item_count"], COUNT_QUANTUM),
        pass_count=_payload_decimal("pass_count", payload["pass_count"], COUNT_QUANTUM),
        watch_count=_payload_decimal(
            "watch_count",
            payload["watch_count"],
            COUNT_QUANTUM,
        ),
        block_count=_payload_decimal(
            "block_count",
            payload["block_count"],
            COUNT_QUANTUM,
        ),
        average_edge_memory_calibration_score=_payload_decimal(
            "average_edge_memory_calibration_score",
            payload["average_edge_memory_calibration_score"],
            RATIO_QUANTUM,
        ),
        average_error_rate=_payload_decimal(
            "average_error_rate",
            payload["average_error_rate"],
            RATIO_QUANTUM,
        ),
        oldest_memory_age_seconds=_payload_decimal(
            "oldest_memory_age_seconds",
            payload["oldest_memory_age_seconds"],
            RATIO_QUANTUM,
        ),
        status=_payload_status(payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("report payload must use canonical report payload schema")


def _payload_row(payload: dict[str, Any]) -> ResearchStrategyDomainEdgeMemoryCalibrationRow:
    _require_payload_keys("row payload", payload, ROW_PAYLOAD_KEYS)
    return ResearchStrategyDomainEdgeMemoryCalibrationRow(
        rank=_payload_decimal("rank", payload["rank"], COUNT_QUANTUM),
        domain_key=_payload_string("domain_key", payload["domain_key"]),
        edge_memory_digest=_payload_digest(
            "edge_memory_digest",
            payload["edge_memory_digest"],
        ),
        status=_payload_status(payload["status"]),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        memory_age_seconds=_payload_decimal(
            "memory_age_seconds",
            payload["memory_age_seconds"],
            RATIO_QUANTUM,
        ),
        historical_hit_rate=_payload_decimal(
            "historical_hit_rate",
            payload["historical_hit_rate"],
            RATIO_QUANTUM,
        ),
        calibration_alignment_score=_payload_decimal(
            "calibration_alignment_score",
            payload["calibration_alignment_score"],
            RATIO_QUANTUM,
        ),
        domain_transfer_score=_payload_decimal(
            "domain_transfer_score",
            payload["domain_transfer_score"],
            RATIO_QUANTUM,
        ),
        recency_score=_payload_decimal(
            "recency_score",
            payload["recency_score"],
            RATIO_QUANTUM,
        ),
        sample_support_score=_payload_decimal(
            "sample_support_score",
            payload["sample_support_score"],
            RATIO_QUANTUM,
        ),
        error_rate=_payload_decimal(
            "error_rate",
            payload["error_rate"],
            RATIO_QUANTUM,
        ),
        edge_memory_calibration_score=_payload_decimal(
            "edge_memory_calibration_score",
            payload["edge_memory_calibration_score"],
            RATIO_QUANTUM,
        ),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _payload_reason_code_count(
    payload: dict[str, Any],
) -> ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount:
    _require_payload_keys(
        "reason code count payload",
        payload,
        REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    return ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"], COUNT_QUANTUM),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )


def _require_payload_keys(
    label: str,
    payload: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(payload) is not dict or set(payload) != set(expected_keys):
        raise ValueError(f"{label} must use canonical report payload schema")


def _payload_object_list(field_name: str, value: object) -> tuple[dict[str, Any], ...]:
    if type(value) is not list or any(type(item) is not dict for item in value):
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return tuple(value)


def _payload_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: Sequence[str],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return _normalize_reason_codes(field_name, tuple(value), allowed_reason_codes)


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return value


def _payload_status(value: object) -> str:
    return _require_member(
        "status",
        _payload_string("status", value),
        RESEARCH_STRATEGY_DOMAIN_EDGE_MEMORY_CALIBRATION_STATUSES,
    )


def _payload_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        normalized = _as_utc(field_name, datetime.fromisoformat(value))
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return normalized


def _payload_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical report payload schema")
    try:
        parsed = Decimal(value)
        normalized = _normalize_decimal(field_name, parsed, quantum=quantum)
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc
    if value != str(normalized):
        raise ValueError(f"{field_name} must use canonical report payload schema")
    return normalized


def _payload_digest(field_name: str, value: object) -> str:
    try:
        return _normalize_sha256(field_name, value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must use canonical report payload schema",
        ) from exc


def _build_row(
    item: ResearchStrategyDomainEdgeMemoryCalibrationInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainEdgeMemoryCalibrationConfig,
) -> ResearchStrategyDomainEdgeMemoryCalibrationRow:
    memory_age_seconds = _age_seconds(item.observed_at, generated_at)
    edge_memory_calibration_score = _edge_memory_calibration_score(item, config=config)
    reason_codes = _row_reason_codes(
        historical_hit_rate=item.historical_hit_rate,
        calibration_alignment_score=item.calibration_alignment_score,
        domain_transfer_score=item.domain_transfer_score,
        recency_score=item.recency_score,
        sample_support_score=item.sample_support_score,
        error_rate=item.error_rate,
        edge_memory_calibration_score=edge_memory_calibration_score,
        config=config,
    )
    return ResearchStrategyDomainEdgeMemoryCalibrationRow(
        rank=COUNT_QUANTUM,
        domain_key=item.domain_key,
        edge_memory_digest=_edge_memory_digest(item.edge_memory_ref),
        status=_status_from_reason_codes(reason_codes),
        observed_at=item.observed_at,
        memory_age_seconds=memory_age_seconds,
        historical_hit_rate=item.historical_hit_rate,
        calibration_alignment_score=item.calibration_alignment_score,
        domain_transfer_score=item.domain_transfer_score,
        recency_score=item.recency_score,
        sample_support_score=item.sample_support_score,
        error_rate=item.error_rate,
        edge_memory_calibration_score=edge_memory_calibration_score,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
) -> tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...]:
    return tuple(
        ResearchStrategyDomainEdgeMemoryCalibrationRow(
            rank=_count(index),
            domain_key=row.domain_key,
            edge_memory_digest=row.edge_memory_digest,
            status=row.status,
            observed_at=row.observed_at,
            memory_age_seconds=row.memory_age_seconds,
            historical_hit_rate=row.historical_hit_rate,
            calibration_alignment_score=row.calibration_alignment_score,
            domain_transfer_score=row.domain_transfer_score,
            recency_score=row.recency_score,
            sample_support_score=row.sample_support_score,
            error_rate=row.error_rate,
            edge_memory_calibration_score=row.edge_memory_calibration_score,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    historical_hit_rate: Decimal,
    calibration_alignment_score: Decimal,
    domain_transfer_score: Decimal,
    recency_score: Decimal,
    sample_support_score: Decimal,
    error_rate: Decimal,
    edge_memory_calibration_score: Decimal,
    config: ResearchStrategyDomainEdgeMemoryCalibrationConfig,
) -> tuple[str, ...]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    if edge_memory_calibration_score < config.watch_threshold:
        block_codes.append("edge_memory_calibration_score_block")
    elif edge_memory_calibration_score < config.pass_threshold:
        watch_codes.append("edge_memory_calibration_score_watch")
    if historical_hit_rate < config.min_watch_historical_hit_rate:
        block_codes.append("historical_hit_rate_block")
    elif historical_hit_rate < config.min_pass_historical_hit_rate:
        watch_codes.append("historical_hit_rate_watch")
    if calibration_alignment_score < config.min_watch_calibration_alignment_score:
        block_codes.append("calibration_alignment_score_block")
    elif calibration_alignment_score < config.min_pass_calibration_alignment_score:
        watch_codes.append("calibration_alignment_score_watch")
    if domain_transfer_score < config.min_watch_domain_transfer_score:
        block_codes.append("domain_transfer_score_block")
    elif domain_transfer_score < config.min_pass_domain_transfer_score:
        watch_codes.append("domain_transfer_score_watch")
    if recency_score < config.min_watch_recency_score:
        block_codes.append("recency_score_block")
    elif recency_score < config.min_pass_recency_score:
        watch_codes.append("recency_score_watch")
    if sample_support_score < config.min_watch_sample_support_score:
        block_codes.append("sample_support_score_block")
    elif sample_support_score < config.min_pass_sample_support_score:
        watch_codes.append("sample_support_score_watch")
    if error_rate >= config.max_watch_error_rate:
        block_codes.append("error_rate_block")
    elif error_rate >= config.max_pass_error_rate:
        watch_codes.append("error_rate_watch")
    if block_codes:
        return _normalize_reason_codes("reason_codes", tuple(block_codes), ROW_REASON_CODES)
    if watch_codes:
        return _normalize_reason_codes("reason_codes", tuple(watch_codes), ROW_REASON_CODES)
    return (ROW_PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _status_rollup(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    present: list[str] = []
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            present.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(present), REPORT_REASON_CODES)


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
) -> tuple[ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if counter[reason_code] > 0
    )


def _edge_memory_calibration_score(
    item: ResearchStrategyDomainEdgeMemoryCalibrationInput,
    *,
    config: ResearchStrategyDomainEdgeMemoryCalibrationConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.historical_hit_rate * config.historical_hit_rate_weight
            + item.calibration_alignment_score
            * config.calibration_alignment_score_weight
            + item.domain_transfer_score * config.domain_transfer_score_weight
            + item.recency_score * config.recency_score_weight
            + item.sample_support_score * config.sample_support_score_weight
            + (ONE_RATIO - item.error_rate) * config.error_reserve_weight
        )
    return _normalize_probability(
        "edge_memory_calibration_score",
        score,
    )


def _validate_report(report: ResearchStrategyDomainEdgeMemoryCalibrationReport) -> None:
    rows = report.rows
    if report.item_count != _count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.average_edge_memory_calibration_score != _average_field(
        rows,
        "edge_memory_calibration_score",
    ):
        raise ValueError("average_edge_memory_calibration_score must match rows")
    if report.average_error_rate != _average_field(rows, "error_rate"):
        raise ValueError("average_error_rate must match rows")
    if report.oldest_memory_age_seconds != _max_measure_field(
        rows,
        "memory_age_seconds",
    ):
        raise ValueError("oldest_memory_age_seconds must match rows")
    if report.status != _status_rollup(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.rank != _count(index):
            raise ValueError("row ranks must match deterministic sequence")


def _revalidate_config(
    config: ResearchStrategyDomainEdgeMemoryCalibrationConfig,
) -> ResearchStrategyDomainEdgeMemoryCalibrationConfig:
    return ResearchStrategyDomainEdgeMemoryCalibrationConfig(
        **{
            field.name: getattr(config, field.name)
            for field in fields(ResearchStrategyDomainEdgeMemoryCalibrationConfig)
        },
    )


def _revalidate_input(
    item: ResearchStrategyDomainEdgeMemoryCalibrationInput,
) -> ResearchStrategyDomainEdgeMemoryCalibrationInput:
    return ResearchStrategyDomainEdgeMemoryCalibrationInput(
        **{
            field.name: getattr(item, field.name)
            for field in fields(ResearchStrategyDomainEdgeMemoryCalibrationInput)
        },
    )


def _normalize_inputs(
    items: Sequence[ResearchStrategyDomainEdgeMemoryCalibrationInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyDomainEdgeMemoryCalibrationInput, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence")
    normalized: list[ResearchStrategyDomainEdgeMemoryCalibrationInput] = []
    for item in items:
        if type(item) is not ResearchStrategyDomainEdgeMemoryCalibrationInput:
            raise ValueError(
                "items must contain ResearchStrategyDomainEdgeMemoryCalibrationInput",
            )
        item = _revalidate_input(item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.domain_key,
                item.observed_at,
                _edge_memory_digest(item.edge_memory_ref),
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyDomainEdgeMemoryCalibrationRow],
) -> tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyDomainEdgeMemoryCalibrationRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyDomainEdgeMemoryCalibrationRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainEdgeMemoryCalibrationRow",
            )
        normalized.append(row)
    normalized_tuple = tuple(normalized)
    if normalized_tuple != tuple(sorted(normalized_tuple, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized_tuple


def _normalize_reason_code_counts(
    reason_code_counts: Sequence[
        ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount,
    ],
) -> tuple[ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)) or not isinstance(
        reason_code_counts,
        Sequence,
    ):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount] = []
    for item in reason_code_counts:
        if type(item) is not ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainEdgeMemoryCalibrationReasonCodeCount",
            )
        normalized.append(item)
    normalized_tuple = tuple(normalized)
    if normalized_tuple != tuple(
        sorted(normalized_tuple, key=lambda item: ROW_REASON_CODES.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized_tuple


def _row_sort_key(row: ResearchStrategyDomainEdgeMemoryCalibrationRow) -> tuple[object, ...]:
    return (
        STATUS_WEIGHT[row.status],
        row.edge_memory_calibration_score,
        row.domain_key,
        row.edge_memory_digest,
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        average = sum((getattr(row, field_name) for row in rows), ZERO_RATIO) / _count(
            len(rows),
        )
    return _quantize_ratio(average)


def _max_measure_field(
    rows: tuple[ResearchStrategyDomainEdgeMemoryCalibrationRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO_RATIO)


def _age_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _normalize_nonnegative_measure("memory_age_seconds", seconds)


def _edge_memory_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_safe_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    text = value
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains restricted references")
    _reject_unsafe_public_string(field_name, text)
    return text


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _require_member(field_name: str, value: object, allowed_values: Sequence[str]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_descending_threshold(
    label: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{label} pass threshold must be at least watch threshold")


def _require_ascending_threshold(
    label: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{label} pass threshold must not exceed watch threshold")


def _require_weight_total(
    config: ResearchStrategyDomainEdgeMemoryCalibrationConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            config.historical_hit_rate_weight
            + config.calibration_alignment_score_weight
            + config.domain_transfer_score_weight
            + config.recency_score_weight
            + config.sample_support_score_weight
            + config.error_reserve_weight
        )
    total = _quantize_ratio(total)
    if total != ONE_RATIO:
        raise ValueError("edge memory calibration weights must sum to one")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
    allowed_reason_codes: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    raw = tuple(reason_codes)
    seen: list[str] = []
    for reason_code in raw:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.append(reason_code)
    expected = tuple(reason_code for reason_code in allowed_reason_codes if reason_code in seen)
    if raw != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return raw


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, quantum=RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, quantum=COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_measure(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, quantum=RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object, *, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized == ZERO_COUNT:
        return ZERO_COUNT.quantize(quantum)
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(RATIO_QUANTUM)
    if normalized == ZERO_COUNT:
        return ZERO_RATIO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchStrategyDomainEdgeMemoryCalibrationReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _validate_report_derived_validation_digest(
    report: ResearchStrategyDomainEdgeMemoryCalibrationReport,
) -> None:
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, label)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, label)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{label} contains unsupported public value")


def _reject_unsafe_public_key(key: str, label: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
