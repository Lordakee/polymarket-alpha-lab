"""Synthetic research-to-paper assembly; no provider, database or network."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal as D, localcontext
import json

import pytest

from polymarket_alpha_lab import research_paper as core
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions as Costs, PaperCostAwareEventStrategyConfig as Gates,
)
from polymarket_alpha_lab.research_paper_inputs import ResearchPaperBook as Book, ResearchPaperScenario as Scenario
from polymarket_alpha_lab.research_execution import CapturedResearchRequest, CapturedResearchExecution
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, TeamResearchResult
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord, ResearchEvaluationReport

NOW = datetime(2026, 9, 15, 10, tzinfo=UTC)
PRIVATE = 'synthetic-private-evidence-not-for-output'


def request(n=1, team='crypto_btc', at=NOW):
    cid = '0x' + format(n, '064x')
    asset, ticker = ('Bitcoin','BTC') if team == 'crypto_btc' else ('Ethereum','ETH')
    opening = at.replace(second=0, microsecond=0)+timedelta(minutes=30)
    # Use UTC dated observation rather than local time or the current year.
    months = ('January','February','March','April','May','June','July','August','September','October','November','December')
    question = f'Will the price of {asset} be above $2,000 on {months[opening.month-1]} {opening.day}, {opening.year}?'
    clock = f'{opening.hour % 12 or 12}:{opening.minute:02d} ' + ('AM' if opening.hour < 12 else 'PM')
    rules = (f'This market will resolve to "Yes" if the Close price of the Binance {ticker}/USDT '
        f'1-minute candle at {clock} UTC on the date in the title is above $2,000. Otherwise it will resolve to "No".')
    raw = dict(conditionId=cid, slug=f'synthetic-{n}', question=question, description=rules,
        active=True, closed=False, acceptingOrders=True, enableOrderBook=True,
        orderMinSize='1', orderPriceMinTickSize='0.001',
        endDate=(opening+timedelta(hours=1)).isoformat(), outcomes=['Yes','No'], clobTokenIds=['101','102'])
    evidence = ResearchEvidence('source', team, cid, 'Fixture', PRIVATE, 'fixture:source', at)
    intake = prepare_team_research_from_gamma(GammaMarketSnapshot(raw['slug'], at, json.dumps(raw).encode()),
        task_id=f'task-{n}', team_id=team, condition_id=cid, as_of=at, evidence=(evidence,))
    return CapturedResearchRequest(f'record-{n}', 'synthetic-model', 'synthetic-protocol',
        opening-timedelta(seconds=1), intake, required_source_ids=('source',)), raw


def captured(req, p='0.7', status='completed', at=None):
    i=req.intake
    fields=dict(task_id=i.task_id,team_id=i.team_id,condition_id=i.condition_id,
        market_slug=i.market_slug,as_of=i.as_of,status=status,
        reason_code='research_completed' if status=='completed' else 'model_failed')
    if status=='completed': fields.update(probability_yes=D(p),confidence=D('.9'),source_ids=('source',),summary=PRIVATE)
    record=ResearchEvaluationRecord(req.record_id,req.model_id,req.protocol_version,at or i.as_of,
        MarketTeamResearchRun(i,TeamResearchResult(**fields)))
    return CapturedResearchExecution(req, i.as_of, 'captured', record)


def book(token,cid,at,asks=(('0.4','10'),),bids=(('0.39','10'),)):
    epoch=datetime(1970,1,1,tzinfo=UTC)
    delta=at-epoch
    millis=delta.days*86400000+delta.seconds*1000+delta.microseconds//1000
    return Book(at,json.dumps(dict(asset_id=token,market=cid,timestamp=str(millis),
        bids=[dict(price=p,size=s) for p,s in bids], asks=[dict(price=p,size=s) for p,s in asks])).encode())


def scenario(execution,raw,at=None):
    req=execution.request
    at=at or execution.record.recorded_at+timedelta(seconds=1)
    return Scenario(req.record_id,execution.record.content_sha256,at,
        GammaMarketSnapshot(req.intake.market_slug,at,json.dumps(raw).encode()),
        book('101',req.intake.condition_id,at),
        book('102',req.intake.condition_id,at,asks=(('0.6','10'),),bids=(('0.59','10'),)),
        D('5'), Costs(D('.02'),D('.001'),D('0'),D('0'),D('0'),D('0')),
        Gates('explicit-test',min_confidence=D('.7'),max_spread=D('.05'),
              max_resolution_risk=D('.2'),min_ask_size=D('1'),min_net_edge=D('.01')),
        D('.1'),'explicit-synthetic-costs',60)


def fixture(team='crypto_btc',p='0.7'):
    req,raw=request(team=team);e=captured(req,p=p);s=scenario(e,raw)
    h=ResearchEvaluationReport((e.record,),(),s.decision_at)
    return h,s,e


def run(h,s,e):
    return core.ResearchPaperEvaluation(h,(s,),(e,)).to_dict()


@pytest.mark.parametrize('team',['crypto_btc','crypto_eth'])
@pytest.mark.parametrize('p,chosen',[('0.7','yes'),('0.1','no'),('0.4','none')])
def test_original_probability_and_cost_risk_fill_composition(team,p,chosen):
    h,s,e=fixture(team,p);out=run(h,s,e);row=out['paper_attempts'][0]
    assert row['selected_side']==chosen
    assert row['book_walks']['yes']['side']==row['book_walks']['no']['side']=='buy'
    assert out['history']==h.to_dict() and out['attempt_count']==1
    assert row['original_reason_code']=='outcome_pending'
    assert out['paper_trades_created']==0 and out['realized_pnl'] is None and out['tariff_verified'] is False
    assert PRIVATE not in json.dumps(out)


def test_depth_changes_execution_price_and_does_not_resize_partial():
    h,s,e=fixture();s=replace(s,yes_book=book('101',e.request.intake.condition_id,s.decision_at,
        asks=(('0.4','2'),('0.5','3'))))
    row=run(h,s,e)['paper_attempts'][0]
    assert row['book_walks']['yes']['average_price']=='0.460'
    assert row['strategy']['yes_result']['executable_price']=='0.5'
    assert row['assumed_totals']['entry_notional_upper_bound']=='2.5'
    s=replace(s,requested_size=D('11'))
    row=run(h,s,e)['paper_attempts'][0]
    assert row['selected_side']=='none'
    assert row['book_walks']['yes']['requested_size']=='11' and row['book_walks']['yes']['unfilled_size']=='6'


@pytest.mark.parametrize('updates',[dict(resolution_risk=D('.9')),
    dict(gates=Gates('strict-confidence',min_confidence=D('.99'))),
    dict(gates=Gates('strict-depth',min_ask_size=D('100'))),
    dict(costs=Costs(D('1'),D('1'),D('0'),D('0'),D('0'),D('0')))])
def test_existing_risk_cost_decision_blocks(updates):
    h,s,e=fixture();row=run(h,replace(s,**updates),e)['paper_attempts'][0]
    assert row['status']=='paper_scenario_rejected' and row['selected_side']=='none'


@pytest.mark.parametrize('updates',[dict(requested_size=D('0')),dict(requested_size=D('NaN')),
    dict(requested_size=True),dict(requested_size=D('1E+999999')),dict(requested_size=D('0.0000000001')),
    dict(record_sha256='bad'),dict(readonly=False),dict(paper_only=1),dict(report_only=False),
    dict(max_age_seconds=0),dict(max_age_seconds=301),dict(max_age_seconds=True),
    dict(resolution_risk=D('1.01')),dict(assumptions_id='bad id'),dict(costs=None),
    dict(costs=Costs(D('1.1'),D('0'),D('0'),D('0'),D('0'),D('0')))])
def test_structural_inputs_fail(updates):
    _,s,_=fixture()
    with pytest.raises(ValueError):replace(s,**updates)


@pytest.mark.parametrize('field',['record_id','record_sha256'])
def test_wrong_original_binding_rejects_entire_composition(field):
    h,s,e=fixture();s=replace(s,**{field:'other' if field=='record_id' else 'b'*64})
    with pytest.raises(ValueError,match='binding_mismatch'):run(h,s,e)


@pytest.mark.parametrize('field',['market','yes_book','no_book'])
@pytest.mark.parametrize('seconds',[-61,1])
def test_freshness_window_never_extends(field,seconds):
    h,s,e=fixture();value=getattr(s,field)
    clock='fetched_at' if field=='market' else 'captured_at'
    s=replace(s,**{field:replace(value,**{clock:s.decision_at+timedelta(seconds=seconds)})})
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


@pytest.mark.parametrize('key,value',[('asset_id','foreign'),('market','foreign'),('timestamp',None),
    ('bids',[]),('asks',[]),('bids',[dict(price='0.5',size='10')])])
def test_missing_crossed_foreign_books_rejected(key,value):
    h,s,e=fixture();raw=json.loads(s.yes_book.raw_json);raw[key]=value
    s=replace(s,yes_book=replace(s.yes_book,raw_json=json.dumps(raw).encode()))
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


def test_reversed_outcome_order_maps_by_name_not_position():
    h,s,e=fixture();raw=json.loads(s.market.raw_json)
    raw['outcomes']=['No','Yes'];raw['clobTokenIds']=['102','101']
    s=replace(s,market=replace(s.market,raw_json=json.dumps(raw).encode()))
    assert run(h,s,e)['paper_attempts'][0]['selected_side']=='yes'


def test_no_hiding_missing_inputs_failed_and_later_attempts():
    h,s,e=fixture();req,raw=request(2);failed=captured(req,status='failed')
    later_req=replace(e.request,record_id='later',intake=replace(e.request.intake,
        task_id='later-task',task=replace(e.request.intake.task,task_id='later-task')))
    later=captured(later_req,at=NOW+timedelta(seconds=1))
    history=ResearchEvaluationReport((e.record,failed.record,later.record),(),s.decision_at)
    out=core.ResearchPaperEvaluation(history,(s,),(e,)).to_dict()
    assert out['attempt_count']==3
    reasons={r['record_id']:r['reason_code'] for r in out['paper_attempts']}
    assert reasons['record-2']=='research_failed' and reasons['later']=='later_attempt'
    empty=core.ResearchPaperEvaluation(history,(),()).to_dict()
    assert empty['attempt_count']==3 and empty['ready_scenario_count']==0


def test_ambient_decimal_context_cannot_change_result():
    h,s,e=fixture();expected=run(h,s,e)
    with localcontext() as ctx:
        ctx.prec=3
        actual=run(h,s,e)
    assert actual==expected


@pytest.fixture
def storage(monkeypatch):
    h,s,e=fixture();state=dict(history=h,scenario=s,execution=e,calls=[])
    def load(dsn,**kw):
        state['calls'].append(('history',kw))
        if state.get('error'):raise state['error']
        return state['history']
    def inspect(dsn,**kw):state['calls'].append(('execution',kw));return state['execution']
    monkeypatch.setattr(core,'load_captured_research_evaluation_with_psycopg',load)
    monkeypatch.setattr(core,'inspect_captured_research_with_psycopg',inspect)
    return state


def test_managed_assembly_reuses_complete_history_and_immutable_lookup(storage):
    report=core.evaluate_research_paper_with_psycopg('test-seam',scenarios=(storage['scenario'],))
    assert report.to_dict()['ready_scenario_count']==1
    assert [a for a,_ in storage['calls']]==['history','execution']


def test_incomplete_history_block_is_not_bypassed(storage):
    from polymarket_alpha_lab.research_capture_psycopg import ResearchCaptureConflict
    storage['error']=ResearchCaptureConflict('research_execution_history_incomplete')
    with pytest.raises(ResearchCaptureConflict):
        core.evaluate_research_paper_with_psycopg('test-seam',scenarios=(storage['scenario'],))
    assert len(storage['calls'])==1


def test_bad_scenarios_precede_store_and_missing_record_is_not_adopted(storage):
    with pytest.raises(ValueError):core.evaluate_research_paper_with_psycopg('test-seam',scenarios=[storage['scenario']])
    assert not storage['calls']
    storage['execution']=None
    with pytest.raises(ValueError):core.evaluate_research_paper_with_psycopg('test-seam',scenarios=(storage['scenario'],))
