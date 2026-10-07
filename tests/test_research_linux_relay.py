"""Crossing-independent validation matrix for the L9 relay core (slice 1).

Covers everything in ``research_linux_relay`` that does NOT depend on how the
relay channel crosses the namespace boundary (INNER_PEER_SOURCE/STAGE_SOURCE
are deliberately absent pending the design amendment):

* declaration tests - bounds table, closed outcome vocabulary, trust-record
  validation, policy-digest shape/sensitivity, port draw;
* static engine-source tests - stdlib-only AST, protocol/TLS/CA pins, no
  proxy semantics, single upstream socket site;
* exec'd-engine pure-function units - permitted-address matrix, request
  validation order, strict CRLF split, origin-only reconstruction;
* real-subprocess matrix - the ENGINE_SOURCE runs as an actual OS child
  process over harness pipes (two relay channel halves, control, report,
  liveness, sealed CA descriptor). On Windows, where ``select`` refuses pipe
  descriptors and ``pass_fds`` does not exist, the test-only driver installs
  the inherited pipe handles as descriptors and the engine's own portable
  wait fallback applies (the L8-B select-shim philosophy: only the WAIT
  differs, never the byte path). DNS resolution is injected into the child
  through a getaddrinfo stub so no test ever performs real name resolution
  or off-loopback egress; TLS fakes use synthetic self-signed test
  identities generated at test time.

No real provider, credential or official client is involved anywhere. All
sentinels are synthetic test markers; evidence-hygiene assertions prove none
of them ever reach a report or counter.
"""
from hashlib import sha256
import ast
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time

import pytest

from polymarket_alpha_lab import research_linux_relay as relay

if os.name == 'nt':  # Windows development host support (test harness only)
    import msvcrt

OPENSSL = shutil.which('openssl')
ORIGIN_HOSTNAME = 'pal-relay-origin.invalid'
MISMATCH_HOSTNAME = 'pal-relay-mismatch.invalid'
UNRELATED_HOSTNAME = 'pal-relay-unrelated.invalid'
KEY_SENTINEL = b'PAL-KEY-SENTINEL-1234'
PROMPT_SENTINEL = b'PAL-PROMPT-SENTINEL-987'
RESPONSE_SENTINEL = b'PAL-RESPONSE-SENTINEL'
SYNTHETIC_CA_BYTES = b'pal-synthetic-relay-ca-bytes-v1\n'
SYNTHETIC_CA = {'pem': SYNTHETIC_CA_BYTES,
                'sha256': sha256(SYNTHETIC_CA_BYTES).hexdigest(),
                'size': len(SYNTHETIC_CA_BYTES)}
DNS_LOOPBACK = {'results': [['2', '127.0.0.1']]}


# ---------------------------------------------------------------------------
# Declaration tests: constants, vocabulary, records, digest input
# ---------------------------------------------------------------------------

def test_bounds_table_constants():
    assert relay.RELAY_PROTOCOL_VERSION == 'research-linux-relay-v1'
    assert relay.DEFAULT_ORIGIN_HOSTNAME == 'api.anthropic.com'
    assert relay.MAX_RELAY_REQUEST_BYTES == 16_000_000
    assert relay.MAX_RELAY_RESPONSE_BYTES == 32 * 1024 * 1024
    assert relay.RELAY_RESPONSE_READ_CHUNK == 4096
    assert relay.RELAY_CONNECT_TIMEOUT_MS == 10_000
    assert relay.RELAY_HANDSHAKE_TIMEOUT_MS == 10_000
    assert relay.RELAY_IDLE_TIMEOUT_MS == 30_000
    assert relay.RELAY_PORT_WINDOW == (20000, 32767)
    assert relay.MAX_RELAY_HEADER_COUNT == 32
    assert relay.MAX_RELAY_HEADER_BYTES == 8192
    assert relay.MAX_RELAY_HEAD_BYTES == 65536
    assert relay.RELAY_CA_SIZE_CAP == 1024 * 1024


def test_outcome_vocabulary_is_closed_and_exact():
    assert relay.RELAY_OUTCOMES == frozenset((
        'relay_ok', 'relay_stopped', 'relay_parent_lost',
        'relay_refused_method', 'relay_refused_target',
        'relay_refused_authority', 'relay_refused_header',
        'relay_refused_framing', 'relay_refused_cardinality',
        'relay_redirect_refused', 'relay_dns_refused',
        'relay_request_bytes_exceeded', 'relay_response_bytes_exceeded',
        'relay_connect_timeout', 'relay_handshake_timeout',
        'relay_idle_timeout', 'relay_total_timeout', 'relay_channel_failed',
        'relay_teardown_failed', 'relay_preflight_not_approved'))
    assert type(relay.RELAY_OUTCOMES) is frozenset


def test_validate_relay_outcome_membership():
    for outcome in relay.RELAY_OUTCOMES:
        assert relay.validate_relay_outcome(outcome) == outcome
    for bad in ('relay_ok ', 'ok', 'relay_retry', '', 'RELAY_OK', None, 7):
        with pytest.raises(ValueError, match='relay_outcome_invalid'):
            relay.validate_relay_outcome(bad)


def test_module_is_stdlib_only_with_no_import_time_io():
    source = Path(relay.__file__).read_text(encoding='utf-8')
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or '')
    assert imported <= {'__future__', 'dataclasses', 'hashlib', 'os', 're'}
    # No module-level call expressions outside class bodies / functions: the
    # module performs no I/O at import (dataclass field defaults inside class
    # bodies are the only tolerated call sites).
    for statement in tree.body:
        assert isinstance(statement, (ast.Import, ast.ImportFrom, ast.Assign,
                                      ast.AnnAssign, ast.Expr, ast.FunctionDef,
                                      ast.ClassDef)), statement
    assert 'import socket' not in source.split('ENGINE_SOURCE')[0]
    assert 'polymarket_alpha_lab' not in source.split('ENGINE_SOURCE =')[0]
    assert 'psycopg' not in source


def test_omission_boundary_is_declared_and_inner_peer_absent():
    source = Path(relay.__file__).read_text(encoding='utf-8')
    # The crossing-dependent sources are absent as constants; the docstring
    # still names them as the declared omission boundary.
    assert not hasattr(relay, 'INNER_PEER_SOURCE')
    assert not hasattr(relay, 'STAGE_SOURCE')
    assert 'INNER_PEER_SOURCE =' not in source
    assert 'STAGE_SOURCE =' not in source
    assert 'Slice boundary (deliberate omission)' in relay.__doc__
    assert 'INNER_PEER_SOURCE' in relay.__doc__


def test_engine_digest_mirrors_the_helper_digest_pattern():
    computed = sha256(relay.ENGINE_SOURCE.encode('utf-8')).hexdigest()
    assert relay._engine_digest() == computed
    assert len(computed) == 64
    assert all(character in '0123456789abcdef' for character in computed)
    mutated = relay.ENGINE_SOURCE.replace('MAX_HEAD_BYTES', 'MAX_HEAD_BYTES ', 1)
    assert sha256(mutated.encode('utf-8')).hexdigest() != computed


def test_draw_relay_port_is_fresh_and_inside_the_window():
    draws = [relay.draw_relay_port() for _ in range(400)]
    assert all(relay.RELAY_PORT_WINDOW[0] <= port <= relay.RELAY_PORT_WINDOW[1]
               for port in draws)
    # A fresh os.urandom draw per call: hundreds of draws produce a wide
    # spread (a sequential or cached value could not).
    assert len(set(draws)) > 120
    low, high = relay.RELAY_PORT_WINDOW
    assert low == 20000 and high == 32767


@pytest.mark.parametrize('name,max_count,required', [
    ('Host', 1, True), ('x api key', 1, True), ('x-api-key ', 1, True),
    ('-leading', 1, True), ('', 1, True), ('UPPER', 1, True),
    ('x-api-key', 2, True), ('x-api-key', 0, True),
    ('x-api-key', 1, 'yes'), ('content-length', 1, True),
    ('transfer-encoding', 1, True), ('a' * 129, 1, True),
])
def test_header_rule_closed_validation(name, max_count, required):
    with pytest.raises(ValueError, match='relay_trust_config_invalid'):
        relay.RelayHeaderRule(name=name, max_count=max_count, required=required)


def test_header_rule_accepts_exact_lowercase_single_required():
    rule = relay.RelayHeaderRule(name='anthropic-beta')
    assert rule.max_count == 1 and rule.required is True
    assert rule.rule_dict() == {'name': 'anthropic-beta', 'max_count': 1,
                                'required': True}


@pytest.mark.parametrize('changes', [
    {'method': 'GET'}, {'method': 'get'}, {'method': 'CONNECT'},
    {'target': 'v1/messages'}, {'target': '/v1/messages?beta=true'},
    {'target': '/v1 messages'}, {'target': '/v1/messages\x00'},
    {'query': '?beta=true'}, {'query': 'be ta'},
    {'forwarded_headers': ()},
    {'forwarded_headers': (relay.RelayHeaderRule('x-api-key'),)},
    {'forwarded_headers': (relay.RelayHeaderRule('host'),
                           relay.RelayHeaderRule('host'))},
    {'forwarded_headers': (relay.RelayHeaderRule('host'),
                           relay.RelayHeaderRule('x-api-key'),
                           relay.RelayHeaderRule('x-api-key'))},
])
def test_request_entry_closed_validation(changes):
    with pytest.raises(ValueError, match='relay_trust_config_invalid'):
        relay.RelayRequestEntry(**changes)


