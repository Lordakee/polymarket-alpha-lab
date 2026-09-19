"""Synthetic call ordering and metadata integrity; no provider or database I/O."""
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import json
import traceback

import pytest

from polymarket_alpha_lab import research_uncapped_audit as values
from polymarket_alpha_lab import research_uncapped_audit_store as store
from polymarket_alpha_lab import research_uncapped_runner as runner
from tests.test_research_uncapped import Harness, approval, req, NOW, run
from tests.test_research_execution import Model


def start(number=1, **kwargs):
    r = req(); p = approval()
    fields = dict(authorization_id=p.authorization_id, authorization_sha256=p.content_sha256,
        record_id=r.record_id, request_sha256=r.content_sha256, call_number=number,
        message_sha256='b'*64, message_bytes=2, max_output_tokens=100,
        started_at=NOW+timedelta(seconds=3))
    fields.update(kwargs)
    return values.UncappedCallStart(**fields)


class AuditHarness(Harness):
    def __init__(self, monkeypatch):
        super().__init__(monkeypatch)
        self.starts, self.outcomes = [], []
        self.begin_error = self.finish_error = None
        def require(dsn, p):
            self.events.append('authorization')
        def begin(dsn, *, authorization, request, call_number, messages_json, max_output_tokens):
            self.events.append('start_commit')
            if self.begin_error: raise self.begin_error
            value = start(call_number, record_id=request.record_id, request_sha256=request.content_sha256,
                authorization_id=authorization.authorization_id, authorization_sha256=authorization.content_sha256,
                message_sha256=sha256(messages_json.encode()).hexdigest(), message_bytes=len(messages_json.encode()),
                max_output_tokens=max_output_tokens, started_at=NOW+timedelta(seconds=3+2*(call_number-1)))
            self.starts.append(value)
            return value
        def finish(dsn, *, start, status, reply=None):
            self.events.append('outcome_'+status)
            if self.finish_error: raise self.finish_error
            checksum = None if reply is None else values.reply_fingerprint(reply)[1]
            out = values.UncappedCallOutcome(start, status, None if reply is None else reply.total_tokens,
                                            checksum, start.started_at+timedelta(seconds=1))
            self.outcomes.append(out)
            return out
        monkeypatch.setattr(store, 'require_authorization', require)
        monkeypatch.setattr(store, '_begin_call', begin)
        monkeypatch.setattr(store, '_finish_call', finish)


@pytest.mark.parametrize('number', [0,1])
def test_commit_before_factory_reply_before_capture_and_inert_replay(monkeypatch, number):
    h = AuditHarness(monkeypatch); r = req(number)
    result = run(h, request=r, require_durable_audit=True)
    assert h.events == ['authorization', 'claim', 'start_commit', 'factory', 'complete',
                        'outcome_returned', 'start_commit', 'complete', 'outcome_returned', 'capture']
    assert result.record.run.research.status == 'completed'
    summary = values.UncappedAuditSnapshot(r.record_id, tuple(h.starts), tuple(h.outcomes)).to_dict()
    assert summary['validated_reply_count'] == 2
    assert summary['reported_tokens_known_subset'] == result.record.run.research.total_tokens == 4
    assert summary['actual_billed_micros'] is summary['provider_submission_count'] is None
    h.events.clear()
    assert run(h, request=r, require_durable_audit=True) == result
    assert h.events == ['authorization', 'replay']


@pytest.mark.parametrize('error', [RuntimeError('SECRET-SENTINEL'), KeyboardInterrupt(), SystemExit(0)])
def test_start_failure_never_enters_factory_or_writes_invented_terminal(monkeypatch, error):
    h = AuditHarness(monkeypatch); h.begin_error = error
    if isinstance(error, Exception):
        result = run(h, require_durable_audit=True)
        assert result.record.run.research.status == 'failed'
        assert h.events == ['authorization','claim','start_commit','capture']
    else:
        with pytest.raises(type(error)):
            run(h, require_durable_audit=True)
        assert h.events == ['authorization','claim','start_commit']
    assert not h.starts and not h.outcomes


