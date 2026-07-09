"""Deterministic report-only checks for claim resolution authority floors."""

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
    "ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate",
    "ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow",
    "ResearchSourceClaimResolutionAuthorityMemoryFloorConfig",
    "ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount",
    "ResearchSourceClaimResolutionAuthorityMemoryFloorReport",
    "build_research_source_claim_resolution_authority_memory_floor_report",
    "research_source_claim_resolution_authority_memory_floor_report_payload",
    "validate_research_source_claim_resolution_authority_memory_floor_report_payload",
)


DEFAULT_CONFIG_VERSION = (
    "research-source-claim-resolution-authority-memory-floor-report-v0"
)
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityMemoryFloorConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_authority_score: Decimal = Decimal("0.750000")
    min_memory_floor_count: Decimal = Decimal("2")
    min_independent_source_count: Decimal = Decimal("2")
    min_resolution_signal_count: Decimal = Decimal("1")
    pass_authority_floor_ratio: Decimal = Decimal("0.600000")
    watch_authority_floor_ratio: Decimal = Decimal("0.333333")
    stale_age_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_authority_score",
            _require_probability_decimal("min_authority_score", self.min_authority_score),
        )
        for field_name in (
            "min_memory_floor_count",
            "min_independent_source_count",
            "min_resolution_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pass_authority_floor_ratio",
            _require_probability_decimal(
                "pass_authority_floor_ratio",
                self.pass_authority_floor_ratio,
            ),
        )
        object.__setattr__(
            self,
            "watch_authority_floor_ratio",
            _require_probability_decimal(
                "watch_authority_floor_ratio",
                self.watch_authority_floor_ratio,
            ),
        )
        if self.pass_authority_floor_ratio <= self.watch_authority_floor_ratio:
            raise ValueError(
                "pass_authority_floor_ratio must be greater than "
                "watch_authority_floor_ratio",
            )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate:
    candidate_id: str
    claim_id: str
    market_id: str | None
    market_slug: str | None
    market_question: str | None
    source_url: str | None
    source_text: str | None
    source_family: str
    authority_score: Decimal
    memory_floor_count: Decimal
    independent_source_count: Decimal
    resolution_signal_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("claim_id", self.claim_id)
        object.__setattr__(
            self,
            "market_id",
            _require_optional_text("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_optional_text("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "market_question",
            _require_optional_text("market_question", self.market_question),
        )
        object.__setattr__(
            self,
            "source_url",
            _require_optional_text("source_url", self.source_url),
        )
        object.__setattr__(
            self,
            "source_text",
            _require_optional_text("source_text", self.source_text),
        )
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "authority_score",
            _require_probability_decimal("authority_score", self.authority_score),
        )
        for field_name in (
            "memory_floor_count",
            "independent_source_count",
            "resolution_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow:
    claim_digest: str
    candidate_count: Decimal
    authority_candidate_count: Decimal
    independent_source_count: Decimal
    memory_floor_count: Decimal
    resolution_signal_count: Decimal
    latest_observed_at: datetime
    latest_authority_age_seconds: Decimal
    average_authority_score: Decimal
    authority_floor_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest("claim_digest", self.claim_digest)
        object.__setattr__(
            self,
            "candidate_count",
            _require_positive_whole_decimal("candidate_count", self.candidate_count),
        )
        object.__setattr__(
            self,
            "authority_candidate_count",
            _require_nonnegative_whole_decimal(
                "authority_candidate_count",
                self.authority_candidate_count,
            ),
        )
        for field_name in (
            "independent_source_count",
            "memory_floor_count",
            "resolution_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_authority_age_seconds",
            _require_nonnegative_decimal(
                "latest_authority_age_seconds",
                self.latest_authority_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "average_authority_score",
            _require_probability_decimal(
                "average_authority_score",
                self.average_authority_score,
            ),
        )
        object.__setattr__(
            self,
            "authority_floor_ratio",
            _require_probability_decimal(
                "authority_floor_ratio",
                self.authority_floor_ratio,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.authority_candidate_count > self.candidate_count:
            raise ValueError("authority_candidate_count must not exceed candidate_count")
        _require_hard_flags("claim row", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionAuthorityMemoryFloorReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...]
    reason_code_counts: tuple[
        ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_source_claim_resolution_authority_memory_floor_report(
    candidate_rows: Iterable[object],
    *,
    config: ResearchSourceClaimResolutionAuthorityMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchSourceClaimResolutionAuthorityMemoryFloorReport:
    if type(config) is not ResearchSourceClaimResolutionAuthorityMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimResolutionAuthorityMemoryFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidates = _normalize_candidate_rows(candidate_rows)
    for candidate in candidates:
        _reject_future_observed_at(candidate, generated_at_utc)

    grouped: dict[str, list[ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.claim_id, []).append(candidate)

    rows = tuple(
        _row_for_claim(
            claim_id=claim_id,
            candidates=tuple(grouped[claim_id]),
            config=config,
            generated_at=generated_at_utc,
        )
        for claim_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceClaimResolutionAuthorityMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_decimal_count(len(rows)),
        candidate_count=sum((row.candidate_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_claim_resolution_authority_memory_floor_report_payload(
    report: ResearchSourceClaimResolutionAuthorityMemoryFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceClaimResolutionAuthorityMemoryFloorReport:
        raise ValueError(
            "report must be a ResearchSourceClaimResolutionAuthorityMemoryFloorReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload["validation_sha256"] = _payload_digest(payload)
    return payload


def validate_research_source_claim_resolution_authority_memory_floor_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        return False
    digest = payload.get("validation_sha256")
    if type(digest) is not str:
        return False
    unsigned_payload = {
        key: value for key, value in payload.items() if key != "validation_sha256"
    }
    return digest == _payload_digest(unsigned_payload)


def _row_for_claim(
    *,
    claim_id: str,
    candidates: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate, ...],
    config: ResearchSourceClaimResolutionAuthorityMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow:
    if not candidates:
        raise ValueError("candidates must be nonempty")
    sorted_candidates = tuple(sorted(candidates, key=lambda item: item.candidate_id))
    latest = max(sorted_candidates, key=lambda item: (item.observed_at, item.candidate_id))
    latest_age = _age_seconds(generated_at, latest.observed_at)
    candidate_count = len(sorted_candidates)
    authority_candidate_count = sum(
        1 for candidate in sorted_candidates if _meets_authority_floor(candidate, config)
    )
    independent_source_count = max(
        candidate.independent_source_count for candidate in sorted_candidates
    )
    memory_floor_count = max(candidate.memory_floor_count for candidate in sorted_candidates)
    resolution_signal_count = max(
        candidate.resolution_signal_count for candidate in sorted_candidates
    )
    average_authority_score = _average_decimal(
        tuple(candidate.authority_score for candidate in sorted_candidates),
    )
    authority_floor_ratio = _ratio(
        _decimal_count(authority_candidate_count),
        _decimal_count(candidate_count),
    )
    status = _row_status(
        authority_candidate_count=_decimal_count(authority_candidate_count),
        independent_source_count=independent_source_count,
        memory_floor_count=memory_floor_count,
        resolution_signal_count=resolution_signal_count,
        authority_floor_ratio=authority_floor_ratio,
        latest_age=latest_age,
        config=config,
    )

    return ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow(
        claim_digest=_digest_text(claim_id),
        candidate_count=_decimal_count(candidate_count),
        authority_candidate_count=_decimal_count(authority_candidate_count),
        independent_source_count=independent_source_count,
        memory_floor_count=memory_floor_count,
        resolution_signal_count=resolution_signal_count,
        latest_observed_at=latest.observed_at,
        latest_authority_age_seconds=latest_age,
        average_authority_score=average_authority_score,
        authority_floor_ratio=authority_floor_ratio,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            authority_candidate_count=_decimal_count(authority_candidate_count),
            independent_source_count=independent_source_count,
            memory_floor_count=memory_floor_count,
            resolution_signal_count=resolution_signal_count,
            authority_floor_ratio=authority_floor_ratio,
            latest_age=latest_age,
            config=config,
        ),
    )


def _meets_authority_floor(
    candidate: ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate,
    config: ResearchSourceClaimResolutionAuthorityMemoryFloorConfig,
) -> bool:
    return (
        candidate.authority_score >= config.min_authority_score
        and candidate.memory_floor_count >= config.min_memory_floor_count
        and candidate.independent_source_count >= config.min_independent_source_count
        and candidate.resolution_signal_count >= config.min_resolution_signal_count
    )


def _row_status(
    *,
    authority_candidate_count: Decimal,
    independent_source_count: Decimal,
    memory_floor_count: Decimal,
    resolution_signal_count: Decimal,
    authority_floor_ratio: Decimal,
    latest_age: Decimal,
    config: ResearchSourceClaimResolutionAuthorityMemoryFloorConfig,
) -> str:
    if (
        authority_candidate_count == ZERO
        or independent_source_count < config.min_independent_source_count
        or memory_floor_count < config.min_memory_floor_count
        or resolution_signal_count < config.min_resolution_signal_count
        or authority_floor_ratio < config.watch_authority_floor_ratio
    ):
        return "block"
    if (
        authority_floor_ratio < config.pass_authority_floor_ratio
        or latest_age >= config.stale_age_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    authority_candidate_count: Decimal,
    independent_source_count: Decimal,
    memory_floor_count: Decimal,
    resolution_signal_count: Decimal,
    authority_floor_ratio: Decimal,
    latest_age: Decimal,
    config: ResearchSourceClaimResolutionAuthorityMemoryFloorConfig,
) -> tuple[str, ...]:
    reason_codes = {f"authority_memory_floor_{status}"}
    reason_codes.add(
        "authority_candidates_present"
        if authority_candidate_count > ZERO
        else "no_authority_candidates",
    )
    reason_codes.add(
        "independent_sources_met"
        if independent_source_count >= config.min_independent_source_count
        else "independent_sources_below_minimum",
    )
    reason_codes.add(
        "memory_floor_met"
        if memory_floor_count >= config.min_memory_floor_count
        else "memory_floor_below_minimum",
    )
    reason_codes.add(
        "resolution_signals_met"
        if resolution_signal_count >= config.min_resolution_signal_count
        else "resolution_signals_below_minimum",
    )
    reason_codes.add(
        "stale_authority_memory_floor"
        if latest_age >= config.stale_age_seconds
        else "fresh_authority_memory_floor",
    )
    if authority_floor_ratio < config.watch_authority_floor_ratio:
        reason_codes.add("authority_floor_ratio_block")
    elif authority_floor_ratio < config.pass_authority_floor_ratio:
        reason_codes.add("authority_floor_ratio_watch")
    else:
        reason_codes.add("authority_floor_ratio_pass")
    return tuple(sorted(reason_codes))


def _normalize_candidate_rows(
    candidate_rows: Iterable[object],
) -> tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate, ...]:
    if isinstance(candidate_rows, (str, bytes)):
        raise ValueError("candidate_rows must be an iterable")
    try:
        values = tuple(candidate_rows)
    except TypeError as exc:
        raise ValueError("candidate_rows must be an iterable") from exc
    return tuple(_coerce_candidate_row(value) for value in values)


def _coerce_candidate_row(
    value: object,
) -> ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate:
    if type(value) is ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate:
        _require_hard_flags("candidate", value)
        return value
    _require_hard_flags("candidate", value)
    return ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate(
        candidate_id=_field_value(value, "candidate_id"),
        claim_id=_field_value(value, "claim_id"),
        market_id=_field_value(value, "market_id", default=None),
        market_slug=_field_value(value, "market_slug", default=None),
        market_question=_field_value(value, "market_question", default=None),
        source_url=_field_value(value, "source_url", default=None),
        source_text=_field_value(value, "source_text", default=None),
        source_family=_field_value(value, "source_family"),
        authority_score=_field_value(value, "authority_score"),
        memory_floor_count=_field_value(value, "memory_floor_count"),
        independent_source_count=_field_value(value, "independent_source_count"),
        resolution_signal_count=_field_value(value, "resolution_signal_count"),
        observed_at=_field_value(value, "observed_at"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _normalize_rows(
    rows: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...],
) -> tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow:
            raise ValueError(
                "rows must contain "
                "ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow values",
            )
        _require_hard_flags("claim row", row)
        if row.claim_digest in seen_digests:
            raise ValueError("rows must have unique claim_digest values")
        seen_digests.add(row.claim_digest)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[
        ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount,
        ...
    ],
) -> tuple[
    ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount,
    ...
]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_report_consistency(
    report: ResearchSourceClaimResolutionAuthorityMemoryFloorReport,
) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.candidate_count != sum((row.candidate_count for row in report.rows), ZERO):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _summary_status(
    rows: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_authority_memory_floor_candidates",)
    if all(row.status == "pass" for row in rows):
        return ("authority_memory_floor_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reject_future_observed_at(
    candidate: ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate,
    generated_at: datetime,
) -> None:
    if candidate.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize(numerator / denominator)


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


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_optional_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    allowed = "0123456789abcdef"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
