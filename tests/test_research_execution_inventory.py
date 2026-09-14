"""Bounded complete inventories, existing codecs and no model/DB side effects."""
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone
import json

import pytest

from polymarket_alpha_lab import research_execution_inventory as inv
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from polymarket_alpha_lab.research_capture_codec import encode_research_capture, payload_sha256
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS
from tests.test_research_execution import NOW, request, state, record_for, make_run
from tests.test_research_execution_psycopg import claim_row
from tests.test_research_capture_psycopg import DSN, FakeConnection, install

AT = NOW + timedelta(seconds=10)


def saved(kind="completed", rid="r1", team="crypto_eth"):
    run = make_run(task=rid, team=team, status="failed" if kind == "blocked" else
                   "completed" if kind == "incomplete" else kind)
    if kind == "blocked":
        run = replace(run, research=replace(run.research, status="blocked", reason_code="invalid_model_action"))
    req = request(record_id=rid, intake=run.intake)
    return state(req) if kind == "incomplete" else replace(state(req), status="already_captured", record=record_for(req, run))


def record_row(item):
    r = item.record
    i = r.run.intake
    payload = encode_research_capture(record_id=r.record_id, model_id=r.model_id,
                                      protocol_version=r.protocol_version, run=r.run)
    return (r.record_id, i.condition_id, i.market_slug, i.team_id, r.model_id, r.protocol_version,
            i.task_id, i.as_of, r.recorded_at, payload, payload_sha256(payload), True, True, True)


def answers(items=(), unclaimed=0):
    claims = [claim_row(item.request, item.claimed_at) for item in items]
    records = [record_row(item) for item in items if item.record is not None]
    def stats(rows):
        return (len(rows), sum(len(row[9].encode()) for row in rows), max((row[8] for row in rows), default=None))
    return [(AT,), stats(claims), stats(records), (unclaimed,), claims, records]


def load(monkeypatch, rows=None, **config):
    connection = FakeConnection(answers() if rows is None else rows)
    calls = install(monkeypatch, connection)
    result = inv.load_execution_inventory_with_psycopg(DSN, **config)
    assert calls == [(DSN, {"connect_timeout": 5})]
    assert connection.events == ["opened", "cursor_closed", "commit", "closed"]
    assert connection.calls[0][0].endswith("REPEATABLE READ READ ONLY")
    assert all(not q.startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "TRUNCATE")) for q, _ in connection.calls)
    assert len([q for q, _ in connection.calls if q.startswith("SELECT")]) == 6
    return result, connection


@pytest.mark.parametrize("kind", ("incomplete", "completed", "failed", "blocked", "intake_blocked"))
@pytest.mark.parametrize("team", TEAM_IDS)
def test_all_teams_and_states_preserve_existing_metadata_and_explicit_unknowns(kind, team):
    item = saved(kind, team=team)
    report = inv.ResearchExecutionInventory(AT, (item,), 3)
    output = report.to_dict()
    incomplete = kind == "incomplete"
    assert output["claim_count"] == 1 and output["incomplete_claim_count"] == int(incomplete)
    assert output["captured_result_count"] == int(not incomplete) and output["unclaimed_attempt_count"] == 3
    assert sum(output["state_counts"].values()) == 1
    assert output["inventory_status"] == ("incomplete_claims_present" if incomplete else "all_claims_have_results")
    row = output["executions"][0]
    assert row["record_id"] == "r1" and row["team_id"] == team
    assert row["request_sha256"] == item.request.content_sha256
    assert row["recorded_at"] == (None if incomplete else item.record.recorded_at.isoformat())
    assert row["record_sha256"] == (None if incomplete else item.record.content_sha256)
    assert row["worker_liveness"] == "unknown"
    assert output["entire_history_checked"] is output["scoring_performed"] is output["automatic_retry_permitted"] is False
    assert output["claim_inventory_complete"] is True and output["unclaimed_attempts_decoded"] is False
    for forbidden in ("SYNTHETIC-PRIVATE", "synthetic:source", "probability_yes", "tool_trace", "raw_json", "question"):
        assert forbidden not in json.dumps(output) and forbidden not in repr(report)
    if incomplete:
        assert row["stored_research"] is None and row["recorded_at"] is None
    with pytest.raises(FrozenInstanceError): report.generated_at = NOW


