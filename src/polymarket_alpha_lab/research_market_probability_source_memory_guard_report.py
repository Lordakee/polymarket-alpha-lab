from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_SOURCE_MEMORY_GUARD_CONFIG_VERSION",
    "PROBABILITY_SOURCE_MEMORY_GUARD_STATUSES",
    "ResearchMarketProbabilitySourceMemoryGuardConfig",
    "ResearchMarketProbabilitySourceMemoryGuardInputRow",
    "ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount",
    "ResearchMarketProbabilitySourceMemoryGuardReport",
    "ResearchMarketProbabilitySourceMemoryGuardReportRow",
    "build_research_market_probability_source_memory_guard_report",
    "research_market_probability_source_memory_guard_public_payload",
    "validate_research_market_probability_source_memory_guard_payload_digest",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_SOURCE_MEMORY_GUARD_CONFIG_VERSION = (
    "probability-memory-guard-v0"
)
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PROBABILITY_SOURCE_MEMORY_GUARD_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
NO_INPUTS_REASON = "no_probability_memory_inputs"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_REASON_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_PUBLIC_STRING_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
_PRIVATE_TERMS = (
    "candidate",
    "market",
    "source_" + "ur" + "l",
    "ur" + "l",
    "te" + "xt",
    "ds" + "n",
    "ta" + "ble",
    "to" + "ken",
)


