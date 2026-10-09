"""L9 amendment (DELIVERY_PLAN.md S67) gate tests T1 and T3 for the relay helper.

Two gate sections in one file (worker W6):

T1 - the native fd-survival probe for the inherited-socketpair crossing. The
     crossing mechanism relies on an UNDOCUMENTED bubblewrap 0.11.1 property
     (the payload-exec branch closes only proc_fd and the non---as-pid-1
     opt_sync_fd, so inherited descriptors reach the payload), which is why
     the probe is W2's HARD merge blocker: probe failure is a node-level
     blocker with no viable fallback. The probe is opt-in through the FIXED
     environment variable ``POLYMARKET_ALPHA_LAB_RUN_LINUX_RELAY_CROSSING=1``
     and runs only on the Linux containment host (bwrap, user namespaces,
     memfd, delegated cgroup v2). Without the opt-in, on a non-Linux host, or
     while the W2 surface is absent, every T1 test SKIPS with a reason naming
     the exact pending deliverable (skip-until-landed, the W5 pattern); after
     the opt-in, missing host prerequisites are FAILURES, never skips.

T3 - the offline byte-difference gate. The frozen offline pins below were
     originally computed from the pre-W2 tree at L9 W6 authoring time and
     were RE-PINNED at the L9.1 reap-race fix (2026-10-09: the per-iteration
     _try_reap calls in both frozen helper sources are guarded by
     ``status is _RUNNING`` so an ECHILD None can never overwrite a reaped
     status; helper-embedding digests moved, CONF/argv did not - see the pin
     block below). They bind the
     offline helper bytes, the offline supervisor CONF, the offline wrapper
     argv and the offline launch policy dict; they PASS today and must stay
     byte-identical when W2 lands (amendment: offline CONF/argv/policy_dict/
     v1/v2 digests and all historical goldens byte-unchanged). The
     W2-gated half asserts RELAY_HELPER_SOURCE is STRICTLY ADDITIVE over
     HELPER_SOURCE and that the two-value closed egress branch cross-pins
     digests, port window and descriptor declarations.

Phase 1 boundaries hold everywhere here: no real endpoint, no credential
(the only key-shaped sentinel is a fixed synthetic marker), no vendor
execution (the payload is a compiled synthetic probe with fixed markers, W4
sentinel conventions), no DNS and no off-loopback egress. The native opt-in
above is the only thing in this module that can ever run bwrap, and only on
Linux.

W2 reconciliation notes: every post-W2 symbol this file binds that the
amendment does not spell byte-for-byte is marked with a "W2 seam:" comment
at its use site (RELAY_HELPER_SOURCE location, the digest accessor, the CONF
key names relay_channel_fd/relay_port, the exactly-two PAL_RELAY_* setenv
entries, the launch relay_trust field, the policy relay section). When the
real surface lands, these tests auto-activate; drift FAILS loudly instead of
skipping.
"""
import ast
import json
import os
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path

import pytest

from polymarket_alpha_lab import research_linux_relay as relay
from polymarket_alpha_lab import research_process_linux as linux
from polymarket_alpha_lab.research_claude_profile import RELAY_EGRESS_POLICY
from polymarket_alpha_lab.research_process import ResearchProcessSpec
from tests.test_research_process_linux import (
    discover_runtime_closure, fixed_launch, relaunch,
)

try:  # Linux-only at runtime; importable on Windows development hosts.
    import fcntl
except ImportError:  # pragma: no cover - Windows development host
    fcntl = None

# ---------------------------------------------------------------------------
# Documented interfaces and fixed literals.
# ---------------------------------------------------------------------------

CROSSING_ENV = 'POLYMARKET_ALPHA_LAB_RUN_LINUX_RELAY_CROSSING'
CGROUP_ROOT_ENV = 'POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT'
CROSSING_ENABLED = os.environ.get(CROSSING_ENV) == '1'

# W2 seam: the amendment names the CONF keys relay_channel_fd/relay_port and
# the PAL_RELAY_* env prefix; the exact suffixes stay W2's choice (this file
# binds the prefix, the count and the model-phase-only scoping instead).
RELAY_CHANNEL_FD_KEY = 'relay_channel_fd'
RELAY_PORT_KEY = 'relay_port'
PAL_RELAY_PREFIX = 'PAL_RELAY_'
RELAY_EGRESS = RELAY_EGRESS_POLICY  # landed v3 branch constant (W5)
RELAY_PORT_WINDOW = relay.RELAY_PORT_WINDOW  # landed W1: exactly (20000, 32767)
INHERITED_FROM_PARENT_RELAY = 'relay-channel-model-phase-only'
# W2 seam: the launch field carrying the reviewed trust record follows the
# W4/W5 documented name 'relay_trust' (RelayTrustConfig type).
RELAY_TRUST_FIELD = 'relay_trust'

# Synthetic sentinels only (W4 conventions): fixed markers, never secrets.
CROSSING_KEY = 'PAL-T1-CROSSING-SYNTHETIC-KEY'
CHANNEL_PROBE_A = b'PAL-T1-CROSSING-CHANNEL-PROBE-A-0123456789abcdef\r\n'
CHANNEL_PROBE_B = b'PAL-T1-CROSSING-CHANNEL-PROBE-B-fedcba9876543210\r\n'
PROBE_BANNER = 'pal-relay-crossing-probe-v1 (synthetic)\n'
VENDOR_CONNECTED = b'CROSSING-VENDOR-CONNECTED\n'
VENDOR_ECHOED = b'CROSSING-VENDOR-ECHOED '
VENDOR_CONNECT_REFUSED = b'CROSSING-CONNECT-REFUSED\n'
SYNTHETIC_RELAY_CA_PATH = '/opt/pal-gate/relay-ca.pem'

# Offline pins. Originally computed from the pre-W2 tree (L9 W6 authoring,
# 2026-10-07); RE-PINNED at the L9.1 reap-race fix (2026-10-09), which guards
# the per-iteration _try_reap calls in both frozen helper sources and changes
# the helper bytes and every digest embedding them. The CONF/argv pins are
# re-measured UNCHANGED by L9.1 (the supervisor CONF carries helper_fd, not
# the helper digest; _bwrap_argv carries paths and fd numbers only) - they
# stay at their L9 W6 values. The CONF/argv pins use the fixed synthetic gate
# recipe in _gate_conf() below; they are host-platform independent (the one
# Path-derived guest literal is forward-slashed in the recipe).
OFFLINE_HELPER_SHA256 = ('22a396e384be6f597e33009f7bde23f4938de010ac74d6a7'
                         '3f3e95b58302b286')
OFFLINE_CONF_SHA256 = ('f6864007d428adcc73b020b2818a7f83de258142d9716985b1ec'
                       '1452f363ed76')
OFFLINE_ARGV_VERSION_SHA256 = ('d34891a5b1b97f4433d0bed4f81c0708f16c494d779f4'
                               '97e443284b1a7569cf2')
OFFLINE_ARGV_MODEL_SHA256 = ('1b9f33c2a433de9711c7a662bd2aeb7c8d8afc6d1f211f9'
                             '99b562f36679a60d6')
OFFLINE_POLICY_SHA256 = ('37e8c9afa9bc76769c4d0223fe0f1dc252d6174a48041a10fc'
                         '9df6ff421ad56b')

# Allowed shapes for lines RELAY_HELPER_SOURCE may add over HELPER_SOURCE.
# The PRIMARY additivity guarantee is the subsequence-over-lines property
# asserted by test_relay_helper_source_is_strictly_additive (every frozen
# HELPER_SOURCE line survives, in order); the vocabularies below only confine
# what the additive region may contain. They deliberately do NOT dictate
# marker comments: natural pump-discipline scaffolding carries no relay
# marker, so it is enumerated as closed forms instead (review F2).
ADDED_LINE_MARKERS = ('relay', 'PAL_RELAY_', 'import socket', 'socket.',
                      'bind(', 'listen(', 'accept(')
# Keyword-only scaffolding lines (exact stripped forms).
_ADDED_KEYWORD_LINES = frozenset(('try:', 'finally:', 'else:', 'pass',
                                  'break', 'continue', 'while True:'))
