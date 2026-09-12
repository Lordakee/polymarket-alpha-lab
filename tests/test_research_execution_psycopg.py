"""Local DSN/short-transaction/claim contracts with fake native cursor replies."""
from dataclasses import replace
from datetime import timedelta

import pytest

from polymarket_alpha_lab import research_execution_psycopg as runner
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from tests.test_research_execution import NOW, Model, request, record_for
from tests.test_research_capture_codec import make_run
from tests.test_research_capture_psycopg import DSN, FakeConnection, install, market_row
from polymarket_alpha_lab.research_capture_codec import encode_research_capture,payload_sha256


def claim_row(req=None,at=NOW+timedelta(seconds=1)):
    req=req or request();i=req.intake
    return (req.record_id,i.condition_id,i.market_slug,i.team_id,req.model_id,req.protocol_version,
            i.task_id,i.as_of,at,req.payload,req.content_sha256,True,True,True)


def record_row(req,run=None):
    run=run or make_run();i=run.intake
    payload=encode_research_capture(record_id=req.record_id,model_id=req.model_id,protocol_version=req.protocol_version,run=run)
    return (req.record_id,i.condition_id,i.market_slug,i.team_id,req.model_id,req.protocol_version,
            i.task_id,i.as_of,NOW+timedelta(seconds=2),payload,payload_sha256(payload),True,True,True)


@pytest.mark.parametrize("market_exists",(True,False))
def test_new_claim_commits_and_has_no_caller_timestamp(monkeypatch,market_exists):
    req=request();answers=[None,None,None,None]
    answers+= [market_row()] if market_exists else [None,market_row()]
    answers += [(NOW+timedelta(seconds=1),),claim_row(req)]
    conn=FakeConnection(answers);calls=install(monkeypatch,conn)
    owned,result=runner._claim(DSN,req)
    assert owned and result.status=="incomplete"
    assert conn.events[-2:]==["commit","closed"] and calls==[(DSN,{"connect_timeout":5})]
    insert=[(q,p) for q,p in conn.calls if q.startswith("INSERT INTO research_capture.execution_claims")][0]
    assert "claimed_at" not in insert[0].split("RETURNING")[0]
    assert insert[1][-2:]==(req.payload,req.content_sha256)


@pytest.mark.parametrize("captured",(False,True))
def test_claim_replay_only_reads_under_lock(monkeypatch,captured):
    req=request();conn=FakeConnection((claim_row(req),record_row(req) if captured else None))
    install(monkeypatch,conn)
    owned,result=runner._claim(DSN,req)
    assert not owned and result.status==("already_captured" if captured else "incomplete")
    assert not any(q.startswith(("INSERT","UPDATE","DELETE")) for q,p in conn.calls)


@pytest.mark.parametrize("kind",("request","task","legacy","market"))
def test_conflicts_prevent_model_and_do_not_overwrite(monkeypatch,kind):
    req=request()
    answers={"request":(claim_row(replace(req,model_id="other")),None),
             "task":(None,("other",)),"legacy":(None,None,("r1",)),
             "market":(None,None,None,None,("fixture","market-fixture",NOW+timedelta(hours=2),NOW-timedelta(seconds=1),True,True,True))}[kind]
    conn=FakeConnection(answers);install(monkeypatch,conn)
    def forbidden(_):pytest.fail("no model on conflict")
    with pytest.raises(runner.db.ResearchCaptureConflict):runner.run_captured_research_with_psycopg(DSN,request=req,model_factory=forbidden)
    assert conn.events[-2:]==["rollback","closed"]


@pytest.mark.parametrize("delta",(-1,301,3600))
def test_future_stale_and_postcutoff_requests_do_not_start(monkeypatch,delta):
    req=request();conn=FakeConnection((None,None,None,None,market_row(),(NOW+timedelta(seconds=delta),)))
    install(monkeypatch,conn)
    with pytest.raises(runner.db.ResearchCaptureConflict,match="not_startable"):
        runner.run_captured_research_with_psycopg(DSN,request=req,model_factory=lambda _:pytest.fail("must not start"))
    assert not any(q.startswith("INSERT INTO research_capture.execution_claims") for q,p in conn.calls)


