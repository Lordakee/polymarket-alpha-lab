"""Prospective simulation storage contracts with synthetic records and no I/O."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal as D
import json

import pytest

from polymarket_alpha_lab import research_paper_capture as store
from polymarket_alpha_lab import research_paper_capture_codec as codec
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions as Costs, PaperCostAwareEventStrategyConfig as Gates,
)
from polymarket_alpha_lab.research_execution import CapturedResearchRequest, CapturedResearchExecution
from polymarket_alpha_lab.research_paper import ResearchPaperEvaluation
from polymarket_alpha_lab.research_paper_inputs import ResearchPaperBook as Book, ResearchPaperScenario as Scenario
from polymarket_alpha_lab.research_capture_codec import encode_research_capture
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, TeamResearchResult
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord, ResearchEvaluationReport
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun

NOW = datetime(2026, 9, 15, 10, tzinfo=UTC)
PRIVATE = 'synthetic-private-evidence-never-echo'


def inputs(n=1, team='crypto_btc', *, at=NOW):
    cid = '0x'+format(n, '064x')
    opening = at.replace(second=0, microsecond=0)+timedelta(minutes=10)
    months = ('January','February','March','April','May','June','July','August','September','October','November','December')
    asset, ticker = ('Bitcoin','BTC') if team == 'crypto_btc' else ('Ethereum','ETH')
    title = f'Will the price of {asset} be above $2,000 on {months[opening.month-1]} {opening.day}, {opening.year}?'
    clock = f'{opening.hour % 12 or 12}:{opening.minute:02d} '+('AM' if opening.hour < 12 else 'PM')
    rules = (f'This market will resolve to "Yes" if the Close price of the Binance {ticker}/USDT '
             f'1-minute candle at {clock} UTC on the date in the title is above $2,000. '
             'Otherwise it will resolve to "No".')
    raw = dict(conditionId=cid, slug=f'synthetic-{n}', question=title, description=rules,
        active=True, closed=False, acceptingOrders=True, enableOrderBook=True,
        orderMinSize='1', orderPriceMinTickSize='0.001', endDate=(opening+timedelta(hours=1)).isoformat(),
        outcomes=['Yes','No'], clobTokenIds=['101','102'])
    evidence = ResearchEvidence('source', team, cid, 'Synthetic', PRIVATE, 'fixture:source', at)
    intake = prepare_team_research_from_gamma(GammaMarketSnapshot(raw['slug'], at, json.dumps(raw).encode()),
        task_id=f'task-{n}', team_id=team, condition_id=cid, as_of=at, evidence=(evidence,))
    return CapturedResearchRequest(f'record-{n}', 'synthetic-model', 'synthetic-protocol',
        opening-timedelta(seconds=1), intake, required_source_ids=('source',)), raw


def captured(request, status='completed'):
    i = request.intake
    v = dict(task_id=i.task_id, team_id=i.team_id, condition_id=i.condition_id, market_slug=i.market_slug,
        as_of=i.as_of, status=status, reason_code='research_completed' if status=='completed' else 'model_failed')
    if status == 'completed':
        v.update(probability_yes=D('.7'), confidence=D('.9'), source_ids=('source',), summary=PRIVATE)
    record = ResearchEvaluationRecord(request.record_id, request.model_id, request.protocol_version,
        i.as_of, MarketTeamResearchRun(i, TeamResearchResult(**v)))
    return CapturedResearchExecution(request, i.as_of, 'captured', record)


def scenario(execution, raw, at=None):
    r = execution.record; at = at or r.recorded_at+timedelta(seconds=1)
    delta = at-datetime(1970,1,1,tzinfo=UTC)
    millis = delta.days*86400000+delta.seconds*1000+delta.microseconds//1000
    def book(token, bid, ask):
        return Book(at, json.dumps(dict(asset_id=token, market=r.run.intake.condition_id,
            timestamp=str(millis), bids=[dict(price=bid,size='10')], asks=[dict(price=ask,size='10')])).encode())
    return Scenario(r.record_id, r.content_sha256, at,
        GammaMarketSnapshot(r.run.intake.market_slug, at, json.dumps(raw).encode()),
        book('101','0.39','0.4'), book('102','0.59','0.6'), D('5'),
        Costs(D('.02'), D('.001'), D('0'), D('0'), D('0'), D('0')),
        Gates('explicit-test', min_confidence=D('.7'),max_spread=D('.05'),max_resolution_risk=D('.2'),
              min_ask_size=D('1'),min_net_edge=D('.01')), D('.1'), 'synthetic-costs', 60)


def sample(team='crypto_btc', status='completed'):
    req, raw = inputs(team=team); e = captured(req,status); s = scenario(e,raw)
    h = ResearchEvaluationReport((e.record,), (), s.decision_at)
    body = store._result_for(h,s,e)
    capture_hash = codec.checksum(encode_research_capture(record_id=req.record_id, model_id=req.model_id,
                                                        protocol_version=req.protocol_version,run=e.record.run))
    receipt = store.StoredResearchPaper(s, req.content_sha256, capture_hash, req.record_id,
        h.generated_at,h.input_sha256,req.forecast_cutoff_at,s.decision_at+timedelta(seconds=1),codec.dump(body))
    return e,s,h,receipt


@pytest.mark.parametrize('team',['crypto_btc','crypto_eth'])
def test_canonical_inputs_retain_raw_bytes_and_explicit_costs(team):
    _,s,_,_ = sample(team)
    for changed in (s,replace(s,yes_book=replace(s.yes_book,raw_json=b'not-json\xff'))):
        payload=codec.encode_paper_scenario(changed)
        assert codec.decode_paper_scenario(payload,codec.checksum(payload))==changed
        assert codec.encode_paper_scenario(codec.decode_paper_scenario(payload,codec.checksum(payload)))==payload


@pytest.mark.parametrize('mutation',['extra','missing','cost-missing','cost-number','raw-hash','whitespace','duplicate','nan'])
def test_noncanonical_or_partial_input_never_defaults(mutation):
    _,s,_,_=sample();payload=codec.encode_paper_scenario(s);v=json.loads(payload)
    if mutation=='extra':v['unexpected']=True
    elif mutation=='missing':v.pop('readonly')
    elif mutation=='cost-missing':v['costs'].pop('taker_fee_rate')
    elif mutation=='cost-number':v['costs']['taker_fee_rate']=0
    elif mutation=='raw-hash':v['market']['raw_base64']='!!!'
    elif mutation=='nan':v['requested_size']='NaN'
    payload=json.dumps(v) if mutation=='whitespace' else codec.dump(v)
    if mutation=='duplicate':payload=payload.replace('"readonly":true','"readonly":true,"readonly":true')
    with pytest.raises(ValueError,match='input_invalid'):codec.decode_paper_scenario(payload,codec.checksum(payload))


def test_payload_digest_and_size_checked():
    _,s,_,_=sample();payload=codec.encode_paper_scenario(s)
    with pytest.raises(ValueError):codec.decode_paper_scenario(payload,'0'*64)
    with pytest.raises(ValueError):codec.decode_paper_scenario('x'*(codec.MAX_PAYLOAD_BYTES+1),'0'*64)


@pytest.mark.parametrize('status',['completed','failed','blocked'])
def test_saved_success_or_denial_is_explicit_and_metadata_only(status):
    _,s,_,receipt=sample(status=status);out=receipt.to_dict()
    assert out['durable_simulation_evidence'] is True and out['paper_trades_created']==0
    assert out['commit_before_cutoff_verified'] is False
    assert PRIVATE not in json.dumps(out)+repr(receipt)
    if status=='completed':assert out['result']['status']=='paper_scenario_ready'
    else:assert out['result']['status']=='not_simulated'


@pytest.mark.parametrize('field,value',[
    ('first_record_id','bad id'),('request_sha256','bad'),('history_sha256','A'*64),
    ('recorded_at',NOW),('recorded_at',NOW+timedelta(hours=1)),
    ('history_at',NOW+timedelta(days=1)),('readonly',False),('paper_only',1),
])
def test_receipt_rejects_bad_binding_time_flags(field,value):
    *_,r=sample()
    with pytest.raises(ValueError):replace(r,**{field:value})


def test_known_invalid_book_can_be_retained_as_rejection():
    e,s,h,r=sample();s=replace(s,yes_book=replace(s.yes_book,raw_json=b'{broken'))
    r=replace(r,scenario=s,result_payload=codec.dump(store._result_for(h,s,e)))
    assert r.to_dict()['result']['status']=='paper_scenario_rejected'
    assert r.to_dict()['result']['reason_code']=='malformed_market_or_book'


@pytest.fixture
def seam(monkeypatch):
    e,s,h,r=sample();state=dict(e=e,s=s,h=h,r=r,existing=None,calls=[],writes=0,clock=r.recorded_at)
    def transaction(dsn,operation,**kw):
        state['calls'].append(('transaction',kw))
        result=operation(Cursor())
        if state.get('cleanup_error'):raise state['cleanup_error']
        return result
    class Cursor:
        row=None
        def execute(self,sql,params=None):
            state['calls'].append((sql,params))
            if sql.startswith('SELECT clock_timestamp'):self.row=(state['clock'],)
            elif sql.startswith('SELECT record_id'):self.row=(state.get('first_id',e.request.record_id),)
            elif sql.startswith('SELECT payload_sha256'):self.row=(r.attempt_payload_sha256,)
            elif sql.startswith('INSERT'):
                state['writes']+=1
                if state.get('write_error'):raise state['write_error']
                self.row='insert-row'
        def fetchone(self):return self.row
    def load(cursor,record_id):return state['existing']
    def original(cursor,record_id):return state['e']
    def evaluated(dsn,**kw):
        state['calls'].append(('evaluate',kw))
        if state.get('history_error'):raise state['history_error']
        eligible=e.record.run.research.status=='completed'
        return ResearchPaperEvaluation(state['h'],(state['s'],),(e,) if eligible else ())
    monkeypatch.setattr(store.db,'_local_transaction',transaction)
    monkeypatch.setattr(store,'_load',load);monkeypatch.setattr(store,'_original',original)
    monkeypatch.setattr(store,'_row',lambda *a:r)
    monkeypatch.setattr(store,'evaluate_research_paper_with_psycopg',evaluated)
    return state


def call(state,**kw):
    return store.capture_research_paper_with_psycopg('test-seam',scenario=state['s'],allow_paper_write=True,**kw)


def test_new_write_uses_old_full_history_and_commits_once(seam):
    assert call(seam)==seam['r'] and seam['writes']==1
    assert any(sql=='evaluate' for sql,_ in seam['calls'])
    assert sum(sql.startswith('INSERT') for sql,_ in seam['calls'])==1


def test_identical_replay_skips_history_and_new_clock_checks(seam):
    seam['existing']=seam['r'];seam['clock']=NOW+timedelta(days=1)
    seam['history_error']=AssertionError('history must not run on replay')
    assert call(seam)==seam['r'] and seam['writes']==0
    assert not any(sql=='evaluate' for sql,_ in seam['calls'])


def test_replayed_input_change_cannot_overwrite(seam):
    seam['existing']=seam['r'];seam['s']=replace(seam['s'],requested_size=D(6))
    with pytest.raises(store.db.ResearchCaptureConflict,match='identity_conflict'):call(seam)
    assert seam['writes']==0


@pytest.mark.parametrize('opt',[False,None,0,1,'true'])
def test_write_permission_exact_before_store(seam,opt):
    with pytest.raises(ValueError):store.capture_research_paper_with_psycopg('unused',scenario=seam['s'],allow_paper_write=opt)
    assert not seam['calls']


@pytest.mark.parametrize('where',['history_error','write_error','cleanup_error'])
def test_errors_do_not_trigger_hidden_retry_or_success(seam,where):
    seam[where]=RuntimeError('synthetic failure')
    with pytest.raises(RuntimeError):call(seam)
    assert seam['writes']<=1


@pytest.mark.parametrize('seconds',[61,600,-1])
def test_nonprospective_admission_aborts_without_insert(seam,seconds):
    seam['clock']=seam['s'].decision_at+timedelta(seconds=seconds)
    with pytest.raises(store.db.ResearchCaptureConflict,match='not_prospective'):call(seam)
    assert seam['writes']==0


def test_changed_first_selection_cannot_replace_original(seam):
    seam['first_id']='some-earlier-record'
    with pytest.raises(store.db.ResearchCaptureConflict,match='selection_changed'):call(seam)
    assert seam['writes']==0


def test_payload_limit_is_checked_before_row_load(monkeypatch):
    class Cursor:
        calls=[]
        def execute(self,sql,params):self.calls.append(sql)
        def fetchone(self):return (codec.MAX_PAYLOAD_BYTES+1,2)
    c=Cursor()
    with pytest.raises(store.db.ResearchCaptureConflict,match='payload_limit'):store._load(c,'record-1')
    assert len(c.calls)==1
