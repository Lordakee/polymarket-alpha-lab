"""Prospective launch gates using synthetic snapshots and no real HTTP/DB/model."""
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
import importlib.util
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab import research_crypto_launch as core
from polymarket_alpha_lab import research_crypto_launch_service as service
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits
from polymarket_alpha_lab.team_research_cross_source import CrossSourcePolicy
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from tests.test_team_research_cross_source import fixtures, alter, Model

NOW = datetime(2026, 9, 13, 12, 10, tzinfo=UTC)
CID = '0x' + 'a' * 64


def spec(**changes):
    data = dict(record_id='prospective-1', team_id='crypto_eth', condition_id=CID,
                market_slug='synthetic-event', forecast_cutoff_at=NOW+timedelta(hours=1),
                model_id='synthetic-function-model')
    data.update(changes)
    return core.CryptoResearchSpec(**data)


def snapshots(s=None, at=NOW, **market_changes):
    s = s or spec()
    asset, ticker = ('Bitcoin', 'BTC') if s.team_id == 'crypto_btc' else ('Ethereum', 'ETH')
    # An actual dated observation, not the machine's current year. Keep the
    # native proof prospective even when it runs late in the UTC day.
    observed_date = at.date() + timedelta(days=0 if at.hour < 14 else 1)
    months = ('January','February','March','April','May','June','July','August',
              'September','October','November','December')
    title_date = f'{months[observed_date.month-1]} {observed_date.day}, {observed_date.year}'
    latest_noon = datetime(observed_date.year, observed_date.month, observed_date.day, 19, tzinfo=UTC)
    end = max(at + timedelta(days=1), latest_noon)
    raw = dict(slug=s.market_slug, conditionId=s.condition_id,
               question=f'Will the price of {asset} be above $2,000 on {title_date}?',
               description=(f'This market will resolve to \"Yes\" if the Close price of the Binance {ticker}/USDT '
                            '1-minute candle at 12:00 PM ET on the date in the title is above $2,000. '
                            'Otherwise it will resolve to \"No\". Synthetic fixture only.'), active=True, closed=False,
               outcomes='["Yes","No"]', endDate=end.isoformat())
    raw.update(market_changes)
    window = core.candle_window(s, at)
    cb, kr = fixtures(window)
    return (GammaMarketSnapshot(s.market_slug, at, json.dumps(raw).encode()),
            replace(cb, fetched_at=at), replace(kr, fetched_at=at))


def preview(s=None, **changes):
    s = s or spec()
    m, cb, kr = snapshots(s, **changes)
    return core.CryptoResearchPreview(s, NOW, NOW, m, cb, kr)


def test_protocol_does_not_fragment_cohort_by_record_or_event():
    first = spec()
    second = spec(record_id='prospective-2', condition_id='0x'+'b'*64, market_slug='another-event',
                  forecast_cutoff_at=NOW+timedelta(hours=2))
    # Protocol represents research configuration, NOT an event/task identifier.
    assert first.protocol() == second.protocol()


@pytest.mark.parametrize('team,product', [('crypto_btc','BTC-USD'),('crypto_eth','ETH-USD')])
def test_complete_preparation_requires_two_sources_and_has_no_probabilities(team,product):
    p=preview(spec(team_id=team));out=p.to_dict()
    req=p.request(approved_terms_sha256=out['terms_sha256'])
    assert req.intake.status=='prepared' and req.intake.team_id==team
    assert p.coinbase.window.product_id==product
    assert len(req.required_source_ids)==2 and len(req.intake.task.evidence)==2
    assert out['compared_candles']==3 and out['readiness_only'] is True
    assert out['model_called'] is out['database_written'] is False
    assert 'probability_yes' not in out and 'raw_json' not in str(out)
    assert req.intake.task.question==out['question']
    assert req.intake.task.resolution_criteria==out['resolution_criteria']
    assert p.coinbase.raw_json==snapshots(spec(team_id=team))[1].raw_json
    assert 'raw_json' not in repr(p)
    with pytest.raises(FrozenInstanceError):p.as_of=NOW


@pytest.mark.parametrize('changes', [dict(record_id='bad id'),dict(team_id='politics'),dict(condition_id='legacy'),
    dict(condition_id='0x'+'A'*64),dict(market_slug='../escape'),dict(model_id=''),dict(lookback_hours=True),
    dict(lookback_hours=0),dict(lookback_hours=25),dict(limits={}),dict(policy={}),dict(readonly=False),
    dict(paper_only=1),dict(report_only=False),dict(forecast_cutoff_at=NOW.replace(tzinfo=None))])