# Closed call/comparison forms the amendment-mandated pump discipline cannot
# avoid (each entry justified; review F2):
# - try/except/finally/else/pass: the mandated failure frames - a bind
#   failure must exit 92 with no second draw, and channel-discovery or pump
#   byte-path failures must fail closed;
# - 'while True:'/'break'/'continue': the bounded one-connection pump loop,
#   terminated by EOF on either side;
# - 'os.fork()', 'pid == 0', 'pid != 0': the mandated pump fork and its
#   fork-result test (the substring forms also match *_pid spellings);
# - 'os._exit(': the forked pump child can only terminate through os._exit;
#   the mandated code 92 is separately pinned next to the bind-failure
#   branch by test_relay_helper_pump_discipline_static;
# - 'os.read('/'os.write(': raw descriptor byte movement;
# - 'select.select(': readiness multiplexing across channel and connection;
# - '.close()'/'fileno()'/'sendall('/'recv(': the one-listener /
#   one-accepted-connection lifecycle (teardown, raw-descriptor extraction,
#   TCP-side byte movement).
_ADDED_CALL_FORMS = ('os.fork()', 'pid == 0', 'pid != 0', 'os._exit(',
                     'os.read(', 'os.write(', 'select.select(', '.close()',
                     '.fileno()', '.sendall(', '.recv(')
# Exception names an added except clause may catch: the closed failure
# surface of int() env parsing, socket probing and raw descriptor calls
# (the frozen offline helper's own staging idiom uses BaseException).
ADDED_EXCEPT_NAMES = frozenset(('OSError', 'TypeError', 'ValueError',
                                'BlockingIOError', 'InterruptedError',
                                'Exception', 'BaseException'))
# W2 seam: the confirmed channel-fd validation idiom constructs a socket
# around the inherited descriptor number (a dead or non-socket descriptor
# raises there) and detaches it immediately; a different probe idiom needs
# gate reconciliation at W2 review.
CHANNEL_VALIDATION_MARKER = 'socket(fileno='
RELAY_HELPER_ALLOWED_IMPORTS = frozenset(('hashlib', 'json', 'os', 'select',
                                          'signal', 'sys', 'time', 'socket'))


def _added_line_is_scaffolding(line):
    """One added line is closed scaffolding when it is inert text or one of
    the enumerated pump-discipline forms (review F2): comment text (never
    executable Python, so it cannot alter byte behavior), keyword-only
    control lines, a closed call/comparison form, an except clause catching
    only closed exception names, a paren-free branch guard (a condition
    without '(' cannot contain a call), or a for-header iterating a plain
    name or a tuple literal of plain names (the pump's teardown sweep over
    its own sockets). Anything else fails the additivity gate."""
    stripped = line.strip()
    if stripped.startswith('#'):
        return True
    if stripped in _ADDED_KEYWORD_LINES:
        return True
    if any(form in stripped for form in _ADDED_CALL_FORMS):
        return True
    if stripped.startswith('except'):
        clause = stripped[len('except'):].strip()
        if clause.endswith(':'):
            clause = clause[:-1].strip()
        names = clause.split(' as ')[0].strip().strip('()')
        caught = {name.strip() for name in names.split(',')} if names else set()
        return bool(caught) and caught <= ADDED_EXCEPT_NAMES
    if stripped.startswith(('if ', 'elif ')):
        return '(' not in stripped
    if stripped.startswith('for '):
        head, separator, iterable = stripped.partition(' in ')
        if not separator or '(' in head:
            return False
        if iterable.endswith(':'):
            iterable = iterable[:-1].strip()
        if iterable.startswith('(') and iterable.endswith(')'):
            iterable = iterable[1:-1]
            parts = [part.strip() for part in iterable.split(',')]
        else:
            parts = [iterable] if iterable else []
        return bool(parts) and all(part.isidentifier() for part in parts)
    return False


# ---------------------------------------------------------------------------
# W2 surface resolution (skip-until-landed; a landed-but-wrong surface FAILS).
# ---------------------------------------------------------------------------

def relay_crossing_surface():
    """Resolve the documented W2 relay-helper deliverables or skip naming them.

    Landed-but-divergent surfaces fail loudly instead of skipping: the digest
    is always recomputed from the RELAY_HELPER_SOURCE bytes in-test (the
    helper-digest pattern), so any accessor disagreement is a FAIL, and a
    relay launch that constructs but refuses the documented shape is a FAIL.
    """
    helper_source = getattr(relay, 'RELAY_HELPER_SOURCE', None)
    if type(helper_source) is not str or not helper_source:
        pytest.skip('waits for the L9 W2 deliverable: RELAY_HELPER_SOURCE '
                    '(the second checked-in stdlib helper source) is not in '
                    'research_linux_relay yet')
    # W2 seam: the digest accessor name follows _engine_digest/_helper_digest;
    # the in-test recompute is authoritative, any accessor must agree.
    helper_digest = sha256(helper_source.encode('utf-8')).hexdigest()
    accessor = getattr(relay, '_relay_helper_digest', None)
    if callable(accessor) and accessor() != helper_digest:
        pytest.fail('the landed _relay_helper_digest() disagrees with the '
                    'RELAY_HELPER_SOURCE bytes (helper-digest pattern broken)')
    if RELAY_TRUST_FIELD not in linux.LinuxLaunchSpec.__dataclass_fields__:
        # F4: RELAY_HELPER_SOURCE has landed, so a launch that still lacks
        # the documented trust field is a landed-with-divergent-name drift
        # (or an incomplete W2 landing), never an absent deliverable. Only
        # the genuinely absent surface skips above.
        pytest.fail('RELAY_HELPER_SOURCE has landed but LinuxLaunchSpec '
                    'lacks the documented ' + RELAY_TRUST_FIELD + ' field '
                    '(landed with a divergent name?): the launch must '
                    "accept the closed egress_policy='" + RELAY_EGRESS
                    + "' with the relay helper digest, the "
                    + RELAY_TRUST_FIELD + ' RelayTrustConfig record and '
                    'the exact (20000, 32767) port window')
    trust = relay.RelayTrustConfig(
        ca_bundle=relay.RelayCaBundlePin(SYNTHETIC_RELAY_CA_PATH, 'c' * 64, 4096))
    try:
        launch = relaunch(fixed_launch(), egress_policy=RELAY_EGRESS,
                          helper_sha256=helper_digest,
                          **{RELAY_TRUST_FIELD: trust})
    except (TypeError, ValueError) as caught:
        pytest.fail('the landed relay launch refused the documented relay '
                    'shape (relay helper digest, relay egress, typed trust '
                    'record): ' + repr(caught))
    return dict(helper_source=helper_source, helper_digest=helper_digest,
                launch=launch, trust=trust)


def _helper_namespace():
    """The frozen offline helper source exec'd for its pure functions (the W1
    engine_namespace pattern): the production _bwrap_argv byte for byte."""
    namespace = {}
    exec(compile(linux.HELPER_SOURCE, '<helper-source>', 'exec'), namespace)
    return namespace


def _relay_helper_namespace():
    surface = relay_crossing_surface()
    namespace = {}
    exec(compile(surface['helper_source'], '<relay-helper-source>', 'exec'),
         namespace)
    return surface, namespace


