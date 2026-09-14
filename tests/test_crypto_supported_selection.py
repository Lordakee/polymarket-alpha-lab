"""WP-01 orchestration: real gates and synthetic public sources, no model/DB."""
from dataclasses import replace
from datetime import timedelta
import importlib.util
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab import research_crypto_selection as s
from polymarket_alpha_lab.research_crypto_discovery import CryptoDiscovery
from polymarket_alpha_lab.research_crypto_launch import CryptoResearchPreview, CryptoResearchSpec
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from tests.test_research_crypto_launch import NOW, snapshots


def setup(monkeypatch, kinds=('good',), *, team='crypto_btc', codes=('received',), final='good', clocks=None):
    events, metadata, search_rows = [], {}, []
    for n, kind in enumerate(kinds):
        cid, slug = '0x'+f'{n+1:064x}', f'selected-event-{n}'
        spec = CryptoResearchSpec('fixture', team, cid, slug, NOW+timedelta(minutes=30), 'not-called')
        m, _, _ = snapshots(spec)
        data = json.loads(m.raw_json)
        data['endDate'] = (NOW+timedelta(days=1, minutes=n)).isoformat()
        search_rows.append(dict(data))
        if kind == 'path':
            data['description'] += ' Any candle Low counts.'
        elif kind == 'past':
            data['question'] = data['question'].replace('September 13, 2026', 'September 12, 2026')
        elif kind == 'closed': data['closed'] = True
        elif kind == 'unknown': data['description'] = 'Unclassified synthetic rule.'
        elif kind == 'identity': data['conditionId'] = '0x'+'f'*64
        elif kind == 'missing_rules': data.pop('description')
        elif kind == 'missing_active': data.pop('active')
        raw = b'broken-json' if kind == 'bad_json' else json.dumps(data).encode()
        metadata[slug] = (OSError('private-transport-detail') if kind == 'error'
                         else None if kind == 'invalid' else GammaMarketSnapshot(slug, NOW, raw))
    raw_search = json.dumps(dict(events=[dict(markets=search_rows)])).encode()
    discovery = CryptoDiscovery(team, NOW, codes, raw_search if codes[-1]=='received' else None)
    def discover(*args, **kwargs):
        events.append(('discovery', args, kwargs));return discovery
    monkeypatch.setattr(s, 'discover_crypto_markets', discover)
    if clocks is None:
        monkeypatch.setattr(s, '_now', lambda: NOW)
    else:
        times=iter(clocks);monkeypatch.setattr(s, '_now', lambda: next(times))
    class Reader:
        def __init__(self, *, allow_public_fetch): assert allow_public_fetch is True
        def fetch(self, *, market_slug):
            events.append(('metadata',market_slug))
            value=metadata[market_slug]
            if isinstance(value, Exception): raise value
            return value
    monkeypatch.setattr(s, 'GammaResearchReader', Reader)
    def preview(spec, *, allow_public_fetch):
        assert allow_public_fetch is True
        events.append(('preview', spec))
        if final=='error': raise OSError('private-preview-detail')
        if final=='invalid': return object()
        m, cb, kr = snapshots(spec)
        if final=='path':
            data=json.loads(m.raw_json);data['description']+=' Any candle Low counts.'
            m=replace(m,raw_json=json.dumps(data).encode())
        if final=='wrong_id': spec=replace(spec,record_id='wrong-id')
        return CryptoResearchPreview(spec, NOW, NOW, m, cb, kr)
    monkeypatch.setattr(s,'fetch_crypto_research_preview',preview)
    return events, discovery


def run(**kw):
    return s.select_supported_crypto('crypto_btc', allow_public_fetch=True, **kw)


def names(events): return [e[0] for e in events]


