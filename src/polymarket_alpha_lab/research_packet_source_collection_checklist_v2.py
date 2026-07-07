"""Phase 1 report-only research packet source collection checklist."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CONFIG_VERSION = (
    "research-packet-source-collection-checklist-v2"
)

RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS = (
    "official_source",
    "primary_source",
    "independent_corroboration",
    "contradiction_follow_up",
    "market_move_explanation",
    "resolution_rule_source",
    "timestamp_freshness",
)

_SOURCE_TYPES = frozenset(RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS[:-1])
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_REQUIRED_CHECK_COUNT = Decimal("7.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CHECKLIST_STATUSES = frozenset(("pass", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "empty_source_collection",
    "missing_official_source",
    "missing_primary_source",
    "missing_independent_corroboration",
    "missing_contradiction_follow_up",
    "missing_market_move_explanation",
    "missing_resolution_rule_source",
    "stale_source_timestamp",
    "source_collection_blocked",
    "source_collection_watch",
    "source_collection_pass",
)
_BLOCKING_MISSING_CHECKS = frozenset(
    (
        "official_source",
        "primary_source",
        "resolution_rule_source",
        "timestamp_freshness",
    ),
)


@dataclass(frozen=True)
class ResearchPacketSourceCollectionChecklistConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CONFIG_VERSION
    )
    max_source_age_minutes: Decimal = Decimal("1440.000000")
    min_independent_corroboration_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceCollectionChecklistConfig:
            raise TypeError(
                "ResearchPacketSourceCollectionChecklistConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceCollectionChecklistConfig:
            raise ValueError(
                "config must be exactly ResearchPacketSourceCollectionChecklistConfig",
            )
        _require_supported_config_version(self.config_version)
        object.__setattr__(
            self,
            "max_source_age_minutes",
            _require_positive_decimal(
                "max_source_age_minutes",
                self.max_source_age_minutes,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_corroboration_count",
            _require_positive_decimal(
                "min_independent_corroboration_count",
                self.min_independent_corroboration_count,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceCollectionChecklistEvidence:
    packet_id: str
    claim_id: str
    source_id: str
    source_type: str
    source_family: str
    observed_at: datetime
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceCollectionChecklistEvidence:
            raise TypeError(
                "ResearchPacketSourceCollectionChecklistEvidence does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceCollectionChecklistEvidence:
            raise ValueError(
                "evidence must be exactly "
                "ResearchPacketSourceCollectionChecklistEvidence",
            )
        for field_name in ("packet_id", "claim_id", "source_id", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_type",
            _require_source_type("source_type", self.source_type),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchPacketSourceCollectionChecklistPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceCollectionChecklistPublicPayloadItem:
            raise TypeError(
                "ResearchPacketSourceCollectionChecklistPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceCollectionChecklistPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchPacketSourceCollectionChecklistPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchPacketSourceCollectionChecklistRow:
    packet_id: str
    claim_id: str
    source_count: Decimal
    official_source_count: Decimal
    primary_source_count: Decimal
    independent_corroboration_count: Decimal
    contradiction_follow_up_count: Decimal
    market_move_explanation_count: Decimal
    resolution_rule_source_count: Decimal
    required_check_count: Decimal
    satisfied_check_count: Decimal
    completion_score: Decimal
    latest_source_observed_at: datetime | None
    latest_source_age_minutes: Decimal
    stale_source_count: Decimal
    official_source_present: bool
    primary_source_present: bool
    independent_corroboration_present: bool
    contradiction_follow_up_present: bool
    market_move_explanation_present: bool
    resolution_rule_source_present: bool
    timestamp_fresh: bool
    checklist_status: str
    satisfied_checks: tuple[str, ...]
    missing_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceCollectionChecklistRow:
            raise TypeError(
                "ResearchPacketSourceCollectionChecklistRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceCollectionChecklistRow:
            raise ValueError(
                "row must be exactly ResearchPacketSourceCollectionChecklistRow",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("claim_id", self.claim_id)
        for field_name in (
            "source_count",
            "official_source_count",
            "primary_source_count",
            "independent_corroboration_count",
            "contradiction_follow_up_count",
            "market_move_explanation_count",
            "resolution_rule_source_count",
            "required_check_count",
            "satisfied_check_count",
            "latest_source_age_minutes",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completion_score",
            _require_ratio_decimal("completion_score", self.completion_score),
        )
        if self.latest_source_observed_at is not None:
            object.__setattr__(
                self,
                "latest_source_observed_at",
                _as_utc("latest_source_observed_at", self.latest_source_observed_at),
            )
        for field_name in (
            "official_source_present",
            "primary_source_present",
            "independent_corroboration_present",
            "contradiction_follow_up_present",
            "market_move_explanation_present",
            "resolution_rule_source_present",
            "timestamp_fresh",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "checklist_status",
            _require_checklist_status("checklist_status", self.checklist_status),
        )
        object.__setattr__(
            self,
            "satisfied_checks",
            _normalize_checks("satisfied_checks", self.satisfied_checks),
        )
        object.__setattr__(
            self,
            "missing_checks",
            _normalize_checks("missing_checks", self.missing_checks),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceCollectionChecklistReport:
    generated_at: datetime
    config_version: str
    checklist_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_completion_score: Decimal
    rows: tuple[ResearchPacketSourceCollectionChecklistRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchPacketSourceCollectionChecklistPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceCollectionChecklistReport:
            raise TypeError(
                "ResearchPacketSourceCollectionChecklistReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceCollectionChecklistReport:
            raise ValueError(
                "report must be exactly ResearchPacketSourceCollectionChecklistReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        object.__setattr__(
            self,
            "checklist_status",
            _require_checklist_status("checklist_status", self.checklist_status),
        )
        for field_name in ("packet_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_completion_score",
            _require_ratio_decimal(
                "average_completion_score",
                self.average_completion_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketSourceCollectionChecklistReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_source_collection_checklist_v2_report(
    evidence: Sequence[ResearchPacketSourceCollectionChecklistEvidence],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceCollectionChecklistConfig | None = None,
    public_payload: Sequence[ResearchPacketSourceCollectionChecklistPublicPayloadItem] = (),
) -> ResearchPacketSourceCollectionChecklistReport:
    """Build a local report-only Phase 1 source collection checklist snapshot."""

    if config is None:
        config = ResearchPacketSourceCollectionChecklistConfig()
    if type(config) is not ResearchPacketSourceCollectionChecklistConfig:
        raise ValueError(
            "config must be a ResearchPacketSourceCollectionChecklistConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_evidence, generated_at, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "checklist_status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_completion_score": _average(
            tuple(row.completion_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketSourceCollectionChecklistReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    evidence: tuple[ResearchPacketSourceCollectionChecklistEvidence, ...],
    generated_at: datetime,
    config: ResearchPacketSourceCollectionChecklistConfig,
) -> tuple[ResearchPacketSourceCollectionChecklistRow, ...]:
    grouped: dict[
        tuple[str, str],
        list[ResearchPacketSourceCollectionChecklistEvidence],
    ] = {}
    for item in evidence:
        grouped.setdefault((item.packet_id, item.claim_id), []).append(item)
    rows = [
        _row_for_group(packet_id, claim_id, tuple(items), generated_at, config)
        for (packet_id, claim_id), items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_group(
    packet_id: str,
    claim_id: str,
    evidence: tuple[ResearchPacketSourceCollectionChecklistEvidence, ...],
    generated_at: datetime,
    config: ResearchPacketSourceCollectionChecklistConfig,
) -> ResearchPacketSourceCollectionChecklistRow:
    source_counts = {
        source_type: _decimal_count(
            sum(1 for item in evidence if item.source_type == source_type),
        )
        for source_type in sorted(_SOURCE_TYPES)
    }
    latest_observed_at = max((item.observed_at for item in evidence), default=None)
    latest_source_age_minutes = (
        _age_minutes(generated_at, latest_observed_at)
        if latest_observed_at is not None
        else _ZERO
    )
    stale_source_count = _decimal_count(
        sum(
            1
            for item in evidence
            if _age_minutes(generated_at, item.observed_at)
            > config.max_source_age_minutes
        ),
    )
    official_source_present = source_counts["official_source"] > _ZERO
    primary_source_present = source_counts["primary_source"] > _ZERO
    independent_corroboration_present = (
        source_counts["independent_corroboration"]
        >= config.min_independent_corroboration_count
    )
    contradiction_follow_up_present = (
        source_counts["contradiction_follow_up"] > _ZERO
    )
    market_move_explanation_present = (
        source_counts["market_move_explanation"] > _ZERO
    )
    resolution_rule_source_present = (
        source_counts["resolution_rule_source"] > _ZERO
    )
    timestamp_fresh = bool(evidence) and stale_source_count == _ZERO
    satisfied_checks = _satisfied_checks(
        official_source_present=official_source_present,
        primary_source_present=primary_source_present,
        independent_corroboration_present=independent_corroboration_present,
        contradiction_follow_up_present=contradiction_follow_up_present,
        market_move_explanation_present=market_move_explanation_present,
        resolution_rule_source_present=resolution_rule_source_present,
        timestamp_fresh=timestamp_fresh,
    )
    missing_checks = _missing_checks(satisfied_checks)
    checklist_status = _row_status(missing_checks)
    return ResearchPacketSourceCollectionChecklistRow(
        packet_id=packet_id,
        claim_id=claim_id,
        source_count=_decimal_count(len(evidence)),
        official_source_count=source_counts["official_source"],
        primary_source_count=source_counts["primary_source"],
        independent_corroboration_count=source_counts["independent_corroboration"],
        contradiction_follow_up_count=source_counts["contradiction_follow_up"],
        market_move_explanation_count=source_counts["market_move_explanation"],
        resolution_rule_source_count=source_counts["resolution_rule_source"],
        required_check_count=_REQUIRED_CHECK_COUNT,
        satisfied_check_count=_decimal_count(len(satisfied_checks)),
        completion_score=_completion_score(satisfied_checks),
        latest_source_observed_at=latest_observed_at,
        latest_source_age_minutes=latest_source_age_minutes,
        stale_source_count=stale_source_count,
        official_source_present=official_source_present,
        primary_source_present=primary_source_present,
        independent_corroboration_present=independent_corroboration_present,
        contradiction_follow_up_present=contradiction_follow_up_present,
        market_move_explanation_present=market_move_explanation_present,
        resolution_rule_source_present=resolution_rule_source_present,
        timestamp_fresh=timestamp_fresh,
        checklist_status=checklist_status,
        satisfied_checks=satisfied_checks,
        missing_checks=missing_checks,
        reason_codes=_row_reason_codes(missing_checks, checklist_status),
    )


def _satisfied_checks(
    *,
    official_source_present: bool,
    primary_source_present: bool,
    independent_corroboration_present: bool,
    contradiction_follow_up_present: bool,
    market_move_explanation_present: bool,
    resolution_rule_source_present: bool,
    timestamp_fresh: bool,
) -> tuple[str, ...]:
    present_by_check = {
        "official_source": official_source_present,
        "primary_source": primary_source_present,
        "independent_corroboration": independent_corroboration_present,
        "contradiction_follow_up": contradiction_follow_up_present,
        "market_move_explanation": market_move_explanation_present,
        "resolution_rule_source": resolution_rule_source_present,
        "timestamp_freshness": timestamp_fresh,
    }
    return tuple(
        check
        for check in RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS
        if present_by_check[check]
    )


def _missing_checks(satisfied_checks: tuple[str, ...]) -> tuple[str, ...]:
    satisfied = frozenset(satisfied_checks)
    return tuple(
        check
        for check in RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS
        if check not in satisfied
    )


def _completion_score(satisfied_checks: tuple[str, ...]) -> Decimal:
    return _quantize(_decimal_count(len(satisfied_checks)) / _REQUIRED_CHECK_COUNT)


def _row_reason_codes(
    missing_checks: tuple[str, ...],
    checklist_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for missing_check in missing_checks:
        if missing_check == "timestamp_freshness":
            reason_codes.append("stale_source_timestamp")
        else:
            reason_codes.append(f"missing_{missing_check}")
    reason_codes.append(f"source_collection_{checklist_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(missing_checks: tuple[str, ...]) -> str:
    if not missing_checks:
        return "pass"
    if any(check in _BLOCKING_MISSING_CHECKS for check in missing_checks):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[ResearchPacketSourceCollectionChecklistRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.checklist_status == "blocked" for row in rows):
        return "blocked"
    if any(row.checklist_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceCollectionChecklistRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_source_collection", "source_collection_blocked")
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchPacketSourceCollectionChecklistRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.checklist_status == status)


def _validate_row_consistency(row: ResearchPacketSourceCollectionChecklistRow) -> None:
    source_type_count = _quantize(
        row.official_source_count
        + row.primary_source_count
        + row.independent_corroboration_count
        + row.contradiction_follow_up_count
        + row.market_move_explanation_count
        + row.resolution_rule_source_count,
    )
    if row.source_count != source_type_count:
        raise ValueError("source_count must match source type counts")
    if row.required_check_count != _REQUIRED_CHECK_COUNT:
        raise ValueError("required_check_count must match checklist size")
    if row.satisfied_check_count != _decimal_count(len(row.satisfied_checks)):
        raise ValueError("satisfied_check_count must match satisfied_checks")
    if row.completion_score != _completion_score(row.satisfied_checks):
        raise ValueError("completion_score must match satisfied_checks")
    if row.satisfied_checks != _satisfied_checks(
        official_source_present=row.official_source_present,
        primary_source_present=row.primary_source_present,
        independent_corroboration_present=row.independent_corroboration_present,
        contradiction_follow_up_present=row.contradiction_follow_up_present,
        market_move_explanation_present=row.market_move_explanation_present,
        resolution_rule_source_present=row.resolution_rule_source_present,
        timestamp_fresh=row.timestamp_fresh,
    ):
        raise ValueError("satisfied_checks must match checklist booleans")
    if row.missing_checks != _missing_checks(row.satisfied_checks):
        raise ValueError("missing_checks must complement satisfied_checks")
    if row.checklist_status != _row_status(row.missing_checks):
        raise ValueError("checklist_status must match missing_checks")
    if row.reason_codes != _row_reason_codes(row.missing_checks, row.checklist_status):
        raise ValueError("reason_codes must match checklist status")
    if row.latest_source_observed_at is None and row.source_count > _ZERO:
        raise ValueError("latest_source_observed_at is required when sources exist")
    if row.latest_source_observed_at is not None and row.source_count == _ZERO:
        raise ValueError("latest_source_observed_at requires sources")
    if row.timestamp_fresh and row.stale_source_count != _ZERO:
        raise ValueError("timestamp_fresh rows must not include stale sources")


def _validate_report_consistency(
    report: ResearchPacketSourceCollectionChecklistReport,
) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_completion_score != _average(
        tuple(row.completion_score for row in report.rows),
    ):
        raise ValueError("average_completion_score must match rows")
    if report.checklist_status != _report_status(report.rows):
        raise ValueError("checklist_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_evidence(
    evidence: Sequence[ResearchPacketSourceCollectionChecklistEvidence],
) -> tuple[ResearchPacketSourceCollectionChecklistEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchPacketSourceCollectionChecklistEvidence] = []
    for item in evidence:
        if type(item) is not ResearchPacketSourceCollectionChecklistEvidence:
            raise ValueError(
                "evidence items must be "
                "ResearchPacketSourceCollectionChecklistEvidence",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.claim_id,
                item.observed_at,
                item.source_type,
                item.source_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchPacketSourceCollectionChecklistRow],
) -> tuple[ResearchPacketSourceCollectionChecklistRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchPacketSourceCollectionChecklistRow] = []
    for row in rows:
        if type(row) is not ResearchPacketSourceCollectionChecklistRow:
            raise ValueError(
                "rows must contain ResearchPacketSourceCollectionChecklistRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.claim_id)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchPacketSourceCollectionChecklistPublicPayloadItem],
) -> tuple[ResearchPacketSourceCollectionChecklistPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchPacketSourceCollectionChecklistPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchPacketSourceCollectionChecklistPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchPacketSourceCollectionChecklistPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_checks(
    field_name: str,
    checks: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(checks, (str, bytes)) or not isinstance(checks, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for check in checks:
        _require_public_identifier("check", check)
        if check not in RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS:
            raise ValueError(f"{field_name} must contain supported checks")
        if check not in normalized:
            normalized.append(check)
    return tuple(
        check
        for check in RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS
        if check in normalized
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_supported_config_version(value: object) -> str:
    config_version = _require_public_identifier("config_version", value)
    if config_version != DEFAULT_RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return config_version


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_source_type(field_name: str, value: object) -> str:
    source_type = _require_public_identifier(field_name, value)
    if source_type not in _SOURCE_TYPES:
        raise ValueError(f"{field_name} must be a supported source type")
    return source_type


def _require_checklist_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _CHECKLIST_STATUSES:
        raise ValueError(f"{field_name} must be a known checklist status")
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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _age_minutes(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at = _as_utc("generated_at", generated_at)
    observed_at = _as_utc("observed_at", observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    total_microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
        + delta.microseconds
    )
    return _quantize(Decimal(total_microseconds) / Decimal("60000000"))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchPacketSourceCollectionChecklistReport,
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CONFIG_VERSION",
    "RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS",
    "ResearchPacketSourceCollectionChecklistConfig",
    "ResearchPacketSourceCollectionChecklistEvidence",
    "ResearchPacketSourceCollectionChecklistPublicPayloadItem",
    "ResearchPacketSourceCollectionChecklistReport",
    "ResearchPacketSourceCollectionChecklistRow",
    "build_research_packet_source_collection_checklist_v2_report",
)
