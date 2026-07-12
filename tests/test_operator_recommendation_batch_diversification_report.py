from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.operator_recommendation_batch_diversification_report import (
    OperatorRecommendationBatchDiversificationInput,
    OperatorRecommendationBatchDiversificationReport,
    build_operator_recommendation_batch_diversification_report,
    operator_recommendation_batch_diversification_report_digest,
    operator_recommendation_batch_diversification_report_payload,
)


def test_builds_diversified_readonly_report_payload_and_digest() -> None:
    report = build_operator_recommendation_batch_diversification_report(
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("9"),
            category_count=Decimal("4"),
            dominant_category_count=Decimal("3"),
            correlated_cluster_count=Decimal("2"),
            minimum_category_count=Decimal("3"),
        ),
    )

    assert report.diversification_status == "diversified"
    assert report.reason_codes == ("operator_recommendation_batch_diversified",)
    assert report.manual_next_step == "manual_review_batch_diversification"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.category_ratio == Decimal("0.444444")
    assert report.dominant_category_ratio == Decimal("0.333333")

    payload = report.public_payload
    assert payload == {
        "config_version": "operator_recommendation_batch_diversification_report.v1",
        "diversification_status": "diversified",
        "reason_codes": ("operator_recommendation_batch_diversified",),
        "manual_next_step": "manual_review_batch_diversification",
        "recommendation_count": "9.000000",
        "category_count": "4.000000",
        "dominant_category_count": "3.000000",
        "correlated_cluster_count": "2.000000",
        "minimum_category_count": "3.000000",
        "category_ratio": "0.444444",
        "dominant_category_ratio": "0.333333",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }
    assert payload["payload_digest"] == report.payload_digest
    assert (
        operator_recommendation_batch_diversification_report_payload(report) == payload
    )
    assert (
        operator_recommendation_batch_diversification_report_digest(report)
        == report.payload_digest
    )

    with pytest.raises(TypeError):
        payload["diversification_status"] = "mutated"


def test_reports_attention_when_minimum_category_count_is_not_met() -> None:
    report = build_operator_recommendation_batch_diversification_report(
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("8"),
            category_count=Decimal("2"),
            dominant_category_count=Decimal("4"),
            correlated_cluster_count=Decimal("2"),
            minimum_category_count=Decimal("3"),
        ),
    )

    assert report.diversification_status == "attention"
    assert report.reason_codes == (
        "minimum_category_count_not_met",
        "dominant_category_concentration_watch",
    )
    assert report.manual_next_step == "manual_add_independent_category_review"


def test_reports_blocked_for_empty_or_single_category_batches() -> None:
    empty_report = build_operator_recommendation_batch_diversification_report(
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("0"),
            category_count=Decimal("0"),
            dominant_category_count=Decimal("0"),
            correlated_cluster_count=Decimal("0"),
            minimum_category_count=Decimal("3"),
        ),
    )
    single_category_report = build_operator_recommendation_batch_diversification_report(
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("5"),
            category_count=Decimal("1"),
            dominant_category_count=Decimal("5"),
            correlated_cluster_count=Decimal("1"),
            minimum_category_count=Decimal("3"),
        ),
    )

    assert empty_report.diversification_status == "blocked"
    assert empty_report.reason_codes == ("recommendation_batch_empty",)
    assert empty_report.manual_next_step == "manual_add_recommendations_before_review"
    assert single_category_report.diversification_status == "blocked"
    assert single_category_report.reason_codes == (
        "single_category_recommendation_batch",
        "minimum_category_count_not_met",
        "dominant_category_concentration_blocker",
    )
    assert (
        single_category_report.manual_next_step
        == "manual_split_batch_or_add_uncorrelated_categories"
    )


def test_report_rejects_inconsistent_counts_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="category_count must not exceed recommendation_count"):
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("2"),
            category_count=Decimal("3"),
            dominant_category_count=Decimal("1"),
            correlated_cluster_count=Decimal("1"),
            minimum_category_count=Decimal("2"),
        )

    with pytest.raises(ValueError, match="dominant_category_count must not exceed"):
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("2"),
            category_count=Decimal("2"),
            dominant_category_count=Decimal("3"),
            correlated_cluster_count=Decimal("1"),
            minimum_category_count=Decimal("2"),
        )

    report = build_operator_recommendation_batch_diversification_report(
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("6"),
            category_count=Decimal("3"),
            dominant_category_count=Decimal("2"),
            correlated_cluster_count=Decimal("2"),
            minimum_category_count=Decimal("2"),
        ),
    )
    with pytest.raises(ValueError, match="payload_digest must match public payload"):
        OperatorRecommendationBatchDiversificationReport(
            config_version=report.config_version,
            diversification_status=report.diversification_status,
            reason_codes=report.reason_codes,
            manual_next_step=report.manual_next_step,
            recommendation_count=report.recommendation_count,
            category_count=report.category_count,
            dominant_category_count=report.dominant_category_count,
            correlated_cluster_count=report.correlated_cluster_count,
            minimum_category_count=report.minimum_category_count,
            category_ratio=report.category_ratio,
            dominant_category_ratio=report.dominant_category_ratio,
            payload_digest="0" * 64,
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    inputs = OperatorRecommendationBatchDiversificationInput(
        recommendation_count=Decimal("4"),
        category_count=Decimal("2"),
        dominant_category_count=Decimal("2"),
        correlated_cluster_count=Decimal("1"),
        minimum_category_count=Decimal("2"),
    )
    report = build_operator_recommendation_batch_diversification_report(inputs)

    with pytest.raises(FrozenInstanceError):
        inputs.recommendation_count = Decimal("5")
    with pytest.raises(FrozenInstanceError):
        report.diversification_status = "blocked"

    with pytest.raises(ValueError, match="recommendation_count must be Decimal"):
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=4,
            category_count=Decimal("2"),
            dominant_category_count=Decimal("2"),
            correlated_cluster_count=Decimal("1"),
            minimum_category_count=Decimal("2"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("4"),
            category_count=Decimal("2"),
            dominant_category_count=Decimal("2"),
            correlated_cluster_count=Decimal("1"),
            minimum_category_count=Decimal("2"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        OperatorRecommendationBatchDiversificationReport(
            config_version=report.config_version,
            diversification_status=report.diversification_status,
            reason_codes=report.reason_codes,
            manual_next_step=report.manual_next_step,
            recommendation_count=report.recommendation_count,
            category_count=report.category_count,
            dominant_category_count=report.dominant_category_count,
            correlated_cluster_count=report.correlated_cluster_count,
            minimum_category_count=report.minimum_category_count,
            category_ratio=report.category_ratio,
            dominant_category_ratio=report.dominant_category_ratio,
            payload_digest=report.payload_digest,
            readonly=False,
        )


def test_public_payload_rejects_execution_auth_wallet_key_and_persistence_surfaces() -> None:
    report = build_operator_recommendation_batch_diversification_report(
        OperatorRecommendationBatchDiversificationInput(
            recommendation_count=Decimal("5"),
            category_count=Decimal("3"),
            dominant_category_count=Decimal("2"),
            correlated_cluster_count=Decimal("1"),
            minimum_category_count=Decimal("2"),
        ),
    )

    for unsafe_key in (
        "live",
        "auth",
        "wallet",
        "private_key",
        "signature",
        "signed_order",
        "auto_execute",
        "execution_path",
        "jsonl_path",
        "file_persistence",
    ):
        payload = dict(report.public_payload)
        payload[unsafe_key] = True
        with pytest.raises(ValueError, match="unsafe public payload"):
            operator_recommendation_batch_diversification_report_payload(payload)