@pytest.mark.parametrize('team', ['crypto_btc','crypto_eth'])
def test_skips_path_and_past_before_one_real_gated_preview(monkeypatch, team):
    ev,_=setup(monkeypatch,('path','past','good','good'),team=team)
    r=s.select_supported_crypto(team,allow_public_fetch=True)
    assert r['status']=='ready_for_operator_review'
    assert [x['status'] for x in r['checks']]==['scope_blocked','time_blocked','eligible_for_preview']
    assert r['checked_count']==3 and r['unexamined_count']==1
    assert r['public_gets_upper_bound']==7 and r['configured_public_gets_ceiling']==9
    assert names(ev)==['discovery','metadata','metadata','metadata','preview']
    assert r['pending_spec']['operator_approved'] is False
    assert r['pending_spec']['model_id']=='operator-model-not-selected'
    assert r['pending_spec']['terms_sha256']==r['preview']['terms_sha256']
    assert r['preview']['forecast_start_status']=='requires_operator_approval'
    assert r['source_suitability_review_required'] is True
    assert r['preview']['contract_scope']['settlement_source_verified'] is False
    assert r['preview']['required_source_ids'] and r['model_called'] is r['database_written'] is False
    assert r['selection_is_approval'] is False and r['selection_is_global_scan'] is False


@pytest.mark.parametrize('kind', ['error','invalid','bad_json','identity','missing_rules'])
def test_unreadable_information_is_not_no_eligible_market(monkeypatch, kind):
    ev,_=setup(monkeypatch,(kind,))
    r=run()
    assert r['status']=='candidate_checks_failed'
    assert r['failed_check_count']==1 and r['eligibility_scan_complete'] is False
    assert r['preview_invocations']==0 and r['pending_spec'] is None
    assert r['public_gets_upper_bound']==2
    assert names(ev)==['discovery','metadata']
    assert 'private-' not in json.dumps(r)


def test_failures_remain_visible_when_later_market_succeeds(monkeypatch):
    ev,_=setup(monkeypatch,('error','good'),codes=('public_response_incomplete','received'))
    r=run(max_attempts=3)
    assert r['status']=='ready_for_operator_review' and r['failed_check_count']==1
    assert r['recovered_after_failure'] is True
    assert [x['reason_code'] for x in r['attempts']]==['public_response_incomplete','received']
    assert r['public_gets_upper_bound']==7 and not r['eligibility_scan_complete']
    assert names(ev).count('metadata')==2 and names(ev).count('preview')==1


@pytest.mark.parametrize('kinds,status', [((),'no_candidates_in_search_page'),
    (('path','past','closed','unknown'),'no_eligible_in_search_page')])
def test_empty_or_rejected_page_is_bounded_not_global(monkeypatch, kinds, status):
    ev,_=setup(monkeypatch,kinds)
    r=run()
    assert r['status']==status and r['unexamined_count']==0 and r['failed_check_count']==0
    assert r['preview_invocations']==0 and 'preview' not in names(ev)
    assert r['one_page_only'] is True and r['selection_is_global_scan'] is False


@pytest.mark.parametrize('limit', [1,2,5,10])
def test_candidate_limit_is_hard_and_unexamined_not_rejected(monkeypatch, limit):
    ev,_=setup(monkeypatch,('path',)*10+('good',))
    r=run(max_candidates=limit)
    assert r['status']=='candidate_check_limit_reached'
    assert r['checked_count']==limit and r['unexamined_count']==11-limit
    assert not r['eligibility_scan_complete'] and r['preview_invocations']==0
    assert names(ev).count('metadata')==limit and r['public_gets_upper_bound']==1+limit


@pytest.mark.parametrize('final,expected', [('error','preview_failed'),('invalid','preview_failed'),
    ('wrong_id','preview_failed'),('path','preview_no_longer_eligible')])
def test_failed_or_changed_preview_never_tries_next_candidate(monkeypatch, final, expected):
    ev,_=setup(monkeypatch,('good','good'),final=final)
    r=run()
    assert r['status']==expected and r['pending_spec'] is None
    assert r['unexamined_count']==1 and r['public_gets_upper_bound']==5
    assert names(ev)==['discovery','metadata','preview']
    assert 'private-' not in str(r)