def test_empty_claims_do_not_mean_no_standalone_attempts(monkeypatch):
    result, _ = load(monkeypatch, answers(unclaimed=4))
    out = result.to_dict()
    assert out["inventory_status"] == "no_claims" and out["unclaimed_attempt_count"] == 4
    assert out["claim_count"] == out["captured_result_count"] == out["incomplete_claim_count"] == 0
    assert out["executions"] == [] and sum(out["state_counts"].values()) == 0


def test_complete_snapshot_order_binding_counts_and_constant_query_count(monkeypatch):
    items = (saved("incomplete", "z"), saved("completed", "a"), saved("failed", "b"))
    result, connection = load(monkeypatch, answers(items, unclaimed=2))
    output = result.to_dict()
    assert [row["record_id"] for row in output["executions"]] == ["a", "b", "z"]
    assert output["captured_result_count"] == 2 and output["incomplete_claim_count"] == 1
    assert output["incomplete_claims_block_evaluation"] is True
    assert result.executions[0].record == items[1].record
    sql = "\n".join(q for q, _ in connection.calls)
    assert "octet_length(request_payload)" in sql and "octet_length(a.payload)" in sql
    assert 'COLLATE "C"' in sql and "LIMIT" not in sql and "outcomes" not in sql
    assert "record_id=%s" not in sql  # Bulk decode, not N separate lookup transactions.


@pytest.mark.parametrize("value", (True, 0, -1, 1001, "1", None, 1.0))
def test_invalid_bound_never_opens_driver(monkeypatch, value):
    calls = install(monkeypatch, FakeConnection())
    with pytest.raises(ValueError): inv.load_execution_inventory_with_psycopg(DSN, max_records=value)
    assert calls == []


def test_nonlocal_dsn_never_reaches_driver(monkeypatch):
    calls = install(monkeypatch, FakeConnection())
    with pytest.raises(ValueError): inv.load_execution_inventory_with_psycopg("postgresql://user@remote.invalid/db")
    assert calls == []


@pytest.mark.parametrize("phase", ("count", "claim_bytes", "combined_bytes"))
def test_caps_block_before_fetching_payloads(monkeypatch, phase):
    rows = answers((saved(), saved("failed", "r2")))
    if phase == "count": config = {"max_records": 1}
    else:
        config = {}
        ceiling = rows[1][1] - 1 if phase == "claim_bytes" else rows[1][1] + rows[2][1] - 1
        monkeypatch.setattr(inv.db, "MAX_READ_BYTES", ceiling)
    connection = FakeConnection(rows); install(monkeypatch, connection)
    with pytest.raises(inv.db.ResearchCaptureConflict, match="inventory_limit"):
        inv.load_execution_inventory_with_psycopg(DSN, **config)
    assert not any("SELECT record_id," in q or "SELECT a.record_id," in q for q, _ in connection.calls)
    assert connection.events[-2:] == ["rollback", "closed"]


def test_exact_count_and_combined_byte_limits_are_allowed(monkeypatch):
    rows = answers((saved(),))
    monkeypatch.setattr(inv.db, "MAX_READ_BYTES", rows[1][1] + rows[2][1])
    assert len(load(monkeypatch, rows, max_records=1)[0].executions) == 1


@pytest.mark.parametrize("where", (1, 2))
def test_future_aggregate_receipt_blocks_instead_of_hiding_rows(monkeypatch, where):
    rows = answers((saved(),)); n, size, _ = rows[where]
    rows[where] = (n, size, AT + timedelta(microseconds=1))
    connection = FakeConnection(rows); install(monkeypatch, connection)
    with pytest.raises(inv.db.ResearchCaptureConflict, match="future_record"):
        inv.load_execution_inventory_with_psycopg(DSN)
    assert not any("SELECT record_id," in q for q, _ in connection.calls)


@pytest.mark.parametrize("broken", ((0,1,None), (0,0,AT), (1,0,AT), (1,1,None), (True,1,AT), (1,-1,AT)))
def test_invalid_aggregate_shape_cannot_become_empty_success(monkeypatch, broken):
    rows = answers((saved(),)); rows[1] = broken
    connection = FakeConnection(rows); install(monkeypatch, connection)
    with pytest.raises(RuntimeError, match="research_capture_database_failed"):
        inv.load_execution_inventory_with_psycopg(DSN)


@pytest.mark.parametrize("defect", ("missing_claim", "missing_record", "claim_bytes", "record_bytes", "duplicate_claim",
    "duplicate_record", "foreign_record", "claim_hash", "record_hash", "record_flags", "claim_scope", "record_binding"))
