"""Transaction contract tests. Real SQL is covered separately by native proof."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256

import pytest

from polymarket_alpha_lab import research_capture_psycopg as cap
from polymarket_alpha_lab import research_resolution_store as store
from polymarket_alpha_lab.research_resolution_codec import encode_resolution
from tests.test_research_resolution import CID, SLUG, NOW, submission


class Cursor:
    def __init__(self):
        self.market=(CID,SLUG,NOW-timedelta(seconds=10),NOW-timedelta(seconds=20),True,True,True)
        self.reviews={}
        self.outcome=None
        self.now=NOW+timedelta(seconds=1)
        self.commands=[]
        self.failure=None
        self.answer=None

    def execute(self,sql,args=()):
        self.commands.append((sql,args))
        if self.failure and self.failure in sql:
            raise RuntimeError('synthetic-private-sql-detail')
        if 'pg_advisory' in sql:self.answer=None
        elif 'FROM research_capture.markets' in sql:self.answer=self.market
        elif 'SELECT clock_timestamp' in sql:self.answer=(self.now,)
        elif sql.startswith('SELECT') and 'FROM research_capture.resolution_reviews' in sql:
            self.answer=self.reviews.get(args[0])
        elif sql.startswith('SELECT') and 'FROM research_capture.outcomes' in sql:
            self.answer=self.outcome
        elif sql.startswith('INSERT INTO research_capture.resolution_reviews'):
            rid,cid,slug,at,status,reason,yes,resolved,payload,digest=args
            row=(rid,cid,slug,at,self.now,status,reason,yes,resolved,payload,digest,True,True,True)
            self.reviews[rid]=row;self.answer=row
        elif sql.startswith('INSERT INTO research_capture.outcomes'):
            cid,slug,resolved,yes,ref,digest=args
            self.outcome=(cid,slug,self.market[2],resolved,self.now,yes,ref,digest,True,True,True)
            self.answer=None
        else:raise AssertionError(sql)

    def fetchone(self):return self.answer


@pytest.fixture
def database(monkeypatch):
    cursor=Cursor();calls=[]
    def transaction(dsn,operation,*,readonly=False):
        before=deepcopy((cursor.reviews,cursor.outcome))
        calls.append(readonly)
        try:return operation(cursor)
        except BaseException:
            cursor.reviews,cursor.outcome=before
            raise
    monkeypatch.setattr(cap,'_local_transaction',transaction)
    return cursor,calls


def save(item=None):
    return store.record_resolution_review_with_psycopg('synthetic-dsn-not-connected',submission=item or submission())


def test_evidence_and_outcome_are_written_in_same_transaction_and_linked(database):
    cursor,calls=database
    result=save()
    assert calls==[False]
    assert result.outcome.actual_yes is True and result.outcome.resolved_at==NOW-timedelta(seconds=1)
    assert result.outcome.source_reference.endswith(':review-1')
    assert result.outcome.source_content_sha256==sha256(encode_resolution(submission()).encode()).hexdigest()
    assert len(cursor.reviews)==1
    assert store.load_resolution_review_with_psycopg('fixture',review_id='review-1')==result
    assert calls==[False,True]


@pytest.mark.parametrize('data', [None,{'closed':False},{'umaResolutionStatus':'disputed'},
    {'outcomePrices':['0.5','0.5']},{'conditionId':'0x'+'b'*64}])
def test_nonconfirmed_reviews_are_retained_but_never_create_outcome(database,data):
    cursor,_=database
    result=save(submission(data=data,confirmation=False))
    assert len(cursor.reviews)==1 and cursor.outcome is None and result.outcome is None


def test_exact_retry_returns_original_time_even_after_expiry(database):
    cursor,_=database;first=save()
    cursor.now=NOW+timedelta(days=2)
    again=save()
    assert first==again and len(cursor.reviews)==1
    assert sum(sql.startswith('INSERT INTO research_capture.outcomes') for sql,_ in cursor.commands)==1


def test_changed_review_id_content_or_second_outcome_cannot_overwrite(database):
    cursor,_=database;first=save();item=submission()
    changed=replace(item,checked_at=NOW+timedelta(seconds=1))
    with pytest.raises(cap.ResearchCaptureConflict,match='review_conflict'):save(changed)
    with pytest.raises(cap.ResearchCaptureConflict,match='outcome_conflict'):
        save(replace(item,review_id='different-id'))
    assert save()==first and len(cursor.reviews)==1


@pytest.mark.parametrize('mode', ['unregistered','wrong_slug','before_cutoff','future_check','late_capture'])
def test_no_implicit_registration_time_backfill_or_late_import(database,mode):
    cursor,_=database
    if mode=='unregistered':cursor.market=None
    elif mode=='wrong_slug':cursor.market=tuple('different' if i==1 else v for i,v in enumerate(cursor.market))
    elif mode=='before_cutoff':cursor.market=tuple(NOW if i==2 else v for i,v in enumerate(cursor.market))
    elif mode=='future_check':cursor.now=NOW-timedelta(microseconds=1)
    else:cursor.now=NOW+timedelta(seconds=601)
    with pytest.raises(cap.ResearchCaptureConflict):save()
    assert not cursor.reviews and cursor.outcome is None


def test_outcome_insert_failure_rolls_back_the_review(database):
    cursor,_=database;cursor.failure='INSERT INTO research_capture.outcomes'
    with pytest.raises(RuntimeError):save()
    assert not cursor.reviews and cursor.outcome is None


@pytest.mark.parametrize('index,value', [(0,'other-review'),(1,'0x'+'b'*64),(2,'other-slug'),
    (5,'blocked'),(6,'unknown'),(7,1),(10,'0'*64),(11,1),(12,False),(13,False)])
def test_readback_detects_row_tampering(database,index,value):
    cursor,_=database;save()
    row=list(cursor.reviews['review-1']);row[index]=value;cursor.reviews['review-1']=tuple(row)
    with pytest.raises(ValueError):store.load_resolution_review_with_psycopg('fixture',review_id='review-1')


def test_ready_readback_cannot_hide_missing_linked_outcome(database):
    cursor,_=database;save();cursor.outcome=None
    with pytest.raises(ValueError,match='outcome_link'):store.load_resolution_review_with_psycopg('fixture',review_id='review-1')


def test_bad_input_does_not_reach_connection_wrapper(monkeypatch):
    monkeypatch.setattr(cap,'_local_transaction',lambda *a,**kw:pytest.fail('no DB activity'))
    with pytest.raises(ValueError):store.record_resolution_review_with_psycopg('fixture',submission={})
    with pytest.raises(ValueError):store.load_resolution_review_with_psycopg('fixture',review_id='bad id')
    item=submission();object.__setattr__(item.confirmation,'readonly',False)
    with pytest.raises(ValueError):save(item)


def test_unknown_review_is_none_not_a_negative_outcome(database):
    assert store.load_resolution_review_with_psycopg('fixture',review_id='missing') is None


def test_managed_session_uses_existing_bound_connection_scope(monkeypatch):
    from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
    from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
    class DB:
        def _dsn(self,_):return 'opaque-managed-dsn'
    identity=dict(instance_id='a'*32,root_sha256='b'*64,system_identifier='123')
    session=ProjectResearchSession(DB(),identity);calls=[]
    monkeypatch.setattr(store,'record_resolution_review_with_psycopg',lambda dsn,**kw:calls.append((dsn,kw)))
    monkeypatch.setattr(store,'load_resolution_review_with_psycopg',lambda dsn,**kw:calls.append((dsn,kw)))
    session.record_resolution(submission=submission());session.inspect_resolution(review_id='review-1')
    assert len(calls)==2 and all(dsn=='opaque-managed-dsn' for dsn,_ in calls)
    session.close()
    with pytest.raises(ProjectDatabaseError):session.inspect_resolution(review_id='review-1')


def test_readback_rechecks_database_receipt_window_for_pending_reviews(database):
    cursor,_=database
    save(submission(confirmation=False))
    row=list(cursor.reviews['review-1'])
    row[4]=NOW+timedelta(seconds=601)
    cursor.reviews['review-1']=tuple(row)
    with pytest.raises(ValueError,match='receipt_time_invalid'):
        store.load_resolution_review_with_psycopg('fixture',review_id='review-1')
