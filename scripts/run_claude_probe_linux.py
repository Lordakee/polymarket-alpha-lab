"""L7 outer probe runner: admission, boundary enforcement, bounded evidence export.

This script is the narrowly scoped OUTER runner of plan step 3 (codex-verdict.md)
plus amendments A1-A3. It executes NOTHING itself except the reviewed bwrap
wrapper and the already-downloaded official IMAGE bytes: it never downloads,
authenticates, contacts a provider, reads credentials, or performs any external
I/O. The inner official pipeline (official-probe.sh -> pytest six-case entry ->
tests/claude_cli_probe.py -> loopback HTTP + official CLI in the same netns) is
launched inside one rootless bwrap 0.11.1 namespace behind one delegated-cgroup
gate. Generation of the plan is scripts/claude_probe_environment.py's job; this
runner only consumes a validated plan.

Pipeline implemented here (plan step 3)::

    admission (measure + seal)            gate                    supervision
    IMAGE six-key manifest  ─┐
    environment-manifest     ├─ verify    workload cgroup         hold + drain
    runtime bind closure    ─┘  sha256    memory.max 4 GiB        /proc/<pid>/root
    bwrap 0.11.1 identity      bytes     swap.max 0               export <= 64 MiB
    setuid/setgid/caps                    pids.max 64             exclusive no-follow
    rejected                               readback BEFORE release
                                                   │
    teardown: close hold pipe -> cgroup.kill -> reap direct child -> verified-empty
              cgroup.procs -> resource-limit event check (memory.events/pids.events)

Single source of truth: the namespace-plan v2 JSON emitted by the reviewed
``official-config --platform linux`` generator (schema
``research-linux-launch-v2``). v1 plans (``claude-probe-namespace-linux-v1``,
generation-only, unenforced resources, writable host OUTPUT) are REFUSED with a
fixed code. The consumed schema is exactly the generator's: top-level keys
schema/generation/runner/image/namespaces/network/mounts/export/launcher/
runtime_binds/runtime_layout/environment/modes/excluded_host_surfaces/argv/
bounds/official_cli_executed/activation_authorized, with six ordered mounts
(INPUT/IMAGE/CONTROL read-only binds; OUTPUT/SCRATCH/TMP sized tmpfs using
bwrap 0.11.1's ``--size N --tmpfs PATH``; OUTPUT carries
``host_role: export_destination`` and an ``export`` section that pins the HOST
EXPORT DESTINATION, 64 MiB bound, exclusive no-follow creation, never mounted
writable into the namespace), a REQUIRED ``launcher`` block
``{path, sha256, bytes}`` naming the host twin of the guest
``/pal-control/official-probe.sh`` final command for BOTH launcher modes (the
on-disk file must be a regular non-symlink, mode exactly 0755, whose measured
digest and length equal the block; it is re-measured after the drain and a
divergence fails acceptance), every runtime bind enumerated as
``{guest, mode: ro, source, sha256, bytes}`` at canonical guest paths, a clean
``environment.setenv`` (PATH pinned to /usr/bin:/bin), pinned ``bounds``
(memory 4096 MiB, swap 0, pids 64, deadline 900 s), and the plan's ``argv``
equal to the runner's canonical reconstruction (fixed flag order; sorted
--setenv; ``--tmpfs /`` empty guest root; ro-binds; three sized tmpfs mounts;
runtime binds sorted by guest path; tail == the official-six command; no ip
command anywhere).

Two documented deviations are applied when EXECUTING, never when validating:

D1 (sealing choice): the verified official IMAGE member is measured once, then
    sealed into an immutable memfd (F_SEAL_ALL, mode 0555) and bound into the
    namespace as ``--ro-bind /proc/self/fd/<N> <image guest path>`` replacing
    the plan's pathname bind of the IMAGE DIRECTORY (the sealed member replaces
    the whole-directory bind; image-manifest.json is not needed inside the
    namespace). bwrap 0.11.1 supports /proc/self/fd bind sources, so the
    executed bytes are the sealed snapshot and are immune to host pathname
    substitution after admission. bwrap itself is executed by its measured,
    resolved, non-setuid absolute pathname (never a PATH re-lookup). The
    runtime closure and the payload tree cannot be sealed this way
    (directory-sized, multi-file), so every file bind and the payload
    inventory are hash-verified at admission and the IMAGE pathname is
    re-measured once more after the drain; the CONTROL launcher twin carries
    its own required identity block and is likewise measured twice (at
    admission and post-drain), both measurements recorded in the run record.
D2 (holder): the selected mode's final command is wrapped in
    ``/bin/sh -c '<command>; status=$?; printf ... > /pal-output/pal-holder-status;
    IFS= read -r hold'`` using only shell builtins (the plan pins
    launcher_externals to shell builtins plus the payload Python), so the
    mount namespace stays alive after the workload finishes. The supervisor
    (outside the workload cgroup) then exports /pal-output through the trusted
    bounded channel (reading /proc/<member>/root/pal-output, creating files in
    the HOST EXPORT DESTINATION exclusively with O_CREAT|O_EXCL|O_NOFOLLOW,
    64 MiB aggregate cap, supervisor evidence names reserved) BEFORE any
    teardown. An interrupted or incomplete export fails acceptance.

Mode-selection surface (amendment A3, matching the generator's pinned modes):
the two launcher modes are DATA in the single plan JSON. The runner is invoked
with ``--mode qualify-version|official-six`` (also the API's ``mode``
argument); the selected mode's ``command``/``expected_banner``/
``synthetic_request`` are read from the plan. qualify-version runs exactly one
official version invocation by replacing the plan argv's final command with
``modes[qualify-version].command`` (``<image guest> --version``) BEFORE and
INSTEAD OF the pytest entry, and requires the exact
``modes[qualify-version].expected_banner + newline`` on stdout plus clean
lifecycle; it gates the batch. official-six keeps the plan argv's final
command (the CONTROL launcher) unchanged and is accepted only on structural
evidence: launcher holder status 0, exported exit-code.txt 0, JUnit with
exactly six executed scenario testcases, zero skips/failures/errors, the exact
six-mode observation multiset with schema ``claude-cli-probe-v2`` and
``activation_authorized=false`` everywhere. The two modes are two separate
fresh runner attempts; ``depends_on`` is recorded, never auto-chained. A
signal death or infrastructure failure appears as a JUnit failure or a
nonzero exit and FAILS the case here; the runner records and gates, the
harness classifies.

Accepted-plan supersets beyond the generator's pinned emission (each exists
only so native qualification can drive the exact same execution path with a
stand-in interpreter; each is boundary-neutral because the boundary is
carried by the exact argv reconstruction plus the measured read-only binds,
and each is fail-closed — malformed shapes are refused with fixed codes):
1. qualify-version ``command`` may be any bounded token list whose first
   token is the sealed IMAGE executable (the generator pins
   ``[<image guest>, "--version"]``); one sealed-image invocation is still
   the enforced semantic.
2. ``runtime_layout.ld_library_path`` may be ``"ld_library_path_env"`` with a
   matching ``LD_LIBRARY_PATH`` setenv entry (the generator pins
   ``"not_used"`` and emits PATH only).
3. ``runtime_layout.library_search`` is accepted with any bounded list of
   absolute directories (the generator pins LINUX_RUNTIME_LIBRARY_DIRS); it
   is declaration metadata, never an executed search path.
4. ``environment.setenv`` may carry additional variables beyond PATH (still
   name/value-validated and cross-checked against the argv's --setenv pairs).
5. ``excluded_host_surfaces`` accepts any non-empty list of strings (the
   generator pins LINUX_EXCLUDED_SURFACES); it is documentation, not a mount
   decision.
The exact-shape compatibility test pins everything else to the generator's
actual constants.

Stop conditions (recorded in run-record.json, first failure preserved, no
retries): ``completed``, ``deadline_exceeded`` (outer deadline 900 s,
env-overridable upward only via POLYMARKET_ALPHA_LAB_LINUX_PROBE_RUNNER_TIMEOUT,
same raise-only pattern as POLYMARKET_ALPHA_LAB_PACKAGED_RECIPE_TIMEOUT),
``driver_lost`` (the CLI's driving stdin pipe closed), ``supervisor_error``,
plus admission/teardown/export/gate fixed failure codes in ``findings``.

Qualification tests live in tests/test_claude_probe_linux_execution.py. They
use synthetic stand-ins only and NEVER the official binary.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
try:  # Linux-only at runtime; importable on Windows development hosts.
    import fcntl
except ImportError:  # pragma: no cover - Windows development host
    fcntl = None
import json
import os
from pathlib import Path
import re
import select
import shutil
import stat
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

PLAN_SCHEMA = 'research-linux-launch-v2'
PLAN_SCHEMA_V1 = 'claude-probe-namespace-linux-v1'
PLAN_MAX_BYTES = 1048576
LAUNCHER_MODES = ('qualify-version', 'official-six')
SCENARIOS = ('invalid_action', 'rate_limit', 'server_error', 'success',
             'tool_use', 'truncated')
OBSERVATION_SCHEMA = 'claude-cli-probe-v2'
NAMESPACES = ('user', 'mount', 'pid', 'network', 'ipc', 'uts')
BWRAP_VERSION = '0.11.1'
IMAGE_MEMBER = 'claude'
IMAGE_VERSION = '2.1.278'
IMAGE_PLATFORM = 'linux-x86_64'
IMAGE_MANIFEST_NAME = 'image-manifest.json'
IMAGE_MANIFEST_KEYS = frozenset(('schema', 'path', 'sha256', 'bytes', 'version',
                                 'platform'))
IMAGE_MANIFEST_MAX_BYTES = 4096
IMAGE_MAX_BYTES = 536870912
ENVIRONMENT_MANIFEST_SCHEMA = 'claude-probe-environment-v1'
PAYLOAD_MANIFEST_MEMBER = 'environment-manifest.json'
PAYLOAD_MAX_FILES = 25000
PAYLOAD_MAX_BYTES = 1500000000
PAYLOAD_MAX_FILE = 150000000
RUNTIME_BIND_MAX = 512
RUNTIME_BIND_MAX_BYTES = 536870912
CHILD_ENV_MAX = 64
MEMORY_MAX_BYTES = 4294967296
MEMORY_SWAP_MAX_BYTES = 0
PIDS_MAX = 64
SCRATCH_BYTES = 1073741824
TMP_BYTES = 536870912
OUTPUT_BYTES = 67108864
EXPORT_CAP_BYTES = 67108864
DEFAULT_DEADLINE_SECONDS = 900
DEADLINE_ENV = 'POLYMARKET_ALPHA_LAB_LINUX_PROBE_RUNNER_TIMEOUT'
CGROUP_ROOT_ENV = 'POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT'
GUEST_INPUT = '/pal-input'
GUEST_IMAGE_DIR = '/pal-claude-image'
GUEST_IMAGE = '/pal-claude-image/claude'
GUEST_CONTROL = '/pal-control'
GUEST_CONTROL_LAUNCHER = 'official-probe.sh'
GUEST_OUTPUT = '/pal-output'
GUEST_SCRATCH = '/pal-scratch'
GUEST_SH = '/bin/sh'
HOLDER_STATUS_NAME = 'pal-holder-status'
EXIT_CODE_NAME = 'exit-code.txt'
JUNIT_NAME = 'junit.xml'
STDOUT_CAP_BYTES = 1048576
REAP_ALLOWANCE_S = 5.0
KILL_ALLOWANCE_S = 10.0
CHUNK = 65536
ELF_MAGIC = b'\x7fELF'
_F_ADD_SEALS = 1033
_F_SEAL_ALL = 0x0004 | 0x0002 | 0x0008 | 0x0010
_O_NOFOLLOW = getattr(os, 'O_NOFOLLOW', 0)
_O_DIRECTORY = getattr(os, 'O_DIRECTORY', 0)
_O_NONBLOCK = getattr(os, 'O_NONBLOCK', 0)
_O_BINARY = getattr(os, 'O_BINARY', 0)
RUN_RECORD_NAME = 'run-record.json'
EXPORT_MANIFEST_NAME = 'export-manifest.json'
RUNNER_RECORD_SCHEMA = 'claude-probe-runner-linux-v1'
EXPORT_TREE_MAX_DEPTH = 8
EXPORT_TREE_MAX_ENTRIES = 4096
APPROVED_BWRAP_FLAGS = frozenset((
    '--unshare-user', '--unshare-ipc', '--unshare-pid', '--unshare-net',
    '--unshare-uts', '--die-with-parent', '--new-session', '--clearenv',
    '--cap-drop', '--dev', '--proc', '--ro-bind', '--size', '--tmpfs',
    '--setenv'))
RESOURCE_EVENT_KEYS = frozenset(('max', 'oom', 'oom_kill', 'oom_group'))


def fail(code):
    raise ValueError(code)


def _linux_abspath(text):
    """Lexical absolute-guest-path rule, host-independent (validation only)."""
    return (type(text) is str and text.startswith('/') and text != '/'
            and '\\' not in text and '\x00' not in text
            and '..' not in text.split('/')
            and 1 <= len(text.encode('utf-8')) <= 4096
            and not any(ord(c) < 32 or ord(c) == 127 or c == '%' for c in text))


def _sha256_text(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _bounded_int(value, low, high):
    return type(value) is int and low <= value <= high


def strict_json(text):
    """Duplicate-key-free, NaN/Inf-free JSON; fixed code on any deviation."""
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                fail('plan_invalid_json')
            value[key] = item
        return value
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: fail('plan_invalid_json'))
    except ValueError:
        fail('plan_invalid_json')


def probe_deadline(default_seconds):
    """Raise-only outer-deadline override (floor = the reviewed default)."""
    raw = os.environ.get(DEADLINE_ENV)
    if raw is None:
        return default_seconds
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError(
            'probe runner deadline override is not an integer') from None
    if value < default_seconds:
        raise RuntimeError(
            'probe runner deadline override is below the reviewed floor')
    return value


# --------------------------------------------------------------------------
# Namespace-plan v2 validation (pure; no filesystem access)
# --------------------------------------------------------------------------

def _plan_section(value, keys, code):
    if type(value) is not dict or set(value) != set(keys):
        fail(code)
    return value


def plan_hosts(plan):
    """Role -> host path mapping of the six reviewed mounts."""
    return {mount['role']: mount['host'] for mount in plan['mounts']}


def plan_mode(plan, mode):
    """The selected launcher-mode declaration (A3: modes are plan data)."""
    for entry in plan['modes']:
        if entry.get('mode') == mode:
            return entry
    fail('plan_mode_invalid')


def canonical_argv(plan):
    """The one argv reconstruction the declarations above may produce.

    Mirrors the reviewed generator's fixed order: unshares and hardening,
    sorted --setenv pairs, empty tmpfs guest root, minimal /dev and /proc,
    read-only INPUT/IMAGE/CONTROL binds, the three sized tmpfs mounts, the
    measured runtime binds sorted by guest path, then the official-six final
    command.
    """
    environment = plan['environment']['setenv']
    argv = ['bwrap', '--unshare-user', '--unshare-ipc', '--unshare-pid',
            '--unshare-net', '--unshare-uts', '--die-with-parent',
            '--new-session', '--cap-drop', 'ALL', '--clearenv']
    for key in sorted(environment):
        argv += ['--setenv', key, environment[key]]
    argv += ['--tmpfs', '/', '--dev', '/dev', '--proc', '/proc']
    hosts = plan_hosts(plan)
    for role, guest in (('INPUT', GUEST_INPUT), ('IMAGE', GUEST_IMAGE_DIR),
                        ('CONTROL', GUEST_CONTROL)):
        argv += ['--ro-bind', hosts[role], guest]
    # The generator's fixed tmpfs order (SCRATCH, TMP, OUTPUT), independent of
    # the mounts list ordering.
    for guest, size in ((GUEST_SCRATCH, SCRATCH_BYTES), ('/tmp', TMP_BYTES),
                        (GUEST_OUTPUT, OUTPUT_BYTES)):
        argv += ['--size', str(size), '--tmpfs', guest]
    for bind in sorted(plan['runtime_binds'], key=lambda item: item['guest']):
        argv += ['--ro-bind', bind['source'], bind['guest']]
    return argv + list(plan_mode(plan, 'official-six')['command'])


def plan_problem(plan):
    """Fixed-code structural problem of a loaded plan, or None when valid."""
    if type(plan) is not dict:
        return 'plan_invalid'
    if plan.get('schema') == PLAN_SCHEMA_V1:
        return 'plan_schema_v1_refused'
    if plan.get('schema') != PLAN_SCHEMA:
        return 'plan_schema_unsupported'
    expected = {'schema', 'generation', 'runner', 'image', 'namespaces',
                'network', 'mounts', 'export', 'launcher', 'runtime_binds',
                'runtime_layout', 'environment', 'modes',
                'excluded_host_surfaces', 'argv', 'bounds',
                'official_cli_executed', 'activation_authorized'}
    if set(plan) != expected:
        return 'plan_invalid'
    if plan['generation'] != 'config_only_not_executed':
        return 'plan_invalid'
    wrapper = _plan_section(plan['runner'], ('bwrap_version', 'execution',
                                             'supervision'),
                            'plan_runner_invalid')
    if (wrapper['bwrap_version'] != BWRAP_VERSION
            or wrapper['execution'] != 'outer_runner_owned_separately'
            or wrapper['supervision'] != 'outside_workload_cgroup'):
        return 'plan_runner_invalid'
    if sorted(plan['namespaces']) != sorted(NAMESPACES):
        return 'plan_namespaces_invalid'
    network = _plan_section(plan['network'], ('mode', 'external_egress',
                                              'address', 'loopback'),
                            'plan_network_invalid')
    if (network['mode'] != 'loopback_only'
            or network['external_egress'] != 'unavailable'
            or network['address'] != '127.0.0.1'
            or network['loopback'] != 'automatic_under_unshare_net_no_ip_command'):
        return 'plan_network_invalid'
    image = _plan_section(plan['image'], ('bytes', 'closure_derived_from',
                                          'member', 'platform',
                                          'runtime_interp', 'runtime_needed',
                                          'sha256', 'version'),
                          'plan_image_invalid')
    if (image['closure_derived_from'] != 'image_bytes'
            or image['member'] != IMAGE_MEMBER
            or image['platform'] != IMAGE_PLATFORM
            or image['version'] != IMAGE_VERSION
            or not _sha256_text(image['sha256'])
            or not _bounded_int(image['bytes'], 1, IMAGE_MAX_BYTES)
            or type(image['runtime_interp']) is not str
            or not image['runtime_interp'].startswith('/')
            or any(ord(c) < 33 or ord(c) > 126 for c in image['runtime_interp'])
            or type(image['runtime_needed']) is not list
            or not 0 <= len(image['runtime_needed']) <= 1024
            or any(type(name) is not str or not name or len(name) > 4096
                   or any(ord(c) < 33 or ord(c) > 126 for c in name)
                   for name in image['runtime_needed'])
            or image['runtime_needed'] != sorted(set(image['runtime_needed']))):
        return 'plan_image_invalid'
    mounts = plan['mounts']
    if type(mounts) is not list or len(mounts) != 6:
        return 'plan_mounts_invalid'
    order = ('INPUT', 'IMAGE', 'CONTROL', 'OUTPUT', 'SCRATCH', 'TMP')
    readonlys = {'INPUT': True, 'IMAGE': True, 'CONTROL': True,
                 'OUTPUT': False, 'SCRATCH': False, 'TMP': False}
    guests = {'INPUT': GUEST_INPUT, 'IMAGE': GUEST_IMAGE_DIR,
              'CONTROL': GUEST_CONTROL, 'OUTPUT': GUEST_OUTPUT,
              'SCRATCH': GUEST_SCRATCH, 'TMP': '/tmp'}
    sizes = {'OUTPUT': OUTPUT_BYTES, 'SCRATCH': SCRATCH_BYTES, 'TMP': TMP_BYTES}
    hosts = {}
    for index, mount in enumerate(mounts):
        if type(mount) is not dict or mount.get('role') != order[index]:
            return 'plan_mounts_invalid'
        role = mount['role']
        keys = {'role', 'host', 'guest', 'readonly', 'kind'}
        if role in sizes:
            keys.add('size_limit_bytes')
        if role == 'OUTPUT':
            keys.add('host_role')
        if (set(mount) != keys or mount['kind'] != ('tmpfs' if role in sizes
                                                    else 'bind')
                or mount['readonly'] is not readonlys[role]
                or mount['guest'] != guests[role]):
            return 'plan_mounts_invalid'
        if role == 'OUTPUT':
            if (mount['host_role'] != 'export_destination'
                    or mount['size_limit_bytes'] != sizes[role]
                    or type(mount['host']) is not str or not mount['host']
                    or not _linux_abspath(mount['host'])):
                return 'plan_mounts_invalid'
        elif role in sizes:
            if mount['host'] is not None \
                    or mount['size_limit_bytes'] != sizes[role]:
                return 'plan_mounts_invalid'
        elif (type(mount['host']) is not str or not mount['host']
                or not _linux_abspath(mount['host'])):
            return 'plan_mounts_invalid'
        hosts[role] = mount['host']
    export = _plan_section(plan['export'], ('bounded_bytes', 'creation',
                                            'destination',
                                            'mounted_writable_in_namespace'),
                           'plan_export_invalid')
    if (export['destination'] != hosts['OUTPUT']
            or export['bounded_bytes'] != EXPORT_CAP_BYTES
            or export['creation'] != 'exclusive_no_follow'
            or export['mounted_writable_in_namespace'] is not False
            or not _linux_abspath(export['destination'])):
        return 'plan_export_invalid'
    export_path = export['destination']
    for prefix in (hosts['INPUT'], hosts['IMAGE'], hosts['CONTROL']):
        if (export_path == prefix
                or export_path.startswith(prefix.rstrip('/') + '/')
                or prefix.startswith(export_path.rstrip('/') + '/')):
            return 'plan_export_invalid'
    # The CONTROL launcher identity is REQUIRED (the generator always emits
    # it and always binds the launcher file, for BOTH launcher modes): the
    # host twin of the guest /pal-control/official-probe.sh final command,
    # with its measured digest and length. The on-disk file is re-measured
    # against these values at admission and again after the drain, closing
    # the host-swap window between generation and execution.
    launcher = plan['launcher']
    if (type(launcher) is not dict
            or set(launcher) != {'path', 'sha256', 'bytes'}
            or launcher.get('path') != hosts['CONTROL'] + '/' + GUEST_CONTROL_LAUNCHER
            or not _sha256_text(launcher.get('sha256'))
            or not _bounded_int(launcher.get('bytes'), 1, RUNTIME_BIND_MAX_BYTES)):
        return 'plan_launcher_invalid'
    binds = plan['runtime_binds']
    if type(binds) is not list or not 1 <= len(binds) <= RUNTIME_BIND_MAX:
        return 'plan_runtime_binds_invalid'
    bind_guests, bind_sources = set(), set()
    for bind in binds:
        if type(bind) is not dict or set(bind) != {'guest', 'mode', 'source',
                                                   'sha256', 'bytes'}:
            return 'plan_runtime_binds_invalid'
        if (bind['mode'] != 'ro'
                or not _linux_abspath(bind['guest'])
                or not _linux_abspath(bind['source'])
                or not _sha256_text(bind['sha256'])
                or not _bounded_int(bind['bytes'], 1, RUNTIME_BIND_MAX_BYTES)):
            return 'plan_runtime_binds_invalid'
        if bind['guest'] in bind_guests or bind['source'] in bind_sources:
            return 'plan_runtime_binds_invalid'
        bind_guests.add(bind['guest'])
        bind_sources.add(bind['source'])
    if GUEST_SH not in bind_guests:
        return 'plan_runtime_binds_invalid'  # the D2 holder needs /bin/sh
    if not bind_guests.isdisjoint(set(guests.values())):
        return 'plan_runtime_binds_invalid'
    layout = _plan_section(plan['runtime_layout'], ('guest_paths',
                                                    'ld_library_path',
                                                    'launcher_externals',
                                                    'library_search',
                                                    'shell_guest', 'shell_source'),
                           'plan_runtime_layout_invalid')
    if (layout['guest_paths'] != 'canonical'
            # Consumer supersets 2-3 of 5 (docstring list): the generator
            # pins 'not_used' and LINUX_RUNTIME_LIBRARY_DIRS; qualification
            # stand-ins may declare the env layout and their own search dirs.
            or layout['ld_library_path'] not in ('not_used',
                                                 'ld_library_path_env')
            or layout['launcher_externals']
            != 'shell_builtins_and_payload_python_only'
            or type(layout['library_search']) is not list
            or not 1 <= len(layout['library_search']) <= 64
            or any(type(item) is not str or not _linux_abspath(item)
                   for item in layout['library_search'])
            or layout['shell_guest'] != GUEST_SH
            or type(layout['shell_source']) is not str
            or layout['shell_source'] not in bind_sources):
        return 'plan_runtime_layout_invalid'
    environment = _plan_section(plan['environment'], ('clearenv', 'setenv'),
                                'plan_environment_invalid')
    child = environment['setenv']
    if (environment['clearenv'] is not True or type(child) is not dict
            or not 1 <= len(child) <= CHILD_ENV_MAX
            or child.get('PATH') != '/usr/bin:/bin'
            or any(type(k) is not str or type(v) is not str
                   or re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', k) is None
                   or not v or len(v) > 4096
                   or any(ord(c) < 32 or ord(c) == 127 for c in v)
                   for k, v in child.items())
            or ('LD_LIBRARY_PATH' in child
                and layout['ld_library_path'] != 'ld_library_path_env')):
        return 'plan_environment_invalid'
    modes = plan['modes']
    if type(modes) is not list or len(modes) != 2:
        return 'plan_modes_invalid'
    qualify, batch = modes
    mode_keys = {'command', 'depends_on', 'expected_banner', 'mode',
                 'selection', 'synthetic_request'}
    for entry in modes:
        if type(entry) is not dict or set(entry) != mode_keys:
            return 'plan_modes_invalid'
    image_guest = GUEST_IMAGE_DIR + '/' + image['member']
    if (qualify['mode'] != 'qualify-version'
            or qualify['selection'] != 'outer_runner_final_command_replacement'
            or type(qualify['command']) is not list
            or not 2 <= len(qualify['command']) <= 8
            or qualify['command'][0] != image_guest
            or any(type(token) is not str or not token or len(token) > 4096
                   for token in qualify['command'])
            or qualify['expected_banner'] != image['version'] + ' (Claude Code)'
            or qualify['synthetic_request'] is not False
            or qualify['depends_on'] != []):
        # Consumer superset 1 of 5 (see the module docstring's full list):
        # the generator pins command == [image_guest, '--version']; any
        # bounded token list invoking the sealed IMAGE executable itself is
        # admitted so native qualification can drive the same path with a
        # stand-in interpreter. Boundary-neutral and fail-closed.
        return 'plan_modes_invalid'
    launcher_guest = GUEST_CONTROL + '/' + GUEST_CONTROL_LAUNCHER
    if (batch['mode'] != 'official-six'
            or batch['selection'] != 'plan_argv_final_command'
            or batch['command'] != [launcher_guest, '--isolated-host-attested']
            or batch['expected_banner'] is not None
            or batch['synthetic_request'] is not True
            or batch['depends_on'] != ['qualify-version']):
        return 'plan_modes_invalid'
    bounds = _plan_section(plan['bounds'], ('cgroup_controls', 'deadline_seconds',
                                            'memory_mb', 'memory_swap_max',
                                            'pids_max'),
                           'plan_bounds_invalid')
    if (bounds['memory_mb'] != MEMORY_MAX_BYTES // (1024 * 1024)
            or bounds['memory_swap_max'] != MEMORY_SWAP_MAX_BYTES
            or bounds['pids_max'] != PIDS_MAX
            or bounds['deadline_seconds'] != DEFAULT_DEADLINE_SECONDS
            or bounds['cgroup_controls'] != 'require_qualification_before_run'):
        return 'plan_bounds_invalid'
    if (type(plan['excluded_host_surfaces']) is not list
            or not plan['excluded_host_surfaces']
            or any(type(item) is not str for item in plan['excluded_host_surfaces'])):
        return 'plan_surfaces_invalid'
    argv = plan['argv']
    if (type(argv) is not list or len(argv) < 8 or argv[0] != 'bwrap'
            or any(type(item) is not str or not item for item in argv)):
        return 'plan_argv_invalid'
    # Unknown bwrap flags are refused in the wrapper region only; the final
    # command may legitimately carry tokens such as --isolated-host-attested.
    for flag in ('--unshare-user', '--unshare-ipc', '--unshare-pid',
                 '--unshare-net', '--unshare-uts', '--die-with-parent',
                 '--new-session', '--clearenv', '--dev', '--proc'):
        if argv.count(flag) != 1:
            return 'plan_argv_invalid'
    if ('--cap-drop' not in argv
            or any(argv[index] == '--cap-drop' and argv[index + 1] != 'ALL'
                   for index in range(len(argv) - 1))):
        return 'plan_argv_invalid'
    if any(item.startswith('--') and item not in APPROVED_BWRAP_FLAGS
           for item in argv[:-2]):
        return 'plan_argv_invalid'
    if any(item == 'ip' or item.startswith('ip ') for item in argv):
        return 'plan_argv_invalid'
    setenv_pairs = {(argv[index + 1], argv[index + 2])
                    for index in range(len(argv) - 2)
                    if argv[index] == '--setenv'}
    if setenv_pairs != set(child.items()):
        return 'plan_argv_invalid'
    ro_pairs = {(argv[index + 1], argv[index + 2])
                for index in range(len(argv) - 2)
                if argv[index] == '--ro-bind'}
    expected_pairs = {(hosts['INPUT'], GUEST_INPUT),
                      (hosts['IMAGE'], GUEST_IMAGE_DIR),
                      (hosts['CONTROL'], GUEST_CONTROL)} \
        | {(bind['source'], bind['guest']) for bind in binds}
    if ro_pairs != expected_pairs or argv.count('--ro-bind') != 3 + len(binds):
        return 'plan_argv_invalid'
    if argv.count('--tmpfs') != 4 or argv.count('--size') != 3:
        return 'plan_argv_invalid'
    if argv != canonical_argv(plan):
        return 'plan_argv_invalid'
    if (plan['official_cli_executed'] is not False
            or plan['activation_authorized'] is not False):
        return 'plan_generation_invalid'
    return None


def _plan_from_bytes(data):
    """Strict parse + full structural validation of already-read plan bytes."""
    if len(data) > PLAN_MAX_BYTES:
        fail('plan_unreadable')
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError:
        fail('plan_invalid_json')
    plan = strict_json(text)
    problem = plan_problem(plan)
    if problem is not None:
        fail(problem)
    return plan


def load_plan(path):
    """Bounded read + strict parse + full structural validation."""
    path = Path(path)
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > PLAN_MAX_BYTES:
            fail('plan_unreadable')
        data = path.read_bytes()
    except OSError:
        fail('plan_unreadable')
    return _plan_from_bytes(data)


# --------------------------------------------------------------------------
# Admission (measure, reject elevation, seal)
# --------------------------------------------------------------------------

def _open_plain(path):
    return os.open(str(path), os.O_RDONLY | _O_BINARY | _O_NOFOLLOW | _O_NONBLOCK)


def verify_pinned_file(path, expected_sha256, expected_size, *, max_bytes,
                       require_elf):
    """One-hash admission of a pathname; returns the first bytes read."""
    fd = _open_plain(path)
    failure = None
    prefix = b''
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
            raise ValueError('probe_admission_invalid')
        digest, size = sha256(), 0
        while True:
            block = os.read(fd, CHUNK)
            if not block:
                break
            if not prefix:
                prefix = block[:4]
            size += len(block)
            if size > max_bytes:
                raise ValueError('probe_admission_invalid')
            digest.update(block)
        if (size != expected_size or digest.hexdigest() != expected_sha256
                or (require_elf and not prefix.startswith(ELF_MAGIC))):
            raise ValueError('probe_admission_invalid')
    except (OSError, ValueError) as error:
        failure = error
    finally:
        try:
            os.close(fd)
        except OSError as error:
            failure = failure if failure is not None else error
    if failure is not None:
        if isinstance(failure, ValueError) and type(failure.args[0]) is str:
            raise failure from None
        fail('probe_admission_invalid')
    return prefix


def reject_elevation(path):
    """setuid/setgid or file-capability bits refuse admission."""
    info = os.stat(str(path), follow_symlinks=False)
    if info.st_mode & (stat.S_ISUID | stat.S_ISGID):
        fail('probe_artifact_elevated')
    try:
        if os.getxattr(str(path), 'security.capability'):
            fail('probe_artifact_elevated')
    except (OSError, AttributeError):
        pass  # absent xattr, or a development host without os.getxattr


def seal_verified_file(path, expected_sha256, expected_size, *, max_bytes):
    """Verify once, then seal the exact bytes into an immutable memfd."""
    if (sys.platform != 'linux' or not hasattr(os, 'memfd_create')
            or fcntl is None):
        fail('runner_platform_unsupported')
    fd = _open_plain(path)
    failure = None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
            raise ValueError('probe_admission_invalid')
        memfd = os.memfd_create('pal-l7-image',
                                os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING
                                | getattr(os, 'MFD_EXEC', 0))
        try:
            digest, size = sha256(), 0
            while True:
                block = os.read(fd, CHUNK)
                if not block:
                    break
                size += len(block)
                if size > max_bytes:
                    raise ValueError('probe_admission_invalid')
                view = memoryview(block)
                while view:
                    view = view[os.write(memfd, view):]
                digest.update(block)
            if size != expected_size or digest.hexdigest() != expected_sha256:
                raise ValueError('probe_admission_invalid')
            os.lseek(memfd, 0, os.SEEK_SET)
            if os.read(memfd, 4) != ELF_MAGIC:
                raise ValueError('probe_admission_invalid')
            os.lseek(memfd, 0, os.SEEK_SET)
            os.fchmod(memfd, 0o555)
            fcntl.fcntl(memfd, _F_ADD_SEALS, _F_SEAL_ALL)
            # Move past the low descriptors the bootstrap child will install.
            sealed = fcntl.fcntl(memfd, fcntl.F_DUPFD, 100)
            os.close(memfd)
            return sealed
        except BaseException:
            try:
                os.close(memfd)
            except OSError:
                pass
            raise
    except (OSError, ValueError) as error:
        failure = error
    finally:
        try:
            os.close(fd)
        except OSError as error:
            failure = failure if failure is not None else error
    if failure is not None:
        if isinstance(failure, ValueError) and type(failure.args[0]) is str:
            raise failure from None
        fail('probe_admission_invalid')


def _elf64_x86_64(path):
    """Bounded ELF identity check of an already-measured image (admission)."""
    with open(path, 'rb') as stream:
        header = stream.read(20)
    if (len(header) != 20 or not header.startswith(ELF_MAGIC)
            or header[4] != 2 or header[5] != 1
            or int.from_bytes(header[18:20], 'little') != 62):
        fail('probe_image_elf_invalid')


def image_manifest_problem(value):
    """Pure six-key operator-manifest check (cross-platform unit-testable)."""
    if (type(value) is not dict or set(value) != set(IMAGE_MANIFEST_KEYS)
            or value.get('schema') != 'claude-probe-image-linux-v1'
            or value.get('path') != IMAGE_MEMBER
            or not _sha256_text(value.get('sha256'))
            or not _bounded_int(value.get('bytes'), 1, IMAGE_MAX_BYTES)
            or value.get('version') != IMAGE_VERSION
            or value.get('platform') != IMAGE_PLATFORM):
        return 'probe_image_manifest_invalid'
    return None


def verify_image_admission(image, image_dir):
    """Six-key operator manifest vs measured member; returns manifest facts."""
    if sys.platform != 'linux':
        fail('runner_platform_unsupported')
    directory = Path(image_dir)
    try:
        entries = sorted(os.listdir(directory))
    except OSError:
        fail('probe_image_unavailable')
    if entries != sorted([IMAGE_MEMBER, IMAGE_MANIFEST_NAME]):
        fail('probe_image_inventory_invalid')
    manifest_path = directory / IMAGE_MANIFEST_NAME
    info = manifest_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > IMAGE_MANIFEST_MAX_BYTES:
        fail('probe_image_manifest_invalid')
    try:
        value = strict_json(manifest_path.read_bytes().decode('ascii'))
    except (OSError, UnicodeDecodeError):
        fail('probe_image_manifest_invalid')
    problem = image_manifest_problem(value)
    if problem is not None:
        fail(problem)
    member = directory / IMAGE_MEMBER
    if (value['sha256'] != image['sha256'] or value['bytes'] != image['bytes']
            or value['version'] != image['version']):
        fail('probe_image_manifest_mismatch')
    reject_elevation(member)
    verify_pinned_file(member, image['sha256'], image['bytes'],
                       max_bytes=IMAGE_MAX_BYTES, require_elf=True)
    _elf64_x86_64(member)
    return dict(value)


def verify_environment_inventory(payload_root):
    """Hash every payload file; the operator manifest must match exactly."""
    root = Path(payload_root)
    files = {}
    try:
        def on_error(error):
            raise error
        for current, _dirs, names in os.walk(root, followlinks=False,
                                             onerror=on_error):
            for name in names:
                path = Path(current) / name
                info = path.lstat()
                rel = path.relative_to(root).as_posix()
                if (stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode)
                        or '..' in rel.split('/') or rel in files
                        or info.st_size > PAYLOAD_MAX_FILE
                        or len(files) >= PAYLOAD_MAX_FILES):
                    fail('probe_payload_invalid')
                fd = _open_plain(path)
                try:
                    opened = os.fstat(fd)
                    if (not stat.S_ISREG(opened.st_mode)
                            or (opened.st_dev, opened.st_ino, opened.st_size)
                            != (info.st_dev, info.st_ino, info.st_size)):
                        raise OSError
                    digest, size = sha256(), 0
                    while True:
                        block = os.read(fd, CHUNK)
                        if not block:
                            break
                        size += len(block)
                        digest.update(block)
                finally:
                    os.close(fd)
                if size != info.st_size:
                    fail('probe_payload_invalid')
                files[rel] = (size, digest.hexdigest())
        # The operator manifest is read and schema-checked, never self-listed
        # (same convention as the preparation's environment-manifest.json).
        if PAYLOAD_MANIFEST_MEMBER not in files:
            fail('probe_payload_invalid')
        files.pop(PAYLOAD_MANIFEST_MEMBER)
        manifest_path = root / PAYLOAD_MANIFEST_MEMBER
        text = manifest_path.read_bytes()
        if len(text) > 16777216:
            fail('probe_payload_manifest_invalid')
        value = strict_json(text.decode('utf-8'))
    except (OSError, UnicodeDecodeError):
        fail('probe_payload_invalid')
    if (type(value) is not dict
            or set(value) != {'schema', 'source_commit', 'source_tree',
                              'dependencies', 'python', 'official_cli_included',
                              'activation_authorized', 'files'}
            or value['schema'] != ENVIRONMENT_MANIFEST_SCHEMA
            or value['official_cli_included'] is not False
            or value['activation_authorized'] is not False
            or type(value['files']) is not list
            or not 1 <= len(value['files']) <= PAYLOAD_MAX_FILES):
        fail('probe_payload_manifest_invalid')
    seen = set()
    for entry in value['files']:
        if (type(entry) is not dict or set(entry) != {'path', 'bytes', 'sha256'}
                or type(entry['path']) is not str
                or '..' in entry['path'].split('/')
                or entry['path'] in seen or entry['path'] not in files
                or not _bounded_int(entry['bytes'], 0, PAYLOAD_MAX_FILE)
                or not _sha256_text(entry['sha256'])
                or files[entry['path']] != (entry['bytes'], entry['sha256'])):
            fail('probe_payload_manifest_invalid')
        seen.add(entry['path'])
    if seen != set(files):
        fail('probe_payload_unexpected_files')
    return dict(files=len(files), bytes=sum(size for size, _ in files.values()),
                source_commit=value['source_commit'])


def verify_runtime_binds(plan):
    """Measure every enumerated file bind; elevation is refused per file."""
    if sys.platform != 'linux':
        fail('runner_platform_unsupported')
    measured = []
    for bind in plan['runtime_binds']:
        reject_elevation(bind['source'])
        verify_pinned_file(bind['source'], bind['sha256'], bind['bytes'],
                           max_bytes=RUNTIME_BIND_MAX_BYTES, require_elf=False)
        measured.append(dict(guest=bind['guest'], sha256=bind['sha256'],
                             bytes=bind['bytes']))
    hosts = plan_hosts(plan)
    for role in ('INPUT', 'IMAGE', 'CONTROL'):
        info = Path(hosts[role]).stat(follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode):
            fail('probe_directory_bind_invalid')
    launcher = Path(hosts['CONTROL'], GUEST_CONTROL_LAUNCHER)
    try:
        entries = sorted(os.listdir(Path(hosts['CONTROL'])))
    except OSError:
        fail('probe_control_invalid')
    if entries != [GUEST_CONTROL_LAUNCHER]:
        fail('probe_control_invalid')
    info = launcher.lstat()
    if not stat.S_ISREG(info.st_mode):
        fail('probe_control_invalid')
    if stat.S_IMODE(info.st_mode) != 0o755:
        fail('launcher_mode_invalid')
    reject_elevation(launcher)
    # Re-measure the on-disk launcher against the plan's identity block:
    # digest and length must match exactly, closing the host-swap window.
    try:
        verify_pinned_file(str(launcher), plan['launcher']['sha256'],
                           plan['launcher']['bytes'],
                           max_bytes=RUNTIME_BIND_MAX_BYTES, require_elf=False)
    except ValueError:
        fail('launcher_identity_mismatch')
    return measured


def bwrap_identity():
    """Resolve, version-check and measure the reviewed wrapper executable."""
    if sys.platform != 'linux':
        fail('runner_platform_unsupported')
    resolved = shutil.which('bwrap')
    if resolved is None:
        fail('bwrap_unavailable')
    real = str(Path(resolved).resolve())
    info = os.stat(real, follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        fail('bwrap_unavailable')
    reject_elevation(real)
    try:
        completed = subprocess.run([real, '--version'], capture_output=True,
                                   timeout=10, env={'PATH': '/usr/bin:/bin'})
    except (OSError, subprocess.SubprocessError):
        fail('bwrap_unavailable')
    if completed.returncode != 0:
        fail('bwrap_unavailable')
    version = completed.stdout.decode('ascii', 'replace').strip()
    if version != 'bubblewrap %s' % BWRAP_VERSION:
        fail('bwrap_version_mismatch')
    with open(real, 'rb') as stream:
        payload = stream.read()
    if len(payload) > RUNTIME_BIND_MAX_BYTES:
        fail('bwrap_unavailable')
    return dict(path=real, version=BWRAP_VERSION,
                sha256=sha256(payload).hexdigest(), bytes=len(payload))


# --------------------------------------------------------------------------
# Delegated cgroup (narrow re-implementation of the L5 gate principle)
# --------------------------------------------------------------------------

class WorkloadCgroup:
    """One fresh workload cgroup under the delegated root; readback enforced."""

    __slots__ = ('root', 'path', 'limits', 'baseline_events')

    def __init__(self, root, allocation):
        self.root = str(root)
        self.path = os.path.join(self.root, allocation)
        self.limits = (('memory.max', str(MEMORY_MAX_BYTES)),
                       ('memory.swap.max', str(MEMORY_SWAP_MAX_BYTES)),
                       ('pids.max', str(PIDS_MAX)))
        self.baseline_events = {}

    def _write(self, name, value):
        with open(os.path.join(self.path, name), 'w') as handle:
            handle.write(value + '\n')

    def _read(self, name):
        with open(os.path.join(self.path, name)) as handle:
            return handle.read().strip()

    def _root_enabled(self):
        with open(os.path.join(self.root, 'cgroup.subtree_control')) as handle:
            active = handle.read().split()
        return 'memory' in active and 'pids' in active

    def _enable_root(self):
        if self._root_enabled():
            return
        target = os.path.join(self.root, 'cgroup.subtree_control')
        try:
            with open(target, 'w') as handle:
                handle.write('+memory +pids\n')
            if self._root_enabled():
                return
        except OSError:
            pass
        for name in os.listdir(self.root):
            if name.startswith('pal-l7-'):
                try:
                    os.rmdir(os.path.join(self.root, name))
                except OSError:
                    pass
        with open(target, 'w') as handle:
            handle.write('+memory +pids\n')
        if not self._root_enabled():
            fail('cgroup_root_unavailable')

    def create(self):
        self._enable_root()
        try:
            os.mkdir(self.path)
        except OSError:
            fail('cgroup_setup_failed')
        for name, value in self.limits:
            try:
                self._write(name, value)
                if self._read(name) != value:
                    raise OSError(name)
            except OSError:
                fail('cgroup_limit_not_enforced')
        self.baseline_events = self.events()
        if self.members():
            fail('cgroup_setup_failed')

    def admit(self, pid):
        try:
            self._write('cgroup.procs', str(pid))
            if str(pid) not in self._read('cgroup.procs').split():
                raise OSError
        except OSError:
            fail('cgroup_admission_failed')

    def members(self):
        try:
            return self._read('cgroup.procs').split()
        except OSError:
            fail('cgroup_unavailable')

    def events(self):
        result = {}
        for name in ('memory.events', 'pids.events'):
            try:
                with open(os.path.join(self.path, name)) as handle:
                    for line in handle:
                        key, _, value = line.strip().partition(' ')
                        if key and value.isdigit():
                            result['%s.%s' % (name, key)] = int(value)
            except OSError:
                continue
        return result

    def resource_limit_events(self):
        after = self.events()
        increased = []
        for key, value in after.items():
            if (key.rsplit('.', 1)[1] in RESOURCE_EVENT_KEYS
                    and value > self.baseline_events.get(key, 0)):
                increased.append(key)
        return sorted(increased)

    def signal_kill(self):
        """Request SIGKILL for every process currently in the cgroup."""
        try:
            self._write('cgroup.kill', '1')
        except OSError:
            pass

    def wait_empty(self, deadline):
        """True once cgroup.procs is empty (zombies count until reaped)."""
        while time.monotonic() < deadline:
            try:
                if not self.members():
                    return True
            except ValueError:
                return False
            time.sleep(0.01)
        try:
            return not self.members()
        except ValueError:
            return False

    def remove(self):
        try:
            os.rmdir(self.path)
        except OSError:
            pass


# --------------------------------------------------------------------------
# Execution derivation (documented deviations D1/D2)
# --------------------------------------------------------------------------

def _sh_quote(token):
    return "'" + token.replace("'", "'\\''") + "'"


def wrap_guest_entry(command):
    """D2: shell-builtin holder around the selected mode's final command."""
    if (len(command) == 3 and command[0] == GUEST_SH and command[1] == '-c'):
        text = command[2]
        if text.startswith('exec '):
            text = text[5:]
    else:
        text = ' '.join(_sh_quote(token) for token in command)
    return (text + ' ; pal_holder_status=$? ; printf "%s\\n" "$pal_holder_status"'
            ' > ' + GUEST_OUTPUT + '/' + HOLDER_STATUS_NAME + ' 2>/dev/null || true'
            ' ; IFS= read -r pal_holder_hold ; exit "$pal_holder_status"')


