"""Pure report-only research team domain memory summary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SUMMARY_CONFIG_VERSION = (
    "research-team-domain-memory-summary-v0"
)
DEFAULT_RESEARCH_TEAM_MEMORY_DOMAINS = (
    "politics",
    "macro",
    "crypto",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_ERROR_RATE_PENALTY = Decimal("4.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUSES = ("pass", "watch", "block")
_ROW_REASON_CODE_SEQUENCE = (
    "domain_memory_summary_pass",
    "domain_memory_summary_watch",
    "domain_memory_summary_block",
    "missing_domain_memory",
    "experience_depth_pass",
    "experience_depth_watch",
    "experience_depth_low",
    "error_pattern_rate_pass",
    "error_pattern_rate_watch",
    "error_pattern_rate_high",
    "postmortem_quality_pass",
    "postmortem_quality_watch",
    "postmortem_quality_low",
    "memory_quality_pass",
    "memory_quality_watch",
    "memory_quality_low",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "domain_memory_summary_report_pass",
    "domain_memory_summary_report_block_rows",
    "domain_memory_summary_report_watch_rows",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_ref",
    "source_refs",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommendation",
    "position",
    "supabase",
    "database",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SUMMARY_CONFIG_VERSION",
    "DEFAULT_RESEARCH_TEAM_MEMORY_DOMAINS",
    "ResearchTeamDomainMemorySummaryConfig",
    "ResearchTeamDomainMemoryObservation",
    "ResearchTeamDomainMemorySummaryRow",
    "ResearchTeamDomainMemorySummaryReport",
    "build_research_team_domain_memory_summary",
    "research_team_domain_memory_summary_payload",
)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySummaryConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SUMMARY_CONFIG_VERSION
    domain_ids: tuple[str, ...] = DEFAULT_RESEARCH_TEAM_MEMORY_DOMAINS
    min_pass_experience_count: Decimal = Decimal("20.000000")
    min_watch_experience_count: Decimal = Decimal("5.000000")
    max_pass_error_pattern_rate: Decimal = Decimal("0.100000")
    max_watch_error_pattern_rate: Decimal = Decimal("0.250000")
    min_pass_postmortem_quality_rate: Decimal = Decimal("0.800000")
    min_watch_postmortem_quality_rate: Decimal = Decimal("0.500000")
    min_pass_memory_quality_score: Decimal = Decimal("0.750000")
    min_watch_memory_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemorySummaryConfig:
            raise ValueError(
                "config must be exactly ResearchTeamDomainMemorySummaryConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        object.__setattr__(self, "domain_ids", _normalize_domain_ids(self.domain_ids))
        for field_name in (
            "min_pass_experience_count",
            "min_watch_experience_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_error_pattern_rate",
            "max_watch_error_pattern_rate",
            "min_pass_postmortem_quality_rate",
            "min_watch_postmortem_quality_rate",
            "min_pass_memory_quality_score",
            "min_watch_memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryObservation:
    domain_id: str
    team_id: str
    experience_count: Decimal
    error_pattern_count: Decimal
    postmortem_count: Decimal
    high_quality_postmortem_count: Decimal
    memory_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemoryObservation:
            raise ValueError(
                "observation must be exactly ResearchTeamDomainMemoryObservation",
            )
        object.__setattr__(
            self,
            "domain_id",
            _require_public_identifier("domain_id", self.domain_id),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        for field_name in (
            "experience_count",
            "error_pattern_count",
            "postmortem_count",
            "high_quality_postmortem_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.error_pattern_count > self.experience_count:
            raise ValueError("error_pattern_count must not exceed experience_count")
        if self.high_quality_postmortem_count > self.postmortem_count:
            raise ValueError(
                "high_quality_postmortem_count must not exceed postmortem_count",
            )
        object.__setattr__(
            self,
            "memory_quality_score",
            _require_ratio_decimal("memory_quality_score", self.memory_quality_score),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySummaryRow:
    domain_id: str
    observation_count: Decimal
    contributing_team_count: Decimal
    experience_count: Decimal
    error_pattern_count: Decimal
    error_pattern_rate: Decimal
    postmortem_count: Decimal
    high_quality_postmortem_count: Decimal
    postmortem_quality_rate: Decimal
    memory_quality_score: Decimal
    domain_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemorySummaryRow:
            raise ValueError("row must be exactly ResearchTeamDomainMemorySummaryRow")
        object.__setattr__(
            self,
            "domain_id",
            _require_public_identifier("domain_id", self.domain_id),
        )
        for field_name in (
            "observation_count",
            "contributing_team_count",
            "experience_count",
            "error_pattern_count",
            "postmortem_count",
            "high_quality_postmortem_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.error_pattern_count > self.experience_count:
            raise ValueError("error_pattern_count must not exceed experience_count")
        if self.high_quality_postmortem_count > self.postmortem_count:
            raise ValueError(
                "high_quality_postmortem_count must not exceed postmortem_count",
            )
        for field_name in (
            "error_pattern_rate",
            "postmortem_quality_rate",
            "memory_quality_score",
            "domain_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemorySummaryReport:
    generated_at: datetime
    config_version: str
    report_status: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_experience_count: Decimal
    total_error_pattern_count: Decimal
    total_postmortem_count: Decimal
    total_high_quality_postmortem_count: Decimal
    average_domain_memory_score: Decimal
    lowest_domain_memory_score: Decimal
    rows: tuple[ResearchTeamDomainMemorySummaryRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemorySummaryReport:
            raise ValueError(
                "report must be exactly ResearchTeamDomainMemorySummaryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_status("report_status", self.report_status)
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_experience_count",
            "total_error_pattern_count",
            "total_postmortem_count",
            "total_high_quality_postmortem_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_domain_memory_score",
            "lowest_domain_memory_score",
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_team_domain_memory_summary(
    observations: Sequence[ResearchTeamDomainMemoryObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemorySummaryConfig | None = None,
) -> ResearchTeamDomainMemorySummaryReport:
    if config is None:
        config = ResearchTeamDomainMemorySummaryConfig()
    if type(config) is not ResearchTeamDomainMemorySummaryConfig:
        raise ValueError("config must be a ResearchTeamDomainMemorySummaryConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_domain(
            domain_id=domain_id,
            observations=tuple(
                item for item in normalized_observations if item.domain_id == domain_id
            ),
            config=config,
        )
        for domain_id in config.domain_ids
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "domain_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "total_experience_count": _sum_decimal(
            row.experience_count for row in rows
        ),
        "total_error_pattern_count": _sum_decimal(
            row.error_pattern_count for row in rows
        ),
        "total_postmortem_count": _sum_decimal(row.postmortem_count for row in rows),
        "total_high_quality_postmortem_count": _sum_decimal(
            row.high_quality_postmortem_count for row in rows
        ),
        "average_domain_memory_score": _average_domain_memory_score(rows),
        "lowest_domain_memory_score": _lowest_domain_memory_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainMemorySummaryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_memory_summary_payload(
    report: ResearchTeamDomainMemorySummaryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainMemorySummaryReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamDomainMemorySummaryReport or payload",
    )


@dataclass(frozen=True)
class _DictFlags:
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


def _row_for_domain(
    *,
    domain_id: str,
    observations: tuple[ResearchTeamDomainMemoryObservation, ...],
    config: ResearchTeamDomainMemorySummaryConfig,
) -> ResearchTeamDomainMemorySummaryRow:
    experience_count = _sum_decimal(item.experience_count for item in observations)
    error_pattern_count = _sum_decimal(item.error_pattern_count for item in observations)
    postmortem_count = _sum_decimal(item.postmortem_count for item in observations)
    high_quality_postmortem_count = _sum_decimal(
        item.high_quality_postmortem_count for item in observations
    )
    error_pattern_rate = _ratio_or_zero(error_pattern_count, experience_count)
    postmortem_quality_rate = _ratio_or_zero(
        high_quality_postmortem_count,
        postmortem_count,
    )
    memory_quality_score = _average_memory_quality_score(observations)
    domain_memory_score = _domain_memory_score(
        experience_count=experience_count,
        error_pattern_rate=error_pattern_rate,
        postmortem_quality_rate=postmortem_quality_rate,
        memory_quality_score=memory_quality_score,
        config=config,
    )
    status = _row_status(
        experience_count=experience_count,
        error_pattern_rate=error_pattern_rate,
        postmortem_quality_rate=postmortem_quality_rate,
        memory_quality_score=memory_quality_score,
        domain_memory_score=domain_memory_score,
        config=config,
    )
    team_count = len({item.team_id for item in observations})
    return ResearchTeamDomainMemorySummaryRow(
        domain_id=domain_id,
        observation_count=_decimal_count(len(observations)),
        contributing_team_count=_decimal_count(team_count),
        experience_count=experience_count,
        error_pattern_count=error_pattern_count,
        error_pattern_rate=error_pattern_rate,
        postmortem_count=postmortem_count,
        high_quality_postmortem_count=high_quality_postmortem_count,
        postmortem_quality_rate=postmortem_quality_rate,
        memory_quality_score=memory_quality_score,
        domain_memory_score=domain_memory_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation_count=_decimal_count(len(observations)),
            experience_count=experience_count,
            error_pattern_rate=error_pattern_rate,
            postmortem_quality_rate=postmortem_quality_rate,
            memory_quality_score=memory_quality_score,
            status=status,
            config=config,
        ),
    )


def _domain_memory_score(
    *,
    experience_count: Decimal,
    error_pattern_rate: Decimal,
    postmortem_quality_rate: Decimal,
    memory_quality_score: Decimal,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> Decimal:
    experience_depth_score = _clamp_ratio(experience_count / config.min_pass_experience_count)
    error_quality_score = _clamp_ratio(_ONE - error_pattern_rate * _ERROR_RATE_PENALTY)
    return _clamp_ratio(
        (
            experience_depth_score
            + error_quality_score
            + postmortem_quality_rate
            + memory_quality_score
        )
        / Decimal("4.000000"),
    )


def _row_status(
    *,
    experience_count: Decimal,
    error_pattern_rate: Decimal,
    postmortem_quality_rate: Decimal,
    memory_quality_score: Decimal,
    domain_memory_score: Decimal,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> str:
    if (
        experience_count < config.min_watch_experience_count
        or error_pattern_rate > config.max_watch_error_pattern_rate
        or postmortem_quality_rate < config.min_watch_postmortem_quality_rate
        or memory_quality_score < config.min_watch_memory_quality_score
        or domain_memory_score < config.min_watch_memory_quality_score
    ):
        return "block"
    if (
        experience_count < config.min_pass_experience_count
        or error_pattern_rate > config.max_pass_error_pattern_rate
        or postmortem_quality_rate < config.min_pass_postmortem_quality_rate
        or memory_quality_score < config.min_pass_memory_quality_score
        or domain_memory_score < config.min_pass_memory_quality_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observation_count: Decimal,
    experience_count: Decimal,
    error_pattern_rate: Decimal,
    postmortem_quality_rate: Decimal,
    memory_quality_score: Decimal,
    status: str,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> tuple[str, ...]:
    codes = [f"domain_memory_summary_{status}"]
    if observation_count == _ZERO:
        codes.append("missing_domain_memory")
    codes.append(_experience_depth_reason(experience_count, config))
    codes.append(_error_pattern_rate_reason(error_pattern_rate, config))
    codes.append(_postmortem_quality_reason(postmortem_quality_rate, config))
    codes.append(_memory_quality_reason(memory_quality_score, config))
    return _normalize_row_reason_codes(tuple(codes))


def _experience_depth_reason(
    value: Decimal,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> str:
    if value >= config.min_pass_experience_count:
        return "experience_depth_pass"
    if value >= config.min_watch_experience_count:
        return "experience_depth_watch"
    return "experience_depth_low"


def _error_pattern_rate_reason(
    value: Decimal,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> str:
    if value <= config.max_pass_error_pattern_rate:
        return "error_pattern_rate_pass"
    if value <= config.max_watch_error_pattern_rate:
        return "error_pattern_rate_watch"
    return "error_pattern_rate_high"


def _postmortem_quality_reason(
    value: Decimal,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> str:
    if value >= config.min_pass_postmortem_quality_rate:
        return "postmortem_quality_pass"
    if value >= config.min_watch_postmortem_quality_rate:
        return "postmortem_quality_watch"
    return "postmortem_quality_low"


def _memory_quality_reason(
    value: Decimal,
    config: ResearchTeamDomainMemorySummaryConfig,
) -> str:
    if value >= config.min_pass_memory_quality_score:
        return "memory_quality_pass"
    if value >= config.min_watch_memory_quality_score:
        return "memory_quality_watch"
    return "memory_quality_low"


def _report_status(rows: tuple[ResearchTeamDomainMemorySummaryRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemorySummaryRow, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("domain_memory_summary_report_block_rows")
    if any(row.status == "watch" for row in rows):
        codes.append("domain_memory_summary_report_watch_rows")
    if not codes:
        codes.append("domain_memory_summary_report_pass")
    return _normalize_report_reason_codes(tuple(codes))


def _status_count(
    rows: tuple[ResearchTeamDomainMemorySummaryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_domain_memory_score(
    rows: tuple[ResearchTeamDomainMemorySummaryRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _quantize(_sum_decimal(row.domain_memory_score for row in rows) / Decimal(len(rows)))


def _lowest_domain_memory_score(
    rows: tuple[ResearchTeamDomainMemorySummaryRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.domain_memory_score for row in rows)


def _average_memory_quality_score(
    observations: tuple[ResearchTeamDomainMemoryObservation, ...],
) -> Decimal:
    if not observations:
        return _ZERO
    return _quantize(
        _sum_decimal(item.memory_quality_score for item in observations)
        / Decimal(len(observations)),
    )


def _normalize_observations(
    observations: Sequence[ResearchTeamDomainMemoryObservation],
) -> tuple[ResearchTeamDomainMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchTeamDomainMemoryObservation] = []
    seen_keys: set[tuple[str, str]] = set()
    for observation in observations:
        if type(observation) is not ResearchTeamDomainMemoryObservation:
            raise ValueError(
                "observations must contain ResearchTeamDomainMemoryObservation",
            )
        _require_hard_flags("observation", observation)
        key = (observation.domain_id, observation.team_id)
        if key in seen_keys:
            raise ValueError("duplicate domain/team observation")
        seen_keys.add(key)
        normalized.append(observation)
    return tuple(sorted(normalized, key=lambda item: (item.domain_id, item.team_id)))


def _normalize_rows(
    rows: Sequence[ResearchTeamDomainMemorySummaryRow],
) -> tuple[ResearchTeamDomainMemorySummaryRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamDomainMemorySummaryRow] = []
    seen_domains: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainMemorySummaryRow:
            raise ValueError("rows must contain ResearchTeamDomainMemorySummaryRow")
        _require_hard_flags("row", row)
        if row.domain_id in seen_domains:
            raise ValueError("duplicate domain row")
        seen_domains.add(row.domain_id)
        normalized.append(row)
    return tuple(normalized)


def _normalize_domain_ids(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("domain_ids must be a sequence")
    domain_ids = tuple(_require_public_identifier("domain_id", item) for item in value)
    if not domain_ids:
        raise ValueError("domain_ids must not be empty")
    if len(set(domain_ids)) != len(domain_ids):
        raise ValueError("domain_ids must be unique")
    return domain_ids


def _normalize_row_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(reason_codes, _ROW_REASON_CODE_SEQUENCE)


def _normalize_report_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(reason_codes, _REPORT_REASON_CODE_SEQUENCE)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in known_reason_codes:
            raise ValueError("reason_codes must contain supported values")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in known_reason_codes if reason_code in normalized
    )


def _validate_config(config: ResearchTeamDomainMemorySummaryConfig) -> None:
    if config.min_watch_experience_count > config.min_pass_experience_count:
        raise ValueError("min_watch_experience_count must not exceed min_pass_experience_count")
    if config.max_pass_error_pattern_rate > config.max_watch_error_pattern_rate:
        raise ValueError("max_pass_error_pattern_rate must not exceed max_watch_error_pattern_rate")
    if config.min_watch_postmortem_quality_rate > config.min_pass_postmortem_quality_rate:
        raise ValueError(
            "min_watch_postmortem_quality_rate must not exceed "
            "min_pass_postmortem_quality_rate",
        )
    if config.min_watch_memory_quality_score > config.min_pass_memory_quality_score:
        raise ValueError(
            "min_watch_memory_quality_score must not exceed "
            "min_pass_memory_quality_score",
        )


def _validate_row(row: ResearchTeamDomainMemorySummaryRow) -> None:
    expected_status_code = f"domain_memory_summary_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("row status must match reason_codes")
    if row.observation_count == _ZERO and "missing_domain_memory" not in row.reason_codes:
        raise ValueError("missing rows must include missing_domain_memory")
    if row.observation_count > _ZERO and "missing_domain_memory" in row.reason_codes:
        raise ValueError("observed rows must not include missing_domain_memory")


def _validate_report(report: ResearchTeamDomainMemorySummaryReport) -> None:
    rows = report.rows
    if report.domain_count != _decimal_count(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.total_experience_count != _sum_decimal(row.experience_count for row in rows):
        raise ValueError("total_experience_count must match rows")
    if report.total_error_pattern_count != _sum_decimal(row.error_pattern_count for row in rows):
        raise ValueError("total_error_pattern_count must match rows")
    if report.total_postmortem_count != _sum_decimal(row.postmortem_count for row in rows):
        raise ValueError("total_postmortem_count must match rows")
    if report.total_high_quality_postmortem_count != _sum_decimal(
        row.high_quality_postmortem_count for row in rows
    ):
        raise ValueError("total_high_quality_postmortem_count must match rows")
    if report.average_domain_memory_score != _average_domain_memory_score(rows):
        raise ValueError("average_domain_memory_score must match rows")
    if report.lowest_domain_memory_score != _lowest_domain_memory_score(rows):
        raise ValueError("lowest_domain_memory_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_for_json_payload(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _report_values_without_digest(
    report: ResearchTeamDomainMemorySummaryReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_for_json_payload(_json_ready(values))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _sum_decimal(values: Any) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized.quantize(_COUNT_QUANT) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"unsafe public payload at {field_name}")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public payload at {field_name}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_string(item_path, key)
            if key in _PHASE_FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None or type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")
