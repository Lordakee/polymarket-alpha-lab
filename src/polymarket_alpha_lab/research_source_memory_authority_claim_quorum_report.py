"""Pure report-only memory authority claim quorum report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json


DEFAULT_RESEARCH_SOURCE_MEMORY_AUTHORITY_CLAIM_QUORUM_REPORT_CONFIG_VERSION = (
    "research-source-memory-authority-claim-quorum-report-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PRIVATE_DIGEST_PREFIX = "sha256:"
STATUSES = ("pass", "watch", "block")
PASS_REASON = "claim_quorum_pass"
WATCH_REASON = "claim_quorum_watch"
BLOCK_REASON = "claim_quorum_block"
STALE_REASON = "claim_quorum_memory_stale"
CONFLICT_WATCH_REASON = "claim_quorum_conflict_watch"
CONFLICT_BLOCK_REASON = "claim_quorum_conflict_block"
INSUFFICIENT_AUTHORITY_REASON = "claim_quorum_insufficient_authority"
INSUFFICIENT_WEIGHT_REASON = "claim_quorum_insufficient_weight"
EMPTY_REASON = "no_claim_quorum_inputs"
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "marketprivate",
    "raw",
    "sourceurl",
    "sourcetext",
    "rawtext",
    "://",
    "www.",
    "dsn",
    "table",
    "token",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_MEMORY_AUTHORITY_CLAIM_QUORUM_REPORT_CONFIG_VERSION",
    "ResearchSourceMemoryAuthorityClaimQuorumConfig",
    "ResearchSourceMemoryAuthorityClaimQuorumInput",
    "ResearchSourceMemoryAuthorityClaimQuorumReport",
    "ResearchSourceMemoryAuthorityClaimQuorumRow",
    "build_research_source_memory_authority_claim_quorum_report",
    "research_source_memory_authority_claim_quorum_report_digest",
    "research_source_memory_authority_claim_quorum_report_public_payload",
    "validate_research_source_memory_authority_claim_quorum_report_public_payload",
)


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
class ResearchSourceMemoryAuthorityClaimQuorumConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_MEMORY_AUTHORITY_CLAIM_QUORUM_REPORT_CONFIG_VERSION
    )
    min_pass_claim_quorum_score: Decimal = Decimal("0.800000")
    min_watch_claim_quorum_score: Decimal = Decimal("0.550000")
    min_pass_authority_count: Decimal = Decimal("2.000000")
    min_pass_support_weight: Decimal = Decimal("2.000000")
    max_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_conflict_weight: Decimal = Decimal("0.250000")
    block_conflict_weight: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceMemoryAuthorityClaimQuorumConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MEMORY_AUTHORITY_CLAIM_QUORUM_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_claim_quorum_score",
            "min_watch_claim_quorum_score",
            "watch_conflict_weight",
            "block_conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_authority_count",
            "min_pass_support_weight",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_claim_quorum_score <= self.min_watch_claim_quorum_score:
            raise ValueError(
                "min_pass_claim_quorum_score must exceed min_watch_claim_quorum_score",
            )
        if self.block_conflict_weight <= self.watch_conflict_weight:
            raise ValueError("block_conflict_weight must exceed watch_conflict_weight")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceMemoryAuthorityClaimQuorumInput(_FinalPublicDataclass):
    claim_group: str
    authority_group: str
    private_candidate_ref: str
    private_market_ref: str
    private_locator_ref: str
    observed_at: datetime
    authority_weight: Decimal
    memory_authority_score: Decimal
    claim_support_score: Decimal
    contradiction_weight: Decimal = ZERO
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceMemoryAuthorityClaimQuorumInput, "input")
        _require_public_string("claim_group", self.claim_group)
        _require_public_string("authority_group", self.authority_group)
        for field_name in (
            "private_candidate_ref",
            "private_market_ref",
            "private_locator_ref",
        ):
            _require_nonempty_private_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_weight",
            _require_nonnegative_decimal("authority_weight", self.authority_weight),
        )
        for field_name in ("memory_authority_score", "claim_support_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_weight",
            _require_nonnegative_decimal(
                "contradiction_weight",
                self.contradiction_weight,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceMemoryAuthorityClaimQuorumRow(_FinalPublicDataclass):
    claim_group: str
    claim_ref_digest: str
    locator_ref_digest: str
    latest_observed_at: datetime
    latest_age_seconds: Decimal
    evidence_count: Decimal
    authority_count: Decimal
    support_weight: Decimal
    conflict_weight: Decimal
    claim_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceMemoryAuthorityClaimQuorumRow, "row")
        _require_public_string("claim_group", self.claim_group)
        for field_name in ("claim_ref_digest", "locator_ref_digest"):
            _require_private_digest(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "latest_age_seconds",
            "evidence_count",
            "authority_count",
            "support_weight",
            "conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "claim_quorum_score",
            _require_ratio_decimal("claim_quorum_score", self.claim_quorum_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(_row_public_payload(self))


@dataclass(frozen=True)
class ResearchSourceMemoryAuthorityClaimQuorumReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_claim_quorum_score: Decimal
    minimum_claim_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceMemoryAuthorityClaimQuorumReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "row_count",
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
            "average_claim_quorum_score",
            "minimum_claim_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_counts(self)
        _require_hard_flags("report", self)
        expected_digest = research_source_memory_authority_claim_quorum_report_digest(
            _report_public_payload(self, include_digest=False),
        )
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _reject_unsafe_public_payload(_report_public_payload(self, include_digest=True))


def build_research_source_memory_authority_claim_quorum_report(
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...],
    *,
    config: ResearchSourceMemoryAuthorityClaimQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceMemoryAuthorityClaimQuorumReport:
    if type(config) is not ResearchSourceMemoryAuthorityClaimQuorumConfig:
        raise ValueError("config must be a ResearchSourceMemoryAuthorityClaimQuorumConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (
                _build_row(group, config=config, generated_at=generated_at_utc)
                for group in _group_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceMemoryAuthorityClaimQuorumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_count(len(report_rows)),
        pass_count=_status_count(report_rows, "pass"),
        watch_count=_status_count(report_rows, "watch"),
        block_count=_status_count(report_rows, "block"),
        average_claim_quorum_score=_average(
            tuple(row.claim_quorum_score for row in report_rows),
        ),
        minimum_claim_quorum_score=_minimum(
            tuple(row.claim_quorum_score for row in report_rows),
        ),
        status=_rollup_status(tuple(row.status for row in report_rows)),
        reason_codes=_report_reason_codes(report_rows),
        rows=report_rows,
    )


def research_source_memory_authority_claim_quorum_report_public_payload(
    report: ResearchSourceMemoryAuthorityClaimQuorumReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is dict:
        validate_research_source_memory_authority_claim_quorum_report_public_payload(
            report,
        )
        return report
    if type(report) is not ResearchSourceMemoryAuthorityClaimQuorumReport:
        raise ValueError("report must be a ResearchSourceMemoryAuthorityClaimQuorumReport")
    expected_digest = research_source_memory_authority_claim_quorum_report_digest(
        _report_public_payload(report, include_digest=False),
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")
    payload = _report_public_payload(report, include_digest=True)
    _reject_unsafe_public_payload(payload)
    return payload


def validate_research_source_memory_authority_claim_quorum_report_public_payload(
    payload: dict[str, object],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    digest_material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = research_source_memory_authority_claim_quorum_report_digest(
        digest_material,
    )
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")
    return True


def research_source_memory_authority_claim_quorum_report_digest(
    payload: dict[str, object],
) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _group_inputs(
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...],
) -> tuple[tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...], ...]:
    groups: dict[str, list[ResearchSourceMemoryAuthorityClaimQuorumInput]] = {}
    for row in rows:
        groups.setdefault(row.claim_group, []).append(row)
    return tuple(
        tuple(sorted(group, key=_input_sort_key))
        for _, group in sorted(groups.items(), key=lambda pair: pair[0])
    )


def _build_row(
    group: tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...],
    *,
    config: ResearchSourceMemoryAuthorityClaimQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceMemoryAuthorityClaimQuorumRow:
    latest_observed_at = max(row.observed_at for row in group)
    latest_age_seconds = _seconds_between(generated_at, latest_observed_at)
    evidence_count = _count(len(group))
    authority_count = _count(len({row.authority_group for row in group}))
    support_weight = _sum(tuple(row.authority_weight for row in group))
    conflict_weight = _sum(tuple(row.contradiction_weight for row in group))
    score = _claim_quorum_score(
        group,
        latest_age_seconds=latest_age_seconds,
        config=config,
    )
    status = _row_status(
        authority_count=authority_count,
        support_weight=support_weight,
        conflict_weight=conflict_weight,
        score=score,
        latest_age_seconds=latest_age_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        group,
        authority_count=authority_count,
        support_weight=support_weight,
        conflict_weight=conflict_weight,
        score=score,
        status=status,
        latest_age_seconds=latest_age_seconds,
        config=config,
    )
    return ResearchSourceMemoryAuthorityClaimQuorumRow(
        claim_group=group[0].claim_group,
        claim_ref_digest=_private_digest(
            "claim",
            group[0].claim_group,
            *(row.private_candidate_ref for row in group),
            *(row.private_market_ref for row in group),
        ),
        locator_ref_digest=_private_digest(
            "locator",
            *(row.private_locator_ref for row in group),
        ),
        latest_observed_at=latest_observed_at,
        latest_age_seconds=latest_age_seconds,
        evidence_count=evidence_count,
        authority_count=authority_count,
        support_weight=support_weight,
        conflict_weight=conflict_weight,
        claim_quorum_score=score,
        status=status,
        reason_codes=reason_codes,
    )


def _claim_quorum_score(
    group: tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...],
    *,
    latest_age_seconds: Decimal,
    config: ResearchSourceMemoryAuthorityClaimQuorumConfig,
) -> Decimal:
    if latest_age_seconds > config.max_memory_age_seconds:
        return ZERO
    values: list[Decimal] = []
    for row in group:
        values.append(row.memory_authority_score)
        values.append(row.claim_support_score)
    return _minimum(tuple(values))


def _row_status(
    *,
    authority_count: Decimal,
    support_weight: Decimal,
    conflict_weight: Decimal,
    score: Decimal,
    latest_age_seconds: Decimal,
    config: ResearchSourceMemoryAuthorityClaimQuorumConfig,
) -> str:
    if (
        latest_age_seconds > config.max_memory_age_seconds
        or score < config.min_watch_claim_quorum_score
        or conflict_weight >= config.block_conflict_weight
    ):
        return "block"
    if (
        score < config.min_pass_claim_quorum_score
        or authority_count < config.min_pass_authority_count
        or support_weight < config.min_pass_support_weight
        or conflict_weight >= config.watch_conflict_weight
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    group: tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...],
    *,
    authority_count: Decimal,
    support_weight: Decimal,
    conflict_weight: Decimal,
    score: Decimal,
    status: str,
    latest_age_seconds: Decimal,
    config: ResearchSourceMemoryAuthorityClaimQuorumConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if latest_age_seconds > config.max_memory_age_seconds:
        return (BLOCK_REASON, STALE_REASON)
    if conflict_weight >= config.block_conflict_weight:
        reason_codes.append(CONFLICT_BLOCK_REASON)
    elif conflict_weight >= config.watch_conflict_weight:
        reason_codes.append(CONFLICT_WATCH_REASON)
    if authority_count < config.min_pass_authority_count:
        reason_codes.append(INSUFFICIENT_AUTHORITY_REASON)
    if support_weight < config.min_pass_support_weight:
        reason_codes.append(INSUFFICIENT_WEIGHT_REASON)
    if status == "block":
        reason_codes.append(BLOCK_REASON)
    elif status == "watch":
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(PASS_REASON)
    for row in group:
        for reason_code in row.reason_codes:
            reason_codes.append(f"input_{reason_code}")
    if score < ZERO:
        raise ValueError("claim_quorum_score must be nonnegative")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if any(row.status == "block" for row in rows):
        return tuple(
            sorted({code for row in rows if row.status == "block" for code in row.reason_codes}),
        )
    if any(row.status == "watch" for row in rows):
        return tuple(
            sorted({code for row in rows if row.status == "watch" for code in row.reason_codes}),
        )
    return (PASS_REASON,)


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchSourceMemoryAuthorityClaimQuorumRow) -> tuple[str, str]:
    return ({"block": "0", "watch": "1", "pass": "2"}[row.status], row.claim_group)


def _input_sort_key(row: ResearchSourceMemoryAuthorityClaimQuorumInput) -> tuple[str, str]:
    return (row.claim_group, row.authority_group)


def _report_public_payload(
    report: ResearchSourceMemoryAuthorityClaimQuorumReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at": _datetime_public(report.generated_at),
        "config_version": report.config_version,
        "row_count": _decimal_public(report.row_count),
        "pass_count": _decimal_public(report.pass_count),
        "watch_count": _decimal_public(report.watch_count),
        "block_count": _decimal_public(report.block_count),
        "average_claim_quorum_score": _decimal_public(
            report.average_claim_quorum_score,
        ),
        "minimum_claim_quorum_score": _decimal_public(
            report.minimum_claim_quorum_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_public_payload(row: ResearchSourceMemoryAuthorityClaimQuorumRow) -> dict[str, object]:
    return {
        "claim_group": row.claim_group,
        "claim_ref_digest": row.claim_ref_digest,
        "locator_ref_digest": row.locator_ref_digest,
        "latest_observed_at": _datetime_public(row.latest_observed_at),
        "latest_age_seconds": _decimal_public(row.latest_age_seconds),
        "evidence_count": _decimal_public(row.evidence_count),
        "authority_count": _decimal_public(row.authority_count),
        "support_weight": _decimal_public(row.support_weight),
        "conflict_weight": _decimal_public(row.conflict_weight),
        "claim_quorum_score": _decimal_public(row.claim_quorum_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_report_counts(
    report: ResearchSourceMemoryAuthorityClaimQuorumReport,
) -> None:
    row_count = _count(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _rollup_status(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")


def _normalize_inputs(
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...],
) -> tuple[ResearchSourceMemoryAuthorityClaimQuorumInput, ...]:
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceMemoryAuthorityClaimQuorumInput:
            raise ValueError("rows must contain ResearchSourceMemoryAuthorityClaimQuorumInput")
        _require_hard_flags("input", row)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchSourceMemoryAuthorityClaimQuorumRow, ...],
) -> tuple[ResearchSourceMemoryAuthorityClaimQuorumRow, ...]:
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceMemoryAuthorityClaimQuorumRow:
            raise ValueError("rows must contain ResearchSourceMemoryAuthorityClaimQuorumRow")
        _require_hard_flags("row", row)
    return normalized


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(_sum(values) / _count(len(values)))


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _sum(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days) * Decimal("86400")
    seconds += Decimal(delta.seconds)
    seconds += Decimal(delta.microseconds) / Decimal("1000000")
    if seconds < ZERO:
        return ZERO
    return _quantize(seconds)


def _private_digest(label: str, *parts: str) -> str:
    material = json.dumps(
        [label, *sorted(parts)],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{PRIVATE_DIGEST_PREFIX}{hashlib.sha256(material).hexdigest()}"


def _decimal_public(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("public Decimal value must be exactly Decimal")
    return str(value)


def _datetime_public(value: datetime) -> str:
    if type(value) is not datetime:
        raise ValueError("public datetime value must be exactly datetime")
    return value.astimezone(UTC).isoformat()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 128:
        raise ValueError(f"{field_name} must not exceed 128 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_nonempty_private_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code.strip() != reason_code or not reason_code:
            raise ValueError("reason_codes must be non-empty")
        if not reason_code.replace("_", "").isalnum() or not reason_code[0].islower():
            raise ValueError("reason_codes must be stable snake case")
        _reject_unsafe_public_string("reason_code", reason_code)
    return tuple(dict.fromkeys(normalized))


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    prefix = PRIVATE_DIGEST_PREFIX if field_name.endswith("_digest") else ""
    digest = value.removeprefix(prefix)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not value.startswith(PRIVATE_DIGEST_PREFIX):
        raise ValueError(f"{field_name} must be a private sha256 digest")
    _require_digest(field_name, value)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is str:
        _reject_unsafe_public_string("public value", value)
        return
    if type(value) is dict:
        for key, item_value in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string("public key", key)
            _reject_unsafe_public_payload(item_value)
        return
    if type(value) is list:
        for item_value in value:
            _reject_unsafe_public_payload(item_value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("public payload values must be strings, lists, dicts, bools, or null")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    allowed = {
        "configversion",
        "researchsourcememoryauthorityclaimquorumreportv0",
    }
    if normalized in allowed:
        return
    if normalized.startswith("researchsourcememoryauthorityclaimquorum"):
        return
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public string in {field_name}")
