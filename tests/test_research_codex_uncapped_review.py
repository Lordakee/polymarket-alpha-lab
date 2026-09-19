"""Separate adversarial review pass; no provider, credentials or real database."""
from dataclasses import replace
from datetime import timedelta
import json
import traceback

import pytest

from polymarket_alpha_lab import research_codex_exec as codex
from polymarket_alpha_lab import research_uncapped_runner as runner
from tests.test_research_codex_exec import events, output, action
from tests.test_research_uncapped import approval, Harness, run, req, NOW
from tests.test_research_dispatch_rotation import Harness as RotationHarness, inputs, run as turn


@pytest.mark.parametrize('separator', ['\u0085', '\u2028', '\u2029'])
def test_valid_unicode_inside_json_is_not_a_record_separator(separator):
    rows = events([action(arguments={'query': 'BTC' + separator + 'ETH'})])
    reply = codex.decode_codex_exec_output(output(rows), call_number=1)
    assert json.loads(reply.calls[0].arguments_json)['query'] == 'BTC' + separator + 'ETH'


@pytest.mark.parametrize('limit', [1, 19])
def test_reported_output_overrun_closes_client_without_repair(limit):
    calls = []
    class Host:
        def run(self, request):
            calls.append(request)
            return output(events(output_tokens=20))
    client = codex.CodexExecModel(model_id='model', transport=Host())
    with pytest.raises(ValueError, match='call_failed'):
        client.complete(messages_json='[{}]', max_output_tokens=limit)
    with pytest.raises(ValueError, match='stopped'):
        client.complete(messages_json='[{}]', max_output_tokens=100)
    assert len(calls) == 1


def test_factory_is_not_entered_for_empty_message_array(monkeypatch):
    h = Harness(monkeypatch)
    client = runner._UncappedModel(approval(), req(), h.factory, None)
    with pytest.raises(ValueError):
        client.complete(messages_json='[]', max_output_tokens=10)
    assert h.events == []


def test_expired_authorization_does_not_reserve_a_new_rotation(monkeypatch):
    h = RotationHarness(monkeypatch)
    requests = tuple(r for snap in inputs() for r in snap.stored.batch.requests)
    p = approval(requests)
    monkeypatch.setattr(runner, '_now', lambda: p.expires_at)
    with pytest.raises(ValueError, match='not_available'):
        turn(uncapped_authorization=p, allow_uncapped_costs=True)
    assert h.saved == {} and h.calls == []


@pytest.mark.parametrize('ending', [b'', b'\n', b'\r\n'])
def test_valid_jsonl_ending(ending):
    wire = output().stdout.rstrip(b'\n')
    wire = wire.replace(b'\n', b'\r\n') if ending == b'\r\n' else wire
    assert codex.decode_codex_exec_output(codex.CodexExecOutput(0, wire + ending), call_number=1).total_tokens == 120


@pytest.mark.parametrize('defect', ['new_record_with_cr', 'double_newline', 'trailing_data', 'invalid_utf8'])
def test_non_jsonl_delimiters_and_trailing_content_are_rejected(defect):
    wire = output().stdout
    if defect == 'new_record_with_cr': wire = wire.replace(b'\n', b'\r')
    elif defect == 'double_newline': wire += b'\n'
    elif defect == 'trailing_data': wire += b'PRIVATE-SENTINEL'
    else: wire += b'\xff'
    with pytest.raises(ValueError, match='response_invalid') as error:
        codex.decode_codex_exec_output(codex.CodexExecOutput(0, wire), call_number=1)
    assert 'PRIVATE-SENTINEL' not in ''.join(traceback.format_exception(error.value))


@pytest.mark.parametrize('failure', ['bad_receipt', 'lookup_failure', 'wrong_request'])
def test_expired_history_error_never_falls_through_to_new_claim(monkeypatch, failure):
    h = Harness(monkeypatch)
    original = run(h)
    h.events.clear()
    p = approval()
    monkeypatch.setattr(runner, '_now', lambda: p.expires_at)
    def bad(*args, **kwargs):
        if failure == 'lookup_failure': raise ValueError('synthetic history failure')
        if failure == 'bad_receipt': return object()
        return replace(original, request=replace(original.request, required_source_ids=('s',)))
    monkeypatch.setattr(runner.execution, 'inspect_captured_research_with_psycopg', bad)
    with pytest.raises(ValueError): run(h, authorization=p)
    assert h.events == []


def test_integration_guide_is_shipped_with_its_referring_runbooks():
    from polymarket_alpha_lab.project_postgres.distribution import selected_source
    assert selected_source('docs/research-local-agent.md')


