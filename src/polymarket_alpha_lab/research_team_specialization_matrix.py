"""Pure report-only research team specialization matrix."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_SPECIALIZATION_MATRIX_CONFIG_VERSION = (
    "research-team-specialization-matrix-v1"
)
DEFAULT_RESEARCH_TEAM_SPECIALIZATION_DOMAINS = (
    "politics",
    "macro",
    "crypto",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
)
RESEARCH_TEAM_SPECIALIZATION_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_ROW_REASON_CODE_SEQUENCE = (
    "specialization_matrix_pass",
    "specialization_matrix_watch",
    "specialization_matrix_block",
    "missing_domain_specialization",
    "role_coverage_pass",
    "role_coverage_watch",
    "role_coverage_low",
    "memory_quality_pass",
    "memory_quality_watch",
    "memory_quality_low",
    "capacity_pass",
    "capacity_watch",
    "capacity_low",
    "review_quality_pass",
    "review_quality_watch",
    "review_quality_low",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "specialization_matrix_report_pass",
    "specialization_matrix_report_block_rows",
    "specialization_matrix_report_watch_rows",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "ref",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchTeamSpecializationMatrixConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_SPECIALIZATION_MATRIX_CONFIG_VERSION
    domain_ids: tuple[str, ...] = DEFAULT_RESEARCH_TEAM_SPECIALIZATION_DOMAINS
    min_pass_role_coverage_ratio: Decimal = Decimal("1.000000")
    min_watch_role_coverage_ratio: Decimal = Decimal("0.800000")
    min_pass_memory_quality_score: Decimal = Decimal("0.750000")
    min_watch_memory_quality_score: Decimal = Decimal("0.500000")
    min_pass_capacity_ratio: Decimal = Decimal("0.250000")
    min_watch_capacity_ratio: Decimal = Decimal("0.100000")
    min_pass_review_quality_ratio: Decimal = Decimal("0.800000")
    min_watch_review_quality_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecializationMatrixConfig:
            raise ValueError(
                "config must be exactly ResearchTeamSpecializationMatrixConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        object.__setattr__(self, "domain_ids", _normalize_domain_ids(self.domain_ids))
        for field_name in (
            "min_pass_role_coverage_ratio",
            "min_watch_role_coverage_ratio",
            "min_pass_memory_quality_score",
            "min_watch_memory_quality_score",
            "min_pass_capacity_ratio",
            "min_watch_capacity_ratio",
            "min_pass_review_quality_ratio",
            "min_watch_review_quality_ratio",
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
class ResearchTeamSpecializationObservation:
    domain_id: str
    team_code: str
    covered_role_count: Decimal
    required_role_count: Decimal
    memory_quality_score: Decimal
    available_capacity_count: Decimal
    required_capacity_count: Decimal
    review_count: Decimal
    high_quality_review_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecializationObservation:
            raise ValueError(
                "observation must be exactly ResearchTeamSpecializationObservation",
            )
        object.__setattr__(
            self,
            "domain_id",
            _require_public_identifier("domain_id", self.domain_id),
        )
        object.__setattr__(
            self,
            "team_code",
            _require_public_identifier("team_code", self.team_code),
        )
        for field_name in (
            "covered_role_count",
            "available_capacity_count",
            "review_count",
            "high_quality_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("required_role_count", "required_capacity_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_quality_score",
            _require_ratio_decimal("memory_quality_score", self.memory_quality_score),
        )
        if self.covered_role_count > self.required_role_count:
            raise ValueError("covered_role_count must not exceed required_role_count")
        if self.available_capacity_count > self.required_capacity_count:
            raise ValueError(
                "available_capacity_count must not exceed required_capacity_count",
            )
        if self.high_quality_review_count > self.review_count:
            raise ValueError("high_quality_review_count must not exceed review_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecializationMatrixRow:
    domain_id: str
    observation_count: Decimal
    covered_role_count: Decimal
    required_role_count: Decimal
    role_coverage_ratio: Decimal
    memory_quality_score: Decimal
    available_capacity_count: Decimal
    required_capacity_count: Decimal
    capacity_ratio: Decimal
    review_count: Decimal
    high_quality_review_count: Decimal
    review_quality_ratio: Decimal
    specialization_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecializationMatrixRow:
            raise ValueError("row must be exactly ResearchTeamSpecializationMatrixRow")
        object.__setattr__(
            self,
            "domain_id",
            _require_public_identifier("domain_id", self.domain_id),
        )
        for field_name in (
            "observation_count",
            "covered_role_count",
            "required_role_count",
            "available_capacity_count",
            "required_capacity_count",
            "review_count",
            "high_quality_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.covered_role_count > self.required_role_count:
            raise ValueError("covered_role_count must not exceed required_role_count")
        if self.available_capacity_count > self.required_capacity_count:
            raise ValueError(
                "available_capacity_count must not exceed required_capacity_count",
            )
        if self.high_quality_review_count > self.review_count:
            raise ValueError("high_quality_review_count must not exceed review_count")
        for field_name in (
            "role_coverage_ratio",
            "memory_quality_score",
            "capacity_ratio",
            "review_quality_ratio",
            "specialization_score",
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
class ResearchTeamSpecializationMatrixReport:
    generated_at: datetime
    config_version: str
    report_status: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_covered_role_count: Decimal
    total_required_role_count: Decimal
    total_available_capacity_count: Decimal
    total_required_capacity_count: Decimal
    total_review_count: Decimal
    total_high_quality_review_count: Decimal
    average_specialization_score: Decimal
    lowest_specialization_score: Decimal
    rows: tuple[ResearchTeamSpecializationMatrixRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamSpecializationMatrixReport:
            raise ValueError(
                "report must be exactly ResearchTeamSpecializationMatrixReport",
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
            "total_covered_role_count",
            "total_required_role_count",
            "total_available_capacity_count",
            "total_required_capacity_count",
            "total_review_count",
            "total_high_quality_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_specialization_score",
            "lowest_specialization_score",
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
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
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


def build_research_team_specialization_matrix(
    observations: Sequence[ResearchTeamSpecializationObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecializationMatrixConfig | None = None,
) -> ResearchTeamSpecializationMatrixReport:
    if config is None:
        config = ResearchTeamSpecializationMatrixConfig()
    if type(config) is not ResearchTeamSpecializationMatrixConfig:
        raise ValueError("config must be a ResearchTeamSpecializationMatrixConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_domain(
            domain_id=domain_id,
            observations=tuple(
                item
                for item in normalized_observations
                if item.domain_id == domain_id
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
        "total_covered_role_count": _sum_decimal(
            row.covered_role_count for row in rows
        ),
        "total_required_role_count": _sum_decimal(
            row.required_role_count for row in rows
        ),
        "total_available_capacity_count": _sum_decimal(
            row.available_capacity_count for row in rows
        ),
        "total_required_capacity_count": _sum_decimal(
            row.required_capacity_count for row in rows
        ),
        "total_review_count": _sum_decimal(row.review_count for row in rows),
        "total_high_quality_review_count": _sum_decimal(
            row.high_quality_review_count for row in rows
        ),
        "average_specialization_score": _average_specialization_score(rows),
        "lowest_specialization_score": _lowest_specialization_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecializationMatrixReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_specialization_matrix_payload(
    report: ResearchTeamSpecializationMatrixReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecializationMatrixReport:
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
        "report must be a ResearchTeamSpecializationMatrixReport or payload",
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
    observations: tuple[ResearchTeamSpecializationObservation, ...],
    config: ResearchTeamSpecializationMatrixConfig,
) -> ResearchTeamSpecializationMatrixRow:
    covered_role_count = _sum_decimal(item.covered_role_count for item in observations)
    required_role_count = _sum_decimal(item.required_role_count for item in observations)
    available_capacity_count = _sum_decimal(
        item.available_capacity_count for item in observations
    )
    required_capacity_count = _sum_decimal(
        item.required_capacity_count for item in observations
    )
    review_count = _sum_decimal(item.review_count for item in observations)
    high_quality_review_count = _sum_decimal(
        item.high_quality_review_count for item in observations
    )
    role_coverage_ratio = _ratio_or_zero(covered_role_count, required_role_count)
    memory_quality_score = _average_memory_quality_score(observations)
    capacity_ratio = _ratio_or_zero(available_capacity_count, required_capacity_count)
    review_quality_ratio = _ratio_or_zero(high_quality_review_count, review_count)
    specialization_score = _specialization_score(
        role_coverage_ratio=role_coverage_ratio,
        memory_quality_score=memory_quality_score,
        capacity_ratio=capacity_ratio,
        review_quality_ratio=review_quality_ratio,
    )
    status = _row_status(
        observation_count=_decimal_count(len(observations)),
        role_coverage_ratio=role_coverage_ratio,
        memory_quality_score=memory_quality_score,
        capacity_ratio=capacity_ratio,
        review_quality_ratio=review_quality_ratio,
        config=config,
    )
    return ResearchTeamSpecializationMatrixRow(
        domain_id=domain_id,
        observation_count=_decimal_count(len(observations)),
        covered_role_count=covered_role_count,
        required_role_count=required_role_count,
        role_coverage_ratio=role_coverage_ratio,
        memory_quality_score=memory_quality_score,
        available_capacity_count=available_capacity_count,
        required_capacity_count=required_capacity_count,
        capacity_ratio=capacity_ratio,
        review_count=review_count,
        high_quality_review_count=high_quality_review_count,
        review_quality_ratio=review_quality_ratio,
        specialization_score=specialization_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation_count=_decimal_count(len(observations)),
            role_coverage_ratio=role_coverage_ratio,
            memory_quality_score=memory_quality_score,
            capacity_ratio=capacity_ratio,
            review_quality_ratio=review_quality_ratio,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    observation_count: Decimal,
    role_coverage_ratio: Decimal,
    memory_quality_score: Decimal,
    capacity_ratio: Decimal,
    review_quality_ratio: Decimal,
    config: ResearchTeamSpecializationMatrixConfig,
) -> str:
    if (
        observation_count == _ZERO
        or role_coverage_ratio < config.min_watch_role_coverage_ratio
        or memory_quality_score < config.min_watch_memory_quality_score
        or capacity_ratio < config.min_watch_capacity_ratio
        or review_quality_ratio < config.min_watch_review_quality_ratio
    ):
        return "block"
    if (
        role_coverage_ratio < config.min_pass_role_coverage_ratio
        or memory_quality_score < config.min_pass_memory_quality_score
        or capacity_ratio < config.min_pass_capacity_ratio
        or review_quality_ratio < config.min_pass_review_quality_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observation_count: Decimal,
    role_coverage_ratio: Decimal,
    memory_quality_score: Decimal,
    capacity_ratio: Decimal,
    review_quality_ratio: Decimal,
    status: str,
    config: ResearchTeamSpecializationMatrixConfig,
) -> tuple[str, ...]:
    codes = [f"specialization_matrix_{status}"]
    if observation_count == _ZERO:
        codes.append("missing_domain_specialization")
    codes.append(_role_coverage_reason(role_coverage_ratio, config))
    codes.append(_memory_quality_reason(memory_quality_score, config))
    codes.append(_capacity_reason(capacity_ratio, config))
    codes.append(_review_quality_reason(review_quality_ratio, config))
    return _normalize_row_reason_codes(tuple(codes))


def _role_coverage_reason(
    value: Decimal,
    config: ResearchTeamSpecializationMatrixConfig,
) -> str:
    if value >= config.min_pass_role_coverage_ratio:
        return "role_coverage_pass"
    if value >= config.min_watch_role_coverage_ratio:
        return "role_coverage_watch"
    return "role_coverage_low"


def _memory_quality_reason(
    value: Decimal,
    config: ResearchTeamSpecializationMatrixConfig,
) -> str:
    if value >= config.min_pass_memory_quality_score:
        return "memory_quality_pass"
    if value >= config.min_watch_memory_quality_score:
        return "memory_quality_watch"
    return "memory_quality_low"


def _capacity_reason(
    value: Decimal,
    config: ResearchTeamSpecializationMatrixConfig,
) -> str:
    if value >= config.min_pass_capacity_ratio:
        return "capacity_pass"
    if value >= config.min_watch_capacity_ratio:
        return "capacity_watch"
    return "capacity_low"


def _review_quality_reason(
    value: Decimal,
    config: ResearchTeamSpecializationMatrixConfig,
) -> str:
    if value >= config.min_pass_review_quality_ratio:
        return "review_quality_pass"
    if value >= config.min_watch_review_quality_ratio:
        return "review_quality_watch"
    return "review_quality_low"


def _specialization_score(
    *,
    role_coverage_ratio: Decimal,
    memory_quality_score: Decimal,
    capacity_ratio: Decimal,
    review_quality_ratio: Decimal,
) -> Decimal:
    return _clamp_ratio(
        (
            role_coverage_ratio
            + memory_quality_score
            + capacity_ratio
            + review_quality_ratio
        )
        / Decimal("4.000000"),
    )


def _average_memory_quality_score(
    observations: tuple[ResearchTeamSpecializationObservation, ...],
) -> Decimal:
    if not observations:
        return _ZERO
    return _quantize(
        _sum_decimal(item.memory_quality_score for item in observations)
        / Decimal(len(observations)),
    )


def _report_status(rows: tuple[ResearchTeamSpecializationMatrixRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecializationMatrixRow, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("specialization_matrix_report_block_rows")
    if any(row.status == "watch" for row in rows):
        codes.append("specialization_matrix_report_watch_rows")
    if not codes:
        codes.append("specialization_matrix_report_pass")
    return _normalize_report_reason_codes(tuple(codes))


def _average_specialization_score(
    rows: tuple[ResearchTeamSpecializationMatrixRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _quantize(
        _sum_decimal(row.specialization_score for row in rows) / Decimal(len(rows)),
    )


def _lowest_specialization_score(
    rows: tuple[ResearchTeamSpecializationMatrixRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.specialization_score for row in rows)


def _status_count(
    rows: tuple[ResearchTeamSpecializationMatrixRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchTeamSpecializationObservation],
) -> tuple[ResearchTeamSpecializationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchTeamSpecializationObservation] = []
    seen_keys: set[tuple[str, str]] = set()
    for observation in observations:
        if type(observation) is not ResearchTeamSpecializationObservation:
            raise ValueError(
                "observations must contain ResearchTeamSpecializationObservation",
            )
        _require_hard_flags("observation", observation)
        key = (observation.domain_id, observation.team_code)
        if key in seen_keys:
            raise ValueError("duplicate domain/team observation")
        seen_keys.add(key)
        normalized.append(observation)
    return tuple(sorted(normalized, key=lambda item: (item.domain_id, item.team_code)))


def _normalize_rows(
    rows: Sequence[ResearchTeamSpecializationMatrixRow],
) -> tuple[ResearchTeamSpecializationMatrixRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamSpecializationMatrixRow] = []
    seen_domains: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecializationMatrixRow:
            raise ValueError("rows must contain ResearchTeamSpecializationMatrixRow")
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


def _validate_config(config: ResearchTeamSpecializationMatrixConfig) -> None:
    if config.min_watch_role_coverage_ratio > config.min_pass_role_coverage_ratio:
        raise ValueError(
            "min_watch_role_coverage_ratio must not exceed "
            "min_pass_role_coverage_ratio",
        )
    if config.min_watch_memory_quality_score > config.min_pass_memory_quality_score:
        raise ValueError(
            "min_watch_memory_quality_score must not exceed "
            "min_pass_memory_quality_score",
        )
    if config.min_watch_capacity_ratio > config.min_pass_capacity_ratio:
        raise ValueError(
            "min_watch_capacity_ratio must not exceed min_pass_capacity_ratio",
        )
    if config.min_watch_review_quality_ratio > config.min_pass_review_quality_ratio:
        raise ValueError(
            "min_watch_review_quality_ratio must not exceed "
            "min_pass_review_quality_ratio",
        )


def _validate_row(row: ResearchTeamSpecializationMatrixRow) -> None:
    if row.role_coverage_ratio != _ratio_or_zero(
        row.covered_role_count,
        row.required_role_count,
    ):
        raise ValueError("role_coverage_ratio must match covered over required")
    if row.capacity_ratio != _ratio_or_zero(
        row.available_capacity_count,
        row.required_capacity_count,
    ):
        raise ValueError("capacity_ratio must match available over required")
    if row.review_quality_ratio != _ratio_or_zero(
        row.high_quality_review_count,
        row.review_count,
    ):
        raise ValueError("review_quality_ratio must match high quality over total")
    if row.specialization_score != _specialization_score(
        role_coverage_ratio=row.role_coverage_ratio,
        memory_quality_score=row.memory_quality_score,
        capacity_ratio=row.capacity_ratio,
        review_quality_ratio=row.review_quality_ratio,
    ):
        raise ValueError("specialization_score must match component average")
    if f"specialization_matrix_{row.status}" not in row.reason_codes:
        raise ValueError("row status must match reason_codes")


def _validate_report(report: ResearchTeamSpecializationMatrixReport) -> None:
    rows = report.rows
    if report.domain_count != _decimal_count(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.total_covered_role_count != _sum_decimal(
        row.covered_role_count for row in rows
    ):
        raise ValueError("total_covered_role_count must match rows")
    if report.total_required_role_count != _sum_decimal(
        row.required_role_count for row in rows
    ):
        raise ValueError("total_required_role_count must match rows")
    if report.total_available_capacity_count != _sum_decimal(
        row.available_capacity_count for row in rows
    ):
        raise ValueError("total_available_capacity_count must match rows")
    if report.total_required_capacity_count != _sum_decimal(
        row.required_capacity_count for row in rows
    ):
        raise ValueError("total_required_capacity_count must match rows")
    if report.total_review_count != _sum_decimal(row.review_count for row in rows):
        raise ValueError("total_review_count must match rows")
    if report.total_high_quality_review_count != _sum_decimal(
        row.high_quality_review_count for row in rows
    ):
        raise ValueError("total_high_quality_review_count must match rows")
    if report.average_specialization_score != _average_specialization_score(rows):
        raise ValueError("average_specialization_score must match rows")
    if report.lowest_specialization_score != _lowest_specialization_score(rows):
        raise ValueError("lowest_specialization_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    expected_digest = _report_digest_from_values(_payload_values_without_digest(payload))
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _payload_values_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    return values


def _report_values_without_digest(
    report: ResearchTeamSpecializationMatrixReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    if type(ready) is not dict:
        raise ValueError("digest values must be a JSON object")
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
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


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal numeric strings")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key)
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_key(value: str) -> None:
    normalized = value.casefold()
    if any(term in normalized for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public payload field: {value}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.casefold()
    if "http://" in normalized or "https://" in normalized:
        raise ValueError(f"{label} has unsafe public payload value")
    if any(term in normalized for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{label} has unsafe public payload value")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is str:
        _reject_unsafe_public_text(field_name, value)
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_SPECIALIZATION_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _sum_decimal(values: Sequence[Decimal] | object) -> Decimal:
    total = _ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be exactly Decimal")
        total += value
    return _quantize(total)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < _ZERO:
        return _ZERO
    if quantized > _ONE:
        return _ONE
    return quantized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIZATION_DOMAINS",
    "DEFAULT_RESEARCH_TEAM_SPECIALIZATION_MATRIX_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIZATION_STATUSES",
    "ResearchTeamSpecializationMatrixConfig",
    "ResearchTeamSpecializationMatrixReport",
    "ResearchTeamSpecializationMatrixRow",
    "ResearchTeamSpecializationObservation",
    "build_research_team_specialization_matrix",
    "research_team_specialization_matrix_payload",
)
