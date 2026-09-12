"""Driver call/transaction contracts using scripted cursor responses, no DB."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import sys
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab.research_capture_codec import encode_research_capture, payload_sha256
from tests.test_research_capture_codec import NOW, make_run

DSN = "postgresql://fixture@localhost:54322/postgres"


def market_row():
    return ("fixture", "market-fixture", NOW+timedelta(hours=1), NOW-timedelta(seconds=1), True, True, True)


def record_row(run=None):
    run = run or make_run()
    body = encode_research_capture(record_id="r1", model_id="m", protocol_version="v1", run=run)
    i = run.intake
    return ("r1", i.condition_id, i.market_slug, i.team_id, "m", "v1", i.task_id, i.as_of,
            NOW+timedelta(seconds=1), body, payload_sha256(body), True, True, True)


def outcome_row():
    return ("fixture", "market-fixture", NOW+timedelta(hours=1), NOW+timedelta(hours=2),
            NOW+timedelta(hours=3), True, "synthetic:confirmed", "a"*64, True, True, True)


class FakeConnection:
    def __init__(self, answers=(), error=None, commit_error=False):
        self.answers = iter(answers)
        self.calls = []
        self.events = []
        self.error = error
        self.commit_error = commit_error
    def __enter__(self):
        self.events.append("opened")
        return self
    def __exit__(self, typ, value, tb):
        self.events.append("rollback" if typ else "commit")
        self.events.append("closed")
        if self.commit_error: raise RuntimeError("SYNTHETIC-PRIVATE-COMMIT")
    def cursor(self):
        outer = self
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *args): outer.events.append("cursor_closed")
            def execute(self, sql, params=None):
                outer.calls.append((sql,params))
                if outer.error: raise outer.error
            def fetchone(self): return next(outer.answers)
            def fetchall(self): return next(outer.answers)
        return Cursor()


def install(monkeypatch, connection):
    calls=[]
    def connect(dsn, **kwargs):
        calls.append((dsn,kwargs))
        return connection
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))
    return calls


def capture(**changes):
    args = dict(record_id="r1", model_id="m", protocol_version="v1", run=make_run())
    args.update(changes)
    return db.capture_research_with_psycopg(DSN, **args)


def confirm(**changes):
    args = dict(condition_id="fixture", market_slug="market-fixture", resolved_at=NOW+timedelta(hours=2),
                actual_yes=True, source_reference="synthetic:confirmed", source_content_sha256="a"*64)
    args.update(changes)
    return db.capture_research_outcome_with_psycopg(DSN, **args)


def test_capture_commits_with_database_time_and_bound_parameters(monkeypatch):
    conn=FakeConnection((market_row(), None, record_row()))
    calls=install(monkeypatch,conn)
    result=capture()
    assert result.recorded_at==record_row()[8]
    assert conn.events==["opened","cursor_closed","commit","closed"]
    assert calls==[(DSN,{"connect_timeout":5})]
    insert=[(q,p) for q,p in conn.calls if q.startswith("INSERT")][0]
    assert "recorded_at" not in insert[0].split("RETURNING")[0]
    assert "SYNTHETIC-PRIVATE" not in insert[0]
    assert insert[1][-1]==payload_sha256(insert[1][-2])
    assert conn.calls[0][0].endswith("READ COMMITTED READ WRITE")
    assert any("pg_advisory_xact_lock" in q for q,p in conn.calls)


def test_identical_retry_reads_original_without_insert(monkeypatch):
    conn=FakeConnection((market_row(), record_row()))
    install(monkeypatch,conn)
    assert capture().recorded_at==record_row()[8]
    assert not any(q.startswith("INSERT") for q,p in conn.calls)


def test_content_conflict_rolls_back_and_never_overwrites(monkeypatch):
    conn=FakeConnection((market_row(), record_row()))
    install(monkeypatch,conn)
    with pytest.raises(db.ResearchCaptureConflict, match="research_record_conflict"):
        capture(model_id="other")
    assert conn.events[-2:]==["rollback","closed"]
    assert not any(q.startswith(("INSERT","UPDATE","DELETE")) for q,p in conn.calls)


def test_missing_registration_blocks_capture(monkeypatch):
    conn=FakeConnection((None,));install(monkeypatch,conn)
    with pytest.raises(db.ResearchCaptureConflict, match="not_registered"):capture()
    assert not any(q.startswith("INSERT") for q,p in conn.calls)


@pytest.mark.parametrize("exists",(False,True))
def test_register_exact_retry_works_even_after_cutoff(monkeypatch,exists):
    conn=FakeConnection((market_row(),) if exists else (None,market_row()));install(monkeypatch,conn)
    result=db.register_research_market_with_psycopg(DSN,condition_id="fixture",market_slug="market-fixture",
                                                   forecast_cutoff_at=market_row()[2])
    assert result.registered_at==market_row()[3]
    assert sum(q.startswith("INSERT") for q,p in conn.calls)==int(not exists)


def test_changed_registered_cutoff_is_conflict(monkeypatch):
    conn=FakeConnection((market_row(),));install(monkeypatch,conn)
    with pytest.raises(db.ResearchCaptureConflict):
        db.register_research_market_with_psycopg(DSN,condition_id="fixture",market_slug="market-fixture",
                                               forecast_cutoff_at=NOW+timedelta(days=1))


@pytest.mark.parametrize("exists",(False,True))
def test_outcome_uses_preregistered_cutoff_and_database_time(monkeypatch,exists):
    conn=FakeConnection((market_row(),outcome_row()) if exists else (market_row(),None,outcome_row()))
    install(monkeypatch,conn)
    result=confirm()
    assert result.forecast_cutoff_at==market_row()[2] and result.recorded_at==outcome_row()[4]
    for q,p in conn.calls:
        if q.startswith("INSERT"):
            assert "forecast_cutoff_at" not in q.split("RETURNING")[0]
            assert "recorded_at" not in q.split("RETURNING")[0]


def test_changed_outcome_cannot_replace_original(monkeypatch):
    conn=FakeConnection((market_row(),outcome_row()));install(monkeypatch,conn)
    with pytest.raises(db.ResearchCaptureConflict):confirm(actual_yes=False)
    assert conn.events[-2:]==["rollback","closed"]


@pytest.mark.parametrize("kind",("capture","register","outcome","read"))
def test_remote_dsn_is_rejected_before_driver_connect(monkeypatch,kind):
    conn=FakeConnection();calls=install(monkeypatch,conn)
    dsn="postgresql://fixture@remote.invalid/postgres"
    with pytest.raises(ValueError):
        if kind=="capture":db.capture_research_with_psycopg(dsn,record_id="r",model_id="m",protocol_version="v",run=make_run())
        elif kind=="register":db.register_research_market_with_psycopg(dsn,condition_id="fixture",market_slug="market-fixture",forecast_cutoff_at=NOW)
        elif kind=="outcome":db.capture_research_outcome_with_psycopg(dsn,condition_id="fixture",market_slug="market-fixture",resolved_at=NOW,actual_yes=True,source_reference="synthetic:x",source_content_sha256="a"*64)
        else:db.load_research_evaluation_with_psycopg(dsn)
    assert calls==[]


@pytest.mark.parametrize("error",(RuntimeError("SYNTHETIC-PRIVATE-SQL"),ValueError("SYNTHETIC-PRIVATE-PAYLOAD")))
def test_driver_failure_redacted_and_rolled_back(monkeypatch,error,capsys):
    conn=FakeConnection(error=error);install(monkeypatch,conn)
    with pytest.raises(RuntimeError,match="^research_capture_database_failed$") as exc:capture()
    assert exc.value.__suppress_context__ is True
    assert conn.events[-2:]==["rollback","closed"]
    assert capsys.readouterr()==("","")


def test_commit_failure_never_returns_success(monkeypatch):
    conn=FakeConnection((market_row(),None,record_row()),commit_error=True);install(monkeypatch,conn)
    with pytest.raises(RuntimeError,match="database_failed"):capture()


def test_cancel_rolls_back_closes_and_propagates(monkeypatch):
    conn=FakeConnection(error=KeyboardInterrupt());install(monkeypatch,conn)
    with pytest.raises(KeyboardInterrupt):capture()
    assert conn.events[-2:]==["rollback","closed"]


def test_consistent_full_history_readback_scores_and_omits_raw_text(monkeypatch):
    conn=FakeConnection(((NOW+timedelta(hours=4),),(1,5000),(1,),[record_row()],[outcome_row()]))
    install(monkeypatch,conn)
    report=db.load_research_evaluation_with_psycopg(DSN)
    assert report.groups[0].scores.mean_brier_score==Decimal("0.09")
    assert conn.calls[0][0].endswith("REPEATABLE READ READ ONLY")
    assert "SYNTHETIC-PRIVATE" not in str(report.to_dict())
    assert all("status=" not in q and "LIMIT" not in q for q,p in conn.calls)


@pytest.mark.parametrize("counts",((10001,100,0),(1,33554433,0),(1,1,10001)))
def test_no_partial_scoring_after_history_limits(monkeypatch,counts):
    n,size,outcomes=counts
    conn=FakeConnection(((NOW+timedelta(days=1),),(n,size),(outcomes,)));install(monkeypatch,conn)
    with pytest.raises(db.ResearchCaptureConflict,match="history_limit"):
        db.load_research_evaluation_with_psycopg(DSN)
    assert not any("SELECT record_id" in q for q,p in conn.calls)


def test_future_evaluation_not_allowed(monkeypatch):
    conn=FakeConnection(((NOW,),));install(monkeypatch,conn)
    with pytest.raises(db.ResearchCaptureConflict,match="from_future"):
        db.load_research_evaluation_with_psycopg(DSN,generated_at=NOW+timedelta(seconds=1))


@pytest.mark.parametrize("index,value",((0,"changed"),(2,"wrong-market"),(3,"crypto_btc"),(10,"0"*64),(11,1)))
def test_corrupt_stored_rows_are_not_scored(monkeypatch,index,value):
    row=list(record_row());row[index]=value
    conn=FakeConnection(((NOW+timedelta(hours=4),),(1,100),(0,),[tuple(row)]));install(monkeypatch,conn)
    with pytest.raises(RuntimeError,match="database_failed"):
        db.load_research_evaluation_with_psycopg(DSN)


@pytest.mark.parametrize("kwargs",({"max_records":True},{"max_records":10001},{"bucket_count":0},{"generated_at":NOW.replace(tzinfo=None)}))
def test_invalid_read_parameters_prevent_connect(monkeypatch,kwargs):
    calls=install(monkeypatch,FakeConnection())
    with pytest.raises(ValueError):db.load_research_evaluation_with_psycopg(DSN,**kwargs)
    assert calls==[]


def test_invalid_write_parameters_prevent_connect(monkeypatch):
    calls=install(monkeypatch,FakeConnection())
    with pytest.raises(ValueError):capture(record_id="bad id")
    with pytest.raises(ValueError):confirm(actual_yes=1)
    with pytest.raises(ValueError):confirm(source_content_sha256="not-a-hash")
    assert calls==[]
