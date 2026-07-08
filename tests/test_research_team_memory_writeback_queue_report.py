from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=UTC)


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
        "polymarket_alpha_lab.research_team_memory_writeback_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_TEAM_MEMORY_WRITEBACK_QUEUE_CONFIG_VERSION
        ),
        "min_postmortem_summary_score": d("0.750000"),
        "min_deidentification_pass_score": d("0.900000"),
        "min_deidentification_block_score": d("0.500000"),
        "min_calibration_update_score": d("0.700000"),
        "stale_postmortem_watch_seconds": d("2592000.000000"),
        "stale_postmortem_block_seconds": d("7776000.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryWritebackQueueConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "writeback_reference": "writeback-alpha",
        "source_bundle_reference": "source-alpha",
        "scope_reference": "scope-alpha",
        "team_domain": "finance.crypto.btc",
        "memory_topic": "resolution-policy",
        "postmortem_summary": "Resolved policy drift with deidentified evidence.",
        "postmortem_completed_at": GENERATED_AT - timedelta(days=5),
        "postmortem_summary_score": d("0.900000"),
        "deidentification_score": d("0.950000"),
        "conflict_resolution_state": "resolved",
        "calibration_update_score": d("0.850000"),
        "local_store_plan_state": "ready",
        "owner_review_required": False,
    }
    values.update(overrides)
    return module.ResearchTeamMemoryWritebackCandidate(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_memory_writeback_queue_report(
        items,
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


def test_builds_pass_watch_block_writeback_planning_report() -> None:
    result = report(
        candidate(
            writeback_reference="pass-writeback",
            source_bundle_reference="pass-source",
            scope_reference="pass-scope",
            postmortem_summary_score=d("0.900000"),
            deidentification_score=d("0.950000"),
            conflict_resolution_state="resolved",
            calibration_update_score=d("0.850000"),
            local_store_plan_state="ready",
            owner_review_required=False,
        ),
        candidate(
            writeback_reference="watch-writeback",
            source_bundle_reference="watch-source",
            scope_reference="watch-scope",
            postmortem_completed_at=GENERATED_AT - timedelta(days=40),
            postmortem_summary_score=d("0.600000"),
            deidentification_score=d("0.820000"),
            conflict_resolution_state="needs_review",
            calibration_update_score=d("0.550000"),
            local_store_plan_state="needs_review",
            owner_review_required=True,
        ),
        candidate(
            writeback_reference="block-writeback",
            source_bundle_reference="block-source",
            scope_reference="block-scope",
            postmortem_summary_score=d("0.900000"),
            deidentification_score=d("0.300000"),
            conflict_resolution_state="blocked",
            calibration_update_score=d("0.800000"),
            local_store_plan_state="blocked",
            owner_review_required=True,
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.item_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.owner_review_required_count == d("2")
    assert result.deidentification_watch_count == d("1")
    assert result.deidentification_block_count == d("1")
    assert result.local_store_ready_count == d("1")
    assert result.status == "block"
    assert result.reason_codes == (
        "deidentification_block",
        "conflict_resolution_block",
        "local_store_plan_block",
        "postmortem_summary_watch",
        "stale_postmortem_watch",
        "deidentification_watch",
        "conflict_resolution_watch",
        "calibration_update_watch",
        "local_store_plan_watch",
        "owner_review_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows

    assert blocked.status == "block"
    assert blocked.deidentification_plan == "block_until_redaction_passes"
    assert blocked.conflict_resolution_plan == "hold_until_conflict_owner_resolution"
    assert blocked.calibration_update_plan == "apply_calibration_update"
    assert blocked.local_store_write_plan == "do_not_prepare_local_store_plan"
    assert blocked.reason_codes == (
        "deidentification_block",
        "conflict_resolution_block",
        "local_store_plan_block",
        "owner_review_watch",
    )

    assert watched.status == "watch"
    assert watched.postmortem_age_seconds == d("3456000.000000")
    assert watched.postmortem_summary_plan == "revise_postmortem_summary"
    assert watched.deidentification_plan == "strengthen_deidentification"
    assert watched.conflict_resolution_plan == "queue_conflict_owner_review"
    assert watched.calibration_update_plan == "queue_calibration_review"
    assert watched.local_store_write_plan == (
        "hold_local_supabase_postgres_plan_for_review"
    )
    assert watched.reason_codes == (
        "postmortem_summary_watch",
        "stale_postmortem_watch",
        "deidentification_watch",
        "conflict_resolution_watch",
        "calibration_update_watch",
        "local_store_plan_watch",
        "owner_review_watch",
    )

    assert passed.status == "pass"
    assert passed.postmortem_summary_plan == "include_deidentified_postmortem_summary"
    assert passed.deidentification_plan == "use_redacted_markers_only"
    assert passed.conflict_resolution_plan == "apply_resolved_memory"
    assert passed.calibration_update_plan == "apply_calibration_update"
    assert passed.local_store_write_plan == "prepare_local_supabase_postgres_write_plan"
    assert passed.reason_codes == ("memory_writeback_queue_pass",)


def test_empty_input_returns_pass_report() -> None:
    result = report()

    assert result.item_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.status == "pass"
    assert result.reason_codes == ("memory_writeback_queue_empty",)
    assert result.rows == ()


def test_payload_uses_decimal_strings_and_redacts_private_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    result = report(
        candidate(
            writeback_reference="internal-writeback-token-wallet",
            source_bundle_reference=(
                "postgres://private.example/dsn/table/raw/source/token"
            ),
            scope_reference="polymarket-market-id-slug-question-auth-token",
            deidentification_score=d("0.300000"),
            conflict_resolution_state="blocked",
            local_store_plan_state="blocked",
            owner_review_required=True,
        ),
    )

    payload = module.research_team_memory_writeback_queue_report_payload(result)
    rendered = json.dumps(payload, sort_keys=True).lower()
    keys = tuple(key.lower() for key in _walk_keys(payload))

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["writeback_marker"].startswith("writeback_marker_")
    assert payload["rows"][0]["evidence_bundle_marker"].startswith("evidence_marker_")
    assert payload["rows"][0]["scope_marker"].startswith("scope_marker_")
    assert payload["rows"][0]["deidentification_score"] == "0.300000"
    assert payload["owner_review_required_count"] == "1"
    assert_no_int_or_float_values(payload)

    for forbidden in (
        "internal-writeback",
        "postgres://",
        "private.example",
        "dsn",
        "table",
        "raw/source",
        "raw_source",
        "source_bundle_reference",
        "source_reference",
        "polymarket-market",
        "market-id",
        "market_reference",
        "market_id",
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
            "source_bundle_reference",
            "market_reference",
            "market_id",
        )
    )

    def unsafe_json_ready_key(value: object) -> dict[str, object]:
        assert value is result
        return {"paper_only": True, "report_only": True, "readonly": True, "dsn": "x"}

    monkeypatch.setattr(module, "json_ready_no_floats", unsafe_json_ready_key)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_memory_writeback_queue_report_payload(result)

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
        module.research_team_memory_writeback_queue_report_payload(result)


def test_rejects_bad_types_times_order_unsafe_text_and_flags() -> None:
    valid_candidate = candidate()

    with pytest.raises(ValueError, match="min_postmortem_summary_score"):
        config(min_postmortem_summary_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_deidentification_pass_score"):
        config(min_deidentification_pass_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="min_deidentification_block_score"):
        config(min_deidentification_block_score=d("0.950000"))
    with pytest.raises(ValueError, match="stale_postmortem_block_seconds"):
        config(stale_postmortem_block_seconds=d("2592000.000000"))
    with pytest.raises(ValueError, match="postmortem_summary_score"):
        candidate(postmortem_summary_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deidentification_score"):
        candidate(deidentification_score=_DecimalSubclass("0.950000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(valid_candidate, generated_at=datetime(2026, 7, 8, 9, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            valid_candidate,
            generated_at=_DatetimeSubclass(2026, 7, 8, 9, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="postmortem_completed_at"):
        candidate(postmortem_completed_at=datetime(2026, 7, 8, 9, 30))
    with pytest.raises(ValueError, match="postmortem_completed_at"):
        candidate(
            postmortem_completed_at=datetime(
                2026,
                7,
                8,
                9,
                30,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="postmortem_completed_at"):
        report(
            candidate(postmortem_completed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="postmortem_summary"):
        candidate(postmortem_summary="raw source token from market id")
    with pytest.raises(ValueError, match="conflict_resolution_state"):
        candidate(conflict_resolution_state="unknown")
    with pytest.raises(ValueError, match="local_store_plan_state"):
        candidate(local_store_plan_state="remote")
    with pytest.raises(ValueError, match="owner_review_required"):
        candidate(owner_review_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_candidate, paper_only=False)


def test_frozen_dataclasses_and_manual_report_consistency() -> None:
    result = report(
        candidate(writeback_reference="item-1"),
        candidate(
            writeback_reference="item-2",
            source_bundle_reference="source-2",
            scope_reference="scope-2",
            deidentification_score=d("0.300000"),
            conflict_resolution_state="blocked",
            local_store_plan_state="blocked",
            owner_review_required=True,
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
        module.research_team_memory_writeback_queue_report_payload(result.rows[0])


def test_module_has_no_database_trading_or_network_write_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_memory_writeback_queue_report.py"
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
        "insert",
        "upsert",
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
