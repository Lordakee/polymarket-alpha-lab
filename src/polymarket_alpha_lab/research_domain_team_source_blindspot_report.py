"""Pure report-only domain-team source blindspot reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_TEAM_SOURCE_BLINDSPOT_CONFIG_VERSION = (
    "research-domain-team-source-blindspot-report-v1"
)
SOURCE_BLINDSPOT_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_DIGEST_LENGTH = 64
_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "token",
    "private_key",
    "secret_key",
    "api_secret",
    "client_secret",
    "access_token",
    "bearer ",
    "auth",
    "wallet",
    "order",
    "trade",
    "trading",
    "buy",
    "sell",
    "fill",
    "position",
    "portfolio",
    "live",
    "execution",
    "signing",
    "mutation",
    "persist",
    "database",
    "dsn",
    "table_name",
    "table_names",
    "db_table",
    "database_table",
    "network",
    "requests",
    "urllib",
    "socket",
    "sqlite",
    "candidate_id",
    "candidate_ids",
    "candidate_slug",
    "candidate_question",
    "market_id",
    "market_slug",
    "market_question",
    "event_id",
    "source_url",
    "source_name",
    "source_text",
    "raw_source",
    "recommend",
    "sizing",
)
_REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "domain_team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_source_count",
        "total_missing_source_class_count",
        "total_stale_source_class_count",
        "max_dominant_source_class_share",
        "max_source_age_seconds",
        "report_status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "domain_team",
        "source_class_count",
        "total_source_count",
        "dominant_source_class_count",
        "dominant_source_class_share",
        "missing_source_class_count",
        "stale_source_class_count",
        "max_source_age_seconds",
        "source_blindspot_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "domain_team_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_source_count",
    "total_missing_source_class_count",
    "total_stale_source_class_count",
    "max_dominant_source_class_share",
    "max_source_age_seconds",
)
_ROW_DECIMAL_PAYLOAD_FIELDS = (
    "source_class_count",
    "total_source_count",
    "dominant_source_class_count",
    "dominant_source_class_share",
    "missing_source_class_count",
    "stale_source_class_count",
    "max_source_age_seconds",
)


@dataclass(frozen=True)
class ResearchDomainTeamSourceBlindspotConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_TEAM_SOURCE_BLINDSPOT_CONFIG_VERSION
    required_source_classes: tuple[str, ...] = ("official", "primary", "context")
    watch_dominant_source_class_share: Decimal = Decimal("0.650000")
    block_dominant_source_class_share: Decimal = Decimal("0.850000")
    watch_source_age_seconds: Decimal = Decimal("3600.000000")
    block_source_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamSourceBlindspotConfig, "config")
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "required_source_classes",
            _normalize_required_source_classes(self.required_source_classes),
        )
        for field_name in (
            "watch_dominant_source_class_share",
            "block_dominant_source_class_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_source_age_seconds", "block_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_dominant_source_class_share > self.block_dominant_source_class_share:
            raise ValueError(
                "watch_dominant_source_class_share must not exceed "
                "block_dominant_source_class_share",
            )
        if self.watch_source_age_seconds > self.block_source_age_seconds:
            raise ValueError(
                "watch_source_age_seconds must not exceed block_source_age_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainTeamSourceCoverageSnapshot:
    domain_team: str
    source_class: str
    source_count: Decimal
    latest_source_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamSourceCoverageSnapshot, "snapshot")
        _require_public_code("domain_team", self.domain_team)
        _require_public_code("source_class", self.source_class)
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchDomainTeamSourceBlindspotRow:
    domain_team: str
    source_class_count: Decimal
    total_source_count: Decimal
    dominant_source_class_count: Decimal
    dominant_source_class_share: Decimal
    missing_source_class_count: Decimal
    stale_source_class_count: Decimal
    max_source_age_seconds: Decimal
    source_blindspot_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamSourceBlindspotRow, "row")
        _require_public_code("domain_team", self.domain_team)
        for field_name in (
            "source_class_count",
            "total_source_count",
            "dominant_source_class_count",
            "dominant_source_class_share",
            "missing_source_class_count",
            "stale_source_class_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_unit_decimal(
            "dominant_source_class_share",
            self.dominant_source_class_share,
        )
        _require_status("source_blindspot_status", self.source_blindspot_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainTeamSourceBlindspotReport:
    generated_at: datetime
    config_version: str
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_source_count: Decimal
    total_missing_source_class_count: Decimal
    total_stale_source_class_count: Decimal
    max_dominant_source_class_share: Decimal
    max_source_age_seconds: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchDomainTeamSourceBlindspotRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamSourceBlindspotReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_source_count",
            "total_missing_source_class_count",
            "total_stale_source_class_count",
            "max_dominant_source_class_share",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_unit_decimal(
            "max_dominant_source_class_share",
            self.max_dominant_source_class_share,
        )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report")
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_team_source_blindspot_report_payload(self)


def build_research_domain_team_source_blindspot_report(
    snapshots: object,
    *,
    generated_at: datetime,
    config: ResearchDomainTeamSourceBlindspotConfig,
) -> ResearchDomainTeamSourceBlindspotReport:
    if type(config) is not ResearchDomainTeamSourceBlindspotConfig:
        raise ValueError("config must be a ResearchDomainTeamSourceBlindspotConfig")
    _require_hard_flags("config", config)
    rows = _rows_for_snapshots(_normalize_snapshots(snapshots), config=config)
    return ResearchDomainTeamSourceBlindspotReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        domain_team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_source_count=_sum_decimal(tuple(row.total_source_count for row in rows)),
        total_missing_source_class_count=_sum_decimal(
            tuple(row.missing_source_class_count for row in rows),
        ),
        total_stale_source_class_count=_sum_decimal(
            tuple(row.stale_source_class_count for row in rows),
        ),
        max_dominant_source_class_share=max(
            (row.dominant_source_class_share for row in rows),
            default=ZERO,
        ),
        max_source_age_seconds=max(
            (row.max_source_age_seconds for row in rows),
            default=ZERO,
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_domain_team_source_blindspot_report_payload(
    report: ResearchDomainTeamSourceBlindspotReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainTeamSourceBlindspotReport:
        raise ValueError("report must be a ResearchDomainTeamSourceBlindspotReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_domain_team_source_blindspot_report_payload(payload)
    return payload


def validate_research_domain_team_source_blindspot_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    _validate_public_report_payload_schema(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload")
    return True


def _rows_for_snapshots(
    snapshots: tuple[ResearchDomainTeamSourceCoverageSnapshot, ...],
    *,
    config: ResearchDomainTeamSourceBlindspotConfig,
) -> tuple[ResearchDomainTeamSourceBlindspotRow, ...]:
    grouped: dict[str, list[ResearchDomainTeamSourceCoverageSnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.domain_team, []).append(snapshot)
    return tuple(
        _row_for_domain_team(domain_team, tuple(grouped[domain_team]), config=config)
        for domain_team in sorted(grouped)
    )


def _row_for_domain_team(
    domain_team: str,
    snapshots: tuple[ResearchDomainTeamSourceCoverageSnapshot, ...],
    *,
    config: ResearchDomainTeamSourceBlindspotConfig,
) -> ResearchDomainTeamSourceBlindspotRow:
    source_counts: dict[str, Decimal] = {}
    latest_ages: dict[str, Decimal] = {}
    for snapshot in snapshots:
        source_counts[snapshot.source_class] = _sum_decimal(
            (source_counts.get(snapshot.source_class, ZERO), snapshot.source_count),
        )
        latest_ages[snapshot.source_class] = max(
            latest_ages.get(snapshot.source_class, ZERO),
            snapshot.latest_source_age_seconds,
        )
    total_source_count = _sum_decimal(tuple(source_counts.values()))
    dominant_source_class_count = max(source_counts.values(), default=ZERO)
    dominant_share = _ratio_or_zero(dominant_source_class_count, total_source_count)
    missing_source_class_count = _count(
        sum(
            1
            for source_class in config.required_source_classes
            if source_counts.get(source_class, ZERO) == ZERO
        ),
    )
    stale_source_class_count = _count(
        sum(
            1
            for source_class in config.required_source_classes
            if source_counts.get(source_class, ZERO) > ZERO
            and latest_ages.get(source_class, ZERO) >= config.watch_source_age_seconds
        ),
    )
    max_source_age_seconds = max(latest_ages.values(), default=ZERO)
    status = _row_status(
        total_source_count=total_source_count,
        dominant_source_class_share=dominant_share,
        missing_source_class_count=missing_source_class_count,
        max_source_age_seconds=max_source_age_seconds,
        config=config,
    )
    return ResearchDomainTeamSourceBlindspotRow(
        domain_team=domain_team,
        source_class_count=_count(len(source_counts)),
        total_source_count=total_source_count,
        dominant_source_class_count=dominant_source_class_count,
        dominant_source_class_share=dominant_share,
        missing_source_class_count=missing_source_class_count,
        stale_source_class_count=stale_source_class_count,
        max_source_age_seconds=max_source_age_seconds,
        source_blindspot_status=status,
        reason_codes=_row_reason_codes(
            dominant_source_class_share=dominant_share,
            missing_source_class_count=missing_source_class_count,
            max_source_age_seconds=max_source_age_seconds,
            source_blindspot_status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    total_source_count: Decimal,
    dominant_source_class_share: Decimal,
    missing_source_class_count: Decimal,
    max_source_age_seconds: Decimal,
    config: ResearchDomainTeamSourceBlindspotConfig,
) -> str:
    if total_source_count == ZERO:
        return "block"
    if (
        dominant_source_class_share >= config.block_dominant_source_class_share
        or max_source_age_seconds >= config.block_source_age_seconds
        or missing_source_class_count > ONE
    ):
        return "block"
    if (
        dominant_source_class_share >= config.watch_dominant_source_class_share
        or max_source_age_seconds >= config.watch_source_age_seconds
        or missing_source_class_count > ZERO
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    dominant_source_class_share: Decimal,
    missing_source_class_count: Decimal,
    max_source_age_seconds: Decimal,
    source_blindspot_status: str,
    config: ResearchDomainTeamSourceBlindspotConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if dominant_source_class_share >= config.block_dominant_source_class_share:
        reason_codes.append("dominant_source_class_share_block")
    elif dominant_source_class_share >= config.watch_dominant_source_class_share:
        reason_codes.append("dominant_source_class_share_watch")
    if max_source_age_seconds >= config.block_source_age_seconds:
        reason_codes.append("source_class_age_block")
    elif max_source_age_seconds >= config.watch_source_age_seconds:
        reason_codes.append("source_class_age_watch")
    if missing_source_class_count > ONE:
        reason_codes.append("missing_source_class_block")
    elif missing_source_class_count > ZERO:
        reason_codes.append("missing_source_class_watch")
    reason_codes.append(f"domain_team_source_blindspot_{source_blindspot_status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchDomainTeamSourceBlindspotRow, ...]) -> str:
    if not rows or any(row.source_blindspot_status == "block" for row in rows):
        return "block"
    if any(row.source_blindspot_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainTeamSourceBlindspotRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("domain_team_source_blindspot_report_block",)
    report_status = _report_status(rows)
    reason_codes = [f"domain_team_source_blindspot_report_{report_status}"]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _normalize_snapshots(
    value: object,
) -> tuple[ResearchDomainTeamSourceCoverageSnapshot, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        snapshots = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    for snapshot in snapshots:
        if type(snapshot) is not ResearchDomainTeamSourceCoverageSnapshot:
            raise ValueError(
                "snapshots must contain ResearchDomainTeamSourceCoverageSnapshot values",
            )
        _require_hard_flags("snapshot", snapshot)
    return tuple(
        sorted(
            snapshots,
            key=lambda item: (item.domain_team, item.source_class),
        ),
    )


def _normalize_rows(value: object) -> tuple[ResearchDomainTeamSourceBlindspotRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchDomainTeamSourceBlindspotRow:
            raise ValueError("rows must contain ResearchDomainTeamSourceBlindspotRow values")
        _require_hard_flags("row", row)
    normalized = tuple(sorted(rows, key=lambda row: row.domain_team))
    if rows != normalized:
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_required_source_classes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("required_source_classes must be a list or tuple")
    required = tuple(value)
    if not required:
        raise ValueError("required_source_classes must not be empty")
    normalized: list[str] = []
    for source_class in required:
        _require_public_code("required_source_classes", source_class)
        if source_class not in normalized:
            normalized.append(source_class)
    return tuple(sorted(normalized))


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _validate_row(row: ResearchDomainTeamSourceBlindspotRow) -> None:
    if row.source_class_count > row.total_source_count and row.total_source_count > ZERO:
        raise ValueError("source_class_count must not exceed total_source_count")
    if row.dominant_source_class_count > row.total_source_count:
        raise ValueError("dominant_source_class_count must not exceed total_source_count")
    expected_share = _ratio_or_zero(
        row.dominant_source_class_count,
        row.total_source_count,
    )
    if row.dominant_source_class_share != expected_share:
        raise ValueError("dominant_source_class_share must match row counts")


def _validate_report(report: ResearchDomainTeamSourceBlindspotReport) -> None:
    if report.domain_team_count != _count(len(report.rows)):
        raise ValueError("domain_team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_source_count != _sum_decimal(
        tuple(row.total_source_count for row in report.rows),
    ):
        raise ValueError("total_source_count must match rows")
    if report.total_missing_source_class_count != _sum_decimal(
        tuple(row.missing_source_class_count for row in report.rows),
    ):
        raise ValueError("total_missing_source_class_count must match rows")
    if report.total_stale_source_class_count != _sum_decimal(
        tuple(row.stale_source_class_count for row in report.rows),
    ):
        raise ValueError("total_stale_source_class_count must match rows")
    expected_max_share = max(
        (row.dominant_source_class_share for row in report.rows),
        default=ZERO,
    )
    if report.max_dominant_source_class_share != expected_max_share:
        raise ValueError("max_dominant_source_class_share must match rows")
    expected_max_age = max((row.max_source_age_seconds for row in report.rows), default=ZERO)
    if report.max_source_age_seconds != expected_max_age:
        raise ValueError("max_source_age_seconds must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchDomainTeamSourceBlindspotRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.source_blindspot_status == status))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_DOMAIN_TEAM_SOURCE_BLINDSPOT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _reject_unsafe_public_text("config_version", value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_BLINDSPOT_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_text(field_name, value)
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    _require_unit_decimal(field_name, normalized)
    return normalized


def _require_unit_decimal(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_derived_validation_digest(
    report: ResearchDomainTeamSourceBlindspotReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_public_payload_for_digest(
    report: ResearchDomainTeamSourceBlindspotReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    return payload


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime value", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON compatible")


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public text")


def _validate_public_report_payload_schema(payload: dict[str, Any]) -> None:
    if frozenset(payload) != _REPORT_PUBLIC_PAYLOAD_KEYS:
        raise ValueError("public report schema must match")
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    ResearchDomainTeamSourceBlindspotReport(
        generated_at=_datetime_from_public_payload(payload["generated_at"]),
        config_version=_payload_required_string(payload, "config_version"),
        domain_team_count=_decimal_from_public_payload(payload, "domain_team_count"),
        pass_count=_decimal_from_public_payload(payload, "pass_count"),
        watch_count=_decimal_from_public_payload(payload, "watch_count"),
        block_count=_decimal_from_public_payload(payload, "block_count"),
        total_source_count=_decimal_from_public_payload(payload, "total_source_count"),
        total_missing_source_class_count=_decimal_from_public_payload(
            payload,
            "total_missing_source_class_count",
        ),
        total_stale_source_class_count=_decimal_from_public_payload(
            payload,
            "total_stale_source_class_count",
        ),
        max_dominant_source_class_share=_decimal_from_public_payload(
            payload,
            "max_dominant_source_class_share",
        ),
        max_source_age_seconds=_decimal_from_public_payload(
            payload,
            "max_source_age_seconds",
        ),
        report_status=_payload_required_string(payload, "report_status"),
        reason_codes=_reason_codes_from_public_payload(payload, "reason_codes"),
        rows=rows,
        derived_validation_digest=_payload_required_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    row: object,
) -> ResearchDomainTeamSourceBlindspotRow:
    if type(row) is not dict:
        raise ValueError("rows must contain dict values")
    if frozenset(row) != _ROW_PUBLIC_PAYLOAD_KEYS:
        raise ValueError("public row schema must match")
    _require_payload_hard_flags(row)
    return ResearchDomainTeamSourceBlindspotRow(
        domain_team=_payload_required_string(row, "domain_team"),
        source_class_count=_decimal_from_public_payload(row, "source_class_count"),
        total_source_count=_decimal_from_public_payload(row, "total_source_count"),
        dominant_source_class_count=_decimal_from_public_payload(
            row,
            "dominant_source_class_count",
        ),
        dominant_source_class_share=_decimal_from_public_payload(
            row,
            "dominant_source_class_share",
        ),
        missing_source_class_count=_decimal_from_public_payload(
            row,
            "missing_source_class_count",
        ),
        stale_source_class_count=_decimal_from_public_payload(
            row,
            "stale_source_class_count",
        ),
        max_source_age_seconds=_decimal_from_public_payload(
            row,
            "max_source_age_seconds",
        ),
        source_blindspot_status=_payload_required_string(row, "source_blindspot_status"),
        reason_codes=_reason_codes_from_public_payload(row, "reason_codes"),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _decimal_from_public_payload(payload: dict[str, Any], field_name: str) -> Decimal:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _normalize_nonnegative_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_public_payload(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("generated_at must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at must be an ISO datetime string") from exc
    normalized = _as_utc("generated_at", parsed)
    if normalized.isoformat() != value:
        raise ValueError("generated_at must be a canonical UTC datetime string")
    return normalized


def _reason_codes_from_public_payload(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value))


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_TEAM_SOURCE_BLINDSPOT_CONFIG_VERSION",
    "SOURCE_BLINDSPOT_STATUSES",
    "ResearchDomainTeamSourceBlindspotConfig",
    "ResearchDomainTeamSourceBlindspotReport",
    "ResearchDomainTeamSourceBlindspotRow",
    "ResearchDomainTeamSourceCoverageSnapshot",
    "build_research_domain_team_source_blindspot_report",
    "research_domain_team_source_blindspot_report_payload",
    "validate_research_domain_team_source_blindspot_report_payload",
)
