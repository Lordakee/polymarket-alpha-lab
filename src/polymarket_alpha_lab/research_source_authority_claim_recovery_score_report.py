"""Pure report-only authority claim recovery scoring for research coverage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_RECOVERY_SCORE_CONFIG_VERSION = (
    "research-source-authority-claim-recovery-score-v0"
)

STATUSES = ("pass", "watch", "block")
NO_INPUTS_REASON = "research_source_authority_claim_recovery_no_inputs"
NO_RECOVERY_REASON = "research_source_authority_claim_recovery_no_recovery"
LOW_AUTHORITY_REASON = "research_source_authority_claim_recovery_low_authority"
STALE_SUPPORT_REASON = "research_source_authority_claim_recovery_stale_support"
CONTRADICTION_PRESSURE_REASON = (
    "research_source_authority_claim_recovery_contradiction_pressure"
)
WATCH_REASON = "research_source_authority_claim_recovery_watch"
BLOCK_REASON = "research_source_authority_claim_recovery_block"
PASS_REASON = "research_source_authority_claim_recovery_pass"
REASON_CODES = (
    NO_INPUTS_REASON,
    NO_RECOVERY_REASON,
    LOW_AUTHORITY_REASON,
    STALE_SUPPORT_REASON,
    CONTRADICTION_PRESSURE_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    PASS_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidateid",
    "market_id",
    "marketid",
    "market_slug",
    "marketslug",
    "question",
    "source_id",
    "sourceid",
    "source_url",
    "sourceurl",
    "source_text",
    "sourcetext",
    "dsn",
    "table_name",
    "tablename",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "private_key",
    "credential",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimRecoveryScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_RECOVERY_SCORE_CONFIG_VERSION
    )
    pass_recovery_score: Decimal = Decimal("0.700000")
    watch_recovery_score: Decimal = Decimal("0.400000")
    authority_watch_floor: Decimal = Decimal("0.600000")
    freshness_watch_floor: Decimal = Decimal("0.500000")
    contradiction_watch_ratio: Decimal = Decimal("0.250000")
    contradiction_block_ratio: Decimal = Decimal("0.500000")
    authority_weight: Decimal = Decimal("0.400000")
    recovery_weight: Decimal = Decimal("0.350000")
    freshness_weight: Decimal = Decimal("0.150000")
    contradiction_penalty_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_identifier("config_version", self.config_version)
        for field_name in (
            "pass_recovery_score",
            "watch_recovery_score",
            "authority_watch_floor",
            "freshness_watch_floor",
            "contradiction_watch_ratio",
            "contradiction_block_ratio",
            "authority_weight",
            "recovery_weight",
            "freshness_weight",
            "contradiction_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.pass_recovery_score <= self.watch_recovery_score:
            raise ValueError("pass_recovery_score must exceed watch_recovery_score")
        if self.contradiction_block_ratio < self.contradiction_watch_ratio:
            raise ValueError(
                "contradiction_block_ratio must not be below watch ratio",
            )
        weight_sum = _quantize(
            self.authority_weight
            + self.recovery_weight
            + self.freshness_weight
            + self.contradiction_penalty_weight,
        )
        if weight_sum != ONE:
            raise ValueError("score weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimRecoveryInput:
    claim_bucket: str
    authority_group: str
    claim_count: Decimal
    recovered_claim_count: Decimal
    authoritative_corroboration_count: Decimal
    authority_score: Decimal
    freshness_score: Decimal
    contradiction_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claim_bucket",
            _require_canonical_identifier("claim_bucket", self.claim_bucket),
        )
        object.__setattr__(
            self,
            "authority_group",
            _require_canonical_identifier("authority_group", self.authority_group),
        )
        object.__setattr__(
            self,
            "claim_count",
            _require_positive_count("claim_count", self.claim_count),
        )
        for field_name in (
            "recovered_claim_count",
            "authoritative_corroboration_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("authority_score", "freshness_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimRecoveryScoreRow:
    claim_bucket: str
    authority_group: str
    claim_count: Decimal
    recovered_claim_count: Decimal
    authoritative_corroboration_count: Decimal
    recovery_ratio: Decimal
    authority_score: Decimal
    freshness_score: Decimal
    contradiction_count: Decimal
    contradiction_ratio: Decimal
    recovery_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claim_bucket",
            _require_canonical_identifier("claim_bucket", self.claim_bucket),
        )
        object.__setattr__(
            self,
            "authority_group",
            _require_canonical_identifier("authority_group", self.authority_group),
        )
        object.__setattr__(
            self,
            "claim_count",
            _require_positive_count("claim_count", self.claim_count),
        )
        for field_name in (
            "recovered_claim_count",
            "authoritative_corroboration_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recovery_ratio",
            "authority_score",
            "freshness_score",
            "contradiction_ratio",
            "recovery_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_counts(self)
        _require_hard_flags("recovery row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimRecoveryScoreReport:
    generated_at: datetime
    config_version: str
    bucket_count: Decimal
    claim_count: Decimal
    recovered_claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recovery_score: Decimal
    max_contradiction_ratio: Decimal
    min_authority_score: Decimal
    min_freshness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    recovery_rows: tuple[ResearchSourceAuthorityClaimRecoveryScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_identifier("config_version", self.config_version)
        for field_name in (
            "bucket_count",
            "claim_count",
            "recovered_claim_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_recovery_score",
            "max_contradiction_ratio",
            "min_authority_score",
            "min_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "recovery_rows", _normalize_recovery_rows(self.recovery_rows))
        _require_hard_flags("report", self)
        _require_or_set_digest(self)
        _validate_report(self)


def build_research_source_authority_claim_recovery_score_report(
    inputs: list[ResearchSourceAuthorityClaimRecoveryInput]
    | tuple[ResearchSourceAuthorityClaimRecoveryInput, ...],
    *,
    config: ResearchSourceAuthorityClaimRecoveryScoreConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityClaimRecoveryScoreReport:
    if type(config) is not ResearchSourceAuthorityClaimRecoveryScoreConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityClaimRecoveryScoreConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _recovery_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityClaimRecoveryScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        bucket_count=_count(len(rows)),
        claim_count=_sum_rows(rows, "claim_count"),
        recovered_claim_count=_sum_rows(rows, "recovered_claim_count"),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        average_recovery_score=_ratio(
            _sum_rows(rows, "recovery_score"),
            _count(len(rows)),
        ),
        max_contradiction_ratio=_max_rows(rows, "contradiction_ratio"),
        min_authority_score=_min_rows(rows, "authority_score"),
        min_freshness_score=_min_rows(rows, "freshness_score"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        recovery_rows=rows,
    )


def research_source_authority_claim_recovery_score_report_payload(
    report: ResearchSourceAuthorityClaimRecoveryScoreReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityClaimRecoveryScoreReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityClaimRecoveryScoreReport",
        )
    _require_hard_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_claim_recovery_score_report_digest(
    report: ResearchSourceAuthorityClaimRecoveryScoreReport,
) -> str:
    payload = research_source_authority_claim_recovery_score_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityClaimRecoveryInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityClaimRecoveryInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityClaimRecoveryInput",
            )
        _require_hard_flags("input", row)
        key = (row.claim_bucket, row.authority_group)
        if key in seen:
            raise ValueError("inputs must be unique by claim bucket and authority group")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.claim_bucket, row.authority_group)))


def _recovery_rows(
    rows: tuple[ResearchSourceAuthorityClaimRecoveryInput, ...],
    *,
    config: ResearchSourceAuthorityClaimRecoveryScoreConfig,
) -> tuple[ResearchSourceAuthorityClaimRecoveryScoreRow, ...]:
    return tuple(
        sorted(
            (_recovery_row(row, config=config) for row in rows),
            key=_row_sort_key,
        ),
    )


def _recovery_row(
    row: ResearchSourceAuthorityClaimRecoveryInput,
    *,
    config: ResearchSourceAuthorityClaimRecoveryScoreConfig,
) -> ResearchSourceAuthorityClaimRecoveryScoreRow:
    recovery_ratio = _ratio(row.recovered_claim_count, row.claim_count)
    contradiction_ratio = _ratio(row.contradiction_count, row.claim_count)
    recovery_score = _recovery_score(
        authority_score=row.authority_score,
        recovery_ratio=recovery_ratio,
        freshness_score=row.freshness_score,
        contradiction_ratio=contradiction_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        recovered_claim_count=row.recovered_claim_count,
        authority_score=row.authority_score,
        freshness_score=row.freshness_score,
        contradiction_ratio=contradiction_ratio,
        recovery_score=recovery_score,
        config=config,
    )
    return ResearchSourceAuthorityClaimRecoveryScoreRow(
        claim_bucket=row.claim_bucket,
        authority_group=row.authority_group,
        claim_count=row.claim_count,
        recovered_claim_count=row.recovered_claim_count,
        authoritative_corroboration_count=row.authoritative_corroboration_count,
        recovery_ratio=recovery_ratio,
        authority_score=row.authority_score,
        freshness_score=row.freshness_score,
        contradiction_count=row.contradiction_count,
        contradiction_ratio=contradiction_ratio,
        recovery_score=recovery_score,
        status=_row_status(
            recovered_claim_count=row.recovered_claim_count,
            authority_score=row.authority_score,
            freshness_score=row.freshness_score,
            contradiction_ratio=contradiction_ratio,
            recovery_score=recovery_score,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _recovery_score(
    *,
    authority_score: Decimal,
    recovery_ratio: Decimal,
    freshness_score: Decimal,
    contradiction_ratio: Decimal,
    config: ResearchSourceAuthorityClaimRecoveryScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            authority_score * config.authority_weight
            + recovery_ratio * config.recovery_weight
            + freshness_score * config.freshness_weight
            - contradiction_ratio * config.contradiction_penalty_weight
        ).quantize(QUANT)
    return min(max(raw_score, ZERO), ONE)


def _row_reason_codes(
    *,
    recovered_claim_count: Decimal,
    authority_score: Decimal,
    freshness_score: Decimal,
    contradiction_ratio: Decimal,
    recovery_score: Decimal,
    config: ResearchSourceAuthorityClaimRecoveryScoreConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if recovered_claim_count == ZERO:
        reasons.append(NO_RECOVERY_REASON)
    if authority_score < config.authority_watch_floor:
        reasons.append(LOW_AUTHORITY_REASON)
    if freshness_score < config.freshness_watch_floor:
        reasons.append(STALE_SUPPORT_REASON)
    if contradiction_ratio >= config.contradiction_watch_ratio:
        reasons.append(CONTRADICTION_PRESSURE_REASON)
    status = _row_status(
        recovered_claim_count=recovered_claim_count,
        authority_score=authority_score,
        freshness_score=freshness_score,
        contradiction_ratio=contradiction_ratio,
        recovery_score=recovery_score,
        config=config,
    )
    if status == "block":
        reasons.append(BLOCK_REASON)
    elif status == "watch":
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _row_status(
    *,
    recovered_claim_count: Decimal,
    authority_score: Decimal,
    freshness_score: Decimal,
    contradiction_ratio: Decimal,
    recovery_score: Decimal,
    config: ResearchSourceAuthorityClaimRecoveryScoreConfig,
) -> str:
    if (
        recovered_claim_count == ZERO
        or recovery_score < config.watch_recovery_score
        or contradiction_ratio >= config.contradiction_block_ratio
    ):
        return "block"
    if (
        recovery_score >= config.pass_recovery_score
        and authority_score >= config.authority_watch_floor
        and freshness_score >= config.freshness_watch_floor
        and contradiction_ratio < config.contradiction_watch_ratio
    ):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourceAuthorityClaimRecoveryScoreRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityClaimRecoveryScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_INPUTS_REASON, PASS_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (PASS_REASON,)


def _row_sort_key(
    row: ResearchSourceAuthorityClaimRecoveryScoreRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.recovery_score,
        row.claim_bucket,
        row.authority_group,
    )


def _normalize_recovery_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityClaimRecoveryScoreRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("recovery_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str, str] | None = None
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityClaimRecoveryScoreRow:
            raise ValueError(
                "recovery_rows must contain ResearchSourceAuthorityClaimRecoveryScoreRow",
            )
        _require_hard_flags("recovery row", row)
        key = (row.claim_bucket, row.authority_group)
        if key in seen:
            raise ValueError(
                "recovery_rows must contain unique claim bucket and authority group",
            )
        seen.add(key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("recovery_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_input_counts(row: ResearchSourceAuthorityClaimRecoveryInput) -> None:
    if row.recovered_claim_count > row.claim_count:
        raise ValueError("recovered_claim_count must not exceed claim_count")
    if row.authoritative_corroboration_count > row.recovered_claim_count:
        raise ValueError(
            "authoritative_corroboration_count must not exceed recovered_claim_count",
        )
    if row.contradiction_count > row.claim_count:
        raise ValueError("contradiction_count must not exceed claim_count")


def _validate_row_counts(row: ResearchSourceAuthorityClaimRecoveryScoreRow) -> None:
    if row.recovered_claim_count > row.claim_count:
        raise ValueError("recovered_claim_count must not exceed claim_count")
    if row.authoritative_corroboration_count > row.recovered_claim_count:
        raise ValueError(
            "authoritative_corroboration_count must not exceed recovered_claim_count",
        )
    if row.contradiction_count > row.claim_count:
        raise ValueError("contradiction_count must not exceed claim_count")
    if row.recovery_ratio != _ratio(row.recovered_claim_count, row.claim_count):
        raise ValueError("recovery_ratio must match claim counts")
    if row.contradiction_ratio != _ratio(row.contradiction_count, row.claim_count):
        raise ValueError("contradiction_ratio must match claim counts")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only carry pass reason")
    if row.status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include block reason")
    if row.status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include watch reason")


def _validate_report(report: ResearchSourceAuthorityClaimRecoveryScoreReport) -> None:
    if report.bucket_count != _count(len(report.recovery_rows)):
        raise ValueError("bucket_count must match recovery_rows")
    if report.claim_count != _sum_rows(report.recovery_rows, "claim_count"):
        raise ValueError("claim_count must match recovery_rows")
    if report.recovered_claim_count != _sum_rows(
        report.recovery_rows,
        "recovered_claim_count",
    ):
        raise ValueError("recovered_claim_count must match recovery_rows")
    if report.pass_count != _count(sum(row.status == "pass" for row in report.recovery_rows)):
        raise ValueError("pass_count must match recovery_rows")
    if report.watch_count != _count(sum(row.status == "watch" for row in report.recovery_rows)):
        raise ValueError("watch_count must match recovery_rows")
    if report.block_count != _count(sum(row.status == "block" for row in report.recovery_rows)):
        raise ValueError("block_count must match recovery_rows")
    if report.average_recovery_score != _ratio(
        _sum_rows(report.recovery_rows, "recovery_score"),
        _count(len(report.recovery_rows)),
    ):
        raise ValueError("average_recovery_score must match recovery_rows")
    if report.max_contradiction_ratio != _max_rows(
        report.recovery_rows,
        "contradiction_ratio",
    ):
        raise ValueError("max_contradiction_ratio must match recovery_rows")
    if report.min_authority_score != _min_rows(report.recovery_rows, "authority_score"):
        raise ValueError("min_authority_score must match recovery_rows")
    if report.min_freshness_score != _min_rows(report.recovery_rows, "freshness_score"):
        raise ValueError("min_freshness_score must match recovery_rows")
    if report.status != _report_status(report.recovery_rows):
        raise ValueError("status must match recovery_rows")
    if report.reason_codes != _report_reason_codes(report.recovery_rows):
        raise ValueError("reason_codes must match recovery_rows")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return _require_nonnegative_decimal(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _max_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_identifier(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        index = REASON_CODES.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        previous_index = index
        seen.add(reason_code)
    return reason_codes


def _require_canonical_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_whole_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_or_set_digest(report: ResearchSourceAuthorityClaimRecoveryScoreReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchSourceAuthorityClaimRecoveryScoreReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
        _reject_unsafe_public_string("JSON string value", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_key(key)
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str):
        _reject_unsafe_public_string("public payload value", value)


def _reject_unsafe_public_key(key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("public payload contains unsafe key")


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must fit the decimal context") from exc


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_RECOVERY_SCORE_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceAuthorityClaimRecoveryInput",
    "ResearchSourceAuthorityClaimRecoveryScoreConfig",
    "ResearchSourceAuthorityClaimRecoveryScoreReport",
    "ResearchSourceAuthorityClaimRecoveryScoreRow",
    "build_research_source_authority_claim_recovery_score_report",
    "research_source_authority_claim_recovery_score_report_digest",
    "research_source_authority_claim_recovery_score_report_payload",
)
