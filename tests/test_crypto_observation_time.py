"""Observation time, not delayed listing end, gates prospective research."""
from datetime import UTC, datetime, timedelta

import pytest

from polymarket_alpha_lab import research_crypto_launch as core
from tests.test_research_crypto_launch import NOW, preview, spec


def test_past_observation_cannot_be_forecast_despite_future_market_end():
    p = preview(question='Will Ethereum be above $2,000 on September 12, 2026?')
    with pytest.raises(core.CryptoLaunchBlocked, match='observation_not_future'):
        p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])


def test_forecast_cutoff_must_precede_observation_candle_open():
    p = preview(spec(forecast_cutoff_at=NOW.replace(hour=17)))
    with pytest.raises(core.CryptoLaunchBlocked, match='cutoff_not_before_observation'):
        p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])


def test_missing_year_is_not_inferred_from_system_clock_or_listing_end():
    p = preview(question='Will Ethereum be above $2,000 on September 13?')
    with pytest.raises(core.CryptoLaunchBlocked, match='observation_year_missing'):
        p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])

from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import json

from polymarket_alpha_lab import research_crypto_observation as clock
from polymarket_alpha_lab import research_crypto_launch_service as service

RULES = ('This market will resolve to "Yes" if the Close price of the Binance ETH/USDT '
         '1-minute candle at 12:00 PM ET on the date in the title is above $2,000. '
         'Otherwise it will resolve to "No".')


def assess(**changes):
    args = dict(team_id='crypto_eth', question='Will Ethereum be above $2,000 on September 13, 2026?',
                resolution_criteria=RULES, market_slug='synthetic-event', as_of=NOW,
                forecast_cutoff_at=NOW+timedelta(hours=1), scheduled_end_at=NOW+timedelta(days=1))
    args.update(changes)
    return clock.assess_crypto_observation_time(**args)


@pytest.mark.parametrize('month,day,hour', [('January',15,17),('July',15,16),
    ('March',7,17),('March',8,16),('November',1,17),('October',31,16)])
def test_et_noon_uses_calendar_dst_not_fixed_offset(month,day,hour):
    m = clock._MONTHS.index(month.lower())+1
    date = datetime(2026,m,day,tzinfo=UTC)
    result = assess(question=f'Will Ethereum be above $2,000 on {month} {day}, 2026?',
                    as_of=date, forecast_cutoff_at=date+timedelta(hours=1),
                    scheduled_end_at=date+timedelta(days=1))
    assert result.candle_open_at == date.replace(hour=hour)
    assert result.new_launch_time_eligible
    value = result.to_dict()
    assert value['timezone'] == 'America/New_York'
    assert value['timestamp_computed'] is True
    assert value['observation_time_independently_verified'] is False
    assert value['settlement_source_verified'] is False
    assert value['date_basis'] == 'question_year'
    assert value['tzdata_version']
    assert datetime.fromisoformat(value['candle_close_not_before'])-result.candle_open_at == timedelta(minutes=1)


@pytest.mark.parametrize('label,hour', [('12:00 AM',0),('12:00 PM',12),('1:15 PM',13),('11:30 PM',23)])
def test_utc_am_pm_and_minute_close_boundary(label,hour):
    minute = int(label[3:5]) if label.startswith('12') else int(label.split(':')[1][:2])
    result=assess(resolution_criteria=RULES.replace('12:00 PM ET',label+' UTC'),
        as_of=NOW-timedelta(days=1),forecast_cutoff_at=NOW-timedelta(hours=13))
    assert result.candle_open_at==NOW.replace(hour=hour,minute=minute,second=0)
    assert result.timezone_key=='UTC' and result.tzdata_version is None
    assert result.new_launch_time_eligible


def test_documented_noon_wording_and_matching_slug_supply_explicit_year():
    rules=('This market will resolve to "Yes" if the Binance 1 minute candle for '
           'ETH/USDT 12:00 in the ET timezone (noon) on the title date has a final '
           '"Close" price higher than the price in the title. Otherwise, this market will resolve to "No".')
    value=assess(question='Will Ethereum be above $2,000 on September 13?',resolution_criteria=rules,
                 market_slug='ethereum-above-2000-on-september-13-2026')
    assert value.new_launch_time_eligible and value.date_basis=='dated_slug'
    assert value.candle_open_at==datetime(2026,9,13,16,tzinfo=UTC)


@pytest.mark.parametrize('slug', ['ethereum-above-2000-on-september-14-2026',
    'ethereum-above-2000-on-october-13-2026','ethereum-above-2000-on-september-13-2027'])
