"""Pure report-only source authority claim latency decay report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_REPORT_CONFIG_VERSION = (
    "research-source-authority-claim-latency-decay-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_claim_latency_decay_empty"
HEALTHY_REASON = "authority_claim_latency_decay_healthy"
CLAIM_LATENCY_WATCH_REASON = "claim_latency_decay_watch"
CLAIM_LATENCY_BLOCK_REASON = "claim_latency_decay_block"
AUTHORITY_DECAY_WATCH_REASON = "authority_decay_watch"
AUTHORITY_DECAY_BLOCK_REASON = "authority_decay_block"
CORROBORATION_LAG_WATCH_REASON = "corroboration_lag_watch"
CORROBORATION_LAG_BLOCK_REASON = "corroboration_lag_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
RESOLUTION_PRESSURE_WATCH_REASON = "resolution_pressure_watch"
RESOLUTION_PRESSURE_BLOCK_REASON = "resolution_pressure_block"

ROW_REASON_CODES = (
    HEALTHY_REASON,
    CLAIM_LATENCY_BLOCK_REASON,
    AUTHORITY_DECAY_BLOCK_REASON,
    CORROBORATION_LAG_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    RESOLUTION_PRESSURE_BLOCK_REASON,
    CLAIM_LATENCY_WATCH_REASON,
    AUTHORITY_DECAY_WATCH_REASON,
    CORROBORATION_LAG_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    RESOLUTION_PRESSURE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")

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
class ResearchSourceAuthorityClaimLatencyDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_REPORT_CONFIG_VERSION
    )
    claim_latency_watch_seconds: Decimal = Decimal("1800.000000")
    claim_latency_block_seconds: Decimal = Decimal("7200.000000")
    authority_decay_watch_age_seconds: Decimal = Decimal("3600.000000")
    authority_decay_block_age_seconds: Decimal = Decimal("14400.000000")
    corroboration_pass_count: Decimal = Decimal("2.000000")
    corroboration_block_count: Decimal = Decimal("0.000000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.600000")
    resolution_watch_seconds_remaining: Decimal = Decimal("1800.000000")
    resolution_block_seconds_remaining: Decimal = Decimal("600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityClaimLatencyDecayConfig:
            raise TypeError(
                "ResearchSourceAuthorityClaimLatencyDecayConfig cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityClaimLatencyDecayConfig:
            raise ValueError(
                "config must be exactly ResearchSourceAuthorityClaimLatencyDecayConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "claim_latency_watch_seconds",
            "claim_latency_block_seconds",
            "authority_decay_watch_age_seconds",
            "authority_decay_block_age_seconds",
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
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
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
class ResearchSourceAuthorityClaimLatencyDecayInput:
    authority_family: str
    claim_bucket: str
    source_authority_score: Decimal
    authority_claim_latency_seconds: Decimal
    claim_age_seconds: Decimal
    corroboration_count: Decimal
    contradiction_pressure_score: Decimal
    resolution_window_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityClaimLatencyDecayInput:
            raise TypeError(
                "ResearchSourceAuthorityClaimLatencyDecayInput cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityClaimLatencyDecayInput:
            raise ValueError(
                "input must be exactly ResearchSourceAuthorityClaimLatencyDecayInput",
            )
        object.__setattr__(
            self,
            "authority_family",
            _require_public_label("authority_family", self.authority_family),
        )
        object.__setattr__(
            self,
            "claim_bucket",
            _require_public_label("claim_bucket", self.claim_bucket),
        )
        object.__setattr__(
            self,
            "source_authority_score",
            _require_ratio("source_authority_score", self.source_authority_score),
        )
        for field_name in (
            "authority_claim_latency_seconds",
            "claim_age_seconds",
            "resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_whole_decimal("corroboration_count", self.corroboration_count),
        )
        object.__setattr__(
            self,
            "contradiction_pressure_score",
            _require_ratio(
                "contradiction_pressure_score",
                self.contradiction_pressure_score,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityClaimLatencyDecayRow:
    authority_family: str
    claim_bucket: str
    source_authority_score: Decimal
    authority_claim_latency_seconds: Decimal
    claim_age_seconds: Decimal
    latency_band: str
    authority_age_band: str
    corroboration_count: Decimal
    corroboration_band: str
    contradiction_pressure_score: Decimal
    resolution_window_seconds: Decimal
    resolution_window_band: str
    effective_authority_score: Decimal
    latency_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityClaimLatencyDecayRow:
            raise TypeError(
                "ResearchSourceAuthorityClaimLatencyDecayRow cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityClaimLatencyDecayRow:
            raise ValueError(
                "row must be exactly ResearchSourceAuthorityClaimLatencyDecayRow",
            )
        object.__setattr__(
            self,
            "authority_family",
            _require_public_label("authority_family", self.authority_family),
        )
        object.__setattr__(
            self,
            "claim_bucket",
            _require_public_label("claim_bucket", self.claim_bucket),
        )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure_score",
            "effective_authority_score",
            "latency_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_claim_latency_seconds",
            "claim_age_seconds",
            "resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_whole_decimal("corroboration_count", self.corroboration_count),
        )
        _require_choice("latency_band", self.latency_band, ("current", "delayed", "blocked"))
        _require_choice("authority_age_band", self.authority_age_band, ("fresh", "stale", "expired"))
        _require_choice("corroboration_band", self.corroboration_band, ("corroborated", "thin", "missing"))
        _require_choice(
            "resolution_window_band",
            self.resolution_window_band,
            ("open", "near", "immediate"),
        )
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
class ResearchSourceAuthorityClaimLatencyDecayReport:
    generated_at: datetime
    config_version: str
    authority_claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_latency_count: Decimal
    authority_decay_count: Decimal
    corroboration_lag_count: Decimal
    contradiction_pressure_count: Decimal
    resolution_pressure_count: Decimal
    lowest_effective_authority_score: Decimal
    highest_latency_decay_score: Decimal
    max_authority_claim_latency_seconds: Decimal
    max_claim_age_seconds: Decimal
    nearest_resolution_window_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityClaimLatencyDecayReport:
            raise TypeError(
                "ResearchSourceAuthorityClaimLatencyDecayReport cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityClaimLatencyDecayReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthorityClaimLatencyDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_latency_count",
            "authority_decay_count",
            "corroboration_lag_count",
            "contradiction_pressure_count",
            "resolution_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_effective_authority_score",
            "highest_latency_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_authority_claim_latency_seconds",
            "max_claim_age_seconds",
            "nearest_resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        return research_source_authority_claim_latency_decay_report_payload(self)


def build_research_source_authority_claim_latency_decay_report(
    inputs: tuple[
        ResearchSourceAuthorityClaimLatencyDecayInput
        | ResearchSourceAuthorityClaimLatencyDecayRow,
        ...,
    ]
    | list[
        ResearchSourceAuthorityClaimLatencyDecayInput
        | ResearchSourceAuthorityClaimLatencyDecayRow
    ],
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceAuthorityClaimLatencyDecayReport:
    if config is None:
        config = ResearchSourceAuthorityClaimLatencyDecayConfig()
    if type(config) is not ResearchSourceAuthorityClaimLatencyDecayConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityClaimLatencyDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _decay_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityClaimLatencyDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        authority_claim_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        high_latency_count=_reason_count(
            rows,
            (CLAIM_LATENCY_WATCH_REASON, CLAIM_LATENCY_BLOCK_REASON),
        ),
        authority_decay_count=_reason_count(
            rows,
            (AUTHORITY_DECAY_WATCH_REASON, AUTHORITY_DECAY_BLOCK_REASON),
        ),
        corroboration_lag_count=_reason_count(
            rows,
            (CORROBORATION_LAG_WATCH_REASON, CORROBORATION_LAG_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        resolution_pressure_count=_reason_count(
            rows,
            (RESOLUTION_PRESSURE_WATCH_REASON, RESOLUTION_PRESSURE_BLOCK_REASON),
        ),
        lowest_effective_authority_score=min(
            (row.effective_authority_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_latency_decay_score=max(
            (row.latency_decay_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        max_authority_claim_latency_seconds=max(
            (row.authority_claim_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        max_claim_age_seconds=max(
            (row.claim_age_seconds for row in rows),
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


def research_source_authority_claim_latency_decay_report_payload(
    report: ResearchSourceAuthorityClaimLatencyDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceAuthorityClaimLatencyDecayReport:
        validate_research_source_authority_claim_latency_decay_report_digest(report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_source_authority_claim_latency_decay_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_research_source_authority_claim_latency_decay_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_source_authority_claim_latency_decay_public_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchSourceAuthorityClaimLatencyDecayReport",
    )


def research_source_authority_claim_latency_decay_report_digest(
    report: ResearchSourceAuthorityClaimLatencyDecayReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityClaimLatencyDecayReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityClaimLatencyDecayReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_claim_latency_decay_report_digest(
    report: ResearchSourceAuthorityClaimLatencyDecayReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityClaimLatencyDecayReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityClaimLatencyDecayReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def validate_research_source_authority_claim_latency_decay_public_payload(
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
) -> tuple[ResearchSourceAuthorityClaimLatencyDecayInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized: list[ResearchSourceAuthorityClaimLatencyDecayInput] = []
    seen: set[tuple[str, str]] = set()
    for item in value:
        if type(item) is ResearchSourceAuthorityClaimLatencyDecayRow:
            row = ResearchSourceAuthorityClaimLatencyDecayInput(
                authority_family=item.authority_family,
                claim_bucket=item.claim_bucket,
                source_authority_score=item.source_authority_score,
                authority_claim_latency_seconds=item.authority_claim_latency_seconds,
                claim_age_seconds=item.claim_age_seconds,
                corroboration_count=item.corroboration_count,
                contradiction_pressure_score=item.contradiction_pressure_score,
                resolution_window_seconds=item.resolution_window_seconds,
                paper_only=item.paper_only,
                report_only=item.report_only,
                readonly=item.readonly,
            )
        elif type(item) is ResearchSourceAuthorityClaimLatencyDecayInput:
            row = item
        else:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityClaimLatencyDecayInput",
            )
        _require_hard_flags("input", row)
        key = (row.authority_family, row.claim_bucket)
        if key in seen:
            raise ValueError("inputs must be unique by authority_family and claim_bucket")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.authority_family, row.claim_bucket)))


def _decay_rows(
    inputs: tuple[ResearchSourceAuthorityClaimLatencyDecayInput, ...],
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...]:
    return tuple(sorted((_decay_row(row, config=config) for row in inputs), key=_row_sort_key))


def _decay_row(
    row: ResearchSourceAuthorityClaimLatencyDecayInput,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> ResearchSourceAuthorityClaimLatencyDecayRow:
    reason_codes = _row_reason_codes(row, config=config)
    effective_authority_score = _effective_authority_score(row, config=config)
    return ResearchSourceAuthorityClaimLatencyDecayRow(
        authority_family=row.authority_family,
        claim_bucket=row.claim_bucket,
        source_authority_score=row.source_authority_score,
        authority_claim_latency_seconds=row.authority_claim_latency_seconds,
        claim_age_seconds=row.claim_age_seconds,
        latency_band=_latency_band(row.authority_claim_latency_seconds, config=config),
        authority_age_band=_authority_age_band(row.claim_age_seconds, config=config),
        corroboration_count=row.corroboration_count,
        corroboration_band=_corroboration_band(row.corroboration_count, config=config),
        contradiction_pressure_score=row.contradiction_pressure_score,
        resolution_window_seconds=row.resolution_window_seconds,
        resolution_window_band=_resolution_window_band(
            row.resolution_window_seconds,
            config=config,
        ),
        effective_authority_score=effective_authority_score,
        latency_decay_score=(ONE - effective_authority_score).quantize(QUANT),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityClaimLatencyDecayInput,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.authority_claim_latency_seconds >= config.claim_latency_block_seconds:
        reasons.append(CLAIM_LATENCY_BLOCK_REASON)
    elif row.authority_claim_latency_seconds > config.claim_latency_watch_seconds:
        reasons.append(CLAIM_LATENCY_WATCH_REASON)
    if row.claim_age_seconds >= config.authority_decay_block_age_seconds:
        reasons.append(AUTHORITY_DECAY_BLOCK_REASON)
    elif row.claim_age_seconds > config.authority_decay_watch_age_seconds:
        reasons.append(AUTHORITY_DECAY_WATCH_REASON)
    if row.corroboration_count <= config.corroboration_block_count:
        reasons.append(CORROBORATION_LAG_BLOCK_REASON)
    elif row.corroboration_count < config.corroboration_pass_count:
        reasons.append(CORROBORATION_LAG_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.resolution_window_seconds <= config.resolution_block_seconds_remaining:
        reasons.append(RESOLUTION_PRESSURE_BLOCK_REASON)
    elif row.resolution_window_seconds < config.resolution_watch_seconds_remaining:
        reasons.append(RESOLUTION_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(HEALTHY_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _effective_authority_score(
    row: ResearchSourceAuthorityClaimLatencyDecayInput,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_health = (
            _latency_freshness_score(
                row.authority_claim_latency_seconds,
                config=config,
            )
            * Decimal("0.250000")
            + _authority_age_score(row.claim_age_seconds, config=config)
            * Decimal("0.250000")
            + _corroboration_score(row.corroboration_count, config=config)
            * Decimal("0.200000")
            + (ONE - row.contradiction_pressure_score) * Decimal("0.200000")
            + _resolution_window_score(row.resolution_window_seconds, config=config)
            * Decimal("0.100000")
        )
        return min(row.source_authority_score * weighted_health, ONE).quantize(QUANT)


def _latency_freshness_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        latency_fraction = min(value / config.claim_latency_block_seconds, ONE)
        return (ONE - latency_fraction).quantize(QUANT)


def _authority_age_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_fraction = min(value / config.authority_decay_block_age_seconds, ONE)
        return (ONE - age_fraction).quantize(QUANT)


def _corroboration_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / config.corroboration_pass_count, ONE).quantize(QUANT)


def _resolution_window_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / config.resolution_watch_seconds_remaining, ONE).quantize(QUANT)


def _latency_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> str:
    if value >= config.claim_latency_block_seconds:
        return "blocked"
    if value > config.claim_latency_watch_seconds:
        return "delayed"
    return "current"


def _authority_age_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> str:
    if value >= config.authority_decay_block_age_seconds:
        return "expired"
    if value > config.authority_decay_watch_age_seconds:
        return "stale"
    return "fresh"


def _corroboration_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> str:
    if value <= config.corroboration_block_count:
        return "missing"
    if value < config.corroboration_pass_count:
        return "thin"
    return "corroborated"


def _resolution_window_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityClaimLatencyDecayConfig,
) -> str:
    if value <= config.resolution_block_seconds_remaining:
        return "immediate"
    if value < config.resolution_watch_seconds_remaining:
        return "near"
    return "open"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if all(row.status == "pass" for row in rows):
        return (HEALTHY_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != HEALTHY_REASON
        ),
        REPORT_REASON_CODES,
    )


def _row_sort_key(row: ResearchSourceAuthorityClaimLatencyDecayRow) -> tuple[Decimal, str, str]:
    return (-row.latency_decay_score, row.authority_family, row.claim_bucket)


def _status_count(
    rows: tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _validate_config(config: ResearchSourceAuthorityClaimLatencyDecayConfig) -> None:
    if config.claim_latency_block_seconds <= config.claim_latency_watch_seconds:
        raise ValueError(
            "claim_latency_watch_seconds must be below claim_latency_block_seconds",
        )
    if config.authority_decay_block_age_seconds <= config.authority_decay_watch_age_seconds:
        raise ValueError(
            "authority_decay_watch_age_seconds must be below authority_decay_block_age_seconds",
        )
    if config.corroboration_block_count >= config.corroboration_pass_count:
        raise ValueError("corroboration_block_count must be below corroboration_pass_count")
    if config.contradiction_block_threshold <= config.contradiction_watch_threshold:
        raise ValueError(
            "contradiction_watch_threshold must be below contradiction_block_threshold",
        )
    if config.resolution_block_seconds_remaining >= config.resolution_watch_seconds_remaining:
        raise ValueError(
            "resolution_block_seconds_remaining must be below resolution_watch_seconds_remaining",
        )


def _validate_row(row: ResearchSourceAuthorityClaimLatencyDecayRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (HEALTHY_REASON,):
        raise ValueError("pass rows require healthy reason")
    if row.status != "pass" and row.reason_codes == (HEALTHY_REASON,):
        raise ValueError("issue rows require active reason codes")
    if row.latency_decay_score != (ONE - row.effective_authority_score).quantize(QUANT):
        raise ValueError("latency_decay_score must match effective_authority_score")


def _validate_report(report: ResearchSourceAuthorityClaimLatencyDecayReport) -> None:
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must be normalized")
    if report.authority_claim_count != _count(len(report.rows)):
        raise ValueError("authority_claim_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.high_latency_count != _reason_count(
        report.rows,
        (CLAIM_LATENCY_WATCH_REASON, CLAIM_LATENCY_BLOCK_REASON),
    ):
        raise ValueError("high_latency_count must match rows")
    if report.authority_decay_count != _reason_count(
        report.rows,
        (AUTHORITY_DECAY_WATCH_REASON, AUTHORITY_DECAY_BLOCK_REASON),
    ):
        raise ValueError("authority_decay_count must match rows")
    if report.corroboration_lag_count != _reason_count(
        report.rows,
        (CORROBORATION_LAG_WATCH_REASON, CORROBORATION_LAG_BLOCK_REASON),
    ):
        raise ValueError("corroboration_lag_count must match rows")
    if report.contradiction_pressure_count != _reason_count(
        report.rows,
        (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
    ):
        raise ValueError("contradiction_pressure_count must match rows")
    if report.resolution_pressure_count != _reason_count(
        report.rows,
        (RESOLUTION_PRESSURE_WATCH_REASON, RESOLUTION_PRESSURE_BLOCK_REASON),
    ):
        raise ValueError("resolution_pressure_count must match rows")
    if report.lowest_effective_authority_score != min(
        (row.effective_authority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_effective_authority_score must match rows")
    if report.highest_latency_decay_score != max(
        (row.latency_decay_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_latency_decay_score must match rows")
    if report.max_authority_claim_latency_seconds != max(
        (row.authority_claim_latency_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("max_authority_claim_latency_seconds must match rows")
    if report.max_claim_age_seconds != max(
        (row.claim_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("max_claim_age_seconds must match rows")
    if report.nearest_resolution_window_seconds != min(
        (row.resolution_window_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("nearest_resolution_window_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceAuthorityClaimLatencyDecayRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchSourceAuthorityClaimLatencyDecayRow:
            raise ValueError("rows must contain ResearchSourceAuthorityClaimLatencyDecayRow")
        key = (row.authority_family, row.claim_bucket)
        if key in seen:
            raise ValueError("rows must be unique by authority_family and claim_bucket")
        seen.add(key)
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_choice(field_name, item, allowed)
    return tuple(reason for reason in allowed if reason in items)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or len(value) > 96:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if PUBLIC_LABEL_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a public label")
    return text


def _require_choice(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_choice(
        field_name,
        value,
        RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_STATUSES,
    )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value.quantize(QUANT)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(QUANT)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(QUANT)


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(QUANT), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _report_digest_from_public_payload(
    report: ResearchSourceAuthorityClaimLatencyDecayReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if any(fragment in key_lower for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} has unsafe public field")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} has unsafe public value")


def _reject_public_numerics(label: str, value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_numerics(label, item)
        return
    if type(value) in (Decimal, int, float):
        raise ValueError(f"{label} must not contain raw numeric values")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag in value and value[flag] is not True:
                raise ValueError(f"{label} must be {flag}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_flag_downgrades(label, item)


def _validate_status_values_in_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key == "status" and item not in RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_STATUSES:
                raise ValueError("status must be pass, watch, or block")
            _validate_status_values_in_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _validate_status_values_in_payload(item)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_CLAIM_LATENCY_DECAY_STATUSES",
    "ResearchSourceAuthorityClaimLatencyDecayConfig",
    "ResearchSourceAuthorityClaimLatencyDecayInput",
    "ResearchSourceAuthorityClaimLatencyDecayReport",
    "ResearchSourceAuthorityClaimLatencyDecayRow",
    "build_research_source_authority_claim_latency_decay_report",
    "research_source_authority_claim_latency_decay_report_digest",
    "research_source_authority_claim_latency_decay_report_payload",
    "validate_research_source_authority_claim_latency_decay_public_payload",
    "validate_research_source_authority_claim_latency_decay_report_digest",
)