def test_discovery_failure_does_not_open_metadata_reader(monkeypatch):
    ev,_=setup(monkeypatch,codes=('public_timeout',)*3)
    monkeypatch.setattr(s,'GammaResearchReader',lambda **k:pytest.fail('unnecessary metadata reader'))
    r=run(max_attempts=3)
    assert r['status']=='discovery_failed' and r['request_attempts']==3
    assert r['metadata_get_attempts']==0 and r['public_gets_upper_bound']==3
    assert names(ev)==['discovery']


def test_same_slug_different_condition_refused_before_lookup(monkeypatch):
    ev,d=setup(monkeypatch,('good','good'))
    data=json.loads(d.raw_json);rows=data['events'][0]['markets'];rows[1]['slug']=rows[0]['slug']
    changed=replace(d,raw_json=json.dumps(data).encode())
    monkeypatch.setattr(s,'discover_crypto_markets',lambda *a,**k:changed)
    r=run()
    assert r['status']=='discovery_identity_conflict' and r['checked_count']==0 and ev==[]


@pytest.mark.parametrize('config', [dict(max_candidates=0),dict(max_candidates=11),dict(max_candidates=True),
    dict(max_attempts=0),dict(max_attempts=4),dict(max_attempts=True),dict(cutoff_lead_minutes=0),
    dict(cutoff_lead_minutes=61),dict(cutoff_lead_minutes=True),dict(allow_public_fetch=False),
    dict(allow_public_fetch=1),dict(team_id='politics')])
def test_invalid_configuration_before_network(monkeypatch, config):
    monkeypatch.setattr(s,'discover_crypto_markets',lambda *a,**k:pytest.fail('invalid configuration I/O'))
    args=dict(team_id='crypto_btc',allow_public_fetch=True);args.update(config)
    with pytest.raises(ValueError):s.select_supported_crypto(**args)


@pytest.mark.parametrize('clocks,kinds,metadata', [
    ([NOW,NOW+timedelta(minutes=30)],('good',),0),
    ([NOW,NOW,NOW,NOW+timedelta(minutes=30)],('path','good'),1),
    ([NOW,NOW,NOW,NOW+timedelta(minutes=30)],('good',),1),
    ([NOW,NOW,NOW+timedelta(minutes=30)],('good',),1),
])
def test_expiry_stops_before_next_request_or_preview(monkeypatch, clocks, kinds, metadata):
    ev,_=setup(monkeypatch,kinds,clocks=clocks)
    r=run()
    assert r['status']=='selection_cutoff_elapsed' and r['pending_spec'] is None
    assert names(ev).count('metadata')==metadata and 'preview' not in names(ev)
    assert r['public_gets_upper_bound']==1+metadata
    assert r['temporary_forecast_cutoff_at']==(NOW+timedelta(minutes=30)).isoformat()


@pytest.mark.parametrize('clocks,kinds,metadata', [
    ([NOW-timedelta(seconds=1)],('good',),0),
    ([NOW,NOW-timedelta(seconds=1)],('good',),0),
    ([NOW,NOW,NOW-timedelta(seconds=1)],('good',),1),
    ([NOW,NOW,NOW,NOW-timedelta(seconds=1)],('path','good'),1),
])
def test_clock_rollback_stops_before_next_stage(monkeypatch, clocks, kinds, metadata):
    ev,_=setup(monkeypatch,kinds,clocks=clocks)
    r=run()
    assert r['status']=='selection_clock_regressed'
    assert names(ev).count('metadata')==metadata and 'preview' not in names(ev)


def test_cutoff_expiring_after_preview_does_not_expose_pending_spec(monkeypatch):
    ev,_=setup(monkeypatch,clocks=[NOW,NOW,NOW,NOW,NOW+timedelta(minutes=30)])
    r=run()
    assert r['status']=='selection_cutoff_elapsed' and r['pending_spec'] is None
    assert r['preview_invocations']==1 and r['public_gets_upper_bound']==5


