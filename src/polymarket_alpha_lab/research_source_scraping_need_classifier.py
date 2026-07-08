"""Report-only classifier for safe research source collection needs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPING_NEED_CLASSIFIER_CONFIG_VERSION = (
    "research-source-scraping-need-classifier-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUSES = frozenset(("pass", "watch", "block"))
_GAP_KINDS = frozenset(
    (
        "official_resolution",
        "independent_confirmation",
        "freshness_refresh",
        "dynamic_render_check",
        "unstructured_source_parse",
        "manual_verification",
    ),
)
_TASK_TYPES = frozenset(
    (
        "none",
        "agent_reach",
        "scrapling",
        "browser",
        "manual_verification",
    ),
)
_UNSAFE_KEY_TERMS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "auth",
)
_UNSAFE_TEXT_TERMS = _UNSAFE_KEY_TERMS + (
    "source-ref",
    "source-url",
    "source-text",
    "http://",
    "https://",
    "://",
)
_REASON_CODE_SEQUENCE = (
    "scraping_need_empty",
    "missing_official_anchor",
    "missing_independent_source",
    "low_source_family_diversity",
    "source_freshness_watch",
    "source_freshness_block",
    "agent_reach_needed",
    "scrapling_extraction_needed",
    "browser_collection_needed",
    "conflict_flag_present",
    "manual_verification_required",
    "scraping_need_pass",
    "scraping_need_watch",
    "scraping_need_block",
)


@dataclass(frozen=True)
class ResearchSourceScrapingNeedConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_SCRAPING_NEED_CLASSIFIER_CONFIG_VERSION
    min_source_family_count: Decimal = Decimal("2")
    watch_need_score: Decimal = Decimal("0.250000")
    block_need_score: Decimal = Decimal("0.800000")
    missing_official_weight: Decimal = Decimal("0.250000")
    missing_independent_weight: Decimal = Decimal("0.200000")
    staleness_weight: Decimal = Decimal("0.200000")
    scrapling_weight: Decimal = Decimal("0.150000")
    browser_weight: Decimal = Decimal("0.200000")
    manual_verification_weight: Decimal = Decimal("0.400000")
    conflict_weight: Decimal = Decimal("0.300000")
    low_diversity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingNeedConfig:
            raise TypeError("ResearchSourceScrapingNeedConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingNeedConfig:
            raise ValueError("config must be exactly ResearchSourceScrapingNeedConfig")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPING_NEED_CLASSIFIER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_positive_whole_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        for field_name in (
            "watch_need_score",
            "block_need_score",
            "missing_official_weight",
            "missing_independent_weight",
            "staleness_weight",
            "scrapling_weight",
            "browser_weight",
            "manual_verification_weight",
            "conflict_weight",
            "low_diversity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_need_score >= self.block_need_score:
            raise ValueError("watch_need_score must be less than block_need_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScrapingNeedGap:
    public_gap_key: str
    gap_kind: str
    freshness_score: Decimal
    source_family_count: Decimal
    has_official_anchor: bool
    has_independent_source: bool
    needs_dynamic_rendering: bool = False
    needs_unstructured_extraction: bool = False
    requires_human_verification: bool = False
    conflict_flag: bool = False
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingNeedGap:
            raise TypeError("ResearchSourceScrapingNeedGap does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingNeedGap:
            raise ValueError("gap must be exactly ResearchSourceScrapingNeedGap")
        _require_public_identifier("public_gap_key", self.public_gap_key)
        _require_member("gap_kind", self.gap_kind, _GAP_KINDS)
        object.__setattr__(
            self,
            "freshness_score",
            _require_probability_decimal("freshness_score", self.freshness_score),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_whole_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        for field_name in (
            "has_official_anchor",
            "has_independent_source",
            "needs_dynamic_rendering",
            "needs_unstructured_extraction",
            "requires_human_verification",
            "conflict_flag",
        ):
            object.__setattr__(self, field_name, _require_bool(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("gap", self)
        _reject_unsafe_public_payload("gap", self)


@dataclass(frozen=True)
class ResearchSourceScrapingNeedRow:
    public_gap_key: str
    gap_kind: str
    status: str
    task_types: tuple[str, ...]
    need_score: Decimal
    reason_codes: tuple[str, ...]
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingNeedRow:
            raise TypeError("ResearchSourceScrapingNeedRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingNeedRow:
            raise ValueError("row must be exactly ResearchSourceScrapingNeedRow")
        _require_public_identifier("public_gap_key", self.public_gap_key)
        _require_member("gap_kind", self.gap_kind, _GAP_KINDS)
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "task_types", _normalize_task_types(self.task_types))
        object.__setattr__(
            self,
            "need_score",
            _require_probability_decimal("need_score", self.need_score),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScrapingNeedReport:
    generated_at: datetime
    config_version: str
    status: str
    gap_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    agent_reach_count: Decimal
    scrapling_count: Decimal
    browser_count: Decimal
    manual_verification_count: Decimal
    average_need_score: Decimal | None
    rows: tuple[ResearchSourceScrapingNeedRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingNeedReport:
            raise TypeError("ResearchSourceScrapingNeedReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingNeedReport:
            raise ValueError("report must be exactly ResearchSourceScrapingNeedReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPING_NEED_CLASSIFIER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("status", self.status, _STATUSES)
        for field_name in (
            "gap_count",
            "pass_count",
            "watch_count",
            "block_count",
            "agent_reach_count",
            "scrapling_count",
            "browser_count",
            "manual_verification_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_need_score",
            _require_optional_probability_decimal(
                "average_need_score",
                self.average_need_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSourceScrapingNeedReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_scraping_need_report(
    gaps: Sequence[ResearchSourceScrapingNeedGap],
    *,
    config: ResearchSourceScrapingNeedConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingNeedReport:
    if type(config) is not ResearchSourceScrapingNeedConfig:
        raise ValueError("config must be a ResearchSourceScrapingNeedConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _build_rows(_normalize_gaps(gaps), config)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "gap_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "agent_reach_count": _decimal_count(_task_count(rows, "agent_reach")),
        "scrapling_count": _decimal_count(_task_count(rows, "scrapling")),
        "browser_count": _decimal_count(_task_count(rows, "browser")),
        "manual_verification_count": _decimal_count(
            _task_count(rows, "manual_verification"),
        ),
        "average_need_score": _average_need_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceScrapingNeedReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_scraping_need_report_payload(
    report: ResearchSourceScrapingNeedReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceScrapingNeedReport:
        raise ValueError("report must be a ResearchSourceScrapingNeedReport")
    _require_hard_flags("report", report)
    return report.payload


def research_source_scraping_need_report_digest(
    report: ResearchSourceScrapingNeedReport,
) -> str:
    if type(report) is not ResearchSourceScrapingNeedReport:
        raise ValueError("report must be a ResearchSourceScrapingNeedReport")
    _require_hard_flags("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def _build_rows(
    gaps: tuple[ResearchSourceScrapingNeedGap, ...],
    config: ResearchSourceScrapingNeedConfig,
) -> tuple[ResearchSourceScrapingNeedRow, ...]:
    return tuple(_row_for_gap(gap, config) for gap in gaps)


def _row_for_gap(
    gap: ResearchSourceScrapingNeedGap,
    config: ResearchSourceScrapingNeedConfig,
) -> ResearchSourceScrapingNeedRow:
    score = _need_score(gap, config)
    task_types = _task_types_for_gap(gap, config)
    status = _row_status(gap, task_types, score, config)
    reason_codes = _row_reason_codes(gap, task_types, status, config)
    return ResearchSourceScrapingNeedRow(
        public_gap_key=gap.public_gap_key,
        gap_kind=gap.gap_kind,
        status=status,
        task_types=task_types,
        need_score=score,
        reason_codes=reason_codes,
        public_note=gap.public_note,
    )


def _need_score(
    gap: ResearchSourceScrapingNeedGap,
    config: ResearchSourceScrapingNeedConfig,
) -> Decimal:
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        score = (config.staleness_weight * (_ONE - gap.freshness_score)).quantize(
            _QUANT,
        )
        if not gap.has_official_anchor:
            score += config.missing_official_weight
        if not gap.has_independent_source:
            score += config.missing_independent_weight
        if gap.source_family_count < config.min_source_family_count:
            score += config.low_diversity_weight
        if gap.needs_unstructured_extraction:
            score += config.scrapling_weight
        if gap.needs_dynamic_rendering:
            score += config.browser_weight
        if gap.requires_human_verification:
            score += config.manual_verification_weight
        if gap.conflict_flag:
            score += config.conflict_weight
    if score > _ONE:
        return _ONE
    return score.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _task_types_for_gap(
    gap: ResearchSourceScrapingNeedGap,
    config: ResearchSourceScrapingNeedConfig,
) -> tuple[str, ...]:
    if gap.requires_human_verification or gap.conflict_flag:
        return ("manual_verification",)
    tasks: list[str] = []
    if gap.needs_dynamic_rendering:
        tasks.append("browser")
    if gap.needs_unstructured_extraction:
        tasks.append("scrapling")
    if (
        not gap.has_official_anchor
        or not gap.has_independent_source
        or gap.source_family_count < config.min_source_family_count
    ):
        tasks.append("agent_reach")
    if not tasks:
        return ("none",)
    return tuple(tasks)


def _row_status(
    gap: ResearchSourceScrapingNeedGap,
    task_types: tuple[str, ...],
    need_score: Decimal,
    config: ResearchSourceScrapingNeedConfig,
) -> str:
    if gap.requires_human_verification or gap.conflict_flag:
        return "block"
    if need_score >= config.block_need_score:
        return "block"
    if need_score >= config.watch_need_score or task_types != ("none",):
        return "watch"
    return "pass"


def _row_reason_codes(
    gap: ResearchSourceScrapingNeedGap,
    task_types: tuple[str, ...],
    status: str,
    config: ResearchSourceScrapingNeedConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not gap.has_official_anchor:
        reason_codes.append("missing_official_anchor")
    if not gap.has_independent_source:
        reason_codes.append("missing_independent_source")
    if gap.source_family_count < config.min_source_family_count:
        reason_codes.append("low_source_family_diversity")
    if gap.freshness_score <= Decimal("0.200000"):
        reason_codes.append("source_freshness_block")
    elif gap.freshness_score <= Decimal("0.800000"):
        reason_codes.append("source_freshness_watch")
    if "agent_reach" in task_types:
        reason_codes.append("agent_reach_needed")
    if "scrapling" in task_types:
        reason_codes.append("scrapling_extraction_needed")
    if "browser" in task_types:
        reason_codes.append("browser_collection_needed")
    if "manual_verification" in task_types:
        reason_codes.append("manual_verification_required")
    if gap.conflict_flag:
        reason_codes.append("conflict_flag_present")
    reason_codes.append(f"scraping_need_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_gaps(
    gaps: Sequence[ResearchSourceScrapingNeedGap],
) -> tuple[ResearchSourceScrapingNeedGap, ...]:
    if isinstance(gaps, (str, bytes)) or not isinstance(gaps, Sequence):
        raise ValueError("gaps must be a sequence")
    normalized: list[ResearchSourceScrapingNeedGap] = []
    for gap in gaps:
        if type(gap) is not ResearchSourceScrapingNeedGap:
            raise ValueError("gaps must contain ResearchSourceScrapingNeedGap values")
        _require_hard_flags("gap", gap)
        _reject_unsafe_public_payload("gap", gap)
        normalized.append(gap)
    return tuple(sorted(normalized, key=lambda item: item.public_gap_key))


def _normalize_rows(
    rows: Sequence[ResearchSourceScrapingNeedRow],
) -> tuple[ResearchSourceScrapingNeedRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceScrapingNeedRow] = []
    for row in rows:
        if type(row) is not ResearchSourceScrapingNeedRow:
            raise ValueError("rows must contain ResearchSourceScrapingNeedRow values")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.public_gap_key))


def _report_status(rows: tuple[ResearchSourceScrapingNeedRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchSourceScrapingNeedRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("scraping_need_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[ResearchSourceScrapingNeedRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _task_count(rows: tuple[ResearchSourceScrapingNeedRow, ...], task_type: str) -> int:
    return sum(1 for row in rows if task_type in row.task_types)


def _average_need_score(rows: tuple[ResearchSourceScrapingNeedRow, ...]) -> Decimal | None:
    if not rows:
        return None
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        return (sum((row.need_score for row in rows), _ZERO) / _decimal_count(len(rows))).quantize(
            _QUANT,
        )


def _validate_row_consistency(row: ResearchSourceScrapingNeedRow) -> None:
    if row.status == "pass":
        if row.task_types != ("none",):
            raise ValueError("pass rows must not require collection tasks")
        if row.reason_codes != ("scraping_need_pass",):
            raise ValueError("pass rows must only include scraping_need_pass")
    if row.status == "watch":
        if "scraping_need_watch" not in row.reason_codes:
            raise ValueError("watch rows must include scraping_need_watch")
        if "scraping_need_block" in row.reason_codes:
            raise ValueError("watch rows must not include scraping_need_block")
    if row.status == "block" and "scraping_need_block" not in row.reason_codes:
        raise ValueError("block rows must include scraping_need_block")
    for task_type, reason_code in (
        ("agent_reach", "agent_reach_needed"),
        ("scrapling", "scrapling_extraction_needed"),
        ("browser", "browser_collection_needed"),
        ("manual_verification", "manual_verification_required"),
    ):
        if task_type in row.task_types and reason_code not in row.reason_codes:
            raise ValueError(f"{task_type} rows must include {reason_code}")
        if task_type not in row.task_types and reason_code in row.reason_codes:
            raise ValueError(f"{reason_code} must match task_types")


def _validate_report_consistency(report: ResearchSourceScrapingNeedReport) -> None:
    if report.gap_count != _decimal_count(len(report.rows)):
        raise ValueError("gap_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.agent_reach_count != _decimal_count(_task_count(report.rows, "agent_reach")):
        raise ValueError("agent_reach_count must match rows")
    if report.scrapling_count != _decimal_count(_task_count(report.rows, "scrapling")):
        raise ValueError("scrapling_count must match rows")
    if report.browser_count != _decimal_count(_task_count(report.rows, "browser")):
        raise ValueError("browser_count must match rows")
    if report.manual_verification_count != _decimal_count(
        _task_count(report.rows, "manual_verification"),
    ):
        raise ValueError("manual_verification_count must match rows")
    if report.average_need_score != _average_need_score(report.rows):
        raise ValueError("average_need_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {tuple(sorted(allowed))}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe detail")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if "?" in value or _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe detail")
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_task_types(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("task_types must be a sequence")
    normalized: list[str] = []
    for task_type in value:
        _require_member("task_type", task_type, _TASK_TYPES)
        normalized.append(task_type)
    if not normalized:
        raise ValueError("task_types must not be empty")
    if "none" in normalized and len(normalized) != 1:
        raise ValueError("none task_type cannot be mixed with collection tasks")
    return tuple(dict.fromkeys(normalized))


def _normalize_reason_codes(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason code")
        normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in frozenset(normalized)
    )


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: ResearchSourceScrapingNeedReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
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
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime", value).isoformat()
    if type(value) is bool or type(value) is str or type(value) is int:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
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
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    normalized = key.lower().replace("-", "_")
    if any(term in normalized for term in _UNSAFE_KEY_TERMS):
        raise ValueError(f"{path}.{key} contains unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{path} contains unsafe public detail")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in _UNSAFE_TEXT_TERMS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPING_NEED_CLASSIFIER_CONFIG_VERSION",
    "ResearchSourceScrapingNeedConfig",
    "ResearchSourceScrapingNeedGap",
    "ResearchSourceScrapingNeedReport",
    "ResearchSourceScrapingNeedRow",
    "build_research_source_scraping_need_report",
    "research_source_scraping_need_report_digest",
    "research_source_scraping_need_report_payload",
)
