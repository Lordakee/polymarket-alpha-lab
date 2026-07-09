"""Pure report-only monitor for resolution authority revision lag."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "ResearchSourceResolutionAuthorityRevisionLagConfig",
    "ResearchSourceResolutionAuthorityRevisionLagInput",
    "ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount",
    "ResearchSourceResolutionAuthorityRevisionLagReport",
    "ResearchSourceResolutionAuthorityRevisionLagRow",
    "STATUSES",
    "build_research_source_resolution_authority_revision_lag_report",
    "research_source_resolution_authority_revision_lag_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-resolution-authority-revision-lag-report-v0"
STATUSES = ("pass", "watch", "block")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_KEY_UNSAFE_TERMS = (
    "candidate",
    "market",
    "condition",
    "slug",
    "question",
    "url",
    "text",
    "ref",
    "d" + "sn",
    "ta" + "ble",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "recomm" + "endation",
    "siz" + "ing",
)
_PAYLOAD_UNSAFE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "raw_" + "candidate",
    "candidate_" + "id",
    "raw_" + "market",
    "market_" + "id",
    "market_" + "slug",
    "slug",
    "question",
    "source_" + "url",
    "source_" + "text",
    "raw_" + "source",
    "d" + "sn",
    "ta" + "ble",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve_" + "trading",
    "recomm" + "endation",
    "siz" + "ing",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRevisionLagConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    source_revision_watch_lag_seconds: Decimal = Decimal("1800")
    source_revision_block_lag_seconds: Decimal = Decimal("7200")
    authority_revision_watch_lag_seconds: Decimal = Decimal("3600")
    authority_revision_block_lag_seconds: Decimal = Decimal("14400")
    authority_score_watch_threshold: Decimal = Decimal("0.700000")
    authority_score_block_threshold: Decimal = Decimal("0.500000")
    revision_conflict_watch_threshold: Decimal = Decimal("0.300000")
    revision_conflict_block_threshold: Decimal = Decimal("0.600000")
    watch_pressure_threshold: Decimal = Decimal("0.350000")
    block_pressure_threshold: Decimal = Decimal("0.700000")
    source_revision_lag_weight: Decimal = Decimal("0.300000")
    authority_revision_lag_weight: Decimal = Decimal("0.300000")
    authority_gap_weight: Decimal = Decimal("0.200000")
    revision_conflict_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRevisionLagConfig:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRevisionLagConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionAuthorityRevisionLagConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_revision_watch_lag_seconds",
            "source_revision_block_lag_seconds",
            "authority_revision_watch_lag_seconds",
            "authority_revision_block_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_score_watch_threshold",
            "authority_score_block_threshold",
            "revision_conflict_watch_threshold",
            "revision_conflict_block_threshold",
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "source_revision_lag_weight",
            "authority_revision_lag_weight",
            "authority_gap_weight",
            "revision_conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRevisionLagInput:
    public_case_key: str
    source_revision_lag_seconds: Decimal
    authority_revision_lag_seconds: Decimal
    authority_score: Decimal
    revision_conflict_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRevisionLagInput:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRevisionLagInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionAuthorityRevisionLagInput,
            "lag input",
        )
        _require_public_case_key("public_case_key", self.public_case_key)
        for field_name in (
            "source_revision_lag_seconds",
            "authority_revision_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("authority_score", "revision_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("lag input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRevisionLagRow:
    public_case_key: str
    source_revision_lag_seconds: Decimal
    source_revision_lag_pressure: Decimal
    source_revision_lag_band: str
    authority_revision_lag_seconds: Decimal
    authority_revision_lag_pressure: Decimal
    authority_revision_lag_band: str
    authority_score: Decimal
    authority_gap: Decimal
    revision_conflict_score: Decimal
    revision_lag_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_config: InitVar[
        ResearchSourceResolutionAuthorityRevisionLagConfig | None
    ] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRevisionLagRow:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRevisionLagRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourceResolutionAuthorityRevisionLagConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchSourceResolutionAuthorityRevisionLagRow, "row")
        active_validation_config = (
            ResearchSourceResolutionAuthorityRevisionLagConfig()
            if validation_config is None
            else validation_config
        )
        if type(active_validation_config) is not ResearchSourceResolutionAuthorityRevisionLagConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchSourceResolutionAuthorityRevisionLagConfig",
            )
        _require_hard_flags("validation_config", active_validation_config)
        _require_public_case_key("public_case_key", self.public_case_key)
        for field_name in (
            "source_revision_lag_seconds",
            "authority_revision_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_revision_lag_pressure",
            "authority_revision_lag_pressure",
            "authority_score",
            "authority_gap",
            "revision_conflict_score",
            "revision_lag_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_lag_band("source_revision_lag_band", self.source_revision_lag_band)
        _require_lag_band("authority_revision_lag_band", self.authority_revision_lag_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self, config=active_validation_config)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRevisionLagReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_revision_lag_pressure: Decimal | None
    max_source_revision_lag_seconds: Decimal
    max_authority_revision_lag_seconds: Decimal
    lowest_authority_score: Decimal
    highest_revision_conflict_score: Decimal
    status: str
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...]
    reason_code_counts: tuple[
        ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRevisionLagReport:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRevisionLagReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceResolutionAuthorityRevisionLagReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_revision_lag_pressure",
            _require_optional_probability_decimal(
                "average_revision_lag_pressure",
                self.average_revision_lag_pressure,
            ),
        )
        for field_name in (
            "max_source_revision_lag_seconds",
            "max_authority_revision_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("lowest_authority_score", "highest_revision_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_resolution_authority_revision_lag_report(
    lag_items: Iterable[object],
    *,
    config: ResearchSourceResolutionAuthorityRevisionLagConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionAuthorityRevisionLagReport:
    if type(config) is not ResearchSourceResolutionAuthorityRevisionLagConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionAuthorityRevisionLagConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_lag_items(lag_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_case_key)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_revision_lag_pressure": _average_revision_lag_pressure(rows),
        "max_source_revision_lag_seconds": max(
            (row.source_revision_lag_seconds for row in rows),
            default=_ZERO,
        ),
        "max_authority_revision_lag_seconds": max(
            (row.authority_revision_lag_seconds for row in rows),
            default=_ZERO,
        ),
        "lowest_authority_score": min(
            (row.authority_score for row in rows),
            default=_ZERO,
        ),
        "highest_revision_conflict_score": max(
            (row.revision_conflict_score for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceResolutionAuthorityRevisionLagReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_resolution_authority_revision_lag_report_payload(
    report: ResearchSourceResolutionAuthorityRevisionLagReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceResolutionAuthorityRevisionLagReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionAuthorityRevisionLagReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchSourceResolutionAuthorityRevisionLagInput,
    *,
    config: ResearchSourceResolutionAuthorityRevisionLagConfig,
) -> ResearchSourceResolutionAuthorityRevisionLagRow:
    source_revision_lag_pressure = _linear_pressure(
        item.source_revision_lag_seconds,
        capped_at=config.source_revision_block_lag_seconds,
    )
    authority_revision_lag_pressure = _linear_pressure(
        item.authority_revision_lag_seconds,
        capped_at=config.authority_revision_block_lag_seconds,
    )
    authority_gap = _quantize(_ONE - item.authority_score)
    revision_lag_pressure = _quantize(
        (source_revision_lag_pressure * config.source_revision_lag_weight)
        + (authority_revision_lag_pressure * config.authority_revision_lag_weight)
        + (authority_gap * config.authority_gap_weight)
        + (item.revision_conflict_score * config.revision_conflict_weight),
    )
    status = _row_status(revision_lag_pressure, config=config)
    return ResearchSourceResolutionAuthorityRevisionLagRow(
        public_case_key=item.public_case_key,
        source_revision_lag_seconds=item.source_revision_lag_seconds,
        source_revision_lag_pressure=source_revision_lag_pressure,
        source_revision_lag_band=_lag_band(
            item.source_revision_lag_seconds,
            watch_at=config.source_revision_watch_lag_seconds,
            block_at=config.source_revision_block_lag_seconds,
        ),
        authority_revision_lag_seconds=item.authority_revision_lag_seconds,
        authority_revision_lag_pressure=authority_revision_lag_pressure,
        authority_revision_lag_band=_lag_band(
            item.authority_revision_lag_seconds,
            watch_at=config.authority_revision_watch_lag_seconds,
            block_at=config.authority_revision_block_lag_seconds,
        ),
        authority_score=item.authority_score,
        authority_gap=authority_gap,
        revision_conflict_score=item.revision_conflict_score,
        revision_lag_pressure=revision_lag_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            source_revision_lag_seconds=item.source_revision_lag_seconds,
            authority_revision_lag_seconds=item.authority_revision_lag_seconds,
            authority_score=item.authority_score,
            revision_conflict_score=item.revision_conflict_score,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
        validation_config=config,
    )


def _normalize_lag_items(
    lag_items: Iterable[object],
) -> tuple[ResearchSourceResolutionAuthorityRevisionLagInput, ...]:
    if isinstance(lag_items, (str, bytes)):
        raise ValueError("lag_items must be an iterable")
    try:
        values = tuple(lag_items)
    except TypeError as exc:
        raise ValueError("lag_items must be an iterable") from exc
    normalized = tuple(_coerce_lag_item(value) for value in values)
    public_case_keys = tuple(item.public_case_key for item in normalized)
    if len(set(public_case_keys)) != len(public_case_keys):
        raise ValueError("duplicate public_case_key")
    return normalized


def _coerce_lag_item(value: object) -> ResearchSourceResolutionAuthorityRevisionLagInput:
    if type(value) is ResearchSourceResolutionAuthorityRevisionLagInput:
        _require_hard_flags("lag input", value)
        return value
    _require_hard_flags("lag input", value)
    return ResearchSourceResolutionAuthorityRevisionLagInput(
        public_case_key=_field_value(value, "public_case_key"),
        source_revision_lag_seconds=_field_value(value, "source_revision_lag_seconds"),
        authority_revision_lag_seconds=_field_value(
            value,
            "authority_revision_lag_seconds",
        ),
        authority_score=_field_value(value, "authority_score"),
        revision_conflict_score=_field_value(value, "revision_conflict_score"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _linear_pressure(value: Decimal, *, capped_at: Decimal) -> Decimal:
    if value >= capped_at:
        return _ONE
    return _quantize(value / capped_at)


def _lag_band(value: Decimal, *, watch_at: Decimal, block_at: Decimal) -> str:
    if value >= block_at:
        return "stale"
    if value >= watch_at:
        return "late"
    return "fresh"


def _row_status(
    revision_lag_pressure: Decimal,
    *,
    config: ResearchSourceResolutionAuthorityRevisionLagConfig,
) -> str:
    if revision_lag_pressure >= config.block_pressure_threshold:
        return "block"
    if revision_lag_pressure >= config.watch_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_revision_lag_seconds: Decimal,
    authority_revision_lag_seconds: Decimal,
    authority_score: Decimal,
    revision_conflict_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchSourceResolutionAuthorityRevisionLagConfig,
) -> tuple[str, ...]:
    codes: set[str] = {f"revision_lag_{status}"}
    if source_revision_lag_seconds >= config.source_revision_block_lag_seconds:
        codes.add("source_revision_lag_block")
    elif source_revision_lag_seconds >= config.source_revision_watch_lag_seconds:
        codes.add("source_revision_lag_watch")
    else:
        codes.add("source_revision_lag_fresh")
    if authority_revision_lag_seconds >= config.authority_revision_block_lag_seconds:
        codes.add("authority_revision_lag_block")
    elif authority_revision_lag_seconds >= config.authority_revision_watch_lag_seconds:
        codes.add("authority_revision_lag_watch")
    else:
        codes.add("authority_revision_lag_fresh")
    if authority_score <= config.authority_score_block_threshold:
        codes.add("authority_score_block")
    elif authority_score < config.authority_score_watch_threshold:
        codes.add("authority_score_watch")
    else:
        codes.add("authority_score_strong")
    if revision_conflict_score >= config.revision_conflict_block_threshold:
        codes.add("revision_conflict_block")
    elif revision_conflict_score >= config.revision_conflict_watch_threshold:
        codes.add("revision_conflict_watch")
    else:
        codes.add("revision_conflict_low")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_authority_revision_lag_items",)
    if all(row.status == "pass" for row in rows):
        return ("authority_revision_lag_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_revision_lag_pressure(
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.revision_lag_pressure for row in rows), _ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...],
) -> tuple[ResearchSourceResolutionAuthorityRevisionLagRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceResolutionAuthorityRevisionLagRow:
            raise ValueError(
                "rows must contain ResearchSourceResolutionAuthorityRevisionLagRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_case_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_case_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount, ...],
) -> tuple[ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_config(config: ResearchSourceResolutionAuthorityRevisionLagConfig) -> None:
    if config.source_revision_block_lag_seconds <= config.source_revision_watch_lag_seconds:
        raise ValueError(
            "source_revision_watch_lag_seconds must be below "
            "source_revision_block_lag_seconds",
        )
    if (
        config.authority_revision_block_lag_seconds
        <= config.authority_revision_watch_lag_seconds
    ):
        raise ValueError(
            "authority_revision_watch_lag_seconds must be below "
            "authority_revision_block_lag_seconds",
        )
    if config.authority_score_block_threshold >= config.authority_score_watch_threshold:
        raise ValueError(
            "authority_score_block_threshold must be below "
            "authority_score_watch_threshold",
        )
    if (
        config.revision_conflict_block_threshold
        <= config.revision_conflict_watch_threshold
    ):
        raise ValueError(
            "revision_conflict_block_threshold must exceed "
            "revision_conflict_watch_threshold",
        )
    if config.block_pressure_threshold <= config.watch_pressure_threshold:
        raise ValueError("block_pressure_threshold must exceed watch_pressure_threshold")
    weight_sum = _quantize(
        config.source_revision_lag_weight
        + config.authority_revision_lag_weight
        + config.authority_gap_weight
        + config.revision_conflict_weight,
    )
    if weight_sum != _ONE:
        raise ValueError(
            "source_revision_lag_weight, authority_revision_lag_weight, "
            "authority_gap_weight, and revision_conflict_weight must sum to 1",
        )


def _validate_row_consistency(
    row: ResearchSourceResolutionAuthorityRevisionLagRow,
    *,
    config: ResearchSourceResolutionAuthorityRevisionLagConfig,
) -> None:
    if row.authority_gap != _quantize(_ONE - row.authority_score):
        raise ValueError("authority_gap must match authority_score")
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"revision_lag_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    if row.status == "pass" and row.revision_lag_pressure >= config.watch_pressure_threshold:
        raise ValueError("revision_lag_pressure must match status")
    if row.status == "watch" and (
        row.revision_lag_pressure < config.watch_pressure_threshold
        or row.revision_lag_pressure >= config.block_pressure_threshold
    ):
        raise ValueError("revision_lag_pressure must match status")
    if row.status == "block" and row.revision_lag_pressure < config.block_pressure_threshold:
        raise ValueError("revision_lag_pressure must match status")


def _validate_report_consistency(
    report: ResearchSourceResolutionAuthorityRevisionLagReport,
) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_revision_lag_pressure != _average_revision_lag_pressure(report.rows):
        raise ValueError("average_revision_lag_pressure must match rows")
    expected_max_source_lag = max(
        (row.source_revision_lag_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_source_revision_lag_seconds != expected_max_source_lag:
        raise ValueError("max_source_revision_lag_seconds must match rows")
    expected_max_authority_lag = max(
        (row.authority_revision_lag_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_authority_revision_lag_seconds != expected_max_authority_lag:
        raise ValueError("max_authority_revision_lag_seconds must match rows")
    expected_lowest_authority_score = min(
        (row.authority_score for row in report.rows),
        default=_ZERO,
    )
    if report.lowest_authority_score != expected_lowest_authority_score:
        raise ValueError("lowest_authority_score must match rows")
    expected_highest_conflict_score = max(
        (row.revision_conflict_score for row in report.rows),
        default=_ZERO,
    )
    if report.highest_revision_conflict_score != expected_highest_conflict_score:
        raise ValueError("highest_revision_conflict_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchSourceResolutionAuthorityRevisionLagReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON value must use exact Decimal values")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        _reject_text_value("JSON string value", value)
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _field_value(value: object, name: str, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if any(field.name == name for field in fields(value)):
            return getattr(value, name)
    elif isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{name} is required")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_text_value(name, value)
    return value


def _require_public_case_key(name: str, value: str) -> str:
    _require_public_identifier(name, value)
    normalized = value.lower()
    if any(term in normalized for term in _PUBLIC_KEY_UNSAFE_TERMS):
        raise ValueError(f"{name} must not expose restricted identifiers")
    return value


def _require_reason_code(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase reason code")
    _reject_text_value(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be nonempty")
    normalized = tuple(_require_reason_code(name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(sorted(normalized))


def _require_status(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_lag_band(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in ("fresh", "late", "stale"):
        raise ValueError(f"{name} must be fresh, late, or stale")
    return value


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(result)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(result)


def _require_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_positive_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_probability_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO or result > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(result)


def _require_optional_probability_decimal(
    name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(name, value)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_text_value(f"{label} key", key)
            _reject_public_payload(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
    elif isinstance(value, str):
        _reject_text_value(label, value)


def _reject_text_value(name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _PAYLOAD_UNSAFE_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public payload text")
