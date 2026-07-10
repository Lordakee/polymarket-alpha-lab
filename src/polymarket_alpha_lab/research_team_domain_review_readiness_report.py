"""Public report-only readiness scoring for domain analyst review teams."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_READINESS_CONFIG_VERSION = (
    "research-team-domain-review-readiness-report-v0"
)
PUBLIC_DOMAIN_CATEGORIES = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)
PUBLIC_REVIEW_READINESS_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
ZERO_TIME_DELTA = timedelta(0)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
SHA256_HEX_CHARS = frozenset("0123456789abcdef")

PASS_REASON = "domain_review_readiness_pass"
MISSING_DOMAIN_REASON = "domain_review_readiness_missing_domain"
NO_INPUTS_REASON = "domain_review_readiness_no_inputs"
BLOCK_PRESENT_REASON = "domain_review_readiness_block_present"
WATCH_PRESENT_REASON = "domain_review_readiness_watch_present"
MISSING_DOMAIN_PRESENT_REASON = "domain_review_readiness_missing_domain_present"
CALIBRATION_PRESENT_REASON = "domain_review_readiness_calibration_issue_present"
MEMORY_PRESENT_REASON = "domain_review_readiness_memory_freshness_issue_present"
COVERAGE_PRESENT_REASON = "domain_review_readiness_coverage_issue_present"
WORKLOAD_PRESENT_REASON = "domain_review_readiness_workload_issue_present"
CORRECTION_PRESENT_REASON = (
    "domain_review_readiness_correction_follow_through_issue_present"
)
PASS_PRESENT_REASON = "domain_review_readiness_pass_present"

REASON_SEQUENCE = (
    MISSING_DOMAIN_REASON,
    "domain_review_readiness_calibration_block",
    "domain_review_readiness_memory_freshness_block",
    "domain_review_readiness_coverage_block",
    "domain_review_readiness_workload_block",
    "domain_review_readiness_correction_follow_through_block",
    "domain_review_readiness_calibration_watch",
    "domain_review_readiness_memory_freshness_watch",
    "domain_review_readiness_coverage_watch",
    "domain_review_readiness_workload_watch",
    "domain_review_readiness_correction_follow_through_watch",
    PASS_REASON,
)
REPORT_REASON_SEQUENCE = (
    NO_INPUTS_REASON,
    BLOCK_PRESENT_REASON,
    WATCH_PRESENT_REASON,
    MISSING_DOMAIN_PRESENT_REASON,
    CALIBRATION_PRESENT_REASON,
    MEMORY_PRESENT_REASON,
    COVERAGE_PRESENT_REASON,
    WORKLOAD_PRESENT_REASON,
    CORRECTION_PRESENT_REASON,
    PASS_PRESENT_REASON,
)
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_REPORT_COUNT_FIELDS = (
    "domain_count",
    "observed_domain_count",
    "missing_domain_count",
    "pass_count",
    "watch_count",
    "block_count",
)
_REPORT_RATIO_FIELDS = (
    "average_readiness_score",
    "weakest_readiness_score",
    "average_calibration_score",
    "average_memory_freshness_score",
    "average_evidence_coverage_score",
    "average_workload_health_score",
    "average_correction_follow_through_score",
)
_ROW_RATIO_FIELDS = (
    "readiness_score",
    "calibration_score",
    "memory_freshness_score",
    "evidence_coverage_score",
    "workload_health_score",
    "correction_follow_through_score",
)
_ROW_AGE_FIELDS = (
    "newest_memory_age_seconds",
    "oldest_memory_age_seconds",
    "newest_observation_age_seconds",
    "oldest_observation_age_seconds",
)
_PUBLIC_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    *_REPORT_COUNT_FIELDS,
    *_REPORT_RATIO_FIELDS,
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_ROW_PAYLOAD_FIELDS = (
    "domain_category",
    "status",
    "team_count",
    *_ROW_RATIO_FIELDS,
    *_ROW_AGE_FIELDS,
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        _join_parts("can", "did", "ate"),
        _join_parts("mar", "ket"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("sou", "rce"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("au", "th"),
        _join_parts("ac", "count"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("siz", "ing"),
        _join_parts("pos", "ition"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("recom", "mend"),
        _join_parts("li", "ve"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        "broker",
        "clob",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_READINESS_CONFIG_VERSION",
    "PUBLIC_DOMAIN_CATEGORIES",
    "PUBLIC_REVIEW_READINESS_STATUSES",
    "ResearchTeamDomainReviewReadinessConfig",
    "ResearchTeamDomainReviewReadinessInput",
    "ResearchTeamDomainReviewReadinessReport",
    "ResearchTeamDomainReviewReadinessRow",
    "build_research_team_domain_review_readiness_report",
    "research_team_domain_review_readiness_report_digest",
    "research_team_domain_review_readiness_report_payload",
    "validate_research_team_domain_review_readiness_public_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainReviewReadinessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_READINESS_CONFIG_VERSION
    )
    max_watch_memory_age_seconds: Decimal = Decimal("2592000.000000")
    min_pass_calibration_score: Decimal = Decimal("0.700000")
    min_watch_calibration_score: Decimal = Decimal("0.500000")
    min_pass_memory_freshness_score: Decimal = Decimal("0.800000")
    min_watch_memory_freshness_score: Decimal = Decimal("0.500000")
    min_pass_evidence_coverage_score: Decimal = Decimal("0.700000")
    min_watch_evidence_coverage_score: Decimal = Decimal("0.500000")
    min_pass_workload_health_score: Decimal = Decimal("0.500000")
    min_watch_workload_health_score: Decimal = Decimal("0.200000")
    min_pass_correction_follow_through_score: Decimal = Decimal("0.700000")
    min_watch_correction_follow_through_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainReviewReadinessConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_watch_memory_age_seconds",
            _require_positive_decimal(
                "max_watch_memory_age_seconds",
                self.max_watch_memory_age_seconds,
            ),
        )
        for field_name in (
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "min_pass_memory_freshness_score",
            "min_watch_memory_freshness_score",
            "min_pass_evidence_coverage_score",
            "min_watch_evidence_coverage_score",
            "min_pass_workload_health_score",
            "min_watch_workload_health_score",
            "min_pass_correction_follow_through_score",
            "min_watch_correction_follow_through_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for pass_field, watch_field in (
            ("min_pass_calibration_score", "min_watch_calibration_score"),
            ("min_pass_memory_freshness_score", "min_watch_memory_freshness_score"),
            ("min_pass_evidence_coverage_score", "min_watch_evidence_coverage_score"),
            ("min_pass_workload_health_score", "min_watch_workload_health_score"),
            (
                "min_pass_correction_follow_through_score",
                "min_watch_correction_follow_through_score",
            ),
        ):
            if getattr(self, pass_field) < getattr(self, watch_field):
                raise ValueError(f"{pass_field} must be at least {watch_field}")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewReadinessInput(_FinalDataclass):
    domain_category: str
    team_label: str
    calibration_score: Decimal
    memory_refreshed_at: datetime
    evidence_coverage_score: Decimal
    workload_ratio: Decimal
    correction_follow_through_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainReviewReadinessInput, "input")
        object.__setattr__(
            self,
            "domain_category",
            _require_domain_category("domain_category", self.domain_category),
        )
        object.__setattr__(
            self,
            "team_label",
            _require_public_label("team_label", self.team_label),
        )
        for field_name in (
            "calibration_score",
            "evidence_coverage_score",
            "workload_ratio",
            "correction_follow_through_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_refreshed_at",
            _as_utc("memory_refreshed_at", self.memory_refreshed_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewReadinessRow(_FinalDataclass):
    domain_category: str
    status: str
    team_count: Decimal
    readiness_score: Decimal
    calibration_score: Decimal
    memory_freshness_score: Decimal
    evidence_coverage_score: Decimal
    workload_health_score: Decimal
    correction_follow_through_score: Decimal
    newest_memory_age_seconds: Decimal | None
    oldest_memory_age_seconds: Decimal | None
    newest_observation_age_seconds: Decimal | None
    oldest_observation_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainReviewReadinessRow, "row")
        object.__setattr__(
            self,
            "domain_category",
            _require_domain_category("domain_category", self.domain_category),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "team_count",
            _require_count_decimal("team_count", self.team_count),
        )
        for field_name in (
            "readiness_score",
            "calibration_score",
            "memory_freshness_score",
            "evidence_coverage_score",
            "workload_health_score",
            "correction_follow_through_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_memory_age_seconds",
            "oldest_memory_age_seconds",
            "newest_observation_age_seconds",
            "oldest_observation_age_seconds",
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
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewReadinessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    observed_domain_count: Decimal
    missing_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    weakest_readiness_score: Decimal
    average_calibration_score: Decimal
    average_memory_freshness_score: Decimal
    average_evidence_coverage_score: Decimal
    average_workload_health_score: Decimal
    average_correction_follow_through_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamDomainReviewReadinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainReviewReadinessReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "domain_count",
            "observed_domain_count",
            "missing_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "weakest_readiness_score",
            "average_calibration_score",
            "average_memory_freshness_score",
            "average_evidence_coverage_score",
            "average_workload_health_score",
            "average_correction_follow_through_score",
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
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_domain_review_readiness_report(
    inputs: Iterable[ResearchTeamDomainReviewReadinessInput],
    *,
    config: ResearchTeamDomainReviewReadinessConfig,
    generated_at: datetime,
) -> ResearchTeamDomainReviewReadinessReport:
    _require_exact_type(config, ResearchTeamDomainReviewReadinessConfig, "config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    for item in input_rows:
        _validate_not_after("memory_refreshed_at", item.memory_refreshed_at, generated_at_utc)
        _validate_not_after("observed_at", item.observed_at, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_domain(
                    domain_category,
                    inputs=tuple(
                        item
                        for item in input_rows
                        if item.domain_category == domain_category
                    ),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for domain_category in PUBLIC_DOMAIN_CATEGORIES
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "domain_count": _count(len(PUBLIC_DOMAIN_CATEGORIES)),
        "observed_domain_count": _count(
            len({item.domain_category for item in input_rows}),
        ),
        "missing_domain_count": _reason_count(rows, MISSING_DOMAIN_REASON),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_readiness_score": _mean(row.readiness_score for row in rows),
        "weakest_readiness_score": _min_decimal(row.readiness_score for row in rows),
        "average_calibration_score": _mean(row.calibration_score for row in rows),
        "average_memory_freshness_score": _mean(
            row.memory_freshness_score for row in rows
        ),
        "average_evidence_coverage_score": _mean(
            row.evidence_coverage_score for row in rows
        ),
        "average_workload_health_score": _mean(
            row.workload_health_score for row in rows
        ),
        "average_correction_follow_through_score": _mean(
            row.correction_follow_through_score for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows, had_inputs=bool(input_rows)),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainReviewReadinessReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_domain_review_readiness_report_payload(
    report: ResearchTeamDomainReviewReadinessReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainReviewReadinessReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchTeamDomainReviewReadinessReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_team_domain_review_readiness_public_payload(payload)
    return payload


def validate_research_team_domain_review_readiness_public_payload(
    payload: dict[str, object],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("public payload", _MappingFlags(payload))
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    _reject_public_numerics(payload)
    _require_exact_payload_fields(
        "public payload",
        payload,
        _PUBLIC_REPORT_PAYLOAD_FIELDS,
    )
    _validate_payload_statuses(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    try:
        expected_digest = _digest_from_payload(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("public payload must contain canonical JSON values") from exc
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    report = _report_from_public_payload(payload)
    canonical_payload = _json_ready(asdict(report))
    if payload != canonical_payload:
        raise ValueError("public payload must use the canonical report schema")


def research_team_domain_review_readiness_report_digest(
    report: ResearchTeamDomainReviewReadinessReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_review_readiness_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _report_from_public_payload(
    payload: dict[str, object],
) -> ResearchTeamDomainReviewReadinessReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON array")
    rows = tuple(
        _row_from_public_payload(row_value, index=index)
        for index, row_value in enumerate(rows_value)
    )
    return ResearchTeamDomainReviewReadinessReport(
        generated_at=_public_utc_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        domain_count=_public_count_decimal("domain_count", payload["domain_count"]),
        observed_domain_count=_public_count_decimal(
            "observed_domain_count",
            payload["observed_domain_count"],
        ),
        missing_domain_count=_public_count_decimal(
            "missing_domain_count",
            payload["missing_domain_count"],
        ),
        pass_count=_public_count_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_count_decimal("watch_count", payload["watch_count"]),
        block_count=_public_count_decimal("block_count", payload["block_count"]),
        average_readiness_score=_public_ratio_decimal(
            "average_readiness_score",
            payload["average_readiness_score"],
        ),
        weakest_readiness_score=_public_ratio_decimal(
            "weakest_readiness_score",
            payload["weakest_readiness_score"],
        ),
        average_calibration_score=_public_ratio_decimal(
            "average_calibration_score",
            payload["average_calibration_score"],
        ),
        average_memory_freshness_score=_public_ratio_decimal(
            "average_memory_freshness_score",
            payload["average_memory_freshness_score"],
        ),
        average_evidence_coverage_score=_public_ratio_decimal(
            "average_evidence_coverage_score",
            payload["average_evidence_coverage_score"],
        ),
        average_workload_health_score=_public_ratio_decimal(
            "average_workload_health_score",
            payload["average_workload_health_score"],
        ),
        average_correction_follow_through_score=_public_ratio_decimal(
            "average_correction_follow_through_score",
            payload["average_correction_follow_through_score"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_list("reason_codes", payload["reason_codes"]),
        rows=rows,
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamDomainReviewReadinessRow:
    if type(value) is not dict:
        raise ValueError(f"rows[{index}] must be a JSON object")
    _require_exact_payload_fields(
        f"rows[{index}]",
        value,
        _PUBLIC_ROW_PAYLOAD_FIELDS,
    )
    return ResearchTeamDomainReviewReadinessRow(
        domain_category=_public_string(
            f"rows[{index}].domain_category",
            value["domain_category"],
        ),
        status=_public_string(f"rows[{index}].status", value["status"]),
        team_count=_public_count_decimal(
            f"rows[{index}].team_count",
            value["team_count"],
        ),
        readiness_score=_public_ratio_decimal(
            f"rows[{index}].readiness_score",
            value["readiness_score"],
        ),
        calibration_score=_public_ratio_decimal(
            f"rows[{index}].calibration_score",
            value["calibration_score"],
        ),
        memory_freshness_score=_public_ratio_decimal(
            f"rows[{index}].memory_freshness_score",
            value["memory_freshness_score"],
        ),
        evidence_coverage_score=_public_ratio_decimal(
            f"rows[{index}].evidence_coverage_score",
            value["evidence_coverage_score"],
        ),
        workload_health_score=_public_ratio_decimal(
            f"rows[{index}].workload_health_score",
            value["workload_health_score"],
        ),
        correction_follow_through_score=_public_ratio_decimal(
            f"rows[{index}].correction_follow_through_score",
            value["correction_follow_through_score"],
        ),
        newest_memory_age_seconds=_public_optional_nonnegative_decimal(
            f"rows[{index}].newest_memory_age_seconds",
            value["newest_memory_age_seconds"],
        ),
        oldest_memory_age_seconds=_public_optional_nonnegative_decimal(
            f"rows[{index}].oldest_memory_age_seconds",
            value["oldest_memory_age_seconds"],
        ),
        newest_observation_age_seconds=_public_optional_nonnegative_decimal(
            f"rows[{index}].newest_observation_age_seconds",
            value["newest_observation_age_seconds"],
        ),
        oldest_observation_age_seconds=_public_optional_nonnegative_decimal(
            f"rows[{index}].oldest_observation_age_seconds",
            value["oldest_observation_age_seconds"],
        ),
        reason_codes=_public_string_list(
            f"rows[{index}].reason_codes",
            value["reason_codes"],
        ),
        paper_only=_public_true(
            f"rows[{index}].paper_only",
            value["paper_only"],
        ),
        report_only=_public_true(
            f"rows[{index}].report_only",
            value["report_only"],
        ),
        readonly=_public_true(f"rows[{index}].readonly", value["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    value: Mapping[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    if set(value) != set(expected_fields):
        raise ValueError(f"{label} fields must match the public schema exactly")


def _public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _public_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _public_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_count_decimal(field_name, _public_decimal(field_name, value))


def _public_ratio_decimal(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(field_name, _public_decimal(field_name, value))


def _public_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_optional_nonnegative_decimal(
        field_name,
        _public_decimal(field_name, value),
    )


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
        normalized = _require_decimal(field_name, parsed)
    except (DecimalException, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _public_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_generated_at_utc(field_name, parsed)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _row_for_domain(
    domain_category: str,
    *,
    inputs: tuple[ResearchTeamDomainReviewReadinessInput, ...],
    config: ResearchTeamDomainReviewReadinessConfig,
    generated_at: datetime,
) -> ResearchTeamDomainReviewReadinessRow:
    if not inputs:
        return ResearchTeamDomainReviewReadinessRow(
            domain_category=domain_category,
            status="block",
            team_count=ZERO,
            readiness_score=ZERO,
            calibration_score=ZERO,
            memory_freshness_score=ZERO,
            evidence_coverage_score=ZERO,
            workload_health_score=ZERO,
            correction_follow_through_score=ZERO,
            newest_memory_age_seconds=None,
            oldest_memory_age_seconds=None,
            newest_observation_age_seconds=None,
            oldest_observation_age_seconds=None,
            reason_codes=(MISSING_DOMAIN_REASON,),
        )
    memory_ages = tuple(
        _seconds_between(item.memory_refreshed_at, generated_at) for item in inputs
    )
    observation_ages = tuple(
        _seconds_between(item.observed_at, generated_at) for item in inputs
    )
    calibration_score = _mean(item.calibration_score for item in inputs)
    memory_freshness_score = _mean(
        _memory_freshness_score(age, config) for age in memory_ages
    )
    evidence_coverage_score = _mean(item.evidence_coverage_score for item in inputs)
    workload_health_score = _mean(ONE - item.workload_ratio for item in inputs)
    correction_follow_through_score = _mean(
        item.correction_follow_through_score for item in inputs
    )
    readiness_score = _mean(
        (
            calibration_score,
            memory_freshness_score,
            evidence_coverage_score,
            workload_health_score,
            correction_follow_through_score,
        ),
    )
    reason_codes = _row_reason_codes(
        config=config,
        calibration_score=calibration_score,
        memory_freshness_score=memory_freshness_score,
        evidence_coverage_score=evidence_coverage_score,
        workload_health_score=workload_health_score,
        correction_follow_through_score=correction_follow_through_score,
    )
    return ResearchTeamDomainReviewReadinessRow(
        domain_category=domain_category,
        status=_row_status(reason_codes),
        team_count=_count(len(inputs)),
        readiness_score=readiness_score,
        calibration_score=calibration_score,
        memory_freshness_score=memory_freshness_score,
        evidence_coverage_score=evidence_coverage_score,
        workload_health_score=workload_health_score,
        correction_follow_through_score=correction_follow_through_score,
        newest_memory_age_seconds=_min_decimal(memory_ages),
        oldest_memory_age_seconds=_max_decimal(memory_ages),
        newest_observation_age_seconds=_min_decimal(observation_ages),
        oldest_observation_age_seconds=_max_decimal(observation_ages),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    config: ResearchTeamDomainReviewReadinessConfig,
    calibration_score: Decimal,
    memory_freshness_score: Decimal,
    evidence_coverage_score: Decimal,
    workload_health_score: Decimal,
    correction_follow_through_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_threshold_reason(
        reasons,
        metric=calibration_score,
        watch=config.min_pass_calibration_score,
        block=config.min_watch_calibration_score,
        watch_code="domain_review_readiness_calibration_watch",
        block_code="domain_review_readiness_calibration_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=memory_freshness_score,
        watch=config.min_pass_memory_freshness_score,
        block=config.min_watch_memory_freshness_score,
        watch_code="domain_review_readiness_memory_freshness_watch",
        block_code="domain_review_readiness_memory_freshness_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=evidence_coverage_score,
        watch=config.min_pass_evidence_coverage_score,
        block=config.min_watch_evidence_coverage_score,
        watch_code="domain_review_readiness_coverage_watch",
        block_code="domain_review_readiness_coverage_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=workload_health_score,
        watch=config.min_pass_workload_health_score,
        block=config.min_watch_workload_health_score,
        watch_code="domain_review_readiness_workload_watch",
        block_code="domain_review_readiness_workload_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=correction_follow_through_score,
        watch=config.min_pass_correction_follow_through_score,
        block=config.min_watch_correction_follow_through_score,
        watch_code="domain_review_readiness_correction_follow_through_watch",
        block_code="domain_review_readiness_correction_follow_through_block",
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
    elif metric < watch:
        reasons.append(watch_code)


def _memory_freshness_score(
    memory_age_seconds: Decimal,
    config: ResearchTeamDomainReviewReadinessConfig,
) -> Decimal:
    if memory_age_seconds >= config.max_watch_memory_age_seconds:
        return ZERO
    return (ONE - (memory_age_seconds / config.max_watch_memory_age_seconds)).quantize(
        QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_DOMAIN_REASON in reason_codes or any(
        reason_code.endswith("_block") for reason_code in reason_codes
    ):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamDomainReviewReadinessRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainReviewReadinessRow, ...],
    *,
    had_inputs: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not had_inputs:
        reasons.append(NO_INPUTS_REASON)
    if any(row.status == "block" for row in rows):
        reasons.append(BLOCK_PRESENT_REASON)
    if any(row.status == "watch" for row in rows):
        reasons.append(WATCH_PRESENT_REASON)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    if MISSING_DOMAIN_REASON in found:
        reasons.append(MISSING_DOMAIN_PRESENT_REASON)
    if any("calibration_" in reason_code for reason_code in found):
        reasons.append(CALIBRATION_PRESENT_REASON)
    if any("memory_freshness_" in reason_code for reason_code in found):
        reasons.append(MEMORY_PRESENT_REASON)
    if any("_coverage_" in reason_code for reason_code in found):
        reasons.append(COVERAGE_PRESENT_REASON)
    if any("workload_" in reason_code for reason_code in found):
        reasons.append(WORKLOAD_PRESENT_REASON)
    if any("correction_follow_through_" in reason_code for reason_code in found):
        reasons.append(CORRECTION_PRESENT_REASON)
    if PASS_REASON in found:
        reasons.append(PASS_PRESENT_REASON)
    return _require_report_reason_codes(tuple(reasons))


def _row_sort_key(row: ResearchTeamDomainReviewReadinessRow) -> tuple[int, Decimal, str]:
    return (STATUS_WEIGHT[row.status], row.readiness_score, row.domain_category)


def _normalize_inputs(
    inputs: Iterable[ResearchTeamDomainReviewReadinessInput],
) -> tuple[ResearchTeamDomainReviewReadinessInput, ...]:
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be iterable") from exc
    seen_labels: set[tuple[str, str]] = set()
    normalized: list[ResearchTeamDomainReviewReadinessInput] = []
    for item in items:
        if type(item) is not ResearchTeamDomainReviewReadinessInput:
            raise ValueError("input must be a ResearchTeamDomainReviewReadinessInput")
        _require_hard_flags("input", item)
        label_pair = (item.domain_category, item.team_label)
        if label_pair in seen_labels:
            raise ValueError("domain team labels must be unique")
        seen_labels.add(label_pair)
        normalized.append(item)
    return tuple(normalized)


def _validate_row(row: ResearchTeamDomainReviewReadinessRow) -> None:
    expected_score = _mean(
        (
            row.calibration_score,
            row.memory_freshness_score,
            row.evidence_coverage_score,
            row.workload_health_score,
            row.correction_follow_through_score,
        ),
    )
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score is inconsistent with component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status is inconsistent with reason_codes")
    if row.team_count == ZERO:
        if row.reason_codes != (MISSING_DOMAIN_REASON,):
            raise ValueError("missing domain rows must use the missing domain reason")
        if any(getattr(row, field_name) != ZERO for field_name in _ROW_RATIO_FIELDS):
            raise ValueError("missing domain rows must use zero scores")
        if any(getattr(row, field_name) is not None for field_name in _ROW_AGE_FIELDS):
            raise ValueError("missing domain rows must not include ages")
        return
    if MISSING_DOMAIN_REASON in row.reason_codes:
        raise ValueError("observed domain rows must not use the missing domain reason")
    if any(getattr(row, field_name) is None for field_name in _ROW_AGE_FIELDS):
        raise ValueError("observed domain rows must include ages")
    if row.newest_memory_age_seconds > row.oldest_memory_age_seconds:
        raise ValueError("memory ages must be ordered")
    if row.newest_observation_age_seconds > row.oldest_observation_age_seconds:
        raise ValueError("observation ages must be ordered")
    if row.team_count == ONE:
        if row.newest_memory_age_seconds != row.oldest_memory_age_seconds:
            raise ValueError("single-team memory ages must match")
        if row.newest_observation_age_seconds != row.oldest_observation_age_seconds:
            raise ValueError("single-team observation ages must match")
    config = ResearchTeamDomainReviewReadinessConfig()
    expected_reasons = _row_reason_codes(
        config=config,
        calibration_score=row.calibration_score,
        memory_freshness_score=row.memory_freshness_score,
        evidence_coverage_score=row.evidence_coverage_score,
        workload_health_score=row.workload_health_score,
        correction_follow_through_score=row.correction_follow_through_score,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes are inconsistent with component scores")
    freshest_memory_score = _memory_freshness_score(
        row.newest_memory_age_seconds,
        config,
    )
    stalest_memory_score = _memory_freshness_score(
        row.oldest_memory_age_seconds,
        config,
    )
    remaining_team_count = row.team_count - ONE
    minimum_memory_score = (
        (
            freshest_memory_score
            + (stalest_memory_score * remaining_team_count)
        )
        / row.team_count
    ).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    maximum_memory_score = (
        (
            stalest_memory_score
            + (freshest_memory_score * remaining_team_count)
        )
        / row.team_count
    ).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    if not (
        minimum_memory_score
        <= row.memory_freshness_score
        <= maximum_memory_score
    ):
        raise ValueError(
            "memory_freshness_score is inconsistent with memory ages",
        )


def _validate_report(report: ResearchTeamDomainReviewReadinessReport) -> None:
    rows = report.rows
    config = ResearchTeamDomainReviewReadinessConfig()
    for row in rows:
        if row.team_count == ZERO:
            continue
        expected_reasons = _row_reason_codes(
            config=config,
            calibration_score=row.calibration_score,
            memory_freshness_score=row.memory_freshness_score,
            evidence_coverage_score=row.evidence_coverage_score,
            workload_health_score=row.workload_health_score,
            correction_follow_through_score=row.correction_follow_through_score,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("row reason_codes are inconsistent with component scores")
    expected_values = {
        "domain_count": _count(len(PUBLIC_DOMAIN_CATEGORIES)),
        "observed_domain_count": _count(
            sum(1 for row in rows if MISSING_DOMAIN_REASON not in row.reason_codes),
        ),
        "missing_domain_count": _reason_count(rows, MISSING_DOMAIN_REASON),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_readiness_score": _mean(row.readiness_score for row in rows),
        "weakest_readiness_score": _min_decimal(row.readiness_score for row in rows),
        "average_calibration_score": _mean(row.calibration_score for row in rows),
        "average_memory_freshness_score": _mean(
            row.memory_freshness_score for row in rows
        ),
        "average_evidence_coverage_score": _mean(
            row.evidence_coverage_score for row in rows
        ),
        "average_workload_health_score": _mean(
            row.workload_health_score for row in rows
        ),
        "average_correction_follow_through_score": _mean(
            row.correction_follow_through_score for row in rows
        ),
        "status": _report_status(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")
    expected_reason_codes = _report_reason_codes(
        rows,
        had_inputs=any(row.team_count > ZERO for row in rows),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes are inconsistent with rows")


def _require_rows(
    rows: object,
) -> tuple[ResearchTeamDomainReviewReadinessRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchTeamDomainReviewReadinessRow] = []
    seen_categories: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainReviewReadinessRow:
            raise ValueError("row must be a ResearchTeamDomainReviewReadinessRow")
        _require_hard_flags("row", row)
        if row.domain_category in seen_categories:
            raise ValueError("domain categories must be unique")
        seen_categories.add(row.domain_category)
        normalized.append(row)
    if seen_categories != set(PUBLIC_DOMAIN_CATEGORIES):
        raise ValueError("rows must cover every public domain category")
    normalized_rows = tuple(normalized)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical report order")
    return normalized_rows


def _status_count(
    rows: tuple[ResearchTeamDomainReviewReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchTeamDomainReviewReadinessRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _mean(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    total = ZERO
    for item in items:
        total += item
    return (total / _count(len(items))).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return min(items).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return _quantize_decimal(field_name, decimal_value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(field_name, decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize_decimal(field_name, decimal_value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_decimal(field_name, decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(
        field_name,
        _require_finite_decimal(field_name, value),
    )


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a finite Decimal") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _as_generated_at_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != ZERO_TIME_DELTA:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _validate_not_after(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return total.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_REVIEW_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_domain_category(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_DOMAIN_CATEGORIES:
        raise ValueError(f"{field_name} must be a public domain category")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public aggregate label")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if PUBLIC_LABEL_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a public aggregate label")
    return text


def _require_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in REASON_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason")
        if item not in normalized:
            normalized.append(item)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in normalized)


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_codes contains unsupported report reason")
        if item not in normalized:
            normalized.append(item)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in normalized
    )


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in SHA256_HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _report_values_without_digest(
    report: ResearchTeamDomainReviewReadinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_payload(_json_ready(values))


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_payload(unsigned)


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_payload_statuses(payload: Mapping[str, object]) -> None:
    status = payload.get("status")
    if type(status) is not str or status not in PUBLIC_REVIEW_READINESS_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, Mapping):
                row_status = row.get("status")
                if (
                    type(row_status) is not str
                    or row_status not in PUBLIC_REVIEW_READINESS_STATUSES
                ):
                    raise ValueError("row status must be pass, watch, or block")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, (Decimal, float)) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public aggregate label in {label}")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public aggregate field in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and type(value) is list:
            raise ValueError(f"unsafe public container in {label}")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
