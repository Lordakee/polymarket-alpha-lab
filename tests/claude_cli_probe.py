"""Opt-in TEST harness for an operator-supplied native Claude image.

No download, login, real key, database, forwarding proxy or production entry.
Use only a disposable host with external egress denied. The test endpoint is
HTTP on numeric loopback: the sole deliberate override of the production HTTPS
profile. This does not test TLS, outside-root writes, or transient/deleted files.
Observations are metadata only, never an activation authorization.

v2 observation semantics: a negative scenario passes ONLY after its one
matching request/response AND either an ordinary nonzero child exit or a
returned result rejected by the strict decoder. Signal death, timeout, stop,
failed startup, output limit, incomplete input, cleanup failure and generic
infrastructure failure fail the case even when the response preceded them.

v2 diagnostic additions (first-official-six arbitration prescriptions 2-5):
a bounded sanitized server transcript, a pre-decode capture of the returned
result, a three-snapshot state inventory and bounded /pal-output sidecar
files under a fixed sub-budget. Every diagnostic field is observation-only:
counters, matching decisions, the qualification baseline and observation_passed
are unchanged, and a failed diagnostic capture is recorded as incomplete, never
raised into the qualification itself.

v2 prospective criteria (owner-approved acceptance changes, 2026-09-29,
DELIVERY_PLAN section 63): L7-Q1 permits exactly one bodyless unauthenticated
HEAD /api/hello to this same numeric-loopback server -- answered with the fixed
404 the server already sends, strictly before the one unchanged contract-matching
POST, validated by method, target, framing, header allowlist, order and
cardinality, and recorded as an expected preflight (preflight_head_observed),
never as an unexpected request. L7-Q2 keeps the original initial snapshot and
the raw five-entry delta recorded, and admits exactly the five demonstrated
first-run bootstrap additions after closed-schema content validation inside the
disposable synthetic root. Every other request, retry, sequencing deviation or
external destination, and any other addition, modification, removal, unsafe
entry, sentinel, oversized file or nonconforming content still fails. Baseline
relocation is expressly excluded from the approval and is not implemented.
"""
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import stat
from threading import Thread
from urllib.parse import urlsplit

from polymarket_alpha_lab import research_process as process
from polymarket_alpha_lab.research_claude_exec import (
    CLAUDE_VERSION, MAX_RESULT_BYTES, ClaudeExecInput, decode_claude_result)
from polymarket_alpha_lab.research_claude_profile import ClaudeExecProfile, MODEL_ID
from polymarket_alpha_lab.team_research_agent_types import strict_json

MODES = ('success', 'rate_limit', 'server_error', 'invalid_action', 'tool_use', 'truncated')
VERSION_OUTPUT = CLAUDE_VERSION + ' (Claude Code)\n'
TEST_KEY = 'SYNTHETIC-PAL-PROBE-NOT-A-CREDENTIAL'
APPROVED = 'SYNTHETIC-PAL-APPROVED-PROMPT'
UNRELATED = 'SYNTHETIC-PAL-UNRELATED-CONTEXT'
RESPONSE = 'SYNTHETIC-PAL-MOCK-RESPONSE'
MAX_FILE_BYTES, MAX_STATE_BYTES, MAX_ENTRIES = 65536, 4194304, 256
MAX_HTTP_BYTES, MAX_REQUESTS = 1048576, 8
# --- Owner-approved L7-Q1 request-sequence exception (2026-09-29, section 63) --
# Exactly one bodyless unauthenticated HEAD to the exact /api/hello path on
# this same numeric-loopback server, answered with the fixed 404, strictly
# before the one contract-matching POST. The preflight header allowlist is the
# demonstrated diagnostic-cohort header-name set; any other name -- including
# any credential-bearing header, Content-Length or Transfer-Encoding -- makes
# the HEAD an unexpected request again.
PREFLIGHT_HEAD_PATH = '/api/hello'
PREFLIGHT_HEADER_NAMES = frozenset(('accept', 'accept-encoding', 'connection',
                                    'host', 'user-agent'))
# --- Owner-approved L7-Q2 five-entry bootstrap exception (2026-09-29, section 63) --
# Closed schemas derived only from the demonstrated diagnostic capture
# (ubuntu@166.1.232.93:~/pal-artifacts/l7-work/diag/export/pytest-tmp/
# test_supplied_claude_profile_l0/claude-probe/): the real config/.claude.json
# the CLI wrote (423 bytes, exactly nine bootstrap keys) and the real backup
# (84 bytes, exactly the two-key pre-migration subset; it is NOT byte-identical
# to .claude.json). No credential, prompt, response, session-transcript or
# tool data is admissible: every admitted value is one of the bounded forms
# validated below, and unknown keys are rejected outright.
BOOTSTRAP_CONFIG_MAX_BYTES = 4096
BOOTSTRAP_BACKUP_MAX_BYTES = 1024
BOOTSTRAP_MIGRATION_VERSION = 14
BOOTSTRAP_CONFIG_SCHEMA = 'claude-cli-bootstrap-config-v1'
BOOTSTRAP_BACKUP_SCHEMA = 'claude-cli-bootstrap-backup-v1'
_BOOTSTRAP_INSTANT = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:'
                                '[0-9]{2}\\.[0-9]{3}Z')
_BOOTSTRAP_ID = re.compile('[0-9a-f]{64}')
_BOOTSTRAP_BACKUP_NAME = re.compile(r'\.claude\.json\.backup\.[0-9]{13}')
# --- v2 diagnostic constants (observation-only, never qualification inputs) --
DIAGNOSTIC_SCHEMA = 'claude-cli-probe-diagnostics-v1'
MAX_TRANSCRIPT_ENTRIES = 64
MAX_TRANSCRIPT_STRING = 256
MAX_HEADER_PAIRS = 64
MAX_STDOUT_EXCERPT_BYTES = 4096
MAX_INVENTORY_ENTRIES = 64
DIAGNOSTIC_BUDGET_BYTES = 8388608  # fixed 8 MiB sub-budget inside the 64 MiB export allowance
DIAGNOSTIC_DIR_SUFFIX = '-diagnostics'
SIDECAR_NAMES = ('server-transcript.json', 'predecode.json', 'state-inventory.json')
_MARKER_SECRETS = (TEST_KEY, APPROVED, UNRELATED)
_HEADER_NAME_OK = re.compile("[!#$%&'*+\\-.^_`|~0-9A-Za-z]{1,128}")
# Header values are redacted by name, EXCEPT two structurally safe ones:
# content-length (digit-only, already regex-validated by the handler itself)
# and content-type (retained only when it matches this token charset, so it
# cannot carry credential bytes). Safe-value regexes are applied, not trusted.
_SAFE_HEADER_VALUE = {'content-length': re.compile('[0-9]{1,7}'),
                      'content-type': re.compile('[A-Za-z0-9./+-]{1,64}')}
# Fixed mirror of the pinned decoder's outer result-key contract at the
# revision under test; diagnostic staging only, never an admission decision.
_OUTER_REQUIRED = ('type', 'subtype', 'is_error', 'num_turns', 'session_id', 'result',
                   'duration_ms', 'duration_api_ms', 'stop_reason', 'usage', 'modelUsage',
                   'permission_denials')