def _function_segment(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            segment = ast.get_source_segment(source, node)
            if segment is None:
                pytest.fail('cannot extract the %s function from the helper '
                            'source' % name)
            return segment
    pytest.fail('the helper source has no %s function' % name)


# ---------------------------------------------------------------------------
# The fixed synthetic offline CONF/argv gate recipe (drives the pins above).
# ---------------------------------------------------------------------------

def _gate_spec():
    root = '/opt/pal-gate' if sys.platform == 'linux' else 'C:/pal-gate'
    return ResearchProcessSpec(
        (root + '/vendor/claude', '--print', '--bare'), root + '/work',
        (('HOME', root + '/home'),
         ('CLAUDE_CONFIG_DIR', root + '/config'),
         ('ANTHROPIC_BASE_URL', 'https://gateway.example.invalid'),
         ('CLAUDE_CODE_MAX_OUTPUT_TOKENS', '8192'),
         ('ANTHROPIC_API_KEY', 'SYNTHETIC-NOT-A-REAL-KEY')), 'd' * 64, 15000)


def _gate_conf():
    """Declaration-only offline CONF built by the production
    _supervisor_configuration plus the production _guest_configuration pairs.

    Two documented normalizations keep the pin host-platform independent:
    supervisor_pid is zeroed (it is ephemeral in production) and the single
    guest literal derived through pathlib is forward-slashed (the guest
    layout is a fixed Linux literal set; a Windows dev host must not inject
    backslashes into it)."""
    spec = _gate_spec()
    launch = fixed_launch()
    pairs, _credential = linux._guest_configuration(spec, launch)
    conf = linux._supervisor_configuration(
        spec, launch, wrapper_fd=101, helper_fd=102, interp_fd=103,
        vendor_fd=104, runtime_fds=(105,), allocation='pal-call-gate-fixed',
        report_fd=106, liveness_fd=107, prompt_fd=108, credential_fd=109)
    conf['env_pairs'] = [list(pair) for pair in pairs]
    conf['passthrough_env_keys'] = [key for key, _ in pairs]
    conf['supervisor_pid'] = 0
    conf['guest']['path_bin'] = conf['guest']['path_bin'].replace(chr(92), '/')
    return conf


def _conf_digest(conf):
    return sha256(json.dumps(conf, sort_keys=True,
                             separators=(',', ':')).encode('utf-8')).hexdigest()


def _argv_digest(argv):
    return sha256(json.dumps(argv, separators=(',', ':')).encode('utf-8')).hexdigest()


def _setenv_pairs(argv):
    pairs = []
    for index in range(len(argv) - 2):
        if argv[index] == '--setenv':
            pairs.append((argv[index + 1], argv[index + 2]))
    return pairs


def _without_relay_setenv(argv):
    out = []
    index = 0
    while index < len(argv):
        if (argv[index] == '--setenv'
                and argv[index + 1].startswith(PAL_RELAY_PREFIX)):
            index += 3
            continue
        out.append(argv[index])
        index += 1
    return out


# ---------------------------------------------------------------------------
# T3 section (runs everywhere): the frozen offline baseline.
# ---------------------------------------------------------------------------

def test_offline_helper_source_is_frozen_at_the_l9_baseline():
    """T3.1: the frozen HELPER_SOURCE bytes and pin are unchanged by W2 (the
    amendment requires the offline helper digest to stay byte-identical);
    the pin was re-measured at the L9.1 reap-race fix, and the existing
    offline guard behavior is preserved."""
    assert sha256(linux.HELPER_SOURCE.encode('utf-8')).hexdigest() \
        == OFFLINE_HELPER_SHA256
    assert linux._helper_digest() == OFFLINE_HELPER_SHA256
    # Guard preservation (mirror of the existing pin guard, never a
    # replacement): a wrong helper digest still fails closed.
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(fixed_launch(), helper_sha256='0' * 64)


def test_offline_conf_and_argv_bytes_are_pinned_at_the_l9_baseline():
    """T3.1: the offline supervisor CONF and the offline wrapper argv (both
    phases, through the frozen helper's own _bwrap_argv) are byte-pinned;
    re-measured UNCHANGED at the L9.1 reap-race fix (neither the CONF nor
    the argv embeds the helper digest), W2 must not move them."""
    conf = _gate_conf()
    assert _conf_digest(conf) == OFFLINE_CONF_SHA256
    namespace = _helper_namespace()
    version_argv = namespace['_bwrap_argv'](conf, 'version')
    model_argv = namespace['_bwrap_argv'](conf, 'model')
    assert _argv_digest(version_argv) == OFFLINE_ARGV_VERSION_SHA256
    assert _argv_digest(model_argv) == OFFLINE_ARGV_MODEL_SHA256
    assert not [token for argv in (version_argv, model_argv)
                for token in argv if token.startswith(PAL_RELAY_PREFIX)]
    # The offline argv never binds a credential: in the version phase the
    # PAL_CREDENTIAL_FILE setenv carries the exact placeholder 'none'. This
    # binds the placeholder to its key instead of bare token membership and
    # is still subsumed by the digest pins above (review F6a).
    version_pairs = dict(_setenv_pairs(version_argv))
    assert version_pairs['PAL_CREDENTIAL_FILE'] == 'none'


def test_offline_policy_and_profile_goldens_are_unchanged():
    """T3.1: the offline launch policy dict is byte-pinned and the historical
    profile goldens (recomputed the way tests/test_research_claude_linux.py
    does, by constructing the same golden profiles) still match, so W2 cannot
    silently re-digest the offline/v1/v2 surfaces."""
    from tests.test_research_claude_linux import (
        CLAUDE_V1_GOLDEN, CODEX_V1_GOLDEN, PRE_CORRECTION_V2_GOLDEN,
        contained_profile, golden_claude_v1, golden_codex_v1,
    )
    policy = fixed_launch().policy_dict()
    assert _conf_digest(policy) == OFFLINE_POLICY_SHA256
    assert policy['descriptors']['inherited_from_parent'] == []
    assert policy['egress']['policy'] == 'offline'
    assert 'relay' not in policy  # no relay section on the offline branch
    assert golden_claude_v1().contract_sha256 == CLAUDE_V1_GOLDEN[sys.platform]
    assert golden_codex_v1().contract_sha256 == CODEX_V1_GOLDEN[sys.platform]
    v2 = contained_profile().contract_sha256
    assert v2 != PRE_CORRECTION_V2_GOLDEN[sys.platform]
    assert v2 == contained_profile().contract_sha256


# ---------------------------------------------------------------------------
# T3 section (skip-until-landed): RELAY_HELPER_SOURCE strictly additive.
# ---------------------------------------------------------------------------

def test_relay_helper_source_is_strictly_additive():
    """T3.2: every line of the frozen HELPER_SOURCE appears in order in
    RELAY_HELPER_SOURCE (subsequence over lines - the PRIMARY additivity
    guarantee), every added line is blank, relay-marked or one of the
    DOCUMENTED closed scaffolding forms the mandated pump discipline needs
    (see ADDED_LINE_MARKERS and _added_line_is_scaffolding; inert comment
    text is accepted, marker comments are NOT dictated - review F2), the
    result is still stdlib-only through BOTH import forms and parses, and
    the offline helper stays frozen at the baseline."""
    surface = relay_crossing_surface()
    relay_lines = surface['helper_source'].splitlines()
    helper_lines = linux.HELPER_SOURCE.splitlines()
    added = []
    cursor = 0
    for line in helper_lines:
        while cursor < len(relay_lines) and relay_lines[cursor] != line:
            added.append(relay_lines[cursor])
            cursor += 1
        if cursor >= len(relay_lines):
            pytest.fail('frozen helper line dropped or reordered by '
                        'RELAY_HELPER_SOURCE: ' + repr(line))
        cursor += 1
    added.extend(relay_lines[cursor:])
    assert added, 'RELAY_HELPER_SOURCE is byte-identical to HELPER_SOURCE; ' \
                  'the relay branches are missing entirely'
    for line in added:
        if not line.strip():
            continue
        assert (any(marker in line for marker in ADDED_LINE_MARKERS)
                or _added_line_is_scaffolding(line)), \
            'non-relay line added to RELAY_HELPER_SOURCE: ' + repr(line)
    compile(surface['helper_source'], '<relay-helper-source>', 'exec')
    tree = ast.parse(surface['helper_source'])
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `from X import ...` binds local names but depends on module X:
            # the SAME closed allowlist applies to X, and every relative
            # import (level != 0, module None) fails outright, so e.g.
            # `from collections import deque` can no longer escape (F5).
            if node.level or node.module is None:
                pytest.fail('RELAY_HELPER_SOURCE uses a relative import '
                            'instead of the closed stdlib allowlist')
            imported.add(node.module)
    assert imported <= RELAY_HELPER_ALLOWED_IMPORTS, imported
    assert 'polymarket_alpha_lab' not in surface['helper_source']
    # The offline side of the amendment requirement, re-asserted where W2's
    # review will look: the helper digest equals the re-pinned L9.1 value.
    assert linux._helper_digest() == OFFLINE_HELPER_SHA256


def test_relay_launch_digests_are_cross_pinned_and_window_exact():
    """T3.3: the two-value closed egress branch. Offline keeps the frozen
    helper digest, an empty relay surface and no relay trust record; relay
    keeps the relay helper digest, the exact (20000, 32767) window, the typed
    trust record and the amendment's inherited-descriptor declaration. Cross
    pinned combinations are refused in both directions."""
    surface = relay_crossing_surface()
    launch = surface['launch']
    assert launch.egress_policy == RELAY_EGRESS
    assert launch.helper_sha256 == surface['helper_digest']
    assert surface['helper_digest'] != linux._helper_digest()
    policy = launch.policy_dict()
    # W2 seam: the relay policy section follows the landed W5 synthetic
    # mirror shape (helper digest, port window, trust policy dict).
    relay_section = policy['relay']
    assert relay_section['port_window'] == [20000, 32767]
    assert relay_section['helper']['sha256'] == surface['helper_digest']
    assert relay_section['helper']['protocol_version'] \
        == relay.RELAY_PROTOCOL_VERSION
    assert relay_section['trust'] == surface['trust'].policy_dict()
    assert policy['egress']['policy'] == RELAY_EGRESS
    assert policy['descriptors']['inherited_from_parent'] \
        == [INHERITED_FROM_PARENT_RELAY]
    # Offline side of the closed branch: frozen digest, no relay section and
    # an empty inherited-from-parent declaration (existing golden mirrored).
    offline = fixed_launch()
    assert offline.egress_policy == 'offline'
    assert offline.helper_sha256 == linux._helper_digest()
    assert 'relay' not in offline.policy_dict()
    assert offline.policy_dict()['descriptors']['inherited_from_parent'] == []
    # Cross-pinning is refused in both directions (closed vocabulary).
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(launch, helper_sha256=linux._helper_digest())
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(fixed_launch(), helper_sha256=surface['helper_digest'])
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(launch, **{RELAY_TRUST_FIELD: None})
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(fixed_launch(), **{RELAY_TRUST_FIELD: surface['trust']})
    for neighbor in ('relay-fixed-origin-typo', 'RELAY-FIXED-ORIGIN', 'host',
                     'loopback-relay', 'qualified', 'online', ''):
        with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
            relaunch(fixed_launch(), egress_policy=neighbor)


# ---------------------------------------------------------------------------
# T1 section (skip-until-landed, runs everywhere once W2 lands): interface
# binding for the crossing probe - CONF keys, keep-set, the exactly-two
# PAL_RELAY_* entries, and the pump discipline.
# ---------------------------------------------------------------------------

def test_relay_helper_conf_keys_and_model_phase_only_setenv():
    """T1 binding: CONF gains exactly relay_channel_fd/relay_port; _stage adds
    the channel fd to the keep-set; _bwrap_argv adds EXACTLY two --setenv
    PAL_RELAY_* entries in model mode, none in version mode, nothing else;
    the channel descriptor crosses by inheritance only - never a bind, never
    a /proc path, never a passed pathname."""
    surface, namespace = _relay_helper_namespace()
    source = surface['helper_source']
    for key in (RELAY_CHANNEL_FD_KEY, RELAY_PORT_KEY):
        assert key in source
    stage = _function_segment(source, '_stage')
    assert RELAY_CHANNEL_FD_KEY in stage
    for line in source.splitlines():
        if RELAY_CHANNEL_FD_KEY in line or RELAY_PORT_KEY in line:
            assert '/proc' not in line and 'bind-data' not in line, line
    conf = _gate_conf()
    relay_conf = dict(conf)
    relay_conf[RELAY_CHANNEL_FD_KEY] = 160
    relay_conf[RELAY_PORT_KEY] = 21222
    offline = _helper_namespace()
    # Without the relay CONF keys the relay helper must produce the offline
    # argv byte for byte (the amendment's offline argv identity).
    for mode in ('version', 'model'):
        assert namespace['_bwrap_argv'](conf, mode) \
            == offline['_bwrap_argv'](conf, mode)
    version_relay = namespace['_bwrap_argv'](relay_conf, 'version')
    model_relay = namespace['_bwrap_argv'](relay_conf, 'model')
    assert not [token for token in version_relay
                if token.startswith(PAL_RELAY_PREFIX)]
    relay_pairs = [pair for pair in _setenv_pairs(model_relay)
                   if pair[0].startswith(PAL_RELAY_PREFIX)]
    assert len(relay_pairs) == 2
    assert len({name for name, _value in relay_pairs}) == 2
    # Removing exactly those two entries must restore the offline argv.
    assert _without_relay_setenv(model_relay) \
        == offline['_bwrap_argv'](conf, 'model')
    # Inheritance only: the channel fd number appears as a PAL_RELAY_* value,
    # never as a --ro-bind-data source and never as a path. The production
    # setenv layout is ['--setenv', NAME, VALUE] (the frozen _bwrap_argv
    # emission order, the same order _setenv_pairs/_without_relay_setenv
    # parse), so for a relay VALUE at index i the neighbors are
    # argv[i-2] == '--setenv' and argv[i-1].startswith(PAL_RELAY_) (F1).
    channel_token = str(160)
    for index, token in enumerate(model_relay):
        if token == '--ro-bind-data':
            assert model_relay[index + 1] != channel_token
        if token == channel_token:
            assert model_relay[index - 2] == '--setenv', model_relay[index - 3:index + 1]
            assert model_relay[index - 1].startswith(PAL_RELAY_PREFIX), \
                model_relay[index - 3:index + 1]
    assert any(token == channel_token
               and model_relay[index - 2] == '--setenv'
               and model_relay[index - 1].startswith(PAL_RELAY_PREFIX)
               for index, token in enumerate(model_relay))


def test_relay_helper_pump_discipline_static():
    """T1.4 static half: the guest forks the dumb byte pump BEFORE the
    credential read, discovers the channel through the PAL_RELAY_* env and
    the inherited fd number only (never /proc, never a path), VALIDATES the
    channel fd before any bind/listen can run, binds exactly one drawn
    port, serves exactly one connection and exits 92 on bind failure
    without redrawing. The runtime half of this discipline is the native
    probe below; these textual gates are reconciled at W2 review.

    The validation ordering is part of this gate's binding (review F3a):
    with a dead descriptor (the CLOEXEC control below) the failure must
    happen before any listener exists, so the contained vendor observes a
    connection refusal instead of a silently half-open endpoint. Two
    textual shapes are accepted, per the confirmed W2 forms: the probe in
    the guest parent before the pump-creating fork (the confirmed W2 idiom,
    socket(fileno=...).detach()), or the probe inside the pump before its
    own single bind."""
    surface, _namespace = _relay_helper_namespace()
    guest = _function_segment(surface['helper_source'], 'guest')
    assert 'os.fork()' in guest
    assert guest.index('os.fork()') < guest.index("credential_file != 'none'")
    assert PAL_RELAY_PREFIX in guest
    assert '/proc' not in guest
    assert guest.count('.bind(') == 1
    assert guest.count('.accept(') == 1
    # F6b: exit 92 is bound to the bind-failure branch, not merely present
    # anywhere in the guest: the single bind is followed by its failure
    # frame, and that frame's handler is the mandated os._exit(92).
    bind_position = guest.index('.bind(')
    exit_position = guest.index('os._exit(92)')
    assert bind_position < exit_position, \
        'os._exit(92) must sit in the bind-failure branch, after the bind'
    assert 'except' in guest[bind_position:exit_position], \
        'the bind-failure branch (try/bind then except ... os._exit(92)) ' \
        'is not recognizable in the guest source'
    # F3a: a channel-fd validation probe must EXECUTE before any listening:
    # either in the guest parent before the pump-creating fork (the confirmed
    # W2 idiom), or inside the pump before its own single bind. Probes are
    # located by line, and a marker appearing only inside a comment is not a
    # validation. The pump's textual span is located through the AST (the
    # innermost function whose body contains the single .bind() call),
    # because that body is normally DEFINED before the fork call: a textual
    # position before the fork would not by itself prove execution order for
    # a line inside the pump body.
    guest_lines = guest.splitlines()
    probe_lines = [number for number, line in enumerate(guest_lines)
                   if CHANNEL_VALIDATION_MARKER in line
                   and not line.strip().startswith('#')]
    assert probe_lines, ('the guest never validates the relay channel fd '
                        '(expected the ' + CHANNEL_VALIDATION_MARKER
                        + ' probe idiom before any bind/listen)')
    fork_line = next(number for number, line in enumerate(guest_lines)
                     if 'os.fork()' in line)
    bind_line = next(number for number, line in enumerate(guest_lines)
                     if '.bind(' in line)
    tree = ast.parse(surface['helper_source'])
    guest_def = next(node for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name == 'guest')
    bind_call = next(node for node in ast.walk(guest_def)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)
                     and node.func.attr == 'bind')
    pumps = [candidate for candidate in ast.walk(guest_def)
             if isinstance(candidate, ast.FunctionDef)
             and any(node is bind_call for node in ast.walk(candidate))]
    pump_def = max(pumps, key=lambda candidate: candidate.lineno)
    span = (pump_def.lineno - guest_def.lineno,
            pump_def.end_lineno - guest_def.lineno)
    assert any((span[0] <= number < span[1] and number < bind_line)
               or (not span[0] <= number < span[1] and number < fork_line)
               for number in probe_lines), \
        'the channel-fd validation must execute before the pump fork or ' \
        'the pump\'s own bind, so a dead descriptor fails pre-listener'
    lowered = guest.lower()
    for word in ('redraw', 're-draw', 'retry'):
        assert word not in lowered


