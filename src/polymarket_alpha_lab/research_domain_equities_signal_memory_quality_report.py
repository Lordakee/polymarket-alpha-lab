"""Pure report-only quality check for equity-index signal memory inputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Callable


DEFAULT_RESEARCH_DOMAIN_EQUITIES_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION = (
    "research-domain-equities-signal-memory-quality-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

NO_INPUTS_REASON = "research_domain_equities_signal_memory_quality_no_inputs"
PASS_REASON = "research_domain_equities_signal_memory_quality_pass"
WATCH_CONFLICTING_REASON = (
    "research_domain_equities_signal_memory_quality_watch_conflicting"
)
WATCH_MISSING_REASON = "research_domain_equities_signal_memory_quality_watch_missing"
WATCH_STALE_REASON = "research_domain_equities_signal_memory_quality_watch_stale"
BLOCK_CONFLICTING_REASON = (
    "research_domain_equities_signal_memory_quality_block_conflicting"
)
BLOCK_MISSING_REASON = "research_domain_equities_signal_memory_quality_block_missing"
BLOCK_STALE_REASON = "research_domain_equities_signal_memory_quality_block_stale"

REASON_CODES = (
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_CONFLICTING_REASON,
    WATCH_MISSING_REASON,
    WATCH_STALE_REASON,
    BLOCK_CONFLICTING_REASON,
    BLOCK_MISSING_REASON,
    BLOCK_STALE_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("s", "lug"),
    _join_parts("question"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("source"),
    _join_parts("http"),
    _join_parts(":", "/", "/"),
    _join_parts("dsn"),
    _join_parts("table"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("liv", "e"),
    _join_parts("siz", "ing"),
    _join_parts("pos", "ition"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
    _join_parts("rec", "ommend"),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_EQUITIES_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
    "ResearchDomainEquitiesSignalMemoryQualityConfig",
    "ResearchDomainEquitiesSignalMemoryQualityInput",
    "ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount",
    "ResearchDomainEquitiesSignalMemoryQualityReport",
    "ResearchDomainEquitiesSignalMemoryQualityRow",
    "build_research_domain_equities_signal_memory_quality_report",
    "research_domain_equities_signal_memory_quality_report_digest",
    "research_domain_equities_signal_memory_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainEquitiesSignalMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_EQUITIES_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
    )
    pass_min_coverage_ratio: Decimal = Decimal("0.900000")
    watch_min_coverage_ratio: Decimal = Decimal("0.700000")
    pass_max_conflict_ratio: Decimal = Decimal("0.050000")
    block_min_conflict_ratio: Decimal = Decimal("0.250000")
    pass_max_refresh_age_seconds: Decimal = Decimal("172800.000000")
    block_min_refresh_age_seconds: Decimal = Decimal("604800.000000")
    block_min_missing_catalyst_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainEquitiesSignalMemoryQualityConfig:
            raise TypeError(
                "ResearchDomainEquitiesSignalMemoryQualityConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainEquitiesSignalMemoryQualityConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchDomainEquitiesSignalMemoryQualityConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_min_coverage_ratio",
            "watch_min_coverage_ratio",
            "pass_max_conflict_ratio",
            "block_min_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_max_refresh_age_seconds",
            "block_min_refresh_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "block_min_missing_catalyst_count",
            _require_positive_whole_decimal(
                "block_min_missing_catalyst_count",
                self.block_min_missing_catalyst_count,
            ),
        )
        if self.pass_min_coverage_ratio < self.watch_min_coverage_ratio:
            raise ValueError(
                "pass_min_coverage_ratio must not be below watch_min_coverage_ratio",
            )
        if self.block_min_conflict_ratio <= self.pass_max_conflict_ratio:
            raise ValueError(
                "block_min_conflict_ratio must exceed pass_max_conflict_ratio",
            )
        if self.block_min_refresh_age_seconds <= self.pass_max_refresh_age_seconds:
            raise ValueError(
                "block_min_refresh_age_seconds must exceed "
                "pass_max_refresh_age_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchDomainEquitiesSignalMemoryQualityInput:
    team_key: str
    index_signal_group: str
    catalyst_family: str
    available_catalyst_count: Decimal
    required_catalyst_count: Decimal
    stale_catalyst_count: Decimal
    conflicting_catalyst_count: Decimal
    latest_refresh_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainEquitiesSignalMemoryQualityInput:
            raise TypeError(
                "ResearchDomainEquitiesSignalMemoryQualityInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainEquitiesSignalMemoryQualityInput:
            raise ValueError(
                "input must be exactly ResearchDomainEquitiesSignalMemoryQualityInput",
            )
        for field_name in ("team_key", "index_signal_group", "catalyst_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "available_catalyst_count",
            _require_nonnegative_whole_decimal(
                "available_catalyst_count",
                self.available_catalyst_count,
            ),
        )
        object.__setattr__(
            self,
            "required_catalyst_count",
            _require_positive_whole_decimal(
                "required_catalyst_count",
                self.required_catalyst_count,
            ),
        )
        for field_name in ("stale_catalyst_count", "conflicting_catalyst_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_refresh_age_seconds",
            _require_nonnegative_decimal(
                "latest_refresh_age_seconds",
                self.latest_refresh_age_seconds,
            ),
        )
        if self.stale_catalyst_count > self.available_catalyst_count:
            raise ValueError("stale_catalyst_count must not exceed available count")
        if self.conflicting_catalyst_count > self.available_catalyst_count:
            raise ValueError(
                "conflicting_catalyst_count must not exceed available count",
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchDomainEquitiesSignalMemoryQualityRow:
    team_key: str
    index_signal_group: str
    catalyst_family: str
    public_status: str
    available_catalyst_count: Decimal
    required_catalyst_count: Decimal
    missing_catalyst_count: Decimal
    stale_catalyst_count: Decimal
    conflicting_catalyst_count: Decimal
    latest_refresh_age_seconds: Decimal
    coverage_ratio: Decimal
    conflict_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainEquitiesSignalMemoryQualityRow:
            raise TypeError(
                "ResearchDomainEquitiesSignalMemoryQualityRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainEquitiesSignalMemoryQualityRow:
            raise ValueError("row must be exactly ResearchDomainEquitiesSignalMemoryQualityRow")
        for field_name in ("team_key", "index_signal_group", "catalyst_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_public_status("public_status", self.public_status)
        for field_name in (
            "available_catalyst_count",
            "missing_catalyst_count",
            "stale_catalyst_count",
            "conflicting_catalyst_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_catalyst_count",
            _require_positive_whole_decimal(
                "required_catalyst_count",
                self.required_catalyst_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_refresh_age_seconds",
            _require_nonnegative_decimal(
                "latest_refresh_age_seconds",
                self.latest_refresh_age_seconds,
            ),
        )
        for field_name in ("coverage_ratio", "conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.public_status != _public_status_from_reason_codes(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        if self.stale_catalyst_count > self.available_catalyst_count:
            raise ValueError("stale_catalyst_count must not exceed available count")
        if self.conflicting_catalyst_count > self.available_catalyst_count:
            raise ValueError(
                "conflicting_catalyst_count must not exceed available count",
            )
        if self.missing_catalyst_count != _positive_gap(
            self.required_catalyst_count,
            self.available_catalyst_count,
        ):
            raise ValueError("missing_catalyst_count must match available and required")
        if self.coverage_ratio != _ratio(
            self.available_catalyst_count,
            self.required_catalyst_count,
        ):
            raise ValueError("coverage_ratio must match available and required")
        if self.conflict_ratio != _ratio(
            self.conflicting_catalyst_count,
            self.available_catalyst_count,
        ):
            raise ValueError("conflict_ratio must match conflicting and available")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount:
            raise TypeError(
                "ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchDomainEquitiesSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_input_count: Decimal
    conflicting_input_count: Decimal
    stale_input_count: Decimal
    total_available_catalyst_count: Decimal
    total_required_catalyst_count: Decimal
    total_missing_catalyst_count: Decimal
    total_conflicting_catalyst_count: Decimal
    total_stale_catalyst_count: Decimal
    average_coverage_ratio: Decimal
    average_conflict_ratio: Decimal
    max_refresh_age_seconds: Decimal
    rows: tuple[ResearchDomainEquitiesSignalMemoryQualityRow, ...]
    reason_code_counts: tuple[
        ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainEquitiesSignalMemoryQualityReport:
            raise TypeError(
                "ResearchDomainEquitiesSignalMemoryQualityReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainEquitiesSignalMemoryQualityReport:
            raise ValueError(
                "report must be exactly ResearchDomainEquitiesSignalMemoryQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_status("report_status", self.report_status)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_input_count",
            "conflicting_input_count",
            "stale_input_count",
            "total_available_catalyst_count",
            "total_required_catalyst_count",
            "total_missing_catalyst_count",
            "total_conflicting_catalyst_count",
            "total_stale_catalyst_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_coverage_ratio", "average_conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_refresh_age_seconds",
            _require_nonnegative_decimal(
                "max_refresh_age_seconds",
                self.max_refresh_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _require_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_count_tuple("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_equities_signal_memory_quality_report_payload(self)


def build_research_domain_equities_signal_memory_quality_report(
    rows: object,
    *,
    config: ResearchDomainEquitiesSignalMemoryQualityConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainEquitiesSignalMemoryQualityReport:
    cfg = config or ResearchDomainEquitiesSignalMemoryQualityConfig()
    if type(cfg) is not ResearchDomainEquitiesSignalMemoryQualityConfig:
        raise TypeError(
            "config must be exactly ResearchDomainEquitiesSignalMemoryQualityConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)

    if not input_rows:
        reason_counts = (
            ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
        values: dict[str, object] = {
            "generated_at": generated_at_utc,
            "config_version": cfg.config_version,
            "report_status": STATUS_BLOCK,
            "input_count": ZERO,
            "pass_count": ZERO,
            "watch_count": ZERO,
            "block_count": ZERO,
            "missing_input_count": ZERO,
            "conflicting_input_count": ZERO,
            "stale_input_count": ZERO,
            "total_available_catalyst_count": ZERO,
            "total_required_catalyst_count": ZERO,
            "total_missing_catalyst_count": ZERO,
            "total_conflicting_catalyst_count": ZERO,
            "total_stale_catalyst_count": ZERO,
            "average_coverage_ratio": ZERO,
            "average_conflict_ratio": ZERO,
            "max_refresh_age_seconds": ZERO,
            "rows": (),
            "reason_code_counts": reason_counts,
            "reason_codes": (NO_INPUTS_REASON,),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        values["derived_validation_digest"] = _derived_validation_digest(values)
        return ResearchDomainEquitiesSignalMemoryQualityReport(**values)

    report_rows = tuple(_build_row(row, config=cfg) for row in input_rows)
    sorted_rows = tuple(
        sorted(
            report_rows,
            key=lambda row: (
                _STATUS_RANK[row.public_status],
                row.team_key,
                row.index_signal_group,
                row.catalyst_family,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "report_status": _report_status(sorted_rows),
        "input_count": _count_decimal(sorted_rows),
        "pass_count": _sum_if(sorted_rows, lambda row: row.public_status == STATUS_PASS),
        "watch_count": _sum_if(sorted_rows, lambda row: row.public_status == STATUS_WATCH),
        "block_count": _sum_if(sorted_rows, lambda row: row.public_status == STATUS_BLOCK),
        "missing_input_count": _sum_if(
            sorted_rows,
            lambda row: row.missing_catalyst_count > ZERO,
        ),
        "conflicting_input_count": _sum_if(
            sorted_rows,
            lambda row: row.conflicting_catalyst_count > ZERO,
        ),
        "stale_input_count": _sum_if(
            sorted_rows,
            lambda row: row.stale_catalyst_count > ZERO
            or row.latest_refresh_age_seconds > cfg.pass_max_refresh_age_seconds,
        ),
        "total_available_catalyst_count": _sum_decimal(
            row.available_catalyst_count for row in sorted_rows
        ),
        "total_required_catalyst_count": _sum_decimal(
            row.required_catalyst_count for row in sorted_rows
        ),
        "total_missing_catalyst_count": _sum_decimal(
            row.missing_catalyst_count for row in sorted_rows
        ),
        "total_conflicting_catalyst_count": _sum_decimal(
            row.conflicting_catalyst_count for row in sorted_rows
        ),
        "total_stale_catalyst_count": _sum_decimal(
            row.stale_catalyst_count for row in sorted_rows
        ),
        "average_coverage_ratio": _average(row.coverage_ratio for row in sorted_rows),
        "average_conflict_ratio": _average(row.conflict_ratio for row in sorted_rows),
        "max_refresh_age_seconds": max(
            (row.latest_refresh_age_seconds for row in sorted_rows),
            default=ZERO,
        ).quantize(QUANT),
        "rows": sorted_rows,
        "reason_code_counts": reason_counts,
        "reason_codes": tuple(item.reason_code for item in reason_counts),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchDomainEquitiesSignalMemoryQualityReport(**values)


def research_domain_equities_signal_memory_quality_report_payload(
    report: ResearchDomainEquitiesSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainEquitiesSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        payload = _payload_value(asdict(report))
        _reject_unsafe_public_payload("report payload", payload)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _require_payload_flags(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_payload_digest(payload)
        return payload
    raise TypeError("report must be exactly ResearchDomainEquitiesSignalMemoryQualityReport")


def research_domain_equities_signal_memory_quality_report_digest(
    report: ResearchDomainEquitiesSignalMemoryQualityReport,
) -> dict[str, Any]:
    payload = research_domain_equities_signal_memory_quality_report_payload(report)
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "report_status": payload["report_status"],
        "input_count": payload["input_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "reason_codes": payload["reason_codes"],
        "derived_validation_digest": payload["derived_validation_digest"],
    }


def _build_row(
    row: ResearchDomainEquitiesSignalMemoryQualityInput,
    *,
    config: ResearchDomainEquitiesSignalMemoryQualityConfig,
) -> ResearchDomainEquitiesSignalMemoryQualityRow:
    missing_count = _positive_gap(row.required_catalyst_count, row.available_catalyst_count)
    coverage_ratio = _ratio(row.available_catalyst_count, row.required_catalyst_count)
    conflict_ratio = _ratio(
        row.conflicting_catalyst_count,
        row.available_catalyst_count,
    )

    reasons: list[str] = []
    if conflict_ratio >= config.block_min_conflict_ratio:
        reasons.append(BLOCK_CONFLICTING_REASON)
    elif conflict_ratio > config.pass_max_conflict_ratio:
        reasons.append(WATCH_CONFLICTING_REASON)

    if (
        missing_count >= config.block_min_missing_catalyst_count
        or coverage_ratio < config.watch_min_coverage_ratio
    ):
        reasons.append(BLOCK_MISSING_REASON)
    elif missing_count > ZERO or coverage_ratio < config.pass_min_coverage_ratio:
        reasons.append(WATCH_MISSING_REASON)

    if row.latest_refresh_age_seconds >= config.block_min_refresh_age_seconds:
        reasons.append(BLOCK_STALE_REASON)
    elif (
        row.latest_refresh_age_seconds > config.pass_max_refresh_age_seconds
        or row.stale_catalyst_count > ZERO
    ):
        reasons.append(WATCH_STALE_REASON)

    if not reasons:
        reasons.append(PASS_REASON)

    reason_codes = _normalize_reason_codes("reason_codes", tuple(reasons))
    return ResearchDomainEquitiesSignalMemoryQualityRow(
        team_key=row.team_key,
        index_signal_group=row.index_signal_group,
        catalyst_family=row.catalyst_family,
        public_status=_public_status_from_reason_codes(reason_codes),
        available_catalyst_count=row.available_catalyst_count,
        required_catalyst_count=row.required_catalyst_count,
        missing_catalyst_count=missing_count,
        stale_catalyst_count=row.stale_catalyst_count,
        conflicting_catalyst_count=row.conflicting_catalyst_count,
        latest_refresh_age_seconds=row.latest_refresh_age_seconds,
        coverage_ratio=coverage_ratio,
        conflict_ratio=conflict_ratio,
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    value: object,
) -> tuple[ResearchDomainEquitiesSignalMemoryQualityInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise TypeError("rows must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchDomainEquitiesSignalMemoryQualityInput:
            raise ValueError(
                "rows must contain ResearchDomainEquitiesSignalMemoryQualityInput",
            )
        _require_hard_flags("input", row)
    keys = tuple(
        (
            row.team_key,
            row.index_signal_group,
            row.catalyst_family,
            row.available_catalyst_count,
            row.required_catalyst_count,
            row.stale_catalyst_count,
            row.conflicting_catalyst_count,
            row.latest_refresh_age_seconds,
        )
        for row in rows
    )
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicates")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchDomainEquitiesSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount, ...]:
    row_count = _count_decimal(rows)
    counts: dict[str, Decimal] = {}
    sequence: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in counts:
                counts[reason_code] = ZERO
                sequence.append(reason_code)
            counts[reason_code] += ONE
    return tuple(
        ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            row_ratio=_ratio(counts[reason_code], row_count),
        )
        for reason_code in sequence
    )


def _report_status(
    rows: tuple[ResearchDomainEquitiesSignalMemoryQualityRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _public_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block_conflicting") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_block_missing") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_block_stale") for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _count_decimal(value: tuple[object, ...]) -> Decimal:
    return Decimal(len(value)).quantize(QUANT)


def _sum_decimal(values: Any) -> Decimal:
    return sum(tuple(values), ZERO).quantize(QUANT)


def _sum_if(
    rows: tuple[ResearchDomainEquitiesSignalMemoryQualityRow, ...],
    predicate: Callable[[ResearchDomainEquitiesSignalMemoryQualityRow], bool],
) -> Decimal:
    return Decimal(sum(1 for row in rows if predicate(row))).quantize(QUANT)


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(items, ZERO) / Decimal(len(items))).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, numerator / denominator)).quantize(QUANT)


def _positive_gap(required: Decimal, available: Decimal) -> Decimal:
    return max(ZERO, required - available).quantize(QUANT)


def _require_row_tuple(
    field_name: str,
    value: tuple[ResearchDomainEquitiesSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainEquitiesSignalMemoryQualityRow, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchDomainEquitiesSignalMemoryQualityRow:
            raise ValueError(
                f"{field_name} must contain ResearchDomainEquitiesSignalMemoryQualityRow",
            )
    return value


def _require_reason_count_tuple(
    field_name: str,
    value: tuple[ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain "
                "ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount",
            )
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_status(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} contains duplicate reason code values")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANT)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value.quantize(QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_payload_flags(value: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_payload_digest(value: dict[str, object]) -> None:
    digest = value.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest must match payload")


def _payload_value(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat().replace("+00:00", "Z")
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload public numerics must be Decimal-derived strings")
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} must be public")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (int, float):
        raise ValueError(f"{label} must be public")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} must be public")


def _validate_report_consistency(
    report: ResearchDomainEquitiesSignalMemoryQualityReport,
) -> None:
    if report.input_count != _count_decimal(report.rows):
        raise ValueError("input_count must match rows")
    if report.pass_count != _sum_if(
        report.rows,
        lambda row: row.public_status == STATUS_PASS,
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_if(
        report.rows,
        lambda row: row.public_status == STATUS_WATCH,
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _sum_if(
        report.rows,
        lambda row: row.public_status == STATUS_BLOCK,
    ):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
