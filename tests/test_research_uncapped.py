"""Explicit no-monetary-cap permission and original claims; synthetic I/O only."""
from dataclasses import replace
from datetime import timedelta, timezone
from hashlib import sha256
import json
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

import pytest

from polymarket_alpha_lab import research_uncapped as core
from polymarket_alpha_lab import research_uncapped_runner as runner
from polymarket_alpha_lab import research_dispatch_runner as dispatch
from polymarket_alpha_lab import research_dispatch_rotation_runner as rotation
from polymarket_alpha_lab.research_dispatch import ResearchBatch, StoredResearchBatch, ResearchBatchSnapshot
from tests.test_research_model_budget import req
from tests.test_research_execution import NOW, Model, state, record_for
from tests.test_research_dispatch_rotation import Harness as RotationHarness, inputs, run as run_turn


def approval(requests=None, **kw):
    requests = (req(), req(1)) if requests is None else requests
    values = dict(authorization_id='approved-no-cap', model_id='synthetic-model',
                  adapter_contract_sha256='a'*64, approved_at=NOW,
                  expires_at=NOW+timedelta(minutes=30),
                  request_keys=tuple((r.record_id, r.content_sha256) for r in requests),
                  no_monetary_cap_approved=True, research_data_send_approved=True)
    values.update(kw)
    return core.UncappedResearchAuthorization(**values)


class Harness:
    def __init__(self, monkeypatch):
        self.claims, self.events, self.lock = {}, [], Lock()
        monkeypatch.setattr(runner, '_now', lambda: NOW+timedelta(seconds=3))
        monkeypatch.setattr(runner.execution, '_claim', self.claim)
        monkeypatch.setattr(runner.execution, '_capture', self.capture)
        monkeypatch.setattr(runner.execution, 'inspect_captured_research_with_psycopg', self.inspect)

    def claim(self, dsn, request):
        with self.lock:
            prior = self.claims.get(request.record_id)
            if prior is not None:
                assert prior.request.payload == request.payload
                self.events.append('replay')
                return False, prior
            self.events.append('claim')
            value = state(request)
            self.claims[request.record_id] = value
            return True, value

    def capture(self, dsn, value, run):
        self.events.append('capture')
        result = replace(value, status='captured', record=record_for(value.request, run))
        self.claims[value.request.record_id] = result
        return result

    def inspect(self, dsn, *, record_id):
        self.events.append('inspect')
        return self.claims.get(record_id)

    def factory(self, team):
        self.events.append('factory')
        model = Model()
        events = self.events
        class Client:
            def complete(self, **kw):
                events.append('complete')
                return model.complete(**kw)
        return Client()


def run(h, *, request=None, authorization=None, **kw):
    r = req() if request is None else request
    return runner.run_uncapped_research_with_psycopg('synthetic', request=r,
        authorization=approval((r,)) if authorization is None else authorization,
        model_factory=kw.pop('model_factory', h.factory),
        allow_model_calls=kw.pop('allow_model_calls', True),
        allow_uncapped_costs=kw.pop('allow_uncapped_costs', True), **kw)


def test_canonical_roundtrip_and_unknown_not_zero():
    p = approval()
    copied = core.decode_authorization(p.payload, p.content_sha256)
    assert copied == p and copied is not p
    assert copied.bind_request(req()).payload == req().payload
    metadata = copied.to_dict()
    assert metadata['monetary_cap'] is metadata['actual_billed_micros'] is None
    assert metadata['provider_charge_bound_verified'] is False
    assert metadata['durable_authorization_record_created'] is False
    assert 'total_micros' not in p.payload and 'per_call_micros' not in p.payload
    assert 'SYNTHETIC-PRIVATE' not in repr(p) + json.dumps(metadata)