def test_request_entry_default_is_the_messages_post():
    entry = relay.RelayRequestEntry()
    assert entry.method == 'POST'
    assert entry.target == '/v1/messages'
    assert entry.query == 'beta=true'
    assert entry.expected_target() == '/v1/messages?beta=true'
    names = {rule.name for rule in entry.forwarded_headers}
    assert names == {'host', 'x-api-key', 'content-type', 'accept',
                     'accept-encoding', 'anthropic-version', 'anthropic-beta'}


@pytest.mark.parametrize('path,sha256,size', [
    ('C:\\pal\\ca.pem', 'a' * 64, 2048),
    ('relative/ca.pem', 'a' * 64, 2048),
    ('/pal/../ca.pem', 'a' * 64, 2048),
    ('/pal/ca.pem', 'A' * 64, 2048),
    ('/pal/ca.pem', 'a' * 63, 2048),
    ('/pal/ca.pem', 'a' * 64, 0),
    ('/pal/ca.pem', 'a' * 64, relay.RELAY_CA_SIZE_CAP + 1),
])
def test_ca_bundle_pin_local_validation(path, sha256, size):
    with pytest.raises(ValueError, match='relay_trust_config_invalid'):
        relay.RelayCaBundlePin(path, sha256, size)


def _trust(**changes):
    values = dict(
        ca_bundle=relay.RelayCaBundlePin('/opt/pal-synthetic/relay-ca.pem',
                                         SYNTHETIC_CA['sha256'],
                                         SYNTHETIC_CA['size']),
        origin_hostname=ORIGIN_HOSTNAME,
        permitted_address_rule='qualification-loopback-only')
    values.update(changes)
    return relay.RelayTrustConfig(**values)


@pytest.mark.parametrize('changes', [
    {'origin_hostname': 'api.anthropic.com/user'},
    {'origin_hostname': 'api.anthropic.com?q'},
    {'origin_hostname': 'api.anthropic.com#f'},
    {'origin_hostname': 'user@api.anthropic.com'},
    {'origin_hostname': 'api.anthropic.com:443'},
    {'origin_hostname': 'API.anthropic.com'},
    {'origin_hostname': 'api anthropic'},
    {'origin_hostname': ''},
    {'origin_hostname': 'a' * 254},
    {'origin_scheme': 'http'},
    {'origin_port': 0}, {'origin_port': 65536},
    {'permitted_address_rule': 'anything-goes'},
    {'tls_floor': 'tls10'}, {'tls_floor': 'tls13'},
    {'max_relay_request_bytes': 0},
    {'max_relay_request_bytes': relay.MAX_RELAY_REQUEST_BYTES + 1},
    {'max_relay_response_bytes': 0},
    {'relay_response_read_chunk': 0},
    {'relay_response_read_chunk': 4097},
    {'connect_timeout_ms': 0}, {'handshake_timeout_ms': -1},
    {'idle_timeout_ms': 0}, {'total_timeout_ms': 0},
    {'total_timeout_ms': relay.RELAY_TOTAL_TIMEOUT_CAP_MS + 1},
    {'max_header_count': 0}, {'max_header_bytes': 0}, {'max_head_bytes': 0},
    {'max_relay_request_bytes': True},
    {'requests': ()},
    {'requests': (relay.RelayRequestEntry(), relay.RelayRequestEntry())},
    {'requests': (relay.RelayRequestEntry(target='/v1/other'),)},
])
def test_trust_config_closed_validation(changes):
    with pytest.raises(ValueError, match='relay_trust_config_invalid'):
        _trust(**changes)


def test_trust_config_preflight_refusal_uses_its_own_code():
    entry = relay.RelayRequestEntry(target='/api/hello', query='')
    with pytest.raises(ValueError, match='relay_preflight_not_approved'):
        _trust(preflight_entries=(entry,))


def test_trust_config_total_timeout_none_means_spec_budget():
    assert _trust().total_timeout_ms is None
    assert _trust(total_timeout_ms=1200).total_timeout_ms == 1200


def test_policy_dict_shape_and_digest_sensitivity():
    policy = _trust().policy_dict()
    assert policy['protocol_version'] == relay.RELAY_PROTOCOL_VERSION
    assert policy['origin'] == {'scheme': 'https',
                                'hostname': ORIGIN_HOSTNAME, 'port': 443}
    assert policy['ca_bundle'] == {'path': '/opt/pal-synthetic/relay-ca.pem',
                                   'sha256': SYNTHETIC_CA['sha256'],
                                   'size_bytes': SYNTHETIC_CA['size']}
    assert policy['permitted_address_rule'] == 'qualification-loopback-only'
    assert policy['tls_floor'] == 'tls12'
    assert policy['endpoint_binding'] == 'per-call-numeric-loopback-http'
    assert policy['limits']['total_timeout_ms'] is None
    assert policy['preflight'] == []
    assert len(policy['requests']) == 1
    entry = policy['requests'][0]
    assert entry['method'] == 'POST' and entry['target'] == '/v1/messages'
    assert entry['query'] == 'beta=true'
    assert {rule['name'] for rule in entry['forwarded_headers']} == {
        'host', 'x-api-key', 'content-type', 'accept', 'accept-encoding',
        'anthropic-version', 'anthropic-beta'}
    # Digest sensitivity: every reviewed decision field changes the input.
    variants = [
        _trust(origin_hostname='api.anthropic.com'),
        _trust(origin_port=8443),
        _trust(ca_bundle=relay.RelayCaBundlePin(
            '/opt/pal-synthetic/other-ca.pem', 'b' * 64, 4096)),
        _trust(permitted_address_rule='public-global-unicast-only'),
        _trust(max_relay_request_bytes=15_999_999),
        _trust(total_timeout_ms=60000),
    ]
    for variant in variants:
        assert variant.policy_dict() != policy
    # No ephemeral port, descriptor number, credential or PID anywhere.
    encoded = json.dumps(policy)
    assert 'port": 443' in encoded  # origin port is reviewed config, not drawn
    assert 'fd' not in encoded and 'credential' not in encoded.lower()
    assert _trust().policy_dict() == _trust().policy_dict()


def test_default_forwarded_header_order_is_hash_seed_stable():
    # Binding W5-review finding: the default forwarded-header tuple order is
    # policy-dict digest input, so iterating the FORWARDED_HEADER_NAMES
    # frozenset directly would make trust digests vary per process under hash
    # randomization. Prove canonical order in-process and byte equality of the
    # full digest input across exec'd hash seeds (the module is standalone
    # stdlib-only, so it loads by file path without the package).
    names = [rule.name for rule in relay.RelayRequestEntry().forwarded_headers]
    assert names == sorted(relay.FORWARDED_HEADER_NAMES)
    snippet = (
        'import importlib.util, json, sys\n'
        'spec = importlib.util.spec_from_file_location("relay_seed_probe",'
        ' sys.argv[1])\n'
        'module = importlib.util.module_from_spec(spec)\n'
        'sys.modules["relay_seed_probe"] = module\n'
        'spec.loader.exec_module(module)\n'
        'pin = module.RelayCaBundlePin("/opt/pal-synthetic/relay-ca.pem",'
        ' "%s", %d)\n'
        'print(json.dumps(module.RelayTrustConfig(ca_bundle=pin).policy_dict(),'
        ' sort_keys=True))\n'
    ) % (SYNTHETIC_CA['sha256'], SYNTHETIC_CA['size'])
    outputs = set()
    for seed in ('0', '1', '424242'):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith('PYTEST')}
        env['PYTHONHASHSEED'] = seed
        env['PYTHONUTF8'] = '1'
        completed = subprocess.run(
            [sys.executable, '-c', snippet, str(Path(relay.__file__).resolve())],
            capture_output=True, env=env, timeout=120, text=True)
        assert completed.returncode == 0, completed.stderr
        outputs.add(completed.stdout)
    in_process = json.dumps(relay.RelayTrustConfig(
        ca_bundle=relay.RelayCaBundlePin('/opt/pal-synthetic/relay-ca.pem',
                                         SYNTHETIC_CA['sha256'],
                                         SYNTHETIC_CA['size'])).policy_dict(),
        sort_keys=True)
    assert outputs == {in_process + '\n'}


# ---------------------------------------------------------------------------
# Static engine-source tests
# ---------------------------------------------------------------------------

def test_engine_source_is_stdlib_only():
    tree = ast.parse(relay.ENGINE_SOURCE)
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.Import) for alias in node.names}
    assert imported <= {'hashlib', 'ipaddress', 'json', 'os', 'select',
                        'socket', 'ssl', 'sys', 'time'}
    for forbidden in ('polymarket_alpha_lab', 'psycopg', 'subprocess',
                      'threading'):
        assert forbidden not in relay.ENGINE_SOURCE
    # Comment lines document the prohibitions; the CODE must never call them.
    code_only = '\n'.join(line for line in relay.ENGINE_SOURCE.splitlines()
                          if not line.lstrip().startswith('#'))
    for forbidden in ('create_default_context(', 'load_default_certs(',
                      'ssl._create_unverified_context', 'check_hostname = False',
                      'verify_mode = ssl.CERT_NONE'):
        assert forbidden not in code_only, forbidden


def test_engine_source_pins_protocol_tls_floor_and_pinned_ca_loading():
    source = relay.ENGINE_SOURCE
    assert "PROTOCOL_VERSION = 'research-linux-relay-v1'" in source
    assert 'ssl.PROTOCOL_TLS_CLIENT' in source
    assert 'ssl.TLSVersion.TLSv1_2' in source
    assert 'context.check_hostname = True' in source
    assert 'context.verify_mode = ssl.CERT_REQUIRED' in source
    assert "'/proc/self/fd/%d' % ca_fd" in source
    # Exactly ONE upstream socket creation site and no proxy semantics in
    # CODE (the header comment states the prohibitions).
    assert source.count('socket.socket(') == 1
    code_only = '\n'.join(line for line in source.splitlines()
                          if not line.lstrip().startswith('#'))
    for forbidden in ("b'CONNECT'", "'CONNECT'", 'socks', 'SOCKS', 'proxy',
                      'Proxy', 'http_tunnel', 'connect_ex('):
        assert forbidden not in code_only, forbidden
    # The inner-hop framing refusals and redirect refusal are pinned.
    assert 'relay_refused_framing' in source
    assert 'relay_redirect_refused' in source
    assert 'relay_preflight_not_approved' in source
    assert 'relay_request_bytes_exceeded' in source
    assert 'relay_response_bytes_exceeded' in source


