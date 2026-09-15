"""Separate same-assistant adversarial pass, not external/fresh-agent review."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
import json

import pytest

from polymarket_alpha_lab import research_paper_settlement as core
from polymarket_alpha_lab.research_paper_capture_codec import dump
from tests.test_research_paper_settlement import case, assemble, Cursor, seam


def test_wrong_valid_review_cannot_certify_the_outcome(seam):
    # Same original condition and terms, opposite independently valid outcome.
    _,_,wrong,_,_=case(actual=False)
    seam['v']=wrong
    with pytest.raises(ValueError):core.evaluate_settled_paper_with_psycopg('synthetic')


def test_null_totals_are_distinct_from_a_real_break_even():
    h,r,v,e,c=case()
    s=replace(r.scenario,costs=replace(r.scenario.costs,taker_fee_rate=D(0),slippage_cost_per_share=D('.6')))
    # Deliberately exercise arithmetic in isolation; not a stored admissible trade.
    result=json.loads(r.result_payload);result['assumed_totals']={
        'entry_notional_upper_bound':'2','assumed_fee_upper_bound':'0',
        'assumed_non_fee_cost_upper_bound':'3','assumed_total_cost_upper_bound':'5'}
    out=core._amounts(replace(r,scenario=s,result_payload=dump(dict(result,scenario_binding=core.json_value(s.binding())))),
                      result,v.outcome,v,e.record)
    assert out['settled_pnl_lower_bound']==0


@pytest.mark.parametrize('variant',['cost','first','cutoff','terms','side'])
def test_bound_integrity_rejects_bad_money_inputs(variant):
    h,r,v,e,c=case();result=json.loads(r.result_payload);outcome=v.outcome;record=e.record
    if variant=='cost':result['assumed_totals']['assumed_total_cost_upper_bound']='0'
    elif variant=='first':r=replace(r,first_record_id='foreign')
    elif variant=='cutoff':outcome=replace(outcome,forecast_cutoff_at=outcome.forecast_cutoff_at-timedelta(seconds=1))
    elif variant=='side':result['selected_side']='sell'
    else:
        record=replace(e.record,run=replace(e.record.run,intake=replace(e.record.run.intake,
            task=replace(e.record.run.intake.task,question='Different original question'))))
    with pytest.raises(ValueError):core._amounts(r,result,outcome,v,record)


@pytest.mark.parametrize('payload_size',[0,-1,core.MAX_RESOLUTION_PAYLOAD_BYTES+1])
def test_review_payload_bound_precedes_actual_body(payload_size):
    h,*_=case();cursor=Cursor([(payload_size,)])
    with pytest.raises(core.db.ResearchCaptureConflict):core._review(cursor,'valid',h.generated_at,[core.db.MAX_READ_BYTES])
    assert len(cursor.calls)==1


@pytest.mark.parametrize('ids',[[],[('missing',)],[('record-1',),('record-1',)]])
def test_bad_paper_inventory_cannot_silently_drop_or_duplicate(monkeypatch,ids):
    h,*_=case();cursor=Cursor([(1,100),ids])
    monkeypatch.setattr(core.paper,'_load',lambda *a:pytest.fail('must reject inventory before bodies'))
    with pytest.raises(ValueError):core._paper_rows(cursor,h,100,[1000])


@pytest.mark.parametrize('fault',['changed-schema-payload','changed-source','foreign-anchor','wrong-candidate'])
def test_crypto_attestation_not_just_a_boolean_label(monkeypatch,fault):
    h,r,v,e,c=case();source=json.loads(v.submission.confirmation.source_text)
    if fault=='changed-schema-payload':source['extra']='must not be silently ignored'
    if fault=='changed-source':source['source_venue']='coinbase'
    if fault.startswith('changed'):
        sub=replace(v.submission,confirmation=replace(v.submission.confirmation,source_text=dump(source)))
        outcome=replace(v.outcome,source_content_sha256=core.checksum(core.encode_resolution(sub)))
        v=replace(v,submission=sub,outcome=outcome);h=replace(h,outcomes=(outcome,))
    if fault=='foreign-anchor':h=replace(h,records=())
    if fault=='wrong-candidate':_,_,_,_,c=case(2)
    monkeypatch.setattr(core,'_review',lambda cursor,rid,*a:v if rid==v.submission.review_id else c)
    monkeypatch.setattr(core.paper,'_original',lambda *a:e)
    with pytest.raises(ValueError):core._crypto_review(Cursor([(10,)]),v.outcome,h,[1000])


def test_legacy_generic_confirmation_remains_unpriced(monkeypatch):
    h,r,v,e,c=case()
    sub=replace(v.submission,confirmation=replace(v.submission.confirmation,source_text='ordinary manual proof'))
    outcome=replace(v.outcome,source_content_sha256=core.checksum(core.encode_resolution(sub)))
    v=replace(v,submission=sub,outcome=outcome)
    monkeypatch.setattr(core,'_review',lambda *a:v)
    assert core._crypto_review(Cursor([]),outcome,replace(h,outcomes=(outcome,)),[1000]) is None


def test_outcome_does_not_change_the_saved_direction_or_cost():
    a=case(actual=True);b=case(actual=False)
    ra=assemble(a[0],{'record-1':a[1]},{a[2].outcome.condition_id:a[2]})['attempts'][0]
    rb=assemble(b[0],{'record-1':b[1]},{b[2].outcome.condition_id:b[2]})['attempts'][0]
    assert ra['paper_input_sha256']==rb['paper_input_sha256']
    assert ra['paper_result_sha256']==rb['paper_result_sha256']
    assert ra['amounts']['selected_side']==rb['amounts']['selected_side']
    assert D(ra['amounts']['settled_pnl_lower_bound'])-D(rb['amounts']['settled_pnl_lower_bound'])==5


def test_outcome_review_metadata_not_from_another_condition(monkeypatch):
    h,r,v,e,c=case();wrong=case(2)[2]
    monkeypatch.setattr(core,'_review',lambda *a:wrong)
    with pytest.raises(ValueError,match='outcome_mismatch'):
        core._crypto_review(Cursor([]),v.outcome,h,[1000])


def test_no_auto_retry_on_history_limit(seam):
    seam['history_error']=core.db.ResearchCaptureConflict('research_capture_history_limit')
    with pytest.raises(core.db.ResearchCaptureConflict):core.evaluate_settled_paper_with_psycopg('synthetic')
    assert len(seam['tx'])==1
