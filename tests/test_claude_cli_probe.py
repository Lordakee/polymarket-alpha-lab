"""Synthetic evidence-harness tests, never an official-CLI success claim."""
from dataclasses import replace
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import sys

import pytest

from polymarket_alpha_lab import research_process as core
from tests import claude_cli_probe as probe
from tests.test_research_claude_exec import envelope


def image():
    path = Path(sys.executable).resolve()
    return str(path), sha256(path.read_bytes()).hexdigest(), path.stat().st_size


def simulated_runner(events, *, version=None, fault=None, outcome=None, rejected_result=False,
                     version_outcome=None):
    """Synthetic stand-in CLI.

    Performs the owner-approved L7-Q1 sequence: exactly one bodyless
    unauthenticated HEAD /api/hello (fixed 404) strictly before the one
    matching POST. ``outcome`` raises that fixed process code AFTER the one
    matching request/response ('before_request' raises an ordinary nonzero
    exit after the preflight, before the POST). ``rejected_result`` returns a
    CLI result the strict decoder must reject. ``version_outcome`` fails the
    --version invocation.
    """
    def run(*, spec, stdin, allow_process_start, **kwargs):
        assert allow_process_start is True
        assert set(dict(spec.environment)).isdisjoint({'PATH', 'HTTP_PROXY', 'HTTPS_PROXY'})
        if spec.argv[1:] == ('--version',):
            events.append('version')
            if version_outcome is not None:
                raise core.ResearchProcessError(version_outcome)
            return core.ResearchProcessResult((version or probe.VERSION_OUTPUT).encode(), 0, 1)
        events.append('message')
        env = dict(spec.environment)
        assert env['ANTHROPIC_API_KEY'] == probe.TEST_KEY
        assert env['ANTHROPIC_BASE_URL'].startswith('http://127.0.0.1:')
        assert '--no-session-persistence' in spec.argv and '--restricted' in spec.argv
        assert stdin.decode() == probe.test_input().prompt_json
        if outcome == 'before_request':
            raise core.ResearchProcessError('research_process_nonzero_exit')
        address = env['ANTHROPIC_BASE_URL'].removeprefix('http://')
        conn = http.client.HTTPConnection(address, timeout=2)
        # The approved preflight: one bodyless unauthenticated HEAD /api/hello.
        conn.request('HEAD', probe.PREFLIGHT_HEAD_PATH)
        conn.getresponse().read()
        body = {'model': probe.MODEL_ID, 'max_tokens': 1024, 'stream': True,
                'tools': [], 'messages': [{'role': 'user', 'content': stdin.decode()}]}
        if fault == 'context':
            body['system'] = probe.UNRELATED
        if fault == 'tools':
            body['tools'] = [{'name': 'Read'}]
        if fault == 'output_cap':
            body['max_tokens'] = 1025
        if fault == 'key_body':
            body['system'] = probe.TEST_KEY
        headers = {'Content-Type': 'application/json', 'x-api-key': probe.TEST_KEY}
        if fault == 'auth': headers['x-api-key'] = 'NOT-THE-TEST-KEY'
        for _ in range(2 if fault == 'retry' else 1):
            conn.request('POST', '/v1/messages?beta=true', json.dumps(body), headers)
            response = conn.getresponse(); raw = response.read(); status = response.status
        conn.close()
        if fault == 'write': (Path(spec.cwd)/'new-state.sqlite').write_bytes(b'SQLite format 3\x00')
        if fault == 'persist_prompt': (Path(env['HOME'])/'transcript').write_bytes(stdin)
        if fault == 'persist_response': (Path(env['CLAUDE_CONFIG_DIR'])/'response').write_text(probe.response_text('success'))
        if rejected_result:
            value = envelope(); value['result'] = '{invalid'
            return core.ResearchProcessResult(json.dumps(value).encode(), 0, 1)
        if outcome is not None:
            raise core.ResearchProcessError(outcome)
        if status != 200: raise core.ResearchProcessError('research_process_nonzero_exit')
        if b'"name": "Read"' in raw or raw.endswith(b'event: message_delta\n'):
            raise core.ResearchProcessError('research_process_nonzero_exit')
        value = envelope()
        if b'{invalid' in raw: value['result'] = '{invalid'
        else: value['result'] = probe.response_text('success')
        return core.ResearchProcessResult(json.dumps(value).encode(), 0, 1)
    return run


@pytest.mark.parametrize('mode', probe.MODES)
def test_each_scenario_observes_actual_mock_request_and_fixed_response(tmp_path, mode):
    events = []
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
                             allow_probe=True, process_runner=simulated_runner(events))
    assert events == ['version', 'message']
    assert result['request_count'] == 1 and result['request_contract_matches'] is True
    assert result['version_matches'] is True and result['state']['changed_entries'] == 0
    assert probe.observation_passed(result) is True
    assert result['activation_authorized'] is False
    assert result['outside_root_verified'] is result['external_egress_verified'] is False
    assert probe.TEST_KEY not in json.dumps(result) and probe.APPROVED not in json.dumps(result)
    # v2 observation: fixed allowlisted process codes, none for clean phases.
    assert result['schema_version'] == 'claude-cli-probe-v2'
    assert result['version_error_code'] is None
    # L7-Q1: the approved HEAD preflight is expected, never unexpected.
    assert result['preflight_head_observed'] == 1
    assert result['unexpected_requests'] == 0
    expected = ('research_process_nonzero_exit'
                if mode in ('rate_limit', 'server_error', 'tool_use', 'truncated') else None)
    assert result['process_error_code'] == expected


NEGATIVE_MODES = tuple(mode for mode in probe.MODES if mode != 'success')
# Fixed process codes that are NOT an ordinary nonzero exit; each must fail a
# negative case even when its one matching request/response already happened.
FAILING_OUTCOMES = (
    'research_process_signaled', 'research_process_timeout',
    'research_process_stopped', 'research_process_not_started',
    'research_process_output_limit', 'research_process_input_incomplete',
    'research_process_cleanup_failed', 'research_process_failed')


