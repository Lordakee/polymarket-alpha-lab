"""Report-only audit of domain team decision memory decay."""

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


DEFAULT_RESEARCH_TEAM_DOMAIN_DECISION_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-team-domain-decision-memory-decay-report-v0"
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

MISSING_DECISION_MEMORY_REASON = (
    "research_team_domain_decision_memory_decay_missing_memory"
)
BLOCK_MEMORY_DECAY_REASON = (
    "research_team_domain_decision_memory_decay_block_memory_decay"
)
WATCH_MEMORY_DECAY_REASON = (
    "research_team_domain_decision_memory_decay_watch_memory_decay"
)
STALE_REVIEW_REASON = "research_team_domain_decision_memory_decay_stale_review"
BLOCK_UNRESOLVED_REASON = (
    "research_team_domain_decision_memory_decay_block_unresolved_decisions"
)
HIGH_UNRESOLVED_REASON = (
    "research_team_domain_decision_memory_decay_high_unresolved_decisions"
)
BLOCK_LOW_REUSE_REASON = (
    "research_team_domain_decision_memory_decay_block_low_reuse"
)
LOW_REUSE_REASON = "research_team_domain_decision_memory_decay_low_reuse"
BLOCK_LOW_CALIBRATION_REASON = (
    "research_team_domain_decision_memory_decay_block_low_calibration"
)
LOW_CALIBRATION_REASON = (
    "research_team_domain_decision_memory_decay_low_calibration"
)
HEALTHY_MEMORY_REASON = "research_team_domain_decision_memory_decay_healthy_memory"

REPORT_NO_INPUTS_REASON = (
    "research_team_domain_decision_memory_decay_report_no_inputs"
)
REPORT_BLOCK_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_block_present"
)
REPORT_WATCH_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_watch_present"
)
REPORT_MISSING_MEMORY_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_missing_memory_present"
)
REPORT_MEMORY_DECAY_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_memory_decay_present"
)
REPORT_STALE_REVIEW_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_stale_review_present"
)
REPORT_UNRESOLVED_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_unresolved_present"
)
REPORT_LOW_REUSE_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_low_reuse_present"
)
REPORT_LOW_CALIBRATION_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_low_calibration_present"
)
REPORT_HEALTHY_MEMORY_PRESENT_REASON = (
    "research_team_domain_decision_memory_decay_report_healthy_memory_present"
)