_OUTER_OPTIONAL = ('uuid', 'total_cost_usd', 'structured_output', 'deferred_tool_use', 'errors',
                   'api_error_status', 'terminal_reason', 'origin')
# Same fixed-mirror doctrine for the decoder's SECOND admitted closed shape:
# the calibrated 25-key terminal representation (L7 final ruling; the exact
# key set production pins in research_claude_exec._TERMINAL_KEYS). A payload
# matching this set is staged through the terminal branch below instead of
# being mislabeled outer_keys; diagnostic staging only, never an admission
# decision.
_TERMINAL_OUTER_KEYS = frozenset((
    'api_error_status', 'duration_api_ms', 'duration_ms',
    'fast_mode_disabled_reason', 'fast_mode_state', 'first_content_frame_ms',
    'is_error', 'modelUsage', 'num_turns', 'permission_denials', 'queued_turn_count',
    'result', 'result_index', 'session_id', 'stop_reason', 'subagent_stats', 'subtype',
    'terminal_reason', 'time_to_request_ms', 'total_cost_usd', 'ttft_ms',
    'ttft_stream_ms', 'type', 'usage', 'uuid'))
# Fixed process-failure codes the v2 observation may carry; anything else is
# recorded as None and can never satisfy a negative case.
PROCESS_ERROR_CODES = frozenset((
    'research_process_nonzero_exit', 'research_process_signaled',
    'research_process_timeout', 'research_process_stopped',
    'research_process_not_started', 'research_process_output_limit',
    'research_process_input_incomplete', 'research_process_cleanup_failed',
    'research_process_failed'))
_ENV = ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE', 'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE', 'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256',
        'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES', 'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST')


def _process_error_code(error):
    """Allowlisted fixed code only; never echo a foreign message or diagnostic."""
    if (type(error) is process.ResearchProcessError and len(error.args) == 1
            and type(error.args[0]) is str and error.args[0] in PROCESS_ERROR_CODES):
        return error.args[0]
    return None


def _image_values(image, digest, size):
    if (type(image) is not str or not Path(image).is_absolute() or '\x00' in image
            or type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None
            or type(size) is not int or not 1 <= size <= 536870912):
        raise ValueError('probe_image_invalid')
    image.encode('utf-8')
    return image, digest, size


def configured_image(environment):
    """No implicit image discovery. Partial opt-in fails rather than skips."""
    values = {key: environment[key] for key in _ENV if key in environment}
    if not values:
        return None
    try:
        if (set(values) != set(_ENV) or values[_ENV[0]] != '1' or values[_ENV[4]] != '1'
                or re.fullmatch('[1-9][0-9]{0,8}', values[_ENV[3]]) is None):
            raise ValueError
        return _image_values(values[_ENV[1]], values[_ENV[2]], int(values[_ENV[3]]))
    except Exception:
        raise ValueError('probe_configuration_invalid') from None


def test_input():
    return ClaudeExecInput(MODEL_ID, json.dumps([{'role': 'user', 'content': APPROVED}]), 1024)


def response_text(mode):
    if mode == 'invalid_action':
        return '{invalid'
    return json.dumps({'calls': [{'name': 'search_evidence',
                                 'arguments_json': json.dumps({'query': RESPONSE})}]})


def _stream(mode):
    text = response_text(mode)
    usage = dict(input_tokens=3, output_tokens=0,
                 cache_creation_input_tokens=7, cache_read_input_tokens=11)
    start = dict(id='msg_pal_synthetic', type='message', role='assistant', model=MODEL_ID,
                 content=[], stop_reason=None, stop_sequence=None, usage=usage)
    block = ({'type': 'tool_use', 'id': 'toolu_pal_synthetic', 'name': 'Read',
              'input': {}} if mode == 'tool_use' else {'type': 'text', 'text': ''})
    delta = ({'type': 'input_json_delta', 'partial_json': '{"file_path":"CLAUDE.md"}'}
             if mode == 'tool_use' else {'type': 'text_delta', 'text': text})
    events = [dict(type='message_start', message=start),
        dict(type='content_block_start', index=0, content_block=block),
        dict(type='content_block_delta', index=0, delta=delta),
        dict(type='content_block_stop', index=0),
        dict(type='message_delta', delta={'stop_reason': 'tool_use' if mode == 'tool_use' else 'end_turn',
                                         'stop_sequence': None}, usage={'output_tokens': 5}),
        dict(type='message_stop')]
    if mode == 'truncated':
        events = events[:3]
    wire = ''.join('event: '+event['type']+'\ndata: '+json.dumps(event)+'\n\n' for event in events)
    return (wire + ('event: message_delta\n' if mode == 'truncated' else '')).encode()


def _strings(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is str:
            yield item
        elif type(item) is dict:
            pending.extend(item.keys()); pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)


def _redaction_secrets(root):
    """Marker sentinels plus the probe paths; longest first so a contained
    shorter occurrence cannot survive a partial replace."""
    paths = (str(root), str(Path(root).parent), Path(root).as_posix(),
             Path(Path(root).parent).as_posix())
    return tuple(sorted({value for value in (*_MARKER_SECRETS, *paths) if value},
                        key=len, reverse=True))


def _redact_text(text, secrets):
    for secret in secrets:
        text = text.replace(secret, '[REDACTED]')
    return text


def _sanitize_target(path):
    if type(path) is not str:
        return dict(text=None, length=None)
    text = path[:MAX_TRANSCRIPT_STRING]
    if any(ord(character) < 32 or ord(character) > 126 for character in text):
        text = '[non-printable-target]'
    return dict(text=_redact_text(text, _MARKER_SECRETS), length=len(path))


def _header_pairs(headers):
    pairs, redacted, truncated = [], [], False
    try:
        for name, value in headers.items():
            if len(pairs) >= MAX_HEADER_PAIRS:
                truncated = True
                break
            safe_name = (name if type(name) is str and _HEADER_NAME_OK.fullmatch(name)
                         else '[invalid-header-name]')
            retained = None
            if (type(name) is str and type(value) is str
                    and name.lower() in _SAFE_HEADER_VALUE
                    and _SAFE_HEADER_VALUE[name.lower()].fullmatch(value)):
                retained = value
            else:
                redacted.append(safe_name)
            pairs.append([safe_name, retained])
    except Exception:
        pass
    return dict(pairs=pairs, redacted_values=sorted(set(redacted))[:MAX_HEADER_PAIRS],
        truncated=truncated,
        policy='names with multiplicity; only digit-only Content-Length and '
               'token-charset Content-Type values retained, all other values redacted')


def _json_shape(value):
    try:
        if value is None:
            return 'null'
        if value is True:
            return 'true'
        if value is False:
            return 'false'
        if type(value) is str:
            return 'string:%d' % len(value.encode('utf-8'))
        if type(value) is int:
            return 'int:%d' % value if -10**15 <= value <= 10**15 else 'int:out-of-range'
        if type(value) is Decimal:
            return 'decimal'
        if type(value) is dict:
            return 'object:%d' % len(value)
        if type(value) is list:
            return 'array:%d' % len(value)
        return type(value).__name__
    except Exception:
        return 'string:invalid-utf8'