@pytest.mark.parametrize('mode', NEGATIVE_MODES)
def test_negative_mode_passes_on_ordinary_nonzero_exit_after_matching_response(tmp_path, mode):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
        allow_probe=True, process_runner=simulated_runner([], outcome='research_process_nonzero_exit'))
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['request_contract_matches'] is True
    assert result['process_status'] == 'failed'
    assert result['process_error_code'] == 'research_process_nonzero_exit'
    assert probe.observation_passed(result) is True


@pytest.mark.parametrize('mode', NEGATIVE_MODES)
def test_negative_mode_passes_on_a_decoder_rejected_returned_result(tmp_path, mode):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
        allow_probe=True, process_runner=simulated_runner([], rejected_result=True))
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['request_contract_matches'] is True
    assert result['process_status'] == 'returned' and result['process_error_code'] is None
    assert result['decoder_status'] == 'rejected'
    assert probe.observation_passed(result) is True


@pytest.mark.parametrize('mode', NEGATIVE_MODES)
def test_signal_death_after_the_matching_response_still_fails(tmp_path, mode):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
        allow_probe=True, process_runner=simulated_runner([], outcome='research_process_signaled'))
    # The observation shows the one matching response preceded the signal death.
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['request_contract_matches'] is True
    assert result['process_status'] == 'failed'
    assert result['process_error_code'] == 'research_process_signaled'
    assert probe.observation_passed(result) is False


@pytest.mark.parametrize('outcome', FAILING_OUTCOMES)
@pytest.mark.parametrize('mode', ('rate_limit', 'invalid_action'))
def test_infrastructure_failure_after_the_matching_response_still_fails(tmp_path, mode, outcome):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
        allow_probe=True, process_runner=simulated_runner([], outcome=outcome))
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['request_contract_matches'] is True
    assert result['process_error_code'] == outcome
    assert probe.observation_passed(result) is False


def test_ordinary_nonzero_exit_without_any_matching_request_still_fails(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='rate_limit',
        allow_probe=True, process_runner=simulated_runner([], outcome='before_request'))
    assert result['request_count'] == result['responses_sent'] == 0
    assert result['process_error_code'] == 'research_process_nonzero_exit'
    assert probe.observation_passed(result) is False


def test_success_mode_requires_an_accepted_result_not_a_process_failure(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=simulated_runner([], outcome='research_process_nonzero_exit'))
    assert result['process_error_code'] == 'research_process_nonzero_exit'
    assert probe.observation_passed(result) is False


@pytest.mark.parametrize('code', ('research_process_signaled', 'research_process_failed'))
def test_failed_version_phase_records_its_fixed_code_and_never_reaches_the_message(
        tmp_path, code):
    events = []
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=simulated_runner(events, version_outcome=code))
    assert events == ['version']
    assert result['version_status'] == 'failed' and result['version_error_code'] == code
    assert result['version_matches'] is False and result['process_status'] == 'not_started'
    assert result['request_count'] == 0 and probe.observation_passed(result) is False


@pytest.mark.parametrize('fault', ['context', 'tools', 'output_cap', 'key_body', 'auth', 'retry',
                                    'write', 'persist_prompt', 'persist_response'])
def test_bad_behavior_cannot_pass_even_with_a_success_result(tmp_path, fault):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=simulated_runner([], fault=fault))
    assert probe.observation_passed(result) is False
    text = json.dumps(result)
    assert probe.TEST_KEY not in text and probe.UNRELATED not in text and str(tmp_path) not in text


def test_wrong_version_stops_before_message(tmp_path):
    events = []
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success', allow_probe=True,
        process_runner=simulated_runner(events, version='2.1.277 (Claude Code)\n'))
    assert events == ['version'] and result['request_count'] == 0
    assert result['version_matches'] is False and probe.observation_passed(result) is False


def test_missing_optin_creates_nothing_and_starts_nothing(tmp_path):
    with pytest.raises(ValueError, match='probe_opt_in_required'):
        probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
            process_runner=lambda **_: pytest.fail('launched'))
    assert list(tmp_path.iterdir()) == []


def test_existing_root_is_never_scanned_or_overwritten(tmp_path):
    root = tmp_path/'existing'; root.mkdir(); private = root/'private'; private.write_text('keep')
    with pytest.raises(ValueError, match='probe_root_unavailable'):
        probe.run_probe(*image(), root=root, mode='success', allow_probe=True,
            process_runner=lambda **_: pytest.fail('launched'))
    assert private.read_text() == 'keep' and list(root.iterdir()) == [private]


@pytest.mark.parametrize('value', ['../relative', '', '0'*63, 'g'*64])
def test_bad_digest_cannot_enter_runner(tmp_path, value):
    path, _, size = image()
    with pytest.raises(ValueError, match='probe_image_invalid'):
        probe.run_probe(path, value, size, root=tmp_path/'probe', mode='success', allow_probe=True,
            process_runner=lambda **_: pytest.fail('launched'))
    assert list(tmp_path.iterdir()) == []


def test_environment_optin_absent_is_inert():
    assert probe.configured_image({}) is None


@pytest.mark.parametrize('env', [
    {'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE': '/anything'},
    {'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE': '1'},
    {'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE': 'true'},
])
def test_partial_or_malformed_optin_is_failure_not_silent_skip(env):
    with pytest.raises(ValueError, match='probe_configuration_invalid'):
        probe.configured_image(env)


def test_snapshot_detects_changed_same_size_content(tmp_path):
    root = tmp_path/'state'; root.mkdir(); path = root/'file'; path.write_text('aaaa')
    before = probe.state_snapshot(root)
    path.write_text('bbbb')
    after = probe.state_snapshot(root)
    assert probe.state_delta(before, after)['changed_entries'] == 1


def test_snapshot_does_not_follow_links_outside_root(tmp_path):
    root = tmp_path/'state'; root.mkdir()
    outside = tmp_path/'outside'; outside.write_text(probe.TEST_KEY)
    try: (root/'link').symlink_to(outside)
    except OSError: pytest.skip('symlink privilege unavailable')
    result = probe.state_snapshot(root)
    assert result['complete'] is False and result['unsafe_entries'] == 1
    assert result['sentinel_files'] == 0