@pytest.mark.parametrize('phase', ['factory', 'complete', 'invalid_reply'])
def test_terminal_failure_retains_unknown_usage_and_no_raw_exception(monkeypatch, phase):
    h = AuditHarness(monkeypatch)
    def factory(team):
        if phase == 'factory': raise ValueError('SECRET-SENTINEL')
        class Client:
            def complete(self, **kwargs):
                if phase == 'invalid_reply': return object()
                raise ValueError('SECRET-SENTINEL')
        return Client()
    result = run(h, model_factory=factory, require_durable_audit=True)
    assert result.record.run.research.status == 'failed'
    assert len(h.starts) == len(h.outcomes) == 1
    summary = values.UncappedAuditSnapshot(req().record_id, tuple(h.starts), tuple(h.outcomes)).to_dict()
    assert summary['unknown_usage_call_count'] == 1 and summary['reported_tokens_known_subset'] is None
    assert summary['calls'][0]['status'] == 'failed'
    assert 'SECRET-SENTINEL' not in json.dumps(summary)


@pytest.mark.parametrize('error', [KeyboardInterrupt(), SystemExit(0)])
def test_interrupted_client_keeps_original_interrupt_and_one_outcome(monkeypatch, error):
    h = AuditHarness(monkeypatch)
    def failed(team): raise error
    with pytest.raises(type(error)) as caught:
        run(h, model_factory=failed, require_durable_audit=True)
    assert caught.value is error
    assert h.outcomes[0].status == 'interrupted' and len(h.starts) == 1
    assert h.events == ['authorization','claim','start_commit','outcome_interrupted']


def test_terminal_write_failure_suppresses_success_without_retry(monkeypatch):
    h = AuditHarness(monkeypatch); h.finish_error = RuntimeError('lost COMMIT ack')
    result = run(h, require_durable_audit=True)
    assert result.record.run.research.status == 'failed'
    assert h.events.count('complete') == 1 and h.events.count('outcome_returned') == 1
    assert 'outcome_failed' not in h.events
    snapshot = values.UncappedAuditSnapshot(req().record_id, tuple(h.starts), ())
    assert snapshot.to_dict()['calls'][0]['status'] == 'unknown'
    assert snapshot.to_dict()['reported_tokens_known_subset'] is None


def test_double_failure_does_not_hide_original_interrupt(monkeypatch):
    h = AuditHarness(monkeypatch); h.finish_error = RuntimeError('audit error')
    original = KeyboardInterrupt()
    def factory(team): raise original
    with pytest.raises(KeyboardInterrupt) as caught:
        run(h, model_factory=factory, require_durable_audit=True)
    assert caught.value is original and not h.outcomes
    assert h.events.count('outcome_interrupted') == 1


@pytest.mark.parametrize('required', [1, None, 'true', [], object()])
def test_invalid_audit_flag_rejected_before_io(monkeypatch, required):
    h = AuditHarness(monkeypatch)
    with pytest.raises(ValueError, match='audit_mode_invalid'):
        run(h, require_durable_audit=required)
    assert h.events == []


def test_missing_stored_authorization_before_claim(monkeypatch):
    h = Harness(monkeypatch)
    monkeypatch.setattr(store, 'load_uncapped_authorization_with_psycopg', lambda *a, **k: None)
    with pytest.raises(ValueError, match='authorization_required'):
        run(h, require_durable_audit=True)
    assert h.events == []


@pytest.mark.parametrize('mutation', ['id', 'roster', 'model'])
def test_stored_authorization_must_match_full_canonical_input(monkeypatch, mutation):
    h = Harness(monkeypatch); p = approval()
    changes = dict(id={'authorization_id':'other'}, roster={'request_keys':p.request_keys[:1]},model={'model_id':'other'})
    saved = values.StoredUncappedAuthorization(replace(p, **changes[mutation]), NOW+timedelta(seconds=1))
    monkeypatch.setattr(store, 'load_uncapped_authorization_with_psycopg', lambda *a, **k: saved)
    with pytest.raises(ValueError, match='authorization_required'):
        run(h, authorization=p, require_durable_audit=True)
    assert h.events == []


