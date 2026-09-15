"""Separate same-assistant adversarial review, not an independent-person audit."""
from dataclasses import replace
from datetime import timedelta, timezone
from decimal import Decimal, localcontext, ROUND_UP
import json

import pytest

from polymarket_alpha_lab import research_paper_capture as store
from polymarket_alpha_lab import research_paper_capture_codec as codec
from tests.test_research_paper_capture import sample, seam, call


@pytest.mark.parametrize('field,value', [('history_sha256','b'*64),('first_record_id','foreign'),
                                       ('attempt_payload_sha256','b'*64)])
def test_insert_receipt_must_match_all_supplied_provenance(seam,monkeypatch,field,value):
    wrong=replace(seam['r'],**{field:value})
    monkeypatch.setattr(store,'_row',lambda *a:wrong)
    with pytest.raises(ValueError,match='insert_mismatch'):call(seam)


def row(receipt):
    r=receipt;p=codec.encode_paper_scenario(r.scenario)
    return (r.scenario.record_id,r.request_sha256,r.attempt_payload_sha256,r.first_record_id,
            r.history_at,r.history_sha256,r.forecast_cutoff_at,r.recorded_at,p,codec.checksum(p),
            r.result_payload,codec.checksum(r.result_payload),True,True,True)


def test_actual_row_validation_preserves_success_and_rejects_cost_tampering(monkeypatch):
    e,s,h,r=sample()
    class Cursor:
        def execute(self,*a):pass
        def fetchone(self):return (r.attempt_payload_sha256,)
    monkeypatch.setattr(store,'_original',lambda *a:e)
    assert store._row(Cursor(),row(r))==r
    value=json.loads(r.result_payload)
    value['assumed_totals']['entry_notional_upper_bound']='0'
    poisoned=replace(r,result_payload=codec.dump(value))
    with pytest.raises(ValueError,match='result_changed'):store._row(Cursor(),row(poisoned))


@pytest.mark.parametrize('column,value',[(0,'foreign'),(1,'b'*64),(2,'b'*64),(9,'b'*64),
                                        (11,'b'*64),(12,False),(13,1),(14,None)])
def test_stored_row_identity_hashes_and_flags_reject(monkeypatch,column,value):
    e,s,h,r=sample()
    class Cursor:
        def execute(self,*a):pass
        def fetchone(self):return (r.attempt_payload_sha256,)
    monkeypatch.setattr(store,'_original',lambda *a:e)
    values=list(row(r));values[column]=value
    with pytest.raises(ValueError):store._row(Cursor(),tuple(values))


def test_book_bytes_are_never_replaced_by_normalized_json():
    _,s,_,_=sample();raw=b' {"invalid duplicate":1,"invalid duplicate":2} \xff'
    s=replace(s,yes_book=replace(s.yes_book,raw_json=raw))
    encoded=codec.encode_paper_scenario(s)
    assert codec.decode_paper_scenario(encoded,codec.checksum(encoded)).yes_book.raw_json==raw


def test_timezone_and_decimal_context_preserve_input_bytes():
    _,s,_,_=sample();expected=codec.encode_paper_scenario(s)
    zone=timezone(timedelta(hours=8));s=replace(s,decision_at=s.decision_at.astimezone(zone),
        market=replace(s.market,fetched_at=s.market.fetched_at.astimezone(zone)))
    with localcontext() as ctx:
        ctx.prec=2;ctx.rounding=ROUND_UP
        assert codec.encode_paper_scenario(s)==expected


def test_mutated_nested_cost_is_revalidated_before_database(seam):
    object.__setattr__(seam['s'].costs,'taker_fee_rate',Decimal('-1'))
    with pytest.raises(ValueError):call(seam)
    assert not seam['calls']


def test_commit_ack_loss_never_returns_a_success_receipt(seam):
    seam['cleanup_error']=RuntimeError('commit acknowledgement unknown')
    # The initial read also uses a managed transaction; fail only after INSERT.
    original=store.db._local_transaction
    def tx(dsn,operation,**kw):
        fault=seam.pop('cleanup_error',None)
        try:result=original(dsn,operation,**kw)
        finally:seam['cleanup_error']=fault
        if seam['writes']:raise fault
        return result
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(store.db,'_local_transaction',tx)
        with pytest.raises(RuntimeError,match='unknown'):call(seam)
    assert seam['writes']==1