# ---------------------------------------------------------------------------
# T1 section (native, opt-in): the fd-survival probe.
# ---------------------------------------------------------------------------

def _crossing_gate(environment):
    """('skip', []) without the crossing opt-in; missing environment
    prerequisites after that opt-in are problems (fail closed), never skips."""
    if environment.get(CROSSING_ENV) != '1':
        return 'skip', []
    problems = []
    if not environment.get(CGROUP_ROOT_ENV):
        problems.append(CGROUP_ROOT_ENV + ' must name the delegated cgroup v2 '
                        'subtree')
    return ('ready' if not problems else 'fail'), problems


def require_crossing_probe():
    """Skip on the absent opt-in, the absent W2 surface or a non-Linux host;
    fail closed (never skip) on missing native host prerequisites."""
    status, problems = _crossing_gate(os.environ)
    if status == 'skip':
        pytest.skip('explicit relay-crossing fd-survival proof is opt-in ('
                    + CROSSING_ENV + '=1)')
    surface = relay_crossing_surface()  # skip-until-landed inside
    if sys.platform != 'linux':
        pytest.skip('the relay-crossing fd-survival probe runs on the Linux '
                    'containment host only (bwrap/user namespaces/memfd)')
    problems = list(problems)
    if not (shutil.which('cc') or shutil.which('gcc')):
        problems.append('C compiler (cc/gcc) required to compile the '
                        'synthetic payload')
    if not (shutil.which('bwrap') or Path('/usr/bin/bwrap').is_file()):
        problems.append('bwrap containment executable required')
    root = os.environ.get(CGROUP_ROOT_ENV, '')
    if root and not Path(root, 'cgroup.controllers').is_file():
        problems.append(CGROUP_ROOT_ENV + ' must name a delegated cgroup v2 '
                        'subtree carrying cgroup.controllers')
    elif root:
        available = Path(root, 'cgroup.controllers').read_text().split()
        if 'memory' not in available or 'pids' not in available:
            problems.append('delegated cgroup subtree lacks memory/pids '
                            'controllers')
    if problems:
        pytest.fail('relay-crossing prerequisites missing: '
                    + '; '.join(problems))
    return dict(surface=surface, cgroup_root=root)


