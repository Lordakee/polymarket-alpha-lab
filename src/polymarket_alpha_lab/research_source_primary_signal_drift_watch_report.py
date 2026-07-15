"""Read-only primary signal drift watch report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, cast


DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION = (
    "research-source-primary-signal-drift-watch-report-v0"
)

STATUSES = ("pass", "watch", "block")

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_RANK = {
    "block": 0,
    "watch": 1,
    "pass": 2,
}
_UNSAFE_PUBLIC_FRAGMENTS = (
    "".join(("raw", "_", "candidate")),
    "".join(("candidate", "_", "id")),
    "".join(("candidate", "-", "id")),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("market", "_", "sl", "ug")),
    "".join(("market", "-", "sl", "ug")),
    "".join(("sl", "ug")),
    "".join(("ques", "tion")),
    "".join(("source", "_", "url")),
    "".join(("source", "-", "url")),
    "".join(("source", " ", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("source", " ", "text")),
    "raw",
    "url",
    "".join(("d", "sn")),
    "".join(("ta", "ble", "_", "name")),
    "".join(("ta", "ble", "-", "name")),
    "".join(("ta", "ble", " ", "name")),
    "".join(("to", "ken")),
    "".join(("au", "th", "_")),
    "".join(("au", "th", "-")),
    "api_key",
    "api-key",
    "api key",
    "apikey",
    "secret",
    "password",
    "credential",
    "email",
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("tra", "de")),
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "sqlite://",
    "".join(("siz", "ing")),
    "".join(("reco", "mmend")),
    "position",
    "buy",
    "sell",
)
_COMMON_CREDENTIAL_PATTERNS = (
    re.compile(r"(?:^|[^A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?:$|[^A-Z0-9])"),
    re.compile(r"(?:^|[^A-Za-z0-9])AIza[A-Za-z0-9_-]{20,}(?:$|[^A-Za-z0-9])"),
    re.compile(r"(?:^|[^A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{20,}(?:$|[^A-Za-z0-9])"),
    re.compile(
        r"(?:^|[^A-Za-z0-9])sk-(?:proj-)?[A-Za-z0-9_-]{20,}"
        r"(?:$|[^A-Za-z0-9])",
    ),
    re.compile(r"(?:^|[^A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{20,}(?:$|[^A-Za-z0-9])"),
    re.compile(
        r"(?:^|[^A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{5,}\."
        r"[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}(?:$|[^A-Za-z0-9_-])",
    ),
    re.compile(r"(?i)(?:^|\s)bearer\s+\S{10,}(?:$|\s)"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:^|[^A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"),
)
_ROW_REASON_CODES = (
    "primary_signal_drift_watch_clear",
    "missing_primary_source_block",
    "primary_signal_drift_watch",
    "primary_signal_drift_block",
    "primary_source_stale_watch",
    "primary_source_stale_block",
    "corroboration_gap_watch",
    "corroboration_gap_block",
    "official_conflict_watch",
    "official_conflict_block",
    "evidence_revision_watch",
    "evidence_revision_block",
    "drift_pressure_watch",
    "drift_pressure_block",
)
_REPORT_REASON_CODES = (
    "no_primary_signal_inputs",
    "primary_signal_drift_watch_clear",
    "missing_primary_source_present",
    "primary_signal_drift_present",
    "primary_source_stale_present",
    "corroboration_gap_present",
    "official_conflict_present",
    "evidence_revision_present",
    "drift_pressure_present",
    "primary_signal_drift_block_present",
)
_REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "observed_signal_count",
    "pass_signal_count",
    "watch_signal_count",
    "block_signal_count",
    "stale_primary_source_count",
    "missing_primary_source_count",
    "max_primary_signal_drift_score",
    "max_primary_source_age_seconds",
    "max_drift_pressure_score",
    "watch_ratio",
    "block_ratio",
)
_ROW_DECIMAL_PAYLOAD_FIELDS = (
    "current_primary_signal_score",
    "baseline_primary_signal_score",
    "primary_signal_drift_score",
    "primary_source_age_seconds",
    "primary_source_staleness_score",
    "corroboration_gap_score",
    "official_conflict_score",
    "evidence_revision_score",
    "drift_pressure_score",
)
_ROW_BOOL_PAYLOAD_FIELDS = (
    "primary_source_available",
    "primary_source_stale",
    "paper_only",
    "report_only",
    "readonly",
)
_CONFIG_DECIMAL_PAYLOAD_FIELDS = (
    "watch_primary_signal_drift_score",
    "block_primary_signal_drift_score",
    "watch_primary_source_age_seconds",
    "block_primary_source_age_seconds",
    "watch_corroboration_gap_score",
    "block_corroboration_gap_score",
    "watch_official_conflict_score",
    "block_official_conflict_score",
    "watch_evidence_revision_score",
    "block_evidence_revision_score",
    "watch_drift_pressure_score",
    "block_drift_pressure_score",
    "primary_signal_drift_weight",
    "primary_source_staleness_weight",
    "corroboration_gap_weight",
    "official_conflict_weight",
    "evidence_revision_weight",
)
_CONFIG_PAYLOAD_KEYS = (
    "config_version",
    *_CONFIG_DECIMAL_PAYLOAD_FIELDS,
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "config",
    *_REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "signal_bucket",
    "status",
    *_ROW_DECIMAL_PAYLOAD_FIELDS,
    "primary_source_available",
    "primary_source_stale",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourcePrimarySignalDriftWatchConfig",
    "ResearchSourcePrimarySignalDriftWatchInput",
    "ResearchSourcePrimarySignalDriftWatchReport",
    "ResearchSourcePrimarySignalDriftWatchRow",
    "build_research_source_primary_signal_drift_watch_report",
    "research_source_primary_signal_drift_watch_report_payload",
    "validate_research_source_primary_signal_drift_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchSourcePrimarySignalDriftWatchConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION
    )
    watch_primary_signal_drift_score: Decimal = Decimal("0.200000")
    block_primary_signal_drift_score: Decimal = Decimal("0.500000")
    watch_primary_source_age_seconds: Decimal = Decimal("3600.000000")
    block_primary_source_age_seconds: Decimal = Decimal("86400.000000")
    watch_corroboration_gap_score: Decimal = Decimal("0.300000")
    block_corroboration_gap_score: Decimal = Decimal("0.600000")
    watch_official_conflict_score: Decimal = Decimal("0.250000")
    block_official_conflict_score: Decimal = Decimal("0.550000")
    watch_evidence_revision_score: Decimal = Decimal("0.250000")
    block_evidence_revision_score: Decimal = Decimal("0.600000")
    watch_drift_pressure_score: Decimal = Decimal("0.300000")
    block_drift_pressure_score: Decimal = Decimal("0.650000")
    primary_signal_drift_weight: Decimal = Decimal("0.350000")
    primary_source_staleness_weight: Decimal = Decimal("0.250000")
    corroboration_gap_weight: Decimal = Decimal("0.150000")
    official_conflict_weight: Decimal = Decimal("0.150000")
    evidence_revision_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySignalDriftWatchConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourcePrimarySignalDriftWatchConfig)
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_primary_signal_drift_score",
            "block_primary_signal_drift_score",
            "watch_corroboration_gap_score",
            "block_corroboration_gap_score",
            "watch_official_conflict_score",
            "block_official_conflict_score",
            "watch_evidence_revision_score",
            "block_evidence_revision_score",
            "watch_drift_pressure_score",
            "block_drift_pressure_score",
            "primary_signal_drift_weight",
            "primary_source_staleness_weight",
            "corroboration_gap_weight",
            "official_conflict_weight",
            "evidence_revision_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_primary_source_age_seconds",
            "block_primary_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "watch_primary_signal_drift_score",
            self.watch_primary_signal_drift_score,
            "block_primary_signal_drift_score",
            self.block_primary_signal_drift_score,
        )
        _require_threshold_pair(
            "watch_corroboration_gap_score",
            self.watch_corroboration_gap_score,
            "block_corroboration_gap_score",
            self.block_corroboration_gap_score,
        )
        _require_threshold_pair(
            "watch_official_conflict_score",
            self.watch_official_conflict_score,
            "block_official_conflict_score",
            self.block_official_conflict_score,
        )
        _require_threshold_pair(
            "watch_evidence_revision_score",
            self.watch_evidence_revision_score,
            "block_evidence_revision_score",
            self.block_evidence_revision_score,
        )
        _require_threshold_pair(
            "watch_drift_pressure_score",
            self.watch_drift_pressure_score,
            "block_drift_pressure_score",
            self.block_drift_pressure_score,
        )
        if self.watch_primary_source_age_seconds <= _ZERO:
            raise ValueError("watch_primary_source_age_seconds must be positive")
        if self.block_primary_source_age_seconds <= self.watch_primary_source_age_seconds:
            raise ValueError(
                "block_primary_source_age_seconds must exceed "
                "watch_primary_source_age_seconds",
            )
        with localcontext(_DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.primary_signal_drift_weight
                + self.primary_source_staleness_weight
                + self.corroboration_gap_weight
                + self.official_conflict_weight
                + self.evidence_revision_weight,
            )
        if weight_sum != _ONE:
            raise ValueError("drift pressure weights must sum to one")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimarySignalDriftWatchInput:
    signal_bucket: str
    primary_source_age_seconds: Decimal
    current_primary_signal_score: Decimal
    baseline_primary_signal_score: Decimal
    corroboration_gap_score: Decimal
    official_conflict_score: Decimal
    evidence_revision_score: Decimal
    primary_source_available: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySignalDriftWatchInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchSourcePrimarySignalDriftWatchInput)
        _require_public_identifier("signal_bucket", self.signal_bucket)
        object.__setattr__(
            self,
            "primary_source_age_seconds",
            _normalize_nonnegative_decimal(
                "primary_source_age_seconds",
                self.primary_source_age_seconds,
            ),
        )
        for field_name in (
            "current_primary_signal_score",
            "baseline_primary_signal_score",
            "corroboration_gap_score",
            "official_conflict_score",
            "evidence_revision_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.primary_source_available) is not bool:
            raise ValueError("primary_source_available must be a bool")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourcePrimarySignalDriftWatchRow:
    signal_bucket: str
    status: str
    current_primary_signal_score: Decimal
    baseline_primary_signal_score: Decimal
    primary_signal_drift_score: Decimal
    primary_source_age_seconds: Decimal
    primary_source_staleness_score: Decimal
    corroboration_gap_score: Decimal
    official_conflict_score: Decimal
    evidence_revision_score: Decimal
    drift_pressure_score: Decimal
    primary_source_available: bool
    primary_source_stale: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySignalDriftWatchRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourcePrimarySignalDriftWatchRow)
        _require_public_identifier("signal_bucket", self.signal_bucket)
        _require_status("status", self.status)
        for field_name in (
            "current_primary_signal_score",
            "baseline_primary_signal_score",
            "primary_signal_drift_score",
            "primary_source_staleness_score",
            "corroboration_gap_score",
            "official_conflict_score",
            "evidence_revision_score",
            "drift_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "primary_source_age_seconds",
            _normalize_nonnegative_decimal(
                "primary_source_age_seconds",
                self.primary_source_age_seconds,
            ),
        )
        for field_name in ("primary_source_available", "primary_source_stale"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourcePrimarySignalDriftWatchReport:
    generated_at: datetime
    config_version: str
    config: ResearchSourcePrimarySignalDriftWatchConfig
    observed_signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    block_signal_count: Decimal
    stale_primary_source_count: Decimal
    missing_primary_source_count: Decimal
    max_primary_signal_drift_score: Decimal
    max_primary_source_age_seconds: Decimal
    max_drift_pressure_score: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourcePrimarySignalDriftWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySignalDriftWatchReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourcePrimarySignalDriftWatchReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _revalidate_config(self.config)
        _require_hard_flags(self.config)
        _reject_unsafe_public_payload("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "observed_signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "block_signal_count",
            "stale_primary_source_count",
            "missing_primary_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_primary_signal_drift_score",
            "max_drift_pressure_score",
            "watch_ratio",
            "block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_primary_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_primary_source_age_seconds",
                self.max_primary_source_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_primary_signal_drift_watch_report_payload(self)


def build_research_source_primary_signal_drift_watch_report(
    inputs: Iterable[ResearchSourcePrimarySignalDriftWatchInput],
    *,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
    generated_at: datetime,
) -> ResearchSourcePrimarySignalDriftWatchReport:
    _revalidate_config(config)
    _require_hard_flags(config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config)
                for value in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    observed_signal_count = _decimal_count(len(rows))
    pass_signal_count = _status_total(rows, "pass")
    watch_signal_count = _status_total(rows, "watch")
    block_signal_count = _status_total(rows, "block")
    stale_primary_source_count = _flag_total(rows, "primary_source_stale")
    missing_primary_source_count = _decimal_count(
        sum(1 for row in rows if not row.primary_source_available),
    )
    watch_ratio = _ratio(
        watch_signal_count + block_signal_count,
        observed_signal_count,
    )
    block_ratio = _ratio(block_signal_count, observed_signal_count)
    return ResearchSourcePrimarySignalDriftWatchReport(
        generated_at=generated_at,
        config_version=config.config_version,
        config=config,
        observed_signal_count=observed_signal_count,
        pass_signal_count=pass_signal_count,
        watch_signal_count=watch_signal_count,
        block_signal_count=block_signal_count,
        stale_primary_source_count=stale_primary_source_count,
        missing_primary_source_count=missing_primary_source_count,
        max_primary_signal_drift_score=_max_ratio(
            row.primary_signal_drift_score for row in rows
        ),
        max_primary_source_age_seconds=_max_decimal(
            row.primary_source_age_seconds for row in rows
        ),
        max_drift_pressure_score=_max_ratio(row.drift_pressure_score for row in rows),
        watch_ratio=watch_ratio,
        block_ratio=block_ratio,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_primary_signal_drift_watch_report_payload(
    report: ResearchSourcePrimarySignalDriftWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourcePrimarySignalDriftWatchReport:
        _require_hard_flags(report)
        _reject_unsafe_public_payload("report", report)
        _require_or_set_digest(report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchSourcePrimarySignalDriftWatchReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_primary_signal_drift_watch_report_payload(payload)
    return _canonical_public_payload(payload)


def validate_research_source_primary_signal_drift_watch_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_values(payload)
    _require_public_payload_schema(payload)
    _validate_payload_digest(payload)
    _report_from_public_payload(payload)
    return True


def _canonical_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    config = {
        field_name: payload["config"][field_name]
        for field_name in _CONFIG_PAYLOAD_KEYS
    }
    rows = [
        {field_name: row[field_name] for field_name in _ROW_PAYLOAD_KEYS}
        for row in payload["rows"]
    ]
    for row in rows:
        row["reason_codes"] = list(row["reason_codes"])
    return {
        field_name: rows
        if field_name == "rows"
        else config
        if field_name == "config"
        else list(payload[field_name])
        if field_name == "reason_codes"
        else payload[field_name]
        for field_name in _REPORT_PAYLOAD_KEYS
    }


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourcePrimarySignalDriftWatchReport:
    config = _config_from_public_payload(payload["config"])
    rows = tuple(_row_from_public_payload(row) for row in payload["rows"])
    return ResearchSourcePrimarySignalDriftWatchReport(
        generated_at=_public_utc_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        config=config,
        observed_signal_count=_public_decimal(
            "observed_signal_count",
            payload["observed_signal_count"],
        ),
        pass_signal_count=_public_decimal(
            "pass_signal_count",
            payload["pass_signal_count"],
        ),
        watch_signal_count=_public_decimal(
            "watch_signal_count",
            payload["watch_signal_count"],
        ),
        block_signal_count=_public_decimal(
            "block_signal_count",
            payload["block_signal_count"],
        ),
        stale_primary_source_count=_public_decimal(
            "stale_primary_source_count",
            payload["stale_primary_source_count"],
        ),
        missing_primary_source_count=_public_decimal(
            "missing_primary_source_count",
            payload["missing_primary_source_count"],
        ),
        max_primary_signal_drift_score=_public_decimal(
            "max_primary_signal_drift_score",
            payload["max_primary_signal_drift_score"],
        ),
        max_primary_source_age_seconds=_public_decimal(
            "max_primary_source_age_seconds",
            payload["max_primary_source_age_seconds"],
        ),
        max_drift_pressure_score=_public_decimal(
            "max_drift_pressure_score",
            payload["max_drift_pressure_score"],
        ),
        watch_ratio=_public_decimal("watch_ratio", payload["watch_ratio"]),
        block_ratio=_public_decimal("block_ratio", payload["block_ratio"]),
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        rows=rows,
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _config_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourcePrimarySignalDriftWatchConfig:
    return ResearchSourcePrimarySignalDriftWatchConfig(
        config_version=payload["config_version"],
        watch_primary_signal_drift_score=_public_decimal(
            "watch_primary_signal_drift_score",
            payload["watch_primary_signal_drift_score"],
        ),
        block_primary_signal_drift_score=_public_decimal(
            "block_primary_signal_drift_score",
            payload["block_primary_signal_drift_score"],
        ),
        watch_primary_source_age_seconds=_public_decimal(
            "watch_primary_source_age_seconds",
            payload["watch_primary_source_age_seconds"],
        ),
        block_primary_source_age_seconds=_public_decimal(
            "block_primary_source_age_seconds",
            payload["block_primary_source_age_seconds"],
        ),
        watch_corroboration_gap_score=_public_decimal(
            "watch_corroboration_gap_score",
            payload["watch_corroboration_gap_score"],
        ),
        block_corroboration_gap_score=_public_decimal(
            "block_corroboration_gap_score",
            payload["block_corroboration_gap_score"],
        ),
        watch_official_conflict_score=_public_decimal(
            "watch_official_conflict_score",
            payload["watch_official_conflict_score"],
        ),
        block_official_conflict_score=_public_decimal(
            "block_official_conflict_score",
            payload["block_official_conflict_score"],
        ),
        watch_evidence_revision_score=_public_decimal(
            "watch_evidence_revision_score",
            payload["watch_evidence_revision_score"],
        ),
        block_evidence_revision_score=_public_decimal(
            "block_evidence_revision_score",
            payload["block_evidence_revision_score"],
        ),
        watch_drift_pressure_score=_public_decimal(
            "watch_drift_pressure_score",
            payload["watch_drift_pressure_score"],
        ),
        block_drift_pressure_score=_public_decimal(
            "block_drift_pressure_score",
            payload["block_drift_pressure_score"],
        ),
        primary_signal_drift_weight=_public_decimal(
            "primary_signal_drift_weight",
            payload["primary_signal_drift_weight"],
        ),
        primary_source_staleness_weight=_public_decimal(
            "primary_source_staleness_weight",
            payload["primary_source_staleness_weight"],
        ),
        corroboration_gap_weight=_public_decimal(
            "corroboration_gap_weight",
            payload["corroboration_gap_weight"],
        ),
        official_conflict_weight=_public_decimal(
            "official_conflict_weight",
            payload["official_conflict_weight"],
        ),
        evidence_revision_weight=_public_decimal(
            "evidence_revision_weight",
            payload["evidence_revision_weight"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourcePrimarySignalDriftWatchRow:
    return ResearchSourcePrimarySignalDriftWatchRow(
        signal_bucket=payload["signal_bucket"],
        status=payload["status"],
        current_primary_signal_score=_public_decimal(
            "current_primary_signal_score",
            payload["current_primary_signal_score"],
        ),
        baseline_primary_signal_score=_public_decimal(
            "baseline_primary_signal_score",
            payload["baseline_primary_signal_score"],
        ),
        primary_signal_drift_score=_public_decimal(
            "primary_signal_drift_score",
            payload["primary_signal_drift_score"],
        ),
        primary_source_age_seconds=_public_decimal(
            "primary_source_age_seconds",
            payload["primary_source_age_seconds"],
        ),
        primary_source_staleness_score=_public_decimal(
            "primary_source_staleness_score",
            payload["primary_source_staleness_score"],
        ),
        corroboration_gap_score=_public_decimal(
            "corroboration_gap_score",
            payload["corroboration_gap_score"],
        ),
        official_conflict_score=_public_decimal(
            "official_conflict_score",
            payload["official_conflict_score"],
        ),
        evidence_revision_score=_public_decimal(
            "evidence_revision_score",
            payload["evidence_revision_score"],
        ),
        drift_pressure_score=_public_decimal(
            "drift_pressure_score",
            payload["drift_pressure_score"],
        ),
        primary_source_available=payload["primary_source_available"],
        primary_source_stale=payload["primary_source_stale"],
        reason_codes=tuple(payload["reason_codes"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _normalize_inputs(
    values: Iterable[ResearchSourcePrimarySignalDriftWatchInput],
) -> tuple[ResearchSourcePrimarySignalDriftWatchInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        inputs = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in inputs:
        if type(value) is not ResearchSourcePrimarySignalDriftWatchInput:
            raise ValueError(
                "inputs must contain ResearchSourcePrimarySignalDriftWatchInput values",
            )
        _revalidate_input(value)
        _require_hard_flags(value)
        _reject_unsafe_public_payload("input", value)
        if value.signal_bucket in seen:
            raise ValueError("signal_bucket values must be unique")
        seen.add(value.signal_bucket)
    return inputs


def _row_from_input(
    value: ResearchSourcePrimarySignalDriftWatchInput,
    *,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
) -> ResearchSourcePrimarySignalDriftWatchRow:
    primary_signal_drift_score = _absolute_ratio_delta(
        value.current_primary_signal_score,
        value.baseline_primary_signal_score,
    )
    raw_primary_source_staleness_score = _raw_ratio(
        value.primary_source_age_seconds,
        config.block_primary_source_age_seconds,
    )
    primary_source_staleness_score = _quantize(raw_primary_source_staleness_score)
    primary_source_stale = (
        (not value.primary_source_available)
        or value.primary_source_age_seconds >= config.watch_primary_source_age_seconds
    )
    raw_drift_pressure_score = _raw_drift_pressure_score(
        primary_signal_drift_score=primary_signal_drift_score,
        primary_source_staleness_score=raw_primary_source_staleness_score,
        corroboration_gap_score=value.corroboration_gap_score,
        official_conflict_score=value.official_conflict_score,
        evidence_revision_score=value.evidence_revision_score,
        config=config,
    )
    drift_pressure_score = _quantize(raw_drift_pressure_score)
    status = _row_status(
        primary_signal_drift_score=primary_signal_drift_score,
        primary_source_age_seconds=value.primary_source_age_seconds,
        corroboration_gap_score=value.corroboration_gap_score,
        official_conflict_score=value.official_conflict_score,
        evidence_revision_score=value.evidence_revision_score,
        drift_pressure_score=raw_drift_pressure_score,
        primary_source_available=value.primary_source_available,
        config=config,
    )
    return ResearchSourcePrimarySignalDriftWatchRow(
        signal_bucket=value.signal_bucket,
        status=status,
        current_primary_signal_score=value.current_primary_signal_score,
        baseline_primary_signal_score=value.baseline_primary_signal_score,
        primary_signal_drift_score=primary_signal_drift_score,
        primary_source_age_seconds=value.primary_source_age_seconds,
        primary_source_staleness_score=primary_source_staleness_score,
        corroboration_gap_score=value.corroboration_gap_score,
        official_conflict_score=value.official_conflict_score,
        evidence_revision_score=value.evidence_revision_score,
        drift_pressure_score=drift_pressure_score,
        primary_source_available=value.primary_source_available,
        primary_source_stale=primary_source_stale,
        reason_codes=_row_reason_codes(
            status=status,
            primary_signal_drift_score=primary_signal_drift_score,
            primary_source_age_seconds=value.primary_source_age_seconds,
            corroboration_gap_score=value.corroboration_gap_score,
            official_conflict_score=value.official_conflict_score,
            evidence_revision_score=value.evidence_revision_score,
            drift_pressure_score=raw_drift_pressure_score,
            primary_source_available=value.primary_source_available,
            primary_source_stale=primary_source_stale,
            config=config,
        ),
    )


def _drift_pressure_score(
    *,
    primary_signal_drift_score: Decimal,
    primary_source_staleness_score: Decimal,
    corroboration_gap_score: Decimal,
    official_conflict_score: Decimal,
    evidence_revision_score: Decimal,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
) -> Decimal:
    return _quantize(
        _raw_drift_pressure_score(
            primary_signal_drift_score=primary_signal_drift_score,
            primary_source_staleness_score=primary_source_staleness_score,
            corroboration_gap_score=corroboration_gap_score,
            official_conflict_score=official_conflict_score,
            evidence_revision_score=evidence_revision_score,
            config=config,
        ),
    )


def _raw_drift_pressure_score(
    *,
    primary_signal_drift_score: Decimal,
    primary_source_staleness_score: Decimal,
    corroboration_gap_score: Decimal,
    official_conflict_score: Decimal,
    evidence_revision_score: Decimal,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _raw_bounded_ratio(
            primary_signal_drift_score * config.primary_signal_drift_weight
            + primary_source_staleness_score * config.primary_source_staleness_weight
            + corroboration_gap_score * config.corroboration_gap_weight
            + official_conflict_score * config.official_conflict_weight
            + evidence_revision_score * config.evidence_revision_weight,
        )


def _row_status(
    *,
    primary_signal_drift_score: Decimal,
    primary_source_age_seconds: Decimal,
    corroboration_gap_score: Decimal,
    official_conflict_score: Decimal,
    evidence_revision_score: Decimal,
    drift_pressure_score: Decimal,
    primary_source_available: bool,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
) -> str:
    if not primary_source_available:
        return "block"
    if (
        primary_signal_drift_score >= config.block_primary_signal_drift_score
        or primary_source_age_seconds >= config.block_primary_source_age_seconds
        or corroboration_gap_score >= config.block_corroboration_gap_score
        or official_conflict_score >= config.block_official_conflict_score
        or evidence_revision_score >= config.block_evidence_revision_score
        or drift_pressure_score >= config.block_drift_pressure_score
    ):
        return "block"
    if (
        primary_signal_drift_score >= config.watch_primary_signal_drift_score
        or primary_source_age_seconds >= config.watch_primary_source_age_seconds
        or corroboration_gap_score >= config.watch_corroboration_gap_score
        or official_conflict_score >= config.watch_official_conflict_score
        or evidence_revision_score >= config.watch_evidence_revision_score
        or drift_pressure_score >= config.watch_drift_pressure_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    primary_signal_drift_score: Decimal,
    primary_source_age_seconds: Decimal,
    corroboration_gap_score: Decimal,
    official_conflict_score: Decimal,
    evidence_revision_score: Decimal,
    drift_pressure_score: Decimal,
    primary_source_available: bool,
    primary_source_stale: bool,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return ("primary_signal_drift_watch_clear",)
    codes: list[str] = []
    if not primary_source_available:
        codes.append("missing_primary_source_block")
    _append_score_code(
        codes,
        "primary_signal_drift",
        primary_signal_drift_score,
        config.watch_primary_signal_drift_score,
        config.block_primary_signal_drift_score,
    )
    if primary_source_stale:
        if primary_source_age_seconds >= config.block_primary_source_age_seconds:
            codes.append("primary_source_stale_block")
        else:
            codes.append("primary_source_stale_watch")
    _append_score_code(
        codes,
        "corroboration_gap",
        corroboration_gap_score,
        config.watch_corroboration_gap_score,
        config.block_corroboration_gap_score,
    )
    _append_score_code(
        codes,
        "official_conflict",
        official_conflict_score,
        config.watch_official_conflict_score,
        config.block_official_conflict_score,
    )
    _append_score_code(
        codes,
        "evidence_revision",
        evidence_revision_score,
        config.watch_evidence_revision_score,
        config.block_evidence_revision_score,
    )
    _append_score_code(
        codes,
        "drift_pressure",
        drift_pressure_score,
        config.watch_drift_pressure_score,
        config.block_drift_pressure_score,
    )
    return tuple(codes)


def _append_score_code(
    codes: list[str],
    prefix: str,
    score: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if score >= block_threshold:
        codes.append(f"{prefix}_block")
    elif score >= watch_threshold:
        codes.append(f"{prefix}_watch")


def _report_status(rows: tuple[ResearchSourcePrimarySignalDriftWatchRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimarySignalDriftWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_primary_signal_inputs",)
    if not any(row.status != "pass" for row in rows):
        return ("primary_signal_drift_watch_clear",)
    codes: list[str] = []
    if any(not row.primary_source_available for row in rows):
        codes.append("missing_primary_source_present")
    if any(
        _has_reason(row, "primary_signal_drift_watch", "primary_signal_drift_block")
        for row in rows
    ):
        codes.append("primary_signal_drift_present")
    if any(row.primary_source_stale for row in rows):
        codes.append("primary_source_stale_present")
    if any(_has_reason(row, "corroboration_gap_watch", "corroboration_gap_block") for row in rows):
        codes.append("corroboration_gap_present")
    if any(_has_reason(row, "official_conflict_watch", "official_conflict_block") for row in rows):
        codes.append("official_conflict_present")
    if any(_has_reason(row, "evidence_revision_watch", "evidence_revision_block") for row in rows):
        codes.append("evidence_revision_present")
    if any(_has_reason(row, "drift_pressure_watch", "drift_pressure_block") for row in rows):
        codes.append("drift_pressure_present")
    if any(row.status == "block" for row in rows):
        codes.append("primary_signal_drift_block_present")
    return tuple(codes)


def _has_reason(
    row: ResearchSourcePrimarySignalDriftWatchRow,
    watch_code: str,
    block_code: str,
) -> bool:
    return watch_code in row.reason_codes or block_code in row.reason_codes


def _row_sort_key(
    row: ResearchSourcePrimarySignalDriftWatchRow,
) -> tuple[
    int,
    int,
    int,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
]:
    return (
        _STATUS_RANK[row.status],
        0 if not row.primary_source_available else 1,
        0 if row.primary_source_stale else 1,
        row.drift_pressure_score.copy_negate(),
        row.primary_signal_drift_score.copy_negate(),
        row.current_primary_signal_score.copy_negate(),
        row.baseline_primary_signal_score.copy_negate(),
        row.primary_source_staleness_score.copy_negate(),
        row.primary_source_age_seconds.copy_negate(),
        row.corroboration_gap_score.copy_negate(),
        row.official_conflict_score.copy_negate(),
        row.evidence_revision_score.copy_negate(),
        row.signal_bucket,
    )


def _validate_row_materialized_fields(
    row: ResearchSourcePrimarySignalDriftWatchRow,
    *,
    config: ResearchSourcePrimarySignalDriftWatchConfig,
) -> None:
    expected_drift_score = _absolute_ratio_delta(
        row.current_primary_signal_score,
        row.baseline_primary_signal_score,
    )
    if row.primary_signal_drift_score != expected_drift_score:
        raise ValueError("primary_signal_drift_score must match row inputs")
    raw_expected_staleness_score = _raw_ratio(
        row.primary_source_age_seconds,
        config.block_primary_source_age_seconds,
    )
    expected_staleness_score = _quantize(raw_expected_staleness_score)
    if row.primary_source_staleness_score != expected_staleness_score:
        raise ValueError("primary_source_staleness_score must match row inputs")
    expected_stale = (
        (not row.primary_source_available)
        or row.primary_source_age_seconds >= config.watch_primary_source_age_seconds
    )
    if row.primary_source_stale is not expected_stale:
        raise ValueError("primary_source_stale must match row inputs")
    raw_expected_pressure_score = _raw_drift_pressure_score(
        primary_signal_drift_score=row.primary_signal_drift_score,
        primary_source_staleness_score=raw_expected_staleness_score,
        corroboration_gap_score=row.corroboration_gap_score,
        official_conflict_score=row.official_conflict_score,
        evidence_revision_score=row.evidence_revision_score,
        config=config,
    )
    expected_pressure_score = _quantize(raw_expected_pressure_score)
    if row.drift_pressure_score != expected_pressure_score:
        raise ValueError("drift_pressure_score must match row inputs")
    expected_status = _row_status(
        primary_signal_drift_score=row.primary_signal_drift_score,
        primary_source_age_seconds=row.primary_source_age_seconds,
        corroboration_gap_score=row.corroboration_gap_score,
        official_conflict_score=row.official_conflict_score,
        evidence_revision_score=row.evidence_revision_score,
        drift_pressure_score=raw_expected_pressure_score,
        primary_source_available=row.primary_source_available,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row inputs")
    expected_reason_codes = _row_reason_codes(
        status=expected_status,
        primary_signal_drift_score=row.primary_signal_drift_score,
        primary_source_age_seconds=row.primary_source_age_seconds,
        corroboration_gap_score=row.corroboration_gap_score,
        official_conflict_score=row.official_conflict_score,
        evidence_revision_score=row.evidence_revision_score,
        drift_pressure_score=raw_expected_pressure_score,
        primary_source_available=row.primary_source_available,
        primary_source_stale=row.primary_source_stale,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")


def _validate_row(row: ResearchSourcePrimarySignalDriftWatchRow) -> None:
    if row.status not in STATUSES:
        raise ValueError("status must be pass, watch, or block")
    if row.status == "pass" and row.reason_codes != ("primary_signal_drift_watch_clear",):
        raise ValueError("reason_codes must match status")
    if row.status != "pass" and row.reason_codes == ("primary_signal_drift_watch_clear",):
        raise ValueError("status must match reason_codes")
    if row.status == "block" and not any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and not any(
        code.endswith("_watch") for code in row.reason_codes
    ):
        raise ValueError("status must match reason_codes")
    if row.primary_source_stale and not any(
        code in row.reason_codes
        for code in ("primary_source_stale_watch", "primary_source_stale_block")
    ):
        raise ValueError("primary_source_stale must match reason_codes")
    if (not row.primary_source_available) and (
        "missing_primary_source_block" not in row.reason_codes
    ):
        raise ValueError("primary_source_available must match reason_codes")


def _validate_report(report: ResearchSourcePrimarySignalDriftWatchReport) -> None:
    for row in report.rows:
        _validate_row_materialized_fields(row, config=report.config)
    if report.observed_signal_count != _decimal_count(len(report.rows)):
        raise ValueError("observed_signal_count must match rows")
    for field_name, status in (
        ("pass_signal_count", "pass"),
        ("watch_signal_count", "watch"),
        ("block_signal_count", "block"),
    ):
        if getattr(report, field_name) != _status_total(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.stale_primary_source_count != _flag_total(
        report.rows,
        "primary_source_stale",
    ):
        raise ValueError("stale_primary_source_count must match rows")
    if report.missing_primary_source_count != _decimal_count(
        sum(1 for row in report.rows if not row.primary_source_available),
    ):
        raise ValueError("missing_primary_source_count must match rows")
    if report.max_primary_signal_drift_score != _max_ratio(
        row.primary_signal_drift_score for row in report.rows
    ):
        raise ValueError("max_primary_signal_drift_score must match rows")
    if report.max_primary_source_age_seconds != _max_decimal(
        row.primary_source_age_seconds for row in report.rows
    ):
        raise ValueError("max_primary_source_age_seconds must match rows")
    if report.max_drift_pressure_score != _max_ratio(
        row.drift_pressure_score for row in report.rows
    ):
        raise ValueError("max_drift_pressure_score must match rows")
    if report.watch_ratio != _ratio(
        report.watch_signal_count + report.block_signal_count,
        report.observed_signal_count,
    ):
        raise ValueError("watch_ratio must match counts")
    if report.block_ratio != _ratio(
        report.block_signal_count,
        report.observed_signal_count,
    ):
        raise ValueError("block_ratio must match counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")


def _normalize_rows(
    values: object,
) -> tuple[ResearchSourcePrimarySignalDriftWatchRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(values)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimarySignalDriftWatchRow:
            raise ValueError("rows must contain watch row values")
        _revalidate_row(row)
        _require_hard_flags(row)
        _reject_unsafe_public_payload("row", row)
        if row.signal_bucket in seen:
            raise ValueError("rows must be unique by signal_bucket")
        seen.add(row.signal_bucket)
    return rows


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_public_identifier(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, _REPORT_PAYLOAD_KEYS)
    _public_utc_datetime("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    _require_public_config_payload_schema(payload["config"])
    for field_name in _REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _normalize_reason_codes("reason_codes", payload["reason_codes"], _REPORT_REASON_CODES)
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _require_public_row_payload_schema(row)
    _require_digest_string("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_config_payload_schema(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("config must be a JSON object")
    _reject_unknown_payload_keys("config payload", value, _CONFIG_PAYLOAD_KEYS)
    _require_public_identifier("config_version", value["config_version"])
    if (
        value["config_version"]
        != DEFAULT_RESEARCH_SOURCE_PRIMARY_SIGNAL_DRIFT_WATCH_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    for field_name in _CONFIG_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_row_payload_schema(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _reject_unknown_payload_keys("row payload", value, _ROW_PAYLOAD_KEYS)
    _require_public_identifier("signal_bucket", value["signal_bucket"])
    _require_status("status", value["status"])
    for field_name in _ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in _ROW_BOOL_PAYLOAD_FIELDS:
        if type(value[field_name]) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_reason_codes("reason_codes", value["reason_codes"], _ROW_REASON_CODES)


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if set(payload) != set(allowed_keys):
        raise ValueError(f"{label} must use the public readonly schema")
    if tuple(payload) != allowed_keys:
        raise ValueError(f"{label} must use exact canonical field order")


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if value is None:
        raise ValueError(f"{path} must not contain null values")
    if type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{path} must not contain float values")
    if type(value) is int:
        raise ValueError(f"{path} must use Decimal-derived string values")
    if type(value) is str:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _require_public_payload_values(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} is not JSON serializable")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    current = payload["derived_validation_digest"]
    if current != _derived_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    encoded = json.dumps(
        _canonical_digest_value(value),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_fragment(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
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
    if (
        not value.isprintable()
        or any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
        or any(pattern.search(value) is not None for pattern in _COMMON_CREDENTIAL_PATTERNS)
    ):
        raise ValueError(f"unsafe public surface in {label}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_fragment(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_threshold_pair(
    watch_field_name: str,
    watch_threshold: Decimal,
    block_field_name: str,
    block_threshold: Decimal,
) -> None:
    if watch_threshold <= _ZERO:
        raise ValueError(f"{watch_field_name} must be positive")
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _revalidate_config(value: object) -> None:
    _require_exact_type(
        "config",
        value,
        ResearchSourcePrimarySignalDriftWatchConfig,
    )
    ResearchSourcePrimarySignalDriftWatchConfig.__post_init__(
        cast(ResearchSourcePrimarySignalDriftWatchConfig, value),
    )


def _revalidate_input(value: object) -> None:
    _require_exact_type(
        "input",
        value,
        ResearchSourcePrimarySignalDriftWatchInput,
    )
    ResearchSourcePrimarySignalDriftWatchInput.__post_init__(
        cast(ResearchSourcePrimarySignalDriftWatchInput, value),
    )


def _revalidate_row(value: object) -> None:
    _require_exact_type(
        "row",
        value,
        ResearchSourcePrimarySignalDriftWatchRow,
    )
    ResearchSourcePrimarySignalDriftWatchRow.__post_init__(
        cast(ResearchSourcePrimarySignalDriftWatchRow, value),
    )


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize_field(field_name, decimal_value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_field(field_name, decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_field(field_name, decimal_value)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_field(field_name, _require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize_field(field_name: str, value: Decimal) -> Decimal:
    try:
        normalized = _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places without rounding")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANTUM)
    if normalized.is_zero():
        return _ZERO
    return normalized


def _bounded_ratio(value: Decimal) -> Decimal:
    return _quantize(_raw_bounded_ratio(value))


def _raw_bounded_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _status_total(
    rows: tuple[ResearchSourcePrimarySignalDriftWatchRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _flag_total(
    rows: tuple[ResearchSourcePrimarySignalDriftWatchRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _quantize(_raw_ratio(numerator, denominator))


def _raw_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _raw_bounded_ratio(numerator / denominator)


def _absolute_ratio_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _bounded_ratio(abs(left - right))


def _max_ratio(values: Iterable[Decimal]) -> Decimal:
    return _normalize_ratio("max_ratio", max(tuple(values) or (_ZERO,)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return _normalize_nonnegative_decimal("max_decimal", max(tuple(values) or (_ZERO,)))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _require_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    parsed = _require_decimal(field_name, parsed)
    canonical = format(_quantize_field(field_name, parsed), "f")
    if value != canonical:
        raise ValueError(f"{field_name} must use six decimal places")


def _public_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal_string(field_name, value)
    return Decimal(cast(str, value))


def _public_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str or not _is_sha256_hex(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _is_sha256_hex(value: str) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True
