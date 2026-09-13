"""Pure queue selection and bounded consistent-read contracts; no live DB/HTTP."""
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone
import json

import pytest

from polymarket_alpha_lab import research_capture_psycopg as cap
from polymarket_alpha_lab import research_resolution_queue_store as store
from polymarket_alpha_lab.research_resolution_queue import ResolutionWorkItem, ResolutionWorklist
from polymarket_alpha_lab.research_resolution_store import StoredResolutionReview
from polymarket_alpha_lab.research_resolution import assess_resolution
from polymarket_alpha_lab.research_resolution_codec import encode_resolution
from hashlib import sha256
from tests.test_research_resolution import CID, SLUG, NOW, submission


def market(**changes):
    values = dict(condition_id=CID, market_slug=SLUG, forecast_cutoff_at=NOW-timedelta(seconds=600),
                  registered_at=NOW-timedelta(seconds=1000))
    values.update(changes)
    return cap.RegisteredResearchMarket(**values)


def review(*, age=0, fetched_age=None, data=None, **changes):
    item = submission(confirmation=False, data=data)
    checked = NOW-timedelta(seconds=age)
    snap = replace(item.snapshot, fetched_at=NOW-timedelta(seconds=age if fetched_age is None else fetched_age))
    item = replace(item, snapshot=snap, checked_at=checked)
    return StoredResolutionReview(item, checked, **changes)


def worklist(*, latest=None, at=NOW, **changes):
    return ResolutionWorklist(at, (ResolutionWorkItem(market(), latest_review=latest),), 1, **changes)


def test_no_review_is_due_and_summary_contains_no_source_text():
    report = worklist()
    assert len(report.due_items()) == 1
    result = report.to_dict()
    assert result['state_counts']['fetch_due'] == 1
    assert result['registered_market_count'] == result['unresolved_market_count'] == 1
    assert result['settled_market_count'] == 0
    assert result['items'][0]['candidate_yes'] is None
    assert result['outcome_confirmation_performed'] is result['live_model_called'] is False
    assert result['paper_only'] is result['report_only'] is result['readonly'] is True
    with pytest.raises(FrozenInstanceError): report.registered_market_count = 2
    output = worklist(latest=review()).to_dict()
    assert 'Synthetic source' not in json.dumps(output) and 'raw_json' not in json.dumps(output)


@pytest.mark.parametrize('age,expected', [(0,'waiting'),(299,'waiting'),(300,'fetch_due'),(301,'fetch_due')])
def test_pending_refresh_boundary(age,expected):
    result = worklist(latest=review(age=age,data={'closed':False})).to_dict()
    assert result['items'][0]['state'] == expected
    assert result['items'][0]['latest_status'] == 'pending'


@pytest.mark.parametrize('age,fetched_age,expected', [(0,0,'needs_confirmation'),(300,600,'needs_confirmation'),
    (1,601,'fetch_due'),(600,600,'needs_confirmation'),(601,601,'fetch_due')])
def test_confirmation_expires_from_source_fetch_not_check_time(age,fetched_age,expected):
    result=worklist(latest=review(age=age,fetched_age=fetched_age)).to_dict()['items'][0]
    assert result['state']==expected and result['candidate_yes'] is True


@pytest.mark.parametrize('data', [{'outcomePrices':['0.5','0.5']},{'slug':'other'}, {'closed':None}])
def test_blocked_reviews_require_attention_not_silent_repoll(data):
    result=worklist(latest=review(age=700,data=data)).to_dict()['items'][0]
    assert result['state']=='blocked_review' and result['next_check_at'] is None
    assert result['candidate_yes'] is None


def test_future_cutoff_and_unsupported_legacy_ids_remain_visible():
    items=(ResolutionWorkItem(market(forecast_cutoff_at=NOW+timedelta(seconds=1))),
           ResolutionWorkItem(market(condition_id='legacy-identifier'), 2, 1))
    result=ResolutionWorklist(NOW,items,3,incomplete_execution_count=1).to_dict()
    assert result['state_counts']['awaiting_cutoff']==result['state_counts']['unsupported_market']==1
    assert result['settled_market_count']==1
    row=next(r for r in result['items'] if r['condition_id']=='legacy-identifier')
    assert row['attempt_count']==2 and row['incomplete_claim_count']==1 and row['next_check_at'] is None


