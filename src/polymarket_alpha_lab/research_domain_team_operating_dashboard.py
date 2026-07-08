"""Report-only research domain team operating dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_DOMAIN_TEAM_OPERATING_DASHBOARD_CONFIG_VERSION = (
    "research-domain-team-operating-dashboard-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
RESEARCH_DOMAINS = (
    "basketball",
    "baseball",
    "crypto",
    "energy",
    "equities",
    "gold",
    "hockey",
    "macro",
    "oil",
    "politics",
    "rates",
    "soccer",
    "tennis",
    "weather",
)
REASON_CODES = (
    "domain_workload_pass",
    "domain_workload_watch",
    "domain_memory_coverage_pass",
    "domain_memory_coverage_watch",
    "domain_memory_coverage_block",
    "domain_pending_review_watch",
    "domain_stale_memory_watch",
    "domain_blocked_review_present",
    "domain_evidence_gap_present",
    "dashboard_all_domains_pass",
    "dashboard_domain_watch",
    "dashboard_domain_block",
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "account",
    "balance",
    "buy",
    "candidate_id",
    "cancel",
    "credential",
    "dsn",
    "market_id",
    "market_slug",
    "order",
    "position",
    "private_key",
    "question",
    "raw_candidate",
    "recommend",
    "replace",
    "sell",
    "sign",
    "source_ref",
    "source_reference",
    "source_text",
    "source_url",
    "table",
    "token",
    "trade",
    "trading",
    "url",
    "wallet",
)


@dataclass(frozen=True)
class ResearchDomainTeamOperatingDashboardConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_TEAM_OPERATING_DASHBOARD_CONFIG_VERSION
    workload_watch_threshold: Decimal = Decimal("12.000000")
    memory_coverage_watch_threshold: Decimal = Decimal("0.700000")
    memory_coverage_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamOperatingDashboardConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "workload_watch_threshold",
            _normalize_nonnegative_decimal(
                "workload_watch_threshold",
                self.workload_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "memory_coverage_watch_threshold",
            _normalize_ratio(
                "memory_coverage_watch_threshold",
                self.memory_coverage_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "memory_coverage_block_threshold",
            _normalize_ratio(
                "memory_coverage_block_threshold",
                self.memory_coverage_block_threshold,
            ),
        )
        if self.memory_coverage_block_threshold >= self.memory_coverage_watch_threshold:
            raise ValueError(
                "memory_coverage_block_threshold must be below "
                "memory_coverage_watch_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchDomainTeamOperatingObservation:
    domain: str
    workload_count: Decimal
    active_research_count: Decimal
    memory_covered_count: Decimal
    memory_total_count: Decimal
    pending_review_count: Decimal
    stale_memory_count: Decimal
    blocked_review_count: Decimal
    evidence_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamOperatingObservation, "observation")
        _require_domain(self.domain)
        for field_name in (
            "workload_count",
            "active_research_count",
            "memory_covered_count",
            "memory_total_count",
            "pending_review_count",
            "stale_memory_count",
            "blocked_review_count",
            "evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.active_research_count > self.workload_count:
            raise ValueError("active_research_count must not exceed workload_count")
        if self.memory_covered_count > self.memory_total_count:
            raise ValueError("memory_covered_count must not exceed memory_total_count")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchDomainTeamOperatingDashboardRow:
    domain: str
    public_status: str
    workload_count: Decimal
    active_research_count: Decimal
    memory_covered_count: Decimal
    memory_total_count: Decimal
    memory_coverage_ratio: Decimal
    pending_review_count: Decimal
    stale_memory_count: Decimal
    blocked_review_count: Decimal
    evidence_gap_count: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamOperatingDashboardRow, "row")
        _require_domain(self.domain)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "workload_count",
            "active_research_count",
            "memory_covered_count",
            "memory_total_count",
            "pending_review_count",
            "stale_memory_count",
            "blocked_review_count",
            "evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_coverage_ratio",
            _normalize_ratio("memory_coverage_ratio", self.memory_coverage_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(self),
            ),
        )


@dataclass(frozen=True)
class ResearchDomainTeamOperatingDashboardReport:
    generated_at: datetime
    config_version: str
    public_status: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_workload_count: Decimal
    total_active_research_count: Decimal
    total_memory_covered_count: Decimal
    total_memory_total_count: Decimal
    average_memory_coverage_ratio: Decimal
    total_pending_review_count: Decimal
    total_stale_memory_count: Decimal
    total_blocked_review_count: Decimal
    total_evidence_gap_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchDomainTeamOperatingDashboardRow, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamOperatingDashboardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_workload_count",
            "total_active_research_count",
            "total_memory_covered_count",
            "total_memory_total_count",
            "total_pending_review_count",
            "total_stale_memory_count",
            "total_blocked_review_count",
            "total_evidence_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_coverage_ratio",
            _normalize_ratio(
                "average_memory_coverage_ratio",
                self.average_memory_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(self),
            ),
        )


def build_research_domain_team_operating_dashboard(
    observations: Iterable[ResearchDomainTeamOperatingObservation],
    *,
    config: ResearchDomainTeamOperatingDashboardConfig,
    generated_at: datetime,
) -> ResearchDomainTeamOperatingDashboardReport:
    if type(config) is not ResearchDomainTeamOperatingDashboardConfig:
        raise ValueError("config must be a ResearchDomainTeamOperatingDashboardConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                )
                for observation in normalized
            ),
            key=lambda row: row.domain,
        ),
    )
    return ResearchDomainTeamOperatingDashboardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        public_status=_report_status(rows),
        domain_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_workload_count=_sum_row_decimal(rows, "workload_count"),
        total_active_research_count=_sum_row_decimal(rows, "active_research_count"),
        total_memory_covered_count=_sum_row_decimal(rows, "memory_covered_count"),
        total_memory_total_count=_sum_row_decimal(rows, "memory_total_count"),
        average_memory_coverage_ratio=_average_row_ratio(rows, "memory_coverage_ratio"),
        total_pending_review_count=_sum_row_decimal(rows, "pending_review_count"),
        total_stale_memory_count=_sum_row_decimal(rows, "stale_memory_count"),
        total_blocked_review_count=_sum_row_decimal(rows, "blocked_review_count"),
        total_evidence_gap_count=_sum_row_decimal(rows, "evidence_gap_count"),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_domain_team_operating_dashboard_payload(
    report: ResearchDomainTeamOperatingDashboardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainTeamOperatingDashboardReport:
        _validate_report_runtime(report)
        payload = _json_value(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        payload = _json_value(report, allow_decimal=False)
    else:
        raise ValueError("report must be a ResearchDomainTeamOperatingDashboardReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("research domain team operating dashboard payload", payload)
    _require_payload_flags(payload)
    _validate_payload_digest(payload)
    return payload


def research_domain_team_operating_dashboard_digest(
    report: ResearchDomainTeamOperatingDashboardReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_domain_team_operating_dashboard_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "public_status": payload["public_status"],
        "domain_count": payload["domain_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "total_workload_count": payload["total_workload_count"],
        "total_active_research_count": payload["total_active_research_count"],
        "total_memory_covered_count": payload["total_memory_covered_count"],
        "total_memory_total_count": payload["total_memory_total_count"],
        "average_memory_coverage_ratio": payload["average_memory_coverage_ratio"],
        "total_pending_review_count": payload["total_pending_review_count"],
        "total_stale_memory_count": payload["total_stale_memory_count"],
        "total_blocked_review_count": payload["total_blocked_review_count"],
        "total_evidence_gap_count": payload["total_evidence_gap_count"],
        "reason_codes": payload["reason_codes"],
        "report_validation_digest": payload["validation_digest"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("research domain team operating dashboard digest", digest)
    digest["digest_validation_digest"] = _digest_validation_digest(digest)
    return digest


def _row_from_observation(
    observation: ResearchDomainTeamOperatingObservation,
    *,
    config: ResearchDomainTeamOperatingDashboardConfig,
) -> ResearchDomainTeamOperatingDashboardRow:
    memory_coverage_ratio = _coverage_ratio(
        observation.memory_covered_count,
        observation.memory_total_count,
    )
    reason_codes = _row_reason_codes(
        observation,
        memory_coverage_ratio=memory_coverage_ratio,
        config=config,
    )
    return ResearchDomainTeamOperatingDashboardRow(
        domain=observation.domain,
        public_status=_row_status(reason_codes),
        workload_count=observation.workload_count,
        active_research_count=observation.active_research_count,
        memory_covered_count=observation.memory_covered_count,
        memory_total_count=observation.memory_total_count,
        memory_coverage_ratio=memory_coverage_ratio,
        pending_review_count=observation.pending_review_count,
        stale_memory_count=observation.stale_memory_count,
        blocked_review_count=observation.blocked_review_count,
        evidence_gap_count=observation.evidence_gap_count,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchDomainTeamOperatingObservation,
    *,
    memory_coverage_ratio: Decimal,
    config: ResearchDomainTeamOperatingDashboardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.workload_count > config.workload_watch_threshold:
        reason_codes.append("domain_workload_watch")
    else:
        reason_codes.append("domain_workload_pass")
    if memory_coverage_ratio < config.memory_coverage_block_threshold:
        reason_codes.append("domain_memory_coverage_block")
    elif memory_coverage_ratio < config.memory_coverage_watch_threshold:
        reason_codes.append("domain_memory_coverage_watch")
    else:
        reason_codes.append("domain_memory_coverage_pass")
    if observation.pending_review_count > ZERO:
        reason_codes.append("domain_pending_review_watch")
    if observation.stale_memory_count > ZERO:
        reason_codes.append("domain_stale_memory_watch")
    if observation.blocked_review_count > ZERO:
        reason_codes.append("domain_blocked_review_present")
    if observation.evidence_gap_count > ZERO:
        reason_codes.append("domain_evidence_gap_present")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "domain_memory_coverage_block" in reason_codes
        or "domain_blocked_review_present" in reason_codes
        or "domain_evidence_gap_present" in reason_codes
    ):
        return "block"
    if (
        "domain_workload_watch" in reason_codes
        or "domain_memory_coverage_watch" in reason_codes
        or "domain_pending_review_watch" in reason_codes
        or "domain_stale_memory_watch" in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDomainTeamOperatingDashboardRow, ...]) -> str:
    statuses = tuple(row.public_status for row in rows)
    if not statuses or "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainTeamOperatingDashboardRow, ...],
) -> tuple[str, ...]:
    values = {reason_code for row in rows for reason_code in row.reason_codes}
    status = _report_status(rows)
    if status == "block":
        values.add("dashboard_domain_block")
    elif status == "watch":
        values.add("dashboard_domain_watch")
    else:
        values.add("dashboard_all_domains_pass")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _normalize_observations(
    observations: Iterable[ResearchDomainTeamOperatingObservation],
) -> tuple[ResearchDomainTeamOperatingObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen_domains: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchDomainTeamOperatingObservation:
            raise ValueError(
                "observations must contain ResearchDomainTeamOperatingObservation",
            )
        _require_hard_flags(observation)
        if observation.domain in seen_domains:
            raise ValueError("observations must contain one row per domain")
        seen_domains.add(observation.domain)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchDomainTeamOperatingDashboardRow],
) -> tuple[ResearchDomainTeamOperatingDashboardRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    previous_domain = ""
    for row in normalized:
        if type(row) is not ResearchDomainTeamOperatingDashboardRow:
            raise ValueError("rows must contain ResearchDomainTeamOperatingDashboardRow")
        _require_hard_flags(row)
        if previous_domain and row.domain <= previous_domain:
            raise ValueError("rows must be deterministic by domain")
        previous_domain = row.domain
    return normalized


def _validate_row_consistency(row: ResearchDomainTeamOperatingDashboardRow) -> None:
    if row.active_research_count > row.workload_count:
        raise ValueError("active_research_count must not exceed workload_count")
    if row.memory_covered_count > row.memory_total_count:
        raise ValueError("memory_covered_count must not exceed memory_total_count")
    if row.memory_coverage_ratio != _coverage_ratio(
        row.memory_covered_count,
        row.memory_total_count,
    ):
        raise ValueError("memory_coverage_ratio must match memory counts")
    if row.public_status != _row_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")


def _validate_report_consistency(report: ResearchDomainTeamOperatingDashboardReport) -> None:
    if report.domain_count != _count_decimal(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")
    for field_name in (
        "workload_count",
        "active_research_count",
        "memory_covered_count",
        "memory_total_count",
        "pending_review_count",
        "stale_memory_count",
        "blocked_review_count",
        "evidence_gap_count",
    ):
        report_field_name = (
            "total_" + field_name
            if field_name != "active_research_count"
            else "total_active_research_count"
        )
        if getattr(report, report_field_name) != _sum_row_decimal(report.rows, field_name):
            raise ValueError(f"{report_field_name} must match rows")
    if report.average_memory_coverage_ratio != _average_row_ratio(
        report.rows,
        "memory_coverage_ratio",
    ):
        raise ValueError("average_memory_coverage_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_runtime(report: ResearchDomainTeamOperatingDashboardReport) -> None:
    _require_hard_flags(report)
    _as_utc("generated_at", report.generated_at)
    _require_public_identifier("config_version", report.config_version)
    _require_member("public_status", report.public_status, PUBLIC_STATUSES)
    _normalize_rows(report.rows)
    for row in report.rows:
        if row.validation_digest != _row_validation_digest(row):
            raise ValueError("validation_digest must match row")
    _validate_report_consistency(report)
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest must match report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    rows = _payload_rows(payload)
    row_digests = tuple(_payload_row_digest(row) for row in rows)
    for row, row_digest in zip(rows, row_digests, strict=True):
        if _payload_required_digest(row, "validation_digest") != row_digest:
            raise ValueError("validation_digest must match payload row")
    if _payload_required_digest(payload, "validation_digest") != _payload_report_digest(
        payload,
        row_digests,
    ):
        raise ValueError("validation_digest must match payload")
    _validate_payload_consistency(payload, rows)


def _validate_payload_consistency(
    payload: dict[str, Any],
    rows: tuple[dict[str, Any], ...],
) -> None:
    if _payload_required_decimal(payload, "domain_count") != _count_decimal(len(rows)):
        raise ValueError("domain_count must match payload rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if _payload_required_decimal(payload, field_name) != _payload_status_count(
            rows,
            status,
        ):
            raise ValueError(f"{field_name} must match payload rows")
    if _payload_required_member(payload, "public_status", PUBLIC_STATUSES) != (
        _payload_report_status(rows)
    ):
        raise ValueError("public_status must match payload rows")
    if _payload_required_reason_codes(payload, "reason_codes") != _payload_report_reason_codes(
        rows,
    ):
        raise ValueError("reason_codes must match payload rows")


def _payload_report_status(rows: tuple[dict[str, Any], ...]) -> str:
    statuses = tuple(_payload_required_member(row, "public_status", PUBLIC_STATUSES) for row in rows)
    if not statuses or "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _payload_report_reason_codes(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    values = {
        reason_code
        for row in rows
        for reason_code in _payload_required_reason_codes(row, "reason_codes")
    }
    status = _payload_report_status(rows)
    if status == "block":
        values.add("dashboard_domain_block")
    elif status == "watch":
        values.add("dashboard_domain_watch")
    else:
        values.add("dashboard_all_domains_pass")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _json_value(value: Any, *, allow_decimal: bool) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not allow_decimal:
            raise ValueError("JSON numeric value must use Decimal-derived strings")
        return _decimal_payload(value)
    if isinstance(value, datetime):
        return _datetime_payload(value)
    if type(value) is bool:
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item, allow_decimal=allow_decimal)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_value(item, allow_decimal=allow_decimal) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    normalized: list[dict[str, Any]] = []
    previous_domain = ""
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        domain = _payload_required_domain(row)
        if previous_domain and domain <= previous_domain:
            raise ValueError("rows must be deterministic by domain")
        previous_domain = domain
        normalized.append(row)
    return tuple(normalized)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_domain(payload: dict[str, Any]) -> str:
    value = _payload_required_string(payload, "domain")
    _require_domain(value)
    return value


def _payload_required_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_required_string(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_public_identifier(field_name, value)
    return value


def _payload_required_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    canonical = _decimal_payload(_normalize_nonnegative_decimal(field_name, decimal_value))
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(canonical)


def _payload_required_datetime(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    canonical = _datetime_payload(parsed)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return canonical


def _payload_required_reason_codes(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _payload_required_digest(payload: dict[str, Any], field_name: str) -> str:
    return _require_validation_digest(field_name, payload.get(field_name))


def _payload_status_count(rows: tuple[dict[str, Any], ...], status: str) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if _payload_required_member(row, "public_status", PUBLIC_STATUSES) == status
        ),
    )


def _payload_row_digest(row: dict[str, Any]) -> str:
    _require_payload_flags(row)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_domain_team_operating_dashboard_row",
            _payload_required_domain(row),
            _payload_required_member(row, "public_status", PUBLIC_STATUSES),
            _decimal_payload(_payload_required_decimal(row, "workload_count")),
            _decimal_payload(_payload_required_decimal(row, "active_research_count")),
            _decimal_payload(_payload_required_decimal(row, "memory_covered_count")),
            _decimal_payload(_payload_required_decimal(row, "memory_total_count")),
            _decimal_payload(_payload_required_decimal(row, "memory_coverage_ratio")),
            _decimal_payload(_payload_required_decimal(row, "pending_review_count")),
            _decimal_payload(_payload_required_decimal(row, "stale_memory_count")),
            _decimal_payload(_payload_required_decimal(row, "blocked_review_count")),
            _decimal_payload(_payload_required_decimal(row, "evidence_gap_count")),
            _string_sequence_payload(_payload_required_reason_codes(row, "reason_codes")),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_report_digest(
    payload: dict[str, Any],
    row_digests: tuple[str, ...],
) -> str:
    _require_payload_flags(payload)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_domain_team_operating_dashboard_report",
            _payload_required_datetime(payload, "generated_at"),
            _payload_required_string(payload, "config_version"),
            _payload_required_member(payload, "public_status", PUBLIC_STATUSES),
            _decimal_payload(_payload_required_decimal(payload, "domain_count")),
            _decimal_payload(_payload_required_decimal(payload, "pass_count")),
            _decimal_payload(_payload_required_decimal(payload, "watch_count")),
            _decimal_payload(_payload_required_decimal(payload, "block_count")),
            _decimal_payload(_payload_required_decimal(payload, "total_workload_count")),
            _decimal_payload(
                _payload_required_decimal(payload, "total_active_research_count"),
            ),
            _decimal_payload(_payload_required_decimal(payload, "total_memory_covered_count")),
            _decimal_payload(_payload_required_decimal(payload, "total_memory_total_count")),
            _decimal_payload(
                _payload_required_decimal(payload, "average_memory_coverage_ratio"),
            ),
            _decimal_payload(
                _payload_required_decimal(payload, "total_pending_review_count"),
            ),
            _decimal_payload(_payload_required_decimal(payload, "total_stale_memory_count")),
            _decimal_payload(
                _payload_required_decimal(payload, "total_blocked_review_count"),
            ),
            _decimal_payload(_payload_required_decimal(payload, "total_evidence_gap_count")),
            _string_sequence_payload(_payload_required_reason_codes(payload, "reason_codes")),
            _string_sequence_payload(row_digests),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _row_validation_digest(row: ResearchDomainTeamOperatingDashboardRow) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_domain_team_operating_dashboard_row",
            row.domain,
            row.public_status,
            _decimal_payload(row.workload_count),
            _decimal_payload(row.active_research_count),
            _decimal_payload(row.memory_covered_count),
            _decimal_payload(row.memory_total_count),
            _decimal_payload(row.memory_coverage_ratio),
            _decimal_payload(row.pending_review_count),
            _decimal_payload(row.stale_memory_count),
            _decimal_payload(row.blocked_review_count),
            _decimal_payload(row.evidence_gap_count),
            _string_sequence_payload(row.reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _report_validation_digest(report: ResearchDomainTeamOperatingDashboardReport) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_domain_team_operating_dashboard_report",
            _datetime_payload(report.generated_at),
            report.config_version,
            report.public_status,
            _decimal_payload(report.domain_count),
            _decimal_payload(report.pass_count),
            _decimal_payload(report.watch_count),
            _decimal_payload(report.block_count),
            _decimal_payload(report.total_workload_count),
            _decimal_payload(report.total_active_research_count),
            _decimal_payload(report.total_memory_covered_count),
            _decimal_payload(report.total_memory_total_count),
            _decimal_payload(report.average_memory_coverage_ratio),
            _decimal_payload(report.total_pending_review_count),
            _decimal_payload(report.total_stale_memory_count),
            _decimal_payload(report.total_blocked_review_count),
            _decimal_payload(report.total_evidence_gap_count),
            _string_sequence_payload(report.reason_codes),
            _string_sequence_payload(tuple(row.validation_digest for row in report.rows)),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _digest_validation_digest(digest: dict[str, Any]) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_domain_team_operating_dashboard_digest",
            str(digest["generated_at"]),
            str(digest["config_version"]),
            str(digest["public_status"]),
            str(digest["domain_count"]),
            str(digest["pass_count"]),
            str(digest["watch_count"]),
            str(digest["block_count"]),
            str(digest["total_workload_count"]),
            str(digest["total_active_research_count"]),
            str(digest["total_memory_covered_count"]),
            str(digest["total_memory_total_count"]),
            str(digest["average_memory_coverage_ratio"]),
            str(digest["total_pending_review_count"]),
            str(digest["total_stale_memory_count"]),
            str(digest["total_blocked_review_count"]),
            str(digest["total_evidence_gap_count"]),
            _string_sequence_payload(tuple(digest["reason_codes"])),
            str(digest["report_validation_digest"]),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _normalize_validation_digest(
    field_name: str,
    value: object,
    expected_digest: str,
) -> str:
    if value == "":
        return expected_digest
    digest = _require_validation_digest(field_name, value)
    if digest != expected_digest:
        raise ValueError(f"{field_name} must match derived values")
    return digest


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _hash_parts(parts: tuple[str, ...]) -> str:
    rendered = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _coverage_ratio(covered: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("memory_coverage_ratio", covered / total)


def _average_row_ratio(
    rows: tuple[ResearchDomainTeamOperatingDashboardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio(
            field_name,
            sum(getattr(row, field_name) for row in rows) / Decimal(len(rows)),
        )


def _status_count(
    rows: tuple[ResearchDomainTeamOperatingDashboardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _sum_row_decimal(
    rows: tuple[ResearchDomainTeamOperatingDashboardRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count_decimal(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative Decimal")
    return _quantize_decimal(value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return str(_quantize_decimal(value))


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of reason codes")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple of reason codes") from exc
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    normalized: list[str] = []
    for item in items:
        _require_member("reason_code", item, REASON_CODES)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _string_sequence_payload(values: tuple[str, ...]) -> str:
    return "\x1f".join(values)


def _require_domain(value: object) -> None:
    _require_member("domain", value, RESEARCH_DOMAINS)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")
    _reject_unsafe_public_text(field_name, value)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    require_paper_only_flags(value.__class__.__name__, value)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    try:
        reject_unsafe_surface_fields(label, value)
    except ValueError as exc:
        raise ValueError(f"unsafe public field in {label}") from exc
    _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_value(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_value(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_TEAM_OPERATING_DASHBOARD_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "RESEARCH_DOMAINS",
    "ResearchDomainTeamOperatingDashboardConfig",
    "ResearchDomainTeamOperatingDashboardReport",
    "ResearchDomainTeamOperatingDashboardRow",
    "ResearchDomainTeamOperatingObservation",
    "build_research_domain_team_operating_dashboard",
    "research_domain_team_operating_dashboard_digest",
    "research_domain_team_operating_dashboard_payload",
)