def test_expiry_after_turn_commit_keeps_receipt_but_does_not_start_task(monkeypatch):
    h = RotationHarness(monkeypatch)
    requests = tuple(r for snap in inputs() for r in snap.stored.batch.requests)
    p = approval(requests)
    clock = [p.approved_at+timedelta(seconds=3)]
    monkeypatch.setattr(runner, '_now', lambda: clock[0])
    monkeypatch.setattr(runner.execution, 'inspect_captured_research_with_psycopg', lambda *a, **kw: None)
    h.after_reserve = lambda: clock.__setitem__(0, p.expires_at)
    result = turn(uncapped_authorization=p, allow_uncapped_costs=True)
    assert result.status == 'dispatched' and result.stored is not None
    assert len(result.attempts) == 1 and result.attempts[0].status == 'operation_failed'
    assert h.calls == []
    again = turn(uncapped_authorization=p, allow_uncapped_costs=True)
    assert again.status == 'turn_already_reserved' and again.stored == result.stored
    assert h.calls == []


@pytest.mark.parametrize('messages', [
    r'[{"role":"user","content":"\ud800"}]',
    r'[{"role":"user","content":"\udfff"}]',
    r'[{"\ud800":"value"}]',
    r'[{"role":"user","content":[{"text":"\udfff"}]}]',
])
def test_escaped_surrogate_in_input_rejected_before_transport(messages):
    seen = []
    class Host:
        def run(self, request):
            seen.append(request)
            return output()
    client = codex.CodexExecModel(model_id='model', transport=Host())
    with pytest.raises(ValueError, match='call_failed'):
        client.complete(messages_json=messages, max_output_tokens=100)
    assert seen == []
    with pytest.raises(ValueError, match='stopped'):
        client.complete(messages_json='[{}]', max_output_tokens=100)


@pytest.mark.parametrize('surrogate', ['\ud800', '\udfff'])
@pytest.mark.parametrize('target', ['query', 'source_id', 'summary', 'source_ids'])
def test_escaped_surrogate_in_nested_action_is_not_a_valid_reply(surrogate, target):
    if target == 'query':
        name, args = 'search_evidence', {'query': 'prefix' + surrogate}
    elif target == 'source_id':
        name, args = 'read_evidence', {'source_id': 'prefix' + surrogate}
    else:
        name = 'finish_research'
        args = dict(probability_yes='0.6', confidence='0.4',
                    summary='Synthetic evidence', source_ids=['source-1'])
        args[target] = ['prefix' + surrogate] if target == 'source_ids' else 'prefix' + surrogate
    # All three JSON envelopes are valid UTF-8 bytes; only the final nested
    # action decoder exposes the invalid Unicode scalar. Do not alter the wire.
    selected = dict(name=name, arguments_json=json.dumps(args, ensure_ascii=True))
    with pytest.raises(ValueError, match='response_invalid'):
        codex.decode_codex_exec_output(output(events([selected])), call_number=1)


@pytest.mark.parametrize('messages', [
    r'[{"role":"user","content":"\ud83d\ude00","measurement":0.125}]',
    '[{"role":"user","content":"中文 😀","measurement":0.125}]',
])
def test_valid_unicode_and_decimal_input_preserve_exact_approved_text(messages):
    request = codex.CodexExecInput('model', messages, 100)
    assert request.messages_json == messages
    assert json.loads(request.prompt_json)['messages_json'] == messages


def test_valid_surrogate_pair_inside_action_still_decodes():
    selected = dict(name='search_evidence', arguments_json=r'{"query":"BTC \ud83d\ude00"}')
    reply = codex.decode_codex_exec_output(output(events([selected])), call_number=1)
    assert json.loads(reply.calls[0].arguments_json)['query'] == 'BTC 😀'


@pytest.mark.parametrize('number', [0, 1])
@pytest.mark.parametrize('surrogate', ['\ud800', '\udfff'])
def test_invalid_nested_reply_captures_failure_and_replays_without_host(monkeypatch, number, surrogate):
    h = Harness(monkeypatch)
    request = req(number)
    source_id = request.intake.task.evidence[0].source_id
    seen = []
    class Host:
        def run(self, item):
            seen.append(item)
            if len(seen) == 1:
                return output(events([action('read_evidence', {'source_id': source_id})]))
            args = dict(probability_yes='0.6', confidence='0.4', summary='bad' + surrogate,
                        source_ids=[source_id])
            selected = dict(name='finish_research', arguments_json=json.dumps(args, ensure_ascii=True))
            return output(events([selected]))
    def factory(team):
        assert team == request.intake.team_id
        return codex.CodexExecModel(model_id=request.model_id, transport=Host())
    result = run(h, request=request, model_factory=factory)
    assert result.status == 'captured'
    research = result.record.run.research
    assert research.status == 'failed' and research.reason_code == 'model_failed'
    assert research.summary == '' and research.source_ids == ()
    assert research.model_calls == 2 and research.total_tokens == 120
    assert len(seen) == 2 and h.events == ['claim', 'capture']
    assert result.request.content_sha256 == request.content_sha256
    replay = run(h, request=request, model_factory=lambda _: pytest.fail('replayed host'))
    assert replay == result and len(seen) == 2