def _body_summary(raw):
    """Sanitized retention of the POST bytes the handler already read:
    byte length, digest and a shapes-only view. String VALUES (which carry the
    prompt and any credential echoes) are replaced by their utf-8 lengths."""
    summary = dict(read=True, bytes=len(raw), sha256=sha256(raw).hexdigest() if raw else None,
        utf8=None, top_level_keys=None, value_shapes=None, keys_truncated=False,
        redaction='json string values replaced by length; numbers kept only when small')
    try:
        text = raw.decode('utf-8')
        summary['utf8'] = True
        body = strict_json(text)
    except Exception:
        return summary
    keys = sorted(body) if type(body) is dict else ['<root>']
    bounded, truncated = keys[:MAX_HEADER_PAIRS], len(keys) > MAX_HEADER_PAIRS
    summary['top_level_keys'] = [_redact_text(key, _MARKER_SECRETS)[:MAX_TRANSCRIPT_STRING]
                                 for key in bounded]
    summary['keys_truncated'] = truncated
    summary['value_shapes'] = {_redact_text(key, _MARKER_SECRETS)[:MAX_TRANSCRIPT_STRING]:
                               _json_shape(body[key] if type(body) is dict else body)
                               for key in bounded}
    return summary


def _response_summary(code, payload, content_type):
    summary = dict(status=code, content_type=content_type, bytes=len(payload),
                   sha256=sha256(payload).hexdigest() if payload else None,
                   sse_events=None, sse_trailing_partial_frame=None)
    if content_type == 'text/event-stream' and payload:
        try:
            text = payload.decode('utf-8')
            frames = text.split('\n\n')
            if frames and frames[-1] != '':
                summary['sse_trailing_partial_frame'] = frames[-1][:MAX_TRANSCRIPT_STRING]
                frames = frames[:-1]
            summary['sse_events'] = [line[7:][:MAX_TRANSCRIPT_STRING]
                                     for frame in frames for line in frame.split('\n')
                                     if line.startswith('event: ')]
        except Exception:
            pass
    return summary


def _body_predicates(body, texts, headers, path):
    """Diagnostic mirror of the do_POST contract conjunction, evaluated only
    AFTER the original ``good`` expression has been computed unchanged. Each
    predicate is guarded; a non-evaluable one is None. Never a decision input."""
    def evaluate():
        route = urlsplit(path)
        is_object = type(body) is dict
        return dict(
            route_path=route.path == '/v1/messages',
            route_scheme=not route.scheme,
            route_netloc=not route.netloc,
            route_query=route.query in ('', 'beta=true'),
            route_fragment=not route.fragment,
            body_is_object=is_object,
            model=is_object and body.get('model') == MODEL_ID,
            max_tokens=(is_object and type(body.get('max_tokens')) is int
                        and body['max_tokens'] == 1024),
            stream=is_object and body.get('stream') is True,
            tools=is_object and body.get('tools') in (None, []),
            prompt_present=any(test_input().prompt_json in text for text in texts),
            no_unrelated_or_test_key=all(UNRELATED not in text and TEST_KEY not in text
                                         for text in texts),
            x_api_key=headers.get_all('x-api-key', []) == [TEST_KEY],
            no_authorization=headers.get('Authorization') is None)
    try:
        return evaluate()
    except Exception:
        return None


class _Server(HTTPServer):
    allow_reuse_address = False

    def __init__(self, mode):
        self.mode, self.count, self.unexpected = mode, 0, 0
        self.matches, self.faults, self.responses = True, 0, 0
        # L7-Q1 expected-preflight counter: HEADs admitted by the approved
        # sequence never touch the unexpected counter; cardinality is one.
        self.preflight_heads = 0
        # Diagnostic-only transcript state; never read by any gate.
        self.transcript, self.transcript_truncated, self.phase = [], False, 'version'
        super().__init__(('127.0.0.1', 0), _Handler)

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(2)
        return sock, address

    def handle_error(self, *_):
        self.faults += 1  # Never print peer headers/body or exception text.
        try:  # Diagnostic note only; no peer data is ever recorded.
            if len(self.transcript) < MAX_TRANSCRIPT_ENTRIES:
                self.transcript.append(dict(kind='connection_error', phase=self.phase))
            else:
                self.transcript_truncated = True
        except Exception:
            pass


