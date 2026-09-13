"""Public probe and synthetic demo stay free of database/model activity."""
from dataclasses import replace
from datetime import UTC, datetime
import json

import pytest

from scripts import probe_research_resolution as probe, run_resolution_review_demo as demo
from tests.test_research_resolution import submission


def args():
    item = submission(confirmation=False)
    return ['--condition-id',item.condition_id,'--market-slug',item.snapshot.market_slug]


@pytest.mark.parametrize('extra', ([], ['--condition-id','not-canonical']))
def test_preflight_does_not_construct_reader(monkeypatch,extra):
    def forbidden(**kwargs):
        pytest.fail('invalid/disabled public request')
    monkeypatch.setattr(probe,'GammaResearchReader',forbidden)
    with pytest.raises(SystemExit):
        probe.main(args()+extra)


def test_public_probe_never_claims_independent_confirmation(monkeypatch,capsys):
    calls = []
    snapshot = replace(submission(confirmation=False).snapshot, fetched_at=datetime.now(UTC))
    class Reader:
        def __init__(self,**kw):
            assert kw == {'allow_public_fetch':True}
        def fetch(self,**kw):
            calls.append(kw)
            return snapshot
    monkeypatch.setattr(probe,'GammaResearchReader',Reader)
    assert probe.main(args()+['--allow-public-fetch']) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['assessment']['status']=='needs_confirmation'
    assert output['outcome_recorded'] is False
    assert output['live_model_called'] is False
    assert output['independent_confirmation_performed'] is False
    assert calls == [{'market_slug':snapshot.market_slug}]


def test_public_probe_redacts_provider_failure(monkeypatch,capsys):
    def broken(**kwargs):
        raise RuntimeError('synthetic-provider-detail')
    monkeypatch.setattr(probe,'GammaResearchReader',broken)
    assert probe.main(args()+['--allow-public-fetch'])==1
    output = capsys.readouterr()
    assert 'synthetic-provider-detail' not in output.out + output.err
    assert json.loads(output.out)['reason_code']=='resolution_public_probe_failed'