@pytest.mark.parametrize('field,value', [
    ('authorization_id', ''), ('authorization_id', 'bad value'), ('model_id', ''),
    ('adapter_contract_sha256', 'x'*64), ('adapter_contract_sha256', 'a'*63),
    ('approved_at', NOW.replace(tzinfo=None)), ('approved_at', NOW+timedelta(hours=1)),
    ('expires_at', NOW), ('expires_at', NOW.replace(tzinfo=None)),
    ('request_keys', []), ('request_keys', ()), ('request_keys', (('r','a'*64),('r','b'*64))),
    ('request_keys', (['r','a'*64],)), ('request_keys', (('r','z'*64),)),
    ('request_keys', tuple((f'r{i}','a'*64) for i in range(101))),
    ('no_monetary_cap_approved', False), ('no_monetary_cap_approved', 1),
    ('research_data_send_approved', False), ('research_data_send_approved', 'yes'),
    ('paper_only', False), ('report_only', 1), ('readonly', None),
])
def test_authorization_rejects_invalid_fields(field, value):
    with pytest.raises(ValueError): approval(**{field:value})


@pytest.mark.parametrize('defect', ['unknown','missing','missing_flag','version','hash','whitespace',
                                   'duplicate','array','request_member','wrong_time','surrogate'])
def test_closed_codec_rejects_corruption(defect):
    p = approval(); data = json.loads(p.payload)
    if defect=='unknown': data['extra'] = 'PRIVATE-SENTINEL'
    if defect=='missing': data.pop('model_id')
    if defect=='missing_flag': data.pop('readonly')
    if defect=='version': data['schema_version'] = 'v2'
    if defect=='array': data=[]
    if defect=='request_member': data['request_keys'][0] = 'bad'
    if defect=='wrong_time': data['approved_at'] = 'bad'
    if defect=='surrogate': data['model_id'] = '\ud800'
    raw=json.dumps(data,sort_keys=True,separators=(',',':'))
    if defect=='whitespace': raw+='\n'
    if defect=='duplicate': raw='{"model_id":"PRIVATE-SENTINEL",'+raw[1:]
    checksum='0'*64 if defect=='hash' else sha256(raw.encode()).hexdigest()
    with pytest.raises(ValueError, match='payload_invalid') as error: core.decode_authorization(raw, checksum)
    assert 'PRIVATE-SENTINEL' not in str(error.value)


def test_timezone_normalization_and_snapshot_revalidation():
    p=approval(); zone=timezone(timedelta(hours=8))
    assert replace(p,approved_at=p.approved_at.astimezone(zone),expires_at=p.expires_at.astimezone(zone)).payload==p.payload
    object.__setattr__(p,'no_monetary_cap_approved',False)
    with pytest.raises(ValueError): core.copy_authorization(p)


@pytest.mark.parametrize('change', [dict(model_id='other'),dict(max_start_delay_seconds=1),dict(record_id='other')])
def test_original_request_hash_is_not_rewritten(change):
    with pytest.raises(ValueError,match='request_mismatch'): approval().bind_request(replace(req(),**change))


@pytest.mark.parametrize('number',[0,1])
def test_original_claim_and_success_replay_without_budget(monkeypatch,number):
    h=Harness(monkeypatch); r=req(number); original=r.payload
    out=run(h,request=r)
    assert h.events==['claim','factory','complete','complete','capture']
    assert out.record.run.research.status=='completed'
    assert out.record.run.research.total_tokens==4
    assert out.request.payload==r.payload==original
    assert run(h,request=r)==out
    assert h.events[-1]=='replay' and h.events.count('complete')==2


@pytest.mark.parametrize('flag,value', [(f,v) for f in ('allow_model_calls','allow_uncapped_costs') for v in (False,1,None,'yes')])
def test_double_optin_before_database(monkeypatch,flag,value):
    h=Harness(monkeypatch)
    with pytest.raises(ValueError): run(h,**{flag:value})
    assert not h.events


