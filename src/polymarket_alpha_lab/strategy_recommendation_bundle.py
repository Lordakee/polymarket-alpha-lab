"""Paper-only strategy recommendation bundle reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
    PaperStrategySelectionPolicyReport,
    build_paper_strategy_selection_policy_report,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
    PaperStrategyCandidateRecommendationReport,
    build_paper_strategy_candidate_recommendation_report,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
    build_paper_strategy_recommendation_explanation_report,
)


__all__ = (
    "PaperStrategyRecommendationBundleConfig",
    "PaperStrategyRecommendationBundleReport",
    "build_paper_strategy_recommendation_bundle_report",
)


ZERO = Decimal("0")


@dataclass(frozen=True)
class PaperStrategyRecommendationBundleConfig:
    config_version: str
    recommendation_config: PaperStrategyCandidateRecommendationConfig
    selection_policy_config: PaperStrategySelectionPolicyConfig

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            type(self.recommendation_config)
            is not PaperStrategyCandidateRecommendationConfig
        ):
            raise ValueError(
                "recommendation_config must be a "
                "PaperStrategyCandidateRecommendationConfig",
            )
        if type(self.selection_policy_config) is not PaperStrategySelectionPolicyConfig:
            raise ValueError(
                "selection_policy_config must be a PaperStrategySelectionPolicyConfig",
            )


@dataclass(frozen=True)
class PaperStrategyRecommendationBundleReport:
    generated_at: datetime
    config_version: str
    candidate_count: int
    recommend_count: int
    selected_count: int
    total_selected_notional: Decimal
    recommendation_report: PaperStrategyCandidateRecommendationReport
    selection_policy_report: PaperStrategySelectionPolicyReport
    explanation_report: PaperStrategyRecommendationExplanationReport
    skipped_count: int | None = None
    not_selected_count: int | None = None
    total_suggested_notional: Decimal | None = None
    skipped_suggested_notional: Decimal | None = None
    remaining_total_notional: Decimal | None = None
    primary_reason_code_counts: tuple[tuple[str, int], ...] | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("candidate_count", self.candidate_count)
        _require_nonnegative_int("recommend_count", self.recommend_count)
        _require_nonnegative_int("selected_count", self.selected_count)
        _require_nonnegative_decimal(
            "total_selected_notional",
            self.total_selected_notional,
        )
        _validate_nested_report(
            "recommendation_report",
            self.recommendation_report,
            PaperStrategyCandidateRecommendationReport,
        )
        _validate_nested_report(
            "selection_policy_report",
            self.selection_policy_report,
            PaperStrategySelectionPolicyReport,
        )
        _validate_nested_report(
            "explanation_report",
            self.explanation_report,
            PaperStrategyRecommendationExplanationReport,
        )
        _normalize_summary_fields(self)
        _validate_report_consistency(self)
        _normalize_primary_reason_code_counts_field(self)
        _validate_hard_flags("bundle_report", self)


def build_paper_strategy_recommendation_bundle_report(
    assessment_report: object,
    readiness_report: object,
    *,
    config: PaperStrategyRecommendationBundleConfig,
    generated_at: datetime,
) -> PaperStrategyRecommendationBundleReport:
    """Bundle paper recommendation, selection, and explanation reports."""

    if type(config) is not PaperStrategyRecommendationBundleConfig:
        raise ValueError("config must be a PaperStrategyRecommendationBundleConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    recommendation_report = build_paper_strategy_candidate_recommendation_report(
        assessment_report,
        readiness_report,
        config=config.recommendation_config,
        generated_at=generated_at,
    )
    selection_policy_report = build_paper_strategy_selection_policy_report(
        recommendation_report,
        config=config.selection_policy_config,
        generated_at=generated_at,
    )
    explanation_report = build_paper_strategy_recommendation_explanation_report(
        recommendation_report,
        generated_at=generated_at,
    )

    return PaperStrategyRecommendationBundleReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=recommendation_report.candidate_count,
        recommend_count=recommendation_report.recommend_count,
        selected_count=selection_policy_report.selected_count,
        total_selected_notional=selection_policy_report.total_selected_notional,
        recommendation_report=recommendation_report,
        selection_policy_report=selection_policy_report,
        explanation_report=explanation_report,
        skipped_count=_summary_int(
            selection_policy_report,
            "skipped_count",
            _decision_count(selection_policy_report.selection_rows, "skipped"),
        ),
        not_selected_count=_summary_int(
            selection_policy_report,
            "not_selected_count",
            _decision_count(selection_policy_report.selection_rows, "not_selected"),
        ),
        total_suggested_notional=_summary_notional(
            selection_policy_report,
            "total_suggested_notional",
            _total_suggested_notional(selection_policy_report.selection_rows),
        ),
        skipped_suggested_notional=_summary_notional(
            selection_policy_report,
            "skipped_suggested_notional",
            _skipped_suggested_notional(selection_policy_report.selection_rows),
        ),
        remaining_total_notional=_optional_summary_notional(
            selection_policy_report,
            "remaining_total_notional",
        ),
        primary_reason_code_counts=_summary_primary_reason_code_counts(
            explanation_report,
        ),
    )


def _normalize_summary_fields(report: PaperStrategyRecommendationBundleReport) -> None:
    selection_rows = report.selection_policy_report.selection_rows
    object.__setattr__(
        report,
        "skipped_count",
        _normalize_report_int(
            "skipped_count",
            report.skipped_count,
            _summary_int(
                report.selection_policy_report,
                "skipped_count",
                _decision_count(selection_rows, "skipped"),
            ),
        ),
    )
    object.__setattr__(
        report,
        "not_selected_count",
        _normalize_report_int(
            "not_selected_count",
            report.not_selected_count,
            _summary_int(
                report.selection_policy_report,
                "not_selected_count",
                _decision_count(selection_rows, "not_selected"),
            ),
        ),
    )
    object.__setattr__(
        report,
        "total_suggested_notional",
        _normalize_report_notional(
            "total_suggested_notional",
            report.total_suggested_notional,
            _summary_notional(
                report.selection_policy_report,
                "total_suggested_notional",
                _total_suggested_notional(selection_rows),
            ),
        ),
    )
    object.__setattr__(
        report,
        "skipped_suggested_notional",
        _normalize_report_notional(
            "skipped_suggested_notional",
            report.skipped_suggested_notional,
            _summary_notional(
                report.selection_policy_report,
                "skipped_suggested_notional",
                _skipped_suggested_notional(selection_rows),
            ),
        ),
    )
    object.__setattr__(
        report,
        "remaining_total_notional",
        _normalize_optional_report_notional(
            "remaining_total_notional",
            report.remaining_total_notional,
            _optional_summary_notional(
                report.selection_policy_report,
                "remaining_total_notional",
            ),
        ),
    )


def _normalize_primary_reason_code_counts_field(
    report: PaperStrategyRecommendationBundleReport,
) -> None:
    explanation_rows = report.explanation_report.explanation_rows
    object.__setattr__(
        report,
        "primary_reason_code_counts",
        _normalize_primary_reason_code_counts(
            report.primary_reason_code_counts,
            _summary_primary_reason_code_counts(report.explanation_report),
            explanation_rows,
        ),
    )


def _validate_report_consistency(
    report: PaperStrategyRecommendationBundleReport,
) -> None:
    recommendation_report = report.recommendation_report
    selection_policy_report = report.selection_policy_report
    explanation_report = report.explanation_report

    if recommendation_report.generated_at != report.generated_at:
        raise ValueError("recommendation_report generated_at must match bundle")
    if selection_policy_report.generated_at != report.generated_at:
        raise ValueError("selection_policy_report generated_at must match bundle")
    if explanation_report.generated_at != report.generated_at:
        raise ValueError("explanation_report generated_at must match bundle")

    if report.candidate_count != recommendation_report.candidate_count:
        raise ValueError("candidate_count must match recommendation_report")
    if report.candidate_count != selection_policy_report.row_count:
        raise ValueError("candidate_count must match selection_policy_report")
    if report.candidate_count != explanation_report.recommendation_count:
        raise ValueError("candidate_count must match explanation_report")

    if report.recommend_count != recommendation_report.recommend_count:
        raise ValueError("recommend_count must match recommendation_report")
    if report.recommend_count != explanation_report.recommend_count:
        raise ValueError("recommend_count must match explanation_report")
    if recommendation_report.watch_count != explanation_report.watch_count:
        raise ValueError("watch_count must match explanation_report")
    if recommendation_report.reject_count != explanation_report.reject_count:
        raise ValueError("reject_count must match explanation_report")

    if report.selected_count != selection_policy_report.selected_count:
        raise ValueError("selected_count must match selection_policy_report")
    if report.skipped_count != _summary_int(
        selection_policy_report,
        "skipped_count",
        _decision_count(selection_policy_report.selection_rows, "skipped"),
    ):
        raise ValueError("skipped_count must match selection_policy_report")
    if report.not_selected_count != _summary_int(
        selection_policy_report,
        "not_selected_count",
        _decision_count(selection_policy_report.selection_rows, "not_selected"),
    ):
        raise ValueError("not_selected_count must match selection_policy_report")
    if report.total_selected_notional != selection_policy_report.total_selected_notional:
        raise ValueError(
            "total_selected_notional must match selection_policy_report",
        )
    if report.total_suggested_notional != _summary_notional(
        selection_policy_report,
        "total_suggested_notional",
        _total_suggested_notional(selection_policy_report.selection_rows),
    ):
        raise ValueError("total_suggested_notional must match selection_policy_report")
    if report.skipped_suggested_notional != _summary_notional(
        selection_policy_report,
        "skipped_suggested_notional",
        _skipped_suggested_notional(selection_policy_report.selection_rows),
    ):
        raise ValueError("skipped_suggested_notional must match selection_policy_report")
    if report.remaining_total_notional != _optional_summary_notional(
        selection_policy_report,
        "remaining_total_notional",
    ):
        raise ValueError("remaining_total_notional must match selection_policy_report")
    if explanation_report.source_config_version != recommendation_report.config_version:
        raise ValueError(
            "explanation_report source_config_version must match "
            "recommendation_report config_version",
        )
    _validate_selection_rows_match_recommendations(report)
    _validate_explanation_rows_match_recommendations(report)


def _validate_selection_rows_match_recommendations(
    report: PaperStrategyRecommendationBundleReport,
) -> None:
    recommendation_rows = report.recommendation_report.recommendation_rows
    selection_rows = report.selection_policy_report.selection_rows
    if len(selection_rows) != len(recommendation_rows):
        raise ValueError("selection_policy_report rows must match recommendation rows")
    for recommendation_row, selection_row in zip(
        recommendation_rows,
        selection_rows,
        strict=True,
    ):
        if (
            selection_row.market_slug != recommendation_row.market_slug
            or selection_row.question != recommendation_row.question
            or selection_row.source_action != recommendation_row.action
            or selection_row.selected_side != recommendation_row.selected_side
            or selection_row.recommendation_score
            != recommendation_row.recommendation_score
        ):
            raise ValueError(
                "selection_policy_report rows must match recommendation rows",
            )


def _validate_explanation_rows_match_recommendations(
    report: PaperStrategyRecommendationBundleReport,
) -> None:
    recommendation_rows = report.recommendation_report.recommendation_rows
    explanation_rows = report.explanation_report.explanation_rows
    if len(explanation_rows) != len(recommendation_rows):
        raise ValueError("explanation_report rows must match recommendation rows")
    for recommendation_row, explanation_row in zip(
        recommendation_rows,
        explanation_rows,
        strict=True,
    ):
        if (
            explanation_row.market_slug != recommendation_row.market_slug
            or explanation_row.action != recommendation_row.action
            or explanation_row.selected_side != recommendation_row.selected_side
            or explanation_row.recommendation_score
            != recommendation_row.recommendation_score
            or explanation_row.reason_codes != recommendation_row.reason_codes
        ):
            raise ValueError(
                "explanation_report rows must match recommendation rows",
            )


def _validate_nested_report(
    field_name: str,
    report: Any,
    expected_type: type[Any],
) -> None:
    if type(report) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _validate_hard_flags(field_name, report)


def _validate_hard_flags(field_name: str, report: Any) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(report, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _normalize_report_int(
    field_name: str,
    value: int | None,
    expected: int,
) -> int:
    if value is None:
        return expected
    _require_nonnegative_int(field_name, value)
    if value != expected:
        raise ValueError(f"{field_name} must match nested reports")
    return value


def _normalize_report_notional(
    field_name: str,
    value: Decimal | None,
    expected: Decimal,
) -> Decimal:
    if value is None:
        return expected
    _require_nonnegative_decimal(field_name, value)
    if value != expected:
        raise ValueError(f"{field_name} must match nested reports")
    return value


def _normalize_optional_report_notional(
    field_name: str,
    value: Decimal | None,
    expected: Decimal | None,
) -> Decimal | None:
    if expected is None:
        if value is not None:
            _require_nonnegative_decimal(field_name, value)
            raise ValueError(f"{field_name} must match nested reports")
        return None
    return _normalize_report_notional(field_name, value, expected)


def _normalize_primary_reason_code_counts(
    value: tuple[tuple[str, int], ...] | None,
    expected: tuple[tuple[str, int], ...],
    rows: tuple[Any, ...],
) -> tuple[tuple[str, int], ...]:
    if value is None:
        return expected
    counts = _normalize_reason_code_counts("primary_reason_code_counts", value)
    if counts != expected:
        raise ValueError("primary_reason_code_counts must match nested reports")
    row_derived = _primary_reason_code_counts_from_rows(rows)
    if counts != row_derived:
        raise ValueError("primary_reason_code_counts must match explanation rows")
    return counts


def _summary_int(report: object, field_name: str, fallback: int) -> int:
    value = getattr(report, field_name, None)
    if value is None:
        return fallback
    _require_nonnegative_int(field_name, value)
    if value != fallback:
        raise ValueError(f"{field_name} must match rows")
    return value


def _summary_notional(
    report: object,
    field_name: str,
    fallback: Decimal,
) -> Decimal:
    value = getattr(report, field_name, None)
    if value is None:
        return fallback
    _require_nonnegative_decimal(field_name, value)
    if value != fallback:
        raise ValueError(f"{field_name} must match rows")
    return value


def _optional_summary_notional(report: object, field_name: str) -> Decimal | None:
    value = getattr(report, field_name, None)
    if value is None:
        return None
    _require_nonnegative_decimal(field_name, value)
    return value


def _summary_primary_reason_code_counts(
    report: object,
) -> tuple[tuple[str, int], ...]:
    rows = tuple(getattr(report, "explanation_rows", ()))
    row_counts = _primary_reason_code_counts_from_rows(rows)
    value = getattr(report, "primary_reason_code_counts", None)
    if value is None:
        return row_counts
    counts = _normalize_reason_code_counts("primary_reason_code_counts", value)
    if counts != row_counts:
        raise ValueError("primary_reason_code_counts must match explanation rows")
    return counts


def _decision_count(rows: tuple[Any, ...], decision: str) -> int:
    return sum(1 for row in rows if row.decision == decision)


def _total_suggested_notional(rows: tuple[Any, ...]) -> Decimal:
    return sum(
        (
            row.suggested_position_notional
            for row in rows
            if row.source_action == "recommend"
        ),
        ZERO,
    )


def _skipped_suggested_notional(rows: tuple[Any, ...]) -> Decimal:
    return sum(
        (
            row.suggested_position_notional
            for row in rows
            if row.decision == "skipped"
        ),
        ZERO,
    )


def _primary_reason_code_counts_from_rows(rows: tuple[Any, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        reason_code = getattr(row, "primary_reason_code")
        _require_canonical_string("primary_reason_code", reason_code)
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _normalize_reason_code_counts(
    field_name: str,
    value: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in counts:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError(f"{field_name} entries must be (reason_code, count) pairs")
        reason_code, count = item
        _require_canonical_string(f"{field_name} reason_code", reason_code)
        _require_nonnegative_int(f"{field_name} count", count)
    return counts


def _as_utc(value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
