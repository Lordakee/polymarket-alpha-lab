"""Pure report-only reducer for research-team review memory quality regression."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_REVIEW_MEMORY_QUALITY_REGRESSION_CONFIG_VERSION = (
    "research-team-review-memory-quality-regression-report-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HALF = Decimal("0.500000")
_QUANT = Decimal("0.000001")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_CONFIG_RATIO_FIELDS = (
    "max_pass_stale_memory_reuse_rate",
    "max_watch_stale_memory_reuse_rate",
    "min_pass_correction_followthrough_score",
    "min_watch_correction_followthrough_score",
    "max_pass_calibration_drop_score",
    "max_watch_calibration_drop_score",
    "min_pass_evidence_coverage_score",
    "min_watch_evidence_coverage_score",
    "min_pass_contradiction_handling_score",
    "min_watch_contradiction_handling_score",
)
_CONFIG_MEASURE_FIELDS = (
    "max_pass_review_latency_hours",
    "max_watch_review_latency_hours",
)
_ROW_REASON_CODE_GROUPS = (
    (
        "stale_memory_reuse_pass",
        "stale_memory_reuse_watch",
        "stale_memory_reuse_high",
    ),
    (
        "correction_followthrough_pass",
        "correction_followthrough_watch",
        "correction_followthrough_low",
    ),
    (
        "calibration_trend_pass",
        "calibration_trend_watch",
        "calibration_trend_drop",
    ),
    (
        "evidence_coverage_pass",
        "evidence_coverage_watch",
        "evidence_coverage_low",
    ),
    (
        "contradiction_handling_pass",
        "contradiction_handling_watch",
        "contradiction_handling_low",
    ),
    (
        "review_latency_pass",
        "review_latency_watch",
        "review_latency_slow",
    ),
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "live",
    "buy",
    "sell",
    "position",
    "recommend",
    "sizing",
    "source",
)
_REASON_CODE_SEQUENCE = (
    "review_memory_quality_regression_report_pass",
    "review_memory_quality_regression_report_block_rows",
    "review_memory_quality_regression_report_watch_rows",
    "review_memory_quality_regression_empty_input",
    "review_memory_quality_regression_pass",
    "review_memory_quality_regression_watch",
    "review_memory_quality_regression_block",
    "stale_memory_reuse_pass",
    "stale_memory_reuse_watch",
    "stale_memory_reuse_high",
    "correction_followthrough_pass",
    "correction_followthrough_watch",
    "correction_followthrough_low",
    "calibration_trend_pass",
    "calibration_trend_watch",
    "calibration_trend_drop",
    "evidence_coverage_pass",
    "evidence_coverage_watch",
    "evidence_coverage_low",
    "contradiction_handling_pass",
    "contradiction_handling_watch",
    "contradiction_handling_low",
    "review_latency_pass",
    "review_latency_watch",
    "review_latency_slow",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_MEMORY_QUALITY_REGRESSION_CONFIG_VERSION",
    "ResearchTeamReviewMemoryQualityRegressionConfig",
    "ResearchTeamReviewMemoryQualityRegressionReasonCodeCount",
    "ResearchTeamReviewMemoryQualityRegressionReport",
    "ResearchTeamReviewMemoryQualityRegressionRow",
    "ResearchTeamReviewMemoryQualityRegressionSnapshot",
    "build_research_team_review_memory_quality_regression_report",
    "research_team_review_memory_quality_regression_report_digest",
    "research_team_review_memory_quality_regression_report_payload",
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
class ResearchTeamReviewMemoryQualityRegressionConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_REVIEW_MEMORY_QUALITY_REGRESSION_CONFIG_VERSION
    )
    max_pass_stale_memory_reuse_rate: Decimal = Decimal("0.050000")
    max_watch_stale_memory_reuse_rate: Decimal = Decimal("0.200000")
    min_pass_correction_followthrough_score: Decimal = Decimal("0.900000")
    min_watch_correction_followthrough_score: Decimal = Decimal("0.700000")
    max_pass_calibration_drop_score: Decimal = Decimal("0.020000")
    max_watch_calibration_drop_score: Decimal = Decimal("0.100000")
    min_pass_evidence_coverage_score: Decimal = Decimal("0.900000")
    min_watch_evidence_coverage_score: Decimal = Decimal("0.700000")
    min_pass_contradiction_handling_score: Decimal = Decimal("0.900000")
    min_watch_contradiction_handling_score: Decimal = Decimal("0.700000")
    max_pass_review_latency_hours: Decimal = Decimal("12.000000")
    max_watch_review_latency_hours: Decimal = Decimal("36.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamReviewMemoryQualityRegressionConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for field_name in _CONFIG_RATIO_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in _CONFIG_MEASURE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewMemoryQualityRegressionSnapshot(_FinalPublicDataclass):
    team_key: str
    reviewed_item_count: Decimal
    stale_memory_reuse_count: Decimal
    correction_required_count: Decimal
    correction_completed_count: Decimal
    calibration_prior_score: Decimal
    calibration_current_score: Decimal
    evidence_required_count: Decimal
    evidence_confirmed_count: Decimal
    contradiction_flag_count: Decimal
    contradiction_resolved_count: Decimal
    mean_review_latency_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamReviewMemoryQualityRegressionSnapshot,
            "snapshot",
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        for field_name in (
            "reviewed_item_count",
            "stale_memory_reuse_count",
            "correction_required_count",
            "correction_completed_count",
            "evidence_required_count",
            "evidence_confirmed_count",
            "contradiction_flag_count",
            "contradiction_resolved_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_prior_score",
            "calibration_current_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_review_latency_hours",
            _require_nonnegative_measure_decimal(
                "mean_review_latency_hours",
                self.mean_review_latency_hours,
            ),
        )
        _validate_snapshot(self)
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamReviewMemoryQualityRegressionRow(_FinalPublicDataclass):
    team_key: str
    reviewed_item_count: Decimal
    stale_memory_reuse_rate: Decimal
    correction_followthrough_score: Decimal
    calibration_drop_score: Decimal
    evidence_coverage_score: Decimal
    contradiction_handling_score: Decimal
    mean_review_latency_hours: Decimal
    quality_regression_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewMemoryQualityRegressionRow, "row")
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "reviewed_item_count",
            _require_nonnegative_count_decimal(
                "reviewed_item_count",
                self.reviewed_item_count,
            ),
        )
        for field_name in (
            "stale_memory_reuse_rate",
            "correction_followthrough_score",
            "calibration_drop_score",
            "evidence_coverage_score",
            "contradiction_handling_score",
            "quality_regression_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_review_latency_hours",
            _require_nonnegative_measure_decimal(
                "mean_review_latency_hours",
                self.mean_review_latency_hours,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamReviewMemoryQualityRegressionReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamReviewMemoryQualityRegressionReasonCodeCount,
            "count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_supported_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamReviewMemoryQualityRegressionReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    max_pass_stale_memory_reuse_rate: Decimal
    max_watch_stale_memory_reuse_rate: Decimal
    min_pass_correction_followthrough_score: Decimal
    min_watch_correction_followthrough_score: Decimal
    max_pass_calibration_drop_score: Decimal
    max_watch_calibration_drop_score: Decimal
    min_pass_evidence_coverage_score: Decimal
    min_watch_evidence_coverage_score: Decimal
    min_pass_contradiction_handling_score: Decimal
    min_watch_contradiction_handling_score: Decimal
    max_pass_review_latency_hours: Decimal
    max_watch_review_latency_hours: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_stale_memory_reuse_rate: Decimal
    mean_correction_followthrough_score: Decimal
    mean_calibration_drop_score: Decimal
    mean_evidence_coverage_score: Decimal
    mean_contradiction_handling_score: Decimal
    mean_review_latency_hours: Decimal
    mean_quality_regression_score: Decimal
    max_quality_regression_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamReviewMemoryQualityRegressionReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewMemoryQualityRegressionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for field_name in _CONFIG_RATIO_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in _CONFIG_MEASURE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_stale_memory_reuse_rate",
            "mean_correction_followthrough_score",
            "mean_calibration_drop_score",
            "mean_evidence_coverage_score",
            "mean_contradiction_handling_score",
            "mean_quality_regression_score",
            "max_quality_regression_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_review_latency_hours",
            _require_nonnegative_measure_decimal(
                "mean_review_latency_hours",
                self.mean_review_latency_hours,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.public_digest:
            _require_sha256_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report fields")
        object.__setattr__(self, "public_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        validated = _revalidate_report(self)
        payload = _json_ready(asdict(validated))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_team_review_memory_quality_regression_report(
    snapshots: Sequence[ResearchTeamReviewMemoryQualityRegressionSnapshot],
    *,
    generated_at: datetime,
    config: ResearchTeamReviewMemoryQualityRegressionConfig | None = None,
) -> ResearchTeamReviewMemoryQualityRegressionReport:
    if config is None:
        config = ResearchTeamReviewMemoryQualityRegressionConfig()
    config = _revalidate_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(_row_from_snapshot(snapshot, config) for snapshot in normalized_snapshots)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        **{
            field_name: getattr(config, field_name)
            for field_name in _CONFIG_RATIO_FIELDS + _CONFIG_MEASURE_FIELDS
        },
        "team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": (
            _decimal_count(1) if not rows else _decimal_count(_status_count(rows, "block"))
        ),
        "mean_stale_memory_reuse_rate": _mean_row_decimal(
            rows,
            "stale_memory_reuse_rate",
            ratio=True,
        ),
        "mean_correction_followthrough_score": _mean_row_decimal(
            rows,
            "correction_followthrough_score",
            ratio=True,
        ),
        "mean_calibration_drop_score": _mean_row_decimal(
            rows,
            "calibration_drop_score",
            ratio=True,
        ),
        "mean_evidence_coverage_score": _mean_row_decimal(
            rows,
            "evidence_coverage_score",
            ratio=True,
        ),
        "mean_contradiction_handling_score": _mean_row_decimal(
            rows,
            "contradiction_handling_score",
            ratio=True,
        ),
        "mean_review_latency_hours": _mean_row_decimal(
            rows,
            "mean_review_latency_hours",
        ),
        "mean_quality_regression_score": _mean_row_decimal(
            rows,
            "quality_regression_score",
            ratio=True,
        ),
        "max_quality_regression_score": _max_row_decimal(
            rows,
            "quality_regression_score",
            ratio=True,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": (),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["reason_code_counts"] = _reason_code_counts(values["reason_codes"], rows)
    return ResearchTeamReviewMemoryQualityRegressionReport(
        **values,
        public_digest=_digest_from_values(values),
    )


def research_team_review_memory_quality_regression_report_payload(
    report: ResearchTeamReviewMemoryQualityRegressionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamReviewMemoryQualityRegressionReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        validated_report = _report_from_public_payload(report)
        payload = validated_report.payload
        if payload != report:
            raise ValueError("payload must use canonical public ordering and values")
        return payload
    raise ValueError(
        "report must be a ResearchTeamReviewMemoryQualityRegressionReport or payload",
    )


def research_team_review_memory_quality_regression_report_digest(
    report: ResearchTeamReviewMemoryQualityRegressionReport | dict[str, Any],
) -> str:
    payload = research_team_review_memory_quality_regression_report_payload(report)
    return _payload_digest(payload)


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


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamReviewMemoryQualityRegressionReport:
    _require_exact_payload_fields(
        "payload",
        payload,
        ResearchTeamReviewMemoryQualityRegressionReport,
    )
    _validate_payload_digest(payload)
    rows = tuple(
        _row_from_public_payload(item)
        for item in _require_payload_list("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in _require_payload_list(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    reason_codes = tuple(
        _require_payload_string("reason_code", item)
        for item in _require_payload_list("reason_codes", payload["reason_codes"])
    )
    report = ResearchTeamReviewMemoryQualityRegressionReport(
        generated_at=_require_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_require_payload_string(
            "config_version",
            payload["config_version"],
        ),
        **{
            field_name: _require_payload_decimal(
                field_name,
                payload[field_name],
            )
            for field_name in _CONFIG_RATIO_FIELDS + _CONFIG_MEASURE_FIELDS
        },
        team_count=_require_payload_decimal("team_count", payload["team_count"]),
        pass_count=_require_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_require_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_require_payload_decimal("block_count", payload["block_count"]),
        mean_stale_memory_reuse_rate=_require_payload_decimal(
            "mean_stale_memory_reuse_rate",
            payload["mean_stale_memory_reuse_rate"],
        ),
        mean_correction_followthrough_score=_require_payload_decimal(
            "mean_correction_followthrough_score",
            payload["mean_correction_followthrough_score"],
        ),
        mean_calibration_drop_score=_require_payload_decimal(
            "mean_calibration_drop_score",
            payload["mean_calibration_drop_score"],
        ),
        mean_evidence_coverage_score=_require_payload_decimal(
            "mean_evidence_coverage_score",
            payload["mean_evidence_coverage_score"],
        ),
        mean_contradiction_handling_score=_require_payload_decimal(
            "mean_contradiction_handling_score",
            payload["mean_contradiction_handling_score"],
        ),
        mean_review_latency_hours=_require_payload_decimal(
            "mean_review_latency_hours",
            payload["mean_review_latency_hours"],
        ),
        mean_quality_regression_score=_require_payload_decimal(
            "mean_quality_regression_score",
            payload["mean_quality_regression_score"],
        ),
        max_quality_regression_score=_require_payload_decimal(
            "max_quality_regression_score",
            payload["max_quality_regression_score"],
        ),
        status=_require_payload_string("status", payload["status"]),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        public_digest=_require_payload_string(
            "public_digest",
            payload["public_digest"],
        ),
        paper_only=_require_payload_true("paper_only", payload["paper_only"]),
        report_only=_require_payload_true("report_only", payload["report_only"]),
        readonly=_require_payload_true("readonly", payload["readonly"]),
    )
    return report


def _row_from_public_payload(
    payload: object,
) -> ResearchTeamReviewMemoryQualityRegressionRow:
    payload = _require_payload_dict("row payload", payload)
    _require_exact_payload_fields(
        "row payload",
        payload,
        ResearchTeamReviewMemoryQualityRegressionRow,
    )
    return ResearchTeamReviewMemoryQualityRegressionRow(
        team_key=_require_payload_string("team_key", payload["team_key"]),
        reviewed_item_count=_require_payload_decimal(
            "reviewed_item_count",
            payload["reviewed_item_count"],
        ),
        stale_memory_reuse_rate=_require_payload_decimal(
            "stale_memory_reuse_rate",
            payload["stale_memory_reuse_rate"],
        ),
        correction_followthrough_score=_require_payload_decimal(
            "correction_followthrough_score",
            payload["correction_followthrough_score"],
        ),
        calibration_drop_score=_require_payload_decimal(
            "calibration_drop_score",
            payload["calibration_drop_score"],
        ),
        evidence_coverage_score=_require_payload_decimal(
            "evidence_coverage_score",
            payload["evidence_coverage_score"],
        ),
        contradiction_handling_score=_require_payload_decimal(
            "contradiction_handling_score",
            payload["contradiction_handling_score"],
        ),
        mean_review_latency_hours=_require_payload_decimal(
            "mean_review_latency_hours",
            payload["mean_review_latency_hours"],
        ),
        quality_regression_score=_require_payload_decimal(
            "quality_regression_score",
            payload["quality_regression_score"],
        ),
        status=_require_payload_string("status", payload["status"]),
        reason_codes=tuple(
            _require_payload_string("reason_code", item)
            for item in _require_payload_list("reason_codes", payload["reason_codes"])
        ),
        paper_only=_require_payload_true("paper_only", payload["paper_only"]),
        report_only=_require_payload_true("report_only", payload["report_only"]),
        readonly=_require_payload_true("readonly", payload["readonly"]),
    )


def _reason_code_count_from_public_payload(
    payload: object,
) -> ResearchTeamReviewMemoryQualityRegressionReasonCodeCount:
    payload = _require_payload_dict("reason code count payload", payload)
    _require_exact_payload_fields(
        "reason code count payload",
        payload,
        ResearchTeamReviewMemoryQualityRegressionReasonCodeCount,
    )
    return ResearchTeamReviewMemoryQualityRegressionReasonCodeCount(
        reason_code=_require_payload_string("reason_code", payload["reason_code"]),
        count=_require_payload_decimal("count", payload["count"]),
        paper_only=_require_payload_true("paper_only", payload["paper_only"]),
        report_only=_require_payload_true("report_only", payload["report_only"]),
        readonly=_require_payload_true("readonly", payload["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    payload: dict[str, Any],
    public_type: type[object],
) -> None:
    expected_fields = {field.name for field in fields(public_type)}
    if any(type(key) is not str for key in payload) or set(payload) != expected_fields:
        raise ValueError(f"{label} fields must exactly match the public schema")


def _require_payload_dict(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a dict")
    return value


def _require_payload_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(
            f"{field_name} must use canonical six-decimal string form",
        )
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(
            f"{field_name} must use canonical six-decimal string form",
        ) from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    if format(_quantize_decimal(decimal_value), "f") != value:
        raise ValueError(
            f"{field_name} must use canonical six-decimal string form",
        )
    return decimal_value


def _require_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    parsed = _as_utc(field_name, parsed)
    if parsed.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return parsed


def _row_from_snapshot(
    snapshot: ResearchTeamReviewMemoryQualityRegressionSnapshot,
    config: ResearchTeamReviewMemoryQualityRegressionConfig,
) -> ResearchTeamReviewMemoryQualityRegressionRow:
    stale_reuse_rate = _ratio_or_zero(
        snapshot.stale_memory_reuse_count,
        snapshot.reviewed_item_count,
    )
    correction_score = _ratio_or_one(
        snapshot.correction_completed_count,
        snapshot.correction_required_count,
    )
    calibration_drop = _calibration_drop(snapshot)
    evidence_score = _ratio_or_zero(
        snapshot.evidence_confirmed_count,
        snapshot.evidence_required_count,
    )
    contradiction_score = _ratio_or_one(
        snapshot.contradiction_resolved_count,
        snapshot.contradiction_flag_count,
    )
    regression_score = _quality_regression_score(
        stale_memory_reuse_rate=stale_reuse_rate,
        correction_followthrough_score=correction_score,
        calibration_drop_score=calibration_drop,
        evidence_coverage_score=evidence_score,
        contradiction_handling_score=contradiction_score,
        review_latency_hours=snapshot.mean_review_latency_hours,
        config=config,
    )
    status = _row_status(
        stale_memory_reuse_rate=stale_reuse_rate,
        correction_followthrough_score=correction_score,
        calibration_drop_score=calibration_drop,
        evidence_coverage_score=evidence_score,
        contradiction_handling_score=contradiction_score,
        review_latency_hours=snapshot.mean_review_latency_hours,
        config=config,
    )
    return ResearchTeamReviewMemoryQualityRegressionRow(
        team_key=snapshot.team_key,
        reviewed_item_count=snapshot.reviewed_item_count,
        stale_memory_reuse_rate=stale_reuse_rate,
        correction_followthrough_score=correction_score,
        calibration_drop_score=calibration_drop,
        evidence_coverage_score=evidence_score,
        contradiction_handling_score=contradiction_score,
        mean_review_latency_hours=snapshot.mean_review_latency_hours,
        quality_regression_score=regression_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            stale_memory_reuse_rate=stale_reuse_rate,
            correction_followthrough_score=correction_score,
            calibration_drop_score=calibration_drop,
            evidence_coverage_score=evidence_score,
            contradiction_handling_score=contradiction_score,
            review_latency_hours=snapshot.mean_review_latency_hours,
            config=config,
        ),
    )


def _quality_regression_score(
    *,
    stale_memory_reuse_rate: Decimal,
    correction_followthrough_score: Decimal,
    calibration_drop_score: Decimal,
    evidence_coverage_score: Decimal,
    contradiction_handling_score: Decimal,
    review_latency_hours: Decimal,
    config: ResearchTeamReviewMemoryQualityRegressionConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _ratio(
            _lower_ratio_is_better_variance(
                stale_memory_reuse_rate,
                config.max_pass_stale_memory_reuse_rate,
                config.max_watch_stale_memory_reuse_rate,
            )
            + _higher_is_better_variance(
                correction_followthrough_score,
                config.min_pass_correction_followthrough_score,
                config.min_watch_correction_followthrough_score,
            )
            + _lower_ratio_is_better_variance(
                calibration_drop_score,
                config.max_pass_calibration_drop_score,
                config.max_watch_calibration_drop_score,
            )
            + _higher_is_better_variance(
                evidence_coverage_score,
                config.min_pass_evidence_coverage_score,
                config.min_watch_evidence_coverage_score,
            )
            + _higher_is_better_variance(
                contradiction_handling_score,
                config.min_pass_contradiction_handling_score,
                config.min_watch_contradiction_handling_score,
            )
            + _lower_measure_is_better_variance(
                review_latency_hours,
                config.max_pass_review_latency_hours,
                config.max_watch_review_latency_hours,
            ),
            Decimal("6.000000"),
        )


def _row_status(
    *,
    stale_memory_reuse_rate: Decimal,
    correction_followthrough_score: Decimal,
    calibration_drop_score: Decimal,
    evidence_coverage_score: Decimal,
    contradiction_handling_score: Decimal,
    review_latency_hours: Decimal,
    config: ResearchTeamReviewMemoryQualityRegressionConfig,
) -> str:
    if (
        stale_memory_reuse_rate > config.max_watch_stale_memory_reuse_rate
        or correction_followthrough_score
        < config.min_watch_correction_followthrough_score
        or calibration_drop_score > config.max_watch_calibration_drop_score
        or evidence_coverage_score < config.min_watch_evidence_coverage_score
        or contradiction_handling_score
        < config.min_watch_contradiction_handling_score
        or review_latency_hours > config.max_watch_review_latency_hours
    ):
        return "block"
    if (
        stale_memory_reuse_rate > config.max_pass_stale_memory_reuse_rate
        or correction_followthrough_score < config.min_pass_correction_followthrough_score
        or calibration_drop_score > config.max_pass_calibration_drop_score
        or evidence_coverage_score < config.min_pass_evidence_coverage_score
        or contradiction_handling_score < config.min_pass_contradiction_handling_score
        or review_latency_hours > config.max_pass_review_latency_hours
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    stale_memory_reuse_rate: Decimal,
    correction_followthrough_score: Decimal,
    calibration_drop_score: Decimal,
    evidence_coverage_score: Decimal,
    contradiction_handling_score: Decimal,
    review_latency_hours: Decimal,
    config: ResearchTeamReviewMemoryQualityRegressionConfig,
) -> tuple[str, ...]:
    reason_codes = [f"review_memory_quality_regression_{status}"]
    reason_codes.append(
        _low_metric_reason(
            "stale_memory_reuse",
            stale_memory_reuse_rate,
            config.max_pass_stale_memory_reuse_rate,
            config.max_watch_stale_memory_reuse_rate,
            high_reason="stale_memory_reuse_high",
        ),
    )
    reason_codes.append(
        _high_metric_reason(
            "correction_followthrough",
            correction_followthrough_score,
            config.min_pass_correction_followthrough_score,
            config.min_watch_correction_followthrough_score,
            low_reason="correction_followthrough_low",
        ),
    )
    reason_codes.append(
        _low_metric_reason(
            "calibration_trend",
            calibration_drop_score,
            config.max_pass_calibration_drop_score,
            config.max_watch_calibration_drop_score,
            high_reason="calibration_trend_drop",
        ),
    )
    reason_codes.append(
        _high_metric_reason(
            "evidence_coverage",
            evidence_coverage_score,
            config.min_pass_evidence_coverage_score,
            config.min_watch_evidence_coverage_score,
            low_reason="evidence_coverage_low",
        ),
    )
    reason_codes.append(
        _high_metric_reason(
            "contradiction_handling",
            contradiction_handling_score,
            config.min_pass_contradiction_handling_score,
            config.min_watch_contradiction_handling_score,
            low_reason="contradiction_handling_low",
        ),
    )
    reason_codes.append(
        _low_metric_reason(
            "review_latency",
            review_latency_hours,
            config.max_pass_review_latency_hours,
            config.max_watch_review_latency_hours,
            pass_reason="review_latency_pass",
            watch_reason="review_latency_watch",
            high_reason="review_latency_slow",
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _higher_is_better_variance(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value >= pass_threshold:
        return _ZERO
    if value >= watch_threshold:
        return _clamp_ratio(
            ((pass_threshold - value) / (pass_threshold - watch_threshold)) * _HALF,
        )
    return _clamp_ratio(_HALF + ((watch_threshold - value) / watch_threshold) * _HALF)


def _lower_ratio_is_better_variance(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return _ZERO
    if value <= watch_threshold:
        return _clamp_ratio(
            ((value - pass_threshold) / (watch_threshold - pass_threshold)) * _HALF,
        )
    return _clamp_ratio(
        _HALF + ((value - watch_threshold) / (_ONE - watch_threshold)) * _HALF,
    )


def _lower_measure_is_better_variance(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return _ZERO
    if value <= watch_threshold:
        return _clamp_ratio(
            ((value - pass_threshold) / (watch_threshold - pass_threshold)) * _HALF,
        )
    return _clamp_ratio(_HALF + ((value - watch_threshold) / watch_threshold) * _HALF)


def _high_metric_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    *,
    low_reason: str,
) -> str:
    if value >= pass_threshold:
        return f"{prefix}_pass"
    if value >= watch_threshold:
        return f"{prefix}_watch"
    return low_reason


def _low_metric_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    *,
    pass_reason: str | None = None,
    watch_reason: str | None = None,
    high_reason: str,
) -> str:
    if value <= pass_threshold:
        return pass_reason if pass_reason is not None else f"{prefix}_pass"
    if value <= watch_threshold:
        return watch_reason if watch_reason is not None else f"{prefix}_watch"
    return high_reason


def _calibration_drop(
    snapshot: ResearchTeamReviewMemoryQualityRegressionSnapshot,
) -> Decimal:
    if snapshot.calibration_current_score >= snapshot.calibration_prior_score:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(
            snapshot.calibration_prior_score - snapshot.calibration_current_score,
        )


def _report_status(
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("review_memory_quality_regression_empty_input",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append("review_memory_quality_regression_report_block_rows")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("review_memory_quality_regression_report_watch_rows")
    if not reason_codes:
        reason_codes.append("review_memory_quality_regression_report_pass")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    report_reason_codes: object,
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
) -> tuple[ResearchTeamReviewMemoryQualityRegressionReasonCodeCount, ...]:
    if type(report_reason_codes) is not tuple:
        raise ValueError("report_reason_codes must be a tuple")
    counter: Counter[str] = Counter(report_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamReviewMemoryQualityRegressionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _ratio(numerator, denominator)


def _ratio_or_one(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ONE
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize_decimal(value)


def _mean_row_decimal(
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
    field_name: str,
    *,
    ratio: bool = False,
) -> Decimal:
    if not rows:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        value = sum(
            (getattr(row, field_name) for row in rows),
            start=_ZERO,
        ) / _decimal_count(len(rows))
    if ratio:
        return _clamp_ratio(value)
    return _quantize_decimal(value)


def _max_row_decimal(
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
    field_name: str,
    *,
    ratio: bool = False,
) -> Decimal:
    if not rows:
        return _ZERO
    value = max(getattr(row, field_name) for row in rows)
    if ratio:
        return _clamp_ratio(value)
    return _quantize_decimal(value)


def _status_count(
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _public_dataclass_values(
    value: object,
    public_type: type[object],
) -> dict[str, object]:
    return {
        field.name: getattr(value, field.name)
        for field in fields(public_type)
    }


def _revalidate_config(
    config: object,
) -> ResearchTeamReviewMemoryQualityRegressionConfig:
    _require_exact_type(
        config,
        ResearchTeamReviewMemoryQualityRegressionConfig,
        "config",
    )
    return ResearchTeamReviewMemoryQualityRegressionConfig(
        **_public_dataclass_values(
            config,
            ResearchTeamReviewMemoryQualityRegressionConfig,
        ),
    )


def _revalidate_report(
    report: object,
) -> ResearchTeamReviewMemoryQualityRegressionReport:
    _require_exact_type(
        report,
        ResearchTeamReviewMemoryQualityRegressionReport,
        "report",
    )
    return ResearchTeamReviewMemoryQualityRegressionReport(
        **_public_dataclass_values(
            report,
            ResearchTeamReviewMemoryQualityRegressionReport,
        ),
    )


def _normalize_snapshots(
    snapshots: Sequence[ResearchTeamReviewMemoryQualityRegressionSnapshot],
) -> tuple[ResearchTeamReviewMemoryQualityRegressionSnapshot, ...]:
    normalized: list[ResearchTeamReviewMemoryQualityRegressionSnapshot] = []
    seen_keys: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not ResearchTeamReviewMemoryQualityRegressionSnapshot:
            raise ValueError(
                "snapshots must contain ResearchTeamReviewMemoryQualityRegressionSnapshot",
            )
        snapshot = ResearchTeamReviewMemoryQualityRegressionSnapshot(
            **_public_dataclass_values(
                snapshot,
                ResearchTeamReviewMemoryQualityRegressionSnapshot,
            ),
        )
        if snapshot.team_key in seen_keys:
            raise ValueError("team_key values must be unique")
        seen_keys.add(snapshot.team_key)
        normalized.append(snapshot)
    return tuple(sorted(normalized, key=lambda item: item.team_key))


def _normalize_rows(
    rows: tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...],
) -> tuple[ResearchTeamReviewMemoryQualityRegressionRow, ...]:
    normalized: list[ResearchTeamReviewMemoryQualityRegressionRow] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamReviewMemoryQualityRegressionRow:
            raise ValueError("rows must contain ResearchTeamReviewMemoryQualityRegressionRow")
        row = ResearchTeamReviewMemoryQualityRegressionRow(
            **_public_dataclass_values(
                row,
                ResearchTeamReviewMemoryQualityRegressionRow,
            ),
        )
        if row.team_key in seen_keys:
            raise ValueError("team_key values must be unique")
        seen_keys.add(row.team_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda item: item.team_key))


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamReviewMemoryQualityRegressionReasonCodeCount, ...],
) -> tuple[ResearchTeamReviewMemoryQualityRegressionReasonCodeCount, ...]:
    normalized: list[ResearchTeamReviewMemoryQualityRegressionReasonCodeCount] = []
    seen_reason_codes: set[str] = set()
    for item in counts:
        if type(item) is not ResearchTeamReviewMemoryQualityRegressionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamReviewMemoryQualityRegressionReasonCodeCount",
            )
        item = ResearchTeamReviewMemoryQualityRegressionReasonCodeCount(
            **_public_dataclass_values(
                item,
                ResearchTeamReviewMemoryQualityRegressionReasonCodeCount,
            ),
        )
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reason_codes.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(normalized, key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code)),
    )


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        reason_code = _require_supported_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(
        sorted(normalized, key=lambda reason_code: _REASON_CODE_SEQUENCE.index(reason_code)),
    )


def _require_supported_reason_code(field_name: str, value: str) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _validate_config(config: ResearchTeamReviewMemoryQualityRegressionConfig) -> None:
    if (
        config.max_pass_stale_memory_reuse_rate
        >= config.max_watch_stale_memory_reuse_rate
    ):
        raise ValueError(
            "max_pass_stale_memory_reuse_rate must be less than "
            "max_watch_stale_memory_reuse_rate",
        )
    if (
        config.min_pass_correction_followthrough_score
        <= config.min_watch_correction_followthrough_score
    ):
        raise ValueError(
            "min_pass_correction_followthrough_score must exceed "
            "min_watch_correction_followthrough_score",
        )
    if (
        config.max_pass_calibration_drop_score
        >= config.max_watch_calibration_drop_score
    ):
        raise ValueError(
            "max_pass_calibration_drop_score must be less than "
            "max_watch_calibration_drop_score",
        )
    if (
        config.min_pass_evidence_coverage_score
        <= config.min_watch_evidence_coverage_score
    ):
        raise ValueError(
            "min_pass_evidence_coverage_score must exceed "
            "min_watch_evidence_coverage_score",
        )
    if (
        config.min_pass_contradiction_handling_score
        <= config.min_watch_contradiction_handling_score
    ):
        raise ValueError(
            "min_pass_contradiction_handling_score must exceed "
            "min_watch_contradiction_handling_score",
        )
    if config.max_pass_review_latency_hours >= config.max_watch_review_latency_hours:
        raise ValueError(
            "max_pass_review_latency_hours must be less than "
            "max_watch_review_latency_hours",
        )


def _validate_snapshot(
    snapshot: ResearchTeamReviewMemoryQualityRegressionSnapshot,
) -> None:
    if snapshot.reviewed_item_count <= _ZERO:
        raise ValueError("reviewed_item_count must be positive")
    if snapshot.evidence_required_count <= _ZERO:
        raise ValueError("evidence_required_count must be positive")
    if snapshot.stale_memory_reuse_count > snapshot.reviewed_item_count:
        raise ValueError("stale_memory_reuse_count must not exceed reviewed_item_count")
    if snapshot.correction_completed_count > snapshot.correction_required_count:
        raise ValueError(
            "correction_completed_count must not exceed correction_required_count",
        )
    if snapshot.evidence_confirmed_count > snapshot.evidence_required_count:
        raise ValueError("evidence_confirmed_count must not exceed evidence_required_count")
    if snapshot.contradiction_resolved_count > snapshot.contradiction_flag_count:
        raise ValueError(
            "contradiction_resolved_count must not exceed contradiction_flag_count",
        )


def _validate_row(row: ResearchTeamReviewMemoryQualityRegressionRow) -> None:
    expected_reason = f"review_memory_quality_regression_{row.status}"
    if row.reason_codes[0] != expected_reason:
        raise ValueError(f"{row.status} row reason_codes must start with status reason")
    metric_reason_codes = row.reason_codes[1:]
    if len(metric_reason_codes) != len(_ROW_REASON_CODE_GROUPS):
        raise ValueError("row reason_codes must contain one reason per metric")
    for reason_code, supported_group in zip(
        metric_reason_codes,
        _ROW_REASON_CODE_GROUPS,
        strict=True,
    ):
        if reason_code not in supported_group:
            raise ValueError("row reason_codes must contain one reason per metric")


def _validate_report(report: ResearchTeamReviewMemoryQualityRegressionReport) -> None:
    config = _config_from_report(report)
    rows = report.rows
    for row in rows:
        _validate_row_against_config(row, config)
    if report.team_count != _decimal_count(len(rows)):
        raise ValueError("team_count must match rows")
    expected_block_count = _decimal_count(1) if not rows else _decimal_count(
        _status_count(rows, "block"),
    )
    expected_counts = {
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": expected_block_count,
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_means = {
        "mean_stale_memory_reuse_rate": _mean_row_decimal(
            rows,
            "stale_memory_reuse_rate",
            ratio=True,
        ),
        "mean_correction_followthrough_score": _mean_row_decimal(
            rows,
            "correction_followthrough_score",
            ratio=True,
        ),
        "mean_calibration_drop_score": _mean_row_decimal(
            rows,
            "calibration_drop_score",
            ratio=True,
        ),
        "mean_evidence_coverage_score": _mean_row_decimal(
            rows,
            "evidence_coverage_score",
            ratio=True,
        ),
        "mean_contradiction_handling_score": _mean_row_decimal(
            rows,
            "contradiction_handling_score",
            ratio=True,
        ),
        "mean_review_latency_hours": _mean_row_decimal(
            rows,
            "mean_review_latency_hours",
        ),
        "mean_quality_regression_score": _mean_row_decimal(
            rows,
            "quality_regression_score",
            ratio=True,
        ),
        "max_quality_regression_score": _max_row_decimal(
            rows,
            "quality_regression_score",
            ratio=True,
        ),
    }
    for field_name, expected in expected_means.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_row_against_config(
    row: ResearchTeamReviewMemoryQualityRegressionRow,
    config: ResearchTeamReviewMemoryQualityRegressionConfig,
) -> None:
    expected_score = _quality_regression_score(
        stale_memory_reuse_rate=row.stale_memory_reuse_rate,
        correction_followthrough_score=row.correction_followthrough_score,
        calibration_drop_score=row.calibration_drop_score,
        evidence_coverage_score=row.evidence_coverage_score,
        contradiction_handling_score=row.contradiction_handling_score,
        review_latency_hours=row.mean_review_latency_hours,
        config=config,
    )
    if row.quality_regression_score != expected_score:
        raise ValueError("quality_regression_score must match row metrics")
    expected_status = _row_status(
        stale_memory_reuse_rate=row.stale_memory_reuse_rate,
        correction_followthrough_score=row.correction_followthrough_score,
        calibration_drop_score=row.calibration_drop_score,
        evidence_coverage_score=row.evidence_coverage_score,
        contradiction_handling_score=row.contradiction_handling_score,
        review_latency_hours=row.mean_review_latency_hours,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row metrics")
    expected_reason_codes = _row_reason_codes(
        status=expected_status,
        stale_memory_reuse_rate=row.stale_memory_reuse_rate,
        correction_followthrough_score=row.correction_followthrough_score,
        calibration_drop_score=row.calibration_drop_score,
        evidence_coverage_score=row.evidence_coverage_score,
        contradiction_handling_score=row.contradiction_handling_score,
        review_latency_hours=row.mean_review_latency_hours,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")


def _config_from_report(
    report: ResearchTeamReviewMemoryQualityRegressionReport,
) -> ResearchTeamReviewMemoryQualityRegressionConfig:
    return ResearchTeamReviewMemoryQualityRegressionConfig(
        config_version=report.config_version,
        **{
            field_name: getattr(report, field_name)
            for field_name in _CONFIG_RATIO_FIELDS + _CONFIG_MEASURE_FIELDS
        },
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: str) -> str:
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_value(field_name, value)
    return value


def _require_public_label(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_value(field_name, value)
    return value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return _quantize_decimal(value)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_measure_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_decimal(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        quantized = value.quantize(_QUANT)
    if quantized.is_zero():
        return _ZERO
    return quantized


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchTeamReviewMemoryQualityRegressionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_digest", None)
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return _json_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    values = dict(payload)
    values.pop("public_digest", None)
    return _json_digest(values)


def _json_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    if public_digest != _payload_digest(payload):
        raise ValueError("public_digest must match payload fields")


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON numeric value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize_decimal(value), "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if _contains_unsafe_public_term(key_text):
                raise ValueError(f"unsafe public payload key in {label}: {key_text}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    if _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value for {field_name}")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)
