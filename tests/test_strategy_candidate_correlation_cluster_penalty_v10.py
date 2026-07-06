import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-candidate-correlation-cluster-penalty-test-v0"


def d(value: str) -> Decimal:
    return Decimal(value)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_correlation_cluster_penalty_v10",
    )


def config():
    digest = module()
    return digest.StrategyCandidateCorrelationClusterPenaltyConfig(
        config_version=CONFIG_VERSION,
        resolution_timing_window_hours=d("72"),
        watch_penalty_threshold=d("0.300000"),
        blocked_penalty_threshold=d("0.500000"),
        min_adjusted_score=d("0.250000"),
    )


def candidate(
    candidate_id: str,
    *,
    category: str,
    event_cluster_id: str,
    source_ids: tuple[str, ...],
    resolution_offset_hours: str,
    proposed_notional: str,
    base_score: str,
):
    digest = module()
    return digest.StrategyCandidateCorrelationCandidateInput(
        candidate_id=candidate_id,
        category=category,
        event_cluster_id=event_cluster_id,
        source_ids=source_ids,
        resolution_at=GENERATED_AT + timedelta(hours=int(resolution_offset_hours)),
        proposed_notional=d(proposed_notional),
        base_score=d(base_score),
    )


def position(
    position_id: str,
    *,
    category: str,
    event_cluster_id: str,
    source_ids: tuple[str, ...],
    resolution_offset_hours: str,
    current_notional: str,
):
    digest = module()
    return digest.StrategyCandidateCorrelationPortfolioPosition(
        position_id=position_id,
        category=category,
        event_cluster_id=event_cluster_id,
        source_ids=source_ids,
        resolution_at=GENERATED_AT + timedelta(hours=int(resolution_offset_hours)),
        current_notional=d(current_notional),
    )


def build_report(*candidates, portfolio=()):
    digest = module()
    return digest.build_strategy_candidate_correlation_cluster_penalty_report(
        candidates,
        existing_positions=portfolio,
        config=config(),
        generated_at=GENERATED_AT,
    )


def test_correlation_cluster_penalty_builds_deterministic_readonly_report() -> None:
    portfolio = (
        position(
            "position-politics",
            category="politics",
            event_cluster_id="election-2028",
            source_ids=("polls", "news"),
            resolution_offset_hours="24",
            current_notional="100.000000",
        ),
        position(
            "position-macro",
            category="macro",
            event_cluster_id="fed-2026",
            source_ids=("polls", "rates"),
            resolution_offset_hours="48",
            current_notional="50.000000",
        ),
        position(
            "position-sports",
            category="sports",
            event_cluster_id="nba-finals",
            source_ids=("box-score",),
            resolution_offset_hours="300",
            current_notional="50.000000",
        ),
    )

    report = build_report(
        candidate(
            "candidate-correlated",
            category="politics",
            event_cluster_id="election-2028",
            source_ids=("polls", "forecast"),
            resolution_offset_hours="36",
            proposed_notional="100.000000",
            base_score="0.800000",
        ),
        candidate(
            "candidate-diversified",
            category="sports",
            event_cluster_id="nba-finals-next",
            source_ids=("injury-report",),
            resolution_offset_hours="240",
            proposed_notional="25.000000",
            base_score="0.700000",
        ),
        portfolio=portfolio,
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == d("2")
    assert report.pass_candidate_count == d("1")
    assert report.watch_candidate_count == d("0")
    assert report.blocked_candidate_count == d("1")
    assert report.max_correlation_penalty == d("0.620833")
    assert report.mean_adjusted_score == d("0.362500")
    assert report.status == "blocked"
    assert report.reason_codes == (
        "strategy_candidate_correlation_cluster_penalty_blocked",
        "strategy_candidate_correlation_cluster_penalty_concentration",
        "strategy_candidate_correlation_cluster_penalty_overlap",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-correlated",
        "candidate-diversified",
    )

    correlated = report.rows[0]
    assert correlated.rank == d("1")
    assert correlated.category_overlap_score == d("0.500000")
    assert correlated.event_cluster_overlap_score == d("0.500000")
    assert correlated.shared_source_overlap_score == d("0.750000")
    assert correlated.resolution_timing_overlap_score == d("0.750000")
    assert correlated.portfolio_concentration_score == d("0.666667")
    assert correlated.correlation_penalty == d("0.620833")
    assert correlated.adjusted_score == d("0.179167")
    assert correlated.status == "blocked"
    assert correlated.reason_codes == (
        "candidate_category_overlap",
        "candidate_event_cluster_overlap",
        "candidate_shared_source_overlap",
        "candidate_resolution_timing_overlap",
        "candidate_portfolio_concentration_pressure",
        "candidate_correlation_penalty_blocked",
    )

    diversified = report.rows[1]
    assert diversified.category_overlap_score == d("0.250000")
    assert diversified.event_cluster_overlap_score == d("0.000000")
    assert diversified.shared_source_overlap_score == d("0.000000")
    assert diversified.resolution_timing_overlap_score == d("0.250000")
    assert diversified.portfolio_concentration_score == d("0.333333")
    assert diversified.correlation_penalty == d("0.154167")
    assert diversified.adjusted_score == d("0.545833")
    assert diversified.status == "pass"
    assert diversified.reason_codes == (
        "candidate_category_overlap",
        "candidate_resolution_timing_overlap",
        "candidate_portfolio_concentration_pressure",
        "candidate_correlation_penalty_pass",
    )


def test_empty_portfolio_penalizes_only_new_candidate_concentration() -> None:
    report = build_report(
        candidate(
            "candidate-empty-portfolio",
            category="macro",
            event_cluster_id="fed-2026",
            source_ids=("rates",),
            resolution_offset_hours="120",
            proposed_notional="10.000000",
            base_score="0.600000",
        ),
    )

    row = report.rows[0]
    assert row.category_overlap_score == d("0.000000")
    assert row.event_cluster_overlap_score == d("0.000000")
    assert row.shared_source_overlap_score == d("0.000000")
    assert row.resolution_timing_overlap_score == d("0.000000")
    assert row.portfolio_concentration_score == d("1.000000")
    assert row.correlation_penalty == d("0.200000")
    assert row.adjusted_score == d("0.400000")
    assert row.status == "pass"
    assert report.status == "pass"


def test_public_types_are_frozen_decimal_only_and_revalidate_flags() -> None:
    digest = module()

    assert digest.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_CORRELATION_CLUSTER_PENALTY_CONFIG_VERSION",
        "StrategyCandidateCorrelationCandidateInput",
        "StrategyCandidateCorrelationClusterPenaltyConfig",
        "StrategyCandidateCorrelationClusterPenaltyReport",
        "StrategyCandidateCorrelationPenaltyRow",
        "StrategyCandidateCorrelationPortfolioPosition",
        "build_strategy_candidate_correlation_cluster_penalty_report",
        "strategy_candidate_correlation_cluster_penalty_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            public_numeric_fields = {
                field.name
                for field in fields(value)
                if any(
                    fragment in field.name
                    for fragment in (
                        "count",
                        "hours",
                        "notional",
                        "penalty",
                        "score",
                        "threshold",
                        "weight",
                    )
                )
            }
            for field_name in public_numeric_fields:
                assert value.__annotations__[field_name] is Decimal

    item = candidate(
        "candidate-frozen",
        category="macro",
        event_cluster_id="fed-2026",
        source_ids=("rates",),
        resolution_offset_hours="120",
        proposed_notional="10.000000",
        base_score="0.600000",
    )
    report = build_report(item)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        item.base_score = d("0.1")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="adjusted_score must match"):
        replace(row, adjusted_score=d("0.100000"))