# ---------------------------------------------------------------------------
# Exec'd engine pure-function units (no I/O)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def engine_namespace():
    namespace = {}
    exec(compile(relay.ENGINE_SOURCE, '<engine-source>', 'exec'), namespace)
    return namespace


def _engine_config(engine_namespace, trust=None):
    code, config = engine_namespace['_validate_trust'](trust or _trust().policy_dict())
    assert code is None and config is not None
    return config


def test_engine_address_permitted_matrix(engine_namespace):
    permitted = engine_namespace['_address_permitted']
    default = 'public-global-unicast-only'
    for text in ('127.0.0.1', '127.8.8.8', '10.0.0.1', '192.168.0.1',
                 '172.16.0.1', '169.254.169.254', '224.0.0.1', '0.0.0.0',
                 '::1', 'fe80::1', '::ffff:127.0.0.1', '::ffff:8.8.8.8',
                 'ff02::1', 'not-an-address'):
        assert permitted(default, text) is False, text
    # Public global unicast PASSES the filter (pure function: no connection).
    for text in ('8.8.8.8', '2606:4700::1111'):
        assert permitted(default, text) is True, text
    qualification = 'qualification-loopback-only'
    assert permitted(qualification, '127.0.0.1') is True
    assert permitted(qualification, '127.200.3.4') is True
    for text in ('::1', '10.0.0.1', '8.8.8.8', '169.254.0.1'):
        assert permitted(qualification, text) is False, text


def test_engine_trust_validation_refusals(engine_namespace):
    validate = engine_namespace['_validate_trust']
    base = _trust().policy_dict()
    code, config = validate(base)
    assert code is None and config['hostname'] == ORIGIN_HOSTNAME
    # preflight declared -> its own refusal code, before any request
    declared = dict(base)
    declared['preflight'] = base['requests']
    assert validate(declared) == ('relay_preflight_not_approved', None)
    # closed field refusals
    for mutation in (
            {'protocol_version': 'research-linux-relay-v2'},
            {'origin': {'scheme': 'http', 'hostname': ORIGIN_HOSTNAME,
                        'port': 443}},
            {'origin': {'scheme': 'https', 'hostname': 'Upper.host',
                        'port': 443}},
            {'origin': {'scheme': 'https', 'hostname': ORIGIN_HOSTNAME,
                        'port': 0}},
            {'permitted_address_rule': 'any'},
            {'tls_floor': 'tls13'},
            {'endpoint_binding': 'static-https'},
            {'requests': []},
            {'requests': [dict(base['requests'][0], method='GET')]},
    ):
        broken = json.loads(json.dumps(base))
        broken.update(mutation)
        assert validate(broken) == ('relay_config_invalid', None), mutation
    limits_break = json.loads(json.dumps(base))
    limits_break['limits']['max_relay_request_bytes'] = 16000001
    assert validate(limits_break) == ('relay_config_invalid', None)


def _run_validate(engine_namespace, head_lines, cursor=0, bound='127.0.0.1:21222',
                  trust=None, raw_head=None):
    head = raw_head if raw_head is not None else b'\r\n'.join(head_lines)
    split = engine_namespace['_split_head'](head)
    if split is None:
        return 'relay_refused_framing', None, None
    line, entries = split
    config = _engine_config(engine_namespace, trust)
    code, validated = engine_namespace['_validate_request'](
        config, line, entries, cursor, bound)
    return code, validated, line


def test_engine_validate_request_order_and_codes(engine_namespace):
    body = b'{}'
    good = [b'POST /v1/messages?beta=true HTTP/1.1', b'Host: 127.0.0.1:21222',
            b'x-api-key: k', b'content-type: application/json',
            b'accept: application/json', b'accept-encoding: gzip',
            b'anthropic-version: 2023-06-01',
            b'anthropic-beta: oauth-2025-04-20', b'Content-Length: 2']
    # approved
    code, validated, _ = _run_validate(engine_namespace, good)
    assert code is None and validated['body_length'] == 2
    # framing-first: a non-digit CL wins over an unknown header
    code, _, _ = _run_validate(engine_namespace, [
        b'POST /v1/messages?beta=true HTTP/1.1', b'Host: 127.0.0.1:21222',
        b'x-evil: 1', b'Content-Length: abc'])
    assert code == 'relay_refused_framing'
    # authority: missing, duplicated and mismatched Host
    for head in (good[:1] + good[2:], good + [b'Host: 127.0.0.1:9'],
                 [b'POST /v1/messages?beta=true HTTP/1.1',
                  b'Host: evil.invalid', b'Content-Length: 2']):
        code, _, _ = _run_validate(engine_namespace, head)
        assert code == 'relay_refused_authority', head
    code, _, _ = _run_validate(engine_namespace, good + [b'Host: again'])
    assert code == 'relay_refused_authority'
    # method / target literals, unnormalized
    for line, expected in (
            (b'get /v1/messages?beta=true HTTP/1.1', 'relay_refused_method'),
            (b'POST /v1%2Fmessages?beta=true HTTP/1.1', 'relay_refused_target'),
            (b'POST /V1/messages?beta=true HTTP/1.1', 'relay_refused_target'),
            (b'POST //v1/messages?beta=true HTTP/1.1', 'relay_refused_target'),
            (b'POST /v1/messages?true=beta HTTP/1.1', 'relay_refused_target'),
            (b'POST /v1/messages?beta=true&x=1 HTTP/1.1', 'relay_refused_target'),
            (b'POST /v1/messages HTTP/1.1', 'relay_refused_target'),
            (b'POST https://host/v1/messages?beta=true HTTP/1.1',
             'relay_refused_target')):
        head = [line, b'Host: 127.0.0.1:21222', b'Content-Length: 2']
        code, _, _ = _run_validate(engine_namespace, head)
        assert code == expected, line
    # lowercase method is NOT folded to POST
    head = [b'post /v1/messages?beta=true HTTP/1.1', b'Host: 127.0.0.1:21222',
            b'Content-Length: 2']
    code, _, _ = _run_validate(engine_namespace, head)
    assert code == 'relay_refused_method'
    # header allowlist: unknown, duplicate, missing required
    for extra, expected in ((b'x-unknown: 1', 'relay_refused_header'),
                            (b'x-api-key: 2', 'relay_refused_header')):
        head = [b'POST /v1/messages?beta=true HTTP/1.1',
                b'Host: 127.0.0.1:21222', b'x-api-key: k', extra,
                b'Content-Length: 2']
        code, _, _ = _run_validate(engine_namespace, head)
        assert code == expected, extra
    head = [b'POST /v1/messages?beta=true HTTP/1.1', b'Host: 127.0.0.1:21222',
            b'accept: */*', b'Content-Length: 2']  # x-api-key missing
    code, _, _ = _run_validate(engine_namespace, head)
    assert code == 'relay_refused_header'
    # chunked TE refused at the inner hop; HTTP/1.0 and 2-part lines refused
    for head in ([b'POST /v1/messages?beta=true HTTP/1.1',
                  b'Host: 127.0.0.1:21222',
                  b'Transfer-Encoding: chunked'],
                 [b'POST /v1/messages?beta=true HTTP/1.0',
                  b'Host: 127.0.0.1:21222', b'Content-Length: 2'],
                 [b'POST/v1/messages?beta=true',
                  b'Host: 127.0.0.1:21222', b'Content-Length: 2']):
        code, _, _ = _run_validate(engine_namespace, head)
        assert code == 'relay_refused_framing', head
    # duplicate Content-Length refused as framing
    code, _, _ = _run_validate(engine_namespace, good + [b'Content-Length: 2'])
    assert code == 'relay_refused_framing'


def test_engine_validate_request_cardinality(engine_namespace):
    full = [b'Host: 127.0.0.1:21222', b'x-api-key: k',
            b'content-type: application/json', b'accept: application/json',
            b'accept-encoding: gzip', b'anthropic-version: 2023-06-01',
            b'anthropic-beta: oauth-2025-04-20', b'Content-Length: 2']
    first = relay.RelayRequestEntry().entry_dict()
    second = relay.RelayRequestEntry(target='/v1/messages', query='v2').entry_dict()
    two = json.loads(json.dumps(_trust().policy_dict()))
    two['requests'] = [first, second]
    # second approved literal sent FIRST -> out of order
    head = [b'POST /v1/messages?v2 HTTP/1.1'] + full
    code, _, _ = _run_validate(engine_namespace, head, cursor=0, trust=two)
    assert code == 'relay_refused_cardinality'
    # in-order second entry accepted
    code, validated, _ = _run_validate(engine_namespace, head, cursor=1, trust=two)
    assert code is None and validated['entry']['query'] == 'v2'
    # cursor exhausted -> cardinality
    single = _trust().policy_dict()
    code, _, _ = _run_validate(engine_namespace, [
        b'POST /v1/messages?beta=true HTTP/1.1', b'Host: 127.0.0.1:21222',
        b'Content-Length: 2'], cursor=1, trust=single)
    assert code == 'relay_refused_cardinality'


