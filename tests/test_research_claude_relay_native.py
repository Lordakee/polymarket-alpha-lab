"""EXPLICIT OPT-IN relay qualification only; FAKE service, DUMMY credentials.

This module is the L9 amendment section 5 test T8 (worker W4). It qualifies
the bounded fixed-origin validating request relay against a FAKE Messages TLS
service (a self-signed test CA generated in-test inside this test process)
using DUMMY synthetic credentials through the real supplier/factory/model/
contained-process chain. This is NOT a real endpoint, NOT credential use and
NOT activation: ``activation_authorized`` stays False everywhere and no
engineering pass can ever authorize real activation (mirroring
tests/test_research_claude_profile_native.py).

Opt-in surface: the native proof requires the explicit
POLYMARKET_ALPHA_LAB_CLAUDE_RELAY_QUALIFICATION=1 PLUS the supplied official
image opt-in (the five POLYMARKET_ALPHA_LAB_CLAUDE_PROBE* variables, reused
from tests/claude_cli_probe.py) PLUS native containment
(POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT=1), the native PostgreSQL prefix
(POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX) and the delegated cgroup v2 root
(POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT). After the explicit relay opt-in,
every missing prerequisite is a FAILURE, never a skip (the
require_native_containment pattern from tests/test_research_process_linux.py);
without the relay opt-in the native proof skips by design.

Runs NOW on every host (no opt-in needed): the gating matrix, the in-test CA
generation, the pinned-context fake Messages TLS service round trip and the
W1 relay trust configuration against the generated CA
(qualification-loopback-only rule, closed single-POST request set, blocked
preflight declaration).

WAITS (skip-until-landed, each skip names the exact missing deliverable):
the native proof executes only after the L9 W2/W3 deliverables land
(RELAY_HELPER_SOURCE and the relay-fixed-origin launch branch in
research_process_linux, carrying the reviewed trust configuration on the
launch) and the W1 v3 profile branch lands in research_claude_profile (the
branch is selected by the launch's closed egress value and accepts exactly
the symbolic numeric-loopback http endpoint), AND the 166 Linux host
recovers. Until then the native test skips at its first missing interface
probe while collection stays clean; the documented interfaces it was
authored against are pinned in the constants and probes below.
"""
from contextlib import contextmanager
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import sys
from threading import Thread

import pytest

from polymarket_alpha_lab.research_claude_profile import MODEL_ID
from polymarket_alpha_lab.research_process import ResearchProcessSpec
from polymarket_alpha_lab.team_research_agent_types import strict_json
from tests import claude_cli_probe as probe

RELAY_OPT_IN_ENV = 'POLYMARKET_ALPHA_LAB_CLAUDE_RELAY_QUALIFICATION'
CONTAINMENT_ENV = 'POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT'
PG_PREFIX_ENV = 'POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'
CGROUP_ROOT_ENV = 'POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT'
RELAY_QUALIFICATION_ENABLED = os.environ.get(RELAY_OPT_IN_ENV) == '1'

# Documented qualification interface (L9 amendment / L8-D design, frozen for
# this test; the literals match the landed W1 v3 branch constants
# RELAY_EGRESS_POLICY / RELAY_ENDPOINT_DECLARATION verbatim, kept local here
# so collection never depends on unlanded imports).
QUALIFICATION_BIND_ADDRESS = '127.0.0.1'
QUALIFICATION_HOSTNAME = 'localhost'  # resolves to numeric loopback only
QUALIFICATION_ADDRESS_RULE = 'qualification-loopback-only'
SYMBOLIC_RELAY_ENDPOINT = 'http://127.0.0.1:0'  # v3 symbolic per-call port
RELAY_EGRESS_POLICY = 'relay-fixed-origin'
LAUNCH_TRUST_FIELD = 'relay_trust'  # W3 relay-launch field (RelayTrustConfig)
FIXED_QUALIFICATION_CA_PATH = '/opt/pal-qualification/ca/qualification-ca.pem'
RELAY_PORT_WINDOW = (20000, 32767)
RELAY_PROTOCOL_VERSION = 'research-linux-relay-v1'
RELAY_EVIDENCE_ACCESSOR = 'LINUX_RELAY_EVIDENCE'  # documented W2/W3 seam
OBSERVATION_SCHEMA = 'claude-relay-qualification-v1'
RELAY_TEST_KEY = 'SYNTHETIC-PAL-RELAY-NOT-A-CREDENTIAL'
# Preflight-shaped refusals: a request OUTSIDE the approved single-POST set
# (a preflight attempt, or a duplicate/second request such as a retry) must
# close the call with the refusal recorded and nothing patched. A header or
# framing refusal of the Messages POST itself is NOT in this set: that is a
# contract mismatch that fails the qualification outright.
PREFLIGHT_REFUSAL_CODES = frozenset(('relay_refused_method', 'relay_refused_target',
                                     'relay_refused_cardinality'))