def derive_executed_argv(plan, mode, sealed_fd, bwrap_path):
    """Plan argv plus exactly the documented deviations for one mode."""
    mode_entry = plan_mode(plan, mode)
    argv = [bwrap_path] + list(plan['argv'][1:])
    batch = plan_mode(plan, 'official-six')['command']
    if argv[-len(batch):] != list(batch):
        fail('plan_argv_invalid')
    command = list(mode_entry['command'])
    if mode == 'official-six':
        argv = argv[:-len(command)]
    else:
        # qualify-version replaces the final command before the pytest entry.
        argv = argv[:-len(batch)]
    image_guest = GUEST_IMAGE_DIR + '/' + plan['image']['member']
    pair = ['--ro-bind', plan_hosts(plan)['IMAGE'], GUEST_IMAGE_DIR]
    index = next((i for i in range(len(argv) - 2) if argv[i:i + 3] == pair), None)
    if index is None:
        fail('plan_argv_invalid')
    argv[index:index + 3] = ['--ro-bind', '/proc/self/fd/%d' % sealed_fd,
                             image_guest]
    return argv + [GUEST_SH, '-c', wrap_guest_entry(command)]


# --------------------------------------------------------------------------
# Bounded evidence export (trusted channel, exclusive, no-follow)
# --------------------------------------------------------------------------

