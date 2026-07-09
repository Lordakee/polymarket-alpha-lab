"""Pure in-memory source authority usefulness decay alert report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_REPORT_CONFIG_VERSION = (
    "research-source-authority-decay-alert-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_decay_alert_empty"
HEALTHY_REASON = "source_authority_usefulness_healthy"
STALE_PUBLICATION_WATCH_REASON = "stale_publication_age_watch"
STALE_PUBLICATION_BLOCK_REASON = "stale_publication_age_block"
MISSING_CORROBORATION_WATCH_REASON = "missing_corroboration_watch"
MISSING_CORROBORATION_BLOCK_REASON = "missing_corroboration_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
EXTRACTION_UNCERTAINTY_WATCH_REASON = "extraction_uncertainty_watch"
EXTRACTION_UNCERTAINTY_BLOCK_REASON = "extraction_uncertainty_block"
RESOLUTION_WINDOW_WATCH_REASON = "resolution_window_watch"
RESOLUTION_WINDOW_BLOCK_REASON = "resolution_window_block"

ROW_REASON_CODES = (
    HEALTHY_REASON,
    STALE_PUBLICATION_BLOCK_REASON,
    MISSING_CORROBORATION_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    EXTRACTION_UNCERTAINTY_BLOCK_REASON,
    RESOLUTION_WINDOW_BLOCK_REASON,
    STALE_PUBLICATION_WATCH_REASON,
    MISSING_CORROBORATION_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    EXTRACTION_UNCERTAINTY_WATCH_REASON,
    RESOLUTION_WINDOW_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, HEALTHY_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "://",
    "http",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityDecayAlertConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_REPORT_CONFIG_VERSION
    stale_publication_watch_age_seconds: Decimal = Decimal("3600.000000")
    stale_publication_block_age_seconds: Decimal = Decimal("7200.000000")
    corroboration_pass_count: Decimal = Decimal("3.000000")
    corroboration_block_count: Decimal = Decimal("0.000000")
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
        if cls is not ResearchSourceAuthorityDecayAlertConfig:
            raise TypeError(
                "ResearchSourceAuthorityDecayAlertConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityDecayAlertConfig:
            raise ValueError("config must be exactly ResearchSourceAuthorityDecayAlertConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_publication_watch_age_seconds",
            "stale_publication_block_age_seconds",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("corroboration_pass_count", "corroboration_block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
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
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityDecayAlertInput:
    source_family: str
    source_authority_score: Decimal
    publication_age_seconds: Decimal
    corroboration_count: Decimal
    contradiction_pressure_score: Decimal
    extraction_uncertainty_score: Decimal
    resolution_window_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityDecayAlertInput:
            raise TypeError(
                "ResearchSourceAuthorityDecayAlertInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityDecayAlertInput:
            raise ValueError("input must be exactly ResearchSourceAuthorityDecayAlertInput")
        object.__setattr__(
            self,
            "source_family",
            _require_public_label("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "source_authority_score",
            _require_ratio("source_authority_score", self.source_authority_score),
        )
        for field_name in ("publication_age_seconds", "resolution_window_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_count("corroboration_count", self.corroboration_count),
        )
        for field_name in (
            "contradiction_pressure_score",
            "extraction_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityDecayAlertRow:
    source_family: str
    source_authority_score: Decimal
    publication_age_seconds: Decimal
    publication_age_band: str
    corroboration_count: Decimal
    corroboration_band: str
    contradiction_pressure_score: Decimal
    extraction_uncertainty_score: Decimal
    resolution_window_seconds: Decimal
    resolution_window_band: str
    authority_usefulness_score: Decimal
    authority_decay_alert_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityDecayAlertRow:
            raise TypeError(
                "ResearchSourceAuthorityDecayAlertRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityDecayAlertRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityDecayAlertRow")
        object.__setattr__(
            self,
            "source_family",
            _require_public_label("source_family", self.source_family),
        )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure_score",
            "extraction_uncertainty_score",
            "authority_usefulness_score",
            "authority_decay_alert_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("publication_age_seconds", "resolution_window_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_count("corroboration_count", self.corroboration_count),
        )
        _require_publication_age_band("publication_age_band", self.publication_age_band)
        _require_corroboration_band("corroboration_band", self.corroboration_band)
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
class ResearchSourceAuthorityDecayAlertReport:
    generated_at: datetime
    config_version: str
    source_family_count: Decimal
    pass_source_family_count: Decimal
    watch_source_family_count: Decimal
    block_source_family_count: Decimal
    stale_publication_source_count: Decimal
    missing_corroboration_source_count: Decimal
    contradiction_pressure_source_count: Decimal
    extraction_uncertainty_source_count: Decimal
    resolution_window_source_count: Decimal
    lowest_authority_usefulness_score: Decimal
    highest_authority_decay_alert_score: Decimal
    oldest_publication_age_seconds: Decimal
    nearest_resolution_window_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityDecayAlertRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityDecayAlertReport:
            raise TypeError(
                "ResearchSourceAuthorityDecayAlertReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityDecayAlertReport:
            raise ValueError("report must be exactly ResearchSourceAuthorityDecayAlertReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_family_count",
            "pass_source_family_count",
            "watch_source_family_count",
            "block_source_family_count",
            "stale_publication_source_count",
            "missing_corroboration_source_count",
            "contradiction_pressure_source_count",
            "extraction_uncertainty_source_count",
            "resolution_window_source_count",
            "oldest_publication_age_seconds",
            "nearest_resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_authority_usefulness_score",
            "highest_authority_decay_alert_score",
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
        return research_source_authority_decay_alert_report_payload(self)


def build_research_source_authority_decay_alert_report(
    inputs: list[ResearchSourceAuthorityDecayAlertInput]
    | tuple[ResearchSourceAuthorityDecayAlertInput, ...],
    *,
    config: ResearchSourceAuthorityDecayAlertConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceAuthorityDecayAlertReport:
    if config is None:
        config = ResearchSourceAuthorityDecayAlertConfig()
    if type(config) is not ResearchSourceAuthorityDecayAlertConfig:
        raise ValueError("config must be a ResearchSourceAuthorityDecayAlertConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _decay_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityDecayAlertReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_family_count=_count(len(rows)),
        pass_source_family_count=_status_count(rows, "pass"),
        watch_source_family_count=_status_count(rows, "watch"),
        block_source_family_count=_status_count(rows, "block"),
        stale_publication_source_count=_reason_count(
            rows,
            (STALE_PUBLICATION_WATCH_REASON, STALE_PUBLICATION_BLOCK_REASON),
        ),
        missing_corroboration_source_count=_reason_count(
            rows,
            (MISSING_CORROBORATION_WATCH_REASON, MISSING_CORROBORATION_BLOCK_REASON),
        ),
        contradiction_pressure_source_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        extraction_uncertainty_source_count=_reason_count(
            rows,
            (EXTRACTION_UNCERTAINTY_WATCH_REASON, EXTRACTION_UNCERTAINTY_BLOCK_REASON),
        ),
        resolution_window_source_count=_reason_count(
            rows,
            (RESOLUTION_WINDOW_WATCH_REASON, RESOLUTION_WINDOW_BLOCK_REASON),
        ),
        lowest_authority_usefulness_score=min(
            (row.authority_usefulness_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_authority_decay_alert_score=max(
            (row.authority_decay_alert_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_publication_age_seconds=max(
            (row.publication_age_seconds for row in rows),
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


def research_source_authority_decay_alert_report_payload(
    report: ResearchSourceAuthorityDecayAlertReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceAuthorityDecayAlertReport:
        validate_research_source_authority_decay_alert_report_digest(report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_source_authority_decay_alert_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_research_source_authority_decay_alert_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_source_authority_decay_alert_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchSourceAuthorityDecayAlertReport")


def research_source_authority_decay_alert_report_digest(
    report: ResearchSourceAuthorityDecayAlertReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityDecayAlertReport:
        raise ValueError("report must be a ResearchSourceAuthorityDecayAlertReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_decay_alert_report_digest(
    report: ResearchSourceAuthorityDecayAlertReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityDecayAlertReport:
        raise ValueError("report must be a ResearchSourceAuthorityDecayAlertReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def validate_research_source_authority_decay_alert_public_payload(
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
) -> tuple[ResearchSourceAuthorityDecayAlertInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityDecayAlertInput:
            raise ValueError("inputs must contain ResearchSourceAuthorityDecayAlertInput")
        _require_hard_flags("input", row)
        if row.source_family in seen:
            raise ValueError("inputs must be unique by source_family")
        seen.add(row.source_family)
    return tuple(sorted(rows, key=lambda row: row.source_family))


def _decay_rows(
    inputs: tuple[ResearchSourceAuthorityDecayAlertInput, ...],
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> tuple[ResearchSourceAuthorityDecayAlertRow, ...]:
    return tuple(sorted((_decay_row(row, config=config) for row in inputs), key=_row_sort_key))


def _decay_row(
    row: ResearchSourceAuthorityDecayAlertInput,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> ResearchSourceAuthorityDecayAlertRow:
    reason_codes = _row_reason_codes(row, config=config)
    authority_usefulness_score = _authority_usefulness_score(row, config=config)
    return ResearchSourceAuthorityDecayAlertRow(
        source_family=row.source_family,
        source_authority_score=row.source_authority_score,
        publication_age_seconds=row.publication_age_seconds,
        publication_age_band=_publication_age_band(row.publication_age_seconds, config=config),
        corroboration_count=row.corroboration_count,
        corroboration_band=_corroboration_band(row.corroboration_count, config=config),
        contradiction_pressure_score=row.contradiction_pressure_score,
        extraction_uncertainty_score=row.extraction_uncertainty_score,
        resolution_window_seconds=row.resolution_window_seconds,
        resolution_window_band=_resolution_window_band(
            row.resolution_window_seconds,
            config=config,
        ),
        authority_usefulness_score=authority_usefulness_score,
        authority_decay_alert_score=(ONE - authority_usefulness_score).quantize(QUANT),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityDecayAlertInput,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.publication_age_seconds >= config.stale_publication_block_age_seconds:
        reasons.append(STALE_PUBLICATION_BLOCK_REASON)
    elif row.publication_age_seconds > config.stale_publication_watch_age_seconds:
        reasons.append(STALE_PUBLICATION_WATCH_REASON)
    if row.corroboration_count <= config.corroboration_block_count:
        reasons.append(MISSING_CORROBORATION_BLOCK_REASON)
    elif row.corroboration_count < config.corroboration_pass_count:
        reasons.append(MISSING_CORROBORATION_WATCH_REASON)
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
        reasons.append(HEALTHY_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _authority_usefulness_score(
    row: ResearchSourceAuthorityDecayAlertInput,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_health = (
            _publication_age_score(row.publication_age_seconds, config=config)
            * Decimal("0.250000")
            + _corroboration_score(row.corroboration_count, config=config)
            * Decimal("0.250000")
            + (ONE - row.contradiction_pressure_score) * Decimal("0.200000")
            + (ONE - row.extraction_uncertainty_score) * Decimal("0.200000")
            + _resolution_window_score(row.resolution_window_seconds, config=config)
            * Decimal("0.100000")
        )
        return min(row.source_authority_score * weighted_health, ONE).quantize(QUANT)


def _publication_age_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_fraction = min(value / config.stale_publication_block_age_seconds, ONE)
        return (ONE - age_fraction).quantize(QUANT)


def _corroboration_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / config.corroboration_pass_count, ONE).quantize(QUANT)


def _resolution_window_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / config.resolution_watch_seconds_remaining, ONE).quantize(QUANT)


def _publication_age_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> str:
    if value <= config.stale_publication_watch_age_seconds:
        return "fresh"
    if value < config.stale_publication_block_age_seconds:
        return "stale"
    return "expired"


def _corroboration_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> str:
    if value <= config.corroboration_block_count:
        return "missing"
    if value < config.corroboration_pass_count:
        return "thin"
    return "corroborated"


def _resolution_window_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityDecayAlertConfig,
) -> str:
    if value <= config.resolution_block_seconds_remaining:
        return "immediate"
    if value < config.resolution_watch_seconds_remaining:
        return "near"
    return "open"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (HEALTHY_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceAuthorityDecayAlertRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityDecayAlertRow, ...],
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
    return (HEALTHY_REASON,)


def _row_sort_key(row: ResearchSourceAuthorityDecayAlertRow) -> tuple[Decimal, str]:
    return (-row.authority_decay_alert_score, row.source_family)


def _status_count(rows: tuple[ResearchSourceAuthorityDecayAlertRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityDecayAlertRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceAuthorityDecayAlertConfig) -> None:
    if (
        config.stale_publication_watch_age_seconds
        >= config.stale_publication_block_age_seconds
    ):
        raise ValueError(
            "stale_publication_watch_age_seconds must be less than "
            "stale_publication_block_age_seconds",
        )
    if config.corroboration_block_count >= config.corroboration_pass_count:
        raise ValueError("corroboration_block_count must be below corroboration_pass_count")
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


def _validate_row(row: ResearchSourceAuthorityDecayAlertRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (HEALTHY_REASON,):
        raise ValueError("pass rows must be healthy")
    if row.authority_decay_alert_score != (ONE - row.authority_usefulness_score).quantize(QUANT):
        raise ValueError("authority_decay_alert_score must match authority_usefulness_score")


def _validate_report(report: ResearchSourceAuthorityDecayAlertReport) -> None:
    if report.source_family_count != _count(len(report.rows)):
        raise ValueError("source_family_count must match rows")
    for status, field_name in (
        ("pass", "pass_source_family_count"),
        ("watch", "watch_source_family_count"),
        ("block", "block_source_family_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "stale_publication_source_count",
            (STALE_PUBLICATION_WATCH_REASON, STALE_PUBLICATION_BLOCK_REASON),
        ),
        (
            "missing_corroboration_source_count",
            (MISSING_CORROBORATION_WATCH_REASON, MISSING_CORROBORATION_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_source_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        (
            "extraction_uncertainty_source_count",
            (EXTRACTION_UNCERTAINTY_WATCH_REASON, EXTRACTION_UNCERTAINTY_BLOCK_REASON),
        ),
        (
            "resolution_window_source_count",
            (RESOLUTION_WINDOW_WATCH_REASON, RESOLUTION_WINDOW_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.lowest_authority_usefulness_score != min(
        (row.authority_usefulness_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_authority_usefulness_score must match rows")
    if report.highest_authority_decay_alert_score != max(
        (row.authority_decay_alert_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_authority_decay_alert_score must match rows")
    if report.oldest_publication_age_seconds != max(
        (row.publication_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_publication_age_seconds must match rows")
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
        raise ValueError("rows must use deterministic authority decay alert sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityDecayAlertRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityDecayAlertRow:
            raise ValueError("rows must contain ResearchSourceAuthorityDecayAlertRow")
        _require_hard_flags("row", row)
        if row.source_family in seen:
            raise ValueError("rows must be unique by source_family")
        seen.add(row.source_family)
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
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
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
    if type(value) is not str or value not in RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_publication_age_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "stale", "expired"):
        raise ValueError(f"{field_name} must be fresh, stale, or expired")


def _require_corroboration_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("corroborated", "thin", "missing"):
        raise ValueError(f"{field_name} must be corroborated, thin, or missing")


def _require_resolution_window_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("open", "near", "immediate"):
        raise ValueError(f"{field_name} must be open, near, or immediate")


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
        raise ValueError(f"{field_name} must be a public family label")
    return value


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
        raise ValueError(f"{field_name} must be a SHA-256 digest")
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
    report: ResearchSourceAuthorityDecayAlertReport,
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
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
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
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_DECAY_ALERT_STATUSES",
    "ResearchSourceAuthorityDecayAlertConfig",
    "ResearchSourceAuthorityDecayAlertInput",
    "ResearchSourceAuthorityDecayAlertReport",
    "ResearchSourceAuthorityDecayAlertRow",
    "build_research_source_authority_decay_alert_report",
    "research_source_authority_decay_alert_report_digest",
    "research_source_authority_decay_alert_report_payload",
    "validate_research_source_authority_decay_alert_public_payload",
    "validate_research_source_authority_decay_alert_report_digest",
)