def test_spec_invalid(changes):
    with pytest.raises(ValueError):spec(**changes)


@pytest.mark.parametrize('changes,reason', [({'closed':True},'market_not_open'),({'active':False},'market_not_open'),
    ({'conditionId':'0x'+'b'*64},'market_identity_mismatch'),({'description':''},'missing_resolution_criteria'),
    ({'endDate':NOW.isoformat()},'market_already_ended'),({'outcomes':['Up','Down']},'unsupported_market_outcomes'),
    ({'endDate':(NOW+timedelta(minutes=20)).isoformat()},'cutoff_not_before_market_end')])
def test_bad_market_blocks(changes,reason):
    with pytest.raises(core.CryptoLaunchBlocked,match=reason):preview(**changes)


def test_explicit_cutoff_never_defaults_to_scheduled_end():
    with pytest.raises(core.CryptoLaunchBlocked,match='cutoff_elapsed'):preview(spec(forecast_cutoff_at=NOW))
    with pytest.raises(core.CryptoLaunchBlocked,match='cutoff_not_before'):preview(spec(forecast_cutoff_at=NOW+timedelta(days=1)))


def test_terms_approval_ignores_quotes_but_not_question_rules_or_cutoff():
    p=preview();h=p.to_dict()['terms_sha256']
    quotes=preview(outcomePrices=['0.1','0.9'],volume='12345')
    assert quotes.to_dict()['terms_sha256']==h
    for other in (preview(question='Changed?'),preview(description='Changed rules.'),
                  preview(spec(forecast_cutoff_at=NOW+timedelta(hours=2)))):
        with pytest.raises(core.CryptoLaunchBlocked,match='approval_mismatch'):other.request(approved_terms_sha256=h)


@pytest.mark.parametrize('bad',['0'*64,'A'*64,'',None,True])
def test_wrong_approval_never_builds_request(bad):
    with pytest.raises(ValueError):preview().request(approved_terms_sha256=bad)


def test_window_is_closed_and_utc_even_in_repeated_local_hour():
    s=spec();w=core.candle_window(s,NOW.astimezone(timezone(timedelta(hours=8))))
    assert w.end==NOW.replace(minute=0)-timedelta(hours=1)
    assert w.start==w.end-timedelta(hours=3)
    assert w.expected_count==3
    assert core.candle_window(s,NOW)==w


def test_snapshot_mutation_and_wrong_window_are_revalidated():
    p=preview();wrong=replace(p.coinbase,window=replace(p.coinbase.window,end=p.coinbase.window.end+timedelta(hours=1)))
    with pytest.raises(core.CryptoLaunchBlocked,match='window_mismatch'):replace(p,coinbase=wrong)
    object.__setattr__(p.kraken,'readonly',False)
    with pytest.raises(ValueError):p.to_dict()
    with pytest.raises(ValueError):p.request(approved_terms_sha256='a'*64)


@pytest.mark.parametrize('name',['market','coinbase','kraken'])
@pytest.mark.parametrize('delta',[-1,1])
def test_snapshots_must_be_collected_in_selected_run(name,delta):
    p=preview();wrong=replace(getattr(p,name),fetched_at=NOW+timedelta(seconds=delta))
    with pytest.raises(core.CryptoLaunchBlocked,match='snapshot_clock'):replace(p,**{name:wrong})


def test_cross_source_disagreement_stops_before_request():
    p=preview()
    bad=alter(p.kraken,lambda body,rows: rows[0].__setitem__(4,'200'))
    with pytest.raises(core.CryptoLaunchBlocked,match='close_price_divergence'):replace(p,kraken=bad)


@pytest.fixture
def transport(monkeypatch):
    calls=[]
    monkeypatch.setattr(service,'_now',lambda:NOW)
    m,cb,kr=snapshots()
    class Gamma:
        def __init__(self,allow_public_fetch=False):assert allow_public_fetch is True
        def fetch(self,*,market_slug):calls.append('gamma');return m
    class Coinbase:
        def __init__(self,enabled):assert enabled is True
        def fetch(self,window):calls.append('coinbase');assert window==cb.window;return cb
    class Kraken:
        def __init__(self,enabled):assert enabled is True
        def fetch(self,window):calls.append('kraken');assert window==kr.window;return kr
    monkeypatch.setattr(service,'GammaResearchReader',Gamma)
    monkeypatch.setattr(service,'CoinbaseCandleReader',Coinbase)
    monkeypatch.setattr(service,'KrakenCandleReader',Kraken)
    return calls,Gamma,Coinbase,Kraken