def test_engine_split_head_strict_crlf(engine_namespace):
    split = engine_namespace['_split_head']
    assert split(b'POST / HTTP/1.1\r\nHost: h') == (b'POST / HTTP/1.1',
                                                    [(b'host', b'h', b'Host: h')])
    assert split(b'POST / HTTP/1.1\nHost: h') is None          # bare LF
    assert split(b'POST / HTTP/1.1\r\nnocolon') is None         # no colon
    assert split(b'POST / HTTP/1.1\r\n: v') is None             # empty name
    assert split(b'POST / HTTP/1.1\r\nBad Name: v') is None     # space in name
    entries = split(b'GET / HTTP/1.1\r\nX-Api-Key:  v')[1]
    assert entries[0][0] == b'x-api-key' and entries[0][1] == b'v'
    assert entries[0][2] == b'X-Api-Key:  v'                     # raw verbatim


def test_engine_reconstruct_uses_only_the_approved_origin(engine_namespace):
    config = _engine_config(engine_namespace)
    validated = {'entry': config['requests'][0],
                 'entries': [(b'host', b'127.0.0.1:21222', b'Host: 127.0.0.1:21222'),
                             (b'x-api-key', KEY_SENTINEL, b'x-api-key: ' + KEY_SENTINEL),
                             (b'content-length', b'7', b'Content-Length: 7')],
                 'body_length': 7}
    rebuilt = engine_namespace['_reconstruct'](config, validated, b'payload')
    lines = rebuilt.split(b'\r\n')
    assert lines[0] == b'POST /v1/messages?beta=true HTTP/1.1'
    assert lines[1] == b'Host: ' + ORIGIN_HOSTNAME.encode('ascii')
    assert b'x-api-key: ' + KEY_SENTINEL in lines            # verbatim
    assert b'Content-Length: 7' in lines                      # measured body
    assert rebuilt.endswith(b'\r\n\r\npayload')
    assert b'127.0.0.1' not in rebuilt                        # guest authority gone
    # non-default origin port reconstructs host:port from the origin triple
    ported = _engine_config(engine_namespace, _trust(origin_port=8443).policy_dict())
    rebuilt2 = engine_namespace['_reconstruct'](ported, validated, b'payload')
    assert b'Host: %s:8443\r\n' % ORIGIN_HOSTNAME.encode('ascii') in rebuilt2


# ---------------------------------------------------------------------------
# Subprocess harness: driver, readers, fake upstreams, engine runner
# ---------------------------------------------------------------------------

DRIVER_SOURCE = '''\
# Test-only child bootstrap: installs the inherited channel descriptors
# (fd numbers on POSIX, inherited handle values on Windows), optionally
# stubs socket.getaddrinfo from PAL_TEST_DNS (resolution-injection harness;
# the stub is installed OUTSIDE the pristine engine source), builds the CONF
# line the engine reads on stdin, then executes the byte-exact ENGINE_SOURCE
# with __main__ semantics. Only channel PLUMBING differs per host; every
# engine byte path is production code.
import io
import json
import os
import sys

engine_path = sys.argv[1]
fds = {}
for spec in sys.argv[2:]:
    name, _, value = spec.partition('=')
    if os.name == 'nt':
        import msvcrt
        fds[name] = msvcrt.open_osfhandle(int(value, 16), os.O_BINARY | os.O_RDWR)
    else:
        fds[name] = int(value)

conf = json.loads(bytes.fromhex(os.environ['PAL_TEST_CONF_HEX']).decode('ascii'))
conf['relay_read_fd'] = fds['chan_r']
conf['relay_write_fd'] = fds['chan_w']
conf['control_fd'] = fds['control']
conf['report_fd'] = fds['report']
conf['liveness_fd'] = fds['liveness']
conf['ca_fd'] = fds['ca']

dns_table = os.environ.get('PAL_TEST_DNS')
stub_calls = []
if dns_table is not None:
    import socket as socket_module
    table = json.loads(dns_table)

    def fake_getaddrinfo(host, port, *args, **kwargs):
        stub_calls.append([host, port])
        return [(int(family), socket_module.SOCK_STREAM, 6, '', (address, port))
                for family, address in table['results']]

    socket_module.getaddrinfo = fake_getaddrinfo

line = (b'CONF ' + json.dumps(conf, separators=(',', ':')).encode('utf-8')
        ).hex().encode('ascii') + b'\\n'
sys.stdin = io.TextIOWrapper(io.BytesIO(line), encoding='ascii')

with open(engine_path, 'rb') as handle:
    source = handle.read()
code = compile(source, engine_path, 'exec')
namespace = {'__name__': '__main__'}
try:
    exec(code, namespace)
except SystemExit:
    if dns_table is not None:
        sys.stderr.write('DNSCALLS ' + json.dumps(stub_calls) + '\\n')
        sys.stderr.flush()
    raise
'''


class _LineReader(threading.Thread):
    """Drains a report pipe into parsed JSON lines (blocking-thread reader)."""

    def __init__(self, fd):
        super().__init__(daemon=True)
        self.fd = fd
        self.lines = queue.Queue()
        self.raw = bytearray()
        self.error = None

    def run(self):
        buffer = bytearray()
        try:
            while True:
                block = os.read(self.fd, 4096)
                if not block:
                    break
                self.raw.extend(block)
                buffer.extend(block)
                while b'\n' in buffer:
                    line, _, rest = bytes(buffer).partition(b'\n')
                    self.lines.put(line)
                    buffer = bytearray(rest)
        except OSError as failure:
            self.error = failure


class _ChunkReader(threading.Thread):
    """Drains the engine->guest response pipe into byte chunks."""

    def __init__(self, fd):
        super().__init__(daemon=True)
        self.fd = fd
        self.chunks = queue.Queue()
        self.total = 0

    def run(self):
        try:
            while True:
                block = os.read(self.fd, 65536)
                if not block:
                    break
                self.total += len(block)
                self.chunks.put(block)
        except OSError:
            pass
        self.chunks.put(None)

    def read_exact(self, count, timeout):
        out = bytearray()
        deadline = time.monotonic() + timeout
        while len(out) < count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                pytest.fail('response timeout: wanted %d bytes, got %d'
                            % (count, len(out)))
            try:
                block = self.chunks.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue
            if block is None:
                pytest.fail('response EOF: wanted %d bytes, got %d'
                            % (count, len(out)))
            out.extend(block)
        return bytes(out)

    def read_for(self, seconds):
        out = bytearray()
        deadline = time.monotonic() + seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                block = self.chunks.get(timeout=remaining)
            except queue.Empty:
                break
            if block is None:
                break
            out.extend(block)
        return bytes(out)


def read_request_upstream(stream, record, timeout=8.0):
    """Fake-upstream helper: read one full request (head + exact CL body)."""
    stream.settimeout(timeout)
    data = bytearray()
    while True:
        if b'\r\n\r\n' in data:
            head, _, rest = bytes(data).partition(b'\r\n\r\n')
            length = 0
            for line in head.split(b'\r\n')[1:]:
                name, _, value = line.partition(b':')
                if name.strip().lower() == b'content-length':
                    length = int(value.strip())
            if len(rest) >= length:
                break
        block = stream.recv(65536)
        if not block:
            break
        data.extend(block)
    record['received'].extend(data)
    return bytes(data)


def ok_handler(body=RESPONSE_SENTINEL, status=b'200 OK',
               headers=(), after=b'', delay=0.0):
    def handler(stream, record):
        read_request_upstream(stream, record)
        if delay:
            time.sleep(delay)
        head = (b'HTTP/1.1 ' + status + b'\r\nContent-Length: '
                + str(len(body)).encode('ascii') + b'\r\n')
        for header in headers:
            head += header + b'\r\n'
        stream.sendall(head + b'\r\n' + body)
        if after:
            stream.sendall(after)
    return handler


def redirect_handler(location=b'https://elsewhere.invalid/v1/messages'):
    def handler(stream, record):
        read_request_upstream(stream, record)
        stream.sendall(b'HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\n'
                       b'Location: ' + location + b'\r\n\r\n')
    return handler


def stall_handler(read_first=True, seconds=6.0):
    def handler(stream, record):
        if read_first:
            read_request_upstream(stream, record)
        time.sleep(seconds)
    return handler


def zero_response_handler():
    def handler(stream, record):
        read_request_upstream(stream, record)
        stream.shutdown(socket.SHUT_RDWR)
    return handler


def partial_response_handler():
    def handler(stream, record):
        read_request_upstream(stream, record)
        head = b'HTTP/1.1 200 OK\r\nContent-Length: 1000\r\n\r\n'
        stream.sendall(head + b'P' * 300)   # complete head, partial body
        time.sleep(6.0)
    return handler


def chunked_handler(chunks=(b'hello ', b'world'), truncated=False):
    def handler(stream, record):
        read_request_upstream(stream, record)
        head = b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
        body = b''
        for chunk in chunks:
            body += (hex(len(chunk))[2:].encode('ascii') + b'\r\n' + chunk
                     + b'\r\n')
        if truncated:
            body += b'64\r\n' + b'x' * 10
        else:
            body += b'0\r\n\r\n'
        stream.sendall(head + body)
    return handler


def close_delimited_handler(body=b'plain-body-until-close'):
    def handler(stream, record):
        read_request_upstream(stream, record)
        stream.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n'
                       + body)
        stream.shutdown(socket.SHUT_RDWR)
    return handler


def oversized_handler(declared=8192, send=8192):
    def handler(stream, record):
        read_request_upstream(stream, record)
        head = (b'HTTP/1.1 200 OK\r\nContent-Length: '
                + str(declared).encode('ascii') + b'\r\n\r\n')
        stream.sendall(head + b'R' * send)
    return handler


