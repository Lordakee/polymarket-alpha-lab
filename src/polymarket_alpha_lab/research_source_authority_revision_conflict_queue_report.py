"""Pure report-only source authority revision-conflict queue report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_REVISION_CONFLICT_QUEUE_REPORT_CONFIG_VERSION = (
    "research-source-authority-revision-conflict-queue-report-v0"
)
STATUSES = ("pass", "watch", "block")

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_ZERO = Decimal("0.000000")
_PUBLIC_CASE_UNSAFE_TERMS = (
    "candidate",
    "market",
    "condition",
    "slug",
    "question",
    "url",
    "text",
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
_UNSAFE_PUBLIC_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "www.",
    "raw_" + "candidate",
    "candidate_" + "id",
    "condition_" + "id",
    "raw_" + "market",
    "market_" + "id",
    "market_" + "slug",
    "market_" + "question",
    "slug",
    "question",
    "source_" + "url",
    "source_" + "text",
    "raw_" + "source",
    "raw_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve_" + "trading",
    "recomm" + "endation",
    "siz" + "ing",
    "private_",
    "secret",
    "credential",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceAuthorityRevisionConflictQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_REVISION_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
    )
    revision_watch_age_seconds: Decimal = Decimal("3600.000000")
    revision_block_age_seconds: Decimal = Decimal("21600.000000")
    authority_score_watch_threshold: Decimal = Decimal("0.700000")
    authority_score_block_threshold: Decimal = Decimal("0.300000")
    revision_conflict_watch_threshold: Decimal = Decimal("0.300000")
    revision_conflict_block_threshold: Decimal = Decimal("0.700000")
    corroboration_gap_watch_threshold: Decimal = Decimal("0.500000")
    corroboration_gap_block_threshold: Decimal = Decimal("0.800000")
    watch_queue_pressure_score: Decimal = Decimal("0.250000")
    block_queue_pressure_score: Decimal = Decimal("0.700000")
    revision_age_weight: Decimal = Decimal("0.300000")
    authority_gap_weight: Decimal = Decimal("0.250000")
    revision_conflict_weight: Decimal = Decimal("0.300000")
    authority_corroboration_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuthorityRevisionConflictQueueConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityRevisionConflictQueueConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_REVISION_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "revision_watch_age_seconds",
            "revision_block_age_seconds",
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
            "corroboration_gap_watch_threshold",
            "corroboration_gap_block_threshold",
            "watch_queue_pressure_score",
            "block_queue_pressure_score",
            "revision_age_weight",
            "authority_gap_weight",
            "revision_conflict_weight",
            "authority_corroboration_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityRevisionConflictQueueInput:
    public_case_key: str
    authority_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    revision_observed_at: datetime
    authority_revision_observed_at: datetime
    authority_score: Decimal
    revision_conflict_score: Decimal
    corroborating_authority_count: Decimal
    required_authority_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuthorityRevisionConflictQueueInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityRevisionConflictQueueInput,
            "input",
        )
        _require_public_case_key("public_case_key", self.public_case_key)
        _require_public_identifier("authority_bucket", self.authority_bucket)
        _reject_unsafe_public_string("authority_bucket", self.authority_bucket)
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_reference",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "revision_observed_at",
            _as_utc("revision_observed_at", self.revision_observed_at),
        )
        object.__setattr__(
            self,
            "authority_revision_observed_at",
            _as_utc(
                "authority_revision_observed_at",
                self.authority_revision_observed_at,
            ),
        )
        for field_name in ("authority_score", "revision_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroborating_authority_count",
            _require_nonnegative_decimal(
                "corroborating_authority_count",
                self.corroborating_authority_count,
            ),
        )
        object.__setattr__(
            self,
            "required_authority_count",
            _require_positive_decimal(
                "required_authority_count",
                self.required_authority_count,
            ),
        )
        if self.corroborating_authority_count > self.required_authority_count:
            raise ValueError(
                "corroborating_authority_count must not exceed "
                "required_authority_count",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityRevisionConflictQueueRow:
    public_case_key: str
    authority_bucket: str
    revision_age_seconds: Decimal
    authority_revision_age_seconds: Decimal
    revision_age_pressure: Decimal
    revision_age_band: str
    authority_score: Decimal
    authority_gap_score: Decimal
    revision_conflict_score: Decimal
    corroborating_authority_count: Decimal
    required_authority_count: Decimal
    authority_corroboration_gap_score: Decimal
    conflict_queue_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuthorityRevisionConflictQueueRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityRevisionConflictQueueRow, "row")
        _require_public_case_key("public_case_key", self.public_case_key)
        _require_public_identifier("authority_bucket", self.authority_bucket)
        _reject_unsafe_public_string("authority_bucket", self.authority_bucket)
        for field_name in (
            "revision_age_seconds",
            "authority_revision_age_seconds",
            "corroborating_authority_count",
            "required_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_authority_count <= _ZERO:
            raise ValueError("required_authority_count must be positive")
        if self.corroborating_authority_count > self.required_authority_count:
            raise ValueError(
                "corroborating_authority_count must not exceed "
                "required_authority_count",
            )
        for field_name in (
            "revision_age_pressure",
            "authority_score",
            "authority_gap_score",
            "revision_conflict_score",
            "authority_corroboration_gap_score",
            "conflict_queue_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_revision_age_band("revision_age_band", self.revision_age_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityRevisionConflictQueueReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    stale_revision_count: Decimal
    low_authority_count: Decimal
    conflict_count: Decimal
    corroboration_gap_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_conflict_queue_pressure_score: Decimal
    max_conflict_queue_pressure_score: Decimal
    status: str
    rows: tuple[ResearchSourceAuthorityRevisionConflictQueueRow, ...]
    reason_code_counts: tuple[
        ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceAuthorityRevisionConflictQueueReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityRevisionConflictQueueReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_REVISION_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "stale_revision_count",
            "low_authority_count",
            "conflict_count",
            "corroboration_gap_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_conflict_queue_pressure_score",
            "max_conflict_queue_pressure_score",
        ):
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
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_source_authority_revision_conflict_queue_report(
    revision_items: Iterable[object],
    *,
    config: ResearchSourceAuthorityRevisionConflictQueueConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityRevisionConflictQueueReport:
    if type(config) is not ResearchSourceAuthorityRevisionConflictQueueConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityRevisionConflictQueueConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_revision_items(revision_items)
    for item in normalized_items:
        if item.revision_observed_at > generated_at_utc:
            raise ValueError("revision_observed_at must not be after generated_at")
        if item.authority_revision_observed_at > generated_at_utc:
            raise ValueError(
                "authority_revision_observed_at must not be after generated_at",
            )
    rows = _normalize_rows(
        tuple(
            _row_from_item(item, config=config, generated_at=generated_at_utc)
            for item in normalized_items
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "row_count": _decimal_count(len(rows)),
        "stale_revision_count": _decimal_count(_revision_age_count(rows)),
        "low_authority_count": _decimal_count(_authority_gap_count(rows)),
        "conflict_count": _decimal_count(_revision_conflict_count(rows)),
        "corroboration_gap_count": _decimal_count(_corroboration_gap_count(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_conflict_queue_pressure_score": _average(
            tuple(row.conflict_queue_pressure_score for row in rows),
        ),
        "max_conflict_queue_pressure_score": max(
            (row.conflict_queue_pressure_score for row in rows),
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
    return ResearchSourceAuthorityRevisionConflictQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_authority_revision_conflict_queue_report_payload(
    report: ResearchSourceAuthorityRevisionConflictQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceAuthorityRevisionConflictQueueReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError(
            "report must be a ResearchSourceAuthorityRevisionConflictQueueReport",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
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


def _row_from_item(
    item: ResearchSourceAuthorityRevisionConflictQueueInput,
    *,
    config: ResearchSourceAuthorityRevisionConflictQueueConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityRevisionConflictQueueRow:
    revision_age = _seconds_between(generated_at, item.revision_observed_at)
    authority_revision_age = _seconds_between(
        generated_at,
        item.authority_revision_observed_at,
    )
    revision_age_pressure = _linear_pressure(
        revision_age,
        capped_at=config.revision_block_age_seconds,
    )
    authority_gap = _clamp_probability(_ONE - item.authority_score)
    corroboration_gap = _clamp_probability(
        _ONE
        - _clamp_probability(
            item.corroborating_authority_count / item.required_authority_count,
        ),
    )
    pressure_score = _pressure_score(
        revision_age_pressure=revision_age_pressure,
        authority_gap_score=authority_gap,
        revision_conflict_score=item.revision_conflict_score,
        authority_corroboration_gap_score=corroboration_gap,
        config=config,
    )
    status = _row_status(
        revision_age_pressure=revision_age_pressure,
        authority_score=item.authority_score,
        revision_conflict_score=item.revision_conflict_score,
        authority_corroboration_gap_score=corroboration_gap,
        conflict_queue_pressure_score=pressure_score,
        config=config,
    )
    return ResearchSourceAuthorityRevisionConflictQueueRow(
        public_case_key=item.public_case_key,
        authority_bucket=item.authority_bucket,
        revision_age_seconds=revision_age,
        authority_revision_age_seconds=authority_revision_age,
        revision_age_pressure=revision_age_pressure,
        revision_age_band=_revision_age_band(
            revision_age,
            watch_at=config.revision_watch_age_seconds,
            block_at=config.revision_block_age_seconds,
        ),
        authority_score=item.authority_score,
        authority_gap_score=authority_gap,
        revision_conflict_score=item.revision_conflict_score,
        corroborating_authority_count=item.corroborating_authority_count,
        required_authority_count=item.required_authority_count,
        authority_corroboration_gap_score=corroboration_gap,
        conflict_queue_pressure_score=pressure_score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            revision_age=revision_age,
            authority_corroboration_gap_score=corroboration_gap,
            config=config,
        ),
    )


def _normalize_revision_items(
    revision_items: Iterable[object],
) -> tuple[ResearchSourceAuthorityRevisionConflictQueueInput, ...]:
    if isinstance(revision_items, (str, bytes)):
        raise ValueError("revision_items must be an iterable")
    try:
        values = tuple(revision_items)
    except TypeError as exc:
        raise ValueError("revision_items must be an iterable") from exc
    normalized = tuple(_coerce_revision_item(value) for value in values)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        key = (item.public_case_key, item.authority_bucket)
        if key in seen:
            raise ValueError("duplicate public_case_key and authority_bucket pair")
        seen.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.public_case_key, item.authority_bucket)))


def _coerce_revision_item(
    value: object,
) -> ResearchSourceAuthorityRevisionConflictQueueInput:
    if type(value) is ResearchSourceAuthorityRevisionConflictQueueInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchSourceAuthorityRevisionConflictQueueInput(
        public_case_key=_field_value(value, "public_case_key"),
        authority_bucket=_field_value(value, "authority_bucket"),
        private_candidate_reference=_field_value(value, "private_candidate_reference"),
        private_market_reference=_field_value(value, "private_market_reference"),
        private_source_reference=_field_value(value, "private_source_reference"),
        revision_observed_at=_field_value(value, "revision_observed_at"),
        authority_revision_observed_at=_field_value(
            value,
            "authority_revision_observed_at",
        ),
        authority_score=_field_value(value, "authority_score"),
        revision_conflict_score=_field_value(value, "revision_conflict_score"),
        corroborating_authority_count=_field_value(
            value,
            "corroborating_authority_count",
        ),
        required_authority_count=_field_value(value, "required_authority_count"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _linear_pressure(value: Decimal, *, capped_at: Decimal) -> Decimal:
    if value >= capped_at:
        return _ONE
    return _clamp_probability(value / capped_at)


def _revision_age_band(
    value: Decimal,
    *,
    watch_at: Decimal,
    block_at: Decimal,
) -> str:
    if value >= block_at:
        return "stale"
    if value >= watch_at:
        return "late"
    return "fresh"


def _pressure_score(
    *,
    revision_age_pressure: Decimal,
    authority_gap_score: Decimal,
    revision_conflict_score: Decimal,
    authority_corroboration_gap_score: Decimal,
    config: ResearchSourceAuthorityRevisionConflictQueueConfig,
) -> Decimal:
    return _clamp_probability(
        (revision_age_pressure * config.revision_age_weight)
        + (authority_gap_score * config.authority_gap_weight)
        + (revision_conflict_score * config.revision_conflict_weight)
        + (
            authority_corroboration_gap_score
            * config.authority_corroboration_gap_weight
        ),
    )


def _row_status(
    *,
    revision_age_pressure: Decimal,
    authority_score: Decimal,
    revision_conflict_score: Decimal,
    authority_corroboration_gap_score: Decimal,
    conflict_queue_pressure_score: Decimal,
    config: ResearchSourceAuthorityRevisionConflictQueueConfig,
) -> str:
    if (
        conflict_queue_pressure_score >= config.block_queue_pressure_score
        or revision_age_pressure == _ONE
        or authority_score <= config.authority_score_block_threshold
        or revision_conflict_score >= config.revision_conflict_block_threshold
        or authority_corroboration_gap_score >= config.corroboration_gap_block_threshold
    ):
        return "block"
    if (
        conflict_queue_pressure_score >= config.watch_queue_pressure_score
        or revision_age_pressure >= config.watch_queue_pressure_score
        or authority_score <= config.authority_score_watch_threshold
        or revision_conflict_score >= config.revision_conflict_watch_threshold
        or authority_corroboration_gap_score >= config.corroboration_gap_watch_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchSourceAuthorityRevisionConflictQueueInput,
    status: str,
    revision_age: Decimal,
    authority_corroboration_gap_score: Decimal,
    config: ResearchSourceAuthorityRevisionConflictQueueConfig,
) -> tuple[str, ...]:
    reason_codes = {f"authority_revision_conflict_queue_{status}"}
    if revision_age >= config.revision_block_age_seconds:
        reason_codes.add("revision_age_block")
    elif revision_age >= config.revision_watch_age_seconds:
        reason_codes.add("revision_age_watch")
    else:
        reason_codes.add("revision_age_fresh")
    if item.authority_score <= config.authority_score_block_threshold:
        reason_codes.add("authority_gap_block")
    elif item.authority_score <= config.authority_score_watch_threshold:
        reason_codes.add("authority_gap_watch")
    else:
        reason_codes.add("authority_gap_clear")
    if item.revision_conflict_score >= config.revision_conflict_block_threshold:
        reason_codes.add("revision_conflict_block")
    elif item.revision_conflict_score >= config.revision_conflict_watch_threshold:
        reason_codes.add("revision_conflict_watch")
    else:
        reason_codes.add("revision_conflict_clear")
    if authority_corroboration_gap_score >= config.corroboration_gap_block_threshold:
        reason_codes.add("authority_corroboration_block")
    elif authority_corroboration_gap_score >= config.corroboration_gap_watch_threshold:
        reason_codes.add("authority_corroboration_watch")
    else:
        reason_codes.add("authority_corroboration_clear")
    for reason_code in item.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_rows(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> tuple[ResearchSourceAuthorityRevisionConflictQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceAuthorityRevisionConflictQueueRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityRevisionConflictQueueRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthorityRevisionConflictQueueRow "
                "values",
            )
        _require_hard_flags("row", row)
        key = (row.public_case_key, row.authority_bucket)
        if key in seen:
            raise ValueError("duplicate row public_case_key and authority_bucket pair")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceAuthorityRevisionConflictQueueRow,
) -> tuple[Decimal, int, str, str]:
    return (
        -row.conflict_queue_pressure_score,
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.public_case_key,
        row.authority_bucket,
    )


def _normalize_reason_code_counts(
    counts: Sequence[ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount],
) -> tuple[ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        normalized.append(count)
    sorted_counts = tuple(sorted(normalized, key=lambda count: count.reason_code))
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return sorted_counts


def _report_reason_codes(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> tuple[str, ...]:
    if not rows:
        return ("authority_revision_conflict_queue_empty",)
    reason_codes = {f"authority_revision_conflict_queue_{_report_status(rows)}"}
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _revision_age_count(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> int:
    return sum(
        1
        for row in rows
        if "revision_age_watch" in row.reason_codes
        or "revision_age_block" in row.reason_codes
    )


def _authority_gap_count(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> int:
    return sum(
        1
        for row in rows
        if "authority_gap_watch" in row.reason_codes
        or "authority_gap_block" in row.reason_codes
    )


def _revision_conflict_count(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> int:
    return sum(
        1
        for row in rows
        if "revision_conflict_watch" in row.reason_codes
        or "revision_conflict_block" in row.reason_codes
    )


def _corroboration_gap_count(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> int:
    return sum(
        1
        for row in rows
        if "authority_corroboration_watch" in row.reason_codes
        or "authority_corroboration_block" in row.reason_codes
    )


def _report_status(
    rows: Sequence[ResearchSourceAuthorityRevisionConflictQueueRow],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _average(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _validate_config(
    config: ResearchSourceAuthorityRevisionConflictQueueConfig,
) -> None:
    if config.revision_block_age_seconds <= config.revision_watch_age_seconds:
        raise ValueError(
            "revision_watch_age_seconds must be below revision_block_age_seconds",
        )
    if config.authority_score_block_threshold >= config.authority_score_watch_threshold:
        raise ValueError(
            "authority_score_block_threshold must be below "
            "authority_score_watch_threshold",
        )
    if (
        config.revision_conflict_block_threshold
        < config.revision_conflict_watch_threshold
    ):
        raise ValueError(
            "revision_conflict_block_threshold must be at least "
            "revision_conflict_watch_threshold",
        )
    if (
        config.corroboration_gap_block_threshold
        < config.corroboration_gap_watch_threshold
    ):
        raise ValueError(
            "corroboration_gap_block_threshold must be at least "
            "corroboration_gap_watch_threshold",
        )
    if config.block_queue_pressure_score <= config.watch_queue_pressure_score:
        raise ValueError(
            "block_queue_pressure_score must exceed watch_queue_pressure_score",
        )
    weight_sum = _quantize(
        config.revision_age_weight
        + config.authority_gap_weight
        + config.revision_conflict_weight
        + config.authority_corroboration_gap_weight,
    )
    if weight_sum != _ONE:
        raise ValueError(
            "revision_age_weight, authority_gap_weight, revision_conflict_weight, "
            "and authority_corroboration_gap_weight must sum to 1",
        )


def _validate_row_consistency(
    row: ResearchSourceAuthorityRevisionConflictQueueRow,
) -> None:
    if row.authority_gap_score != _quantize(_ONE - row.authority_score):
        raise ValueError("authority_gap_score must match authority_score")
    expected_corroboration_gap = _clamp_probability(
        _ONE
        - _clamp_probability(
            row.corroborating_authority_count / row.required_authority_count,
        ),
    )
    if row.authority_corroboration_gap_score != expected_corroboration_gap:
        raise ValueError(
            "authority_corroboration_gap_score must match authority counts",
        )
    if f"authority_revision_conflict_queue_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    expected_pressure = _pressure_score_from_row(row)
    if row.conflict_queue_pressure_score != expected_pressure:
        raise ValueError("conflict_queue_pressure_score must match component scores")


def _pressure_score_from_row(
    row: ResearchSourceAuthorityRevisionConflictQueueRow,
) -> Decimal:
    return _clamp_probability(
        (row.revision_age_pressure * Decimal("0.300000"))
        + (row.authority_gap_score * Decimal("0.250000"))
        + (row.revision_conflict_score * Decimal("0.300000"))
        + (row.authority_corroboration_gap_score * Decimal("0.150000")),
    )


def _validate_report_consistency(
    report: ResearchSourceAuthorityRevisionConflictQueueReport,
) -> None:
    rows = report.rows
    expected_counts = {
        "row_count": _decimal_count(len(rows)),
        "stale_revision_count": _decimal_count(_revision_age_count(rows)),
        "low_authority_count": _decimal_count(_authority_gap_count(rows)),
        "conflict_count": _decimal_count(_revision_conflict_count(rows)),
        "corroboration_gap_count": _decimal_count(_corroboration_gap_count(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_conflict_queue_pressure_score != _average(
        tuple(row.conflict_queue_pressure_score for row in rows),
    ):
        raise ValueError("average_conflict_queue_pressure_score must match rows")
    if report.max_conflict_queue_pressure_score != max(
        (row.conflict_queue_pressure_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_conflict_queue_pressure_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchSourceAuthorityRevisionConflictQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    digest = payload["derived_validation_digest"]
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected = _report_digest_from_values(unsigned_payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _json_ready(value: Any) -> Any:
    if type(value) is bool or value is None:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal subclasses are not supported")
        return _quantize(value).to_eng_string()
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) is str:
        _reject_unsafe_public_string("JSON string value", value)
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    raise ValueError(f"unsupported JSON payload value {type(value).__name__}")


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


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_public_case_key(field_name: str, value: object) -> str:
    result = _require_public_identifier(field_name, value)
    lowered = result.lower()
    if any(term in lowered for term in _PUBLIC_CASE_UNSAFE_TERMS):
        raise ValueError(f"{field_name} must not expose restricted identifiers")
    return result


def _require_nonempty_text(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be nonempty text")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase reason code")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        normalized_code = _require_reason_code(field_name, reason_code)
        if normalized_code not in seen:
            normalized.append(normalized_code)
            seen.add(normalized_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_revision_age_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "late", "stale"):
        raise ValueError(f"{field_name} must be one of fresh/late/stale")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _hard_flag_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _hard_flag_value(value: object, field_name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(field_name)
    return getattr(value, field_name, None)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_string(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, str):
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    raise ValueError(f"{label} contains unsupported public value")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_REVISION_CONFLICT_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchSourceAuthorityRevisionConflictQueueConfig",
    "ResearchSourceAuthorityRevisionConflictQueueInput",
    "ResearchSourceAuthorityRevisionConflictQueueReasonCodeCount",
    "ResearchSourceAuthorityRevisionConflictQueueReport",
    "ResearchSourceAuthorityRevisionConflictQueueRow",
    "STATUSES",
    "build_research_source_authority_revision_conflict_queue_report",
    "research_source_authority_revision_conflict_queue_report_payload",
)