ROW_REASON_CODE_SEQUENCE = (
    MISSING_DECISION_MEMORY_REASON,
    BLOCK_MEMORY_DECAY_REASON,
    WATCH_MEMORY_DECAY_REASON,
    STALE_REVIEW_REASON,
    BLOCK_UNRESOLVED_REASON,
    HIGH_UNRESOLVED_REASON,
    BLOCK_LOW_REUSE_REASON,
    LOW_REUSE_REASON,
    BLOCK_LOW_CALIBRATION_REASON,
    LOW_CALIBRATION_REASON,
    HEALTHY_MEMORY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    REPORT_NO_INPUTS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_MISSING_MEMORY_PRESENT_REASON,
    REPORT_MEMORY_DECAY_PRESENT_REASON,
    REPORT_STALE_REVIEW_PRESENT_REASON,
    REPORT_UNRESOLVED_PRESENT_REASON,
    REPORT_LOW_REUSE_PRESENT_REASON,
    REPORT_LOW_CALIBRATION_PRESENT_REASON,
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
        "sizing",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_DECISION_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "PUBLIC_DOMAIN_CATEGORIES",
    "PUBLIC_STATUSES",
    "ResearchTeamDomainDecisionMemoryDecayConfig",
    "ResearchTeamDomainDecisionMemoryDecayObservation",
    "ResearchTeamDomainDecisionMemoryDecayRow",
    "ResearchTeamDomainDecisionMemoryDecayReport",
    "build_research_team_domain_decision_memory_decay_report",
    "research_team_domain_decision_memory_decay_report_payload",
    "research_team_domain_decision_memory_decay_report_digest",
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
class ResearchTeamDomainDecisionMemoryDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_DECISION_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    watch_memory_decay_after_seconds: Decimal = Decimal("5184000.000000")
    block_memory_decay_after_seconds: Decimal = Decimal("10368000.000000")
    stale_review_after_seconds: Decimal = Decimal("3888000.000000")
    max_watch_unresolved_decisions: Decimal = Decimal("3.000000")
    max_block_unresolved_decisions: Decimal = Decimal("8.000000")
    min_pass_memory_reuse_ratio: Decimal = Decimal("0.650000")
    min_watch_memory_reuse_ratio: Decimal = Decimal("0.400000")
    min_pass_calibration_score: Decimal = Decimal("0.700000")
    min_watch_calibration_score: Decimal = Decimal("0.500000")
    min_pass_decision_hit_rate: Decimal = Decimal("0.650000")
    min_watch_decision_hit_rate: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainDecisionMemoryDecayConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "watch_memory_decay_after_seconds",
            "block_memory_decay_after_seconds",
            "stale_review_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_watch_unresolved_decisions",
            "max_block_unresolved_decisions",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "min_pass_memory_reuse_ratio",
            "min_watch_memory_reuse_ratio",
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "min_pass_decision_hit_rate",
            "min_watch_decision_hit_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_memory_decay_after_seconds > self.block_memory_decay_after_seconds:
            raise ValueError(
                "watch_memory_decay_after_seconds must not exceed block threshold",
            )
        if self.max_watch_unresolved_decisions > self.max_block_unresolved_decisions:
            raise ValueError(
                "max_watch_unresolved_decisions must not exceed block threshold",
            )
        if self.min_watch_memory_reuse_ratio > self.min_pass_memory_reuse_ratio:
            raise ValueError(
                "min_watch_memory_reuse_ratio must not exceed pass threshold",
            )
        if self.min_watch_calibration_score > self.min_pass_calibration_score:
            raise ValueError(
                "min_watch_calibration_score must not exceed pass threshold",
            )
        if self.min_watch_decision_hit_rate > self.min_pass_decision_hit_rate:
            raise ValueError(
                "min_watch_decision_hit_rate must not exceed pass threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainDecisionMemoryDecayObservation(_FinalPublicDataclass):
    domain_category: str
    team_key: str
    decision_memory_updated_at: datetime
    latest_decision_review_at: datetime | None
    resolved_decision_count: Decimal
    unresolved_decision_count: Decimal
    decision_hit_rate: Decimal
    decision_calibration_score: Decimal
    memory_reuse_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainDecisionMemoryDecayObservation,
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
            "decision_memory_updated_at",
            _as_utc("decision_memory_updated_at", self.decision_memory_updated_at),
        )
        object.__setattr__(
            self,
            "latest_decision_review_at",
            _optional_utc("latest_decision_review_at", self.latest_decision_review_at),
        )
        for field_name in ("resolved_decision_count", "unresolved_decision_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "decision_hit_rate",
            "decision_calibration_score",
            "memory_reuse_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamDomainDecisionMemoryDecayRow(_FinalPublicDataclass):
    domain_category: str
    public_status: str
    team_count: Decimal
    resolved_decision_count: Decimal
    unresolved_decision_count: Decimal
    newest_decision_memory_age_seconds: Decimal | None
    oldest_decision_memory_age_seconds: Decimal | None
    newest_decision_review_age_seconds: Decimal | None
    oldest_decision_review_age_seconds: Decimal | None
    average_decision_hit_rate: Decimal
    average_decision_calibration_score: Decimal
    average_memory_reuse_ratio: Decimal
    decayed_team_count: Decimal
    stale_review_team_count: Decimal
    low_reuse_team_count: Decimal
    low_calibration_team_count: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainDecisionMemoryDecayRow, "row")
        object.__setattr__(
            self,
            "domain_category",
            _require_public_category("domain_category", self.domain_category),
        )
        object.__setattr__(self, "public_status", _require_status(self.public_status))
        for field_name in (
            "team_count",
            "resolved_decision_count",
            "unresolved_decision_count",
            "decayed_team_count",
            "stale_review_team_count",
            "low_reuse_team_count",
            "low_calibration_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "newest_decision_memory_age_seconds",
            "oldest_decision_memory_age_seconds",
            "newest_decision_review_age_seconds",
            "oldest_decision_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_decision_hit_rate",
            "average_decision_calibration_score",
            "average_memory_reuse_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)
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
class ResearchTeamDomainDecisionMemoryDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    category_count: Decimal
    observed_category_count: Decimal
    missing_category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    decayed_category_count: Decimal
    stale_review_category_count: Decimal
    unresolved_category_count: Decimal
    low_reuse_category_count: Decimal
    low_calibration_category_count: Decimal
    average_decision_hit_rate: Decimal
    average_decision_calibration_score: Decimal
    average_memory_reuse_ratio: Decimal
    max_oldest_decision_memory_age_seconds: Decimal
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainDecisionMemoryDecayReport, "report")
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
            "decayed_category_count",
            "stale_review_category_count",
            "unresolved_category_count",
            "low_reuse_category_count",
            "low_calibration_category_count",
            "max_oldest_decision_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_decision_hit_rate",
            "average_decision_calibration_score",
            "average_memory_reuse_ratio",
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
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
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
        return research_team_domain_decision_memory_decay_report_payload(self)


def build_research_team_domain_decision_memory_decay_report(
    observations: Iterable[object],
    *,
    config: ResearchTeamDomainDecisionMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchTeamDomainDecisionMemoryDecayReport:
    if type(config) is not ResearchTeamDomainDecisionMemoryDecayConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainDecisionMemoryDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.decision_memory_updated_at > generated_at_utc:
            raise ValueError("decision_memory_updated_at must not be after generated_at")
        if (
            item.latest_decision_review_at is not None
            and item.latest_decision_review_at > generated_at_utc
        ):
            raise ValueError(
                "latest_decision_review_at must not be after generated_at",
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
    observed_rows = tuple(
        row for row in rows if MISSING_DECISION_MEMORY_REASON not in row.reason_codes
    )
    return ResearchTeamDomainDecisionMemoryDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        public_status=_report_public_status(rows),
        category_count=_decimal_count(len(PUBLIC_DOMAIN_CATEGORIES)),
        observed_category_count=_decimal_count(
            len({item.domain_category for item in items}),
        ),
        missing_category_count=_reason_count(rows, MISSING_DECISION_MEMORY_REASON),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        decayed_category_count=_reason_count_any(
            rows,
            (BLOCK_MEMORY_DECAY_REASON, WATCH_MEMORY_DECAY_REASON),
        ),
        stale_review_category_count=_reason_count(rows, STALE_REVIEW_REASON),
        unresolved_category_count=_reason_count_any(
            rows,
            (BLOCK_UNRESOLVED_REASON, HIGH_UNRESOLVED_REASON),
        ),
        low_reuse_category_count=_reason_count_any(
            rows,
            (BLOCK_LOW_REUSE_REASON, LOW_REUSE_REASON),
        ),
        low_calibration_category_count=_reason_count_any(
            rows,
            (BLOCK_LOW_CALIBRATION_REASON, LOW_CALIBRATION_REASON),
        ),
        average_decision_hit_rate=_mean(
            tuple(row.average_decision_hit_rate for row in observed_rows),
        ),
        average_decision_calibration_score=_mean(
            tuple(row.average_decision_calibration_score for row in observed_rows),
        ),
        average_memory_reuse_ratio=_mean(
            tuple(row.average_memory_reuse_ratio for row in observed_rows),
        ),
        max_oldest_decision_memory_age_seconds=_max_optional_decimal(
            tuple(row.oldest_decision_memory_age_seconds for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows, had_inputs=bool(items)),
    )


def research_team_domain_decision_memory_decay_report_payload(
    report: ResearchTeamDomainDecisionMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainDecisionMemoryDecayReport:
        _validate_report_runtime(report)
        payload = _json_ready_public_payload(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        _validate_payload_statuses(report)
        payload = _json_ready_public_payload(report, allow_decimal=False)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainDecisionMemoryDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("domain decision memory decay payload must be a JSON object")
    _reject_unsafe_public_payload("domain decision memory decay payload", payload)
    _validate_report_payload(payload)
    return payload


def research_team_domain_decision_memory_decay_report_digest(
    report: ResearchTeamDomainDecisionMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_team_domain_decision_memory_decay_report_payload(report)
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
        "decayed_category_count",
        "stale_review_category_count",
        "unresolved_category_count",
        "low_reuse_category_count",
        "low_calibration_category_count",
        "average_decision_hit_rate",
        "average_decision_calibration_score",
        "average_memory_reuse_ratio",
        "max_oldest_decision_memory_age_seconds",
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
    observations: tuple[ResearchTeamDomainDecisionMemoryDecayObservation, ...],
    config: ResearchTeamDomainDecisionMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchTeamDomainDecisionMemoryDecayRow:
    if not observations:
        return ResearchTeamDomainDecisionMemoryDecayRow(
            domain_category=category,
            public_status=STATUS_BLOCK,
            team_count=ZERO,
            resolved_decision_count=ZERO,
            unresolved_decision_count=ZERO,
            newest_decision_memory_age_seconds=None,
            oldest_decision_memory_age_seconds=None,
            newest_decision_review_age_seconds=None,
            oldest_decision_review_age_seconds=None,
            average_decision_hit_rate=ZERO,
            average_decision_calibration_score=ZERO,
            average_memory_reuse_ratio=ZERO,
            decayed_team_count=ZERO,
            stale_review_team_count=ZERO,
            low_reuse_team_count=ZERO,
            low_calibration_team_count=ZERO,
            reason_codes=(MISSING_DECISION_MEMORY_REASON,),
        )

    memory_ages = tuple(
        _age_seconds("decision_memory_updated_at", item.decision_memory_updated_at, generated_at)
        for item in observations
    )
    review_ages = tuple(
        _age_seconds(
            "latest_decision_review_at",
            item.latest_decision_review_at,
            generated_at,
        )
        for item in observations
        if item.latest_decision_review_at is not None
    )
    resolved_count = _sum_decimal(item.resolved_decision_count for item in observations)
    unresolved_count = _sum_decimal(
        item.unresolved_decision_count for item in observations
    )
    hit_rate = _mean(tuple(item.decision_hit_rate for item in observations))
    calibration_score = _mean(
        tuple(item.decision_calibration_score for item in observations),
    )
    reuse_ratio = _mean(tuple(item.memory_reuse_ratio for item in observations))
    reason_codes = _row_reason_codes(
        oldest_memory_age_seconds=max(memory_ages),
        newest_review_age_seconds=min(review_ages) if review_ages else None,
        unresolved_decision_count=unresolved_count,
        average_decision_hit_rate=hit_rate,
        average_calibration_score=calibration_score,
        average_memory_reuse_ratio=reuse_ratio,
        config=config,
    )
    return ResearchTeamDomainDecisionMemoryDecayRow(
        domain_category=category,
        public_status=_row_public_status(reason_codes),
        team_count=_decimal_count(len({item.team_key for item in observations})),
        resolved_decision_count=resolved_count,
        unresolved_decision_count=unresolved_count,
        newest_decision_memory_age_seconds=min(memory_ages),
        oldest_decision_memory_age_seconds=max(memory_ages),
        newest_decision_review_age_seconds=min(review_ages) if review_ages else None,
        oldest_decision_review_age_seconds=max(review_ages) if review_ages else None,
        average_decision_hit_rate=hit_rate,
        average_decision_calibration_score=calibration_score,
        average_memory_reuse_ratio=reuse_ratio,
        decayed_team_count=_decimal_count(
            sum(
                1
                for age in memory_ages
                if age >= config.watch_memory_decay_after_seconds
            ),
        ),
        stale_review_team_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.latest_decision_review_at is None
                or _age_seconds(
                    "latest_decision_review_at",
                    item.latest_decision_review_at,
                    generated_at,
                )
                >= config.stale_review_after_seconds
            ),
        ),
        low_reuse_team_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.memory_reuse_ratio < config.min_pass_memory_reuse_ratio
            ),
        ),
        low_calibration_team_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.decision_calibration_score < config.min_pass_calibration_score
                or item.decision_hit_rate < config.min_pass_decision_hit_rate
            ),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    oldest_memory_age_seconds: Decimal,
    newest_review_age_seconds: Decimal | None,
    unresolved_decision_count: Decimal,
    average_decision_hit_rate: Decimal,
    average_calibration_score: Decimal,
    average_memory_reuse_ratio: Decimal,
    config: ResearchTeamDomainDecisionMemoryDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if oldest_memory_age_seconds >= config.block_memory_decay_after_seconds:
        reason_codes.append(BLOCK_MEMORY_DECAY_REASON)
    elif oldest_memory_age_seconds >= config.watch_memory_decay_after_seconds:
        reason_codes.append(WATCH_MEMORY_DECAY_REASON)

    if (
        newest_review_age_seconds is None
        or newest_review_age_seconds >= config.stale_review_after_seconds
    ):
        reason_codes.append(STALE_REVIEW_REASON)

    if unresolved_decision_count >= config.max_block_unresolved_decisions:
        reason_codes.append(BLOCK_UNRESOLVED_REASON)
    elif unresolved_decision_count >= config.max_watch_unresolved_decisions:
        reason_codes.append(HIGH_UNRESOLVED_REASON)

    if average_memory_reuse_ratio < config.min_watch_memory_reuse_ratio:
        reason_codes.append(BLOCK_LOW_REUSE_REASON)
    elif average_memory_reuse_ratio < config.min_pass_memory_reuse_ratio:
        reason_codes.append(LOW_REUSE_REASON)

    if (
        average_calibration_score < config.min_watch_calibration_score
        or average_decision_hit_rate < config.min_watch_decision_hit_rate
    ):
        reason_codes.append(BLOCK_LOW_CALIBRATION_REASON)
    elif (
        average_calibration_score < config.min_pass_calibration_score
        or average_decision_hit_rate < config.min_pass_decision_hit_rate
    ):
        reason_codes.append(LOW_CALIBRATION_REASON)

    return _normalize_reason_codes(
        tuple(reason_codes) or (HEALTHY_MEMORY_REASON,),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_public_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            MISSING_DECISION_MEMORY_REASON,
            BLOCK_MEMORY_DECAY_REASON,
            BLOCK_UNRESOLVED_REASON,
            BLOCK_LOW_REUSE_REASON,
            BLOCK_LOW_CALIBRATION_REASON,
        )
    ):
        return STATUS_BLOCK
    if any(reason_code != HEALTHY_MEMORY_REASON for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_public_status(
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...],
) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...],
    *,
    had_inputs: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not had_inputs:
        reason_codes.append(REPORT_NO_INPUTS_REASON)
    if any(row.public_status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.public_status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if _reason_count(rows, MISSING_DECISION_MEMORY_REASON) > ZERO:
        reason_codes.append(REPORT_MISSING_MEMORY_PRESENT_REASON)
    if _reason_count_any(
        rows,
        (BLOCK_MEMORY_DECAY_REASON, WATCH_MEMORY_DECAY_REASON),
    ) > ZERO:
        reason_codes.append(REPORT_MEMORY_DECAY_PRESENT_REASON)
    if _reason_count(rows, STALE_REVIEW_REASON) > ZERO:
        reason_codes.append(REPORT_STALE_REVIEW_PRESENT_REASON)
    if _reason_count_any(rows, (BLOCK_UNRESOLVED_REASON, HIGH_UNRESOLVED_REASON)) > ZERO:
        reason_codes.append(REPORT_UNRESOLVED_PRESENT_REASON)
    if _reason_count_any(rows, (BLOCK_LOW_REUSE_REASON, LOW_REUSE_REASON)) > ZERO:
        reason_codes.append(REPORT_LOW_REUSE_PRESENT_REASON)
    if _reason_count_any(
        rows,
        (BLOCK_LOW_CALIBRATION_REASON, LOW_CALIBRATION_REASON),
    ) > ZERO:
        reason_codes.append(REPORT_LOW_CALIBRATION_PRESENT_REASON)
    if _reason_count(rows, HEALTHY_MEMORY_REASON) > ZERO:
        reason_codes.append(REPORT_HEALTHY_MEMORY_PRESENT_REASON)
    return _normalize_reason_codes(reason_codes, REPORT_REASON_CODE_SEQUENCE)


def _validate_row(row: ResearchTeamDomainDecisionMemoryDecayRow) -> None:
    if row.team_count == ZERO:
        if row.public_status != STATUS_BLOCK:
            raise ValueError("missing memory row must block")
        if row.reason_codes != (MISSING_DECISION_MEMORY_REASON,):
            raise ValueError("missing memory row must use missing reason")
    if row.resolved_decision_count + row.unresolved_decision_count == ZERO:
        if MISSING_DECISION_MEMORY_REASON not in row.reason_codes:
            raise ValueError("empty decision memory must use missing reason")
    if row.public_status != _row_public_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    if (
        row.newest_decision_memory_age_seconds is not None
        and row.oldest_decision_memory_age_seconds is not None
        and row.newest_decision_memory_age_seconds
        > row.oldest_decision_memory_age_seconds
    ):
        raise ValueError("newest decision memory age must not exceed oldest age")
    if (
        row.newest_decision_review_age_seconds is not None
        and row.oldest_decision_review_age_seconds is not None
        and row.newest_decision_review_age_seconds
        > row.oldest_decision_review_age_seconds
    ):
        raise ValueError("newest decision review age must not exceed oldest age")
    _validate_digest_if_present(
        "validation_digest",
        row.validation_digest,
        _row_validation_digest(row),
    )


def _validate_report(report: ResearchTeamDomainDecisionMemoryDecayReport) -> None:
    rows = report.rows
    if report.category_count != _decimal_count(len(PUBLIC_DOMAIN_CATEGORIES)):
        raise ValueError("category_count must match public categories")
    if report.observed_category_count != _decimal_count(
        len(
            {
                row.domain_category
                for row in rows
                if MISSING_DECISION_MEMORY_REASON not in row.reason_codes
            },
        ),
    ):
        raise ValueError("observed_category_count must match rows")
    if report.missing_category_count != _reason_count(rows, MISSING_DECISION_MEMORY_REASON):
        raise ValueError("missing_category_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.decayed_category_count != _reason_count_any(
        rows,
        (BLOCK_MEMORY_DECAY_REASON, WATCH_MEMORY_DECAY_REASON),
    ):
        raise ValueError("decayed_category_count must match rows")
    if report.stale_review_category_count != _reason_count(rows, STALE_REVIEW_REASON):
        raise ValueError("stale_review_category_count must match rows")
    if report.unresolved_category_count != _reason_count_any(
        rows,
        (BLOCK_UNRESOLVED_REASON, HIGH_UNRESOLVED_REASON),
    ):
        raise ValueError("unresolved_category_count must match rows")
    if report.low_reuse_category_count != _reason_count_any(
        rows,
        (BLOCK_LOW_REUSE_REASON, LOW_REUSE_REASON),
    ):
        raise ValueError("low_reuse_category_count must match rows")
    if report.low_calibration_category_count != _reason_count_any(
        rows,
        (BLOCK_LOW_CALIBRATION_REASON, LOW_CALIBRATION_REASON),
    ):
        raise ValueError("low_calibration_category_count must match rows")
    observed_rows = tuple(
        row for row in rows if MISSING_DECISION_MEMORY_REASON not in row.reason_codes
    )
    if report.average_decision_hit_rate != _mean(
        tuple(row.average_decision_hit_rate for row in observed_rows),
    ):
        raise ValueError("average_decision_hit_rate must match rows")
    if report.average_decision_calibration_score != _mean(
        tuple(row.average_decision_calibration_score for row in observed_rows),
    ):
        raise ValueError("average_decision_calibration_score must match rows")
    if report.average_memory_reuse_ratio != _mean(
        tuple(row.average_memory_reuse_ratio for row in observed_rows),
    ):
        raise ValueError("average_memory_reuse_ratio must match rows")
    if report.max_oldest_decision_memory_age_seconds != _max_optional_decimal(
        tuple(row.oldest_decision_memory_age_seconds for row in rows),
    ):
        raise ValueError("max_oldest_decision_memory_age_seconds must match rows")
    if report.public_status != _report_public_status(rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, had_inputs=bool(observed_rows)):
        raise ValueError("reason_codes must match rows")
    _validate_digest_if_present(
        "validation_digest",
        report.validation_digest,
        _report_validation_digest(report),
    )


def _validate_report_runtime(report: ResearchTeamDomainDecisionMemoryDecayReport) -> None:
    _validate_report(report)
    for row in report.rows:
        _validate_row(row)


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    if payload.get("public_status") not in PUBLIC_STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rows must contain objects")
        if row.get("public_status") not in PUBLIC_STATUSES:
            raise ValueError("row public_status must be pass, watch, or block")


def _validate_report_payload(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    _require_digest_shape("validation_digest", payload.get("validation_digest"))
    expected_digest = _payload_digest(payload)
    if payload["validation_digest"] != expected_digest:
        raise ValueError("validation_digest must match report contents")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rows must contain objects")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if row.get(flag_name) is not True:
                raise ValueError(f"row {flag_name} must be True")
        _require_digest_shape("row validation_digest", row.get("validation_digest"))
        expected_row_digest = _payload_digest(row)
        if row["validation_digest"] != expected_row_digest:
            raise ValueError("row validation_digest must match row contents")


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchTeamDomainDecisionMemoryDecayObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized: list[ResearchTeamDomainDecisionMemoryDecayObservation] = []
    for item in observations:
        if type(item) is not ResearchTeamDomainDecisionMemoryDecayObservation:
            raise ValueError(
                "observations must contain ResearchTeamDomainDecisionMemoryDecayObservation",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.domain_category, item.team_key)))


