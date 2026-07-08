"""Pure aggregate event evidence update cadence report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_EVIDENCE_UPDATE_CADENCE_CONFIG_VERSION = (
    "research-event-evidence-update-cadence-report-v0"
)

EVENT_EVIDENCE_UPDATE_CADENCE_STATUSES = ("pass", "watch", "block")

NO_INPUT_REASON_CODE = "event_evidence_update_cadence_no_inputs"
SUMMARY_PASS_REASON_CODE = "event_evidence_update_cadence_pass"
GROUP_WATCH_REASON_CODE = "event_evidence_update_cadence_group_watch"
GROUP_BLOCK_REASON_CODE = "event_evidence_update_cadence_group_block"

REASON_CODES = (
    NO_INPUT_REASON_CODE,
    "update_interval_pass",
    "update_interval_watch",
    "update_interval_block",
    "latest_update_age_pass",
    "latest_update_age_watch",
    "latest_update_age_block",
    "stale_source_pressure_pass",
    "stale_source_pressure_watch",
    "stale_source_pressure_block",
    "contradiction_pressure_pass",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "resolution_rule_coverage_pass",
    "resolution_rule_coverage_watch",
    "resolution_rule_coverage_block",
    GROUP_WATCH_REASON_CODE,
    GROUP_BLOCK_REASON_CODE,
    SUMMARY_PASS_REASON_CODE,
)

_ROW_REASON_PREFIXES = (
    "update_interval_",
    "latest_update_age_",
    "stale_source_pressure_",
    "contradiction_pressure_",
    "resolution_rule_coverage_",
)
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROSECOND_DIVISOR = Decimal("1000000.000000")

_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "://",
    "www.",
    "candidate",
    "condition_id",
    "".join(("data", "base")),
    "dsn",
    "".join(("live",)),
    "".join(("auth",)),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("market", "_", "slug")),
    "".join(("market", "-", "slug")),
    "".join(("net", "work")),
    "".join(("or", "der")),
    "".join(("ques", "tion")),
    "raw",
    "".join(("recommend",)),
    "".join(("sizing",)),
    "".join(("sl", "ug")),
    "".join(("source", "_", "id")),
    "".join(("source", "-", "id")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("source", "_", "url")),
    "".join(("source", "-", "url")),
    "table",
    "token",
    "".join(("tra", "de")),
    "".join(("tra", "ding")),
    "url",
    "".join(("wall", "et")),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_EVIDENCE_UPDATE_CADENCE_CONFIG_VERSION",
    "EVENT_EVIDENCE_UPDATE_CADENCE_STATUSES",
    "REASON_CODES",
    "ResearchEventEvidenceUpdateCadenceConfig",
    "ResearchEventEvidenceUpdateCadenceReasonCodeCount",
    "ResearchEventEvidenceUpdateCadenceReport",
    "ResearchEventEvidenceUpdateCadenceRow",
    "ResearchEventEvidenceUpdateCadenceSample",
    "build_research_event_evidence_update_cadence_report",
    "research_event_evidence_update_cadence_report_digest",
    "research_event_evidence_update_cadence_report_payload",
    "validate_research_event_evidence_update_cadence_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchEventEvidenceUpdateCadenceConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_EVENT_EVIDENCE_UPDATE_CADENCE_CONFIG_VERSION
    max_pass_update_interval_seconds: Decimal = Decimal("3600.000000")
    max_watch_update_interval_seconds: Decimal = Decimal("14400.000000")
    max_pass_latest_update_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_latest_update_age_seconds: Decimal = Decimal("7200.000000")
    max_pass_stale_source_pressure_ratio: Decimal = Decimal("0.100000")
    max_watch_stale_source_pressure_ratio: Decimal = Decimal("0.400000")
    max_pass_contradiction_pressure_ratio: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure_ratio: Decimal = Decimal("0.400000")
    min_pass_resolution_rule_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_resolution_rule_coverage_ratio: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventEvidenceUpdateCadenceConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_EVIDENCE_UPDATE_CADENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_update_interval_seconds",
            "max_watch_update_interval_seconds",
            "max_pass_latest_update_age_seconds",
            "max_watch_latest_update_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_source_pressure_ratio",
            "max_watch_stale_source_pressure_ratio",
            "max_pass_contradiction_pressure_ratio",
            "max_watch_contradiction_pressure_ratio",
            "min_pass_resolution_rule_coverage_ratio",
            "min_watch_resolution_rule_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_upper_threshold_pair(
            "max_pass_update_interval_seconds",
            self.max_pass_update_interval_seconds,
            "max_watch_update_interval_seconds",
            self.max_watch_update_interval_seconds,
        )
        _require_upper_threshold_pair(
            "max_pass_latest_update_age_seconds",
            self.max_pass_latest_update_age_seconds,
            "max_watch_latest_update_age_seconds",
            self.max_watch_latest_update_age_seconds,
        )
        _require_upper_threshold_pair(
            "max_pass_stale_source_pressure_ratio",
            self.max_pass_stale_source_pressure_ratio,
            "max_watch_stale_source_pressure_ratio",
            self.max_watch_stale_source_pressure_ratio,
        )
        _require_upper_threshold_pair(
            "max_pass_contradiction_pressure_ratio",
            self.max_pass_contradiction_pressure_ratio,
            "max_watch_contradiction_pressure_ratio",
            self.max_watch_contradiction_pressure_ratio,
        )
        if (
            self.min_watch_resolution_rule_coverage_ratio
            > self.min_pass_resolution_rule_coverage_ratio
        ):
            raise ValueError(
                "min_watch_resolution_rule_coverage_ratio cannot exceed "
                "min_pass_resolution_rule_coverage_ratio",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchEventEvidenceUpdateCadenceSample(_FinalPublicDataclass):
    cadence_group: str
    previous_update_at: datetime
    latest_update_at: datetime
    source_count: Decimal
    stale_source_count: Decimal
    checked_claim_count: Decimal
    contradiction_count: Decimal
    resolution_rule_count: Decimal
    resolution_rule_covered_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("sample", self, ResearchEventEvidenceUpdateCadenceSample)
        _require_public_label("cadence_group", self.cadence_group)
        for field_name in ("previous_update_at", "latest_update_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_count",
            "stale_source_count",
            "checked_claim_count",
            "contradiction_count",
            "resolution_rule_count",
            "resolution_rule_covered_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_sample_consistency(self)
        _require_hard_flags("sample", self)
        _reject_unsafe_public_surface("sample", self)


@dataclass(frozen=True)
class ResearchEventEvidenceUpdateCadenceRow(_FinalPublicDataclass):
    aggregate_public_label: str
    update_interval_seconds: Decimal
    latest_update_age_seconds: Decimal
    source_count: Decimal
    stale_source_count: Decimal
    stale_source_pressure_ratio: Decimal
    checked_claim_count: Decimal
    contradiction_count: Decimal
    contradiction_pressure_ratio: Decimal
    resolution_rule_count: Decimal
    resolution_rule_covered_count: Decimal
    resolution_rule_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventEvidenceUpdateCadenceRow)
        _require_redacted_label("aggregate_public_label", self.aggregate_public_label)
        for field_name in ("update_interval_seconds", "latest_update_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_count",
            "stale_source_count",
            "checked_claim_count",
            "contradiction_count",
            "resolution_rule_count",
            "resolution_rule_covered_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_pressure_ratio",
            "contradiction_pressure_ratio",
            "resolution_rule_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchEventEvidenceUpdateCadenceReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchEventEvidenceUpdateCadenceReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_surface("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventEvidenceUpdateCadenceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    update_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_update_interval_seconds: Decimal
    max_update_interval_seconds: Decimal
    max_latest_update_age_seconds: Decimal
    source_count: Decimal
    stale_source_count: Decimal
    stale_source_pressure_ratio: Decimal
    checked_claim_count: Decimal
    contradiction_count: Decimal
    contradiction_pressure_ratio: Decimal
    resolution_rule_count: Decimal
    resolution_rule_covered_count: Decimal
    resolution_rule_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventEvidenceUpdateCadenceReasonCodeCount, ...]
    rows: tuple[ResearchEventEvidenceUpdateCadenceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventEvidenceUpdateCadenceReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_EVIDENCE_UPDATE_CADENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "update_group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "source_count",
            "stale_source_count",
            "checked_claim_count",
            "contradiction_count",
            "resolution_rule_count",
            "resolution_rule_covered_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_update_interval_seconds",
            "max_update_interval_seconds",
            "max_latest_update_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_pressure_ratio",
            "contradiction_pressure_ratio",
            "resolution_rule_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest != "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_evidence_update_cadence_report_payload(self)


def build_research_event_evidence_update_cadence_report(
    samples: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchEventEvidenceUpdateCadenceConfig | None = None,
) -> ResearchEventEvidenceUpdateCadenceReport:
    if config is None:
        config = ResearchEventEvidenceUpdateCadenceConfig()
    if type(config) is not ResearchEventEvidenceUpdateCadenceConfig:
        raise ValueError("config must be a ResearchEventEvidenceUpdateCadenceConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_surface("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_samples(samples, generated_at=generated_at_utc)
    public_labels = {
        sample.cadence_group: f"cadence-group-{index:03d}"
        for index, sample in enumerate(normalized, start=1)
    }
    rows = tuple(
        sorted(
            (
                _row_from_sample(
                    sample,
                    aggregate_public_label=public_labels[sample.cadence_group],
                    generated_at=generated_at_utc,
                    config=config,
                )
                for sample in normalized
            ),
            key=_row_sort_key,
        ),
    )
    return _report_from_rows(rows, generated_at=generated_at_utc, config=config)


def research_event_evidence_update_cadence_report_payload(
    report: ResearchEventEvidenceUpdateCadenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventEvidenceUpdateCadenceReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        if report.derived_validation_digest != _report_derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchEventEvidenceUpdateCadenceReport")
    if not validate_research_event_evidence_update_cadence_report_payload(payload):
        raise ValueError("report payload failed validation")
    return dict(payload)


def research_event_evidence_update_cadence_report_digest(
    report: ResearchEventEvidenceUpdateCadenceReport,
) -> str:
    if type(report) is not ResearchEventEvidenceUpdateCadenceReport:
        raise ValueError("report must be a ResearchEventEvidenceUpdateCadenceReport")
    _require_hard_flags("report", report)
    digest = _report_derived_validation_digest(report)
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_event_evidence_update_cadence_report_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_surface("public payload", payload, allow_mapping=True)
        _require_public_payload_values(payload)
        _require_payload_hard_flags(payload)
        if payload.get("status") not in EVENT_EVIDENCE_UPDATE_CADENCE_STATUSES:
            return False
        rows = payload.get("rows")
        if type(rows) is not list:
            return False
        for row in rows:
            if type(row) is not dict:
                return False
            if row.get("status") not in EVENT_EVIDENCE_UPDATE_CADENCE_STATUSES:
                return False
            _require_payload_hard_flags(row)
        reason_code_counts = payload.get("reason_code_counts")
        if type(reason_code_counts) is not list:
            return False
        for reason_code_count in reason_code_counts:
            if type(reason_code_count) is not dict:
                return False
            _require_payload_hard_flags(reason_code_count)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str:
            return False
        _require_sha256_digest("derived_validation_digest", digest)
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest", None)
        if digest != _payload_digest(unsigned):
            return False
        return True
    except (TypeError, ValueError):
        return False


def _report_from_rows(
    rows: tuple[ResearchEventEvidenceUpdateCadenceRow, ...],
    *,
    generated_at: datetime,
    config: ResearchEventEvidenceUpdateCadenceConfig,
) -> ResearchEventEvidenceUpdateCadenceReport:
    reason_codes = _report_reason_codes(rows)
    source_count = _sum_counts(row.source_count for row in rows)
    stale_source_count = _sum_counts(row.stale_source_count for row in rows)
    checked_claim_count = _sum_counts(row.checked_claim_count for row in rows)
    contradiction_count = _sum_counts(row.contradiction_count for row in rows)
    resolution_rule_count = _sum_counts(row.resolution_rule_count for row in rows)
    resolution_rule_covered_count = _sum_counts(
        (row.resolution_rule_covered_count for row in rows),
    )
    return ResearchEventEvidenceUpdateCadenceReport(
        generated_at=generated_at,
        config_version=config.config_version,
        update_group_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_update_interval_seconds=_average_decimal(
            (row.update_interval_seconds for row in rows),
        ),
        max_update_interval_seconds=_max_decimal(
            (row.update_interval_seconds for row in rows),
        ),
        max_latest_update_age_seconds=_max_decimal(
            (row.latest_update_age_seconds for row in rows),
        ),
        source_count=source_count,
        stale_source_count=stale_source_count,
        stale_source_pressure_ratio=_ratio(stale_source_count, source_count),
        checked_claim_count=checked_claim_count,
        contradiction_count=contradiction_count,
        contradiction_pressure_ratio=_ratio(contradiction_count, checked_claim_count),
        resolution_rule_count=resolution_rule_count,
        resolution_rule_covered_count=resolution_rule_covered_count,
        resolution_rule_coverage_ratio=_ratio(
            resolution_rule_covered_count,
            resolution_rule_count,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def _row_from_sample(
    sample: ResearchEventEvidenceUpdateCadenceSample,
    *,
    aggregate_public_label: str,
    generated_at: datetime,
    config: ResearchEventEvidenceUpdateCadenceConfig,
) -> ResearchEventEvidenceUpdateCadenceRow:
    update_interval_seconds = _datetime_delta_seconds(
        sample.latest_update_at,
        sample.previous_update_at,
    )
    latest_update_age_seconds = _datetime_delta_seconds(
        generated_at,
        sample.latest_update_at,
    )
    stale_source_pressure_ratio = _ratio(sample.stale_source_count, sample.source_count)
    contradiction_pressure_ratio = _ratio(
        sample.contradiction_count,
        sample.checked_claim_count,
    )
    resolution_rule_coverage_ratio = _ratio(
        sample.resolution_rule_covered_count,
        sample.resolution_rule_count,
    )
    reason_codes = _row_reason_codes(
        update_interval_status=_upper_bound_status(
            update_interval_seconds,
            pass_threshold=config.max_pass_update_interval_seconds,
            watch_threshold=config.max_watch_update_interval_seconds,
        ),
        latest_update_age_status=_upper_bound_status(
            latest_update_age_seconds,
            pass_threshold=config.max_pass_latest_update_age_seconds,
            watch_threshold=config.max_watch_latest_update_age_seconds,
        ),
        stale_source_pressure_status=_upper_bound_status(
            stale_source_pressure_ratio,
            pass_threshold=config.max_pass_stale_source_pressure_ratio,
            watch_threshold=config.max_watch_stale_source_pressure_ratio,
        ),
        contradiction_pressure_status=_upper_bound_status(
            contradiction_pressure_ratio,
            pass_threshold=config.max_pass_contradiction_pressure_ratio,
            watch_threshold=config.max_watch_contradiction_pressure_ratio,
        ),
        resolution_rule_coverage_status=_lower_bound_status(
            resolution_rule_coverage_ratio,
            pass_threshold=config.min_pass_resolution_rule_coverage_ratio,
            watch_threshold=config.min_watch_resolution_rule_coverage_ratio,
        ),
    )
    return ResearchEventEvidenceUpdateCadenceRow(
        aggregate_public_label=aggregate_public_label,
        update_interval_seconds=update_interval_seconds,
        latest_update_age_seconds=latest_update_age_seconds,
        source_count=sample.source_count,
        stale_source_count=sample.stale_source_count,
        stale_source_pressure_ratio=stale_source_pressure_ratio,
        checked_claim_count=sample.checked_claim_count,
        contradiction_count=sample.contradiction_count,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        resolution_rule_count=sample.resolution_rule_count,
        resolution_rule_covered_count=sample.resolution_rule_covered_count,
        resolution_rule_coverage_ratio=resolution_rule_coverage_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    update_interval_status: str,
    latest_update_age_status: str,
    stale_source_pressure_status: str,
    contradiction_pressure_status: str,
    resolution_rule_coverage_status: str,
) -> tuple[str, ...]:
    statuses = (
        update_interval_status,
        latest_update_age_status,
        stale_source_pressure_status,
        contradiction_pressure_status,
        resolution_rule_coverage_status,
    )
    for status in statuses:
        _require_status("metric status", status)
    return _normalize_reason_codes(
        (
            f"update_interval_{update_interval_status}",
            f"latest_update_age_{latest_update_age_status}",
            f"stale_source_pressure_{stale_source_pressure_status}",
            f"contradiction_pressure_{contradiction_pressure_status}",
            f"resolution_rule_coverage_{resolution_rule_coverage_status}",
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchEventEvidenceUpdateCadenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUT_REASON_CODE,)
    if all(row.status == "pass" for row in rows):
        return (SUMMARY_PASS_REASON_CODE,)
    reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if not reason_code.endswith("_pass")
    )
    if any(row.status == "block" for row in rows):
        reason_codes = reason_codes + (GROUP_BLOCK_REASON_CODE,)
    elif any(row.status == "watch" for row in rows):
        reason_codes = reason_codes + (GROUP_WATCH_REASON_CODE,)
    return _normalize_reason_codes(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchEventEvidenceUpdateCadenceRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventEvidenceUpdateCadenceReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    if not rows or reason_codes == (SUMMARY_PASS_REASON_CODE,):
        counts.update(reason_codes)
    else:
        for row in rows:
            counts.update(row.reason_codes)
        for reason_code in reason_codes:
            if reason_code in (GROUP_WATCH_REASON_CODE, GROUP_BLOCK_REASON_CODE):
                counts.update((reason_code,))
    return tuple(
        ResearchEventEvidenceUpdateCadenceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODES.index(item[0]),
        )
    )


def _normalize_samples(
    samples: Iterable[object],
    *,
    generated_at: datetime,
) -> tuple[ResearchEventEvidenceUpdateCadenceSample, ...]:
    if isinstance(samples, (str, bytes)):
        raise ValueError("samples must be an iterable")
    try:
        values = tuple(samples)
    except TypeError as exc:
        raise ValueError("samples must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[ResearchEventEvidenceUpdateCadenceSample] = []
    for value in values:
        if type(value) is not ResearchEventEvidenceUpdateCadenceSample:
            raise ValueError(
                "samples must contain ResearchEventEvidenceUpdateCadenceSample values",
            )
        _require_hard_flags("sample", value)
        if value.cadence_group in seen:
            raise ValueError("cadence_group values must be unique")
        seen.add(value.cadence_group)
        if value.latest_update_at > generated_at:
            raise ValueError("latest_update_at must not be after generated_at")
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda sample: sample.cadence_group))


def _normalize_rows(
    rows: Iterable[ResearchEventEvidenceUpdateCadenceRow],
) -> tuple[ResearchEventEvidenceUpdateCadenceRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventEvidenceUpdateCadenceRow:
            raise ValueError(
                "rows must contain ResearchEventEvidenceUpdateCadenceRow values",
            )
        _require_hard_flags("row", value)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchEventEvidenceUpdateCadenceReasonCodeCount],
) -> tuple[ResearchEventEvidenceUpdateCadenceReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventEvidenceUpdateCadenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventEvidenceUpdateCadenceReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
    if values != tuple(sorted(values, key=lambda row: REASON_CODES.index(row.reason_code))):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _validate_sample_consistency(
    sample: ResearchEventEvidenceUpdateCadenceSample,
) -> None:
    if sample.latest_update_at < sample.previous_update_at:
        raise ValueError("latest_update_at must not be before previous_update_at")
    if sample.source_count <= _ZERO:
        raise ValueError("source_count must be positive")
    if sample.checked_claim_count <= _ZERO:
        raise ValueError("checked_claim_count must be positive")
    if sample.resolution_rule_count <= _ZERO:
        raise ValueError("resolution_rule_count must be positive")
    if sample.stale_source_count > sample.source_count:
        raise ValueError("stale_source_count cannot exceed source_count")
    if sample.contradiction_count > sample.checked_claim_count:
        raise ValueError("contradiction_count cannot exceed checked_claim_count")
    if sample.resolution_rule_covered_count > sample.resolution_rule_count:
        raise ValueError(
            "resolution_rule_covered_count cannot exceed resolution_rule_count",
        )


def _validate_row_consistency(row: ResearchEventEvidenceUpdateCadenceRow) -> None:
    prefixes = tuple(reason_code.rsplit("_", 1)[0] + "_" for reason_code in row.reason_codes)
    if prefixes != _ROW_REASON_PREFIXES:
        raise ValueError("row reason_codes must cover each cadence check")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row status must match reason_codes")
    if row.stale_source_pressure_ratio != _ratio(row.stale_source_count, row.source_count):
        raise ValueError("stale_source_pressure_ratio must match counts")
    if row.contradiction_pressure_ratio != _ratio(
        row.contradiction_count,
        row.checked_claim_count,
    ):
        raise ValueError("contradiction_pressure_ratio must match counts")
    if row.resolution_rule_coverage_ratio != _ratio(
        row.resolution_rule_covered_count,
        row.resolution_rule_count,
    ):
        raise ValueError("resolution_rule_coverage_ratio must match counts")


def _validate_report_consistency(
    report: ResearchEventEvidenceUpdateCadenceReport,
) -> None:
    if report.update_group_count != _decimal_count(len(report.rows)):
        raise ValueError("update_group_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_update_interval_seconds != _average_decimal(
        (row.update_interval_seconds for row in report.rows),
    ):
        raise ValueError("mean_update_interval_seconds must match rows")
    if report.max_update_interval_seconds != _max_decimal(
        (row.update_interval_seconds for row in report.rows),
    ):
        raise ValueError("max_update_interval_seconds must match rows")
    if report.max_latest_update_age_seconds != _max_decimal(
        (row.latest_update_age_seconds for row in report.rows),
    ):
        raise ValueError("max_latest_update_age_seconds must match rows")
    source_count = _sum_counts(row.source_count for row in report.rows)
    stale_source_count = _sum_counts(row.stale_source_count for row in report.rows)
    checked_claim_count = _sum_counts(row.checked_claim_count for row in report.rows)
    contradiction_count = _sum_counts(row.contradiction_count for row in report.rows)
    resolution_rule_count = _sum_counts(row.resolution_rule_count for row in report.rows)
    resolution_rule_covered_count = _sum_counts(
        (row.resolution_rule_covered_count for row in report.rows),
    )
    if report.source_count != source_count:
        raise ValueError("source_count must match rows")
    if report.stale_source_count != stale_source_count:
        raise ValueError("stale_source_count must match rows")
    if report.checked_claim_count != checked_claim_count:
        raise ValueError("checked_claim_count must match rows")
    if report.contradiction_count != contradiction_count:
        raise ValueError("contradiction_count must match rows")
    if report.resolution_rule_count != resolution_rule_count:
        raise ValueError("resolution_rule_count must match rows")
    if report.resolution_rule_covered_count != resolution_rule_covered_count:
        raise ValueError("resolution_rule_covered_count must match rows")
    if report.stale_source_pressure_ratio != _ratio(stale_source_count, source_count):
        raise ValueError("stale_source_pressure_ratio must match rows")
    if report.contradiction_pressure_ratio != _ratio(
        contradiction_count,
        checked_claim_count,
    ):
        raise ValueError("contradiction_pressure_ratio must match rows")
    if report.resolution_rule_coverage_ratio != _ratio(
        resolution_rule_covered_count,
        resolution_rule_count,
    ):
        raise ValueError("resolution_rule_coverage_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(row: ResearchEventEvidenceUpdateCadenceRow) -> tuple[int, str]:
    return (_STATUS_RANK[row.status] * -1, row.aggregate_public_label)


def _upper_bound_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "pass"
    if value <= watch_threshold:
        return "watch"
    return "block"


def _lower_bound_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return "pass"
    if value >= watch_threshold:
        return "watch"
    return "block"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    statuses = tuple(_reason_code_status(reason_code) for reason_code in reason_codes)
    return max(statuses, key=lambda status: _STATUS_RANK[status])


def _reason_code_status(reason_code: str) -> str:
    _require_reason_code("reason_code", reason_code)
    if reason_code == NO_INPUT_REASON_CODE:
        return "block"
    if reason_code == SUMMARY_PASS_REASON_CODE:
        return "pass"
    status = reason_code.rsplit("_", 1)[-1]
    _require_status("reason_code status", status)
    return status


def _status_count(
    rows: tuple[ResearchEventEvidenceUpdateCadenceRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(sum(normalized, _ZERO) / Decimal(len(normalized)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _sum_counts(values: Iterable[Decimal]) -> Decimal:
    return _quantize_decimal(sum(tuple(values), _ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamped_ratio(numerator / denominator)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("later datetime must not be before earlier datetime")
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECOND_DIVISOR)
    )
    return _normalize_nonnegative_decimal("datetime_delta_seconds", seconds)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("Decimal values must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_upper_threshold_pair(
    pass_field_name: str,
    pass_threshold: Decimal,
    watch_field_name: str,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold > watch_threshold:
        raise ValueError(f"{pass_field_name} cannot exceed {watch_field_name}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    _reject_unsafe_public_string(field_name, value)


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    assert type(value) is str
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a sanitized public label")
    if not value[0].isalpha():
        raise ValueError(f"{field_name} must start with a letter")


def _require_redacted_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    assert type(value) is str
    prefix = "cadence-group-"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a redacted cadence label")
    suffix = value.removeprefix(prefix)
    if len(suffix) != 3 or not suffix.isdecimal():
        raise ValueError(f"{field_name} must be a redacted cadence label")


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in EVENT_EVIDENCE_UPDATE_CADENCE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain a supported reason code")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    values = tuple(value)
    if not values:
        raise ValueError("reason_codes must not be empty")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in values)
    if values != expected:
        return expected
    return values


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{context} must expose {field_name}")
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = payload.get(field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value


def _report_derived_validation_digest(
    report: ResearchEventEvidenceUpdateCadenceReport,
) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_surface("payload", payload, allow_mapping=True)
    _require_public_payload_values(payload)
    encoded = json.dumps(
        _payload_value(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchEventEvidenceUpdateCadenceReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "update_group_count": _payload_value(report.update_group_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "mean_update_interval_seconds": _payload_value(
            report.mean_update_interval_seconds,
        ),
        "max_update_interval_seconds": _payload_value(
            report.max_update_interval_seconds,
        ),
        "max_latest_update_age_seconds": _payload_value(
            report.max_latest_update_age_seconds,
        ),
        "source_count": _payload_value(report.source_count),
        "stale_source_count": _payload_value(report.stale_source_count),
        "stale_source_pressure_ratio": _payload_value(
            report.stale_source_pressure_ratio,
        ),
        "checked_claim_count": _payload_value(report.checked_claim_count),
        "contradiction_count": _payload_value(report.contradiction_count),
        "contradiction_pressure_ratio": _payload_value(
            report.contradiction_pressure_ratio,
        ),
        "resolution_rule_count": _payload_value(report.resolution_rule_count),
        "resolution_rule_covered_count": _payload_value(
            report.resolution_rule_covered_count,
        ),
        "resolution_rule_coverage_ratio": _payload_value(
            report.resolution_rule_coverage_ratio,
        ),
        "status": report.status,
        "reason_codes": _payload_value(report.reason_codes),
        "reason_code_counts": _payload_value(report.reason_code_counts),
        "rows": _payload_value(report.rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchEventEvidenceUpdateCadenceRow) -> dict[str, Any]:
    return {
        "aggregate_public_label": row.aggregate_public_label,
        "update_interval_seconds": _payload_value(row.update_interval_seconds),
        "latest_update_age_seconds": _payload_value(row.latest_update_age_seconds),
        "source_count": _payload_value(row.source_count),
        "stale_source_count": _payload_value(row.stale_source_count),
        "stale_source_pressure_ratio": _payload_value(row.stale_source_pressure_ratio),
        "checked_claim_count": _payload_value(row.checked_claim_count),
        "contradiction_count": _payload_value(row.contradiction_count),
        "contradiction_pressure_ratio": _payload_value(
            row.contradiction_pressure_ratio,
        ),
        "resolution_rule_count": _payload_value(row.resolution_rule_count),
        "resolution_rule_covered_count": _payload_value(
            row.resolution_rule_covered_count,
        ),
        "resolution_rule_coverage_ratio": _payload_value(
            row.resolution_rule_coverage_ratio,
        ),
        "status": row.status,
        "reason_codes": _payload_value(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchEventEvidenceUpdateCadenceReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _payload_value(row.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is ResearchEventEvidenceUpdateCadenceRow:
        return _row_payload(value)
    if type(value) is ResearchEventEvidenceUpdateCadenceReasonCodeCount:
        return _reason_code_count_payload(value)
    if type(value) is ResearchEventEvidenceUpdateCadenceReport:
        return _report_payload(value, include_digest=True)
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in sorted(value.items())}
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _require_public_payload_values(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_payload_values(item)
        return
    if type(value) is list:
        for item in value:
            _require_public_payload_values(item)
        return
    if type(value) is bool or type(value) is str or value is None:
        return
    raise ValueError("public payload numeric values must use Decimal strings")


def _reject_unsafe_public_surface(
    context: str,
    value: object,
    *,
    allow_mapping: bool = False,
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
            _reject_unsafe_public_string(f"{context} key", field_name)
            _reject_unsafe_public_surface(
                f"{context}.{field_name}",
                getattr(value, field_name),
            )
        return
    if isinstance(value, Mapping):
        if not allow_mapping:
            raise ValueError(f"{context} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} payload keys must be strings")
            _reject_unsafe_public_string(f"{context} key", key)
            _reject_unsafe_public_surface(
                f"{context}.{key}",
                item,
                allow_mapping=True,
            )
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_surface(context, item, allow_mapping=allow_mapping)
        return
    if type(value) is str:
        _reject_unsafe_public_string(context, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{context} Decimal value must be finite")
        return
    if type(value) is datetime:
        _as_utc("datetime payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"{context} contains unsupported public value")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")
