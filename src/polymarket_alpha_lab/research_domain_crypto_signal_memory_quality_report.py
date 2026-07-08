"""Pure report-only crypto signal memory quality report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_CRYPTO_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "ResearchDomainCryptoSignalMemoryQualityConfig",
    "ResearchDomainCryptoSignalMemoryQualityInput",
    "ResearchDomainCryptoSignalMemoryQualityReasonCodeCount",
    "ResearchDomainCryptoSignalMemoryQualityReport",
    "ResearchDomainCryptoSignalMemoryQualityRow",
    "build_research_domain_crypto_signal_memory_quality_report",
    "research_domain_crypto_signal_memory_quality_report_payload",
)


DEFAULT_RESEARCH_DOMAIN_CRYPTO_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-crypto-signal-memory-quality-report-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0"),
    STATUS_WATCH: Decimal("1"),
    STATUS_PASS: Decimal("2"),
}
PAPER_ACTION_BY_STATUS = {
    STATUS_PASS: "paper_crypto_memory_handoff_pass",
    STATUS_WATCH: "paper_crypto_memory_handoff_watch",
    STATUS_BLOCK: "paper_crypto_memory_handoff_block",
}

EMPTY_REPORT_REASON_CODE = "crypto_memory_quality_no_memory_sets"
PASS_ROW_REASON_CODE = "crypto_memory_quality_clear"
REPORT_REASON_BY_STATUS = {
    STATUS_PASS: "crypto_memory_quality_report_pass",
    STATUS_WATCH: "crypto_memory_quality_report_watch",
    STATUS_BLOCK: "crypto_memory_quality_report_block",
}
BLOCK_REASON_CODES = (
    "missing_memory_inputs_block",
    "stale_memory_inputs_block",
    "conflicting_memory_inputs_block",
    "memory_age_block",
    "memory_quality_block",
)
WATCH_REASON_CODES = (
    "missing_memory_inputs_watch",
    "stale_memory_inputs_watch",
    "conflicting_memory_inputs_watch",
    "memory_age_watch",
    "memory_quality_watch",
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PRIORITY = BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODES = (
    EMPTY_REPORT_REASON_CODE,
    PASS_ROW_REASON_CODE,
    *REPORT_REASON_BY_STATUS.values(),
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
HEX_CHARS = frozenset("0123456789abcdef")
SAFE_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "can" + "didate",
        "mar" + "ket",
        "slu" + "g",
        "ques" + "tion",
        "ur" + "l",
        "sou" + "rce",
        "ds" + "n",
        "tab" + "le",
        "tok" + "en",
        "wa" + "llet",
        "ord" + "er",
        "tra" + "de",
        "data" + "base",
        "net" + "work",
        "au" + "th",
        "li" + "ve",
        "siz" + "ing",
        "recom" + "mendation",
        "http",
        "www.",
        "raw",
        "quote",
        "excerpt",
        "transcript",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchDomainCryptoSignalMemoryQualityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_CRYPTO_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    watch_missing_memory_input_count: Decimal = Decimal("1")
    block_missing_memory_input_count: Decimal = Decimal("2")
    watch_stale_memory_input_count: Decimal = Decimal("1")
    block_stale_memory_input_count: Decimal = Decimal("2")
    watch_conflicting_memory_input_count: Decimal = Decimal("1")
    block_conflicting_memory_input_count: Decimal = Decimal("2")
    watch_memory_age_seconds: Decimal = Decimal("21600.000000")
    block_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_min_quality_score: Decimal = Decimal("0.850000")
    block_min_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCryptoSignalMemoryQualityConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "watch_missing_memory_input_count",
            "block_missing_memory_input_count",
            "watch_stale_memory_input_count",
            "block_stale_memory_input_count",
            "watch_conflicting_memory_input_count",
            "block_conflicting_memory_input_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_memory_age_seconds", "block_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_min_quality_score", "block_min_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainCryptoSignalMemoryQualityInput(_FinalPublicDataclass):
    domain_label: str
    catalyst_family: str
    memory_bucket: str
    latest_refresh_at: datetime
    expected_memory_input_count: Decimal
    available_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCryptoSignalMemoryQualityInput,
            "input",
        )
        for field_name in ("domain_label", "catalyst_family", "memory_bucket"):
            _require_safe_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_refresh_at",
            _as_utc("latest_refresh_at", self.latest_refresh_at),
        )
        for field_name in (
            "expected_memory_input_count",
            "available_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainCryptoSignalMemoryQualityRow(_FinalPublicDataclass):
    domain_label: str
    catalyst_family: str
    memory_bucket: str
    latest_refresh_at: datetime
    expected_memory_input_count: Decimal
    available_memory_input_count: Decimal
    missing_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    memory_age_seconds: Decimal
    completeness_ratio: Decimal
    freshness_score: Decimal
    quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainCryptoSignalMemoryQualityRow, "row")
        for field_name in ("domain_label", "catalyst_family", "memory_bucket"):
            _require_safe_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_refresh_at",
            _as_utc("latest_refresh_at", self.latest_refresh_at),
        )
        for field_name in (
            "expected_memory_input_count",
            "available_memory_input_count",
            "missing_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in ("completeness_ratio", "freshness_score", "quality_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainCryptoSignalMemoryQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainCryptoSignalMemoryQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainCryptoSignalMemoryQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    handoff_at: datetime
    config_version: str
    memory_set_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_memory_input_total: Decimal
    stale_memory_input_total: Decimal
    conflicting_memory_input_total: Decimal
    max_memory_age_seconds: Decimal
    min_quality_score: Decimal
    status: str
    paper_handoff_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchDomainCryptoSignalMemoryQualityReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainCryptoSignalMemoryQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "handoff_at", _as_utc("handoff_at", self.handoff_at))
        _require_config_version(self.config_version)
        for field_name in (
            "memory_set_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_memory_input_total",
            "stale_memory_input_total",
            "conflicting_memory_input_total",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_quality_score",
            _require_ratio_decimal("min_quality_score", self.min_quality_score),
        )
        _require_status("status", self.status)
        _require_public_string("paper_handoff_action", self.paper_handoff_action)
        if self.paper_handoff_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_handoff_action must match status")
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
        digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != digest:
                raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", _json_ready(self))


def build_research_domain_crypto_signal_memory_quality_report(
    memory_inputs: Iterable[ResearchDomainCryptoSignalMemoryQualityInput],
    *,
    config: ResearchDomainCryptoSignalMemoryQualityConfig,
    generated_at: datetime,
    handoff_at: datetime,
) -> ResearchDomainCryptoSignalMemoryQualityReport:
    if type(config) is not ResearchDomainCryptoSignalMemoryQualityConfig:
        raise ValueError("config must be a ResearchDomainCryptoSignalMemoryQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    handoff_at_utc = _as_utc("handoff_at", handoff_at)
    if handoff_at_utc > generated_at_utc:
        raise ValueError("handoff_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    handoff_at=handoff_at_utc,
                )
                for item in _normalize_inputs(memory_inputs)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(reason_codes)
    return ResearchDomainCryptoSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        handoff_at=handoff_at_utc,
        config_version=config.config_version,
        memory_set_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        missing_memory_input_total=_sum_counts(
            tuple(row.missing_memory_input_count for row in rows),
        ),
        stale_memory_input_total=_sum_counts(
            tuple(row.stale_memory_input_count for row in rows),
        ),
        conflicting_memory_input_total=_sum_counts(
            tuple(row.conflicting_memory_input_count for row in rows),
        ),
        max_memory_age_seconds=_max_decimal(tuple(row.memory_age_seconds for row in rows)),
        min_quality_score=_min_quality_score(rows),
        status=status,
        paper_handoff_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_domain_crypto_signal_memory_quality_report_payload(
    report: ResearchDomainCryptoSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainCryptoSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        if "derived_validation_digest" not in payload:
            raise ValueError("derived_validation_digest is required")
        supplied_digest = payload["derived_validation_digest"]
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchDomainCryptoSignalMemoryQualityReport")


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _normalize_inputs(
    memory_inputs: Iterable[ResearchDomainCryptoSignalMemoryQualityInput],
) -> tuple[ResearchDomainCryptoSignalMemoryQualityInput, ...]:
    if isinstance(memory_inputs, (str, bytes)):
        raise ValueError("memory_inputs must be an iterable")
    try:
        items = tuple(memory_inputs)
    except TypeError as exc:
        raise ValueError("memory_inputs must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if type(item) is not ResearchDomainCryptoSignalMemoryQualityInput:
            raise ValueError(
                "memory_inputs must contain ResearchDomainCryptoSignalMemoryQualityInput",
            )
        _require_hard_flags("input", item)
        key = (item.domain_label, item.catalyst_family, item.memory_bucket)
        if key in seen:
            raise ValueError("memory_inputs must contain unique memory buckets")
        seen.add(key)
    return items


def _row_from_input(
    item: ResearchDomainCryptoSignalMemoryQualityInput,
    *,
    config: ResearchDomainCryptoSignalMemoryQualityConfig,
    handoff_at: datetime,
) -> ResearchDomainCryptoSignalMemoryQualityRow:
    if item.latest_refresh_at > handoff_at:
        raise ValueError("latest_refresh_at must not be in the future")
    memory_age_seconds = _age_seconds(handoff_at, item.latest_refresh_at)
    completeness_ratio = _completeness_ratio(item)
    freshness_score = _freshness_score(memory_age_seconds, config)
    quality_score = min(completeness_ratio, freshness_score)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        memory_age_seconds=memory_age_seconds,
        quality_score=quality_score,
    )
    return ResearchDomainCryptoSignalMemoryQualityRow(
        domain_label=item.domain_label,
        catalyst_family=item.catalyst_family,
        memory_bucket=item.memory_bucket,
        latest_refresh_at=item.latest_refresh_at,
        expected_memory_input_count=item.expected_memory_input_count,
        available_memory_input_count=item.available_memory_input_count,
        missing_memory_input_count=(
            item.expected_memory_input_count - item.available_memory_input_count
        ).quantize(COUNT_QUANTUM),
        stale_memory_input_count=item.stale_memory_input_count,
        conflicting_memory_input_count=item.conflicting_memory_input_count,
        memory_age_seconds=memory_age_seconds,
        completeness_ratio=completeness_ratio,
        freshness_score=freshness_score,
        quality_score=quality_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _completeness_ratio(
    item: ResearchDomainCryptoSignalMemoryQualityInput,
) -> Decimal:
    if item.expected_memory_input_count == ZERO_COUNT:
        return ONE_RATIO
    return _ratio(
        item.available_memory_input_count,
        item.expected_memory_input_count,
    )


def _freshness_score(
    memory_age_seconds: Decimal,
    config: ResearchDomainCryptoSignalMemoryQualityConfig,
) -> Decimal:
    if memory_age_seconds >= config.block_memory_age_seconds:
        return ZERO_RATIO
    return ONE_RATIO - _ratio(memory_age_seconds, config.block_memory_age_seconds)


def _row_reason_codes(
    item: ResearchDomainCryptoSignalMemoryQualityInput,
    *,
    config: ResearchDomainCryptoSignalMemoryQualityConfig,
    memory_age_seconds: Decimal,
    quality_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    missing_count = item.expected_memory_input_count - item.available_memory_input_count
    if missing_count >= config.block_missing_memory_input_count:
        reason_codes.append("missing_memory_inputs_block")
    elif missing_count >= config.watch_missing_memory_input_count:
        reason_codes.append("missing_memory_inputs_watch")

    if item.stale_memory_input_count >= config.block_stale_memory_input_count:
        reason_codes.append("stale_memory_inputs_block")
    elif item.stale_memory_input_count >= config.watch_stale_memory_input_count:
        reason_codes.append("stale_memory_inputs_watch")

    if item.conflicting_memory_input_count >= config.block_conflicting_memory_input_count:
        reason_codes.append("conflicting_memory_inputs_block")
    elif item.conflicting_memory_input_count >= config.watch_conflicting_memory_input_count:
        reason_codes.append("conflicting_memory_inputs_watch")

    if memory_age_seconds >= config.block_memory_age_seconds:
        reason_codes.append("memory_age_block")
    elif memory_age_seconds >= config.watch_memory_age_seconds:
        reason_codes.append("memory_age_watch")

    if quality_score < config.block_min_quality_score:
        reason_codes.append("memory_quality_block")
    elif quality_score < config.watch_min_quality_score:
        reason_codes.append("memory_quality_watch")

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _status_from_rows(rows)
    reason_codes = [REPORT_REASON_BY_STATUS[status]]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return STATUS_BLOCK
    if REPORT_REASON_BY_STATUS[STATUS_BLOCK] in reason_codes:
        return STATUS_BLOCK
    if REPORT_REASON_BY_STATUS[STATUS_WATCH] in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_rows(
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchDomainCryptoSignalMemoryQualityReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return (
            ResearchDomainCryptoSignalMemoryQualityReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    counter.update((REPORT_REASON_BY_STATUS[_status_from_rows(rows)],))
    return tuple(
        ResearchDomainCryptoSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in sorted(reason_codes)
    )


def _row_sort_key(
    row: ResearchDomainCryptoSignalMemoryQualityRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -_row_severity_score(row),
        row.domain_label,
        row.catalyst_family,
        row.memory_bucket,
    )


def _row_severity_score(row: ResearchDomainCryptoSignalMemoryQualityRow) -> Decimal:
    return _quantize_ratio(
        (ONE_RATIO - row.quality_score)
        + _ratio_capped(row.missing_memory_input_count, Decimal("10"))
        + _ratio_capped(row.stale_memory_input_count, Decimal("10"))
        + _ratio_capped(row.conflicting_memory_input_count, Decimal("10"))
        + _ratio_capped(row.memory_age_seconds, Decimal("172800.000000")),
    )


def _status_count(
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _min_quality_score(
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(row.quality_score for row in rows)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values)


def _validate_config(config: ResearchDomainCryptoSignalMemoryQualityConfig) -> None:
    if config.block_missing_memory_input_count < config.watch_missing_memory_input_count:
        raise ValueError(
            "block_missing_memory_input_count must be at least "
            "watch_missing_memory_input_count",
        )
    if config.block_stale_memory_input_count < config.watch_stale_memory_input_count:
        raise ValueError(
            "block_stale_memory_input_count must be at least "
            "watch_stale_memory_input_count",
        )
    if (
        config.block_conflicting_memory_input_count
        < config.watch_conflicting_memory_input_count
    ):
        raise ValueError(
            "block_conflicting_memory_input_count must be at least "
            "watch_conflicting_memory_input_count",
        )
    if config.block_memory_age_seconds < config.watch_memory_age_seconds:
        raise ValueError(
            "block_memory_age_seconds must be at least watch_memory_age_seconds",
        )
    if config.watch_min_quality_score <= config.block_min_quality_score:
        raise ValueError("watch_min_quality_score must exceed block_min_quality_score")


def _validate_input(item: ResearchDomainCryptoSignalMemoryQualityInput) -> None:
    if item.available_memory_input_count > item.expected_memory_input_count:
        raise ValueError(
            "available_memory_input_count must not exceed expected_memory_input_count",
        )
    if item.stale_memory_input_count > item.expected_memory_input_count:
        raise ValueError(
            "stale_memory_input_count must not exceed expected_memory_input_count",
        )
    if item.conflicting_memory_input_count > item.expected_memory_input_count:
        raise ValueError(
            "conflicting_memory_input_count must not exceed expected_memory_input_count",
        )


def _validate_row(row: ResearchDomainCryptoSignalMemoryQualityRow) -> None:
    if row.missing_memory_input_count != (
        row.expected_memory_input_count - row.available_memory_input_count
    ).quantize(COUNT_QUANTUM):
        raise ValueError("missing_memory_input_count must match row counts")
    if row.completeness_ratio != (
        ONE_RATIO
        if row.expected_memory_input_count == ZERO_COUNT
        else _ratio(row.available_memory_input_count, row.expected_memory_input_count)
    ):
        raise ValueError("completeness_ratio must match row counts")
    if row.quality_score != min(row.completeness_ratio, row.freshness_score):
        raise ValueError("quality_score must match row scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require crypto_memory_quality_clear")
    if row.status != STATUS_PASS and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("non-pass rows must not contain clear reason_codes")


def _validate_report_materialized_fields(
    report: ResearchDomainCryptoSignalMemoryQualityReport,
) -> None:
    rows = report.rows
    checks = {
        "memory_set_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "missing_memory_input_total": _sum_counts(
            tuple(row.missing_memory_input_count for row in rows),
        ),
        "stale_memory_input_total": _sum_counts(
            tuple(row.stale_memory_input_count for row in rows),
        ),
        "conflicting_memory_input_total": _sum_counts(
            tuple(row.conflicting_memory_input_count for row in rows),
        ),
        "max_memory_age_seconds": _max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        "min_quality_score": _min_quality_score(rows),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.paper_handoff_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_handoff_action must match status")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainCryptoSignalMemoryQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDomainCryptoSignalMemoryQualityRow:
            raise ValueError("rows must contain ResearchDomainCryptoSignalMemoryQualityRow")
        _require_hard_flags("row", row)
        key = (row.domain_label, row.catalyst_family, row.memory_bucket)
        if key in seen:
            raise ValueError("rows must contain unique memory buckets")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _require_reason_code_counts(
    counts: tuple[ResearchDomainCryptoSignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainCryptoSignalMemoryQualityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchDomainCryptoSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainCryptoSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    if len({count.reason_code for count in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    if normalized != tuple(sorted(normalized, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_config_version(value: object) -> None:
    if (
        type(value) is not str
        or value
        != DEFAULT_RESEARCH_DOMAIN_CRYPTO_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _require_safe_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if any(character not in SAFE_LABEL_CHARS for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(reason_codes, require_nonempty=True)
    if normalized == (EMPTY_REPORT_REASON_CODE,):
        return normalized
    if normalized[0] not in tuple(REPORT_REASON_BY_STATUS.values()):
        raise ValueError("reason_codes must start with a report status reason")
    for reason_code in normalized[1:]:
        if reason_code not in REPORT_REASON_PRIORITY:
            raise ValueError("reason_code must be supported")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize_ratio(
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000"),
    )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("value must be quantizable") from exc


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_COUNT)
    return total.quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE_RATIO:
        return ONE_RATIO
    return value


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _unsigned_payload(
    report: ResearchDomainCryptoSignalMemoryQualityReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return unsigned


def _derived_validation_digest(
    report: ResearchDomainCryptoSignalMemoryQualityReport,
) -> str:
    return _payload_validation_digest(_unsigned_payload(report))


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
    elif type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")
