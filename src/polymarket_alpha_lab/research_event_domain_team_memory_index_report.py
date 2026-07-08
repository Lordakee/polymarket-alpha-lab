"""Public report-only index of team memory coverage by event domain."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_DOMAIN_TEAM_MEMORY_INDEX_REPORT_CONFIG_VERSION = (
    "research-event-domain-team-memory-index-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
PUBLIC_STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

STRONG_MEMORY_REASON = "research_event_domain_team_memory_index_strong_memory"
STALE_MEMORY_REASON = "research_event_domain_team_memory_index_stale_memory"
BLOCK_STALE_MEMORY_REASON = (
    "research_event_domain_team_memory_index_block_stale_memory"
)
LOW_TEAM_COVERAGE_REASON = (
    "research_event_domain_team_memory_index_low_team_coverage"
)
COVERAGE_GAP_REASON = "research_event_domain_team_memory_index_coverage_gap"
WEAK_MEMORY_REASON = "research_event_domain_team_memory_index_weak_memory"

REPORT_NO_INPUTS_REASON = "research_event_domain_team_memory_index_report_no_inputs"
REPORT_BLOCK_PRESENT_REASON = (
    "research_event_domain_team_memory_index_report_block_present"
)
REPORT_STALE_PRESENT_REASON = (
    "research_event_domain_team_memory_index_report_stale_present"
)
REPORT_COVERAGE_GAP_PRESENT_REASON = (
    "research_event_domain_team_memory_index_report_coverage_gap_present"
)
REPORT_WEAK_MEMORY_PRESENT_REASON = (
    "research_event_domain_team_memory_index_report_weak_memory_present"
)
REPORT_STRONG_MEMORY_PRESENT_REASON = (
    "research_event_domain_team_memory_index_report_strong_memory_present"
)

ROW_REASON_CODE_SEQUENCE = (
    BLOCK_STALE_MEMORY_REASON,
    STALE_MEMORY_REASON,
    LOW_TEAM_COVERAGE_REASON,
    COVERAGE_GAP_REASON,
    WEAK_MEMORY_REASON,
    STRONG_MEMORY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    REPORT_NO_INPUTS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_STALE_PRESENT_REASON,
    REPORT_COVERAGE_GAP_PRESENT_REASON,
    REPORT_WEAK_MEMORY_PRESENT_REASON,
    REPORT_STRONG_MEMORY_PRESENT_REASON,
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
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
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
        "secret",
        "account",
        "balance",
        "cancel",
        "replace",
        "sign",
        "broker",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_DOMAIN_TEAM_MEMORY_INDEX_REPORT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchEventDomainTeamMemoryIndexConfig",
    "ResearchEventDomainTeamMemoryIndexObservation",
    "ResearchEventDomainTeamMemoryIndexReport",
    "ResearchEventDomainTeamMemoryIndexRow",
    "build_research_event_domain_team_memory_index_report",
    "research_event_domain_team_memory_index_report_digest",
    "research_event_domain_team_memory_index_report_payload",
)


@dataclass(frozen=True)
class ResearchEventDomainTeamMemoryIndexConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_DOMAIN_TEAM_MEMORY_INDEX_REPORT_CONFIG_VERSION
    )
    stale_after_seconds: Decimal = Decimal("7776000.000000")
    block_stale_after_seconds: Decimal = Decimal("15552000.000000")
    min_pass_team_count: Decimal = Decimal("2.000000")
    min_pass_coverage_ratio: Decimal = Decimal("0.750000")
    min_strong_memory_score: Decimal = Decimal("0.800000")
    min_watch_memory_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainTeamMemoryIndexConfig:
            raise TypeError(
                "ResearchEventDomainTeamMemoryIndexConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainTeamMemoryIndexConfig:
            raise ValueError(
                "config must be exactly ResearchEventDomainTeamMemoryIndexConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_after_seconds",
            _require_positive_whole_decimal(
                "stale_after_seconds",
                self.stale_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "block_stale_after_seconds",
            _require_positive_whole_decimal(
                "block_stale_after_seconds",
                self.block_stale_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_pass_team_count",
            _require_positive_whole_decimal(
                "min_pass_team_count",
                self.min_pass_team_count,
            ),
        )
        for field_name in (
            "min_pass_coverage_ratio",
            "min_strong_memory_score",
            "min_watch_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_after_seconds > self.block_stale_after_seconds:
            raise ValueError("stale_after_seconds must not exceed block threshold")
        if self.min_watch_memory_score > self.min_strong_memory_score:
            raise ValueError(
                "min_watch_memory_score must not exceed strong memory threshold",
            )
        _reject_unsafe_public_payload("config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchEventDomainTeamMemoryIndexObservation:
    event_domain: str
    event_subdomain: str
    team_key: str
    memory_updated_at: datetime
    memory_strength_score: Decimal
    long_term_memory_count: Decimal
    covered_event_count: Decimal
    total_event_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainTeamMemoryIndexObservation:
            raise TypeError(
                "ResearchEventDomainTeamMemoryIndexObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainTeamMemoryIndexObservation:
            raise ValueError(
                "observation must be exactly ResearchEventDomainTeamMemoryIndexObservation",
            )
        _require_public_string("event_domain", self.event_domain)
        _require_public_string("event_subdomain", self.event_subdomain)
        _require_public_string("team_key", self.team_key)
        object.__setattr__(
            self,
            "memory_updated_at",
            _as_utc("memory_updated_at", self.memory_updated_at),
        )
        object.__setattr__(
            self,
            "memory_strength_score",
            _require_ratio_decimal(
                "memory_strength_score",
                self.memory_strength_score,
            ),
        )
        for field_name in (
            "long_term_memory_count",
            "covered_event_count",
            "total_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.total_event_count == ZERO:
            raise ValueError("total_event_count must be positive")
        if self.covered_event_count > self.total_event_count:
            raise ValueError("covered_event_count must not exceed total_event_count")
        _reject_unsafe_public_payload("observation", self)
        require_paper_only_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventDomainTeamMemoryIndexRow:
    event_domain: str
    event_subdomain: str
    public_status: str
    team_count: Decimal
    long_term_memory_count: Decimal
    coverage_ratio: Decimal
    average_memory_strength_score: Decimal
    newest_memory_age_seconds: Decimal
    oldest_memory_age_seconds: Decimal
    stale_team_count: Decimal
    strong_team_count: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainTeamMemoryIndexRow:
            raise TypeError(
                "ResearchEventDomainTeamMemoryIndexRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainTeamMemoryIndexRow:
            raise ValueError("row must be exactly ResearchEventDomainTeamMemoryIndexRow")
        _require_public_string("event_domain", self.event_domain)
        _require_public_string("event_subdomain", self.event_subdomain)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "team_count",
            "long_term_memory_count",
            "newest_memory_age_seconds",
            "oldest_memory_age_seconds",
            "stale_team_count",
            "strong_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("coverage_ratio", "average_memory_strength_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)
        require_paper_only_flags("row", self)
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
class ResearchEventDomainTeamMemoryIndexReport:
    generated_at: datetime
    config_version: str
    public_status: str
    domain_count: Decimal
    subdomain_count: Decimal
    team_domain_pair_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    strong_memory_subdomain_count: Decimal
    stale_memory_subdomain_count: Decimal
    average_coverage_ratio: Decimal
    average_memory_strength_score: Decimal
    max_oldest_memory_age_seconds: Decimal
    rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainTeamMemoryIndexReport:
            raise TypeError(
                "ResearchEventDomainTeamMemoryIndexReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainTeamMemoryIndexReport:
            raise ValueError(
                "report must be exactly ResearchEventDomainTeamMemoryIndexReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "domain_count",
            "subdomain_count",
            "team_domain_pair_count",
            "pass_count",
            "watch_count",
            "block_count",
            "strong_memory_subdomain_count",
            "stale_memory_subdomain_count",
            "max_oldest_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_coverage_ratio",
            "average_memory_strength_score",
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
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        require_paper_only_flags("report", self)
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
        return research_event_domain_team_memory_index_report_payload(self)


def build_research_event_domain_team_memory_index_report(
    observations: list[ResearchEventDomainTeamMemoryIndexObservation]
    | tuple[ResearchEventDomainTeamMemoryIndexObservation, ...],
    *,
    config: ResearchEventDomainTeamMemoryIndexConfig,
    generated_at: datetime,
) -> ResearchEventDomainTeamMemoryIndexReport:
    if type(config) is not ResearchEventDomainTeamMemoryIndexConfig:
        raise ValueError("config must be a ResearchEventDomainTeamMemoryIndexConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)

    if not normalized_observations:
        return ResearchEventDomainTeamMemoryIndexReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            public_status=STATUS_BLOCK,
            domain_count=ZERO,
            subdomain_count=ZERO,
            team_domain_pair_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            strong_memory_subdomain_count=ZERO,
            stale_memory_subdomain_count=ZERO,
            average_coverage_ratio=ZERO,
            average_memory_strength_score=ZERO,
            max_oldest_memory_age_seconds=ZERO,
            rows=(),
            reason_codes=(REPORT_NO_INPUTS_REASON,),
        )

    rows = tuple(
        sorted(
            (
                _build_row(
                    group,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for group in _observation_groups(normalized_observations)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventDomainTeamMemoryIndexReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        public_status=_report_public_status(rows),
        domain_count=_decimal_count_from_int(
            len({observation.event_domain for observation in normalized_observations}),
        ),
        subdomain_count=_decimal_count_from_int(len(rows)),
        team_domain_pair_count=_decimal_count_from_int(
            len(
                {
                    (
                        observation.event_domain,
                        observation.event_subdomain,
                        observation.team_key,
                    )
                    for observation in normalized_observations
                },
            ),
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        strong_memory_subdomain_count=_reason_count(rows, STRONG_MEMORY_REASON),
        stale_memory_subdomain_count=_reason_count_any(
            rows,
            (BLOCK_STALE_MEMORY_REASON, STALE_MEMORY_REASON),
        ),
        average_coverage_ratio=_average_decimal(
            tuple(row.coverage_ratio for row in rows),
        ),
        average_memory_strength_score=_average_decimal(
            tuple(row.average_memory_strength_score for row in rows),
        ),
        max_oldest_memory_age_seconds=max(
            (row.oldest_memory_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_event_domain_team_memory_index_report_payload(
    report: ResearchEventDomainTeamMemoryIndexReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventDomainTeamMemoryIndexReport:
        _validate_report_runtime(report)
        payload = _json_ready_public_payload(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        _validate_payload_statuses(report)
        payload = _json_ready_public_payload(report, allow_decimal=False)
    else:
        raise ValueError(
            "report must be a ResearchEventDomainTeamMemoryIndexReport",
        )
    if type(payload) is not dict:
        raise ValueError("domain team memory index payload must be a JSON object")
    _validate_report_payload(payload)
    _reject_unsafe_public_payload("domain team memory index payload", payload)
    return payload


def research_event_domain_team_memory_index_report_digest(
    report: ResearchEventDomainTeamMemoryIndexReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_event_domain_team_memory_index_report_payload(report)
    digest_keys = (
        "generated_at",
        "config_version",
        "public_status",
        "domain_count",
        "subdomain_count",
        "team_domain_pair_count",
        "pass_count",
        "watch_count",
        "block_count",
        "strong_memory_subdomain_count",
        "stale_memory_subdomain_count",
        "average_coverage_ratio",
        "average_memory_strength_score",
        "max_oldest_memory_age_seconds",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    return {key: payload[key] for key in digest_keys}


def _build_row(
    observations: tuple[ResearchEventDomainTeamMemoryIndexObservation, ...],
    *,
    config: ResearchEventDomainTeamMemoryIndexConfig,
    generated_at: datetime,
) -> ResearchEventDomainTeamMemoryIndexRow:
    event_domain = observations[0].event_domain
    event_subdomain = observations[0].event_subdomain
    ages = tuple(
        _age_seconds(
            "memory_updated_at",
            observation.memory_updated_at,
            generated_at,
        )
        for observation in observations
    )
    team_count = _decimal_count_from_int(
        len({observation.team_key for observation in observations}),
    )
    long_term_memory_count = _sum_decimal(
        observation.long_term_memory_count for observation in observations
    )
    coverage_ratio = _ratio(
        _sum_decimal(observation.covered_event_count for observation in observations),
        _sum_decimal(observation.total_event_count for observation in observations),
    )
    average_memory_strength_score = _average_decimal(
        tuple(observation.memory_strength_score for observation in observations),
    )
    reason_codes = _row_reason_codes(
        team_count=team_count,
        coverage_ratio=coverage_ratio,
        average_memory_strength_score=average_memory_strength_score,
        oldest_memory_age_seconds=max(ages),
        config=config,
    )
    return ResearchEventDomainTeamMemoryIndexRow(
        event_domain=event_domain,
        event_subdomain=event_subdomain,
        public_status=_row_public_status(reason_codes),
        team_count=team_count,
        long_term_memory_count=long_term_memory_count,
        coverage_ratio=coverage_ratio,
        average_memory_strength_score=average_memory_strength_score,
        newest_memory_age_seconds=min(ages),
        oldest_memory_age_seconds=max(ages),
        stale_team_count=_decimal_count_from_int(
            sum(1 for age in ages if age >= config.stale_after_seconds),
        ),
        strong_team_count=_decimal_count_from_int(
            sum(
                1
                for observation in observations
                if observation.memory_strength_score >= config.min_strong_memory_score
            ),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    team_count: Decimal,
    coverage_ratio: Decimal,
    average_memory_strength_score: Decimal,
    oldest_memory_age_seconds: Decimal,
    config: ResearchEventDomainTeamMemoryIndexConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if oldest_memory_age_seconds >= config.block_stale_after_seconds:
        reason_codes.append(BLOCK_STALE_MEMORY_REASON)
    elif oldest_memory_age_seconds >= config.stale_after_seconds:
        reason_codes.append(STALE_MEMORY_REASON)
    if team_count < config.min_pass_team_count:
        reason_codes.append(LOW_TEAM_COVERAGE_REASON)
    if coverage_ratio < config.min_pass_coverage_ratio:
        reason_codes.append(COVERAGE_GAP_REASON)
    if average_memory_strength_score < config.min_watch_memory_score:
        reason_codes.append(WEAK_MEMORY_REASON)
    return _normalize_row_reason_codes(
        "reason_codes",
        tuple(reason_codes) or (STRONG_MEMORY_REASON,),
    )


def _row_public_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            BLOCK_STALE_MEMORY_REASON,
            LOW_TEAM_COVERAGE_REASON,
            WEAK_MEMORY_REASON,
        )
    ):
        return STATUS_BLOCK
    if any(
        reason_code in reason_codes
        for reason_code in (STALE_MEMORY_REASON, COVERAGE_GAP_REASON)
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _report_public_status(rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REPORT_NO_INPUTS_REASON,)
    reason_codes: list[str] = []
    row_reason_codes = {
        reason_code for row in rows for reason_code in row.reason_codes
    }
    if any(row.public_status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if row_reason_codes.intersection(
        {BLOCK_STALE_MEMORY_REASON, STALE_MEMORY_REASON},
    ):
        reason_codes.append(REPORT_STALE_PRESENT_REASON)
    if COVERAGE_GAP_REASON in row_reason_codes:
        reason_codes.append(REPORT_COVERAGE_GAP_PRESENT_REASON)
    if WEAK_MEMORY_REASON in row_reason_codes:
        reason_codes.append(REPORT_WEAK_MEMORY_PRESENT_REASON)
    if STRONG_MEMORY_REASON in row_reason_codes:
        reason_codes.append(REPORT_STRONG_MEMORY_PRESENT_REASON)
    return _normalize_report_reason_codes("reason_codes", tuple(reason_codes))


def _observation_groups(
    observations: tuple[ResearchEventDomainTeamMemoryIndexObservation, ...],
) -> tuple[tuple[ResearchEventDomainTeamMemoryIndexObservation, ...], ...]:
    grouped: dict[
        tuple[str, str],
        list[ResearchEventDomainTeamMemoryIndexObservation],
    ] = {}
    for observation in observations:
        key = (observation.event_domain, observation.event_subdomain)
        grouped.setdefault(key, []).append(observation)
    return tuple(
        tuple(grouped[key])
        for key in sorted(grouped)
    )


def _normalize_observations(
    observations: list[ResearchEventDomainTeamMemoryIndexObservation]
    | tuple[ResearchEventDomainTeamMemoryIndexObservation, ...],
) -> tuple[ResearchEventDomainTeamMemoryIndexObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchEventDomainTeamMemoryIndexObservation:
            raise ValueError(
                "observations must contain ResearchEventDomainTeamMemoryIndexObservation",
            )
        require_paper_only_flags("observation", observation)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...],
) -> tuple[ResearchEventDomainTeamMemoryIndexRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventDomainTeamMemoryIndexRow:
            raise ValueError("rows must contain ResearchEventDomainTeamMemoryIndexRow")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by public status and domain")
    return rows


def _row_sort_key(row: ResearchEventDomainTeamMemoryIndexRow) -> tuple[int, str, str]:
    return (
        PUBLIC_STATUS_SORT_SEQUENCE.index(row.public_status),
        row.event_domain,
        row.event_subdomain,
    )


def _status_count(
    rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count_from_int(sum(1 for row in rows if row.public_status == status))


def _reason_count(
    rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count_from_int(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _reason_count_any(
    rows: tuple[ResearchEventDomainTeamMemoryIndexRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count_from_int(
        sum(
            1
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in reason_codes)
        ),
    )


def _validate_row(row: ResearchEventDomainTeamMemoryIndexRow) -> None:
    if row.newest_memory_age_seconds > row.oldest_memory_age_seconds:
        raise ValueError("newest_memory_age_seconds must not exceed oldest")
    if row.stale_team_count > row.team_count:
        raise ValueError("stale_team_count must not exceed team_count")
    if row.strong_team_count > row.team_count:
        raise ValueError("strong_team_count must not exceed team_count")
    if row.long_term_memory_count < row.team_count:
        raise ValueError("long_term_memory_count must be at least team_count")
    if row.public_status != _row_public_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    if STRONG_MEMORY_REASON in row.reason_codes and row.reason_codes != (
        STRONG_MEMORY_REASON,
    ):
        raise ValueError("strong memory reason must be standalone")


def _validate_report(report: ResearchEventDomainTeamMemoryIndexReport) -> None:
    rows = report.rows
    if report.public_status != _report_public_status(rows):
        raise ValueError("public_status must match rows")
    if report.domain_count != _decimal_count_from_int(
        len({row.event_domain for row in rows}),
    ):
        raise ValueError("domain_count must match rows")
    if report.subdomain_count != _decimal_count_from_int(len(rows)):
        raise ValueError("subdomain_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.strong_memory_subdomain_count != _reason_count(rows, STRONG_MEMORY_REASON):
        raise ValueError("strong_memory_subdomain_count must match rows")
    if report.stale_memory_subdomain_count != _reason_count_any(
        rows,
        (BLOCK_STALE_MEMORY_REASON, STALE_MEMORY_REASON),
    ):
        raise ValueError("stale_memory_subdomain_count must match rows")
    if report.average_coverage_ratio != _average_decimal(
        tuple(row.coverage_ratio for row in rows),
    ):
        raise ValueError("average_coverage_ratio must match rows")
    if report.average_memory_strength_score != _average_decimal(
        tuple(row.average_memory_strength_score for row in rows),
    ):
        raise ValueError("average_memory_strength_score must match rows")
    if report.max_oldest_memory_age_seconds != max(
        (row.oldest_memory_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_oldest_memory_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_runtime(report: ResearchEventDomainTeamMemoryIndexReport) -> None:
    expected_digest = _report_validation_digest(report)
    if report.validation_digest != expected_digest:
        raise ValueError("validation_digest must match report contents")


def _validate_report_payload(payload: dict[str, Any]) -> None:
    _require_payload_flags(payload)
    _validate_payload_statuses(payload)
    _require_sha256_digest("validation_digest", payload.get("validation_digest"))
    expected_digest = _payload_validation_digest(payload)
    if payload["validation_digest"] != expected_digest:
        raise ValueError("validation_digest must match report contents")


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    public_status = payload.get("public_status")
    if public_status not in PUBLIC_STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    for row in payload.get("rows", []):
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        row_status = row.get("public_status")
        if row_status not in PUBLIC_STATUSES:
            raise ValueError("row public_status must be pass, watch, or block")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _row_validation_digest(row: ResearchEventDomainTeamMemoryIndexRow) -> str:
    payload = _json_ready_public_payload(
        {
            "event_domain": row.event_domain,
            "event_subdomain": row.event_subdomain,
            "public_status": row.public_status,
            "team_count": row.team_count,
            "long_term_memory_count": row.long_term_memory_count,
            "coverage_ratio": row.coverage_ratio,
            "average_memory_strength_score": row.average_memory_strength_score,
            "newest_memory_age_seconds": row.newest_memory_age_seconds,
            "oldest_memory_age_seconds": row.oldest_memory_age_seconds,
            "stale_team_count": row.stale_team_count,
            "strong_team_count": row.strong_team_count,
            "reason_codes": row.reason_codes,
            "paper_only": row.paper_only,
            "report_only": row.report_only,
            "readonly": row.readonly,
        },
        allow_decimal=True,
    )
    return _digest_payload(payload)


def _report_validation_digest(report: ResearchEventDomainTeamMemoryIndexReport) -> str:
    payload = _json_ready_public_payload(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "public_status": report.public_status,
            "domain_count": report.domain_count,
            "subdomain_count": report.subdomain_count,
            "team_domain_pair_count": report.team_domain_pair_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "strong_memory_subdomain_count": report.strong_memory_subdomain_count,
            "stale_memory_subdomain_count": report.stale_memory_subdomain_count,
            "average_coverage_ratio": report.average_coverage_ratio,
            "average_memory_strength_score": report.average_memory_strength_score,
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
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _age_seconds(field_name: str, observed_at: datetime, generated_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(seconds)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a public string")
    _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    reject_unsafe_surface_fields(label, payload)
    _walk_public_payload(label, payload)


def _walk_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _walk_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_text(label, key)
            _walk_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _walk_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_row_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        field_name,
        value,
        allowed_values=ROW_REASON_CODE_SEQUENCE,
    )


def _normalize_report_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        field_name,
        value,
        allowed_values=REPORT_REASON_CODE_SEQUENCE,
    )


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    *,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in allowed_values if reason_code in normalized
    )


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_count_from_int(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _decimal_count_from_int(len(values)))
