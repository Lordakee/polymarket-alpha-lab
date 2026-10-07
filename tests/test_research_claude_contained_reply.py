"""Contained terminal-reply COMPOSITION proofs for the Claude client stack.

Proves, end to end through the real factory, client, relay and decoder
objects, that the retained L7 terminal reply (the exact 1671-byte official
CLI envelope kept in
.agent-artifacts/polymarket-alpha-lab/l7-final-ruling/retained-success-predecode.json,
outside this repository) survives the contained wiring unmodified:

* decoding path - the exact retained bytes through claude_profile_factory
  (contained v2 profile, finite in-memory supplier) -> ClaudeProcessModel ->
  decode_claude_result decode to the single exact search_evidence
  {"query": "SYNTHETIC-PAL-MOCK-RESPONSE"} action, the composed call ids
  and the synthetic 26-token total;
* pipe-delivery path - the real two-phase supervisor model-phase relay core
  (ContainedSession.run_model_phase -> _drain_model -> _final_drain) over
  real OS anonymous pipes with fragmented then final draining, asserting byte
  equality at the receive end with no version or control bytes injected;
* rejection matrix - representative truncation, nonzero stderr, unknown-key
  envelope, model mismatch and usage disagreement reject through the same
  wiring without repair or retry.

This proves COMPOSITION only; it is NOT official-image L5 qualification. The
replay emitter and the retained bytes are synthetic evidence fixtures; no
real provider, credential or official CLI image is executed anywhere here.

Portability: the decoding, relay-core and rejection slices run on every host
where the retained fixture is present (the fixture slice skips explicitly on
hosts without the artifact directory). Hosts that cannot execute the
Linux-only relay primitives (memfd/cgroup/bwrap namespaces) collect-and-skip
the native two-phase slices by design behind the same explicit opt-in the
containment suite uses (POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT=1); under
that opt-in missing prerequisites fail closed, never skip. On Windows the
relay core needs a pipe-safe readiness shim (select.select there waits only
on sockets): the shim replaces ONLY the wait, never the byte path - the
production reads, writes, caps and report protocol still move real bytes
through real OS pipes.
"""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from polymarket_alpha_lab import research_claude_exec as cli
from polymarket_alpha_lab import research_process_linux as linux
from polymarket_alpha_lab.research_claude_profile import (
    FiniteInMemoryApiKeySupplier, claude_profile_factory,
)
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_process import (
    ResearchProcessResult, ResearchProcessSpec, run_research_process,
)
from polymarket_alpha_lab.team_research_agent_types import strict_json
from tests.test_research_claude_exec import MODEL
from tests.test_research_claude_profile import candidate, permission
from tests.test_research_process_linux import (
    CONTAINMENT_ENABLED, build_native_launch, fixed_launch, relaunch,
    require_native_containment,
)

# The retained L7 final-ruling evidence lives OUTSIDE the repository; resolve
# it relative to this file so the suite does not depend on the cwd.
FIXTURE_PATH = (Path(__file__).resolve().parents[2] / '.agent-artifacts'
                / 'polymarket-alpha-lab' / 'l7-final-ruling'
                / 'retained-success-predecode.json')

EXPECTED_CALL = {'query': 'SYNTHETIC-PAL-MOCK-RESPONSE'}


def load_retained_document():
    """The retained fixture document, or an explicit skip on hosts without
    the artifact directory (the evidence lives outside the repository)."""
    if not FIXTURE_PATH.is_file():
        pytest.skip('retained L7 terminal fixture not present: %s' % FIXTURE_PATH)
    return json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def retained_bytes():
    """The exact retained terminal stdout bytes, cross-checked against the
    fixture's own recorded identity before any test uses them."""
    predecode = load_retained_document()['predecode']
    payload = predecode['stdout_excerpt_redacted'].encode('utf-8')
    assert predecode['stdout_excerpt_truncated'] is False
    assert predecode['stdout_utf8'] is True
    assert len(payload) == predecode['stdout_bytes'] == 1671
    assert sha256(payload).hexdigest() == predecode['stdout_sha256']
    return payload