def test_uncertain_claim_commit_never_starts_model(monkeypatch):
    req=request();conn=FakeConnection((None,None,None,None,market_row(),(NOW+timedelta(seconds=1),),claim_row(req)),commit_error=True)
    install(monkeypatch,conn)
    with pytest.raises(RuntimeError,match="database_failed") as err:
        runner.run_captured_research_with_psycopg(DSN,request=req,model_factory=lambda _:pytest.fail("must not start"))
    assert "SYNTHETIC-PRIVATE" not in str(err.value)


@pytest.mark.parametrize("operation",("run","inspect","retry","evaluate"))
def test_remote_dsn_rejected_before_driver_or_model(monkeypatch,operation):
    conn=FakeConnection();calls=install(monkeypatch,conn);req=request()
    bad="postgresql://fixture@remote.invalid/postgres"
    ops=dict(run=lambda:runner.run_captured_research_with_psycopg(bad,request=req,model_factory=lambda _:pytest.fail("no model")),
             inspect=lambda:runner.inspect_captured_research_with_psycopg(bad,record_id="r1"),
             retry=lambda:runner.retry_research_capture_with_psycopg(bad,request=req,run=make_run()),
             evaluate=lambda:runner.load_captured_research_evaluation_with_psycopg(bad))
    with pytest.raises(ValueError):ops[operation]()
    assert calls==[]


def test_inspect_missing_is_readonly_without_writes(monkeypatch):
    conn=FakeConnection((None,));install(monkeypatch,conn)
    assert runner.inspect_captured_research_with_psycopg(DSN,record_id="r1") is None
    assert conn.calls[0][0].endswith("REPEATABLE READ READ ONLY")


@pytest.mark.parametrize("index,value",((0,"wrong-id"),(8,NOW-timedelta(seconds=1)),(10,"0"*64),(11,False)))
def test_claim_row_corruption_is_rejected(index,value):
    row=list(claim_row());row[index]=value
    with pytest.raises(ValueError):runner._claim_row(tuple(row))


def test_incomplete_execution_blocks_before_loading_payloads(monkeypatch):
    conn=FakeConnection(((NOW,), (1,)));install(monkeypatch,conn)
    with pytest.raises(runner.db.ResearchCaptureConflict,match="history_incomplete"):
        runner.load_captured_research_evaluation_with_psycopg(DSN)
    assert any("LEFT JOIN research_capture.attempts" in q and p==(NOW,NOW) for q,p in conn.calls)
    assert not any("ORDER BY record_id" in q for q,p in conn.calls)


def test_complete_execution_history_uses_existing_evaluator(monkeypatch):
    conn=FakeConnection(((NOW,), (0,), (0,0),(0,),[],[]));install(monkeypatch,conn)
    result=runner.load_captured_research_evaluation_with_psycopg(DSN)
    assert result.records==() and result.groups==()
    assert conn.events[-2:]==["commit","closed"]


@pytest.mark.parametrize("flag",(None,1,"true"))
def test_guard_flag_requires_exact_bool_before_connection(monkeypatch,flag):
    calls=install(monkeypatch,FakeConnection())
    with pytest.raises(ValueError):runner.db.load_research_evaluation_with_psycopg(DSN,require_execution_complete=flag)
    assert calls==[]


def test_new_task_cannot_bypass_unfinished_attempt_in_same_cohort(monkeypatch):
    req=request();conn=FakeConnection((None,None,None,("original-unfinished-record",)))
    install(monkeypatch,conn)
    with pytest.raises(runner.db.ResearchCaptureConflict,match="prior_incomplete"):
        runner.run_captured_research_with_psycopg(DSN,request=req,model_factory=lambda _:pytest.fail("no model"))