def test_snapshot_large_file_is_incomplete_not_no_write(tmp_path):
    root = tmp_path/'state'; root.mkdir(); (root/'large').write_bytes(b'x'*(probe.MAX_FILE_BYTES+1))
    result = probe.state_snapshot(root)
    assert result['complete'] is False and result['limit_reached'] is True


def test_interrupt_is_preserved_and_server_stopped(tmp_path):
    original = KeyboardInterrupt()
    def run(**_): raise original
    with pytest.raises(KeyboardInterrupt) as caught:
        probe.run_probe(*image(), root=tmp_path/'probe', mode='success', allow_probe=True,process_runner=run)
    assert caught.value is original


# This child is deliberately a stdlib Python stand-in, not an official binary.
# It exercises the real supervisor, sockets, SSE and original result decoder.
_STAND_IN = r'''
import http.client, json, os, sys
if '--version' in sys.argv:
    sys.stdout.write('2.1.278 (Claude Code)\n')
    raise SystemExit(0)
prompt = sys.stdin.buffer.read().decode('utf-8')
url = os.environ['ANTHROPIC_BASE_URL']
assert url.startswith('http://127.0.0.1:')
connection = http.client.HTTPConnection(url.removeprefix('http://'), timeout=2)
# Owner-approved L7-Q1 sequence: the one bodyless HEAD preflight first.
connection.request('HEAD','/api/hello')
preflight=connection.getresponse(); preflight.read()
body = {'model':'claude-opus-5', 'max_tokens':1024, 'stream':True, 'tools':[],
        'messages':[{'role':'user','content':prompt}]}
connection.request('POST','/v1/messages',json.dumps(body),
    {'Content-Type':'application/json','x-api-key':os.environ['ANTHROPIC_API_KEY']})
reply = connection.getresponse(); data=reply.read(); connection.close()
if reply.status != 200: raise SystemExit(3)
events = [json.loads(line[6:]) for line in data.decode().splitlines() if line.startswith('data: ')]
if events[-1]['type'] != 'message_stop': raise SystemExit(4)
if any(e.get('content_block',{}).get('type')=='tool_use' for e in events): raise SystemExit(5)
text = ''.join(e['delta'].get('text','') for e in events if e['type']=='content_block_delta')
output = dict(type='result',subtype='success',is_error=False,num_turns=1,
    session_id='11111111-1111-4111-8111-111111111111',duration_ms=4,duration_api_ms=3,
    stop_reason='end_turn',result=text,permission_denials=[],
    usage=dict(input_tokens=3,output_tokens=5,cache_creation_input_tokens=7,cache_read_input_tokens=11),
    modelUsage={'claude-opus-5':dict(inputTokens=3,outputTokens=5,cacheCreationInputTokens=7,cacheReadInputTokens=11)})
print(json.dumps(output))
'''


@pytest.mark.parametrize('mode', probe.MODES)
def test_real_synthetic_processes_exercise_probe_without_official_cli(tmp_path, mode):
    launched = []
    def run(**kwargs):
        spec = kwargs['spec']
        launched.append(spec.argv[1:])
        kwargs['spec'] = replace(spec, argv=(spec.argv[0], '-I', '-S', '-c', _STAND_IN, *spec.argv[1:]))
        return core.run_research_process(**kwargs)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
                             allow_probe=True, process_runner=run)
    assert len(launched) == 2 and launched[0] == ('--version',)
    assert probe.observation_passed(result) is True, result
    assert result['vendor_provenance_verified'] is False


# ---------------------------------------------------------------------------
# v2 diagnostic observation additions (first-official-six arbitration
# prescriptions 2-5). These tests cover the observation-only capture; none of
# them may change any qualification assertion above.
# ---------------------------------------------------------------------------

def test_transcript_records_the_admitted_message_post(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=simulated_runner([]))
    transcript = result['diagnostics']['transcript']
    assert len(transcript) == 2 and result['diagnostics']['transcript_truncated'] is False
    # L7-Q1: the approved preflight is fully visible, first, and expected.
    head = transcript[0]
    assert head['kind'] == 'request' and head['phase'] == 'message'
    assert head['method'] == 'HEAD' and head['target']['text'] == '/api/hello'
    assert head['stage'] == 'preflight_head_admitted' and head['body_not_read'] is True
    assert head['response']['status'] == 404 and head['response']['bytes'] == 0
    head_names = {name.lower() for name, _ in head['headers']['pairs']}
    assert head_names <= probe.PREFLIGHT_HEADER_NAMES
    entry = transcript[1]
    assert entry['kind'] == 'request' and entry['phase'] == 'message'
    assert entry['method'] == 'POST' and entry['target']['text'] == '/v1/messages?beta=true'
    assert entry['stage'] == 'responded_scenario'
    assert entry['predicates'] == dict(route_path=True, route_scheme=True,
        route_netloc=True, route_query=True, route_fragment=True, body_is_object=True,
        model=True, max_tokens=True, stream=True, tools=True, prompt_present=True,
        no_unrelated_or_test_key=True, x_api_key=True, no_authorization=True)
    assert entry['body']['bytes'] > 0 and len(entry['body']['sha256']) == 64
    assert entry['body']['utf8'] is True
    for key in ('model', 'max_tokens', 'stream', 'tools', 'messages'):
        assert key in entry['body']['top_level_keys']
    assert entry['body']['value_shapes']['messages'].startswith('array:')
    headers = dict(entry['headers']['pairs'])
    assert headers['x-api-key'] is None and headers['Content-Type'] == 'application/json'
    assert 'x-api-key' in entry['headers']['redacted_values']
    assert entry['response']['status'] == 200
    assert entry['response']['content_type'] == 'text/event-stream'
    assert entry['response']['sse_events'] == ['message_start', 'content_block_start',
        'content_block_delta', 'content_block_stop', 'message_delta', 'message_stop']
    assert entry['response']['sse_trailing_partial_frame'] is None
    # Only shapes are retained: no prompt, key or unrelated context anywhere.
    text = json.dumps(entry)
    for secret in (probe.APPROVED, probe.TEST_KEY, probe.UNRELATED, str(tmp_path)):
        assert secret not in text