def assert_search_evidence_reply(reply, call_number=1):
    """The retained reply decodes to exactly one synthetic search call."""
    assert reply.total_tokens == 3 + 5 + 7 + 11 == 26
    assert len(reply.calls) == 1
    assert reply.calls[0].call_id == 'claude-%d-0' % call_number
    assert reply.calls[0].name == 'search_evidence'
    assert strict_json(reply.calls[0].arguments_json) == EXPECTED_CALL
# ---------------------------------------------------------------------------
# Slice A - decoding path through the real factory and client (portable)
# ---------------------------------------------------------------------------

def bound_contained_factory(contained, supplier, stop):
    """The real factory binding for a contained v2 profile and its finite
    team-scoped supplier; no credential is used until the model call."""
    return claude_profile_factory(profile=contained,
        authorization=permission(contained), api_key_supplier=supplier,
        allow_process_start=True, allow_api_key_use=True, stop=stop)


def finite_supplier(stop):
    """Two explicit synthetic slots per team, mirroring the contained-profile
    suite's synthetic stand-ins; never a real credential."""
    return FiniteInMemoryApiKeySupplier(stop=stop,
        crypto_btc=('KEY-BTC-1', 'KEY-BTC-2'),
        crypto_eth=('KEY-ETH-1', 'KEY-ETH-2'))


def test_retained_fixture_is_the_calibrated_terminal_representation(retained_bytes):
    """The fixture bytes are exactly the 25-key terminal envelope the shared
    production decoder admits, with the retained capture's own metadata."""
    predecode = load_retained_document()['predecode']
    envelope = strict_json(retained_bytes.decode('utf-8'))
    assert set(envelope) == set(cli._TERMINAL_KEYS)
    assert sorted(envelope) == predecode['stdout_json_top_keys']
    assert predecode['stderr_bytes'] == 0
    assert envelope['type'] == 'result' and envelope['subtype'] == 'success'
    assert envelope['is_error'] is False and envelope['num_turns'] == 1
    assert envelope['stop_reason'] == 'end_turn'
    assert envelope['terminal_reason'] == 'completed'
    assert envelope['fast_mode_state'] == 'off'
    assert envelope['result'] == (
        '{"calls": [{"name": "search_evidence", '
        '"arguments_json": "{\\"query\\": \\"SYNTHETIC-PAL-MOCK-RESPONSE\\"}"}]}')
def test_contained_factory_decodes_retained_terminal_bytes(monkeypatch, tmp_path,
                                                            retained_bytes):
    """The exact retained bytes through the REAL contained wiring (v2 profile,
    finite supplier, team-scoped delayed key use) decode via the shared
    production decoder; no second admission decoder exists in this path."""
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop)
    contained = candidate(tmp_path, linux_launch=fixed_launch())
    calls = []

    def process(**kwargs):
        calls.append(kwargs)
        return ResearchProcessResult(retained_bytes, 0, 12)

    monkeypatch.setattr(cli, 'run_research_process', process)
    reply = bound_contained_factory(contained, supplier, stop)('crypto_btc') \
        .complete(messages_json='[{}]', max_output_tokens=100)
    assert_search_evidence_reply(reply)
    assert len(calls) == 1
    assert calls[0]['linux_launch'] is contained.linux_launch
    environment = dict(calls[0]['spec'].environment)
    assert environment['ANTHROPIC_API_KEY'] == 'KEY-BTC-1'
    assert environment['ANTHROPIC_BASE_URL'] == contained.endpoint_url
    assert supplier.remaining('crypto_btc') == 1
    assert supplier.remaining('crypto_eth') == 2


def replay_emitter_script(payload, delay=0.005):
    """The synthetic replay emitter (owned by this file): a real OS process
    that consumes the whole reviewed prompt, then writes the retained bytes
    to stdout in small irregular fragments with flushes between them."""
    sizes = (97, 1, 512, 13, 640, 211, 64, 300)
    return (
        'import sys,time\n'
        'data=sys.stdin.buffer.read()\n'
        'assert data.startswith(b\'{"schema_version":"research-claude-actions-v1"\')\n'
        'payload=%r\n'
        'sizes=%r\n'
        'pos=i=0\n'
        'while pos<len(payload):\n'
        '    c=min(sizes[i%%len(sizes)],len(payload)-pos)\n'
        '    sys.stdout.buffer.write(payload[pos:pos+c])\n'
        '    sys.stdout.buffer.flush()\n'
        '    pos+=c;i+=1\n'
        '    time.sleep(%.4f)\n'
        'sys.stdout.buffer.flush()\n'
        'sys.exit(0)\n') % (payload, sizes, delay)


