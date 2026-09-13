"""Contract scope is separate from fresh, consistent reference-price inputs."""
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab import research_crypto_launch as core
from polymarket_alpha_lab import research_crypto_launch_service as service
from polymarket_alpha_lab.research_crypto_contract_scope import assess_crypto_contract_scope, CryptoContractScope
from tests.test_research_crypto_launch import preview, spec

PATH_QUESTION = 'Will Bitcoin dip to $66,000 September 7-13?'
PATH_RULES = ('This market will resolve to "Yes" if any Binance BTC/USDT 1-minute candle '
              'during the stated period has a Low at or below $66,000. Otherwise it will '
              'resolve to "No". Synthetic contract fixture; not real observations.')


def path_preview():
    return preview(spec(team_id='crypto_btc'), question=PATH_QUESTION, description=PATH_RULES)


def test_touch_event_cannot_be_launched_on_recent_hourly_reference_bars():
    p = path_preview()
    digest = p.to_dict()['terms_sha256']
    with pytest.raises(core.CryptoLaunchBlocked, match='path_history_required'):
        p.request(approved_terms_sha256=digest)


def test_unknown_contract_does_not_default_to_terminal_price():
    p = preview(question='Synthetic YES/NO event?', description='Unclassified settlement rules.')
    with pytest.raises(core.CryptoLaunchBlocked, match='contract_scope_unsupported'):
        p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])


def test_input_preview_reports_scope_block_without_claiming_bad_transport():
    report = path_preview().to_dict()
    assert report['status'] == 'prepared' and report['readiness_only'] is True
    assert report['contract_scope']['kind'] == 'path_dependent'
    assert report['contract_scope']['new_launch_policy_eligible'] is False
    assert report['forecast_start_status'] == 'blocked_by_contract_scope'
    assert report['model_called'] is report['database_written'] is False


def assess(question=None, rules=None, team='crypto_eth'):
    p = preview(spec(team_id=team))
    terms, _, _ = p._prepared()
    return assess_crypto_contract_scope(team, question or terms['question'], rules or terms['resolution_criteria'])


@pytest.mark.parametrize('team', ['crypto_btc', 'crypto_eth'])
def test_supported_terminal_hints_still_require_review_and_do_not_verify_oracle(team):
    p = preview(spec(team_id=team))
    report = p.to_dict()
    scope = report['contract_scope']
    assert scope['kind'] == 'terminal_price_hint'
    assert scope['new_launch_policy_eligible'] is True
    assert report['forecast_start_status'] == 'requires_operator_approval'
    assert scope['operator_terms_approval_required'] is True
    assert scope['classification_is_semantic_proof'] is scope['settlement_source_verified'] is False
    assert scope['history_coverage_verified'] is scope['observation_time_verified'] is False
    assert scope['reference_quote'] == 'USD' and scope['reference_candle_seconds'] == 3600
    assert scope['warning_codes'] == ['reference_feeds_not_settlement_verification',
        'observation_time_not_verified', 'binance_vs_reference_venues', 'usd_vs_usdt', 'hourly_vs_minute']
    req = p.request(approved_terms_sha256=report['terms_sha256'])
    assert len(req.required_source_ids) == 2
    assert req.intake.task.resolution_criteria == report['resolution_criteria']


@pytest.mark.parametrize('marker', ['touch', 'hit', 'reach', 'dip', 'ever', 'at any time',
    'at least once', 'throughout', 'remain', 'lowest', 'highest', 'Low', 'High', 'every 1-minute candle'])
def test_path_marker_in_rules_overrides_terminal_question(marker):
    p = preview()
    rules = p.to_dict()['resolution_criteria'] + ' Also inspect ' + marker + ' in the event period.'
    s = assess(rules=rules)
    assert s.kind == 'path_dependent'
    assert s.to_dict()['complete_contract_history_required'] is True
    assert not s.new_launch_policy_eligible


