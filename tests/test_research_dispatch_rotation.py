"""Fair durable turns with synthetic snapshots and no model/DB/network service."""
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab import research_dispatch_rotation as core
from polymarket_alpha_lab import research_dispatch_rotation_store as store
from polymarket_alpha_lab import research_dispatch_rotation_runner as runner
from polymarket_alpha_lab.research_dispatch import ResearchBatch, StoredResearchBatch, ResearchBatchSnapshot
from tests.test_research_dispatch import req, receipt, NOW, Cursor, state


def inputs(lengths=(2, 2), histories=None):
    snaps = []
    for b, n in enumerate(lengths):
        batch = ResearchBatch('batch-'+str(b), tuple(req(10*b+p,
            team='crypto_btc' if b%2 else 'crypto_eth') for p in range(n)))
        executions = tuple(None if histories is None else histories.get(r.record_id) for r in batch.requests)
        snaps.append(ResearchBatchSnapshot(StoredResearchBatch(batch, NOW), NOW+timedelta(seconds=5), executions))
    return tuple(snaps)


def turn(*, start=0, number=1, turn_id='t1', lengths=(2, 2), max_tasks=1, states=None):
    roster, at, found, requests = core.roster_inputs(inputs(lengths))
    return core.ResearchRotationTurn('rotation', turn_id, number, roster, at,
        found if states is None else states, tuple((r.record_id,r.content_sha256) for r in requests),
        start, max_tasks, 1)


def saved(t=None):
    return core.StoredResearchRotationTurn(turn() if t is None else t, NOW+timedelta(seconds=6))


def row(t=None):
    s=saved(t);t=s.turn
    return (t.rotation_id,t.turn_id,t.turn_number,t.start_slot,t.next_slot,t.roster_sha256,
            t.payload,t.content_sha256,s.reserved_at,True,True,True)


def test_interleaved_slots_unequal_batches_and_exact_wire():
    t=turn(lengths=(3,1,2),max_tasks=4)
    assert core.slots(t.roster)==((0,0),(1,0),(2,0),(0,1),(2,1),(0,2))
    assert t.chosen==(0,1,2,3) and t.next_slot==4
    assert core.decode_turn(t.payload,t.content_sha256)==t
    assert 'Synthetic' not in json.dumps(saved(t).to_dict())


@pytest.mark.parametrize('start',[0,1,2,3])
@pytest.mark.parametrize('cap',[1,2,3,4,100])
def test_cyclic_selection_visits_each_slot_at_most_once(start,cap):
    t=replace(turn(),start_slot=start,max_tasks=cap)
    expect=tuple((start+i)%4 for i in range(min(cap,4)))
    assert t.chosen==expect and t.next_slot==(start+len(expect))%4


def test_selection_skips_all_nonpending_and_does_not_drop_uncertainty():
    t=turn(states=('incomplete','expired','captured','pending'))
    assert t.chosen==(3,) and t.next_slot==0
    t=replace(t,states=('incomplete','expired','captured','incomplete'))
    assert not t.chosen and t.next_slot==0


@pytest.mark.parametrize('change',[{'roster':[]},{'states':('pending',)}, {'observed_at':()},
    {'max_tasks':True},{'max_workers':9},{'start_slot':4},{'turn_number':0},
    {'request_keys':()}, {'readonly':False},{'paper_only':1},{'report_only':None}])
def test_invalid_turn_never_reaches_storage(change):
    with pytest.raises(ValueError):replace(turn(),**change)


@pytest.mark.parametrize('defect',['hash','noncanonical','extra','flag','unknown_state','list_member','duplicate_id'])
def test_decode_fail_closed(defect):
    t=turn();data=json.loads(t.payload)
    if defect=='extra':data['private']='not-exported'
    if defect=='flag':data['readonly']=False
    if defect=='unknown_state':data['states'][0]='reclaimed'
    if defect=='list_member':data['roster'][0]='not-array'
    if defect=='duplicate_id':data['request_keys'][1]=data['request_keys'][0]
    raw=core._dump(data)+ ('\n' if defect=='noncanonical' else '')
    digest='0'*64 if defect=='hash' else sha256(raw.encode()).hexdigest()
    with pytest.raises(ValueError,match='payload_invalid'):core.decode_turn(raw,digest)


