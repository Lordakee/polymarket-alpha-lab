"""Discovery transport/framing and per-attempt audit without live requests."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from http.client import IncompleteRead
from io import BytesIO
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import ssl
from urllib.error import HTTPError, URLError

import pytest

from polymarket_alpha_lab import research_crypto_discovery as d
from tests.test_public_http import response

NOW = datetime(2026, 9, 13, 14, tzinfo=UTC)
CID = '0x'+'a'*64


def market(**changes):
    result = dict(conditionId=CID, slug='bitcoin-price-event', question='Bitcoin above $70,000?',
                  outcomes='["Yes","No"]', active=True, closed=False,
                  endDate=(NOW+timedelta(days=1)).isoformat())
    result.update(changes)
    return result


def body(markets=None):
    return json.dumps(dict(events=[dict(markets=[market()] if markets is None else markets)])).encode()


def raw_response(raw=None, headers=None):
    raw = body() if raw is None else raw
    r = response(raw, f'Content-Length: {len(raw)}\r\n'.encode() if headers is None else headers)
    r.url = d.endpoint('crypto_btc')
    return r


def fake(monkeypatch, replies):
    calls, handlers, sleeps = [], [], []
    replies = iter(replies)
    class Opener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            value = next(replies)
            if isinstance(value, Exception):
                raise value
            return value
    def build(*args):
        handlers.append(args)
        return Opener()
    monkeypatch.setattr(d, 'build_opener', build)
    monkeypatch.setattr(d, 'sleep', sleeps.append)
    monkeypatch.setattr(d, '_now', lambda: NOW)
    return calls, handlers, sleeps


def discover(**kwargs):
    return d.discover_crypto_markets('crypto_btc', allow_public_fetch=True, **kwargs)


def test_single_public_get_raw_provenance_and_no_hidden_credentials(monkeypatch):
    r=raw_response();calls,handlers,sleeps=fake(monkeypatch,[r])
    value=discover();out=value.to_dict()
    assert out['status']=='candidates' and out['candidate_count']==1
    assert out['attempts']==[dict(number=1,reason_code='received')]
    assert out['request_attempts']==1 and out['recovered_after_failure'] is False
    assert out['source_sha256']==sha256(body()).hexdigest() and value.raw_json==body()
    req,timeout=calls[0]
    assert req.full_url==d.endpoint('crypto_btc') and req.get_method()=='GET' and req.data is None
    assert req.get_header('Authorization') is req.get_header('Cookie') is None
    assert req.get_header('Accept-encoding')=='identity' and timeout==15
    assert handlers[0][0].proxies=={}
    assert handlers[0][1].redirect_request(None) is None
    assert sleeps==[] and r.isclosed() and 'Bitcoin above' not in repr(value)
    assert not out['model_called'] and not out['database_written'] and not out['selection_is_approval']


def test_real_short_content_length_failure_then_fresh_complete_request(monkeypatch):
    first=raw_response(b'{"events":[]}',b'Content-Length: 100\r\n')
    last=raw_response();calls,_,sleeps=fake(monkeypatch,[first,last])
    value=discover(max_attempts=2)
    assert value.attempt_codes==('public_response_incomplete','received')
    assert value.to_dict()['recovered_after_failure'] is True and value.raw_json==body()
    assert len(calls)==2 and sleeps==[0.25] and first.isclosed() and last.isclosed()


def test_default_does_not_retry_and_has_no_partial_hash(monkeypatch):
    calls,_,sleeps=fake(monkeypatch,[IncompleteRead(b'synthetic-secret-partial',7),raw_response()])
    result=discover().to_dict()
    assert result['status']=='failed' and result['reason_code']=='public_response_incomplete'
    assert result['source_sha256'] is None and result['candidates']==[]
    assert len(calls)==1 and sleeps==[] and 'secret' not in str(result)


@pytest.mark.parametrize('error,code', [
    (IncompleteRead(b'partial',10),'public_response_incomplete'),
    (TimeoutError('sensitive'),'public_timeout'),
    (URLError(TimeoutError('sensitive')),'public_timeout'),
    (ConnectionResetError('sensitive'),'public_connection_interrupted'),
    (ConnectionAbortedError('sensitive'),'public_connection_interrupted'),
])
def test_explicit_retry_budget_preserves_all_failures(monkeypatch,error,code):
    calls,_,sleeps=fake(monkeypatch,[error,error,error])
    value=discover(max_attempts=3)
    assert value.attempt_codes==(code,)*3 and value.raw_json is None
    assert len(calls)==3 and sleeps==list(d.RETRY_DELAYS)
    assert value.to_dict()['recovered_after_failure'] is False


@pytest.mark.parametrize('error,code', [
    (ssl.SSLCertVerificationError('private'),'public_tls_failed'),
    (URLError(ssl.SSLError('private')),'public_tls_failed'),
    (URLError('DNS sensitive detail'),'public_fetch_failed'),
    (ValueError('private'),'public_fetch_failed'),
    (ConnectionRefusedError('private'),'public_fetch_failed'),
])
def test_other_failures_not_retried_or_leaked(monkeypatch,error,code):
    calls,_,sleeps=fake(monkeypatch,[error])
    value=discover(max_attempts=3)
    assert value.attempt_codes==(code,) and len(calls)==1 and sleeps==[]
    assert 'private' not in str(value.to_dict())


@pytest.mark.parametrize('code',[301,302,307,401,403,404,429,500,503])
def test_http_errors_are_closed_never_retried(monkeypatch,code):
    stream=BytesIO(b'sensitive raw response')
    error=HTTPError(d.endpoint('crypto_btc'),code,'private',{},stream)
    calls,_,sleeps=fake(monkeypatch,[error])
    assert discover(max_attempts=3).attempt_codes==('public_http_rejected',)
    assert stream.closed and len(calls)==1 and sleeps==[]


@pytest.mark.parametrize('kind',['origin','type','encoding','size','malformed_json','duplicate','bad_shape'])
def test_complete_but_invalid_response_not_retried(monkeypatch,kind):
    r=raw_response()
    if kind=='origin':r.url='https://example.invalid/other'
    elif kind=='type':r.headers.replace_header('Content-Type','text/html')
    elif kind=='encoding':r.headers['Content-Encoding']='gzip'
    elif kind=='size':r.headers.replace_header('Content-Length',str(d.MAX_BODY+1))
    elif kind=='malformed_json':r=raw_response(b'not json')
    elif kind=='duplicate':r=raw_response(b'{"events":[],"events":[]}')
    elif kind=='bad_shape':r=raw_response(b'{"events":null}')
    calls,_,sleeps=fake(monkeypatch,[r])
    assert discover(max_attempts=3).to_dict()['status']=='failed'
    assert len(calls)==1 and sleeps==[] and r.isclosed()


@pytest.mark.parametrize('kwargs',[dict(allow_public_fetch=False),dict(allow_public_fetch=1),dict(max_attempts=True),
    dict(max_attempts=0),dict(max_attempts=4),dict(timeout_seconds=0),dict(timeout_seconds=True)])
def test_invalid_optin_and_config_before_network(monkeypatch,kwargs):
    monkeypatch.setattr(d,'build_opener',lambda *a:pytest.fail('unexpected network'))
    values=dict(allow_public_fetch=True);values.update(kwargs)
    with pytest.raises(ValueError):d.discover_crypto_markets('crypto_btc',**values)


@pytest.mark.parametrize('changes',[dict(active=False),dict(closed=True),dict(active=1),dict(question='Who wins an election?'),
    dict(outcomes=['Up','Down']),dict(conditionId='legacy'),dict(slug='../escape'),dict(endDate=NOW.isoformat()),
    dict(endDate=(NOW+timedelta(hours=2)).isoformat()),dict(endDate=(NOW+timedelta(days=365)).isoformat()),
    dict(endDate='2026-09-14'),dict(question=''),dict(question='ETH price above $2000?')])
def test_ineligible_market_is_not_a_candidate(changes):
    assert d.select_candidates(body([market(**changes)]),'crypto_btc',NOW)==()


def test_empty_is_valid_but_unknown_is_not():
    assert d.select_candidates(body([]),'crypto_btc',NOW)==()
    with pytest.raises(ValueError):d.select_candidates(b'{"events":null}','crypto_btc',NOW)


def test_discovery_order_dedup_and_contradiction():
    early=market(conditionId='0x'+'b'*64,slug='btc-earlier',endDate=(NOW+timedelta(hours=5)).isoformat())
    items=d.select_candidates(body([market(),early,early]),'crypto_btc',NOW)
    assert [x.market_slug for x in items]==['btc-earlier','bitcoin-price-event']
    with pytest.raises(ValueError):d.select_candidates(body([market(),market(slug='conflicting')]),'crypto_btc',NOW)


def test_global_shape_caps_not_silent_truncation():
    for raw in (json.dumps(dict(events=[dict(markets=[])]*101)).encode(),body([market()]*1001)):
        with pytest.raises(ValueError):d.select_candidates(raw,'crypto_btc',NOW)


def test_complete_framing_with_chunked_truncation_is_retried(monkeypatch):
    first=raw_response(b'2\r\n{}\r\n',b'Transfer-Encoding: chunked\r\n')
    fake(monkeypatch,[first,raw_response()])
    assert discover(max_attempts=2).attempt_codes==('public_response_incomplete','received')


def test_invalid_success_trace_and_mutation_fail_closed():
    with pytest.raises(ValueError):d.CryptoDiscovery('crypto_btc',NOW,('received','received'),body())
    with pytest.raises(ValueError):d.CryptoDiscovery('crypto_btc',NOW,('public_timeout',),b'partial')
    value=d.CryptoDiscovery('crypto_btc',NOW,('received',),body())
    object.__setattr__(value,'raw_json',b'{"events":null}')
    with pytest.raises(ValueError):value.to_dict()


def test_interrupt_not_swallowed(monkeypatch):
    def interrupted(*a,**k):raise KeyboardInterrupt()
    monkeypatch.setattr(d,'_one_get',interrupted)
    with pytest.raises(KeyboardInterrupt):discover(max_attempts=3)


@pytest.fixture
def cli():
    path=Path(__file__).resolve().parents[1]/'scripts/discover_crypto_research.py'
    spec=importlib.util.spec_from_file_location('discovery_cli_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_cli_no_implicit_network(cli,monkeypatch,capsys):
    monkeypatch.setattr(cli,'discover_crypto_markets',lambda *a,**k:pytest.fail('network'))
    assert cli.main(['--team','crypto_btc','--preview','--attempts','3'])==0
    assert json.loads(capsys.readouterr().out)['status']=='disabled'


def test_cli_retry_trace_and_no_preview_when_discovery_failed(cli,monkeypatch,capsys):
    monkeypatch.setattr(cli,'discover_crypto_markets',lambda t,**k:d.CryptoDiscovery(t,NOW,('public_timeout',)*3))
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',lambda *a,**k:pytest.fail('preview'))
    assert cli.main(['--team','crypto_btc','--preview','--attempts','3','--allow-public-fetch'])==1
    out=json.loads(capsys.readouterr().out)
    assert out['discovery_request_attempts']==3 and out['public_gets_upper_bound']==3
    assert out['configured_public_gets_ceiling']==6


def test_cli_recovered_discovery_invokes_preview_only_once(cli,monkeypatch,capsys):
    from tests.test_research_crypto_launch import preview
    monkeypatch.setattr(cli,'discover_crypto_markets',lambda t,**k:d.CryptoDiscovery(t,NOW,('public_timeout','received'),body()))
    calls=[]
    def make(spec,**kw):calls.append(spec);return preview()
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',make)
    assert cli.main(['--team','crypto_btc','--preview','--attempts','3','--allow-public-fetch'])==0
    out=json.loads(capsys.readouterr().out)
    assert len(calls)==1 and out['discovery_request_attempts']==2 and out['public_gets_upper_bound']==5
    assert calls[0].model_id=='operator-model-not-selected'
    assert out['results'][0]['recovered_after_failure'] is True


def test_cli_preview_failure_never_retry(cli,monkeypatch,capsys):
    monkeypatch.setattr(cli,'discover_crypto_markets',lambda t,**k:d.CryptoDiscovery(t,NOW,('received',),body()))
    calls=[]
    def error(*a,**k):calls.append(1);raise RuntimeError('private error')
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',error)
    assert cli.main(['--team','crypto_btc','--preview','--allow-public-fetch'])==1
    out=capsys.readouterr().out
    assert calls==[1] and 'private error' not in out