@pytest.mark.parametrize('marker', ['average', 'averaged', 'averaging', 'mean', 'median', 'TWAP', 'VWAP'])
def test_aggregate_rules_need_full_window_not_recent_closes(marker):
    p = preview()
    s = assess(rules=p.to_dict()['resolution_criteria'] + ' Use the ' + marker + ' over the period.')
    assert s.kind == 'aggregate_price'
    assert s.reason_code == 'crypto_launch_aggregate_history_required'
    assert not s.new_launch_policy_eligible


@pytest.mark.parametrize('question', ['Will Ethereum exceed $2,000?', 'Ethereum above $2,000?',
    'Will Ethereum be above $2,000 on September 13? Also touch $3,000?',
    'Will the price of Bitcoin be above $2,000 on September 13?', '以太坊是否高于两千美元？'])
def test_unsupported_or_cross_asset_question_cannot_default_to_eligible(question):
    assert assess(question=question).new_launch_policy_eligible is False


@pytest.mark.parametrize('defect', ['missing_clock', 'missing_minute', 'missing_close', 'missing_otherwise',
    'opposite_direction', 'negated', 'compound', 'different_asset', 'multiple_conditions'])
def test_incomplete_or_conflicting_terminal_rules_are_unclassified(defect):
    rules = preview().to_dict()['resolution_criteria']
    if defect == 'missing_clock': rules = rules.replace('at 12:00 PM ET', 'at an unspecified time')
    elif defect == 'missing_minute': rules = rules.replace('1-minute', 'unknown-frequency')
    elif defect == 'missing_close': rules = rules.replace('Close', 'mark')
    elif defect == 'missing_otherwise': rules = rules.split('Otherwise')[0].strip()
    elif defect == 'opposite_direction': rules = rules.replace('is above', 'is below')
    elif defect == 'negated': rules = rules.replace('is above', 'is not above')
    elif defect == 'compound': rules = rules.replace('is above $2,000', 'is above $2,000 and another condition is met')
    elif defect == 'different_asset': rules = rules.replace('ETH/USDT', 'BTC/USDT')
    elif defect == 'multiple_conditions': rules = rules + ' ' + rules
    assert assess(rules=rules).kind == 'unclassified'


def test_lower_terminal_and_presentation_normalization():
    p = preview()
    question = p.to_dict()['question'].replace('above', 'below')
    rules = p.to_dict()['resolution_criteria'].replace('above', 'below')
    assert assess(question, rules).new_launch_policy_eligible
    rules = rules.replace('"Yes"', '“Yes”').replace('"No"', '“No”').replace('1-minute', '１-minute')
    assert assess(question.upper(), rules).kind == 'terminal_price_hint'
    rules += ' The candle Ｌｏｗ also counts.'
    assert assess(question, rules).kind == 'path_dependent'


@pytest.mark.parametrize('kwargs', [dict(team_id='sports'), dict(question=''), dict(resolution_criteria=''),
    dict(question='x'*2001), dict(resolution_criteria='x'*4001), dict(question=1)])
def test_input_contract_is_bounded(kwargs):
    args = dict(team_id='crypto_eth', question='Question?', resolution_criteria='Rules')
    args.update(kwargs)
    with pytest.raises(ValueError): assess_crypto_contract_scope(**args)


def test_mutation_does_not_manufacture_an_approval_or_change_raw_terms():
    p = path_preview()
    original_rules = p._prepared()[0]['resolution_criteria']
    report = p.to_dict()
    report['contract_scope']['kind'] = 'terminal_price_hint'
    report['contract_scope']['new_launch_policy_eligible'] = True
    with pytest.raises(core.CryptoLaunchBlocked, match='path_history_required'):
        p.request(approved_terms_sha256=report['terms_sha256'])
    assert p.to_dict()['resolution_criteria'] == original_rules
    assert p.to_dict()['contract_scope']['kind'] == 'path_dependent'


@pytest.mark.parametrize('lookback', [1, 3, 24])
def test_lookback_length_cannot_stand_in_for_contract_source_history(lookback):
    p = preview(spec(team_id='crypto_btc', lookback_hours=lookback), question=PATH_QUESTION, description=PATH_RULES)
    with pytest.raises(core.CryptoLaunchBlocked, match='path_history_required'):
        p.request(approved_terms_sha256=p.to_dict()['terms_sha256'])


