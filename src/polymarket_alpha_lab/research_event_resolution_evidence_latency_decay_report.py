"""Report-only event resolution evidence latency decay triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Iterable, Mapping

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_REPORT_CONFIG_VERSION = (
    "research-event-resolution-evidence-latency-decay-report-v1"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

ROW_REASON_CODES = (
    "evidence_latency_stale",
    "evidence_trust_gap",
    "evidence_strength_gap",
    "evidence_revision_risk",
    "resolution_deadline_pressure",
    "evidence_latency_decay_elevated",
    "evidence_latency_clear",
)
REPORT_REASON_CODES = (
    "evidence_latency_empty",
    "evidence_latency_stale",
    "evidence_trust_gap",
    "evidence_strength_gap",
    "evidence_revision_risk",
    "resolution_deadline_pressure",
    "evidence_latency_decay_elevated",
    "evidence_latency_clear",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
PUBLIC_SURFACE_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source url",
    "source_url",
    "url",
    "text",
    "dsn",
    "table",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "http",
    "://",
)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceLatencyDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_REPORT_CONFIG_VERSION
    )
    evidence_latency_watch_seconds: Decimal = Decimal("3600.000000")
    evidence_latency_block_seconds: Decimal = Decimal("10800.000000")
    deadline_watch_seconds: Decimal = Decimal("7200.000000")
    deadline_block_seconds: Decimal = Decimal("1800.000000")
    minimum_evidence_trust_score: Decimal = Decimal("0.700000")
    minimum_evidence_strength_score: Decimal = Decimal("0.700000")
    revision_watch_threshold: Decimal = Decimal("0.300000")
    revision_block_threshold: Decimal = Decimal("0.700000")
    decay_watch_threshold: Decimal = Decimal("0.300000")
    decay_block_threshold: Decimal = Decimal("0.700000")
    latency_weight: Decimal = Decimal("0.400000")
    trust_gap_weight: Decimal = Decimal("0.200000")
    strength_gap_weight: Decimal = Decimal("0.200000")
    revision_weight: Decimal = Decimal("0.100000")
    deadline_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceLatencyDecayConfig:
            raise TypeError(
                "ResearchEventResolutionEvidenceLatencyDecayConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventResolutionEvidenceLatencyDecayConfig,
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "evidence_latency_watch_seconds",
            "evidence_latency_block_seconds",
            "deadline_watch_seconds",
            "deadline_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_evidence_trust_score",
            "minimum_evidence_strength_score",
            "revision_watch_threshold",
            "revision_block_threshold",
            "decay_watch_threshold",
            "decay_block_threshold",
            "latency_weight",
            "trust_gap_weight",
            "strength_gap_weight",
            "revision_weight",
            "deadline_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("evidence latency decay config", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceLatencyDecayInput:
    event_reference: str
    evidence_observed_at: datetime
    resolution_deadline_at: datetime | None
    evidence_trust_score: Decimal
    evidence_strength_score: Decimal
    evidence_revision_risk: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceLatencyDecayInput:
            raise TypeError(
                "ResearchEventResolutionEvidenceLatencyDecayInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchEventResolutionEvidenceLatencyDecayInput)
        _require_private_reference("event_reference", self.event_reference)
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_optional_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "evidence_trust_score",
            "evidence_strength_score",
            "evidence_revision_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_extra_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("evidence latency decay input", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceLatencyDecayRow:
    event_digest: str
    status: str
    evidence_observed_at: datetime
    resolution_deadline_at: datetime | None
    evidence_age_seconds: Decimal
    deadline_proximity_seconds: Decimal | None
    evidence_trust_score: Decimal
    evidence_strength_score: Decimal
    evidence_revision_risk: Decimal
    latency_pressure_score: Decimal
    trust_gap_score: Decimal
    strength_gap_score: Decimal
    deadline_pressure_score: Decimal
    evidence_latency_decay_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceLatencyDecayRow:
            raise TypeError(
                "ResearchEventResolutionEvidenceLatencyDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventResolutionEvidenceLatencyDecayRow)
        _require_sha256_digest("event_digest", self.event_digest)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_optional_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_seconds_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "deadline_proximity_seconds",
            _normalize_optional_nonnegative_seconds_decimal(
                "deadline_proximity_seconds",
                self.deadline_proximity_seconds,
            ),
        )
        for field_name in (
            "evidence_trust_score",
            "evidence_strength_score",
            "evidence_revision_risk",
            "latency_pressure_score",
            "trust_gap_score",
            "strength_gap_score",
            "deadline_pressure_score",
            "evidence_latency_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("evidence latency decay row", self)
        _reject_unsafe_public_payload("evidence latency decay row", self)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceLatencyDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_count: Decimal
    trust_gap_count: Decimal
    strength_gap_count: Decimal
    revision_risk_count: Decimal
    deadline_pressure_count: Decimal
    max_evidence_age_seconds: Decimal
    average_evidence_latency_decay_score: Decimal
    highest_evidence_latency_decay_score: Decimal
    rows: tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceLatencyDecayReport:
            raise TypeError(
                "ResearchEventResolutionEvidenceLatencyDecayReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventResolutionEvidenceLatencyDecayReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_count",
            "trust_gap_count",
            "strength_gap_count",
            "revision_risk_count",
            "deadline_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_nonnegative_seconds_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        for field_name in (
            "average_evidence_latency_decay_score",
            "highest_evidence_latency_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_values_without_digest(self)),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        require_paper_only_flags("evidence latency decay report", self)
        _reject_unsafe_public_payload("evidence latency decay report", self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_evidence_latency_decay_payload(self)


def build_research_event_resolution_evidence_latency_decay_report(
    events: Iterable[ResearchEventResolutionEvidenceLatencyDecayInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionEvidenceLatencyDecayConfig | None = None,
) -> ResearchEventResolutionEvidenceLatencyDecayReport:
    """Build a deterministic, read-only evidence latency decay report."""

    if config is None:
        config = ResearchEventResolutionEvidenceLatencyDecayConfig()
    if type(config) is not ResearchEventResolutionEvidenceLatencyDecayConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionEvidenceLatencyDecayConfig",
        )
    require_paper_only_flags("evidence latency decay config", config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events)
    _validate_event_times(normalized_events, normalized_generated_at)
    rows = _sort_rows(
        tuple(
            _row_from_event(
                event,
                config=config,
                generated_at=normalized_generated_at,
            )
            for event in normalized_events
        ),
    )
    score_values = tuple(row.evidence_latency_decay_score for row in rows)
    age_values = tuple(row.evidence_age_seconds for row in rows)
    values: dict[str, object] = {
        "generated_at": normalized_generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "stale_count": _reason_count(rows, "evidence_latency_stale"),
        "trust_gap_count": _reason_count(rows, "evidence_trust_gap"),
        "strength_gap_count": _reason_count(rows, "evidence_strength_gap"),
        "revision_risk_count": _reason_count(rows, "evidence_revision_risk"),
        "deadline_pressure_count": _reason_count(rows, "resolution_deadline_pressure"),
        "max_evidence_age_seconds": max(age_values, default=ZERO),
        "average_evidence_latency_decay_score": _average_ratio(score_values),
        "highest_evidence_latency_decay_score": max(score_values, default=ZERO),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionEvidenceLatencyDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_evidence_latency_decay_payload(
    report: ResearchEventResolutionEvidenceLatencyDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionEvidenceLatencyDecayReport:
        require_paper_only_flags("evidence latency decay report", report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionEvidenceLatencyDecayReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_event_resolution_evidence_latency_decay_digest(
    report: ResearchEventResolutionEvidenceLatencyDecayReport,
) -> str:
    if type(report) is not ResearchEventResolutionEvidenceLatencyDecayReport:
        raise ValueError("report must be a ResearchEventResolutionEvidenceLatencyDecayReport")
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_event_resolution_evidence_latency_decay_digest(
    report: ResearchEventResolutionEvidenceLatencyDecayReport,
) -> None:
    if type(report) is not ResearchEventResolutionEvidenceLatencyDecayReport:
        raise ValueError("report must be a ResearchEventResolutionEvidenceLatencyDecayReport")
    if report.derived_validation_digest != research_event_resolution_evidence_latency_decay_digest(
        report,
    ):
        raise ValueError("derived_validation_digest must match report payload")


def _row_from_event(
    event: ResearchEventResolutionEvidenceLatencyDecayInput,
    *,
    config: ResearchEventResolutionEvidenceLatencyDecayConfig,
    generated_at: datetime,
) -> ResearchEventResolutionEvidenceLatencyDecayRow:
    age_seconds = _duration_seconds(event.evidence_observed_at, generated_at)
    deadline_seconds = _deadline_proximity_seconds(
        generated_at,
        event.resolution_deadline_at,
    )
    latency_pressure_score = _capped_ratio(age_seconds, config.evidence_latency_block_seconds)
    trust_gap_score = _score_gap(event.evidence_trust_score)
    strength_gap_score = _score_gap(event.evidence_strength_score)
    deadline_pressure_score = _deadline_pressure_score(deadline_seconds, config)
    decay_score = _decay_score(
        latency_pressure_score=latency_pressure_score,
        trust_gap_score=trust_gap_score,
        strength_gap_score=strength_gap_score,
        revision_risk=event.evidence_revision_risk,
        deadline_pressure_score=deadline_pressure_score,
        config=config,
    )
    status = _row_status(
        age_seconds=age_seconds,
        evidence_trust_score=event.evidence_trust_score,
        evidence_strength_score=event.evidence_strength_score,
        evidence_revision_risk=event.evidence_revision_risk,
        deadline_proximity_seconds=deadline_seconds,
        evidence_latency_decay_score=decay_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        event.reason_codes,
        age_seconds=age_seconds,
        evidence_trust_score=event.evidence_trust_score,
        evidence_strength_score=event.evidence_strength_score,
        evidence_revision_risk=event.evidence_revision_risk,
        deadline_proximity_seconds=deadline_seconds,
        evidence_latency_decay_score=decay_score,
        config=config,
    )
    return ResearchEventResolutionEvidenceLatencyDecayRow(
        event_digest=_event_digest(event.event_reference),
        status=status,
        evidence_observed_at=event.evidence_observed_at,
        resolution_deadline_at=event.resolution_deadline_at,
        evidence_age_seconds=age_seconds,
        deadline_proximity_seconds=deadline_seconds,
        evidence_trust_score=event.evidence_trust_score,
        evidence_strength_score=event.evidence_strength_score,
        evidence_revision_risk=event.evidence_revision_risk,
        latency_pressure_score=latency_pressure_score,
        trust_gap_score=trust_gap_score,
        strength_gap_score=strength_gap_score,
        deadline_pressure_score=deadline_pressure_score,
        evidence_latency_decay_score=decay_score,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    age_seconds: Decimal,
    evidence_trust_score: Decimal,
    evidence_strength_score: Decimal,
    evidence_revision_risk: Decimal,
    deadline_proximity_seconds: Decimal | None,
    evidence_latency_decay_score: Decimal,
    config: ResearchEventResolutionEvidenceLatencyDecayConfig,
) -> str:
    if (
        age_seconds >= config.evidence_latency_block_seconds
        or evidence_trust_score <= ZERO
        or evidence_strength_score <= ZERO
        or evidence_revision_risk >= config.revision_block_threshold
        or evidence_latency_decay_score >= config.decay_block_threshold
        or (
            deadline_proximity_seconds is not None
            and deadline_proximity_seconds <= config.deadline_block_seconds
        )
    ):
        return STATUS_BLOCK
    if (
        age_seconds >= config.evidence_latency_watch_seconds
        or evidence_trust_score < config.minimum_evidence_trust_score
        or evidence_strength_score < config.minimum_evidence_strength_score
        or evidence_revision_risk >= config.revision_watch_threshold
        or evidence_latency_decay_score >= config.decay_watch_threshold
        or (
            deadline_proximity_seconds is not None
            and deadline_proximity_seconds <= config.deadline_watch_seconds
        )
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    extra_reason_codes: tuple[str, ...],
    *,
    age_seconds: Decimal,
    evidence_trust_score: Decimal,
    evidence_strength_score: Decimal,
    evidence_revision_risk: Decimal,
    deadline_proximity_seconds: Decimal | None,
    evidence_latency_decay_score: Decimal,
    config: ResearchEventResolutionEvidenceLatencyDecayConfig,
) -> tuple[str, ...]:
    issue_codes: list[str] = []
    if age_seconds >= config.evidence_latency_watch_seconds:
        issue_codes.append("evidence_latency_stale")
    if evidence_trust_score < config.minimum_evidence_trust_score:
        issue_codes.append("evidence_trust_gap")
    if evidence_strength_score < config.minimum_evidence_strength_score:
        issue_codes.append("evidence_strength_gap")
    if evidence_revision_risk >= config.revision_watch_threshold:
        issue_codes.append("evidence_revision_risk")
    if (
        deadline_proximity_seconds is not None
        and deadline_proximity_seconds <= config.deadline_watch_seconds
    ):
        issue_codes.append("resolution_deadline_pressure")
    if evidence_latency_decay_score >= config.decay_watch_threshold:
        issue_codes.append("evidence_latency_decay_elevated")
    if not issue_codes:
        return tuple(sorted(extra_reason_codes)) + ("evidence_latency_clear",)
    return tuple(issue_codes) + tuple(sorted(extra_reason_codes))


def _report_status(
    rows: tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("evidence_latency_empty",)
    issue_codes = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code
        not in (
            "evidence_latency_empty",
            "evidence_latency_clear",
        )
        and any(reason_code in row.reason_codes for row in rows)
    )
    if issue_codes:
        return issue_codes
    return ("evidence_latency_clear",)


def _normalize_events(
    events: Iterable[ResearchEventResolutionEvidenceLatencyDecayInput],
) -> tuple[ResearchEventResolutionEvidenceLatencyDecayInput, ...]:
    if isinstance(events, str | bytes):
        raise ValueError("events must be an iterable")
    try:
        normalized = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    seen: set[str] = set()
    for event in normalized:
        if type(event) is not ResearchEventResolutionEvidenceLatencyDecayInput:
            raise ValueError(
                "events must contain ResearchEventResolutionEvidenceLatencyDecayInput values",
            )
        require_paper_only_flags("evidence latency decay input", event)
        if event.event_reference in seen:
            raise ValueError("event_reference values must be unique")
        seen.add(event.event_reference)
    return tuple(
        sorted(
            normalized,
            key=lambda event: (
                _event_digest(event.event_reference),
                event.evidence_observed_at,
            ),
        ),
    )


def _validate_event_times(
    events: tuple[ResearchEventResolutionEvidenceLatencyDecayInput, ...],
    generated_at: datetime,
) -> None:
    for event in events:
        if event.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must be <= generated_at")


def _sort_rows(
    rows: tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...],
) -> tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchEventResolutionEvidenceLatencyDecayRow,
) -> tuple[int, str]:
    return (STATUS_RANK[row.status], row.event_digest)


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionEvidenceLatencyDecayRow],
) -> tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionEvidenceLatencyDecayRow:
            raise ValueError("rows must contain exact evidence latency decay rows")
        require_paper_only_flags("evidence latency decay row", row)
        if row.event_digest in seen:
            raise ValueError("rows event_digest values must be unique")
        seen.add(row.event_digest)
    if normalized != _sort_rows(normalized):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _validate_config(
    config: ResearchEventResolutionEvidenceLatencyDecayConfig,
) -> None:
    if config.evidence_latency_block_seconds <= config.evidence_latency_watch_seconds:
        raise ValueError(
            "evidence_latency_block_seconds must exceed evidence_latency_watch_seconds",
        )
    if config.deadline_block_seconds > config.deadline_watch_seconds:
        raise ValueError("deadline_block_seconds must not exceed deadline_watch_seconds")
    if config.revision_block_threshold < config.revision_watch_threshold:
        raise ValueError("revision_block_threshold must be at least revision_watch_threshold")
    if config.decay_block_threshold <= config.decay_watch_threshold:
        raise ValueError("decay_block_threshold must exceed decay_watch_threshold")
    weights = (
        config.latency_weight
        + config.trust_gap_weight
        + config.strength_gap_weight
        + config.revision_weight
        + config.deadline_weight
    )
    if weights != ONE:
        raise ValueError("decay weights must sum to 1.000000")


def _validate_row(row: ResearchEventResolutionEvidenceLatencyDecayRow) -> None:
    if (
        row.resolution_deadline_at is None
        and row.deadline_proximity_seconds is not None
    ):
        raise ValueError("deadline_proximity_seconds must be none without deadline")
    if row.status == STATUS_PASS and "evidence_latency_clear" not in row.reason_codes:
        raise ValueError("pass rows must have the clear reason code")
    if row.status != STATUS_PASS and "evidence_latency_clear" in row.reason_codes:
        raise ValueError("non-pass rows must not have the clear reason code")


def _validate_report(report: ResearchEventResolutionEvidenceLatencyDecayReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    for status in RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_STATUSES:
        field_name = f"{status}_count"
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    expected_reason_count_fields = {
        "stale_count": "evidence_latency_stale",
        "trust_gap_count": "evidence_trust_gap",
        "strength_gap_count": "evidence_strength_gap",
        "revision_risk_count": "evidence_revision_risk",
        "deadline_pressure_count": "resolution_deadline_pressure",
    }
    for field_name, reason_code in expected_reason_count_fields.items():
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    age_values = tuple(row.evidence_age_seconds for row in report.rows)
    score_values = tuple(row.evidence_latency_decay_score for row in report.rows)
    if report.max_evidence_age_seconds != max(age_values, default=ZERO):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.average_evidence_latency_decay_score != _average_ratio(score_values):
        raise ValueError("average_evidence_latency_decay_score must match rows")
    if report.highest_evidence_latency_decay_score != max(score_values, default=ZERO):
        raise ValueError("highest_evidence_latency_decay_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match report payload")


def _status_count(
    rows: tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventResolutionEvidenceLatencyDecayRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("duration seconds must be nonnegative")
    return seconds.quantize(QUANTUM)


def _deadline_proximity_seconds(
    generated_at: datetime,
    deadline_at: datetime | None,
) -> Decimal | None:
    if deadline_at is None:
        return None
    if deadline_at <= generated_at:
        return ZERO
    return _duration_seconds(generated_at, deadline_at)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = (numerator / denominator).quantize(QUANTUM)
    if value > ONE:
        return ONE
    return value


def _score_gap(value: Decimal) -> Decimal:
    return (ONE - value).quantize(QUANTUM)


def _deadline_pressure_score(
    deadline_proximity_seconds: Decimal | None,
    config: ResearchEventResolutionEvidenceLatencyDecayConfig,
) -> Decimal:
    if deadline_proximity_seconds is None:
        return ZERO
    if deadline_proximity_seconds <= config.deadline_block_seconds:
        return ONE
    if deadline_proximity_seconds > config.deadline_watch_seconds:
        return ZERO
    denominator = config.deadline_watch_seconds - config.deadline_block_seconds
    return _capped_ratio(config.deadline_watch_seconds - deadline_proximity_seconds, denominator)


def _decay_score(
    *,
    latency_pressure_score: Decimal,
    trust_gap_score: Decimal,
    strength_gap_score: Decimal,
    revision_risk: Decimal,
    deadline_pressure_score: Decimal,
    config: ResearchEventResolutionEvidenceLatencyDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            latency_pressure_score * config.latency_weight
            + trust_gap_score * config.trust_gap_weight
            + strength_gap_score * config.strength_gap_weight
            + revision_risk * config.revision_weight
            + deadline_pressure_score * config.deadline_weight
        ).quantize(QUANTUM)


def _require_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_seconds_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_optional_nonnegative_seconds_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_seconds_decimal(field_name, value)


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return quantized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_extra_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(reason_codes))


def _normalize_row_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _normalize_report_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    expected = tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sorting")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_supported_config_version(value: object) -> None:
    _require_public_string("config_version", value)
    if value != DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_public_surface_fragment(value):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_public_surface_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_public_surface_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_public_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in PUBLIC_SURFACE_FRAGMENTS)


def _event_digest(event_reference: str) -> str:
    return hashlib.sha256(event_reference.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchEventResolutionEvidenceLatencyDecayReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_payload(payload)


def _digest_payload(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_STATUSES",
    "ResearchEventResolutionEvidenceLatencyDecayConfig",
    "ResearchEventResolutionEvidenceLatencyDecayInput",
    "ResearchEventResolutionEvidenceLatencyDecayReport",
    "ResearchEventResolutionEvidenceLatencyDecayRow",
    "build_research_event_resolution_evidence_latency_decay_report",
    "research_event_resolution_evidence_latency_decay_digest",
    "research_event_resolution_evidence_latency_decay_payload",
    "validate_research_event_resolution_evidence_latency_decay_digest",
)
