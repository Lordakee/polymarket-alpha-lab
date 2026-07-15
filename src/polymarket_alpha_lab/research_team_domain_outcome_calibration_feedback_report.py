"""Pure report reducer for settled team-domain outcome calibration feedback."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_OUTCOME_CALIBRATION_FEEDBACK_CONFIG_VERSION = (
    "research-team-domain-outcome-calibration-feedback-report-v0"
)
OUTCOME_CALIBRATION_REVIEW_BUCKETS = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EMPTY_REASON = "team_domain_outcome_calibration_feedback_empty"
PASS_REASON = "team_domain_outcome_calibration_feedback_pass"
REASON_SEQUENCE = (
    "team_domain_outcome_feedback_sample_count_block",
    "team_domain_outcome_feedback_brier_like_error_block",
    "team_domain_outcome_feedback_source_disagreement_block",
    "team_domain_outcome_feedback_memory_reuse_block",
    "team_domain_outcome_feedback_sample_count_watch",
    "team_domain_outcome_feedback_brier_like_error_watch",
    "team_domain_outcome_feedback_source_disagreement_watch",
    "team_domain_outcome_feedback_memory_reuse_watch",
    PASS_REASON,
)
REPORT_REASON_SEQUENCE = (EMPTY_REASON,) + REASON_SEQUENCE
BLOCK_REASONS = frozenset(reason for reason in REASON_SEQUENCE if reason.endswith("_block"))
WATCH_REASONS = frozenset(reason for reason in REASON_SEQUENCE if reason.endswith("_watch"))
BUCKET_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}

UNSAFE_IDENTIFIER_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source",
    "dsn",
    "table",
    "private",
    "internal",
    "confidential",
    "proprietary",
    "secret",
    "token",
    "password",
    "credential",
    "api_key",
    "private_key",
    "wallet",
    "account",
    "auth",
    "order",
    "trade",
    "trading",
    "live",
    "execute",
    "execution",
    "route",
    "buy",
    "sell",
    "size",
    "position",
    "sizing",
    "recommend",
    "recommendation",
)

ROW_PUBLIC_FIELDS = (
    "domain_id",
    "team_id",
    "sample_count",
    "brier_like_error",
    "source_disagreement_rate",
    "memory_reuse_rate",
    "review_bucket",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    "generated_at",
    "config_version",
    "min_pass_sample_count",
    "min_watch_sample_count",
    "max_pass_brier_like_error",
    "max_watch_brier_like_error",
    "max_pass_source_disagreement_rate",
    "max_watch_source_disagreement_rate",
    "min_pass_memory_reuse_rate",
    "min_watch_memory_reuse_rate",
    "input_count",
    "total_sample_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_brier_like_error",
    "average_source_disagreement_rate",
    "average_memory_reuse_rate",
    "review_bucket",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_OUTCOME_CALIBRATION_FEEDBACK_CONFIG_VERSION",
    "OUTCOME_CALIBRATION_REVIEW_BUCKETS",
    "ResearchTeamDomainOutcomeCalibrationFeedbackConfig",
    "ResearchTeamDomainSettledOutcomeFeedbackSummary",
    "ResearchTeamDomainOutcomeCalibrationFeedbackRow",
    "ResearchTeamDomainOutcomeCalibrationFeedbackReport",
    "build_research_team_domain_outcome_calibration_feedback_report",
    "research_team_domain_outcome_calibration_feedback_report_digest",
    "research_team_domain_outcome_calibration_feedback_report_payload",
    "validate_research_team_domain_outcome_calibration_feedback_public_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainOutcomeCalibrationFeedbackConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_OUTCOME_CALIBRATION_FEEDBACK_CONFIG_VERSION
    )
    min_pass_sample_count: Decimal = Decimal("30.000000")
    min_watch_sample_count: Decimal = Decimal("10.000000")
    max_pass_brier_like_error: Decimal = Decimal("0.100000")
    max_watch_brier_like_error: Decimal = Decimal("0.250000")
    max_pass_source_disagreement_rate: Decimal = Decimal("0.100000")
    max_watch_source_disagreement_rate: Decimal = Decimal("0.250000")
    min_pass_memory_reuse_rate: Decimal = Decimal("0.750000")
    min_watch_memory_reuse_rate: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainOutcomeCalibrationFeedbackConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_OUTCOME_CALIBRATION_FEEDBACK_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_pass_sample_count", "min_watch_sample_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_brier_like_error",
            "max_watch_brier_like_error",
            "max_pass_source_disagreement_rate",
            "max_watch_source_disagreement_rate",
            "min_pass_memory_reuse_rate",
            "min_watch_memory_reuse_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_sample_count < self.min_watch_sample_count:
            raise ValueError(
                "min_pass_sample_count must be at least min_watch_sample_count",
            )
        if self.max_pass_brier_like_error > self.max_watch_brier_like_error:
            raise ValueError(
                "max_pass_brier_like_error must not exceed "
                "max_watch_brier_like_error",
            )
        if (
            self.max_pass_source_disagreement_rate
            > self.max_watch_source_disagreement_rate
        ):
            raise ValueError(
                "max_pass_source_disagreement_rate must not exceed "
                "max_watch_source_disagreement_rate",
            )
        if self.min_pass_memory_reuse_rate < self.min_watch_memory_reuse_rate:
            raise ValueError(
                "min_pass_memory_reuse_rate must be at least "
                "min_watch_memory_reuse_rate",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSettledOutcomeFeedbackSummary(_FinalDataclass):
    domain_id: str
    team_id: str
    sample_count: Decimal
    brier_like_error: Decimal
    source_disagreement_rate: Decimal
    memory_reuse_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSettledOutcomeFeedbackSummary,
            "summary",
        )
        _require_public_identifier("domain_id", self.domain_id)
        _require_public_identifier("team_id", self.team_id)
        object.__setattr__(
            self,
            "sample_count",
            _require_count_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "brier_like_error",
            "source_disagreement_rate",
            "memory_reuse_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("summary", self)


@dataclass(frozen=True)
class ResearchTeamDomainOutcomeCalibrationFeedbackRow(_FinalDataclass):
    domain_id: str
    team_id: str
    sample_count: Decimal
    brier_like_error: Decimal
    source_disagreement_rate: Decimal
    memory_reuse_rate: Decimal
    review_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainOutcomeCalibrationFeedbackRow,
            "row",
        )
        _require_public_identifier("domain_id", self.domain_id)
        _require_public_identifier("team_id", self.team_id)
        object.__setattr__(
            self,
            "sample_count",
            _require_count_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "brier_like_error",
            "source_disagreement_rate",
            "memory_reuse_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_review_bucket("review_bucket", self.review_bucket)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_empty_reason=False),
        )
        if self.review_bucket != _review_bucket_for_reason_codes(self.reason_codes):
            raise ValueError("review_bucket must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainOutcomeCalibrationFeedbackReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    min_pass_sample_count: Decimal
    min_watch_sample_count: Decimal
    max_pass_brier_like_error: Decimal
    max_watch_brier_like_error: Decimal
    max_pass_source_disagreement_rate: Decimal
    max_watch_source_disagreement_rate: Decimal
    min_pass_memory_reuse_rate: Decimal
    min_watch_memory_reuse_rate: Decimal
    input_count: Decimal
    total_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_brier_like_error: Decimal | None
    average_source_disagreement_rate: Decimal | None
    average_memory_reuse_rate: Decimal | None
    review_bucket: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamDomainOutcomeCalibrationFeedbackRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainOutcomeCalibrationFeedbackReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "min_pass_sample_count",
            "min_watch_sample_count",
            "input_count",
            "total_sample_count",
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
            "max_pass_brier_like_error",
            "max_watch_brier_like_error",
            "max_pass_source_disagreement_rate",
            "max_watch_source_disagreement_rate",
            "min_pass_memory_reuse_rate",
            "min_watch_memory_reuse_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_brier_like_error",
            "average_source_disagreement_rate",
            "average_memory_reuse_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_review_bucket("review_bucket", self.review_bucket)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_domain_outcome_calibration_feedback_report(
    summaries: Iterable[ResearchTeamDomainSettledOutcomeFeedbackSummary],
    *,
    config: ResearchTeamDomainOutcomeCalibrationFeedbackConfig,
    generated_at: datetime,
) -> ResearchTeamDomainOutcomeCalibrationFeedbackReport:
    _require_exact_type(
        config,
        ResearchTeamDomainOutcomeCalibrationFeedbackConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_summaries = _normalize_summaries(summaries)
    rows = tuple(
        sorted(
            (
                _row_from_summary(summary, config=config)
                for summary in normalized_summaries
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "min_pass_sample_count": config.min_pass_sample_count,
        "min_watch_sample_count": config.min_watch_sample_count,
        "max_pass_brier_like_error": config.max_pass_brier_like_error,
        "max_watch_brier_like_error": config.max_watch_brier_like_error,
        "max_pass_source_disagreement_rate": (
            config.max_pass_source_disagreement_rate
        ),
        "max_watch_source_disagreement_rate": (
            config.max_watch_source_disagreement_rate
        ),
        "min_pass_memory_reuse_rate": config.min_pass_memory_reuse_rate,
        "min_watch_memory_reuse_rate": config.min_watch_memory_reuse_rate,
        "input_count": _count(len(rows)),
        "total_sample_count": _sum_decimal(row.sample_count for row in rows),
        "pass_count": _bucket_count(rows, "pass"),
        "watch_count": _bucket_count(rows, "watch"),
        "block_count": _bucket_count(rows, "block"),
        "average_brier_like_error": _weighted_average(rows, "brier_like_error"),
        "average_source_disagreement_rate": _weighted_average(
            rows,
            "source_disagreement_rate",
        ),
        "average_memory_reuse_rate": _weighted_average(rows, "memory_reuse_rate"),
        "review_bucket": _report_review_bucket(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainOutcomeCalibrationFeedbackReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_domain_outcome_calibration_feedback_report_payload(
    report: ResearchTeamDomainOutcomeCalibrationFeedbackReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainOutcomeCalibrationFeedbackReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a "
            "ResearchTeamDomainOutcomeCalibrationFeedbackReport or plain dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_team_domain_outcome_calibration_feedback_public_payload(payload)
    return payload


def validate_research_team_domain_outcome_calibration_feedback_public_payload(
    payload: dict[str, object],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_public_fields("public payload", payload, REPORT_PUBLIC_FIELDS)
    _require_payload_flags("public payload", payload)
    _require_canonical_public_json(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    if digest != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    _report_from_public_payload(payload)


def research_team_domain_outcome_calibration_feedback_report_digest(
    report: ResearchTeamDomainOutcomeCalibrationFeedbackReport | dict[str, object],
) -> str:
    payload = research_team_domain_outcome_calibration_feedback_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_summary(
    summary: ResearchTeamDomainSettledOutcomeFeedbackSummary,
    *,
    config: ResearchTeamDomainOutcomeCalibrationFeedbackConfig,
) -> ResearchTeamDomainOutcomeCalibrationFeedbackRow:
    reason_codes = _expected_row_reason_codes(
        sample_count=summary.sample_count,
        brier_like_error=summary.brier_like_error,
        source_disagreement_rate=summary.source_disagreement_rate,
        memory_reuse_rate=summary.memory_reuse_rate,
        config=config,
    )
    return ResearchTeamDomainOutcomeCalibrationFeedbackRow(
        domain_id=summary.domain_id,
        team_id=summary.team_id,
        sample_count=summary.sample_count,
        brier_like_error=summary.brier_like_error,
        source_disagreement_rate=summary.source_disagreement_rate,
        memory_reuse_rate=summary.memory_reuse_rate,
        review_bucket=_review_bucket_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _expected_row_reason_codes(
    *,
    sample_count: Decimal,
    brier_like_error: Decimal,
    source_disagreement_rate: Decimal,
    memory_reuse_rate: Decimal,
    config: ResearchTeamDomainOutcomeCalibrationFeedbackConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_reason(
        reasons,
        value=sample_count,
        pass_floor=config.min_pass_sample_count,
        watch_floor=config.min_watch_sample_count,
        watch_reason="team_domain_outcome_feedback_sample_count_watch",
        block_reason="team_domain_outcome_feedback_sample_count_block",
    )
    _append_high_reason(
        reasons,
        value=brier_like_error,
        pass_ceiling=config.max_pass_brier_like_error,
        watch_ceiling=config.max_watch_brier_like_error,
        watch_reason="team_domain_outcome_feedback_brier_like_error_watch",
        block_reason="team_domain_outcome_feedback_brier_like_error_block",
    )
    _append_high_reason(
        reasons,
        value=source_disagreement_rate,
        pass_ceiling=config.max_pass_source_disagreement_rate,
        watch_ceiling=config.max_watch_source_disagreement_rate,
        watch_reason="team_domain_outcome_feedback_source_disagreement_watch",
        block_reason="team_domain_outcome_feedback_source_disagreement_block",
    )
    _append_low_reason(
        reasons,
        value=memory_reuse_rate,
        pass_floor=config.min_pass_memory_reuse_rate,
        watch_floor=config.min_watch_memory_reuse_rate,
        watch_reason="team_domain_outcome_feedback_memory_reuse_watch",
        block_reason="team_domain_outcome_feedback_memory_reuse_block",
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _ordered_reason_codes(tuple(reasons), REPORT_REASON_SEQUENCE)


def _append_low_reason(
    reasons: list[str],
    *,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < watch_floor:
        reasons.append(block_reason)
    elif value < pass_floor:
        reasons.append(watch_reason)


def _append_high_reason(
    reasons: list[str],
    *,
    value: Decimal,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_ceiling:
        reasons.append(block_reason)
    elif value > pass_ceiling:
        reasons.append(watch_reason)


def _normalize_summaries(
    summaries: Iterable[ResearchTeamDomainSettledOutcomeFeedbackSummary],
) -> tuple[ResearchTeamDomainSettledOutcomeFeedbackSummary, ...]:
    if isinstance(summaries, (str, bytes)):
        raise ValueError("summaries must be an iterable")
    try:
        values = tuple(summaries)
    except TypeError as exc:
        raise ValueError("summaries must be an iterable") from exc
    normalized: list[ResearchTeamDomainSettledOutcomeFeedbackSummary] = []
    seen_pairs: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not ResearchTeamDomainSettledOutcomeFeedbackSummary:
            raise ValueError(
                "summaries must contain "
                "ResearchTeamDomainSettledOutcomeFeedbackSummary values",
            )
        _require_hard_flags("summary", value)
        pair = (value.domain_id, value.team_id)
        if pair in seen_pairs:
            raise ValueError("domain/team summaries must be unique")
        seen_pairs.add(pair)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: (item.domain_id, item.team_id)))


def _validate_report(
    report: ResearchTeamDomainOutcomeCalibrationFeedbackReport,
) -> None:
    config = _config_from_report(report)
    for row in report.rows:
        expected_reasons = _expected_row_reason_codes(
            sample_count=row.sample_count,
            brier_like_error=row.brier_like_error,
            source_disagreement_rate=row.source_disagreement_rate,
            memory_reuse_rate=row.memory_reuse_rate,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("row reason_codes must match calibration diagnostics")
        if row.review_bucket != _review_bucket_for_reason_codes(expected_reasons):
            raise ValueError("row review_bucket must match calibration diagnostics")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.total_sample_count != _sum_decimal(
        row.sample_count for row in report.rows
    ):
        raise ValueError("total_sample_count must match rows")
    if report.pass_count != _bucket_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _bucket_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _bucket_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_brier_like_error != _weighted_average(
        report.rows,
        "brier_like_error",
    ):
        raise ValueError("average_brier_like_error must match rows")
    if report.average_source_disagreement_rate != _weighted_average(
        report.rows,
        "source_disagreement_rate",
    ):
        raise ValueError("average_source_disagreement_rate must match rows")
    if report.average_memory_reuse_rate != _weighted_average(
        report.rows,
        "memory_reuse_rate",
    ):
        raise ValueError("average_memory_reuse_rate must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.review_bucket != _report_review_bucket(report.rows):
        raise ValueError("review_bucket must match rows")


def _config_from_report(
    report: ResearchTeamDomainOutcomeCalibrationFeedbackReport,
) -> ResearchTeamDomainOutcomeCalibrationFeedbackConfig:
    return ResearchTeamDomainOutcomeCalibrationFeedbackConfig(
        config_version=report.config_version,
        min_pass_sample_count=report.min_pass_sample_count,
        min_watch_sample_count=report.min_watch_sample_count,
        max_pass_brier_like_error=report.max_pass_brier_like_error,
        max_watch_brier_like_error=report.max_watch_brier_like_error,
        max_pass_source_disagreement_rate=(
            report.max_pass_source_disagreement_rate
        ),
        max_watch_source_disagreement_rate=(
            report.max_watch_source_disagreement_rate
        ),
        min_pass_memory_reuse_rate=report.min_pass_memory_reuse_rate,
        min_watch_memory_reuse_rate=report.min_watch_memory_reuse_rate,
    )


def _require_rows(
    rows: object,
) -> tuple[ResearchTeamDomainOutcomeCalibrationFeedbackRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    values = tuple(rows)
    normalized_rows: list[ResearchTeamDomainOutcomeCalibrationFeedbackRow] = []
    seen_pairs: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not ResearchTeamDomainOutcomeCalibrationFeedbackRow:
            raise ValueError(
                "rows must contain "
                "ResearchTeamDomainOutcomeCalibrationFeedbackRow values",
            )
        row = ResearchTeamDomainOutcomeCalibrationFeedbackRow(
            domain_id=value.domain_id,
            team_id=value.team_id,
            sample_count=value.sample_count,
            brier_like_error=value.brier_like_error,
            source_disagreement_rate=value.source_disagreement_rate,
            memory_reuse_rate=value.memory_reuse_rate,
            review_bucket=value.review_bucket,
            reason_codes=value.reason_codes,
            paper_only=value.paper_only,
            report_only=value.report_only,
            readonly=value.readonly,
        )
        pair = (row.domain_id, row.team_id)
        if pair in seen_pairs:
            raise ValueError("row domain/team values must be unique")
        seen_pairs.add(pair)
        normalized_rows.append(row)
    normalized = tuple(normalized_rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: ResearchTeamDomainOutcomeCalibrationFeedbackRow,
) -> tuple[int, str, str]:
    return (BUCKET_SORT_RANK[row.review_bucket], row.domain_id, row.team_id)


def _report_review_bucket(
    rows: tuple[ResearchTeamDomainOutcomeCalibrationFeedbackRow, ...],
) -> str:
    if any(row.review_bucket == "block" for row in rows):
        return "block"
    if any(row.review_bucket == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainOutcomeCalibrationFeedbackRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _combined_reason_codes(
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason != PASS_REASON for reason in reason_codes):
        reason_codes = tuple(
            reason for reason in reason_codes if reason != PASS_REASON
        )
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_codes must contain supported values")
    unique_reason_codes = tuple(
        reason for reason in REPORT_REASON_SEQUENCE if reason in reason_codes
    )
    return _ordered_reason_codes(unique_reason_codes, REPORT_REASON_SEQUENCE)


def _review_bucket_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return "block"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _bucket_count(
    rows: tuple[ResearchTeamDomainOutcomeCalibrationFeedbackRow, ...],
    review_bucket: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.review_bucket == review_bucket))


def _weighted_average(
    rows: tuple[ResearchTeamDomainOutcomeCalibrationFeedbackRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        total_sample_count = _sum_decimal(row.sample_count for row in rows)
        if total_sample_count == ZERO:
            return _quantize_ratio(
                _sum_decimal(getattr(row, field_name) for row in rows)
                / _count(len(rows)),
            )
        weighted_total = sum(
            (getattr(row, field_name) * row.sample_count for row in rows),
            ZERO,
        )
        return _quantize_ratio(weighted_total / total_sample_count)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _report_values_without_digest(
    report: ResearchTeamDomainOutcomeCalibrationFeedbackReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest values must produce a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return format(value, ".6f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool, int):
        return value
    raise ValueError("public payload contains an unsupported value")


def _report_from_public_payload(
    payload: dict[str, object],
) -> ResearchTeamDomainOutcomeCalibrationFeedbackReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a public list")
    rows = tuple(_row_from_public_payload(item) for item in rows_value)
    return ResearchTeamDomainOutcomeCalibrationFeedbackReport(
        generated_at=_require_public_datetime("generated_at", payload["generated_at"]),
        config_version=_require_public_identifier(
            "config_version",
            payload["config_version"],
        ),
        min_pass_sample_count=_require_public_count(
            "min_pass_sample_count",
            payload["min_pass_sample_count"],
        ),
        min_watch_sample_count=_require_public_count(
            "min_watch_sample_count",
            payload["min_watch_sample_count"],
        ),
        max_pass_brier_like_error=_require_public_ratio(
            "max_pass_brier_like_error",
            payload["max_pass_brier_like_error"],
        ),
        max_watch_brier_like_error=_require_public_ratio(
            "max_watch_brier_like_error",
            payload["max_watch_brier_like_error"],
        ),
        max_pass_source_disagreement_rate=_require_public_ratio(
            "max_pass_source_disagreement_rate",
            payload["max_pass_source_disagreement_rate"],
        ),
        max_watch_source_disagreement_rate=_require_public_ratio(
            "max_watch_source_disagreement_rate",
            payload["max_watch_source_disagreement_rate"],
        ),
        min_pass_memory_reuse_rate=_require_public_ratio(
            "min_pass_memory_reuse_rate",
            payload["min_pass_memory_reuse_rate"],
        ),
        min_watch_memory_reuse_rate=_require_public_ratio(
            "min_watch_memory_reuse_rate",
            payload["min_watch_memory_reuse_rate"],
        ),
        input_count=_require_public_count("input_count", payload["input_count"]),
        total_sample_count=_require_public_count(
            "total_sample_count",
            payload["total_sample_count"],
        ),
        pass_count=_require_public_count("pass_count", payload["pass_count"]),
        watch_count=_require_public_count("watch_count", payload["watch_count"]),
        block_count=_require_public_count("block_count", payload["block_count"]),
        average_brier_like_error=_require_optional_public_ratio(
            "average_brier_like_error",
            payload["average_brier_like_error"],
        ),
        average_source_disagreement_rate=_require_optional_public_ratio(
            "average_source_disagreement_rate",
            payload["average_source_disagreement_rate"],
        ),
        average_memory_reuse_rate=_require_optional_public_ratio(
            "average_memory_reuse_rate",
            payload["average_memory_reuse_rate"],
        ),
        review_bucket=_require_review_bucket(
            "review_bucket",
            payload["review_bucket"],
        ),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_SEQUENCE,
        ),
        rows=rows,
        derived_validation_digest=_require_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_true_flag("paper_only", payload["paper_only"]),
        report_only=_require_true_flag("report_only", payload["report_only"]),
        readonly=_require_true_flag("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchTeamDomainOutcomeCalibrationFeedbackRow:
    if type(value) is not dict:
        raise ValueError("rows must contain public JSON objects")
    _require_public_fields("row", value, ROW_PUBLIC_FIELDS)
    _require_payload_flags("row", value)
    return ResearchTeamDomainOutcomeCalibrationFeedbackRow(
        domain_id=_require_public_identifier("domain_id", value["domain_id"]),
        team_id=_require_public_identifier("team_id", value["team_id"]),
        sample_count=_require_public_count("sample_count", value["sample_count"]),
        brier_like_error=_require_public_ratio(
            "brier_like_error",
            value["brier_like_error"],
        ),
        source_disagreement_rate=_require_public_ratio(
            "source_disagreement_rate",
            value["source_disagreement_rate"],
        ),
        memory_reuse_rate=_require_public_ratio(
            "memory_reuse_rate",
            value["memory_reuse_rate"],
        ),
        review_bucket=_require_review_bucket(
            "review_bucket",
            value["review_bucket"],
        ),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            value["reason_codes"],
            REASON_SEQUENCE,
        ),
        paper_only=_require_true_flag("paper_only", value["paper_only"]),
        report_only=_require_true_flag("report_only", value["report_only"]),
        readonly=_require_true_flag("readonly", value["readonly"]),
    )


def _require_public_fields(
    label: str,
    value: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} keys must be strings")
    actual_fields = tuple(value)
    if frozenset(actual_fields) != frozenset(expected_fields):
        raise ValueError(f"{label} must contain exact public fields")
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must use canonical field order")


def _require_payload_flags(label: str, value: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_true_flag(field_name, value.get(field_name))


def _require_canonical_public_json(
    value: object,
    path: str = "public payload",
) -> None:
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{path} must use Decimal-derived strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} must use canonical plain JSON values")
            _require_canonical_public_json(item, f"{path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_canonical_public_json(item, f"{path}.{index}")
        return
    raise ValueError(f"{path} must use canonical plain JSON values")


def _require_public_reason_codes(
    field_name: str,
    value: object,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    return _ordered_reason_codes(tuple(value), sequence)


def _require_reason_codes(
    value: object,
    *,
    allow_empty_reason: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    allowed = REPORT_REASON_SEQUENCE if allow_empty_reason else REASON_SEQUENCE
    return _ordered_reason_codes(reason_codes, allowed)


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    return _ordered_reason_codes(reason_codes, REPORT_REASON_SEQUENCE)


def _ordered_reason_codes(
    reason_codes: tuple[object, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in sequence:
            raise ValueError("reason_codes must contain supported values")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    ordered = tuple(reason for reason in sequence if reason in normalized)
    if tuple(normalized) != ordered:
        raise ValueError("reason_codes must be deterministically ordered")
    if EMPTY_REASON in ordered and ordered != (EMPTY_REASON,):
        raise ValueError("empty reason must be exclusive")
    if PASS_REASON in ordered and ordered != (PASS_REASON,):
        raise ValueError("pass reason must be exclusive")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_review_bucket(field_name: str, value: object) -> str:
    if type(value) is not str or value not in OUTCOME_CALIBRATION_REVIEW_BUCKETS:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(field_name, value)
    if decimal_value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    normalized = _quantize(decimal_value)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        if normalized != normalized.quantize(COUNT_QUANTUM):
            raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    normalized = _require_decimal(field_name, value)
    return normalized


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    return _quantize(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return Decimal(value)


def _require_public_count(field_name: str, value: object) -> Decimal:
    return _require_count_decimal(
        field_name,
        _require_public_decimal(field_name, value),
    )


def _require_public_ratio(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(
        field_name,
        _require_public_decimal(field_name, value),
    )


def _require_optional_public_ratio(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_public_ratio(field_name, value)


def _require_public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized
