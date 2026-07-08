"""Pure aggregate memory readiness report for equity-index event research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EQUITY_INDEX_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-equity-index-event-team-memory-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
SECONDS_QUANT = Decimal("0.000001")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
ZERO_COUNT = Decimal("0")
ZERO_SECONDS = Decimal("0.000000")

STATUSES = ("pass", "watch", "block")
REPORT_REASON_CODES = (
    "equity_index_event_team_memory_report_pass",
    "equity_index_event_team_memory_report_watch",
    "equity_index_event_team_memory_report_block",
    "memory_readiness_pass",
    "memory_readiness_watch",
    "memory_readiness_block",
    "calibration_notes_pass",
    "calibration_notes_watch",
    "calibration_notes_block",
    "evidence_recency_pass",
    "evidence_recency_watch",
    "evidence_recency_block",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "auth",
    "buy",
    "database",
    "http",
    "identifier",
    "live",
    "mutation",
    "network",
    "order",
    "persist",
    "raw",
    "sell",
    "signing",
    "source",
    "text",
    "trade",
    "url",
)

__all__ = (
    "DEFAULT_RESEARCH_EQUITY_INDEX_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "ResearchEquityIndexEventTeamMemoryReportConfig",
    "ResearchEquityIndexEventTeamMemorySignal",
    "ResearchEquityIndexEventTeamMemoryReport",
    "build_research_equity_index_event_team_memory_report",
    "research_equity_index_event_team_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchEquityIndexEventTeamMemoryReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EQUITY_INDEX_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    pass_min_memory_readiness_score: Decimal = Decimal("0.850000")
    watch_min_memory_readiness_score: Decimal = Decimal("0.600000")
    pass_min_calibration_note_coverage_ratio: Decimal = Decimal("0.800000")
    watch_min_calibration_note_coverage_ratio: Decimal = Decimal("0.550000")
    watch_max_unresolved_calibration_note_count: Decimal = Decimal("1")
    block_max_unresolved_calibration_note_count: Decimal = Decimal("3")
    pass_max_evidence_age_seconds: Decimal = Decimal("86400.000000")
    watch_max_evidence_age_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "pass_min_memory_readiness_score",
            "watch_min_memory_readiness_score",
            "pass_min_calibration_note_coverage_ratio",
            "watch_min_calibration_note_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_max_unresolved_calibration_note_count",
            "block_max_unresolved_calibration_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "pass_max_evidence_age_seconds",
            "watch_max_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("ResearchEquityIndexEventTeamMemoryReportConfig", self)
        _reject_unsafe_public_payload(
            "ResearchEquityIndexEventTeamMemoryReportConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchEquityIndexEventTeamMemorySignal:
    memory_readiness_score: Decimal
    calibration_note_coverage_ratio: Decimal
    unresolved_calibration_note_count: Decimal
    latest_evidence_age_seconds: Decimal
    evidence_packet_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "memory_readiness_score",
            "calibration_note_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_calibration_note_count",
            _normalize_nonnegative_integral_decimal(
                "unresolved_calibration_note_count",
                self.unresolved_calibration_note_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _normalize_nonnegative_seconds(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "evidence_packet_count",
            _normalize_nonnegative_integral_decimal(
                "evidence_packet_count",
                self.evidence_packet_count,
            ),
        )
        _require_hard_flags("ResearchEquityIndexEventTeamMemorySignal", self)
        _reject_unsafe_public_payload(
            "ResearchEquityIndexEventTeamMemorySignal",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchEquityIndexEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    report_status: str
    memory_readiness_status: str
    calibration_notes_status: str
    evidence_recency_status: str
    memory_signal_count: Decimal
    average_memory_readiness_score: Decimal
    average_calibration_note_coverage_ratio: Decimal
    unresolved_calibration_note_count: Decimal
    max_evidence_age_seconds: Decimal
    evidence_packet_count: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "report_status",
            "memory_readiness_status",
            "calibration_notes_status",
            "evidence_recency_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "memory_signal_count",
            _normalize_nonnegative_integral_decimal(
                "memory_signal_count",
                self.memory_signal_count,
            ),
        )
        for field_name in (
            "average_memory_readiness_score",
            "average_calibration_note_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_calibration_note_count",
            _normalize_nonnegative_integral_decimal(
                "unresolved_calibration_note_count",
                self.unresolved_calibration_note_count,
            ),
        )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_nonnegative_seconds(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "evidence_packet_count",
            _normalize_nonnegative_integral_decimal(
                "evidence_packet_count",
                self.evidence_packet_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("ResearchEquityIndexEventTeamMemoryReport", self)
        _reject_unsafe_public_payload(
            "ResearchEquityIndexEventTeamMemoryReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_equity_index_event_team_memory_report_payload(self)


def build_research_equity_index_event_team_memory_report(
    memory_signals: object,
    *,
    config: ResearchEquityIndexEventTeamMemoryReportConfig | None = None,
    generated_at: datetime,
) -> ResearchEquityIndexEventTeamMemoryReport:
    if config is None:
        config = ResearchEquityIndexEventTeamMemoryReportConfig()
    if type(config) is not ResearchEquityIndexEventTeamMemoryReportConfig:
        raise ValueError(
            "config must be a ResearchEquityIndexEventTeamMemoryReportConfig",
        )
    _require_hard_flags("ResearchEquityIndexEventTeamMemoryReportConfig", config)
    signals = _normalize_memory_signals(memory_signals)

    signal_count = Decimal(len(signals)).quantize(COUNT_QUANT)
    average_memory_readiness_score = _average_ratio(
        tuple(signal.memory_readiness_score for signal in signals),
    )
    average_calibration_note_coverage_ratio = _average_ratio(
        tuple(signal.calibration_note_coverage_ratio for signal in signals),
    )
    unresolved_calibration_note_count = _sum_counts(
        tuple(signal.unresolved_calibration_note_count for signal in signals),
    )
    max_evidence_age_seconds = _max_seconds(
        tuple(signal.latest_evidence_age_seconds for signal in signals),
    )
    evidence_packet_count = _sum_counts(
        tuple(signal.evidence_packet_count for signal in signals),
    )

    memory_readiness_status = _memory_readiness_status(
        signal_count,
        average_memory_readiness_score,
        config,
    )
    calibration_notes_status = _calibration_notes_status(
        signal_count,
        average_calibration_note_coverage_ratio,
        unresolved_calibration_note_count,
        config,
    )
    evidence_recency_status = _evidence_recency_status(
        signal_count,
        evidence_packet_count,
        max_evidence_age_seconds,
        config,
    )
    report_status = _report_status(
        (
            memory_readiness_status,
            calibration_notes_status,
            evidence_recency_status,
        ),
    )

    values: dict[str, object] = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "report_status": report_status,
        "memory_readiness_status": memory_readiness_status,
        "calibration_notes_status": calibration_notes_status,
        "evidence_recency_status": evidence_recency_status,
        "memory_signal_count": signal_count,
        "average_memory_readiness_score": average_memory_readiness_score,
        "average_calibration_note_coverage_ratio": average_calibration_note_coverage_ratio,
        "unresolved_calibration_note_count": unresolved_calibration_note_count,
        "max_evidence_age_seconds": max_evidence_age_seconds,
        "evidence_packet_count": evidence_packet_count,
        "reason_codes": _report_reason_codes(
            report_status,
            memory_readiness_status,
            calibration_notes_status,
            evidence_recency_status,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchEquityIndexEventTeamMemoryReport(**values)


def research_equity_index_event_team_memory_report_payload(
    report: ResearchEquityIndexEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEquityIndexEventTeamMemoryReport:
        _require_hard_flags("ResearchEquityIndexEventTeamMemoryReport", report)
        payload = _payload_value(asdict(report))
        _reject_unsafe_public_payload(
            "ResearchEquityIndexEventTeamMemoryReport.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "research_equity_index_event_team_memory_report_payload",
            report,
        )
        _require_payload_flags(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _require_payload_digest(payload)
        return payload
    raise ValueError("report must be a ResearchEquityIndexEventTeamMemoryReport")


def _normalize_memory_signals(
    value: object,
) -> tuple[ResearchEquityIndexEventTeamMemorySignal, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("memory signals must be an iterable")
    signals = tuple(value)
    for item in signals:
        if type(item) is not ResearchEquityIndexEventTeamMemorySignal:
            raise ValueError(
                "memory signals must contain ResearchEquityIndexEventTeamMemorySignal",
            )
        _require_hard_flags("ResearchEquityIndexEventTeamMemorySignal", item)
    keys = tuple(
        (
            item.memory_readiness_score,
            item.calibration_note_coverage_ratio,
            item.unresolved_calibration_note_count,
            item.latest_evidence_age_seconds,
            item.evidence_packet_count,
        )
        for item in signals
    )
    if len(set(keys)) != len(keys):
        raise ValueError("memory signals must not contain duplicates")
    return tuple(sorted(signals, key=_signal_sort_key))


def _signal_sort_key(
    signal: ResearchEquityIndexEventTeamMemorySignal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        signal.memory_readiness_score,
        signal.calibration_note_coverage_ratio,
        signal.unresolved_calibration_note_count,
        signal.latest_evidence_age_seconds,
        signal.evidence_packet_count,
    )


def _memory_readiness_status(
    signal_count: Decimal,
    average_memory_readiness_score: Decimal,
    config: ResearchEquityIndexEventTeamMemoryReportConfig,
) -> str:
    if signal_count == ZERO_COUNT:
        return "block"
    if average_memory_readiness_score >= config.pass_min_memory_readiness_score:
        return "pass"
    if average_memory_readiness_score >= config.watch_min_memory_readiness_score:
        return "watch"
    return "block"


def _calibration_notes_status(
    signal_count: Decimal,
    average_calibration_note_coverage_ratio: Decimal,
    unresolved_calibration_note_count: Decimal,
    config: ResearchEquityIndexEventTeamMemoryReportConfig,
) -> str:
    if signal_count == ZERO_COUNT:
        return "block"
    if (
        average_calibration_note_coverage_ratio
        >= config.pass_min_calibration_note_coverage_ratio
        and unresolved_calibration_note_count
        <= config.watch_max_unresolved_calibration_note_count
    ):
        return "pass"
    if (
        average_calibration_note_coverage_ratio
        < config.watch_min_calibration_note_coverage_ratio
        or unresolved_calibration_note_count
        >= config.block_max_unresolved_calibration_note_count
    ):
        return "block"
    return "watch"


def _evidence_recency_status(
    signal_count: Decimal,
    evidence_packet_count: Decimal,
    max_evidence_age_seconds: Decimal,
    config: ResearchEquityIndexEventTeamMemoryReportConfig,
) -> str:
    if signal_count == ZERO_COUNT or evidence_packet_count == ZERO_COUNT:
        return "block"
    if max_evidence_age_seconds <= config.pass_max_evidence_age_seconds:
        return "pass"
    if max_evidence_age_seconds <= config.watch_max_evidence_age_seconds:
        return "watch"
    return "block"


def _report_status(component_statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in component_statuses):
        return "block"
    if any(status == "watch" for status in component_statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    report_status: str,
    memory_readiness_status: str,
    calibration_notes_status: str,
    evidence_recency_status: str,
) -> tuple[str, ...]:
    return (
        f"equity_index_event_team_memory_report_{report_status}",
        f"memory_readiness_{memory_readiness_status}",
        f"calibration_notes_{calibration_notes_status}",
        f"evidence_recency_{evidence_recency_status}",
    )


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        average = sum(values) / Decimal(len(values))
        return min(ONE_RATIO, max(ZERO_RATIO, average)).quantize(RATIO_QUANT)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_COUNT
    return sum(values, ZERO_COUNT).quantize(COUNT_QUANT)


def _max_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SECONDS
    return max(values).quantize(SECONDS_QUANT)


def _validate_config(
    config: ResearchEquityIndexEventTeamMemoryReportConfig,
) -> None:
    if config.pass_min_memory_readiness_score < config.watch_min_memory_readiness_score:
        raise ValueError(
            "pass_min_memory_readiness_score must not be below "
            "watch_min_memory_readiness_score",
        )
    if (
        config.pass_min_calibration_note_coverage_ratio
        < config.watch_min_calibration_note_coverage_ratio
    ):
        raise ValueError(
            "pass_min_calibration_note_coverage_ratio must not be below "
            "watch_min_calibration_note_coverage_ratio",
        )
    if (
        config.block_max_unresolved_calibration_note_count
        < config.watch_max_unresolved_calibration_note_count
    ):
        raise ValueError(
            "block_max_unresolved_calibration_note_count must not be below "
            "watch_max_unresolved_calibration_note_count",
        )
    if config.watch_max_evidence_age_seconds < config.pass_max_evidence_age_seconds:
        raise ValueError(
            "watch_max_evidence_age_seconds must not be below "
            "pass_max_evidence_age_seconds",
        )


def _validate_report_consistency(
    report: ResearchEquityIndexEventTeamMemoryReport,
) -> None:
    expected_status = _report_status(
        (
            report.memory_readiness_status,
            report.calibration_notes_status,
            report.evidence_recency_status,
        ),
    )
    if report.report_status != expected_status:
        raise ValueError("report_status must match component statuses")
    if report.reason_codes != _report_reason_codes(
        report.report_status,
        report.memory_readiness_status,
        report.calibration_notes_status,
        report.evidence_recency_status,
    ):
        raise ValueError("reason_codes must match report statuses")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(reason_code not in REPORT_REASON_CODES for reason_code in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be >= 0")
    if value > ONE_RATIO:
        raise ValueError(f"{field_name} must be <= 1")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be >= 0")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANT)


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be >= 0")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SECONDS_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _require_payload_flags(value: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_payload_digest(value: dict[str, object]) -> None:
    digest = value.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest must match payload")


def _payload_value(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload public numerics must be Decimal-derived strings")
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
