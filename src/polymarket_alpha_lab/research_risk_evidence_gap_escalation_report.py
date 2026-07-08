"""Pure Phase 1 aggregate evidence-gap escalation report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_RISK_EVIDENCE_GAP_ESCALATION_CONFIG_VERSION = (
    "research-risk-evidence-gap-escalation-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
REASON_CODE_SEQUENCE = (
    "missing_source_class_gap",
    "stale_research_observation",
    "unresolved_evidence_contradiction",
    "manual_review_urgency_block",
    "manual_review_urgency_watch",
    "evidence_gap_escalation_pass",
)
PASS_REASON = "evidence_gap_escalation_pass"
MISSING_SOURCE_CLASS_REASON = "missing_source_class_gap"
STALE_OBSERVATION_REASON = "stale_research_observation"
UNRESOLVED_CONTRADICTION_REASON = "unresolved_evidence_contradiction"
MANUAL_REVIEW_URGENCY_BLOCK_REASON = "manual_review_urgency_block"
MANUAL_REVIEW_URGENCY_WATCH_REASON = "manual_review_urgency_watch"

TOP_LEVEL_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "reason_codes",
    "counts",
    "manual_review_urgency_score",
    "thresholds",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
TOP_LEVEL_PAYLOAD_FIELDS = (
    *TOP_LEVEL_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
COUNT_PAYLOAD_FIELDS = (
    "research_item_count",
    "observation_count",
    "required_source_class_count",
    "observed_source_class_count",
    "missing_source_class_count",
    "stale_observation_count",
    "unresolved_contradiction_count",
    "pass_count",
    "watch_count",
    "block_count",
)
THRESHOLD_PAYLOAD_FIELDS = (
    "required_source_classes",
    "stale_observation_seconds",
    "watch_manual_review_urgency",
    "block_manual_review_urgency",
)
ROW_PAYLOAD_FIELDS = (
    "research_slug",
    "observation_count",
    "observed_source_class_count",
    "required_source_class_count",
    "missing_source_class_count",
    "missing_source_classes",
    "stale_observation_count",
    "unresolved_contradiction_count",
    "max_observation_age_seconds",
    "manual_review_urgency_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "recommendation",
        "sizing",
        "raw_id",
        "raw-id",
        "rawid",
        "url",
        "http://",
        "https://",
        "source_text",
        "source text",
        "database",
        "network",
        "wallet",
        "order",
        "live",
        "trading",
        "trade",
        "auth",
        "private",
        "secret",
        "token",
        "account",
        "buy",
        "sell",
    ),
)


@dataclass(frozen=True)
class ResearchRiskEvidenceGapEscalationConfig:
    config_version: str = DEFAULT_RESEARCH_RISK_EVIDENCE_GAP_ESCALATION_CONFIG_VERSION
    required_source_classes: tuple[str, ...] = ("official", "primary", "context")
    stale_observation_seconds: Decimal = Decimal("86400.000000")
    watch_manual_review_urgency: Decimal = Decimal("0.333333")
    block_manual_review_urgency: Decimal = Decimal("0.666667")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchRiskEvidenceGapEscalationConfig:
            raise TypeError(
                "ResearchRiskEvidenceGapEscalationConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchRiskEvidenceGapEscalationConfig:
            raise ValueError(
                "config must be exactly ResearchRiskEvidenceGapEscalationConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_source_classes",
            _normalize_required_source_classes(self.required_source_classes),
        )
        object.__setattr__(
            self,
            "stale_observation_seconds",
            _require_positive_decimal(
                "stale_observation_seconds",
                self.stale_observation_seconds,
            ),
        )
        for field_name in (
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_manual_review_urgency <= self.watch_manual_review_urgency:
            raise ValueError(
                "block_manual_review_urgency must exceed watch_manual_review_urgency",
            )
        require_paper_only_flags("research risk evidence gap escalation config", self)


@dataclass(frozen=True)
class ResearchRiskEvidenceGapEscalationObservation:
    research_slug: str
    source_class: str
    observed_at: datetime
    contradiction_open: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchRiskEvidenceGapEscalationObservation:
            raise TypeError(
                "ResearchRiskEvidenceGapEscalationObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchRiskEvidenceGapEscalationObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchRiskEvidenceGapEscalationObservation",
            )
        _require_public_string("research_slug", self.research_slug)
        _require_public_string("source_class", self.source_class)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.contradiction_open) is not bool:
            raise ValueError("contradiction_open must be a bool")
        require_paper_only_flags(
            "research risk evidence gap escalation observation",
            self,
        )


@dataclass(frozen=True)
class ResearchRiskEvidenceGapEscalationRow:
    research_slug: str
    observation_count: Decimal
    observed_source_class_count: Decimal
    required_source_class_count: Decimal
    missing_source_class_count: Decimal
    missing_source_classes: tuple[str, ...]
    stale_observation_count: Decimal
    unresolved_contradiction_count: Decimal
    max_observation_age_seconds: Decimal
    manual_review_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchRiskEvidenceGapEscalationRow:
            raise TypeError(
                "ResearchRiskEvidenceGapEscalationRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchRiskEvidenceGapEscalationRow:
            raise ValueError("row must be exactly ResearchRiskEvidenceGapEscalationRow")
        _require_public_string("research_slug", self.research_slug)
        for field_name in (
            "observation_count",
            "observed_source_class_count",
            "required_source_class_count",
            "missing_source_class_count",
            "stale_observation_count",
            "unresolved_contradiction_count",
            "max_observation_age_seconds",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_source_classes",
            _normalize_source_class_tuple(
                "missing_source_classes",
                self.missing_source_classes,
                allow_empty=True,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("research risk evidence gap escalation row", self)


@dataclass(frozen=True)
class ResearchRiskEvidenceGapEscalationReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    research_item_count: Decimal
    observation_count: Decimal
    required_source_class_count: Decimal
    observed_source_class_count: Decimal
    missing_source_class_count: Decimal
    stale_observation_count: Decimal
    unresolved_contradiction_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    manual_review_urgency_score: Decimal
    required_source_classes: tuple[str, ...]
    stale_observation_seconds: Decimal
    watch_manual_review_urgency: Decimal
    block_manual_review_urgency: Decimal
    rows: tuple[ResearchRiskEvidenceGapEscalationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchRiskEvidenceGapEscalationReport:
            raise TypeError(
                "ResearchRiskEvidenceGapEscalationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchRiskEvidenceGapEscalationReport:
            raise ValueError(
                "report must be exactly ResearchRiskEvidenceGapEscalationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "research_item_count",
            "observation_count",
            "required_source_class_count",
            "observed_source_class_count",
            "missing_source_class_count",
            "stale_observation_count",
            "unresolved_contradiction_count",
            "pass_count",
            "watch_count",
            "block_count",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_classes",
            _normalize_required_source_classes(self.required_source_classes),
        )
        object.__setattr__(
            self,
            "stale_observation_seconds",
            _require_positive_decimal(
                "stale_observation_seconds",
                self.stale_observation_seconds,
            ),
        )
        for field_name in (
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_manual_review_urgency <= self.watch_manual_review_urgency:
            raise ValueError(
                "block_manual_review_urgency must exceed watch_manual_review_urgency",
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("research risk evidence gap escalation report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_research_risk_evidence_gap_escalation_report(
    observations: list[ResearchRiskEvidenceGapEscalationObservation]
    | tuple[ResearchRiskEvidenceGapEscalationObservation, ...],
    *,
    config: ResearchRiskEvidenceGapEscalationConfig,
    generated_at: datetime,
) -> ResearchRiskEvidenceGapEscalationReport:
    if type(config) is not ResearchRiskEvidenceGapEscalationConfig:
        raise ValueError("config must be a ResearchRiskEvidenceGapEscalationConfig")
    require_paper_only_flags("research risk evidence gap escalation config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = _rows_from_observations(
        normalized_observations,
        config=config,
        generated_at=generated_at_utc,
    )

    return ResearchRiskEvidenceGapEscalationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        research_item_count=_decimal_count(len(rows)),
        observation_count=_sum_decimal(row.observation_count for row in rows),
        required_source_class_count=_sum_decimal(
            row.required_source_class_count for row in rows
        ),
        observed_source_class_count=_sum_decimal(
            row.observed_source_class_count for row in rows
        ),
        missing_source_class_count=_sum_decimal(
            row.missing_source_class_count for row in rows
        ),
        stale_observation_count=_sum_decimal(
            row.stale_observation_count for row in rows
        ),
        unresolved_contradiction_count=_sum_decimal(
            row.unresolved_contradiction_count for row in rows
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        manual_review_urgency_score=_max_manual_review_urgency_score(rows),
        required_source_classes=config.required_source_classes,
        stale_observation_seconds=config.stale_observation_seconds,
        watch_manual_review_urgency=config.watch_manual_review_urgency,
        block_manual_review_urgency=config.block_manual_review_urgency,
        rows=rows,
    )


def research_risk_evidence_gap_escalation_report_payload(
    report: ResearchRiskEvidenceGapEscalationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchRiskEvidenceGapEscalationReport:
        require_paper_only_flags("research risk evidence gap escalation report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchRiskEvidenceGapEscalationReport")


def _rows_from_observations(
    observations: tuple[ResearchRiskEvidenceGapEscalationObservation, ...],
    *,
    config: ResearchRiskEvidenceGapEscalationConfig,
    generated_at: datetime,
) -> tuple[ResearchRiskEvidenceGapEscalationRow, ...]:
    by_slug: dict[str, list[ResearchRiskEvidenceGapEscalationObservation]] = {}
    for observation in observations:
        by_slug.setdefault(observation.research_slug, []).append(observation)
    return _sort_rows(
        tuple(
            _row_from_observations(
                research_slug,
                tuple(slug_observations),
                config=config,
                generated_at=generated_at,
            )
            for research_slug, slug_observations in sorted(by_slug.items())
        ),
    )


def _row_from_observations(
    research_slug: str,
    observations: tuple[ResearchRiskEvidenceGapEscalationObservation, ...],
    *,
    config: ResearchRiskEvidenceGapEscalationConfig,
    generated_at: datetime,
) -> ResearchRiskEvidenceGapEscalationRow:
    observed_source_classes = tuple(sorted({row.source_class for row in observations}))
    missing_source_classes = tuple(
        source_class
        for source_class in config.required_source_classes
        if source_class not in observed_source_classes
    )
    stale_observation_count = _decimal_count(
        sum(
            1
            for observation in observations
            if _age_seconds(generated_at, observation.observed_at)
            > config.stale_observation_seconds
        ),
    )
    unresolved_contradiction_count = _decimal_count(
        sum(1 for observation in observations if observation.contradiction_open),
    )
    missing_source_class_count = _decimal_count(len(missing_source_classes))
    required_source_class_count = _decimal_count(len(config.required_source_classes))
    manual_review_urgency_score = _manual_review_urgency_score(
        missing_source_class_count=missing_source_class_count,
        stale_observation_count=stale_observation_count,
        unresolved_contradiction_count=unresolved_contradiction_count,
        required_source_class_count=required_source_class_count,
    )
    status = _status_from_manual_review_urgency_score(
        manual_review_urgency_score,
        config=config,
    )

    return ResearchRiskEvidenceGapEscalationRow(
        research_slug=research_slug,
        observation_count=_decimal_count(len(observations)),
        observed_source_class_count=_decimal_count(len(observed_source_classes)),
        required_source_class_count=required_source_class_count,
        missing_source_class_count=missing_source_class_count,
        missing_source_classes=missing_source_classes,
        stale_observation_count=stale_observation_count,
        unresolved_contradiction_count=unresolved_contradiction_count,
        max_observation_age_seconds=max(
            (_age_seconds(generated_at, observation.observed_at) for observation in observations),
            default=ZERO,
        ),
        manual_review_urgency_score=manual_review_urgency_score,
        status=status,
        reason_codes=_row_reason_codes(
            missing_source_class_count=missing_source_class_count,
            stale_observation_count=stale_observation_count,
            unresolved_contradiction_count=unresolved_contradiction_count,
            status=status,
        ),
    )


def _manual_review_urgency_score(
    *,
    missing_source_class_count: Decimal,
    stale_observation_count: Decimal,
    unresolved_contradiction_count: Decimal,
    required_source_class_count: Decimal,
) -> Decimal:
    gap_count = (
        missing_source_class_count
        + stale_observation_count
        + unresolved_contradiction_count
    )
    return min(ONE, _ratio(gap_count, required_source_class_count))


def _status_from_manual_review_urgency_score(
    manual_review_urgency_score: Decimal,
    *,
    config: ResearchRiskEvidenceGapEscalationConfig,
) -> str:
    if manual_review_urgency_score >= config.block_manual_review_urgency:
        return "block"
    if manual_review_urgency_score >= config.watch_manual_review_urgency:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    missing_source_class_count: Decimal,
    stale_observation_count: Decimal,
    unresolved_contradiction_count: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_source_class_count > ZERO:
        reason_codes.append(MISSING_SOURCE_CLASS_REASON)
    if stale_observation_count > ZERO:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if unresolved_contradiction_count > ZERO:
        reason_codes.append(UNRESOLVED_CONTRADICTION_REASON)
    if status == "block":
        reason_codes.append(MANUAL_REVIEW_URGENCY_BLOCK_REASON)
    elif status == "watch":
        reason_codes.append(MANUAL_REVIEW_URGENCY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchRiskEvidenceGapEscalationRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code == PASS_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _report_status(rows: tuple[ResearchRiskEvidenceGapEscalationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_public_payload_values(
    report: ResearchRiskEvidenceGapEscalationReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "counts": {
            "research_item_count": str(report.research_item_count),
            "observation_count": str(report.observation_count),
            "required_source_class_count": str(report.required_source_class_count),
            "observed_source_class_count": str(report.observed_source_class_count),
            "missing_source_class_count": str(report.missing_source_class_count),
            "stale_observation_count": str(report.stale_observation_count),
            "unresolved_contradiction_count": str(
                report.unresolved_contradiction_count,
            ),
            "pass_count": str(report.pass_count),
            "watch_count": str(report.watch_count),
            "block_count": str(report.block_count),
        },
        "manual_review_urgency_score": str(report.manual_review_urgency_score),
        "thresholds": {
            "required_source_classes": list(report.required_source_classes),
            "stale_observation_seconds": str(report.stale_observation_seconds),
            "watch_manual_review_urgency": str(report.watch_manual_review_urgency),
            "block_manual_review_urgency": str(report.block_manual_review_urgency),
        },
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchRiskEvidenceGapEscalationRow) -> dict[str, Any]:
    return {
        "research_slug": row.research_slug,
        "observation_count": str(row.observation_count),
        "observed_source_class_count": str(row.observed_source_class_count),
        "required_source_class_count": str(row.required_source_class_count),
        "missing_source_class_count": str(row.missing_source_class_count),
        "missing_source_classes": list(row.missing_source_classes),
        "stale_observation_count": str(row.stale_observation_count),
        "unresolved_contradiction_count": str(row.unresolved_contradiction_count),
        "max_observation_age_seconds": str(row.max_observation_age_seconds),
        "manual_review_urgency_score": str(row.manual_review_urgency_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: ResearchRiskEvidenceGapEscalationReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: ResearchRiskEvidenceGapEscalationReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        field_name: payload[field_name]
        for field_name in TOP_LEVEL_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(
        ("research_risk_evidence_gap_escalation_report|" + encoded).encode("utf-8"),
    ).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _require_exact_keys("payload", payload, TOP_LEVEL_PAYLOAD_FIELDS)
    _datetime_from_payload_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_status("status", payload["status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _validate_public_counts(payload["counts"])
    _require_decimal_payload_string(
        "manual_review_urgency_score",
        payload["manual_review_urgency_score"],
    )
    _validate_public_thresholds(payload["thresholds"])
    _validate_public_rows(payload["rows"])
    _require_public_payload_flags("payload", payload)
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    _validate_public_payload_consistency(payload)


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    counts = payload["counts"]
    thresholds = payload["thresholds"]
    ResearchRiskEvidenceGapEscalationReport(
        generated_at=_datetime_from_payload_string("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        research_item_count=_decimal_from_payload_string(
            "research_item_count",
            counts["research_item_count"],
        ),
        observation_count=_decimal_from_payload_string(
            "observation_count",
            counts["observation_count"],
        ),
        required_source_class_count=_decimal_from_payload_string(
            "required_source_class_count",
            counts["required_source_class_count"],
        ),
        observed_source_class_count=_decimal_from_payload_string(
            "observed_source_class_count",
            counts["observed_source_class_count"],
        ),
        missing_source_class_count=_decimal_from_payload_string(
            "missing_source_class_count",
            counts["missing_source_class_count"],
        ),
        stale_observation_count=_decimal_from_payload_string(
            "stale_observation_count",
            counts["stale_observation_count"],
        ),
        unresolved_contradiction_count=_decimal_from_payload_string(
            "unresolved_contradiction_count",
            counts["unresolved_contradiction_count"],
        ),
        pass_count=_decimal_from_payload_string("pass_count", counts["pass_count"]),
        watch_count=_decimal_from_payload_string("watch_count", counts["watch_count"]),
        block_count=_decimal_from_payload_string("block_count", counts["block_count"]),
        manual_review_urgency_score=_decimal_from_payload_string(
            "manual_review_urgency_score",
            payload["manual_review_urgency_score"],
        ),
        required_source_classes=tuple(thresholds["required_source_classes"]),
        stale_observation_seconds=_decimal_from_payload_string(
            "stale_observation_seconds",
            thresholds["stale_observation_seconds"],
        ),
        watch_manual_review_urgency=_decimal_from_payload_string(
            "watch_manual_review_urgency",
            thresholds["watch_manual_review_urgency"],
        ),
        block_manual_review_urgency=_decimal_from_payload_string(
            "block_manual_review_urgency",
            thresholds["block_manual_review_urgency"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in payload["rows"]),
        derived_validation_digest=payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )


def _row_from_public_payload(row: dict[str, Any]) -> ResearchRiskEvidenceGapEscalationRow:
    return ResearchRiskEvidenceGapEscalationRow(
        research_slug=row["research_slug"],
        observation_count=_decimal_from_payload_string(
            "observation_count",
            row["observation_count"],
        ),
        observed_source_class_count=_decimal_from_payload_string(
            "observed_source_class_count",
            row["observed_source_class_count"],
        ),
        required_source_class_count=_decimal_from_payload_string(
            "required_source_class_count",
            row["required_source_class_count"],
        ),
        missing_source_class_count=_decimal_from_payload_string(
            "missing_source_class_count",
            row["missing_source_class_count"],
        ),
        missing_source_classes=tuple(row["missing_source_classes"]),
        stale_observation_count=_decimal_from_payload_string(
            "stale_observation_count",
            row["stale_observation_count"],
        ),
        unresolved_contradiction_count=_decimal_from_payload_string(
            "unresolved_contradiction_count",
            row["unresolved_contradiction_count"],
        ),
        max_observation_age_seconds=_decimal_from_payload_string(
            "max_observation_age_seconds",
            row["max_observation_age_seconds"],
        ),
        manual_review_urgency_score=_decimal_from_payload_string(
            "manual_review_urgency_score",
            row["manual_review_urgency_score"],
        ),
        status=row["status"],
        reason_codes=tuple(row["reason_codes"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _validate_public_counts(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("counts must be an object")
    _require_exact_keys("counts", value, COUNT_PAYLOAD_FIELDS)
    for field_name in COUNT_PAYLOAD_FIELDS:
        _require_decimal_payload_string(field_name, value[field_name])


def _validate_public_thresholds(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("thresholds must be an object")
    _require_exact_keys("thresholds", value, THRESHOLD_PAYLOAD_FIELDS)
    _normalize_public_string_list(
        "required_source_classes",
        value["required_source_classes"],
    )
    _require_decimal_payload_string(
        "stale_observation_seconds",
        value["stale_observation_seconds"],
    )
    _require_decimal_payload_string(
        "watch_manual_review_urgency",
        value["watch_manual_review_urgency"],
    )
    _require_decimal_payload_string(
        "block_manual_review_urgency",
        value["block_manual_review_urgency"],
    )


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    seen: set[str] = set()
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows entries must be objects")
        _require_exact_keys("rows", row, ROW_PAYLOAD_FIELDS)
        _require_public_string("research_slug", row["research_slug"])
        if row["research_slug"] in seen:
            raise ValueError("rows must be unique by research_slug")
        seen.add(row["research_slug"])
        for field_name in (
            "observation_count",
            "observed_source_class_count",
            "required_source_class_count",
            "missing_source_class_count",
            "stale_observation_count",
            "unresolved_contradiction_count",
            "max_observation_age_seconds",
            "manual_review_urgency_score",
        ):
            _require_decimal_payload_string(field_name, row[field_name])
        _normalize_public_string_list(
            "missing_source_classes",
            row["missing_source_classes"],
        )
        _require_status("status", row["status"])
        _normalize_public_reason_codes("reason_codes", row["reason_codes"])
        _require_public_payload_flags("row", row)


def _validate_row(row: ResearchRiskEvidenceGapEscalationRow) -> None:
    if row.required_source_class_count <= ZERO:
        raise ValueError("required_source_class_count must be positive")
    if row.observed_source_class_count > row.observation_count:
        raise ValueError("observed_source_class_count must not exceed observation_count")
    if row.missing_source_class_count != _decimal_count(len(row.missing_source_classes)):
        raise ValueError("missing_source_class_count must match missing_source_classes")
    if row.observed_source_class_count + row.missing_source_class_count < ONE:
        raise ValueError("row must contain at least one source class signal")
    expected_score = _manual_review_urgency_score(
        missing_source_class_count=row.missing_source_class_count,
        stale_observation_count=row.stale_observation_count,
        unresolved_contradiction_count=row.unresolved_contradiction_count,
        required_source_class_count=row.required_source_class_count,
    )
    if row.manual_review_urgency_score != expected_score:
        raise ValueError("manual_review_urgency_score must match row evidence gaps")
    if row.reason_codes != _row_reason_codes(
        missing_source_class_count=row.missing_source_class_count,
        stale_observation_count=row.stale_observation_count,
        unresolved_contradiction_count=row.unresolved_contradiction_count,
        status=row.status,
    ):
        raise ValueError("reason_codes must match row evidence gaps")


def _validate_report(report: ResearchRiskEvidenceGapEscalationReport) -> None:
    if report.research_item_count != _decimal_count(len(report.rows)):
        raise ValueError("research_item_count must match rows")
    if report.observation_count != _sum_decimal(row.observation_count for row in report.rows):
        raise ValueError("observation_count must match rows")
    if report.required_source_class_count != _sum_decimal(
        row.required_source_class_count for row in report.rows
    ):
        raise ValueError("required_source_class_count must match rows")
    if report.observed_source_class_count != _sum_decimal(
        row.observed_source_class_count for row in report.rows
    ):
        raise ValueError("observed_source_class_count must match rows")
    if report.missing_source_class_count != _sum_decimal(
        row.missing_source_class_count for row in report.rows
    ):
        raise ValueError("missing_source_class_count must match rows")
    if report.stale_observation_count != _sum_decimal(
        row.stale_observation_count for row in report.rows
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.unresolved_contradiction_count != _sum_decimal(
        row.unresolved_contradiction_count for row in report.rows
    ):
        raise ValueError("unresolved_contradiction_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.manual_review_urgency_score != _max_manual_review_urgency_score(report.rows):
        raise ValueError("manual_review_urgency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchRiskEvidenceGapEscalationObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    for observation in observations:
        if type(observation) is not ResearchRiskEvidenceGapEscalationObservation:
            raise ValueError("observations must contain evidence gap observations")
        require_paper_only_flags(
            "research risk evidence gap escalation observation",
            observation,
        )
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.research_slug,
                observation.source_class,
                observation.observed_at,
                observation.contradiction_open,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchRiskEvidenceGapEscalationRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchRiskEvidenceGapEscalationRow:
            raise ValueError("rows must contain evidence gap escalation rows")
        require_paper_only_flags("research risk evidence gap escalation row", row)
        if row.research_slug in seen:
            raise ValueError("rows must be unique by research_slug")
        seen.add(row.research_slug)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _sort_rows(
    rows: tuple[ResearchRiskEvidenceGapEscalationRow, ...],
) -> tuple[ResearchRiskEvidenceGapEscalationRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                -row.manual_review_urgency_score,
                -row.missing_source_class_count,
                -row.stale_observation_count,
                -row.unresolved_contradiction_count,
                row.research_slug,
            ),
        ),
    )


def _normalize_required_source_classes(value: object) -> tuple[str, ...]:
    return _normalize_source_class_tuple(
        "source classes",
        value,
        allow_empty=False,
    )


def _normalize_source_class_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    source_classes = tuple(value)
    if not source_classes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for source_class in source_classes:
        _require_public_string("source_class", source_class)
        if source_class in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(source_class)
    return source_classes


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODE_SEQUENCE if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _normalize_public_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_public_string(field_name, item)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return tuple(value)


def _status_count(
    rows: tuple[ResearchRiskEvidenceGapEscalationRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _max_manual_review_urgency_score(
    rows: tuple[ResearchRiskEvidenceGapEscalationRow, ...],
) -> Decimal:
    return max((row.manual_review_urgency_score for row in rows), default=ZERO)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal_payload_string(field_name: str, value: object) -> None:
    _decimal_from_payload_string(field_name, value)


def _decimal_from_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    _require_public_string(field_name, value)
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANT)


def _datetime_from_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    _require_public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a concrete UTC offset")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe text in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"unsafe field in {label}")
            if key == DERIVED_VALIDATION_DIGEST_FIELD:
                continue
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _require_exact_keys(
    label: str,
    value: dict[Any, Any],
    expected_fields: tuple[str, ...],
) -> None:
    for field_name in expected_fields:
        if field_name not in value:
            raise ValueError(f"{label}.{field_name} is required")
    extra_fields = sorted(set(value) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _require_public_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "DEFAULT_RESEARCH_RISK_EVIDENCE_GAP_ESCALATION_CONFIG_VERSION",
    "ResearchRiskEvidenceGapEscalationConfig",
    "ResearchRiskEvidenceGapEscalationObservation",
    "ResearchRiskEvidenceGapEscalationReport",
    "ResearchRiskEvidenceGapEscalationRow",
    "build_research_risk_evidence_gap_escalation_report",
    "research_risk_evidence_gap_escalation_report_payload",
)