@pytest.mark.parametrize('kw', [dict(status='returned',reported_total_tokens=None,reply_sha256=None),
    dict(status='failed',reported_total_tokens=0,reply_sha256=None),
    dict(status='returned',reported_total_tokens=True,reply_sha256='a'*64),
    dict(status='returned',reported_total_tokens=1,reply_sha256='bad'),
    dict(status='unknown',reported_total_tokens=None,reply_sha256=None)])
def test_outcome_cannot_turn_missing_or_failed_usage_into_zero(kw):
    with pytest.raises(ValueError): values.UncappedCallOutcome(start(), recorded_at=NOW+timedelta(seconds=4), **kw)


@pytest.mark.parametrize('bad', ['duplicate', 'gap', 'wrong_id', 'wrong_authorization', 'failed_previous', 'missing_previous'])
def test_snapshot_rejects_impossible_sequences(bad):
    one, two = start(), start(2,started_at=NOW+timedelta(seconds=5))
    out = values.UncappedCallOutcome(one,'returned',2,'a'*64,NOW+timedelta(seconds=4))
    calls, outcomes = (one,two), (out,)
    if bad == 'duplicate': outcomes=(out,out)
    if bad == 'gap': calls=(one,replace(two,call_number=3))
    if bad == 'wrong_id': calls=(replace(one,record_id='other'),)
    if bad == 'wrong_authorization': calls=(one,replace(two,authorization_id='other'))
    if bad == 'failed_previous': outcomes=(replace(out,status='failed',reported_total_tokens=None,reply_sha256=None),)
    if bad == 'missing_previous': outcomes=()
    with pytest.raises(ValueError): values.UncappedAuditSnapshot(req().record_id,calls,outcomes)


def test_stored_permission_copies_input_and_preserves_original_timestamp():
    p = approval(); saved = values.StoredUncappedAuthorization(p,NOW+timedelta(seconds=1))
    assert saved.authorization is not p
    assert saved.to_dict()['durable_authorization_record_created'] is True
    object.__setattr__(p,'model_id','mutated')
    assert saved.authorization.model_id != p.model_id
    assert saved.to_dict()['approval_identity_authenticated'] is False


def test_no_rows_is_not_a_zero_billing_or_no_provider_claim():
    result = values.UncappedAuditSnapshot('legacy',(),()).to_dict()
    assert result['audit_coverage'] == 'no_audited_calls'
    assert result['reported_tokens_known_subset'] is result['provider_submission_count'] is result['actual_billed_micros'] is None


def test_authorization_write_requires_explicit_permission_before_connection(monkeypatch):
    monkeypatch.setattr(store.db,'_local_transaction',lambda *a,**k: pytest.fail('connection entered'))
    with pytest.raises(ValueError): store.create_uncapped_authorization_with_psycopg('fake',authorization=approval())


@pytest.mark.parametrize('bad', [None,(),('a',)*6,('a',)*7])
def test_invalid_authorization_database_rows_fail_closed(bad):
    with pytest.raises(ValueError): store._auth_row(bad)


@pytest.mark.parametrize('change', [dict(call_number=True),dict(message_bytes=0),dict(request_sha256='bad'),
                                   dict(started_at=NOW.replace(tzinfo=None))])
def test_invalid_call_metadata(change):
    with pytest.raises(ValueError): start(**change)


class Cursor:
    def __init__(self, rows=(), all_rows=()):
        self.rows=list(rows); self.all_rows=list(all_rows); self.statements=[]
    def execute(self,sql,params=None): self.statements.append((sql,params))
    def fetchone(self): return self.rows.pop(0)
    def fetchall(self): return self.all_rows.pop(0)


def auth_row(p=None):
    p=approval() if p is None else p
    return (p.authorization_id,p.payload,p.content_sha256,NOW+timedelta(seconds=1),True,True,True)


def start_row(s=None):
    from dataclasses import astuple
    return (*astuple(start() if s is None else s),True,True,True)


def transaction(monkeypatch,cursor):
    calls=[]
    def run(dsn,operation,**kwargs):
        calls.append(kwargs)
        return operation(cursor)
    monkeypatch.setattr(store.db,'_local_transaction',run)
    return calls


