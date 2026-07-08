from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_candidate_disagreement_resolution_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_candidate_disagreement_resolution_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def cfg(**overrides: object) -> object:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_DISAGREEMENT_RESOLUTION_CONFIG_VERSION
        ),
        "watch_unresolved_disagreement_score": d("0.350000"),
        "block_unresolved_disagreement_score": d("0.700000"),
        "watch_view_disagreement": d("0.350000"),
        "block_view_disagreement": d("0.700000"),
        "model_signal_weight": d("0.200000"),
        "specialist_memory_weight": d("0.200000"),
        "consensus_weight": d("0.200000"),
        "mechanics_weight": d("0.200000"),
        "resolution_risk_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateDisagreementResolutionConfig(**values)


def item(candidate_id: str = "candidate-alpha", **overrides: object) -> object:
    module = api()
    values = {
        "candidate_id": candidate_id,
        "model_signal_disagreement": d("0.100000"),
        "specialist_memory_disagreement": d("0.050000"),
        "consensus_disagreement": d("0.150000"),
        "mechanics_disagreement": d("0.100000"),
        "resolution_risk_disagreement": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateDisagreementResolutionInput(**values)


def report(
    *items: object,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return api().build_research_strategy_candidate_disagreement_resolution_report(
        items,
        config=config or cfg(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item_value in value.values():
            nested.extend(walk_values(item_value))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item_value in value:
            nested.extend(walk_values(item_value))
        return tuple(nested)
    return (value,)


def test_builds_candidate_disagreement_resolution_report_for_analyst_review() -> None:
    module = api()
    built = report(
        item(
            "raw-candidate-alpha-market-id-slug-question-source-url",
            model_signal_disagreement=d("0.850000"),
            specialist_memory_disagreement=d("0.750000"),
            consensus_disagreement=d("0.800000"),
            mechanics_disagreement=d("0.650000"),
            resolution_risk_disagreement=d("0.900000"),
        ),
        item(
            "candidate-watch",
            model_signal_disagreement=d("0.200000"),
            specialist_memory_disagreement=d("0.400000"),
            consensus_disagreement=d("0.300000"),
            mechanics_disagreement=d("0.500000"),
            resolution_risk_disagreement=d("0.100000"),
        ),
        item(
            "candidate-pass",
            model_signal_disagreement=d("0.100000"),
            specialist_memory_disagreement=d("0.050000"),
            consensus_disagreement=d("0.150000"),
            mechanics_disagreement=d("0.100000"),
            resolution_risk_disagreement=d("0.100000"),
        ),
    )

    assert type(built) is module.ResearchStrategyCandidateDisagreementResolutionReport
    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_DISAGREEMENT_RESOLUTION_CONFIG_VERSION
    )
    assert built.status == "block"
    assert built.candidate_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_unresolved_disagreement_score == d("0.396667")
    assert built.max_unresolved_disagreement_score == d("0.790000")
    assert built.max_model_signal_disagreement == d("0.850000")
    assert built.max_specialist_memory_disagreement == d("0.750000")
    assert built.max_consensus_disagreement == d("0.800000")
    assert built.max_mechanics_disagreement == d("0.650000")
    assert built.max_resolution_risk_disagreement == d("0.900000")
    assert built.reason_codes == (
        "model_signal_disagreement_block",
        "specialist_memory_disagreement_block",
        "consensus_disagreement_block",
        "mechanics_disagreement_watch",
        "resolution_risk_disagreement_block",
        "unresolved_disagreement_score_block",
        "specialist_memory_disagreement_watch",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    blocked, watched, passed = built.rows
    assert blocked.candidate_digest.startswith("sha256:")
    assert "raw-candidate-alpha" not in blocked.candidate_digest
    assert blocked.unresolved_disagreement_score == d("0.790000")
    assert blocked.dominant_disagreement_view == "resolution_risk"
    assert blocked.reason_codes == (
        "model_signal_disagreement_block",
        "specialist_memory_disagreement_block",
        "consensus_disagreement_block",
        "mechanics_disagreement_watch",
        "resolution_risk_disagreement_block",
        "unresolved_disagreement_score_block",
    )

    assert watched.status == "watch"
    assert watched.unresolved_disagreement_score == d("0.300000")
    assert watched.dominant_disagreement_view == "mechanics"
    assert watched.reason_codes == (
        "specialist_memory_disagreement_watch",
        "mechanics_disagreement_watch",
    )

    assert passed.status == "pass"
    assert passed.unresolved_disagreement_score == d("0.100000")
    assert passed.dominant_disagreement_view == "consensus"
    assert passed.reason_codes == ("candidate_disagreement_resolution_pass",)


def test_payload_is_deterministic_redacted_decimal_only_and_digest_validated() -> None:
    module = api()
    built = report(
        item("candidate://market-123/slug/question?source=https://example.invalid"),
        item(
            "candidate-beta",
            model_signal_disagreement=d("0.200000"),
            specialist_memory_disagreement=d("0.400000"),
            consensus_disagreement=d("0.300000"),
            mechanics_disagreement=d("0.500000"),
            resolution_risk_disagreement=d("0.100000"),
        ),
    )

    payload = module.research_strategy_candidate_disagreement_resolution_report_payload(
        built,
    )
    payload_again = module.research_strategy_candidate_disagreement_resolution_report_payload(
        built,
    )

    assert payload == payload_again
    assert payload == built.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "2.000000"
    assert payload["rows"][0]["candidate_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64

    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()
    assert "candidate://market-123" not in encoded
    assert "candidate-beta" not in encoded
    for forbidden in (
        "market-123",
        "slug",
        "question",
        "https://",
        "example.invalid",
        "postgres://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
    ):
        assert forbidden not in rendered
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_candidate_disagreement_resolution_report_payload(
            tampered,
        )

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_candidate_disagreement_resolution_report_payload(
            downgraded,
        )

    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.invalid/private"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_candidate_disagreement_resolution_report_payload(
            unsafe,
        )


def test_empty_input_is_pass_report_only_without_decision_surfaces() -> None:
    module = api()
    empty = report()
    payload = module.research_strategy_candidate_disagreement_resolution_report_payload(
        empty,
    )

    assert empty.status == "pass"
    assert empty.candidate_count == ZERO
    assert empty.rows == ()
    assert empty.reason_codes == ("empty_input",)
    assert empty.reason_code_counts == (
        module.ResearchStrategyCandidateDisagreementResolutionReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )

    rendered = repr(payload).casefold()
    for forbidden in (
        "recommendation",
        "recommended",
        "sizing",
        "stake",
        "position",
        "allocation",
        "buy",
        "sell",
    ):
        assert forbidden not in rendered


def test_frozen_decimal_only_status_and_hard_flag_guards() -> None:
    module = api()
    built = report(item("candidate-a"))

    for cls_name in (
        "ResearchStrategyCandidateDisagreementResolutionConfig",
        "ResearchStrategyCandidateDisagreementResolutionInput",
        "ResearchStrategyCandidateDisagreementResolutionRow",
        "ResearchStrategyCandidateDisagreementResolutionReasonCodeCount",
        "ResearchStrategyCandidateDisagreementResolutionReport",
    ):
        assert is_dataclass(getattr(module, cls_name))

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].unresolved_disagreement_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="model_signal_disagreement"):
        item("candidate-a", model_signal_disagreement=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="consensus_disagreement"):
        item("candidate-a", consensus_disagreement=d("1.000001"))
    with pytest.raises(ValueError, match="specialist_memory_disagreement"):
        item(
            "candidate-a",
            specialist_memory_disagreement=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(item("candidate-a"), generated_at=_DateTimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        item("candidate-a", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(built, report_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="review")

    for value in (built, *built.rows, *built.reason_code_counts):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            field_value = getattr(value, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal
            if field.name.endswith(("_count", "_score", "_ratio", "_disagreement")):
                assert type(field_value) is Decimal


def test_source_has_no_network_db_or_live_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imports: list[str] = []
    calls: list[str] = []
    public_field_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            public_field_names.append(node.target.id.casefold())

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    }
    forbidden_calls = {"open", "connect", "execute", "post", "put", "patch", "delete"}
    forbidden_public_field_fragments = {
        "auth",
        "dsn",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
    }

    assert forbidden_imports.isdisjoint(imports)
    assert forbidden_calls.isdisjoint(calls)
    assert not any(
        fragment in field_name
        for fragment in forbidden_public_field_fragments
        for field_name in public_field_names
    )
