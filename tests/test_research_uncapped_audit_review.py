"""Separate adversarial review of audit error priority and returned bindings."""
from dataclasses import replace
from datetime import timedelta

import pytest

from polymarket_alpha_lab import research_uncapped_audit as values
from polymarket_alpha_lab import research_uncapped_audit_store as store
from tests.test_research_uncapped_audit import AuditHarness, start
from tests.test_research_uncapped import req, NOW, run


@pytest.mark.parametrize('interrupt', [KeyboardInterrupt(),SystemExit(0)])
def test_new_interrupt_during_failure_logging_is_not_swallowed(monkeypatch, interrupt):
    h = AuditHarness(monkeypatch); h.finish_error = interrupt
    def factory(team): raise ValueError('ordinary provider failure')
    with pytest.raises(type(interrupt)) as caught:
        run(h,model_factory=factory,require_durable_audit=True)
    assert caught.value is interrupt
    assert 'capture' not in h.events and h.events.count('outcome_failed') == 1


def test_snapshot_rejects_next_call_before_previous_reply_recorded():
    one = start(); two = start(2,started_at=NOW+timedelta(seconds=5))
    out = values.UncappedCallOutcome(one,'returned',2,'a'*64,NOW+timedelta(seconds=6))
    with pytest.raises(ValueError): values.UncappedAuditSnapshot(req().record_id,(one,two),(out,))


@pytest.mark.parametrize('changes', [dict(authorization_id='other'),dict(call_number=2),dict(message_sha256='f'*64)])
def test_corrupt_start_receipt_never_enters_client(monkeypatch, changes):
    h = AuditHarness(monkeypatch); original = store._begin_call
    def wrong(*args,**kwargs): return replace(original(*args,**kwargs),**changes)
    monkeypatch.setattr(store,'_begin_call',wrong)
    result = run(h,require_durable_audit=True)
    assert result.record.run.research.status == 'failed'
    assert 'factory' not in h.events and 'complete' not in h.events
    assert not h.outcomes


@pytest.mark.parametrize('changes', [dict(reply_sha256='f'*64),dict(reported_total_tokens=123),
    dict(status='failed',reported_total_tokens=None,reply_sha256=None)])
def test_corrupt_success_receipt_suppresses_reply_and_next_call(monkeypatch, changes):
    h = AuditHarness(monkeypatch); original = store._finish_call
    def wrong(*args,**kwargs): return replace(original(*args,**kwargs),**changes)
    monkeypatch.setattr(store,'_finish_call',wrong)
    result = run(h,require_durable_audit=True)
    assert result.record.run.research.status == 'failed'
    assert h.events.count('complete') == h.events.count('outcome_returned') == 1
    assert 'outcome_failed' not in h.events