def test_rejects_non_decimal_subclasses_duplicates_and_invalid_temporal_inputs() -> None:
    digest = module()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="base_score must be a Decimal"):
        digest.StrategyCandidateCorrelationCandidateInput(
            candidate_id="candidate-derived",
            category="macro",
            event_cluster_id="fed-2026",
            source_ids=("rates",),
            resolution_at=GENERATED_AT,
            proposed_notional=d("10.000000"),
            base_score=DerivedDecimal("0.600000"),
        )
    with pytest.raises(ValueError, match="proposed_notional must be a Decimal"):
        digest.StrategyCandidateCorrelationCandidateInput(
            candidate_id="candidate-float",
            category="macro",
            event_cluster_id="fed-2026",
            source_ids=("rates",),
            resolution_at=GENERATED_AT,
            proposed_notional=10.0,
            base_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate candidate_id values"):
        build_report(
            candidate(
                "candidate-duplicate",
                category="macro",
                event_cluster_id="fed-2026",
                source_ids=("rates",),
                resolution_offset_hours="120",
                proposed_notional="10.000000",
                base_score="0.600000",
            ),
            candidate(
                "candidate-duplicate",
                category="sports",
                event_cluster_id="nba-finals",
                source_ids=("box-score",),
                resolution_offset_hours="240",
                proposed_notional="5.000000",
                base_score="0.500000",
            ),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_strategy_candidate_correlation_cluster_penalty_report(
            (),
            existing_positions=(),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )


def test_payload_is_json_ready_and_has_no_decimal_or_float_values() -> None:
    digest = module()
    report = build_report(
        candidate(
            "candidate-payload",
            category="macro",
            event_cluster_id="fed-2026",
            source_ids=("rates",),
            resolution_offset_hours="120",
            proposed_notional="10.000000",
            base_score="0.600000",
        ),
    )

    payload = digest.strategy_candidate_correlation_cluster_penalty_payload(report)
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["correlation_penalty"] == "0.200000"
    json.dumps(payload, sort_keys=True)

    def assert_payload_safe(value: object) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                assert_payload_safe(nested)
        elif isinstance(value, list):
            for nested in value:
                assert_payload_safe(nested)
        else:
            assert not isinstance(value, Decimal)
            assert not isinstance(value, float)

    assert_payload_safe(payload)

    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.strategy_candidate_correlation_cluster_penalty_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="must not be a float"):
        digest.strategy_candidate_correlation_cluster_penalty_payload(
            {**payload, "max_correlation_penalty": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        digest.strategy_candidate_correlation_cluster_penalty_payload(
            {**payload, "wallet_address": "0xabc"},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        digest.strategy_candidate_correlation_cluster_penalty_payload(
            {
                **payload,
                "rows": [
                    {
                        **payload["rows"][0],
                        "reason_codes": ["candidate_correlation_penalty_place_order"],
                    },
                ],
            },
        )


def test_module_scope_has_no_live_external_or_persistence_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_correlation_cluster_penalty_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "investment_recommendation",
        "trade_advice",
        "open(",
        ".read",
        ".write",
        "request",
        "http",
        "urllib",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "socket",
        "subprocess",
        "os.environ",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "float",
                    "open",
                    "print",
                    "submit",
                    "sign",
                }
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "fetch",
                    "read",
                    "send",
                    "submit",
                    "write",
                }