def _normalize_rows(
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...],
) -> tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamDomainDecisionMemoryDecayRow:
            raise ValueError("rows must contain ResearchTeamDomainDecisionMemoryDecayRow")
        _require_hard_flags("row", row)
    normalized = tuple(sorted(rows, key=_row_sort_key))
    if len({row.domain_category for row in normalized}) != len(normalized):
        raise ValueError("rows must not duplicate domain_category")
    if tuple(row.domain_category for row in normalized) != tuple(
        row.domain_category for row in rows
    ):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _row_sort_key(row: ResearchTeamDomainDecisionMemoryDecayRow) -> tuple[int, str]:
    return (
        PUBLIC_STATUS_SORT_SEQUENCE.index(row.public_status),
        row.domain_category,
    )


def _status_count(
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.public_status == status))


def _reason_count(
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_count_any(
    rows: tuple[ResearchTeamDomainDecisionMemoryDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANT)


def _max_optional_decimal(values: tuple[Decimal | None, ...]) -> Decimal:
    present = tuple(value for value in values if value is not None)
    if not present:
        return ZERO
    return max(present)


def _age_seconds(field_name: str, value: datetime | None, generated_at: datetime) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} must be present")
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")
    return _quantize(Decimal(str((generated_at - value).total_seconds())))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = normalized.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")
    return normalized


def _require_public_category(field_name: str, value: str) -> str:
    normalized = _require_public_string(field_name, value)
    if normalized not in PUBLIC_DOMAIN_CATEGORIES:
        raise ValueError(f"{field_name} must be a public category")
    return normalized


def _require_status(value: str) -> str:
    if type(value) is not str:
        raise ValueError("public_status must be exactly str")
    if value not in PUBLIC_STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize(normalized)


def _require_positive_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(
    reason_codes: Iterable[str],
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in allowed_sequence:
            raise ValueError("reason_codes contains unsupported value")
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_code for reason_code in allowed_sequence if reason_code in seen)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_text(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_text(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_text(label, item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload")


def _row_validation_digest(row: ResearchTeamDomainDecisionMemoryDecayRow) -> str:
    payload = asdict(row)
    payload["validation_digest"] = ""
    return _payload_digest(payload)


def _report_validation_digest(report: ResearchTeamDomainDecisionMemoryDecayReport) -> str:
    payload = asdict(report)
    payload["validation_digest"] = ""
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["validation_digest"] = ""
    canonical = json.dumps(
        _json_ready_public_payload(digest_payload, allow_decimal=True),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{VALIDATION_DIGEST_ALGORITHM}:{sha256(canonical.encode('utf-8')).hexdigest()}"


def _validate_digest_if_present(
    field_name: str,
    actual: str,
    expected: str,
) -> None:
    if actual in ("", expected):
        return
    _require_digest_shape(field_name, actual)
    raise ValueError(f"{field_name} must match report contents")


def _normalize_validation_digest(
    field_name: str,
    actual: str,
    expected: str,
) -> str:
    if actual == "":
        return expected
    _require_digest_shape(field_name, actual)
    if actual != expected:
        raise ValueError(f"{field_name} must match report contents")
    return actual


def _require_digest_shape(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    prefix = f"{VALIDATION_DIGEST_ALGORITHM}:"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a sha256 digest")
    digest = value[len(prefix) :]
    if len(digest) != 64 or any(char not in HEX_DIGITS for char in digest):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _json_ready_public_payload(value: object, *, allow_decimal: bool) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_public_payload(asdict(value), allow_decimal=allow_decimal)
    if isinstance(value, dict):
        return {
            str(key): _json_ready_public_payload(item, allow_decimal=allow_decimal)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _json_ready_public_payload(item, allow_decimal=allow_decimal)
            for item in value
        ]
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("payload numeric values must already be JSON strings")
        return format(value, "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is float or type(value) is int:
        raise ValueError("payload must not contain non-Decimal numerics")
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"payload contains unsupported value type {type(value).__name__}")