def test_stored_authorization_exact_replay_is_read_only_in_write_transaction(monkeypatch):
    p=approval(); row=auth_row(p); c=Cursor([(len(p.payload.encode()),),row]); transaction(monkeypatch,c)
    result=store.create_uncapped_authorization_with_psycopg('fake',authorization=p,allow_authorization_write=True)
    assert result.recorded_at == row[3] and result.authorization == p
    assert not any(sql.startswith('INSERT') for sql,_ in c.statements)


def test_authorization_changed_same_id_never_overwrites(monkeypatch):
    p=approval(); c=Cursor([(len(p.payload),),auth_row(p)]); transaction(monkeypatch,c)
    with pytest.raises(store.db.ResearchCaptureConflict):
        store.create_uncapped_authorization_with_psycopg('fake',authorization=replace(p,adapter_contract_sha256='c'*64),allow_authorization_write=True)
    assert not any(sql.startswith('INSERT') for sql,_ in c.statements)


def test_authorization_insert_verifies_full_returned_payload(monkeypatch):
    p=approval(); c=Cursor([None,auth_row(replace(p,adapter_contract_sha256='c'*64))]); transaction(monkeypatch,c)
    with pytest.raises(ValueError,match='insert_mismatch'):
        store.create_uncapped_authorization_with_psycopg('fake',authorization=p,allow_authorization_write=True)


def test_auth_size_checked_before_payload_read(monkeypatch):
    c=Cursor([(store.MAX_AUTHORIZATION_BYTES+1,)]); transaction(monkeypatch,c)
    with pytest.raises(ValueError): store.load_uncapped_authorization_with_psycopg('fake',authorization_id='x')
    assert len(c.statements)==1


def test_inspection_uses_read_snapshot_and_keeps_missing_terminal_unknown(monkeypatch):
    c=Cursor([None],[[start_row()]]); calls=transaction(monkeypatch,c)
    result=store.inspect_uncapped_calls_with_psycopg('fake',record_id=req().record_id)
    assert calls==[dict(readonly=True)]
    assert result.to_dict()['calls'][0]['status']=='unknown'
    assert not any('INSERT' in sql for sql,_ in c.statements)


def test_begin_checks_claim_and_committed_payload_binding(monkeypatch):
    from tests.test_research_execution import state
    p=approval(); r=req(); raw='[{}]'; s=start(message_sha256=sha256(raw.encode()).hexdigest(),message_bytes=len(raw))
    c=Cursor([(len(p.payload),),auth_row(p),start_row(s)]); transaction(monkeypatch,c)
    monkeypatch.setattr(store.execution,'_lookup',lambda cursor,record_id:state(r))
    result=store._begin_call('fake',authorization=p,request=r,call_number=1,messages_json=raw,max_output_tokens=100)
    assert result==s
    assert sum(sql.startswith('INSERT') for sql,_ in c.statements)==1


def test_begin_without_claim_never_inserts(monkeypatch):
    p=approval(); c=Cursor([(len(p.payload),),auth_row(p)]); transaction(monkeypatch,c)
    monkeypatch.setattr(store.execution,'_lookup',lambda *a:None)
    with pytest.raises(store.db.ResearchCaptureConflict):
        store._begin_call('fake',authorization=p,request=req(),call_number=1,messages_json='[{}]',max_output_tokens=100)
    assert not any(sql.startswith('INSERT') for sql,_ in c.statements)


def test_same_terminal_replay_does_not_append_or_change_timestamp(monkeypatch):
    s=start(); row=(s.record_id,1,'failed',None,None,NOW+timedelta(seconds=4),True,True,True)
    c=Cursor([start_row(s),row]); transaction(monkeypatch,c)
    out=store._finish_call('fake',start=s,status='failed')
    assert out.recorded_at==row[5]
    assert not any(sql.startswith('INSERT') for sql,_ in c.statements)


def test_changed_terminal_conflicts_without_rewrite(monkeypatch):
    s=start(); row=(s.record_id,1,'interrupted',None,None,NOW+timedelta(seconds=4),True,True,True)
    c=Cursor([start_row(s),row]); transaction(monkeypatch,c)
    with pytest.raises(store.db.ResearchCaptureConflict): store._finish_call('fake',start=s,status='failed')
    assert not any(sql.startswith('INSERT') for sql,_ in c.statements)
