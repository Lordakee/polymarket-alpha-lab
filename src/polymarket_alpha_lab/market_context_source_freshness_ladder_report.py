"""Pure in-memory Phase 1 market-context source freshness ladder reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_CONTEXT_SOURCE_FRESHNESS_LADDER_REPORT_CONFIG_VERSION = (
    "market-context-source-freshness-ladder-v0"
)
CHECK_NAMES = (
    "liquidity",
    "price_probability",
    "event_news",
    "close_time",
    "resolution_source",
)
MARKET_CONTEXT_SOURCE_CHECK_KINDS = CHECK_NAMES
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
STALE_ACKNOWLEDGEMENT_SEVERITIES = ("none", "acknowledged", "unacknowledged")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
CHECK_RANK = {check_name: rank for rank, check_name in enumerate(CHECK_NAMES)}
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "reason_codes",
    "counts",
    "ratios",
    "max_observed_age_seconds",
    "thresholds",
    "min_market_count",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
COUNT_PAYLOAD_FIELDS = (
    "market_count",
    "required_check_count",
    "row_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "stale_acknowledged_count",
    "unacknowledged_stale_count",
    "missing_count",
    "source_blocked_count",
)
RATIO_PAYLOAD_FIELDS = ("freshness_ratio", "stale_acknowledged_ratio")
THRESHOLD_PAYLOAD_FIELDS = ("check_name", "max_age_seconds")
ROW_PAYLOAD_FIELDS = (
    "market_slug",
    "check_name",
    "source_id",
    "observed_at",
    "stale_acknowledged_at",
    "age_seconds",
    "max_age_seconds",
    "status",
    "stale_acknowledgement_severity",
    "missing_reason",
    "blocked_reason",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

PASS_REASON = "market_context_source_freshness_ladder_passed"
MISSING_REASON = "missing_market_context_source"
SOURCE_BLOCKED_REASON = "blocked_market_context_source"
UNACKNOWLEDGED_STALE_REASON = "unacknowledged_stale_market_context_source"
ACKNOWLEDGED_STALE_REASON = "stale_acknowledged_market_context_source"
INSUFFICIENT_MARKET_REASON = "insufficient_market_context_source_markets"
REPORT_REASON_SEQUENCE = (
    SOURCE_BLOCKED_REASON,
    MISSING_REASON,
    UNACKNOWLEDGED_STALE_REASON,
    ACKNOWLEDGED_STALE_REASON,
    INSUFFICIENT_MARKET_REASON,
    PASS_REASON,
)

SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("a", "u", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("or", "d", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "v", "ice"),
        _join_parts("live"),
        _join_parts("tra", "ding"),
        _join_parts("tra", "de"),
        _join_parts("ex", "change"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pass", "word"),
        _join_parts("api", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("priv", "ate"),
        _join_parts("cre", "dent", "ial"),
    ),
)


@dataclass(frozen=True)
class MarketContextSourceFreshnessLadderConfig:
    config_version: str = (
        DEFAULT_MARKET_CONTEXT_SOURCE_FRESHNESS_LADDER_REPORT_CONFIG_VERSION
    )
    max_age_seconds_by_check: tuple[tuple[str, Decimal], ...] = (
        ("liquidity", Decimal("300")),
        ("price_probability", Decimal("300")),
        ("event_news", Decimal("600")),
        ("close_time", Decimal("300")),
        ("resolution_source", Decimal("86400")),
    )
    min_market_count: Decimal = Decimal("1")
    required_check_names: tuple[str, ...] = CHECK_NAMES
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_age_seconds_by_check",
            _normalize_thresholds(self.max_age_seconds_by_check),
        )
        object.__setattr__(
            self,
            "min_market_count",
            _require_positive_decimal("min_market_count", self.min_market_count),
        )
        object.__setattr__(
            self,
            "required_check_names",
            _normalize_required_check_names(self.required_check_names),
        )
        _require_thresholds_cover_required_checks(self)
        require_paper_only_flags("market context source freshness ladder config", self)


@dataclass(frozen=True)
class MarketContextSourceFreshnessObservation:
    market_slug: str
    check_name: str
    source_id: str
    observed_at: datetime | None = None
    stale_acknowledged_at: datetime | None = None
    missing_reason: str | None = None
    blocked_reason: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_slug", self.market_slug)
        _require_check_name("check_name", self.check_name)
        _require_public_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "observed_at",
            _as_optional_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "stale_acknowledged_at",
            _as_optional_utc("stale_acknowledged_at", self.stale_acknowledged_at),
        )
        _require_optional_public_string("missing_reason", self.missing_reason)
        _require_optional_public_string("blocked_reason", self.blocked_reason)
        _validate_observation_shape(self)
        require_paper_only_flags("market context source freshness observation", self)


@dataclass(frozen=True)
class MarketContextSourceFreshnessLadderRow:
    market_slug: str
    check_name: str
    source_id: str
    observed_at: datetime | None
    stale_acknowledged_at: datetime | None
    age_seconds: Decimal | None
    max_age_seconds: Decimal
    status: str
    stale_acknowledgement_severity: str
    missing_reason: str | None
    blocked_reason: str | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_slug", self.market_slug)
        _require_check_name("check_name", self.check_name)
        _require_public_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "observed_at",
            _as_optional_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "stale_acknowledged_at",
            _as_optional_utc("stale_acknowledged_at", self.stale_acknowledged_at),
        )
        object.__setattr__(
            self,
            "age_seconds",
            _normalize_optional_decimal("age_seconds", self.age_seconds),
        )
        object.__setattr__(
            self,
            "max_age_seconds",
            _require_positive_decimal("max_age_seconds", self.max_age_seconds),
        )
        _require_status("status", self.status, ROW_STATUSES)
        _require_stale_acknowledgement_severity(
            "stale_acknowledgement_severity",
            self.stale_acknowledgement_severity,
        )
        _require_optional_public_string("missing_reason", self.missing_reason)
        _require_optional_public_string("blocked_reason", self.blocked_reason)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_shape(self)
        require_paper_only_flags("market context source freshness ladder row", self)


@dataclass(frozen=True)
class MarketContextSourceFreshnessLadderReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    required_check_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_acknowledged_count: Decimal
    unacknowledged_stale_count: Decimal
    missing_count: Decimal
    source_blocked_count: Decimal
    freshness_ratio: Decimal
    stale_acknowledged_ratio: Decimal
    max_observed_age_seconds: Decimal | None
    max_age_seconds_by_check: tuple[tuple[str, Decimal], ...]
    min_market_count: Decimal
    rows: tuple[MarketContextSourceFreshnessLadderRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "required_check_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_acknowledged_count",
            "unacknowledged_stale_count",
            "missing_count",
            "source_blocked_count",
            "freshness_ratio",
            "stale_acknowledged_ratio",
            "min_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_market_count <= ZERO:
            raise ValueError("min_market_count must be positive")
        object.__setattr__(
            self,
            "max_observed_age_seconds",
            _normalize_optional_decimal(
                "max_observed_age_seconds",
                self.max_observed_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_age_seconds_by_check",
            _normalize_thresholds(self.max_age_seconds_by_check),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("market context source freshness ladder report", self)
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


def build_market_context_source_freshness_ladder_report(
    observations: list[MarketContextSourceFreshnessObservation]
    | tuple[MarketContextSourceFreshnessObservation, ...],
    *,
    config: MarketContextSourceFreshnessLadderConfig,
    generated_at: datetime,
) -> MarketContextSourceFreshnessLadderReport:
    if type(config) is not MarketContextSourceFreshnessLadderConfig:
        raise ValueError("config must be a MarketContextSourceFreshnessLadderConfig")
    require_paper_only_flags("market context source freshness ladder config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _rows_from_observations(
        normalized_observations,
        config=config,
        generated_at=generated_at_utc,
    )
    market_count = _decimal_count(len({row.market_slug for row in rows}))
    row_count = _decimal_count(len(rows))
    reason_codes = _report_reason_codes(
        rows,
        market_count=market_count,
        min_market_count=config.min_market_count,
    )
    status = _report_status(
        rows,
        market_count=market_count,
        min_market_count=config.min_market_count,
    )

    return MarketContextSourceFreshnessLadderReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        reason_codes=reason_codes,
        market_count=market_count,
        required_check_count=_decimal_count(len(config.required_check_names)),
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        stale_acknowledged_count=_severity_count(rows, "acknowledged"),
        unacknowledged_stale_count=_severity_count(rows, "unacknowledged"),
        missing_count=_decimal_count(sum(1 for row in rows if row.missing_reason is not None)),
        source_blocked_count=_decimal_count(
            sum(1 for row in rows if row.blocked_reason is not None),
        ),
        freshness_ratio=_ratio(_status_count(rows, "pass"), row_count),
        stale_acknowledged_ratio=_ratio(_severity_count(rows, "acknowledged"), row_count),
        max_observed_age_seconds=_max_optional(tuple(row.age_seconds for row in rows)),
        max_age_seconds_by_check=_thresholds_for_required_checks(config),
        min_market_count=config.min_market_count,
        rows=rows,
    )


def to_market_context_source_freshness_ladder_payload(
    report: MarketContextSourceFreshnessLadderReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is not MarketContextSourceFreshnessLadderReport:
        if type(report) is dict:
            _reject_unsafe_public_payload("payload", report)
            _require_public_payload_fields(report)
            _validate_public_payload(report)
            return dict(report)
        raise ValueError("report must be a MarketContextSourceFreshnessLadderReport")
    require_paper_only_flags("market context source freshness ladder report", report)
    _validate_report_derived_validation_digest(report)
    payload = _report_public_payload_values(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    _validate_public_payload(payload)
    return payload


def _report_public_payload_values(
    report: MarketContextSourceFreshnessLadderReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "counts": {
            "market_count": str(report.market_count),
            "required_check_count": str(report.required_check_count),
            "row_count": str(report.row_count),
            "pass_count": str(report.pass_count),
            "watch_count": str(report.watch_count),
            "blocked_count": str(report.blocked_count),
            "stale_acknowledged_count": str(report.stale_acknowledged_count),
            "unacknowledged_stale_count": str(report.unacknowledged_stale_count),
            "missing_count": str(report.missing_count),
            "source_blocked_count": str(report.source_blocked_count),
        },
        "ratios": {
            "freshness_ratio": str(report.freshness_ratio),
            "stale_acknowledged_ratio": str(report.stale_acknowledged_ratio),
        },
        "max_observed_age_seconds": (
            str(report.max_observed_age_seconds)
            if report.max_observed_age_seconds is not None
            else None
        ),
        "thresholds": [
            {"check_name": check_name, "max_age_seconds": str(max_age_seconds)}
            for check_name, max_age_seconds in report.max_age_seconds_by_check
        ],
        "min_market_count": str(report.min_market_count),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: MarketContextSourceFreshnessLadderReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: MarketContextSourceFreshnessLadderReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        field_name: payload[field_name]
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }
    encoded_payload = _json_digest_value(digest_payload)
    return hashlib.sha256(
        (
            "market_context_source_freshness_ladder_report_derived|"
            + encoded_payload
        ).encode("utf-8"),
    ).hexdigest()


def _json_digest_value(value: object) -> str:
    if value is None:
        return "null"
    if type(value) in (str, bool):
        return repr(value)
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            parts.append(f"{key}:{_json_digest_value(value[key])}")
        return "{" + ",".join(parts) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_json_digest_value(item) for item in value) + "]"
    raise ValueError("digest payload value is not public JSON")


def _require_public_payload_fields(payload: dict[str, Any]) -> None:
    for field_name in PUBLIC_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_public_payload_fields(payload)
    _require_public_payload_datetime("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    _require_status("status", payload["status"], REPORT_STATUSES)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _validate_public_counts(payload["counts"])
    _validate_public_ratios(payload["ratios"])
    _require_optional_decimal_payload_string(
        "max_observed_age_seconds",
        payload["max_observed_age_seconds"],
    )
    _validate_public_thresholds(payload["thresholds"])
    _require_decimal_payload_string("min_market_count", payload["min_market_count"])
    if _decimal_from_payload_string(
        "min_market_count",
        payload["min_market_count"],
    ) <= ZERO:
        raise ValueError("min_market_count must be positive")
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
    ratios = payload["ratios"]
    if type(counts) is not dict:
        raise ValueError("counts must be an object")
    if type(ratios) is not dict:
        raise ValueError("ratios must be an object")

    MarketContextSourceFreshnessLadderReport(
        generated_at=_datetime_from_payload_string(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=payload["config_version"],
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        market_count=_decimal_from_payload_string("market_count", counts["market_count"]),
        required_check_count=_decimal_from_payload_string(
            "required_check_count",
            counts["required_check_count"],
        ),
        row_count=_decimal_from_payload_string("row_count", counts["row_count"]),
        pass_count=_decimal_from_payload_string("pass_count", counts["pass_count"]),
        watch_count=_decimal_from_payload_string("watch_count", counts["watch_count"]),
        blocked_count=_decimal_from_payload_string(
            "blocked_count",
            counts["blocked_count"],
        ),
        stale_acknowledged_count=_decimal_from_payload_string(
            "stale_acknowledged_count",
            counts["stale_acknowledged_count"],
        ),
        unacknowledged_stale_count=_decimal_from_payload_string(
            "unacknowledged_stale_count",
            counts["unacknowledged_stale_count"],
        ),
        missing_count=_decimal_from_payload_string(
            "missing_count",
            counts["missing_count"],
        ),
        source_blocked_count=_decimal_from_payload_string(
            "source_blocked_count",
            counts["source_blocked_count"],
        ),
        freshness_ratio=_decimal_from_payload_string(
            "freshness_ratio",
            ratios["freshness_ratio"],
        ),
        stale_acknowledged_ratio=_decimal_from_payload_string(
            "stale_acknowledged_ratio",
            ratios["stale_acknowledged_ratio"],
        ),
        max_observed_age_seconds=_optional_decimal_from_payload_string(
            "max_observed_age_seconds",
            payload["max_observed_age_seconds"],
        ),
        max_age_seconds_by_check=_thresholds_from_public_payload(
            payload["thresholds"],
        ),
        min_market_count=_decimal_from_payload_string(
            "min_market_count",
            payload["min_market_count"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in payload["rows"]),
        derived_validation_digest=payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )


def _thresholds_from_public_payload(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not list:
        raise ValueError("thresholds must be a list")
    return tuple(
        (
            row["check_name"],
            _decimal_from_payload_string("max_age_seconds", row["max_age_seconds"]),
        )
        for row in value
    )


def _row_from_public_payload(
    row: dict[str, Any],
) -> MarketContextSourceFreshnessLadderRow:
    return MarketContextSourceFreshnessLadderRow(
        market_slug=row["market_slug"],
        check_name=row["check_name"],
        source_id=row["source_id"],
        observed_at=_optional_datetime_from_payload_string(
            "observed_at",
            row["observed_at"],
        ),
        stale_acknowledged_at=_optional_datetime_from_payload_string(
            "stale_acknowledged_at",
            row["stale_acknowledged_at"],
        ),
        age_seconds=_optional_decimal_from_payload_string(
            "age_seconds",
            row["age_seconds"],
        ),
        max_age_seconds=_decimal_from_payload_string(
            "max_age_seconds",
            row["max_age_seconds"],
        ),
        status=row["status"],
        stale_acknowledgement_severity=row["stale_acknowledgement_severity"],
        missing_reason=row["missing_reason"],
        blocked_reason=row["blocked_reason"],
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


def _validate_public_ratios(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("ratios must be an object")
    _require_exact_keys("ratios", value, RATIO_PAYLOAD_FIELDS)
    for field_name in RATIO_PAYLOAD_FIELDS:
        _require_decimal_payload_string(field_name, value[field_name])


def _validate_public_thresholds(value: object) -> None:
    if type(value) is not list:
        raise ValueError("thresholds must be a list")
    seen_check_names: set[str] = set()
    for row in value:
        if type(row) is not dict:
            raise ValueError("thresholds entries must be objects")
        _require_exact_keys("thresholds", row, THRESHOLD_PAYLOAD_FIELDS)
        _require_check_name("check_name", row["check_name"])
        if row["check_name"] in seen_check_names:
            raise ValueError("thresholds must be unique by check_name")
        seen_check_names.add(row["check_name"])
        max_age_seconds = _decimal_from_payload_string(
            "max_age_seconds",
            row["max_age_seconds"],
        )
        if max_age_seconds <= ZERO:
            raise ValueError("max_age_seconds must be positive")


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    seen_keys: set[tuple[str, str]] = set()
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows entries must be objects")
        _require_exact_keys("rows", row, ROW_PAYLOAD_FIELDS)
        _require_public_string("market_slug", row["market_slug"])
        _require_check_name("check_name", row["check_name"])
        _require_public_string("source_id", row["source_id"])
        _require_optional_public_payload_datetime("observed_at", row["observed_at"])
        _require_optional_public_payload_datetime(
            "stale_acknowledged_at",
            row["stale_acknowledged_at"],
        )
        _require_optional_decimal_payload_string("age_seconds", row["age_seconds"])
        max_age_seconds = _decimal_from_payload_string(
            "max_age_seconds",
            row["max_age_seconds"],
        )
        if max_age_seconds <= ZERO:
            raise ValueError("max_age_seconds must be positive")
        _require_status("status", row["status"], ROW_STATUSES)
        _require_stale_acknowledgement_severity(
            "stale_acknowledgement_severity",
            row["stale_acknowledgement_severity"],
        )
        _require_optional_public_string("missing_reason", row["missing_reason"])
        _require_optional_public_string("blocked_reason", row["blocked_reason"])
        _normalize_public_reason_codes("reason_codes", row["reason_codes"])
        _require_public_payload_flags("row", row)
        key = (row["market_slug"], row["check_name"])
        if key in seen_keys:
            raise ValueError("rows must be unique by market_slug and check_name")
        seen_keys.add(key)


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


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one value")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return reason_codes


def _require_optional_decimal_payload_string(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal_payload_string(field_name, value)


def _optional_decimal_from_payload_string(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_payload_string(field_name, value)


def _require_decimal_payload_string(field_name: str, value: object) -> None:
    _decimal_from_payload_string(field_name, value)


def _decimal_from_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    _require_canonical_string(field_name, value)
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_public_payload_datetime(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_public_payload_datetime(field_name, value)


def _optional_datetime_from_payload_string(
    field_name: str,
    value: object,
) -> datetime | None:
    if value is None:
        return None
    return _datetime_from_payload_string(field_name, value)


def _require_public_payload_datetime(field_name: str, value: object) -> None:
    _datetime_from_payload_string(field_name, value)


def _datetime_from_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    _require_canonical_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _normalize_sha256(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(
        character not in "0123456789abcdef"
        for character in value
    ):
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
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def market_context_source_freshness_ladder_report_payload(
    report: MarketContextSourceFreshnessLadderReport,
) -> dict[str, Any]:
    return to_market_context_source_freshness_ladder_payload(report)


def _row_payload(row: MarketContextSourceFreshnessLadderRow) -> dict[str, Any]:
    return {
        "market_slug": row.market_slug,
        "check_name": row.check_name,
        "source_id": row.source_id,
        "observed_at": row.observed_at.isoformat() if row.observed_at is not None else None,
        "stale_acknowledged_at": (
            row.stale_acknowledged_at.isoformat()
            if row.stale_acknowledged_at is not None
            else None
        ),
        "age_seconds": str(row.age_seconds) if row.age_seconds is not None else None,
        "max_age_seconds": str(row.max_age_seconds),
        "status": row.status,
        "stale_acknowledgement_severity": row.stale_acknowledgement_severity,
        "missing_reason": row.missing_reason,
        "blocked_reason": row.blocked_reason,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _rows_from_observations(
    observations: tuple[MarketContextSourceFreshnessObservation, ...],
    *,
    config: MarketContextSourceFreshnessLadderConfig,
    generated_at: datetime,
) -> tuple[MarketContextSourceFreshnessLadderRow, ...]:
    thresholds = dict(config.max_age_seconds_by_check)
    observations_by_key = {
        (observation.market_slug, observation.check_name): observation
        for observation in observations
    }
    market_slugs = tuple(sorted({observation.market_slug for observation in observations}))
    rows: list[MarketContextSourceFreshnessLadderRow] = []
    for market_slug in market_slugs:
        for check_name in config.required_check_names:
            observation = observations_by_key.get((market_slug, check_name))
            if observation is None:
                rows.append(
                    _missing_required_row(
                        market_slug=market_slug,
                        check_name=check_name,
                        max_age_seconds=thresholds[check_name],
                    ),
                )
                continue
            rows.append(
                _row_from_observation(
                    observation,
                    max_age_seconds=thresholds[check_name],
                    generated_at=generated_at,
                ),
            )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_observation(
    observation: MarketContextSourceFreshnessObservation,
    *,
    max_age_seconds: Decimal,
    generated_at: datetime,
) -> MarketContextSourceFreshnessLadderRow:
    if observation.missing_reason is not None:
        return MarketContextSourceFreshnessLadderRow(
            market_slug=observation.market_slug,
            check_name=observation.check_name,
            source_id=observation.source_id,
            observed_at=None,
            stale_acknowledged_at=None,
            age_seconds=None,
            max_age_seconds=max_age_seconds,
            status="blocked",
            stale_acknowledgement_severity="none",
            missing_reason=observation.missing_reason,
            blocked_reason=None,
            reason_codes=(_missing_source_reason(observation.check_name),),
        )
    if observation.blocked_reason is not None:
        return MarketContextSourceFreshnessLadderRow(
            market_slug=observation.market_slug,
            check_name=observation.check_name,
            source_id=observation.source_id,
            observed_at=None,
            stale_acknowledged_at=None,
            age_seconds=None,
            max_age_seconds=max_age_seconds,
            status="blocked",
            stale_acknowledgement_severity="none",
            missing_reason=None,
            blocked_reason=observation.blocked_reason,
            reason_codes=(_blocked_source_reason(observation.check_name),),
        )
    if observation.observed_at is None:
        raise ValueError("observed_at is required for observed market context sources")
    age_seconds = _age_seconds(
        generated_at,
        observation.observed_at,
        field_name="observed_at",
    )
    if age_seconds <= max_age_seconds:
        return MarketContextSourceFreshnessLadderRow(
            market_slug=observation.market_slug,
            check_name=observation.check_name,
            source_id=observation.source_id,
            observed_at=observation.observed_at,
            stale_acknowledged_at=None,
            age_seconds=age_seconds,
            max_age_seconds=max_age_seconds,
            status="pass",
            stale_acknowledgement_severity="none",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=(_fresh_source_reason(observation.check_name),),
        )
    if observation.stale_acknowledged_at is not None:
        _age_seconds(
            generated_at,
            observation.stale_acknowledged_at,
            field_name="stale_acknowledged_at",
        )
        return MarketContextSourceFreshnessLadderRow(
            market_slug=observation.market_slug,
            check_name=observation.check_name,
            source_id=observation.source_id,
            observed_at=observation.observed_at,
            stale_acknowledged_at=observation.stale_acknowledged_at,
            age_seconds=age_seconds,
            max_age_seconds=max_age_seconds,
            status="watch",
            stale_acknowledgement_severity="acknowledged",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=(_acknowledged_stale_source_reason(observation.check_name),),
        )
    return MarketContextSourceFreshnessLadderRow(
        market_slug=observation.market_slug,
        check_name=observation.check_name,
        source_id=observation.source_id,
        observed_at=observation.observed_at,
        stale_acknowledged_at=None,
        age_seconds=age_seconds,
        max_age_seconds=max_age_seconds,
        status="blocked",
        stale_acknowledgement_severity="unacknowledged",
        missing_reason=None,
        blocked_reason=None,
        reason_codes=(_unacknowledged_stale_source_reason(observation.check_name),),
    )


def _missing_required_row(
    *,
    market_slug: str,
    check_name: str,
    max_age_seconds: Decimal,
) -> MarketContextSourceFreshnessLadderRow:
    return MarketContextSourceFreshnessLadderRow(
        market_slug=market_slug,
        check_name=check_name,
        source_id="required_check",
        observed_at=None,
        stale_acknowledged_at=None,
        age_seconds=None,
        max_age_seconds=max_age_seconds,
        status="blocked",
        stale_acknowledgement_severity="none",
        missing_reason="required_check_missing",
        blocked_reason=None,
        reason_codes=(_missing_source_reason(check_name),),
    )


def _report_status(
    rows: tuple[MarketContextSourceFreshnessLadderRow, ...],
    *,
    market_count: Decimal,
    min_market_count: Decimal,
) -> str:
    if market_count < min_market_count:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketContextSourceFreshnessLadderRow, ...],
    *,
    market_count: Decimal,
    min_market_count: Decimal,
) -> tuple[str, ...]:
    candidates: list[str] = []
    if market_count < min_market_count:
        candidates.append(INSUFFICIENT_MARKET_REASON)
    if any(row.blocked_reason is not None for row in rows):
        candidates.append(SOURCE_BLOCKED_REASON)
    if any(row.missing_reason is not None for row in rows):
        candidates.append(MISSING_REASON)
    if any(row.stale_acknowledgement_severity == "unacknowledged" for row in rows):
        candidates.append(UNACKNOWLEDGED_STALE_REASON)
    if any(row.stale_acknowledgement_severity == "acknowledged" for row in rows):
        candidates.append(ACKNOWLEDGED_STALE_REASON)
    if not candidates:
        candidates.append(PASS_REASON)
    return tuple(reason for reason in REPORT_REASON_SEQUENCE if reason in candidates)


def _normalize_observations(value: object) -> tuple[MarketContextSourceFreshnessObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for observation in observations:
        if type(observation) is not MarketContextSourceFreshnessObservation:
            raise ValueError("observations must contain MarketContextSourceFreshnessObservation")
        require_paper_only_flags("market context source freshness observation", observation)
        key = (observation.market_slug, observation.check_name)
        if key in seen_keys:
            raise ValueError("duplicate market context source check")
        seen_keys.add(key)
    return tuple(sorted(observations, key=lambda row: (row.market_slug, row.check_name)))


def _normalize_rows(value: object) -> tuple[MarketContextSourceFreshnessLadderRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketContextSourceFreshnessLadderRow:
            raise ValueError("rows must contain MarketContextSourceFreshnessLadderRow")
        require_paper_only_flags("market context source freshness ladder row", row)
        key = (row.market_slug, row.check_name)
        if key in seen_keys:
            raise ValueError("rows must be unique by market_slug and check_name")
        seen_keys.add(key)
    return rows


def _validate_observation_shape(observation: MarketContextSourceFreshnessObservation) -> None:
    if observation.missing_reason is not None and observation.blocked_reason is not None:
        raise ValueError("blocked_reason cannot be combined with missing_reason")
    if observation.observed_at is not None and (
        observation.missing_reason is not None or observation.blocked_reason is not None
    ):
        raise ValueError("observed_at cannot be combined with missing or blocked reasons")
    if observation.observed_at is None and (
        observation.missing_reason is None and observation.blocked_reason is None
    ):
        raise ValueError("observed_at is required unless a missing or blocked reason is present")


def _validate_row_shape(row: MarketContextSourceFreshnessLadderRow) -> None:
    if row.missing_reason is not None and row.blocked_reason is not None:
        raise ValueError("blocked_reason cannot be combined with missing_reason")
    if row.observed_at is None and row.age_seconds is not None:
        raise ValueError("age_seconds must be absent when observed_at is absent")
    if row.observed_at is not None and row.age_seconds is None:
        raise ValueError("age_seconds is required when observed_at is present")
    expected_status, expected_severity, expected_reason = _expected_row_state(row)
    if row.status != expected_status:
        raise ValueError("status must match row freshness state")
    if row.stale_acknowledgement_severity != expected_severity:
        raise ValueError("stale_acknowledgement_severity must match row freshness state")
    if row.reason_codes != (expected_reason,):
        raise ValueError("reason_codes must match row freshness state")


def _expected_row_state(row: MarketContextSourceFreshnessLadderRow) -> tuple[str, str, str]:
    if row.missing_reason is not None:
        return "blocked", "none", _missing_source_reason(row.check_name)
    if row.blocked_reason is not None:
        return "blocked", "none", _blocked_source_reason(row.check_name)
    if row.age_seconds is None:
        raise ValueError("age_seconds is required for observed rows")
    if row.age_seconds <= row.max_age_seconds:
        return "pass", "none", _fresh_source_reason(row.check_name)
    if row.stale_acknowledged_at is not None:
        return "watch", "acknowledged", _acknowledged_stale_source_reason(row.check_name)
    return "blocked", "unacknowledged", _unacknowledged_stale_source_reason(row.check_name)


def _validate_report(report: MarketContextSourceFreshnessLadderReport) -> None:
    if tuple(_row_sort_key(row) for row in report.rows) != tuple(
        sorted(_row_sort_key(row) for row in report.rows),
    ):
        raise ValueError("rows must use deterministic severity and source check sequence")
    market_count = _decimal_count(len({row.market_slug for row in report.rows}))
    if report.market_count != market_count:
        raise ValueError("market_count must match rows")
    if report.required_check_count != _decimal_count(len(report.max_age_seconds_by_check)):
        raise ValueError("required_check_count must match thresholds")
    _validate_report_threshold_coverage(report)
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    for status in ROW_STATUSES:
        field_name = f"{status}_count"
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.stale_acknowledged_count != _severity_count(report.rows, "acknowledged"):
        raise ValueError("stale_acknowledged_count must match rows")
    if report.unacknowledged_stale_count != _severity_count(report.rows, "unacknowledged"):
        raise ValueError("unacknowledged_stale_count must match rows")
    if report.missing_count != _decimal_count(
        sum(1 for row in report.rows if row.missing_reason is not None),
    ):
        raise ValueError("missing_count must match rows")
    if report.source_blocked_count != _decimal_count(
        sum(1 for row in report.rows if row.blocked_reason is not None),
    ):
        raise ValueError("source_blocked_count must match rows")
    if report.freshness_ratio != _ratio(report.pass_count, report.row_count):
        raise ValueError("freshness_ratio must match rows")
    if report.stale_acknowledged_ratio != _ratio(
        report.stale_acknowledged_count,
        report.row_count,
    ):
        raise ValueError("stale_acknowledged_ratio must match rows")
    if report.max_observed_age_seconds != _max_optional(
        tuple(row.age_seconds for row in report.rows),
    ):
        raise ValueError("max_observed_age_seconds must match rows")
    expected_status = _report_status(
        report.rows,
        market_count=report.market_count,
        min_market_count=report.min_market_count,
    )
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reasons = _report_reason_codes(
        report.rows,
        market_count=report.market_count,
        min_market_count=report.min_market_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    _validate_report_generated_ages(report)


def _validate_report_threshold_coverage(
    report: MarketContextSourceFreshnessLadderReport,
) -> None:
    thresholds = dict(report.max_age_seconds_by_check)
    required_check_names = frozenset(thresholds)
    rows_by_market: dict[str, set[str]] = {}
    for row in report.rows:
        if row.check_name not in thresholds:
            raise ValueError("rows must use configured thresholds")
        if row.max_age_seconds != thresholds[row.check_name]:
            raise ValueError("max_age_seconds must match thresholds")
        rows_by_market.setdefault(row.market_slug, set()).add(row.check_name)

    for check_names in rows_by_market.values():
        if check_names != required_check_names:
            raise ValueError("rows must provide required check coverage per market")


def _validate_report_generated_ages(report: MarketContextSourceFreshnessLadderReport) -> None:
    for row in report.rows:
        if row.observed_at is not None:
            expected_age = _age_seconds(report.generated_at, row.observed_at, field_name="observed_at")
            if row.age_seconds != expected_age:
                raise ValueError("age_seconds must match generated_at")
        if row.stale_acknowledged_at is not None:
            _age_seconds(
                report.generated_at,
                row.stale_acknowledged_at,
                field_name="stale_acknowledged_at",
            )


def _thresholds_for_required_checks(
    config: MarketContextSourceFreshnessLadderConfig,
) -> tuple[tuple[str, Decimal], ...]:
    thresholds = dict(config.max_age_seconds_by_check)
    return tuple((check_name, thresholds[check_name]) for check_name in config.required_check_names)


def _normalize_thresholds(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("max_age_seconds_by_check must be a list or tuple")
    rows = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    seen_check_names: set[str] = set()
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError("max_age_seconds_by_check entries must be check/seconds pairs")
        check_name, max_age_seconds = row
        _require_check_name("check_name", check_name)
        if check_name in seen_check_names:
            raise ValueError("max_age_seconds_by_check must be unique by check_name")
        seen_check_names.add(check_name)
        normalized.append(
            (
                check_name,
                _require_positive_decimal("max_age_seconds", max_age_seconds),
            ),
        )
    return tuple(sorted(normalized, key=lambda item: CHECK_RANK[item[0]]))


def _normalize_required_check_names(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("required_check_names must be a list or tuple")
    check_names = tuple(value)
    if not check_names:
        raise ValueError("required_check_names must contain at least one check")
    seen_check_names: set[str] = set()
    for check_name in check_names:
        _require_check_name("check_name", check_name)
        if check_name in seen_check_names:
            raise ValueError("required_check_names must be unique")
        seen_check_names.add(check_name)
    return check_names


def _require_thresholds_cover_required_checks(
    config: MarketContextSourceFreshnessLadderConfig,
) -> None:
    threshold_check_names = {check_name for check_name, _ in config.max_age_seconds_by_check}
    for check_name in config.required_check_names:
        if check_name not in threshold_check_names:
            raise ValueError("max_age_seconds_by_check must cover required_check_names")


def _fresh_source_reason(check_name: str) -> str:
    return f"fresh_{check_name}_source"


def _missing_source_reason(check_name: str) -> str:
    return f"missing_{check_name}_source"


def _blocked_source_reason(check_name: str) -> str:
    return f"blocked_{check_name}_source"


def _acknowledged_stale_source_reason(check_name: str) -> str:
    return f"acknowledged_stale_{check_name}_source"


def _unacknowledged_stale_source_reason(check_name: str) -> str:
    return f"unacknowledged_stale_{check_name}_source"


def _status_count(
    rows: tuple[MarketContextSourceFreshnessLadderRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _severity_count(
    rows: tuple[MarketContextSourceFreshnessLadderRow, ...],
    severity: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if row.stale_acknowledgement_severity == severity),
    )


def _row_sort_key(row: MarketContextSourceFreshnessLadderRow) -> tuple[int, int, str]:
    return (STATUS_RANK[row.status], CHECK_RANK[row.check_name], row.market_slug)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _max_optional(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return None
    return max(present_values)


def _age_seconds(later: datetime, earlier: datetime, *, field_name: str) -> Decimal:
    later_utc = _as_utc("generated_at", later)
    earlier_utc = _as_utc(field_name, earlier)
    if earlier_utc > later_utc:
        raise ValueError(f"{field_name} must not be in the future")
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


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
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _require_status(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known status")


def _require_stale_acknowledgement_severity(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STALE_ACKNOWLEDGEMENT_SEVERITIES:
        raise ValueError(f"{field_name} must be a known severity")


def _require_check_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CHECK_NAMES:
        raise ValueError(f"{field_name} must be a known market context source check")


def _require_optional_public_string(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_public_string(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single-line")


__all__ = (
    "CHECK_NAMES",
    "DEFAULT_MARKET_CONTEXT_SOURCE_FRESHNESS_LADDER_REPORT_CONFIG_VERSION",
    "MARKET_CONTEXT_SOURCE_CHECK_KINDS",
    "MarketContextSourceFreshnessLadderConfig",
    "MarketContextSourceFreshnessLadderReport",
    "MarketContextSourceFreshnessLadderRow",
    "MarketContextSourceFreshnessObservation",
    "build_market_context_source_freshness_ladder_report",
    "market_context_source_freshness_ladder_report_payload",
    "to_market_context_source_freshness_ladder_payload",
)
