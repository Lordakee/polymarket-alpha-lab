"""Durable batch contracts and dispatch scheduling with no DB/network/model API."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from dataclasses import replace
from datetime import timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from threading import Event, Lock

import pytest

from polymarket_alpha_lab import research_dispatch as core
from polymarket_alpha_lab import research_dispatch_runner as runner
from polymarket_alpha_lab import research_dispatch_store as store
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from tests.test_research_execution import request, state, record_for
from tests.test_research_capture_codec import make_run, NOW


def req(n=0, *, team='crypto_eth', now=NOW, **kw):
    return request(record_id='q-'+str(n), intake=make_run(condition='condition-'+str(n),
        task='task-'+str(n), team=team, now=now).intake,
        forecast_cutoff_at=now+timedelta(hours=1), **kw)


def batch(n=3, **kw):
    return core.ResearchBatch('batch-1', tuple(req(i, team='crypto_btc' if i%2 else 'crypto_eth') for i in range(n)), **kw)


def snapshot(n=3, *, at=NOW+timedelta(seconds=1), executions=None):
    b=batch(n)
    return core.ResearchBatchSnapshot(core.StoredResearchBatch(b, NOW), at,
        (None,)*n if executions is None else executions)


def receipt(r):
    run=make_run(condition=r.intake.condition_id, task=r.intake.task_id, team=r.intake.team_id)
    return CapturedResearchExecution(r, NOW+timedelta(seconds=1), 'captured', record_for(r,run))


def test_exact_canonical_roundtrip_copy_and_redacted_views():
    b=batch();raw=b.payload;restored=core.decode_batch(raw,b.content_sha256)
    assert restored==b and restored is not b and restored.requests[0] is not b.requests[0]
    assert 'SYNTHETIC-PRIVATE' not in repr(restored)
    s=snapshot();out=s.to_dict()
    assert out['state_counts']==dict(pending=3,expired=0,incomplete=0,captured=0)
    assert 'SYNTHETIC-PRIVATE' not in json.dumps(out)
    assert out['model_called'] is out['database_written'] is out['automatic_reclaim_permitted'] is False
    assert core.copy_batch(b).payload==raw
    object.__setattr__(b.requests[0].intake.task.evidence[0],'readonly',False)
    with pytest.raises(ValueError):core.copy_batch(b)


@pytest.mark.parametrize('value',[[],(),(object(),),(req(),)*101])
def test_batch_rejects_invalid_inputs(value):
    with pytest.raises(ValueError):core.ResearchBatch('b',value)


@pytest.mark.parametrize('flag',['paper_only','report_only','readonly'])
@pytest.mark.parametrize('value',[False,1,None])
def test_batch_flags_are_strict(flag,value):
    with pytest.raises(ValueError):batch(**{flag:value})


def test_duplicate_record_and_logical_task_and_other_team_block():
    r=req()
    with pytest.raises(ValueError):core.ResearchBatch('b',(r,r))
    with pytest.raises(ValueError):core.ResearchBatch('b',(r,replace(r,record_id='another')))
    with pytest.raises(ValueError):core.ResearchBatch('b',(req(team='politics'),))


@pytest.mark.parametrize('defect',['hash','extra','missing','request_type','version','noncanonical','false'])
def test_corrupt_batch_decode(defect):
    b=batch();data=json.loads(b.payload)
    if defect=='extra':data['unknown']=0
    elif defect=='missing':del data['batch_id']
    elif defect=='request_type':data['requests'][0]={}
    elif defect=='version':data['schema_version']='bad'
    elif defect=='false':data['readonly']=False
    raw=json.dumps(data,sort_keys=True,separators=(',',':'))
    if defect=='noncanonical':raw+='\n'
    digest='0'*64 if defect=='hash' else sha256(raw.encode()).hexdigest()
    with pytest.raises(ValueError):core.decode_batch(raw,digest)


def test_payload_bound_precedes_db(monkeypatch):
    monkeypatch.setattr(core,'MAX_BATCH_BYTES',1)
    with pytest.raises(ValueError,match='too_large'):batch()


@pytest.mark.parametrize('offset,ok',[(-1,False),(0,True),(300,True),(301,False),(3600,False)])
def test_enqueue_time_and_selection_age_boundary(offset,ok):
    at=NOW+timedelta(seconds=offset)
    assert core.startable(req(),at)==ok
    if ok:core.StoredResearchBatch(batch(),at)
    else:
        with pytest.raises(ValueError):core.StoredResearchBatch(batch(),at)


def test_snapshot_mixed_states_and_timezone_identity():
    b=batch(4);done=replace(receipt(b.requests[0]),status='already_captured')
    held=state(b.requests[1])
    s=core.ResearchBatchSnapshot(core.StoredResearchBatch(b,NOW),NOW+timedelta(seconds=301),(done,held,None,None))
    assert s.states()==('captured','incomplete','expired','expired')
    out=s.to_dict()
    assert out['items'][1]['worker_liveness']=='unknown'
    assert out['items'][2]['execution'] is None
    shifted=replace(s,generated_at=s.generated_at.astimezone(timezone(timedelta(hours=8))))
    assert shifted.to_dict()==out


@pytest.mark.parametrize('change',[{'executions':()}, {'executions':[]}, {'generated_at':NOW-timedelta(seconds=1)},
                                  {'executions':(object(),)*3}])
def test_snapshot_rejects_incomplete_or_wrong_data(change):
    with pytest.raises(ValueError):replace(snapshot(),**change)


def test_snapshot_foreign_receipt_and_mutation_rejected():
    with pytest.raises(ValueError):replace(snapshot(),executions=(state(req(8)),None,None))
    s=snapshot();object.__setattr__(s.stored.batch.requests[0],'readonly',False)
    with pytest.raises(ValueError):s.to_dict()


def batch_row(b=None):
    b=b or batch()
    return (b.batch_id,len(b.requests),NOW,b.payload,b.content_sha256,True,True,True)


class Cursor:
    def __init__(self,answers):self.answers=list(answers);self.calls=[]
    def execute(self,q,args=()):self.calls.append((q,args));self.result=self.answers.pop(0)
    def fetchone(self):return self.result


def transaction(monkeypatch,cursor):
    seen=[]
    def call(dsn,operation,*,readonly=False):
        seen.append((dsn,readonly));return operation(cursor)
    monkeypatch.setattr(store.db,'_local_transaction',call)
    return seen


def test_new_enqueue_atomic_time_then_insert_and_no_claim(monkeypatch):
    b=batch();c=Cursor([None,None,(NOW,),batch_row(b)]);seen=transaction(monkeypatch,c)
    saved=store.enqueue_research_batch_with_psycopg('fake',batch=b,allow_queue_write=True)
    assert saved.batch==b and seen==[('fake',False)] and not c.answers
    assert sum('INSERT INTO' in q for q,_ in c.calls)==1
    assert all('INSERT INTO research_capture.markets' not in q and 'execution_claims' not in q for q,_ in c.calls)


def test_enqueue_replay_keeps_original_receipt_and_refuses_changed_content(monkeypatch):
    b=batch();c=Cursor([None,(len(b.payload),),batch_row(b)]);transaction(monkeypatch,c)
    assert store.enqueue_research_batch_with_psycopg('fake',batch=b,allow_queue_write=True).enqueued_at==NOW
    assert all('INSERT ' not in q for q,_ in c.calls)
    c=Cursor([None,(len(b.payload),),batch_row(b)]);transaction(monkeypatch,c)
    with pytest.raises(store.db.ResearchCaptureConflict,match='identity_conflict'):
        store.enqueue_research_batch_with_psycopg('fake',batch=batch(2),allow_queue_write=True)


@pytest.mark.parametrize('value',[False,1,None,'yes'])
def test_queue_optin_before_connection(monkeypatch,value):
    monkeypatch.setattr(store.db,'_local_transaction',lambda *a,**k:pytest.fail('DB reached'))
    with pytest.raises(ValueError):store.enqueue_research_batch_with_psycopg('fake',batch=batch(),allow_queue_write=value)


def test_expired_admission_does_not_insert(monkeypatch):
    c=Cursor([None,None,(NOW+timedelta(seconds=301),)]);transaction(monkeypatch,c)
    with pytest.raises(store.db.ResearchCaptureConflict,match='not_startable'):
        store.enqueue_research_batch_with_psycopg('fake',batch=batch(),allow_queue_write=True)
    assert all('INSERT ' not in q for q,_ in c.calls)


def test_read_uses_readonly_snapshot_and_original_decoder(monkeypatch):
    b=batch();c=Cursor([(NOW+timedelta(seconds=2),),(len(b.payload),),batch_row(b),(0,)]);seen=transaction(monkeypatch,c)
    ids=[]
    monkeypatch.setattr(store.execution,'_lookup',lambda cur,rid:ids.append(rid))
    s=store.load_research_batch_with_psycopg('fake',batch_id=b.batch_id)
    assert seen==[('fake',True)] and s.states()==('pending',)*3
    assert ids==[r.record_id for r in b.requests] and 'sum(octet_length' in c.calls[-1][0]


def test_unknown_batch_and_oversize_read(monkeypatch):
    c=Cursor([(NOW,),None]);transaction(monkeypatch,c)
    assert store.load_research_batch_with_psycopg('fake',batch_id='unknown') is None
    c=Cursor([(NOW,),(core.MAX_BATCH_BYTES+1,)]);transaction(monkeypatch,c)
    with pytest.raises(store.db.ResearchCaptureConflict,match='payload_limit'):
        store.load_research_batch_with_psycopg('fake',batch_id='b')
    b=batch();c=Cursor([(NOW,),(len(b.payload),),batch_row(b),(store.db.MAX_READ_BYTES+1,)])
    transaction(monkeypatch,c)
    with pytest.raises(store.db.ResearchCaptureConflict,match='execution_payload_limit'):
        store.load_research_batch_with_psycopg('fake',batch_id='batch-1')


def test_remote_dsn_refused_by_existing_validator():
    with pytest.raises(ValueError):store.load_research_batch_with_psycopg('postgresql://u@192.0.2.1/db',batch_id='b')


@pytest.fixture
def worker(monkeypatch):
    calls=[]
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:snapshot())
    def execute(dsn,*,request,model_factory):calls.append(request.record_id);return receipt(request)
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',execute)
    return calls


def dispatch(**kw):
    return runner.run_research_batch_with_psycopg('fake',batch_id='batch-1',model_factory=lambda _:None,
        allow_model_calls=True,**kw)


@pytest.mark.parametrize('kw',[{'max_workers':0},{'max_workers':9},{'max_workers':True},{'max_tasks':0},
                              {'max_tasks':101},{'stop':object()}])
def test_invalid_dispatch_before_db(monkeypatch,kw):
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:pytest.fail('DB reached'))
    with pytest.raises(ValueError):dispatch(**kw)


@pytest.mark.parametrize('enabled',[False,1,None,'yes'])
def test_model_optin_before_db(monkeypatch,enabled):
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:pytest.fail('DB reached'))
    with pytest.raises(ValueError):runner.run_research_batch_with_psycopg('x',batch_id='b',model_factory=lambda _:None,allow_model_calls=enabled)


def test_fifo_bounded_dispatch_has_ordered_receipts(worker):
    result=dispatch(max_workers=1,max_tasks=2)
    assert worker==['q-0','q-1']
    out=result.to_dict()
    assert out['execution_invocations']==2 and out['not_invoked_pending_count']==1
    assert [r['record_id'] for r in out['attempts']]==worker
    assert out['final_database_state_checked'] is out['hard_money_cap_enforced'] is False
    assert 'SYNTHETIC-PRIVATE' not in json.dumps(out) and 'SYNTHETIC-PRIVATE' not in repr(result)


def test_stopped_before_start_no_pool_or_execute(worker,monkeypatch):
    control=runner.ResearchDispatchStop();control.request_stop()
    monkeypatch.setattr(runner,'ThreadPoolExecutor',lambda *a,**k:pytest.fail('pool reached'))
    out=dispatch(stop=control).to_dict()
    assert worker==[] and out['execution_invocations']==0 and out['not_invoked_pending_count']==3


def test_stop_after_first_keeps_remaining_pending(worker,monkeypatch):
    control=runner.ResearchDispatchStop()
    def execute(dsn,*,request,model_factory):
        worker.append(request.record_id);control.request_stop();return receipt(request)
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',execute)
    report=dispatch(stop=control,max_workers=1)
    assert worker==['q-0'] and report.to_dict()['not_invoked_pending_count']==2


def test_existing_incomplete_and_captured_are_not_executed(worker,monkeypatch):
    b=batch();s=snapshot(executions=(state(b.requests[0]),replace(receipt(b.requests[1]),status='already_captured'),None),
                       at=NOW+timedelta(seconds=3))
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:s)
    out=dispatch().to_dict()
    assert worker==['q-2'] and out['execution_invocations']==1


def test_expired_queue_never_creates_pool(worker,monkeypatch):
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:snapshot(at=NOW+timedelta(seconds=301)))
    monkeypatch.setattr(runner,'ThreadPoolExecutor',lambda *a,**k:pytest.fail('expired pool'))
    assert dispatch().attempts==() and worker==[]


def test_partial_operation_failure_is_retained_without_retry(worker,monkeypatch):
    def execute(dsn,*,request,model_factory):
        worker.append(request.record_id)
        if request.record_id=='q-0':raise RuntimeError('private-detail')
        return receipt(request)
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',execute)
    out=dispatch(max_workers=1).to_dict()
    assert worker==['q-0','q-1','q-2'] and out['operation_failure_count']==1
    assert 'private-detail' not in json.dumps(out)


def test_capture_failed_keeps_original_pending_run_in_memory(worker,monkeypatch):
    r=batch().requests[0];run=make_run(condition=r.intake.condition_id,task=r.intake.task_id,team=r.intake.team_id)
    failed=CapturedResearchExecution(r,NOW+timedelta(seconds=1),'capture_failed',pending_run=run)
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',lambda *a,**k:failed)
    out=dispatch(max_tasks=1)
    assert out.attempts[0].execution.pending_run==run
    assert out.to_dict()['attempts'][0]['execution']['record_sha256'] is None


def test_two_workers_inherit_separate_contexts_and_bound_concurrency(monkeypatch):
    marker=ContextVar('dispatch-test',default=None);token=marker.set('original')
    first=Event();second=Event();lock=Lock();active=0;peak=0;calls=[]
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:snapshot(4))
    def execute(dsn,*,request,model_factory):
        nonlocal active,peak
        assert marker.get()=='original';marker.set(request.record_id)
        with lock:active+=1;peak=max(peak,active);calls.append(request.record_id)
        if request.record_id=='q-0':
            first.set();assert second.wait(5)
        elif request.record_id=='q-1':
            assert first.wait(5);second.set()
        with lock:active-=1
        return receipt(request)
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',execute)
    try:
        report=dispatch(max_workers=2)
        assert marker.get()=='original' and peak==2 and len(calls)==4
        assert [a.position for a in report.attempts]==[0,1,2,3]
    finally:marker.reset(token)


def test_keyboard_interrupt_requests_stop_and_propagates(worker,monkeypatch):
    control=runner.ResearchDispatchStop()
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',lambda *a,**k:(_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):dispatch(max_workers=1,stop=control)
    assert control.is_stopped()


def test_wrong_receipt_and_missing_batch_never_false_success(worker,monkeypatch):
    monkeypatch.setattr(runner,'run_captured_research_with_psycopg',lambda *a,**k:receipt(req(8)))
    assert dispatch(max_tasks=1).attempts[0].status=='operation_failed'
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:None)
    with pytest.raises(ValueError,match='not_found'):dispatch()


@pytest.mark.parametrize('change',[{'attempts':()}, {'max_workers':True}, {'stop_requested':1},
    {'attempts':(runner.DispatchAttempt(2,'operation_failed'),)}, {'attempts':[]}])
def test_fabricated_report_is_rejected(worker,change):
    report=dispatch(max_workers=1)
    with pytest.raises(ValueError):replace(report,**change)


def test_closed_managed_session_and_binding(monkeypatch):
    from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
    from polymarket_alpha_lab.project_postgres import binding,files
    seen=[]
    class DB:
        def _dsn(self,_):return 'managed'
    session=ProjectResearchSession(DB(),dict(instance_id='a'*32,root_sha256='b'*64,system_identifier='123'))
    def op(dsn,**kw):seen.append(binding._EXPECTED.get());return 'ok'
    monkeypatch.setattr(store,'enqueue_research_batch_with_psycopg',op)
    monkeypatch.setattr(store,'load_research_batch_with_psycopg',op)
    monkeypatch.setattr(runner,'run_research_batch_with_psycopg',op)
    assert session.enqueue_research_batch(batch=batch(),allow_queue_write=True)=='ok'
    assert session.inspect_research_batch(batch_id='b')=='ok'
    assert session.run_research_batch(batch_id='b')=='ok'
    assert all(x==('a'*32,'b'*64,'123') for x in seen) and binding._EXPECTED.get() is None
    session.close()
    with pytest.raises(files.ProjectDatabaseError):session.run_research_batch(batch_id='b')


def test_migration_tail_hashes_and_no_lease_or_destructive_ddl():
    root=Path(__file__).resolve().parents[1]
    entries=json.loads((root/'database/migrations.lock.json').read_text())['migrations']
    assert len(entries)==66
    entry=entries[63];assert entry['name']=='20260914000000_research_dispatch_batches.sql'
    sql=(root/'supabase/migrations'/entry['name']).read_bytes()
    assert entry['sha256']==sha256(sql).hexdigest()
    assert 'reject_mutation' in sql.decode() and 'security definer' not in sql.decode().lower()
    assert 'create table research_capture.dispatch_batches' in sql.decode()