def test_transcript_records_sse_truncation_framing_and_error_status(tmp_path):
    truncated = probe.run_probe(*image(), root=tmp_path/'probe', mode='truncated',
        allow_probe=True, process_runner=simulated_runner([]))
    response = truncated['diagnostics']['transcript'][-1]['response']
    assert response['sse_events'] == ['message_start', 'content_block_start',
                                      'content_block_delta']
    assert response['sse_trailing_partial_frame'] == 'event: message_delta\n'
    limited = probe.run_probe(*image(), root=tmp_path/'probe2', mode='rate_limit',
        allow_probe=True, process_runner=simulated_runner([]))
    response = limited['diagnostics']['transcript'][-1]['response']
    assert response['status'] == 429 and response['content_type'] == 'application/json'
    assert response['sse_events'] is None and response['sse_trailing_partial_frame'] is None


@pytest.mark.parametrize('fault,name', [
    ('context', 'no_unrelated_or_test_key'), ('key_body', 'no_unrelated_or_test_key'),
    ('auth', 'x_api_key'), ('tools', 'tools'), ('output_cap', 'max_tokens')])
def test_transcript_identifies_the_failing_contract_predicate(tmp_path, fault, name):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=simulated_runner([], fault=fault))
    # The approved HEAD preflight precedes the refused POST; the POST is last.
    assert [entry['method'] for entry in result['diagnostics']['transcript']] == ['HEAD', 'POST']
    entry = result['diagnostics']['transcript'][-1]
    assert entry['stage'] == 'refused_contract' and entry['response']['status'] == 400
    assert entry['predicates'][name] is False
    assert all(value is True for key, value in entry['predicates'].items() if key != name)
    assert probe.observation_passed(result) is False


def test_transcript_captures_the_extra_non_post_request_signature(tmp_path):
    """Reproduce the recorded first-attempt extra request (a GET /api/hello)
    ahead of the approved sequence and pin that the transcript explains it
    while every counter keeps its original value: under the owner-approved
    L7-Q1 sequence a GET (or any non-HEAD method) is NOT the one permitted
    bodyless HEAD preflight, so it stays an unexpected request and fails."""
    original = simulated_runner([])
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            return original(**kwargs)
        env = dict(kwargs['spec'].environment)
        conn = http.client.HTTPConnection(env['ANTHROPIC_BASE_URL'].removeprefix('http://'), timeout=2)
        conn.request('GET', '/api/hello')
        conn.getresponse().read(); conn.close()
        return original(**kwargs)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=run)
    transcript = result['diagnostics']['transcript']
    assert [entry['method'] for entry in transcript] == ['GET', 'HEAD', 'POST']
    get = transcript[0]
    assert get['stage'] == 'refused_unexpected_method' and get['body_not_read'] is True
    assert get['phase'] == 'message' and get['response']['status'] == 404
    assert transcript[1]['stage'] == 'preflight_head_admitted'
    assert transcript[2]['stage'] == 'responded_scenario'
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['unexpected_requests'] == 1 and result['server_faults'] == 0
    assert result['preflight_head_observed'] == 1
    assert result['request_contract_matches'] is False
    assert probe.observation_passed(result) is False


def test_transcript_records_malformed_body_and_parser_refusals(tmp_path):
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            return core.ResearchProcessResult(probe.VERSION_OUTPUT.encode(), 0, 1)
        env = dict(kwargs['spec'].environment)
        conn = http.client.HTTPConnection(env['ANTHROPIC_BASE_URL'].removeprefix('http://'), timeout=2)
        conn.request('POST', '/v1/messages', 'not-json',
                     {'Content-Type': 'application/json', 'x-api-key': probe.TEST_KEY})
        try:
            conn.getresponse().read()
        except http.client.RemoteDisconnected:
            pass
        finally:
            conn.close()
        value = envelope(); value['result'] = probe.response_text('success')
        return core.ResearchProcessResult(json.dumps(value).encode(), 0, 1)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=run)
    entry = result['diagnostics']['transcript'][0]
    assert entry['stage'] == 'handler_fault'
    assert entry['stage_detail'] == 'body_json_invalid_or_not_utf8'
    assert entry['body']['utf8'] is True and entry['body']['top_level_keys'] is None
    assert entry['body']['bytes'] == len('not-json')
    assert result['server_faults'] == 1 and probe.observation_passed(result) is False


def test_transcript_records_the_parser_refusal_for_an_unknown_method(tmp_path):
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            return core.ResearchProcessResult(probe.VERSION_OUTPUT.encode(), 0, 1)
        env = dict(kwargs['spec'].environment)
        conn = http.client.HTTPConnection(env['ANTHROPIC_BASE_URL'].removeprefix('http://'), timeout=2)
        conn.request('BREW', '/v1/messages')
        try:
            conn.getresponse().read()
        except http.client.RemoteDisconnected:
            pass
        finally:
            conn.close()
        value = envelope(); value['result'] = probe.response_text('success')
        return core.ResearchProcessResult(json.dumps(value).encode(), 0, 1)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=run)
    entry = result['diagnostics']['transcript'][0]
    assert entry['kind'] == 'request' and entry['method'] == 'BREW'
    assert entry['stage'] == 'refused_parser' and entry['refusal_status'] == 501
    assert entry['body_not_read'] is True
    assert probe.observation_passed(result) is False


def test_predecode_capture_fields_for_an_accepted_result(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=simulated_runner([]))
    capture = result['diagnostics']['predecode']
    assert capture['capture_status'] == 'captured' and capture['stderr_bytes'] == 0
    assert capture['stdout_utf8'] is True and capture['stdout_bytes'] > 0
    assert capture['stdout_excerpt_truncated'] is False
    assert capture['first_failing_validation_stage'] is None
    assert capture['stdout_json_top_keys'] == sorted(envelope())
    assert capture['stdout_json_value_shapes']['result'].startswith('string:')
    assert len(capture['stdout_sha256']) == 64
    # The public synthetic action payload stays visible in the redacted excerpt;
    # credentials and probe paths never do.
    assert probe.RESPONSE in capture['stdout_excerpt_redacted']
    assert probe.TEST_KEY not in capture['stdout_excerpt_redacted']