def test_public_preview_reads_three_sources_once_without_database(transport,monkeypatch):
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:pytest.fail('preview DB'))
    result=service.fetch_crypto_research_preview(spec(),allow_public_fetch=True)
    assert result.to_dict()['status']=='prepared' and transport[0]==['gamma','coinbase','kraken']


@pytest.mark.parametrize('opt',[False,1,None,'true'])
def test_no_public_optin_no_work(transport,opt):
    with pytest.raises(ValueError):service.fetch_crypto_research_preview(spec(),allow_public_fetch=opt)
    assert transport[0]==[]


@pytest.mark.parametrize('index,label',[(1,'gamma'),(2,'coinbase'),(3,'kraken')])
def test_transport_failure_is_fixed_redacted_and_not_retried(transport,monkeypatch,index,label):
    def fail(*a,**k):raise OSError('secret-error-detail')
    monkeypatch.setattr(transport[index],'fetch',fail)
    with pytest.raises(core.CryptoLaunchBlocked,match=label+'_fetch_failed') as e:
        service.fetch_crypto_research_preview(spec(),allow_public_fetch=True)
    assert 'secret-error-detail' not in str(e.value)
    assert len(transport[0])==index-1


def test_closed_market_stops_before_venues(transport,monkeypatch):
    monkeypatch.setattr(transport[1],'fetch',lambda *a,**k:snapshots(closed=True)[0])
    with pytest.raises(core.CryptoLaunchBlocked):service.fetch_crypto_research_preview(spec(),allow_public_fetch=True)
    assert transport[0]==[]


def test_elapsed_cutoff_stops_before_public_requests(transport):
    with pytest.raises(core.CryptoLaunchBlocked):service.fetch_crypto_research_preview(spec(forecast_cutoff_at=NOW),allow_public_fetch=True)
    assert transport[0]==[]


def launch(p=None,**changes):
    p=p or preview()
    kw=dict(spec=p.spec,approved_terms_sha256=p.to_dict()['terms_sha256'],model_factory=lambda _:Model(),
            allow_public_fetch=True,allow_model_calls=True)
    kw.update(changes)
    return service.launch_crypto_research_with_psycopg('opaque-test-only',**kw)


@pytest.mark.parametrize('key,value',[('allow_public_fetch',False),('allow_model_calls',False),('allow_model_calls',1),
    ('approved_terms_sha256',''),('model_factory',None),('preview',object())])
def test_launch_permission_before_database(transport,monkeypatch,key,value):
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:pytest.fail('unexpected DB'))
    with pytest.raises(ValueError):launch(**{key:value})
    assert transport[0]==[]


def test_new_launch_uses_existing_claim_runner_and_bound_sources(transport,monkeypatch):
    order=[]
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:order.append('inspect'))
    def execute(dsn,*,request,model_factory):
        order.append('existing-runner')
        assert request.intake.status=='prepared' and len(request.required_source_ids)==2
        assert dsn=='opaque-test-only'
        return 'existing-receipt'
    monkeypatch.setattr(service.execution,'run_captured_research_with_psycopg',execute)
    assert launch()=='existing-receipt'
    assert order==['inspect','existing-runner'] and transport[0]==['gamma','coinbase','kraken']


def test_existing_claim_returned_without_any_fetch_model_or_write(transport,monkeypatch):
    p=preview();req=p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])
    result=SimpleNamespace(request=req,status='incomplete')
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:result)
    monkeypatch.setattr(service.execution,'run_captured_research_with_psycopg',lambda *a,**k:pytest.fail('repeat run'))
    assert launch(model_factory=lambda _:pytest.fail('repeat model')) is result
    assert transport[0]==[]


@pytest.mark.parametrize('changes',[dict(lookback_hours=2),dict(model_id='different'),dict(team_id='crypto_btc'),
    dict(condition_id='0x'+'b'*64),dict(market_slug='other'),dict(forecast_cutoff_at=NOW+timedelta(hours=2)),
    dict(limits=ResearchAgentLimits(max_model_calls=1)),dict(policy=CrossSourcePolicy(Decimal('200')))])
