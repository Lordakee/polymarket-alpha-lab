"""Read-only aggregate event resolution timing risk report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMING_RISK_CONFIG_VERSION = (
    "research-event-resolution-timing-risk-report-v0"
)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
AGE_SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_AGE_SECONDS = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

TIMING_RISK_STATUSES = ("pass", "watch", "block")
REPORT_REASON_CODES = (
    "resolution_timing_risk_clear",
    "stale_evidence_age_present",
    "resolution_window_pressure_present",
    "source_refresh_lag_present",
    "ambiguity_burden_present",
    "recheck_urgency_present",
)
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "raw_text",
    "url",
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
)
CONFIG_DECIMAL_PAYLOAD_FIELDS = (
    "stale_evidence_age_seconds_threshold",
    "near_resolution_window_seconds_threshold",
    "source_refresh_lag_seconds_threshold",
    "watch_timing_risk_score_threshold",
    "block_timing_risk_score_threshold",
)
SNAPSHOT_DECIMAL_PAYLOAD_FIELDS = (
    "event_count",
    "ambiguous_event_count",
    "recheck_due_count",
)
SNAPSHOT_DATETIME_PAYLOAD_FIELDS = (
    "evidence_observed_at",
    "nearest_resolution_at",
    "source_refreshed_at",
)
REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "snapshot_count",
    "event_count",
    "stale_evidence_event_count",
    "near_resolution_event_count",
    "source_refresh_lag_event_count",
    "ambiguous_event_count",
    "recheck_due_count",
    "max_evidence_age_seconds",
    "min_resolution_window_seconds",
    "max_source_refresh_lag_seconds",
    "stale_evidence_ratio",
    "resolution_window_pressure_ratio",
    "source_refresh_lag_ratio",
    "ambiguity_burden_ratio",
    "recheck_urgency_ratio",
    "timing_risk_score",
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
class ResearchEventResolutionTimingRiskConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMING_RISK_CONFIG_VERSION
    stale_evidence_age_seconds_threshold: Decimal = Decimal("14400")
    near_resolution_window_seconds_threshold: Decimal = Decimal("3600")
    source_refresh_lag_seconds_threshold: Decimal = Decimal("10800")
    watch_timing_risk_score_threshold: Decimal = Decimal("0.250000")
    block_timing_risk_score_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingRiskConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMING_RISK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_evidence_age_seconds_threshold",
            "near_resolution_window_seconds_threshold",
            "source_refresh_lag_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_age_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_timing_risk_score_threshold",
            "block_timing_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_timing_risk_score_threshold <= self.watch_timing_risk_score_threshold:
            raise ValueError(
                "block_timing_risk_score_threshold must exceed "
                "watch_timing_risk_score_threshold",
            )
        require_paper_only_flags("research event resolution timing risk config", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimingRiskSnapshot:
    event_count: Decimal
    evidence_observed_at: datetime
    nearest_resolution_at: datetime
    source_refreshed_at: datetime
    ambiguous_event_count: Decimal
    recheck_due_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingRiskSnapshot:
            raise ValueError("snapshot must be exact")
        for field_name in SNAPSHOT_DECIMAL_PAYLOAD_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in SNAPSHOT_DATETIME_PAYLOAD_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        if self.ambiguous_event_count > self.event_count:
            raise ValueError("ambiguous_event_count must not exceed event_count")
        if self.recheck_due_count > self.event_count:
            raise ValueError("recheck_due_count must not exceed event_count")
        require_paper_only_flags("research event resolution timing risk snapshot", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimingRiskReport:
    generated_at: datetime
    config_version: str
    stale_evidence_age_seconds_threshold: Decimal
    near_resolution_window_seconds_threshold: Decimal
    source_refresh_lag_seconds_threshold: Decimal
    watch_timing_risk_score_threshold: Decimal
    block_timing_risk_score_threshold: Decimal
    snapshot_count: Decimal
    event_count: Decimal
    stale_evidence_event_count: Decimal
    near_resolution_event_count: Decimal
    source_refresh_lag_event_count: Decimal
    ambiguous_event_count: Decimal
    recheck_due_count: Decimal
    max_evidence_age_seconds: Decimal
    min_resolution_window_seconds: Decimal
    max_source_refresh_lag_seconds: Decimal
    stale_evidence_ratio: Decimal
    resolution_window_pressure_ratio: Decimal
    source_refresh_lag_ratio: Decimal
    ambiguity_burden_ratio: Decimal
    recheck_urgency_ratio: Decimal
    timing_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    source_snapshots: tuple[ResearchEventResolutionTimingRiskSnapshot, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingRiskReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMING_RISK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in CONFIG_DECIMAL_PAYLOAD_FIELDS:
            if field_name.endswith("_threshold") and "score" in field_name:
                normalizer = _normalize_ratio
            elif field_name.endswith("_threshold"):
                normalizer = _normalize_nonnegative_age_seconds
            else:
                raise ValueError(f"unsupported config field: {field_name}")
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        if self.block_timing_risk_score_threshold <= self.watch_timing_risk_score_threshold:
            raise ValueError(
                "block_timing_risk_score_threshold must exceed "
                "watch_timing_risk_score_threshold",
            )
        for field_name in (
            "snapshot_count",
            "event_count",
            "stale_evidence_event_count",
            "near_resolution_event_count",
            "source_refresh_lag_event_count",
            "ambiguous_event_count",
            "recheck_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_age_seconds",
            "min_resolution_window_seconds",
            "max_source_refresh_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_age_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_evidence_ratio",
            "resolution_window_pressure_ratio",
            "source_refresh_lag_ratio",
            "ambiguity_burden_ratio",
            "recheck_urgency_ratio",
            "timing_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, TIMING_RISK_STATUSES)
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
        require_paper_only_flags("research event resolution timing risk report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("research event resolution timing risk report", self)
        _validate_derived_validation_digest(self)


def build_research_event_resolution_timing_risk_report(
    snapshots: list[ResearchEventResolutionTimingRiskSnapshot]
    | tuple[ResearchEventResolutionTimingRiskSnapshot, ...],
    *,
    config: ResearchEventResolutionTimingRiskConfig,
    generated_at: datetime,
) -> ResearchEventResolutionTimingRiskReport:
    if type(config) is not ResearchEventResolutionTimingRiskConfig:
        raise ValueError("config must be a ResearchEventResolutionTimingRiskConfig")
    require_paper_only_flags("research event resolution timing risk config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_snapshots = _normalize_snapshots(snapshots)
    for snapshot in source_snapshots:
        if snapshot.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")
        if snapshot.source_refreshed_at > generated_at:
            raise ValueError("source_refreshed_at must not be after generated_at")

    snapshot_count = _count(len(source_snapshots))
    event_count = _sum_count(snapshot.event_count for snapshot in source_snapshots)
    stale_evidence_event_count = _sum_count(
        snapshot.event_count
        for snapshot in source_snapshots
        if _age_seconds(generated_at, snapshot.evidence_observed_at)
        >= config.stale_evidence_age_seconds_threshold
    )
    near_resolution_event_count = _sum_count(
        snapshot.event_count
        for snapshot in source_snapshots
        if _resolution_window_seconds(generated_at, snapshot.nearest_resolution_at)
        <= config.near_resolution_window_seconds_threshold
    )
    source_refresh_lag_event_count = _sum_count(
        snapshot.event_count
        for snapshot in source_snapshots
        if _age_seconds(generated_at, snapshot.source_refreshed_at)
        >= config.source_refresh_lag_seconds_threshold
    )
    ambiguous_event_count = _sum_count(
        snapshot.ambiguous_event_count for snapshot in source_snapshots
    )
    recheck_due_count = _sum_count(snapshot.recheck_due_count for snapshot in source_snapshots)
    stale_evidence_ratio = _ratio(stale_evidence_event_count, event_count)
    resolution_window_pressure_ratio = _ratio(near_resolution_event_count, event_count)
    source_refresh_lag_ratio = _ratio(source_refresh_lag_event_count, event_count)
    ambiguity_burden_ratio = _ratio(ambiguous_event_count, event_count)
    recheck_urgency_ratio = _ratio(recheck_due_count, event_count)
    timing_risk_score = _timing_risk_score(
        (
            stale_evidence_ratio,
            resolution_window_pressure_ratio,
            source_refresh_lag_ratio,
            ambiguity_burden_ratio,
            recheck_urgency_ratio,
        ),
    )
    status = _status(
        timing_risk_score,
        watch_threshold=config.watch_timing_risk_score_threshold,
        block_threshold=config.block_timing_risk_score_threshold,
    )
    reason_codes = _reason_codes(
        stale_evidence_ratio=stale_evidence_ratio,
        resolution_window_pressure_ratio=resolution_window_pressure_ratio,
        source_refresh_lag_ratio=source_refresh_lag_ratio,
        ambiguity_burden_ratio=ambiguity_burden_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
    )

    return ResearchEventResolutionTimingRiskReport(
        generated_at=generated_at,
        config_version=config.config_version,
        stale_evidence_age_seconds_threshold=config.stale_evidence_age_seconds_threshold,
        near_resolution_window_seconds_threshold=(
            config.near_resolution_window_seconds_threshold
        ),
        source_refresh_lag_seconds_threshold=config.source_refresh_lag_seconds_threshold,
        watch_timing_risk_score_threshold=config.watch_timing_risk_score_threshold,
        block_timing_risk_score_threshold=config.block_timing_risk_score_threshold,
        snapshot_count=snapshot_count,
        event_count=event_count,
        stale_evidence_event_count=stale_evidence_event_count,
        near_resolution_event_count=near_resolution_event_count,
        source_refresh_lag_event_count=source_refresh_lag_event_count,
        ambiguous_event_count=ambiguous_event_count,
        recheck_due_count=recheck_due_count,
        max_evidence_age_seconds=_max_age_seconds(
            _age_seconds(generated_at, snapshot.evidence_observed_at)
            for snapshot in source_snapshots
        ),
        min_resolution_window_seconds=_min_age_seconds(
            _resolution_window_seconds(generated_at, snapshot.nearest_resolution_at)
            for snapshot in source_snapshots
        ),
        max_source_refresh_lag_seconds=_max_age_seconds(
            _age_seconds(generated_at, snapshot.source_refreshed_at)
            for snapshot in source_snapshots
        ),
        stale_evidence_ratio=stale_evidence_ratio,
        resolution_window_pressure_ratio=resolution_window_pressure_ratio,
        source_refresh_lag_ratio=source_refresh_lag_ratio,
        ambiguity_burden_ratio=ambiguity_burden_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        timing_risk_score=timing_risk_score,
        status=status,
        reason_codes=reason_codes,
        source_snapshots=source_snapshots,
        derived_validation_digest=_derived_validation_digest(
            generated_at=generated_at,
            config_version=config.config_version,
            stale_evidence_age_seconds_threshold=(
                config.stale_evidence_age_seconds_threshold
            ),
            near_resolution_window_seconds_threshold=(
                config.near_resolution_window_seconds_threshold
            ),
            source_refresh_lag_seconds_threshold=(
                config.source_refresh_lag_seconds_threshold
            ),
            watch_timing_risk_score_threshold=config.watch_timing_risk_score_threshold,
            block_timing_risk_score_threshold=config.block_timing_risk_score_threshold,
            snapshot_count=snapshot_count,
            event_count=event_count,
            stale_evidence_event_count=stale_evidence_event_count,
            near_resolution_event_count=near_resolution_event_count,
            source_refresh_lag_event_count=source_refresh_lag_event_count,
            ambiguous_event_count=ambiguous_event_count,
            recheck_due_count=recheck_due_count,
            max_evidence_age_seconds=_max_age_seconds(
                _age_seconds(generated_at, snapshot.evidence_observed_at)
                for snapshot in source_snapshots
            ),
            min_resolution_window_seconds=_min_age_seconds(
                _resolution_window_seconds(generated_at, snapshot.nearest_resolution_at)
                for snapshot in source_snapshots
            ),
            max_source_refresh_lag_seconds=_max_age_seconds(
                _age_seconds(generated_at, snapshot.source_refreshed_at)
                for snapshot in source_snapshots
            ),
            stale_evidence_ratio=stale_evidence_ratio,
            resolution_window_pressure_ratio=resolution_window_pressure_ratio,
            source_refresh_lag_ratio=source_refresh_lag_ratio,
            ambiguity_burden_ratio=ambiguity_burden_ratio,
            recheck_urgency_ratio=recheck_urgency_ratio,
            timing_risk_score=timing_risk_score,
            status=status,
            reason_codes=reason_codes,
            source_snapshots=source_snapshots,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )


def research_event_resolution_timing_risk_payload(
    report: ResearchEventResolutionTimingRiskReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionTimingRiskReport:
        require_paper_only_flags("research event resolution timing risk report", report)
        reject_unsafe_surface_fields("research event resolution timing risk report", report)
        _reject_unsafe_public_payload("research event resolution timing risk report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        reject_unsafe_surface_fields("research event resolution timing risk payload", report)
        _reject_unsafe_public_payload("research event resolution timing risk payload", report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError("report must be a ResearchEventResolutionTimingRiskReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    require_paper_only_flags("research event resolution timing risk payload", _DictFlags(payload))
    return payload


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


def _validate_report(report: ResearchEventResolutionTimingRiskReport) -> None:
    if report.snapshot_count != _count(len(report.source_snapshots)):
        raise ValueError("snapshot_count must match source_snapshots")
    if report.event_count != _sum_count(
        snapshot.event_count for snapshot in report.source_snapshots
    ):
        raise ValueError("event_count must match source_snapshots")
    for field_name in (
        "stale_evidence_event_count",
        "near_resolution_event_count",
        "source_refresh_lag_event_count",
        "ambiguous_event_count",
        "recheck_due_count",
    ):
        if getattr(report, field_name) > report.event_count:
            raise ValueError(f"{field_name} must not exceed event_count")
    if report.ambiguous_event_count != _sum_count(
        snapshot.ambiguous_event_count for snapshot in report.source_snapshots
    ):
        raise ValueError("ambiguous_event_count must match source_snapshots")
    if report.recheck_due_count != _sum_count(
        snapshot.recheck_due_count for snapshot in report.source_snapshots
    ):
        raise ValueError("recheck_due_count must match source_snapshots")
    if report.stale_evidence_ratio != _ratio(
        report.stale_evidence_event_count,
        report.event_count,
    ):
        raise ValueError("stale_evidence_ratio must match counts")
    if report.resolution_window_pressure_ratio != _ratio(
        report.near_resolution_event_count,
        report.event_count,
    ):
        raise ValueError("resolution_window_pressure_ratio must match counts")
    if report.source_refresh_lag_ratio != _ratio(
        report.source_refresh_lag_event_count,
        report.event_count,
    ):
        raise ValueError("source_refresh_lag_ratio must match counts")
    if report.ambiguity_burden_ratio != _ratio(
        report.ambiguous_event_count,
        report.event_count,
    ):
        raise ValueError("ambiguity_burden_ratio must match counts")
    if report.recheck_urgency_ratio != _ratio(report.recheck_due_count, report.event_count):
        raise ValueError("recheck_urgency_ratio must match counts")
    expected_score = _timing_risk_score(
        (
            report.stale_evidence_ratio,
            report.resolution_window_pressure_ratio,
            report.source_refresh_lag_ratio,
            report.ambiguity_burden_ratio,
            report.recheck_urgency_ratio,
        ),
    )
    if report.timing_risk_score != expected_score:
        raise ValueError("timing_risk_score must match component ratios")
    expected_status = _status(
        report.timing_risk_score,
        watch_threshold=report.watch_timing_risk_score_threshold,
        block_threshold=report.block_timing_risk_score_threshold,
    )
    if report.status != expected_status:
        raise ValueError("status must match timing_risk_score")
    expected_reason_codes = _reason_codes(
        stale_evidence_ratio=report.stale_evidence_ratio,
        resolution_window_pressure_ratio=report.resolution_window_pressure_ratio,
        source_refresh_lag_ratio=report.source_refresh_lag_ratio,
        ambiguity_burden_ratio=report.ambiguity_burden_ratio,
        recheck_urgency_ratio=report.recheck_urgency_ratio,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match component ratios")
    if report.source_snapshots != tuple(
        sorted(report.source_snapshots, key=_snapshot_sort_key)
    ):
        raise ValueError("source_snapshots must use deterministic sequence")


def _normalize_snapshots(
    values: list[ResearchEventResolutionTimingRiskSnapshot]
    | tuple[ResearchEventResolutionTimingRiskSnapshot, ...],
) -> tuple[ResearchEventResolutionTimingRiskSnapshot, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("source_snapshots must be a list or tuple")
    snapshots = tuple(values)
    for snapshot in snapshots:
        if type(snapshot) is not ResearchEventResolutionTimingRiskSnapshot:
            raise ValueError(
                "source_snapshots must contain "
                "ResearchEventResolutionTimingRiskSnapshot values",
            )
        require_paper_only_flags("research event resolution timing risk snapshot", snapshot)
    return tuple(sorted(snapshots, key=_snapshot_sort_key))


def _snapshot_sort_key(
    snapshot: ResearchEventResolutionTimingRiskSnapshot,
) -> tuple[datetime, datetime, datetime, Decimal, Decimal, Decimal]:
    return (
        snapshot.evidence_observed_at,
        snapshot.nearest_resolution_at,
        snapshot.source_refreshed_at,
        snapshot.event_count,
        snapshot.ambiguous_event_count,
        snapshot.recheck_due_count,
    )


def _validate_derived_validation_digest(
    report: ResearchEventResolutionTimingRiskReport,
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
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMING_RISK_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in CONFIG_DECIMAL_PAYLOAD_FIELDS:
        if field_name.endswith("_threshold") and "score" in field_name:
            _require_decimal_string(field_name, payload[field_name])
        elif field_name.endswith("_threshold"):
            _require_decimal_string(field_name, payload[field_name])
        else:
            raise ValueError(f"unsupported config field: {field_name}")
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_member("status", payload["status"], TIMING_RISK_STATUSES)
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
    stale_evidence_ratio: Decimal,
    resolution_window_pressure_ratio: Decimal,
    source_refresh_lag_ratio: Decimal,
    ambiguity_burden_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if stale_evidence_ratio > ZERO_RATIO:
        codes.append("stale_evidence_age_present")
    if resolution_window_pressure_ratio > ZERO_RATIO:
        codes.append("resolution_window_pressure_present")
    if source_refresh_lag_ratio > ZERO_RATIO:
        codes.append("source_refresh_lag_present")
    if ambiguity_burden_ratio > ZERO_RATIO:
        codes.append("ambiguity_burden_present")
    if recheck_urgency_ratio > ZERO_RATIO:
        codes.append("recheck_urgency_present")
    return tuple(codes) if codes else ("resolution_timing_risk_clear",)


def _status(
    timing_risk_score: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if timing_risk_score >= block_threshold:
        return "block"
    if timing_risk_score >= watch_threshold:
        return "watch"
    return "pass"


def _report_derived_validation_digest(
    report: ResearchEventResolutionTimingRiskReport,
) -> str:
    return _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        stale_evidence_age_seconds_threshold=(
            report.stale_evidence_age_seconds_threshold
        ),
        near_resolution_window_seconds_threshold=(
            report.near_resolution_window_seconds_threshold
        ),
        source_refresh_lag_seconds_threshold=report.source_refresh_lag_seconds_threshold,
        watch_timing_risk_score_threshold=report.watch_timing_risk_score_threshold,
        block_timing_risk_score_threshold=report.block_timing_risk_score_threshold,
        snapshot_count=report.snapshot_count,
        event_count=report.event_count,
        stale_evidence_event_count=report.stale_evidence_event_count,
        near_resolution_event_count=report.near_resolution_event_count,
        source_refresh_lag_event_count=report.source_refresh_lag_event_count,
        ambiguous_event_count=report.ambiguous_event_count,
        recheck_due_count=report.recheck_due_count,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        min_resolution_window_seconds=report.min_resolution_window_seconds,
        max_source_refresh_lag_seconds=report.max_source_refresh_lag_seconds,
        stale_evidence_ratio=report.stale_evidence_ratio,
        resolution_window_pressure_ratio=report.resolution_window_pressure_ratio,
        source_refresh_lag_ratio=report.source_refresh_lag_ratio,
        ambiguity_burden_ratio=report.ambiguity_burden_ratio,
        recheck_urgency_ratio=report.recheck_urgency_ratio,
        timing_risk_score=report.timing_risk_score,
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
    stale_evidence_age_seconds_threshold: Decimal,
    near_resolution_window_seconds_threshold: Decimal,
    source_refresh_lag_seconds_threshold: Decimal,
    watch_timing_risk_score_threshold: Decimal,
    block_timing_risk_score_threshold: Decimal,
    snapshot_count: Decimal,
    event_count: Decimal,
    stale_evidence_event_count: Decimal,
    near_resolution_event_count: Decimal,
    source_refresh_lag_event_count: Decimal,
    ambiguous_event_count: Decimal,
    recheck_due_count: Decimal,
    max_evidence_age_seconds: Decimal,
    min_resolution_window_seconds: Decimal,
    max_source_refresh_lag_seconds: Decimal,
    stale_evidence_ratio: Decimal,
    resolution_window_pressure_ratio: Decimal,
    source_refresh_lag_ratio: Decimal,
    ambiguity_burden_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
    timing_risk_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    source_snapshots: tuple[ResearchEventResolutionTimingRiskSnapshot, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    return _hash_digest_parts(
        (
            generated_at.isoformat(),
            config_version,
            str(stale_evidence_age_seconds_threshold),
            str(near_resolution_window_seconds_threshold),
            str(source_refresh_lag_seconds_threshold),
            str(watch_timing_risk_score_threshold),
            str(block_timing_risk_score_threshold),
            str(snapshot_count),
            str(event_count),
            str(stale_evidence_event_count),
            str(near_resolution_event_count),
            str(source_refresh_lag_event_count),
            str(ambiguous_event_count),
            str(recheck_due_count),
            str(max_evidence_age_seconds),
            str(min_resolution_window_seconds),
            str(max_source_refresh_lag_seconds),
            str(stale_evidence_ratio),
            str(resolution_window_pressure_ratio),
            str(source_refresh_lag_ratio),
            str(ambiguity_burden_ratio),
            str(recheck_urgency_ratio),
            str(timing_risk_score),
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
    snapshot: ResearchEventResolutionTimingRiskSnapshot,
) -> tuple[str, ...]:
    return (
        str(snapshot.event_count),
        str(snapshot.ambiguous_event_count),
        str(snapshot.recheck_due_count),
        snapshot.evidence_observed_at.isoformat(),
        snapshot.nearest_resolution_at.isoformat(),
        snapshot.source_refreshed_at.isoformat(),
        str(snapshot.paper_only),
        str(snapshot.report_only),
        str(snapshot.readonly),
    )


def _payload_snapshot_digest_parts(snapshot: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(snapshot["event_count"]),
        str(snapshot["ambiguous_event_count"]),
        str(snapshot["recheck_due_count"]),
        str(snapshot["evidence_observed_at"]),
        str(snapshot["nearest_resolution_at"]),
        str(snapshot["source_refreshed_at"]),
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


def _timing_risk_score(ratios: tuple[Decimal, ...]) -> Decimal:
    if not ratios:
        return ZERO_RATIO
    total = ZERO_RATIO
    for ratio in ratios:
        total += _normalize_ratio("ratio", ratio)
    with localcontext(DECIMAL_CONTEXT):
        return (total / Decimal(len(ratios))).quantize(RATIO_QUANTUM)


def _max_age_seconds(values: object) -> Decimal:
    maximum = ZERO_AGE_SECONDS
    for value in values:
        candidate = _normalize_nonnegative_age_seconds("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _min_age_seconds(values: object) -> Decimal:
    minimum: Decimal | None = None
    for value in values:
        candidate = _normalize_nonnegative_age_seconds("value", value)
        if minimum is None or candidate < minimum:
            minimum = candidate
    return ZERO_AGE_SECONDS if minimum is None else minimum


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    return _duration_seconds(generated_at - observed_at)


def _resolution_window_seconds(generated_at: datetime, resolution_at: datetime) -> Decimal:
    if resolution_at <= generated_at:
        return ZERO_AGE_SECONDS
    return _duration_seconds(resolution_at - generated_at)


def _duration_seconds(delta: object) -> Decimal:
    whole_seconds = delta.days * 86_400 + delta.seconds
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(whole_seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)
        ).quantize(AGE_SECONDS_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_AGE_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(AGE_SECONDS_QUANTUM)


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
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMING_RISK_CONFIG_VERSION",
    "ResearchEventResolutionTimingRiskConfig",
    "ResearchEventResolutionTimingRiskReport",
    "ResearchEventResolutionTimingRiskSnapshot",
    "build_research_event_resolution_timing_risk_report",
    "research_event_resolution_timing_risk_payload",
)