def test_roster_duplicate_across_batches_and_aggregate_limit(monkeypatch):
    a=inputs((1,))[0];b=replace(a,stored=StoredResearchBatch(replace(a.stored.batch,batch_id='other'),NOW))
    with pytest.raises(ValueError,match='duplicate_request'):core.roster_inputs((a,b))
    with pytest.raises(ValueError,match='input_limit'):core.roster_inputs(inputs((51,50)))
    monkeypatch.setattr(core,'MAX_BATCH_BYTES',1)
    with pytest.raises(ValueError,match='input_limit'):core.roster_inputs((a,))


def test_captured_and_incomplete_snapshots_keep_original_identity():
    requests=inputs((1,1));r=requests[0].stored.batch.requests[0];r2=requests[1].stored.batch.requests[0]
    histories={r.record_id:replace(receipt(r),status='already_captured'),r2.record_id:state(r2)}
    roster,at,states,got=core.roster_inputs(inputs((1,1),histories))
    assert states==('captured','incomplete') and got[0]==r and got[1]==r2


class Harness:
    def __init__(self,monkeypatch):
        self.history={};self.saved={};self.calls=[];self.fail={'q-0'};self.after_reserve=None
        monkeypatch.setattr(runner,'inspect_research_turn_with_psycopg',lambda dsn,**k:self.saved.get(k['turn_id']))
        monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda dsn,*,batch_id:
            next(s for s in inputs(histories=self.history) if s.stored.batch.batch_id==batch_id))
        monkeypatch.setattr(runner,'_reserve',self.reserve)
        monkeypatch.setattr(runner.drain,'run_captured_research_with_psycopg',self.execute)
    def reserve(self,dsn,**k):
        previous=list(self.saved.values())[-1] if self.saved else None
        t=core.ResearchRotationTurn(k['rotation_id'],k['turn_id'],len(self.saved)+1,k['roster'],
            k['observed_at'],k['states'],k['request_keys'],0 if previous is None else previous.turn.next_slot,
            k['max_tasks'],k['max_workers'])
        s=saved(t);self.saved[k['turn_id']]=s
        if self.after_reserve:self.after_reserve()
        return True,s
    def execute(self,dsn,*,request,model_factory):
        self.calls.append(request.record_id)
        if request.record_id in self.fail:raise RuntimeError('private-db-detail')
        model_factory(request.intake.team_id)
        r=receipt(request);self.history[request.record_id]=replace(r,status='already_captured')
        return r


def run(turn_id='t1',**kw):
    return runner.run_research_rotation_with_psycopg('fake',rotation_id='rotation',turn_id=turn_id,
        batch_ids_to_run=('batch-0','batch-1'),model_factory=lambda _:None,allow_model_calls=True,
        max_tasks=kw.pop('max_tasks',1),max_workers=kw.pop('max_workers',1),**kw)


def test_durable_cursor_moves_past_persistent_unclaimed_failure(monkeypatch):
    h=Harness(monkeypatch)
    reports=[run('t'+str(i)) for i in range(1,6)]
    assert h.calls==['q-0','q-10','q-1','q-11','q-0']
    assert [r.stored.turn.next_slot for r in reports]==[1,2,3,0,1]
    assert reports[0].attempts[0].status=='operation_failed'
    assert 'private-db-detail' not in json.dumps(reports[0].to_dict())


def test_same_turn_replay_does_not_load_batches_or_execute(monkeypatch):
    h=Harness(monkeypatch);original=run()
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:pytest.fail('replay refetch'))
    repeat=run()
    assert repeat.stored==original.stored and repeat.status=='turn_already_reserved'
    assert repeat.to_dict()['execution_invocations']==0 and h.calls==['q-0']
    with pytest.raises(store.db.ResearchCaptureConflict):run(max_tasks=2)