def _relay_module():
    """L9 W1 core (the reviewed trust configuration records); skip-until-landed."""
    try:
        from polymarket_alpha_lab import research_linux_relay as module
    except ImportError:
        pytest.skip('waits for the L9 W1 deliverable: research_linux_relay '
                    '(RelayTrustConfig/RelayCaBundlePin) has not landed yet')
    return module


# ---------------------------------------------------------------------------
# Opt-in gating: skip only on the absent relay opt-in; fail closed after it.
# ---------------------------------------------------------------------------

def _relay_gate(environment):
    """('skip', []) without the relay opt-in; every OTHER missing prerequisite
    after that opt-in is a problem (fail closed), never a skip."""
    if environment.get(RELAY_OPT_IN_ENV) != '1':
        return 'skip', []
    problems = []
    if environment.get(CONTAINMENT_ENV) != '1':
        problems.append(CONTAINMENT_ENV + '=1 is required with the relay opt-in')
    invalid_image = False
    try:
        image = probe.configured_image(environment)
    except ValueError:
        invalid_image = True
        image = None
        problems.append('the supplied official image opt-in is partial or invalid: '
                        'exactly ' + ', '.join(probe._ENV) + ' are required')
    if image is None and not invalid_image:
        problems.append('the supplied official image opt-in is absent: '
                        + ', '.join(probe._ENV) + ' are required')
    if not environment.get(PG_PREFIX_ENV):
        problems.append(PG_PREFIX_ENV + ' must name the native PostgreSQL prefix')
    if not environment.get(CGROUP_ROOT_ENV):
        problems.append(CGROUP_ROOT_ENV + ' must name the delegated cgroup v2 subtree')
    return ('ready' if not problems else 'fail'), problems


def require_relay_qualification():
    """Fail closed (never skip) when the explicit relay opt-in lacks prerequisites."""
    status, problems = _relay_gate(os.environ)
    if status == 'skip':
        pytest.skip('explicit relay qualification opt-in required')
    if sys.platform != 'linux':
        problems.append('linux host required')
    if not (shutil.which('bwrap') or Path('/usr/bin/bwrap').is_file()):
        problems.append('bwrap containment executable required')
    if shutil.which('openssl') is None:
        problems.append('openssl CLI required to generate the in-test CA')
    root = os.environ.get(CGROUP_ROOT_ENV, '')
    if root:
        controllers = Path(root, 'cgroup.controllers')
        if not controllers.is_file():
            problems.append(CGROUP_ROOT_ENV + ' must name a delegated cgroup v2 '
                            'subtree carrying cgroup.controllers')
        else:
            try:
                available = controllers.read_text().split()
            except OSError:
                problems.append(CGROUP_ROOT_ENV + ' cgroup.controllers is not readable')
                available = ()
            if 'memory' not in available or 'pids' not in available:
                problems.append('delegated cgroup subtree lacks memory/pids controllers')
    prefix = os.environ.get(PG_PREFIX_ENV, '')
    if prefix and not Path(prefix).is_dir():
        problems.append(PG_PREFIX_ENV + ' must name the native PostgreSQL prefix directory')
    if problems:
        pytest.fail('relay qualification prerequisites missing: ' + '; '.join(problems))
    return dict(image=probe.configured_image(os.environ), cgroup_root=root,
                pg_prefix=prefix)


# ---------------------------------------------------------------------------
# Fake Messages TLS service machinery and the in-test qualification CA.
# ---------------------------------------------------------------------------

def generate_qualification_ca(directory):
    """Self-signed qualification CA plus a localhost server leaf, generated
    in-test through the openssl CLI. The CA bytes are the ONLY trust material
    any context in this module ever loads; nothing here is a real credential,
    a real endpoint or activation material."""
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    ca_key = directory / 'qualification-ca.key'
    ca_cert = directory / 'qualification-ca.pem'
    server_key = directory / 'messages-server.key'
    server_csr = directory / 'messages-server.csr'
    server_cert = directory / 'messages-server.pem'
    names = directory / 'localhost.ext'
    names.write_text('subjectAltName=DNS:localhost\n', encoding='ascii')
    commands = (
        ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
         '-keyout', str(ca_key), '-out', str(ca_cert), '-days', '2',
         '-subj', '/CN=PAL-Relay-Qualification-Test-CA',
         '-addext', 'basicConstraints=critical,CA:TRUE',
         '-addext', 'keyUsage=critical,keyCertSign'],
        ['openssl', 'req', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(server_key),
         '-out', str(server_csr), '-subj', '/CN=localhost'],
        ['openssl', 'x509', '-req', '-in', str(server_csr), '-CA', str(ca_cert),
         '-CAkey', str(ca_key), '-CAcreateserial', '-out', str(server_cert),
         '-days', '2', '-extfile', str(names)])
    for command in commands:
        subprocess.run(command, check=True, capture_output=True, timeout=120)
    bundle = ca_cert.read_bytes()
    return ca_cert, bundle, sha256(bundle).hexdigest(), len(bundle), server_cert, server_key