def test_launch_blocks_before_claim_factory_or_model(monkeypatch):
    p = path_preview()
    monkeypatch.setattr(service.execution, 'inspect_captured_research_with_psycopg', lambda *a, **k: None)
    monkeypatch.setattr(service.execution, 'run_captured_research_with_psycopg', lambda *a, **k: pytest.fail('claim'))
    monkeypatch.setattr(service, 'fetch_crypto_research_preview', lambda *a, **k: pytest.fail('refetch'))
    with pytest.raises(core.CryptoLaunchBlocked, match='path_history_required'):
        service.launch_crypto_research_with_psycopg('opaque', spec=p.spec, preview=p,
            approved_terms_sha256=p.to_dict()['terms_sha256'], model_factory=lambda _: pytest.fail('model'),
            allow_public_fetch=True, allow_model_calls=True)


def test_legacy_captured_request_replay_remains_readonly_not_recertified(monkeypatch):
    # Old captures were constructed before the scope gate. They remain readable
    # and do not trigger a new model run or a rewrite of historical receipts.
    from polymarket_alpha_lab.research_execution import CapturedResearchRequest
    p = path_preview()
    terms, check, intake = p._prepared()
    request = CapturedResearchRequest(p.spec.record_id, p.spec.model_id, p.spec.protocol(),
        p.spec.forecast_cutoff_at, intake, limits=p.spec.limits,
        required_source_ids=tuple(r.source_id for r in check.source_receipts))
    old = SimpleNamespace(request=request, status='already_captured')
    monkeypatch.setattr(service.execution, 'inspect_captured_research_with_psycopg', lambda *a, **k: old)
    monkeypatch.setattr(service.execution, 'run_captured_research_with_psycopg', lambda *a, **k: pytest.fail('rewrite'))
    monkeypatch.setattr(service, 'fetch_crypto_research_preview', lambda *a, **k: pytest.fail('refetch'))
    actual = service.launch_crypto_research_with_psycopg('opaque', spec=p.spec,
        approved_terms_sha256=terms['terms_sha256'], model_factory=lambda _: pytest.fail('model'),
        allow_public_fetch=True, allow_model_calls=True)
    assert actual is old


def test_scope_diagnostics_do_not_depend_on_live_quote_or_approval_hash():
    a, b = preview(), preview(outcomePrices=['0.01', '0.99'], volume='900000')
    assert a.to_dict()['contract_scope'] == b.to_dict()['contract_scope']
    assert a.to_dict()['terms_sha256'] == b.to_dict()['terms_sha256']
    # Do not split cohorts by event text or append untrusted annotations to rules.
    assert a.spec.protocol() == b.spec.protocol()


def test_scope_value_revalidates_unsupported_mutation():
    s = assess()
    object.__setattr__(s, 'kind', 'approved')
    with pytest.raises(ValueError): s.to_dict()
    with pytest.raises(ValueError): s.new_launch_policy_eligible
    with pytest.raises(ValueError): CryptoContractScope('unclassified', ())


def test_conflicting_explicit_threshold_is_not_a_terminal_candidate():
    rules = preview().to_dict()['resolution_criteria'].replace('above $2,000', 'above $3,000')
    assert assess(rules=rules).kind == 'unclassified'


def test_documented_noon_candle_wording_is_a_hint_not_a_resolved_time():
    rules = ('This market will resolve to "Yes" if the Binance 1 minute candle for '
             'ETH/USDT 12:00 in the ET timezone (noon) on the title date has a final '
             '"Close" price higher than the price in the title. Otherwise, this market '
             'will resolve to "No". Synthetic wording fixture only.')
    result = assess(rules=rules)
    assert result.kind == 'terminal_price_hint'
    assert result.to_dict()['observation_time_verified'] is False


def test_unclassified_history_requirement_is_unknown_not_false():
    result = assess(question='Unclassified event?').to_dict()
    assert result['kind'] == 'unclassified'
    assert result['complete_contract_history_required'] is None
    assert result['new_launch_policy_eligible'] is False