@pytest.mark.parametrize('mode', ('invalid_action', 'tool_use'))
def test_predecode_stage_for_a_decoder_rejected_result(tmp_path, mode):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode,
        allow_probe=True, process_runner=simulated_runner([], rejected_result=True))
    capture = result['diagnostics']['predecode']
    assert capture['first_failing_validation_stage'] == 'result_json'
    assert result['decoder_status'] == 'rejected'
    assert probe.observation_passed(result) is True  # negative path unchanged


def test_predecode_stage_orders_stderr_before_stdout_parsing(tmp_path):
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            return core.ResearchProcessResult(probe.VERSION_OUTPUT.encode(), 0, 1)
        env = dict(kwargs['spec'].environment)
        conn = http.client.HTTPConnection(env['ANTHROPIC_BASE_URL'].removeprefix('http://'), timeout=2)
        conn.request('HEAD', probe.PREFLIGHT_HEAD_PATH)
        conn.getresponse().read()
        body = json.dumps({'model': probe.MODEL_ID, 'max_tokens': 1024, 'stream': True,
                           'tools': [], 'messages': [{'role': 'user', 'content': kwargs['stdin'].decode()}]})
        conn.request('POST', '/v1/messages', body,
                     {'x-api-key': probe.TEST_KEY, 'Content-Type': 'application/json'})
        conn.getresponse().read(); conn.close()
        return core.ResearchProcessResult(json.dumps(envelope()).encode(), 3, 1)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='rate_limit',
                             allow_probe=True, process_runner=run)
    capture = result['diagnostics']['predecode']
    assert capture['stderr_bytes'] == 3  # only the byte count, never content
    assert capture['first_failing_validation_stage'] == 'stderr_nonzero'
    assert result['decoder_status'] == 'rejected'
    assert probe.observation_passed(result) is True  # eligible negative disposition unchanged


@pytest.mark.parametrize('mutate,stage', [
    (lambda value: None, None),
    (lambda value: value.update(result='not json'), 'result_json'),
    (lambda value: value.update(result='{"calls": []}'), 'action_validation'),
    (lambda value: value.update(result='{"calls": [{"name": "x"}]}'), 'action_validation'),
    (lambda value: value.update(result=5), 'result_json'),
    (lambda value: value.pop('usage'), 'outer_keys'),
    (lambda value: value.update(unexpected=1), 'outer_keys'),
    (lambda value: value.update(type='error'), 'envelope_values'),
    (lambda value: value.update(is_error=True), 'envelope_values'),
    (lambda value: value.update(num_turns=2), 'envelope_values'),
    (lambda value: value.update(permission_denials=[{}]), 'envelope_values'),
    (lambda value: value.update(modelUsage={}), 'usage'),
    (lambda value: value.update(modelUsage={'other-model': {}}), 'usage'),
])
def test_decoder_stage_ladder_matches_the_pinned_admission_order(mutate, stage):
    value = envelope()
    mutate(value)
    result = core.ResearchProcessResult(json.dumps(value).encode(), 0, 1)
    assert probe._decoder_stage(result, probe.test_input()) == stage
    assert probe._decoder_stage(core.ResearchProcessResult(b'', 0, 1), probe.test_input()) \
        == 'stdout_bounds'
    assert probe._decoder_stage(core.ResearchProcessResult(b'{', 0, 1), probe.test_input()) \
        == 'outer_json'
    assert probe._decoder_stage(core.ResearchProcessResult(b'{}', 0, 1), probe.test_input()) \
        == 'outer_keys'
    assert probe._decoder_stage('not-a-result', probe.test_input()) == 'not_a_process_result'


def test_decoder_stage_ladder_stderr_precedes_outer_json():
    result = core.ResearchProcessResult(b'not json', 7, 1)
    assert probe._decoder_stage(result, probe.test_input()) == 'stderr_nonzero'


def test_state_inventory_attributes_changes_to_phases_but_baseline_counts_all(tmp_path):
    original = simulated_runner([], fault='write')
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            home = Path(dict(kwargs['spec'].environment)['HOME'])
            (home/'version-marker').write_bytes(b'v1')
        return original(**kwargs)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=run)
    inventory = result['diagnostics']['state_inventory']
    assert inventory['qualification_baseline'] == 'original initial snapshot (unchanged)'
    assert inventory['version_time']['changed_entries'] == 1
    version_name = str(Path('home', 'version-marker'))  # snapshot paths are native-form
    work_name = str(Path('work', 'new-state.sqlite'))
    assert [entry['path'] for entry in inventory['version_time']['entries']] == [version_name]
    assert inventory['version_time']['entries'][0]['before'] is None
    assert inventory['version_time']['entries'][0]['after'][0] == 'file'
    assert inventory['scenario_time']['changed_entries'] == 1
    assert [entry['path'] for entry in inventory['scenario_time']['entries']] == [work_name]
    # The qualification gate still compares the ORIGINAL snapshot to the end:
    # both phases count, and the zero-change gate fails exactly as before.
    assert result['state']['changed_entries'] == 2
    assert probe.observation_passed(result) is False


def test_state_inventory_is_empty_when_nothing_changes(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=simulated_runner([]))
    inventory = result['diagnostics']['state_inventory']
    for phase in ('version_time', 'scenario_time'):
        assert inventory[phase]['changed_entries'] == 0 and inventory[phase]['entries'] == []
    assert result['state']['changed_entries'] == 0
    assert probe.observation_passed(result) is True