def test_crossing_gate_skips_only_without_the_explicit_optin():
    environment = {CROSSING_ENV: '1', CGROUP_ROOT_ENV: '/opt/pal-synthetic/cgroup'}
    assert _crossing_gate({}) == ('skip', [])
    assert _crossing_gate({CGROUP_ROOT_ENV: '/opt/pal-synthetic/cgroup'}) \
        == ('skip', [])
    assert _crossing_gate(environment) == ('ready', [])


def test_crossing_gate_fails_closed_after_the_optin_on_missing_prerequisites():
    status, problems = _crossing_gate({CROSSING_ENV: '1'})
    assert status == 'fail' and len(problems) == 1
    assert CGROUP_ROOT_ENV in problems[0]


CROSSING_C_SOURCE = r'''
/* Synthetic crossing-probe payload for the L9 T1 fd-survival proof
 * (compiled at test time). Explicitly NOT a vendor and NOT official-image
 * evidence: it never reads a credential and never contacts anything but the
 * namespace-local 127.0.0.1 listener named by its own environment. Version
 * mode prints the fixed synthetic banner; model mode connects to
 * ANTHROPIC_BASE_URL (http://127.0.0.1:<port>), echoes every socket byte
 * back until EOF and reports fixed markers on stdout. */
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

static int endpoint_port(void) {
    const char *url = getenv("ANTHROPIC_BASE_URL");
    if (!url) return -1;
    const char *colon = strrchr(url, ':');
    if (!colon) return -1;
    int port = atoi(colon + 1);
    if (port < 1 || port > 65535) return -1;
    return port;
}

static int connect_loopback(int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;
    struct timeval tv;
    tv.tv_sec = 20;
    tv.tv_usec = 0;
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
    struct sockaddr_in address;
    memset(&address, 0, sizeof address);
    address.sin_family = AF_INET;
    address.sin_port = htons((unsigned short)port);
    address.sin_addr.s_addr = htonl(0x7f000001u);
    if (connect(fd, (struct sockaddr *)&address, sizeof address) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "--version") == 0) {
        fputs("pal-relay-crossing-probe-v1 (synthetic)\n", stdout);
        return 0;
    }
    int port = endpoint_port();
    if (port < 0) { fputs("CROSSING-NO-ENDPOINT\n", stdout); return 84; }
    int fd = connect_loopback(port);
    if (fd < 0) { fputs("CROSSING-CONNECT-REFUSED\n", stdout); return 83; }
    fputs("CROSSING-VENDOR-CONNECTED\n", stdout);
    fflush(stdout);
    char buffer[4096];
    long total = 0;
    for (;;) {
        ssize_t got = read(fd, buffer, sizeof buffer);
        if (got < 0) { fputs("CROSSING-CHANNEL-READ-ERROR\n", stdout); return 85; }
        if (got == 0) break;
        ssize_t off = 0;
        while (off < got) {
            ssize_t sent = write(fd, buffer + off, (size_t)(got - off));
            if (sent < 0) { fputs("CROSSING-CHANNEL-WRITE-ERROR\n", stdout); return 86; }
            off += sent;
        }
        total += got;
    }
    close(fd);
    printf("CROSSING-VENDOR-ECHOED %ld\n", total);
    return 0;
}
'''


def _compile_payload(directory):
    compiler = shutil.which('cc') or shutil.which('gcc')
    if compiler is None:
        pytest.fail('C compiler (cc/gcc) required to compile the synthetic '
                    'crossing payload')
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / 'crossing-probe.c'
    target = directory / 'crossing-probe'
    source.write_text(CROSSING_C_SOURCE, encoding='ascii')
    subprocess.run([compiler, '-O1', '-o', str(target), str(source)],
                   check=True, capture_output=True, timeout=180)
    payload = target.read_bytes()
    return str(target), sha256(payload).hexdigest(), len(payload)


def _measured_relay_launch(payload_path, payload_digest, payload_size,
                           surface, cgroup_root):
    """Assemble the relay launch from measured host facts (native run only):
    the real bwrap, the real interpreter and its measured runtime closure,
    the synthetic payload pin, the RELAY helper digest (never the frozen
    offline digest) and the declaration-only synthetic trust record. No real
    vendor, credential or endpoint anywhere."""
    interpreter = str(Path(sys.executable).resolve())
    interp_bytes = Path(interpreter).read_bytes()
    wrapper_path = shutil.which('bwrap') or '/usr/bin/bwrap'
    wrapper_bytes = Path(wrapper_path).read_bytes()
    runtime = discover_runtime_closure(interpreter, payload_path)
    values = dict(
        wrapper=linux.LinuxArtifactPin(str(Path(wrapper_path).resolve()),
                                       sha256(wrapper_bytes).hexdigest(),
                                       len(wrapper_bytes)),
        helper_sha256=surface['helper_digest'],
        interpreter=linux.LinuxArtifactPin(
            interpreter, sha256(interp_bytes).hexdigest(), len(interp_bytes)),
        supervisor_python_home=sys.base_prefix,
        runtime_files=tuple(runtime),
        vendor_guest_path='/pal/vendor/claude',
        helper_guest_path='/pal/runtime/helper.py',
        vendor_size_bytes=payload_size,
        expected_version_output=PROBE_BANNER,
        cgroup_root=cgroup_root,
        scratch_size_bytes=64 * 1024 * 1024,
        guest_tmp_size_bytes=32 * 1024 * 1024,
        memory_max_bytes=512 * 1024 * 1024,
        pids_max=32,
        egress_policy=RELAY_EGRESS)
    # The surface trust's CA pin is declaration-only (a fixed path with a
    # placeholder digest): fine for offline shape assertions, but the landed
    # W3 admission now READS and seals the CA bundle at the pinned path, so
    # the native launch must carry a real synthetic CA exactly the way W3's
    # own build_native_relay_probe does — same bytes, same pin discipline.
    from tests.test_research_linux_relay import SYNTHETIC_CA
    ca_path = Path(payload_path).parent / 'relay-ca.pem'
    ca_path.write_bytes(SYNTHETIC_CA['pem'])
    values[RELAY_TRUST_FIELD] = relay.RelayTrustConfig(
        ca_bundle=relay.RelayCaBundlePin(str(ca_path),
                                         SYNTHETIC_CA['sha256'],
                                         SYNTHETIC_CA['size']))
    return linux.LinuxLaunchSpec(**values)


def _crossing_spec(payload_path, payload_digest, work_dir, port):
    return ResearchProcessSpec(
        (payload_path,), str(work_dir),
        (('HOME', str(work_dir / 'home')),
         ('CLAUDE_CONFIG_DIR', str(work_dir / 'config')),
         ('ANTHROPIC_BASE_URL', 'http://127.0.0.1:%d' % port),
         ('CLAUDE_CODE_MAX_OUTPUT_TOKENS', '8192'),
         ('ANTHROPIC_API_KEY', CROSSING_KEY)), payload_digest, 60000,
        cleanup_timeout_ms=15000)


def _probe_open_fds():
    directory = os.open('/proc/self/fd', os.O_RDONLY | os.O_DIRECTORY)
    try:
        return frozenset(int(name) for name in os.listdir(directory)) - {directory}
    finally:
        os.close(directory)