class FakeUpstream:
    """Local loopback fake upstream. TLS mode serves a synthetic self-signed
    certificate (records the client SNI); raw mode is a plain socket used to
    prove nothing guest-controlled ever crosses without TLS."""

    def __init__(self, handler, cert_path=None, key_path=None):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(('127.0.0.1', 0))
        self.listener.listen(8)
        self.port = self.listener.getsockname()[1]
        self.handler = handler
        self.cert_path = cert_path
        self.key_path = key_path
        self.tls = cert_path is not None
        self.connections = []
        self.sni_names = []
        self._lock = threading.Lock()
        self._closed = threading.Event()
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while not self._closed.is_set():
            try:
                conn, _peer = self.listener.accept()
            except OSError:
                break
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn):
        record = {'peer': conn.getpeername(), 'received': bytearray(),
                  'sni': None}
        with self._lock:
            self.connections.append(record)
        stream = conn
        try:
            if self.tls:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(self.cert_path, self.key_path)

                def sni_callback(sock, server_name, sslcontext):
                    with self._lock:
                        self.sni_names.append(server_name)

                context.sni_callback = sni_callback
                conn.settimeout(8.0)
                stream = context.wrap_socket(conn, server_side=True)
            else:
                conn.settimeout(8.0)
            self.handler(stream, record)
        except (OSError, ssl.SSLError, ValueError):
            pass
        finally:
            for handle in (stream, conn):
                try:
                    handle.close()
                except Exception:
                    pass

    def requests(self):
        with self._lock:
            return list(self.connections)

    def close(self):
        self._closed.set()
        try:
            self.listener.close()
        except OSError:
            pass


@pytest.fixture(scope='module')
def cert_material(tmp_path_factory):
    """Synthetic self-signed test identities generated at test time."""
    if OPENSSL is None:
        return None
    directory = tmp_path_factory.mktemp('relay-certs')
    material = {}
    for hostname in (ORIGIN_HOSTNAME, MISMATCH_HOSTNAME, UNRELATED_HOSTNAME):
        base = directory / hostname
        key, cert = str(base) + '.key', str(base) + '.pem'
        subprocess.run([OPENSSL, 'req', '-x509', '-newkey', 'rsa:2048',
                        '-nodes', '-keyout', key, '-out', cert, '-days', '2',
                        '-subj', '/CN=' + hostname,
                        '-addext', 'subjectAltName=DNS:' + hostname],
                       capture_output=True, timeout=180, check=True)
        payload = Path(cert).read_bytes()
        material[hostname] = {'cert': cert, 'key': key, 'pem': payload,
                              'sha256': sha256(payload).hexdigest(),
                              'size': len(payload)}
    return material


def require_certs(material):
    if material is None:
        pytest.skip('openssl unavailable: TLS fake-upstream cases are '
                    'environment-limited (explicit skip, not silent)')


class EngineRun:
    """Drives the pristine ENGINE_SOURCE as a real subprocess over harness
    pipes (channel halves, control, report, liveness, sealed CA)."""

    def __init__(self, directory, trust, ca_bytes, *, bound_port=None,
                 total_ms=15000, dns=None):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'engine.py').write_text(relay.ENGINE_SOURCE,
                                             encoding='ascii')
        (directory / 'driver.py').write_text(DRIVER_SOURCE, encoding='ascii')
        names = ('chan_in', 'chan_out', 'control', 'report', 'liveness', 'ca')
        pairs = {name: os.pipe() for name in names}
        self.guest_w = pairs['chan_in'][1]
        self.control_w = pairs['control'][1]
        self.liveness_w = pairs['liveness'][1]
        self.response_reader = _ChunkReader(pairs['chan_out'][0])
        self.report_reader = _LineReader(pairs['report'][0])
        child_fds = {'chan_r': pairs['chan_in'][0],
                     'chan_w': pairs['chan_out'][1],
                     'control': pairs['control'][0],
                     'report': pairs['report'][1],
                     'liveness': pairs['liveness'][0],
                     'ca': pairs['ca'][0]}
        conf = {'protocol_version': relay.RELAY_PROTOCOL_VERSION,
                'trust': trust,
                'bound_authority': '%s:%d' % (
                    relay.RELAY_LOOPBACK_BIND_ADDRESS,
                    bound_port if bound_port is not None
                    else relay.draw_relay_port()),
                'total_timeout_ms': total_ms}
        env = {'PAL_TEST_CONF_HEX': json.dumps(
            conf, separators=(',', ':')).encode('utf-8').hex()}
        if dns is not None:
            env['PAL_TEST_DNS'] = json.dumps(dns)
        if os.name == 'nt':
            env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', '')
        argv = [sys.executable, str(directory / 'driver.py'),
                str(directory / 'engine.py')]
        pass_fds = []
        for name in ('chan_r', 'chan_w', 'control', 'report', 'liveness', 'ca'):
            fd = child_fds[name]
            if os.name == 'nt':
                os.set_inheritable(fd, True)
                argv.append('%s=%s' % (name, hex(msvcrt.get_osfhandle(fd))))
            else:
                argv.append('%s=%d' % (name, fd))
                pass_fds.append(fd)
        os.write(pairs['ca'][1], ca_bytes)
        os.close(pairs['ca'][1])
        if os.name == 'nt':
            self.proc = subprocess.Popen(argv, env=env, close_fds=False,
                                         stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        else:
            self.proc = subprocess.Popen(argv, env=env, pass_fds=pass_fds,
                                         stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        for fd in child_fds.values():
            os.close(fd)
        self.response_reader.start()
        self.report_reader.start()
        self._stderr = None

    def next_report(self, timeout=20.0):
        try:
            line = self.report_reader.lines.get(timeout=timeout)
        except queue.Empty:
            pytest.fail('engine report timeout after %ss' % timeout)
        return json.loads(line.decode('utf-8'))

    def wait_started(self, timeout=20.0):
        event = self.next_report(timeout)
        assert event['type'] == 'started', event
        assert event['protocol_version'] == relay.RELAY_PROTOCOL_VERSION
        return event

    def call_done(self, timeout=20.0):
        event = self.next_report(timeout)
        assert event['type'] == 'call_done', event
        return event

    def engine_done(self, timeout=20.0):
        while True:
            event = self.next_report(timeout)
            assert event['type'] in ('call_done', 'engine_done'), event
            if event['type'] == 'engine_done':
                return event

    def send_guest(self, data):
        os.write(self.guest_w, data)

    def close_guest(self):
        if self.guest_w is not None:
            os.close(self.guest_w)
            self.guest_w = None

    def stop(self):
        os.write(self.control_w, b'STOP\n')

    def close_liveness(self):
        os.close(self.liveness_w)
        self.liveness_w = None

    def wait_exit(self, timeout=20.0):
        code = self.proc.wait(timeout=timeout)
        try:
            self._stderr = self.proc.stderr.read().decode('utf-8', 'replace')
        except OSError:
            self._stderr = ''
        return code

    def dns_calls(self):
        assert self._stderr is not None, 'call wait_exit() first'
        for line in self._stderr.splitlines():
            if line.startswith('DNSCALLS '):
                return json.loads(line[len('DNSCALLS '):])
        return None

    def close(self):
        self.close_guest()
        for name in ('control_w', 'liveness_w'):
            fd = getattr(self, name, None)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
                setattr(self, name, None)
        if self.proc.poll() is None:
            try:
                self.proc.kill()
            except OSError:
                pass
        for reader in (self.response_reader, self.report_reader):
            try:
                os.close(reader.fd)
            except OSError:
                pass
            reader.join(timeout=5)


def approved_head(bound_authority, *, key=KEY_SENTINEL, key_name=b'x-api-key',
                  body=64):
    """The approved guest request head for the bound loopback authority."""
    base = b'{"prompt":"' + PROMPT_SENTINEL + b'","n":1}'
    payload = base[:body].ljust(body, b'}')
    head = b''.join([
        b'POST /v1/messages?beta=true HTTP/1.1\r\n',
        b'Host: ' + bound_authority.encode('ascii') + b'\r\n',
        key_name + b': ' + key + b'\r\n',
        b'anthropic-version: 2023-06-01\r\n',
        b'anthropic-beta: oauth-2025-04-20\r\n',
        b'content-type: application/json\r\n',
        b'accept: application/json\r\n',
        b'accept-encoding: gzip\r\n',
        b'Content-Length: ' + str(len(payload)).encode('ascii') + b'\r\n\r\n'])
    return head + payload


DEFAULT_RESPONSE = (b'HTTP/1.1 200 OK\r\nContent-Length: '
                    + str(len(RESPONSE_SENTINEL)).encode('ascii')
                    + b'\r\n\r\n' + RESPONSE_SENTINEL)


# ---------------------------------------------------------------------------
# Subprocess matrix
# ---------------------------------------------------------------------------

def test_engine_approved_round_trip_and_reconstruction(tmp_path, cert_material):
    """Happy path through a REAL subprocess and a TLS fake upstream: the
    upstream-visible request is reconstructed from the approved origin only,
    the credential header forwards verbatim, the response returns unmodified,
    exactly one resolution and one connection happen, and teardown is clean."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=5000,
                       connect_timeout_ms=6000, handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            request = approved_head('127.0.0.1:%d' % bound_port)
            run.send_guest(request)
            response = run.response_reader.read_exact(len(DEFAULT_RESPONSE), 10)
            assert response == DEFAULT_RESPONSE
            done = run.call_done()
            assert done['code'] == 'relay_ok'
            counters = done['counters']
            assert counters['requests_observed'] == 1
            assert counters['requests_refused'] == 0
            assert counters['dns_resolutions'] == 1
            assert counters['upstream_connections'] == 1
            assert counters['guest_bytes_in'] == len(request)
            assert counters['guest_bytes_out'] == len(DEFAULT_RESPONSE)
            assert counters['teardown_failures'] == 0
            run.close_guest()
            assert run.engine_done()['code'] == 'relay_ok'
            assert run.wait_exit() == 0
            assert run.dns_calls() == [[ORIGIN_HOSTNAME, upstream.port]]
        finally:
            run.close()
        connections = upstream.requests()
        assert len(connections) == 1
        seen = bytes(connections[0]['received'])
        assert seen.startswith(b'POST /v1/messages?beta=true HTTP/1.1\r\n')
        authority = (b'Host: ' + ORIGIN_HOSTNAME.encode('ascii')
                     + b':%d\r\n' % upstream.port)
        assert authority in seen                       # reconstructed origin
        assert b'127.0.0.1:' not in seen               # guest authority never copied
        assert b'\r\nx-api-key: ' + KEY_SENTINEL + b'\r\n' in seen
        assert b'\r\nanthropic-version: 2023-06-01\r\n' in seen
        body = seen[seen.index(b'\r\n\r\n') + 4:]
        assert PROMPT_SENTINEL in body
        assert seen.count(b'Content-Length:') == 1
        assert upstream.sni_names == [ORIGIN_HOSTNAME]  # SNI from config
        assert connections[0]['peer'][0] == '127.0.0.1'  # by resolved address
        # Evidence hygiene: no sentinel ever reaches a report byte.
        reports = bytes(run.report_reader.raw)
        for sentinel in (KEY_SENTINEL, PROMPT_SENTINEL, RESPONSE_SENTINEL):
            assert sentinel not in reports
    finally:
        upstream.close()


def test_engine_header_name_case_matches_and_forwards_verbatim(
        tmp_path, cert_material):
    """HTTP header NAMES match case-insensitively while the raw guest
    spelling and value forward verbatim."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            request = approved_head('127.0.0.1:%d' % bound_port,
                                    key_name=b'X-Api-Key')
            run.send_guest(request)
            run.response_reader.read_exact(len(DEFAULT_RESPONSE), 10)
            done = run.call_done()
            assert done['code'] == 'relay_ok'
            run.close_guest()
            assert run.engine_done()['code'] == 'relay_ok'
            run.wait_exit()
        finally:
            run.close()
        seen = bytes(upstream.requests()[0]['received'])
        assert b'\r\nX-Api-Key: ' + KEY_SENTINEL + b'\r\n' in seen
    finally:
        upstream.close()


@pytest.mark.parametrize('request_line', [
    b'GET /v1/messages?beta=true HTTP/1.1',
    b'post /v1/messages?beta=true HTTP/1.1',
    b'PUT /v1/messages?beta=true HTTP/1.1',
])
def test_engine_refuses_wrong_method(tmp_path, request_line):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        body = b'{}'
        run.send_guest(request_line + b'\r\nHost: 127.0.0.1:%d\r\n'
                       b'x-api-key: k\r\nContent-Length: 2\r\n\r\n' % bound_port
                       + body)
        done = run.call_done()
        assert done['code'] == 'relay_refused_method'
        assert done['counters']['upstream_connections'] == 0
        assert done['counters']['dns_resolutions'] == 0
        run.stop()
        assert run.engine_done()['code'] == 'relay_stopped'
        run.wait_exit()
    finally:
        run.close()


@pytest.mark.parametrize('target', [
    b'/v1%2Fmessages?beta=true',      # percent-encoded path
    b'/V1/Messages?beta=true',       # case folding attempt
    b'//v1/messages?beta=true',      # path normalization attempt
    b'/v1/messages',                 # missing query
    b'/v1/messages?beta=true&x=1',   # extra parameter
    b'/v1/messages?true=beta',       # reordered query
    b'/v1/./messages?beta=true',     # dot segment
    b'https://pal-relay-origin.invalid/v1/messages?beta=true',  # absolute-form
])
def test_engine_refuses_wrong_target_unnormalized(tmp_path, target):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST ' + target + b' HTTP/1.1\r\nHost: 127.0.0.1:%d'
                       b'\r\nx-api-key: k\r\nContent-Length: 2\r\n\r\n{}'
                       % bound_port)
        done = run.call_done()
        assert done['code'] == 'relay_refused_target'
        assert done['counters']['upstream_connections'] == 0
        assert done['counters']['dns_resolutions'] == 0
        run.stop()
        assert run.engine_done()['code'] == 'relay_stopped'
        run.wait_exit()
    finally:
        run.close()


