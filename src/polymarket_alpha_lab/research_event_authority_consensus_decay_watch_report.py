"""Report-only event authority consensus decay watch reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_REPORT_CONFIG_VERSION = (
    "research-event-authority-consensus-decay-watch-report-v0"
)
RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_event_authority_consensus_decay_watch_empty"
CLEAR_REASON = "event_authority_consensus_decay_clear"
AUTHORITY_SIGNAL_WATCH_REASON = "authority_signal_count_watch"
AUTHORITY_SIGNAL_BLOCK_REASON = "authority_signal_count_block"
AUTHORITY_FAMILY_WATCH_REASON = "authority_family_diversity_watch"
AUTHORITY_FAMILY_BLOCK_REASON = "authority_family_diversity_block"
CONSENSUS_AGREEMENT_WATCH_REASON = "consensus_agreement_low_watch"
CONSENSUS_AGREEMENT_BLOCK_REASON = "consensus_agreement_low_block"
AUTHORITY_UPDATE_WATCH_REASON = "authority_update_age_watch"
AUTHORITY_UPDATE_BLOCK_REASON = "authority_update_age_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
EXTRACTION_UNCERTAINTY_WATCH_REASON = "extraction_uncertainty_watch"
EXTRACTION_UNCERTAINTY_BLOCK_REASON = "extraction_uncertainty_block"
RESOLUTION_WINDOW_WATCH_REASON = "resolution_window_watch"
RESOLUTION_WINDOW_BLOCK_REASON = "resolution_window_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    AUTHORITY_SIGNAL_BLOCK_REASON,
    AUTHORITY_FAMILY_BLOCK_REASON,
    CONSENSUS_AGREEMENT_BLOCK_REASON,
    AUTHORITY_UPDATE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    EXTRACTION_UNCERTAINTY_BLOCK_REASON,
    RESOLUTION_WINDOW_BLOCK_REASON,
    AUTHORITY_SIGNAL_WATCH_REASON,
    AUTHORITY_FAMILY_WATCH_REASON,
    CONSENSUS_AGREEMENT_WATCH_REASON,
    AUTHORITY_UPDATE_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    EXTRACTION_UNCERTAINTY_WATCH_REASON,
    RESOLUTION_WINDOW_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64
AGREEMENT_DECAY_WEIGHT = Decimal("243.000000") / Decimal("1160.000000")
FRESHNESS_DECAY_WEIGHT = Decimal("819.000000") / Decimal("2900.000000")
WINDOW_DECAY_WEIGHT = Decimal("354.000000") / Decimal("725.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    _join_parts("que", "stion"),
    _join_parts("ur", "l"),
    _join_parts("te", "xt"),
    "dsn",
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    "://",
    "http",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "endation"),
)


@dataclass(frozen=True)
class ResearchEventAuthorityConsensusDecayWatchConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_REPORT_CONFIG_VERSION
    )
    authority_signal_pass_count: Decimal = Decimal("3.000000")
    authority_signal_watch_count: Decimal = Decimal("2.000000")
    authority_family_pass_count: Decimal = Decimal("2.000000")
    authority_family_watch_count: Decimal = Decimal("1.000000")
    consensus_agreement_watch_below: Decimal = Decimal("0.750000")
    consensus_agreement_block_below: Decimal = Decimal("0.500000")
    authority_update_watch_age_seconds: Decimal = Decimal("3600.000000")
    authority_update_block_age_seconds: Decimal = Decimal("7200.000000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.600000")
    extraction_uncertainty_watch_threshold: Decimal = Decimal("0.250000")
    extraction_uncertainty_block_threshold: Decimal = Decimal("0.500000")
    resolution_watch_seconds_remaining: Decimal = Decimal("1800.000000")
    resolution_block_seconds_remaining: Decimal = Decimal("600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityConsensusDecayWatchConfig:
            raise TypeError(
                "ResearchEventAuthorityConsensusDecayWatchConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityConsensusDecayWatchConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventAuthorityConsensusDecayWatchConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_signal_pass_count",
            "authority_signal_watch_count",
            "authority_family_pass_count",
            "authority_family_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "consensus_agreement_watch_below",
            "consensus_agreement_block_below",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "extraction_uncertainty_watch_threshold",
            "extraction_uncertainty_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_update_watch_age_seconds",
            "authority_update_block_age_seconds",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventAuthorityConsensusDecayWatchInput:
    event_digest: str
    consensus_digest: str
    authority_signal_count: Decimal
    authority_family_count: Decimal
    consensus_agreement_score: Decimal
    newest_authority_update_age_seconds: Decimal
    oldest_authority_update_age_seconds: Decimal
    contradiction_pressure_score: Decimal
    extraction_uncertainty_score: Decimal
    resolution_window_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityConsensusDecayWatchInput:
            raise TypeError(
                "ResearchEventAuthorityConsensusDecayWatchInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityConsensusDecayWatchInput:
            raise ValueError(
                "input must be exactly ResearchEventAuthorityConsensusDecayWatchInput",
            )
        _require_sha256("event_digest", self.event_digest)
        _require_sha256("consensus_digest", self.consensus_digest)
        for field_name in ("authority_signal_count", "authority_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "consensus_agreement_score",
            "contradiction_pressure_score",
            "extraction_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_authority_update_age_seconds",
            "oldest_authority_update_age_seconds",
            "resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.oldest_authority_update_age_seconds
            < self.newest_authority_update_age_seconds
        ):
            raise ValueError(
                "oldest_authority_update_age_seconds must be greater than or equal "
                "to newest_authority_update_age_seconds",
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventAuthorityConsensusDecayWatchRow:
    event_digest: str
    consensus_digest: str
    authority_signal_count: Decimal
    authority_signal_band: str
    authority_family_count: Decimal
    authority_family_band: str
    consensus_agreement_score: Decimal
    consensus_agreement_band: str
    newest_authority_update_age_seconds: Decimal
    oldest_authority_update_age_seconds: Decimal
    authority_freshness_band: str
    contradiction_pressure_score: Decimal
    extraction_uncertainty_score: Decimal
    resolution_window_seconds: Decimal
    resolution_window_band: str
    consensus_health_score: Decimal
    consensus_decay_watch_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityConsensusDecayWatchRow:
            raise TypeError(
                "ResearchEventAuthorityConsensusDecayWatchRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityConsensusDecayWatchRow:
            raise ValueError(
                "row must be exactly ResearchEventAuthorityConsensusDecayWatchRow",
            )
        _require_sha256("event_digest", self.event_digest)
        _require_sha256("consensus_digest", self.consensus_digest)
        for field_name in ("authority_signal_count", "authority_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "consensus_agreement_score",
            "contradiction_pressure_score",
            "extraction_uncertainty_score",
            "consensus_health_score",
            "consensus_decay_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_authority_update_age_seconds",
            "oldest_authority_update_age_seconds",
            "resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.oldest_authority_update_age_seconds
            < self.newest_authority_update_age_seconds
        ):
            raise ValueError(
                "oldest_authority_update_age_seconds must be greater than or equal "
                "to newest_authority_update_age_seconds",
            )
        _require_authority_signal_band("authority_signal_band", self.authority_signal_band)
        _require_authority_family_band("authority_family_band", self.authority_family_band)
        _require_consensus_agreement_band(
            "consensus_agreement_band",
            self.consensus_agreement_band,
        )
        _require_authority_freshness_band(
            "authority_freshness_band",
            self.authority_freshness_band,
        )
        _require_resolution_window_band("resolution_window_band", self.resolution_window_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventAuthorityConsensusDecayWatchReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    block_event_count: Decimal
    low_authority_signal_event_count: Decimal
    thin_authority_family_event_count: Decimal
    low_consensus_agreement_event_count: Decimal
    stale_authority_update_event_count: Decimal
    contradiction_pressure_event_count: Decimal
    extraction_uncertainty_event_count: Decimal
    resolution_window_event_count: Decimal
    lowest_consensus_health_score: Decimal
    highest_consensus_decay_watch_score: Decimal
    oldest_authority_update_age_seconds: Decimal
    nearest_resolution_window_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityConsensusDecayWatchReport:
            raise TypeError(
                "ResearchEventAuthorityConsensusDecayWatchReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityConsensusDecayWatchReport:
            raise ValueError(
                "report must be exactly ResearchEventAuthorityConsensusDecayWatchReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "block_event_count",
            "low_authority_signal_event_count",
            "thin_authority_family_event_count",
            "low_consensus_agreement_event_count",
            "stale_authority_update_event_count",
            "contradiction_pressure_event_count",
            "extraction_uncertainty_event_count",
            "resolution_window_event_count",
            "oldest_authority_update_age_seconds",
            "nearest_resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_consensus_health_score",
            "highest_consensus_decay_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_public_payload(self),
            )
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_public_payload(self):
                raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_authority_consensus_decay_watch_report_payload(self)


def build_research_event_authority_consensus_decay_watch_report(
    inputs: list[ResearchEventAuthorityConsensusDecayWatchInput]
    | tuple[ResearchEventAuthorityConsensusDecayWatchInput, ...],
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig | None = None,
    generated_at: datetime,
) -> ResearchEventAuthorityConsensusDecayWatchReport:
    if config is None:
        config = ResearchEventAuthorityConsensusDecayWatchConfig()
    if type(config) is not ResearchEventAuthorityConsensusDecayWatchConfig:
        raise ValueError(
            "config must be a ResearchEventAuthorityConsensusDecayWatchConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _watch_rows(_normalize_inputs(inputs), config=config)
    return ResearchEventAuthorityConsensusDecayWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_event_count=_status_count(rows, "pass"),
        watch_event_count=_status_count(rows, "watch"),
        block_event_count=_status_count(rows, "block"),
        low_authority_signal_event_count=_reason_count(
            rows,
            (AUTHORITY_SIGNAL_WATCH_REASON, AUTHORITY_SIGNAL_BLOCK_REASON),
        ),
        thin_authority_family_event_count=_reason_count(
            rows,
            (AUTHORITY_FAMILY_WATCH_REASON, AUTHORITY_FAMILY_BLOCK_REASON),
        ),
        low_consensus_agreement_event_count=_reason_count(
            rows,
            (CONSENSUS_AGREEMENT_WATCH_REASON, CONSENSUS_AGREEMENT_BLOCK_REASON),
        ),
        stale_authority_update_event_count=_reason_count(
            rows,
            (AUTHORITY_UPDATE_WATCH_REASON, AUTHORITY_UPDATE_BLOCK_REASON),
        ),
        contradiction_pressure_event_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        extraction_uncertainty_event_count=_reason_count(
            rows,
            (EXTRACTION_UNCERTAINTY_WATCH_REASON, EXTRACTION_UNCERTAINTY_BLOCK_REASON),
        ),
        resolution_window_event_count=_reason_count(
            rows,
            (RESOLUTION_WINDOW_WATCH_REASON, RESOLUTION_WINDOW_BLOCK_REASON),
        ),
        lowest_consensus_health_score=min(
            (row.consensus_health_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_consensus_decay_watch_score=max(
            (row.consensus_decay_watch_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_authority_update_age_seconds=max(
            (row.oldest_authority_update_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        nearest_resolution_window_seconds=min(
            (row.resolution_window_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_authority_consensus_decay_watch_report_payload(
    report: ResearchEventAuthorityConsensusDecayWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventAuthorityConsensusDecayWatchReport:
        validate_research_event_authority_consensus_decay_watch_report_digest(report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_event_authority_consensus_decay_watch_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_research_event_authority_consensus_decay_watch_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_event_authority_consensus_decay_watch_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchEventAuthorityConsensusDecayWatchReport")


def research_event_authority_consensus_decay_watch_report_digest(
    report: ResearchEventAuthorityConsensusDecayWatchReport,
) -> str:
    if type(report) is not ResearchEventAuthorityConsensusDecayWatchReport:
        raise ValueError("report must be a ResearchEventAuthorityConsensusDecayWatchReport")
    return _report_digest_from_public_payload(report)


def validate_research_event_authority_consensus_decay_watch_report_digest(
    report: ResearchEventAuthorityConsensusDecayWatchReport,
) -> None:
    if type(report) is not ResearchEventAuthorityConsensusDecayWatchReport:
        raise ValueError("report must be a ResearchEventAuthorityConsensusDecayWatchReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def validate_research_event_authority_consensus_decay_watch_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics("public payload", payload)
    _reject_flag_downgrades("public payload", payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _validate_status_values_in_payload(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _payload_validation_digest(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    value: object,
) -> tuple[ResearchEventAuthorityConsensusDecayWatchInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventAuthorityConsensusDecayWatchInput:
            raise ValueError(
                "inputs must contain ResearchEventAuthorityConsensusDecayWatchInput",
            )
        _require_hard_flags("input", row)
        if row.event_digest in seen:
            raise ValueError("inputs must be unique by event_digest")
        seen.add(row.event_digest)
    return tuple(sorted(rows, key=lambda row: row.event_digest))


def _watch_rows(
    inputs: tuple[ResearchEventAuthorityConsensusDecayWatchInput, ...],
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...]:
    return tuple(sorted((_watch_row(row, config=config) for row in inputs), key=_row_sort_key))


def _watch_row(
    row: ResearchEventAuthorityConsensusDecayWatchInput,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> ResearchEventAuthorityConsensusDecayWatchRow:
    reason_codes = _row_reason_codes(row, config=config)
    decay_score = _consensus_decay_watch_score(row, config=config)
    return ResearchEventAuthorityConsensusDecayWatchRow(
        event_digest=row.event_digest,
        consensus_digest=row.consensus_digest,
        authority_signal_count=row.authority_signal_count,
        authority_signal_band=_authority_signal_band(
            row.authority_signal_count,
            config=config,
        ),
        authority_family_count=row.authority_family_count,
        authority_family_band=_authority_family_band(
            row.authority_family_count,
            config=config,
        ),
        consensus_agreement_score=row.consensus_agreement_score,
        consensus_agreement_band=_consensus_agreement_band(
            row.consensus_agreement_score,
            config=config,
        ),
        newest_authority_update_age_seconds=row.newest_authority_update_age_seconds,
        oldest_authority_update_age_seconds=row.oldest_authority_update_age_seconds,
        authority_freshness_band=_authority_freshness_band(
            row.newest_authority_update_age_seconds,
            row.oldest_authority_update_age_seconds,
            config=config,
        ),
        contradiction_pressure_score=row.contradiction_pressure_score,
        extraction_uncertainty_score=row.extraction_uncertainty_score,
        resolution_window_seconds=row.resolution_window_seconds,
        resolution_window_band=_resolution_window_band(
            row.resolution_window_seconds,
            config=config,
        ),
        consensus_health_score=(ONE - decay_score).quantize(QUANT),
        consensus_decay_watch_score=decay_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchEventAuthorityConsensusDecayWatchInput,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.authority_signal_count < config.authority_signal_watch_count:
        reasons.append(AUTHORITY_SIGNAL_BLOCK_REASON)
    elif row.authority_signal_count < config.authority_signal_pass_count:
        reasons.append(AUTHORITY_SIGNAL_WATCH_REASON)
    if row.authority_family_count < config.authority_family_watch_count:
        reasons.append(AUTHORITY_FAMILY_BLOCK_REASON)
    elif row.authority_family_count < config.authority_family_pass_count:
        reasons.append(AUTHORITY_FAMILY_WATCH_REASON)
    if row.consensus_agreement_score < config.consensus_agreement_block_below:
        reasons.append(CONSENSUS_AGREEMENT_BLOCK_REASON)
    elif row.consensus_agreement_score < config.consensus_agreement_watch_below:
        reasons.append(CONSENSUS_AGREEMENT_WATCH_REASON)
    if row.newest_authority_update_age_seconds >= config.authority_update_block_age_seconds:
        reasons.append(AUTHORITY_UPDATE_BLOCK_REASON)
    elif row.oldest_authority_update_age_seconds > config.authority_update_watch_age_seconds:
        reasons.append(AUTHORITY_UPDATE_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.extraction_uncertainty_score >= config.extraction_uncertainty_block_threshold:
        reasons.append(EXTRACTION_UNCERTAINTY_BLOCK_REASON)
    elif row.extraction_uncertainty_score >= config.extraction_uncertainty_watch_threshold:
        reasons.append(EXTRACTION_UNCERTAINTY_WATCH_REASON)
    if row.resolution_window_seconds <= config.resolution_block_seconds_remaining:
        reasons.append(RESOLUTION_WINDOW_BLOCK_REASON)
    elif row.resolution_window_seconds < config.resolution_watch_seconds_remaining:
        reasons.append(RESOLUTION_WINDOW_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _consensus_decay_watch_score(
    row: ResearchEventAuthorityConsensusDecayWatchInput,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _agreement_decay(row.consensus_agreement_score) * AGREEMENT_DECAY_WEIGHT
            + _authority_freshness_decay(
                row.oldest_authority_update_age_seconds,
                config=config,
            )
            * FRESHNESS_DECAY_WEIGHT
            + _resolution_window_decay(row.resolution_window_seconds, config=config)
            * WINDOW_DECAY_WEIGHT
        )
        return min(score, ONE).quantize(QUANT)


def _agreement_decay(value: Decimal) -> Decimal:
    return (ONE - value).quantize(QUANT)


def _authority_freshness_decay(
    value: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / config.authority_update_block_age_seconds, ONE).quantize(QUANT)


def _resolution_window_decay(
    value: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value >= config.resolution_watch_seconds_remaining:
            return ZERO
        return (ONE - value / config.resolution_watch_seconds_remaining).quantize(QUANT)


def _authority_signal_band(
    value: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> str:
    if value < config.authority_signal_watch_count:
        return "missing"
    if value < config.authority_signal_pass_count:
        return "thin"
    return "sufficient"


def _authority_family_band(
    value: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> str:
    if value < config.authority_family_watch_count:
        return "single"
    if value < config.authority_family_pass_count:
        return "thin"
    return "diverse"


def _consensus_agreement_band(
    value: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> str:
    if value < config.consensus_agreement_block_below:
        return "fractured"
    if value < config.consensus_agreement_watch_below:
        return "weak"
    return "aligned"


def _authority_freshness_band(
    newest_age_seconds: Decimal,
    oldest_age_seconds: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> str:
    if newest_age_seconds >= config.authority_update_block_age_seconds:
        return "expired"
    if oldest_age_seconds > config.authority_update_watch_age_seconds:
        return "stale"
    return "fresh"


def _resolution_window_band(
    value: Decimal,
    *,
    config: ResearchEventAuthorityConsensusDecayWatchConfig,
) -> str:
    if value <= config.resolution_block_seconds_remaining:
        return "immediate"
    if value < config.resolution_watch_seconds_remaining:
        return "near"
    return "open"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _row_sort_key(
    row: ResearchEventAuthorityConsensusDecayWatchRow,
) -> tuple[Decimal, str]:
    return (-row.consensus_decay_watch_score, row.event_digest)


def _status_count(
    rows: tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchEventAuthorityConsensusDecayWatchConfig) -> None:
    if config.authority_signal_watch_count > config.authority_signal_pass_count:
        raise ValueError(
            "authority_signal_watch_count must not exceed authority_signal_pass_count",
        )
    if config.authority_family_watch_count > config.authority_family_pass_count:
        raise ValueError(
            "authority_family_watch_count must not exceed authority_family_pass_count",
        )
    if config.consensus_agreement_block_below > config.consensus_agreement_watch_below:
        raise ValueError(
            "consensus_agreement_block_below must not exceed "
            "consensus_agreement_watch_below",
        )
    if (
        config.authority_update_watch_age_seconds
        >= config.authority_update_block_age_seconds
    ):
        raise ValueError(
            "authority_update_watch_age_seconds must be less than "
            "authority_update_block_age_seconds",
        )
    if config.contradiction_watch_threshold > config.contradiction_block_threshold:
        raise ValueError(
            "contradiction_watch_threshold must not exceed contradiction_block_threshold",
        )
    if (
        config.extraction_uncertainty_watch_threshold
        > config.extraction_uncertainty_block_threshold
    ):
        raise ValueError(
            "extraction_uncertainty_watch_threshold must not exceed "
            "extraction_uncertainty_block_threshold",
        )
    if config.resolution_block_seconds_remaining >= config.resolution_watch_seconds_remaining:
        raise ValueError(
            "resolution_block_seconds_remaining must be below "
            "resolution_watch_seconds_remaining",
        )


def _validate_row(row: ResearchEventAuthorityConsensusDecayWatchRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must be clear")
    if row.consensus_decay_watch_score != (ONE - row.consensus_health_score).quantize(QUANT):
        raise ValueError("consensus_decay_watch_score must match consensus_health_score")


def _validate_report(report: ResearchEventAuthorityConsensusDecayWatchReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    for status, field_name in (
        ("pass", "pass_event_count"),
        ("watch", "watch_event_count"),
        ("block", "block_event_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_authority_signal_event_count",
            (AUTHORITY_SIGNAL_WATCH_REASON, AUTHORITY_SIGNAL_BLOCK_REASON),
        ),
        (
            "thin_authority_family_event_count",
            (AUTHORITY_FAMILY_WATCH_REASON, AUTHORITY_FAMILY_BLOCK_REASON),
        ),
        (
            "low_consensus_agreement_event_count",
            (CONSENSUS_AGREEMENT_WATCH_REASON, CONSENSUS_AGREEMENT_BLOCK_REASON),
        ),
        (
            "stale_authority_update_event_count",
            (AUTHORITY_UPDATE_WATCH_REASON, AUTHORITY_UPDATE_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_event_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        (
            "extraction_uncertainty_event_count",
            (EXTRACTION_UNCERTAINTY_WATCH_REASON, EXTRACTION_UNCERTAINTY_BLOCK_REASON),
        ),
        (
            "resolution_window_event_count",
            (RESOLUTION_WINDOW_WATCH_REASON, RESOLUTION_WINDOW_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.lowest_consensus_health_score != min(
        (row.consensus_health_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_consensus_health_score must match rows")
    if report.highest_consensus_decay_watch_score != max(
        (row.consensus_decay_watch_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_consensus_decay_watch_score must match rows")
    if report.oldest_authority_update_age_seconds != max(
        (row.oldest_authority_update_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_authority_update_age_seconds must match rows")
    if report.nearest_resolution_window_seconds != min(
        (row.resolution_window_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("nearest_resolution_window_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic consensus decay watch sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventAuthorityConsensusDecayWatchRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventAuthorityConsensusDecayWatchRow:
            raise ValueError(
                "rows must contain ResearchEventAuthorityConsensusDecayWatchRow",
            )
        _require_hard_flags("row", row)
        if row.event_digest in seen:
            raise ValueError("rows must be unique by event_digest")
        seen.add(row.event_digest)
    return tuple(sorted(rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


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
    if not value.same_quantum(QUANT):
        raise ValueError(f"{field_name} must use six decimal places")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


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
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_authority_signal_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("sufficient", "thin", "missing"):
        raise ValueError(f"{field_name} must be sufficient, thin, or missing")


def _require_authority_family_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("diverse", "thin", "single"):
        raise ValueError(f"{field_name} must be diverse, thin, or single")


def _require_consensus_agreement_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("aligned", "weak", "fractured"):
        raise ValueError(f"{field_name} must be aligned, weak, or fractured")


def _require_authority_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "stale", "expired"):
        raise ValueError(f"{field_name} must be fresh, stale, or expired")


def _require_resolution_window_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("open", "near", "immediate"):
        raise ValueError(f"{field_name} must be open, near, or immediate")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _report_digest_from_public_payload(
    report: ResearchEventAuthorityConsensusDecayWatchReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    return _payload_validation_digest(unsigned_payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        _require_nonnegative_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_public_numerics(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_numerics(label, asdict(value))
        return
    if isinstance(value, (Decimal, float)) or type(value) is int:
        raise ValueError(f"{label} numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numerics(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_flag_downgrades(label, asdict(value))
        return
    if isinstance(value, dict):
        for flag in ("paper_only", "report_only", "readonly"):
            if flag in value and value[flag] is not True:
                raise ValueError(f"{flag} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _validate_status_values_in_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_status_values_in_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_status_values_in_payload(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_AUTHORITY_CONSENSUS_DECAY_WATCH_STATUSES",
    "ResearchEventAuthorityConsensusDecayWatchConfig",
    "ResearchEventAuthorityConsensusDecayWatchInput",
    "ResearchEventAuthorityConsensusDecayWatchReport",
    "ResearchEventAuthorityConsensusDecayWatchRow",
    "build_research_event_authority_consensus_decay_watch_report",
    "research_event_authority_consensus_decay_watch_report_digest",
    "research_event_authority_consensus_decay_watch_report_payload",
    "validate_research_event_authority_consensus_decay_watch_public_payload",
    "validate_research_event_authority_consensus_decay_watch_report_digest",
)
