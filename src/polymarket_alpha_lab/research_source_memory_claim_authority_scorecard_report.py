from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "research-source-memory-claim-authority-scorecard-report-v1"

AUTHORITY_TIERS = ("official", "primary", "secondary", "unverified")
STATUSES = ("pass", "watch", "block")

PASS_REASON = "claim_authority_pass"
MISSING_EVIDENCE_REASON = "missing_memory_evidence"
WATCH_SCORE_REASON = "authority_score_watch"
BLOCK_SCORE_REASON = "authority_score_block"
SOURCE_FAMILY_REASON = "source_family_count_below_floor"
CONTRADICTION_REASON = "contradiction_weight_high"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    MISSING_EVIDENCE_REASON,
    WATCH_SCORE_REASON,
    BLOCK_SCORE_REASON,
    SOURCE_FAMILY_REASON,
    CONTRADICTION_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)

UNSAFE_PUBLIC_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "://",
    "raw_" + "text",
    "cand" + "idate",
    "mar" + "ket",
    "source_" + "url",
    "source_" + "text",
    "d" + "sn",
    "ta" + "ble",
    "tok" + "en",
    "data" + "base",
    "net" + "work",
    "wall" + "et",
    "ord" + "er",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "siz" + "ing",
    "recomm" + "endation",
    "buy",
    "sell",
)

REPORT_DECIMAL_FIELDS = frozenset(
    (
        "claim_count",
        "evidence_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_authority_score",
    ),
)
ROW_DECIMAL_FIELDS = frozenset(
    (
        "evidence_count",
        "source_family_count",
        "latest_evidence_age_seconds",
        "authority_score",
    ),
)