def test_interrupt_propagates_without_retry(monkeypatch):
    ev,_=setup(monkeypatch)
    class Reader:
        def __init__(self,**kw):pass
        def fetch(self,**kw):raise KeyboardInterrupt()
    monkeypatch.setattr(s,'GammaResearchReader',Reader)
    with pytest.raises(KeyboardInterrupt):run()
    assert names(ev)==['discovery']


@pytest.fixture
def cli():
    path=Path(__file__).resolve().parents[1]/'scripts/discover_crypto_research.py'
    spec=importlib.util.spec_from_file_location('supported_selection_cli',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_cli_disabled_before_any_selection(cli,monkeypatch,capsys):
    monkeypatch.setattr(s,'select_supported_crypto',lambda *a,**k:pytest.fail('disabled I/O'))
    assert cli.main(['--team','crypto_btc','--select-supported'])==0
    assert json.loads(capsys.readouterr().out)['public_gets_upper_bound']==0


@pytest.mark.parametrize('flags', [['--preview','--select-supported'],['--max-candidates','2'],
    ['--cutoff-lead-minutes','5'],['--select-supported','--max-candidates','11']])
def test_cli_invalid_combinations_before_io(cli,monkeypatch,flags):
    monkeypatch.setattr(s,'select_supported_crypto',lambda *a,**k:pytest.fail('invalid I/O'))
    with pytest.raises(SystemExit) as e:cli.main(['--team','crypto_btc',*flags])
    assert e.value.code==2


def test_cli_two_teams_and_duplicate_team_share_explicit_ceiling(cli,monkeypatch,capsys):
    calls=[]
    def select(team,**kwargs):
        calls.append((team,kwargs))
        return dict(status='ready_for_operator_review',configured_public_gets_ceiling=8,
                    request_attempts=2,public_gets_upper_bound=6)
    monkeypatch.setattr(s,'select_supported_crypto',select)
    args=['--team','crypto_btc','--team','crypto_eth','--team','crypto_btc','--select-supported',
          '--max-candidates','3','--attempts','2','--allow-public-fetch']
    assert cli.main(args)==0
    r=json.loads(capsys.readouterr().out)
    assert len(calls)==2 and r['configured_public_gets_ceiling']==16 and r['public_gets_upper_bound']==12
    assert all(x[1]['max_candidates']==3 and x[1]['max_attempts']==2 for x in calls)
    assert r['model_called'] is r['database_written'] is False


def test_cli_real_controller_and_gates(cli,monkeypatch,capsys):
    ev,_=setup(monkeypatch,('path','good'))
    assert cli.main(['--team','crypto_btc','--select-supported','--allow-public-fetch'])==0
    r=json.loads(capsys.readouterr().out)
    assert r['results'][0]['status']=='ready_for_operator_review'
    assert r['results'][0]['pending_spec']['operator_approved'] is False


def test_cli_failure_is_fixed_and_count_unknown_not_zero(cli,monkeypatch,capsys):
    def fail(*a,**k):raise RuntimeError('private-injected-detail')
    monkeypatch.setattr(s,'select_supported_crypto',fail)
    assert cli.main(['--team','crypto_btc','--select-supported','--allow-public-fetch'])==1
    out=capsys.readouterr().out
    assert 'private-injected-detail' not in out
    assert json.loads(out)['public_gets_upper_bound'] is None


def test_missing_open_flag_is_unknown_not_complete_negative_evidence(monkeypatch):
    setup(monkeypatch,('missing_active',))
    r=run()
    assert r['status']=='candidate_checks_failed'
    assert r['checks'][0]['status']=='check_failed'
    assert r['eligibility_scan_complete'] is False


def test_discovery_trace_cannot_exceed_requested_allowance(monkeypatch):
    ev,_=setup(monkeypatch,codes=('public_timeout','received'))
    with pytest.raises(ValueError,match='selection_discovery_budget_invalid'):
        run(max_attempts=1)
    assert 'metadata' not in names(ev) and 'preview' not in names(ev)