def test_order_is_oldest_cutoff_then_condition_and_empty_is_not_error():
    first=market(condition_id='0x'+'0'*64)
    last=market(forecast_cutoff_at=NOW,condition_id='0x'+'b'*64)
    original=(ResolutionWorkItem(last),ResolutionWorkItem(market()),ResolutionWorkItem(first))
    report=ResolutionWorklist(NOW,original,3)
    assert [i.market.condition_id for i in report.items]==[first.condition_id,CID,last.condition_id]
    assert report.items[0] is not original[2]
    assert ResolutionWorklist(NOW,(),4).to_dict()['settled_market_count']==4


@pytest.mark.parametrize('kwargs', [{'items':[]},{'items':(object(),)},{'registered_market_count':True},
    {'registered_market_count':0},{'recheck_after_seconds':59},{'recheck_after_seconds':86401},
    {'recheck_after_seconds':True},{'paper_only':False},{'report_only':1},{'readonly':False},
    {'generated_at':NOW.replace(tzinfo=None)},{'incomplete_execution_count':True}])
def test_invalid_queue_contract(kwargs):
    args=dict(generated_at=NOW,items=(ResolutionWorkItem(market()),),registered_market_count=1)
    args.update(kwargs)
    with pytest.raises(ValueError):ResolutionWorklist(**args)


@pytest.mark.parametrize('kwargs', [{'attempt_count':True},{'attempt_count':-1},{'incomplete_claim_count':-1},
    {'market':object()},{'latest_review':object()}])
def test_invalid_item(kwargs):
    args=dict(market=market());args.update(kwargs)
    with pytest.raises(ValueError):ResolutionWorkItem(**args)


def test_cross_scope_duplicate_and_future_rows_refused():
    with pytest.raises(ValueError):ResolutionWorkItem(market(market_slug='other'),latest_review=review())
    with pytest.raises(ValueError):ResolutionWorklist(NOW,(ResolutionWorkItem(market()),)*2,2)
    with pytest.raises(ValueError):worklist(latest=review(age=-1))
    future=market(registered_at=NOW+timedelta(seconds=1),forecast_cutoff_at=NOW+timedelta(seconds=2))
    with pytest.raises(ValueError):ResolutionWorklist(NOW,(ResolutionWorkItem(future),),1)


def test_mutated_nested_flags_revalidated_and_timezones_normalized():
    original=review()
    object.__setattr__(original.submission.snapshot,'readonly',False)
    with pytest.raises(ValueError):worklist(latest=original)
    shifted=NOW.astimezone(timezone(timedelta(hours=8)))
    assert worklist(at=shifted).to_dict()==worklist().to_dict()


def row(value):
    payload=encode_resolution(value.submission);a=assess_resolution(value.submission)
    return (value.submission.review_id,CID,SLUG,value.submission.checked_at,value.recorded_at,
            a.status,a.reason_code,None,None,payload,sha256(payload.encode()).hexdigest(),True,True,True)


class Cursor:
    """Ordered query contract, with explicit aggregate/payload responses."""
    def __init__(self, *, latest=(), count=1, size=None, attempts=(), claims=()):
        m=market()
        self.answers=[(NOW,),(count,), (count,), (sum(n for _,n in claims),)]
        if count:
            self.answers += [[(m.condition_id,m.market_slug,m.forecast_cutoff_at,m.registered_at,True,True,True)],
                (len(latest),sum(len(r[9].encode()) for r in latest) if size is None else size),list(latest),list(attempts),list(claims)]
        self.commands=[]
    def execute(self, sql, args=()):
        self.commands.append((sql,args));self.answer=self.answers.pop(0)
    def fetchone(self):return self.answer
    def fetchall(self):return self.answer


def load(monkeypatch,cursor,**kwargs):
    flags=[]
    def transaction(dsn,operation,*,readonly=False):
        flags.append((dsn,readonly));return operation(cursor)
    monkeypatch.setattr(cap,'_local_transaction',transaction)
    result=store.load_resolution_worklist_with_psycopg('opaque-test-dsn',**kwargs)
    assert flags==[('opaque-test-dsn',True)]
    assert all('INSERT ' not in q and 'UPDATE ' not in q for q,_ in cursor.commands)
    return result


