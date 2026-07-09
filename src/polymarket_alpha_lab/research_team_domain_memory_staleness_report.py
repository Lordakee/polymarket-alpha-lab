"""Public report-only audit of domain team memory staleness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_STALENESS_REPORT_CONFIG_VERSION = (
    "research-team-domain-memory-staleness-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
PUBLIC_STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

PUBLIC_DOMAIN_CATEGORIES = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)

MISSING_DOMAIN_MEMORY_REASON = (
    "research_team_domain_memory_staleness_missing_domain_memory"
)
BLOCK_STALE_MEMORY_REASON = (
    "research_team_domain_memory_staleness_block_stale_memory"
)
STALE_MEMORY_REASON = "research_team_domain_memory_staleness_stale_memory"
BLOCK_MEMORY_COVERAGE_REASON = (
    "research_team_domain_memory_staleness_block_memory_coverage"
)
LOW_MEMORY_COVERAGE_REASON = (
    "research_team_domain_memory_staleness_low_memory_coverage"
)
BLOCK_UNDER_CALIBRATED_REASON = (
    "research_team_domain_memory_staleness_block_under_calibrated"
)
UNDER_CALIBRATED_REASON = (
    "research_team_domain_memory_staleness_under_calibrated"
)
MISSING_RECENT_OUTCOME_FEEDBACK_REASON = (
    "research_team_domain_memory_staleness_missing_recent_outcome_feedback"
)
HEALTHY_MEMORY_REASON = "research_team_domain_memory_staleness_healthy_memory"

REPORT_NO_INPUTS_REASON = "research_team_domain_memory_staleness_report_no_inputs"
REPORT_BLOCK_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_block_present"
)
REPORT_WATCH_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_watch_present"
)
REPORT_MISSING_DOMAIN_MEMORY_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_missing_domain_memory_present"
)
REPORT_STALE_MEMORY_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_stale_memory_present"
)
REPORT_UNDER_CALIBRATED_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_under_calibrated_present"
)
REPORT_MISSING_OUTCOME_FEEDBACK_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_missing_outcome_feedback_present"
)
REPORT_HEALTHY_MEMORY_PRESENT_REASON = (
    "research_team_domain_memory_staleness_report_healthy_memory_present"
)

ROW_REASON_CODE_SEQUENCE = (
    MISSING_DOMAIN_MEMORY_REASON,
    BLOCK_STALE_MEMORY_REASON,
    STALE_MEMORY_REASON,
    BLOCK_MEMORY_COVERAGE_REASON,
    LOW_MEMORY_COVERAGE_REASON,
    BLOCK_UNDER_CALIBRATED_REASON,
    UNDER_CALIBRATED_REASON,
    MISSING_RECENT_OUTCOME_FEEDBACK_REASON,
    HEALTHY_MEMORY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    REPORT_NO_INPUTS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_MISSING_DOMAIN_MEMORY_PRESENT_REASON,
    REPORT_STALE_MEMORY_PRESENT_REASON,
    REPORT_UNDER_CALIBRATED_PRESENT_REASON,
    REPORT_MISSING_OUTCOME_FEEDBACK_PRESENT_REASON,
    REPORT_HEALTHY_MEMORY_PRESENT_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
        "position",
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("reco", "mmend"),
        "advice",
        "private",
        "account",
        "balance",
        "broker",
        "clob",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_STALENESS_REPORT_CONFIG_VERSION",
    "PUBLIC_DOMAIN_CATEGORIES",
    "PUBLIC_STATUSES",
    "ResearchTeamDomainMemoryStalenessConfig",
    "ResearchTeamDomainMemoryStalenessObservation",
    "ResearchTeamDomainMemoryStalenessRow",
    "ResearchTeamDomainMemoryStalenessReport",
    "build_research_team_domain_memory_staleness_report",
    "research_team_domain_memory_staleness_report_payload",
    "research_team_domain_memory_staleness_report_digest",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamDomainMemoryStalenessConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_STALENESS_REPORT_CONFIG_VERSION
    )
    stale_after_seconds: Decimal = Decimal("7776000.000000")
    block_stale_after_seconds: Decimal = Decimal("15552000.000000")
    stale_outcome_feedback_after_seconds: Decimal = Decimal("3888000.000000")
    min_recent_outcome_feedback_count: Decimal = Decimal("2.000000")
    min_pass_memory_coverage_ratio: Decimal = Decimal("0.700000")
    min_watch_memory_coverage_ratio: Decimal = Decimal("0.400000")
    min_pass_calibration_score: Decimal = Decimal("0.700000")
    min_watch_calibration_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainMemoryStalenessConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "stale_after_seconds",
            "block_stale_after_seconds",
            "stale_outcome_feedback_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "min_recent_outcome_feedback_count",
            _require_nonnegative_integral_decimal(
                "min_recent_outcome_feedback_count",
                self.min_recent_outcome_feedback_count,
            ),
        )
        for field_name in (
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
            "min_pass_calibration_score",
            "min_watch_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_after_seconds > self.block_stale_after_seconds:
            raise ValueError("stale_after_seconds must not exceed block threshold")
        if self.min_watch_memory_coverage_ratio > self.min_pass_memory_coverage_ratio:
            raise ValueError(
                "min_watch_memory_coverage_ratio must not exceed pass threshold",
            )
        if self.min_watch_calibration_score > self.min_pass_calibration_score:
            raise ValueError(
                "min_watch_calibration_score must not exceed pass threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryStalenessObservation(_FinalPublicDataclass):
    domain_category: str
    team_key: str
    memory_updated_at: datetime
    last_outcome_feedback_at: datetime | None
    memory_coverage_ratio: Decimal
    calibration_score: Decimal
    settled_outcome_count: Decimal
    recent_outcome_feedback_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemoryStalenessObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "domain_category",
            _require_public_category("domain_category", self.domain_category),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_string("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "memory_updated_at",
            _as_utc("memory_updated_at", self.memory_updated_at),
        )
        object.__setattr__(
            self,
            "last_outcome_feedback_at",
            _optional_utc("last_outcome_feedback_at", self.last_outcome_feedback_at),
        )
        for field_name in ("memory_coverage_ratio", "calibration_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("settled_outcome_count", "recent_outcome_feedback_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.recent_outcome_feedback_count > self.settled_outcome_count:
            raise ValueError(
                "recent_outcome_feedback_count must not exceed settled_outcome_count",
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryStalenessRow(_FinalPublicDataclass):
    domain_category: str
    public_status: str
    team_count: Decimal
    memory_coverage_ratio: Decimal
    average_calibration_score: Decimal
    settled_outcome_count: Decimal
    recent_outcome_feedback_count: Decimal
    newest_memory_age_seconds: Decimal | None
    oldest_memory_age_seconds: Decimal | None
    newest_outcome_feedback_age_seconds: Decimal | None
    oldest_outcome_feedback_age_seconds: Decimal | None
    stale_team_count: Decimal
    under_calibrated_team_count: Decimal
    missing_recent_outcome_feedback_team_count: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainMemoryStalenessRow, "row")
        object.__setattr__(
            self,
            "domain_category",
            _require_public_category("domain_category", self.domain_category),
        )
        object.__setattr__(self, "public_status", _require_status(self.public_status))
        for field_name in (
            "team_count",
            "settled_outcome_count",
            "recent_outcome_feedback_count",
            "stale_team_count",
            "under_calibrated_team_count",
            "missing_recent_outcome_feedback_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("memory_coverage_ratio", "average_calibration_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_memory_age_seconds",
            "oldest_memory_age_seconds",
            "newest_outcome_feedback_age_seconds",
            "oldest_outcome_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(self),
            ),
        )


@dataclass(frozen=True)
class ResearchTeamDomainMemoryStalenessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    category_count: Decimal
    observed_category_count: Decimal
    missing_category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_category_count: Decimal
    under_calibrated_category_count: Decimal
    missing_recent_outcome_feedback_category_count: Decimal
    average_memory_coverage_ratio: Decimal
    average_calibration_score: Decimal
    max_oldest_memory_age_seconds: Decimal
    rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainMemoryStalenessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(self, "public_status", _require_status(self.public_status))
        for field_name in (
            "category_count",
            "observed_category_count",
            "missing_category_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_category_count",
            "under_calibrated_category_count",
            "missing_recent_outcome_feedback_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_oldest_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_oldest_memory_age_seconds",
                self.max_oldest_memory_age_seconds,
            ),
        )
        for field_name in (
            "average_memory_coverage_ratio",
            "average_calibration_score",
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(self),
            ),
        )

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_memory_staleness_report_payload(self)


def build_research_team_domain_memory_staleness_report(
    observations: Iterable[object],
    *,
    config: ResearchTeamDomainMemoryStalenessConfig,
    generated_at: datetime,
) -> ResearchTeamDomainMemoryStalenessReport:
    if type(config) is not ResearchTeamDomainMemoryStalenessConfig:
        raise ValueError("config must be a ResearchTeamDomainMemoryStalenessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.memory_updated_at > generated_at_utc:
            raise ValueError("memory_updated_at must not be after generated_at")
        if (
            item.last_outcome_feedback_at is not None
            and item.last_outcome_feedback_at > generated_at_utc
        ):
            raise ValueError(
                "last_outcome_feedback_at must not be after generated_at",
            )

    rows = tuple(
        sorted(
            (
                _row_for_category(
                    category,
                    observations=tuple(
                        item for item in items if item.domain_category == category
                    ),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for category in PUBLIC_DOMAIN_CATEGORIES
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamDomainMemoryStalenessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        public_status=_report_public_status(rows),
        category_count=_decimal_count(len(PUBLIC_DOMAIN_CATEGORIES)),
        observed_category_count=_decimal_count(
            len({item.domain_category for item in items}),
        ),
        missing_category_count=_reason_count(rows, MISSING_DOMAIN_MEMORY_REASON),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        stale_category_count=_reason_count_any(
            rows,
            (BLOCK_STALE_MEMORY_REASON, STALE_MEMORY_REASON),
        ),
        under_calibrated_category_count=_reason_count_any(
            rows,
            (BLOCK_UNDER_CALIBRATED_REASON, UNDER_CALIBRATED_REASON),
        ),
        missing_recent_outcome_feedback_category_count=_reason_count(
            rows,
            MISSING_RECENT_OUTCOME_FEEDBACK_REASON,
        ),
        average_memory_coverage_ratio=_mean(
            tuple(
                row.memory_coverage_ratio
                for row in rows
                if MISSING_DOMAIN_MEMORY_REASON not in row.reason_codes
            ),
        ),
        average_calibration_score=_mean(
            tuple(
                row.average_calibration_score
                for row in rows
                if MISSING_DOMAIN_MEMORY_REASON not in row.reason_codes
            ),
        ),
        max_oldest_memory_age_seconds=_max_optional_decimal(
            tuple(row.oldest_memory_age_seconds for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows, had_inputs=bool(items)),
    )


def research_team_domain_memory_staleness_report_payload(
    report: ResearchTeamDomainMemoryStalenessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainMemoryStalenessReport:
        _validate_report_runtime(report)
        payload = _json_ready_public_payload(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        _validate_payload_statuses(report)
        payload = _json_ready_public_payload(report, allow_decimal=False)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainMemoryStalenessReport",
        )
    if type(payload) is not dict:
        raise ValueError("domain memory staleness payload must be a JSON object")
    _validate_report_payload(payload)
    _reject_unsafe_public_payload("domain memory staleness payload", payload)
    return payload


def research_team_domain_memory_staleness_report_digest(
    report: ResearchTeamDomainMemoryStalenessReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_team_domain_memory_staleness_report_payload(report)
    digest_keys = (
        "generated_at",
        "config_version",
        "public_status",
        "category_count",
        "observed_category_count",
        "missing_category_count",
        "pass_count",
        "watch_count",
        "block_count",
        "stale_category_count",
        "under_calibrated_category_count",
        "missing_recent_outcome_feedback_category_count",
        "average_memory_coverage_ratio",
        "average_calibration_score",
        "max_oldest_memory_age_seconds",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    return {key: payload[key] for key in digest_keys}


def _row_for_category(
    category: str,
    *,
    observations: tuple[ResearchTeamDomainMemoryStalenessObservation, ...],
    config: ResearchTeamDomainMemoryStalenessConfig,
    generated_at: datetime,
) -> ResearchTeamDomainMemoryStalenessRow:
    if not observations:
        return ResearchTeamDomainMemoryStalenessRow(
            domain_category=category,
            public_status=STATUS_BLOCK,
            team_count=ZERO,
            memory_coverage_ratio=ZERO,
            average_calibration_score=ZERO,
            settled_outcome_count=ZERO,
            recent_outcome_feedback_count=ZERO,
            newest_memory_age_seconds=None,
            oldest_memory_age_seconds=None,
            newest_outcome_feedback_age_seconds=None,
            oldest_outcome_feedback_age_seconds=None,
            stale_team_count=ZERO,
            under_calibrated_team_count=ZERO,
            missing_recent_outcome_feedback_team_count=ZERO,
            reason_codes=(MISSING_DOMAIN_MEMORY_REASON,),
        )

    memory_ages = tuple(
        _age_seconds("memory_updated_at", item.memory_updated_at, generated_at)
        for item in observations
    )
    outcome_feedback_ages = tuple(
        _age_seconds(
            "last_outcome_feedback_at",
            item.last_outcome_feedback_at,
            generated_at,
        )
        for item in observations
        if item.last_outcome_feedback_at is not None
    )
    coverage_ratio = _mean(tuple(item.memory_coverage_ratio for item in observations))
    calibration_score = _mean(tuple(item.calibration_score for item in observations))
    recent_outcome_feedback_count = _sum_decimal(
        item.recent_outcome_feedback_count for item in observations
    )
    reason_codes = _row_reason_codes(
        oldest_memory_age_seconds=max(memory_ages),
        memory_coverage_ratio=coverage_ratio,
        average_calibration_score=calibration_score,
        recent_outcome_feedback_count=recent_outcome_feedback_count,
        newest_outcome_feedback_age_seconds=min(outcome_feedback_ages)
        if outcome_feedback_ages
        else None,
        config=config,
    )
    return ResearchTeamDomainMemoryStalenessRow(
        domain_category=category,
        public_status=_row_public_status(reason_codes),
        team_count=_decimal_count(len({item.team_key for item in observations})),
        memory_coverage_ratio=coverage_ratio,
        average_calibration_score=calibration_score,
        settled_outcome_count=_sum_decimal(
            item.settled_outcome_count for item in observations
        ),
        recent_outcome_feedback_count=recent_outcome_feedback_count,
        newest_memory_age_seconds=min(memory_ages),
        oldest_memory_age_seconds=max(memory_ages),
        newest_outcome_feedback_age_seconds=min(outcome_feedback_ages)
        if outcome_feedback_ages
        else None,
        oldest_outcome_feedback_age_seconds=max(outcome_feedback_ages)
        if outcome_feedback_ages
        else None,
        stale_team_count=_decimal_count(
            sum(1 for age in memory_ages if age >= config.stale_after_seconds),
        ),
        under_calibrated_team_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.calibration_score < config.min_pass_calibration_score
            ),
        ),
        missing_recent_outcome_feedback_team_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.last_outcome_feedback_at is None
                or item.recent_outcome_feedback_count < ONE
            ),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    oldest_memory_age_seconds: Decimal,
    memory_coverage_ratio: Decimal,
    average_calibration_score: Decimal,
    recent_outcome_feedback_count: Decimal,
    newest_outcome_feedback_age_seconds: Decimal | None,
    config: ResearchTeamDomainMemoryStalenessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if oldest_memory_age_seconds >= config.block_stale_after_seconds:
        reason_codes.append(BLOCK_STALE_MEMORY_REASON)
    elif oldest_memory_age_seconds >= config.stale_after_seconds:
        reason_codes.append(STALE_MEMORY_REASON)

    if memory_coverage_ratio < config.min_watch_memory_coverage_ratio:
        reason_codes.append(BLOCK_MEMORY_COVERAGE_REASON)
    elif memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        reason_codes.append(LOW_MEMORY_COVERAGE_REASON)

    if average_calibration_score < config.min_watch_calibration_score:
        reason_codes.append(BLOCK_UNDER_CALIBRATED_REASON)
    elif average_calibration_score < config.min_pass_calibration_score:
        reason_codes.append(UNDER_CALIBRATED_REASON)

    if (
        recent_outcome_feedback_count < config.min_recent_outcome_feedback_count
        or newest_outcome_feedback_age_seconds is None
        or newest_outcome_feedback_age_seconds
        >= config.stale_outcome_feedback_after_seconds
    ):
        reason_codes.append(MISSING_RECENT_OUTCOME_FEEDBACK_REASON)

    return _normalize_reason_codes(
        tuple(reason_codes) or (HEALTHY_MEMORY_REASON,),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_public_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            MISSING_DOMAIN_MEMORY_REASON,
            BLOCK_STALE_MEMORY_REASON,
            BLOCK_MEMORY_COVERAGE_REASON,
            BLOCK_UNDER_CALIBRATED_REASON,
            MISSING_RECENT_OUTCOME_FEEDBACK_REASON,
        )
    ):
        return STATUS_BLOCK
    if any(
        reason_code in reason_codes
        for reason_code in (
            STALE_MEMORY_REASON,
            LOW_MEMORY_COVERAGE_REASON,
            UNDER_CALIBRATED_REASON,
        )
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _report_public_status(rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...]) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...],
    *,
    had_inputs: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    row_reason_codes = {
        reason_code for row in rows for reason_code in row.reason_codes
    }
    if not had_inputs:
        reason_codes.append(REPORT_NO_INPUTS_REASON)
    if any(row.public_status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.public_status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if MISSING_DOMAIN_MEMORY_REASON in row_reason_codes:
        reason_codes.append(REPORT_MISSING_DOMAIN_MEMORY_PRESENT_REASON)
    if row_reason_codes.intersection({BLOCK_STALE_MEMORY_REASON, STALE_MEMORY_REASON}):
        reason_codes.append(REPORT_STALE_MEMORY_PRESENT_REASON)
    if row_reason_codes.intersection(
        {BLOCK_UNDER_CALIBRATED_REASON, UNDER_CALIBRATED_REASON},
    ):
        reason_codes.append(REPORT_UNDER_CALIBRATED_PRESENT_REASON)
    if MISSING_RECENT_OUTCOME_FEEDBACK_REASON in row_reason_codes:
        reason_codes.append(REPORT_MISSING_OUTCOME_FEEDBACK_PRESENT_REASON)
    if HEALTHY_MEMORY_REASON in row_reason_codes:
        reason_codes.append(REPORT_HEALTHY_MEMORY_PRESENT_REASON)
    return _normalize_reason_codes(tuple(reason_codes), REPORT_REASON_CODE_SEQUENCE)


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchTeamDomainMemoryStalenessObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchTeamDomainMemoryStalenessObservation:
            raise ValueError(
                "observations must contain ResearchTeamDomainMemoryStalenessObservation",
            )
        _require_hard_flags("observation", item)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...],
) -> tuple[ResearchTeamDomainMemoryStalenessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamDomainMemoryStalenessRow:
            raise ValueError("rows must contain ResearchTeamDomainMemoryStalenessRow")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by public status and category")
    if tuple(sorted(row.domain_category for row in rows)) != tuple(
        sorted(PUBLIC_DOMAIN_CATEGORIES),
    ):
        raise ValueError("rows must cover every public domain category")
    return rows


def _row_sort_key(row: ResearchTeamDomainMemoryStalenessRow) -> tuple[int, str]:
    return (PUBLIC_STATUS_SORT_SEQUENCE.index(row.public_status), row.domain_category)


def _status_count(
    rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.public_status == status))


def _reason_count(
    rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_count_any(
    rows: tuple[ResearchTeamDomainMemoryStalenessRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in reason_codes)
        ),
    )


def _validate_row(row: ResearchTeamDomainMemoryStalenessRow) -> None:
    if row.team_count == ZERO and row.reason_codes != (MISSING_DOMAIN_MEMORY_REASON,):
        raise ValueError("missing domain row must use missing domain reason")
    if row.team_count > ZERO and MISSING_DOMAIN_MEMORY_REASON in row.reason_codes:
        raise ValueError("observed domain row must not use missing domain reason")
    if (
        row.newest_memory_age_seconds is None
    ) != (row.oldest_memory_age_seconds is None):
        raise ValueError("memory age fields must both be present or absent")
    if (
        row.newest_outcome_feedback_age_seconds is None
    ) != (row.oldest_outcome_feedback_age_seconds is None):
        raise ValueError("outcome feedback age fields must both be present or absent")
    if (
        row.newest_memory_age_seconds is not None
        and row.oldest_memory_age_seconds is not None
        and row.newest_memory_age_seconds > row.oldest_memory_age_seconds
    ):
        raise ValueError("newest_memory_age_seconds must not exceed oldest")
    if (
        row.newest_outcome_feedback_age_seconds is not None
        and row.oldest_outcome_feedback_age_seconds is not None
        and row.newest_outcome_feedback_age_seconds
        > row.oldest_outcome_feedback_age_seconds
    ):
        raise ValueError("newest_outcome_feedback_age_seconds must not exceed oldest")
    if row.stale_team_count > row.team_count:
        raise ValueError("stale_team_count must not exceed team_count")
    if row.under_calibrated_team_count > row.team_count:
        raise ValueError("under_calibrated_team_count must not exceed team_count")
    if row.missing_recent_outcome_feedback_team_count > row.team_count:
        raise ValueError(
            "missing_recent_outcome_feedback_team_count must not exceed team_count",
        )
    if row.recent_outcome_feedback_count > row.settled_outcome_count:
        raise ValueError(
            "recent_outcome_feedback_count must not exceed settled_outcome_count",
        )
    if row.public_status != _row_public_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    if HEALTHY_MEMORY_REASON in row.reason_codes and row.reason_codes != (
        HEALTHY_MEMORY_REASON,
    ):
        raise ValueError("healthy memory reason must be standalone")


def _validate_report(report: ResearchTeamDomainMemoryStalenessReport) -> None:
    rows = report.rows
    if report.public_status != _report_public_status(rows):
        raise ValueError("public_status must match rows")
    if report.category_count != _decimal_count(len(PUBLIC_DOMAIN_CATEGORIES)):
        raise ValueError("category_count must match public categories")
    if report.observed_category_count != _decimal_count(
        sum(1 for row in rows if MISSING_DOMAIN_MEMORY_REASON not in row.reason_codes),
    ):
        raise ValueError("observed_category_count must match rows")
    if report.missing_category_count != _reason_count(rows, MISSING_DOMAIN_MEMORY_REASON):
        raise ValueError("missing_category_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.stale_category_count != _reason_count_any(
        rows,
        (BLOCK_STALE_MEMORY_REASON, STALE_MEMORY_REASON),
    ):
        raise ValueError("stale_category_count must match rows")
    if report.under_calibrated_category_count != _reason_count_any(
        rows,
        (BLOCK_UNDER_CALIBRATED_REASON, UNDER_CALIBRATED_REASON),
    ):
        raise ValueError("under_calibrated_category_count must match rows")
    if report.missing_recent_outcome_feedback_category_count != _reason_count(
        rows,
        MISSING_RECENT_OUTCOME_FEEDBACK_REASON,
    ):
        raise ValueError(
            "missing_recent_outcome_feedback_category_count must match rows",
        )
    observed_rows = tuple(
        row for row in rows if MISSING_DOMAIN_MEMORY_REASON not in row.reason_codes
    )
    if report.average_memory_coverage_ratio != _mean(
        tuple(row.memory_coverage_ratio for row in observed_rows),
    ):
        raise ValueError("average_memory_coverage_ratio must match rows")
    if report.average_calibration_score != _mean(
        tuple(row.average_calibration_score for row in observed_rows),
    ):
        raise ValueError("average_calibration_score must match rows")
    if report.max_oldest_memory_age_seconds != _max_optional_decimal(
        tuple(row.oldest_memory_age_seconds for row in rows),
    ):
        raise ValueError("max_oldest_memory_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(
        rows,
        had_inputs=bool(observed_rows),
    ):
        raise ValueError("reason_codes must match rows")


def _validate_report_runtime(report: ResearchTeamDomainMemoryStalenessReport) -> None:
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest must match report contents")


def _validate_report_payload(payload: dict[str, Any]) -> None:
    _require_payload_flags(payload)
    _validate_payload_statuses(payload)
    _validate_payload_rows(payload)
    _require_sha256_digest("validation_digest", payload.get("validation_digest"))
    if payload["validation_digest"] != _payload_validation_digest(payload):
        raise ValueError("validation_digest must match report contents")


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    public_status = payload.get("public_status")
    if public_status not in PUBLIC_STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        row_status = row.get("public_status")
        if row_status not in PUBLIC_STATUSES:
            raise ValueError("row public_status must be pass, watch, or block")


def _validate_payload_rows(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    for row in rows:
        _require_payload_flags(row)
        _require_sha256_digest("validation_digest", row.get("validation_digest"))
        if row["validation_digest"] != _payload_validation_digest(row):
            raise ValueError("validation_digest must match report contents")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _row_validation_digest(row: ResearchTeamDomainMemoryStalenessRow) -> str:
    payload = _json_ready_public_payload(
        {
            "domain_category": row.domain_category,
            "public_status": row.public_status,
            "team_count": row.team_count,
            "memory_coverage_ratio": row.memory_coverage_ratio,
            "average_calibration_score": row.average_calibration_score,
            "settled_outcome_count": row.settled_outcome_count,
            "recent_outcome_feedback_count": row.recent_outcome_feedback_count,
            "newest_memory_age_seconds": row.newest_memory_age_seconds,
            "oldest_memory_age_seconds": row.oldest_memory_age_seconds,
            "newest_outcome_feedback_age_seconds": (
                row.newest_outcome_feedback_age_seconds
            ),
            "oldest_outcome_feedback_age_seconds": (
                row.oldest_outcome_feedback_age_seconds
            ),
            "stale_team_count": row.stale_team_count,
            "under_calibrated_team_count": row.under_calibrated_team_count,
            "missing_recent_outcome_feedback_team_count": (
                row.missing_recent_outcome_feedback_team_count
            ),
            "reason_codes": row.reason_codes,
            "paper_only": row.paper_only,
            "report_only": row.report_only,
            "readonly": row.readonly,
        },
        allow_decimal=True,
    )
    return _digest_payload(payload)


def _report_validation_digest(report: ResearchTeamDomainMemoryStalenessReport) -> str:
    payload = _json_ready_public_payload(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "public_status": report.public_status,
            "category_count": report.category_count,
            "observed_category_count": report.observed_category_count,
            "missing_category_count": report.missing_category_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "stale_category_count": report.stale_category_count,
            "under_calibrated_category_count": (
                report.under_calibrated_category_count
            ),
            "missing_recent_outcome_feedback_category_count": (
                report.missing_recent_outcome_feedback_category_count
            ),
            "average_memory_coverage_ratio": report.average_memory_coverage_ratio,
            "average_calibration_score": report.average_calibration_score,
            "max_oldest_memory_age_seconds": report.max_oldest_memory_age_seconds,
            "rows": report.rows,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
        allow_decimal=True,
    )
    return _digest_payload(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    payload_for_digest = dict(payload)
    payload_for_digest.pop("validation_digest", None)
    return _digest_payload(payload_for_digest)


def _digest_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{VALIDATION_DIGEST_ALGORITHM}:{sha256(canonical.encode()).hexdigest()}"


def _normalize_validation_digest(
    field_name: str,
    value: object,
    expected_digest: str,
) -> str:
    if value == "":
        return expected_digest
    _require_sha256_digest(field_name, value)
    if value != expected_digest:
        raise ValueError(f"{field_name} must match report contents")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    prefix = f"{VALIDATION_DIGEST_ALGORITHM}:"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a sha256 digest")
    digest = value[len(prefix) :]
    if len(digest) != 64 or any(character not in HEX_DIGITS for character in digest):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _json_ready_public_payload(value: Any, *, allow_decimal: bool) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_public_payload(asdict(value), allow_decimal=allow_decimal)
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("payload must not contain Decimal values")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_quantize_decimal(value))
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if type(value) in (int, float):
        raise ValueError("payload must not contain int or float values")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text("payload", key)
            ready[key] = _json_ready_public_payload(
                item,
                allow_decimal=allow_decimal,
            )
        return ready
    if type(value) in (list, tuple):
        return [
            _json_ready_public_payload(item, allow_decimal=allow_decimal)
            for item in value
        ]
    raise ValueError("payload contains unsupported value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _age_seconds(
    field_name: str,
    observed_at: datetime | None,
    generated_at: datetime,
) -> Decimal:
    if observed_at is None:
        raise ValueError(f"{field_name} must be present")
    if observed_at > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(seconds)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    return value


def _require_public_category(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public category")
    _reject_unsafe_public_text(field_name, value)
    if value not in PUBLIC_DOMAIN_CATEGORIES:
        raise ValueError(f"{field_name} must be a public category")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a public string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    try:
        reject_unsafe_surface_fields(label, payload)
        _walk_public_payload(label, payload)
    except ValueError as exc:
        if "unsafe public payload" in str(exc):
            raise
        raise ValueError(f"unsafe public payload in {label}") from exc


def _walk_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _walk_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_text(label, key)
            _walk_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _walk_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize_decimal(decimal_value)


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_integral_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(decimal_value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in allowed_sequence:
        if reason_code in reason_codes:
            normalized.append(reason_code)
    if len(normalized) != len(reason_codes):
        raise ValueError("reason_codes contain unsupported values")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(normalized)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _max_optional_decimal(values: tuple[Decimal | None, ...]) -> Decimal:
    present = tuple(value for value in values if value is not None)
    if not present:
        return ZERO
    return max(present)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
