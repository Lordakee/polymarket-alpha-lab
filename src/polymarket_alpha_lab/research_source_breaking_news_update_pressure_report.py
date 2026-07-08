"""Pure report-only breaking news source update pressure report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_BREAKING_NEWS_UPDATE_PRESSURE_CONFIG_VERSION = (
    "research-source-breaking-news-update-pressure-report-v0"
)

BREAKING_NEWS_UPDATE_PRESSURE_STATUSES = ("pass", "watch", "block")
NO_INPUT_REASON_CODE = "breaking_news_update_pressure_no_inputs"
REASON_CODES = (
    NO_INPUT_REASON_CODE,
    "update_age_pass",
    "update_age_watch",
    "update_age_block",
    "corroboration_gap_pass",
    "corroboration_gap_watch",
    "corroboration_gap_block",
    "contradiction_pressure_pass",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "source_family_diversity_pass",
    "source_family_diversity_watch",
    "source_family_diversity_block",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR_CHECKS = Decimal("4.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "://",
        "www.",
        "candidate",
        "condition_id",
        "database",
        "dsn",
        "market_id",
        "market_slug",
        "private_key",
        "question",
        "raw",
        "recommendation",
        "slug",
        "source_id",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "order",
    ),
)

__all__ = (
    "BREAKING_NEWS_UPDATE_PRESSURE_STATUSES",
    "DEFAULT_RESEARCH_SOURCE_BREAKING_NEWS_UPDATE_PRESSURE_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchSourceBreakingNewsUpdatePressureConfig",
    "ResearchSourceBreakingNewsUpdatePressureObservation",
    "ResearchSourceBreakingNewsUpdatePressureReasonCodeCount",
    "ResearchSourceBreakingNewsUpdatePressureReport",
    "build_research_source_breaking_news_update_pressure_report",
    "research_source_breaking_news_update_pressure_report_digest",
    "research_source_breaking_news_update_pressure_report_payload",
    "validate_research_source_breaking_news_update_pressure_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceBreakingNewsUpdatePressureConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_BREAKING_NEWS_UPDATE_PRESSURE_CONFIG_VERSION
    )
    max_pass_update_age_seconds: Decimal = Decimal("900.000000")
    max_watch_update_age_seconds: Decimal = Decimal("3600.000000")
    max_pass_corroboration_gap_ratio: Decimal = Decimal("0.250000")
    max_watch_corroboration_gap_ratio: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure_ratio: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure_ratio: Decimal = Decimal("0.400000")
    min_pass_source_family_count: Decimal = Decimal("3.000000")
    min_watch_source_family_count: Decimal = Decimal("2.000000")
    min_pass_source_family_diversity_ratio: Decimal = Decimal("0.750000")
    min_watch_source_family_diversity_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceBreakingNewsUpdatePressureConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceBreakingNewsUpdatePressureConfig:
            raise ValueError(
                "config must be a ResearchSourceBreakingNewsUpdatePressureConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_BREAKING_NEWS_UPDATE_PRESSURE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_update_age_seconds",
            "max_watch_update_age_seconds",
            "min_pass_source_family_count",
            "min_watch_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_corroboration_gap_ratio",
            "max_watch_corroboration_gap_ratio",
            "max_pass_contradiction_pressure_ratio",
            "max_watch_contradiction_pressure_ratio",
            "min_pass_source_family_diversity_ratio",
            "min_watch_source_family_diversity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.max_pass_update_age_seconds > self.max_watch_update_age_seconds:
            raise ValueError("pass update age threshold cannot exceed watch threshold")
        if (
            self.max_pass_corroboration_gap_ratio
            > self.max_watch_corroboration_gap_ratio
        ):
            raise ValueError(
                "pass corroboration gap threshold cannot exceed watch threshold",
            )
        if (
            self.max_pass_contradiction_pressure_ratio
            > self.max_watch_contradiction_pressure_ratio
        ):
            raise ValueError(
                "pass contradiction pressure threshold cannot exceed watch threshold",
            )
        if self.min_watch_source_family_count > self.min_pass_source_family_count:
            raise ValueError(
                "watch source family count threshold cannot exceed pass threshold",
            )
        if (
            self.min_watch_source_family_diversity_ratio
            > self.min_pass_source_family_diversity_ratio
        ):
            raise ValueError(
                "watch source family diversity threshold cannot exceed pass threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceBreakingNewsUpdatePressureObservation:
    source_family: str
    observed_at: datetime
    corroborating_update_count: Decimal
    required_corroborating_update_count: Decimal
    contradiction_count: Decimal
    checked_claim_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceBreakingNewsUpdatePressureObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceBreakingNewsUpdatePressureObservation:
            raise ValueError(
                "observation must be a ResearchSourceBreakingNewsUpdatePressureObservation",
            )
        _require_public_label("source_family", self.source_family)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "corroborating_update_count",
            "required_corroborating_update_count",
            "contradiction_count",
            "checked_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_corroborating_update_count == ZERO:
            raise ValueError("required_corroborating_update_count must be positive")
        if self.checked_claim_count == ZERO and self.contradiction_count != ZERO:
            raise ValueError(
                "contradiction_count requires a positive checked_claim_count",
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceBreakingNewsUpdatePressureReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceBreakingNewsUpdatePressureReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceBreakingNewsUpdatePressureReasonCodeCount:
            raise ValueError(
                "reason code count must be a ResearchSourceBreakingNewsUpdatePressureReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceBreakingNewsUpdatePressureReport:
    generated_at: datetime
    config_version: str
    status: str
    update_count: Decimal
    source_family_count: Decimal
    latest_update_age_seconds: Decimal
    average_update_age_seconds: Decimal
    corroborating_update_count: Decimal
    required_corroborating_update_count: Decimal
    corroboration_gap_ratio: Decimal
    contradiction_count: Decimal
    checked_claim_count: Decimal
    contradiction_pressure_ratio: Decimal
    source_family_diversity_ratio: Decimal
    check_count: Decimal
    passed_check_count: Decimal
    watch_check_count: Decimal
    blocked_check_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceBreakingNewsUpdatePressureReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceBreakingNewsUpdatePressureReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceBreakingNewsUpdatePressureReport:
            raise ValueError(
                "report must be a ResearchSourceBreakingNewsUpdatePressureReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_BREAKING_NEWS_UPDATE_PRESSURE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "update_count",
            "source_family_count",
            "latest_update_age_seconds",
            "average_update_age_seconds",
            "corroborating_update_count",
            "required_corroborating_update_count",
            "contradiction_count",
            "checked_claim_count",
            "check_count",
            "passed_check_count",
            "watch_check_count",
            "blocked_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroboration_gap_ratio",
            "contradiction_pressure_ratio",
            "source_family_diversity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_breaking_news_update_pressure_report_payload(self)


def build_research_source_breaking_news_update_pressure_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceBreakingNewsUpdatePressureConfig | None = None,
) -> ResearchSourceBreakingNewsUpdatePressureReport:
    """Build a deterministic aggregate report for fast-moving evidence pressure."""

    if config is None:
        config = ResearchSourceBreakingNewsUpdatePressureConfig()
    if type(config) is not ResearchSourceBreakingNewsUpdatePressureConfig:
        raise ValueError(
            "config must be a ResearchSourceBreakingNewsUpdatePressureConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_future_observations(normalized, generated_at_utc)
    if not normalized:
        return ResearchSourceBreakingNewsUpdatePressureReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            status="pass",
            update_count=ZERO,
            source_family_count=ZERO,
            latest_update_age_seconds=ZERO,
            average_update_age_seconds=ZERO,
            corroborating_update_count=ZERO,
            required_corroborating_update_count=ZERO,
            corroboration_gap_ratio=ZERO,
            contradiction_count=ZERO,
            checked_claim_count=ZERO,
            contradiction_pressure_ratio=ZERO,
            source_family_diversity_ratio=ZERO,
            check_count=ZERO,
            passed_check_count=ZERO,
            watch_check_count=ZERO,
            blocked_check_count=ZERO,
            reason_codes=(NO_INPUT_REASON_CODE,),
            reason_code_counts=(),
        )

    update_count = _count(len(normalized))
    source_family_count = _count(len({value.source_family for value in normalized}))
    latest_observed_at = max(value.observed_at for value in normalized)
    latest_update_age_seconds = _datetime_delta_seconds(
        generated_at_utc,
        latest_observed_at,
    )
    average_update_age_seconds = _average_decimal(
        _datetime_delta_seconds(generated_at_utc, value.observed_at)
        for value in normalized
    )
    corroborating_update_count = _sum_decimal(
        value.corroborating_update_count for value in normalized
    )
    required_corroborating_update_count = _sum_decimal(
        value.required_corroborating_update_count for value in normalized
    )
    contradiction_count = _sum_decimal(value.contradiction_count for value in normalized)
    checked_claim_count = _sum_decimal(value.checked_claim_count for value in normalized)
    corroboration_gap_ratio = _clamped_ratio(
        ONE - _ratio(corroborating_update_count, required_corroborating_update_count),
    )
    contradiction_pressure_ratio = _ratio(contradiction_count, checked_claim_count)
    source_family_diversity_ratio = _ratio(source_family_count, update_count)
    check_statuses = (
        _maximum_status(
            latest_update_age_seconds,
            pass_threshold=config.max_pass_update_age_seconds,
            watch_threshold=config.max_watch_update_age_seconds,
        ),
        _maximum_status(
            corroboration_gap_ratio,
            pass_threshold=config.max_pass_corroboration_gap_ratio,
            watch_threshold=config.max_watch_corroboration_gap_ratio,
        ),
        _maximum_status(
            contradiction_pressure_ratio,
            pass_threshold=config.max_pass_contradiction_pressure_ratio,
            watch_threshold=config.max_watch_contradiction_pressure_ratio,
        ),
        _source_family_diversity_status(
            source_family_count=source_family_count,
            source_family_diversity_ratio=source_family_diversity_ratio,
            config=config,
        ),
    )
    reason_codes = (
        f"update_age_{check_statuses[0]}",
        f"corroboration_gap_{check_statuses[1]}",
        f"contradiction_pressure_{check_statuses[2]}",
        f"source_family_diversity_{check_statuses[3]}",
    )
    return ResearchSourceBreakingNewsUpdatePressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_overall_status(check_statuses),
        update_count=update_count,
        source_family_count=source_family_count,
        latest_update_age_seconds=latest_update_age_seconds,
        average_update_age_seconds=average_update_age_seconds,
        corroborating_update_count=corroborating_update_count,
        required_corroborating_update_count=required_corroborating_update_count,
        corroboration_gap_ratio=corroboration_gap_ratio,
        contradiction_count=contradiction_count,
        checked_claim_count=checked_claim_count,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        source_family_diversity_ratio=source_family_diversity_ratio,
        check_count=FOUR_CHECKS,
        passed_check_count=_status_count(check_statuses, "pass"),
        watch_check_count=_status_count(check_statuses, "watch"),
        blocked_check_count=_status_count(check_statuses, "block"),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
    )


def research_source_breaking_news_update_pressure_report_payload(
    report: ResearchSourceBreakingNewsUpdatePressureReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceBreakingNewsUpdatePressureReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_unsafe_public_payload("payload", report, allow_mapping=True)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchSourceBreakingNewsUpdatePressureReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
    return payload


def research_source_breaking_news_update_pressure_report_digest(
    report: ResearchSourceBreakingNewsUpdatePressureReport,
) -> str:
    if type(report) is not ResearchSourceBreakingNewsUpdatePressureReport:
        raise ValueError(
            "report must be a ResearchSourceBreakingNewsUpdatePressureReport",
        )
    _require_hard_flags("report", report)
    digest = _report_derived_validation_digest(report)
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_source_breaking_news_update_pressure_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _require_payload_hard_flags(payload)
        _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str:
            return False
        _require_sha256_digest("derived_validation_digest", digest)
        unsigned_payload = dict(payload)
        unsigned_payload.pop("derived_validation_digest", None)
        if digest != _payload_digest(unsigned_payload):
            return False
        status = payload.get("status")
        if status not in BREAKING_NEWS_UPDATE_PRESSURE_STATUSES:
            return False
        reason_codes = payload.get("reason_codes")
        if type(reason_codes) is not list:
            return False
        if tuple(reason_codes) != _normalize_reason_codes(tuple(reason_codes)):
            return False
        for field_name in (
            "update_count",
            "source_family_count",
            "latest_update_age_seconds",
            "average_update_age_seconds",
            "corroboration_gap_ratio",
            "contradiction_pressure_ratio",
            "source_family_diversity_ratio",
            "check_count",
            "passed_check_count",
            "watch_check_count",
            "blocked_check_count",
        ):
            if type(payload.get(field_name)) is not str:
                return False
        return True
    except (TypeError, ValueError):
        return False


def _source_family_diversity_status(
    *,
    source_family_count: Decimal,
    source_family_diversity_ratio: Decimal,
    config: ResearchSourceBreakingNewsUpdatePressureConfig,
) -> str:
    count_status = _minimum_status(
        source_family_count,
        pass_threshold=config.min_pass_source_family_count,
        watch_threshold=config.min_watch_source_family_count,
    )
    ratio_status = _minimum_status(
        source_family_diversity_ratio,
        pass_threshold=config.min_pass_source_family_diversity_ratio,
        watch_threshold=config.min_watch_source_family_diversity_ratio,
    )
    return _overall_status((count_status, ratio_status))


def _minimum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return "pass"
    if value >= watch_threshold:
        return "watch"
    return "block"


def _maximum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "pass"
    if value <= watch_threshold:
        return "watch"
    return "block"


def _overall_status(statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    for status in values:
        _require_status("status", status)
    if "block" in values:
        return "block"
    if "watch" in values:
        return "watch"
    return "pass"


def _status_count(statuses: Iterable[str], target: str) -> Decimal:
    _require_status("target", target)
    return _count(sum(1 for status in statuses if status == target))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceBreakingNewsUpdatePressureReasonCodeCount, ...]:
    if reason_codes == (NO_INPUT_REASON_CODE,):
        return ()
    return tuple(
        ResearchSourceBreakingNewsUpdatePressureReasonCodeCount(
            reason_code=reason_code,
            count=ONE,
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchSourceBreakingNewsUpdatePressureObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceBreakingNewsUpdatePressureObservation] = []
    for value in values:
        if type(value) is not ResearchSourceBreakingNewsUpdatePressureObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceBreakingNewsUpdatePressureObservation values",
            )
        _require_hard_flags("observation", value)
        normalized.append(value)
    return tuple(
        sorted(
            normalized,
            key=lambda value: (
                value.observed_at,
                value.source_family,
                value.corroborating_update_count,
                value.required_corroborating_update_count,
                value.contradiction_count,
                value.checked_claim_count,
            ),
        ),
    )


def _reject_future_observations(
    observations: tuple[ResearchSourceBreakingNewsUpdatePressureObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _validate_report(report: ResearchSourceBreakingNewsUpdatePressureReport) -> None:
    if report.update_count == ZERO:
        if report.status != "pass":
            raise ValueError("empty report status must be pass")
        if report.check_count != ZERO:
            raise ValueError("empty report check_count must be zero")
        if report.reason_codes != (NO_INPUT_REASON_CODE,):
            raise ValueError("empty report reason_codes must use no-input reason")
        if report.reason_code_counts != ():
            raise ValueError("empty report reason_code_counts must be empty")
    else:
        if report.check_count != FOUR_CHECKS:
            raise ValueError("check_count must equal four pressure checks")
        if (
            report.passed_check_count
            + report.watch_check_count
            + report.blocked_check_count
            != report.check_count
        ):
            raise ValueError("check counts must sum to check_count")
        if report.status != _overall_status(
            _reason_code_status(reason_code) for reason_code in report.reason_codes
        ):
            raise ValueError("status must match reason_codes")
        if report.reason_code_counts != _reason_code_counts(report.reason_codes):
            raise ValueError("reason_code_counts must match reason_codes")
    if report.source_family_count > report.update_count:
        raise ValueError("source_family_count cannot exceed update_count")
    if report.corroborating_update_count > report.required_corroborating_update_count:
        raise ValueError(
            "corroborating_update_count cannot exceed "
            "required_corroborating_update_count",
        )
    if report.contradiction_count > report.checked_claim_count:
        raise ValueError("contradiction_count cannot exceed checked_claim_count")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")


def _reason_code_status(reason_code: str) -> str:
    if reason_code == NO_INPUT_REASON_CODE:
        return "pass"
    status = reason_code.rsplit("_", 1)[-1]
    _require_status("reason_code status", status)
    return status


def _report_payload(
    report: ResearchSourceBreakingNewsUpdatePressureReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "update_count": _payload_value(report.update_count),
        "source_family_count": _payload_value(report.source_family_count),
        "latest_update_age_seconds": _payload_value(
            report.latest_update_age_seconds,
        ),
        "average_update_age_seconds": _payload_value(
            report.average_update_age_seconds,
        ),
        "corroborating_update_count": _payload_value(
            report.corroborating_update_count,
        ),
        "required_corroborating_update_count": _payload_value(
            report.required_corroborating_update_count,
        ),
        "corroboration_gap_ratio": _payload_value(report.corroboration_gap_ratio),
        "contradiction_count": _payload_value(report.contradiction_count),
        "checked_claim_count": _payload_value(report.checked_claim_count),
        "contradiction_pressure_ratio": _payload_value(
            report.contradiction_pressure_ratio,
        ),
        "source_family_diversity_ratio": _payload_value(
            report.source_family_diversity_ratio,
        ),
        "check_count": _payload_value(report.check_count),
        "passed_check_count": _payload_value(report.passed_check_count),
        "watch_check_count": _payload_value(report.watch_check_count),
        "blocked_check_count": _payload_value(report.blocked_check_count),
        "reason_codes": _payload_value(report.reason_codes),
        "reason_code_counts": _payload_value(report.reason_code_counts),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _reason_code_count_payload(
    row: ResearchSourceBreakingNewsUpdatePressureReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _payload_value(row.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is ResearchSourceBreakingNewsUpdatePressureReasonCodeCount:
        return _reason_code_count_payload(value)
    if type(value) is ResearchSourceBreakingNewsUpdatePressureReport:
        return _report_payload(value, include_digest=True)
    if isinstance(value, Mapping):
        return {key: _payload_value(item) for key, item in sorted(value.items())}
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _report_derived_validation_digest(
    report: ResearchSourceBreakingNewsUpdatePressureReport,
) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(normalized, ZERO) / Decimal(len(normalized)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize_decimal(sum(values, ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(numerator / denominator)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECOND_DIVISOR)
    )
    return _normalize_nonnegative_decimal("datetime_delta_seconds", seconds)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("decimal values must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    _reject_unsafe_public_string(field_name, value)


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    assert type(value) is str
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a sanitized public label")
    if not value[0].isalpha():
        raise ValueError(f"{field_name} must start with a letter")


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in BREAKING_NEWS_UPDATE_PRESSURE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain a supported reason code")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    values = tuple(value)
    if not values:
        raise ValueError("reason_codes must be non-empty")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in values)
    if values != expected:
        raise ValueError("reason_codes must be deterministically sorted")
    if values == (NO_INPUT_REASON_CODE,):
        return values
    check_prefixes = (
        "update_age_",
        "corroboration_gap_",
        "contradiction_pressure_",
        "source_family_diversity_",
    )
    if tuple(reason_code.rsplit("_", 1)[0] + "_" for reason_code in values) != check_prefixes:
        raise ValueError("reason_codes must cover each pressure check once")
    return values


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchSourceBreakingNewsUpdatePressureReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchSourceBreakingNewsUpdatePressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceBreakingNewsUpdatePressureReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
    expected = tuple(
        sorted(values, key=lambda row: REASON_CODES.index(row.reason_code)),
    )
    if values != expected:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _reject_unsafe_public_payload(
    context: str,
    value: object,
    *,
    allow_mapping: bool = False,
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
            _reject_unsafe_public_string(f"{context} key", field_name)
            _reject_unsafe_public_payload(
                f"{context}.{field_name}",
                getattr(value, field_name),
            )
        return
    if isinstance(value, Mapping):
        if not allow_mapping:
            raise ValueError(f"{context} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} payload keys must be strings")
            _reject_unsafe_public_string(f"{context} key", key)
            _reject_unsafe_public_payload(
                f"{context}.{key}",
                item,
                allow_mapping=True,
            )
        return
    if type(value) is tuple or type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(
                context,
                item,
                allow_mapping=allow_mapping,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(context, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{context} Decimal value must be finite")
        return
    if type(value) is datetime:
        _as_utc("datetime payload value", value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{context} numeric value must use Decimal strings")
    raise ValueError(f"{context} contains unsupported public payload value")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{context} must expose {field_name}")
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = payload.get(field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value