RESERVED_EXPORT_NAMES = frozenset((RUN_RECORD_NAME, EXPORT_MANIFEST_NAME))


def _clean_export_name(name):
    if name in RESERVED_EXPORT_NAMES:
        return False  # supervisor evidence names; never taken from the tree
    return (type(name) is str and 1 <= len(name) <= 240
            and '\\' not in name and '/' not in name
            and name not in ('.', '..')
            and not any(ord(c) < 32 or ord(c) > 126 for c in name))


def _export_tree(source_dir, prefix, dest_dir, cap, state):
    """Depth-bounded no-follow copy; regular files only, exclusive creation.

    Directory entries are visited in sorted name order so the exported
    manifest, the unsafe-entry list and every cap decision are deterministic
    across platforms and runs (scandir order is filesystem-dependent:
    alphabetical on some, creation/inode order on others). Evidence must be
    reproducible, never a directory-order artifact.
    """
    with os.scandir(source_dir) as stream:
        for entry in sorted(stream, key=lambda item: item.name):
            name = entry.name
            if not _clean_export_name(name):
                state['unsafe'].append(prefix + name)
                continue
            info = entry.stat(follow_symlinks=False)
            source_path = os.path.join(source_dir, name)
            target_path = os.path.join(dest_dir, name)
            if stat.S_ISDIR(info.st_mode):
                if (len(prefix.split('/')) >= EXPORT_TREE_MAX_DEPTH
                        or len(state['manifest']) > EXPORT_TREE_MAX_ENTRIES):
                    state['unsafe'].append(prefix + name + '/')
                    continue
                try:
                    os.mkdir(target_path, 0o755)
                except FileExistsError:
                    pass
                _export_tree(source_path, prefix + name + '/', target_path, cap,
                             state)
                continue
            if not stat.S_ISREG(info.st_mode):
                state['unsafe'].append(prefix + name)
                continue
            if info.st_size + state['bytes'] > cap:
                state['limit_exceeded'] = True
                continue
            try:
                src = os.open(source_path, os.O_RDONLY | _O_NOFOLLOW | _O_BINARY)
            except OSError:
                state['unsafe'].append(prefix + name)
                continue
            try:
                dst = os.open(target_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                              | _O_NOFOLLOW | _O_BINARY, 0o644)
            except OSError:
                os.close(src)
                state['unsafe'].append(prefix + name)
                continue
            digest, size = sha256(), 0
            over_limit = False
            try:
                while True:
                    block = os.read(src, CHUNK)
                    if not block:
                        break
                    if state['bytes'] + size + len(block) > cap:
                        over_limit = True
                        break
                    view = memoryview(block)
                    while view:
                        view = view[os.write(dst, view):]
                    size += len(block)
                    digest.update(block)
            finally:
                os.close(src)
                os.close(dst)
            if over_limit:
                state['limit_exceeded'] = True
                continue
            state['bytes'] += size
            state['manifest'].append(dict(name=prefix + name, bytes=size,
                                          sha256=digest.hexdigest()))