def test_explicit_title_and_slug_disagreement_is_not_silently_resolved(slug):
    value=assess(market_slug=slug)
    assert value.reason=='date_conflict' and value.candle_open_at is None
    assert not value.new_launch_time_eligible


@pytest.mark.parametrize('date', ['February 29, 2026','April 31, 2026','September 0, 2026','September 32, 2026'])
def test_impossible_date_is_not_rolled_forward(date):
    value=assess(question=f'Will Ethereum be above $2,000 on {date}?')
    assert value.reason=='date_invalid' and value.candle_open_at is None


def test_valid_leap_day_is_preserved():
    at=datetime(2028,2,28,tzinfo=UTC)
    value=assess(question='Will Ethereum be above $2,000 on February 29, 2028?',
        as_of=at,forecast_cutoff_at=at+timedelta(hours=1),scheduled_end_at=at+timedelta(days=3))
    assert value.candle_open_at==datetime(2028,2,29,17,tzinfo=UTC)


@pytest.mark.parametrize('date,label,reason', [('March 8, 2026','2:30 AM','clock_nonexistent'),
    ('November 1, 2026','1:30 AM','clock_ambiguous')])
def test_dst_gap_and_fold_block_instead_of_guessing(date,label,reason):
    value=assess(question=f'Will Ethereum be above $2,000 on {date}?',
                 resolution_criteria=RULES.replace('12:00 PM',label))
    assert value.reason==reason and not value.new_launch_time_eligible
    assert value.to_dict()['candle_open_at'] is None


@pytest.mark.parametrize('delta,allowed', [(-1,True),(0,False),(1,False)])
def test_cutoff_must_be_strictly_before_open_including_microseconds(delta,allowed):
    opening=datetime(2026,9,13,16,tzinfo=UTC)
    value=assess(forecast_cutoff_at=opening+timedelta(microseconds=delta))
    assert value.new_launch_time_eligible is allowed
    if not allowed: assert value.reason=='cutoff_not_before_observation'


@pytest.mark.parametrize('delta', [0,1,59,60,600])
def test_after_open_is_not_prospective_even_before_candle_close(delta):
    at=datetime(2026,9,13,16,tzinfo=UTC)+timedelta(seconds=delta)
    value=assess(as_of=at,forecast_cutoff_at=at+timedelta(hours=1))
    assert value.reason=='not_future'
    assert not value.new_launch_time_eligible


def test_future_listing_end_is_not_the_observation_year():
    value=assess(question='Will Ethereum be above $2,000 on September 13?',
                 scheduled_end_at=datetime(2027,9,14,tzinfo=UTC))
    assert value.reason=='year_missing'
    assert value.to_dict()['candle_close_not_before'] is None


def test_listing_cannot_end_before_observation_but_can_equal_open():
    opening=datetime(2026,9,13,16,tzinfo=UTC)
    assert assess(scheduled_end_at=opening-timedelta(seconds=1)).reason=='listing_end_before_observation'
    assert assess(scheduled_end_at=opening).new_launch_time_eligible


@pytest.mark.parametrize('suffix', [' Also at 11:00 AM ET.', ' Also at 12:00 PM UTC.',
    ' Also at 9:00 CST.'])
def test_multiple_or_unsupported_clock_mentions_do_not_select_first(suffix):
    assert assess(resolution_criteria=RULES+suffix).reason=='clock_unsupported'


@pytest.mark.parametrize('change', ['on a different date', 'on the next day', 'on September 14, 2026'])
def test_rules_must_link_time_to_title_date(change):
    result=assess(resolution_criteria=RULES.replace('on the date in the title',change))
    assert result.reason=='rules_date_unsupported' and not result.new_launch_time_eligible


@pytest.mark.parametrize('error', [ImportError('private package path'),OSError('private IO path'),ValueError('bad TZif')])
def test_timezone_data_failure_blocks_without_host_fallback_or_leak(monkeypatch,error):
    def fail():raise error
    monkeypatch.setattr(clock,'_new_york',fail)
    value=assess()
    assert value.reason=='timezone_unavailable' and value.candle_open_at is None
    assert 'private' not in json.dumps(value.to_dict())
    assert assess(resolution_criteria=RULES.replace('PM ET','PM UTC'),
                  as_of=NOW-timedelta(days=1),forecast_cutoff_at=NOW-timedelta(hours=13)).new_launch_time_eligible


def test_package_timezone_does_not_use_environment_or_system_tzpath(monkeypatch):
    import zoneinfo
    old=zoneinfo.TZPATH
    monkeypatch.setenv('TZ','Pacific/Honolulu')
    monkeypatch.setenv('PYTHONTZPATH','/unavailable/timezone-data')
    zoneinfo.reset_tzpath(())
    try:
        result=assess()
        assert result.candle_open_at==datetime(2026,9,13,16,tzinfo=UTC)
    finally:zoneinfo.reset_tzpath(old)