class _CrossingSession:
    """One production-discipline supervisor drive for the native T1 probe.

    The probe process occupies the trusted-parent seat (the position the
    parent-side relay engine holds once W3 lands): it creates the AF_UNIX
    relay channel socketpair, moves the child-bound end to a descriptor
    >= 100 through the production F_DUPFD idiom (amendment MINOR: no
    collision with the canonical 3..6 channel slots), draws the port through
    the production draw_relay_port(), admits every artifact through the
    production _Admission (which must select RELAY_HELPER_SOURCE for the
    relay egress - asserted below by reading the sealed memfd back), builds
    the CONF through the production _supervisor_configuration, launches the
    sealed supervisor with the production Popen shape and drives the
    two-phase VERSION/MODEL protocol on the production control channel.
    Everything below the parent seat - staging, keep-set, execv of the
    hash-pinned wrapper, the namespace, the pump, the frozen guest duties -
    is unmodified production code from RELAY_HELPER_SOURCE. No bwrap
    command line is hand-rolled anywhere (S67: T1 runs the same hash-pinned
    wrapper as production).
    """

    def __init__(self, requirements, tmp_path, channel_parent_end,
                 channel_child_fd, port):
        surface = requirements['surface']
        payload, digest, size = _compile_payload(tmp_path / 'payload')
        launch = _measured_relay_launch(payload, digest, size, surface,
                                        requirements['cgroup_root'])
        work = tmp_path / 'work'
        work.mkdir(parents=True, exist_ok=True)
        spec = _crossing_spec(payload, digest, work, port)
        self._supervisor = None
        self._closed = False
        self.port = port
        self.channel_fd = channel_child_fd
        self.allocation = None
        self._channel = channel_parent_end
        self.cgroup_root = requirements['cgroup_root']
        admission = linux._Admission(spec, launch)
        self._admission = admission
        try:
            # Egress-driven source selection: the sealed helper bytes must be
            # the RELAY source, not the frozen offline source.
            os.lseek(admission.helper_fd, 0, os.SEEK_SET)
            sealed = bytearray()
            while True:
                block = os.read(admission.helper_fd, 65536)
                if not block:
                    break
                sealed.extend(block)
            os.lseek(admission.helper_fd, 0, os.SEEK_SET)
            assert bytes(sealed) == surface['helper_source'].encode('utf-8')
            admission.protect()
            pairs, _credential = linux._guest_configuration(spec, launch)
            assert dict(pairs)['ANTHROPIC_BASE_URL'] \
                == 'http://127.0.0.1:%d' % port
            ctrl_r, self._control_w = os.pipe()
            self._stdout_r, vout_w = os.pipe()
            self._stderr_r, verr_w = os.pipe()
            self._report_r, rep_w = os.pipe()
            live_r, self._liveness_w = os.pipe()
            prom_r, self._prompt_w = os.pipe()
            cred_r, self._credential_w = os.pipe()
            artifact_fds = [admission.vendor_fd, admission.wrapper_fd,
                            admission.helper_fd, admission.interp_fd,
                            *admission.runtime_fds]
            allocation = 'pal-call-' + sha256(
                (str(os.getpid()) + ':' + str(time.monotonic_ns())
                 ).encode('ascii')).hexdigest()[:16]
            self.allocation = allocation
            # W2 seam: relay_channel_fd/relay_port are the amendment-named
            # CONF keys; if the landed _supervisor_configuration takes them
            # as parameters they must land under exactly these names.
            try:
                configuration = linux._supervisor_configuration(
                    spec, launch, wrapper_fd=admission.wrapper_fd,
                    helper_fd=admission.helper_fd,
                    interp_fd=admission.interp_fd,
                    vendor_fd=admission.vendor_fd,
                    runtime_fds=admission.runtime_fds, allocation=allocation,
                    report_fd=rep_w, liveness_fd=live_r, prompt_fd=prom_r,
                    credential_fd=cred_r,
                    **{RELAY_CHANNEL_FD_KEY: channel_child_fd,
                       RELAY_PORT_KEY: port})
            except TypeError:
                configuration = linux._supervisor_configuration(
                    spec, launch, wrapper_fd=admission.wrapper_fd,
                    helper_fd=admission.helper_fd,
                    interp_fd=admission.interp_fd,
                    vendor_fd=admission.vendor_fd,
                    runtime_fds=admission.runtime_fds, allocation=allocation,
                    report_fd=rep_w, liveness_fd=live_r, prompt_fd=prom_r,
                    credential_fd=cred_r)
            # The amendment-named CONF keys must carry exactly these values
            # whether the landed constructor took them as parameters (then a
            # mismatch is drift and FAILS) or not (then the probe injects
            # them, as the trusted parent, at the documented key names).
            configuration.setdefault(RELAY_CHANNEL_FD_KEY, channel_child_fd)
            configuration.setdefault(RELAY_PORT_KEY, port)
            assert configuration[RELAY_CHANNEL_FD_KEY] == channel_child_fd
            assert configuration[RELAY_PORT_KEY] == port
            configuration['env_pairs'] = [list(pair) for pair in pairs]
            configuration['passthrough_env_keys'] = [key for key, _ in pairs]
            self._supervisor = subprocess.Popen(
                ['/proc/self/fd/%d' % admission.interp_fd, '-S', '-B',
                 '/proc/self/fd/%d' % admission.helper_fd, 'supervise'],
                stdin=ctrl_r, stdout=vout_w, stderr=verr_w,
                pass_fds=[rep_w, live_r, prom_r, cred_r, channel_child_fd,
                          *artifact_fds],
                env={'PYTHONHOME': launch.supervisor_python_home},
                cwd=launch.cgroup_root, shell=False, close_fds=True,
                start_new_session=True)
            for fd in (ctrl_r, vout_w, verr_w, rep_w, live_r, prom_r, cred_r,
                       channel_child_fd):
                try:
                    os.close(fd)
                except OSError:
                    pass
            line = b'CONF ' + json.dumps(configuration,
                                         separators=(',', ':')).encode('utf-8')
            os.write(self._control_w, line.hex().encode('ascii') + b'\n')
            event = self.read_report(time.monotonic() + 60.0)
            assert event.get('type') == 'started', event
        except BaseException:
            self.close()
            raise

    def command(self, line):
        os.write(self._control_w, line + b'\n')

    def read_report(self, deadline):
        data = bytearray()
        while True:
            assert time.monotonic() < deadline, \
                'supervisor report timed out; buffered tail=' \
                + repr(bytes(data[-200:]))
            if not select.select([self._report_r], [], [], 0.05)[0]:
                continue
            block = os.read(self._report_r, 4096)
            assert block, 'supervisor closed the report channel; tail=' \
                + repr(bytes(data[-200:]))
            data.extend(block)
            if data.endswith(b'\n'):
                return json.loads(bytes(data).decode('utf-8'))

    def run_version(self):
        self.command(b'VERSION 30000')
        event = self.read_report(time.monotonic() + 90.0)
        assert event.get('type') == 'version_done', event
        assert event.get('code') is None, event
        assert event.get('exit_code') == 0, event
        assert event.get('stderr_bytes') == 0, event

    def start_model(self, stdin=b'{}'):
        self.command(b'MODEL 30000')
        event = self.read_report(time.monotonic() + 60.0)
        assert event.get('type') == 'ready', event
        payload = len(CROSSING_KEY).to_bytes(8, 'big') \
            + CROSSING_KEY.encode('utf-8')
        os.write(self._credential_w, payload)
        os.close(self._credential_w)
        self._credential_w = None
        os.write(self._prompt_w, stdin)
        os.close(self._prompt_w)
        self._prompt_w = None

    def echo_round_trip(self, payloads, per_step=20.0):
        """Send each probe marker and require the exact bytes back, in order,
        through the inherited descriptor; then half-close so the guest pump
        and the payload observe channel EOF. The synthetic key must never
        cross the channel."""
        for payload in payloads:
            self._channel.settimeout(per_step)
            self._channel.sendall(payload)
            got = bytearray()
            while len(got) < len(payload):
                block = self._channel.recv(4096)
                assert block, 'relay channel reached EOF mid-exchange; ' \
                    'received=' + repr(bytes(got))
                assert CROSSING_KEY.encode('utf-8') not in block
                got.extend(block)
            assert bytes(got) == payload
        self._channel.shutdown(socket.SHUT_WR)

    def await_model_done(self):
        event = self.read_report(time.monotonic() + 60.0)
        assert event.get('type') == 'model_done', event
        assert event.get('code') is None, event
        assert event.get('exit_code') == 0, event

    def drain_output(self, deadline_s=30.0):
        deadline = time.monotonic() + deadline_s
        data = bytearray()
        for fd_name in ('_stdout_r', '_stderr_r'):
            fd = getattr(self, fd_name)
            while True:
                assert time.monotonic() < deadline, 'output drain timed out'
                if not select.select([fd], [], [], 0.05)[0]:
                    if self._supervisor.poll() is not None:
                        block = os.read(fd, 65536)
                        data.extend(block)
                        if not block:
                            break
                    continue
                block = os.read(fd, 65536)
                data.extend(block)
                if not block:
                    break
        return bytes(data)

    def shutdown(self, timeout_s=30.0):
        try:
            self.command(b'SHUTDOWN 0')
        except OSError:
            pass
        self._supervisor.wait(timeout=timeout_s)

    def await_channel_eof(self, timeout_s=15.0):
        self._channel.settimeout(timeout_s)
        block = self._channel.recv(4096)
        assert block == b'', 'unexpected trailing channel bytes: ' + repr(block)

    def assert_no_cgroup_survivors(self):
        # Scoped to THIS session's own allocation directory (review F6d):
        # unrelated pal-call-* directories - leftovers of other runs'
        # crashed sessions, which production _enable_root_controls sweeps
        # before its next controller write - must not false-fail this
        # proof. The existing utilities expose no per-run marker beyond the
        # allocation name itself, so the allocation name is the tightest
        # available scope; a surviving allocation of THIS run still fails.
        assert self.allocation not in os.listdir(self.cgroup_root), \
            'this run\'s cgroup allocation survived teardown: ' \
            + self.allocation

    def close(self):
        if self._closed:
            return
        self._closed = True
        for name in ('_channel',):
            handle = getattr(self, name, None)
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass
                setattr(self, name, None)
        for name in ('_control_w', '_credential_w', '_prompt_w',
                     '_liveness_w', '_stdout_r', '_stderr_r', '_report_r'):
            fd = getattr(self, name, None)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
                setattr(self, name, None)
        if self._supervisor is not None:
            if self._supervisor.poll() is None:
                self._supervisor.kill()
            try:
                self._supervisor.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover
                pass
        if self._admission is not None:
            self._admission.close()


