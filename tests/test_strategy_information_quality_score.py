from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict
from decimal import Decimal
import inspect
import json

import pytest

from polymarket_alpha_lab.strategy_information_quality_score import (
    DEFAULT_STRATEGY_INFORMATION_QUALITY_SCORE_CONFIG_VERSION,
    StrategyInformationQualityScoreConfig,
    StrategyInformationQualityScoreInput,
    StrategyInformationQualityScoreResult,
    build_strategy_information_quality_score,
    strategy_information_quality_score_payload,
)


def _input(
    *,
    source_count: str = "4",
    freshness_minutes: str = "12",
    source_reliability_score: str = "0.920000",
    source_diversity_score: str = "0.810000",
    evidence_conflict_score: str = "0.040000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyInformationQualityScoreInput:
    return StrategyInformationQualityScoreInput(
        source_count=Decimal(source_count),
        freshness_minutes=Decimal(freshness_minutes),
        source_reliability_score=Decimal(source_reliability_score),
        source_diversity_score=Decimal(source_diversity_score),
        evidence_conflict_score=Decimal(evidence_conflict_score),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_pass_state_uses_decimal_components_reason_and_flags() -> None:
    result = build_strategy_information_quality_score(
        _input(),
        config=StrategyInformationQualityScoreConfig(),
    )

    assert result.information_quality_status == "pass"
    assert result.reason_codes == ("information_quality_ready",)
    assert result.information_quality_score == Decimal("0.938000")
    assert result.component_scores == (
        ("evidence_conflict_score", Decimal("0.960000")),
        ("freshness_minutes", Decimal("1.000000")),
        ("source_count", Decimal("1.000000")),
        ("source_diversity_score", Decimal("0.810000")),
        ("source_reliability_score", Decimal("0.920000")),
    )
    assert result.source_count == Decimal("4.000000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_watch_state_collects_deterministic_reason_codes() -> None:
    result = build_strategy_information_quality_score(
        _input(
            source_count="2",
            freshness_minutes="45",
            source_reliability_score="0.750000",
            source_diversity_score="0.500000",
            evidence_conflict_score="0.200000",
        ),
        config=StrategyInformationQualityScoreConfig(),
    )

    assert result.information_quality_status == "watch"
    assert result.reason_codes == (
        "evidence_conflict_watch",
        "low_source_count_watch",
        "low_source_diversity_watch",
        "low_source_reliability_watch",
        "stale_evidence_watch",
    )


def test_blocked_state_dominates_watch_conditions() -> None:
    result = build_strategy_information_quality_score(
        _input(
            source_count="1",
            freshness_minutes="120",
            source_reliability_score="0.400000",
            source_diversity_score="0.200000",
            evidence_conflict_score="0.500000",
        ),
        config=StrategyInformationQualityScoreConfig(),
    )

    assert result.information_quality_status == "blocked"
    assert result.reason_codes == (
        "evidence_conflict_blocked",
        "insufficient_source_count",
        "low_source_diversity_blocked",
        "low_source_reliability_blocked",
        "stale_evidence_blocked",
    )
    assert result.information_quality_score == Decimal("0.320000")


def test_config_validates_threshold_order_and_exact_type() -> None:
    with pytest.raises(ValueError, match="min_watch_source_count"):
        StrategyInformationQualityScoreConfig(
            min_watch_source_count=Decimal("4"),
            min_pass_source_count=Decimal("3"),
        )

    with pytest.raises(ValueError, match="max_pass_freshness_minutes"):
        StrategyInformationQualityScoreConfig(
            max_pass_freshness_minutes=Decimal("120"),
            max_watch_freshness_minutes=Decimal("90"),
        )

    with pytest.raises(TypeError):
        class BadConfig(StrategyInformationQualityScoreConfig):
            pass


def test_validation_rejects_float_collections_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="float"):
        StrategyInformationQualityScoreInput(
            source_count=Decimal("3"),
            freshness_minutes=0.1,
            source_reliability_score=Decimal("0.900000"),
            source_diversity_score=Decimal("0.800000"),
            evidence_conflict_score=Decimal("0.050000"),
        )

    with pytest.raises(ValueError, match="source_count must be integral"):
        _input(source_count="2.5")

    with pytest.raises(ValueError, match="paper_only"):
        build_strategy_information_quality_score(
            _input(paper_only=False),
            config=StrategyInformationQualityScoreConfig(),
        )

    result = build_strategy_information_quality_score(
        _input(),
        config=StrategyInformationQualityScoreConfig(),
    )
    with pytest.raises(ValueError, match="component_scores must be a tuple"):
        StrategyInformationQualityScoreResult(
            source_count=result.source_count,
            freshness_minutes=result.freshness_minutes,
            source_reliability_score=result.source_reliability_score,
            source_diversity_score=result.source_diversity_score,
            evidence_conflict_score=result.evidence_conflict_score,
            component_scores=list(result.component_scores),  # type: ignore[arg-type]
            information_quality_score=result.information_quality_score,
            information_quality_status=result.information_quality_status,
            reason_codes=result.reason_codes,
        )


def test_payload_helper_emits_decimal_strings_and_no_floats() -> None:
    result = build_strategy_information_quality_score(
        _input(),
        config=StrategyInformationQualityScoreConfig(),
    )

    payload = strategy_information_quality_score_payload(result)
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["source_count"] == "4.000000"
    assert payload["information_quality_score"] == "0.938000"
    assert payload["component_scores"][0][1] == "0.960000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert "0.938000" in rendered


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    config = StrategyInformationQualityScoreConfig()
    result = build_strategy_information_quality_score(_input(), config=config)

    with pytest.raises(FrozenInstanceError):
        result.information_quality_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="result"):
        StrategyInformationQualityScoreResult(
            source_count=result.source_count,
            freshness_minutes=result.freshness_minutes,
            source_reliability_score=result.source_reliability_score,
            source_diversity_score=result.source_diversity_score,
            evidence_conflict_score=result.evidence_conflict_score,
            component_scores=result.component_scores,
            information_quality_score=result.information_quality_score,
            information_quality_status="pass",
            reason_codes=("information_quality_ready",),
            readonly=False,
        )

    assert asdict(config)["config_version"] == (
        DEFAULT_STRATEGY_INFORMATION_QUALITY_SCORE_CONFIG_VERSION
    )
    for name, value in asdict(result).items():
        if _field_name_is_numeric(name):
            assert type(value) is Decimal, name


def test_static_forbidden_surface_terms_are_absent() -> None:
    import polymarket_alpha_lab.strategy_information_quality_score as module

    public_text = " ".join(
        name
        for name, value in inspect.getmembers(module)
        if not name.startswith("_") and getattr(value, "__module__", module.__name__) == module.__name__
    ).lower()
    source = inspect.getsource(module).lower()

    forbidden_name_fragments = (
        "broker",
        "db",
        "file",
        "network",
        "order",
        "sign",
        "trade",
        "wallet",
    )
    for fragment in forbidden_name_fragments:
        assert fragment not in public_text

    forbidden_source_terms = (
        "requests",
        "httpx",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "socket",
        "subprocess",
        "open(",
        "wallet",
        "broker",
        "signing",
    )
    for term in forbidden_source_terms:
        assert term not in source


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(child for item in value.values() for child in _walk_values(item))
    if isinstance(value, (list, tuple)):
        return tuple(child for item in value for child in _walk_values(item))
    return (value,)


def _field_name_is_numeric(name: str) -> bool:
    numeric_fragments = (
        "conflict",
        "count",
        "diversity",
        "freshness",
        "minutes",
        "quality_score",
        "reliability",
        "score",
    )
    return (
        name not in {"component_scores"}
        and not name.endswith("status")
        and any(fragment in name for fragment in numeric_fragments)
    )