def test_sidecars_are_written_exclusively_outside_the_probe_root(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=simulated_runner([]))
    sidecars = result['diagnostics']['sidecars']
    directory = tmp_path/'probe-diagnostics'
    assert sidecars['directory'] == 'probe-diagnostics'
    assert sidecars['status'] == 'written' and sidecars['budget_bytes'] == 8388608
    assert [entry[0] for entry in sidecars['files']] == list(probe.SIDECAR_NAMES)
    assert all(entry[1] == 'written' for entry in sidecars['files'])
    assert 0 < sidecars['written_bytes'] <= probe.DIAGNOSTIC_BUDGET_BYTES
    for name in probe.SIDECAR_NAMES:
        payload = json.loads((directory/name).read_text(encoding='utf-8'))
        assert payload['schema_version'] == probe.DIAGNOSTIC_SCHEMA and payload['mode'] == 'success'
    # The sidecar directory is a sibling, never inside the snapshotted root.
    assert not (tmp_path/'probe'/('probe'+probe.DIAGNOSTIC_DIR_SUFFIX)).exists()
    assert probe.observation_passed(result) is True
    # Exclusive creation: a second write into the same directory is refused.
    again = probe._write_diagnostic_sidecars(tmp_path/'probe', {'server-transcript.json': {'x': 1}})
    assert again['status'] == 'incomplete-and-recorded'
    assert again['incomplete_reason'] == 'sidecar_creation_failed'
    assert again['files'] == [['server-transcript.json', 'skipped', 0]]


def test_diagnostic_budget_overflow_is_recorded_never_qualification(monkeypatch, tmp_path):
    monkeypatch.setattr(probe, 'DIAGNOSTIC_BUDGET_BYTES', 16)
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=simulated_runner([]))
    sidecars = result['diagnostics']['sidecars']
    assert sidecars['status'] == 'incomplete-and-recorded'
    assert sidecars['incomplete_reason'] == 'diagnostic_budget_exceeded'
    assert [entry[1] for entry in sidecars['files']] == ['not_written']*3
    assert list((tmp_path/'probe-diagnostics').iterdir()) == []
    # The overflow only fails the diagnostic capture, never the qualification.
    assert probe.observation_passed(result) is True


# ---------------------------------------------------------------------------
# Owner-approved prospective criteria (2026-09-29, DELIVERY_PLAN section 63).
# L7-Q1: the expected request sequence is exactly one bodyless unauthenticated
# HEAD /api/hello (fixed 404) strictly before the one contract-matching POST;
# the preflight is an expected preflight, never an unexpected request.
# L7-Q2: the state gate keeps the original baseline and the raw five-entry
# delta, and admits exactly the five demonstrated content-validated bootstrap
# additions. Any deviation still fails.
# ---------------------------------------------------------------------------

def test_approved_preflight_head_is_expected_not_unexpected(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
                             allow_probe=True, process_runner=simulated_runner([]))
    assert result['preflight_head_observed'] == 1
    assert result['unexpected_requests'] == 0 and result['server_faults'] == 0
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['request_contract_matches'] is True
    head = result['diagnostics']['transcript'][0]
    assert head['method'] == 'HEAD' and head['target']['text'] == '/api/hello'
    assert head['stage'] == 'preflight_head_admitted' and head['body_not_read'] is True
    assert head['response']['status'] == 404 and head['response']['bytes'] == 0
    assert result['bootstrap_exception']['applied'] is False  # zero changes: not applied
    assert probe.observation_passed(result) is True


def _preflight_violation_runner(kind):
    """The approved sequence with exactly one deviation. Every request uses a
    fresh connection so a refused exchange cannot mask the next one."""
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            return core.ResearchProcessResult(probe.VERSION_OUTPUT.encode(), 0, 1)
        env = dict(kwargs['spec'].environment)
        address = env['ANTHROPIC_BASE_URL'].removeprefix('http://')

        def exchange(method, target, body=None, headers=None):
            fresh = http.client.HTTPConnection(address, timeout=2)
            fresh.request(method, target, body=body, headers=headers or {})
            try:
                fresh.getresponse().read()
            except Exception:
                pass  # a refused exchange may half-close; counters record it
            finally:
                fresh.close()

        def raw_exchange(target, host_values=None):
            """Full control over the raw request line and every Host header
            line, for unnormalized-target and Host-authority deviations."""
            fresh = http.client.HTTPConnection(address, timeout=2)
            fresh.putrequest('HEAD', target, skip_host=host_values is not None)
            if host_values:
                fresh.putheader('Host', *host_values)
            fresh.endheaders()
            try:
                fresh.getresponse().read()
            except Exception:
                pass
            finally:
                fresh.close()

        deviations = dict(
            get=('GET', probe.PREFLIGHT_HEAD_PATH, None, None),
            put=('PUT', probe.PREFLIGHT_HEAD_PATH, None, None),
            query=('HEAD', probe.PREFLIGHT_HEAD_PATH + '?beta=true', None, None),
            path=('HEAD', probe.PREFLIGHT_HEAD_PATH + '/', None, None),
            other_target=('HEAD', '/api/telemetry', None, None),
            x_api_key=('HEAD', probe.PREFLIGHT_HEAD_PATH, None, {'x-api-key': probe.TEST_KEY}),
            authorization=('HEAD', probe.PREFLIGHT_HEAD_PATH, None,
                           {'Authorization': 'Bearer synthetic-not-a-credential'}),
            content_length=('HEAD', probe.PREFLIGHT_HEAD_PATH, b'x', {}),
            custom_header=('HEAD', probe.PREFLIGHT_HEAD_PATH, None, {'X-Custom': 'anything'}))
        # The designated loopback authority this server actually listens on.
        authority = address  # '127.0.0.1:<port>'
        raw_deviations = dict(
            trailing_question=(probe.PREFLIGHT_HEAD_PATH + '?', None),
            trailing_fragment=(probe.PREFLIGHT_HEAD_PATH + '#', None),
            double_slash=('/' + probe.PREFLIGHT_HEAD_PATH, None),
            missing_host=(probe.PREFLIGHT_HEAD_PATH, []),
            wrong_host=(probe.PREFLIGHT_HEAD_PATH, ['example.invalid']),
            duplicate_host=(probe.PREFLIGHT_HEAD_PATH, [authority, authority]),
            arbitrary_host=(probe.PREFLIGHT_HEAD_PATH, ['api.anthropic.com']))
        if kind == 'two_heads':
            exchange('HEAD', probe.PREFLIGHT_HEAD_PATH)
            exchange('HEAD', probe.PREFLIGHT_HEAD_PATH)
        elif kind in raw_deviations:
            raw_exchange(*raw_deviations[kind])
        elif kind != 'no_head' and kind != 'head_after_post':
            exchange(*deviations[kind])
        body = json.dumps({'model': probe.MODEL_ID, 'max_tokens': 1024, 'stream': True,
                           'tools': [], 'messages': [{'role': 'user', 'content': kwargs['stdin'].decode()}]})
        exchange('POST', '/v1/messages?beta=true', body,
                 {'Content-Type': 'application/json', 'x-api-key': probe.TEST_KEY})
        if kind == 'head_after_post':  # any request after the POST is a failure
            exchange('HEAD', probe.PREFLIGHT_HEAD_PATH)
        value = envelope(); value['result'] = probe.response_text('success')
        return core.ResearchProcessResult(json.dumps(value).encode(), 0, 1)
    return run