class _Handler(BaseHTTPRequestHandler):
    _entry = None  # Diagnostic-only reference to the current transcript entry.

    def log_message(self, *_):
        pass

    def _append(self, entry):
        try:
            transcript = self.server.transcript
            if len(transcript) < MAX_TRANSCRIPT_ENTRIES:
                transcript.append(entry)
            else:
                self.server.transcript_truncated = True
        except Exception:
            pass

    def _begin(self, method):
        entry = dict(kind='request', phase=getattr(self.server, 'phase', 'unknown'),
            method=method if type(method) is str else None,
            target=_sanitize_target(getattr(self, 'path', None)),
            headers=_header_pairs(getattr(self, 'headers', None)),
            stage='unrecorded', stage_detail=None, predicates=None, body=None,
            body_not_read=False, response=None)
        self._entry = entry
        self._append(entry)
        return entry

    def send_error(self, code, message=None, explain=None):
        entry = getattr(self, '_entry', None)
        if entry is None:  # Parser-level refusal (bad request line, unknown method).
            entry = self._begin(getattr(self, 'command', None))
        try:
            entry.update(stage='refused_parser', body_not_read=True, refusal_status=code)
        except Exception:
            pass
        self.server.faults += 1
        super().send_error(code, 'Synthetic probe refusal', 'Request not admitted')

    def _respond(self, code, payload=b'', content_type='application/json'):
        entry = getattr(self, '_entry', None)
        if type(entry) is dict:
            try:
                entry['response'] = _response_summary(code, payload, content_type)
            except Exception:
                pass
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_POST(self):
        s = self.server
        entry = self._begin('POST')
        s.count = min(MAX_REQUESTS+1, s.count+1)
        if s.count > MAX_REQUESTS:
            s.matches = False
            entry['stage'] = 'refused_over_limit'
            entry['body_not_read'] = True
            self._respond(429)
            return
        detail = 'handler_exception'
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if (len(lengths) != 1 or re.fullmatch('[1-9][0-9]{0,6}', lengths[0]) is None
                    or self.headers.get('Transfer-Encoding') is not None):
                detail = 'content_length_or_transfer_encoding_invalid'
                raise ValueError
            length = int(lengths[0])
            if not 1 <= length <= MAX_HTTP_BYTES:
                detail = 'content_length_out_of_range'
                raise ValueError
            raw = self.rfile.read(length)
            if len(raw) != length:
                detail = 'body_read_short'
                raise ValueError
            entry['body'] = _body_summary(raw)
            try:
                body = strict_json(raw.decode('utf-8'))
            except Exception:
                detail = 'body_json_invalid_or_not_utf8'
                raise
            texts = tuple(_strings(body))
            route = urlsplit(self.path)
            good = (route.path == '/v1/messages' and not route.scheme and not route.netloc
                and route.query in ('', 'beta=true') and not route.fragment
                and type(body) is dict and body.get('model') == MODEL_ID
                and type(body.get('max_tokens')) is int and body['max_tokens'] == 1024
                and body.get('stream') is True and body.get('tools') in (None, [])
                and any(test_input().prompt_json in text for text in texts)
                and all(UNRELATED not in text and TEST_KEY not in text for text in texts)
                and self.headers.get_all('x-api-key', []) == [TEST_KEY]
                and self.headers.get('Authorization') is None)
            entry['predicates'] = _body_predicates(body, texts, self.headers, self.path)
            if not good:
                s.matches = False
                entry['stage'] = 'refused_contract'
                self._respond(400)
                return
            entry['stage'] = 'responded_scenario'
            if s.mode in ('rate_limit', 'server_error'):
                payload = json.dumps({'type': 'error', 'error': {
                    'type': 'rate_limit_error' if s.mode == 'rate_limit' else 'api_error',
                    'message': 'Synthetic probe response'}}).encode()
                self._respond(429 if s.mode == 'rate_limit' else 500, payload)
            else:
                self._respond(200, _stream(s.mode), 'text/event-stream')
            s.responses += 1
        except Exception:
            s.faults += 1
            entry.update(stage='handler_fault', stage_detail=detail,
                body_not_read=detail in ('content_length_or_transfer_encoding_invalid',
                                         'content_length_out_of_range'))
            self.close_connection = True

    def _unexpected(self):
        entry = self._begin(self.command)
        self.server.unexpected = min(MAX_REQUESTS+1, self.server.unexpected+1)
        self.server.matches = False
        entry['stage'] = 'refused_unexpected_method'
        entry['body_not_read'] = True
        self._respond(404)

    def _preflight_admissible(self):
        """L7-Q1 validation: exactly one bodyless unauthenticated HEAD to the
        exact /api/hello target, in the message phase and strictly before the
        POST, addressed to exactly one Host naming this designated loopback
        server, carrying only demonstrated preflight header names. Anything
        else stays an unexpected request."""
        server = self.server
        try:
            if (server.phase != 'message' or server.preflight_heads >= 1
                    or server.count > 0 or server.responses > 0
                    or self.command != 'HEAD'):
                return False
            # Unnormalized request target: read it from the RAW request line,
            # not the parser-normalized self.path, so '/api/hello?',
            # '/api/hello#' and '//api/hello' are refused like any other
            # target. Exactly one whitespace-separated token triple (the
            # version token is deliberately unpinned: the approved ruling
            # pins method/target/Host/framing/allowlist/order/cardinality
            # only), target exact.
            line = getattr(self, 'requestline', '')
            parts = line.split() if type(line) is str else []
            if (len(parts) != 3 or parts[0] != 'HEAD'
                    or parts[1] != PREFLIGHT_HEAD_PATH):
                return False
            # Designated authority: exactly one Host header whose value names
            # this numeric-loopback server; missing, duplicate, wrong or
            # arbitrary Host values are refused.
            if self.headers.get_all('Host', []) != [
                    '127.0.0.1:%d' % server.server_port]:
                return False
            # Bodyless framing: no body descriptors; the handler reads no body.
            if (self.headers.get('Content-Length') is not None
                    or self.headers.get('Transfer-Encoding') is not None):
                return False
            # Unauthenticated: credential-bearing names are outside the
            # demonstrated allowlist and fail here already.
            return all(name.lower() in PREFLIGHT_HEADER_NAMES
                       for name in self.headers.keys())
        except Exception:
            return False

    def do_HEAD(self):
        if self._preflight_admissible():
            entry = self._begin('HEAD')
            self.server.preflight_heads += 1
            # Expected preflight per the approved sequence: fully visible in
            # the transcript, never counted as an unexpected request.
            entry['stage'] = 'preflight_head_admitted'
            entry['body_not_read'] = True
            self._respond(404)  # the same fixed 404 the server already sends
            return
        self._unexpected()

    do_GET = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_CONNECT = _unexpected


@contextmanager
def loopback_server(mode):
    server = _Server(mode)
    def serve():
        try:
            server.serve_forever(poll_interval=.05)
        except BaseException:
            server.faults += 1
    worker = Thread(target=serve, name='pal-claude-probe-http')
    failure = None
    try:
        worker.start()
        yield server
    except BaseException as error:
        failure = error
    finally:
        actions = ([server.shutdown] if worker.ident is not None else []) + [server.server_close]
        if worker.ident is not None:
            actions.append(lambda: worker.join(timeout=3))
        for action in actions:
            try:
                action()
            except BaseException as error:
                failure = process._prefer_failure(failure, error)
        if worker.is_alive():
            failure = process._prefer_failure(failure, RuntimeError('probe_server_cleanup_failed'))
    if failure is not None:
        raise failure


def state_snapshot(root, *, expected_root=None):
    """Bounded surviving-state snapshot, not an OS write trace or sandbox.

    Never follows links/reparse points or reads multiply-linked/nonregular files.
    Runtime concurrent replacement is outside the guarantee; any observed
    inconsistency is incomplete, not evidence of no writes.
    """
    root = Path(root)
    files, pending, total, entries = {}, [], 0, 0
    result = dict(complete=True, unsafe_entries=0, limit_reached=False, sentinel_files=0, files=files, root_identity=None)
    needles = tuple(s.encode(encoding) for s in (APPROVED, RESPONSE, TEST_KEY)
                    for encoding in ('utf-8', 'utf-16-le', 'utf-16-be'))
    try:
        info = root.lstat()
        root_id = (info.st_dev, info.st_ino)
        result['root_identity'] = root_id
        if expected_root is not None and root_id != expected_root:
            raise ValueError
        pending.append((root, root_id))
        while pending:
            parent, identity = pending.pop()
            info = parent.lstat()
            if (not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != identity
                    or getattr(info, 'st_file_attributes', 0)
                    & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)):
                result['unsafe_entries'] += 1; result['complete'] = False
                continue
            with os.scandir(parent) as stream:
                for entry in stream:
                    entries += 1
                    if entries > MAX_ENTRIES:
                        result.update(complete=False, limit_reached=True)
                        return result
                    # Windows DirEntry.stat omits device/inode/link count.
                    # Retrieve current identity without following the entry.
                    info = os.stat(entry.path, follow_symlinks=False)
                    name = str(Path(entry.path).relative_to(root))
                    if (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0)
                            & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)):
                        result['unsafe_entries'] += 1; result['complete'] = False
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        files[name] = ('directory',)
                        pending.append((Path(entry.path), (info.st_dev, info.st_ino)))
                        continue
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                        result['unsafe_entries'] += 1; result['complete'] = False
                        continue
                    if info.st_size > MAX_FILE_BYTES or total+info.st_size > MAX_STATE_BYTES:
                        result.update(complete=False, limit_reached=True)
                        return result
                    fd = os.open(entry.path, os.O_RDONLY | getattr(os, 'O_BINARY', 0)
                                 | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
                    failure, content = None, bytearray()
                    try:
                        opened = os.fstat(fd)
                        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                                or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)):
                            raise ValueError
                        while len(content) <= MAX_FILE_BYTES:
                            block = os.read(fd, min(8192, MAX_FILE_BYTES+1-len(content)))
                            if not block:
                                break
                            content.extend(block)
                        if len(content) != info.st_size or os.fstat(fd).st_mtime_ns != info.st_mtime_ns:
                            raise ValueError
                    except BaseException as error:
                        failure = error
                    finally:
                        try:
                            os.close(fd)
                        except BaseException as error:
                            failure = process._prefer_failure(failure, error)
                    if failure is not None:
                        raise failure
                    total += len(content)
                    files[name] = ('file', sha256(content).hexdigest())
                    result['sentinel_files'] += int(any(n in content for n in needles))
    except Exception:
        result['complete'] = False
    return result