def _pinned_client_context(ca_file):
    """Mirror of the relay engine's documented pinned-context contract: TLS 1.2
    floor, hostname checking, CERT_REQUIRED, and ONLY the pinned CA bytes; no
    create_default_context and no load_default_certs anywhere."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(cafile=str(ca_file))
    return context


class _MessagesServer(HTTPServer):
    allow_reuse_address = False

    def __init__(self, certfile, keyfile):
        self.connections, self.requests, self.unexpected = 0, 0, 0
        self.faults, self.responses, self.matches = 0, 0, True
        self.records = []
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certfile=str(certfile), keyfile=str(keyfile))
        super().__init__((QUALIFICATION_BIND_ADDRESS, 0), _MessagesHandler)
        self.socket = context.wrap_socket(self.socket, server_side=True)
        self.socket.settimeout(10)

    def get_request(self):
        sock, address = super().get_request()
        self.connections += 1  # TLS-established connections only
        sock.settimeout(10)
        return sock, address

    def handle_error(self, *_):
        self.faults += 1  # never print peer headers, body or exception text


class _MessagesHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        pass

    def _respond(self, code, payload=b'', content_type='text/event-stream'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_POST(self):
        server = self.server
        server.requests += 1
        record = dict(method='POST', target_ok=False, host_ok=False, framing_ok=False,
                      api_key_ok=False, header_family={}, body_ok=False, body_bytes=0,
                      body_sha256=None)
        server.records.append(record)
        try:
            # Unnormalized request target from the RAW request line (the relay
            # reconstructs the approved literal upstream, never the guest's).
            line = getattr(self, 'requestline', '')
            parts = line.split() if type(line) is str else []
            record['target_ok'] = (len(parts) == 3 and parts[1] == '/v1/messages?beta=true')
            record['host_ok'] = self.headers.get_all('Host', []) == [
                '%s:%d' % (QUALIFICATION_HOSTNAME, server.server_port)]
            lengths = self.headers.get_all('Content-Length', [])
            record['framing_ok'] = (len(lengths) == 1
                and re.fullmatch('[1-9][0-9]{0,6}', lengths[0]) is not None
                and self.headers.get('Transfer-Encoding') is None)
            for name in ('x-api-key', 'anthropic-version', 'anthropic-beta',
                         'content-type', 'accept', 'accept-encoding'):
                record['header_family'][name] = len(self.headers.get_all(name, []))
            record['api_key_ok'] = self.headers.get_all('x-api-key', []) == [RELAY_TEST_KEY]
            length = int(lengths[0]) if record['framing_ok'] else 0
            raw = self.rfile.read(length) if 1 <= length <= 1048576 else b''
            record['body_bytes'] = len(raw)
            record['body_sha256'] = sha256(raw).hexdigest() if raw else None
            try:
                body = strict_json(raw.decode('utf-8'))
            except Exception:
                body = None
            texts = tuple(probe._strings(body)) if body is not None else ()
            record['body_ok'] = (type(body) is dict
                and body.get('model') == MODEL_ID
                and type(body.get('max_tokens')) is int and body['max_tokens'] == 1024
                and body.get('stream') is True
                and any(probe.test_input().prompt_json in text for text in texts)
                and all(RELAY_TEST_KEY not in text and probe.UNRELATED not in text
                        for text in texts))
            good = (record['target_ok'] and record['host_ok'] and record['framing_ok']
                    and record['api_key_ok'] and record['body_ok']
                    and record['header_family']['x-api-key'] == 1
                    and record['header_family']['anthropic-version'] == 1
                    and self.headers.get('Authorization') is None)
            if not good:
                server.matches = False
                self._respond(400)
                return
            self._respond(200, probe._stream('success'))
            server.responses += 1
        except Exception:
            server.faults += 1
            server.matches = False
            self.close_connection = True

    def _unexpected(self):
        # No preflight is approved: anything but the single Messages POST is
        # an unexpected request at this service. The relay must keep such
        # requests from ever arriving here (they are refused inner-hop).
        self.server.unexpected += 1
        self.server.matches = False
        self.server.records.append(dict(method=getattr(self, 'command', None),
                                        unexpected=True))
        self._respond(404)

    do_GET = do_HEAD = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_CONNECT = _unexpected


@contextmanager
def fake_messages_service(certfile, keyfile):
    server = _MessagesServer(certfile, keyfile)

    def serve():
        try:
            server.serve_forever(poll_interval=.05)
        except BaseException:
            server.faults += 1
    worker = Thread(target=serve, name='pal-claude-relay-qualification-tls')
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
                failure = failure if failure is not None else error
        if worker.is_alive():
            failure = failure if failure is not None \
                else RuntimeError('qualification_server_cleanup_failed')
    if failure is not None:
        raise failure


# ---------------------------------------------------------------------------
# Runs-now tests: gating matrix, CA machinery, fake TLS service, trust config.
# ---------------------------------------------------------------------------

def _complete_gate_environment(image):
    return {
        RELAY_OPT_IN_ENV: '1', CONTAINMENT_ENV: '1',
        PG_PREFIX_ENV: '/opt/pal-synthetic/pg-prefix',
        CGROUP_ROOT_ENV: '/opt/pal-synthetic/cgroup',
        'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE': '1',
        'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE': image,
        'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256': 'f' * 64,
        'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES': '33554432',
        'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST': '1',
    }


def test_relay_gate_skips_only_when_the_explicit_optin_is_absent(tmp_path):
    environment = _complete_gate_environment(str(tmp_path / 'official-claude'))
    assert _relay_gate({}) == ('skip', [])
    assert _relay_gate({'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE': '1'}) == ('skip', [])
    status, problems = _relay_gate(environment)
    assert status == 'ready' and problems == []


@pytest.mark.parametrize('remove', [
    CONTAINMENT_ENV, PG_PREFIX_ENV, CGROUP_ROOT_ENV,
    'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE', 'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256',
    'POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST',
])
def test_relay_gate_fails_closed_on_each_missing_prerequisite(tmp_path, remove):
    environment = _complete_gate_environment(str(tmp_path / 'official-claude'))
    del environment[remove]
    status, problems = _relay_gate(environment)
    assert status == 'fail' and problems
    assert any(remove in problem for problem in problems), problems


def test_relay_gate_names_every_missing_prerequisite_at_once():
    status, problems = _relay_gate({RELAY_OPT_IN_ENV: '1'})
    assert status == 'fail'
    assert len(problems) == 4  # containment, absent image opt-in, pg prefix, cgroup root


def test_qualification_ca_and_fake_messages_tls_service_round_trip(tmp_path):
    """The fake-service machinery verifies NOW: a pinned-context TLS client
    exchanges the approved request form with the fake Messages service, and
    the fresh self-signed test CA is trusted by NOTHING but the pinned
    context (zero ambient trust, mirroring the relay engine's contract)."""
    _ca, bundle, digest, size, server_cert, server_key = generate_qualification_ca(tmp_path)
    assert bundle.startswith(b'-----BEGIN CERTIFICATE-----')
    assert digest == sha256(bundle).hexdigest() and size == len(bundle)
    request = probe.test_input()
    assert json.loads(request.messages_json)[0]['content'] == probe.APPROVED
    body = json.dumps(dict(model=MODEL_ID, max_tokens=request.max_output_tokens,
                           stream=True,
                           messages=[{'role': 'user', 'content': request.prompt_json}]),
                      separators=(',', ':')).encode()
    with fake_messages_service(server_cert, server_key) as service:
        port = service.server_port
        head = ('POST /v1/messages?beta=true HTTP/1.1\r\n'
                'Host: %s:%d\r\n'
                'x-api-key: %s\r\n'
                'anthropic-version: 2023-06-01\r\n'
                'anthropic-beta: messages-2023-12-15\r\n'
                'content-type: application/json\r\n'
                'accept: text/event-stream\r\n'
                'accept-encoding: gzip\r\n'
                'Content-Length: %d\r\n\r\n'
                % (QUALIFICATION_HOSTNAME, port, RELAY_TEST_KEY, len(body)))
        context = _pinned_client_context(_ca)
        with socket.create_connection((QUALIFICATION_BIND_ADDRESS, port), timeout=10) as raw:
            with context.wrap_socket(raw, server_hostname=QUALIFICATION_HOSTNAME) as tls:
                assert tls.version() in ('TLSv1.2', 'TLSv1.3')
                tls.sendall(head.encode('latin-1') + body)
                response = bytearray()
                while len(response) < 1048576:
                    block = tls.recv(4096)
                    if not block:
                        break
                    response.extend(block)
        # Zero ambient trust: a default context (ambient roots only, never the
        # pinned CA) must fail the handshake against the same fresh CA.
        ambient = ssl.create_default_context()
        with pytest.raises(ssl.SSLError):
            with socket.create_connection((QUALIFICATION_BIND_ADDRESS, port), timeout=10) as raw:
                with ambient.wrap_socket(raw, server_hostname=QUALIFICATION_HOSTNAME):
                    pass
        connections, requests, faults = service.connections, service.requests, service.faults
        unexpected, responses, matches, records = (service.unexpected, service.responses,
                                                   service.matches, service.records)
    assert bytes(response).startswith(b'HTTP/1.1 200')
    assert b'event: message_start' in bytes(response)
    assert connections == 1 and requests == 1 and unexpected == 0 and faults == 0
    assert responses == 1 and matches is True and len(records) == 1
    record = records[0]
    assert all(record[name] for name in ('target_ok', 'host_ok', 'framing_ok',
                                         'api_key_ok', 'body_ok'))
    assert record['header_family']['anthropic-version'] == 1
    assert record['header_family']['anthropic-beta'] == 1
    assert RELAY_TEST_KEY not in json.dumps(record) and probe.APPROVED not in json.dumps(record)


def test_qualification_trust_config_pins_the_fake_service_and_loopback_only(tmp_path):
    """The W1 trust configuration verifies NOW against the generated CA: the
    qualification-loopback-only address rule, the pinned CA identity, the
    closed single-POST request set over the reviewed port window, and the
    deliberately blocked preflight declaration. The v3 profile binding that
    carries this record waits for W1's profile branch (see the native proof)."""
    relay = _relay_module()
    _ca, _bundle, digest, size, _cert, _key = generate_qualification_ca(tmp_path)
    pin = relay.RelayCaBundlePin(FIXED_QUALIFICATION_CA_PATH, digest, size)
    trust = relay.RelayTrustConfig(
        ca_bundle=pin, origin_hostname=QUALIFICATION_HOSTNAME, origin_port=443,
        permitted_address_rule=QUALIFICATION_ADDRESS_RULE)
    policy = trust.policy_dict()
    encoded = json.dumps(policy, sort_keys=True)
    assert policy['protocol_version'] == RELAY_PROTOCOL_VERSION
    assert policy['permitted_address_rule'] == QUALIFICATION_ADDRESS_RULE
    assert policy['origin'] == dict(scheme='https', hostname=QUALIFICATION_HOSTNAME, port=443)
    assert policy['ca_bundle'] == dict(path=FIXED_QUALIFICATION_CA_PATH,
                                       sha256=digest, size_bytes=size)
    assert policy['endpoint_binding'] == 'per-call-numeric-loopback-http'
    assert [entry['method'] for entry in policy['requests']] == ['POST']
    assert trust.requests[0].expected_target() == '/v1/messages?beta=true'
    assert RELAY_TEST_KEY not in encoded and probe.APPROVED not in encoded
    assert relay.RELAY_PORT_WINDOW == RELAY_PORT_WINDOW == (20000, 32767)
    assert all(RELAY_PORT_WINDOW[0] <= relay.draw_relay_port() <= RELAY_PORT_WINDOW[1]
               for _ in range(64))
    with pytest.raises(ValueError, match='relay_preflight_not_approved'):
        relay.RelayTrustConfig(
            ca_bundle=pin, origin_hostname=QUALIFICATION_HOSTNAME, origin_port=443,
            permitted_address_rule=QUALIFICATION_ADDRESS_RULE,
            preflight_entries=(relay.RelayRequestEntry(),))
    assert relay.validate_relay_outcome('relay_ok') == 'relay_ok'
    with pytest.raises(ValueError):
        relay.validate_relay_outcome('ok')


# ---------------------------------------------------------------------------
# The native T8 proof (waits for W2/W3 landing and the 166 host recovery).
# ---------------------------------------------------------------------------

def _v3_relay_surface():
    """Resolve the documented post-W1/W2/W3 relay interfaces or skip with the
    exact missing deliverable (amendment section 5) until they land.

    Landed surface this resolves against (W1): the v3 profile branch is
    selected by the launch's closed egress value (the branch is duck-typed on
    ``egress_policy == 'relay-fixed-origin'``) and accepts exactly the
    symbolic numeric-loopback http endpoint; the reviewed trust configuration
    is carried ON the relay launch (the ``relay_trust`` field, post-W3), not
    as a profile field."""
    relay = _relay_module()
    helper_source = getattr(relay, 'RELAY_HELPER_SOURCE', None)
    if type(helper_source) is not str or not helper_source:
        pytest.skip('waits for the L9 W2/W3 relay helper deliverable: '
                    'RELAY_HELPER_SOURCE is not in research_linux_relay yet')
    from polymarket_alpha_lab import research_claude_profile as profiles
    from polymarket_alpha_lab import research_process_linux as linux
    from tests.test_research_process_linux import relaunch, synthetic_launch
    helper_digest = sha256(helper_source.encode('utf-8')).hexdigest()
    declaration = relay.RelayTrustConfig(
        ca_bundle=relay.RelayCaBundlePin(FIXED_QUALIFICATION_CA_PATH, 'c' * 64, 4096),
        origin_hostname=QUALIFICATION_HOSTNAME, origin_port=443,
        permitted_address_rule=QUALIFICATION_ADDRESS_RULE)
    relay_changes = dict(egress_policy=RELAY_EGRESS_POLICY,
                         helper_sha256=helper_digest)
    relay_changes[LAUNCH_TRUST_FIELD] = declaration
    try:
        launch = relaunch(synthetic_launch(), **relay_changes)
    except (TypeError, ValueError):
        pytest.skip("waits for the L9 W3 launch deliverable: LinuxLaunchSpec must "
                    "accept egress_policy='" + RELAY_EGRESS_POLICY + "' with the "
                    'relay helper digest, the exact (20000, 32767) port window and '
                    'the ' + LAUNCH_TRUST_FIELD + ' RelayTrustConfig record')
    assert launch.egress_policy == RELAY_EGRESS_POLICY
    if type(getattr(launch, LAUNCH_TRUST_FIELD, None)) is not relay.RelayTrustConfig:
        pytest.skip('waits for the L9 W3 launch deliverable: the relay launch must '
                    'carry the ' + LAUNCH_TRUST_FIELD + ' RelayTrustConfig record')
    with pytest.raises(ValueError):
        # Cross-pinning is rejected: the relay branch must refuse the frozen
        # offline helper digest (amendment MINOR: dual-value closed branch).
        relaunch(synthetic_launch(), **dict(relay_changes,
                                            helper_sha256=linux._helper_digest()))
    process = ResearchProcessSpec(
        ('/opt/pal-qualification/claude',), '/opt/pal-qualification/work',
        (('HOME', '/opt/pal-qualification/home'),
         ('CLAUDE_CONFIG_DIR', '/opt/pal-qualification/config')), 'e' * 64, 30000)
    try:
        profiles.ClaudeExecProfile(process=process,
                                   endpoint_url=SYMBOLIC_RELAY_ENDPOINT,
                                   linux_launch=launch)
    except ValueError as error:
        pytest.fail('the landed v3 profile branch rejected the documented relay '
                    'profile (symbolic endpoint over a relay launch): ' + repr(error))
    return dict(helper_digest=helper_digest, helper_source=helper_source)


def _admitted_call_codes(linux):
    return frozenset(linux._ADMITTED_ERRORS) | {'research_claude_call_failed'}


def _measured_relay_launch(directory, image, image_size, helper_digest, cgroup_root,
                           trust):
    """Assemble the relay launch from measured host facts (native run only):
    the real bwrap, the real interpreter and its measured runtime closure,
    the supplied official vendor image, the RELAY helper digest (never the
    frozen offline helper digest) and the reviewed trust configuration the
    relay launch carries."""
    from hashlib import sha256 as _sha256
    from polymarket_alpha_lab import research_process_linux as linux
    from tests.test_research_process_linux import discover_runtime_closure
    interpreter = str(Path(sys.executable).resolve())
    interp_bytes = Path(interpreter).read_bytes()
    wrapper_path = shutil.which('bwrap') or '/usr/bin/bwrap'
    wrapper_bytes = Path(wrapper_path).read_bytes()
    runtime = discover_runtime_closure(interpreter, image)
    values = dict(
        wrapper=linux.LinuxArtifactPin(str(Path(wrapper_path).resolve()),
                                       _sha256(wrapper_bytes).hexdigest(), len(wrapper_bytes)),
        helper_sha256=helper_digest,
        interpreter=linux.LinuxArtifactPin(interpreter, _sha256(interp_bytes).hexdigest(),
                                           len(interp_bytes)),
        supervisor_python_home=sys.base_prefix,
        runtime_files=tuple(runtime),
        vendor_guest_path='/pal/vendor/claude',
        helper_guest_path='/pal/runtime/helper.py',
        vendor_size_bytes=image_size,
        expected_version_output=probe.CLAUDE_VERSION + ' (Claude Code)\n',
        cgroup_root=cgroup_root,
        egress_policy=RELAY_EGRESS_POLICY,
        scratch_size_bytes=64 * 1024 * 1024,
        guest_tmp_size_bytes=32 * 1024 * 1024,
        memory_max_bytes=512 * 1024 * 1024,
        pids_max=32)
    values[LAUNCH_TRUST_FIELD] = trust
    return linux.LinuxLaunchSpec(**values)


def _relay_call_evidence(call_status):
    """Fixed relay outcome code plus counter metadata for the call.

    Documented post-W2/W3 landing seam: the launch surfaces the engine's
    fixed call_done/engine_done record (a closed RELAY_OUTCOMES code plus
    integer counters) through research_process_linux (expected as a
    LINUX_RELAY_EVIDENCE accessor beside LINUX_PHASE_COUNTERS, or an
    equivalent fixed surface this adapter is pointed at once landed). Until
    then the outcome is DERIVED from the closed vocabulary: a decoded
    successful exchange can only be the 'relay_ok' success code, and any
    failure keeps code None (never a guessed refusal code)."""
    from polymarket_alpha_lab import research_process_linux as linux
    accessor = getattr(linux, RELAY_EVIDENCE_ACCESSOR, None)
    if callable(accessor):
        evidence = accessor()
        if type(evidence) is not dict:
            pytest.fail(RELAY_EVIDENCE_ACCESSOR + ' must return the fixed relay '
                        'outcome record (closed code plus integer counters)')
        return dict(evidence, derived=False)
    return dict(code='relay_ok' if call_status == 'returned' else None,
                counters={}, derived=True)


def _run_relay_qualification(requirements, surface, tmp_path):
    """One contained qualification call: dummy credentials through the actual
    FiniteInMemoryApiKeySupplier -> claude_profile_factory -> ClaudeProcessModel
    -> run_research_process relay-launch path, against the fake TLS service.
    The observation carries metadata only (fixed codes, counters, sanitized
    request records); no credential, prompt or response byte is ever recorded."""
    relay = _relay_module()
    from polymarket_alpha_lab import research_process_linux as linux
    from polymarket_alpha_lab.research_claude_profile import (
        ClaudeExecProfile, FiniteInMemoryApiKeySupplier, claude_profile_factory)
    from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
    from tests.test_research_claude_profile import permission
    image, image_digest, image_size = requirements['image']
    root = tmp_path / 'claude-relay-qualification'
    root.mkdir(mode=0o700)
    for name in ('home', 'config', 'tmp', 'work'):
        (root / name).mkdir(mode=0o700)
    (root / 'CLAUDE.md').write_text(probe.UNRELATED, encoding='utf-8')
    (root / 'work/CLAUDE.md').write_text(probe.UNRELATED, encoding='utf-8')
    (root / 'config/settings.json').write_text(
        json.dumps({'env': {'PAL_UNRELATED': probe.UNRELATED}}), encoding='utf-8')
    ca_cert, _bundle, ca_digest, ca_size, server_cert, server_key = \
        generate_qualification_ca(root / 'ca')
    stop = ResearchDispatchStop()
    supplier = FiniteInMemoryApiKeySupplier(stop=stop, crypto_btc=(RELAY_TEST_KEY,),
                                            crypto_eth=())
    observation = dict(
        schema_version=OBSERVATION_SCHEMA, activation_authorized=False,
        test_service='fake-messages-tls-self-signed-in-test-ca',
        credentials='dummy-synthetic-not-a-real-credential',
        relay_helper_digest=surface['helper_digest'],
        offline_helper_digest=linux._helper_digest(),
        port_window=list(relay.RELAY_PORT_WINDOW),
        endpoint_url=SYMBOLIC_RELAY_ENDPOINT)
    call = dict(status='not_started', error_code=None, decoder_status='not_attempted',
                reported_tokens=None, response_matches=False)
    with fake_messages_service(server_cert, server_key) as service:
        trust = relay.RelayTrustConfig(
            ca_bundle=relay.RelayCaBundlePin(str(ca_cert), ca_digest, ca_size),
            origin_hostname=QUALIFICATION_HOSTNAME, origin_port=service.server_port,
            permitted_address_rule=QUALIFICATION_ADDRESS_RULE)
        launch = _measured_relay_launch(root, image, image_size,
                                        surface['helper_digest'],
                                        requirements['cgroup_root'], trust)
        observation['launch_helper_sha256'] = launch.helper_sha256
        observation['launch_egress_policy'] = launch.egress_policy
        process = ResearchProcessSpec(
            (image,), str(root / 'work'),
            (('HOME', str(root / 'home')), ('CLAUDE_CONFIG_DIR', str(root / 'config'))),
            image_digest, 180000, max_executable_bytes=image_size,
            cleanup_timeout_ms=15000)
        # The v3 profile binds the relay launch (which carries the trust
        # record) and declares only the symbolic numeric-loopback endpoint.
        profile = ClaudeExecProfile(process=process,
                                    endpoint_url=SYMBOLIC_RELAY_ENDPOINT,
                                    linux_launch=launch)
        factory = claude_profile_factory(
            profile=profile, authorization=permission(profile),
            api_key_supplier=supplier, allow_process_start=True,
            allow_api_key_use=True, stop=stop)
        model = factory('crypto_btc')
        request = probe.test_input()
        try:
            reply = model.complete(messages_json=request.messages_json,
                                   max_output_tokens=request.max_output_tokens)
            call.update(status='returned', decoder_status='accepted',
                        reported_tokens=reply.total_tokens)
            call['response_matches'] = (len(reply.calls) == 1
                and reply.calls[0].name == 'search_evidence'
                and strict_json(reply.calls[0].arguments_json) == {'query': probe.RESPONSE})
        except BaseException as error:
            code = (error.args[0] if isinstance(error, Exception) and len(error.args) == 1
                    and type(error.args[0]) is str else None)
            call.update(status='failed',
                        error_code=code if code in _admitted_call_codes(linux) else None)
    evidence = _relay_call_evidence(call['status'])
    observation.update(
        service=dict(port=service.server_port, connections=service.connections,
                     requests=service.requests, unexpected=service.unexpected,
                     faults=service.faults, responses=service.responses,
                     matches=service.matches, records=service.records),
        call=call, relay_evidence=evidence,
        supplier=dict(crypto_btc_remaining=supplier.remaining('crypto_btc'),
                      crypto_eth_remaining=supplier.remaining('crypto_eth')),
        cgroup_survivors=sorted(name for name in os.listdir(requirements['cgroup_root'])
                                if name.startswith('pal-call-')))
    return observation


def qualification_passed(value):
    """Engineering subset only; success can NEVER authorize real activation.

    Two closed outcomes pass:
    1. the success chain: exactly one request crossed to the fake service
       through the relay with the approved method/target/query/header family
       and the dummy key, the engine outcome is the fixed success code with
       integer counter metadata only, the decoded terminal envelope passed
       the shared production decoder, and teardown left no survivor; or
    2. the closed preflight blocker: a request outside the approved set was
       refused and recorded (fixed refusal code, nothing patched, no upstream
       connection ever made) and the call failed closed with the consumed
       supplier slot permanently consumed."""
    encoded = json.dumps(value, sort_keys=True)
    evidence = value['relay_evidence']
    service, call = value['service'], value['call']
    counters = evidence.get('counters')
    common = (value['activation_authorized'] is False
        and value['relay_helper_digest'] == value['launch_helper_sha256']
        and value['launch_helper_sha256'] != value['offline_helper_digest']
        and value['launch_egress_policy'] == RELAY_EGRESS_POLICY
        and value['port_window'] == [20000, 32767]
        and value['cgroup_survivors'] == []
        and call.get('error_code') != 'research_process_cleanup_failed'
        and value['supplier']['crypto_btc_remaining'] == 0
        and evidence.get('derived') is False
        and RELAY_TEST_KEY not in encoded and probe.APPROVED not in encoded)
    if type(counters) is dict:
        # Counter metadata only: integer counters, never prompt, credential
        # or response bytes.
        common = common and all(type(item) is int for item in counters.values())
        if 'upstream_connections' in counters:
            common = common and counters['upstream_connections'] <= 1
    if call['status'] == 'failed':
        return (common and call['error_code'] is not None
            and evidence.get('code') in PREFLIGHT_REFUSAL_CODES
            and service['connections'] == service['requests'] == service['responses'] == 0
            and service['unexpected'] == service['faults'] == 0)
    return (common and service['connections'] == 1 and service['requests'] == 1
        and service['unexpected'] == service['faults'] == 0
        and service['matches'] is True and service['responses'] == 1
        and call['decoder_status'] == 'accepted' and call['reported_tokens'] == 26
        and call['response_matches'] is True
        and evidence.get('code') == 'relay_ok')


@pytest.mark.skipif(not RELAY_QUALIFICATION_ENABLED,
                    reason='explicit relay qualification is opt-in')
def test_supplied_claude_relay_qualification_native(tmp_path, record_property):
    """T8: the official CLI's Messages request crosses the bounded relay to
    the FAKE TLS service (or the unapproved preflight closes the call,
    recorded and unpatched) over a measured relay launch with DUMMY
    credentials. NOT a real endpoint, NOT activation."""
    requirements = require_relay_qualification()
    surface = _v3_relay_surface()
    observation = _run_relay_qualification(requirements, surface, tmp_path)
    text = json.dumps(observation, sort_keys=True, separators=(',', ':'))
    record_property('claude_relay_qualification', text)
    print('CLAUDE_RELAY_QUALIFICATION ' + text, flush=True)
    assert qualification_passed(observation), text
    assert observation['activation_authorized'] is False