@pytest.mark.parametrize('kind', [
    'no_head', 'get', 'put', 'query', 'path', 'other_target', 'x_api_key',
    'authorization', 'content_length', 'custom_header', 'two_heads',
    'head_after_post', 'trailing_question', 'trailing_fragment',
    'double_slash', 'missing_host', 'wrong_host', 'duplicate_host',
    'arbitrary_host'])
def test_any_deviation_from_the_approved_sequence_fails(tmp_path, kind):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=_preflight_violation_runner(kind))
    assert result['request_count'] == result['responses_sent'] == 1
    assert result['request_contract_matches'] is False
    assert probe.observation_passed(result) is False
    if kind == 'no_head':  # missing preflight: zero admitted, nothing unexpected
        assert result['preflight_head_observed'] == 0 and result['unexpected_requests'] == 0
    else:  # every other deviation stays an unexpected request
        assert result['unexpected_requests'] == 1
    if kind in ('two_heads', 'head_after_post'):
        assert result['preflight_head_observed'] in (0, 1)  # never two admitted


BOOTSTRAP_INSTANT = '2026-09-29T02:43:50.216Z'
BOOTSTRAP_BACKUP_NAME = '.claude.json.backup.1790649830552'


def bootstrap_config_text(**override):
    """The nine demonstrated config/.claude.json fields (closed schema)."""
    value = dict(firstStartTime=BOOTSTRAP_INSTANT, firstStartVersion=probe.CLAUDE_VERSION,
        machineID='a'*64, opusProMigrationComplete=True,
        sonnet1m45MigrationComplete=True, seenNotifications={},
        hasResetAutoModeOptInForDefaultOffer=True, migrationVersion=14, userID='b'*64)
    value.update(override)
    return json.dumps(value, indent=2)


def bootstrap_backup_text(first_start=BOOTSTRAP_INSTANT, **override):
    """The two demonstrated backup fields (the real pre-migration subset)."""
    value = dict(firstStartTime=first_start, firstStartVersion=probe.CLAUDE_VERSION)
    value.update(override)
    return json.dumps(value, indent=2)


def bootstrap_runner(*, config_text=None, backup_text=None, backup_name=None,
                     sessions_entry=None, tmp_entry=None, extra_writes=(),
                     remove=(), rewrite=(), outcome=None):
    """Simulated CLI: the approved HEAD+POST sequence plus the five
    demonstrated first-run bootstrap writes; the options perturb them."""
    original = simulated_runner([], outcome=outcome)
    def run(**kwargs):
        if kwargs['spec'].argv[1:] == ('--version',):
            return original(**kwargs)  # first-run writes happen in the scenario phase
        env = dict(kwargs['spec'].environment)
        config = Path(env['CLAUDE_CONFIG_DIR'])
        (config/'backups').mkdir()
        (config/'sessions').mkdir()
        Path(env['TMPDIR'], 'claude-1000').mkdir()
        (config/'.claude.json').write_text(
            config_text if config_text is not None else bootstrap_config_text(),
            encoding='utf-8')
        (config/'backups'/(backup_name or BOOTSTRAP_BACKUP_NAME)).write_text(
            backup_text if backup_text is not None else bootstrap_backup_text(),
            encoding='utf-8')
        if sessions_entry is not None:
            (config/'sessions'/sessions_entry).write_text('entry', encoding='utf-8')
        if tmp_entry is not None:
            Path(env['TMPDIR'], 'claude-1000', tmp_entry).write_text('entry', encoding='utf-8')
        for relative, text in extra_writes:
            target = config.parent/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
        for relative in remove:
            (config.parent/relative).unlink()
        for relative, text in rewrite:
            (config.parent/relative).write_text(text, encoding='utf-8')
        return original(**kwargs)
    return run


@pytest.mark.parametrize('mode', probe.MODES)
def test_approved_five_entry_bootstrap_passes_with_raw_delta_preserved(tmp_path, mode):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode=mode, allow_probe=True,
                             process_runner=bootstrap_runner())
    # The original baseline and the raw five-entry delta stay recorded.
    assert result['state']['changed_entries'] == 5
    assert result['diagnostics']['state_inventory']['qualification_baseline'] \
        == 'original initial snapshot (unchanged)'
    bootstrap = result['bootstrap_exception']
    assert bootstrap['applied'] is True and bootstrap['violations'] == []
    assert bootstrap['raw_delta'] == dict(added=5, removed=0, modified=0)
    assert bootstrap['baseline'] == 'original initial snapshot (unchanged; relocation excluded)'
    assert bootstrap['content']['claude_json']['valid'] is True
    assert bootstrap['content']['backup']['valid'] is True
    assert 0 < bootstrap['content']['claude_json']['bytes'] <= probe.BOOTSTRAP_CONFIG_MAX_BYTES
    assert bootstrap['content']['backup']['name'] == BOOTSTRAP_BACKUP_NAME
    assert result['preflight_head_observed'] == 1 and result['unexpected_requests'] == 0
    assert probe.observation_passed(result) is True, (mode, bootstrap)