def state_delta(before, after):
    names = before['files'].keys() | after['files'].keys()
    return dict(complete=before['complete'] and after['complete'],
        changed_entries=sum(before['files'].get(n) != after['files'].get(n) for n in names),
        unsafe_entries=before['unsafe_entries']+after['unsafe_entries'],
        limit_reached=before['limit_reached'] or after['limit_reached'],
        sentinel_files=after['sentinel_files'])


def _decoder_stage(raw, request):
    """Fixed first-failing validation stage mirroring decode_claude_result's
    admission order (stderr-zero -> outer JSON -> result JSON -> action
    validation, with the envelope/usage steps broken out) for BOTH admitted
    closed shapes: the original envelope and the calibrated 25-key terminal
    representation, whose positive terminal_reason 'completed' is staged at
    the envelope step where neither-shape payloads are still outer_keys.
    Representation-unique deep metadata (uuid/duration formats, subagent
    stats, terminal timing metadata, cost) is not staged, exactly as the
    original mirror never staged it. Diagnostic only: the real decoder
    remains the sole admission decision, and this mirror never feeds
    matching or pass/fail logic. None means every mirrored stage passed."""
    try:
        if type(raw) is not process.ResearchProcessResult:
            return 'not_a_process_result'
        if raw.stderr_bytes != 0:
            return 'stderr_nonzero'
        if not 1 <= len(raw.stdout) <= MAX_RESULT_BYTES:
            return 'stdout_bounds'
        try:
            data = strict_json(raw.stdout.decode('utf-8'))
        except Exception:
            return 'outer_json'
        terminal = type(data) is dict and set(data) == _TERMINAL_OUTER_KEYS
        if (type(data) is not dict
                or (not terminal
                    and not set(_OUTER_REQUIRED) <= set(data) <= set(_OUTER_REQUIRED) | set(_OUTER_OPTIONAL))):
            return 'outer_keys'
        if (data['type'] != 'result' or data['subtype'] != 'success'
                or data['is_error'] is not False or data['stop_reason'] != 'end_turn'
                or data['num_turns'] != 1
                or type(data['permission_denials']) is not list or data['permission_denials']
                or ('errors' in data and (type(data['errors']) is not list or data['errors']))
                or (terminal and data['terminal_reason'] != 'completed')):
            return 'envelope_values'
        if (type(data.get('modelUsage')) is not dict
                or set(data['modelUsage']) != {request.model_id}
                or type(data.get('usage')) is not dict):
            return 'usage'
        if type(data['result']) is not str:
            return 'result_json'
        try:
            actions = strict_json(data['result'])
        except Exception:
            return 'result_json'
        if (type(actions) is not dict or set(actions) != {'calls'}
                or type(actions['calls']) is not list or not 1 <= len(actions['calls']) <= 8):
            return 'action_validation'
        for call in actions['calls']:
            if type(call) is not dict or set(call) != {'name', 'arguments_json'}:
                return 'action_validation'
            try:
                strict_json(call['arguments_json'])
            except Exception:
                return 'action_validation'
        return None
    except Exception:
        return 'not_a_process_result'


def _predecode_capture(raw, request, secrets):
    """Bounded sanitized retention of the returned result BEFORE decoding.

    Keeps stdout length/digest plus a redacted bounded excerpt, the stderr
    BYTE COUNT (ResearchProcessResult retains no stderr content and production
    stderr logging stays disabled), top-level JSON key shapes, and the fixed
    first-failing validation stage. The RESPONSE marker is public synthetic
    data and is deliberately not redacted."""
    capture = dict(stdout_bytes=None, stdout_sha256=None, stdout_utf8=None,
        stdout_excerpt_redacted=None, stdout_excerpt_truncated=None,
        stdout_json_top_keys=None, stdout_json_value_shapes=None, stderr_bytes=None,
        first_failing_validation_stage=_decoder_stage(raw, request),
        capture_status='captured' if type(raw) is process.ResearchProcessResult else 'not_a_result',
        stderr_note='ResearchProcessResult retains only a stderr byte count; '
                    'content is never captured or logged',
        redaction='sentinel markers and probe paths replaced in the retained excerpt')
    if type(raw) is not process.ResearchProcessResult:
        return capture
    stdout = raw.stdout
    capture['stdout_bytes'] = len(stdout)
    capture['stdout_sha256'] = sha256(stdout).hexdigest()
    capture['stderr_bytes'] = raw.stderr_bytes
    try:
        text = stdout.decode('utf-8')
        capture['stdout_utf8'] = True
    except UnicodeDecodeError:
        capture['stdout_utf8'] = False
        text = stdout[:MAX_STDOUT_EXCERPT_BYTES].decode('utf-8', 'replace')
    excerpt_source = text[:MAX_STDOUT_EXCERPT_BYTES]
    capture['stdout_excerpt_truncated'] = len(text) > len(excerpt_source)
    capture['stdout_excerpt_redacted'] = _redact_text(excerpt_source, secrets)
    if capture['stdout_utf8']:
        try:
            data = strict_json(text)
        except Exception:
            data = None
        if type(data) is dict:
            keys = sorted(data)[:MAX_HEADER_PAIRS]
            capture['stdout_json_top_keys'] = [
                _redact_text(key, secrets)[:MAX_TRANSCRIPT_STRING] for key in keys]
            capture['stdout_json_value_shapes'] = {
                _redact_text(key, secrets)[:MAX_TRANSCRIPT_STRING]:
                    _json_shape(data[key]) for key in keys}
    return capture


def _state_inventory(before, after, secrets):
    """Bounded relative-path/entry-type/hash inventory for diagnosis. The
    qualification baseline stays the ORIGINAL initial snapshot via
    state_delta(before, after); this inventory only explains which phase
    produced which change, without hiding either. Never exports the private
    HOME: bounded path/type/hash lists only, no file contents."""
    names = sorted(before['files'].keys() | after['files'].keys(), key=str)
    changed = [name for name in names if before['files'].get(name) != after['files'].get(name)]
    bounded = changed[:MAX_INVENTORY_ENTRIES]

    def sanitized(name):
        return _redact_text(name, secrets)[:MAX_TRANSCRIPT_STRING]
    entries = [dict(path=sanitized(name), before=before['files'].get(name),
                    after=after['files'].get(name)) for name in bounded]
    added = sum(1 for name in changed if name not in before['files'])
    removed = sum(1 for name in changed if name not in after['files'])
    return dict(complete=before['complete'] and after['complete'],
        limit_reached=before['limit_reached'] or after['limit_reached'],
        changed_entries=len(changed), added=added, removed=removed,
        modified=len(changed)-added-removed, entries=entries,
        entries_listed=len(bounded), entries_truncated=len(changed) > MAX_INVENTORY_ENTRIES,
        redaction='relative entry names redacted for sentinel markers only')


