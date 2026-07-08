"""Pure read-only aggregate event resolution clock risk report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_CLOCK_RISK_CONFIG_VERSION = (
    "research-event-resolution-clock-risk-report-v0"
)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_SECONDS = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CLOCK_RISK_STATUSES = ("pass", "watch", "block")
REPORT_REASON_CODES = (
    "resolution_clock_risk_clear",
    "resolution_deadline_pressure_present",
    "evidence_freshness_gap_present",
    "rule_ambiguity_present",
    "pending_source_pressure_present",
)
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "auth",
    "account",
    "balance",
    "candidate",
    "cancel",
    "database",
    "dsn",
    "exchange_mutation",
    "live",
    "market_id",
    "market_slug",
    "network",
    "order",
    "persist",
    "private_key",
    "question",
    "raw_text",
    "recommend",
    "replace",
    "sign",
    "size",
    "slug",
    "source_text",
    "source_url",
    "table",
    "token",
    "trade",
    "url",
    "wallet",
)
CONFIG_DECIMAL_PAYLOAD_FIELDS = (
    "near_deadline_window_seconds_threshold",
    "stale_evidence_age_seconds_threshold",
    "watch_clock_risk_score_threshold",
    "block_clock_risk_score_threshold",
)
SNAPSHOT_DECIMAL_PAYLOAD_FIELDS = (
    "event_count",
    "rule_ambiguity_score",
    "pending_source_count",
)
SNAPSHOT_DATETIME_PAYLOAD_FIELDS = (
    "resolution_deadline_at",
    "evidence_observed_at",
)
REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "snapshot_count",
    "event_count",
    "near_deadline_event_count",
    "stale_evidence_event_count",
    "pending_source_count",
    "min_deadline_window_seconds",
    "max_evidence_age_seconds",
    "max_rule_ambiguity_score",
    "deadline_proximity_ratio",
    "evidence_staleness_ratio",
    "rule_ambiguity_ratio",
    "pending_source_pressure_ratio",
    "clock_risk_score",
)
SNAPSHOT_PAYLOAD_KEYS = (
    *SNAPSHOT_DECIMAL_PAYLOAD_FIELDS,
    *SNAPSHOT_DATETIME_PAYLOAD_FIELDS,
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *CONFIG_DECIMAL_PAYLOAD_FIELDS,
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "source_snapshots",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchEventResolutionClockRiskConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_RESOLUTION_CLOCK_RISK_CONFIG_VERSION
    near_deadline_window_seconds_threshold: Decimal = Decimal("3600.000000")
    stale_evidence_age_seconds_threshold: Decimal = Decimal("14400.000000")
    watch_clock_risk_score_threshold: Decimal = Decimal("0.250000")
    block_clock_risk_score_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClockRiskConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLOCK_RISK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "near_deadline_window_seconds_threshold",
            "stale_evidence_age_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_clock_risk_score_threshold",
            "block_clock_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_clock_risk_score_threshold <= self.watch_clock_risk_score_threshold:
            raise ValueError(
                "block_clock_risk_score_threshold must exceed "
                "watch_clock_risk_score_threshold",
            )
        require_paper_only_flags("research event resolution clock risk config", self)


@dataclass(frozen=True)
class ResearchEventResolutionClockRiskSnapshot:
    event_count: Decimal
    resolution_deadline_at: datetime
    evidence_observed_at: datetime
    rule_ambiguity_score: Decimal
    pending_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClockRiskSnapshot:
            raise ValueError("snapshot must be exact")
        for field_name in ("event_count", "pending_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.pending_source_count > self.event_count:
            raise ValueError("pending_source_count must not exceed event_count")
        object.__setattr__(
            self,
            "rule_ambiguity_score",
            _normalize_ratio("rule_ambiguity_score", self.rule_ambiguity_score),
        )
        for field_name in SNAPSHOT_DATETIME_PAYLOAD_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("research event resolution clock risk snapshot", self)


@dataclass(frozen=True)
class ResearchEventResolutionClockRiskReport:
    generated_at: datetime
    config_version: str
    near_deadline_window_seconds_threshold: Decimal
    stale_evidence_age_seconds_threshold: Decimal
    watch_clock_risk_score_threshold: Decimal
    block_clock_risk_score_threshold: Decimal
    snapshot_count: Decimal
    event_count: Decimal
    near_deadline_event_count: Decimal
    stale_evidence_event_count: Decimal
    pending_source_count: Decimal
    min_deadline_window_seconds: Decimal
    max_evidence_age_seconds: Decimal
    max_rule_ambiguity_score: Decimal
    deadline_proximity_ratio: Decimal
    evidence_staleness_ratio: Decimal
    rule_ambiguity_ratio: Decimal
    pending_source_pressure_ratio: Decimal
    clock_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    source_snapshots: tuple[ResearchEventResolutionClockRiskSnapshot, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClockRiskReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLOCK_RISK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "near_deadline_window_seconds_threshold",
            "stale_evidence_age_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_clock_risk_score_threshold",
            "block_clock_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_clock_risk_score_threshold <= self.watch_clock_risk_score_threshold:
            raise ValueError(
                "block_clock_risk_score_threshold must exceed "
                "watch_clock_risk_score_threshold",
            )
        for field_name in (
            "snapshot_count",
            "event_count",
            "near_deadline_event_count",
            "stale_evidence_event_count",
            "pending_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_deadline_window_seconds", "max_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_rule_ambiguity_score",
            "deadline_proximity_ratio",
            "evidence_staleness_ratio",
            "rule_ambiguity_ratio",
            "pending_source_pressure_ratio",
            "clock_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, CLOCK_RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_snapshots",
            _normalize_snapshots(self.source_snapshots),
        )
        require_paper_only_flags("research event resolution clock risk report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("research event resolution clock risk report", self)
        _validate_derived_validation_digest(self)


def build_research_event_resolution_clock_risk_report(
    snapshots: list[ResearchEventResolutionClockRiskSnapshot]
    | tuple[ResearchEventResolutionClockRiskSnapshot, ...],
    *,
    config: ResearchEventResolutionClockRiskConfig,
    generated_at: datetime,
) -> ResearchEventResolutionClockRiskReport:
    if type(config) is not ResearchEventResolutionClockRiskConfig:
        raise ValueError("config must be a ResearchEventResolutionClockRiskConfig")
    require_paper_only_flags("research event resolution clock risk config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_snapshots = _normalize_snapshots(snapshots)
    for snapshot in source_snapshots:
        if snapshot.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")

    snapshot_count = _count(len(source_snapshots))
    event_count = _sum_count(snapshot.event_count for snapshot in source_snapshots)
    near_deadline_event_count = _sum_count(
        snapshot.event_count
        for snapshot in source_snapshots
        if _deadline_window_seconds(generated_at, snapshot.resolution_deadline_at)
        <= config.near_deadline_window_seconds_threshold
    )
    stale_evidence_event_count = _sum_count(
        snapshot.event_count
        for snapshot in source_snapshots
        if _age_seconds(generated_at, snapshot.evidence_observed_at)
        >= config.stale_evidence_age_seconds_threshold
    )
    pending_source_count = _sum_count(
        snapshot.pending_source_count for snapshot in source_snapshots
    )
    weighted_rule_ambiguity = _weighted_ratio(
        (
            (snapshot.rule_ambiguity_score, snapshot.event_count)
            for snapshot in source_snapshots
        ),
        event_count,
    )
    deadline_proximity_ratio = _ratio(near_deadline_event_count, event_count)
    evidence_staleness_ratio = _ratio(stale_evidence_event_count, event_count)
    pending_source_pressure_ratio = _ratio(pending_source_count, event_count)
    clock_risk_score = _clock_risk_score(
        (
            deadline_proximity_ratio,
            evidence_staleness_ratio,
            weighted_rule_ambiguity,
            pending_source_pressure_ratio,
        ),
    )
    status = _status(
        clock_risk_score,
        watch_threshold=config.watch_clock_risk_score_threshold,
        block_threshold=config.block_clock_risk_score_threshold,
    )
    reason_codes = _reason_codes(
        deadline_proximity_ratio=deadline_proximity_ratio,
        evidence_staleness_ratio=evidence_staleness_ratio,
        rule_ambiguity_ratio=weighted_rule_ambiguity,
        pending_source_pressure_ratio=pending_source_pressure_ratio,
    )
    min_deadline_window_seconds = _min_seconds(
        _deadline_window_seconds(generated_at, snapshot.resolution_deadline_at)
        for snapshot in source_snapshots
    )
    max_evidence_age_seconds = _max_seconds(
        _age_seconds(generated_at, snapshot.evidence_observed_at)
        for snapshot in source_snapshots
    )
    max_rule_ambiguity_score = max(
        (snapshot.rule_ambiguity_score for snapshot in source_snapshots),
        default=ZERO_RATIO,
    )

    return ResearchEventResolutionClockRiskReport(
        generated_at=generated_at,
        config_version=config.config_version,
        near_deadline_window_seconds_threshold=(
            config.near_deadline_window_seconds_threshold
        ),
        stale_evidence_age_seconds_threshold=config.stale_evidence_age_seconds_threshold,
        watch_clock_risk_score_threshold=config.watch_clock_risk_score_threshold,
        block_clock_risk_score_threshold=config.block_clock_risk_score_threshold,
        snapshot_count=snapshot_count,
        event_count=event_count,
        near_deadline_event_count=near_deadline_event_count,
        stale_evidence_event_count=stale_evidence_event_count,
        pending_source_count=pending_source_count,
        min_deadline_window_seconds=min_deadline_window_seconds,
        max_evidence_age_seconds=max_evidence_age_seconds,
        max_rule_ambiguity_score=max_rule_ambiguity_score,
        deadline_proximity_ratio=deadline_proximity_ratio,
        evidence_staleness_ratio=evidence_staleness_ratio,
        rule_ambiguity_ratio=weighted_rule_ambiguity,
        pending_source_pressure_ratio=pending_source_pressure_ratio,
        clock_risk_score=clock_risk_score,
        status=status,
        reason_codes=reason_codes,
        source_snapshots=source_snapshots,
        derived_validation_digest=_derived_validation_digest(
            generated_at=generated_at,
            config_version=config.config_version,
            near_deadline_window_seconds_threshold=(
                config.near_deadline_window_seconds_threshold
            ),
            stale_evidence_age_seconds_threshold=(
                config.stale_evidence_age_seconds_threshold
            ),
            watch_clock_risk_score_threshold=config.watch_clock_risk_score_threshold,
            block_clock_risk_score_threshold=config.block_clock_risk_score_threshold,
            snapshot_count=snapshot_count,
            event_count=event_count,
            near_deadline_event_count=near_deadline_event_count,
            stale_evidence_event_count=stale_evidence_event_count,
            pending_source_count=pending_source_count,
            min_deadline_window_seconds=min_deadline_window_seconds,
            max_evidence_age_seconds=max_evidence_age_seconds,
            max_rule_ambiguity_score=max_rule_ambiguity_score,
            deadline_proximity_ratio=deadline_proximity_ratio,
            evidence_staleness_ratio=evidence_staleness_ratio,
            rule_ambiguity_ratio=weighted_rule_ambiguity,
            pending_source_pressure_ratio=pending_source_pressure_ratio,
            clock_risk_score=clock_risk_score,
            status=status,
            reason_codes=reason_codes,
            source_snapshots=source_snapshots,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )


def research_event_resolution_clock_risk_payload(
    report: ResearchEventResolutionClockRiskReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionClockRiskReport:
        require_paper_only_flags("research event resolution clock risk report", report)
        reject_unsafe_surface_fields("research event resolution clock risk report", report)
        _reject_unsafe_public_payload("research event resolution clock risk report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        reject_unsafe_surface_fields("research event resolution clock risk payload", report)
        _reject_unsafe_public_payload("research event resolution clock risk payload", report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError("report must be a ResearchEventResolutionClockRiskReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    require_paper_only_flags("research event resolution clock risk payload", _DictFlags(payload))
    return payload


def serialize_research_event_resolution_clock_risk_payload(
    report: ResearchEventResolutionClockRiskReport | dict[str, Any],
) -> str:
    payload = research_event_resolution_clock_risk_payload(report)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def research_event_resolution_clock_risk_payload_digest(
    report: ResearchEventResolutionClockRiskReport | dict[str, Any],
) -> str:
    payload = research_event_resolution_clock_risk_payload(report)
    return _payload_derived_validation_digest(payload)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _validate_report(report: ResearchEventResolutionClockRiskReport) -> None:
    if report.snapshot_count != _count(len(report.source_snapshots)):
        raise ValueError("snapshot_count must match source_snapshots")
    if report.event_count != _sum_count(
        snapshot.event_count for snapshot in report.source_snapshots
    ):
        raise ValueError("event_count must match source_snapshots")
    for field_name in (
        "near_deadline_event_count",
        "stale_evidence_event_count",
        "pending_source_count",
    ):
        if getattr(report, field_name) > report.event_count:
            raise ValueError(f"{field_name} must not exceed event_count")
    if report.pending_source_count != _sum_count(
        snapshot.pending_source_count for snapshot in report.source_snapshots
    ):
        raise ValueError("pending_source_count must match source_snapshots")
    if report.deadline_proximity_ratio != _ratio(
        report.near_deadline_event_count,
        report.event_count,
    ):
        raise ValueError("deadline_proximity_ratio must match counts")
    if report.evidence_staleness_ratio != _ratio(
        report.stale_evidence_event_count,
        report.event_count,
    ):
        raise ValueError("evidence_staleness_ratio must match counts")
    if report.rule_ambiguity_ratio != _weighted_ratio(
        (
            (snapshot.rule_ambiguity_score, snapshot.event_count)
            for snapshot in report.source_snapshots
        ),
        report.event_count,
    ):
        raise ValueError("rule_ambiguity_ratio must match source_snapshots")
    if report.pending_source_pressure_ratio != _ratio(
        report.pending_source_count,
        report.event_count,
    ):
        raise ValueError("pending_source_pressure_ratio must match counts")
    expected_score = _clock_risk_score(
        (
            report.deadline_proximity_ratio,
            report.evidence_staleness_ratio,
            report.rule_ambiguity_ratio,
            report.pending_source_pressure_ratio,
        ),
    )
    if report.clock_risk_score != expected_score:
        raise ValueError("clock_risk_score must match component ratios")
    expected_status = _status(
        report.clock_risk_score,
        watch_threshold=report.watch_clock_risk_score_threshold,
        block_threshold=report.block_clock_risk_score_threshold,
    )
    if report.status != expected_status:
        raise ValueError("status must match clock_risk_score")
    expected_reason_codes = _reason_codes(
        deadline_proximity_ratio=report.deadline_proximity_ratio,
        evidence_staleness_ratio=report.evidence_staleness_ratio,
        rule_ambiguity_ratio=report.rule_ambiguity_ratio,
        pending_source_pressure_ratio=report.pending_source_pressure_ratio,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match component ratios")
    if report.source_snapshots != tuple(
        sorted(report.source_snapshots, key=_snapshot_sort_key)
    ):
        raise ValueError("source_snapshots must use deterministic sequence")


def _normalize_snapshots(
    values: list[ResearchEventResolutionClockRiskSnapshot]
    | tuple[ResearchEventResolutionClockRiskSnapshot, ...],
) -> tuple[ResearchEventResolutionClockRiskSnapshot, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("source_snapshots must be a list or tuple")
    snapshots = tuple(values)
    for snapshot in snapshots:
        if type(snapshot) is not ResearchEventResolutionClockRiskSnapshot:
            raise ValueError(
                "source_snapshots must contain "
                "ResearchEventResolutionClockRiskSnapshot values",
            )
        require_paper_only_flags("research event resolution clock risk snapshot", snapshot)
    return tuple(sorted(snapshots, key=_snapshot_sort_key))


def _snapshot_sort_key(
    snapshot: ResearchEventResolutionClockRiskSnapshot,
) -> tuple[datetime, datetime, Decimal, Decimal, Decimal]:
    return (
        snapshot.evidence_observed_at,
        snapshot.resolution_deadline_at,
        snapshot.event_count,
        snapshot.rule_ambiguity_score,
        snapshot.pending_source_count,
    )


def _validate_derived_validation_digest(
    report: ResearchEventResolutionClockRiskReport,
) -> None:
    _require_digest_string("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match derived report values")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLOCK_RISK_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in CONFIG_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_member("status", payload["status"], CLOCK_RISK_STATUSES)
    _normalize_reason_codes("reason_codes", payload["reason_codes"])
    if type(payload["source_snapshots"]) is not list:
        raise ValueError("source_snapshots must be a list")
    for snapshot in payload["source_snapshots"]:
        _validate_public_snapshot_payload(snapshot)
    _require_digest_string("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["derived_validation_digest"] != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_snapshot_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("source_snapshots must contain JSON objects")
    _reject_unknown_payload_keys("source snapshot payload", value, SNAPSHOT_PAYLOAD_KEYS)
    for field_name in SNAPSHOT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in SNAPSHOT_DATETIME_PAYLOAD_FIELDS:
        _require_canonical_string(field_name, value[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys and set(payload.keys()) != set(allowed_keys):
        raise ValueError(f"{label} must use the public readonly schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in REPORT_REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _reason_codes(
    *,
    deadline_proximity_ratio: Decimal,
    evidence_staleness_ratio: Decimal,
    rule_ambiguity_ratio: Decimal,
    pending_source_pressure_ratio: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if deadline_proximity_ratio > ZERO_RATIO:
        codes.append("resolution_deadline_pressure_present")
    if evidence_staleness_ratio > ZERO_RATIO:
        codes.append("evidence_freshness_gap_present")
    if rule_ambiguity_ratio > ZERO_RATIO:
        codes.append("rule_ambiguity_present")
    if pending_source_pressure_ratio > ZERO_RATIO:
        codes.append("pending_source_pressure_present")
    return tuple(codes) if codes else ("resolution_clock_risk_clear",)


def _status(
    clock_risk_score: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if clock_risk_score >= block_threshold:
        return "block"
    if clock_risk_score >= watch_threshold:
        return "watch"
    return "pass"


def _report_derived_validation_digest(
    report: ResearchEventResolutionClockRiskReport,
) -> str:
    return _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        near_deadline_window_seconds_threshold=(
            report.near_deadline_window_seconds_threshold
        ),
        stale_evidence_age_seconds_threshold=report.stale_evidence_age_seconds_threshold,
        watch_clock_risk_score_threshold=report.watch_clock_risk_score_threshold,
        block_clock_risk_score_threshold=report.block_clock_risk_score_threshold,
        snapshot_count=report.snapshot_count,
        event_count=report.event_count,
        near_deadline_event_count=report.near_deadline_event_count,
        stale_evidence_event_count=report.stale_evidence_event_count,
        pending_source_count=report.pending_source_count,
        min_deadline_window_seconds=report.min_deadline_window_seconds,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        max_rule_ambiguity_score=report.max_rule_ambiguity_score,
        deadline_proximity_ratio=report.deadline_proximity_ratio,
        evidence_staleness_ratio=report.evidence_staleness_ratio,
        rule_ambiguity_ratio=report.rule_ambiguity_ratio,
        pending_source_pressure_ratio=report.pending_source_pressure_ratio,
        clock_risk_score=report.clock_risk_score,
        status=report.status,
        reason_codes=report.reason_codes,
        source_snapshots=report.source_snapshots,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    return _hash_digest_parts(
        (
            str(payload["generated_at"]),
            str(payload["config_version"]),
            *(str(payload[field_name]) for field_name in CONFIG_DECIMAL_PAYLOAD_FIELDS),
            *(str(payload[field_name]) for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS),
            str(payload["status"]),
            *tuple(str(reason_code) for reason_code in payload["reason_codes"]),
            *tuple(
                component
                for snapshot in payload["source_snapshots"]
                for component in _payload_snapshot_digest_parts(snapshot)
            ),
            str(payload["paper_only"]),
            str(payload["report_only"]),
            str(payload["readonly"]),
        ),
    )


def _derived_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    near_deadline_window_seconds_threshold: Decimal,
    stale_evidence_age_seconds_threshold: Decimal,
    watch_clock_risk_score_threshold: Decimal,
    block_clock_risk_score_threshold: Decimal,
    snapshot_count: Decimal,
    event_count: Decimal,
    near_deadline_event_count: Decimal,
    stale_evidence_event_count: Decimal,
    pending_source_count: Decimal,
    min_deadline_window_seconds: Decimal,
    max_evidence_age_seconds: Decimal,
    max_rule_ambiguity_score: Decimal,
    deadline_proximity_ratio: Decimal,
    evidence_staleness_ratio: Decimal,
    rule_ambiguity_ratio: Decimal,
    pending_source_pressure_ratio: Decimal,
    clock_risk_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    source_snapshots: tuple[ResearchEventResolutionClockRiskSnapshot, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    return _hash_digest_parts(
        (
            generated_at.isoformat(),
            config_version,
            str(near_deadline_window_seconds_threshold),
            str(stale_evidence_age_seconds_threshold),
            str(watch_clock_risk_score_threshold),
            str(block_clock_risk_score_threshold),
            str(snapshot_count),
            str(event_count),
            str(near_deadline_event_count),
            str(stale_evidence_event_count),
            str(pending_source_count),
            str(min_deadline_window_seconds),
            str(max_evidence_age_seconds),
            str(max_rule_ambiguity_score),
            str(deadline_proximity_ratio),
            str(evidence_staleness_ratio),
            str(rule_ambiguity_ratio),
            str(pending_source_pressure_ratio),
            str(clock_risk_score),
            status,
            *reason_codes,
            *tuple(
                component
                for snapshot in source_snapshots
                for component in _snapshot_digest_parts(snapshot)
            ),
            str(paper_only),
            str(report_only),
            str(readonly),
        ),
    )


def _snapshot_digest_parts(
    snapshot: ResearchEventResolutionClockRiskSnapshot,
) -> tuple[str, ...]:
    return (
        str(snapshot.event_count),
        str(snapshot.rule_ambiguity_score),
        str(snapshot.pending_source_count),
        snapshot.resolution_deadline_at.isoformat(),
        snapshot.evidence_observed_at.isoformat(),
        str(snapshot.paper_only),
        str(snapshot.report_only),
        str(snapshot.readonly),
    )


def _payload_snapshot_digest_parts(snapshot: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(snapshot["event_count"]),
        str(snapshot["rule_ambiguity_score"]),
        str(snapshot["pending_source_count"]),
        str(snapshot["resolution_deadline_at"]),
        str(snapshot["evidence_observed_at"]),
        str(snapshot["paper_only"]),
        str(snapshot["report_only"]),
        str(snapshot["readonly"]),
    )


def _hash_digest_parts(parts: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        digest.update(str(len(encoded)).encode("ascii"))
        digest.update(b":")
        digest.update(encoded)
        digest.update(b"|")
    return digest.hexdigest()


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_count(values: object) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        total += _normalize_nonnegative_count("value", value)
    return total.quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    _normalize_nonnegative_count("numerator", numerator)
    _normalize_nonnegative_count("denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _weighted_ratio(values: object, denominator: Decimal) -> Decimal:
    _normalize_nonnegative_count("denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    total = ZERO_RATIO
    for ratio, weight in values:
        normalized_ratio = _normalize_ratio("ratio", ratio)
        normalized_weight = _normalize_nonnegative_count("weight", weight)
        with localcontext(DECIMAL_CONTEXT):
            total += normalized_ratio * normalized_weight
    with localcontext(DECIMAL_CONTEXT):
        return (total / denominator).quantize(RATIO_QUANTUM)


def _clock_risk_score(ratios: tuple[Decimal, ...]) -> Decimal:
    if not ratios:
        return ZERO_RATIO
    total = ZERO_RATIO
    for ratio in ratios:
        total += _normalize_ratio("ratio", ratio)
    with localcontext(DECIMAL_CONTEXT):
        return (total / Decimal(len(ratios))).quantize(RATIO_QUANTUM)


def _max_seconds(values: object) -> Decimal:
    maximum = ZERO_SECONDS
    for value in values:
        candidate = _normalize_nonnegative_seconds("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _min_seconds(values: object) -> Decimal:
    minimum: Decimal | None = None
    for value in values:
        candidate = _normalize_nonnegative_seconds("value", value)
        if minimum is None or candidate < minimum:
            minimum = candidate
    return ZERO_SECONDS if minimum is None else minimum


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    return _duration_seconds(generated_at - observed_at)


def _deadline_window_seconds(generated_at: datetime, deadline_at: datetime) -> Decimal:
    if deadline_at <= generated_at:
        return ZERO_SECONDS
    return _duration_seconds(deadline_at - generated_at)


def _duration_seconds(delta: object) -> Decimal:
    whole_seconds = delta.days * 86_400 + delta.seconds
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(whole_seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)
        ).quantize(SECONDS_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(SECONDS_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(RATIO_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLOCK_RISK_CONFIG_VERSION",
    "ResearchEventResolutionClockRiskConfig",
    "ResearchEventResolutionClockRiskReport",
    "ResearchEventResolutionClockRiskSnapshot",
    "build_research_event_resolution_clock_risk_report",
    "research_event_resolution_clock_risk_payload",
    "research_event_resolution_clock_risk_payload_digest",
    "serialize_research_event_resolution_clock_risk_payload",
)