@pytest.mark.parametrize('options', [
    dict(extra_writes=[('work/extra.txt', 'a sixth entry')]),
    dict(extra_writes=[('home/leak.txt', probe.TEST_KEY)]),
    dict(config_text=bootstrap_config_text(unknownBootstrapKey='x')),
    dict(config_text=bootstrap_config_text(transcript='[{"role":"user"}]')),
    dict(config_text=bootstrap_config_text(machineID=probe.APPROVED)),
    dict(config_text=bootstrap_config_text(userID=probe.RESPONSE)),
    dict(config_text=bootstrap_config_text(seenNotifications={'tips': 1})),
    dict(config_text=bootstrap_config_text(migrationVersion=15)),
    dict(config_text=bootstrap_config_text(firstStartTime='2026-09-29T02:43:50Z')),
    dict(config_text=bootstrap_config_text(firstStartVersion='2.1.277')),
    dict(config_text='not json'),
    dict(config_text=bootstrap_config_text() + '\n' + ' '*(probe.BOOTSTRAP_CONFIG_MAX_BYTES+1)),
    dict(backup_text=bootstrap_config_text()),
    dict(backup_name='claude.json.backup.1790649830552'),
    dict(backup_name='.claude.json.backup.17906498305'),
    dict(backup_text=bootstrap_backup_text(first_start='2026-09-29T02:43:50.999Z')),
    dict(backup_text=bootstrap_backup_text(firstStartVersion='2.1.277')),
    dict(sessions_entry='session.json'),
    dict(tmp_entry='tool-output.txt'),
    dict(extra_writes=[('config/backups/.claude.json.backup.1790649830553',
                        '{"firstStartTime": "%s", "firstStartVersion": "%s"}'
                        % (BOOTSTRAP_INSTANT, probe.CLAUDE_VERSION))]),
    dict(rewrite=[('CLAUDE.md', 'modified')]),
    dict(remove=['CLAUDE.md']),
])
def test_bootstrap_violations_keep_the_state_gate_failed(tmp_path, options):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=bootstrap_runner(**options))
    bootstrap = result['bootstrap_exception']
    assert bootstrap['applied'] is False and bootstrap['violations'] != []
    assert result['state']['changed_entries'] >= 5  # raw delta still recorded
    assert probe.observation_passed(result) is False


def test_bootstrap_exception_records_no_file_content_and_no_secrets(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=bootstrap_runner())
    text = json.dumps(result)
    assert probe.TEST_KEY not in text and probe.APPROVED not in text
    assert str(tmp_path) not in text
    assert BOOTSTRAP_INSTANT not in text  # values stay out of the observation
    assert 'a'*64 not in text  # the synthetic machineID is not echoed


def test_rejected_bootstrap_pathnames_never_leak_into_observation_or_sidecars(tmp_path):
    """A rejected addition whose FILENAME carries the synthetic key must not
    survive verbatim anywhere: not in the returned observation and not in any
    diagnostic sidecar payload, rejected case included."""
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=bootstrap_runner(
            extra_writes=[(str(Path('work', probe.TEST_KEY + '.txt')), 'a rejected entry')]))
    bootstrap = result['bootstrap_exception']
    assert bootstrap['applied'] is False and bootstrap['violations'] != []
    assert probe.TEST_KEY not in json.dumps(result)
    for name in probe.SIDECAR_NAMES:
        sidecar = (tmp_path/'probe-diagnostics'/name).read_text(encoding='utf-8')
        assert probe.TEST_KEY not in sidecar, name
    for name in bootstrap['added']:
        assert len(name) <= probe.MAX_TRANSCRIPT_STRING
        assert probe.TEST_KEY not in name


def test_bootstrap_exception_redacts_and_bounds_overlength_rejected_names(tmp_path):
    """Over-length rejected pathnames (not creatable portably on disk) are
    exercised directly through the evaluator with synthetic snapshots."""
    long_name = str(Path('work', 'n'*300))
    before = dict(complete=True, unsafe_entries=0, limit_reached=False,
                  sentinel_files=0, files={}, root_identity=None)
    after = dict(complete=True, unsafe_entries=0, limit_reached=False,
                 sentinel_files=0, root_identity=None, files={
                     str(Path('work', probe.TEST_KEY + '.txt')): ('file', '0'*64),
                     long_name: ('file', '0'*64)})
    secrets = probe._redaction_secrets(tmp_path/'probe')
    exception = probe._bootstrap_exception(before, after, tmp_path/'probe', secrets)
    assert exception['applied'] is False and exception['violations'] != []
    exported = json.dumps(exception)
    assert probe.TEST_KEY not in exported and 'n'*300 not in exported
    for name in exception['added']:
        assert len(name) <= probe.MAX_TRANSCRIPT_STRING
    # Raw names remain available to validation only via the bounded counts.
    assert exception['raw_delta'] == dict(added=2, removed=0, modified=0)


def test_applied_bootstrap_exports_only_the_five_bounded_expected_names(tmp_path):
    result = probe.run_probe(*image(), root=tmp_path/'probe', mode='success',
        allow_probe=True, process_runner=bootstrap_runner())
    bootstrap = result['bootstrap_exception']
    assert bootstrap['applied'] is True
    expected = sorted(str(Path(*name)) for name in (
        ('config', '.claude.json'), ('config', 'backups'),
        ('config', 'backups', BOOTSTRAP_BACKUP_NAME),
        ('config', 'sessions'), ('tmp', 'claude-1000')))
    assert sorted(bootstrap['added']) == expected
    exported = (bootstrap['added'] + bootstrap['removed'] + bootstrap['modified']
        + [name for name in bootstrap['entries'].values() if name is not None]
        + [bootstrap['content']['backup']['name']])
    for name in exported:
        assert len(name) <= probe.MAX_TRANSCRIPT_STRING
