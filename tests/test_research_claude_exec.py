"""Closed Claude result protocol and real synthetic subprocesses; no provider."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import traceback

import pytest

from polymarket_alpha_lab import research_claude_exec as cli
from polymarket_alpha_lab.research_process import ResearchProcessResult, ResearchProcessSpec
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.team_research_agent_types import strict_json

MODEL = 'claude-opus-5'
SESSION = '11111111-1111-4111-8111-111111111111'


def action(name='search_evidence', **args):
    return {'name': name, 'arguments_json': json.dumps(args or {'query': '*'}, ensure_ascii=True)}


def envelope(calls=None, **changes):
    value = dict(type='result', subtype='success', is_error=False, num_turns=1,
        session_id=SESSION, duration_ms=4, duration_api_ms=3, stop_reason='end_turn',
        result=json.dumps({'calls': [action()] if calls is None else calls}, ensure_ascii=True),
        permission_denials=[], usage=dict(input_tokens=3, output_tokens=5,
            cache_creation_input_tokens=7, cache_read_input_tokens=11),
        modelUsage={MODEL: dict(inputTokens=3, outputTokens=5,
            cacheCreationInputTokens=7, cacheReadInputTokens=11)})
    value.update(changes)
    return value


def wire(value=None):
    return ResearchProcessResult(json.dumps(envelope() if value is None else value,
        ensure_ascii=True, separators=(',', ':')).encode('utf-8'), 0, 20)


def decode(value=None, **kw):
    return cli.decode_claude_result(wire(value), request=cli.ClaudeExecInput(MODEL, '[{}]', 100),
                                   call_number=kw.pop('call_number', 1), **kw)


@pytest.mark.parametrize('messages', ['[{"role":"user","content":"中文 😀"}]',
    r'[{"role":"user","content":"\ud83d\ude00","decimal":0.123456789123456789}]'])
def test_exact_transcript_and_valid_unicode_preserved(messages):
    request = cli.ClaudeExecInput(MODEL, messages, 100)
    assert json.loads(request.prompt_json)['messages_json'] == messages
    assert 'messages_json=' not in repr(request)
    assert 'action_definitions' in json.loads(request.prompt_json)


@pytest.mark.parametrize('messages', ['', '[]', '{}', 'null', '[NaN]', '[{"x":1,"x":2}]',
    r'[{"content":"\ud800"}]', r'[{"\udfff":"value"}]', '[{"x":"\ud800"}]'])
def test_invalid_input_rejected_without_builder_entry(messages):
    model = cli.ClaudeProcessModel(model_id=MODEL,
        prepare_command=lambda _: pytest.fail('builder entered'), allow_process_start=True)
    with pytest.raises(ValueError, match='call_failed'):
        model.complete(messages_json=messages, max_output_tokens=100)
    with pytest.raises(ValueError, match='stopped'):
        model.complete(messages_json='[{}]', max_output_tokens=100)


def test_cache_usage_is_additive_not_codex_subset_accounting():
    reply = decode()
    assert reply.total_tokens == 26
    assert reply.calls[0].call_id == 'claude-1-0'
    assert decode(call_number=2).calls[0].call_id == 'claude-2-0'


@pytest.mark.parametrize('change', [
    {'type':'assistant'}, {'subtype':'error_max_turns'}, {'is_error':1}, {'is_error':True},
    {'num_turns':0}, {'num_turns':2}, {'num_turns':True}, {'num_turns':'1'},
    {'stop_reason':'max_tokens'}, {'stop_reason':'tool_use'}, {'stop_reason':None},
    {'session_id':'not-uuid'}, {'uuid':'bad'}, {'duration_ms':True}, {'duration_api_ms':-1},
    {'permission_denials':[{'tool':'Bash'}]}, {'permission_denials':{}}, {'errors':['SECRET-SENTINEL']},
    {'errors':False}, {'deferred_tool_use':{}}, {'structured_output':{}},
    {'api_error_status':429}, {'origin':{'kind':'remote'}}, {'terminal_reason':'unknown'},
    {'extra':'SECRET-SENTINEL'}, {'total_cost_usd':True}, {'total_cost_usd':-1},
    {'total_cost_usd':'0'}, {'total_cost_usd':float('inf')}, {'result':{}},
])
def test_unacceptable_result_is_fixed_code(change):
    with pytest.raises(ValueError, match='response_invalid') as caught:
        decode(envelope(**change))
    assert 'SECRET-SENTINEL' not in ''.join(traceback.format_exception(caught.value))


@pytest.mark.parametrize('field', list(envelope()))
def test_missing_required_result_fields_fail_closed(field):
    value = envelope(); del value[field]
    with pytest.raises(ValueError, match='response_invalid'): decode(value)


@pytest.mark.parametrize('field', ['input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'])
@pytest.mark.parametrize('bad', [True, -1, '5', 1.5, 1000001])
def test_usage_must_be_bounded_integers(field, bad):
    value = envelope(); value['usage'][field] = bad
    with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('mutation', ['different_model','extra_model','disagree','missing','extra',
                                     'web_search','server_tool','cache_mismatch','fast'])
def test_model_usage_consistency_and_no_hidden_tools(mutation):
    value = envelope()
    if mutation=='different_model': value['modelUsage'] = {'claude-other': value['modelUsage'][MODEL]}
    elif mutation=='extra_model': value['modelUsage']['claude-other'] = value['modelUsage'][MODEL]
    elif mutation=='disagree': value['modelUsage'][MODEL]['inputTokens'] = 4
    elif mutation=='missing': del value['usage']['cache_read_input_tokens']
    elif mutation=='extra': value['usage']['unreviewed'] = 0
    elif mutation=='web_search': value['modelUsage'][MODEL]['webSearchRequests'] = 1
    elif mutation=='server_tool': value['usage']['server_tool_use'] = dict(web_search_requests=0,web_fetch_requests=1)
    elif mutation=='cache_mismatch': value['usage']['cache_creation'] = dict(ephemeral_5m_input_tokens=0,ephemeral_1h_input_tokens=0)
    elif mutation=='fast': value['usage']['service_tier'] = 'fast'
    with pytest.raises(ValueError): decode(value)


def test_optional_metadata_and_decimal_cost_are_validated_but_not_returned():
    value = envelope(total_cost_usd=0.01, uuid=SESSION, errors=[], origin=None)
    value['usage'].update(service_tier='standard', server_tool_use=dict(web_search_requests=0,web_fetch_requests=0),
                         cache_creation=dict(ephemeral_5m_input_tokens=2,ephemeral_1h_input_tokens=5))
    value['modelUsage'][MODEL].update(webSearchRequests=0,costUSD=0.01,contextWindow=200000,maxOutputTokens=8192)
    reply = decode(value)
    assert reply.total_tokens == 26 and not hasattr(reply,'cost_usd')


@pytest.mark.parametrize('calls', [[], [action()]*9, [dict(name='Bash',arguments_json='{}')],
    [dict(name='read_evidence',arguments_json='{"source_id":"\\ud800"}')],
    [dict(name='read_evidence',arguments_json='{"source_id":"x","extra":0}')],
    [dict(name='search_evidence',arguments_json='{"query":"*"}',call_id='external')],
    [action('finish_research', probability_yes='0.5',confidence='0.2',summary='ok',source_ids=['x']),action()],
])
def test_original_action_contract_and_nested_unicode(calls):
    with pytest.raises(ValueError): decode(envelope(calls))


@pytest.mark.parametrize('defect',['duplicate','trailing','array','bom','invalid_utf8','empty','oversize'])
def test_bad_wire_never_becomes_valid_result(defect):
    raw = wire().stdout
    if defect=='duplicate': raw = b'{"type":"result",'+raw[1:]
    elif defect=='trailing': raw += b'\nSECRET-SENTINEL'
    elif defect=='array': raw = b'['+raw+b']'
    elif defect=='bom': raw = b'\xef\xbb\xbf'+raw
    elif defect=='invalid_utf8': raw = b'\xff'+raw
    elif defect=='empty': raw=b''
    else: raw = b' '*1048577
    with pytest.raises(ValueError):
        cli.decode_claude_result(ResearchProcessResult(raw,0,1),
            request=cli.ClaudeExecInput(MODEL,'[{}]',100),call_number=1)


@pytest.mark.parametrize('limit', [4,5,6])
def test_reported_output_boundary(limit):
    request = cli.ClaudeExecInput(MODEL, '[{}]', limit)
    if limit < 5:
        with pytest.raises(ValueError): cli.decode_claude_result(wire(),request=request,call_number=1)
    else:
        assert cli.decode_claude_result(wire(),request=request,call_number=1).total_tokens == 26


def test_zero_total_and_aggregate_overflow_rejected():
    for number in (0,500000):
        value = envelope()
        value['usage'] = dict.fromkeys(value['usage'],number)
        value['modelUsage'][MODEL] = dict.fromkeys(value['modelUsage'][MODEL],number)
        with pytest.raises(ValueError): decode(value)


# --- The demonstrated 25-key terminal representation (L7 final ruling) ------
# Real values of the retained success capture: stdout 1671 bytes, zero stderr,
# first recorded failing stage outer_keys. The result string below is the
# capture's exact 106-character action serialization.
RETAINED_RESULT = ('{"calls": [{"name": "search_evidence", '
                   '"arguments_json": "{\\"query\\": \\"SYNTHETIC-PAL-MOCK-RESPONSE\\"}"}]}')
RETAINED_KEYS = ('api_error_status', 'duration_api_ms', 'duration_ms',
    'fast_mode_disabled_reason', 'fast_mode_state', 'first_content_frame_ms',
    'is_error', 'modelUsage', 'num_turns', 'permission_denials', 'queued_turn_count',
    'result', 'result_index', 'session_id', 'stop_reason', 'subagent_stats', 'subtype',
    'terminal_reason', 'time_to_request_ms', 'total_cost_usd', 'ttft_ms',
    'ttft_stream_ms', 'type', 'usage', 'uuid')


def retained(**changes):
    value = dict(
        type='result', subtype='success', is_error=False, num_turns=1,
        session_id='79622c9f-b24e-4e73-a5d2-4e4c986dca9c',
        uuid='a6ed1d43-a57e-4afd-b723-1890b5c1a071',
        duration_ms=583, duration_api_ms=340, stop_reason='end_turn',
        time_to_request_ms=208, ttft_stream_ms=282, first_content_frame_ms=284, ttft_ms=322,
        result=RETAINED_RESULT, permission_denials=[], api_error_status=None,
        terminal_reason='completed', total_cost_usd=0.00018925000000000002,
        fast_mode_state='off', fast_mode_disabled_reason='disabled_by_env',
        queued_turn_count=0, result_index=0,
        subagent_stats=dict(spawned=0, requested=dict(background=0, foreground=0, unset=0),
            started_in_background=0, max_depth=0, spawned_by_subagents=0, completed=0,
            failed=0, killed=dict(parent=0, user=0, system=0),
            refused=dict(depth_limit=0, concurrency_limit=0, budget=0), by_type={}),
        usage=dict(input_tokens=3, output_tokens=5, cache_creation_input_tokens=7,
            cache_read_input_tokens=11, output_tokens_details=dict(thinking_tokens=0),
            server_tool_use=dict(web_search_requests=0, web_fetch_requests=0),
            service_tier='standard',
            cache_creation=dict(ephemeral_1h_input_tokens=0, ephemeral_5m_input_tokens=0),
            inference_geo='', iterations=[], speed='standard'),
        modelUsage={MODEL: dict(inputTokens=3, outputTokens=5, cacheReadInputTokens=11,
            cacheCreationInputTokens=7, webSearchRequests=0,
            costUSD=0.00018925000000000002, contextWindow=200000, maxOutputTokens=64000,
            thinkingTokens=0, canonicalModel=MODEL, provider='firstParty', costBasis='list')})
    value.update(changes)
    return value


def test_retained_capture_passes_full_production_ladder():
    assert len(RETAINED_RESULT) == 106  # the ruling's fixture-length corroboration
    assert sorted(retained()) == sorted(RETAINED_KEYS)
    reply = decode(retained())
    assert reply.total_tokens == 26
    assert len(reply.calls) == 1
    assert reply.calls[0].call_id == 'claude-1-0'
    assert reply.calls[0].name == 'search_evidence'
    assert strict_json(reply.calls[0].arguments_json) == {'query': 'SYNTHETIC-PAL-MOCK-RESPONSE'}
    assert decode(retained(), call_number=3).calls[0].call_id == 'claude-3-0'


def test_both_admitted_representations_stay_closed_and_distinct():
    assert decode().total_tokens == 26          # original strict representation
    assert decode(retained()).total_tokens == 26  # demonstrated terminal representation
    # The original representation does not absorb the nine names as optional.
    with pytest.raises(ValueError): decode(envelope(fast_mode_state='off'))
    # The demonstrated representation does not absorb original-only names.
    for name in ('errors', 'structured_output', 'deferred_tool_use', 'origin'):
        value = retained(); value[name] = None
        with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('field', RETAINED_KEYS)
def test_missing_retained_keys_fail_closed(field):
    value = retained(); del value[field]
    with pytest.raises(ValueError, match='response_invalid'): decode(value)


@pytest.mark.parametrize('change', [
    *[{'fast_mode_state': name} for name in ('on', 'OFF', '', 'disabled', 'off ')],
    *[{'fast_mode_state': value} for value in (1, True, None, ['off'])],
    *[{'fast_mode_disabled_reason': value} for value in
      ('', ' disabled_by_env', 'disabled_by_env ', 'x'*129, 0, True, None)],
    *[{'queued_turn_count': value} for value in (1, -1, True, '0', 0.0, None)],
    *[{'result_index': value} for value in (1, -1, True, '0', 0.0, None)],
    *[{name: value} for name in ('first_content_frame_ms', 'time_to_request_ms',
      'ttft_ms', 'ttft_stream_ms') for value in (-1, True, '322', 322.5, None)],
])
def test_retained_nine_new_keys_reject_wrong_types_and_values(change):
    with pytest.raises(ValueError, match='response_invalid') as caught:
        decode(retained(**change))
    assert 'SECRET-SENTINEL' not in ''.join(traceback.format_exception(caught.value))


@pytest.mark.parametrize('mutation', [
    'spawned', 'started_in_background', 'max_depth', 'spawned_by_subagents',
    'completed', 'failed', 'requested.background', 'requested.unset',
    'killed.user', 'killed.system', 'refused.budget', 'refused.depth_limit',
    'by_type.entry', 'by_type.list', 'missing_refused', 'extra_key',
    'requested_missing_unset', 'requested_extra_urgent', 'not_dict', 'as_string',
])
def test_retained_subagent_stats_must_establish_no_activity(mutation):
    value = retained(); stats = value['subagent_stats']
    if mutation == 'by_type.entry': stats['by_type'] = {'Task': {'spawned': 0}}
    elif mutation == 'by_type.list': stats['by_type'] = []
    elif mutation == 'missing_refused': del stats['refused']
    elif mutation == 'extra_key': stats['extra'] = 0
    elif mutation == 'requested_missing_unset': del stats['requested']['unset']
    elif mutation == 'requested_extra_urgent': stats['requested']['urgent'] = 0
    elif mutation == 'not_dict': value['subagent_stats'] = [0]*10
    elif mutation == 'as_string': value['subagent_stats'] = 'spawned'
    elif '.' in mutation:
        outer, inner = mutation.split('.'); stats[outer][inner] = 1
    else: stats[mutation] = 1
    with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('reason', [None, '', 'max_tokens', 'error', 'completed ',
                                    ' Completed', 'COMPLETE', 0, True])
def test_retained_terminal_reason_admits_only_demonstrated_completion(reason):
    with pytest.raises(ValueError, match='response_invalid'): decode(retained(terminal_reason=reason))


@pytest.mark.parametrize('change', [
    {'type':'assistant'}, {'subtype':'error_during_execution'}, {'is_error':1}, {'is_error':True},
    {'num_turns':0}, {'num_turns':2}, {'num_turns':True}, {'num_turns':'1'},
    {'stop_reason':'max_tokens'}, {'stop_reason':'tool_use'}, {'stop_reason':None},
    {'session_id':'not-uuid'}, {'uuid':'bad'}, {'duration_ms':True}, {'duration_api_ms':-1},
    {'permission_denials':[{'tool':'Bash'}]}, {'permission_denials':{}},
    {'api_error_status':429}, {'api_error_status':'overloaded'},
    {'total_cost_usd':True}, {'total_cost_usd':-1}, {'total_cost_usd':'0'},
    {'extra':'SECRET-SENTINEL'}, {'result':{}},
])
def test_retained_envelope_gating_stays_strict(change):
    with pytest.raises(ValueError, match='response_invalid') as caught:
        decode(retained(**change))
    assert 'SECRET-SENTINEL' not in ''.join(traceback.format_exception(caught.value))


@pytest.mark.parametrize('field', [
    'input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens',
    'output_tokens_details', 'server_tool_use', 'service_tier', 'cache_creation',
    'inference_geo', 'iterations', 'speed'])
def test_retained_usage_block_is_closed(field):
    value = retained(); del value['usage'][field]
    with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('mutation', [
    'details_extra', 'details_missing', 'thinking_negative', 'thinking_bool',
    'thinking_string', 'thinking_disagree_usage', 'thinking_disagree_model',
    'geo_int', 'geo_long', 'geo_nul', 'iterations_entry', 'iterations_string',
    'iterations_dict', 'speed_fast', 'speed_none', 'speed_int',
    'cache_extra_key', 'cache_missing_key', 'cache_negative', 'cache_exceeds_total',
    'server_extra', 'server_web_search', 'tier_fast', 'tier_int', 'usage_extra',
])
def test_retained_usage_new_fields_are_validated(mutation):
    value = retained(); usage = value['usage']; model = value['modelUsage'][MODEL]
    if mutation == 'details_extra': usage['output_tokens_details']['duration_ms'] = 0
    elif mutation == 'details_missing': del usage['output_tokens_details']['thinking_tokens']
    elif mutation == 'thinking_negative': usage['output_tokens_details']['thinking_tokens'] = -1
    elif mutation == 'thinking_bool': usage['output_tokens_details']['thinking_tokens'] = True
    elif mutation == 'thinking_string': model['thinkingTokens'] = '0'
    elif mutation == 'thinking_disagree_usage': usage['output_tokens_details']['thinking_tokens'] = 1
    elif mutation == 'thinking_disagree_model': model['thinkingTokens'] = 2
    elif mutation == 'geo_int': usage['inference_geo'] = 5
    elif mutation == 'geo_long': usage['inference_geo'] = 'x'*17
    elif mutation == 'geo_nul': usage['inference_geo'] = 'u\x00s'
    elif mutation == 'iterations_entry': usage['iterations'] = [1]
    elif mutation == 'iterations_string': usage['iterations'] = 'none'
    elif mutation == 'iterations_dict': usage['iterations'] = {}
    elif mutation == 'speed_fast': usage['speed'] = 'fast'
    elif mutation == 'speed_none': usage['speed'] = None
    elif mutation == 'speed_int': usage['speed'] = 1
    elif mutation == 'cache_extra_key': usage['cache_creation']['ephemeral_7d_input_tokens'] = 0
    elif mutation == 'cache_missing_key': del usage['cache_creation']['ephemeral_5m_input_tokens']
    elif mutation == 'cache_negative': usage['cache_creation']['ephemeral_5m_input_tokens'] = -1
    elif mutation == 'cache_exceeds_total': usage['cache_creation'] = dict(ephemeral_5m_input_tokens=5, ephemeral_1h_input_tokens=5)
    elif mutation == 'server_extra': usage['server_tool_use']['web_search'] = 0
    elif mutation == 'server_web_search': usage['server_tool_use']['web_search_requests'] = 1
    elif mutation == 'tier_fast': usage['service_tier'] = 'fast'
    elif mutation == 'tier_int': usage['service_tier'] = 5
    elif mutation == 'usage_extra': usage['unreviewed'] = 0
    with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('field', [
    'inputTokens', 'outputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens',
    'webSearchRequests', 'costUSD', 'contextWindow', 'maxOutputTokens',
    'thinkingTokens', 'canonicalModel', 'provider', 'costBasis'])
def test_retained_model_usage_block_is_closed(field):
    value = retained(); del value['modelUsage'][MODEL][field]
    with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('mutation', [
    'different_model', 'extra_model', 'disagree_input', 'disagree_output',
    'disagree_cache_read', 'disagree_cache_write', 'canonical_other',
    'canonical_nonstring', 'provider_bedrock', 'provider_case', 'provider_int',
    'basis_negotiated', 'basis_none', 'web_search', 'cost_negative',
    'cost_string', 'cost_bool', 'capacity_zero', 'capacity_overflow',
])
def test_retained_model_binding_usage_disagreement_and_metadata(mutation):
    value = retained(); model = value['modelUsage'][MODEL]
    if mutation == 'different_model': value['modelUsage'] = {'claude-other': model}
    elif mutation == 'extra_model': value['modelUsage']['claude-other'] = dict(model)
    elif mutation == 'disagree_input': model['inputTokens'] = 4
    elif mutation == 'disagree_output': model['outputTokens'] = 6
    elif mutation == 'disagree_cache_read': model['cacheReadInputTokens'] = 10
    elif mutation == 'disagree_cache_write': model['cacheCreationInputTokens'] = 8
    elif mutation == 'canonical_other': model['canonicalModel'] = 'claude-other'
    elif mutation == 'canonical_nonstring': model['canonicalModel'] = 5
    elif mutation == 'provider_bedrock': model['provider'] = 'bedrock'
    elif mutation == 'provider_case': model['provider'] = 'FirstParty'
    elif mutation == 'provider_int': model['provider'] = 1
    elif mutation == 'basis_negotiated': model['costBasis'] = 'negotiated'
    elif mutation == 'basis_none': model['costBasis'] = None
    elif mutation == 'web_search': model['webSearchRequests'] = 1
    elif mutation == 'cost_negative': model['costUSD'] = -1
    elif mutation == 'cost_string': model['costUSD'] = '0'
    elif mutation == 'cost_bool': model['costUSD'] = True
    elif mutation == 'capacity_zero': model['maxOutputTokens'] = 0
    elif mutation == 'capacity_overflow': model['contextWindow'] = 10000001
    with pytest.raises(ValueError): decode(value)


def test_retained_zero_total_and_aggregate_overflow_rejected():
    for number in (0, 500000):
        value = retained()
        for name, item in list(value['usage'].items()):
            if type(item) is int: value['usage'][name] = number
        for name, item in list(value['modelUsage'][MODEL].items()):
            if type(item) is int: value['modelUsage'][MODEL][name] = number
        with pytest.raises(ValueError): decode(value)


@pytest.mark.parametrize('limit', [4, 5, 6])
def test_retained_reported_output_boundary(limit):
    request = cli.ClaudeExecInput(MODEL, '[{}]', limit)
    if limit < 5:
        with pytest.raises(ValueError):
            cli.decode_claude_result(wire(retained()), request=request, call_number=1)
    else:
        assert cli.decode_claude_result(wire(retained()), request=request, call_number=1).total_tokens == 26


@pytest.mark.parametrize('calls', [[], [action()]*9, [dict(name='Bash',arguments_json='{}')],
    [dict(name='read_evidence',arguments_json='{"source_id":"\\ud800"}')],
    [dict(name='search_evidence',arguments_json='{"query":"*"}',call_id='external')]])
def test_retained_action_contract_unchanged(calls):
    with pytest.raises(ValueError):
        decode(retained(result=json.dumps({'calls': calls}, ensure_ascii=True)))


@pytest.mark.parametrize('result', [123, '{invalid', '{}', 'null', '"text"', '[]'])
def test_retained_result_string_must_carry_the_action(result):
    with pytest.raises(ValueError): decode(retained(result=result))


@pytest.mark.parametrize('defect', ['duplicate', 'trailing', 'array', 'bom', 'invalid_utf8'])
def test_retained_wire_framing_still_strict(defect):
    raw = wire(retained()).stdout
    if defect == 'duplicate': raw = b'{"type":"result",'+raw[1:]
    elif defect == 'trailing': raw += b'\nSECRET-SENTINEL'
    elif defect == 'array': raw = b'['+raw+b']'
    elif defect == 'bom': raw = b'\xef\xbb\xbf'+raw
    else: raw = b'\xff'+raw
    with pytest.raises(ValueError):
        cli.decode_claude_result(ResearchProcessResult(raw, 0, 1),
            request=cli.ClaudeExecInput(MODEL, '[{}]', 100), call_number=1)


def test_retained_nonzero_stderr_rejected():
    request = cli.ClaudeExecInput(MODEL, '[{}]', 100)
    with pytest.raises(ValueError):
        cli.decode_claude_result(ResearchProcessResult(wire(retained()).stdout, 1, 1),
            request=request, call_number=1)


def synthetic_spec(tmp_path, response, *, fail=False):
    binary = Path(sys.executable).resolve()
    env = tuple((key,os.environ[key]) for key in ('SYSTEMROOT','WINDIR') if key in os.environ)
    script = ('import sys,json;data=json.loads(sys.stdin.buffer.read());'
              'assert data["schema_version"]=="research-claude-actions-v1";'
              f'sys.stdout.buffer.write({response!r});sys.stdout.buffer.flush();sys.exit({1 if fail else 0})')
    return ResearchProcessSpec((str(binary),'-I','-S','-c',script),str(tmp_path),env,
                              sha256(binary.read_bytes()).hexdigest(),10000)


@pytest.mark.parametrize('fail', [False, True])
def test_real_subprocess_success_and_no_retry(tmp_path, fail):
    seen=[]
    def prepare(request):
        seen.append(request)
        assert json.loads(request.prompt_json)['messages_json']=='[{"content":"中文"}]'
        return synthetic_spec(tmp_path,wire().stdout,fail=fail)
    model=cli.ClaudeProcessModel(model_id=MODEL,prepare_command=prepare,allow_process_start=True)
    if fail:
        with pytest.raises(ValueError,match='call_failed'):
            model.complete(messages_json='[{"content":"中文"}]',max_output_tokens=100)
        with pytest.raises(ValueError,match='stopped'):
            model.complete(messages_json='[{}]',max_output_tokens=100)
    else:
        assert model.complete(messages_json='[{"content":"中文"}]',max_output_tokens=100).total_tokens==26
    assert len(seen)==1 and list(tmp_path.iterdir())==[]


def test_real_subprocess_retained_terminal_success(tmp_path):
    seen=[]
    def prepare(request):
        seen.append(request)
        return synthetic_spec(tmp_path, wire(retained()).stdout)
    model=cli.ClaudeProcessModel(model_id=MODEL,prepare_command=prepare,allow_process_start=True)
    reply=model.complete(messages_json='[{"content":"中文"}]',max_output_tokens=100)
    assert reply.total_tokens==26 and reply.calls[0].name=='search_evidence'
    assert strict_json(reply.calls[0].arguments_json)=={'query':'SYNTHETIC-PAL-MOCK-RESPONSE'}
    assert len(seen)==1 and list(tmp_path.iterdir())==[]


@pytest.mark.parametrize('error', [OSError('SECRET-SENTINEL'), KeyboardInterrupt(), SystemExit(0)])
def test_builder_failure_closes_client_and_preserves_interrupt(monkeypatch, error):
    seen=[]
    def prepare(_): seen.append(1); raise error
    monkeypatch.setattr(cli,'run_research_process',lambda **k:pytest.fail('launched'))
    model=cli.ClaudeProcessModel(model_id=MODEL,prepare_command=prepare,allow_process_start=True)
    with pytest.raises(type(error) if not isinstance(error,Exception) else ValueError) as caught:
        model.complete(messages_json='[{}]',max_output_tokens=100)
    if not isinstance(error,Exception): assert caught.value is error
    else: assert 'SECRET-SENTINEL' not in ''.join(traceback.format_exception(caught.value))
    with pytest.raises(ValueError,match='stopped'):model.complete(messages_json='[{}]',max_output_tokens=100)
    assert seen==[1]


def test_stop_before_builder_is_inert():
    stop=ResearchDispatchStop(); stop.request_stop()
    model=cli.ClaudeProcessModel(model_id=MODEL,prepare_command=lambda _:pytest.fail('builder'),
                                allow_process_start=True,stop=stop)
    with pytest.raises(ValueError):model.complete(messages_json='[{}]',max_output_tokens=100)


def test_builder_mutation_cannot_change_original_transcript_or_response_ceiling(monkeypatch,tmp_path):
    sent=[]
    def prepare(request):
        object.__setattr__(request,'messages_json','[{"content":"REPLACED"}]')
        object.__setattr__(request,'max_output_tokens',8192)
        return synthetic_spec(tmp_path,b'')
    def process(**kw):sent.append(kw['stdin']);return wire()
    monkeypatch.setattr(cli,'run_research_process',process)
    model=cli.ClaudeProcessModel(model_id=MODEL,prepare_command=prepare,allow_process_start=True)
    with pytest.raises(ValueError):model.complete(messages_json='[{"content":"ORIGINAL"}]',max_output_tokens=4)
    assert json.loads(sent[0])['messages_json']=='[{"content":"ORIGINAL"}]'