def test_one_readonly_snapshot_checks_caps_before_payloads_and_counts_incomplete(monkeypatch):
    saved=review(data={'closed':False})
    cursor=Cursor(latest=(row(saved),),attempts=((CID,3),),claims=((CID,1),))
    report=load(monkeypatch,cursor)
    assert report.items[0].attempt_count==3 and report.items[0].incomplete_claim_count==1
    assert report.items[0].latest_review==saved
    assert 'sum(octet_length(payload))' in cursor.commands[5][0]
    assert 'checked_at DESC,recorded_at DESC,review_id DESC' in cursor.commands[5][0]
    assert all(NOW in args for _,args in cursor.commands[1:])
    assert 'a.recorded_at<=%s' in cursor.commands[-1][0]
    assert 'c.claimed_at<=%s' in cursor.commands[-1][0]
    assert not cursor.answers


def test_empty_worklist_stops_before_loading_review_bodies(monkeypatch):
    c=Cursor(count=0);result=load(monkeypatch,c)
    assert result.items==() and len(c.commands)==4


@pytest.mark.parametrize('kwargs', [{'max_markets':0},{'max_markets':True},{'max_markets':1001},
    {'recheck_after_seconds':True},{'recheck_after_seconds':0}])
def test_bad_configuration_never_opens_connection(monkeypatch,kwargs):
    monkeypatch.setattr(cap,'_local_transaction',lambda *a,**k:pytest.fail('invalid input reached connection'))
    with pytest.raises(ValueError):store.load_resolution_worklist_with_psycopg('invalid',**kwargs)


def test_market_and_payload_limits_do_not_return_partial_inventory(monkeypatch):
    c=Cursor(count=2)
    with pytest.raises(cap.ResearchCaptureConflict,match='market_limit'):load(monkeypatch,c,max_markets=1)
    assert len(c.commands)==3
    c=Cursor(latest=(row(review()),),size=store.MAX_WORKLIST_BYTES+1)
    with pytest.raises(cap.ResearchCaptureConflict,match='payload_limit'):load(monkeypatch,c)
    assert len(c.commands)==6


def test_latest_review_is_decoded_and_hash_checked(monkeypatch):
    r=list(row(review()));r[10]='0'*64
    with pytest.raises(ValueError):load(monkeypatch,Cursor(latest=(tuple(r),)))


@pytest.mark.parametrize('where', ['attempts','claims'])
def test_foreign_count_rows_cannot_enter_queue(monkeypatch,where):
    with pytest.raises(ValueError,match='count_scope_invalid'):
        load(monkeypatch,Cursor(**{where:(('foreign',1),)}))


def test_real_wrapper_rejects_nonlocal_dsn_without_driver_import():
    with pytest.raises(ValueError):store.load_resolution_worklist_with_psycopg('postgresql://user@192.0.2.1/test')


def test_settled_market_incomplete_claim_is_still_exposed(monkeypatch):
    cursor=Cursor(count=0)
    # All registered markets are settled, but a claimed task never returned.
    cursor.answers=[(NOW,),(1,),(0,),(2,)]
    report=load(monkeypatch,cursor)
    result=report.to_dict()
    assert result['unresolved_market_count']==0 and result['settled_market_count']==1
    assert result['incomplete_execution_count']==2
    assert result['evaluation_blocked_by_incomplete'] is True
    assert not cursor.answers


@pytest.mark.parametrize('field,value',[('readonly',False),('incomplete_execution_count',-1),('registered_market_count',0)])
def test_output_revalidates_mutated_queue(field,value):
    q=worklist();object.__setattr__(q,field,value)
    with pytest.raises(ValueError):q.to_dict()
    with pytest.raises(ValueError):q.due_items()


def test_negative_candidate_is_not_replaced_by_unknown():
    q=worklist(latest=review(data={'outcomePrices':['0','1']}))
    assert q.to_dict()['items'][0]['candidate_yes'] is False
    assert q.to_dict()['items'][0]['state']=='needs_confirmation'