def replay_emitter_spec(tmp_path, payload):
    """A real local-OS subprocess spec for the replay emitter; the contained
    relay itself is covered by the pipe slice and the native opt-in slice."""
    binary = Path(sys.executable).resolve()
    environment = tuple((key, os.environ[key]) for key in ('SYSTEMROOT', 'WINDIR')
                        if key in os.environ)
    return ResearchProcessSpec(
        (str(binary), '-I', '-S', '-c', replay_emitter_script(payload)),
        str(tmp_path), environment, sha256(binary.read_bytes()).hexdigest(), 20000)


def test_fragmented_real_process_reply_decodes_exactly(tmp_path, retained_bytes):
    """A real OS process delivers the retained bytes through the production
    runner in fragments; the client decodes them byte-exactly. The legacy
    local-OS runner is the only production runner this Windows host can
    execute; the contained relay path is proven by the pipe and native slices."""
    seen = []

    def prepare(request):
        seen.append(request)
        return replay_emitter_spec(tmp_path, retained_bytes)

    model = cli.ClaudeProcessModel(model_id=MODEL, prepare_command=prepare,
                                   allow_process_start=True)
    reply = model.complete(messages_json='[{}]', max_output_tokens=100)
    assert_search_evidence_reply(reply)
    assert len(seen) == 1 and list(tmp_path.iterdir()) == []
# ---------------------------------------------------------------------------
# Slice B - pipe-delivery path: the two-phase supervisor model-phase relay
# core over real OS anonymous pipes (portable), then native opt-in execution.
# ---------------------------------------------------------------------------

class _PipeSelectShim:
    """Windows readiness shim: select.select waits only on sockets there.

    Relay stdout/stderr fds are always reported readable (their reads are
    nonblocking, so spurious readiness becomes a caught BlockingIOError),
    while the report fd is reported only while an unread complete line is
    pending - the ready line never passes through the shim because the
    production loop consumes it with a direct blocking read before any
    select. Only the WAIT is replaced; every byte still moves through the
    production read/write/cap/protocol code over real OS pipes.
    """

    def __init__(self, report_fd):
        self.report_fd = report_fd
        self.report_pending = 0

    def select(self, rlist, wlist, xlist, timeout):
        time.sleep(0.0005)
        ready = [fd for fd in rlist if fd != self.report_fd
                 or self.report_pending > 0]
        if self.report_fd in ready:
            self.report_pending -= 1
        return ready, list(wlist), list(xlist)


class _RelaySupervisorStub:
    """Minimal supervisor object for the parent-side relay core."""

    def __init__(self):
        self.exited = False

    def poll(self):
        return 0 if self.exited else None


class _StubAdmission:
    def close(self):
        pass


def _supervisor_role(out_w, err_w, rep_w, cred_r, prom_r, shim, record, payload,
                     prompt, key, stderr_marker, banner):
    """The supervisor/vendor side of the model phase on real pipes: announce
    readiness, consume the one-use credential frame, drain the prompt to EOF,
    then relay the terminal bytes as irregular fragments, report model_done,
    and finally deliver the last fragment AFTER the report (modeling the
    kernel-order arrival between two independent pipes that the final drain
    exists to collect). The version phase's banner bytes never enter these
    relay channels, exactly as in production."""
    os.write(rep_w, b'{"type":"ready"}\n')
    frame = bytearray()
    while len(frame) < 8 + len(key):
        block = os.read(cred_r, 8 + len(key) - len(frame))
        if not block:
            break
        frame.extend(block)
    os.close(cred_r)
    record['credential'] = bytes(frame)
    received = bytearray()
    while True:
        block = os.read(prom_r, 65536)
        if not block:
            break
        received.extend(block)
    record['prompt'] = bytes(received)
    sizes, off, index, head_end = (97, 1, 512, 13, 640, 211, 64, 300), 0, 0, \
        len(payload) - 40
    while off < head_end:
        chunk = min(sizes[index % len(sizes)], head_end - off)
        os.write(out_w, payload[off:off + chunk])
        off += chunk
        index += 1
        time.sleep(0.0005)
    if stderr_marker is not None:
        os.write(err_w, stderr_marker)
    shim.report_pending += 1
    os.write(rep_w, b'{"type":"model_done","code":null,"exit_code":0}\n')
    time.sleep(0.002)
    os.write(out_w, payload[head_end:])
    os.close(out_w)
    os.close(err_w)
    record['banner'] = banner