def test_reused_id_changed_spec_refused_before_refetch(transport,monkeypatch,changes):
    p=preview();req=p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:SimpleNamespace(request=req))
    with pytest.raises(service.ResearchCaptureConflict):launch(spec=spec(**changes))
    assert transport[0]==[]


def test_supplied_preview_avoids_refetch_but_revalidates_approval(transport,monkeypatch):
    p=preview();monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:None)
    seen=[];monkeypatch.setattr(service.execution,'run_captured_research_with_psycopg',lambda *a,**k:seen.append(k['request']))
    launch(preview=p)
    assert len(seen)==1 and transport[0]==[]
    with pytest.raises(core.CryptoLaunchBlocked):launch(preview=p,approved_terms_sha256='0'*64)
    assert len(seen)==1


def test_remote_dsn_rejected_by_existing_read_before_http(transport):
    p=preview()
    with pytest.raises(ValueError):service.launch_crypto_research_with_psycopg('postgresql://user@192.0.2.1/db',
        spec=p.spec,approved_terms_sha256=p.to_dict()['terms_sha256'],model_factory=lambda _:Model(),
        allow_public_fetch=True,allow_model_calls=True)
    assert transport[0]==[]


def test_interruption_not_swallowed(transport,monkeypatch):
    def interrupt(*a,**k):raise KeyboardInterrupt()
    monkeypatch.setattr(transport[1],'fetch',interrupt)
    with pytest.raises(KeyboardInterrupt):service.fetch_crypto_research_preview(spec(),allow_public_fetch=True)


@pytest.fixture
def cli():
    path=Path(__file__).resolve().parents[1]/'scripts/preview_crypto_research.py'
    module_spec=importlib.util.spec_from_file_location('crypto_preview_cli_test',path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    return module


def arguments():
    return ['--record-id','preview-only','--team','crypto_eth','--condition-id',CID,'--market-slug','synthetic-event',
            '--forecast-cutoff',(NOW+timedelta(hours=1)).isoformat(),'--model','no-model-called']


def test_cli_default_has_no_network(cli,monkeypatch,capsys):
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',lambda *a,**k:pytest.fail('implicit I/O'))
    assert cli.main(arguments())==0
    assert json.loads(capsys.readouterr().out)['status']=='disabled'


def test_cli_actual_preview_flag_not_model(cli,monkeypatch,capsys):
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',lambda *a,**k:preview())
    assert cli.main([*arguments(),'--allow-public-fetch'])==0
    out=json.loads(capsys.readouterr().out)
    assert out['status']=='prepared' and out['model_called'] is out['database_written'] is False


def test_cli_unexpected_exception_redacted(cli,monkeypatch,capsys):
    def fail(*a,**k):raise RuntimeError('secret-private-error')
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',fail)
    assert cli.main([*arguments(),'--allow-public-fetch'])==1
    out=capsys.readouterr().out
    assert 'secret-private-error' not in out


def test_cli_invalid_timestamp_rejected_before_any_io(cli,monkeypatch):
    args=arguments();args[args.index('--forecast-cutoff')+1]='2026-10-01'
    monkeypatch.setattr(cli,'fetch_crypto_research_preview',lambda *a,**k:pytest.fail('invalid spec'))
    with pytest.raises(SystemExit) as e:cli.main([*args,'--allow-public-fetch'])
    assert e.value.code==2


def test_reused_id_wrong_approval_refused_without_refetch(transport,monkeypatch):
    p=preview();req=p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:SimpleNamespace(request=req))
    with pytest.raises(service.ResearchCaptureConflict):launch(approved_terms_sha256='0'*64)
    assert transport[0]==[]


def test_different_tasks_same_configuration_remain_same_cohort():
    first=preview();second=preview(spec(record_id='prospective-2',condition_id='0x'+'b'*64,market_slug='other'))
    req1=first.request(approved_terms_sha256=first.to_dict()['terms_sha256'])
    req2=second.request(approved_terms_sha256=second.to_dict()['terms_sha256'])
    assert req1.protocol_version==req2.protocol_version
    assert req1.intake.task_id!=req2.intake.task_id
    assert first.to_dict()['terms_sha256']!=second.to_dict()['terms_sha256']
