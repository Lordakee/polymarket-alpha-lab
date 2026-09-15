"""Outcome-linked simulation bounds; synthetic records only, never an account."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D, localcontext
import json

import pytest

from polymarket_alpha_lab import research_paper_settlement as core
from polymarket_alpha_lab.research_paper_capture_codec import checksum, dump
from polymarket_alpha_lab.research_capture_codec import encode_research_capture
from polymarket_alpha_lab.research_resolution import IndependentResolutionConfirmation, ResolutionSubmission
from polymarket_alpha_lab.research_resolution_confirmation import CryptoSettlementReview, build_crypto_resolution_confirmation
from polymarket_alpha_lab.research_resolution_codec import encode_resolution
from polymarket_alpha_lab.research_resolution_store import StoredResolutionReview
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationReport, ResearchEvaluationOutcome
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from tests.test_research_paper_capture import inputs, captured, scenario, PRIVATE


def confirmation(e, raw, actual_yes, when=None):
    req=e.request;when=when or req.forecast_cutoff_at+timedelta(seconds=61)
    body=dict(raw,closed=True,acceptingOrders=False,umaResolutionStatus='resolved',
              outcomePrices=['1','0'] if actual_yes else ['0','1'])
    candidate=StoredResolutionReview(ResolutionSubmission('candidate-'+req.record_id,req.intake.condition_id,
        GammaMarketSnapshot(req.intake.market_slug,when,json.dumps(body).encode()),when),when)
    confirmed=when+timedelta(seconds=1)
    proof=IndependentResolutionConfirmation(req.intake.condition_id,req.intake.market_slug,actual_yes,
        when,confirmed,candidate.submission.snapshot.content_sha256,'synthetic-reviewer',
        'https://data.binance.vision/synthetic-settlement',PRIVATE,independently_verified=True)
    instruction=CryptoSettlementReview('confirmed-'+req.record_id,req.record_id,req.content_sha256,
        candidate.submission.review_id,checksum(encode_resolution(candidate.submission)),proof,'binance',
        'BTCUSDT' if req.intake.team_id=='crypto_btc' else 'ETHUSDT','1m','close',
        req.forecast_cutoff_at+timedelta(seconds=1))
    submission=build_crypto_resolution_confirmation(instruction=instruction,execution=e,candidate=candidate)
    outcome=ResearchEvaluationOutcome(req.intake.condition_id,req.intake.market_slug,req.forecast_cutoff_at,
        when,confirmed,actual_yes,core.resolution._REFERENCE+submission.review_id,checksum(encode_resolution(submission)))
    return StoredResolutionReview(submission,confirmed,outcome),candidate


def case(n=1,team='crypto_btc',p='.7',actual=True,status='completed'):
    req,raw=inputs(n,team);e=captured(req,status)
    if status=='completed':
        e=replace(e,record=replace(e.record,run=replace(e.record.run,
            research=replace(e.record.run.research,probability_yes=D(p)))))
    s=scenario(e,raw);h=ResearchEvaluationReport((e.record,),(),s.decision_at)
    attempt_hash=checksum(encode_research_capture(record_id=req.record_id,model_id=req.model_id,
        protocol_version=req.protocol_version,run=e.record.run))
    receipt=core.paper.StoredResearchPaper(s,req.content_sha256,attempt_hash,req.record_id,h.generated_at,
        h.input_sha256,req.forecast_cutoff_at,s.decision_at+timedelta(seconds=1),
        dump(core.paper._result_for(h,s,e)))
    review,candidate=confirmation(e,raw,actual) if status=='completed' else (None,None)
    history=ResearchEvaluationReport((e.record,),() if review is None else (review.outcome,),
        req.forecast_cutoff_at+timedelta(minutes=2))
    return history,receipt,review,e,candidate


def assemble(history,papers,reviews):
    with localcontext(core._CONTEXT):return core._assemble(history,papers,reviews)


@pytest.mark.parametrize('team',['crypto_btc','crypto_eth'])
@pytest.mark.parametrize('p,actual,side,payout,cost',[('.7',True,'yes','5','2.029000'),
    ('.7',False,'yes','0','2.029000'),('.1',False,'no','5','3.029000'),('.1',True,'no','0','3.029000')])
def test_yes_no_wins_and_losses_use_saved_cost_bound(team,p,actual,side,payout,cost):
    h,r,v,_,_=case(team=team,p=p,actual=actual)
    out=assemble(h,{r.scenario.record_id:r},{v.outcome.condition_id:v});row=out['attempts'][0]
    assert row['status']=='settled_simulation' and row['amounts']['selected_side']==side
    assert D(row['amounts']['binary_payout'])==D(payout)
    assert D(row['amounts']['assumed_total_cost_upper_bound'])==D(cost)
    assert D(row['amounts']['settled_pnl_lower_bound'])==D(payout)-D(cost)
    assert out['history']==h.to_dict() and out['actual_account_pnl'] is None
    assert out['paper_trades_created']==0 and out['business_writes_performed'] is False
    assert PRIVATE not in json.dumps(out) and 'data.binance.vision' not in json.dumps(out)


def test_all_attempts_remain_visible_and_unsettled_has_no_zero_pnl():
    a=case();b=case(2,status='failed');c=case(3);d=case(4)
    records=tuple(x[0].records[0] for x in (a,b,c,d))
    history=ResearchEvaluationReport(records,(a[2].outcome,),a[0].generated_at)
    papers={x[1].scenario.record_id:x[1] for x in (a,b,c)}
    out=assemble(history,papers,{a[2].outcome.condition_id:a[2]})
    assert out['attempt_count']==4 and out['paper_evidence_count']==3
    assert out['status_counts']==dict(paper_evidence_missing=1,research_not_selected=1,
        paper_not_selected=0,outcome_pending=1,crypto_confirmation_required=0,settled_simulation=1)
    assert all(row['amounts'] is None for row in out['attempts'][1:])
    empty=assemble(ResearchEvaluationReport((),(),history.generated_at),{}, {})
    assert empty['attempt_count']==0 and empty['groups']==[]
    pending=assemble(replace(a[0],outcomes=()),{a[1].scenario.record_id:a[1]}, {})
    assert pending['groups'][0]['settled_pnl_lower_bound_sum'] is None


def test_rejected_paper_is_not_promoted_by_a_winning_outcome():
    h,r,v,e,_=case(p='.4')
    assert json.loads(r.result_payload)['status']=='paper_scenario_rejected'
    out=assemble(h,{r.scenario.record_id:r},{v.outcome.condition_id:v})
    assert out['attempts'][0]['status']=='paper_not_selected' and out['attempts'][0]['amounts'] is None


def test_costs_changed_under_same_label_are_not_pooled():
    h,r,v,e,_=case();h2,r2,v2,e2,_=case(2)
    s=replace(r2.scenario,costs=replace(r2.scenario.costs,slippage_cost_per_share=D('.002')))
    old=ResearchEvaluationReport((e2.record,),(),r2.history_at)
    r2=replace(r2,scenario=s,result_payload=dump(core.paper._result_for(old,s,e2)))
    history=ResearchEvaluationReport(h.records+h2.records,h.outcomes+h2.outcomes,h.generated_at)
    out=assemble(history,{r.scenario.record_id:r,r2.scenario.record_id:r2},
                 {v.outcome.condition_id:v,v2.outcome.condition_id:v2})
    assert len(out['groups'])==2 and all(x['settled_count']==1 for x in out['groups'])


def test_legacy_direct_outcome_is_visible_but_not_scored_as_settled_money():
    h,r,v,e,c=case()
    out=assemble(h,{r.scenario.record_id:r},{})
    assert out['attempts'][0]['status']=='crypto_confirmation_required'
    assert out['attempts'][0]['amounts'] is None


class Cursor:
    def __init__(self,answers):self.answers=list(answers);self.calls=[]
    def execute(self,sql,args=None):self.calls.append((sql,args));self.answer=self.answers.pop(0)
    def fetchone(self):return self.answer
    def fetchall(self):return self.answer


@pytest.fixture
def seam(monkeypatch):
    h,r,v,e,c=case();state=dict(h=h,r=r,v=v,e=e,c=c,tx=[],cursor=object())
    def transaction(dsn,operation,**kw):
        state['tx'].append(kw)
        result=operation(state['cursor'])
        if state.get('exit_error'):raise state['exit_error']
        return result
    def history(cursor,**kw):
        assert cursor is state['cursor'] and kw['require_execution_complete'] is True
        if state.get('history_error'):raise state['history_error']
        return state['h']
    def papers(cursor,*a):
        assert cursor is state['cursor'];return {r.scenario.record_id:r}
    monkeypatch.setattr(core.db,'_local_transaction',transaction)
    monkeypatch.setattr(core.db,'_read_research_evaluation',history)
    monkeypatch.setattr(core,'_paper_rows',papers)
    monkeypatch.setattr(core,'_crypto_review',lambda cursor,*a:state['v'])
    return state


def test_single_readonly_transaction_and_no_public_call(seam):
    out=core.evaluate_settled_paper_with_psycopg('synthetic')
    assert seam['tx']==[dict(readonly=True)]
    assert out['status_counts']['settled_simulation']==1


@pytest.mark.parametrize('kw',[dict(max_records=0),dict(max_records=True),dict(bucket_count=3),
    dict(min_sample_count=0),dict(generated_at='not a timestamp')])
def test_invalid_configuration_before_connection(seam,kw):
    with pytest.raises(ValueError):core.evaluate_settled_paper_with_psycopg('synthetic',**kw)
    assert seam['tx']==[]


def test_incomplete_history_error_propagates_without_fallback(seam):
    seam['history_error']=core.db.ResearchCaptureConflict('research_execution_history_incomplete')
    with pytest.raises(core.db.ResearchCaptureConflict):core.evaluate_settled_paper_with_psycopg('synthetic')
    assert len(seam['tx'])==1


def test_read_cleanup_error_never_returns_a_report(seam):
    seam['exit_error']=RuntimeError('synthetic cleanup failure')
    with pytest.raises(RuntimeError):core.evaluate_settled_paper_with_psycopg('synthetic')
    assert len(seam['tx'])==1


def test_hostile_decimal_context_cannot_change_public_output(seam):
    expected=core.evaluate_settled_paper_with_psycopg('synthetic')
    from decimal import ROUND_UP
    with localcontext() as ctx:
        ctx.prec=2;ctx.rounding=ROUND_UP
        assert core.evaluate_settled_paper_with_psycopg('synthetic')==expected


@pytest.mark.parametrize('count,size',[(10001,1),(1,core.db.MAX_READ_BYTES+1),(-1,0),(1,-1)])
def test_paper_size_or_count_limit_before_body_load(count,size):
    h,*_=case();cursor=Cursor([(count,size)])
    with pytest.raises(core.db.ResearchCaptureConflict):core._paper_rows(cursor,h,10000,[core.db.MAX_READ_BYTES])
    assert len(cursor.calls)==1


def test_paper_loader_binds_snapshot_ids_and_saved_row(monkeypatch):
    h,r,*_=case();cursor=Cursor([(1,123),[(r.scenario.record_id,)]])
    monkeypatch.setattr(core.paper,'_load',lambda c,rid:r)
    assert core._paper_rows(cursor,h,10000,[1000])=={r.scenario.record_id:r}
    assert all(call[1]==(h.generated_at,) for call in cursor.calls)


def test_linked_crypto_confirmation_reuses_original_builder(monkeypatch):
    h,r,v,e,c=case();calls=[]
    def review(cur,rid,*a):calls.append(rid);return v if rid==v.submission.review_id else c
    monkeypatch.setattr(core,'_review',review)
    monkeypatch.setattr(core.paper,'_original',lambda *a:e)
    cursor=Cursor([(100,)])
    assert core._crypto_review(cursor,v.outcome,h,[1000])==v
    assert calls==[v.submission.review_id,c.submission.review_id]


def test_generic_outcome_does_not_query_a_guessed_review():
    h,r,v,e,c=case();outcome=replace(v.outcome,source_reference='fixture:direct')
    assert core._crypto_review(Cursor([]),outcome,h,[100]) is None


def test_managed_session_routes_then_refuses_after_close(monkeypatch):
    from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
    from polymarket_alpha_lab.project_postgres import binding,files
    class DB:
        def _dsn(self,_):return 'synthetic'
    session=ProjectResearchSession(DB(),dict(instance_id='i',root_sha256='r',system_identifier='s'))
    def run(dsn,**kw):assert binding._EXPECTED.get()==('i','r','s');return kw
    monkeypatch.setattr(core,'evaluate_settled_paper_with_psycopg',run)
    assert session.evaluate_settled_paper_research(max_records=4)==dict(max_records=4)
    session.close()
    with pytest.raises(files.ProjectDatabaseError):session.evaluate_settled_paper_research()