def test_stop_before_reserve_touches_no_database(monkeypatch):
    h=Harness(monkeypatch);control=runner.drain.ResearchDispatchStop();control.request_stop()
    monkeypatch.setattr(runner,'inspect_research_turn_with_psycopg',lambda *a,**k:pytest.fail('DB reached'))
    out=run(stop=control).to_dict()
    assert not h.calls and not h.saved and out['cursor_written_here'] is False


def test_stop_after_reserve_keeps_cursor_and_does_not_start_work(monkeypatch):
    h=Harness(monkeypatch);control=runner.drain.ResearchDispatchStop();h.after_reserve=control.request_stop
    a=run(stop=control);assert a.stored.turn.next_slot==1 and not a.attempts and not h.calls
    h.after_reserve=None
    assert run('t2').attempts[0].execution.request.record_id=='q-10'


def test_selection_wrap_order_not_numeric_sort(monkeypatch):
    h=Harness(monkeypatch);h.fail=set();run('t1',max_tasks=3)
    # Repopulate unclaimed hints to probe a cyclic [3,0] selection independently.
    h.history.clear();out=run('t2',max_tasks=2)
    assert [a.position for a in out.attempts]==[3,0]
    assert [a.execution.request.record_id for a in out.attempts]==['q-11','q-0']


def test_incomplete_never_reclaimed_in_new_turn(monkeypatch):
    h=Harness(monkeypatch);r=inputs()[0].stored.batch.requests[0];h.history[r.record_id]=state(r)
    run('t1',max_tasks=4);run('t2',max_tasks=4)
    assert 'q-0' not in h.calls and h.history[r.record_id].status=='incomplete'


def test_commit_failure_or_malformed_input_never_reaches_model(monkeypatch):
    h=Harness(monkeypatch)
    monkeypatch.setattr(runner,'_reserve',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('uncertain commit')))
    with pytest.raises(RuntimeError):run()
    assert not h.calls
    monkeypatch.setattr(runner,'load_research_batch_with_psycopg',lambda *a,**k:object())
    with pytest.raises(ValueError,match='batch_not_found'):run()
    assert not h.calls


def test_receipt_report_rejects_foreign_execution(monkeypatch):
    h=Harness(monkeypatch);h.fail=set();out=run()
    foreign=replace(out.attempts[0],execution=receipt(req(55)))
    with pytest.raises(ValueError,match='binding_invalid'):replace(out,attempts=(foreign,))
    with pytest.raises(ValueError):replace(out,attempts=())


def test_reservation_recheck_race_returns_no_execution(monkeypatch):
    h=Harness(monkeypatch)
    monkeypatch.setattr(runner,'_reserve',lambda *a,**k:(False,saved()))
    out=run();assert out.status=='turn_already_reserved' and not h.calls


def reserve_args(t):
    return dict(rotation_id=t.rotation_id,turn_id=t.turn_id,roster=t.roster,observed_at=t.observed_at,
        states=t.states,request_keys=t.request_keys,max_tasks=t.max_tasks,max_workers=t.max_workers)


def tx(monkeypatch,cur):
    seen=[]
    def operation(dsn,fn,*,readonly=False):seen.append(readonly);return fn(cur)
    monkeypatch.setattr(store.db,'_local_transaction',operation)
    return seen


def test_real_store_first_turn_uses_one_locked_transaction(monkeypatch):
    t=turn();cur=Cursor([None,None,None,row(t)]);seen=tx(monkeypatch,cur)
    owned,s=store._reserve('fake',**reserve_args(t))
    assert owned and s==saved(t) and seen==[False]
    assert 'pg_advisory_xact_lock' in cur.calls[0][0]
    assert 'INSERT INTO research_capture.dispatch_turns' in cur.calls[-1][0]


def test_real_store_next_turn_and_idempotent_receipt(monkeypatch):
    a=turn();b=turn(number=2,start=1,turn_id='t2')
    cur=Cursor([None,None,(len(a.payload),),row(a),row(b)]);tx(monkeypatch,cur)
    assert store._reserve('fake',**reserve_args(b))==(True,saved(b))
    cur=Cursor([None,(len(a.payload),),row(a)]);tx(monkeypatch,cur)
    assert store._reserve('fake',**reserve_args(a))==(False,saved(a))
    assert all('INSERT' not in q for q,_ in cur.calls)