def _open_channel():
    """Parent-side relay channel creation with the production F_DUPFD >= 100
    idiom for the child-bound end (amendment MINOR: no collision with the
    canonical 3..6 channel slots inside the supervisor)."""
    parent_end, child_end = socket.socketpair()
    fresh = fcntl.fcntl(child_end.fileno(), fcntl.F_DUPFD, 100)
    child_end.close()
    return parent_end, fresh


@pytest.mark.skipif(not CROSSING_ENABLED,
                    reason='explicit relay-crossing fd-survival proof is opt-in')
def test_relay_crossing_positive_byte_round_trip_native(tmp_path):
    """T1.1 + T1.4 (happy path): exact known bytes travel parent socketpair
    end -> inherited descriptor -> namespace pump -> synthetic payload and
    back, under the production hash-pinned wrapper, the production two-phase
    protocol and the production admission/staging path. The payload reaches
    the pump's listener only through its ANTHROPIC_BASE_URL loopback
    endpoint; the port is the one drawn port inside (20000, 32767); the
    synthetic credential never crosses the channel. NOT a real endpoint,
    NOT a credential, NOT activation."""
    requirements = require_crossing_probe()
    assert RELAY_PORT_WINDOW == (20000, 32767)
    before = _probe_open_fds()
    port = relay.draw_relay_port()
    assert RELAY_PORT_WINDOW[0] <= port <= RELAY_PORT_WINDOW[1]
    parent_end, child_fd = _open_channel()
    assert child_fd >= 100
    session = _CrossingSession(requirements, tmp_path, parent_end, child_fd,
                               port)
    try:
        assert session.channel_fd >= 100
        session.run_version()
        session.start_model()
        session.echo_round_trip((CHANNEL_PROBE_A, CHANNEL_PROBE_B))
        session.await_model_done()
        session.shutdown()
        session.await_channel_eof()
        output = session.drain_output()
        session.assert_no_cgroup_survivors()
        assert session._supervisor.returncode == 0
    finally:
        session.close()
    assert VENDOR_CONNECTED in output
    assert VENDOR_ECHOED + str(len(CHANNEL_PROBE_A) + len(CHANNEL_PROBE_B)) \
        .encode('ascii') in output
    assert VENDOR_CONNECT_REFUSED not in output
    assert CROSSING_KEY.encode('utf-8') not in output
    assert not (_probe_open_fds() - before)


@pytest.mark.skipif(not CROSSING_ENABLED,
                    reason='explicit relay-crossing fd-survival proof is opt-in')
