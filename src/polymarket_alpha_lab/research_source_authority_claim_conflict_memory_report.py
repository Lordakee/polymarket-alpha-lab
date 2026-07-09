"""Pure report-only source-authority claim conflict memory summary.

Callers provide in-memory evidence rows. This module returns deterministic,
redacted public rows and a tamper-evident digest without touching external
systems.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchSourceAuthorityClaimConflictMemoryConfig",
    "ResearchSourceAuthorityClaimConflictMemoryInput",
    "ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount",
    "ResearchSourceAuthorityClaimConflictMemoryReport",
    "ResearchSourceAuthorityClaimConflictMemoryRow",
    "build_research_source_authority_claim_conflict_memory_report",
    "research_source_authority_claim_conflict_memory_report_digest",
    "research_source_authority_claim_conflict_memory_report_payload",
    "validate_research_source_authority_claim_conflict_memory_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-authority-claim-conflict-memory-report-v0"
STATUSES = ("pass", "watch", "block")
CLAIM_SIDES = ("support", "challenge")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate_ref",
    "market_ref",
    "source_reference",
    "source_excerpt",
    "claim_text",
    "dsn",
    "table",
    "token",
    "url",
    "raw",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "postgres://",
    "http://",
    "https://",
    "token=",
    "private_table",
    "raw-candidate",
    "raw-market",
    "raw claim",
    "raw source",
    "source text",
)


class _Missing:
    pass


_MISSING = _Missing()


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimConflictMemoryConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("86400.000000")
    stale_age_seconds: Decimal = Decimal("604800.000000")
    min_distinct_source_families: Decimal = Decimal("2")
    material_authority_score: Decimal = Decimal("0.650000")
    pass_authority_gap: Decimal = Decimal("0.250000")
    watch_conflict_memory_count: Decimal = Decimal("1")
    block_conflict_memory_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityClaimConflictMemoryConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        object.__setattr__(
            self,
            "min_distinct_source_families",
            _require_positive_count_decimal(
                "min_distinct_source_families",
                self.min_distinct_source_families,
            ),
        )
        for field_name in ("material_authority_score", "pass_authority_gap"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_memory_count",
            "block_conflict_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_conflict_memory_count < self.watch_conflict_memory_count:
            raise ValueError(
                "block_conflict_memory_count must be at least watch_conflict_memory_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimConflictMemoryInput(_FinalPublicDataclass):
    candidate_ref: str
    market_ref: str
    claim_text: str
    source_reference: str
    source_excerpt: str
    source_family: str
    claim_side: str
    authority_score: Decimal
    observed_at: datetime
    conflict_memory_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityClaimConflictMemoryInput,
            "input",
        )
        for field_name in (
            "candidate_ref",
            "market_ref",
            "claim_text",
            "source_reference",
            "source_excerpt",
            "source_family",
        ):
            _require_private_input_string(field_name, getattr(self, field_name))
        _require_enum("claim_side", self.claim_side, CLAIM_SIDES)
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "conflict_memory_count",
            _require_nonnegative_count_decimal(
                "conflict_memory_count",
                self.conflict_memory_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimConflictMemoryRow(_FinalPublicDataclass):
    claim_key: str
    source_count: Decimal
    distinct_source_family_count: Decimal
    support_source_count: Decimal
    challenge_source_count: Decimal
    authority_support_score: Decimal
    authority_challenge_score: Decimal
    authority_gap_abs: Decimal
    max_conflict_memory_count: Decimal
    latest_observed_at: datetime
    latest_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityClaimConflictMemoryRow,
            "row",
        )
        _require_public_string("claim_key", self.claim_key)
        for field_name in (
            "source_count",
            "distinct_source_family_count",
            "support_source_count",
            "challenge_source_count",
            "max_conflict_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_support_score",
            "authority_challenge_score",
            "authority_gap_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_age_seconds",
            _require_nonnegative_decimal("latest_age_seconds", self.latest_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimConflictMemoryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...]
    reason_code_counts: tuple[
        ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityClaimConflictMemoryReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
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
        _validate_report(self)
        _require_hard_flags("report", self)
        expected = _digest_public_payload(_unsigned_payload(self))
        if self.derived_validation_digest != expected:
            raise ValueError("derived_validation_digest must match report payload")


def build_research_source_authority_claim_conflict_memory_report(
    inputs: Iterable[object],
    *,
    config: ResearchSourceAuthorityClaimConflictMemoryConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityClaimConflictMemoryReport:
    if type(config) is not ResearchSourceAuthorityClaimConflictMemoryConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityClaimConflictMemoryConfig",
        )
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    for input_row in input_rows:
        if input_row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchSourceAuthorityClaimConflictMemoryInput]] = {}
    for input_row in input_rows:
        grouped.setdefault(_claim_group_key(input_row), []).append(input_row)

    rows = tuple(
        sorted(
            (
                _build_claim_row(
                    tuple(grouped[group_key]),
                    group_index=index,
                    config=config,
                    generated_at=report_time,
                )
                for index, group_key in enumerate(sorted(grouped), start=1)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    unsigned = {
        "generated_at": _public_value(report_time),
        "config_version": config.config_version,
        "claim_count": _public_value(_count(len(rows))),
        "pass_count": _public_value(_status_count(rows, "pass")),
        "watch_count": _public_value(_status_count(rows, "watch")),
        "block_count": _public_value(_status_count(rows, "block")),
        "status": _report_status(rows),
        "rows": _public_value(rows),
        "reason_code_counts": _public_value(_reason_code_counts(rows, reason_codes)),
        "reason_codes": _public_value(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceAuthorityClaimConflictMemoryReport(
        generated_at=report_time,
        config_version=config.config_version,
        claim_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
        derived_validation_digest=_digest_public_payload(unsigned),
    )


def research_source_authority_claim_conflict_memory_report_payload(
    report: ResearchSourceAuthorityClaimConflictMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityClaimConflictMemoryReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityClaimConflictMemoryReport",
        )
    _require_hard_flags("report", report)
    payload = _signed_payload(report)
    validate_research_source_authority_claim_conflict_memory_report_payload(payload)
    return payload


def research_source_authority_claim_conflict_memory_report_digest(
    report: ResearchSourceAuthorityClaimConflictMemoryReport,
) -> str:
    payload = research_source_authority_claim_conflict_memory_report_payload(report)
    return str(payload["derived_validation_digest"])


def validate_research_source_authority_claim_conflict_memory_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    expected = _digest_public_payload(unsigned)
    if digest != expected:
        raise ValueError("derived_validation_digest must match public payload")
    _validate_public_payload_shape(payload)
    return payload


def _build_claim_row(
    inputs: tuple[ResearchSourceAuthorityClaimConflictMemoryInput, ...],
    *,
    group_index: int,
    config: ResearchSourceAuthorityClaimConflictMemoryConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityClaimConflictMemoryRow:
    ordered_inputs = tuple(
        sorted(
            inputs,
            key=lambda item: (
                item.source_family,
                item.claim_side,
                item.authority_score,
                item.observed_at,
            ),
        ),
    )
    support_scores = tuple(
        item.authority_score for item in ordered_inputs if item.claim_side == "support"
    )
    challenge_scores = tuple(
        item.authority_score for item in ordered_inputs if item.claim_side == "challenge"
    )
    support_score = max(support_scores, default=ZERO).quantize(RATIO_QUANTUM)
    challenge_score = max(challenge_scores, default=ZERO).quantize(RATIO_QUANTUM)
    latest_observed_at = max(item.observed_at for item in ordered_inputs)
    max_conflict_count = max(
        item.conflict_memory_count for item in ordered_inputs
    ).quantize(COUNT_QUANTUM)
    family_count = _count(len({item.source_family for item in ordered_inputs}))
    source_count = _count(len(ordered_inputs))
    gap_abs = abs(support_score - challenge_score).quantize(RATIO_QUANTUM)
    status = _row_status(
        support_score=support_score,
        challenge_score=challenge_score,
        gap_abs=gap_abs,
        family_count=family_count,
        max_conflict_count=max_conflict_count,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        support_score=support_score,
        challenge_score=challenge_score,
        gap_abs=gap_abs,
        family_count=family_count,
        latest_age_seconds=_age_seconds(generated_at, latest_observed_at),
        max_conflict_count=max_conflict_count,
        config=config,
    )
    return ResearchSourceAuthorityClaimConflictMemoryRow(
        claim_key=f"claim-{group_index:06d}",
        source_count=source_count,
        distinct_source_family_count=family_count,
        support_source_count=_count(len(support_scores)),
        challenge_source_count=_count(len(challenge_scores)),
        authority_support_score=support_score,
        authority_challenge_score=challenge_score,
        authority_gap_abs=gap_abs,
        max_conflict_memory_count=max_conflict_count,
        latest_observed_at=latest_observed_at,
        latest_age_seconds=_age_seconds(generated_at, latest_observed_at),
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    support_score: Decimal,
    challenge_score: Decimal,
    gap_abs: Decimal,
    family_count: Decimal,
    max_conflict_count: Decimal,
    config: ResearchSourceAuthorityClaimConflictMemoryConfig,
) -> str:
    has_material_conflict = (
        support_score >= config.material_authority_score
        and challenge_score >= config.material_authority_score
        and gap_abs < config.pass_authority_gap
    )
    if max_conflict_count >= config.block_conflict_memory_count:
        return "block"
    if has_material_conflict:
        return "block"
    if max_conflict_count >= config.watch_conflict_memory_count:
        return "watch"
    if family_count < config.min_distinct_source_families:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    support_score: Decimal,
    challenge_score: Decimal,
    gap_abs: Decimal,
    family_count: Decimal,
    latest_age_seconds: Decimal,
    max_conflict_count: Decimal,
    config: ResearchSourceAuthorityClaimConflictMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if status == "pass":
        reason_codes.add("authority_clear_pass")
    if status == "watch":
        reason_codes.add("remembered_conflict_watch")
    if status == "block":
        reason_codes.add("authority_conflict_memory_block")
    if (
        support_score >= config.material_authority_score
        and challenge_score >= config.material_authority_score
        and gap_abs < config.pass_authority_gap
    ):
        reason_codes.add("material_authority_conflict")
    if max_conflict_count >= config.block_conflict_memory_count:
        reason_codes.add("remembered_conflict_block")
    elif max_conflict_count >= config.watch_conflict_memory_count:
        reason_codes.add("remembered_conflict_watch")
    if status != "block" and family_count >= config.min_distinct_source_families:
        reason_codes.add("distinct_source_families_met")
    elif status != "block":
        reason_codes.add("single_source_family_watch")
    if status == "pass" and latest_age_seconds <= config.fresh_age_seconds:
        reason_codes.add("fresh_authority_claim")
    elif status != "block" and latest_age_seconds >= config.stale_age_seconds:
        reason_codes.add("stale_authority_claim")
    return tuple(sorted(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("claim_conflict_memory_empty",)
    if any(row.status == "block" for row in rows):
        return tuple(
            sorted(
                {
                    code
                    for row in rows
                    if row.status == "block"
                    for code in row.reason_codes
                },
            ),
        )
    if any(row.status == "watch" for row in rows):
        return tuple(
            sorted(
                {
                    code
                    for row in rows
                    if row.status == "watch"
                    for code in row.reason_codes
                },
            ),
        )
    return ("authority_clear_pass",)


def _report_status(rows: tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchSourceAuthorityClaimConflictMemoryInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchSourceAuthorityClaimConflictMemoryInput:
    if type(value) is ResearchSourceAuthorityClaimConflictMemoryInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchSourceAuthorityClaimConflictMemoryInput(
        candidate_ref=_field_value(value, "candidate_ref"),
        market_ref=_field_value(value, "market_ref"),
        claim_text=_field_value(value, "claim_text"),
        source_reference=_field_value(value, "source_reference"),
        source_excerpt=_field_value(value, "source_excerpt"),
        source_family=_field_value(value, "source_family"),
        claim_side=_field_value(value, "claim_side"),
        authority_score=_field_value(value, "authority_score"),
        observed_at=_field_value(value, "observed_at"),
        conflict_memory_count=_field_value(value, "conflict_memory_count", default=ZERO),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _claim_group_key(item: ResearchSourceAuthorityClaimConflictMemoryInput) -> str:
    encoded = "|".join((item.candidate_ref, item.market_ref, item.claim_text))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_sort_key(row: ResearchSourceAuthorityClaimConflictMemoryRow) -> tuple[str, str]:
    return (row.status, row.claim_key)


def _status_count(
    rows: tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    rows: tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...],
) -> tuple[ResearchSourceAuthorityClaimConflictMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceAuthorityClaimConflictMemoryRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthorityClaimConflictMemoryRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount, ...],
) -> tuple[ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_row(row: ResearchSourceAuthorityClaimConflictMemoryRow) -> None:
    if row.source_count <= ZERO:
        raise ValueError("source_count must be positive")
    if row.distinct_source_family_count > row.source_count:
        raise ValueError("distinct_source_family_count must not exceed source_count")
    if row.support_source_count + row.challenge_source_count != row.source_count:
        raise ValueError("support_source_count and challenge_source_count must match")
    expected_gap = abs(
        row.authority_support_score - row.authority_challenge_score,
    ).quantize(RATIO_QUANTUM)
    if row.authority_gap_abs != expected_gap:
        raise ValueError("authority_gap_abs must match support and challenge scores")


def _validate_report(report: ResearchSourceAuthorityClaimConflictMemoryReport) -> None:
    if report.claim_count != _count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")
    status = payload.get("status")
    if status not in STATUSES:
        raise ValueError("status must be pass, watch, or block")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        if row.get("paper_only") is not True:
            raise ValueError("row paper_only must be True")
        if row.get("report_only") is not True:
            raise ValueError("row report_only must be True")
        if row.get("readonly") is not True:
            raise ValueError("row readonly must be True")
        if row.get("status") not in STATUSES:
            raise ValueError("row status must be pass, watch, or block")


def _unsigned_payload(
    report: ResearchSourceAuthorityClaimConflictMemoryReport,
) -> dict[str, Any]:
    payload = _public_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _signed_payload(report: ResearchSourceAuthorityClaimConflictMemoryReport) -> dict[str, Any]:
    payload = _public_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def _public_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _public_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_public_value(item) for item in value]
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _public_value(item) for key, item in value.items()}
    return value


def _digest_public_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            key_text = key.lower()
            if any(fragment in key_text for fragment in _unsafe_public_key_fragments()):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _unsafe_public_value_fragments()):
            raise ValueError("unsafe public payload value")
        return
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if type(value) is bool or value is None:
        return
    raise ValueError("public payload must contain JSON values")


def _unsafe_public_key_fragments() -> tuple[str, ...]:
    return UNSAFE_PUBLIC_KEY_FRAGMENTS + (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_text",
        "source_url",
        "question",
        "slug",
        "wal" + "let",
        "ord" + "er",
        "trad" + "e",
        "execut" + "ion",
    )


def _unsafe_public_value_fragments() -> tuple[str, ...]:
    return UNSAFE_PUBLIC_VALUE_FRAGMENTS + (
        "candidate_id",
        "candidate-",
        "market_id",
        "market-",
        "market_slug",
        "market slug",
        "market_question",
        "market question",
        "source_url",
        "source_text",
        "wal" + "let",
        "ord" + "er",
        "trad" + "e",
        "execut" + "ion",
    )


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    ).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value.quantize(RATIO_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(RATIO_QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(RATIO_QUANTUM)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_private_input_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _unsafe_public_value_fragments()):
        raise ValueError(f"{field_name} must be public safe")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")