def _read_bootstrap_file(path, limit):
    """Bounded no-follow read of one regular singly-linked file. Returns
    (bytes, None) or (None, fixed reason); any anomaly is a validation
    failure, never an exception and never content beyond the bound."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0)
                     | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    except OSError:
        return None, 'unreadable'
    content, failure = bytearray(), None
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError('unsafe_entry')
        if opened.st_size > limit:
            raise ValueError('oversized')
        while len(content) <= limit:
            block = os.read(fd, min(8192, limit+1-len(content)))
            if not block:
                break
            content.extend(block)
        if (len(content) != opened.st_size
                or os.fstat(fd).st_mtime_ns != opened.st_mtime_ns):
            raise ValueError
    except BaseException as error:
        failure = error
    finally:
        try:
            os.close(fd)
        except BaseException as error:
            failure = process._prefer_failure(failure, error)
    if failure is not None:
        reason = failure.args[0] if (type(failure) is ValueError and failure.args
                                     and type(failure.args[0]) is str) else 'read_failed'
        return None, reason
    return bytes(content), None


def _bootstrap_config_schema(data):
    """Closed schema of the demonstrated config/.claude.json: exactly the nine
    demonstrated bootstrap keys with bounded values. Unknown keys (including
    any credential, prompt, response, transcript or tool field), wrong types
    or out-of-bound values are rejected."""
    if type(data) is not dict:
        return 'not_an_object'
    expected = {'firstStartTime', 'firstStartVersion', 'machineID',
                'opusProMigrationComplete', 'sonnet1m45MigrationComplete',
                'seenNotifications', 'hasResetAutoModeOptInForDefaultOffer',
                'migrationVersion', 'userID'}
    if set(data) != expected:
        return 'keys'
    if not (type(data['firstStartTime']) is str
            and _BOOTSTRAP_INSTANT.fullmatch(data['firstStartTime'])):
        return 'firstStartTime'
    if data['firstStartVersion'] != CLAUDE_VERSION:
        return 'firstStartVersion'
    for key in ('machineID', 'userID'):
        if not (type(data[key]) is str and _BOOTSTRAP_ID.fullmatch(data[key])):
            return key
    for key in ('opusProMigrationComplete', 'sonnet1m45MigrationComplete',
                'hasResetAutoModeOptInForDefaultOffer'):
        if data[key] is not True:
            return key
    if type(data['seenNotifications']) is not dict or data['seenNotifications']:
        return 'seenNotifications'
    if (type(data['migrationVersion']) is not int
            or data['migrationVersion'] != BOOTSTRAP_MIGRATION_VERSION):
        return 'migrationVersion'
    return None


def _bootstrap_backup_schema(data):
    """Closed schema of the demonstrated backup: exactly the two demonstrated
    pre-migration keys with the same bounded value forms. The real backup is
    the two-field subset the CLI wrote before migration, not a byte copy of
    .claude.json; a byte-identical copy of the demonstrated backup parses to
    exactly these two keys, anything richer or different is rejected."""
    if type(data) is not dict:
        return 'not_an_object'
    if set(data) != {'firstStartTime', 'firstStartVersion'}:
        return 'keys'
    if not (type(data['firstStartTime']) is str
            and _BOOTSTRAP_INSTANT.fullmatch(data['firstStartTime'])):
        return 'firstStartTime'
    if data['firstStartVersion'] != CLAUDE_VERSION:
        return 'firstStartVersion'
    return None


def _bootstrap_exception(before, after, root, secrets):
    """Owner-approved L7-Q2 five-entry first-run bootstrap evaluation.

    The qualification delta recorded in result['state'] still compares the
    ORIGINAL initial snapshot (no baseline relocation, prewarming, precreation
    or cleanup). This evaluation only decides whether exactly the five
    demonstrated additions -- regular file config/.claude.json, directory
    config/backups/ holding exactly one conforming
    .claude.json.backup.<13-digit epoch-milliseconds> file, and empty
    directories config/sessions/ and tmp/claude-1000/ -- pass closed-schema
    content validation read inside the disposable root. Anything else keeps
    the state gate failed. Raw pathnames are used for validation only: every
    exported pathname (including rejected-case names) passes the existing
    secret redaction with the transcript length bound, and no file content is
    copied into the observation -- outcomes, byte sizes and the
    already-recorded snapshot hashes only."""
    before_files, after_files = before['files'], after['files']
    names = before_files.keys() | after_files.keys()
    added = sorted(str(name) for name in names if name not in before_files)
    removed = sorted(str(name) for name in names if name not in after_files)
    modified = sorted(str(name) for name in names if name in before_files
                      and name in after_files
                      and before_files[name] != after_files[name])
    claude_json = str(Path('config', '.claude.json'))
    backups_dir = str(Path('config', 'backups'))
    sessions_dir = str(Path('config', 'sessions'))
    tmp_dir = str(Path('tmp', 'claude-1000'))
    fixed_expected = (claude_json, backups_dir, sessions_dir, tmp_dir)
    backups_children = sorted(name for name in after_files
                              if name.startswith(backups_dir + os.sep))
    conforming = [name for name in backups_children
                  if _BOOTSTRAP_BACKUP_NAME.fullmatch(name[len(backups_dir)+1:])]
    violations, parsed = [], {}
    entries = dict(claude_json=None, backups_dir=None, backup=None,
                   sessions_dir=None, tmp_dir=None)
    content = dict(claude_json=None, backup=None)
    if not (before['complete'] and after['complete']):
        violations.append('snapshot_incomplete')
    if removed:
        violations.append('removed_entries')
    if modified:
        violations.append('modified_entries')
    if after_files.get(claude_json, (None,))[0] == 'file':
        entries['claude_json'] = claude_json
    else:
        violations.append('claude_json_not_a_regular_file')
    for name, key in ((backups_dir, 'backups_dir'), (sessions_dir, 'sessions_dir'),
                      (tmp_dir, 'tmp_dir')):
        if after_files.get(name) == ('directory',):
            entries[key] = name
        else:
            violations.append(key + '_not_a_directory')
    if len(conforming) != 1:
        violations.append('backup_not_exactly_one_conforming_name')
    else:
        entries['backup'] = conforming[0]
    if backups_children != conforming:
        violations.append('backups_dir_not_exactly_one_backup')
    if any(name.startswith(sessions_dir + os.sep) for name in after_files):
        violations.append('sessions_dir_not_empty')
    if any(name.startswith(tmp_dir + os.sep) for name in after_files):
        violations.append('tmp_dir_not_empty')
    expected_five = fixed_expected + (conforming[0],) if conforming else fixed_expected
    if len(added) != 5 or sorted(added) != sorted(expected_five):
        violations.append('added_not_exactly_the_five_demonstrated')
    if entries['claude_json'] is not None:
        blob, reason = _read_bootstrap_file(Path(root)/'config'/'.claude.json',
                                            BOOTSTRAP_CONFIG_MAX_BYTES)
        if blob is None:
            violations.append('claude_json_' + reason)
            content['claude_json'] = dict(bytes=None, schema=BOOTSTRAP_CONFIG_SCHEMA,
                                          valid=False, reason=reason)
        else:
            schema_reason = None
            try:
                data = strict_json(blob.decode('utf-8'))
                schema_reason = _bootstrap_config_schema(data)
            except Exception:
                schema_reason = 'not_strict_json'
            content['claude_json'] = dict(bytes=len(blob),
                schema=BOOTSTRAP_CONFIG_SCHEMA, valid=schema_reason is None,
                reason=schema_reason)
            if schema_reason is not None:
                violations.append('claude_json_schema_' + schema_reason)
            else:
                parsed['claude_json'] = data
    if entries['backup'] is not None:
        leaf = entries['backup'][len(backups_dir)+1:]
        blob, reason = _read_bootstrap_file(
            Path(root)/'config'/'backups'/leaf, BOOTSTRAP_BACKUP_MAX_BYTES)
        if blob is None:
            violations.append('backup_' + reason)
            content['backup'] = dict(bytes=None, name=_redact_text(leaf, secrets)[:MAX_TRANSCRIPT_STRING],
                schema=BOOTSTRAP_BACKUP_SCHEMA, valid=False, reason=reason)
        else:
            schema_reason = None
            try:
                data = strict_json(blob.decode('utf-8'))
                schema_reason = _bootstrap_backup_schema(data)
            except Exception:
                schema_reason = 'not_strict_json'
            content['backup'] = dict(bytes=len(blob),
                name=_redact_text(leaf, secrets)[:MAX_TRANSCRIPT_STRING],
                schema=BOOTSTRAP_BACKUP_SCHEMA, valid=schema_reason is None,
                reason=schema_reason)
            if schema_reason is not None:
                violations.append('backup_schema_' + schema_reason)
            else:
                parsed['backup'] = data
    if len(parsed) == 2 and (parsed['backup']['firstStartTime']
                             != parsed['claude_json']['firstStartTime']):
        violations.append('backup_firstStartTime_mismatch')

    def sanitized(name):  # exported pathnames: redacted, length-bounded
        return _redact_text(name, secrets)[:MAX_TRANSCRIPT_STRING]
    return dict(applied=not violations,
        approval='L7-Q2 five-entry first-run bootstrap exception '
                 '(owner-approved 2026-09-29, DELIVERY_PLAN section 63)',
        baseline='original initial snapshot (unchanged; relocation excluded)',
        raw_delta=dict(added=len(added), removed=len(removed), modified=len(modified)),
        added=[sanitized(name) for name in added],
        removed=[sanitized(name) for name in removed],
        modified=[sanitized(name) for name in modified],
        entries={key: (sanitized(name) if type(name) is str else None)
                 for key, name in entries.items()},
        content=content, violations=violations)


def _write_diagnostic_sidecars(root, payloads):
    """Write bounded sanitized sidecars next to (never inside) the snapshotted
    probe root, so in the contained run they land under the /pal-output pytest
    base temp outside the snapshotted private root. Files are created
    exclusively (O_CREAT|O_EXCL, no-follow where available) under a fixed
    sub-budget well inside the 64 MiB export allowance. Any failure or budget
    overflow marks THIS diagnostic capture incomplete-and-recorded; it can
    never fail or pass the qualification itself."""
    directory = Path(root).parent / (Path(root).name + DIAGNOSTIC_DIR_SUFFIX)
    status = dict(directory=directory.name, budget_bytes=DIAGNOSTIC_BUDGET_BYTES,
                  files=[], written_bytes=0, status='written', incomplete_reason=None,
                  note='exclusive creation, bounded diagnostic sub-budget; '
                       'incomplete captures are recorded, never raised')
    try:
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            info = directory.lstat()
            if not stat.S_ISDIR(info.st_mode):
                raise
        for name, value in payloads.items():
            blob = json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')
            if status['written_bytes'] + len(blob) > DIAGNOSTIC_BUDGET_BYTES:
                status['status'] = 'incomplete-and-recorded'
                status['incomplete_reason'] = status['incomplete_reason'] or 'diagnostic_budget_exceeded'
                status['files'].append([name, 'not_written', 0])
                continue
            try:
                fd = os.open(directory/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0), 0o600)
                try:
                    written = 0
                    while written < len(blob):
                        written += os.write(fd, blob[written:])
                finally:
                    os.close(fd)
            except OSError:
                status['status'] = 'incomplete-and-recorded'
                status['incomplete_reason'] = status['incomplete_reason'] or 'sidecar_creation_failed'
                status['files'].append([name, 'skipped', 0])
                continue
            status['files'].append([name, 'written', len(blob)])
            status['written_bytes'] += len(blob)
    except Exception:
        status['status'] = 'incomplete-and-recorded'
        status['incomplete_reason'] = status['incomplete_reason'] or 'sidecar_directory_unavailable'
    return status


def run_probe(image, digest, size, *, root, mode, allow_probe=False, process_runner=None):
    """Two explicit operations: --version, then ONE synthetic prompt scenario.

    A hash/version string does not establish vendor provenance. Only one fixed
    endpoint variable is changed for the local HTTP test, never runtime profiles.
    Temp files are retained for local inspection; never upload the entire root.
    """
    if allow_probe is not True:
        raise ValueError('probe_opt_in_required')
    image, digest, size = _image_values(image, digest, size)
    if type(mode) is not str or mode not in MODES:
        raise ValueError('probe_mode_invalid')
    root = Path(root)
    if not root.is_absolute():
        raise ValueError('probe_root_unavailable')
    try:
        root.mkdir(mode=0o700)
    except OSError:
        raise ValueError('probe_root_unavailable') from None
    for name in ('home', 'config', 'tmp', 'work'):
        (root/name).mkdir(mode=0o700)
    (root/'CLAUDE.md').write_text(UNRELATED, encoding='utf-8')
    (root/'work/CLAUDE.md').write_text(UNRELATED, encoding='utf-8')
    (root/'config/settings.json').write_text(json.dumps({'env': {'PAL_UNRELATED': UNRELATED}}), encoding='utf-8')
    env = {'HOME': str(root/'home'), 'USERPROFILE': str(root/'home'), 'CLAUDE_CONFIG_DIR': str(root/'config'),
           'TMPDIR': str(root/'tmp'), 'TMP': str(root/'tmp'), 'TEMP': str(root/'tmp')}
    if os.name == 'nt':
        system = os.environ.get('SystemRoot')
        if not system or not Path(system).is_absolute():
            raise ValueError('probe_system_root_unavailable')
        env.update(SYSTEMROOT=system, WINDIR=system)
    spec = process.ResearchProcessSpec((image,), str(root/'work'), tuple(sorted(env.items())),
        digest, 20000, max_executable_bytes=size)
    # Validate the selected image before any test callback, not just trust a label.
    try:
        info = Path(image).lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size != size:
            raise ValueError
        process._verify_executable(spec)
    except Exception:
        raise ValueError('probe_image_unavailable') from None
    runner = process.run_research_process if process_runner is None else process_runner
    result = dict(schema_version='claude-cli-probe-v2', mode=mode, image_sha256=digest,
        image_bytes=size, cli_version=CLAUDE_VERSION, version_matches=False,
        version_status='not_started', version_error_code=None,
        process_status='not_started', process_error_code=None, decoder_status='not_attempted',
        reported_tokens=None, response_matches=False, test_endpoint_override='numeric-loopback-http',
        activation_authorized=False, external_egress_verified=False, outside_root_verified=False,
        transient_writes_verified=False, vendor_provenance_verified=False,
        preflight_head_observed=0, bootstrap_exception=None)
    before = state_snapshot(root)
    if not before['complete']:
        raise ValueError('probe_initial_snapshot_failed')
    secrets = _redaction_secrets(root)
    predecode = dict(stdout_bytes=None, stdout_sha256=None, stdout_utf8=None,
        stdout_excerpt_redacted=None, stdout_excerpt_truncated=None,
        stdout_json_top_keys=None, stdout_json_value_shapes=None, stderr_bytes=None,
        first_failing_validation_stage=None, capture_status='not_attempted',
        stderr_note='ResearchProcessResult retains only a stderr byte count; '
                    'content is never captured or logged',
        redaction='sentinel markers and probe paths replaced in the retained excerpt')
    with loopback_server(mode) as server:
        profile = ClaudeExecProfile(spec, 'https://127.0.0.1:'+str(server.server_port))
        request = test_input()
        public = profile.prepare(request, api_key=TEST_KEY)
        modified = dict(public.environment)
        modified['ANTHROPIC_BASE_URL'] = 'http://127.0.0.1:'+str(server.server_port)
        selected = replace(public, environment=tuple(sorted(modified.items())))
        result['declared_profile_sha256'] = profile.contract_sha256
        try:
            version = runner(spec=replace(selected, argv=(image, '--version')), stdin=b'', allow_process_start=True)
            result['version_status'] = 'returned'
            result['version_matches'] = (type(version) is process.ResearchProcessResult
                and version.stderr_bytes == 0 and version.stdout in (VERSION_OUTPUT.encode(), VERSION_OUTPUT.replace('\n', '\r\n').encode()))
        except process.ResearchProcessError as error:
            result['version_status'] = 'failed'
            result['version_error_code'] = _process_error_code(error)
        # Diagnostic mid snapshot: separates version-time from prompt-time state
        # changes. The qualification baseline below stays the ORIGINAL snapshot.
        mid = state_snapshot(root, expected_root=before['root_identity'])
        if result['version_matches'] and server.count == server.unexpected == server.faults == 0:
            server.phase = 'message'
            try:
                raw = runner(spec=selected, stdin=request.prompt_json.encode(), allow_process_start=True)
                result['process_status'] = 'returned'
                predecode = _predecode_capture(raw, request, secrets)
                try:
                    reply = decode_claude_result(raw, request=request, call_number=1)
                    result['decoder_status'] = 'accepted'
                    result['reported_tokens'] = reply.total_tokens
                    result['response_matches'] = (len(reply.calls) == 1
                        and reply.calls[0].name == 'search_evidence'
                        and strict_json(reply.calls[0].arguments_json) == {'query': RESPONSE})
                except ValueError:
                    result['decoder_status'] = 'rejected'
            except process.ResearchProcessError as error:
                result['process_status'] = 'failed'
                result['process_error_code'] = _process_error_code(error)
    result.update(request_count=server.count, unexpected_requests=server.unexpected,
        preflight_head_observed=server.preflight_heads,
        request_contract_matches=server.matches and server.count == 1
            and server.preflight_heads == 1,
        server_faults=server.faults, responses_sent=server.responses)
    after = state_snapshot(root, expected_root=before['root_identity'])
    result['state'] = state_delta(before, after)
    # L7-Q2: the raw delta above keeps the ORIGINAL initial snapshot as its
    # baseline; this evaluation records whether the owner-approved five-entry
    # content-validated bootstrap exception applies to the state gate.
    result['bootstrap_exception'] = _bootstrap_exception(before, after, root, secrets)
    # Observation-only diagnostics (arbitration prescriptions 2-5). Nothing
    # below feeds observation_passed, any counter or any matching decision.
    diagnostics = dict(schema_version=DIAGNOSTIC_SCHEMA,
        note='observation-only diagnostics; qualification inputs are unchanged',
        transcript=server.transcript, transcript_truncated=server.transcript_truncated,
        transcript_entry_limit=MAX_TRANSCRIPT_ENTRIES, predecode=predecode,
        state_inventory=dict(initial_complete=before['complete'],
            after_version_complete=mid['complete'], after_scenario_complete=after['complete'],
            version_time=_state_inventory(before, mid, secrets),
            scenario_time=_state_inventory(mid, after, secrets),
            qualification_baseline='original initial snapshot (unchanged)'))
    diagnostics['sidecars'] = _write_diagnostic_sidecars(root, {
        'server-transcript.json': dict(schema_version=DIAGNOSTIC_SCHEMA, mode=mode,
            image_sha256=digest, cli_version=CLAUDE_VERSION, transcript=server.transcript,
            transcript_truncated=server.transcript_truncated,
            counters=dict(requests=server.count, unexpected=server.unexpected,
                          preflight_heads=server.preflight_heads,
                          responses=server.responses, faults=server.faults),
            redaction='header values, body string values and stderr content redacted'),
        'predecode.json': dict(schema_version=DIAGNOSTIC_SCHEMA, mode=mode, predecode=predecode),
        'state-inventory.json': dict(schema_version=DIAGNOSTIC_SCHEMA, mode=mode,
            qualification_state=result['state'],
            preflight_head_observed=server.preflight_heads,
            bootstrap_exception=result['bootstrap_exception'],
            state_inventory=diagnostics['state_inventory'])})
    result['diagnostics'] = diagnostics
    return result


def observation_passed(value):
    """Engineering subset only. Success can NEVER authorize real activation.

    Prospective criteria per the two owner-approved L7 acceptance changes
    (2026-09-29, DELIVERY_PLAN section 63). Request gate (L7-Q1): exactly one
    admitted bodyless unauthenticated preflight HEAD before the one matching
    POST -- unexpected_requests must still be zero and preflight_head_observed
    must be exactly one. State gate (L7-Q2): zero changes, or exactly the five
    demonstrated bootstrap additions with the content-validated exception
    applied while the raw delta stays recorded. Baseline relocation and every
    other request or state change remain failures."""
    state = value['state']
    bootstrap = value.get('bootstrap_exception')
    state_ok = (state['complete'] is True and state['unsafe_entries'] == 0
        and state['sentinel_files'] == 0 and state['limit_reached'] is False
        and (state['changed_entries'] == 0 or (state['changed_entries'] == 5
            and type(bootstrap) is dict and bootstrap.get('applied') is True
            and bootstrap.get('violations') == []
            and bootstrap.get('raw_delta') == dict(added=5, removed=0, modified=0))))
    common = (value['version_matches'] is True and value['request_count'] == 1
        and value.get('preflight_head_observed') == 1
        and value['unexpected_requests'] == value['server_faults'] == 0
        and value['request_contract_matches'] is True and value['responses_sent'] == 1
        and state_ok)
    if value['mode'] == 'success':
        return (common and value['decoder_status'] == 'accepted' and value['reported_tokens'] == 26
                and value['response_matches'] is True)
    if value['mode'] not in MODES:
        return False
    # A negative case passes only after its one matching request/response AND
    # either an ordinary nonzero child exit or a returned result rejected by
    # the strict decoder. Signal death, timeout, stop, failed startup, output
    # limit, incomplete input, cleanup failure, a non-allowlisted code and
    # generic infrastructure failure all fail the case.
    if value['process_status'] == 'failed':
        return common and value['process_error_code'] == 'research_process_nonzero_exit'
    return common and value['process_status'] == 'returned' and value['decoder_status'] == 'rejected'
