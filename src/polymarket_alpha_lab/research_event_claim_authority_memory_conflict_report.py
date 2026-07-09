"""Pure report-only event-claim authority memory conflict summary.

Callers provide in-memory observations. This module returns deterministic,
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
    "DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION",
    "EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES",
    "ResearchEventClaimAuthorityMemoryConflictConfig",
    "ResearchEventClaimAuthorityMemoryConflictObservation",
    "ResearchEventClaimAuthorityMemoryConflictReasonCodeCount",
    "ResearchEventClaimAuthorityMemoryConflictReport",
    "ResearchEventClaimAuthorityMemoryConflictRow",
    "build_research_event_claim_authority_memory_conflict_report",
    "research_event_claim_authority_memory_conflict_report_digest",
    "research_event_claim_authority_memory_conflict_report_payload",
    "validate_research_event_claim_authority_memory_conflict_report_payload",
)


DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION = (
    "research-event-claim-authority-memory-conflict-report-v0"
)
EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES = ("pass", "watch", "block")
CLAIM_SIDES = ("support", "challenge")
ZERO = Decimal("0")
ONE = Decimal("1")
NUMERIC_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "raw",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "candidate-",
    "market-",
    "postgres://",
    "http://",
    "https://",
    "token=",
    "private_table",
    "raw claim",
    "raw evidence",
    "raw memory",
    "wall" "et",
    "or" "der",
    "tra" "de",
    "au" "th_",
    "au" "th:",
    "au" "th=",
)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "claim_count",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
PUBLIC_ROW_KEYS = frozenset(
    {
        "claim_key",
        "evidence_count",
        "distinct_family_count",
        "support_count",
        "challenge_count",
        "support_authority_score",
        "challenge_authority_score",
        "authority_margin_abs",
        "max_memory_conflict_count",
        "latest_observed_at",
        "latest_age_seconds",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    },
)
PUBLIC_REASON_CODE_COUNT_KEYS = frozenset(
    {
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    },
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
class ResearchEventClaimAuthorityMemoryConflictConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION
    )
    fresh_claim_age_seconds: Decimal = Decimal("86400.000000")
    stale_claim_age_seconds: Decimal = Decimal("604800.000000")
    min_family_quorum_count: Decimal = Decimal("2.000000")
    material_authority_score: Decimal = Decimal("0.650000")
    pass_authority_margin: Decimal = Decimal("0.250000")
    watch_memory_conflict_count: Decimal = Decimal("1.000000")
    block_memory_conflict_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventClaimAuthorityMemoryConflictConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_claim_age_seconds", "stale_claim_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_claim_age_seconds <= self.fresh_claim_age_seconds:
            raise ValueError(
                "stale_claim_age_seconds must be greater than fresh_claim_age_seconds",
            )
        object.__setattr__(
            self,
            "min_family_quorum_count",
            _require_positive_count_decimal(
                "min_family_quorum_count",
                self.min_family_quorum_count,
            ),
        )
        for field_name in ("material_authority_score", "pass_authority_margin"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_memory_conflict_count",
            "block_memory_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_memory_conflict_count < self.watch_memory_conflict_count:
            raise ValueError(
                "block_memory_conflict_count must be at least watch_memory_conflict_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventClaimAuthorityMemoryConflictObservation(_FinalPublicDataclass):
    event_ref: str
    candidate_ref: str
    market_ref: str
    claim_text: str
    source_ref: str
    source_detail: str
    source_family: str
    claim_side: str
    authority_score: Decimal
    observed_at: datetime
    memory_conflict_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventClaimAuthorityMemoryConflictObservation,
            "observation",
        )
        for field_name in (
            "event_ref",
            "candidate_ref",
            "market_ref",
            "claim_text",
            "source_ref",
            "source_detail",
            "source_family",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        _require_enum("claim_side", self.claim_side, CLAIM_SIDES)
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_conflict_count",
            _require_nonnegative_count_decimal(
                "memory_conflict_count",
                self.memory_conflict_count,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventClaimAuthorityMemoryConflictRow(_FinalPublicDataclass):
    claim_key: str
    evidence_count: Decimal
    distinct_family_count: Decimal
    support_count: Decimal
    challenge_count: Decimal
    support_authority_score: Decimal
    challenge_authority_score: Decimal
    authority_margin_abs: Decimal
    max_memory_conflict_count: Decimal
    latest_observed_at: datetime
    latest_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventClaimAuthorityMemoryConflictRow, "row")
        _require_public_string("claim_key", self.claim_key)
        for field_name in (
            "evidence_count",
            "distinct_family_count",
            "support_count",
            "challenge_count",
            "max_memory_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "support_authority_score",
            "challenge_authority_score",
            "authority_margin_abs",
            "latest_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.authority_margin_abs > ONE:
            raise ValueError("authority_margin_abs must not exceed one")
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
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
class ResearchEventClaimAuthorityMemoryConflictReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventClaimAuthorityMemoryConflictReasonCodeCount,
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
class ResearchEventClaimAuthorityMemoryConflictReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...]
    reason_code_counts: tuple[
        ResearchEventClaimAuthorityMemoryConflictReasonCodeCount,
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
            ResearchEventClaimAuthorityMemoryConflictReport,
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


def build_research_event_claim_authority_memory_conflict_report(
    observations: Iterable[object],
    *,
    config: ResearchEventClaimAuthorityMemoryConflictConfig,
    generated_at: datetime,
) -> ResearchEventClaimAuthorityMemoryConflictReport:
    if type(config) is not ResearchEventClaimAuthorityMemoryConflictConfig:
        raise ValueError(
            "config must be a ResearchEventClaimAuthorityMemoryConflictConfig",
        )
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations)
    for value in values:
        if value.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchEventClaimAuthorityMemoryConflictObservation]] = {}
    for value in values:
        grouped.setdefault(_claim_group_key(value), []).append(value)

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
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    unsigned = {
        "generated_at": _public_value(report_time),
        "config_version": config.config_version,
        "claim_count": _public_value(_count(len(rows))),
        "pass_count": _public_value(_status_count(rows, "pass")),
        "watch_count": _public_value(_status_count(rows, "watch")),
        "block_count": _public_value(_status_count(rows, "block")),
        "status": _report_status(rows),
        "rows": _public_value(rows),
        "reason_code_counts": _public_value(reason_code_counts),
        "reason_codes": _public_value(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventClaimAuthorityMemoryConflictReport(
        generated_at=report_time,
        config_version=config.config_version,
        claim_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        derived_validation_digest=_digest_public_payload(unsigned),
    )


def research_event_claim_authority_memory_conflict_report_payload(
    report: ResearchEventClaimAuthorityMemoryConflictReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventClaimAuthorityMemoryConflictReport:
        raise ValueError(
            "report must be a ResearchEventClaimAuthorityMemoryConflictReport",
        )
    _require_hard_flags("report", report)
    payload = _signed_payload(report)
    validate_research_event_claim_authority_memory_conflict_report_payload(payload)
    return payload


def research_event_claim_authority_memory_conflict_report_digest(
    report: ResearchEventClaimAuthorityMemoryConflictReport,
) -> str:
    payload = research_event_claim_authority_memory_conflict_report_payload(report)
    return str(payload["derived_validation_digest"])


def validate_research_event_claim_authority_memory_conflict_report_payload(
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
    observations: tuple[ResearchEventClaimAuthorityMemoryConflictObservation, ...],
    *,
    group_index: int,
    config: ResearchEventClaimAuthorityMemoryConflictConfig,
    generated_at: datetime,
) -> ResearchEventClaimAuthorityMemoryConflictRow:
    values = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.source_family,
                item.claim_side,
                item.authority_score,
                item.observed_at,
            ),
        ),
    )
    support_scores = tuple(
        item.authority_score for item in values if item.claim_side == "support"
    )
    challenge_scores = tuple(
        item.authority_score for item in values if item.claim_side == "challenge"
    )
    support_score = max(support_scores, default=ZERO).quantize(NUMERIC_QUANTUM)
    challenge_score = max(challenge_scores, default=ZERO).quantize(NUMERIC_QUANTUM)
    latest_observed_at = max(item.observed_at for item in values)
    max_memory_conflicts = max(item.memory_conflict_count for item in values).quantize(
        NUMERIC_QUANTUM,
    )
    family_count = _count(len({item.source_family for item in values}))
    evidence_count = _count(len(values))
    margin_abs = abs(support_score - challenge_score).quantize(NUMERIC_QUANTUM)
    latest_age_seconds = _age_seconds(generated_at, latest_observed_at)
    status = _row_status(
        support_score=support_score,
        challenge_score=challenge_score,
        margin_abs=margin_abs,
        family_count=family_count,
        latest_age_seconds=latest_age_seconds,
        max_memory_conflicts=max_memory_conflicts,
        config=config,
    )
    return ResearchEventClaimAuthorityMemoryConflictRow(
        claim_key=f"claim-{group_index:06d}",
        evidence_count=evidence_count,
        distinct_family_count=family_count,
        support_count=_count(len(support_scores)),
        challenge_count=_count(len(challenge_scores)),
        support_authority_score=support_score,
        challenge_authority_score=challenge_score,
        authority_margin_abs=margin_abs,
        max_memory_conflict_count=max_memory_conflicts,
        latest_observed_at=latest_observed_at,
        latest_age_seconds=latest_age_seconds,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            support_score=support_score,
            challenge_score=challenge_score,
            margin_abs=margin_abs,
            family_count=family_count,
            latest_age_seconds=latest_age_seconds,
            max_memory_conflicts=max_memory_conflicts,
            config=config,
        ),
    )


def _row_status(
    *,
    support_score: Decimal,
    challenge_score: Decimal,
    margin_abs: Decimal,
    family_count: Decimal,
    latest_age_seconds: Decimal,
    max_memory_conflicts: Decimal,
    config: ResearchEventClaimAuthorityMemoryConflictConfig,
) -> str:
    if max_memory_conflicts >= config.block_memory_conflict_count:
        return "block"
    if _has_material_conflict(
        support_score=support_score,
        challenge_score=challenge_score,
        margin_abs=margin_abs,
        config=config,
    ):
        return "block"
    if max_memory_conflicts >= config.watch_memory_conflict_count:
        return "watch"
    if family_count < config.min_family_quorum_count:
        return "watch"
    if latest_age_seconds >= config.stale_claim_age_seconds:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    support_score: Decimal,
    challenge_score: Decimal,
    margin_abs: Decimal,
    family_count: Decimal,
    latest_age_seconds: Decimal,
    max_memory_conflicts: Decimal,
    config: ResearchEventClaimAuthorityMemoryConflictConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if status == "pass":
        reason_codes.add("authority_clear_pass")
    if status == "watch":
        reason_codes.add("authority_memory_conflict_watch")
    if status == "block":
        reason_codes.add("authority_memory_conflict_block")
    if _has_material_conflict(
        support_score=support_score,
        challenge_score=challenge_score,
        margin_abs=margin_abs,
        config=config,
    ):
        reason_codes.add("material_authority_conflict")
    if max_memory_conflicts >= config.block_memory_conflict_count:
        reason_codes.add("memory_conflict_block")
    elif max_memory_conflicts >= config.watch_memory_conflict_count:
        reason_codes.add("memory_conflict_watch")
    if status != "block" and family_count >= config.min_family_quorum_count:
        reason_codes.add("family_quorum_met")
    elif status != "block":
        reason_codes.add("single_family_watch")
    if status == "pass" and latest_age_seconds <= config.fresh_claim_age_seconds:
        reason_codes.add("fresh_claim_pass")
    elif status != "block" and latest_age_seconds >= config.stale_claim_age_seconds:
        reason_codes.add("stale_claim_watch")
    return tuple(sorted(reason_codes))


def _has_material_conflict(
    *,
    support_score: Decimal,
    challenge_score: Decimal,
    margin_abs: Decimal,
    config: ResearchEventClaimAuthorityMemoryConflictConfig,
) -> bool:
    return (
        support_score >= config.material_authority_score
        and challenge_score >= config.material_authority_score
        and margin_abs < config.pass_authority_margin
    )


def _report_reason_codes(
    rows: tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("authority_memory_conflict_empty",)
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


def _report_status(rows: tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventClaimAuthorityMemoryConflictReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventClaimAuthorityMemoryConflictReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE.quantize(NUMERIC_QUANTUM),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventClaimAuthorityMemoryConflictReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchEventClaimAuthorityMemoryConflictObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(
    value: object,
) -> ResearchEventClaimAuthorityMemoryConflictObservation:
    if type(value) is ResearchEventClaimAuthorityMemoryConflictObservation:
        _require_hard_flags("observation", value)
        return value
    _require_hard_flags("observation", value)
    return ResearchEventClaimAuthorityMemoryConflictObservation(
        event_ref=_field_value(value, "event_ref"),
        candidate_ref=_field_value(value, "candidate_ref"),
        market_ref=_field_value(value, "market_ref"),
        claim_text=_field_value(value, "claim_text"),
        source_ref=_field_value(value, "source_ref"),
        source_detail=_field_value(value, "source_detail"),
        source_family=_field_value(value, "source_family"),
        claim_side=_field_value(value, "claim_side"),
        authority_score=_field_value(value, "authority_score"),
        observed_at=_field_value(value, "observed_at"),
        memory_conflict_count=_field_value(
            value,
            "memory_conflict_count",
            default=ZERO,
        ),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _claim_group_key(
    value: ResearchEventClaimAuthorityMemoryConflictObservation,
) -> str:
    encoded = "|".join(
        (
            value.event_ref,
            value.candidate_ref,
            value.market_ref,
            value.claim_text,
        ),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_sort_key(
    row: ResearchEventClaimAuthorityMemoryConflictRow,
) -> tuple[int, str]:
    return (_STATUS_RANK[row.status], row.claim_key)


def _status_count(
    rows: tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    rows: tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...],
) -> tuple[ResearchEventClaimAuthorityMemoryConflictRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventClaimAuthorityMemoryConflictRow:
            raise ValueError(
                "rows must contain ResearchEventClaimAuthorityMemoryConflictRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchEventClaimAuthorityMemoryConflictReasonCodeCount, ...],
) -> tuple[ResearchEventClaimAuthorityMemoryConflictReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchEventClaimAuthorityMemoryConflictReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventClaimAuthorityMemoryConflictReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    sorted_values = tuple(sorted(values, key=lambda value: value.reason_code))
    if values != sorted_values:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return values


def _validate_row(row: ResearchEventClaimAuthorityMemoryConflictRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.distinct_family_count > row.evidence_count:
        raise ValueError("distinct_family_count must not exceed evidence_count")
    if row.support_count + row.challenge_count != row.evidence_count:
        raise ValueError("support_count and challenge_count must match evidence_count")
    expected_margin = abs(
        row.support_authority_score - row.challenge_authority_score,
    ).quantize(NUMERIC_QUANTUM)
    if row.authority_margin_abs != expected_margin:
        raise ValueError("authority_margin_abs must match support and challenge scores")


def _validate_report(report: ResearchEventClaimAuthorityMemoryConflictReport) -> None:
    if report.claim_count != _count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_public_payload_keys("payload", payload, PUBLIC_PAYLOAD_KEYS)
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")
    if payload.get("status") not in EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    _reject_public_numeric_objects(payload)
    _validate_public_reason_code_list("reason_codes", payload.get("reason_codes"))
    reason_code_counts = payload.get("reason_code_counts")
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        _require_public_payload_keys(
            "reason_code_count",
            reason_code_count,
            PUBLIC_REASON_CODE_COUNT_KEYS,
        )
        _require_public_string("reason_code", reason_code_count.get("reason_code"))
        if reason_code_count.get("paper_only") is not True:
            raise ValueError("reason_code_count paper_only must be True")
        if reason_code_count.get("report_only") is not True:
            raise ValueError("reason_code_count report_only must be True")
        if reason_code_count.get("readonly") is not True:
            raise ValueError("reason_code_count readonly must be True")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_public_payload_keys("row", row, PUBLIC_ROW_KEYS)
        if row.get("paper_only") is not True:
            raise ValueError("row paper_only must be True")
        if row.get("report_only") is not True:
            raise ValueError("row report_only must be True")
        if row.get("readonly") is not True:
            raise ValueError("row readonly must be True")
        if row.get("status") not in EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES:
            raise ValueError("row status must be pass, watch, or block")
        _validate_public_reason_code_list("row reason_codes", row.get("reason_codes"))


def _require_public_payload_keys(
    field_name: str,
    value: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    unexpected_keys = sorted(set(value) - allowed_keys)
    if unexpected_keys:
        raise ValueError(f"unexpected public payload key: {unexpected_keys[0]}")
    missing_keys = sorted(allowed_keys - set(value))
    if missing_keys:
        raise ValueError(f"missing public payload key: {missing_keys[0]}")


def _validate_public_reason_code_list(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    for item in value:
        _require_public_string(field_name, item)


def _unsigned_payload(
    report: ResearchEventClaimAuthorityMemoryConflictReport,
) -> dict[str, Any]:
    payload = _public_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _signed_payload(
    report: ResearchEventClaimAuthorityMemoryConflictReport,
) -> dict[str, Any]:
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
        return {
            field.name: _public_value(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_public_value(item) for item in value]
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _public_value(item) for key, item in value.items()}
    return value


def _digest_public_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_objects(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("unsafe public payload value")


def _reject_public_numeric_objects(value: object) -> None:
    if type(value) in (Decimal, float, int):
        raise ValueError("public payload numerics must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_objects(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_objects(item)


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
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    ).quantize(NUMERIC_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
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
    return decimal_value.quantize(NUMERIC_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(NUMERIC_QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(NUMERIC_QUANTUM)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value.quantize(NUMERIC_QUANTUM)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value.quantize(NUMERIC_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(NUMERIC_QUANTUM)


def _require_private_string(field_name: str, value: object) -> None:
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
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} must be public safe")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES
    ):
        raise ValueError(f"{field_name} must be one of pass, watch, block")


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


def _require_exact_type(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exactly {expected.__name__}")
