from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_domain_specialist_vote_reconciliation_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_specialist_vote_reconciliation_report.py"
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
            module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION
        ),
        "watch_disagreement_breadth": d("0.350000"),
        "block_disagreement_breadth": d("0.700000"),
        "watch_calibration_memory_staleness_score": d("0.200000"),
        "block_calibration_memory_staleness_score": d("0.400000"),
        "watch_evidence_coverage_gap_score": d("0.200000"),
        "block_evidence_coverage_gap_score": d("0.400000"),
        "watch_cost_pressure": d("0.350000"),
        "block_cost_pressure": d("0.700000"),
        "watch_reconciliation_risk_score": d("0.275000"),
        "block_reconciliation_risk_score": d("0.550000"),
        "disagreement_breadth_weight": d("0.250000"),
        "calibration_memory_staleness_weight": d("0.250000"),
        "evidence_coverage_gap_weight": d("0.250000"),
        "cost_pressure_weight": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainSpecialistVoteReconciliationConfig(**values)


def vote(vote_key: str = "private-vote-alpha", **overrides: object) -> object:
    module = api()
    values = {
        "vote_key": vote_key,
        "disagreement_breadth": d("0.100000"),
        "calibration_memory_freshness": d("0.900000"),
        "evidence_coverage": d("0.900000"),
        "cost_pressure": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainSpecialistVoteReconciliationInput(**values)


def report(
    *items: object,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    module = api()
    return module.build_research_strategy_domain_specialist_vote_reconciliation_report(
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


def refresh_payload_digest(payload: dict[str, Any]) -> None:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()


def test_reconciles_vote_disagreement_boundaries_into_analyst_triage() -> None:
    module = api()
    built = report(
        vote(
            "raw-candidate-id-market-id-slug-question-source-url",
            disagreement_breadth=d("0.700000"),
            calibration_memory_freshness=d("0.600000"),
            evidence_coverage=d("0.600000"),
            cost_pressure=d("0.700000"),
        ),
        vote(
            "private-vote-watch",
            disagreement_breadth=d("0.350000"),
            calibration_memory_freshness=d("0.800000"),
            evidence_coverage=d("0.800000"),
            cost_pressure=d("0.350000"),
        ),
        vote("private-vote-pass"),
    )

    assert module.RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_SPECIALIST_VOTE_RECONCILIATION_STATUSES",
        "ResearchStrategyDomainSpecialistVoteReconciliationConfig",
        "ResearchStrategyDomainSpecialistVoteReconciliationInput",
        "ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount",
        "ResearchStrategyDomainSpecialistVoteReconciliationRow",
        "ResearchStrategyDomainSpecialistVoteReconciliationReport",
        "build_research_strategy_domain_specialist_vote_reconciliation_report",
        "research_strategy_domain_specialist_vote_reconciliation_report_payload",
        "research_strategy_domain_specialist_vote_reconciliation_report_digest",
    )
    assert type(built) is module.ResearchStrategyDomainSpecialistVoteReconciliationReport
    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.vote_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.mean_reconciliation_risk_score == d("0.308333")
    assert built.max_disagreement_breadth == d("0.700000")
    assert built.min_calibration_memory_freshness == d("0.600000")
    assert built.min_evidence_coverage == d("0.600000")
    assert built.max_cost_pressure == d("0.700000")
    assert built.reason_codes == (
        "disagreement_breadth_block",
        "calibration_memory_stale_block",
        "evidence_coverage_gap_block",
        "cost_pressure_block",
        "reconciliation_risk_score_block",
        "disagreement_breadth_watch",
        "calibration_memory_stale_watch",
        "evidence_coverage_gap_watch",
        "cost_pressure_watch",
        "reconciliation_risk_score_watch",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.vote_digest.startswith("sha256:")
    assert "raw-candidate-id" not in blocked.vote_digest
    assert blocked.memory_staleness_score == d("0.400000")
    assert blocked.evidence_gap_score == d("0.400000")
    assert blocked.reconciliation_risk_score == d("0.550000")
    assert blocked.dominant_pressure == "disagreement_breadth"
    assert blocked.reason_codes == (
        "disagreement_breadth_block",
        "calibration_memory_stale_block",
        "evidence_coverage_gap_block",
        "cost_pressure_block",
        "reconciliation_risk_score_block",
    )

    assert watched.status == "watch"
    assert watched.memory_staleness_score == d("0.200000")
    assert watched.evidence_gap_score == d("0.200000")
    assert watched.reconciliation_risk_score == d("0.275000")
    assert watched.reason_codes == (
        "disagreement_breadth_watch",
        "calibration_memory_stale_watch",
        "evidence_coverage_gap_watch",
        "cost_pressure_watch",
        "reconciliation_risk_score_watch",
    )

    assert passed.status == "pass"
    assert passed.reconciliation_risk_score == d("0.100000")
    assert passed.reason_codes == ("domain_specialist_vote_reconciliation_pass",)


def test_payload_is_deterministic_redacted_decimal_only_and_digest_guarded() -> None:
    module = api()
    first = report(
        vote("vote://market-123/slug/question?source=https://example.invalid"),
        vote("private-vote-a"),
    )
    second = report(
        vote("private-vote-a"),
        vote("vote://market-123/slug/question?source=https://example.invalid"),
    )

    first_payload = (
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            first,
        )
    )
    second_payload = (
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            second,
        )
    )

    assert first_payload == second_payload
    assert first_payload == first.payload
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["vote_count"] == "2.000000"
    assert first_payload["rows"][0]["vote_digest"].startswith("sha256:")
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first_payload["derived_validation_digest"]) == 64
    assert module.research_strategy_domain_specialist_vote_reconciliation_report_digest(
        first,
    ) == first.derived_validation_digest

    expected_payload = dict(first_payload)
    expected_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(expected_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    assert first_payload["derived_validation_digest"] == expected_digest

    rendered = repr(first_payload).casefold()
    for forbidden in (
        "vote://market-123",
        "private-vote-a",
        "candidate",
        "market_id",
        "market-123",
        "slug",
        "question",
        "source_url",
        "source_text",
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
        "recommendation",
        "sizing",
    ):
        assert forbidden not in rendered
    assert not any(isinstance(value, float) for value in walk_values(first_payload))
    assert not any(type(value) is int for value in walk_values(first_payload))

    tampered = dict(first_payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            tampered,
        )

    downgraded = dict(first_payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            downgraded,
        )

    unsafe = dict(first_payload)
    unsafe["source_url"] = "https://example.invalid/private"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            unsafe,
        )