@pytest.mark.parametrize('name',['as_of','forecast_cutoff_at','scheduled_end_at'])
def test_naive_input_times_are_rejected(name):
    with pytest.raises(ValueError):assess(**{name:NOW.replace(tzinfo=None)})


def test_equal_instants_in_different_timezones_give_equal_results():
    zone=ZoneInfo('Asia/Taipei')
    assert assess(as_of=NOW.astimezone(zone),forecast_cutoff_at=(NOW+timedelta(hours=1)).astimezone(zone))==assess()


def test_unknown_scope_cannot_be_promoted_by_a_date():
    result=assess(question='Will Ethereum touch $2,000 on September 13, 2026?')
    assert result.reason=='scope_unsupported'
    assert result.candle_open_at is None


def test_output_mutation_does_not_bypass_new_request_gate():
    p=preview(question='Will Ethereum be above $2,000 on September 12, 2026?')
    output=p.to_dict()
    assert output['status']=='prepared' and output['forecast_start_status']=='blocked_by_observation_time'
    output['observation_schedule']['new_launch_time_eligible']=True
    output['observation_schedule']['candle_open_at']='2030-01-01T00:00:00+00:00'
    with pytest.raises(core.CryptoLaunchBlocked,match='not_future'):
        p.request(approved_terms_sha256=output['terms_sha256'])
    assert p.to_dict()['observation_schedule']['new_launch_time_eligible'] is False


def test_time_gate_blocks_before_claim_or_model_for_prepared_input(monkeypatch):
    p=preview(question='Will Ethereum be above $2,000 on September 12, 2026?')
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:None)
    monkeypatch.setattr(service.execution,'run_captured_research_with_psycopg',lambda *a,**k:pytest.fail('claim started'))
    with pytest.raises(core.CryptoLaunchBlocked,match='not_future'):
        service.launch_crypto_research_with_psycopg('opaque',spec=p.spec,preview=p,
            approved_terms_sha256=p.to_dict()['terms_sha256'],model_factory=lambda _:pytest.fail('model'),
            allow_public_fetch=True,allow_model_calls=True)


def test_delayed_submission_keeps_cutoff_for_existing_database_clock_guard():
    p=preview()
    report=p.to_dict()
    request=p.request(approved_terms_sha256=report['terms_sha256'])
    assert request.forecast_cutoff_at < datetime.fromisoformat(report['observation_schedule']['candle_open_at'])
    assert request.forecast_cutoff_at==p.spec.forecast_cutoff_at
    assert request.intake.task.question==report['question']


def test_existing_old_dated_capture_replayed_without_new_time_certification(monkeypatch):
    from polymarket_alpha_lab.research_execution import CapturedResearchRequest
    p=preview(question='Will Ethereum be above $2,000 on September 12, 2026?')
    terms,check,intake=p._prepared()
    old_request=CapturedResearchRequest(p.spec.record_id,p.spec.model_id,p.spec.protocol(),p.spec.forecast_cutoff_at,
        intake,limits=p.spec.limits,required_source_ids=tuple(r.source_id for r in check.source_receipts))
    old=SimpleNamespace(request=old_request,status='already_captured')
    monkeypatch.setattr(service.execution,'inspect_captured_research_with_psycopg',lambda *a,**k:old)
    monkeypatch.setattr(service,'fetch_crypto_research_preview',lambda *a,**k:pytest.fail('refetch'))
    monkeypatch.setattr(service.execution,'run_captured_research_with_psycopg',lambda *a,**k:pytest.fail('rewrite'))
    result=service.launch_crypto_research_with_psycopg('opaque',spec=p.spec,
        approved_terms_sha256=terms['terms_sha256'],model_factory=lambda _:pytest.fail('model'),
        allow_public_fetch=True,allow_model_calls=True)
    assert result is old


def test_result_flags_and_frozen_contract():
    result=assess()
    with pytest.raises(FrozenInstanceError):result.reason='ready'
    object.__setattr__(result,'reason','approved')
    with pytest.raises(ValueError):result.to_dict()
    with pytest.raises(ValueError):clock.CryptoObservationTime('requires_operator_review')


def test_clock_suffix_cannot_silently_change_et_offset():
    value=assess(resolution_criteria=RULES.replace('PM ET','PM ET+1'))
    assert value.reason=='clock_unsupported'


def test_other_numeric_date_without_year_cannot_override_title():
    value=assess(resolution_criteria=RULES+' The observation date is 09/14.')
    assert value.reason=='rules_date_unsupported'
