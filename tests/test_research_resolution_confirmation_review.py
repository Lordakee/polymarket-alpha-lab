"""Separately designed adversarial self-review; no claim of external audit."""
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import io
import json

import pytest

from polymarket_alpha_lab import research_resolution_confirmation as core
from polymarket_alpha_lab import research_resolution_confirmation_cli as cli
from polymarket_alpha_lab.research_resolution_codec import encode_resolution
from tests.test_research_resolution_confirmation import (
    ROOT, OPEN, PRIVATE, fixture, build, receipt, input_bytes, managed, invoke,
)


@pytest.mark.parametrize('fault',['foreign-record','opposite-outcome','different-source'])
def test_cli_must_bind_result_to_instruction_not_only_review_id(managed,capsys,fault):
    i,e,c=fixture()
    if fault=='foreign-record':
        other,ex,ca=fixture(record_id='foreign')
        other=replace(other,review_id=i.review_id)
        wrong=receipt(build(other,ex,ca),ex.request)
    elif fault=='opposite-outcome':
        other,ex,ca=fixture(yes=False)
        wrong=receipt(build(other,ex,ca),ex.request)
    else:
        other=replace(i,confirmation=replace(i.confirmation,source_text='other independently reviewed source'))
        wrong=receipt(build(other,e,c),e.request)
    managed['receipt']=wrong
    code,out=invoke(managed,capsys)
    assert code==1 and out['result'] is None
    assert out['business_writes_possible'] is True and managed['closed']


@pytest.mark.parametrize('position',['top','proof'])
def test_stdin_rejects_extra_fields_and_duplicate_approvals(position):
    i,_,_=fixture();raw=input_bytes(i);body=json.loads(raw)
    target=body if position=='top' else body['confirmation']
    target['unexpected']='do not ignore me'
    with pytest.raises(ValueError):cli.decode_review(json.dumps(body).encode())
    key='record_id' if position=='top' else 'actual_yes'
    raw=raw.replace(('"'+key+'":').encode(),('"'+key+'": null,"'+key+'":').encode(),1)
    with pytest.raises(ValueError):cli.decode_review(raw)


@pytest.mark.parametrize('delta_seconds',[-1,0,1,599,600,601])
def test_snapshot_age_boundary_matches_original_gate(delta_seconds):
    i,e,c=fixture();confirmed=c.submission.snapshot.fetched_at+timedelta(seconds=delta_seconds)
    if delta_seconds<0:
        with pytest.raises(ValueError):replace(i.confirmation,confirmed_at=confirmed)
        return
    i=replace(i,confirmation=replace(i.confirmation,confirmed_at=confirmed))
    if delta_seconds>600:
        with pytest.raises(ValueError):build(i,e,c)
    else:
        assert build(i,e,c).checked_at==confirmed


def test_read_call_never_requests_more_than_limit_plus_one(managed,capsys):
    class Bounded:
        def read(self,size):
            assert size==cli.MAX_INPUT_BYTES+1
            return b' '*size
    code=cli.confirm_from_stdin(root=ROOT,stream=Bounded(),allow_resolution_write=True)
    assert code==2 and 'root' not in managed


def test_input_exceptions_are_sanitized_without_db_access(managed,capsys):
    class Broken:
        def read(self,size):raise SystemExit(PRIVATE)
    code=cli.confirm_from_stdin(root=ROOT,stream=Broken(),allow_resolution_write=True)
    output=capsys.readouterr()
    assert code==2 and PRIVATE not in output.out+output.err and 'root' not in managed


def test_terms_and_hash_tampering_is_not_repaired_in_place():
    i,e,c=fixture();before=(e.request.payload,encode_resolution(c.submission))
    object.__setattr__(i,'source_pair','BTCUSD')
    with pytest.raises(ValueError):build(i,e,c)
    assert (e.request.payload,encode_resolution(c.submission))==before