def test_payload_rejects_recomputed_schema_and_nested_flag_drift() -> None:
    module = api()
    payload = module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
        report(vote("private-vote-a")),
    )

    expanded = dict(payload)
    expanded["commentary"] = "paper review only"
    refresh_payload_digest(expanded)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            expanded,
        )

    wrong_container = dict(payload)
    wrong_container["reason_codes"] = tuple(payload["reason_codes"])
    refresh_payload_digest(wrong_container)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            wrong_container,
        )

    downgraded = dict(payload)
    downgraded_rows = [dict(row) for row in payload["rows"]]
    downgraded_rows[0]["readonly"] = False
    downgraded["rows"] = downgraded_rows
    refresh_payload_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            downgraded,
        )


def test_payload_rejects_recomputed_canonical_report_drift() -> None:
    module = api()
    payload = module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
        report(vote("private-vote-a")),
    )

    bad_config = dict(payload)
    bad_config["config_version"] = (
        "research-strategy-domain-specialist-vote-reconciliation-report-v9"
    )
    refresh_payload_digest(bad_config)
    with pytest.raises(ValueError, match="config_version"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            bad_config,
        )

    bad_summary = dict(payload)
    bad_summary["mean_reconciliation_risk_score"] = "0.200000"
    refresh_payload_digest(bad_summary)
    with pytest.raises(ValueError, match="mean_reconciliation_risk_score"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            bad_summary,
        )

    bad_row = dict(payload)
    bad_rows = [dict(row) for row in payload["rows"]]
    bad_rows[0]["memory_staleness_score"] = "0.200000"
    bad_row["rows"] = bad_rows
    refresh_payload_digest(bad_row)
    with pytest.raises(ValueError, match="memory_staleness_score"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            bad_row,
        )


def test_digest_accessor_rejects_tampered_report_state() -> None:
    module = api()
    built = report(vote("private-vote-a"))

    object.__setattr__(built.rows[0], "cost_pressure", d("0.900000"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_digest(
            built,
        )


def test_payload_rejects_non_string_mapping_keys_with_value_error() -> None:
    module = api()
    payload = module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
        report(vote("private-vote-a")),
    )

    malformed_report = dict(payload)
    malformed_report[1] = "paper review only"  # type: ignore[index]

    malformed_nested = dict(payload)
    malformed_rows = [dict(row) for row in payload["rows"]]
    malformed_rows[0][1] = "paper review only"  # type: ignore[index]
    malformed_nested["rows"] = malformed_rows

    for malformed in (malformed_report, malformed_nested):
        with pytest.raises(ValueError, match="keys must be strings"):
            module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
                malformed,
            )