def _run_relay_core(payload, prompt, key, stderr_marker):
    """Drive the REAL parent-side model-phase relay core (run_model_phase ->
    _drain_model -> _final_drain) over real anonymous pipes; on Windows the
    readiness wait goes through the pipe-safe shim, on Linux the real select
    runs unpatched."""
    request = cli.ClaudeExecInput(MODEL, '[{}]', 100)
    assert prompt == request.prompt_json.encode('utf-8')
    banner = fixed_launch().expected_version_output.encode('utf-8')
    # Synthetic never-executed identity for the relay-core spec; abspath keeps
    # the path absolute on both POSIX and Windows (never a drive-less root).
    spec = ResearchProcessSpec(
        (os.path.abspath('/nonexistent/vendor/claude'), '--print'),
        os.path.abspath('/nonexistent/work'),
        (('HOME', os.path.abspath('/nonexistent/home')),),
        'd' * 64, 30000)
    shim = _PipeSelectShim(None)
    record = {}
    pipes = [os.pipe() for _ in range(7)]
    (ctrl_r, ctrl_w), (out_r, out_w), (err_r, err_w), (rep_r, rep_w), \
        (live_r, live_w), (prom_r, prom_w), (cred_r, cred_w) = pipes
    shim.report_fd = rep_r
    if os.name == 'nt':
        os.set_blocking(out_r, False)
        os.set_blocking(err_r, False)
    thread = threading.Thread(target=_supervisor_role,
        args=(out_w, err_w, rep_w, cred_r, prom_r, shim, record, payload,
              prompt, key, stderr_marker, banner))
    thread.start()
    session = linux._ContainedSession.__new__(linux._ContainedSession)
    session._spec = spec
    session._stop = None
    session._deadline = time.monotonic_ns() + 30_000_000_000
    session._prompt_w = prom_w
    session._credential_w = cred_w
    session._control_w = ctrl_w
    session._stdout_r = out_r
    session._stderr_r = err_r
    session._report_r = rep_r
    session._liveness_w = live_w
    session._supervisor = _RelaySupervisorStub()
    session._admission = _StubAdmission()
    session._credential = key
    real_select = linux.select
    if os.name == 'nt':
        linux.select = shim
    try:
        output, stderr_bytes = session.run_model_phase(prompt)
    finally:
        linux.select = real_select
        thread.join(timeout=10)
        session._supervisor.exited = True
        session._cleanup(1000)
    for fd in (ctrl_r, live_r, rep_w):
        try:
            os.close(fd)
        except OSError:
            pass
    return output, stderr_bytes, record, request, banner
