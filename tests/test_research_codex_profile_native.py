"""Opt-in official Linux package + loopback only; synthetic data, no credentials.

This proves the pinned command's observed wire behavior, NOT zero persistence or
an authorized real-model integration. The package is supplied explicitly, never
downloaded/installed by a test. Its temporary SQLite files are synthetic upstream
state, never a project-data backend. Default offline/Windows runs do not launch it.
"""
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import sys
from threading import Thread

import pytest

from polymarket_alpha_lab.research_codex_exec import CodexExecInput, CodexExecModel
from polymarket_alpha_lab.research_codex_process import CodexProcessTransport
from polymarket_alpha_lab.research_codex_profile import CodexExecProfile
from polymarket_alpha_lab.research_process import ResearchProcessSpec

pytestmark = pytest.mark.skipif(
    sys.platform != 'linux' or os.environ.get('POLYMARKET_ALPHA_LAB_TEST_CODEX_PROFILE_NATIVE') != '1',
    reason='explicit pinned Linux Codex package and synthetic loopback opt-in required')

_IMAGE = '0753dfe1d8b87a52436deb13eb1c549661ef4c84fee2c5aa688385eebeccb761'
_COMPANION = '210ab8ebaebf4bc1421d9e30339c858354ca35fa91e2f87f4c6204e5382f8a63'
_APPROVED = 'SYNTHETIC-APPROVED-RESEARCH'
_UNAPPROVED = 'SYNTHETIC-UNRELATED-CONTEXT'


@pytest.fixture(scope='module')
def native_image():
    root = Path(os.environ['POLYMARKET_ALPHA_LAB_TEST_CODEX_PACKAGE_ROOT'])
    assert root.is_absolute()
    binary, companion = root/'bin/codex', root/'bin/codex-code-mode-host'
    assert binary.stat().st_size == 269273536
    assert sha256(binary.read_bytes()).hexdigest() == _IMAGE
    assert sha256(companion.read_bytes()).hexdigest() == _COMPANION
    return binary


@pytest.mark.parametrize('mode', ['success', 'rate_limit', 'server_error', 'malformed_action', 'tool_action'])
def test_actual_pinned_cli_profile_loopback_single_submission(native_image, tmp_path, mode):
    """Five distinct scenarios; errors never trigger another invocation/request."""
    calls, faults = [], []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            calls.append((self.path, {}, {}))
            self.send_response(404); self.send_header('Content-Length', '0'); self.end_headers()
        def do_POST(self):
            try:
                self.connection.settimeout(5)
                count = int(self.headers['Content-Length'])
                assert 0 < count < 1000000
                body = json.loads(self.rfile.read(count))
                calls.append((self.path, dict(self.headers), body))
                if mode in ('rate_limit', 'server_error'):
                    self.send_response(429 if mode == 'rate_limit' else 500)
                    self.send_header('Content-Length', '0'); self.end_headers(); return
                action = '{broken' if mode == 'malformed_action' else json.dumps({'calls': [
                    {'name': 'shell' if mode == 'tool_action' else 'search_evidence',
                     'arguments_json': '{"query":"*"}'}]})
                events = [
                    {'type': 'response.created', 'response': {'id': 'resp_synthetic'}},
                    {'type': 'response.output_item.done', 'item': {'type': 'message', 'role': 'assistant',
                        'id': 'msg_synthetic', 'content': [{'type': 'output_text', 'text': action}]}},
                    {'type': 'response.completed', 'response': {'id': 'resp_synthetic',
                        'usage': {'input_tokens': 100, 'output_tokens': 20,
                                  'input_tokens_details': {'cached_tokens': 0},
                                  'output_tokens_details': {'reasoning_tokens': 0}, 'total_tokens': 120}}}]
                payload = ''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode()
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Content-Length', str(len(payload))); self.end_headers(); self.wfile.write(payload)
            except Exception as error:
                faults.append(type(error).__name__)
                self.close_connection = True
    server = HTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever)
    worker.start()
    try:
        for name in ('home', 'work', 'codex', 'tmp'): (tmp_path/name).mkdir()
        # These fixed synthetic probes are not user files/credentials. Strict
        # config would reject the unknown field if ignore-user-config were lost.
        (tmp_path/'codex/config.toml').write_text('unknown_setting="'+_UNAPPROVED+'"\n')
        (tmp_path/'AGENTS.md').write_text(_UNAPPROVED)
        request = CodexExecInput('gpt-5.6-sol', json.dumps([{'role': 'user', 'content': _APPROVED}]), 1024)
        schema = tmp_path/'schema.json'; schema.write_bytes(request.output_schema_json.encode())
        spec = ResearchProcessSpec((str(native_image),), str(tmp_path/'work'),
            (('CODEX_HOME', str(tmp_path/'codex')), ('HOME', str(tmp_path/'home')), ('TMPDIR', str(tmp_path/'tmp'))),
            _IMAGE, 10000, max_executable_bytes=native_image.stat().st_size)
        profile = CodexExecProfile(spec, request.model_id,
            f'http://127.0.0.1:{server.server_port}/v1', str(schema))
        client = CodexExecModel(model_id=request.model_id, transport=CodexProcessTransport(
            prepare_command=profile, allow_process_start=True))
        if mode == 'success':
            reply = client.complete(messages_json=request.messages_json, max_output_tokens=1024)
            assert reply.total_tokens == 120 and reply.calls[0].name == 'search_evidence'
        else:
            with pytest.raises(ValueError, match='call_failed'):
                client.complete(messages_json=request.messages_json, max_output_tokens=1024)
            with pytest.raises(ValueError, match='stopped'):
                client.complete(messages_json=request.messages_json, max_output_tokens=1024)
        assert faults == [] and len(calls) == 1
        path, headers, body = calls[0]
        assert path == '/v1/responses' and body['model'] == request.model_id
        assert body.get('tools') in (None, [])
        assert 'max_output_tokens' not in body  # Explicitly NOT a hard provider cap.
        assert body['text']['format']['schema'] == json.loads(request.output_schema_json)
        assert not any(k.lower() == 'authorization' for k in headers)
        text = json.dumps(body)
        assert _APPROVED in text and _UNAPPROVED not in text
        # Negative proof: ephemeral is NOT no-state. This must stay visible and
        # blocks activating this profile with real project research inputs.
        assert any((tmp_path/'codex').glob('*.sqlite'))
        assert list((tmp_path/'work').iterdir()) == []
    finally:
        server.shutdown(); server.server_close(); worker.join(timeout=5)
        assert not worker.is_alive()