def test_inconsistent_or_corrupt_snapshot_never_returns_partial_success(monkeypatch, defect):
    rows = answers((saved(), saved("failed", "r2")))
    if defect == "missing_claim": rows[4].pop()
    elif defect == "missing_record": rows[5].pop()
    elif defect == "duplicate_claim": rows[4][1] = rows[4][0]
    elif defect == "duplicate_record": rows[5][1] = rows[5][0]
    elif defect == "foreign_record": rows[5][0] = record_row(saved(rid="xx"))
    elif defect == "claim_bytes": rows[1] = (2, rows[1][1]+1, rows[1][2])
    elif defect == "record_bytes": rows[2] = (2, rows[2][1]+1, rows[2][2])
    else:
        index = 4 if defect.startswith("claim") else 5
        row = list(rows[index][0])
        if defect.endswith("hash"): row[10] = "0"*64
        elif defect == "record_flags": row[11] = False
        elif defect == "claim_scope": row[2] = "foreign-market"
        elif defect == "record_binding":
            other = saved(rid="r1", team="crypto_btc"); row = list(record_row(other))
        rows[index][0] = tuple(row)
    connection = FakeConnection(rows); install(monkeypatch, connection)
    with pytest.raises(RuntimeError, match="research_capture_database_failed"):
        inv.load_execution_inventory_with_psycopg(DSN)
    assert connection.events[-2:] == ["rollback", "closed"]


@pytest.mark.parametrize("changed", ({"executions":[]}, {"executions":(object(),)}, {"unclaimed_attempt_count":True},
    {"unclaimed_attempt_count":-1}, {"generated_at":NOW.replace(tzinfo=None)}))
def test_invalid_inventory(changed):
    args = dict(generated_at=AT, executions=(saved(),)); args.update(changed)
    with pytest.raises(ValueError): inv.ResearchExecutionInventory(**args)


@pytest.mark.parametrize("kind", ("captured", "capture_failed", "duplicate", "too_many", "future_claim", "future_record"))
def test_inventory_rejects_live_receipts_and_wrong_inventory(kind):
    item = saved("incomplete" if kind == "future_claim" else "completed")
    if kind == "captured": items = (replace(item, status="captured"),)
    elif kind == "capture_failed": items = (replace(state(item.request), status="capture_failed", pending_run=item.record.run),)
    elif kind == "duplicate": items = (item, item)
    elif kind == "too_many": items = (item,) * (inv.MAX_CLAIMS+1)
    elif kind == "future_claim": items = (replace(item, claimed_at=AT+timedelta(microseconds=1)),)
    else: items = (replace(item, record=replace(item.record, recorded_at=AT+timedelta(microseconds=1))),)
    with pytest.raises(ValueError): inv.ResearchExecutionInventory(AT, items)


def test_output_revalidation_immutability_and_equivalent_timezone():
    item = saved(); report = inv.ResearchExecutionInventory(AT, (item,))
    assert report.executions[0] is not item
    original = report.to_dict()
    different = replace(report, generated_at=AT.astimezone(timezone(timedelta(hours=8))))
    assert different.to_dict() == original
    original["executions"][0]["limits"]["max_model_calls"] = 999
    assert report.to_dict() != original
    object.__setattr__(report.executions[0].request.intake.source_receipts[0], "content_sha256", "0"*64)
    with pytest.raises(ValueError): report.to_dict()


def test_cleanup_error_does_not_publish_a_success(monkeypatch):
    connection = FakeConnection(answers((saved(),)), commit_error=True); install(monkeypatch, connection)
    with pytest.raises(RuntimeError, match="research_capture_database_failed"):
        inv.load_execution_inventory_with_psycopg(DSN)


def test_managed_session_passes_binding_and_refuses_use_after_close(monkeypatch):
    from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
    from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
    from polymarket_alpha_lab.project_postgres import binding
    events = []
    class Database:
        def _dsn(self, identity): events.append(identity); return "private-managed"
    session = ProjectResearchSession(Database(), dict(instance_id="a"*32, root_sha256="b"*64, system_identifier="1"))
    def load(dsn, **config):
        assert dsn == "private-managed" and config == {"max_records": 4}
        events.append("called"); return inv.ResearchExecutionInventory(AT, ())
    monkeypatch.setattr(inv, "load_execution_inventory_with_psycopg", load)
    assert session.execution_inventory(max_records=4).executions == ()
    assert len(events) == 2
    session.close()
    with pytest.raises(ProjectDatabaseError): session.execution_inventory()
    assert len(events) == 2