@dataclass(frozen=True)
class ResearchMarketProbabilitySourceMemoryGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_SOURCE_MEMORY_GUARD_CONFIG_VERSION
    )
    min_pass_evidence_count: Decimal = Decimal("3.000000")
    min_watch_evidence_count: Decimal = Decimal("2.000000")
    min_pass_probability_confidence: Decimal = Decimal("0.700000")
    min_watch_probability_confidence: Decimal = Decimal("0.450000")
    min_pass_memory_quality_score: Decimal = Decimal("0.800000")
    min_watch_memory_quality_score: Decimal = Decimal("0.550000")
    max_pass_stale_evidence_ratio: Decimal = Decimal("0.100000")
    max_watch_stale_evidence_ratio: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySourceMemoryGuardConfig:
            raise TypeError(
                "ResearchMarketProbabilitySourceMemoryGuardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilitySourceMemoryGuardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketProbabilitySourceMemoryGuardConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_SOURCE_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_evidence_count",
            "min_watch_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "min_pass_probability_confidence",
            "min_watch_probability_confidence",
            "min_pass_memory_quality_score",
            "min_watch_memory_quality_score",
            "max_pass_stale_evidence_ratio",
            "max_watch_stale_evidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_min_thresholds(
            "evidence_count",
            self.min_pass_evidence_count,
            self.min_watch_evidence_count,
        )
        _require_min_thresholds(
            "probability_confidence",
            self.min_pass_probability_confidence,
            self.min_watch_probability_confidence,
        )
        _require_min_thresholds(
            "memory_quality_score",
            self.min_pass_memory_quality_score,
            self.min_watch_memory_quality_score,
        )
        if self.max_pass_stale_evidence_ratio > self.max_watch_stale_evidence_ratio:
            raise ValueError("stale_evidence_ratio watch threshold must cover pass")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySourceMemoryGuardInputRow:
    item_digest: str
    observed_at: datetime
    evidence_count: Decimal
    stale_evidence_count: Decimal
    probability_confidence: Decimal
    memory_quality_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySourceMemoryGuardInputRow:
            raise TypeError(
                "ResearchMarketProbabilitySourceMemoryGuardInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilitySourceMemoryGuardInputRow:
            raise ValueError(
                "input row must be exactly "
                "ResearchMarketProbabilitySourceMemoryGuardInputRow",
            )
        _require_digest("item_digest", self.item_digest)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_whole_decimal(
                "evidence_count",
                self.evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "stale_evidence_count",
            _require_nonnegative_whole_decimal(
                "stale_evidence_count",
                self.stale_evidence_count,
            ),
        )
        if self.stale_evidence_count > self.evidence_count:
            raise ValueError("stale_evidence_count must not exceed evidence_count")
        object.__setattr__(
            self,
            "probability_confidence",
            _require_ratio_decimal(
                "probability_confidence",
                self.probability_confidence,
            ),
        )
        object.__setattr__(
            self,
            "memory_quality_score",
            _require_ratio_decimal(
                "memory_quality_score",
                self.memory_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySourceMemoryGuardReportRow:
    item_digest: str
    observed_at: datetime
    evidence_count: Decimal
    stale_evidence_count: Decimal
    stale_evidence_ratio: Decimal
    probability_confidence: Decimal
    memory_quality_score: Decimal
    memory_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySourceMemoryGuardReportRow:
            raise TypeError(
                "ResearchMarketProbabilitySourceMemoryGuardReportRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilitySourceMemoryGuardReportRow:
            raise ValueError(
                "row must be exactly ResearchMarketProbabilitySourceMemoryGuardReportRow",
            )
        _require_digest("item_digest", self.item_digest)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in ("evidence_count", "stale_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.stale_evidence_count > self.evidence_count:
            raise ValueError("stale_evidence_count must not exceed evidence_count")
        for field_name in (
            "stale_evidence_ratio",
            "probability_confidence",
            "memory_quality_score",
            "memory_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount:
            raise TypeError(
                "ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilitySourceMemoryGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_readiness_score: Decimal | None
    min_probability_confidence: Decimal
    min_memory_quality_score: Decimal
    max_stale_evidence_ratio: Decimal
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardReportRow, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketProbabilitySourceMemoryGuardReport:
            raise TypeError(
                "ResearchMarketProbabilitySourceMemoryGuardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilitySourceMemoryGuardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketProbabilitySourceMemoryGuardReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.average_memory_readiness_score is not None:
            object.__setattr__(
                self,
                "average_memory_readiness_score",
                _require_ratio_decimal(
                    "average_memory_readiness_score",
                    self.average_memory_readiness_score,
                ),
            )
        for field_name in (
            "min_probability_confidence",
            "min_memory_quality_score",
            "max_stale_evidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_rows("rows", self.rows)
        _require_reason_count_rows("reason_code_counts", self.reason_code_counts)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != tuple(
            item.reason_code for item in self.reason_code_counts
        ):
            raise ValueError("reason_codes must match reason_code_counts")
        if self.input_count != _count_decimal(self.rows):
            raise ValueError("input_count must match rows")
        if self.pass_count != _sum_if(self.rows, lambda row: row.status == STATUS_PASS):
            raise ValueError("pass_count must match rows")
        if self.watch_count != _sum_if(self.rows, lambda row: row.status == STATUS_WATCH):
            raise ValueError("watch_count must match rows")
        if self.block_count != _sum_if(self.rows, lambda row: row.status == STATUS_BLOCK):
            raise ValueError("block_count must match rows")
        if self.status != _report_status(self.rows, self.reason_codes):
            raise ValueError("status must match rows and reason_codes")
        if self.rows:
            if self.average_memory_readiness_score != _average_decimal(
                tuple(row.memory_readiness_score for row in self.rows),
            ):
                raise ValueError("average_memory_readiness_score must match rows")
            if self.min_probability_confidence != min(
                row.probability_confidence for row in self.rows
            ):
                raise ValueError("min_probability_confidence must match rows")
            if self.min_memory_quality_score != min(
                row.memory_quality_score for row in self.rows
            ):
                raise ValueError("min_memory_quality_score must match rows")
            if self.max_stale_evidence_ratio != max(
                row.stale_evidence_ratio for row in self.rows
            ):
                raise ValueError("max_stale_evidence_ratio must match rows")
        elif self.average_memory_readiness_score is not None:
            raise ValueError("average_memory_readiness_score must be empty without rows")
        if self.validation_digest != _payload_digest(
            _report_public_values(self, include_digest=False),
        ):
            raise ValueError("validation_digest does not match public payload")
        _require_hard_flags("report", self)


def build_research_market_probability_source_memory_guard_report(
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardInputRow, ...],
    *,
    config: ResearchMarketProbabilitySourceMemoryGuardConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketProbabilitySourceMemoryGuardReport:
    cfg = config or ResearchMarketProbabilitySourceMemoryGuardConfig()
    if type(cfg) is not ResearchMarketProbabilitySourceMemoryGuardConfig:
        raise TypeError(
            "config must be exactly ResearchMarketProbabilitySourceMemoryGuardConfig",
        )
    generated = _as_utc("generated_at", generated_at)
    input_rows = _require_input_rows("rows", rows)
    for row in input_rows:
        if row.observed_at > generated:
            raise ValueError("observed_at must not be after generated_at")

    report_rows = tuple(_build_report_row(row, config=cfg) for row in input_rows)
    rows_for_report = tuple(
        sorted(
            report_rows,
            key=lambda row: (_status_rank(row.status), row.item_digest),
        ),
    )
    if not rows_for_report:
        reason_counts = (
            ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
        public_values = {
            "generated_at": generated,
            "config_version": cfg.config_version,
            "status": STATUS_BLOCK,
            "input_count": ZERO,
            "pass_count": ZERO,
            "watch_count": ZERO,
            "block_count": ZERO,
            "average_memory_readiness_score": None,
            "min_probability_confidence": ZERO,
            "min_memory_quality_score": ZERO,
            "max_stale_evidence_ratio": ZERO,
            "rows": (),
            "reason_code_counts": reason_counts,
            "reason_codes": reason_codes,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        return ResearchMarketProbabilitySourceMemoryGuardReport(
            **public_values,
            validation_digest=_payload_digest(public_values),
        )

    reason_counts = _reason_code_counts(rows_for_report)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    public_values = {
        "generated_at": generated,
        "config_version": cfg.config_version,
        "status": _report_status(rows_for_report, reason_codes),
        "input_count": _count_decimal(rows_for_report),
        "pass_count": _sum_if(rows_for_report, lambda row: row.status == STATUS_PASS),
        "watch_count": _sum_if(rows_for_report, lambda row: row.status == STATUS_WATCH),
        "block_count": _sum_if(rows_for_report, lambda row: row.status == STATUS_BLOCK),
        "average_memory_readiness_score": _average_decimal(
            tuple(row.memory_readiness_score for row in rows_for_report),
        ),
        "min_probability_confidence": min(
            row.probability_confidence for row in rows_for_report
        ),
        "min_memory_quality_score": min(
            row.memory_quality_score for row in rows_for_report
        ),
        "max_stale_evidence_ratio": max(
            row.stale_evidence_ratio for row in rows_for_report
        ),
        "rows": rows_for_report,
        "reason_code_counts": reason_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketProbabilitySourceMemoryGuardReport(
        **public_values,
        validation_digest=_payload_digest(public_values),
    )


def research_market_probability_source_memory_guard_public_payload(
    report: ResearchMarketProbabilitySourceMemoryGuardReport,
) -> dict[str, object]:
    if type(report) is not ResearchMarketProbabilitySourceMemoryGuardReport:
        raise TypeError(
            "report must be exactly ResearchMarketProbabilitySourceMemoryGuardReport",
        )
    payload = _json_ready(_report_public_values(report, include_digest=True))
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    if not validate_research_market_probability_source_memory_guard_payload_digest(
        payload,
    ):
        raise ValueError("public payload validation_digest is invalid")
    return payload


def validate_research_market_probability_source_memory_guard_payload_digest(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    validation_digest = payload.get("validation_digest")
    if type(validation_digest) is not str or not _HEX_SHA256_RE.fullmatch(
        validation_digest,
    ):
        return False
    payload_without_digest = dict(payload)
    payload_without_digest.pop("validation_digest", None)
    try:
        _reject_unsafe_public_payload(
            "public payload",
            payload_without_digest,
            allow_json_containers=True,
        )
        expected_digest = _payload_digest(payload_without_digest)
    except (TypeError, ValueError):
        return False
    return validation_digest == expected_digest


def _build_report_row(
    row: ResearchMarketProbabilitySourceMemoryGuardInputRow,
    *,
    config: ResearchMarketProbabilitySourceMemoryGuardConfig,
) -> ResearchMarketProbabilitySourceMemoryGuardReportRow:
    stale_ratio = _stale_evidence_ratio(row.evidence_count, row.stale_evidence_count)
    readiness_score = _memory_readiness_score(
        evidence_count=row.evidence_count,
        stale_evidence_ratio=stale_ratio,
        probability_confidence=row.probability_confidence,
        memory_quality_score=row.memory_quality_score,
        config=config,
    )
    reason_codes = list(_input_reason_codes(row.reason_codes))
    if row.evidence_count < config.min_watch_evidence_count:
        reason_codes.append("evidence_count_block")
    elif row.evidence_count < config.min_pass_evidence_count:
        reason_codes.append("evidence_count_watch")
    if row.probability_confidence < config.min_watch_probability_confidence:
        reason_codes.append("probability_confidence_block")
    elif row.probability_confidence < config.min_pass_probability_confidence:
        reason_codes.append("probability_confidence_watch")
    if row.memory_quality_score < config.min_watch_memory_quality_score:
        reason_codes.append("memory_quality_block")
    elif row.memory_quality_score < config.min_pass_memory_quality_score:
        reason_codes.append("memory_quality_watch")
    if stale_ratio > config.max_watch_stale_evidence_ratio:
        reason_codes.append("stale_evidence_ratio_block")
    elif stale_ratio > config.max_pass_stale_evidence_ratio:
        reason_codes.append("stale_evidence_ratio_watch")

    status = _status_from_reason_codes(tuple(reason_codes))
    reason_codes.append(f"probability_memory_guard_{status}")
    return ResearchMarketProbabilitySourceMemoryGuardReportRow(
        item_digest=row.item_digest,
        observed_at=row.observed_at,
        evidence_count=row.evidence_count,
        stale_evidence_count=row.stale_evidence_count,
        stale_evidence_ratio=stale_ratio,
        probability_confidence=row.probability_confidence,
        memory_quality_score=row.memory_quality_score,
        memory_readiness_score=readiness_score,
        status=status,
        reason_codes=_normalize_reason_codes("reason_codes", tuple(reason_codes)),
    )


def _report_public_values(
    report: ResearchMarketProbabilitySourceMemoryGuardReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    values: dict[str, object] = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "input_count": report.input_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_memory_readiness_score": report.average_memory_readiness_score,
        "min_probability_confidence": report.min_probability_confidence,
        "min_memory_quality_score": report.min_memory_quality_score,
        "max_stale_evidence_ratio": report.max_stale_evidence_ratio,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        values["validation_digest"] = report.validation_digest
    return values


def _payload_digest(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
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
        return str(_quantize(value))
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _PRIVATE_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or any(term in lowered for term in _PRIVATE_TERMS):
        raise ValueError(f"{path} has unsafe public value")


def _require_input_rows(
    name: str,
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardInputRow, ...],
) -> tuple[ResearchMarketProbabilitySourceMemoryGuardInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilitySourceMemoryGuardInputRow:
            raise ValueError(
                f"{name} entries must be "
                "ResearchMarketProbabilitySourceMemoryGuardInputRow",
            )
    return rows


def _require_report_rows(
    name: str,
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardReportRow, ...],
) -> None:
    if type(rows) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilitySourceMemoryGuardReportRow:
            raise ValueError(
                f"{name} entries must be "
                "ResearchMarketProbabilitySourceMemoryGuardReportRow",
            )


def _require_reason_count_rows(
    name: str,
    rows: tuple[
        ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount,
        ...,
    ],
) -> None:
    if type(rows) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount:
            raise ValueError(
                f"{name} entries must be "
                "ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount",
            )


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardReportRow, ...],
) -> tuple[ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count_decimal(rows)
    return tuple(
        ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount(
            reason_code=reason_code,
            count=_quantize(Decimal(counter[reason_code])),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in sorted(counter)
    )


def _normalize_reason_codes(name: str, reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(sorted(set(reason_codes)))
    for reason_code in normalized:
        _require_reason_code(name, reason_code)
    return normalized


def _input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"input_{reason_code}" for reason_code in reason_codes)


def _require_reason_code(name: str, reason_code: str) -> None:
    if type(reason_code) is not str or not _PUBLIC_REASON_RE.fullmatch(reason_code):
        raise ValueError(f"{name} must contain public snake_case reason codes")
    _reject_unsafe_public_string(name, reason_code)


def _require_digest(name: str, value: str) -> None:
    if type(value) is not str or not _HEX_SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")


def _require_public_string(name: str, value: str) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or not _PUBLIC_STRING_RE.fullmatch(value)
    ):
        raise ValueError(f"{name} must be a canonical public string")
    _reject_unsafe_public_string(name, value)


def _require_status(name: str, value: str) -> None:
    if type(value) is not str or value not in PROBABILITY_SOURCE_MEMORY_GUARD_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    try:
        normalized = _quantize(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be a finite Decimal") from exc
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_min_thresholds(
    name: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"min_watch_{name} must not exceed min_pass_{name}")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("Decimal must be finite")
    return value.quantize(QUANTUM)


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return _quantize(Decimal(len(values)))


def _sum_if(
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardReportRow, ...],
    predicate: object,
) -> Decimal:
    count = ZERO
    for row in rows:
        if predicate(row):
            count += ONE
    return _quantize(count)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    total = ZERO
    for value in values:
        total += value
    return _quantize(total / Decimal(len(values)))


def _status_rank(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ZERO
    if status == STATUS_WATCH:
        return ONE
    return Decimal("2.000000")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardReportRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if reason_codes == (NO_INPUTS_REASON,):
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _stale_evidence_ratio(evidence_count: Decimal, stale_evidence_count: Decimal) -> Decimal:
    if evidence_count == ZERO:
        return ONE
    return _quantize(stale_evidence_count / evidence_count)


def _memory_readiness_score(
    *,
    evidence_count: Decimal,
    stale_evidence_ratio: Decimal,
    probability_confidence: Decimal,
    memory_quality_score: Decimal,
    config: ResearchMarketProbabilitySourceMemoryGuardConfig,
) -> Decimal:
    evidence_score = min(ONE, _quantize(evidence_count / config.min_pass_evidence_count))
    fresh_evidence_score = ONE - stale_evidence_ratio
    return _quantize(
        (
            evidence_score
            + fresh_evidence_score
            + probability_confidence
            + memory_quality_score
        )
        / Decimal("4.000000"),
    )


def _validate_row_consistency(
    row: ResearchMarketProbabilitySourceMemoryGuardReportRow,
) -> None:
    if row.stale_evidence_ratio != _stale_evidence_ratio(
        row.evidence_count,
        row.stale_evidence_count,
    ):
        raise ValueError("stale_evidence_ratio must match evidence counts")
    pass_config = ResearchMarketProbabilitySourceMemoryGuardConfig()
    if row.memory_readiness_score != _memory_readiness_score(
        evidence_count=row.evidence_count,
        stale_evidence_ratio=row.stale_evidence_ratio,
        probability_confidence=row.probability_confidence,
        memory_quality_score=row.memory_quality_score,
        config=pass_config,
    ):
        raise ValueError("memory_readiness_score must match row inputs")
