"""Synthetic resolution evidence tests; no network, DB, model or credentials."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab.research_resolution import (
    IndependentResolutionConfirmation, ResolutionSubmission, assess_resolution,
)
from polymarket_alpha_lab.research_resolution_codec import decode_resolution, encode_resolution
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot

NOW = datetime(2026, 9, 13, tzinfo=UTC)
CID = '0x' + 'a' * 64
SLUG = 'synthetic-resolution'


def submission(*, data=None, confirmation=True, **changes):
    value = dict(conditionId=CID, slug=SLUG, outcomes='["Yes","No"]',
                 outcomePrices='["1","0"]', closed=True, acceptingOrders=False,
                 umaResolutionStatus='resolved', closedTime='not-used-as-resolution-time')
    if data:
        value.update(data)
    snap = GammaMarketSnapshot(SLUG, NOW, json.dumps(value).encode())
    proof = IndependentResolutionConfirmation(CID, SLUG, True, NOW-timedelta(seconds=1), NOW,
        snap.content_sha256, 'operator-1', 'https://example.invalid/official-result',
        'Synthetic source independently checked by the test operator.', independently_verified=True)
    return ResolutionSubmission('review-1', CID, snap, NOW, proof if confirmation else None, **changes)


def assessment(**kwargs):
    return assess_resolution(submission(**kwargs))


def test_final_prices_and_closed_state_never_sufficient_without_attestation():
    result = assessment(confirmation=False)
    assert (result.status, result.reason_code, result.candidate_yes) == (
        'needs_confirmation', 'independent_confirmation_required', True)


def test_ready_and_roundtrip_preserves_exact_evidence_bytes():
    item = submission()
    result = assess_resolution(item)
    assert (result.status, result.reason_code, result.candidate_yes) == ('ready', 'operator_confirmed', True)
    encoded = encode_resolution(item)
    restored = decode_resolution(encoded, expected_sha256=sha256(encoded.encode()).hexdigest())
    assert restored == item and restored is not item
    assert restored.snapshot.raw_json == item.snapshot.raw_json
    assert restored.confirmation.source_text == item.confirmation.source_text
    assert 'Synthetic source' not in repr(restored)


@pytest.mark.parametrize('labels,prices,winner', [
    (['Yes','No'],['1','0'],True), (['No','Yes'],['0','1'],True),
    (['Yes','No'],['0','1'],False), (['NO','YES'],['1','0'],False),
    (['Yes','No'],['0.000','1.000'],False),
])
def test_map_labels_not_array_position(labels,prices,winner):
    item = submission(data={'outcomes': labels, 'outcomePrices': prices})
    item = replace(item, confirmation=replace(item.confirmation, actual_yes=winner))
    assert assess_resolution(item).candidate_yes is winner
    assert assess_resolution(item).status == 'ready'


@pytest.mark.parametrize('data,status,reason', [
    ({'closed':False},'pending','market_not_closed'),
    ({'closed':None},'blocked','invalid_payload'),
    ({'closed':1},'blocked','invalid_payload'),
    ({'closed':'true'},'blocked','invalid_payload'),
    ({'acceptingOrders':True},'blocked','order_state_not_final'),
    ({'acceptingOrders':0},'blocked','order_state_not_final'),
    ({'acceptingOrders':None},'blocked','order_state_not_final'),
    ({'umaResolutionStatus':'proposed'},'pending','resolution_not_final'),
    ({'umaResolutionStatus':'disputed'},'pending','resolution_not_final'),
    ({'umaResolutionStatus':None},'pending','resolution_not_final'),
    ({'umaResolutionStatus':'resolved '},'pending','resolution_not_final'),
    ({'outcomePrices':['0.5','0.5']},'blocked','non_binary_payout'),
    ({'outcomePrices':['0.999','0.001']},'blocked','non_binary_payout'),
    ({'outcomePrices':['0','0']},'blocked','non_binary_payout'),
    ({'outcomePrices':['1','1']},'blocked','non_binary_payout'),
    ({'outcomePrices':[True,False]},'blocked','invalid_payload'),
    ({'outcomePrices':['NaN','0']},'blocked','invalid_payload'),
    ({'outcomePrices':['1e99999999999999999999','0']},'blocked','invalid_payload'),
    ({'outcomePrices':['-0','1']},'blocked','invalid_payload'),
    ({'outcomes':['Up','Down']},'blocked','unsupported_outcomes'),
    ({'outcomes':['Yes','Yes']},'blocked','unsupported_outcomes'),
    ({'outcomes':[' Yes','No']},'blocked','unsupported_outcomes'),
    ({'outcomes':['Yes','No','Void']},'blocked','unsupported_outcomes'),
    ({'outcomes':None},'blocked','unsupported_outcomes'),
    ({'conditionId':'0x'+'b'*64},'blocked','market_identity_mismatch'),
    ({'slug':'some-other-market'},'blocked','market_identity_mismatch'),
])
def test_fail_closed_for_ambiguous_and_incomplete_data(data,status,reason):
    result = assessment(data=data)
    assert result.status == status and result.reason_code == reason
    assert result.candidate_yes is None


@pytest.mark.parametrize('raw', [b'bad-json', b'[]', b'null', b'\xff', b'{"a":1,"a":2}',
    b'{"n":NaN}', b'{"n":1e99999999999999999999999}', b'['*2000+b']'*2000])
def test_untrusted_raw_errors_redacted_and_still_archivable(raw):
    item = submission(confirmation=False)
    item = replace(item, snapshot=replace(item.snapshot, raw_json=raw))
    assert assess_resolution(item).status == 'blocked'
    payload = encode_resolution(item)
    assert decode_resolution(payload, expected_sha256=sha256(payload.encode()).hexdigest()) == item


@pytest.mark.parametrize('delta,status', [(-1,'blocked'),(0,'ready'),(600,'ready'),(601,'blocked')])
def test_snapshot_age_boundaries(delta,status):
    item = replace(submission(), checked_at=NOW+timedelta(seconds=delta))
    assert assess_resolution(item).status == status


@pytest.mark.parametrize('change,reason', [
    ({'actual_yes':False},'confirmation_disagrees'),
    ({'condition_id':'0x'+'b'*64},'confirmation_scope_mismatch'),
    ({'market_slug':'other-market'},'confirmation_scope_mismatch'),
    ({'gamma_content_sha256':'0'*64},'confirmation_scope_mismatch'),
    ({'confirmed_at':NOW-timedelta(microseconds=1)},'confirmation_time_invalid'),
    ({'confirmed_at':NOW+timedelta(microseconds=1)},'confirmation_time_invalid'),
    ({'resolved_at':NOW+timedelta(microseconds=1),'confirmed_at':NOW+timedelta(seconds=1)},'confirmation_time_invalid'),
])
def test_confirmation_cannot_change_identity_result_or_time(change,reason):
    item = submission()
    item = replace(item, confirmation=replace(item.confirmation, **change))
    result = assess_resolution(item)
    assert result.reason_code == reason and result.candidate_yes is None


@pytest.mark.parametrize('url', ['http://example.invalid/result','https://gamma-api.polymarket.com/markets/x',
    'https://polymarket.com./x','https://a.polymarket.com/x','https://user:password@example.invalid',
    'https://example.invalid/#section','https://example.invalid:5432/x','https://example.invalid/\nfoo','file:///tmp/result'])
def test_independent_reference_not_a_second_polymarket_hint_or_secret_url(url):
    with pytest.raises(ValueError):
        replace(submission().confirmation, source_reference=url)


@pytest.mark.parametrize('field,value', [('actual_yes',1),('independently_verified',False),
    ('independently_verified',1),('paper_only',False),('report_only',1),('readonly',False),
    ('source_text',''),('reviewer_id',''),('resolved_at',NOW.replace(tzinfo=None))])
def test_confirmation_requires_exact_attestation_and_flags(field,value):
    with pytest.raises(ValueError):
        replace(submission().confirmation, **{field:value})


@pytest.mark.parametrize('field,value', [('review_id','bad id'),('condition_id','../path'),
    ('paper_only',1),('report_only',False),('readonly',False),('checked_at',NOW.replace(tzinfo=None)),
    ('snapshot',{}),('confirmation',{})])
def test_submission_rejects_invalid_contract(field,value):
    with pytest.raises(ValueError):
        replace(submission(), **{field:value})


def test_utc_normalization_and_nested_flag_mutation_revalidation():
    item = submission()
    offset = timezone(timedelta(hours=8))
    moved = replace(item, checked_at=NOW.astimezone(offset), snapshot=replace(item.snapshot,fetched_at=NOW.astimezone(offset)))
    assert encode_resolution(moved) == encode_resolution(item)
    object.__setattr__(item.confirmation, 'readonly', False)
    with pytest.raises(ValueError):
        assess_resolution(item)


@pytest.mark.parametrize('path,value', [
    (('schema_version',),'other'),(('extra',),True),(('readonly',),False),
    (('snapshot','content_sha256'),'0'*64),(('snapshot','source_reference'),'https://example.invalid'),
    (('assessment','status'),'blocked'),(('assessment','candidate_yes'),False),
    (('confirmation','source_content_sha256'),'0'*64),
])
def test_codec_rejects_tampering_even_with_recomputed_outer_digest(path,value):
    data = json.loads(encode_resolution(submission()))
    target=data
    for key in path[:-1]:target=target[key]
    target[path[-1]]=value
    payload=json.dumps(data,ensure_ascii=True,sort_keys=True,separators=(',',':'))
    with pytest.raises(ValueError,match='resolution_payload_invalid'):
        decode_resolution(payload,expected_sha256=sha256(payload.encode()).hexdigest())


def test_reference_timestamp_is_not_closed_time_end_date_or_fetch_time():
    item=submission(data={'closedTime':'1990-01-01T00:00:00Z','endDate':'1990-01-01T00:00:00Z'})
    assert assess_resolution(item).status=='ready'
    assert item.confirmation.resolved_at==NOW-timedelta(seconds=1)