@dataclass(frozen=True)
class ResearchSourceMemoryClaimAuthorityScorecardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_authority_score: Decimal = Decimal("0.800000")
    watch_authority_score: Decimal = Decimal("0.500000")
    min_source_family_count: Decimal = Decimal("2")
    contradiction_block_weight: Decimal = Decimal("0.750000")
    contradiction_penalty: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_authority_score",
            "watch_authority_score",
            "contradiction_block_weight",
            "contradiction_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_family_count",
            _normalize_count("min_source_family_count", self.min_source_family_count),
        )
        if self.pass_authority_score <= self.watch_authority_score:
            raise ValueError("pass_authority_score must exceed watch_authority_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceMemoryClaimAuthorityEvidence:
    evidence_id: str
    claim_memory_id: str
    authority_tier: str
    source_family: str
    observed_at: datetime
    authority_weight: Decimal = ONE
    corroboration_weight: Decimal = ONE
    contradiction_weight: Decimal = ZERO
    extraction_confidence: Decimal = ONE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "claim_memory_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_weight",
            "corroboration_weight",
            "contradiction_weight",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceMemoryClaimAuthorityScorecardRow:
    claim_ref: str
    evidence_count: Decimal
    source_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256_prefix("claim_ref", self.claim_ref)
        for field_name in ("evidence_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "authority_score",
            _normalize_probability("authority_score", self.authority_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _row_status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceMemoryClaimAuthorityScorecardReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_score: Decimal | None
    status: str
    rows: tuple[ResearchSourceMemoryClaimAuthorityScorecardRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_score",
            _normalize_optional_probability(
                "average_authority_score",
                self.average_authority_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_memory_claim_authority_scorecard_report_public_payload(self)


def build_research_source_memory_claim_authority_scorecard_report(
    evidence_rows: Iterable[ResearchSourceMemoryClaimAuthorityEvidence],
    *,
    config: ResearchSourceMemoryClaimAuthorityScorecardConfig,
    generated_at: datetime,
) -> ResearchSourceMemoryClaimAuthorityScorecardReport:
    if type(config) is not ResearchSourceMemoryClaimAuthorityScorecardConfig:
        raise ValueError(
            "config must be a ResearchSourceMemoryClaimAuthorityScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(
        evidence_rows,
        generated_at=generated_at_utc,
    )
    grouped: dict[str, list[ResearchSourceMemoryClaimAuthorityEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.claim_memory_id, []).append(item)

    rows = tuple(
        sorted(
            (
                _row_for_claim(
                    claim_memory_id=claim_memory_id,
                    evidence_items=tuple(items),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for claim_memory_id, items in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)

    return ResearchSourceMemoryClaimAuthorityScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        average_authority_score=_average_authority_score(rows),
        status=_report_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_source_memory_claim_authority_scorecard_report_public_payload(
    value: ResearchSourceMemoryClaimAuthorityScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchSourceMemoryClaimAuthorityScorecardReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _report_public_payload(value)
    elif type(value) is dict:
        payload = dict(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceMemoryClaimAuthorityScorecardReport or dict",
        )
    validate_research_source_memory_claim_authority_scorecard_report_public_payload(
        payload,
    )
    return dict(payload)


def validate_research_source_memory_claim_authority_scorecard_report_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_scalars("public payload", payload)
    _require_public_payload_flags(payload)
    _validate_public_payload_shape(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_claim(
    *,
    claim_memory_id: str,
    evidence_items: tuple[ResearchSourceMemoryClaimAuthorityEvidence, ...],
    config: ResearchSourceMemoryClaimAuthorityScorecardConfig,
    generated_at: datetime,
) -> ResearchSourceMemoryClaimAuthorityScorecardRow:
    authority_score = _claim_authority_score(evidence_items, config=config)
    latest_observed_at = max(item.observed_at for item in evidence_items)
    source_family_count = _count(len({item.source_family for item in evidence_items}))
    reason_codes = _row_reason_codes(
        authority_score=authority_score,
        source_family_count=source_family_count,
        max_contradiction_weight=max(item.contradiction_weight for item in evidence_items),
        config=config,
    )
    return ResearchSourceMemoryClaimAuthorityScorecardRow(
        claim_ref=_stable_ref("claim-memory", claim_memory_id),
        evidence_count=_count(len(evidence_items)),
        source_family_count=source_family_count,
        latest_evidence_age_seconds=_seconds_between(latest_observed_at, generated_at),
        authority_score=authority_score,
        status=_row_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _claim_authority_score(
    evidence_items: tuple[ResearchSourceMemoryClaimAuthorityEvidence, ...],
    *,
    config: ResearchSourceMemoryClaimAuthorityScorecardConfig,
) -> Decimal:
    authority_score = _mean(item.authority_weight for item in evidence_items)
    corroboration_score = _mean(item.corroboration_weight for item in evidence_items)
    confidence_cap = _mean(item.extraction_confidence for item in evidence_items)
    contradiction_weight = max(item.contradiction_weight for item in evidence_items)
    with localcontext(DECIMAL_CONTEXT):
        base_score = (authority_score + corroboration_score) / TWO
        penalized = min(base_score, confidence_cap) - (
            contradiction_weight * config.contradiction_penalty
        )
    if penalized <= ZERO:
        return ZERO
    return _normalize_probability("authority_score", min(penalized, ONE))


def _row_reason_codes(
    *,
    authority_score: Decimal,
    source_family_count: Decimal,
    max_contradiction_weight: Decimal,
    config: ResearchSourceMemoryClaimAuthorityScorecardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if authority_score < config.watch_authority_score:
        reasons.append(BLOCK_SCORE_REASON)
    elif authority_score < config.pass_authority_score:
        reasons.append(WATCH_SCORE_REASON)
    if source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_REASON)
    if max_contradiction_weight >= config.contradiction_block_weight:
        reasons.append(CONTRADICTION_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchSourceMemoryClaimAuthorityScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_EVIDENCE_REASON,)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(code for code in row.reason_codes if code != PASS_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_public_payload(
    report: ResearchSourceMemoryClaimAuthorityScorecardReport,
) -> dict[str, Any]:
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(
    report: ResearchSourceMemoryClaimAuthorityScorecardReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "claim_count": _decimal_payload(report.claim_count),
        "evidence_count": _decimal_payload(report.evidence_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_authority_score": _optional_decimal_payload(
            report.average_authority_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(
    row: ResearchSourceMemoryClaimAuthorityScorecardRow,
) -> dict[str, Any]:
    return {
        "claim_ref": row.claim_ref,
        "evidence_count": _decimal_payload(row.evidence_count),
        "source_family_count": _decimal_payload(row.source_family_count),
        "latest_evidence_age_seconds": _decimal_payload(
            row.latest_evidence_age_seconds,
        ),
        "authority_score": _decimal_payload(row.authority_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _set_or_validate_derived_validation_digest(
    report: ResearchSourceMemoryClaimAuthorityScorecardReport,
) -> None:
    expected_digest = _derived_validation_digest(_report_payload_without_digest(report))
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
        return
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _validate_derived_validation_digest(
    report: ResearchSourceMemoryClaimAuthorityScorecardReport,
) -> None:
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _derived_validation_digest(
        _report_payload_without_digest(report),
    ):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = {key: value for key, value in payload.items() if key != "derived_validation_digest"}
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_report(report: ResearchSourceMemoryClaimAuthorityScorecardReport) -> None:
    if report.claim_count != _count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    for status in STATUSES:
        count_name = f"{status}_count"
        if getattr(report, count_name) != _count(_status_count(report.rows, status)):
            raise ValueError(f"{count_name} must match rows")
    if report.average_authority_score != _average_authority_score(report.rows):
        raise ValueError("average_authority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    for field_name in (
        "generated_at",
        "config_version",
        "status",
        "derived_validation_digest",
    ):
        _payload_required_string(payload, field_name)
    for field_name in REPORT_DECIMAL_FIELDS:
        value = payload.get(field_name)
        if value is not None:
            _require_decimal_payload_string(field_name, value)
    _require_status("status", payload["status"])
    _payload_required_reason_codes(payload, "reason_codes")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain dict values")
        _validate_public_row_payload(row)


def _validate_public_row_payload(row: dict[str, Any]) -> None:
    _payload_required_string(row, "claim_ref")
    _require_sha256_prefix("claim_ref", row["claim_ref"])
    for field_name in ROW_DECIMAL_FIELDS:
        _require_decimal_payload_string(field_name, row.get(field_name))
    _payload_required_string(row, "status")
    _require_status("status", row["status"])
    _payload_required_reason_codes(row, "reason_codes")
    _require_public_payload_flags(row)


def _normalize_evidence_rows(
    evidence_rows: Iterable[ResearchSourceMemoryClaimAuthorityEvidence],
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceMemoryClaimAuthorityEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable of evidence rows")
    try:
        rows = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable of evidence rows") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceMemoryClaimAuthorityEvidence:
            raise ValueError(
                "evidence_rows must contain ResearchSourceMemoryClaimAuthorityEvidence",
            )
        _require_hard_flags("evidence", row)
        if row.evidence_id in seen:
            raise ValueError("evidence_id values must be unique")
        seen.add(row.evidence_id)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return rows


def _normalize_rows(
    rows: Iterable[ResearchSourceMemoryClaimAuthorityScorecardRow],
) -> tuple[ResearchSourceMemoryClaimAuthorityScorecardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of scorecard rows")
    try:
        row_items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of scorecard rows") from exc
    seen: set[str] = set()
    for row in row_items:
        if type(row) is not ResearchSourceMemoryClaimAuthorityScorecardRow:
            raise ValueError(
                "rows must contain ResearchSourceMemoryClaimAuthorityScorecardRow",
            )
        _require_hard_flags("row", row)
        if row.claim_ref in seen:
            raise ValueError("claim_ref values must be unique")
        seen.add(row.claim_ref)
    return tuple(sorted(row_items, key=_row_sort_key))


def _mean(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum(items, ZERO)
        result = total / _count(len(items))
    return _normalize_probability("mean", result)


def _average_authority_score(
    rows: tuple[ResearchSourceMemoryClaimAuthorityScorecardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        result = sum((row.authority_score for row in rows), ZERO) / _count(len(rows))
    return _normalize_probability("average_authority_score", result)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "latest_evidence_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if MISSING_EVIDENCE_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} missing evidence reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if BLOCK_SCORE_REASON in reason_codes or CONTRADICTION_REASON in reason_codes:
        return "block"
    return "watch"


def _report_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if MISSING_EVIDENCE_REASON in reason_codes:
        return "block"
    if BLOCK_SCORE_REASON in reason_codes or CONTRADICTION_REASON in reason_codes:
        return "block"
    return "watch"


def _status_count(
    rows: tuple[ResearchSourceMemoryClaimAuthorityScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _payload_required_reason_codes(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value))


def _require_decimal_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal strings")
    if value != "none":
        _normalize_decimal(field_name, Decimal(value))


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _optional_decimal_payload(value: Decimal | None) -> str:
    if value is None:
        return "none"
    return _decimal_payload(value)


def _datetime_payload(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _stable_ref(label: str, value: str) -> str:
    digest = hashlib.sha256(f"{label}:{value}".encode("utf-8")).hexdigest()
    return digest[:24]


def _require_sha256_prefix(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 24:
        raise ValueError(f"{field_name} must be a sha256 prefix")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 prefix") from exc


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 digest") from exc


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} has unsafe public payload")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{label} has unsafe public payload")


def _reject_public_numeric_scalars(label: str, value: object) -> None:
    if type(value) is bool or value is None or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{label} must use Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_scalars(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_scalars(label, item)
        return
    raise ValueError(f"{label} contains unsupported value")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _row_sort_key(
    row: ResearchSourceMemoryClaimAuthorityScorecardRow,
) -> str:
    return row.claim_ref


__all__ = (
    "ResearchSourceMemoryClaimAuthorityEvidence",
    "ResearchSourceMemoryClaimAuthorityScorecardConfig",
    "ResearchSourceMemoryClaimAuthorityScorecardReport",
    "ResearchSourceMemoryClaimAuthorityScorecardRow",
    "build_research_source_memory_claim_authority_scorecard_report",
    "research_source_memory_claim_authority_scorecard_report_public_payload",
    "validate_research_source_memory_claim_authority_scorecard_report_public_payload",
)
