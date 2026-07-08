from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_CONFIG_VERSION = (
    "research-market-resolution-evidence-freshness-exception-report-v1"
)
RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_STATUSES = (
    "pass",
    "watch",
    "block",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_ROW_SORT_STATUS_RANK = {"watch": 0, "pass": 1, "block": 2}
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market_id",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "database",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "network",
    "sign",
    "trade",
    "buy",
    "sell",
    "sizing",
    "notional",
    "recommendation",
)
_REASON_CODE_SEQUENCE = (
    "official_evidence_missing_block",
    "official_evidence_age_watch",
    "official_evidence_age_block",
    "independent_corroboration_missing_block",
    "independent_corroboration_age_watch",
    "independent_corroboration_age_block",
    "rule_ambiguity_pressure_watch",
    "rule_ambiguity_pressure_block",
    "unresolved_contradiction_count_watch",
    "unresolved_contradiction_count_block",
    "manual_escalation_urgency_watch",
    "manual_escalation_urgency_block",
    "resolution_evidence_freshness_exception_pass",
    "resolution_evidence_freshness_exception_watch",
    "resolution_evidence_freshness_exception_block",
)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceFreshnessExceptionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_CONFIG_VERSION
    )
    watch_official_evidence_age_seconds: Decimal = Decimal("600.000000")
    block_official_evidence_age_seconds: Decimal = Decimal("1800.000000")
    watch_independent_corroboration_age_seconds: Decimal = Decimal("900.000000")
    block_independent_corroboration_age_seconds: Decimal = Decimal("2700.000000")
    watch_rule_ambiguity_pressure: Decimal = Decimal("0.250000")
    block_rule_ambiguity_pressure: Decimal = Decimal("0.650000")
    watch_unresolved_contradiction_count: Decimal = Decimal("1.000000")
    block_unresolved_contradiction_count: Decimal = Decimal("3.000000")
    watch_manual_escalation_urgency: Decimal = Decimal("0.400000")
    block_manual_escalation_urgency: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceFreshnessExceptionConfig:
            raise TypeError(
                "ResearchMarketResolutionEvidenceFreshnessExceptionConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionEvidenceFreshnessExceptionConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_official_evidence_age_seconds",
            "block_official_evidence_age_seconds",
            "watch_independent_corroboration_age_seconds",
            "block_independent_corroboration_age_seconds",
            "watch_unresolved_contradiction_count",
            "block_unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_rule_ambiguity_pressure",
            "block_rule_ambiguity_pressure",
            "watch_manual_escalation_urgency",
            "block_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_block(
            "official_evidence_age_seconds",
            self.watch_official_evidence_age_seconds,
            self.block_official_evidence_age_seconds,
        )
        _require_watch_not_above_block(
            "independent_corroboration_age_seconds",
            self.watch_independent_corroboration_age_seconds,
            self.block_independent_corroboration_age_seconds,
        )
        _require_watch_not_above_block(
            "rule_ambiguity_pressure",
            self.watch_rule_ambiguity_pressure,
            self.block_rule_ambiguity_pressure,
        )
        _require_watch_not_above_block(
            "unresolved_contradiction_count",
            self.watch_unresolved_contradiction_count,
            self.block_unresolved_contradiction_count,
        )
        _require_watch_not_above_block(
            "manual_escalation_urgency",
            self.watch_manual_escalation_urgency,
            self.block_manual_escalation_urgency,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceFreshnessExceptionInput:
    resolution_case_key: str
    official_evidence_observed_at: datetime | None
    independent_corroboration_observed_at: datetime | None
    rule_ambiguity_pressure: Decimal
    unresolved_contradiction_count: Decimal
    manual_escalation_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceFreshnessExceptionInput:
            raise TypeError(
                "ResearchMarketResolutionEvidenceFreshnessExceptionInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionEvidenceFreshnessExceptionInput,
            "input",
        )
        _require_private_case_key("resolution_case_key", self.resolution_case_key)
        object.__setattr__(
            self,
            "official_evidence_observed_at",
            _as_optional_utc(
                "official_evidence_observed_at",
                self.official_evidence_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "independent_corroboration_observed_at",
            _as_optional_utc(
                "independent_corroboration_observed_at",
                self.independent_corroboration_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "rule_ambiguity_pressure",
            _require_probability_decimal(
                "rule_ambiguity_pressure",
                self.rule_ambiguity_pressure,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_contradiction_count",
            _require_nonnegative_decimal(
                "unresolved_contradiction_count",
                self.unresolved_contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "manual_escalation_urgency",
            _require_probability_decimal(
                "manual_escalation_urgency",
                self.manual_escalation_urgency,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceFreshnessExceptionRow:
    aggregate_row_number: Decimal
    evidence_exception_hash: str
    official_evidence_observed_at: datetime | None
    official_evidence_age_seconds: Decimal | None
    independent_corroboration_observed_at: datetime | None
    independent_corroboration_age_seconds: Decimal | None
    rule_ambiguity_pressure: Decimal
    unresolved_contradiction_count: Decimal
    manual_escalation_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceFreshnessExceptionRow:
            raise TypeError(
                "ResearchMarketResolutionEvidenceFreshnessExceptionRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionEvidenceFreshnessExceptionRow,
            "row",
        )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_sha256_digest("evidence_exception_hash", self.evidence_exception_hash)
        for field_name in (
            "official_evidence_observed_at",
            "independent_corroboration_observed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_evidence_age_seconds",
            "independent_corroboration_age_seconds",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_nonnegative_decimal(field_name, value),
                )
        object.__setattr__(
            self,
            "rule_ambiguity_pressure",
            _require_probability_decimal(
                "rule_ambiguity_pressure",
                self.rule_ambiguity_pressure,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_contradiction_count",
            _require_nonnegative_decimal(
                "unresolved_contradiction_count",
                self.unresolved_contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "manual_escalation_urgency",
            _require_probability_decimal(
                "manual_escalation_urgency",
                self.manual_escalation_urgency,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceFreshnessExceptionReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_official_evidence_age_seconds: Decimal | None
    max_independent_corroboration_age_seconds: Decimal | None
    max_rule_ambiguity_pressure: Decimal
    total_unresolved_contradiction_count: Decimal
    max_manual_escalation_urgency: Decimal
    rows: tuple[ResearchMarketResolutionEvidenceFreshnessExceptionRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceFreshnessExceptionReport:
            raise TypeError(
                "ResearchMarketResolutionEvidenceFreshnessExceptionReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionEvidenceFreshnessExceptionReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_official_evidence_age_seconds",
            "max_independent_corroboration_age_seconds",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_nonnegative_decimal(field_name, value),
                )
        for field_name in (
            "max_rule_ambiguity_pressure",
            "max_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_unresolved_contradiction_count",
            _require_nonnegative_decimal(
                "total_unresolved_contradiction_count",
                self.total_unresolved_contradiction_count,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_market_resolution_evidence_freshness_exception_report(
    observations: Sequence[ResearchMarketResolutionEvidenceFreshnessExceptionInput],
    *,
    config: ResearchMarketResolutionEvidenceFreshnessExceptionConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketResolutionEvidenceFreshnessExceptionReport:
    if config is None:
        config = ResearchMarketResolutionEvidenceFreshnessExceptionConfig()
    if type(config) is not ResearchMarketResolutionEvidenceFreshnessExceptionConfig:
        raise ValueError(
            "config must be a "
            "ResearchMarketResolutionEvidenceFreshnessExceptionConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    provisional_rows = tuple(
        _provisional_row(
            observation,
            config=config,
            generated_at=generated_at_utc,
        )
        for observation in _normalize_observations(observations)
    )
    rows = tuple(
        ResearchMarketResolutionEvidenceFreshnessExceptionRow(
            aggregate_row_number=_decimal_count(index),
            evidence_exception_hash=row_values["evidence_exception_hash"],
            official_evidence_observed_at=row_values["official_evidence_observed_at"],
            official_evidence_age_seconds=row_values["official_evidence_age_seconds"],
            independent_corroboration_observed_at=(
                row_values["independent_corroboration_observed_at"]
            ),
            independent_corroboration_age_seconds=(
                row_values["independent_corroboration_age_seconds"]
            ),
            rule_ambiguity_pressure=row_values["rule_ambiguity_pressure"],
            unresolved_contradiction_count=(
                row_values["unresolved_contradiction_count"]
            ),
            manual_escalation_urgency=row_values["manual_escalation_urgency"],
            status=row_values["status"],
            reason_codes=row_values["reason_codes"],
        )
        for index, row_values in enumerate(
            sorted(
                provisional_rows,
                key=lambda item: (
                    _ROW_SORT_STATUS_RANK[str(item["status"])],
                    str(item["evidence_exception_hash"]),
                ),
            ),
            start=1,
        )
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "max_official_evidence_age_seconds": _max_optional_decimal(
            tuple(row.official_evidence_age_seconds for row in rows),
        ),
        "max_independent_corroboration_age_seconds": _max_optional_decimal(
            tuple(row.independent_corroboration_age_seconds for row in rows),
        ),
        "max_rule_ambiguity_pressure": max(
            (row.rule_ambiguity_pressure for row in rows),
            default=_ZERO,
        ),
        "total_unresolved_contradiction_count": _quantize(
            sum((row.unresolved_contradiction_count for row in rows), _ZERO),
        ),
        "max_manual_escalation_urgency": max(
            (row.manual_escalation_urgency for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketResolutionEvidenceFreshnessExceptionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_resolution_evidence_freshness_exception_report_payload(
    report: ResearchMarketResolutionEvidenceFreshnessExceptionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketResolutionEvidenceFreshnessExceptionReport:
        raise ValueError(
            "report must be a "
            "ResearchMarketResolutionEvidenceFreshnessExceptionReport",
        )
    payload = _public_payload_from_values(_report_values_without_digest(report))
    payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload(
        "research_market_resolution_evidence_freshness_exception_report_payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def research_market_resolution_evidence_freshness_exception_report_digest(
    report: ResearchMarketResolutionEvidenceFreshnessExceptionReport,
) -> str:
    if type(report) is not ResearchMarketResolutionEvidenceFreshnessExceptionReport:
        raise ValueError(
            "report must be a "
            "ResearchMarketResolutionEvidenceFreshnessExceptionReport",
        )
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_market_resolution_evidence_freshness_exception_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    payload_copy = dict(payload)
    _reject_unsafe_public_payload(
        "research_market_resolution_evidence_freshness_exception_public_payload",
        payload_copy,
        allow_json_containers=True,
    )
    digest = payload_copy.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload_copy)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = _public_payload_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return payload_copy


def _provisional_row(
    observation: ResearchMarketResolutionEvidenceFreshnessExceptionInput,
    *,
    config: ResearchMarketResolutionEvidenceFreshnessExceptionConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    official_age = _age_seconds(
        "official_evidence_age_seconds",
        generated_at,
        observation.official_evidence_observed_at,
    )
    independent_age = _age_seconds(
        "independent_corroboration_age_seconds",
        generated_at,
        observation.independent_corroboration_observed_at,
    )
    reason_codes = _row_reason_codes(
        official_evidence_age_seconds=official_age,
        independent_corroboration_age_seconds=independent_age,
        rule_ambiguity_pressure=observation.rule_ambiguity_pressure,
        unresolved_contradiction_count=observation.unresolved_contradiction_count,
        manual_escalation_urgency=observation.manual_escalation_urgency,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return {
        "evidence_exception_hash": _sha256_text(observation.resolution_case_key),
        "official_evidence_observed_at": observation.official_evidence_observed_at,
        "official_evidence_age_seconds": official_age,
        "independent_corroboration_observed_at": (
            observation.independent_corroboration_observed_at
        ),
        "independent_corroboration_age_seconds": independent_age,
        "rule_ambiguity_pressure": observation.rule_ambiguity_pressure,
        "unresolved_contradiction_count": observation.unresolved_contradiction_count,
        "manual_escalation_urgency": observation.manual_escalation_urgency,
        "status": status,
        "reason_codes": reason_codes + (f"resolution_evidence_freshness_exception_{status}",),
    }


def _row_reason_codes(
    *,
    official_evidence_age_seconds: Decimal | None,
    independent_corroboration_age_seconds: Decimal | None,
    rule_ambiguity_pressure: Decimal,
    unresolved_contradiction_count: Decimal,
    manual_escalation_urgency: Decimal,
    config: ResearchMarketResolutionEvidenceFreshnessExceptionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_evidence_age_seconds is None:
        reason_codes.append("official_evidence_missing_block")
    elif official_evidence_age_seconds >= config.block_official_evidence_age_seconds:
        reason_codes.append("official_evidence_age_block")
    elif official_evidence_age_seconds >= config.watch_official_evidence_age_seconds:
        reason_codes.append("official_evidence_age_watch")

    if independent_corroboration_age_seconds is None:
        reason_codes.append("independent_corroboration_missing_block")
    elif (
        independent_corroboration_age_seconds
        >= config.block_independent_corroboration_age_seconds
    ):
        reason_codes.append("independent_corroboration_age_block")
    elif (
        independent_corroboration_age_seconds
        >= config.watch_independent_corroboration_age_seconds
    ):
        reason_codes.append("independent_corroboration_age_watch")

    if rule_ambiguity_pressure >= config.block_rule_ambiguity_pressure:
        reason_codes.append("rule_ambiguity_pressure_block")
    elif rule_ambiguity_pressure >= config.watch_rule_ambiguity_pressure:
        reason_codes.append("rule_ambiguity_pressure_watch")

    if unresolved_contradiction_count >= config.block_unresolved_contradiction_count:
        reason_codes.append("unresolved_contradiction_count_block")
    elif unresolved_contradiction_count >= config.watch_unresolved_contradiction_count:
        reason_codes.append("unresolved_contradiction_count_watch")

    if manual_escalation_urgency >= config.block_manual_escalation_urgency:
        reason_codes.append("manual_escalation_urgency_block")
    elif manual_escalation_urgency >= config.watch_manual_escalation_urgency:
        reason_codes.append("manual_escalation_urgency_watch")

    return _normalize_reason_codes(tuple(reason_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchMarketResolutionEvidenceFreshnessExceptionRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketResolutionEvidenceFreshnessExceptionRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != "resolution_evidence_freshness_exception_pass":
                reason_codes.append(reason_code)
    if not reason_codes:
        return ("resolution_evidence_freshness_exception_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchMarketResolutionEvidenceFreshnessExceptionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchMarketResolutionEvidenceFreshnessExceptionInput],
) -> tuple[ResearchMarketResolutionEvidenceFreshnessExceptionInput, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchMarketResolutionEvidenceFreshnessExceptionInput] = []
    for observation in observations:
        if type(observation) is not ResearchMarketResolutionEvidenceFreshnessExceptionInput:
            raise ValueError(
                "observations must contain "
                "ResearchMarketResolutionEvidenceFreshnessExceptionInput values",
            )
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketResolutionEvidenceFreshnessExceptionRow],
) -> tuple[ResearchMarketResolutionEvidenceFreshnessExceptionRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketResolutionEvidenceFreshnessExceptionRow] = []
    for row in rows:
        if type(row) is not ResearchMarketResolutionEvidenceFreshnessExceptionRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketResolutionEvidenceFreshnessExceptionRow values",
            )
        normalized.append(row)
    sorted_rows = tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.aggregate_row_number,
                _ROW_SORT_STATUS_RANK[row.status],
                row.evidence_exception_hash,
            ),
        ),
    )
    expected_row_numbers = tuple(_decimal_count(index) for index in range(1, len(sorted_rows) + 1))
    if tuple(row.aggregate_row_number for row in sorted_rows) != expected_row_numbers:
        raise ValueError("aggregate_row_number must be contiguous and deterministic")
    return sorted_rows


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _validate_row_consistency(
    row: ResearchMarketResolutionEvidenceFreshnessExceptionRow,
) -> None:
    if row.status != _status_from_reason_codes(
        tuple(
            reason_code
            for reason_code in row.reason_codes
            if not reason_code.startswith("resolution_evidence_freshness_exception_")
        ),
    ):
        raise ValueError("status must match row freshness exception reason codes")
    final_reason_code = f"resolution_evidence_freshness_exception_{row.status}"
    if final_reason_code not in row.reason_codes:
        raise ValueError("reason_codes must include the row status reason code")
    if row.status == "pass" and row.reason_codes != (
        "resolution_evidence_freshness_exception_pass",
    ):
        raise ValueError("pass rows must not include exception reason codes")


def _validate_report_consistency(
    report: ResearchMarketResolutionEvidenceFreshnessExceptionReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.max_official_evidence_age_seconds != _max_optional_decimal(
        tuple(row.official_evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("max_official_evidence_age_seconds must match rows")
    if report.max_independent_corroboration_age_seconds != _max_optional_decimal(
        tuple(row.independent_corroboration_age_seconds for row in report.rows),
    ):
        raise ValueError("max_independent_corroboration_age_seconds must match rows")
    if report.max_rule_ambiguity_pressure != max(
        (row.rule_ambiguity_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_rule_ambiguity_pressure must match rows")
    if report.total_unresolved_contradiction_count != _quantize(
        sum((row.unresolved_contradiction_count for row in report.rows), _ZERO),
    ):
        raise ValueError("total_unresolved_contradiction_count must match rows")
    if report.max_manual_escalation_urgency != max(
        (row.manual_escalation_urgency for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_manual_escalation_urgency must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_values_without_digest(
    report: ResearchMarketResolutionEvidenceFreshnessExceptionReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "row_count": report.row_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "max_official_evidence_age_seconds": report.max_official_evidence_age_seconds,
        "max_independent_corroboration_age_seconds": (
            report.max_independent_corroboration_age_seconds
        ),
        "max_rule_ambiguity_pressure": report.max_rule_ambiguity_pressure,
        "total_unresolved_contradiction_count": (
            report.total_unresolved_contradiction_count
        ),
        "max_manual_escalation_urgency": report.max_manual_escalation_urgency,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_payload_from_values(values: Mapping[str, object]) -> dict[str, Any]:
    rows = values["rows"]
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    payload = {
        "report_type": "resolution_evidence_freshness_exception",
        "generated_at": _json_ready(values["generated_at"]),
        "status": _json_ready(values["status"]),
        "row_count": _json_ready(values["row_count"]),
        "pass_count": _json_ready(values["pass_count"]),
        "watch_count": _json_ready(values["watch_count"]),
        "block_count": _json_ready(values["block_count"]),
        "max_official_evidence_age_seconds": _json_ready(
            values["max_official_evidence_age_seconds"],
        ),
        "max_independent_corroboration_age_seconds": _json_ready(
            values["max_independent_corroboration_age_seconds"],
        ),
        "max_rule_ambiguity_pressure": _json_ready(values["max_rule_ambiguity_pressure"]),
        "total_unresolved_contradiction_count": _json_ready(
            values["total_unresolved_contradiction_count"],
        ),
        "max_manual_escalation_urgency": _json_ready(
            values["max_manual_escalation_urgency"],
        ),
        "rows": [_row_public_payload(row) for row in rows],
        "reason_codes": _json_ready(values["reason_codes"]),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload(
        "research_market_resolution_evidence_freshness_exception_report_payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def _row_public_payload(
    row: ResearchMarketResolutionEvidenceFreshnessExceptionRow,
) -> dict[str, Any]:
    if type(row) is not ResearchMarketResolutionEvidenceFreshnessExceptionRow:
        raise ValueError(
            "rows must contain "
            "ResearchMarketResolutionEvidenceFreshnessExceptionRow values",
        )
    return {
        "aggregate_row_number": _json_ready(row.aggregate_row_number),
        "evidence_exception_hash": row.evidence_exception_hash,
        "official_evidence_observed_at": _json_ready(row.official_evidence_observed_at),
        "official_evidence_age_seconds": _json_ready(row.official_evidence_age_seconds),
        "independent_corroboration_observed_at": _json_ready(
            row.independent_corroboration_observed_at,
        ),
        "independent_corroboration_age_seconds": _json_ready(
            row.independent_corroboration_age_seconds,
        ),
        "rule_ambiguity_pressure": _json_ready(row.rule_ambiguity_pressure),
        "unresolved_contradiction_count": _json_ready(
            row.unresolved_contradiction_count,
        ),
        "manual_escalation_urgency": _json_ready(row.manual_escalation_urgency),
        "status": row.status,
        "reason_codes": _json_ready(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _public_payload_digest(_public_payload_from_values(values))


def _public_payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload(
        "research_market_resolution_evidence_freshness_exception_digest_payload",
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


def _age_seconds(
    field_name: str,
    generated_at: datetime,
    observed_at: datetime | None,
) -> Decimal | None:
    if observed_at is None:
        return None
    age = Decimal(str((_as_utc("generated_at", generated_at) - observed_at).total_seconds()))
    if age < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(age)


def _max_optional_decimal(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present = tuple(value for value in values if value is not None)
    if not present:
        return None
    return max(present)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_case_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank canonical string")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank canonical string")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or value not in RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_STATUSES
    ):
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_watch_not_above_block(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"watch_{field_name} must not exceed block_{field_name}")


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_CONFIG_VERSION",
    "RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_STATUSES",
    "ResearchMarketResolutionEvidenceFreshnessExceptionConfig",
    "ResearchMarketResolutionEvidenceFreshnessExceptionInput",
    "ResearchMarketResolutionEvidenceFreshnessExceptionReport",
    "ResearchMarketResolutionEvidenceFreshnessExceptionRow",
    "build_research_market_resolution_evidence_freshness_exception_report",
    "research_market_resolution_evidence_freshness_exception_report_digest",
    "research_market_resolution_evidence_freshness_exception_report_payload",
    "validate_research_market_resolution_evidence_freshness_exception_public_payload",
)
