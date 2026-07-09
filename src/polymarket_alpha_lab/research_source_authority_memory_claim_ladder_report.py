"""Pure claim-ladder report for caller-supplied research evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchSourceAuthorityMemoryClaimLadderClaim",
    "ResearchSourceAuthorityMemoryClaimLadderConfig",
    "ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount",
    "ResearchSourceAuthorityMemoryClaimLadderReport",
    "ResearchSourceAuthorityMemoryClaimLadderRow",
    "build_research_source_authority_memory_claim_ladder_report",
    "research_source_authority_memory_claim_ladder_report_payload",
    "research_source_authority_memory_claim_ladder_report_public_digest",
)


DEFAULT_CONFIG_VERSION = "research-source-authority-memory-claim-ladder-report-v0"
STATUSES = ("pass", "watch", "block")
AUTHORITY_TIER_SCORES = {
    "primary_record": Decimal("1.000000"),
    "official": Decimal("0.900000"),
    "specialist": Decimal("0.500000"),
    "secondary": Decimal("0.400000"),
}
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_LADDER_SCORE = Decimal("0.750000")
DEFAULT_WATCH_LADDER_SCORE = Decimal("0.400000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


REPORT_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "claim_count",
    "pass_count",
    "watch_count",
    "block_count",
    "mean_claim_ladder_score",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "public_payload_sha256",
)
ROW_PUBLIC_PAYLOAD_KEYS = (
    "claim_id",
    "candidate_ref_digest",
    "market_ref_digest",
    "source_ref_digest",
    "authority_tier",
    "observed_at",
    "source_age_seconds",
    "authority_score",
    "memory_score",
    "corroboration_score",
    "contradiction_penalty_score",
    "claim_ladder_score",
    "pass_ladder_score",
    "watch_ladder_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "private",
    "url",
    "dsn",
    "table",
    _join_parts("wal", "let"),
    _join_parts("cred", "ential"),
    _join_parts("sec", "ret"),
    "token",
    "api_key",
    _join_parts("ord", "er"),
    "broker",
    _join_parts("tra", "de"),
    _join_parts("trad", "ing"),
    "live",
    _join_parts("siz", "ing"),
    _join_parts("recommen", "dation"),
    "execution",
    "persist",
    "database",
    "network",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    _join_parts("post", "gres", "://"),
    _join_parts("post", "gresql", "://"),
    _join_parts("my", "sql", "://"),
    "jdbc:",
    "private",
    _join_parts("wal", "let"),
    _join_parts("cred", "ential"),
    _join_parts("sec", "ret"),
    "token",
    "api_key",
    _join_parts("priv", "ate_key"),
    "authentication",
    _join_parts("authori", "zation"),
    _join_parts("ord", "er"),
    "broker",
    "buy",
    "sell",
    _join_parts("tra", "de"),
    _join_parts("trad", "ing"),
    _join_parts("live", "_trading"),
    _join_parts("position", "_size"),
    _join_parts("siz", "ing"),
    _join_parts("recommen", "dation"),
    "execution",
    "persist",
    "database",
    "network",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceAuthorityMemoryClaimLadderConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_memory_seconds: Decimal = Decimal("3600")
    stale_memory_seconds: Decimal = Decimal("86400")
    min_corroboration_count: Decimal = Decimal("2")
    pass_ladder_score: Decimal = DEFAULT_PASS_LADDER_SCORE
    watch_ladder_score: Decimal = DEFAULT_WATCH_LADDER_SCORE
    authority_weight: Decimal = Decimal("0.500000")
    memory_weight: Decimal = Decimal("0.300000")
    corroboration_weight: Decimal = Decimal("0.200000")
    contradiction_penalty: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityMemoryClaimLadderConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_memory_seconds", "stale_memory_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_memory_seconds <= self.fresh_memory_seconds:
            raise ValueError("stale_memory_seconds must exceed fresh_memory_seconds")
        object.__setattr__(
            self,
            "min_corroboration_count",
            _require_positive_whole_decimal(
                "min_corroboration_count",
                self.min_corroboration_count,
            ),
        )
        for field_name in (
            "pass_ladder_score",
            "watch_ladder_score",
            "authority_weight",
            "memory_weight",
            "corroboration_weight",
            "contradiction_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_ladder_score <= self.watch_ladder_score:
            raise ValueError("pass_ladder_score must exceed watch_ladder_score")
        if (
            _quantize(
                self.authority_weight
                + self.memory_weight
                + self.corroboration_weight,
            )
            != ONE
        ):
            raise ValueError(
                "authority_weight, memory_weight, and corroboration_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityMemoryClaimLadderClaim:
    claim_id: str
    private_candidate_reference: str
    private_market_reference: str
    private_source_reference: str
    authority_tier: str
    observed_at: datetime
    memory_confidence: Decimal
    corroboration_count: Decimal
    contradiction_count: Decimal = Decimal("0")
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityMemoryClaimLadderClaim, "claim")
        _require_public_string("claim_id", self.claim_id)
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_source_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_enum("authority_tier", self.authority_tier, tuple(AUTHORITY_TIER_SCORES))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_confidence",
            _require_probability_decimal("memory_confidence", self.memory_confidence),
        )
        for field_name in ("corroboration_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("claim", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityMemoryClaimLadderRow:
    claim_id: str
    candidate_ref_digest: str
    market_ref_digest: str
    source_ref_digest: str
    authority_tier: str
    observed_at: datetime
    source_age_seconds: Decimal
    authority_score: Decimal
    memory_score: Decimal
    corroboration_score: Decimal
    contradiction_penalty_score: Decimal
    claim_ladder_score: Decimal
    pass_ladder_score: Decimal
    watch_ladder_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityMemoryClaimLadderRow, "row")
        _require_public_string("claim_id", self.claim_id)
        for field_name in (
            "candidate_ref_digest",
            "market_ref_digest",
            "source_ref_digest",
        ):
            _require_digest_reference(field_name, getattr(self, field_name))
        _require_enum("authority_tier", self.authority_tier, tuple(AUTHORITY_TIER_SCORES))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "authority_score",
            "memory_score",
            "corroboration_score",
            "contradiction_penalty_score",
            "claim_ladder_score",
            "pass_ladder_score",
            "watch_ladder_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount,
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
class ResearchSourceAuthorityMemoryClaimLadderReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_claim_ladder_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount, ...]
    rows: tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...]
    public_payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityMemoryClaimLadderReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_claim_ladder_score",
            _require_optional_probability_decimal(
                "mean_claim_ladder_score",
                self.mean_claim_ladder_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_report_public_payload(self, include_digest=False))
        if self.public_payload_sha256:
            _require_public_digest("public_payload_sha256", self.public_payload_sha256)
            if self.public_payload_sha256 != expected_digest:
                raise ValueError("public_payload_sha256 must match public payload")
        else:
            object.__setattr__(self, "public_payload_sha256", expected_digest)


def build_research_source_authority_memory_claim_ladder_report(
    claims: Iterable[object],
    *,
    config: ResearchSourceAuthorityMemoryClaimLadderConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityMemoryClaimLadderReport:
    if type(config) is not ResearchSourceAuthorityMemoryClaimLadderConfig:
        raise ValueError("config must be a ResearchSourceAuthorityMemoryClaimLadderConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    claim_items = _normalize_claims(claims)
    for item in claim_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_claim(item, config=config, generated_at=generated_at_utc)
                for item in claim_items
            ),
            key=lambda row: row.claim_id,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchSourceAuthorityMemoryClaimLadderReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        mean_claim_ladder_score=_mean_claim_ladder_score(rows),
        status=_summary_status(reason_codes),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_source_authority_memory_claim_ladder_report_payload(
    report: ResearchSourceAuthorityMemoryClaimLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityMemoryClaimLadderReport:
        raise ValueError("report must be a ResearchSourceAuthorityMemoryClaimLadderReport")
    _require_hard_flags("report", report)
    expected_digest = _payload_digest(
        _report_public_payload(report, include_digest=False),
    )
    if report.public_payload_sha256 != expected_digest:
        raise ValueError("public_payload_sha256 must match public payload")
    payload = _report_public_payload(report, include_digest=True)
    _validate_public_payload(payload, include_digest=True)
    return payload


def research_source_authority_memory_claim_ladder_report_public_digest(
    report: ResearchSourceAuthorityMemoryClaimLadderReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityMemoryClaimLadderReport:
        raise ValueError("report must be a ResearchSourceAuthorityMemoryClaimLadderReport")
    _require_hard_flags("report", report)
    expected_digest = _payload_digest(_report_public_payload(report, include_digest=False))
    if report.public_payload_sha256 != expected_digest:
        raise ValueError("public_payload_sha256 must match public payload")
    return expected_digest


def _row_from_claim(
    item: ResearchSourceAuthorityMemoryClaimLadderClaim,
    *,
    config: ResearchSourceAuthorityMemoryClaimLadderConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityMemoryClaimLadderRow:
    source_age_seconds = _age_seconds(generated_at, item.observed_at)
    authority_score = AUTHORITY_TIER_SCORES[item.authority_tier]
    memory_score = _quantize(
        item.memory_confidence
        * _recency_score(
            source_age_seconds,
            fresh_memory_seconds=config.fresh_memory_seconds,
            stale_memory_seconds=config.stale_memory_seconds,
        ),
    )
    corroboration_score = _corroboration_score(item.corroboration_count, config)
    contradiction_penalty_score = _quantize(
        min(ONE, config.contradiction_penalty * item.contradiction_count),
    )
    claim_ladder_score = _claim_ladder_score(
        authority_score=authority_score,
        memory_score=memory_score,
        corroboration_score=corroboration_score,
        contradiction_penalty_score=contradiction_penalty_score,
        config=config,
    )
    status = _row_status(
        claim_ladder_score=claim_ladder_score,
        corroboration_count=item.corroboration_count,
        contradiction_count=item.contradiction_count,
        config=config,
    )
    reason_codes = _row_reason_codes(
        authority_tier=item.authority_tier,
        source_age_seconds=source_age_seconds,
        corroboration_count=item.corroboration_count,
        contradiction_count=item.contradiction_count,
        claim_ladder_score=claim_ladder_score,
        status=status,
        config=config,
        input_reason_codes=item.reason_codes,
    )
    return ResearchSourceAuthorityMemoryClaimLadderRow(
        claim_id=item.claim_id,
        candidate_ref_digest=_digest_reference(item.private_candidate_reference),
        market_ref_digest=_digest_reference(item.private_market_reference),
        source_ref_digest=_digest_reference(item.private_source_reference),
        authority_tier=item.authority_tier,
        observed_at=item.observed_at,
        source_age_seconds=source_age_seconds,
        authority_score=authority_score,
        memory_score=memory_score,
        corroboration_score=corroboration_score,
        contradiction_penalty_score=contradiction_penalty_score,
        claim_ladder_score=claim_ladder_score,
        pass_ladder_score=config.pass_ladder_score,
        watch_ladder_score=config.watch_ladder_score,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_claims(
    claims: Iterable[object],
) -> tuple[ResearchSourceAuthorityMemoryClaimLadderClaim, ...]:
    if isinstance(claims, (str, bytes)):
        raise ValueError("claims must be an iterable")
    try:
        values = tuple(claims)
    except TypeError as exc:
        raise ValueError("claims must be an iterable") from exc
    normalized = tuple(_coerce_claim(value) for value in values)
    seen: set[str] = set()
    for item in normalized:
        if item.claim_id in seen:
            raise ValueError("claims must be unique by claim_id")
        seen.add(item.claim_id)
    return normalized


def _coerce_claim(value: object) -> ResearchSourceAuthorityMemoryClaimLadderClaim:
    if type(value) is ResearchSourceAuthorityMemoryClaimLadderClaim:
        _require_hard_flags("claim", value)
        return value
    _require_hard_flags("claim", value)
    return ResearchSourceAuthorityMemoryClaimLadderClaim(
        claim_id=_field_value(value, "claim_id"),
        private_candidate_reference=_field_value(value, "private_candidate_reference"),
        private_market_reference=_field_value(value, "private_market_reference"),
        private_source_reference=_field_value(value, "private_source_reference"),
        authority_tier=_field_value(value, "authority_tier"),
        observed_at=_field_value(value, "observed_at"),
        memory_confidence=_field_value(value, "memory_confidence"),
        corroboration_count=_field_value(value, "corroboration_count"),
        contradiction_count=_field_value(
            value,
            "contradiction_count",
            default=ZERO,
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _recency_score(
    source_age_seconds: Decimal,
    *,
    fresh_memory_seconds: Decimal,
    stale_memory_seconds: Decimal,
) -> Decimal:
    if source_age_seconds <= fresh_memory_seconds:
        return ONE
    if source_age_seconds >= stale_memory_seconds:
        return ZERO
    return _quantize(ONE - (source_age_seconds / stale_memory_seconds))


def _corroboration_score(
    corroboration_count: Decimal,
    config: ResearchSourceAuthorityMemoryClaimLadderConfig,
) -> Decimal:
    return _quantize(min(ONE, corroboration_count / config.min_corroboration_count))


def _claim_ladder_score(
    *,
    authority_score: Decimal,
    memory_score: Decimal,
    corroboration_score: Decimal,
    contradiction_penalty_score: Decimal,
    config: ResearchSourceAuthorityMemoryClaimLadderConfig,
) -> Decimal:
    value = (
        (authority_score * config.authority_weight)
        + (memory_score * config.memory_weight)
        + (corroboration_score * config.corroboration_weight)
        - contradiction_penalty_score
    )
    return _quantize(max(ZERO, min(ONE, value)))


def _row_status(
    *,
    claim_ladder_score: Decimal,
    corroboration_count: Decimal,
    contradiction_count: Decimal,
    config: ResearchSourceAuthorityMemoryClaimLadderConfig,
) -> str:
    if claim_ladder_score < config.watch_ladder_score:
        return "block"
    if claim_ladder_score < config.pass_ladder_score:
        return "watch"
    if corroboration_count < config.min_corroboration_count or contradiction_count > ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    authority_tier: str,
    source_age_seconds: Decimal,
    corroboration_count: Decimal,
    contradiction_count: Decimal,
    claim_ladder_score: Decimal,
    status: str,
    config: ResearchSourceAuthorityMemoryClaimLadderConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = {
        f"authority_tier_{authority_tier}",
        f"source_authority_memory_claim_ladder_{status}",
    }
    if source_age_seconds >= config.stale_memory_seconds:
        reason_codes.add("stale_memory")
    else:
        reason_codes.add("fresh_memory")
    if corroboration_count >= config.min_corroboration_count:
        reason_codes.add("corroborated_claim")
    else:
        reason_codes.add("thin_corroboration")
    if contradiction_count > ZERO:
        reason_codes.add("contradiction_present")
    if claim_ladder_score < config.watch_ladder_score:
        reason_codes.add("low_claim_ladder_score")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_claim_ladder_inputs",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.status == "watch" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("source_authority_memory_claim_ladder_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_claim_ladder_inputs",):
        return "block"
    if "source_authority_memory_claim_ladder_block" in reason_codes:
        return "block"
    if "source_authority_memory_claim_ladder_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _mean_claim_ladder_score(
    rows: tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.claim_ladder_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...],
) -> tuple[ResearchSourceAuthorityMemoryClaimLadderRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityMemoryClaimLadderRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthorityMemoryClaimLadderRow values",
            )
        _require_hard_flags("row", row)
        if row.claim_id in seen:
            raise ValueError("rows must be unique by claim_id")
        seen.add(row.claim_id)
    expected = tuple(sorted(rows, key=lambda row: row.claim_id))
    if rows != expected:
        raise ValueError("rows must be sorted by claim_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount, ...],
) -> tuple[ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityMemoryClaimLadderReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchSourceAuthorityMemoryClaimLadderRow,
) -> None:
    if row.pass_ladder_score <= row.watch_ladder_score:
        raise ValueError("pass_ladder_score must exceed watch_ladder_score")
    if row.status == "pass" and row.claim_ladder_score < row.pass_ladder_score:
        raise ValueError("claim_ladder_score must support pass status")
    if row.status == "watch" and (
        row.claim_ladder_score < row.watch_ladder_score
        or row.claim_ladder_score >= row.pass_ladder_score
        and "thin_corroboration" not in row.reason_codes
        and "contradiction_present" not in row.reason_codes
    ):
        raise ValueError("claim_ladder_score must support watch status")
    if row.status == "block" and row.claim_ladder_score >= row.watch_ladder_score:
        raise ValueError("claim_ladder_score must support block status")
    expected_status_code = f"source_authority_memory_claim_ladder_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchSourceAuthorityMemoryClaimLadderReport,
) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.mean_claim_ladder_score != _mean_claim_ladder_score(report.rows):
        raise ValueError("mean_claim_ladder_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _report_public_payload(
    report: ResearchSourceAuthorityMemoryClaimLadderReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "claim_count": _payload_value(report.claim_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "mean_claim_ladder_score": _payload_value(report.mean_claim_ladder_score),
        "status": report.status,
        "reason_codes": _payload_value(report.reason_codes),
        "reason_code_counts": _payload_value(report.reason_code_counts),
        "rows": _payload_value(report.rows),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["public_payload_sha256"] = report.public_payload_sha256
    return payload


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != "public_payload_sha256"
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _payload_digest(payload: dict[str, Any]) -> str:
    _validate_public_payload(payload, include_digest=False)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _validate_public_payload(
    payload: dict[str, Any],
    *,
    include_digest: bool,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    expected_report_keys = (
        REPORT_PUBLIC_PAYLOAD_KEYS
        if include_digest
        else tuple(
            key
            for key in REPORT_PUBLIC_PAYLOAD_KEYS
            if key != "public_payload_sha256"
        )
    )
    _require_public_payload_keys("public payload", payload, expected_report_keys)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a public JSON list")
    for index, value in enumerate(reason_code_counts):
        if type(value) is not dict:
            raise ValueError(
                "reason_code_counts must contain public JSON objects",
            )
        _require_public_payload_keys(
            f"reason_code_counts[{index}]",
            value,
            REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS,
        )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a public JSON list")
    for index, value in enumerate(rows):
        if type(value) is not dict:
            raise ValueError("rows must contain public JSON objects")
        _require_public_payload_keys(
            f"rows[{index}]",
            value,
            ROW_PUBLIC_PAYLOAD_KEYS,
        )
    if include_digest:
        _require_public_digest(
            "public_payload_sha256",
            payload["public_payload_sha256"],
        )
    _reject_unsafe_public_payload(payload)


def _require_public_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    actual = set(value)
    expected = set(expected_keys)
    missing = tuple(key for key in expected_keys if key not in actual)
    extra = tuple(sorted(actual - expected))
    if missing:
        raise ValueError(
            f"{label} missing public payload keys: {', '.join(missing)}",
        )
    if extra:
        raise ValueError(
            f"{label} has unexpected public payload keys: {', '.join(extra)}",
        )


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if any(
                fragment in lowered_key
                for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS
            ):
                raise ValueError("public payload contains unsafe key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text("public payload", value)
        return
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must not expose numeric primitives")
    if type(value) is datetime:
        raise ValueError("public payload must not expose datetime objects")
    raise ValueError("public payload contains unsupported value")


def _digest_reference(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, exact_type: type[object], name: str) -> None:
    if type(value) is not exact_type:
        raise TypeError(f"{name} must be exactly {exact_type.__name__}")


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


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if value.lower() != value or any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must contain lowercase snake-case values")
    _reject_unsafe_public_text(field_name, value)


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
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    _require_enum(field_name, value, STATUSES)


def _require_digest_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 reference")
    _require_public_digest(field_name, value.removeprefix("sha256:"))


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    allowed = set("0123456789abcdef")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name}.{field_name} must be True")
