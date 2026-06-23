from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_research_packet import PaperResearchPacketReport
from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityReport,
)
from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryReport,
)


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION",
    "PaperResearchPacketOperatorFlowConfig",
    "PaperResearchPacketOperatorFlowReport",
    "build_paper_research_packet_operator_flow_report",
)


DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION = (
    "paper-research-packet-operator-flow-v0"
)
FLOW_STATUSES = ("pass", "watch", "blocked")
REASON_CODE_OPERATOR_FLOW_PASSED = "operator_flow_passed"
REASON_CODE_PACKET_NOT_PERSISTED = "packet_not_persisted"
REASON_CODE_QUALITY_NOT_PERSISTED = "quality_not_persisted"
REASON_CODE_PACKET_QUALITY_BLOCKED = "packet_quality_blocked"
REASON_CODE_PACKET_QUALITY_WATCH = "packet_quality_watch"
REASON_CODE_PACKET_QUALITY_HISTORY_BLOCKED = "packet_quality_history_blocked"
REASON_CODE_PACKET_QUALITY_HISTORY_WATCH = "packet_quality_history_watch"


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowConfig:
    config_version: str = DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowReport:
    generated_at: datetime
    config_version: str
    flow_status: str
    packet_generated_at: datetime
    packet_config_version: str
    packet_persisted: bool
    packet_row_count: int
    included_count: int
    skipped_count: int
    quality_generated_at: datetime
    quality_config_version: str
    quality_source_generated_at: datetime
    quality_source_config_version: str
    quality_source_age_seconds: int
    quality_included_share: Decimal | None
    quality_skipped_share: Decimal | None
    quality_persisted: bool
    quality_status: str
    quality_check_count: int
    quality_pass_count: int
    quality_watch_count: int
    quality_blocked_count: int
    history_generated_at: datetime
    history_config_version: str
    history_source_report_count: int
    history_first_source_generated_at: datetime | None
    history_latest_source_generated_at: datetime | None
    history_latest_quality_status: str | None
    history_latest_source_age_seconds: int | None
    history_latest_included_share: Decimal | None
    history_latest_skipped_share: Decimal | None
    history_duplicate_generated_at_count: int
    history_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("flow_status", self.flow_status)
        object.__setattr__(
            self,
            "packet_generated_at",
            _as_utc("packet_generated_at", self.packet_generated_at),
        )
        _require_canonical_string("packet_config_version", self.packet_config_version)
        _require_bool("packet_persisted", self.packet_persisted)
        _require_nonnegative_int("packet_row_count", self.packet_row_count)
        _require_nonnegative_int("included_count", self.included_count)
        _require_nonnegative_int("skipped_count", self.skipped_count)
        object.__setattr__(
            self,
            "quality_generated_at",
            _as_utc("quality_generated_at", self.quality_generated_at),
        )
        _require_canonical_string("quality_config_version", self.quality_config_version)
        object.__setattr__(
            self,
            "quality_source_generated_at",
            _as_utc("quality_source_generated_at", self.quality_source_generated_at),
        )
        _require_canonical_string(
            "quality_source_config_version",
            self.quality_source_config_version,
        )
        _require_nonnegative_int(
            "quality_source_age_seconds",
            self.quality_source_age_seconds,
        )
        object.__setattr__(
            self,
            "quality_included_share",
            _normalize_optional_decimal("quality_included_share", self.quality_included_share),
        )
        object.__setattr__(
            self,
            "quality_skipped_share",
            _normalize_optional_decimal("quality_skipped_share", self.quality_skipped_share),
        )
        _require_bool("quality_persisted", self.quality_persisted)
        _require_status("quality_status", self.quality_status)
        for field_name in (
            "quality_check_count",
            "quality_pass_count",
            "quality_watch_count",
            "quality_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "history_generated_at",
            _as_utc("history_generated_at", self.history_generated_at),
        )
        _require_canonical_string("history_config_version", self.history_config_version)
        _require_nonnegative_int("history_source_report_count", self.history_source_report_count)
        object.__setattr__(
            self,
            "history_first_source_generated_at",
            _normalize_optional_utc(
                "history_first_source_generated_at",
                self.history_first_source_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "history_latest_source_generated_at",
            _normalize_optional_utc(
                "history_latest_source_generated_at",
                self.history_latest_source_generated_at,
            ),
        )
        if self.history_latest_quality_status is not None:
            _require_status("history_latest_quality_status", self.history_latest_quality_status)
        if self.history_latest_source_age_seconds is not None:
            _require_nonnegative_int(
                "history_latest_source_age_seconds",
                self.history_latest_source_age_seconds,
            )
        object.__setattr__(
            self,
            "history_latest_included_share",
            _normalize_optional_decimal(
                "history_latest_included_share",
                self.history_latest_included_share,
            ),
        )
        object.__setattr__(
            self,
            "history_latest_skipped_share",
            _normalize_optional_decimal(
                "history_latest_skipped_share",
                self.history_latest_skipped_share,
            ),
        )
        _require_nonnegative_int(
            "history_duplicate_generated_at_count",
            self.history_duplicate_generated_at_count,
        )
        _require_status("history_status", self.history_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("operator flow report", self)


def build_paper_research_packet_operator_flow_report(
    *,
    packet_report: PaperResearchPacketReport,
    packet_persisted: bool,
    quality_report: PaperResearchPacketQualityReport,
    quality_persisted: bool,
    quality_history_report: PaperResearchPacketQualityHistoryReport,
    config: PaperResearchPacketOperatorFlowConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowReport:
    if type(packet_report) is not PaperResearchPacketReport:
        raise ValueError("packet_report must be a PaperResearchPacketReport")
    if type(quality_report) is not PaperResearchPacketQualityReport:
        raise ValueError("quality_report must be a PaperResearchPacketQualityReport")
    if type(quality_history_report) is not PaperResearchPacketQualityHistoryReport:
        raise ValueError(
            "quality_history_report must be a PaperResearchPacketQualityHistoryReport",
        )
    if type(config) is not PaperResearchPacketOperatorFlowConfig:
        raise ValueError(
            "config must be a PaperResearchPacketOperatorFlowConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("packet report", packet_report)
    _validate_hard_flags("quality report", quality_report)
    _validate_hard_flags("quality history report", quality_history_report)
    _validate_hard_flags("config", config)
    _require_bool("packet_persisted", packet_persisted)
    _require_bool("quality_persisted", quality_persisted)

    generated_at_utc = _as_utc("generated_at", generated_at)
    packet_generated_at = _as_utc("packet_generated_at", packet_report.generated_at)
    quality_generated_at = _as_utc("quality_generated_at", quality_report.generated_at)
    quality_source_generated_at = _as_utc(
        "quality_source_generated_at",
        quality_report.source_generated_at,
    )
    history_generated_at = _as_utc(
        "history_generated_at",
        quality_history_report.generated_at,
    )

    if quality_source_generated_at != packet_generated_at:
        raise ValueError("quality source_generated_at must match packet generated_at")
    if quality_report.source_config_version != packet_report.config_version:
        raise ValueError("quality source_config_version must match packet config_version")
    if quality_report.input_row_count != packet_report.input_row_count:
        raise ValueError("quality input_row_count must match packet input_row_count")
    if quality_report.packet_row_count != packet_report.packet_row_count:
        raise ValueError("quality packet_row_count must match packet packet_row_count")
    if quality_report.included_count != packet_report.included_count:
        raise ValueError("quality included_count must match packet included_count")
    if quality_report.skipped_count != packet_report.skipped_count:
        raise ValueError("quality skipped_count must match packet skipped_count")
    if quality_report.high_priority_count != packet_report.high_priority_count:
        raise ValueError("quality high_priority_count must match packet high_priority_count")
    if quality_report.medium_priority_count != packet_report.medium_priority_count:
        raise ValueError(
            "quality medium_priority_count must match packet medium_priority_count",
        )
    if quality_report.low_priority_count != packet_report.low_priority_count:
        raise ValueError("quality low_priority_count must match packet low_priority_count")
    if quality_report.source_age_seconds != _timedelta_seconds(
        quality_generated_at - quality_source_generated_at,
    ):
        raise ValueError("quality source_age_seconds must match generated_at values")

    expected_quality_check_count = (
        quality_report.pass_count
        + quality_report.watch_count
        + quality_report.blocked_count
    )
    if quality_report.check_count != expected_quality_check_count:
        raise ValueError("quality check_count must match status counts")
    expected_quality_status = _quality_status_from_counts(
        pass_count=quality_report.pass_count,
        watch_count=quality_report.watch_count,
        blocked_count=quality_report.blocked_count,
    )
    if quality_report.quality_status != expected_quality_status:
        raise ValueError("quality status must match status counts")

    if quality_history_report.latest_quality_status is not None and (
        quality_history_report.latest_quality_status != quality_report.quality_status
    ):
        raise ValueError("history latest_quality_status must match quality status")
    if quality_history_report.latest_source_generated_at is not None and (
        quality_history_report.latest_source_generated_at != quality_generated_at
    ):
        raise ValueError("history latest_source_generated_at must match quality generated_at")
    if quality_history_report.latest_source_age_seconds is not None and (
        quality_history_report.latest_source_age_seconds
        != quality_report.source_age_seconds
    ):
        raise ValueError("history latest_source_age_seconds must match quality source_age_seconds")
    if quality_history_report.latest_included_share is not None and (
        quality_history_report.latest_included_share != quality_report.included_share
    ):
        raise ValueError("history latest_included_share must match quality included_share")
    if quality_history_report.latest_skipped_share is not None and (
        quality_history_report.latest_skipped_share != quality_report.skipped_share
    ):
        raise ValueError("history latest_skipped_share must match quality skipped_share")
    if quality_history_report.source_report_count > 0:
        if quality_history_report.first_source_generated_at is None:
            raise ValueError("history first_source_generated_at must not be absent")
        if quality_history_report.latest_source_generated_at is None:
            raise ValueError("history latest_source_generated_at must not be absent")
        if quality_history_report.first_source_generated_at > quality_history_report.latest_source_generated_at:
            raise ValueError("history source bounds must be chronological")
    if quality_history_report.history_status not in FLOW_STATUSES:
        raise ValueError("history_status must be pass, watch, or blocked")
    if packet_generated_at > quality_generated_at:
        raise ValueError("packet generated_at must not be after quality generated_at")
    if quality_generated_at > history_generated_at:
        raise ValueError("quality generated_at must not be after history generated_at")
    if history_generated_at > generated_at_utc:
        raise ValueError("history generated_at must not be after generated_at")

    reason_codes = _reason_codes(
        packet_persisted=packet_persisted,
        quality_persisted=quality_persisted,
        quality_status=quality_report.quality_status,
        history_status=quality_history_report.history_status,
    )

    flow_status = _flow_status(
        packet_persisted=packet_persisted,
        quality_persisted=quality_persisted,
        quality_status=quality_report.quality_status,
        history_status=quality_history_report.history_status,
    )

    return PaperResearchPacketOperatorFlowReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        flow_status=flow_status,
        packet_generated_at=packet_generated_at,
        packet_config_version=packet_report.config_version,
        packet_persisted=packet_persisted,
        packet_row_count=packet_report.packet_row_count,
        included_count=packet_report.included_count,
        skipped_count=packet_report.skipped_count,
        quality_generated_at=quality_generated_at,
        quality_config_version=quality_report.config_version,
        quality_source_generated_at=quality_source_generated_at,
        quality_source_config_version=quality_report.source_config_version,
        quality_source_age_seconds=quality_report.source_age_seconds,
        quality_included_share=quality_report.included_share,
        quality_skipped_share=quality_report.skipped_share,
        quality_persisted=quality_persisted,
        quality_status=quality_report.quality_status,
        quality_check_count=quality_report.check_count,
        quality_pass_count=quality_report.pass_count,
        quality_watch_count=quality_report.watch_count,
        quality_blocked_count=quality_report.blocked_count,
        history_generated_at=history_generated_at,
        history_config_version=quality_history_report.config_version,
        history_source_report_count=quality_history_report.source_report_count,
        history_first_source_generated_at=quality_history_report.first_source_generated_at,
        history_latest_source_generated_at=quality_history_report.latest_source_generated_at,
        history_latest_quality_status=quality_history_report.latest_quality_status,
        history_latest_source_age_seconds=quality_history_report.latest_source_age_seconds,
        history_latest_included_share=quality_history_report.latest_included_share,
        history_latest_skipped_share=quality_history_report.latest_skipped_share,
        history_duplicate_generated_at_count=quality_history_report.duplicate_generated_at_count,
        history_status=quality_history_report.history_status,
        reason_codes=reason_codes,
    )


def _flow_status(
    *,
    packet_persisted: bool,
    quality_persisted: bool,
    quality_status: str,
    history_status: str,
) -> str:
    if (
        not packet_persisted
        or not quality_persisted
        or quality_status == "blocked"
        or history_status == "blocked"
    ):
        return "blocked"
    if quality_status == "watch" or history_status == "watch":
        return "watch"
    return "pass"


def _quality_status_from_counts(
    *,
    pass_count: int,
    watch_count: int,
    blocked_count: int,
) -> str:
    if blocked_count > 0:
        return "blocked"
    if watch_count > 0:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    packet_persisted: bool,
    quality_persisted: bool,
    quality_status: str,
    history_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not packet_persisted:
        reason_codes.append(REASON_CODE_PACKET_NOT_PERSISTED)
    if not quality_persisted:
        reason_codes.append(REASON_CODE_QUALITY_NOT_PERSISTED)
    if quality_status == "blocked":
        reason_codes.append(REASON_CODE_PACKET_QUALITY_BLOCKED)
    elif quality_status == "watch":
        reason_codes.append(REASON_CODE_PACKET_QUALITY_WATCH)
    if history_status == "blocked":
        reason_codes.append(REASON_CODE_PACKET_QUALITY_HISTORY_BLOCKED)
    elif history_status == "watch":
        reason_codes.append(REASON_CODE_PACKET_QUALITY_HISTORY_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_CODE_OPERATOR_FLOW_PASSED)
    return tuple(sorted(reason_codes))


def _validate_report_consistency(report: PaperResearchPacketOperatorFlowReport) -> None:
    if report.packet_row_count != report.included_count + report.skipped_count:
        raise ValueError("packet_row_count must match included_count and skipped_count")
    if report.quality_source_generated_at != report.packet_generated_at:
        raise ValueError("quality source_generated_at must match packet generated_at")
    if report.quality_source_config_version != report.packet_config_version:
        raise ValueError("quality source_config_version must match packet config_version")
    if report.quality_source_age_seconds != _timedelta_seconds(
        report.quality_generated_at - report.quality_source_generated_at,
    ):
        raise ValueError("quality source_age_seconds must match generated_at values")
    if report.packet_generated_at > report.quality_generated_at:
        raise ValueError("packet generated_at must not be after quality generated_at")
    if report.quality_generated_at > report.history_generated_at:
        raise ValueError("quality generated_at must not be after history generated_at")
    if report.history_generated_at > report.generated_at:
        raise ValueError("history generated_at must not be after generated_at")
    if report.quality_check_count != (
        report.quality_pass_count + report.quality_watch_count + report.quality_blocked_count
    ):
        raise ValueError("quality_check_count must match status counts")
    if report.quality_status != _quality_status_from_counts(
        pass_count=report.quality_pass_count,
        watch_count=report.quality_watch_count,
        blocked_count=report.quality_blocked_count,
    ):
        raise ValueError("quality_status must match status counts")
    if report.history_source_report_count == 0:
        if report.history_first_source_generated_at is not None:
            raise ValueError("history_first_source_generated_at must be absent")
        if report.history_latest_source_generated_at is not None:
            raise ValueError("history_latest_source_generated_at must be absent")
        if report.history_latest_quality_status is not None:
            raise ValueError("history_latest_quality_status must be absent")
        if report.history_latest_source_age_seconds is not None:
            raise ValueError("history_latest_source_age_seconds must be absent")
        if report.history_latest_included_share is not None:
            raise ValueError("history_latest_included_share must be absent")
        if report.history_latest_skipped_share is not None:
            raise ValueError("history_latest_skipped_share must be absent")
    else:
        if report.history_first_source_generated_at is None:
            raise ValueError("history_first_source_generated_at must not be absent")
        if report.history_latest_source_generated_at is None:
            raise ValueError("history_latest_source_generated_at must not be absent")
        if report.history_latest_quality_status is None:
            raise ValueError("history_latest_quality_status must not be absent")
        if report.history_latest_source_age_seconds is None:
            raise ValueError("history_latest_source_age_seconds must not be absent")
        if report.history_latest_included_share is None:
            raise ValueError("history_latest_included_share must not be absent")
        if report.history_latest_skipped_share is None:
            raise ValueError("history_latest_skipped_share must not be absent")
        if report.history_first_source_generated_at > report.history_latest_source_generated_at:
            raise ValueError("history source bounds must be chronological")
        if report.history_latest_source_generated_at != report.quality_generated_at:
            raise ValueError("history latest_source_generated_at must match quality generated_at")
        if report.history_latest_quality_status != report.quality_status:
            raise ValueError("history latest_quality_status must match quality status")
        if report.history_latest_source_age_seconds != report.quality_source_age_seconds:
            raise ValueError("history latest_source_age_seconds must match quality source_age_seconds")
        if report.history_latest_included_share != report.quality_included_share:
            raise ValueError("history latest_included_share must match quality included_share")
        if report.history_latest_skipped_share != report.quality_skipped_share:
            raise ValueError("history latest_skipped_share must match quality skipped_share")
    if report.flow_status != _flow_status(
        packet_persisted=report.packet_persisted,
        quality_persisted=report.quality_persisted,
        quality_status=report.quality_status,
        history_status=report.history_status,
    ):
        raise ValueError("flow_status must match reason_codes")
    if report.reason_codes != _reason_codes(
        packet_persisted=report.packet_persisted,
        quality_persisted=report.quality_persisted,
        quality_status=report.quality_status,
        history_status=report.history_status,
    ):
        raise ValueError("reason_codes must be deterministic")


def _normalize_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_optional_decimal(field_name: str, value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen.add(reason_code)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _timedelta_seconds(value: timedelta) -> int:
    if value < timedelta(0):
        raise ValueError("generated_at values must be chronological")
    return value.days * 86_400 + value.seconds


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FLOW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _validate_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
