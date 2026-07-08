from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_conflict_resolver_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_RESOLVER_CONFIG_VERSION
        ),
        "stale_evidence_watch_seconds": d("604800.000000"),
        "stale_evidence_block_seconds": d("2592000.000000"),
        "domain_priority_watch_score": d("0.700000"),
        "domain_priority_block_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryConflictResolverConfig(**values)


def conflict_case(**overrides: object):
    module = api()
    values = {
        "case_reference": "case-alpha",
        "raw_source_reference": "source-alpha",
        "market_reference": "market-alpha",
        "team_domain": "finance.crypto.btc",
        "memory_topic": "resolution-policy",
        "conflict_type": "source_disagreement",
        "older_evidence_observed_at": GENERATED_AT - timedelta(days=30),
        "newer_evidence_observed_at": GENERATED_AT - timedelta(days=1),
        "domain_priority_score": d("0.200000"),
        "postmortem_conclusion": "resolved",
        "escalation_required": False,
    }
    values.update(overrides)
    return module.ResearchTeamMemoryConflictCase(**values)


def report(*cases: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_memory_conflict_resolver_report(
        cases,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def _walk_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_walk_keys(item))
        return tuple(keys)
    return ()


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def test_scores_memory_conflicts_as_pass_watch_and_block() -> None:
    result = report(
        conflict_case(
            case_reference="pass-case",
            raw_source_reference="pass-source",
            market_reference="pass-market",
            conflict_type="model_assumption",
            older_evidence_observed_at=GENERATED_AT - timedelta(days=20),
            newer_evidence_observed_at=GENERATED_AT - timedelta(days=1),
            domain_priority_score=d("0.200000"),
            postmortem_conclusion="resolved",
            escalation_required=False,
        ),
        conflict_case(
            case_reference="watch-case",
            raw_source_reference="watch-source",
            market_reference="watch-market",
            conflict_type="source_disagreement",
            older_evidence_observed_at=GENERATED_AT - timedelta(days=40),
            newer_evidence_observed_at=GENERATED_AT - timedelta(days=8),
            domain_priority_score=d("0.750000"),
            postmortem_conclusion="needs_recheck",
            escalation_required=False,
        ),
        conflict_case(
            case_reference="block-case",
            raw_source_reference="block-source",
            market_reference="block-market",
            conflict_type="resolution_rule",
            older_evidence_observed_at=GENERATED_AT - timedelta(days=60),
            newer_evidence_observed_at=GENERATED_AT - timedelta(days=2),
            domain_priority_score=d("0.950000"),
            postmortem_conclusion="unresolved",
            escalation_required=True,
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.case_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.escalation_required_count == d("1")
    assert result.stale_newer_evidence_count == d("1")
    assert result.high_domain_priority_count == d("2")
    assert result.status == "block"
    assert result.reason_codes == (
        "escalation_required_block",
        "postmortem_unresolved_block",
        "domain_priority_block",
        "newer_evidence_stale_watch",
        "domain_priority_watch",
        "postmortem_recheck_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows

    assert blocked.conflict_type == "resolution_rule"
    assert blocked.evidence_age_order == "newer_after_older"
    assert blocked.newer_evidence_age_seconds == d("172800.000000")
    assert blocked.evidence_revision_gap_seconds == d("5011200.000000")
    assert blocked.domain_priority_tier == "block"
    assert blocked.postmortem_conclusion == "unresolved"
    assert blocked.escalation_required is True
    assert blocked.reason_codes == (
        "escalation_required_block",
        "postmortem_unresolved_block",
        "domain_priority_block",
    )
    assert blocked.resolver_actions == (
        "escalate_to_memory_owner",
        "freeze_conflicting_memory_until_reviewed",
        "prefer_newer_evidence_after_review",
    )

    assert watched.status == "watch"
    assert watched.newer_evidence_age_seconds == d("691200.000000")
    assert watched.domain_priority_tier == "watch"
    assert watched.reason_codes == (
        "newer_evidence_stale_watch",
        "domain_priority_watch",
        "postmortem_recheck_watch",
    )
    assert passed.status == "pass"
    assert passed.reason_codes == ("memory_conflict_resolver_pass",)
    assert passed.resolver_actions == ("record_resolved_postmortem",)


def test_empty_input_returns_pass_report() -> None:
    result = report()

    assert result.case_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.status == "pass"
    assert result.reason_codes == ("memory_conflict_resolver_empty",)
    assert result.rows == ()


def test_payload_uses_decimal_strings_and_redacts_private_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    result = report(
        conflict_case(
            case_reference="internal-case-token-wallet",
            raw_source_reference="postgres://private.example/dsn/table/raw/source/token",
            market_reference="polymarket-market-id-slug-question-auth-token",
            domain_priority_score=d("0.950000"),
            postmortem_conclusion="unresolved",
            escalation_required=True,
        ),
    )

    payload = module.research_team_memory_conflict_resolver_report_payload(result)
    rendered = json.dumps(payload, sort_keys=True).lower()
    keys = tuple(key.lower() for key in _walk_keys(payload))

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["case_marker"].startswith("case_marker_")
    assert payload["rows"][0]["evidence_bundle_marker"].startswith("evidence_marker_")
    assert payload["rows"][0]["case_scope_marker"].startswith("scope_marker_")
    assert payload["rows"][0]["domain_priority_score"] == "0.950000"
    assert payload["escalation_required_count"] == "1"
    assert_no_int_or_float_values(payload)

    for forbidden in (
        "internal-case",
        "postgres",
        "private.example",
        "dsn",
        "table",
        "raw/source",
        "raw_source",
        "source_reference",
        "polymarket-market",
        "market-id",
        "slug",
        "question",
        "auth",
        "token",
        "wallet",
    ):
        assert forbidden not in rendered
        assert forbidden not in repr(result).lower()
    assert not any(
        fragment in key
        for key in keys
        for fragment in (
            "dsn",
            "table",
            "token",
            "raw_source",
            "source_reference",
            "market_reference",
            "market_id",
        )
    )

    def unsafe_json_ready_key(value: object) -> dict[str, object]:
        assert value is result
        return {"paper_only": True, "report_only": True, "readonly": True, "dsn": "x"}

    monkeypatch.setattr(module, "json_ready_no_floats", unsafe_json_ready_key)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_memory_conflict_resolver_report_payload(result)

    def unsafe_json_ready_value(value: object) -> dict[str, object]:
        assert value is result
        return {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "operator_note": "raw source token from market id",
        }

    monkeypatch.setattr(module, "json_ready_no_floats", unsafe_json_ready_value)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_memory_conflict_resolver_report_payload(result)


def test_rejects_bad_types_times_order_unsafe_text_and_flags() -> None:
    valid_case = conflict_case()

    with pytest.raises(ValueError, match="stale_evidence_watch_seconds"):
        config(stale_evidence_watch_seconds=604800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_priority_watch_score"):
        config(domain_priority_watch_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="stale_evidence_block_seconds"):
        config(stale_evidence_block_seconds=d("604800.000000"))
    with pytest.raises(ValueError, match="domain_priority_block_score"):
        config(domain_priority_block_score=d("0.700000"))
    with pytest.raises(ValueError, match="domain_priority_score"):
        conflict_case(domain_priority_score=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_priority_score"):
        conflict_case(domain_priority_score=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(valid_case, generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            valid_case,
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="older_evidence_observed_at"):
        conflict_case(older_evidence_observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="newer_evidence_observed_at"):
        conflict_case(
            newer_evidence_observed_at=datetime(
                2026,
                7,
                7,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="newer_evidence_observed_at"):
        conflict_case(
            older_evidence_observed_at=GENERATED_AT - timedelta(days=1),
            newer_evidence_observed_at=GENERATED_AT - timedelta(days=2),
        )
    with pytest.raises(ValueError, match="newer_evidence_observed_at"):
        report(
            conflict_case(newer_evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="conflict_type"):
        conflict_case(conflict_type="unknown")
    with pytest.raises(ValueError, match="postmortem_conclusion"):
        conflict_case(postmortem_conclusion="maybe")
    with pytest.raises(ValueError, match="memory_topic"):
        conflict_case(memory_topic="token leakage")
    with pytest.raises(ValueError, match="escalation_required"):
        conflict_case(escalation_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_case, paper_only=False)


def test_frozen_dataclasses_and_manual_report_consistency() -> None:
    result = report(
        conflict_case(case_reference="case-1"),
        conflict_case(
            case_reference="case-2",
            raw_source_reference="source-2",
            market_reference="market-2",
            domain_priority_score=d("0.950000"),
            postmortem_conclusion="unresolved",
            escalation_required=True,
        ),
    )

    with pytest.raises(FrozenInstanceError):
        result.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="pass")
    with pytest.raises(ValueError, match="block_count"):
        replace(result, block_count=d("0"))
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))

    module = api()
    with pytest.raises(ValueError, match="report"):
        module.research_team_memory_conflict_resolver_report_payload(result.rows[0])


def test_module_has_no_database_trading_or_network_write_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_memory_conflict_resolver_report.py"
    )
    tree = ast.parse(source_path.read_text())

    banned_import_roots = {
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "sqlite3",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "web3",
        "py_clob_client",
    }
    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "request",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "submit",
        "order",
        "trade",
        "buy",
        "sell",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            assert _call_name(node.func) not in banned_call_names