@pytest.mark.parametrize('host_line', [
    b'Host: 127.0.0.1:1',             # wrong port
    b'Host: evil.invalid',            # foreign authority
    b'Host: pal-relay-origin.invalid',
])
def test_engine_refuses_authority_override(tmp_path, host_line):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\r\n'
                       + host_line + b'\r\nx-api-key: k\r\n'
                       b'Content-Length: 2\r\n\r\n{}')
        done = run.call_done()
        assert done['code'] == 'relay_refused_authority'
        assert done['counters']['upstream_connections'] == 0
        run.stop()
        assert run.engine_done()['code'] == 'relay_stopped'
        run.wait_exit()
    finally:
        run.close()


def test_engine_refuses_missing_host(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\r\nx-api-key: k'
                       b'\r\nContent-Length: 2\r\n\r\n{}')
        assert run.call_done()['code'] == 'relay_refused_authority'
        run.stop()
        run.wait_exit()
    finally:
        run.close()


@pytest.mark.parametrize('extra_lines,expected', [
    ([b'x-unknown-header: 1'], 'relay_refused_header'),
    ([b'x-api-key: second'], 'relay_refused_header'),
    ([b'accept-encoding: ' + b'a' * 9000], 'relay_refused_header'),
    ([b'x-long: ' + b'a' * 9000], 'relay_refused_header'),
    ([(b'x-fill-%d: v' % index) for index in range(30)], 'relay_refused_header'),
])
def test_engine_refuses_header_violations(tmp_path, extra_lines, expected):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        head = [b'POST /v1/messages?beta=true HTTP/1.1',
                b'Host: 127.0.0.1:%d' % bound_port, b'x-api-key: k'] \
            + list(extra_lines) + [b'Content-Length: 2']
        run.send_guest(b'\r\n'.join(head) + b'\r\n\r\n{}')
        done = run.call_done()
        assert done['code'] == expected
        assert done['counters']['upstream_connections'] == 0
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_refuses_missing_required_header(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        head = (b'POST /v1/messages?beta=true HTTP/1.1\r\n'
                b'Host: 127.0.0.1:%d\r\naccept: */*\r\n'
                b'Content-Length: 2\r\n\r\n{}' % bound_port)  # no x-api-key
        run.send_guest(head)
        assert run.call_done()['code'] == 'relay_refused_header'
        run.stop()
        run.wait_exit()
    finally:
        run.close()


@pytest.mark.parametrize('cl_or_te,expected', [
    (b'Transfer-Encoding: chunked', 'relay_refused_framing'),
    (b'Content-Length: 12a', 'relay_refused_framing'),
    (b'Content-Length: 2\r\nContent-Length: 3', 'relay_refused_framing'),
])
def test_engine_refuses_framing_violations(tmp_path, cl_or_te, expected):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\r\n'
                       b'Host: 127.0.0.1:%d\r\nx-api-key: k\r\n%s\r\n\r\n{}'
                       % (bound_port, cl_or_te))
        done = run.call_done()
        assert done['code'] == expected
        assert done['counters']['upstream_connections'] == 0
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_refuses_old_http_and_bare_lf_head(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        # HTTP/1.0 with strict CRLF framing: parsed, then refused by version.
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.0\r\n'
                       b'Host: 127.0.0.1:%d\r\nx-api-key: k\r\n'
                       b'Content-Length: 2\r\n\r\n{}' % bound_port)
        assert run.call_done()['code'] == 'relay_refused_framing'
        run.stop()
        run.wait_exit()
    finally:
        run.close()
    # A bare-LF request never forms a CRLFCRLF-terminated head: no request is
    # ever observed and the idle deadline ends the engine (fail, no connect).
    run = EngineRun(tmp_path / 'engine2',
                    _trust(idle_timeout_ms=700).policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\n'
                       b'Host: 127.0.0.1:%d\nx-api-key: k\n'
                       b'Content-Length: 2\n\n{}' % bound_port)
        done = run.engine_done(timeout=15)
        assert done['code'] == 'relay_idle_timeout'
        assert done['counters']['requests_observed'] == 0
        assert done['counters']['upstream_connections'] == 0
        run.wait_exit()
    finally:
        run.close()


