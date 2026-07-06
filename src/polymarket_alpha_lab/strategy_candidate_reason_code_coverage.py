"""Pure report-only reason-code coverage audit for strategy candidates.

This module reduces caller-supplied in-memory candidate descriptors into a
readonly audit report. It performs no IO, network access, credential handling,
wallet/account access, order placement, broker interaction, or investment advice.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_REASON_CODE_COVERAGE_CONFIG_VERSION = (
    "strategy-candidate-reason-code-coverage-v0"
)

COVERAGE_STATUSES = ("ready", "watch", "blocked")
CANDIDATE_STATUSES = ("clean", "watch", "blocked")
GROUP_COVERAGE_STATUSES = ("covered", "missing")
REASON_CODES = (
    "missing_strategy_candidate_descriptors",
    "missing_candidate_reason_codes",
    "duplicate_candidate_reason_codes",
    "weak_candidate_evidence_links",
    "stale_candidate_reasoning",
    "missing_team_coverage",
    "missing_category_coverage",
    "strategy_candidate_reason_code_coverage_ready",
)
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
DECIMAL_ZERO = Decimal("0")
UNSAFE_PUBLIC_PAYLOAD_FIELD_FRAGMENTS = (
    "api_key",
    "auth",
    "authorization",
    "credential",
    "database",
    "dsn",
    "exchange_mutation",
    "live",
    "network",
    "order",
    "persistence",
    "private_key",
    "secret",
    "token",
    "trade",
    "wallet",
    "websocket",
)


@dataclass(frozen=True)
class StrategyCandidateReasonCodeCoverageConfig:
    config_version: str = DEFAULT_STRATEGY_CANDIDATE_REASON_CODE_COVERAGE_CONFIG_VERSION
    required_team_codes: tuple[str, ...] = ()
    required_category_codes: tuple[str, ...] = ()
    max_reasoning_age_seconds: Decimal = Decimal("86400")
    min_evidence_link_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_team_codes",
            _normalize_code_tuple("required_team_codes", self.required_team_codes),
        )
        object.__setattr__(
            self,
            "required_category_codes",
            _normalize_code_tuple(
                "required_category_codes",
                self.required_category_codes,
            ),
        )
        object.__setattr__(
            self,
            "max_reasoning_age_seconds",
            _normalize_nonnegative_integral_decimal(
                "max_reasoning_age_seconds",
                self.max_reasoning_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_evidence_link_count",
            _normalize_nonnegative_integral_decimal(
                "min_evidence_link_count",
                self.min_evidence_link_count,
            ),
        )
        require_paper_only_flags("coverage config", self)


@dataclass(frozen=True)
class StrategyCandidateReasonCodeDescriptor:
    candidate_id: str
    team_code: str
    category_code: str
    reason_codes: tuple[str, ...]
    evidence_links: tuple[str, ...]
    reasoning_updated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("team_code", self.team_code)
        _require_canonical_string("category_code", self.category_code)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_code_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "evidence_links",
            _normalize_link_tuple("evidence_links", self.evidence_links),
        )
        object.__setattr__(
            self,
            "reasoning_updated_at",
            _as_utc("reasoning_updated_at", self.reasoning_updated_at),
        )
        require_paper_only_flags("coverage descriptor", self)


@dataclass(frozen=True)
class StrategyCandidateReasonCodeCoverageCandidateRow:
    candidate_id: str
    team_code: str
    category_code: str
    reason_code_count: Decimal
    distinct_reason_code_count: Decimal
    duplicate_reason_code_count: Decimal
    evidence_link_count: Decimal
    weak_evidence_link: bool
    reasoning_age_seconds: Decimal
    stale_reasoning: bool
    candidate_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("team_code", self.team_code)
        _require_canonical_string("category_code", self.category_code)
        for field_name in (
            "reason_code_count",
            "distinct_reason_code_count",
            "duplicate_reason_code_count",
            "evidence_link_count",
            "reasoning_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_bool("weak_evidence_link", self.weak_evidence_link)
        _require_bool("stale_reasoning", self.stale_reasoning)
        _require_candidate_status("candidate_status", self.candidate_status)
        require_paper_only_flags("coverage candidate row", self)


@dataclass(frozen=True)
class StrategyCandidateReasonCodeCoverageTeamRow:
    team_code: str
    candidate_count: Decimal
    coverage_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_code", self.team_code)
        object.__setattr__(
            self,
            "candidate_count",
            _normalize_nonnegative_integral_decimal(
                "candidate_count",
                self.candidate_count,
            ),
        )
        _require_group_coverage_status("coverage_status", self.coverage_status)
        require_paper_only_flags("coverage team row", self)


@dataclass(frozen=True)
class StrategyCandidateReasonCodeCoverageCategoryRow:
    category_code: str
    candidate_count: Decimal
    coverage_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_code", self.category_code)
        object.__setattr__(
            self,
            "candidate_count",
            _normalize_nonnegative_integral_decimal(
                "candidate_count",
                self.candidate_count,
            ),
        )
        _require_group_coverage_status("coverage_status", self.coverage_status)
        require_paper_only_flags("coverage category row", self)


@dataclass(frozen=True)
class StrategyCandidateReasonCodeCoverageReport:
    generated_at: datetime
    config_version: str
    coverage_status: str
    candidate_count: Decimal
    reason_code_total_count: Decimal
    distinct_reason_code_count: Decimal
    missing_reason_code_count: Decimal
    duplicate_reason_code_count: Decimal
    weak_evidence_link_count: Decimal
    stale_reasoning_count: Decimal
    covered_team_count: Decimal
    required_team_count: Decimal
    missing_team_count: Decimal
    missing_team_codes: tuple[str, ...]
    covered_category_count: Decimal
    required_category_count: Decimal
    missing_category_count: Decimal
    missing_category_codes: tuple[str, ...]
    clean_candidate_share: Decimal
    team_coverage_status: str
    category_coverage_status: str
    candidate_rows: tuple[StrategyCandidateReasonCodeCoverageCandidateRow, ...]
    team_rows: tuple[StrategyCandidateReasonCodeCoverageTeamRow, ...]
    category_rows: tuple[StrategyCandidateReasonCodeCoverageCategoryRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_coverage_status("coverage_status", self.coverage_status)
        for field_name in (
            "candidate_count",
            "reason_code_total_count",
            "distinct_reason_code_count",
            "missing_reason_code_count",
            "duplicate_reason_code_count",
            "weak_evidence_link_count",
            "stale_reasoning_count",
            "covered_team_count",
            "required_team_count",
            "missing_team_count",
            "covered_category_count",
            "required_category_count",
            "missing_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "missing_team_codes",
            _normalize_code_tuple("missing_team_codes", self.missing_team_codes),
        )
        object.__setattr__(
            self,
            "missing_category_codes",
            _normalize_code_tuple(
                "missing_category_codes",
                self.missing_category_codes,
            ),
        )
        object.__setattr__(
            self,
            "clean_candidate_share",
            _normalize_ratio("clean_candidate_share", self.clean_candidate_share),
        )
        _require_group_coverage_status(
            "team_coverage_status",
            self.team_coverage_status,
        )
        _require_group_coverage_status(
            "category_coverage_status",
            self.category_coverage_status,
        )
        object.__setattr__(
            self,
            "candidate_rows",
            _normalize_candidate_rows(self.candidate_rows),
        )
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        object.__setattr__(
            self,
            "category_rows",
            _normalize_category_rows(self.category_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("coverage report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report_consistency(self)
        if self.derived_validation_digest != _derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report fields")


def build_strategy_candidate_reason_code_coverage_report(
    descriptors: (
        list[StrategyCandidateReasonCodeDescriptor]
        | tuple[StrategyCandidateReasonCodeDescriptor, ...]
    ),
    *,
    config: StrategyCandidateReasonCodeCoverageConfig,
    generated_at: datetime,
) -> StrategyCandidateReasonCodeCoverageReport:
    if type(config) is not StrategyCandidateReasonCodeCoverageConfig:
        raise ValueError(
            "config must be a StrategyCandidateReasonCodeCoverageConfig",
        )
    require_paper_only_flags("coverage config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_descriptors = _normalize_descriptors(descriptors)
    for descriptor in source_descriptors:
        if descriptor.reasoning_updated_at > generated_at_utc:
            raise ValueError("reasoning_updated_at cannot be in the future")

    candidate_rows = tuple(
        _candidate_row(
            descriptor,
            generated_at=generated_at_utc,
            config=config,
        )
        for descriptor in source_descriptors
    )
    team_rows = _team_rows(source_descriptors, config.required_team_codes)
    category_rows = _category_rows(
        source_descriptors,
        config.required_category_codes,
    )
    missing_team_codes = tuple(
        row.team_code for row in team_rows if row.coverage_status == "missing"
    )
    missing_category_codes = tuple(
        row.category_code for row in category_rows if row.coverage_status == "missing"
    )
    reason_codes = _report_reason_codes(
        candidate_rows,
        missing_team_codes=missing_team_codes,
        missing_category_codes=missing_category_codes,
    )

    return StrategyCandidateReasonCodeCoverageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        coverage_status=_coverage_status(reason_codes),
        candidate_count=Decimal(len(source_descriptors)),
        reason_code_total_count=Decimal(
            sum(len(descriptor.reason_codes) for descriptor in source_descriptors),
        ),
        distinct_reason_code_count=Decimal(
            len(
                {
                    reason_code
                    for descriptor in source_descriptors
                    for reason_code in descriptor.reason_codes
                },
            ),
        ),
        missing_reason_code_count=Decimal(
            sum(1 for row in candidate_rows if row.reason_code_count == DECIMAL_ZERO),
        ),
        duplicate_reason_code_count=Decimal(
            sum(
                1
                for row in candidate_rows
                if row.duplicate_reason_code_count > DECIMAL_ZERO
            ),
        ),
        weak_evidence_link_count=Decimal(
            sum(1 for row in candidate_rows if row.weak_evidence_link),
        ),
        stale_reasoning_count=Decimal(
            sum(1 for row in candidate_rows if row.stale_reasoning),
        ),
        covered_team_count=Decimal(
            sum(1 for row in team_rows if row.coverage_status == "covered"),
        ),
        required_team_count=Decimal(len(config.required_team_codes)),
        missing_team_count=Decimal(len(missing_team_codes)),
        missing_team_codes=missing_team_codes,
        covered_category_count=Decimal(
            sum(1 for row in category_rows if row.coverage_status == "covered"),
        ),
        required_category_count=Decimal(len(config.required_category_codes)),
        missing_category_count=Decimal(len(missing_category_codes)),
        missing_category_codes=missing_category_codes,
        clean_candidate_share=_share(
            Decimal(sum(1 for row in candidate_rows if row.candidate_status == "clean")),
            Decimal(len(candidate_rows)),
        ),
        team_coverage_status="missing" if missing_team_codes else "covered",
        category_coverage_status="missing" if missing_category_codes else "covered",
        candidate_rows=candidate_rows,
        team_rows=team_rows,
        category_rows=category_rows,
        reason_codes=reason_codes,
    )


def strategy_candidate_reason_code_coverage_payload(
    report: StrategyCandidateReasonCodeCoverageReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateReasonCodeCoverageReport:
        raise ValueError(
            "report must be a StrategyCandidateReasonCodeCoverageReport",
        )
    require_paper_only_flags("coverage report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("coverage payload must be a JSON object")
    _require_payload_hard_flags("coverage payload", payload)
    reject_unsafe_surface_fields("coverage payload", payload)
    _reject_unsafe_public_payload_surface("coverage payload", payload)
    return payload


def _candidate_row(
    descriptor: StrategyCandidateReasonCodeDescriptor,
    *,
    generated_at: datetime,
    config: StrategyCandidateReasonCodeCoverageConfig,
) -> StrategyCandidateReasonCodeCoverageCandidateRow:
    reason_count = Decimal(len(descriptor.reason_codes))
    distinct_reason_count = Decimal(len(set(descriptor.reason_codes)))
    duplicate_reason_count = reason_count - distinct_reason_count
    evidence_link_count = Decimal(len(descriptor.evidence_links))
    weak_evidence_link = evidence_link_count < config.min_evidence_link_count
    reasoning_age_seconds = Decimal(
        int((generated_at - descriptor.reasoning_updated_at).total_seconds()),
    )
    stale_reasoning = reasoning_age_seconds > config.max_reasoning_age_seconds
    return StrategyCandidateReasonCodeCoverageCandidateRow(
        candidate_id=descriptor.candidate_id,
        team_code=descriptor.team_code,
        category_code=descriptor.category_code,
        reason_code_count=reason_count,
        distinct_reason_code_count=distinct_reason_count,
        duplicate_reason_code_count=duplicate_reason_count,
        evidence_link_count=evidence_link_count,
        weak_evidence_link=weak_evidence_link,
        reasoning_age_seconds=reasoning_age_seconds,
        stale_reasoning=stale_reasoning,
        candidate_status=_candidate_status(
            reason_count=reason_count,
            duplicate_reason_count=duplicate_reason_count,
            weak_evidence_link=weak_evidence_link,
            stale_reasoning=stale_reasoning,
        ),
    )


def _candidate_status(
    *,
    reason_count: Decimal,
    duplicate_reason_count: Decimal,
    weak_evidence_link: bool,
    stale_reasoning: bool,
) -> str:
    if (
        reason_count == DECIMAL_ZERO
        or duplicate_reason_count > DECIMAL_ZERO
        or stale_reasoning
    ):
        return "blocked"
    if weak_evidence_link:
        return "watch"
    return "clean"


def _team_rows(
    descriptors: tuple[StrategyCandidateReasonCodeDescriptor, ...],
    required_team_codes: tuple[str, ...],
) -> tuple[StrategyCandidateReasonCodeCoverageTeamRow, ...]:
    counts = Counter(descriptor.team_code for descriptor in descriptors)
    return tuple(
        StrategyCandidateReasonCodeCoverageTeamRow(
            team_code=team_code,
            candidate_count=Decimal(counts[team_code]),
            coverage_status="covered" if counts[team_code] > 0 else "missing",
        )
        for team_code in required_team_codes
    )


def _category_rows(
    descriptors: tuple[StrategyCandidateReasonCodeDescriptor, ...],
    required_category_codes: tuple[str, ...],
) -> tuple[StrategyCandidateReasonCodeCoverageCategoryRow, ...]:
    counts = Counter(descriptor.category_code for descriptor in descriptors)
    return tuple(
        StrategyCandidateReasonCodeCoverageCategoryRow(
            category_code=category_code,
            candidate_count=Decimal(counts[category_code]),
            coverage_status="covered" if counts[category_code] > 0 else "missing",
        )
        for category_code in required_category_codes
    )


def _report_reason_codes(
    candidate_rows: tuple[StrategyCandidateReasonCodeCoverageCandidateRow, ...],
    *,
    missing_team_codes: tuple[str, ...],
    missing_category_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not candidate_rows:
        reason_codes.append("missing_strategy_candidate_descriptors")
    if any(row.reason_code_count == DECIMAL_ZERO for row in candidate_rows):
        reason_codes.append("missing_candidate_reason_codes")
    if any(row.duplicate_reason_code_count > DECIMAL_ZERO for row in candidate_rows):
        reason_codes.append("duplicate_candidate_reason_codes")
    if any(row.weak_evidence_link for row in candidate_rows):
        reason_codes.append("weak_candidate_evidence_links")
    if any(row.stale_reasoning for row in candidate_rows):
        reason_codes.append("stale_candidate_reasoning")
    if missing_team_codes:
        reason_codes.append("missing_team_coverage")
    if missing_category_codes:
        reason_codes.append("missing_category_coverage")
    if not reason_codes:
        reason_codes.append("strategy_candidate_reason_code_coverage_ready")
    return tuple(reason_codes)


def _coverage_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            "missing_strategy_candidate_descriptors",
            "missing_candidate_reason_codes",
            "duplicate_candidate_reason_codes",
            "stale_candidate_reasoning",
            "missing_team_coverage",
            "missing_category_coverage",
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    if reason_codes == ("strategy_candidate_reason_code_coverage_ready",):
        return "ready"
    return "watch"


def _validate_report_consistency(
    report: StrategyCandidateReasonCodeCoverageReport,
) -> None:
    if Decimal(len(report.candidate_rows)) != report.candidate_count:
        raise ValueError("candidate_count must match candidate_rows")
    for row in report.candidate_rows:
        if (
            row.distinct_reason_code_count + row.duplicate_reason_code_count
            != row.reason_code_count
        ):
            raise ValueError("candidate row reason code counts must tie")
    if (
        sum((row.reason_code_count for row in report.candidate_rows), DECIMAL_ZERO)
        != report.reason_code_total_count
    ):
        raise ValueError("reason_code_total_count must match candidate_rows")
    if report.distinct_reason_code_count > report.reason_code_total_count:
        raise ValueError(
            "distinct_reason_code_count must not exceed reason_code_total_count",
        )
    if report.candidate_rows and report.distinct_reason_code_count < max(
        row.distinct_reason_code_count for row in report.candidate_rows
    ):
        raise ValueError("distinct_reason_code_count must cover candidate_rows")
    if (
        Decimal(
            sum(
                1
                for row in report.candidate_rows
                if row.reason_code_count == DECIMAL_ZERO
            ),
        )
        != report.missing_reason_code_count
    ):
        raise ValueError("missing_reason_code_count must match candidate_rows")
    if (
        Decimal(
            sum(
                1
                for row in report.candidate_rows
                if row.duplicate_reason_code_count > DECIMAL_ZERO
            ),
        )
        != report.duplicate_reason_code_count
    ):
        raise ValueError("duplicate_reason_code_count must match candidate_rows")
    if (
        Decimal(sum(1 for row in report.candidate_rows if row.weak_evidence_link))
        != report.weak_evidence_link_count
    ):
        raise ValueError("weak_evidence_link_count must match candidate_rows")
    if (
        Decimal(sum(1 for row in report.candidate_rows if row.stale_reasoning))
        != report.stale_reasoning_count
    ):
        raise ValueError("stale_reasoning_count must match candidate_rows")
    if (
        Decimal(
            len(
                {
                    row.team_code
                    for row in report.team_rows
                    if row.coverage_status == "covered"
                },
            ),
        )
        != report.covered_team_count
    ):
        raise ValueError("covered_team_count must match team_rows")
    if Decimal(len(report.team_rows)) != report.required_team_count:
        raise ValueError("required_team_count must match team_rows")
    if Decimal(len(report.missing_team_codes)) != report.missing_team_count:
        raise ValueError("missing_team_count must match missing_team_codes")
    if tuple(
        row.team_code for row in report.team_rows if row.coverage_status == "missing"
    ) != report.missing_team_codes:
        raise ValueError("missing_team_codes must match team_rows")
    if (
        Decimal(
            len(
                {
                    row.category_code
                    for row in report.category_rows
                    if row.coverage_status == "covered"
                },
            ),
        )
        != report.covered_category_count
    ):
        raise ValueError("covered_category_count must match category_rows")
    if Decimal(len(report.category_rows)) != report.required_category_count:
        raise ValueError("required_category_count must match category_rows")
    if Decimal(len(report.missing_category_codes)) != report.missing_category_count:
        raise ValueError("missing_category_count must match missing_category_codes")
    if tuple(
        row.category_code
        for row in report.category_rows
        if row.coverage_status == "missing"
    ) != report.missing_category_codes:
        raise ValueError("missing_category_codes must match category_rows")
    clean_count = Decimal(
        sum(1 for row in report.candidate_rows if row.candidate_status == "clean"),
    )
    if report.clean_candidate_share != _share(clean_count, report.candidate_count):
        raise ValueError("clean_candidate_share must match candidate_rows")
    if report.team_coverage_status != (
        "missing" if report.missing_team_codes else "covered"
    ):
        raise ValueError("team_coverage_status must match missing_team_codes")
    if report.category_coverage_status != (
        "missing" if report.missing_category_codes else "covered"
    ):
        raise ValueError("category_coverage_status must match missing_category_codes")
    if report.coverage_status != _coverage_status(report.reason_codes):
        raise ValueError("coverage_status must match reason_codes")


def _normalize_descriptors(
    value: object,
) -> tuple[StrategyCandidateReasonCodeDescriptor, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("descriptors must be a list or tuple")
    descriptors = tuple(value)
    for descriptor in descriptors:
        if type(descriptor) is not StrategyCandidateReasonCodeDescriptor:
            raise ValueError(
                "descriptors must contain StrategyCandidateReasonCodeDescriptor values",
            )
        require_paper_only_flags("coverage descriptor", descriptor)
    return descriptors


def _normalize_candidate_rows(
    value: object,
) -> tuple[StrategyCandidateReasonCodeCoverageCandidateRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidate_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyCandidateReasonCodeCoverageCandidateRow:
            raise ValueError(
                "candidate_rows must contain "
                "StrategyCandidateReasonCodeCoverageCandidateRow values",
            )
        require_paper_only_flags("coverage candidate row", row)
    if len({row.candidate_id for row in rows}) != len(rows):
        raise ValueError("candidate_rows must have unique candidate_id values")
    return rows


def _normalize_team_rows(
    value: object,
) -> tuple[StrategyCandidateReasonCodeCoverageTeamRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyCandidateReasonCodeCoverageTeamRow:
            raise ValueError(
                "team_rows must contain StrategyCandidateReasonCodeCoverageTeamRow values",
            )
        require_paper_only_flags("coverage team row", row)
    if len({row.team_code for row in rows}) != len(rows):
        raise ValueError("team_rows must have unique team_code values")
    return rows


def _normalize_category_rows(
    value: object,
) -> tuple[StrategyCandidateReasonCodeCoverageCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("category_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyCandidateReasonCodeCoverageCategoryRow:
            raise ValueError(
                "category_rows must contain "
                "StrategyCandidateReasonCodeCoverageCategoryRow values",
            )
        require_paper_only_flags("coverage category row", row)
    if len({row.category_code for row in rows}) != len(rows):
        raise ValueError("category_rows must have unique category_code values")
    return rows


def _normalize_code_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_canonical_string(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return codes


def _normalize_reason_code_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _normalize_link_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    links = tuple(value)
    for link in links:
        _require_canonical_string(field_name, link)
    return links


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known coverage reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _normalize_derived_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _derived_validation_digest(
    report: StrategyCandidateReasonCodeCoverageReport,
) -> str:
    material = asdict(report)
    material.pop("derived_validation_digest", None)
    digest_material = json.dumps(
        _digest_json_ready(material),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(digest_material.encode("utf-8")).hexdigest()


def _digest_json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("digest datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("digest value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        return _digest_json_dict_ready(value)
    if isinstance(value, (list, tuple)):
        return [_digest_json_ready(item) for item in value]
    raise ValueError("digest value is not JSON serializable")


def _digest_json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("digest object keys must be strings")
        ready[key] = _digest_json_ready(item)
    return ready


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(RATIO_QUANT)
    if quantized < DECIMAL_ZERO or quantized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_integral_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _share(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == DECIMAL_ZERO:
        return DECIMAL_ZERO.quantize(RATIO_QUANT)
    return (numerator / denominator).quantize(RATIO_QUANT)


def _require_coverage_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in COVERAGE_STATUSES:
        raise ValueError(f"{field_name} must be one of ready, watch, blocked")


def _require_candidate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CANDIDATE_STATUSES:
        raise ValueError(f"{field_name} must be one of clean, watch, blocked")


def _require_group_coverage_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GROUP_COVERAGE_STATUSES:
        raise ValueError(f"{field_name} must be one of covered, missing")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload_surface(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload_surface(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError("coverage payload keys must be strings")
            lowered_key = key.lower()
            if any(
                fragment in lowered_key
                for fragment in UNSAFE_PUBLIC_PAYLOAD_FIELD_FRAGMENTS
            ):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_public_payload_surface(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload_surface(label, item)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_REASON_CODE_COVERAGE_CONFIG_VERSION",
    "StrategyCandidateReasonCodeCoverageCandidateRow",
    "StrategyCandidateReasonCodeCoverageCategoryRow",
    "StrategyCandidateReasonCodeCoverageConfig",
    "StrategyCandidateReasonCodeCoverageReport",
    "StrategyCandidateReasonCodeCoverageTeamRow",
    "StrategyCandidateReasonCodeDescriptor",
    "build_strategy_candidate_reason_code_coverage_report",
    "strategy_candidate_reason_code_coverage_payload",
)