def test_model_phase_relay_delivers_terminal_bytes_unmodified(retained_bytes):
    """Fragmented then final draining through the real relay core preserves
    the terminal bytes exactly: no version or control bytes injected, byte
    equality at the receive end, one-use credential framing, prompt byte
    conservation, and the relayed bytes decode through the shared decoder."""
    request = cli.ClaudeExecInput(MODEL, '[{}]', 100)
    prompt = request.prompt_json.encode('utf-8')
    key = 'SYNTHETIC-NOT-A-REAL-KEY'
    output, stderr_bytes, record, _request, banner = _run_relay_core(
        retained_bytes, prompt, key, None)
    assert output == retained_bytes
    assert len(output) == 1671
    assert sha256(output).hexdigest() == sha256(retained_bytes).hexdigest()
    assert stderr_bytes == 0
    # No version or control bytes are injected into the relayed model stdout.
    assert banner not in output
    assert b'2.1.278' not in output
    assert b'CONF ' not in output and b'MODEL ' not in output
    # The one-use credential crossed the model-phase pipe with its bounded
    # framing, and only after readiness released it.
    assert record['credential'] == len(key).to_bytes(8, 'big') + key.encode('utf-8')
    # Prompt byte conservation on the relay's input side.
    assert record['prompt'] == prompt
    # Composition: the relayed bytes decode through the shared decoder.
    assert_search_evidence_reply(cli.decode_claude_result(
        ResearchProcessResult(output, stderr_bytes, 7), request=request,
        call_number=1))


def test_model_phase_relay_counts_stderr_and_the_decoder_rejects_it(retained_bytes):
    """The relay tolerates nonzero guest stderr as transport (counted, never
    stored), keeps stdout byte-exact, and the shared decoder still rejects the
    reply at the admission boundary: transport and admission stay separated."""
    request = cli.ClaudeExecInput(MODEL, '[{}]', 100)
    prompt = request.prompt_json.encode('utf-8')
    marker = b'RELAY-STDERR-MARKER\n'
    output, stderr_bytes, record, _request, _banner = _run_relay_core(
        retained_bytes, prompt, 'SYNTHETIC-NOT-A-REAL-KEY', marker)
    assert output == retained_bytes
    assert stderr_bytes == len(marker)
    with pytest.raises(ValueError, match='research_claude_response_invalid'):
        cli.decode_claude_result(
            ResearchProcessResult(output, stderr_bytes, 7), request=request,
            call_number=1)
    assert record['prompt'] == prompt


# ---------------------------------------------------------------------------
# Slice C - rejection matrix through the same contained wiring (portable)
# ---------------------------------------------------------------------------

def _defective_result(retained_bytes, defect):
    """Representative rejected replies, built from the retained envelope."""
    envelope = strict_json(retained_bytes.decode('utf-8'))
    if defect == 'truncated-half':
        return ResearchProcessResult(retained_bytes[:836], 0, 5)
    if defect == 'truncated-tail-cut':
        # Cutting only the trailing newline leaves valid JSON; removing the
        # final closing brace as well makes the truncation genuinely invalid.
        return ResearchProcessResult(retained_bytes[:-2], 0, 5)
    if defect == 'nonzero-stderr':
        return ResearchProcessResult(retained_bytes, 17, 5)
    if defect == 'unknown-key':
        envelope['unreviewed_key'] = 0
        payload = json.dumps(envelope, ensure_ascii=True, separators=(',', ':'))
        return ResearchProcessResult(payload.encode('utf-8'), 0, 5)
    if defect == 'model-mismatch':
        usage = envelope['modelUsage'][MODEL]
        envelope['modelUsage'] = {'claude-other': usage}
        payload = json.dumps(envelope, ensure_ascii=True, separators=(',', ':'))
        return ResearchProcessResult(payload.encode('utf-8'), 0, 5)
    if defect == 'usage-disagreement':
        envelope['modelUsage'][MODEL]['inputTokens'] = 4
        payload = json.dumps(envelope, ensure_ascii=True, separators=(',', ':'))
        return ResearchProcessResult(payload.encode('utf-8'), 0, 5)
    raise AssertionError('unknown defect')