def test_store_rejects_changed_roster_and_read_limit(monkeypatch):
    a=turn();b=turn(lengths=(1,1))
    cur=Cursor([None,None,(len(a.payload),),row(a)]);tx(monkeypatch,cur)
    with pytest.raises(store.db.ResearchCaptureConflict,match='roster_conflict'):
        store._reserve('fake',**reserve_args(b))
    cur=Cursor([(core.MAX_TURN_BYTES+1,)]);seen=tx(monkeypatch,cur)
    with pytest.raises(store.db.ResearchCaptureConflict,match='payload_limit'):
        store.inspect_research_turn_with_psycopg('fake',rotation_id='r',turn_id='t')
    assert seen==[True]


@pytest.mark.parametrize('index,value',[(2,True),(3,99),(4,99),(5,'0'*64),(9,False),(10,1),(11,None)])
def test_corrupt_database_mirror_rejected(index,value):
    values=list(row());values[index]=value
    with pytest.raises(ValueError):store._row(tuple(values))


def test_lookup_cannot_return_a_different_requested_identity(monkeypatch):
    t=turn();cur=Cursor([(len(t.payload),),row(t)]);tx(monkeypatch,cur)
    with pytest.raises(ValueError,match='lookup_mismatch'):
        store.inspect_research_turn_with_psycopg('fake',rotation_id='other',turn_id='t1')


@pytest.mark.parametrize('kwargs',[{'allow_model_calls':False},{'allow_model_calls':1},{'max_tasks':0},
    {'max_workers':True},{'batch_ids_to_run':[]},{'batch_ids_to_run':('x','x')},
    {'turn_id':'with space'},{'rotation_id':''},{'stop':object()}])
def test_invalid_operator_configuration_precedes_database(monkeypatch,kwargs):
    monkeypatch.setattr(runner,'inspect_research_turn_with_psycopg',lambda *a,**k:pytest.fail('DB reached'))
    args=dict(rotation_id='r',turn_id='t',batch_ids_to_run=('x',),model_factory=lambda _:None,
              allow_model_calls=True,max_tasks=1,max_workers=1)
    args.update(kwargs)
    with pytest.raises(ValueError):runner.run_research_rotation_with_psycopg('fake',**args)


def test_managed_rotation_methods_bind_identity_and_expire(monkeypatch):
    from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
    from polymarket_alpha_lab.project_postgres import binding,files
    class DB:
        def _dsn(self,_):return 'managed'
    session=ProjectResearchSession(DB(),dict(instance_id='a'*32,root_sha256='b'*64,system_identifier='123'))
    observed=[]
    def op(dsn,**kw):observed.append((dsn,binding._EXPECTED.get(),kw));return 'ok'
    monkeypatch.setattr(runner,'run_research_rotation_with_psycopg',op)
    monkeypatch.setattr(store,'inspect_research_turn_with_psycopg',op)
    assert session.run_research_rotation(rotation_id='r',turn_id='t')=='ok'
    assert session.inspect_research_turn(rotation_id='r',turn_id='t')=='ok'
    assert all(item[1]==('a'*32,'b'*64,'123') for item in observed)
    assert binding._EXPECTED.get() is None
    session.close()
    with pytest.raises(files.ProjectDatabaseError):session.run_research_rotation(rotation_id='r',turn_id='t')


def test_default_disabled_and_remote_dsn_do_not_open_external_db():
    with pytest.raises(ValueError):runner.run_research_rotation_with_psycopg('postgresql://u@192.0.2.1/db',
        rotation_id='r',turn_id='t',batch_ids_to_run=('b',),model_factory=lambda _:None)
    with pytest.raises(ValueError):store.inspect_research_turn_with_psycopg('postgresql://u@192.0.2.1/db',
        rotation_id='r',turn_id='t')