def export_output_tree(source_dir, destination, cap=EXPORT_CAP_BYTES):
    """Export one namespace output directory into the HOST EXPORT DESTINATION.

    Every source open is O_NOFOLLOW; every destination creation is exclusive;
    the aggregate is capped. Unsafe entries and cap breaches are reported so
    the caller can fail acceptance while keeping the already-exported evidence.
    """
    destination = Path(destination)
    info = destination.lstat()
    if not stat.S_ISDIR(info.st_mode):
        fail('export_destination_invalid')
    if os.listdir(destination):
        fail('export_destination_not_empty')
    state = {'manifest': [], 'bytes': 0, 'unsafe': [], 'limit_exceeded': False}
    try:
        source_info = os.stat(str(source_dir), follow_symlinks=False)
        if not stat.S_ISDIR(source_info.st_mode):
            fail('export_source_unavailable')
        _export_tree(str(source_dir), '', str(destination), cap, state)
    except OSError:
        fail('export_failed')
    return state


def _write_exclusive_json(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | _O_NOFOLLOW | _O_BINARY, 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
    finally:
        os.close(descriptor)


# --------------------------------------------------------------------------
# Structural acceptance gates
# --------------------------------------------------------------------------

def parse_probe_junit(path):
    """Bounded JUnit parse: counts plus claude_cli_probe observation values."""
    try:
        data = Path(path).read_bytes()
        if len(data) > 16777216:
            fail('gate_junit_invalid')
        root = ET.fromstring(data)
    except (OSError, ET.ParseError):
        fail('gate_junit_invalid')
    cases = root.findall('.//testcase')
    counts = {'cases': len(cases), 'skipped': 0, 'failures': 0, 'errors': 0}
    for case in cases:
        if case.find('skipped') is not None:
            counts['skipped'] += 1
        if case.find('failure') is not None:
            counts['failures'] += 1
        if case.find('error') is not None:
            counts['errors'] += 1
    observations = []
    for prop in root.findall('.//property'):
        if prop.get('name') == 'claude_cli_probe':
            try:
                value = strict_json(prop.get('value') or '')
            except ValueError:
                fail('gate_observation_invalid')
            if type(value) is not dict:
                fail('gate_observation_invalid')
            observations.append(value)
    return counts, observations


def _read_status_file(directory, name):
    try:
        text = (Path(directory, name)).read_bytes().decode('ascii').strip()
    except (OSError, UnicodeDecodeError):
        return None
    return text if re.fullmatch('-?[0-9]{1,10}', text) else None


def gate_official_six(export_dir, record):
    """Structural acceptance for the official-six batch (plan step 6)."""
    findings = []
    if record['stop_condition'] != 'completed':
        findings.append('stop_condition_' + record['stop_condition'])
    if record['execution'].get('holder_status') != '0':
        findings.append('launcher_status_not_zero')
    exit_code = _read_status_file(export_dir, EXIT_CODE_NAME)
    if exit_code is None:
        findings.append('exit_code_missing')
    elif exit_code != '0':
        findings.append('exit_code_not_zero')
    try:
        counts, observations = parse_probe_junit(Path(export_dir, JUNIT_NAME))
    except ValueError as error:
        findings.append(error.args[0] if error.args and type(error.args[0]) is str
                        else 'gate_junit_invalid')
        counts, observations = {'cases': 0, 'skipped': 0, 'failures': 0,
                                'errors': 0}, []
    if (counts['cases'] != len(SCENARIOS) or counts['skipped']
            or counts['failures'] or counts['errors']):
        findings.append('junit_structure_rejected')
    modes = sorted(observation.get('mode') for observation in observations
                   if type(observation.get('mode')) is str)
    if len(observations) != len(SCENARIOS) or modes != sorted(SCENARIOS):
        findings.append('observation_multiset_rejected')
    for observation in observations:
        if observation.get('schema_version') != OBSERVATION_SCHEMA:
            findings.append('observation_schema_rejected')
            break
    if any(observation.get('activation_authorized') is not False
           for observation in observations):
        findings.append('observation_activation_rejected')
    return findings


def gate_qualify_version(record, mode_entry):
    """One exact banner plus lifecycle checks; gates the official-six batch."""
    findings = []
    if record['stop_condition'] != 'completed':
        findings.append('stop_condition_' + record['stop_condition'])
    expected = (mode_entry['expected_banner'] + '\n').encode('ascii')
    if record['execution'].get('stdout_bytes_value', b'') != expected:
        findings.append('version_banner_mismatch')
    if record['execution'].get('stderr_bytes', 0) != 0:
        findings.append('version_stderr_nonzero')
    if record['execution'].get('holder_status') != '0':
        findings.append('version_status_not_zero')
    return findings


# --------------------------------------------------------------------------
# Supervision: gate, hold, drain, export, teardown
# --------------------------------------------------------------------------

def _close_except(keep):
    for name in os.listdir('/proc/self/fd'):
        try:
            number = int(name)
        except ValueError:
            continue
        if number not in keep:
            try:
                os.close(number)
            except OSError:
                pass


def _classify_stderr(sniff):
    text = bytes(sniff)
    for marker in (b'Unknown option', b'unrecognized option'):
        if marker in text:
            return 'wrapper_option_unsupported'
    return None


def _namespace_output_dir(members):
    """First live member whose mount namespace still exposes /pal-output."""
    for member in members:
        candidate = os.path.join('/proc', member, 'root', GUEST_OUTPUT.lstrip('/'))
        try:
            fd = os.open(candidate, os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW)
        except OSError:
            continue
        os.close(fd)
        return candidate
    return None


def _holder_status(source_dir):
    if source_dir is None:
        return None
    try:
        fd = os.open(os.path.join(source_dir, HOLDER_STATUS_NAME),
                     os.O_RDONLY | _O_NOFOLLOW | _O_NONBLOCK | _O_BINARY)
    except OSError:
        return None
    try:
        text = os.read(fd, 64).decode('ascii').strip()
    except (OSError, UnicodeDecodeError):
        return None
    finally:
        os.close(fd)
    return text if re.fullmatch('-?[0-9]{1,10}', text) else None


def _reap(pid):
    try:
        os.waitpid(pid, 0)
    except (ChildProcessError, OSError):
        pass


def run_outer_probe(plan_path, *, mode, deadline_seconds=None, driver_stop=None,
                    allocation=None):
    """One full outer attempt for one launcher mode. Returns the record."""
    if sys.platform != 'linux':
        fail('runner_platform_unsupported')
    if mode not in LAUNCHER_MODES:
        fail('plan_mode_invalid')
    try:
        plan_bytes = Path(plan_path).read_bytes()
    except OSError:
        fail('plan_unreadable')
    # One read feeds both the hash and the validation (no read-read TOCTOU).
    plan = _plan_from_bytes(plan_bytes)
    mode_entry = plan_mode(plan, mode)
    deadline_s = (DEFAULT_DEADLINE_SECONDS if deadline_seconds is None
                  else int(deadline_seconds))
    if deadline_s < 1:
        fail('deadline_invalid')
    started = time.monotonic()
    record = {
        'schema': RUNNER_RECORD_SCHEMA, 'mode': mode,
        'mode_depends_on': list(mode_entry['depends_on']),
        'plan_sha256': sha256(plan_bytes).hexdigest(),
        'stop_condition': 'bootstrap_failed', 'accepted': False, 'findings': [],
        'admission': {}, 'cgroup': {}, 'execution': {}, 'export': {},
        'timing_ms': {}, 'official_cli_launched': False,
        'activation_authorized': False}
    findings = []
    sealed_fd = None
    hold_w = out_r = err_r = None
    workload_pid = None
    cgroup = None
    hosts = plan_hosts(plan)
    bwrap = bwrap_identity()
    record['admission']['bwrap'] = bwrap
    image_manifest = verify_image_admission(plan['image'], hosts['IMAGE'])
    record['admission']['image'] = dict(image_manifest)
    sealed_fd = seal_verified_file(
        Path(hosts['IMAGE']) / plan['image']['member'],
        plan['image']['sha256'], plan['image']['bytes'], max_bytes=IMAGE_MAX_BYTES)
    record['admission']['sealed_image_fd'] = sealed_fd
    record['admission']['payload'] = verify_environment_inventory(hosts['INPUT'])
    record['admission']['runtime_binds'] = verify_runtime_binds(plan)
    record['admission']['launcher'] = dict(
        path=plan['launcher']['path'], sha256=plan['launcher']['sha256'],
        bytes=plan['launcher']['bytes'], mode='0755', verified=True)
    export_destination = Path(plan['export']['destination'])
    info = export_destination.lstat()
    if not stat.S_ISDIR(info.st_mode) or os.listdir(export_destination):
        fail('export_destination_invalid')
    root = os.environ.get(CGROUP_ROOT_ENV, '')
    if not root or not Path(root, 'cgroup.controllers').is_file():
        fail('cgroup_root_unavailable')
    controllers = Path(root, 'cgroup.controllers').read_text().split()
    if 'memory' not in controllers or 'pids' not in controllers:
        fail('cgroup_root_unavailable')
    allocation = allocation or ('pal-l7-' + sha256(
        ('%d:%d' % (os.getpid(), time.monotonic_ns())).encode('ascii')
    ).hexdigest()[:16])
    cgroup = WorkloadCgroup(root, allocation)
    cgroup.create()
    record['cgroup'] = {'root': root, 'path': cgroup.path,
                        'limits': {name: value for name, value in cgroup.limits}}
    executed = derive_executed_argv(plan, mode, sealed_fd, bwrap['path'])
    record['execution']['executed_argv'] = executed
    hold_r, hold_w = os.pipe()
    out_r, out_w = os.pipe()
    err_r, err_w = os.pipe()
    gate_r, gate_w = os.pipe()
    workload_pid = os.fork()
    if workload_pid == 0:
        # Bootstrap child: admitted behind the gate, becomes bwrap itself.
        # The supervisor (parent) stays OUTSIDE the workload cgroup.
        try:
            os.dup2(hold_r, 0)
            os.dup2(out_w, 1)
            os.dup2(err_w, 2)
            for fd in (hold_r, out_w, err_w):
                if fd > 2:
                    os.close(fd)
            _close_except({0, 1, 2, gate_r, sealed_fd})
            os.set_inheritable(sealed_fd, True)
            if os.read(gate_r, 1) != b'R':
                os._exit(96)
            os.lseek(sealed_fd, 0, os.SEEK_SET)
            os.execv(bwrap['path'], executed)
        except BaseException:
            os._exit(98)
        os._exit(98)
    for fd in (hold_r, out_w, err_w, gate_r):
        os.close(fd)
    try:
        cgroup.admit(workload_pid)
        record['cgroup']['admitted'] = sorted(cgroup.members())
        if str(workload_pid) not in record['cgroup']['admitted']:
            raise OSError
        os.write(gate_w, b'R')
    except (OSError, ValueError) as error:
        # Placement/readback signals failure both via OSError and via fail()
        # (ValueError carrying its own fixed code); both must fall through to
        # the common supervision teardown so the bootstrap child is reaped,
        # the sealed memfd is closed, the pal-l7-* cgroup is removed and the
        # run record is still written. The workload was never released.
        if (isinstance(error, ValueError) and error.args
                and type(error.args[0]) is str
                and re.fullmatch('[a-z0-9_]{1,64}', error.args[0]) is not None):
            findings.append(error.args[0])
        else:
            findings.append('gate_release_failed')
    finally:
        os.close(gate_w)
    record['official_cli_launched'] = not findings
    os.set_blocking(out_r, False)
    os.set_blocking(err_r, False)
    stdout, sniff = bytearray(), bytearray()
    out_total = err_total = 0
    stop_condition = 'bootstrap_failed'
    bwrap_status = None
    source_dir = None
    export_state = None
    re_raise = None
    deadline = time.monotonic() + deadline_s
    try:
        try:
            while True:
                if driver_stop is not None and driver_stop.is_set():
                    stop_condition = 'driver_lost'
                    break
                if time.monotonic() >= deadline:
                    stop_condition = 'deadline_exceeded'
                    break
                if bwrap_status is None:
                    try:
                        done, status = os.waitpid(workload_pid, os.WNOHANG)
                        if done == workload_pid:
                            bwrap_status = status
                    except ChildProcessError:
                        bwrap_status = 'reaped_unknown'
                try:
                    readable, _, _ = select.select([out_r, err_r], [], [], 0.05)
                except (InterruptedError, OSError):
                    continue
                for index, fd in ((0, out_r), (1, err_r)):
                    if fd not in readable:
                        continue
                    block = os.read(fd, CHUNK)
                    if not block:
                        continue
                    if index == 0:
                        out_total += len(block)
                        if len(stdout) <= STDOUT_CAP_BYTES:
                            stdout.extend(
                                block[:STDOUT_CAP_BYTES + 1 - len(stdout)])
                    else:
                        err_total += len(block)
                        if len(sniff) < 4096:
                            sniff.extend(block[:4096 - len(sniff)])
                source_dir = _namespace_output_dir(cgroup.members())
                if _holder_status(source_dir) is not None:
                    stop_condition = 'completed'
                    break
                if bwrap_status is not None and source_dir is None:
                    stop_condition = 'completed'
                    break
            record['stop_condition'] = stop_condition
            if stop_condition == 'completed':
                # Drain bounded output tails so late evidence is not lost.
                drain_deadline = time.monotonic() + REAP_ALLOWANCE_S
                while time.monotonic() < drain_deadline:
                    try:
                        readable, _, _ = select.select([out_r, err_r], [], [],
                                                        0.05)
                    except (InterruptedError, OSError):
                        break
                    progressed = False
                    for index, fd in ((0, out_r), (1, err_r)):
                        if fd in readable:
                            progressed = True
                            block = os.read(fd, CHUNK)
                            if not block:
                                continue
                            if index == 0:
                                out_total += len(block)
                                if len(stdout) <= STDOUT_CAP_BYTES:
                                    stdout.extend(
                                        block[:STDOUT_CAP_BYTES + 1
                                              - len(stdout)])
                            else:
                                err_total += len(block)
                    if not progressed:
                        break
                source_dir = _namespace_output_dir(cgroup.members())
            record['execution'].update(
                stdout_bytes_value=bytes(stdout), stdout_bytes=len(stdout),
                stderr_bytes=err_total, stdout_total_bytes=out_total,
                stderr_total_bytes=err_total,
                output_truncated=(out_total > STDOUT_CAP_BYTES
                                  or err_total > STDOUT_CAP_BYTES),
                holder_status=_holder_status(source_dir),
                bwrap_status=(None if bwrap_status is None else
                              (bwrap_status if isinstance(bwrap_status, str)
                               else os.waitstatus_to_exitcode(bwrap_status))))
            classified = _classify_stderr(sniff)
            if classified is not None:
                findings.append(classified)
        except BaseException as error:
            # Evidence first: record the failure, keep the teardown below.
            re_raise = error if isinstance(error, (KeyboardInterrupt,
                                                   SystemExit)) else None
            if re_raise is None:
                findings.append('supervisor_internal_error')
                if record['stop_condition'] == 'bootstrap_failed':
                    record['stop_condition'] = 'supervisor_error'
        # Export BEFORE teardown: the holder keeps the namespace alive. Export
        # failures carry their own fixed codes, distinct from supervision.
        export_started = time.monotonic()
        try:
            if source_dir is not None:
                export_state = export_output_tree(source_dir, export_destination)
                record['export'] = {
                    'destination': str(export_destination),
                    'bytes': export_state['bytes'],
                    'files': len(export_state['manifest']),
                    'unsafe_entries': export_state['unsafe'],
                    'limit_exceeded': export_state['limit_exceeded']}
                if export_state['unsafe']:
                    findings.append('export_unsafe_entry')
                if export_state['limit_exceeded']:
                    findings.append('export_limit_exceeded')
            else:
                findings.append('export_source_unavailable')
        except ValueError as error:
            code = error.args[0] if error.args and type(error.args[0]) is str \
                else 'export_failed'
            findings.append(code)
        if not record['export']:
            record['export'] = {'destination': str(export_destination),
                                'bytes': 0, 'files': 0, 'unsafe_entries': [],
                                'limit_exceeded': False}
        record['timing_ms']['export_ms'] = int(
            (time.monotonic() - export_started) * 1000)
    finally:
        # Teardown: release the holder, kill the whole cgroup, reap the direct
        # child (a zombie would otherwise keep cgroup.procs non-empty), then
        # verify the cgroup is empty before accepting anything.
        teardown_started = time.monotonic()
        for fd in (hold_w, out_r, err_r):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        cgroup.signal_kill()
        _reap(workload_pid)
        empty = cgroup.wait_empty(time.monotonic() + KILL_ALLOWANCE_S)
        survivors = cgroup.members() if not empty else []
        if not empty or survivors:
            findings.append('teardown_failed')
        events = cgroup.resource_limit_events()
        record['cgroup']['events_after'] = cgroup.events()
        if events:
            findings.append('resource_limit_event')
            record['cgroup']['resource_limit_events'] = events
        cgroup.remove()
        record['cgroup']['verified_empty'] = bool(empty and not survivors)
        record['timing_ms']['teardown_ms'] = int(
            (time.monotonic() - teardown_started) * 1000)
        if sealed_fd is not None:
            try:
                os.close(sealed_fd)
            except OSError:
                pass
    record['timing_ms']['total_ms'] = int((time.monotonic() - started) * 1000)
    # Post-run re-measure of the IMAGE pathname (D1 evidence; the sealed
    # snapshot is what executed, this catches post-admission substitution).
    try:
        verify_pinned_file(
            Path(hosts['IMAGE']) / plan['image']['member'],
            plan['image']['sha256'], plan['image']['bytes'],
            max_bytes=IMAGE_MAX_BYTES, require_elf=True)
        record['admission']['post_run_image_verified'] = True
    except ValueError:
        record['admission']['post_run_image_verified'] = False
        findings.append('post_run_image_mismatch')
    # Post-drain re-measure of the CONTROL launcher twin: both measurements
    # (admission and post-drain) live in the run record; a divergence between
    # the bound bytes and the surviving pathname fails acceptance.
    try:
        verify_pinned_file(
            Path(plan['launcher']['path']), plan['launcher']['sha256'],
            plan['launcher']['bytes'], max_bytes=RUNTIME_BIND_MAX_BYTES,
            require_elf=False)
        record['admission']['post_run_launcher_verified'] = True
    except ValueError:
        record['admission']['post_run_launcher_verified'] = False
        findings.append('post_run_launcher_mismatch')
    if mode == 'official-six':
        findings.extend(gate_official_six(export_destination, record))
    else:
        findings.extend(gate_qualify_version(record, mode_entry))
    record['findings'] = findings
    record['accepted'] = (record['stop_condition'] == 'completed' and not findings)
    evidence = dict(record)
    evidence['execution'] = dict(record['execution'])
    evidence['execution']['stdout_bytes_value'] = record['execution'].get(
        'stdout_bytes_value', b'').decode('utf-8', 'replace')
    try:
        _write_exclusive_json(export_destination / RUN_RECORD_NAME, evidence)
        if export_state is not None:
            _write_exclusive_json(export_destination / EXPORT_MANIFEST_NAME,
                                  dict(schema='claude-probe-export-v1',
                                       files=export_state['manifest'],
                                       bytes=export_state['bytes']))
    except OSError:
        pass  # evidence write failure cannot be repaired; run already recorded
    if re_raise is not None:
        raise re_raise from None
    return record


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

class DriverStop:
    """Signals that the driving stdin pipe closed (CLI use only)."""

    def __init__(self):
        self._flag = threading.Event()

    def is_set(self):
        return self._flag.is_set()

    def watch(self):
        try:
            if not stat.S_ISFIFO(os.fstat(0).st_mode):
                return
        except OSError:
            return

        def reader():
            while True:
                try:
                    if not os.read(0, 4096):
                        break
                except OSError:
                    break
            self._flag.set()

        threading.Thread(target=reader, name='pal-l7-driver-watch',
                         daemon=True).start()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                     allow_abbrev=False)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check-plan', allow_abbrev=False)
    check.add_argument('--plan', type=Path, required=True)
    run = sub.add_parser('run', allow_abbrev=False)
    run.add_argument('--plan', type=Path, required=True)
    run.add_argument('--mode', choices=LAUNCHER_MODES, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'check-plan':
            plan = load_plan(args.plan)
            result = dict(status='plan_validated',
                          modes=[entry['mode'] for entry in plan['modes']],
                          schema=plan['schema'],
                          runtime_binds=len(plan['runtime_binds']),
                          official_cli_executed=False,
                          activation_authorized=False)
        else:
            plan = load_plan(args.plan)
            deadline = probe_deadline(plan['bounds']['deadline_seconds'])
            stop = DriverStop()
            stop.watch()
            completed = run_outer_probe(args.plan, mode=args.mode,
                                        deadline_seconds=deadline,
                                        driver_stop=stop)
            result = dict(status='completed' if completed['accepted'] else 'REJECTED',
                          mode=completed['mode'],
                          stop_condition=completed['stop_condition'],
                          findings=completed['findings'],
                          export=str(plan['export']['destination']),
                          activation_authorized=False)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['status'] in ('plan_validated', 'completed') else 1
    except Exception as error:
        code = error.args[0] if type(error) is ValueError and len(error.args) == 1 \
            else 'probe_runner_failed'
        if type(code) is not str or not re.fullmatch('[a-z0-9_]{1,64}', code):
            code = 'probe_runner_failed'
        print(json.dumps(dict(status='BLOCKED', reason=code,
                              activation_authorized=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