@pytest.mark.parametrize('defect', [
    'truncated-half', 'truncated-tail-cut', 'nonzero-stderr',
    'unknown-key', 'model-mismatch', 'usage-disagreement',
])
def test_rejection_matrix_rejects_without_repair_or_retry(monkeypatch, tmp_path,
                                                           retained_bytes, defect):
    """Every representative defect rejects through the same contained factory
    wiring; the runner is entered exactly once (no repair, no retry), the
    client is closed after the failure, and the consumed supplier slot stays
    consumed."""
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop)
    contained = candidate(tmp_path, linux_launch=fixed_launch())
    calls = []

    def process(**kwargs):
        calls.append(kwargs)
        return _defective_result(retained_bytes, defect)

    monkeypatch.setattr(cli, 'run_research_process', process)
    model = bound_contained_factory(contained, supplier, stop)('crypto_btc')
    with pytest.raises(ValueError, match='research_claude_call_failed'):
        model.complete(messages_json='[{}]', max_output_tokens=100)
    assert len(calls) == 1
    assert supplier.remaining('crypto_btc') == 1
    with pytest.raises(ValueError, match='research_claude_client_stopped'):
        model.complete(messages_json='[{}]', max_output_tokens=100)
    assert len(calls) == 1
    assert supplier.remaining('crypto_btc') == 1
    assert supplier.remaining('crypto_eth') == 2


# ---------------------------------------------------------------------------
# Native opt-in slices - the real two-phase contained lifecycle (Linux only).
# These collect-and-skip by design on hosts that cannot run the Linux-only
# relay primitives; under the explicit opt-in, missing prerequisites fail
# closed via the shared containment harness guard.
# ---------------------------------------------------------------------------

REPLAY_C_TEMPLATE = r'''
#include <string.h>
#include <unistd.h>
static const unsigned char PAYLOAD[] = {%s};
static const unsigned char VERSION[] = {%s};
static const char MARKER[] = "RELAY-STDERR-MARKER\n";
static const unsigned SIZES[] = {97u,1u,512u,13u,640u,211u,64u,300u};
static int write_all(const unsigned char *data, size_t length) {
    size_t done = 0;
    while (done < length) {
        ssize_t wrote = write(1, data + done, length - done);
        if (wrote <= 0) return 5;
        done += (size_t)wrote;
    }
    return 0;
}
int main(int argc, char **argv) {
    int i, noisy = 0;
    static char sink[65536];
    ssize_t n;
    size_t off;
    unsigned k = 0;
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--version") == 0)
            return write_all(VERSION, sizeof VERSION);
        if (strcmp(argv[i], "--pal-emit-stderr") == 0) noisy = 1;
    }
    while ((n = read(0, sink, sizeof sink)) > 0) { }
    off = 0;
    while (off < sizeof PAYLOAD) {
        size_t chunk = SIZES[k %% (sizeof SIZES / sizeof SIZES[0])];
        if (chunk > sizeof PAYLOAD - off) chunk = sizeof PAYLOAD - off;
        if (write_all(PAYLOAD + off, chunk) != 0) return 6;
        off += chunk;
        k++;
        if (off < sizeof PAYLOAD) usleep(2000);
    }
    if (noisy) {
        size_t done = 0;
        while (done < sizeof MARKER - 1) {
            ssize_t wrote = write(2, MARKER + done, sizeof MARKER - 1 - done);
            if (wrote <= 0) return 7;
            done += (size_t)wrote;
        }
    }
    return 0;
}
'''


def _replay_c_source(payload, version_line):
    def c_bytes(data):
        return ','.join('0x%02x' % byte for byte in data)
    return REPLAY_C_TEMPLATE % (c_bytes(payload), c_bytes(version_line))


def _compile_replay_vendor(directory, payload, launch):
    from tests.test_research_process_linux import _compile
    return _compile(directory, 'pal-replay-vendor',
                    _replay_c_source(payload,
                                     launch.expected_version_output.encode('utf-8')))


def _replay_vendor_spec(binary, digest, work, argv=()):
    return ResearchProcessSpec(
        (binary, '--print', '--bare', *argv), str(work),
        (('HOME', str(work / 'host-home')),
         ('CLAUDE_CONFIG_DIR', str(work / 'host-config')),
         ('ANTHROPIC_BASE_URL', 'https://gateway.example.invalid'),
         ('CLAUDE_CODE_MAX_OUTPUT_TOKENS', '8192'),
         ('ANTHROPIC_API_KEY', 'SYNTHETIC-NOT-A-REAL-KEY')), digest, 30000)
@pytest.mark.skipif(not CONTAINMENT_ENABLED,
                    reason='explicit native containment proof is opt-in')