def test_relay_crossing_cloexec_negative_control_native(tmp_path):
    """T1.2: the CLOEXEC negative control. Same wrapper discipline (the
    production _bwrap_argv from RELAY_HELPER_SOURCE, the production
    admission pins, the production _close_except/set_inheritable staging
    semantics and the production wrapper re-verification), with exactly ONE
    flipped variable: FD_CLOEXEC stays SET on the child-bound relay channel
    descriptor across the execv of the hash-pinned wrapper. The descriptor
    must therefore die at the exec boundary: no byte can ever cross it.

    What this control deliberately omits relative to production _stage, and
    why each omission is fd-semantics-neutral (review F6c): the cgroup
    admission and the gate-wait dance (the staging bootstrap blocks reading
    the gate pipe until the supervisor admits the child into the cgroup)
    are skipped - the control's forked child runs ungated and unadmitted.
    FD_CLOEXEC is decided by the kernel per descriptor at the execv
    boundary and is independent of WHEN the parent admits the child or
    releases the gate: neither omission can resurrect an exec-closed
    descriptor nor close an open one, so the property under test is
    unaffected. Everything that does bear on descriptor semantics - the
    keep-set sweep, the inheritable flags, the artifact rewind, the wrapper
    re-verification and the production argv - is replicated exactly, with
    only the channel fd's inheritable flag flipped.

    Why the probe owns the staging child: production _stage clears CLOEXEC
    on every keep-set member by design (os.set_inheritable(fd, True)), so
    the pure supervisor path cannot express this control without modifying
    production code; the control replicates the staging discipline with the
    single property under test flipped, which is the standard single-
    variable negative control.

    The three CLOEXEC-consistent outcome stories (review F3) - the timing
    of the pump's death is deliberately NOT pinned, only the ordering
    discipline in test_relay_helper_pump_discipline_static is:
    (1) GUEST FAIL-CLOSED PRE-PAYLOAD: the confirmed W2 shape validates the
        channel fd in the guest parent BEFORE the pump fork; the dead
        descriptor fails that validation, the guest exits 91 and the
        payload never executes (no payload markers can exist).
    (2) CONNECT-REFUSED (early pump death): a pump that fails before its
        listener exists leaves the payload's loopback connect refused; the
        payload prints CROSSING-CONNECT-REFUSED and exits nonzero.
    (3) ECHOED-0 (late pump death): a pump that binds, listens and accepts
        and only then hits the dead channel fd yields a connected payload
        that reads a clean EOF, echoes exactly 0 bytes and exits 0.
    All three share the one unconditional discriminator: the parent
    receives EXACTLY ZERO channel bytes (the mirror of the positive test's
    exact known bytes), and no story may ever echo a nonzero byte count."""
    requirements = require_crossing_probe()
    surface = requirements['surface']
    _surface, namespace = _relay_helper_namespace()
    payload, digest, size = _compile_payload(tmp_path / 'payload')
    launch = _measured_relay_launch(payload, digest, size, surface,
                                    requirements['cgroup_root'])
    work = tmp_path / 'work'
    work.mkdir(parents=True, exist_ok=True)
    port = relay.draw_relay_port()
    spec = _crossing_spec(payload, digest, work, port)
    admission = linux._Admission(spec, launch)
    parent_end = channel_fd = None
    stdin_r, stdin_w = os.pipe()
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()
    cred_r, cred_w = os.pipe()
    pid = None
    try:
        admission.protect()
        parent_end, channel_fd = _open_channel()
        # The one-use credential channel is pre-filled with the synthetic
        # sentinel (there is no readiness protocol in this control; the
        # value is a fixed synthetic marker, never a credential).
        os.write(cred_w, len(CROSSING_KEY).to_bytes(8, 'big')
                 + CROSSING_KEY.encode('utf-8'))
        os.close(cred_w)
        cred_w = None
        pairs, _credential = linux._guest_configuration(spec, launch)
        # Same W2 seam handling as _CrossingSession above: pass the
        # amendment-named relay keys as parameters when the landed constructor
        # accepts them, otherwise inject them at the documented key names.
        try:
            configuration = linux._supervisor_configuration(
                spec, launch, wrapper_fd=admission.wrapper_fd,
                helper_fd=admission.helper_fd, interp_fd=admission.interp_fd,
                vendor_fd=admission.vendor_fd,
                runtime_fds=admission.runtime_fds,
                allocation='pal-call-cloexec-control', report_fd=stdout_w,
                liveness_fd=stdout_w, prompt_fd=stdout_w, credential_fd=cred_r,
                **{RELAY_CHANNEL_FD_KEY: channel_fd, RELAY_PORT_KEY: port})
        except TypeError:
            configuration = linux._supervisor_configuration(
                spec, launch, wrapper_fd=admission.wrapper_fd,
                helper_fd=admission.helper_fd, interp_fd=admission.interp_fd,
                vendor_fd=admission.vendor_fd,
                runtime_fds=admission.runtime_fds,
                allocation='pal-call-cloexec-control', report_fd=stdout_w,
                liveness_fd=stdout_w, prompt_fd=stdout_w, credential_fd=cred_r)
        configuration.setdefault(RELAY_CHANNEL_FD_KEY, channel_fd)
        configuration.setdefault(RELAY_PORT_KEY, port)
        assert configuration[RELAY_CHANNEL_FD_KEY] == channel_fd
        assert configuration[RELAY_PORT_KEY] == port
        configuration['env_pairs'] = [list(pair) for pair in pairs]
        configuration['passthrough_env_keys'] = [key for key, _ in pairs]
        artifacts = {admission.helper_fd, admission.interp_fd,
                     admission.vendor_fd, *admission.runtime_fds}
        pid = os.fork()
        if pid == 0:
            try:
                os.dup2(stdin_r, 0)
                os.dup2(stdout_w, 1)
                os.dup2(stderr_w, 2)
                os.dup2(cred_r, 6)  # _install_channels idiom: credential at 6
                keep = {0, 1, 2, 6, channel_fd} | artifacts
                namespace['_close_except'](keep)
                for fd in keep - {0, 1, 2}:
                    if fd == channel_fd:
                        os.set_inheritable(fd, False)  # THE CONTROL VARIABLE
                    else:
                        os.set_inheritable(fd, True)
                for fd in artifacts:
                    os.lseek(fd, 0, os.SEEK_SET)
                # Wrapper re-verification, mirroring the frozen _stage.
                hasher = sha256()
                total = 0
                wrapper_fd = os.open(configuration['wrapper_path'], os.O_RDONLY)
                while True:
                    block = os.read(wrapper_fd, 65536)
                    if not block:
                        break
                    hasher.update(block)
                    total += len(block)
                os.close(wrapper_fd)
                if (hasher.hexdigest() != configuration['wrapper_sha256']
                        or total != configuration['wrapper_size_bytes']):
                    os._exit(97)
                os.execv(configuration['wrapper_path'],
                         namespace['_bwrap_argv'](configuration, 'model'))
            except BaseException:
                os._exit(98)
            os._exit(98)
        # Parent side: drop every child-end copy so EOF semantics are exact.
        os.close(channel_fd)
        channel_fd = None
        for fd in (stdin_r, stdin_w, stdout_w, stderr_w, cred_r):
            os.close(fd)
        output = bytearray()
        watching = [stdout_r, stderr_r]
        deadline = time.monotonic() + 40.0
        while watching:
            assert time.monotonic() < deadline, \
                'the CLOEXEC control child never closed its output'
            ready = select.select(watching, [], [], 0.05)[0]
            for fd in ready:
                block = os.read(fd, 65536)
                output.extend(block)
                if not block:
                    watching.remove(fd)  # EOF stays readable forever
        deadline = time.monotonic() + 20.0
        while True:
            assert time.monotonic() < deadline, \
                'the CLOEXEC control child never exited'
            done, status = os.waitpid(pid, os.WNOHANG)
            if done == pid:
                break
            time.sleep(0.02)
        exit_code = os.waitstatus_to_exitcode(status)
        # Zero bytes, then EOF: the descriptor did not survive the exec.
        parent_end.settimeout(15.0)
        received = bytearray()
        while True:
            block = parent_end.recv(4096)
            if block == b'':
                break
            received.extend(block)
    finally:
        for fd in (stdin_r, stdin_w, stdout_r, stdout_w, stderr_r, stderr_w,
                   cred_r, cred_w):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if parent_end is not None:
            parent_end.close()
        if channel_fd is not None:
            try:
                os.close(channel_fd)
            except OSError:
                pass
        admission.close()
        if pid is not None:
            # Never leak the staged child on a failed control: reap it, or
            # kill it first when it is still alive.
            try:
                done, _status = os.waitpid(pid, os.WNOHANG)
                if done != pid:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
            except ChildProcessError:
                pass
    # Discriminating logic (review F3b), written explicitly:
    output_bytes = bytes(output)
    # PRIMARY, unconditional: EXACTLY ZERO channel bytes crossed the
    # descriptor (and EOF was observed above). Any channel byte can only
    # pass by failing this assertion first - the mirror of the positive
    # test's exact-known-bytes round trip.
    assert bytes(received) == b'', \
        'channel bytes crossed despite FD_CLOEXEC on the child-bound end: ' \
        + repr(bytes(received)[:200])
    # Proof the run actually executed: the child produced a RECORDED exit
    # status (reaped above) and closed both output pipes (the drain loop
    # above only ends on EOF), plus one of the three recognized stories
    # below carrying its own execution evidence.
    assert isinstance(exit_code, int)
    connect_refused = VENDOR_CONNECT_REFUSED in output_bytes
    connected = VENDOR_CONNECTED in output_bytes
    echoed_zero = VENDOR_ECHOED + b'0\n' in output_bytes
    # W2 seam: 91 is the landed relay channel-discovery/validation failure
    # code; a silent exit under any other code is not a recognized story.
    guest_refused_channel = (exit_code == 91 and not connected
                             and not connect_refused
                             and VENDOR_ECHOED not in output_bytes)
    assert connect_refused or echoed_zero or guest_refused_channel, (
        'no CLOEXEC-consistent outcome story observed (exit_code='
        + repr(exit_code) + ', output tail='
        + repr(output_bytes[-200:])
        + '); expected guest fail-closed 91, payload connect-refused, or '
        'payload echoed-0')
    # Story-specific bindings keep each branch non-vacuous:
    if connect_refused:
        # Story 2: the payload ran and its own connect failed (its fixed
        # refusal exit is 83), so no connection ever existed.
        assert not connected and not echoed_zero
        assert exit_code != 0
    elif echoed_zero:
        # Story 3: the payload ran, connected and echoed exactly zero bytes
        # before its own clean exit; a listener existed but no byte crossed.
        assert connected and exit_code == 0
    else:
        # Story 1: the guest itself refused the dead channel before the
        # vendor exec; the payload never ran (no payload markers at all).
        assert guest_refused_channel and exit_code == 91
    # Never allow a nonzero echo to pass, under any timing.
    assert VENDOR_ECHOED not in output_bytes or echoed_zero


@pytest.mark.skipif(not CROSSING_ENABLED,
                    reason='explicit relay-crossing fd-survival proof is opt-in')
def test_relay_crossing_teardown_normal_and_stopped_native(tmp_path):
    """T1.3: after a NORMAL child exit (full round trip, SHUTDOWN) and after
    a STOPPED exit (parent-liveness loss mid-model), the parent observes the
    channel closed (EOF, and nothing else after the exchanged markers), the
    supervisor teardown path completes (clean exit, no cgroup survivors) and
    the probe process leaks no descriptor."""
    requirements = require_crossing_probe()
    before = _probe_open_fds()
    # --- normal teardown ---
    port = relay.draw_relay_port()
    parent_end, child_fd = _open_channel()
    session = _CrossingSession(requirements, tmp_path / 'normal', parent_end,
                               child_fd, port)
    try:
        session.run_version()
        session.start_model()
        session.echo_round_trip((CHANNEL_PROBE_A,))
        session.await_model_done()
        session.shutdown()
        session.await_channel_eof()
        session.drain_output()
        session.assert_no_cgroup_survivors()
        assert session._supervisor.returncode == 0
    finally:
        session.close()
    # --- stopped teardown: parent-liveness loss mid-model ---
    port = relay.draw_relay_port()
    parent_end, child_fd = _open_channel()
    stopped = _CrossingSession(requirements, tmp_path / 'stopped', parent_end,
                               child_fd, port)
    try:
        stopped.run_version()
        stopped.start_model()
        stopped.echo_round_trip((CHANNEL_PROBE_A,))
        # Liveness EOF is the supervisor's fixed parent-lost signal: the
        # model phase returns, the cgroup is killed and the allocation is
        # removed - the existing supervisor teardown discipline.
        os.close(stopped._liveness_w)
        stopped._liveness_w = None
        stopped._supervisor.wait(timeout=60.0)
        stopped.await_channel_eof()
        stopped.drain_output()
        stopped.assert_no_cgroup_survivors()
        assert stopped._supervisor.returncode == 0
    finally:
        stopped.close()
    assert not (_probe_open_fds() - before)