@pytest.mark.parametrize('when',[NOW-timedelta(seconds=1),NOW+timedelta(minutes=30)])
def test_inactive_authorization_no_new_claim_but_exact_history_readable(monkeypatch,when):
    h=Harness(monkeypatch); original=run(h); h.events.clear()
    monkeypatch.setattr(runner,'_now',lambda:when)
    assert run(h)==original and h.events==['inspect']
    h.events.clear(); h.claims.clear()
    with pytest.raises(ValueError,match='not_available'): run(h)
    assert h.events==['inspect']


def test_incomplete_never_reclaimed_under_new_authorization(monkeypatch):
    h=Harness(monkeypatch); h.claims[req().record_id]=state(req())
    out=run(h,authorization=approval(authorization_id='another-explicit-approval'))
    assert out.status=='incomplete' and h.events==['replay']


def test_mutating_caller_authorization_does_not_change_active_permission(monkeypatch):
    h=Harness(monkeypatch); p=approval(); r=req()
    def factory(team):
        object.__setattr__(p,'expires_at',NOW-timedelta(seconds=1))
        object.__setattr__(r,'model_id','changed-after-validation')
        return h.factory(team)
    out=run(h,request=r,authorization=p,model_factory=factory)
    assert out.record.run.research.status=='completed'
    assert out.request.model_id=='synthetic-model'


@pytest.mark.parametrize('exception',[RuntimeError('PRIVATE-SENTINEL'),SystemExit(0),KeyboardInterrupt()])
def test_provider_failure_is_not_retried_or_reclaimed(monkeypatch,exception):
    h=Harness(monkeypatch); seen=[]
    class Bad:
        def complete(self,**kw): seen.append(True); raise exception
    if isinstance(exception,Exception):
        out=run(h,model_factory=lambda _:Bad())
        assert out.record.run.research.reason_code=='model_failed'
        assert 'PRIVATE-SENTINEL' not in repr(out)
    else:
        with pytest.raises(type(exception)): run(h,model_factory=lambda _:Bad())
    assert seen==[True]
    run(h,model_factory=lambda _:pytest.fail('replayed model'))
    assert seen==[True]


def test_expiry_after_factory_is_rechecked_before_provider(monkeypatch):
    h=Harness(monkeypatch)
    def factory(team):
        monkeypatch.setattr(runner,'_now',lambda:approval().expires_at)
        return h.factory(team)
    out=run(h,model_factory=factory)
    assert out.record.run.research.reason_code=='model_failed'
    assert 'complete' not in h.events


def test_stop_between_model_calls_keeps_first_attempt_and_original_claim(monkeypatch):
    h=Harness(monkeypatch); stop=dispatch.ResearchDispatchStop(); model=Model(); calls=[]
    class Client:
        def complete(self,**kw):
            calls.append(True); reply=model.complete(**kw); stop.request_stop(); return reply
    out=run(h,model_factory=lambda _:Client(),stop=stop)
    assert out.record.run.research.reason_code=='model_failed' and calls==[True]
    assert run(h,stop=stop)==out and calls==[True]


def test_invalid_mandatory_evidence_uses_zero_call_capture(monkeypatch):
    from tests.test_research_required_evidence import mixed_request
    h=Harness(monkeypatch); r=mixed_request(0)
    out=run(h,request=r)
    assert out.record.run.research.reason_code=='invalid_citations'
    assert out.record.run.research.model_calls==0 and h.events==['claim','capture']


def test_parallel_same_request_has_only_one_loop_start(monkeypatch):
    h=Harness(monkeypatch)
    with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(lambda _:run(h),range(8)))
    assert len(results)==8 and h.events.count('claim')==1 and h.events.count('complete')==2


@pytest.mark.parametrize('mode', ['batch','rotation'])
@pytest.mark.parametrize('changes',[dict(allow_uncapped_costs=False),dict(allow_uncapped_costs=1),
    dict(model_budget_id='b'),dict(uncapped_authorization=None),dict(uncapped_authorization=object())])
