"""Report-only bridge between source authority, claim support, and age decay."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_DECAY_BRIDGE_CONFIG_VERSION",
    "ResearchSourceClaimAuthorityDecayBridgeConfig",
    "ResearchSourceClaimAuthorityDecayBridgeInput",
    "ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount",
    "ResearchSourceClaimAuthorityDecayBridgeReport",
    "ResearchSourceClaimAuthorityDecayBridgeRow",
    "build_research_source_claim_authority_decay_bridge_report",
    "research_source_claim_authority_decay_bridge_report_payload",
)


DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_DECAY_BRIDGE_CONFIG_VERSION = (
    "research-source-claim-authority-decay-bridge-report-v0"
)

STATUSES = ("pass", "watch", "block")
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "market_id",
    "market_slug",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "sizing",
    "recommendation",
    "credential",
    "signature",
    "network",
    "database",
    "persist",
    "mutation",
    "buy",
    "sell",
)
_SUPPORTED_REASON_CODES = (
    "empty_candidates",
    "missing_supporting_candidates",
    "low_authority_support",
    "decayed_authority_support",
    "source_family_bridge_watch",
    "authority_decay_bridge_watch",
    "authority_decay_bridge_block",
    "authority_decay_bridge_pass",
    "fresh_authority_support",
)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityDecayBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_DECAY_BRIDGE_CONFIG_VERSION
    )
    max_authority_decay_age_seconds: Decimal = Decimal("86400.000000")
    min_source_family_count: Decimal = Decimal("2.000000")
    pass_bridge_score: Decimal = Decimal("0.700000")
    watch_bridge_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimAuthorityDecayBridgeConfig:
            raise TypeError(
                "ResearchSourceClaimAuthorityDecayBridgeConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityDecayBridgeConfig:
            raise ValueError(
                "config must be exactly ResearchSourceClaimAuthorityDecayBridgeConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_DECAY_BRIDGE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_authority_decay_age_seconds",
            _require_positive_decimal(
                "max_authority_decay_age_seconds",
                self.max_authority_decay_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_positive_count_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        for field_name in ("pass_bridge_score", "watch_bridge_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_bridge_score <= self.watch_bridge_score:
            raise ValueError("pass_bridge_score must be greater than watch_bridge_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityDecayBridgeInput:
    candidate_id: str
    claim_key: str
    source_family: str
    observed_at: datetime
    source_authority_score: Decimal
    claim_confidence_score: Decimal
    supports_claim: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimAuthorityDecayBridgeInput:
            raise TypeError(
                "ResearchSourceClaimAuthorityDecayBridgeInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityDecayBridgeInput:
            raise ValueError(
                "input must be exactly ResearchSourceClaimAuthorityDecayBridgeInput",
            )
        _require_candidate_identifier("candidate_id", self.candidate_id)
        _require_public_identifier("claim_key", self.claim_key)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("source_authority_score", "claim_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("supports_claim", self.supports_claim)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityDecayBridgeRow:
    claim_key: str
    candidate_count: Decimal
    supporting_candidate_count: Decimal
    source_family_count: Decimal
    average_authority_score: Decimal
    average_claim_confidence_score: Decimal
    average_decay_factor: Decimal
    bridge_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimAuthorityDecayBridgeRow:
            raise TypeError(
                "ResearchSourceClaimAuthorityDecayBridgeRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityDecayBridgeRow:
            raise ValueError("row must be exactly ResearchSourceClaimAuthorityDecayBridgeRow")
        _require_public_identifier("claim_key", self.claim_key)
        for field_name in (
            "candidate_count",
            "supporting_candidate_count",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_score",
            "average_claim_confidence_score",
            "average_decay_factor",
            "bridge_score",
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount:
            raise TypeError(
                "ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceClaimAuthorityDecayBridgeReport:
    generated_at: datetime
    config_version: str
    status: str
    claim_count: Decimal
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_bridge_score: Decimal | None
    min_bridge_score: Decimal | None
    rows: tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...]
    reason_code_counts: tuple[ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimAuthorityDecayBridgeReport:
            raise TypeError(
                "ResearchSourceClaimAuthorityDecayBridgeReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimAuthorityDecayBridgeReport:
            raise ValueError(
                "report must be exactly ResearchSourceClaimAuthorityDecayBridgeReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_DECAY_BRIDGE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
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
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_bridge_score", "min_bridge_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_claim_authority_decay_bridge_report(
    inputs: Sequence[ResearchSourceClaimAuthorityDecayBridgeInput],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimAuthorityDecayBridgeConfig | None = None,
) -> ResearchSourceClaimAuthorityDecayBridgeReport:
    if config is None:
        config = ResearchSourceClaimAuthorityDecayBridgeConfig()
    if type(config) is not ResearchSourceClaimAuthorityDecayBridgeConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimAuthorityDecayBridgeConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized_inputs, config, generated_at)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "claim_count": _decimal_count(len(rows)),
        "candidate_count": _decimal_count(len(normalized_inputs)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_bridge_score": _average_optional(
            tuple(row.bridge_score for row in rows),
        ),
        "min_bridge_score": min((row.bridge_score for row in rows), default=None),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimAuthorityDecayBridgeReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_authority_decay_bridge_report_payload(
    report: ResearchSourceClaimAuthorityDecayBridgeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceClaimAuthorityDecayBridgeReport:
        raise ValueError(
            "report must be a ResearchSourceClaimAuthorityDecayBridgeReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "ResearchSourceClaimAuthorityDecayBridgeReport.payload",
        payload,
        allow_json_containers=True,
    )
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def _build_rows(
    inputs: tuple[ResearchSourceClaimAuthorityDecayBridgeInput, ...],
    config: ResearchSourceClaimAuthorityDecayBridgeConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...]:
    grouped: dict[str, list[ResearchSourceClaimAuthorityDecayBridgeInput]] = {}
    for item in inputs:
        grouped.setdefault(item.claim_key, []).append(item)
    rows = tuple(
        _row_for_claim(claim_key, tuple(grouped[claim_key]), config, generated_at)
        for claim_key in sorted(grouped)
    )
    return rows


def _row_for_claim(
    claim_key: str,
    inputs: tuple[ResearchSourceClaimAuthorityDecayBridgeInput, ...],
    config: ResearchSourceClaimAuthorityDecayBridgeConfig,
    generated_at: datetime,
) -> ResearchSourceClaimAuthorityDecayBridgeRow:
    supporting = tuple(item for item in inputs if item.supports_claim)
    source_family_count = _decimal_count(len({item.source_family for item in supporting}))
    average_authority_score = _average_optional(
        tuple(item.source_authority_score for item in supporting),
    )
    average_claim_confidence_score = _average_optional(
        tuple(item.claim_confidence_score for item in supporting),
    )
    average_decay_factor = _average_optional(
        tuple(
            _decay_factor(
                _age_seconds(generated_at, item.observed_at),
                config.max_authority_decay_age_seconds,
            )
            for item in supporting
        ),
    )
    if average_authority_score is None or average_decay_factor is None:
        bridge_score = _ZERO
    else:
        bridge_score = _quantize(average_authority_score * average_decay_factor)
    if average_claim_confidence_score is None:
        average_claim_confidence_score = _ZERO
    if average_authority_score is None:
        average_authority_score = _ZERO
    if average_decay_factor is None:
        average_decay_factor = _ZERO
    status = _row_status(
        supporting_candidate_count=_decimal_count(len(supporting)),
        source_family_count=source_family_count,
        bridge_score=bridge_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        supporting_candidate_count=_decimal_count(len(supporting)),
        source_family_count=source_family_count,
        average_authority_score=average_authority_score,
        average_decay_factor=average_decay_factor,
        bridge_score=bridge_score,
        config=config,
        input_reason_codes=tuple(
            reason_code for item in inputs for reason_code in item.reason_codes
        ),
    )
    return ResearchSourceClaimAuthorityDecayBridgeRow(
        claim_key=claim_key,
        candidate_count=_decimal_count(len(inputs)),
        supporting_candidate_count=_decimal_count(len(supporting)),
        source_family_count=source_family_count,
        average_authority_score=average_authority_score,
        average_claim_confidence_score=average_claim_confidence_score,
        average_decay_factor=average_decay_factor,
        bridge_score=bridge_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    supporting_candidate_count: Decimal,
    source_family_count: Decimal,
    bridge_score: Decimal,
    config: ResearchSourceClaimAuthorityDecayBridgeConfig,
) -> str:
    if supporting_candidate_count == _ZERO or bridge_score < config.watch_bridge_score:
        return "block"
    if (
        source_family_count >= config.min_source_family_count
        and bridge_score >= config.pass_bridge_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    supporting_candidate_count: Decimal,
    source_family_count: Decimal,
    average_authority_score: Decimal,
    average_decay_factor: Decimal,
    bridge_score: Decimal,
    config: ResearchSourceClaimAuthorityDecayBridgeConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = list(input_reason_codes)
    if supporting_candidate_count == _ZERO:
        reason_codes.append("missing_supporting_candidates")
    if average_authority_score < config.watch_bridge_score:
        reason_codes.append("low_authority_support")
    if average_decay_factor == _ZERO:
        reason_codes.append("decayed_authority_support")
    elif average_decay_factor >= Decimal("0.750000"):
        reason_codes.append("fresh_authority_support")
    if source_family_count < config.min_source_family_count:
        reason_codes.append("source_family_bridge_watch")
    if status == "pass":
        reason_codes.append("authority_decay_bridge_pass")
    elif status == "watch":
        reason_codes.append("authority_decay_bridge_watch")
    else:
        reason_codes.append("authority_decay_bridge_block")
    if bridge_score < config.watch_bridge_score and supporting_candidate_count != _ZERO:
        reason_codes.append("decayed_authority_support")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _report_status(rows: tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_candidates",)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(counts)
    )


def _status_count(
    rows: tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    inputs: Sequence[ResearchSourceClaimAuthorityDecayBridgeInput],
) -> tuple[ResearchSourceClaimAuthorityDecayBridgeInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchSourceClaimAuthorityDecayBridgeInput:
            raise ValueError(
                "inputs must contain ResearchSourceClaimAuthorityDecayBridgeInput",
            )
        _require_hard_flags("input", item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.claim_key,
                item.source_family,
                item.observed_at,
                item.candidate_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimAuthorityDecayBridgeRow],
) -> tuple[ResearchSourceClaimAuthorityDecayBridgeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceClaimAuthorityDecayBridgeRow:
            raise ValueError(
                "rows must contain ResearchSourceClaimAuthorityDecayBridgeRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(normalized, key=lambda row: row.claim_key))
    if normalized != sorted_rows:
        raise ValueError("rows must be sorted by claim_key")
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount],
) -> tuple[ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(normalized, key=lambda count: count.reason_code))
    if normalized != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return normalized


def _validate_row_consistency(row: ResearchSourceClaimAuthorityDecayBridgeRow) -> None:
    if row.supporting_candidate_count > row.candidate_count:
        raise ValueError("supporting_candidate_count must not exceed candidate_count")
    if row.source_family_count > row.supporting_candidate_count:
        raise ValueError("source_family_count must not exceed supporting_candidate_count")
    if row.status == "pass" and "authority_decay_bridge_pass" not in row.reason_codes:
        raise ValueError("pass rows must include authority_decay_bridge_pass")
    if row.status == "watch" and "authority_decay_bridge_watch" not in row.reason_codes:
        raise ValueError("watch rows must include authority_decay_bridge_watch")
    if row.status == "block" and "authority_decay_bridge_block" not in row.reason_codes:
        raise ValueError("block rows must include authority_decay_bridge_block")


def _validate_report_consistency(
    report: ResearchSourceClaimAuthorityDecayBridgeReport,
) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.candidate_count != sum((row.candidate_count for row in report.rows), _ZERO):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_bridge_score != _average_optional(
        tuple(row.bridge_score for row in report.rows),
    ):
        raise ValueError("average_bridge_score must match rows")
    expected_min = min((row.bridge_score for row in report.rows), default=None)
    if report.min_bridge_score != expected_min:
        raise ValueError("min_bridge_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _decay_factor(age_seconds: Decimal, max_age_seconds: Decimal) -> Decimal:
    if age_seconds >= max_age_seconds:
        return _ZERO
    return _quantize(_ONE - (age_seconds / max_age_seconds))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_candidate_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or len(value) > 256:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "://" in value or "?" in value or "@" in value:
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    if value not in _SUPPORTED_REASON_CODES:
        raise ValueError(f"{field_name} must be supported")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        value = _require_reason_code("reason_code", reason_code)
        if value not in normalized:
            normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(
        reason_code for reason_code in _SUPPORTED_REASON_CODES if reason_code in normalized
    )


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _report_values_without_digest(
    report: ResearchSourceClaimAuthorityDecayBridgeReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if "candidate_id" in lowered:
        raise ValueError(f"{path}.{key} has unsafe public field")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
