"""Opt-in proof on a fresh dedicated loopback PostgreSQL database, never user data.

Uses the already-validated test connector. Applies two migrations only after
asserting the dedicated test DB name and absent research_capture schema.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from os import environ
from pathlib import Path
from threading import Event, Lock
from uuid import uuid4

import pytest

from polymarket_alpha_lab import research_execution_psycopg as runner
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from tests.test_research_execution import Model
from tests.test_research_capture_codec import make_run
from tests.test_research_capture_disposable import _connect, DSN_ENV, DB_NAME
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn

GATE="POLYMARKET_ALPHA_LAB_RUN_RESEARCH_EXECUTION_DISPOSABLE_DB"


def test_real_claim_then_execute_concurrency_recovery_and_complete_history(monkeypatch):
    if environ.get(GATE)!="1":pytest.skip(f"set {GATE}=1 for isolated execution proof")
    dsn=environ.get(DSN_ENV)
    if not dsn:pytest.fail("explicit local disposable DSN required")
    validate_local_postgres_dsn(dsn,env_var_name=DSN_ENV)
    import psycopg
    with _connect(dsn) as conn:
        assert conn.execute("SELECT current_database(),to_regnamespace('research_capture')").fetchone()==(DB_NAME,None)
    root=Path(__file__).resolve().parents[1]
    for name in ("20260912000000_research_evaluation_capture.sql","20260912010000_research_execution_claims.sql"):
        with _connect(dsn) as conn:conn.execute((root/"supabase/migrations"/name).read_text(encoding="utf-8"))

    def now():
        with _connect(dsn) as conn:return conn.execute("SELECT clock_timestamp()").fetchone()[0]

    tag=uuid4().hex[:12]
    def request(suffix,status="completed"):
        stamp=now(); condition=tag+suffix
        run=make_run(condition,condition,now=stamp,status=status)
        return CapturedResearchRequest(condition,"synthetic-model","v1",stamp+timedelta(minutes=5),run.intake,
                                      required_source_ids=() if status=="intake_blocked" else ("s",))

    req=request("-concurrent");started=Event();release=Event();lock=Lock();factory_calls=[]
    def factory(team):
        with lock:factory_calls.append(team)
        # Independent readers/writers must work here: there is no open claim
        # transaction spanning model execution, and the claim is already durable.
        assert runner.inspect_captured_research_with_psycopg(dsn,record_id=req.record_id).status=="incomplete"
        started.set()
        assert release.wait(timeout=20)
        return Model()
    with ThreadPoolExecutor(max_workers=4) as pool:
        first=pool.submit(runner.run_captured_research_with_psycopg,dsn,request=req,model_factory=factory)
        assert started.wait(timeout=20)
        repeats=[pool.submit(runner.run_captured_research_with_psycopg,dsn,request=req,model_factory=factory) for _ in range(7)]
        try:
            assert all(f.result(timeout=20).status=="incomplete" for f in repeats)
        finally:release.set()
        saved=first.result(timeout=20)
    assert factory_calls==[req.intake.team_id] and saved.status=="captured"
    assert saved.claimed_at<=saved.record.recorded_at
    again=runner.run_captured_research_with_psycopg(dsn,request=req,model_factory=factory)
    assert again.status=="already_captured" and again.record==saved.record and len(factory_calls)==1
    with _connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM research_capture.execution_claims").fetchone()[0]==1
        assert conn.execute("SELECT count(*) FROM research_capture.attempts").fetchone()[0]==1
    with pytest.raises(runner.db.ResearchCaptureConflict):
        runner.run_captured_research_with_psycopg(dsn,request=replace(req,model_id="changed"),model_factory=factory)
    with pytest.raises(runner.db.ResearchCaptureConflict):
        runner.run_captured_research_with_psycopg(dsn,request=replace(req,record_id=tag+"-renamed"),model_factory=factory)

    # Normal failure/blocked inputs are stored, not discarded or endlessly retried.
    failed_req=request("-model-failed")
    class FailingModel:
        def complete(self,**kw):raise RuntimeError("SYNTHETIC-PRIVATE-ERROR")
    failed=runner.run_captured_research_with_psycopg(dsn,request=failed_req,model_factory=lambda _:FailingModel())
    assert failed.status=="captured" and failed.record.run.research.status=="failed"
    blocked_req=request("-blocked",status="intake_blocked")
    blocked=runner.run_captured_research_with_psycopg(dsn,request=blocked_req,
        model_factory=lambda _:pytest.fail("blocked intake must not construct model"))
    assert blocked.record.run.intake.status=="blocked"

    # Saving failure preserves the original in-memory run for capture-only retry.
    pending_req=request("-save-failed"); model=Model()
    original_capture=runner.db.capture_research_with_psycopg
    with monkeypatch.context() as patch:
        def unavailable(*args,**kwargs):raise RuntimeError("SYNTHETIC-PRIVATE-DB")
        patch.setattr(runner.db,"capture_research_with_psycopg",unavailable)
        pending=runner.run_captured_research_with_psycopg(dsn,request=pending_req,model_factory=lambda _:model)
    assert pending.status=="capture_failed" and pending.record is None and model.calls==2
    with pytest.raises(runner.db.ResearchCaptureConflict,match="history_incomplete"):
        runner.load_captured_research_evaluation_with_psycopg(dsn)
    # Minting a new task/record ID is not an automatic crash-recovery path.
    new_task=make_run(pending_req.intake.condition_id,tag+"-new-task",now=now()).intake
    changed_request=replace(pending_req,record_id=tag+"-new-record",intake=new_task)
    with pytest.raises(runner.db.ResearchCaptureConflict,match="prior_incomplete"):
        runner.run_captured_research_with_psycopg(dsn,request=changed_request,
            model_factory=lambda _:pytest.fail("new ID must not bypass unfinished research"))
    # The database itself protects the claimed input even via the old API.
    tampered=make_run(pending_req.intake.condition_id,pending_req.intake.task_id,now=now())
    with pytest.raises(RuntimeError,match="database_failed"):
        original_capture(dsn,record_id=pending_req.record_id,model_id=pending_req.model_id,
                         protocol_version=pending_req.protocol_version,run=tampered)
    with _connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM research_capture.attempts WHERE record_id=%s",(pending_req.record_id,)).fetchone()[0]==0
    recovered=runner.retry_research_capture_with_psycopg(dsn,request=pending.request,run=pending.pending_run)
    assert recovered.status=="captured" and recovered.record.run==pending.pending_run and model.calls==2
    assert runner.retry_research_capture_with_psycopg(dsn,request=pending.request,run=pending.pending_run).record==recovered.record
    report=runner.load_captured_research_evaluation_with_psycopg(dsn)
    assert len(report.records)==4 and report.groups[0].failed_or_blocked_count==2
    assert report.groups[0].outcome_pending_count==2
    # At the claim time the result was still unavailable. Historical completeness
    # must not be rewritten by the later successful recovery.
    with pytest.raises(runner.db.ResearchCaptureConflict,match="history_incomplete"):
        runner.load_captured_research_evaluation_with_psycopg(dsn,generated_at=pending.claimed_at)

    # A post-INSERT validation error rolls the claim AND new market back; no model.
    rollback_req=request("-rollback")
    with monkeypatch.context() as patch:
        patch.setattr(runner,"_claim_row",lambda _:(_ for _ in ()).throw(ValueError("bad readback")))
        with pytest.raises(RuntimeError,match="database_failed"):
            runner.run_captured_research_with_psycopg(dsn,request=rollback_req,model_factory=lambda _:pytest.fail("no model"))
    with _connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM research_capture.execution_claims WHERE record_id=%s",(rollback_req.record_id,)).fetchone()[0]==0
        assert conn.execute("SELECT count(*) FROM research_capture.markets WHERE condition_id=%s",(rollback_req.intake.condition_id,)).fetchone()[0]==0

    # Claims cannot be overwritten, cleared, or recycled after a lost execution.
    for sql in ("UPDATE research_capture.execution_claims SET readonly=false",
                "DELETE FROM research_capture.execution_claims","TRUNCATE research_capture.execution_claims"):
        with pytest.raises(psycopg.Error):
            with _connect(dsn) as conn:conn.execute(sql)
    crash_req=request("-crash")
    with monkeypatch.context() as patch:
        def interrupted(*args):raise KeyboardInterrupt()
        patch.setattr(runner,"_execute",interrupted)
        with pytest.raises(KeyboardInterrupt):
            runner.run_captured_research_with_psycopg(dsn,request=crash_req,model_factory=lambda _:Model())
    repeated=runner.run_captured_research_with_psycopg(dsn,request=crash_req,
        model_factory=lambda _:pytest.fail("incomplete claim must not restart"))
    assert repeated.status=="incomplete"
    with pytest.raises(runner.db.ResearchCaptureConflict,match="history_incomplete"):
        runner.load_captured_research_evaluation_with_psycopg(dsn)
    print("real local PostgreSQL execution proof: 8 concurrent submissions/1 loop start, committed claim before model, replay, failures, capture-only recovery, atomic rollback, immutable claims and incomplete-history guard; synthetic model only")