def test_native_contained_relay_delivers_retained_terminal_bytes(tmp_path,
                                                                 retained_bytes):
    """The real bwrap/cgroup/memfd two-phase lifecycle replays the retained
    terminal bytes: the version phase admits the synthetic vendor banner and
    the model phase relays the fragmented terminal bytes to the parent with
    byte equality, zero stderr and one contained execution per phase."""
    require_native_containment()
    _standin, _digest, _size, launch = build_native_launch(tmp_path)
    vendor = tmp_path / 'replay'
    vendor.mkdir()
    binary, digest, size = _compile_replay_vendor(vendor, retained_bytes, launch)
    launch = relaunch(launch, vendor_size_bytes=size)
    work = tmp_path / 'work'
    work.mkdir()
    before = linux.LINUX_PHASE_COUNTERS.snapshot()
    result = run_research_process(spec=_replay_vendor_spec(binary, digest, work),
                                  stdin=cli.ClaudeExecInput(
                                      MODEL, '[{}]', 100).prompt_json.encode('utf-8'),
                                  allow_process_start=True, linux_launch=launch)
    after = linux.LINUX_PHASE_COUNTERS.snapshot()
    assert result.stdout == retained_bytes
    assert result.stderr_bytes == 0
    assert after['version_executions'] == before['version_executions'] + 1
    assert after['model_executions'] == before['model_executions'] + 1
    assert_search_evidence_reply(cli.decode_claude_result(
        result, request=cli.ClaudeExecInput(MODEL, '[{}]', 100), call_number=1))


@pytest.mark.skipif(not CONTAINMENT_ENABLED,
                    reason='explicit native containment proof is opt-in')
def test_native_contained_factory_composition_round_trip(tmp_path, retained_bytes):
    """Full composition natively: contained v2 profile -> real factory with
    the finite team supplier -> real two-phase contained execution of the
    synthetic replay vendor -> shared decoder; the retained reply arrives
    with its exact action, call id and 26-token total."""
    require_native_containment()
    _standin, _digest, _size, launch = build_native_launch(tmp_path)
    vendor = tmp_path / 'replay'
    vendor.mkdir()
    binary, digest, size = _compile_replay_vendor(vendor, retained_bytes, launch)
    launch = relaunch(launch, vendor_size_bytes=size)
    work = tmp_path / 'work'
    work.mkdir()
    base = candidate(tmp_path)
    contained = replace(
        base, process=replace(base.process, argv=(binary,),
                              executable_sha256=digest, cwd=str(work)),
        linux_launch=launch)
    stop = ResearchDispatchStop()
    supplier = finite_supplier(stop)
    reply = bound_contained_factory(contained, supplier, stop)('crypto_btc') \
        .complete(messages_json='[{}]', max_output_tokens=100)
    assert_search_evidence_reply(reply)
    assert supplier.remaining('crypto_btc') == 1
    assert supplier.remaining('crypto_eth') == 2


@pytest.mark.skipif(not CONTAINMENT_ENABLED,
                    reason='explicit native containment proof is opt-in')
def test_native_contained_stderr_noise_rejects_at_the_decoder(tmp_path,
                                                              retained_bytes):
    """Guest stderr noise is transported and counted, never stored; stdout
    stays byte-exact and the shared decoder rejects the reply."""
    require_native_containment()
    _standin, _digest, _size, launch = build_native_launch(tmp_path)
    vendor = tmp_path / 'replay'
    vendor.mkdir()
    binary, digest, size = _compile_replay_vendor(vendor, retained_bytes, launch)
    launch = relaunch(launch, vendor_size_bytes=size)
    work = tmp_path / 'work'
    work.mkdir()
    result = run_research_process(
        spec=_replay_vendor_spec(binary, digest, work, argv=('--pal-emit-stderr',)),
        stdin=b'{}', allow_process_start=True, linux_launch=launch)
    assert result.stdout == retained_bytes
    assert result.stderr_bytes == len(b'RELAY-STDERR-MARKER\n')
    request = cli.ClaudeExecInput(MODEL, '[{}]', 100)
    with pytest.raises(ValueError, match='research_claude_response_invalid'):
        cli.decode_claude_result(result, request=request, call_number=1)
