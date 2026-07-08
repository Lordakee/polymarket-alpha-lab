"""Pure report-only source confidence and specialist memory bridge report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-source-confidence-memory-bridge-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

EMPTY_REASON = "source_confidence_memory_bridge_empty"
CLEAR_REASON = "source_confidence_memory_bridge_clear"
FRESHNESS_BLOCK_REASON = "freshness_block"
FRESHNESS_WATCH_REASON = "freshness_watch"
AUTHORITY_BLOCK_REASON = "authority_block"
AUTHORITY_WATCH_REASON = "authority_watch"
CORROBORATION_BLOCK_REASON = "corroboration_block"
CORROBORATION_WATCH_REASON = "corroboration_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_block"
CONTRADICTION_WATCH_REASON = "contradiction_watch"
CALIBRATION_EVIDENCE_BLOCK_REASON = "calibration_evidence_block"
CALIBRATION_EVIDENCE_WATCH_REASON = "calibration_evidence_watch"
UNRESOLVED_CAVEATS_BLOCK_REASON = "unresolved_caveats_block"
UNRESOLVED_CAVEATS_WATCH_REASON = "unresolved_caveats_watch"
BRIDGE_CONFIDENCE_BLOCK_REASON = "bridge_confidence_block"
BRIDGE_CONFIDENCE_WATCH_REASON = "bridge_confidence_watch"

ROW_REASON_CODES = (
    FRESHNESS_BLOCK_REASON,
    AUTHORITY_BLOCK_REASON,
    CORROBORATION_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    CALIBRATION_EVIDENCE_BLOCK_REASON,
    UNRESOLVED_CAVEATS_BLOCK_REASON,
    BRIDGE_CONFIDENCE_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    AUTHORITY_WATCH_REASON,
    CORROBORATION_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    CALIBRATION_EVIDENCE_WATCH_REASON,
    UNRESOLVED_CAVEATS_WATCH_REASON,
    BRIDGE_CONFIDENCE_WATCH_REASON,
    CLEAR_REASON,
)

REPORT_BLOCK_PRESENT_REASON = "source_confidence_memory_bridge_block_present"
REPORT_WATCH_PRESENT_REASON = "source_confidence_memory_bridge_watch_present"
REPORT_FRESHNESS_GAP_REASON = "freshness_gap_present"
REPORT_AUTHORITY_GAP_REASON = "authority_gap_present"
REPORT_CORROBORATION_GAP_REASON = "corroboration_gap_present"
REPORT_CONTRADICTION_GAP_REASON = "contradiction_gap_present"
REPORT_CALIBRATION_EVIDENCE_GAP_REASON = "calibration_evidence_gap_present"
REPORT_UNRESOLVED_CAVEATS_REASON = "unresolved_caveats_present"
REPORT_BRIDGE_CONFIDENCE_GAP_REASON = "bridge_confidence_gap_present"
REPORT_CLEAR_REASON = "source_confidence_memory_bridge_report_clear"

REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_FRESHNESS_GAP_REASON,
    REPORT_AUTHORITY_GAP_REASON,
    REPORT_CORROBORATION_GAP_REASON,
    REPORT_CONTRADICTION_GAP_REASON,
    REPORT_CALIBRATION_EVIDENCE_GAP_REASON,
    REPORT_UNRESOLVED_CAVEATS_REASON,
    REPORT_BRIDGE_CONFIDENCE_GAP_REASON,
    REPORT_CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_",
    "_raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "recommend",
    "sizing",
    "secret",
    "credential",
    "private",
    "password",
    "database",
    "network",
    "scrape",
    "scraping",
    "url",
)

UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "raw candidate",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source text",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "recommend",
    "sizing",
    "secret",
    "credential",
    "private",
    "password",
    "database",
    "network",
    "scrape",
    "scraping",
)


@dataclass(frozen=True)
class ResearchSourceConfidenceMemoryBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_REPORT_CONFIG_VERSION
    )
    fresh_age_seconds: Decimal = Decimal("1800.000000")
    stale_age_seconds: Decimal = Decimal("7200.000000")
    min_pass_freshness_score: Decimal = Decimal("0.700000")
    min_watch_freshness_score: Decimal = Decimal("0.500000")
    min_pass_authority_score: Decimal = Decimal("0.650000")
    min_watch_authority_score: Decimal = Decimal("0.450000")
    min_pass_corroboration_score: Decimal = Decimal("0.650000")
    min_watch_corroboration_score: Decimal = Decimal("0.450000")
    max_pass_contradiction_score: Decimal = Decimal("0.150000")
    max_watch_contradiction_score: Decimal = Decimal("0.350000")
    min_pass_calibration_evidence_score: Decimal = Decimal("0.700000")
    min_watch_calibration_evidence_score: Decimal = Decimal("0.500000")
    max_pass_unresolved_caveat_score: Decimal = Decimal("0.100000")
    max_watch_unresolved_caveat_score: Decimal = Decimal("0.250000")
    min_pass_bridge_confidence_score: Decimal = Decimal("0.750000")
    min_watch_bridge_confidence_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceConfidenceMemoryBridgeConfig:
            raise TypeError(
                "ResearchSourceConfidenceMemoryBridgeConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceConfidenceMemoryBridgeConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        for field_name in (
            "min_pass_freshness_score",
            "min_watch_freshness_score",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_corroboration_score",
            "min_watch_corroboration_score",
            "max_pass_contradiction_score",
            "max_watch_contradiction_score",
            "min_pass_calibration_evidence_score",
            "min_watch_calibration_evidence_score",
            "max_pass_unresolved_caveat_score",
            "max_watch_unresolved_caveat_score",
            "min_pass_bridge_confidence_score",
            "min_watch_bridge_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceConfidenceMemoryBridgeObservation:
    triage_group: str
    evidence_family_label: str
    specialist_label: str
    observed_at: datetime
    authority_score: Decimal
    corroboration_score: Decimal
    contradiction_score: Decimal
    specialist_memory_confidence_score: Decimal
    calibration_evidence_score: Decimal
    unresolved_caveat_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceConfidenceMemoryBridgeObservation:
            raise TypeError(
                "ResearchSourceConfidenceMemoryBridgeObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceConfidenceMemoryBridgeObservation,
            "observation",
        )
        for field_name in ("triage_group", "evidence_family_label", "specialist_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "corroboration_score",
            "contradiction_score",
            "specialist_memory_confidence_score",
            "calibration_evidence_score",
            "unresolved_caveat_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceConfidenceMemoryBridgeRow:
    triage_group: str
    evidence_family_label: str
    specialist_label: str
    observed_at: datetime
    observation_age_seconds: Decimal
    freshness_score: Decimal
    authority_score: Decimal
    corroboration_score: Decimal
    contradiction_score: Decimal
    specialist_memory_confidence_score: Decimal
    calibration_evidence_score: Decimal
    unresolved_caveat_score: Decimal
    source_confidence_score: Decimal
    memory_confidence_score: Decimal
    bridge_confidence_score: Decimal
    triage_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceConfidenceMemoryBridgeRow:
            raise TypeError(
                "ResearchSourceConfidenceMemoryBridgeRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceConfidenceMemoryBridgeRow, "row")
        for field_name in ("triage_group", "evidence_family_label", "specialist_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in (
            "freshness_score",
            "authority_score",
            "corroboration_score",
            "contradiction_score",
            "specialist_memory_confidence_score",
            "calibration_evidence_score",
            "unresolved_caveat_score",
            "source_confidence_score",
            "memory_confidence_score",
            "bridge_confidence_score",
            "triage_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceConfidenceMemoryBridgeReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    freshness_gap_count: Decimal
    authority_gap_count: Decimal
    corroboration_gap_count: Decimal
    contradiction_gap_count: Decimal
    calibration_evidence_gap_count: Decimal
    unresolved_caveat_gap_count: Decimal
    bridge_confidence_gap_count: Decimal
    average_source_confidence_score: Decimal
    average_memory_confidence_score: Decimal
    average_bridge_confidence_score: Decimal
    lowest_bridge_confidence_score: Decimal
    highest_triage_pressure_score: Decimal
    highest_contradiction_score: Decimal
    highest_unresolved_caveat_score: Decimal
    oldest_observation_age_seconds: Decimal
    rows: tuple[ResearchSourceConfidenceMemoryBridgeRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceConfidenceMemoryBridgeReport:
            raise TypeError(
                "ResearchSourceConfidenceMemoryBridgeReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceConfidenceMemoryBridgeReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "freshness_gap_count",
            "authority_gap_count",
            "corroboration_gap_count",
            "contradiction_gap_count",
            "calibration_evidence_gap_count",
            "unresolved_caveat_gap_count",
            "bridge_confidence_gap_count",
            "oldest_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_confidence_score",
            "average_memory_confidence_score",
            "average_bridge_confidence_score",
            "lowest_bridge_confidence_score",
            "highest_triage_pressure_score",
            "highest_contradiction_score",
            "highest_unresolved_caveat_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_confidence_memory_bridge_report_payload(self)


def build_research_source_confidence_memory_bridge_report(
    observations: Sequence[ResearchSourceConfidenceMemoryBridgeObservation],
    *,
    config: ResearchSourceConfidenceMemoryBridgeConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceConfidenceMemoryBridgeReport:
    cfg = config or ResearchSourceConfidenceMemoryBridgeConfig()
    if type(cfg) is not ResearchSourceConfidenceMemoryBridgeConfig:
        raise ValueError(
            "config must be exactly ResearchSourceConfidenceMemoryBridgeConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceConfidenceMemoryBridgeReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_report_status(rows),
        observation_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        freshness_gap_count=_reason_count(
            rows,
            (FRESHNESS_BLOCK_REASON, FRESHNESS_WATCH_REASON),
        ),
        authority_gap_count=_reason_count(
            rows,
            (AUTHORITY_BLOCK_REASON, AUTHORITY_WATCH_REASON),
        ),
        corroboration_gap_count=_reason_count(
            rows,
            (CORROBORATION_BLOCK_REASON, CORROBORATION_WATCH_REASON),
        ),
        contradiction_gap_count=_reason_count(
            rows,
            (CONTRADICTION_BLOCK_REASON, CONTRADICTION_WATCH_REASON),
        ),
        calibration_evidence_gap_count=_reason_count(
            rows,
            (CALIBRATION_EVIDENCE_BLOCK_REASON, CALIBRATION_EVIDENCE_WATCH_REASON),
        ),
        unresolved_caveat_gap_count=_reason_count(
            rows,
            (UNRESOLVED_CAVEATS_BLOCK_REASON, UNRESOLVED_CAVEATS_WATCH_REASON),
        ),
        bridge_confidence_gap_count=_reason_count(
            rows,
            (BRIDGE_CONFIDENCE_BLOCK_REASON, BRIDGE_CONFIDENCE_WATCH_REASON),
        ),
        average_source_confidence_score=_average(
            tuple(row.source_confidence_score for row in rows),
        ),
        average_memory_confidence_score=_average(
            tuple(row.memory_confidence_score for row in rows),
        ),
        average_bridge_confidence_score=_average(
            tuple(row.bridge_confidence_score for row in rows),
        ),
        lowest_bridge_confidence_score=min(
            (row.bridge_confidence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_triage_pressure_score=max(
            (row.triage_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_score=max(
            (row.contradiction_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_unresolved_caveat_score=max(
            (row.unresolved_caveat_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_observation_age_seconds=max(
            (row.observation_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_source_confidence_memory_bridge_report_payload(
    report: ResearchSourceConfidenceMemoryBridgeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceConfidenceMemoryBridgeReport:
        raise ValueError(
            "report must be exactly ResearchSourceConfidenceMemoryBridgeReport",
        )
    validate_research_source_confidence_memory_bridge_report_digest(report)
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _reject_raw_payload_numbers(payload)
    return payload


def research_source_confidence_memory_bridge_report_digest(
    report: ResearchSourceConfidenceMemoryBridgeReport,
) -> str:
    if type(report) is not ResearchSourceConfidenceMemoryBridgeReport:
        raise ValueError(
            "report must be exactly ResearchSourceConfidenceMemoryBridgeReport",
        )
    validate_research_source_confidence_memory_bridge_report_digest(report)
    return report.derived_validation_digest


def validate_research_source_confidence_memory_bridge_report_digest(
    report: ResearchSourceConfidenceMemoryBridgeReport,
) -> None:
    if type(report) is not ResearchSourceConfidenceMemoryBridgeReport:
        raise ValueError(
            "report must be exactly ResearchSourceConfidenceMemoryBridgeReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceConfidenceMemoryBridgeObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    seen: set[tuple[str, str, str, datetime]] = set()
    for observation in observations:
        if type(observation) is not ResearchSourceConfidenceMemoryBridgeObservation:
            raise ValueError(
                "observations must contain ResearchSourceConfidenceMemoryBridgeObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        key = (
            observation.triage_group,
            observation.evidence_family_label,
            observation.specialist_label,
            observation.observed_at,
        )
        if key in seen:
            raise ValueError("observations must be unique by public triage labels")
        seen.add(key)
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.triage_group,
                observation.evidence_family_label,
                observation.specialist_label,
                observation.observed_at,
            ),
        ),
    )


def _row_from_observation(
    observation: ResearchSourceConfidenceMemoryBridgeObservation,
    *,
    config: ResearchSourceConfidenceMemoryBridgeConfig,
    generated_at: datetime,
) -> ResearchSourceConfidenceMemoryBridgeRow:
    age_seconds = _age_seconds(generated_at, observation.observed_at)
    freshness_score = _freshness_score(age_seconds, config=config)
    source_confidence_score = _source_confidence_score(
        freshness_score=freshness_score,
        authority_score=observation.authority_score,
        corroboration_score=observation.corroboration_score,
        contradiction_score=observation.contradiction_score,
    )
    memory_confidence_score = _memory_confidence_score(
        specialist_memory_confidence_score=(
            observation.specialist_memory_confidence_score
        ),
        calibration_evidence_score=observation.calibration_evidence_score,
        unresolved_caveat_score=observation.unresolved_caveat_score,
    )
    bridge_confidence_score = _average(
        (source_confidence_score, memory_confidence_score),
    )
    reason_codes = _row_reason_codes(
        freshness_score=freshness_score,
        authority_score=observation.authority_score,
        corroboration_score=observation.corroboration_score,
        contradiction_score=observation.contradiction_score,
        calibration_evidence_score=observation.calibration_evidence_score,
        unresolved_caveat_score=observation.unresolved_caveat_score,
        bridge_confidence_score=bridge_confidence_score,
        config=config,
    )
    return ResearchSourceConfidenceMemoryBridgeRow(
        triage_group=observation.triage_group,
        evidence_family_label=observation.evidence_family_label,
        specialist_label=observation.specialist_label,
        observed_at=observation.observed_at,
        observation_age_seconds=age_seconds,
        freshness_score=freshness_score,
        authority_score=observation.authority_score,
        corroboration_score=observation.corroboration_score,
        contradiction_score=observation.contradiction_score,
        specialist_memory_confidence_score=(
            observation.specialist_memory_confidence_score
        ),
        calibration_evidence_score=observation.calibration_evidence_score,
        unresolved_caveat_score=observation.unresolved_caveat_score,
        source_confidence_score=source_confidence_score,
        memory_confidence_score=memory_confidence_score,
        bridge_confidence_score=bridge_confidence_score,
        triage_pressure_score=_triage_pressure_score(
            bridge_confidence_score=bridge_confidence_score,
            corroboration_score=observation.corroboration_score,
            contradiction_score=observation.contradiction_score,
            calibration_evidence_score=observation.calibration_evidence_score,
            unresolved_caveat_score=observation.unresolved_caveat_score,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    freshness_score: Decimal,
    authority_score: Decimal,
    corroboration_score: Decimal,
    contradiction_score: Decimal,
    calibration_evidence_score: Decimal,
    unresolved_caveat_score: Decimal,
    bridge_confidence_score: Decimal,
    config: ResearchSourceConfidenceMemoryBridgeConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if freshness_score < config.min_watch_freshness_score:
        reason_codes.append(FRESHNESS_BLOCK_REASON)
    elif freshness_score < config.min_pass_freshness_score:
        reason_codes.append(FRESHNESS_WATCH_REASON)
    if authority_score < config.min_watch_authority_score:
        reason_codes.append(AUTHORITY_BLOCK_REASON)
    elif authority_score < config.min_pass_authority_score:
        reason_codes.append(AUTHORITY_WATCH_REASON)
    if corroboration_score < config.min_watch_corroboration_score:
        reason_codes.append(CORROBORATION_BLOCK_REASON)
    elif corroboration_score < config.min_pass_corroboration_score:
        reason_codes.append(CORROBORATION_WATCH_REASON)
    if contradiction_score > config.max_watch_contradiction_score:
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_score > config.max_pass_contradiction_score:
        reason_codes.append(CONTRADICTION_WATCH_REASON)
    if calibration_evidence_score < config.min_watch_calibration_evidence_score:
        reason_codes.append(CALIBRATION_EVIDENCE_BLOCK_REASON)
    elif calibration_evidence_score < config.min_pass_calibration_evidence_score:
        reason_codes.append(CALIBRATION_EVIDENCE_WATCH_REASON)
    if unresolved_caveat_score > config.max_watch_unresolved_caveat_score:
        reason_codes.append(UNRESOLVED_CAVEATS_BLOCK_REASON)
    elif unresolved_caveat_score > config.max_pass_unresolved_caveat_score:
        reason_codes.append(UNRESOLVED_CAVEATS_WATCH_REASON)
    if bridge_confidence_score < config.min_watch_bridge_confidence_score:
        reason_codes.append(BRIDGE_CONFIDENCE_BLOCK_REASON)
    elif bridge_confidence_score < config.min_pass_bridge_confidence_score:
        reason_codes.append(BRIDGE_CONFIDENCE_WATCH_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes) or (CLEAR_REASON,),
        ROW_REASON_CODES,
    )


def _source_confidence_score(
    *,
    freshness_score: Decimal,
    authority_score: Decimal,
    corroboration_score: Decimal,
    contradiction_score: Decimal,
) -> Decimal:
    return _average(
        (
            freshness_score,
            authority_score,
            corroboration_score,
            ONE - contradiction_score,
        ),
    )


def _memory_confidence_score(
    *,
    specialist_memory_confidence_score: Decimal,
    calibration_evidence_score: Decimal,
    unresolved_caveat_score: Decimal,
) -> Decimal:
    return _average(
        (
            specialist_memory_confidence_score,
            calibration_evidence_score,
            ONE - unresolved_caveat_score,
        ),
    )


def _triage_pressure_score(
    *,
    bridge_confidence_score: Decimal,
    corroboration_score: Decimal,
    contradiction_score: Decimal,
    calibration_evidence_score: Decimal,
    unresolved_caveat_score: Decimal,
) -> Decimal:
    return _average(
        (
            ONE - bridge_confidence_score,
            ONE - corroboration_score,
            contradiction_score,
            ONE - calibration_evidence_score,
            unresolved_caveat_score,
        ),
    )


def _freshness_score(
    age_seconds: Decimal,
    *,
    config: ResearchSourceConfidenceMemoryBridgeConfig,
) -> Decimal:
    if age_seconds <= config.fresh_age_seconds:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        decay_window = config.stale_age_seconds - config.fresh_age_seconds
        if age_seconds >= config.stale_age_seconds:
            return ZERO
        return ((config.stale_age_seconds - age_seconds) / decay_window).quantize(QUANT)


def _report_status(rows: tuple[ResearchSourceConfidenceMemoryBridgeRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason.endswith("_watch") for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceConfidenceMemoryBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    reason_mappings = (
        (
            REPORT_FRESHNESS_GAP_REASON,
            (FRESHNESS_BLOCK_REASON, FRESHNESS_WATCH_REASON),
        ),
        (
            REPORT_AUTHORITY_GAP_REASON,
            (AUTHORITY_BLOCK_REASON, AUTHORITY_WATCH_REASON),
        ),
        (
            REPORT_CORROBORATION_GAP_REASON,
            (CORROBORATION_BLOCK_REASON, CORROBORATION_WATCH_REASON),
        ),
        (
            REPORT_CONTRADICTION_GAP_REASON,
            (CONTRADICTION_BLOCK_REASON, CONTRADICTION_WATCH_REASON),
        ),
        (
            REPORT_CALIBRATION_EVIDENCE_GAP_REASON,
            (CALIBRATION_EVIDENCE_BLOCK_REASON, CALIBRATION_EVIDENCE_WATCH_REASON),
        ),
        (
            REPORT_UNRESOLVED_CAVEATS_REASON,
            (UNRESOLVED_CAVEATS_BLOCK_REASON, UNRESOLVED_CAVEATS_WATCH_REASON),
        ),
        (
            REPORT_BRIDGE_CONFIDENCE_GAP_REASON,
            (BRIDGE_CONFIDENCE_BLOCK_REASON, BRIDGE_CONFIDENCE_WATCH_REASON),
        ),
    )
    for report_reason, row_reasons in reason_mappings:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            reason_codes.append(report_reason)
    if not reason_codes:
        reason_codes.append(REPORT_CLEAR_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODES,
    )


def _row_sort_key(
    row: ResearchSourceConfidenceMemoryBridgeRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -row.triage_pressure_score,
        row.bridge_confidence_score,
        row.triage_group,
        row.evidence_family_label,
        row.specialist_label,
    )


def _status_count(
    rows: tuple[ResearchSourceConfidenceMemoryBridgeRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceConfidenceMemoryBridgeRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANT)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("observed_at", observed_at)
    delta = generated_at_utc - observed_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds).quantize(QUANT)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be in the future")
    return seconds.quantize(QUANT)


def _validate_config(config: ResearchSourceConfidenceMemoryBridgeConfig) -> None:
    if config.fresh_age_seconds >= config.stale_age_seconds:
        raise ValueError("fresh_age_seconds must be less than stale_age_seconds")
    if config.min_watch_freshness_score > config.min_pass_freshness_score:
        raise ValueError("min_watch_freshness_score must not exceed pass")
    if config.min_watch_authority_score > config.min_pass_authority_score:
        raise ValueError("min_watch_authority_score must not exceed pass")
    if config.min_watch_corroboration_score > config.min_pass_corroboration_score:
        raise ValueError("min_watch_corroboration_score must not exceed pass")
    if config.max_pass_contradiction_score > config.max_watch_contradiction_score:
        raise ValueError("max_pass_contradiction_score must not exceed watch")
    if (
        config.min_watch_calibration_evidence_score
        > config.min_pass_calibration_evidence_score
    ):
        raise ValueError("min_watch_calibration_evidence_score must not exceed pass")
    if config.max_pass_unresolved_caveat_score > config.max_watch_unresolved_caveat_score:
        raise ValueError("max_pass_unresolved_caveat_score must not exceed watch")
    if config.min_watch_bridge_confidence_score > config.min_pass_bridge_confidence_score:
        raise ValueError("min_watch_bridge_confidence_score must not exceed pass")


def _validate_row(row: ResearchSourceConfidenceMemoryBridgeRow) -> None:
    expected_source_confidence = _source_confidence_score(
        freshness_score=row.freshness_score,
        authority_score=row.authority_score,
        corroboration_score=row.corroboration_score,
        contradiction_score=row.contradiction_score,
    )
    if row.source_confidence_score != expected_source_confidence:
        raise ValueError("source_confidence_score must match row components")
    expected_memory_confidence = _memory_confidence_score(
        specialist_memory_confidence_score=row.specialist_memory_confidence_score,
        calibration_evidence_score=row.calibration_evidence_score,
        unresolved_caveat_score=row.unresolved_caveat_score,
    )
    if row.memory_confidence_score != expected_memory_confidence:
        raise ValueError("memory_confidence_score must match row components")
    if row.bridge_confidence_score != _average(
        (row.source_confidence_score, row.memory_confidence_score),
    ):
        raise ValueError("bridge_confidence_score must match row components")
    expected_pressure = _triage_pressure_score(
        bridge_confidence_score=row.bridge_confidence_score,
        corroboration_score=row.corroboration_score,
        contradiction_score=row.contradiction_score,
        calibration_evidence_score=row.calibration_evidence_score,
        unresolved_caveat_score=row.unresolved_caveat_score,
    )
    if row.triage_pressure_score != expected_pressure:
        raise ValueError("triage_pressure_score must match row components")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must carry only the clear reason")


def _validate_report(report: ResearchSourceConfidenceMemoryBridgeReport) -> None:
    rows = report.rows
    if report.observation_count != _count_decimal(len(rows)):
        raise ValueError("observation_count must match rows")
    for status, field_name in (
        (STATUS_PASS, "pass_count"),
        (STATUS_WATCH, "watch_count"),
        (STATUS_BLOCK, "block_count"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "freshness_gap_count",
            (FRESHNESS_BLOCK_REASON, FRESHNESS_WATCH_REASON),
        ),
        (
            "authority_gap_count",
            (AUTHORITY_BLOCK_REASON, AUTHORITY_WATCH_REASON),
        ),
        (
            "corroboration_gap_count",
            (CORROBORATION_BLOCK_REASON, CORROBORATION_WATCH_REASON),
        ),
        (
            "contradiction_gap_count",
            (CONTRADICTION_BLOCK_REASON, CONTRADICTION_WATCH_REASON),
        ),
        (
            "calibration_evidence_gap_count",
            (CALIBRATION_EVIDENCE_BLOCK_REASON, CALIBRATION_EVIDENCE_WATCH_REASON),
        ),
        (
            "unresolved_caveat_gap_count",
            (UNRESOLVED_CAVEATS_BLOCK_REASON, UNRESOLVED_CAVEATS_WATCH_REASON),
        ),
        (
            "bridge_confidence_gap_count",
            (BRIDGE_CONFIDENCE_BLOCK_REASON, BRIDGE_CONFIDENCE_WATCH_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    aggregate_fields = (
        ("average_source_confidence_score", _average(tuple(row.source_confidence_score for row in rows))),
        ("average_memory_confidence_score", _average(tuple(row.memory_confidence_score for row in rows))),
        ("average_bridge_confidence_score", _average(tuple(row.bridge_confidence_score for row in rows))),
        (
            "lowest_bridge_confidence_score",
            min((row.bridge_confidence_score for row in rows), default=ZERO).quantize(QUANT),
        ),
        (
            "highest_triage_pressure_score",
            max((row.triage_pressure_score for row in rows), default=ZERO).quantize(QUANT),
        ),
        (
            "highest_contradiction_score",
            max((row.contradiction_score for row in rows), default=ZERO).quantize(QUANT),
        ),
        (
            "highest_unresolved_caveat_score",
            max((row.unresolved_caveat_score for row in rows), default=ZERO).quantize(QUANT),
        ),
        (
            "oldest_observation_age_seconds",
            max((row.observation_age_seconds for row in rows), default=ZERO).quantize(QUANT),
        ),
    )
    for field_name, expected_value in aggregate_fields:
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic triage pressure sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceConfidenceMemoryBridgeRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, datetime]] = set()
    for row in rows:
        if type(row) is not ResearchSourceConfidenceMemoryBridgeRow:
            raise ValueError("rows must contain ResearchSourceConfidenceMemoryBridgeRow")
        _require_hard_flags("row", row)
        key = (row.triage_group, row.evidence_family_label, row.specialist_label, row.observed_at)
        if key in seen:
            raise ValueError("rows must be unique by public triage labels")
        seen.add(key)
    return tuple(sorted(rows, key=_row_sort_key))


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_status(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be nonempty stripped text")
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    deterministic = tuple(reason for reason in allowed if reason in reason_codes)
    if deterministic != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return deterministic


def _report_digest_from_public_payload(
    report: ResearchSourceConfidenceMemoryBridgeReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived_validation_digest payload", values)
    canonical = json.dumps(
        _json_ready(values),
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
    if type(value) is int or type(value) is float:
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


def _reject_raw_payload_numbers(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_raw_payload_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_raw_payload_numbers(item)
        return
    if type(value) is int or type(value) is float or type(value) is Decimal:
        raise ValueError("public payload numeric values must be Decimal strings")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
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
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{path} contains unsafe text")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or SHA256_HEX_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_STATUSES",
    "ResearchSourceConfidenceMemoryBridgeConfig",
    "ResearchSourceConfidenceMemoryBridgeObservation",
    "ResearchSourceConfidenceMemoryBridgeReport",
    "ResearchSourceConfidenceMemoryBridgeRow",
    "build_research_source_confidence_memory_bridge_report",
    "research_source_confidence_memory_bridge_report_digest",
    "research_source_confidence_memory_bridge_report_payload",
    "validate_research_source_confidence_memory_bridge_report_digest",
)