def test_engine_framing_checked_before_allowlist(tmp_path):
    """Framing-first order: a bad Content-Length wins over an unknown header."""
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\r\n'
                       b'Host: 127.0.0.1:%d\r\nx-evil: 1\r\n'
                       b'Content-Length: abc\r\n\r\n{}' % bound_port)
        assert run.call_done()['code'] == 'relay_refused_framing'
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_request_bytes_exceeded_fails_without_retry(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        request = approved_head('127.0.0.1:%d' % bound_port).replace(
            b'Content-Length: 64\r\n\r\n', b'Content-Length: 16000001\r\n\r\n')
        run.send_guest(request)
        done = run.call_done()
        assert done['code'] == 'relay_request_bytes_exceeded'
        assert done['counters']['upstream_connections'] == 0
        assert done['counters']['dns_resolutions'] == 0
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_head_cap_refused_as_framing(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        filler = b'x-fill: ' + b'a' * 4000 + b'\r\n'
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\r\n'
                       b'Host: 127.0.0.1:%d\r\n' % bound_port + filler * 17)
        assert run.call_done()['code'] == 'relay_refused_framing'
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_redirect_refused_and_never_followed(tmp_path, cert_material):
    """A 3xx is a terminal failure: Location is never read, no second
    connection is opened, and no redirect byte is released to the guest."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(redirect_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_redirect_refused'
            assert done['counters']['upstream_connections'] == 1
            assert done['counters']['guest_bytes_out'] == 0
            leaked = run.response_reader.read_for(1.0)
            assert leaked == b''
            run.stop()
            assert run.engine_done()['code'] == 'relay_stopped'
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1    # never followed, no resend
    finally:
        upstream.close()


def test_engine_immediate_upstream_close_single_attempt(tmp_path, cert_material):
    """A plain TCP upstream that closes at once: the engine attempts exactly
    one connection, the handshake fails with a fixed code, and no
    guest-controlled value ever crosses without TLS (only the ClientHello
    can be observed)."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    def handler(stream, record):
        record['received'].extend(stream.recv(65536))  # ClientHello only
    upstream = FakeUpstream(handler)
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, handshake_timeout_ms=5000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port,
                        dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_channel_failed'
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        connections = upstream.requests()
        assert len(connections) == 1
        for sentinel in (KEY_SENTINEL, PROMPT_SENTINEL):
            assert sentinel not in bytes(connections[0]['received'])
    finally:
        upstream.close()


def test_engine_zero_then_eof_upstream_recorded(tmp_path, cert_material):
    """Upstream completes the handshake then closes without one response
    byte: fixed failure code, zero response bytes out, exactly one attempt."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(zero_response_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_channel_failed'
            assert done['counters']['guest_bytes_out'] == 0
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_second_request_is_cardinality_failure(tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            run.response_reader.read_exact(len(DEFAULT_RESPONSE), 10)
            assert run.call_done()['code'] == 'relay_ok'
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_refused_cardinality'
            assert done['counters']['requests_observed'] == 2
            assert done['counters']['requests_refused'] == 1
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_out_of_order_request_is_cardinality_failure(tmp_path):
    """Harness-built two-entry request set (the parent-side record admits
    exactly one entry today; the engine enforces the ordered set): the second
    approved literal sent first is an out-of-order refusal with no connect."""
    bound_port = relay.draw_relay_port()
    trust = json.loads(json.dumps(_trust().policy_dict()))
    trust['requests'] = [
        relay.RelayRequestEntry().entry_dict(),
        relay.RelayRequestEntry(query='v2').entry_dict()]
    run = EngineRun(tmp_path / 'engine', trust, SYNTHETIC_CA['pem'],
                    bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?v2 HTTP/1.1\r\n'
                       b'Host: 127.0.0.1:%d\r\nx-api-key: k\r\n'
                       b'Content-Length: 2\r\n\r\n{}' % bound_port)
        done = run.call_done()
        assert done['code'] == 'relay_refused_cardinality'
        assert done['counters']['upstream_connections'] == 0
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_pipelined_extra_bytes_refuse_before_upstream(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        request = approved_head('127.0.0.1:%d' % bound_port) \
            + b'POST /v1/messages?beta=true HTTP/1.1\r\n'
        run.send_guest(request)
        assert run.call_done()['code'] == 'relay_refused_cardinality'
        run.stop()
        run.wait_exit()
    finally:
        run.close()


def test_engine_zero_requests_eof_is_cardinality(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.close_guest()
        assert run.engine_done()['code'] == 'relay_refused_cardinality'
        run.wait_exit()
    finally:
        run.close()


def test_engine_stop_while_idle_starts_nothing(tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.stop()
            assert run.engine_done()['code'] == 'relay_stopped'
            run.wait_exit()
            assert run.dns_calls() == []          # no resolution after stop
        finally:
            run.close()
        assert upstream.requests() == []          # no connection after stop
    finally:
        upstream.close()


def test_engine_stop_mid_exchange_no_new_dns_or_connect(
        tmp_path, cert_material):
    """Stop during a stalled handshake: the stalled connection is torn down,
    exactly one resolution and one connection exist, nothing is resent."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(stall_handler(read_first=False),
                            cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, handshake_timeout_ms=8000,
                       idle_timeout_ms=8000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            time.sleep(0.5)
            run.stop()
            done = run.engine_done()
            assert done['code'] == 'relay_stopped'
            counters = done['counters']
            assert counters['dns_resolutions'] == 1
            assert counters['upstream_connections'] == 1
            run.wait_exit()
            assert run.dns_calls() == [[ORIGIN_HOSTNAME, upstream.port]]
        finally:
            run.close()
        assert len(upstream.requests()) == 1     # no second connection
    finally:
        upstream.close()


def test_engine_parent_liveness_eof_exits(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.close_liveness()
        assert run.engine_done()['code'] == 'relay_parent_lost'
        assert run.wait_exit() == 0
    finally:
        run.close()


@pytest.mark.parametrize('injected', [
    {'results': [['2', '127.0.0.1']]},          # loopback
    {'results': [['2', '10.9.9.9']]},           # private
    {'results': [['2', '169.254.7.7']]},        # link-local
    {'results': [['2', '224.0.0.9']]},          # multicast
    {'results': [['2', '0.0.0.0']]},            # unspecified
    {'results': [['10', '::ffff:127.0.0.1']]},  # IPv4-mapped
    {'results': [['10', 'fe80::1']]},           # IPv6 link-local
])
def test_engine_default_rule_refuses_non_public_resolution(
        tmp_path, cert_material, injected):
    """Under the default permitted-address rule every non-public resolution
    class refuses with one resolution and zero connects (the local upstream
    proves no connection was ever attempted)."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       permitted_address_rule='public-global-unicast-only',
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=injected)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_dns_refused'
            assert done['counters']['dns_resolutions'] == 1
            assert done['counters']['upstream_connections'] == 0
            run.stop()
            run.wait_exit()
            assert run.dns_calls() == [[ORIGIN_HOSTNAME, upstream.port]]
        finally:
            run.close()
        assert upstream.requests() == []
    finally:
        upstream.close()


def test_engine_qualification_rule_permits_numeric_loopback_only(
        tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port,
                        dns={'results': [['10', '::1']]})
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_dns_refused'   # ::1 is not numeric v4
            assert done['counters']['upstream_connections'] == 0
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert upstream.requests() == []
    finally:
        upstream.close()


def test_engine_qualification_rule_allows_127(tmp_path, cert_material):
    """The qualification rule permits numeric loopback: same wiring as the
    happy path, explicitly under the qualification rule."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       permitted_address_rule='qualification-loopback-only',
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            run.response_reader.read_exact(len(DEFAULT_RESPONSE), 10)
            assert run.call_done()['code'] == 'relay_ok'
            run.close_guest()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_pinned_ca_only_no_ambient_roots(tmp_path, cert_material):
    """The engine trusts ONLY the pinned bundle: the same synthetic server
    certificate succeeds under its own pin and fails under an unrelated pin
    (no ambient system or user root store can validate it)."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    unrelated = cert_material[UNRELATED_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           unrelated['sha256'], unrelated['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        unrelated['pem'], bound_port=bound_port,
                        dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_channel_failed'  # verify failed
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_hostname_mismatch_fails_handshake(tmp_path, cert_material):
    require_certs(cert_material)
    mismatch = cert_material[MISMATCH_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=mismatch['cert'],
                            key_path=mismatch['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           mismatch['sha256'], mismatch['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        mismatch['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done()
            assert done['code'] == 'relay_channel_failed'
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_handshake_timeout(tmp_path, cert_material):
    """A TLS-less listener that accepts but never handshakes: the handshake
    deadline fails the call with the fixed timeout code and no retry."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    bound_port = relay.draw_relay_port()

    def raw_stall(stream, record):
        time.sleep(8.0)

    upstream = FakeUpstream(raw_stall)
    try:
        trust = _trust(origin_port=upstream.port, handshake_timeout_ms=900,
                       idle_timeout_ms=9000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done(timeout=15)
            assert done['code'] == 'relay_handshake_timeout'
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


@pytest.mark.skipif(os.name == 'nt', reason=(
    'Windows refuses excess backlog connections immediately instead of '
    'dropping SYNs, so a loopback connect-timeout is not deterministically '
    'provable there; the Linux host covers the timeout classification'))
def test_engine_connect_timeout_backlog(tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    fillers = []
    try:
        # Fill the accept backlog; once SYN dropping starts (a filler cannot
        # complete), the queue is full and the engine's connect must hit its
        # deadline instead of succeeding or being refused.
        for _ in range(4):
            filler = socket.socket()
            filler.settimeout(0.5)
            try:
                filler.connect(('127.0.0.1', port))
                fillers.append(filler)
            except OSError:
                filler.close()
                break
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=port, connect_timeout_ms=1200,
                       handshake_timeout_ms=9000, idle_timeout_ms=9000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done(timeout=15)
            assert done['code'] == 'relay_connect_timeout'
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
    finally:
        for filler in fillers:
            filler.close()
        listener.close()


def test_engine_idle_timeout_guest_stalls(tmp_path):
    """A partial guest request that never completes fails on the idle
    deadline (no byte in either direction)."""
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine',
                    _trust(idle_timeout_ms=800).policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port)
    try:
        run.wait_started()
        run.send_guest(b'POST /v1/messages?beta=true HTTP/1.1\r\nHost: 127.')
        done = run.engine_done(timeout=15)
        assert done['code'] == 'relay_idle_timeout'
        assert done['counters']['upstream_connections'] == 0
        run.wait_exit()
    finally:
        run.close()


def test_engine_idle_timeout_upstream_stalls_before_response(
        tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(stall_handler(read_first=True),
                            cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=800,
                       handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.engine_done(timeout=15)
            assert done['code'] == 'relay_idle_timeout'
            counters = done['counters']
            assert counters['upstream_connections'] == 1
            assert counters['requests_observed'] == 1
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_idle_timeout_upstream_stalls_mid_response(
        tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(partial_response_handler(),
                            cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=800,
                       handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.engine_done(timeout=15)
            assert done['code'] == 'relay_idle_timeout'
            assert done['counters']['upstream_connections'] == 1
            partial = run.response_reader.read_for(0.5)
            assert partial.startswith(b'HTTP/1.1 200 OK\r\n')  # head released
            assert len(partial) == len(b'HTTP/1.1 200 OK\r\n'
                                       b'Content-Length: 1000\r\n\r\n') + 300
            run.wait_exit()
        finally:
            run.close()
    finally:
        upstream.close()


def test_engine_total_timeout_supersedes(tmp_path):
    bound_port = relay.draw_relay_port()
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(),
                    SYNTHETIC_CA['pem'], bound_port=bound_port, total_ms=900)
    try:
        started = run.wait_started()
        assert started['type'] == 'started'
        done = run.engine_done(timeout=15)
        assert done['code'] == 'relay_total_timeout'
        run.wait_exit()
    finally:
        run.close()


def test_engine_total_timeout_mid_exchange(tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(stall_handler(read_first=False),
                            cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, handshake_timeout_ms=9000,
                       idle_timeout_ms=9000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, total_ms=4000,
                        dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.engine_done(timeout=15)
            assert done['code'] == 'relay_total_timeout'
            assert done['counters']['upstream_connections'] == 1
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_response_bytes_exceeded(tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(oversized_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=6000,
                       handshake_timeout_ms=6000, max_relay_response_bytes=4096,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done(timeout=15)
            assert done['code'] == 'relay_response_bytes_exceeded'
            assert done['counters']['upstream_connections'] == 1
            assert done['counters']['guest_bytes_out'] <= 4096
            assert done['counters']['teardown_failures'] == 0
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1     # failed, not retried
    finally:
        upstream.close()


def test_engine_over_sending_server_bounded_discard_drain(
        tmp_path, cert_material):
    """An upstream sending far beyond its declared framing: the response
    completes at the exact Content-Length, the surplus dies in the bounded
    discard drain (never forwarded, capped at 4096), and the call still
    succeeds."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(body=b'R' * 1000, after=b'S' * 100_000),
                            cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=6000,
                       handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            response = run.response_reader.read_exact(
                len(b'HTTP/1.1 200 OK\r\nContent-Length: 1000\r\n\r\n') + 1000,
                10)
            assert response.startswith(b'HTTP/1.1 200 OK\r\n')
            assert response.endswith(b'R' * 1000)
            assert b'SS' not in response                  # surplus never forwarded
            done = run.call_done(timeout=15)
            assert done['code'] == 'relay_ok'
            counters = done['counters']
            assert counters['guest_bytes_out'] == len(response)
            assert counters['teardown_failures'] == 0
            run.stop()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_chunked_response_completes_and_truncation_fails(
        tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    body = (b'6\r\nhello \r\n5\r\nworld\r\n0\r\n\r\n')
    head = b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
    upstream = FakeUpstream(chunked_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=6000,
                       handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            response = run.response_reader.read_exact(len(head + body), 10)
            assert response == head + body          # raw bytes unmodified
            assert run.call_done()['code'] == 'relay_ok'
            run.stop()
            run.wait_exit()
        finally:
            run.close()
    finally:
        upstream.close()
    truncated = FakeUpstream(chunked_handler(truncated=True),
                             cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=truncated.port, idle_timeout_ms=1500,
                       handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine2', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            done = run.call_done(timeout=15)
            assert done['code'] in ('relay_channel_failed', 'relay_idle_timeout')
            assert done['counters']['upstream_connections'] == 1
            run.stop()
            run.wait_exit()
        finally:
            run.close()
    finally:
        truncated.close()


def test_engine_close_delimited_response(tmp_path, cert_material):
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    body = b'plain-body-until-close'
    head = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n'
    upstream = FakeUpstream(close_delimited_handler(body=body),
                            cert_path=primary['cert'], key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=6000,
                       handshake_timeout_ms=6000,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            response = run.response_reader.read_exact(len(head + body), 10)
            assert response == head + body
            assert run.call_done()['code'] == 'relay_ok'
            run.close_guest()
            run.wait_exit()
        finally:
            run.close()
    finally:
        upstream.close()


def test_engine_fragmented_response_unmodified(tmp_path, cert_material):
    """Irregular response fragmentation with a tiny configured read chunk:
    the guest still receives the exact bytes (never cached, replayed or
    resent)."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    payload = RESPONSE_SENTINEL + b'-fragment-payload-' * 40

    def fragmented(stream, record):
        read_request_upstream(stream, record)
        head = (b'HTTP/1.1 200 OK\r\nContent-Length: '
                + str(len(payload)).encode('ascii') + b'\r\n\r\n')
        whole = head + payload
        offset = 0
        for size in (1, 7, 3, 61, 2, 400, 5):
            if offset >= len(whole):
                break
            stream.sendall(whole[offset:offset + size])
            offset += size
            time.sleep(0.002)
        if offset < len(whole):
            stream.sendall(whole[offset:])

    upstream = FakeUpstream(fragmented, cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port, idle_timeout_ms=6000,
                       handshake_timeout_ms=6000,
                       relay_response_read_chunk=64,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        expected = (b'HTTP/1.1 200 OK\r\nContent-Length: '
                    + str(len(payload)).encode('ascii') + b'\r\n\r\n' + payload)
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            response = run.response_reader.read_exact(len(expected), 15)
            assert response == expected
            done = run.call_done()
            assert done['code'] == 'relay_ok'
            assert done['counters']['guest_bytes_out'] == len(expected)
            run.close_guest()
            run.wait_exit()
        finally:
            run.close()
        assert len(upstream.requests()) == 1
    finally:
        upstream.close()


def test_engine_ca_pin_mismatch_is_a_startup_error(tmp_path):
    bound_port = relay.draw_relay_port()
    other = b'pal-synthetic-other-bytes\n'
    run = EngineRun(tmp_path / 'engine', _trust().policy_dict(), other,
                    bound_port=bound_port)
    try:
        event = run.next_report(timeout=20)
        assert event == {'type': 'error', 'code': 'relay_ca_pin_mismatch'}
        assert run.wait_exit() == 1
    finally:
        run.close()


def test_engine_conf_declared_preflight_refused(tmp_path):
    bound_port = relay.draw_relay_port()
    trust = json.loads(json.dumps(_trust().policy_dict()))
    trust['preflight'] = trust['requests']
    run = EngineRun(tmp_path / 'engine', trust, SYNTHETIC_CA['pem'],
                    bound_port=bound_port)
    try:
        event = run.next_report(timeout=20)
        assert event == {'type': 'error', 'code': 'relay_preflight_not_approved'}
        assert run.wait_exit() == 1
    finally:
        run.close()


def test_engine_conf_invalid_scheme_refused(tmp_path):
    bound_port = relay.draw_relay_port()
    trust = json.loads(json.dumps(_trust().policy_dict()))
    trust['origin'] = {'scheme': 'http', 'hostname': ORIGIN_HOSTNAME,
                       'port': 443}
    run = EngineRun(tmp_path / 'engine', trust, SYNTHETIC_CA['pem'],
                    bound_port=bound_port)
    try:
        event = run.next_report(timeout=20)
        assert event == {'type': 'error', 'code': 'relay_config_invalid'}
        assert run.wait_exit() == 1
    finally:
        run.close()


def test_engine_report_evidence_hygiene(tmp_path, cert_material):
    """Every report line across a success and a refusal: fixed types, closed
    codes, integer counters only, and no sentinel (credential, prompt or
    response byte) anywhere in the report stream or stderr."""
    require_certs(cert_material)
    primary = cert_material[ORIGIN_HOSTNAME]
    upstream = FakeUpstream(ok_handler(), cert_path=primary['cert'],
                            key_path=primary['key'])
    try:
        bound_port = relay.draw_relay_port()
        trust = _trust(origin_port=upstream.port,
                       ca_bundle=relay.RelayCaBundlePin(
                           '/opt/pal-synthetic/relay-ca.pem',
                           primary['sha256'], primary['size']))
        run = EngineRun(tmp_path / 'engine', trust.policy_dict(),
                        primary['pem'], bound_port=bound_port, dns=DNS_LOOPBACK)
        try:
            run.wait_started()
            run.send_guest(approved_head('127.0.0.1:%d' % bound_port))
            run.response_reader.read_exact(len(DEFAULT_RESPONSE), 10)
            assert run.call_done()['code'] == 'relay_ok'
            run.send_guest(b'GET / HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n'
                           b'Content-Length: 0\r\n\r\n' % bound_port)
            # The call already concluded: ANY further request is the
            # cardinality refusal, before any other validation.
            assert run.call_done()['code'] == 'relay_refused_cardinality'
            run.stop()
            assert run.engine_done()['code'] == 'relay_stopped'
            run.wait_exit()
            stderr = run._stderr or ''
        finally:
            run.close()
    finally:
        upstream.close()
    lines = bytes(run.report_reader.raw).split(b'\n')
    events = [json.loads(line) for line in lines if line]
    assert [event['type'] for event in events] == ['started', 'call_done',
                                                   'call_done', 'engine_done']
    allowed_codes = relay.RELAY_OUTCOMES | {'relay_config_invalid',
                                            'relay_ca_pin_mismatch'}
    for event in events:
        assert set(event) <= {'type', 'code', 'counters',
                              'protocol_version'}
        if 'code' in event:
            assert event['code'] in allowed_codes
        if 'counters' in event:
            assert all(type(value) is int and value >= 0
                       for value in event['counters'].values())
    stream = bytes(run.report_reader.raw) + stderr.encode('utf-8', 'replace')
    for sentinel in (KEY_SENTINEL, PROMPT_SENTINEL, RESPONSE_SENTINEL):
        assert sentinel not in stream