@pytest.mark.parametrize(
    "leaked",
    ("execution-plan", "live_trading-plan", "allocation-plan"),
)
def test_payload_rejects_extended_action_leakage_with_valid_digest(leaked: str) -> None:
    module = api()
    payload = module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
        report(vote("private-vote-a")),
    )
    payload["commentary"] = leaked
    refresh_payload_digest(payload)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
            payload,
        )


def test_custom_config_can_tighten_disagreement_watch_behavior() -> None:
    custom = cfg(
        watch_disagreement_breadth=d("0.200000"),
        block_disagreement_breadth=d("0.900000"),
        watch_calibration_memory_staleness_score=d("0.900000"),
        block_calibration_memory_staleness_score=d("0.950000"),
        watch_evidence_coverage_gap_score=d("0.900000"),
        block_evidence_coverage_gap_score=d("0.950000"),
        watch_cost_pressure=d("0.900000"),
        block_cost_pressure=d("0.950000"),
        watch_reconciliation_risk_score=d("0.900000"),
        block_reconciliation_risk_score=d("0.950000"),
    )
    built = report(
        vote(
            "private-vote-custom",
            disagreement_breadth=d("0.250000"),
            calibration_memory_freshness=d("0.900000"),
            evidence_coverage=d("0.900000"),
            cost_pressure=d("0.100000"),
        ),
        config=custom,
    )

    assert built.status == "watch"
    assert built.watch_count == d("1.000000")
    assert built.block_count == ZERO
    assert built.rows[0].status == "watch"
    assert built.rows[0].reason_codes == ("disagreement_breadth_watch",)


def test_empty_input_is_pass_report_only_without_live_action_surfaces() -> None:
    module = api()
    empty = report()
    payload = module.research_strategy_domain_specialist_vote_reconciliation_report_payload(
        empty,
    )

    assert empty.status == "pass"
    assert empty.vote_count == ZERO
    assert empty.rows == ()
    assert empty.reason_codes == ("empty_input",)
    assert empty.reason_code_counts == (
        module.ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            vote_ratio=d("1.000000"),
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
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in rendered


def test_frozen_decimal_only_hard_flags_and_validation_guards() -> None:
    module = api()
    built = report(vote("private-vote-a"))

    for cls_name in (
        "ResearchStrategyDomainSpecialistVoteReconciliationConfig",
        "ResearchStrategyDomainSpecialistVoteReconciliationInput",
        "ResearchStrategyDomainSpecialistVoteReconciliationRow",
        "ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount",
        "ResearchStrategyDomainSpecialistVoteReconciliationReport",
    ):
        assert is_dataclass(getattr(module, cls_name))

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].reconciliation_risk_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="disagreement_breadth"):
        vote("private-vote-a", disagreement_breadth=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_coverage"):
        vote("private-vote-a", evidence_coverage=d("1.000001"))
    with pytest.raises(ValueError, match="cost_pressure"):
        vote("private-vote-a", cost_pressure=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            vote("private-vote-a"),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            vote("private-vote-a"),
            generated_at=datetime(2026, 7, 8, 12, tzinfo=MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        vote("private-vote-a", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(built, report_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="review")
    with pytest.raises(ValueError, match="block_disagreement_breadth"):
        cfg(block_disagreement_breadth=d("0.350000"))
    with pytest.raises(ValueError, match="empty_input"):
        replace(built.rows[0], reason_codes=("empty_input",))
    with pytest.raises(ValueError, match="pass reason"):
        replace(
            built.rows[0],
            status="watch",
            reason_codes=(
                "cost_pressure_watch",
                "domain_specialist_vote_reconciliation_pass",
            ),
        )

    @dataclass(frozen=True)
    class ReasonCodeCountSubclass(
        module.ResearchStrategyDomainSpecialistVoteReconciliationReasonCodeCount,
    ):
        pass

    with pytest.raises(ValueError, match="reason_code_count"):
        ReasonCodeCountSubclass(
            reason_code="domain_specialist_vote_reconciliation_pass",
            count=d("1.000000"),
            vote_ratio=d("1.000000"),
        )

    for value in (built, *built.rows, *built.reason_code_counts):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            field_value = getattr(value, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal
            if field.name.endswith(("_count", "_score", "_ratio", "_breadth")):
                assert type(field_value) is Decimal


def test_source_has_no_network_db_wallet_order_or_identifier_surfaces() -> None:
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
        "candidate_id",
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
