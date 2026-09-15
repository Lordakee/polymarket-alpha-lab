"""Separately designed same-assistant boundary tests, not an external audit."""
from dataclasses import replace
from decimal import Decimal as D
import json

import pytest

from polymarket_alpha_lab import research_paper as core
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationReport
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from tests.test_research_paper import fixture, run, scenario, captured, book, Costs


def test_cost_rounding_must_not_promote_a_subthreshold_edge():
    h,s,e=fixture(p='0.41')
    s=replace(s,costs=Costs(D(0),D('0.0000001'),D(0),D(0),D(0),D(0)))
    row=run(h,s,e)['paper_attempts'][0]
    assert row['status']=='paper_scenario_rejected'


def test_worst_price_fee_alone_is_not_a_fee_upper_bound():
    h,s,e=fixture(p='0.99')
    s=replace(s,costs=Costs(D('.5'),*(D(0) for _ in range(5))),
        yes_book=book('101',e.request.intake.condition_id,s.decision_at,asks=(('0.4','2'),('0.8','3'))))
    row=run(h,s,e)['paper_attempts'][0]
    exact_fee=D(2)*D('.5')*D('.4')*D('.6')+D(3)*D('.5')*D('.8')*D('.2')
    assert D(row['assumed_totals']['assumed_fee_upper_bound']) >= exact_fee


def test_original_unsupported_path_dependent_rules_are_rejected():
    h,s,e=fixture();req=e.request;raw=json.loads(s.market.raw_json)
    raw['description']='This market resolves Yes if Bitcoin touches $2000 at any time. Otherwise No.'
    intake=prepare_team_research_from_gamma(
        GammaMarketSnapshot(req.intake.market_slug,req.intake.as_of,json.dumps(raw).encode()),
        task_id=req.intake.task_id,team_id=req.intake.team_id,condition_id=req.intake.condition_id,
        as_of=req.intake.as_of,evidence=req.intake.task.evidence)
    req=replace(req,intake=intake);e=captured(req);s=scenario(e,raw)
    h=ResearchEvaluationReport((e.record,),(),s.decision_at)
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


def test_declared_market_minimum_is_not_silently_ignored():
    h,s,e=fixture();raw=json.loads(s.market.raw_json);raw['orderMinSize']='10'
    s=replace(s,market=replace(s.market,raw_json=json.dumps(raw).encode()))
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


@pytest.mark.parametrize('field,raw',[('yes_book',b'{"bids":'),('no_book',b'null')],ids=['bad-json','null-book'])
def test_invalid_market_input_is_retained_as_rejection(field,raw):
    h,s,e=fixture();s=replace(s,**{field:replace(getattr(s,field),raw_json=raw)})
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


def test_outcome_change_cannot_change_selected_scenario():
    from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationOutcome
    from datetime import timedelta
    h,s,e=fixture();when=e.request.forecast_cutoff_at+timedelta(minutes=2)
    outcome=ResearchEvaluationOutcome(e.request.intake.condition_id,e.request.intake.market_slug,
        e.request.forecast_cutoff_at,when,when,True,'fixture:outcome','a'*64)
    a=run(ResearchEvaluationReport(h.records,(outcome,),when),s,e)['paper_attempts'][0]
    b=run(ResearchEvaluationReport(h.records,(replace(outcome,actual_yes=False),),when),s,e)['paper_attempts'][0]
    assert a==b


def test_mutated_nested_scenario_is_revalidated():
    h,s,e=fixture();object.__setattr__(s.costs,'taker_fee_rate',D('-1'))
    with pytest.raises(ValueError):run(h,s,e)


@pytest.mark.parametrize('field,value',[
    ('acceptingOrders',None),('acceptingOrders','true'),('enableOrderBook',False),
    ('orderMinSize',None),('orderMinSize',True),('orderMinSize','NaN'),
    ('orderPriceMinTickSize',None),('orderPriceMinTickSize','0'),
    ('clobTokenIds',['101','101']),('clobTokenIds',[101,102]),('outcomes',['Up','Down']),
    ('outcomes',[{},[]]),('outcomes',['No','No']),
    ('question','Changed original question'),('description','Changed original rules'),
])
def test_market_shape_and_order_constraints_reject_without_fallback(field,value):
    h,s,e=fixture();raw=json.loads(s.market.raw_json);raw[field]=value
    s=replace(s,market=replace(s.market,raw_json=json.dumps(raw).encode()))
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


@pytest.mark.parametrize('level',[
    dict(price='0',size='1'),dict(price='1',size='1'),dict(price='-0.1',size='1'),
    dict(price='NaN',size='1'),dict(price='0.4',size='0'),dict(price='0.4',size='Infinity'),
    dict(price='0.4',size=True),dict(price=0.4,size='1'),dict(price='0.4001',size='1'),
    dict(price='0.4',size='1000001'),dict(price='0.4',size='1',extra=True),
],ids=['zero-price','one-price','negative','nan','zero-size','infinite-size','bool-size','float-price','off-tick','oversize','extra'])
def test_bad_levels_are_not_ignored_as_zero(level):
    h,s,e=fixture();raw=json.loads(s.yes_book.raw_json);raw['asks']=[level]
    s=replace(s,yes_book=replace(s.yes_book,raw_json=json.dumps(raw).encode()))
    assert run(h,s,e)['paper_attempts'][0]['status']=='paper_scenario_rejected'


def test_scenario_dupes_and_extra_claims_are_not_silently_discarded():
    h,s,e=fixture()
    with pytest.raises(ValueError):core.ResearchPaperEvaluation(h,(s,s),(e,))
    with pytest.raises(ValueError):core.ResearchPaperEvaluation(h,(s,),(e,e))
    with pytest.raises(ValueError):core.ResearchPaperEvaluation(h,(s,),())


def test_missing_inputs_are_distinct_from_empty_history():
    h,s,e=fixture()
    out=core.ResearchPaperEvaluation(h,(),()).to_dict()
    assert out['attempt_count']==1 and out['paper_attempts'][0]['reason_code']=='paper_inputs_missing'
    empty=core.ResearchPaperEvaluation(ResearchEvaluationReport((),(),s.decision_at),(),()).to_dict()
    assert empty['attempt_count']==0 and empty['ready_scenario_count']==0


def test_equivalent_timezones_and_host_precision_do_not_change_bindings():
    from datetime import timezone,timedelta
    from decimal import localcontext,ROUND_UP
    h,s,e=fixture();zone=timezone(timedelta(hours=8));expected=run(h,s,e)
    s=replace(s,decision_at=s.decision_at.astimezone(zone),
        market=replace(s.market,fetched_at=s.market.fetched_at.astimezone(zone)),
        yes_book=replace(s.yes_book,captured_at=s.yes_book.captured_at.astimezone(zone)))
    with localcontext() as ctx:
        ctx.prec=2;ctx.rounding=ROUND_UP
        assert run(h,s,e)==expected