def test_ambiguous_modes_reject_before_database(monkeypatch,mode,changes):
    h=Harness(monkeypatch)
    monkeypatch.setattr(dispatch,'load_research_batch_with_psycopg',lambda *a,**k:pytest.fail('DB entered'))
    monkeypatch.setattr(rotation,'inspect_research_turn_with_psycopg',lambda *a,**k:pytest.fail('DB entered'))
    args=dict(model_factory=h.factory,allow_model_calls=True,uncapped_authorization=approval(),allow_uncapped_costs=True)
    args.update(changes)
    with pytest.raises(ValueError):
        if mode=='batch': dispatch.run_research_batch_with_psycopg('fake',batch_id='b',**args)
        else: rotation.run_research_rotation_with_psycopg('fake',rotation_id='r',turn_id='t',batch_ids_to_run=('b',),**args)


def test_batch_runs_two_teams_with_no_monetary_reservation(monkeypatch):
    h=Harness(monkeypatch); requests=(req(),req(1)); batch=ResearchBatch('b',requests)
    snap=ResearchBatchSnapshot(StoredResearchBatch(batch,NOW),NOW+timedelta(seconds=3),(None,None))
    monkeypatch.setattr(dispatch,'load_research_batch_with_psycopg',lambda *a,**k:snap)
    monkeypatch.setattr(dispatch,'run_captured_research_with_psycopg',lambda *a,**k:pytest.fail('legacy fallback'))
    result=dispatch.run_research_batch_with_psycopg('fake',batch_id='b',model_factory=h.factory,
        allow_model_calls=True,uncapped_authorization=approval(requests),allow_uncapped_costs=True,max_tasks=2)
    assert result.to_dict()['execution_invocations']==2
    assert [a.execution.record.run.research.status for a in result.attempts]==['completed','completed']
    assert result.to_dict()['hard_money_cap_enforced'] is False and h.events.count('complete')==4


def test_batch_scope_conflict_is_not_partial_execution(monkeypatch):
    h=Harness(monkeypatch); requests=(req(),req(1)); batch=ResearchBatch('b',requests)
    snap=ResearchBatchSnapshot(StoredResearchBatch(batch,NOW),NOW+timedelta(seconds=3),(None,None))
    monkeypatch.setattr(dispatch,'load_research_batch_with_psycopg',lambda *a,**k:snap)
    with pytest.raises(ValueError,match='request_mismatch'):
        dispatch.run_research_batch_with_psycopg('fake',batch_id='b',model_factory=h.factory,
            allow_model_calls=True,uncapped_authorization=approval(requests[:1]),allow_uncapped_costs=True,max_tasks=2)
    assert not h.claims and not h.events


def test_rotation_forwards_explicit_policy_and_replay_stays_inert(monkeypatch):
    monkeypatch.setattr(runner, '_now', lambda: NOW+timedelta(seconds=3))
    h=RotationHarness(monkeypatch); requests=tuple(r for snap in inputs() for r in snap.stored.batch.requests)
    p=approval(requests); calls=[]
    def execute(dsn,**kw):
        assert kw['authorization']==p and kw['allow_uncapped_costs'] is True and kw['allow_model_calls'] is True
        calls.append(kw['request'].record_id)
        from tests.test_research_dispatch import receipt
        return receipt(kw['request'])
    monkeypatch.setattr(runner,'run_uncapped_research_with_psycopg',execute)
    result=run_turn(uncapped_authorization=p,allow_uncapped_costs=True,max_tasks=2)
    assert len(calls)==2 and result.status=='dispatched'
    replay=run_turn(uncapped_authorization=p,allow_uncapped_costs=True,max_tasks=2)
    assert replay.status=='turn_already_reserved' and len(calls)==2


def test_rotation_scope_rejection_does_not_consume_turn(monkeypatch):
    h=RotationHarness(monkeypatch)
    with pytest.raises(ValueError,match='request_mismatch'): run_turn(uncapped_authorization=approval(),allow_uncapped_costs=True)
    assert not h.saved and not h.calls
