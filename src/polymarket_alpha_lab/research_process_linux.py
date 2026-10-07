"""Contained Linux execution: separate artifact admission plus a two-phase lifecycle.

This module composes BESIDE ``ResearchProcessSpec``: ``spec.argv[0]`` and
``spec.executable_sha256`` always describe the vendor image, never the
wrapper, helper, or interpreter. Each admitted call performs exactly two
contained executions owned by one trusted supervisor and one immutable
artifact set:

1. a version execution of the sealed vendor snapshot (empty stdin, no
   credential or prompt descriptor, denied networking, fresh private state); a
   version mismatch starts no model namespace; and
2. after verified teardown of the version subtree, a model execution in a
   fresh namespace built from the SAME sealed snapshots. The per-call
   credential travels a one-use bounded anonymous pipe only after readiness,
   never in launcher argv or the supervisor environment.

Artifacts are admitted by hashing once, then copied into sealed memfd
snapshots; execution binds to the snapshot descriptors, not to reopenable
pathnames. Egress is offline-only: no production-egress constructor, no
``qualified=True`` escape, and no host-network fallback exists here. This is
synthetic-acceptance engineering, not official-client or TLS qualification.

The embedded :data:`HELPER_SOURCE` is the trusted supervisor/guest entry. It
is standard-library-only and performs no application or PostgreSQL imports.

L9 Amendment 1 (DELIVERY_PLAN.md section 67) adds the closed
``relay-fixed-origin`` egress value: a launch declaring it pins the SECOND
checked-in stdlib helper (:data:`RELAY_HELPER_SOURCE` in
``research_linux_relay``, selected by egress at admission), carries the typed
reviewed relay trust record, and stages one inherited AF_UNIX relay channel
descriptor (duplicated to >= 100 through the existing F_DUPFD idiom) plus one
port drawn from the exact (20000, 32767) window into the model-phase wrapper
argv as two PAL_RELAY_* setenv values. The offline branch keeps the frozen
helper bytes, CONF, argv and policy digests byte-identical; cross-pinned
combinations refuse construction. The relay egress authorizes no real
endpoint, no credential use and no activation; native relay execution stays
deferred to the opt-in Linux probes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
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
import signal
import socket
import stat
import subprocess
import sys
import threading
import time

from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_linux_relay import (
    RELAY_HELPER_SOURCE, RELAY_PORT_WINDOW, RELAY_PROTOCOL_VERSION,
    RelayTrustConfig, _relay_helper_digest, draw_relay_port,
)
from polymarket_alpha_lab.research_process import (
    ResearchProcessError, ResearchProcessResult,
)
from polymarket_alpha_lab.team_research_agent_types import integer

LAUNCH_SCHEMA = 'research-linux-launch-v1'
HELPER_PROTOCOL_VERSION = 'research-linux-helper-v1'
EGRESS_OFFLINE = 'offline'
# L9 Amendment 1 (DELIVERY_PLAN.md section 67): the second admitted closed
# egress value. It selects the RELAY_HELPER_SOURCE helper, the exact
# (20000, 32767) relay port window and the typed reviewed trust record; the
# offline value keeps the frozen helper, an empty relay surface and no trust
# record. Cross-pinned combinations refuse construction.
EGRESS_RELAY = 'relay-fixed-origin'
RELAY_HELPER_DIGEST = _relay_helper_digest()
RELAY_INHERITED_FROM_PARENT = 'relay-channel-model-phase-only'
NAMESPACES = ('user', 'mount', 'pid', 'net', 'ipc', 'uts')
SCRATCH_SIZE_CAP = 1073741824        # 1 GiB declared engineering bound
TMP_SIZE_CAP = 536870912             # 512 MiB declared engineering bound
MEMORY_MAX_CAP = 4294967296          # 4 GiB declared engineering bound
PIDS_MAX_CAP = 64
VENDOR_SIZE_CAP = 536870912
WRAPPER_SIZE_CAP = 67108864
INTERPRETER_SIZE_CAP = 536870912
RUNTIME_FILE_COUNT_CAP = 512
RUNTIME_MEMBER_SIZE_CAP = 536870912
MAX_VERSION_OUTPUT_BYTES = 65536
MAX_CREDENTIAL_BYTES = 4096
REQUIRED_GUEST_ENV = frozenset(('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL',
                                'CLAUDE_CODE_MAX_OUTPUT_TOKENS', 'CLAUDE_CONFIG_DIR', 'HOME'))
DEFAULT_GUEST_ENV = tuple(sorted(REQUIRED_GUEST_ENV | frozenset((
    'CLAUDE_CODE_MAX_RETRIES', 'CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK',
    'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC', 'CLAUDE_CODE_DISABLE_FAST_MODE',
    'CLAUDE_CODE_DISABLE_ATTACHMENTS', 'CLAUDE_CODE_DISABLE_AUTO_MEMORY',
    'CLAUDE_CODE_DISABLE_BACKGROUND_TASKS', 'CLAUDE_CODE_DISABLE_ADVISOR_TOOL',
    'CLAUDE_CODE_DISABLE_TERMINAL_TITLE', 'CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING',
    'CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS', 'CLAUDE_CODE_DISABLE_BUNDLED_SKILLS',
    'CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL', 'DISABLE_COMPACT',
    'DISABLE_UPDATES', 'DISABLE_TELEMETRY', 'DISABLE_ERROR_REPORTING',
    'LD_LIBRARY_PATH'))))
ALLOCATION_RULE = 'per-call-unique-subdirectory'
SUBSTITUTED_ENV = frozenset(('HOME', 'CLAUDE_CONFIG_DIR', 'LD_LIBRARY_PATH'))
ELF_MAGIC = b'\x7fELF'
# Linux UAPI memfd seals (the stdlib fcntl does not expose F_ADD_SEALS).
_F_ADD_SEALS = 1033
_F_SEAL_ALL = 0x0004 | 0x0002 | 0x0008 | 0x0010
_MFD_EXEC = getattr(os, 'MFD_EXEC', 0)

HELPER_SOURCE = '''\
# Trusted containment helper (protocol research-linux-helper-v1).
# Standard library only: no application or PostgreSQL imports.
# Modes: supervise (outside the vendor cgroup) and guest (namespace entry).
import hashlib
import json
import os
import select
import signal
import sys
import time

CHUNK = 65536
_RUNNING = object()
# Canonical channel numbers installed by THIS process at startup: fd 0 is the
# control pipe (supervisor stdin), 1/2 relay vendor stdout/stderr, and the
# four CONF-listed channels are placed at 3..6 here, never in the parent.
CONTROL_FD, RELAY_OUT_FD, RELAY_ERR_FD, REPORT_FD, LIVENESS_FD, PROMPT_FD, CREDENTIAL_FD = range(7)


def _write_all(fd, data):
    view = memoryview(data)
    while view:
        try:
            written = os.write(fd, view)
        except BlockingIOError:
            select.select([], [fd], [], 1.0)
            continue
        view = view[written:]


def _read_line(fd, limit):
    data = bytearray()
    while len(data) < limit:
        block = os.read(fd, min(4096, limit - len(data)))
        if not block:
            raise EOFError('channel closed')
        data.extend(block)
        if data.endswith(b'\\n'):
            return bytes(data[:-1])
    raise ValueError('line too long')


def _report(fd, value):
    _write_all(fd, json.dumps(value, separators=(',', ':')).encode('utf-8') + b'\\n')


def _now_ms():
    return time.monotonic_ns() // 1000000


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


def _install_channels(cfg):
    # Place the CONF-listed inherited channels at the canonical numbers inside
    # THIS fresh process only; the parent never touches its own descriptors.
    for target, name in ((REPORT_FD, 'report_fd'), (LIVENESS_FD, 'liveness_fd'),
                         (PROMPT_FD, 'prompt_fd'), (CREDENTIAL_FD, 'credential_fd')):
        source = cfg[name]
        if source != target:
            os.dup2(source, target)
            os.close(source)


def _enable_root_controls(root):
    # The delegated root must expose the memory/pids controller files to its
    # children. Enabling them here configures only the test-owned delegated
    # subtree; leftover empty per-call directories from crashed runs are
    # removed so the enable write can succeed.
    target = os.path.join(root, 'cgroup.subtree_control')

    def enabled():
        with open(target) as handle:
            active = handle.read().split()
        return 'memory' in active and 'pids' in active

    def attempt():
        with open(target, 'w') as handle:
            handle.write('+memory +pids\\n')
        return enabled()

    if enabled():
        return
    try:
        if attempt():
            return
    except OSError:
        pass
    for name in os.listdir(root):
        if name.startswith('pal-call-'):
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                pass
    if not attempt():
        raise OSError('delegated cgroup controllers cannot be enabled')


class Cgroup:
    def __init__(self, cfg):
        self.path = os.path.join(cfg['cgroup_root'], cfg['alloc_name'])
        self.controls = (('memory.max', str(cfg['memory_max_bytes'])),
                         ('memory.swap.max', str(cfg['memory_swap_max_bytes'])),
                         ('pids.max', str(cfg['pids_max'])))

    def _write(self, name, value):
        with open(os.path.join(self.path, name), 'w') as handle:
            handle.write(value + '\\n')

    def _read(self, name):
        with open(os.path.join(self.path, name)) as handle:
            return handle.read().strip()

    def create(self):
        os.mkdir(self.path)
        for name, value in self.controls:
            self._write(name, value)
            if self._read(name) != value:
                raise OSError('cgroup control not enforced: ' + name)

    def admit(self, pid):
        self._write('cgroup.procs', str(pid))
        if str(pid) not in self._read('cgroup.procs').split():
            raise OSError('cgroup admission failed')

    def kill(self, deadline_ms):
        try:
            self._write('cgroup.kill', '1')
        except OSError:
            pass
        while _now_ms() < deadline_ms:
            if not self._read('cgroup.procs').split():
                return True
            time.sleep(0.01)
        return not self._read('cgroup.procs').split()


def _bwrap_argv(cfg, mode):
    guest = cfg['guest']
    artifacts = [cfg['wrapper_fd'], cfg['helper_fd'], cfg['interp_fd'], cfg['vendor_fd']]
    artifacts.extend(item['fd'] for item in cfg['runtime'])
    argv = ['bwrap', '--unshare-user', '--unshare-ipc', '--unshare-pid',
            '--unshare-net', '--unshare-uts', '--die-with-parent', '--new-session',
            '--cap-drop', 'ALL', '--clearenv', '--dev', '/dev', '--proc', '/proc']
    binds = ((cfg['vendor_fd'], guest['vendor'], '0555'),
             (cfg['interp_fd'], guest['interp'], '0555'),
             (cfg['helper_fd'], guest['helper'], '0444'))
    binds = binds + tuple((item['fd'], item['guest'], '0555') for item in cfg['runtime'])
    for source_fd, target, perms in binds:
        # --ro-bind-data copies the exact sealed-descriptor bytes into the
        # namespace at setup: descriptor-bound (no pathname reopen), with the
        # executable/library mode pinned by --perms.
        argv += ['--perms', perms, '--ro-bind-data', str(source_fd), target]
    if mode == 'model':
        # The one-use credential pipe is copied into the namespace at setup:
        # bwrap consumes it (read to EOF), so the copy completes only when the
        # parent releases the credential after readiness.
        argv += ['--perms', '0400', '--ro-bind-data', str(CREDENTIAL_FD),
                 guest['credential']]
    # bubblewrap 0.11 removed --sizelimit; --size precedes its --tmpfs.
    argv += ['--size', str(cfg['scratch_size_bytes']), '--tmpfs', guest['scratch'],
             '--size', str(cfg['tmp_size_bytes']), '--tmpfs', '/tmp']
    for key, value in cfg['env_pairs']:
        argv += ['--setenv', key, value]
    for key, value in (('PYTHONHOME', '/pal/runtime'),
                       ('PAL_GUEST_HOME', guest['home']), ('PAL_GUEST_CONFIG', guest['config']),
                       ('PAL_GUEST_WORK', guest['work']), ('PAL_GUEST_SCRATCH', guest['scratch']),
                       ('PAL_GUEST_PATH_BIN', guest['path_bin']),
                       ('PAL_GUEST_LD', guest['ld_library_path']),
                       ('PAL_PASSTHROUGH', ','.join(cfg['passthrough_env_keys'])),
                       ('PAL_CREDENTIAL_FILE',
                        guest['credential'] if mode == 'model' else 'none')):
        argv += ['--setenv', key, value]
    tail = cfg['model_argv_tail'] if mode == 'model' else cfg['version_argv_tail']
    return argv + [guest['interp'], '-S', '-B', guest['helper'], 'guest', mode,
                   guest['vendor']] + list(tail)


def _stage(cfg, cgroup, mode, cred_source_fd):
    stdin_r, stdin_w = os.pipe()
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()
    gate_r, gate_w = os.pipe()
    # The one-use credential channel is created by the parent before the
    # supervisor starts and released only after model readiness. Its read end
    # is passed down unread: the credential value never enters this process,
    # and the wrapper consumes it once via --ro-bind-data.
    cred_r = cred_source_fd if mode == 'model' else None
    pid = os.fork()
    if pid == 0:
        try:
            os.dup2(stdin_r, 0)
            os.dup2(stdout_w, 1)
            os.dup2(stderr_w, 2)
            artifacts = {cfg['helper_fd'], cfg['interp_fd'], cfg['vendor_fd']}
            artifacts.update(item['fd'] for item in cfg['runtime'])
            keep = {0, 1, 2, gate_r} | artifacts
            if cred_r is not None:
                keep.add(cred_r)
            _close_except(keep)
            for fd in keep - {0, 1, 2}:
                try:
                    os.set_inheritable(fd, True)
                except OSError:
                    pass
            # The bootstrap waits until the supervisor has placed it in the
            # cgroup and verified the controls; only then may the wrapper run.
            if os.read(gate_r, 1) != b'R':
                os._exit(96)
            # Each wrapper run consumes the artifact descriptors to EOF (the
            # fd copy reads to end); rewind so the next phase copies the full
            # sealed snapshot again.
            for fd in artifacts:
                os.lseek(fd, 0, os.SEEK_SET)
            # The wrapper executes from its pathname after re-verifying the
            # admitted bytes: the host profiles the real bubblewrap path for
            # user namespaces (a memfd-exec'd copy runs restricted and cannot
            # configure the offline network namespace).
            digest = hashlib.sha256()
            size = 0
            wrapper_fd = os.open(cfg['wrapper_path'], os.O_RDONLY)
            while True:
                block = os.read(wrapper_fd, 65536)
                if not block:
                    break
                digest.update(block)
                size += len(block)
            os.close(wrapper_fd)
            if (digest.hexdigest() != cfg['wrapper_sha256']
                    or size != cfg['wrapper_size_bytes']):
                os._exit(97)
            os.execv(cfg['wrapper_path'], _bwrap_argv(cfg, mode))
        except BaseException:
            os._exit(98)
        os._exit(98)
    for fd in (stdin_r, stdout_w, stderr_w, gate_r):
        os.close(fd)
    if cred_r is not None:
        os.close(cred_r)
    try:
        cgroup.admit(pid)
    except BaseException:
        os.kill(pid, signal.SIGKILL)
        try:
            os.waitpid(pid, 0)
        except OSError:
            pass
        for fd in (stdin_w, stdout_r, stderr_r, gate_w):
            try:
                os.close(fd)
            except OSError:
                pass
        raise
    os.write(gate_w, b'R')
    os.close(gate_w)
    return {'pid': pid, 'stdin_w': stdin_w, 'stdout_r': stdout_r,
            'stderr_r': stderr_r}


def _try_reap(pid):
    try:
        done, status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return None
    return status if done == pid else _RUNNING


def _reap(pid, deadline_ms):
    while _now_ms() < deadline_ms:
        status = _try_reap(pid)
        if status is not _RUNNING:
            return status
        time.sleep(0.01)
    return _RUNNING


def _classify_stderr(sniff):
    text = bytes(sniff)
    for marker in (b'--pass-fd', b'Unknown option', b'unrecognized option'):
        if marker in text:
            return 'wrapper_option_unsupported'
    return None


def _run_version(cfg, cgroup, report_fd, liveness_fd, remaining_ms):
    deadline = _now_ms() + max(remaining_ms, 1)
    staged = _stage(cfg, cgroup, 'version', None)
    stdout = bytearray()
    sniff = bytearray()
    stderr_bytes = 0
    failure = None
    exit_code = None
    status = _RUNNING
    out_open = err_open = True
    try:
        while out_open or err_open or status is _RUNNING:
            if _now_ms() >= deadline:
                failure = failure or 'phase_timeout'
                break
            try:
                readable, _, _ = select.select(
                    [fd for fd in (staged['stdout_r'], staged['stderr_r'], liveness_fd)
                     if fd is not None], [], [], 0.05)
            except InterruptedError:
                continue
            if liveness_fd in readable and not os.read(liveness_fd, 1):
                return 'parent_lost'
            if staged['stdout_r'] in readable:
                block = os.read(staged['stdout_r'], CHUNK)
                if block == b'':
                    staged['stdout_r'] = None
                    out_open = False
                else:
                    stdout.extend(block)
                    if len(stdout) > cfg['max_version_output_bytes']:
                        failure = failure or 'version_output_limit'
                        break
            if staged['stderr_r'] in readable:
                block = os.read(staged['stderr_r'], CHUNK)
                if block == b'':
                    staged['stderr_r'] = None
                    err_open = False
                else:
                    stderr_bytes += len(block)
                    if len(sniff) < 4096:
                        sniff.extend(block[:4096 - len(sniff)])
            status = _try_reap(staged['pid'])
            if status is not _RUNNING and not out_open and not err_open:
                break
        if failure is None and status is _RUNNING:
            # A failed phase must not wait on a possibly still-running vendor;
            # the teardown below kills it. A successful phase gets the same
            # extra window as teardown so a loaded host cannot turn a clean
            # exit into an unreaped child.
            status = _reap(staged['pid'], deadline + 5000)
        if status is not _RUNNING and status is not None:
            exit_code = os.waitstatus_to_exitcode(status)
        if failure is None and exit_code is not None:
            if exit_code != 0:
                failure = _classify_stderr(sniff) or 'version_nonzero_exit'
            elif stderr_bytes != 0:
                failure = _classify_stderr(sniff) or 'version_stderr_nonzero'
            elif bytes(stdout).hex() != cfg['expected_version_output_hex']:
                failure = 'version_mismatch'
    finally:
        if not cgroup.kill(deadline + 5000):
            failure = failure or 'teardown_failed'
        _reap(staged['pid'], _now_ms() + 5000)
        for name in ('stdin_w', 'stdout_r', 'stderr_r'):
            if staged[name] is not None:
                try:
                    os.close(staged[name])
                except OSError:
                    pass
    _report(report_fd, {'type': 'version_done', 'code': failure, 'exit_code': exit_code,
                        'stderr_bytes': stderr_bytes})
    return failure is None


def _run_model(cfg, cgroup, report_fd, liveness_fd, prompt_fd, out_fd, err_fd, remaining_ms):
    deadline = _now_ms() + max(remaining_ms, 1)
    prompt_buf = bytearray()
    out_buf = bytearray()
    err_buf = bytearray()
    sniff = bytearray()
    out_total = 0
    err_total = 0
    prompt_open = True
    failure = None
    exit_code = None
    status = _RUNNING
    try:
        # Readiness precedes staging: the wrapper blocks consuming the
        # one-use credential channel during setup, so the credential crosses
        # only after the parent sees ready and releases it.
        _report(report_fd, {'type': 'ready'})
        staged = None
        while staged is None:
            staged = _stage(cfg, cgroup, 'model', CREDENTIAL_FD)
        os.set_blocking(staged['stdin_w'], False)
        os.set_blocking(out_fd, False)
        os.set_blocking(err_fd, False)
        while status is _RUNNING:
            if _now_ms() >= deadline:
                failure = failure or 'phase_timeout'
                break
            watched = [fd for fd in (staged['stdout_r'], staged['stderr_r'], liveness_fd)
                       if fd is not None]
            if prompt_open:
                watched.append(prompt_fd)
            writers = [fd for fd, buf in ((staged['stdin_w'], prompt_buf),
                                          (out_fd, out_buf), (err_fd, err_buf))
                       if fd is not None and buf]
            try:
                readable, writable, _ = select.select(watched, writers, [], 0.05)
            except InterruptedError:
                continue
            if liveness_fd in readable and not os.read(liveness_fd, 1):
                return 'parent_lost'
            if prompt_open and prompt_fd in readable:
                block = os.read(prompt_fd, CHUNK)
                if block == b'':
                    # Parent EOF: stop accepting, but every accepted byte
                    # must still reach guest stdin before its own EOF.
                    prompt_open = False
                    try:
                        os.close(prompt_fd)
                    except OSError:
                        pass
                elif block:
                    prompt_buf.extend(block)
            for fd, buf in ((staged['stdin_w'], prompt_buf), (out_fd, out_buf),
                            (err_fd, err_buf)):
                if fd is not None and fd in writable and buf:
                    try:
                        written = os.write(fd, buf)
                    except BlockingIOError:
                        written = 0
                    except OSError:
                        # Input conservation is the invariant on the prompt
                        # relay; an output pipe failure is a relay failure,
                        # not a lost-prompt condition.
                        failure = failure or ('model_input_incomplete'
                            if fd is staged['stdin_w'] else 'model_relay_failed')
                        written = 0
                    del buf[:written]
            if (not prompt_open and not prompt_buf
                    and staged['stdin_w'] is not None):
                fd, staged['stdin_w'] = staged['stdin_w'], None
                os.close(fd)
            # Relay byte caps mirror the parent's output limits: exceeding one
            # fails the phase immediately instead of buffering unboundedly.
            if staged['stdout_r'] in readable:
                block = os.read(staged['stdout_r'], CHUNK)
                if block:
                    out_total += len(block)
                    if out_total > cfg['max_stdout_bytes']:
                        failure = failure or 'model_output_limit'
                    else:
                        out_buf.extend(block)
            if staged['stderr_r'] in readable:
                block = os.read(staged['stderr_r'], CHUNK)
                if block:
                    err_total += len(block)
                    if len(sniff) < 4096:
                        sniff.extend(block[:4096 - len(sniff)])
                    if err_total > cfg['max_stderr_bytes']:
                        failure = failure or 'model_output_limit'
                    else:
                        err_buf.extend(block)
            if failure == 'model_output_limit':
                break
            status = _try_reap(staged['pid'])
        if failure is None and status is _RUNNING:
            # A failed phase (for example the output cap) must not wait on a
            # still-running vendor; the teardown below kills it. A successful
            # phase gets the same extra window as teardown so a loaded host
            # cannot turn a clean exit into an unreaped child.
            status = _reap(staged['pid'], deadline + 5000)
        if status is not _RUNNING and status is not None:
            exit_code = os.waitstatus_to_exitcode(status)
        # Drain guest pipes to EOF; teardown kills escaped descendants still
        # holding the write ends. Totals stay capped here too. A cap breach
        # skips the drains: fail fast inside the caller's deadline.
        if failure is not None:
            staged['stdout_r'] = None
            staged['stderr_r'] = None
            out_buf = bytearray()
            err_buf = bytearray()
            prompt_buf = bytearray()
        drain_deadline = _now_ms() + 5000
        while (staged['stdout_r'] is not None or staged['stderr_r'] is not None) \
                and _now_ms() < drain_deadline:
            watched = [fd for fd in (staged['stdout_r'], staged['stderr_r']) if fd is not None]
            try:
                readable, _, _ = select.select(watched, [], [], 0.05)
            except (InterruptedError, OSError):
                break
            if staged['stdout_r'] in readable:
                block = os.read(staged['stdout_r'], CHUNK)
                if block:
                    out_total += len(block)
                    if out_total > cfg['max_stdout_bytes']:
                        failure = failure or 'model_output_limit'
                    else:
                        out_buf.extend(block)
                else:
                    staged['stdout_r'] = None
            if staged['stderr_r'] in readable:
                block = os.read(staged['stderr_r'], CHUNK)
                if block:
                    err_total += len(block)
                    if len(sniff) < 4096:
                        sniff.extend(block[:4096 - len(sniff)])
                    if err_total > cfg['max_stderr_bytes']:
                        failure = failure or 'model_output_limit'
                    else:
                        err_buf.extend(block)
                else:
                    staged['stderr_r'] = None
            if failure == 'model_output_limit':
                break
            if not readable:
                break
        if not cgroup.kill(deadline + 5000):
            failure = failure or 'teardown_failed'
        _reap(staged['pid'], _now_ms() + 5000)
        flush_deadline = _now_ms() + 5000
        while (out_buf or err_buf or prompt_buf) and _now_ms() < flush_deadline:
            for fd, buf in ((out_fd, out_buf), (err_fd, err_buf),
                            (staged['stdin_w'], prompt_buf)):
                if fd is not None and buf:
                    try:
                        written = os.write(fd, buf)
                    except BlockingIOError:
                        written = 0
                    except OSError:
                        failure = failure or ('model_input_incomplete'
                            if fd is staged['stdin_w'] else 'model_relay_failed')
                        written = 0
                    del buf[:written]
            if (not prompt_open and not prompt_buf
                    and staged['stdin_w'] is not None):
                fd, staged['stdin_w'] = staged['stdin_w'], None
                os.close(fd)
            if out_buf or err_buf or prompt_buf:
                time.sleep(0.01)
        if failure is None and exit_code is not None and exit_code != 0:
            failure = _classify_stderr(sniff) or 'model_nonzero_exit'
    finally:
        for name in ('stdin_w', 'stdout_r', 'stderr_r'):
            if staged[name] is not None:
                try:
                    os.close(staged[name])
                except (OSError, KeyError):
                    pass
    if failure is None and (out_buf or err_buf or prompt_buf):
        failure = 'model_output_limit' if (out_buf or err_buf) else 'model_input_incomplete'
    _report(report_fd, {'type': 'model_done', 'code': failure, 'exit_code': exit_code})
    return failure is None


def guest():
    # Namespace entry: read the one-use credential channel, close every
    # non-approved descriptor, construct the allowlist environment, and exec
    # the verified vendor snapshot. The credential must never arrive through
    # the launcher environment.
    mode, vendor = sys.argv[2], sys.argv[3]
    if 'ANTHROPIC_API_KEY' in os.environ:
        os._exit(95)
    env = {key: os.environ[key] for key in os.environ['PAL_PASSTHROUGH'].split(',')}
    env['HOME'] = os.environ['PAL_GUEST_HOME']
    env['CLAUDE_CONFIG_DIR'] = os.environ['PAL_GUEST_CONFIG']
    env['PATH'] = os.environ['PAL_GUEST_PATH_BIN']
    env['LD_LIBRARY_PATH'] = os.environ['PAL_GUEST_LD']
    credential_file = os.environ['PAL_CREDENTIAL_FILE']
    if credential_file != 'none':
        # The wrapper copied the one-use credential pipe into the namespace as
        # this file; read it once, bounded by the parent's credential bound.
        fd = os.open(credential_file, os.O_RDONLY)
        data = bytearray()
        while len(data) < 8:
            block = os.read(fd, 8 - len(data))
            if not block:
                os._exit(94)
            data.extend(block)
        size = int.from_bytes(bytes(data), 'big')
        if not 1 <= size <= 4096:  # mirrors the parent's credential bound
            os._exit(94)
        while len(data) < 8 + size:
            block = os.read(fd, 8 + size - len(data))
            if not block:
                os._exit(94)
            data.extend(block)
        os.close(fd)
        env['ANTHROPIC_API_KEY'] = bytes(data[8:]).decode('utf-8')
    for name in ('HOME', 'CLAUDE_CONFIG_DIR'):
        os.makedirs(env[name], exist_ok=True)
    os.makedirs(os.environ['PAL_GUEST_WORK'], exist_ok=True)
    os.makedirs(os.environ['PAL_GUEST_SCRATCH'], exist_ok=True)
    os.chdir(os.environ['PAL_GUEST_WORK'])
    _close_except({0, 1, 2})
    os.execve(vendor, [vendor] + sys.argv[4:], env)


def supervise():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    # The CONF line arrives on fd 0 (the parent-supplied stdin pipe) and names
    # the inherited channel descriptors; install them at the canonical slots
    # before anything else runs. The whole line is hex-encoded, so the CONF
    # marker is validated on the decoded bytes.
    payload = bytes.fromhex(_read_line(CONTROL_FD, 1 << 20).decode('ascii'))
    if not payload.startswith(b'CONF '):
        os._exit(93)
    cfg = json.loads(payload[5:].decode('utf-8'))
    _install_channels(cfg)
    control, out_fd, err_fd = CONTROL_FD, RELAY_OUT_FD, RELAY_ERR_FD
    report_fd, liveness_fd, prompt_fd, cred_fd = (REPORT_FD, LIVENESS_FD,
                                                  PROMPT_FD, CREDENTIAL_FD)
    try:
        _enable_root_controls(cfg['cgroup_root'])
        cgroup = Cgroup(cfg)
        cgroup.create()
    except OSError:
        _report(report_fd, {'type': 'error', 'code': 'cgroup_setup_failed'})
        return
    _report(report_fd, {'type': 'started'})
    try:
        while True:
            try:
                readable, _, _ = select.select([control, liveness_fd], [], [])
            except InterruptedError:
                continue
            if liveness_fd in readable and not os.read(liveness_fd, 1):
                return
            if control not in readable:
                continue
            parts = _read_line(control, 4096).split(b' ')
            command = parts[0]
            remaining_ms = int(parts[1]) if len(parts) > 1 else 0
            if command == b'SHUTDOWN':
                return
            if command == b'VERSION':
                if _run_version(cfg, cgroup, report_fd, liveness_fd, remaining_ms) in (False, 'parent_lost'):
                    return
            elif command == b'MODEL':
                if _run_model(cfg, cgroup, report_fd, liveness_fd, prompt_fd, out_fd,
                              err_fd, remaining_ms) in (False, 'parent_lost'):
                    return
            else:
                _report(report_fd, {'type': 'error', 'code': 'protocol'})
                return
    finally:
        cgroup.kill(_now_ms() + 10000)
        try:
            os.rmdir(cgroup.path)
        except OSError:
            pass


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'guest':
        guest()
    elif len(sys.argv) >= 2 and sys.argv[1] == 'supervise':
        supervise()
    else:
        os._exit(99)
'''


def _helper_digest():
    return sha256(HELPER_SOURCE.encode('utf-8')).hexdigest()


def _helper_source(launch):
    """The sealed helper source selected by the launch's closed egress value:
    the frozen offline helper, or the strictly-additive relay helper for the
    relay-fixed-origin branch (L9 Amendment 1)."""
    if launch.egress_policy == EGRESS_RELAY:
        return RELAY_HELPER_SOURCE
    return HELPER_SOURCE


def _linux_path(value):
    """Linux host/guest path rules, host-independent so that declaration and
    digests behave identically on every development platform."""
    return (type(value) is str and value.startswith('/') and value != '/'
            and '\\' not in value and '\x00' not in value
            and '..' not in value.split('/') and 1 <= len(value.encode('utf-8')) <= 4096)


@dataclass(frozen=True, slots=True)
class LinuxArtifactPin:
    """Independently supplied absolute path plus exact content identity."""
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        if not _linux_path(self.path):
            raise ValueError('linux_artifact_pin_invalid')
        if (type(self.sha256) is not str
                or re.fullmatch('[0-9a-f]{64}', self.sha256) is None):
            raise ValueError('linux_artifact_pin_invalid')
        integer('size_bytes', self.size_bytes, 1, VENDOR_SIZE_CAP)


@dataclass(frozen=True, slots=True)
class LinuxRuntimeFile:
    """One runtime-closure member bound from a host path to a guest path."""
    guest_path: str
    host_path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        for name in ('guest_path', 'host_path'):
            if not _linux_path(getattr(self, name)):
                raise ValueError('linux_runtime_file_invalid')
        if (type(self.sha256) is not str
                or re.fullmatch('[0-9a-f]{64}', self.sha256) is None):
            raise ValueError('linux_runtime_file_invalid')
        integer('size_bytes', self.size_bytes, 1, RUNTIME_MEMBER_SIZE_CAP)


def _guest_path(value):
    if not _linux_path(value):
        raise ValueError('linux_launch_spec_invalid')


def _bound(name, value, low, high):
    """Fixed-code range check for every declared numeric policy field."""
    try:
        integer(name, value, low, high)
    except Exception:
        raise ValueError('linux_launch_spec_invalid') from None


@dataclass(frozen=True, slots=True)
class LinuxLaunchSpec:
    """Immutable offline containment policy; declaration-only construction.

    Construction performs NO filesystem access: the helper pin is compared
    against the checked-in in-memory source only, so inert profiles can be
    constructed on any host. Verification and memfd sealing happen later in
    :func:`run_linux_contained_process`.
    """
    wrapper: LinuxArtifactPin = field(repr=False)
    helper_sha256: str
    interpreter: LinuxArtifactPin = field(repr=False)
    supervisor_python_home: str
    vendor_guest_path: str
    helper_guest_path: str
    vendor_size_bytes: int
    expected_version_output: str
    cgroup_root: str
    runtime_files: tuple[LinuxRuntimeFile, ...] = ()
    launch_schema: str = LAUNCH_SCHEMA
    helper_protocol_version: str = HELPER_PROTOCOL_VERSION
    guest_home_path: str = '/pal/home'
    guest_config_path: str = '/pal/home/.claude'
    guest_work_path: str = '/pal/work'
    guest_scratch_path: str = '/pal/scratch'
    guest_credential_path: str = '/pal/credential'
    interpreter_guest_path: str = '/pal/runtime/bin/python3'
    guest_ld_library_path: str = '/pal/runtime/lib'
    guest_tmp_size_bytes: int = TMP_SIZE_CAP
    scratch_size_bytes: int = SCRATCH_SIZE_CAP
    memory_max_bytes: int = MEMORY_MAX_CAP
    memory_swap_max_bytes: int = 0
    pids_max: int = PIDS_MAX_CAP
    namespaces: tuple[str, ...] = NAMESPACES
    egress_policy: str = EGRESS_OFFLINE
    relay_trust: RelayTrustConfig | None = None
    allowed_guest_env: tuple[str, ...] = DEFAULT_GUEST_ENV
    version_argument: str = '--version'
    max_version_output_bytes: int = 4096
    cgroup_allocation_rule: str = ALLOCATION_RULE

    def __post_init__(self):
        if self.launch_schema != LAUNCH_SCHEMA:
            raise ValueError('linux_launch_spec_invalid')
        if self.helper_protocol_version != HELPER_PROTOCOL_VERSION:
            raise ValueError('linux_launch_spec_invalid')
        if (type(self.wrapper) is not LinuxArtifactPin
                or type(self.interpreter) is not LinuxArtifactPin):
            raise ValueError('linux_launch_spec_invalid')
        if self.wrapper.size_bytes > WRAPPER_SIZE_CAP:
            raise ValueError('linux_launch_spec_invalid')
        if self.interpreter.size_bytes > INTERPRETER_SIZE_CAP:
            raise ValueError('linux_launch_spec_invalid')
        if (self.wrapper.path == self.interpreter.path
                or self.wrapper.sha256 == self.interpreter.sha256):
            raise ValueError('linux_launch_spec_invalid')
        if (type(self.runtime_files) is not tuple
                or not 1 <= len(self.runtime_files) <= RUNTIME_FILE_COUNT_CAP
                or any(type(item) is not LinuxRuntimeFile for item in self.runtime_files)):
            raise ValueError('linux_launch_spec_invalid')
        if not _linux_path(self.supervisor_python_home):
            raise ValueError('linux_launch_spec_invalid')
        for name in ('vendor_guest_path', 'helper_guest_path', 'guest_home_path',
                     'guest_config_path', 'guest_work_path', 'guest_scratch_path',
                     'guest_credential_path', 'interpreter_guest_path'):
            _guest_path(getattr(self, name))
        _guest_path(self.cgroup_root)
        guests = [getattr(self, name) for name in
                  ('vendor_guest_path', 'helper_guest_path', 'guest_home_path',
                   'guest_config_path', 'guest_work_path', 'guest_scratch_path',
                   'guest_credential_path', 'interpreter_guest_path')]
        guests += [item.guest_path for item in self.runtime_files]
        if len(set(guests)) != len(guests):
            raise ValueError('linux_launch_spec_invalid')
        if any(item.guest_path == self.guest_ld_library_path
               or item.host_path in (self.wrapper.path, self.interpreter.path)
               or item.sha256 in (self.wrapper.sha256, self.interpreter.sha256)
               for item in self.runtime_files):
            raise ValueError('linux_launch_spec_invalid')
        _bound('vendor_size_bytes', self.vendor_size_bytes, 1, VENDOR_SIZE_CAP)
        _bound('guest_tmp_size_bytes', self.guest_tmp_size_bytes, 1, TMP_SIZE_CAP)
        _bound('scratch_size_bytes', self.scratch_size_bytes, 1, SCRATCH_SIZE_CAP)
        _bound('memory_max_bytes', self.memory_max_bytes, 1, MEMORY_MAX_CAP)
        _bound('memory_swap_max_bytes', self.memory_swap_max_bytes, 0, 0)
        _bound('pids_max', self.pids_max, 1, PIDS_MAX_CAP)
        if self.namespaces != NAMESPACES:
            raise ValueError('linux_launch_spec_invalid')
        # Two-value closed egress branch (L9 Amendment 1): offline keeps the
        # frozen helper digest, an empty relay surface and no trust record;
        # relay-fixed-origin keeps the relay helper digest and the typed
        # reviewed trust record. Every cross-pinned combination and every
        # neighbor value refuses with the fixed code.
        if self.egress_policy == EGRESS_OFFLINE:
            if self.helper_sha256 != _helper_digest():
                raise ValueError('linux_launch_spec_invalid')
            if self.relay_trust is not None:
                raise ValueError('linux_launch_spec_invalid')
        elif self.egress_policy == EGRESS_RELAY:
            if self.helper_sha256 != RELAY_HELPER_DIGEST:
                raise ValueError('linux_launch_spec_invalid')
            if type(self.relay_trust) is not RelayTrustConfig:
                raise ValueError('linux_launch_spec_invalid')
        else:
            raise ValueError('linux_launch_spec_invalid')
        if (type(self.allowed_guest_env) is not tuple
                or any(type(key) is not str
                       or re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', key) is None
                       for key in self.allowed_guest_env)
                or sorted(self.allowed_guest_env) != list(self.allowed_guest_env)
                or len(set(self.allowed_guest_env)) != len(self.allowed_guest_env)
                or not REQUIRED_GUEST_ENV <= set(self.allowed_guest_env)):
            raise ValueError('linux_launch_spec_invalid')
        if self.version_argument != '--version':
            raise ValueError('linux_launch_spec_invalid')
        encoded = self.expected_version_output.encode('utf-8') \
            if type(self.expected_version_output) is str else b''
        if (not encoded.endswith(b'\n') or b'\n' in encoded[:-1]
                or any(byte < 0x20 or byte > 0x7e for byte in encoded[:-1])
                or not 2 <= len(encoded) <= MAX_VERSION_OUTPUT_BYTES):
            raise ValueError('linux_launch_spec_invalid')
        _bound('max_version_output_bytes', self.max_version_output_bytes, 1,
               MAX_VERSION_OUTPUT_BYTES)
        if self.cgroup_allocation_rule != ALLOCATION_RULE:
            raise ValueError('linux_launch_spec_invalid')

    def policy_dict(self):
        """Public digest input: pins and rules only; never a credential,
        prompt, random allocation name, descriptor number, PID, or port."""
        relay_bearing = self.egress_policy == EGRESS_RELAY
        policy = dict(
            launch_schema=self.launch_schema,
            helper=dict(protocol_version=self.helper_protocol_version,
                        sha256=self.helper_sha256),
            wrapper=dict(path=self.wrapper.path, sha256=self.wrapper.sha256,
                         size_bytes=self.wrapper.size_bytes),
            interpreter=dict(path=self.interpreter.path, sha256=self.interpreter.sha256,
                             size_bytes=self.interpreter.size_bytes,
                             supervisor_python_home=self.supervisor_python_home),
            runtime_closure=[dict(guest_path=item.guest_path, host_path=item.host_path,
                                  sha256=item.sha256, size_bytes=item.size_bytes)
                             for item in self.runtime_files],
            guest_layout=dict(vendor=self.vendor_guest_path, helper=self.helper_guest_path,
                              interpreter=self.interpreter_guest_path, home=self.guest_home_path,
                              config=self.guest_config_path, work=self.guest_work_path,
                              scratch=self.guest_scratch_path,
                              credential=self.guest_credential_path,
                              ld_library_path=self.guest_ld_library_path, tmp='/tmp'),
            namespaces=list(self.namespaces),
            mounts=dict(vendor='ro-bind-sealed-memfd', helper='ro-bind-sealed-memfd',
                        interpreter='ro-bind-sealed-memfd', runtime='ro-bind-sealed-memfd',
                        scratch=dict(kind='tmpfs', size_limit_bytes=self.scratch_size_bytes),
                        tmp=dict(kind='tmpfs', size_limit_bytes=self.guest_tmp_size_bytes),
                        dev='minimal-bwrap-dev', proc='private-proc',
                        writable_host_surfaces=[]),
            environment=dict(allowlist=list(self.allowed_guest_env),
                             substitutions=dict(HOME='guest-home',
                                                CLAUDE_CONFIG_DIR='guest-config',
                                                PATH='guest-runtime-bin',
                                                LD_LIBRARY_PATH='guest-runtime-lib'),
                             credential='one-use-anonymous-pipe-model-phase-only',
                             supervisor_environment='minimal-no-credential'),
            descriptors=dict(guest_baseline=[0, 1, 2], credential_fd='model-phase-only',
                             artifacts='sealed-memfd-no-pathname-reopen',
                             inherited_from_parent=(
                                 [RELAY_INHERITED_FROM_PARENT]
                                 if relay_bearing else [])),
            resources=dict(memory_max_bytes=self.memory_max_bytes,
                           memory_swap_max_bytes=self.memory_swap_max_bytes,
                           pids_max=self.pids_max,
                           scratch_size_bytes=self.scratch_size_bytes,
                           tmp_size_bytes=self.guest_tmp_size_bytes),
            protocol=dict(phases=['version', 'model'], version_argument=self.version_argument,
                          expected_version_output=self.expected_version_output,
                          max_version_output_bytes=self.max_version_output_bytes,
                          version_requires='exit-zero-empty-stderr-exact-output',
                          teardown_between_phases='verified-empty-subtree',
                          retries='none', per_phase_executions=1),
            readiness='model-namespace-staged-and-cgroup-verified-before-credential-release',
            cleanup='cgroup-kill-verified-empty-then-reap',
            egress=dict(policy=self.egress_policy, production_egress='unavailable',
                        host_network_fallback='forbidden',
                        relay=('bounded-fixed-origin-validating-relay'
                               if relay_bearing
                               else 'not-shipped-in-this-node')),
            cgroup=dict(root=self.cgroup_root, allocation_rule=self.cgroup_allocation_rule,
                        supervisor='outside-vendor-cgroup',
                        bootstrap='gate-until-placed-and-verified'),
            vendor_size_bytes=self.vendor_size_bytes)
        if relay_bearing and type(self.relay_trust) is RelayTrustConfig:
            # The relay-bearing policy section: the relay helper pin (the
            # relay engine protocol names the section's helper entry), the
            # exact reviewed per-call port window and the typed reviewed
            # trust record. The drawn port itself, the channel descriptor
            # number and any runtime-discovered value are never inputs. A
            # constructible relay launch ALWAYS carries the typed trust
            # record (the cross-pin refusal); an attribute-tampered object
            # without one digests WITHOUT the relay section, a shape no
            # constructible launch can ever produce.
            policy['relay'] = dict(
                port_window=list(RELAY_PORT_WINDOW),
                helper=dict(protocol_version=RELAY_PROTOCOL_VERSION,
                            sha256=self.helper_sha256),
                trust=self.relay_trust.policy_dict())
        return policy


class _LinuxPhaseCounters:
    """In-memory per-process engineering counters; not persistence."""

    def __init__(self):
        self._lock = threading.Lock()
        self._values = {'version_executions': 0, 'model_executions': 0,
                        'contained_calls': 0, 'teardown_failures': 0}

    def _bump(self, name):
        with self._lock:
            self._values[name] += 1

    def version_execution(self):
        self._bump('version_executions')

    def model_execution(self):
        self._bump('model_executions')

    def contained_call(self):
        self._bump('contained_calls')

    def teardown_failure(self):
        self._bump('teardown_failures')

    def snapshot(self):
        with self._lock:
            return dict(self._values)


LINUX_PHASE_COUNTERS = _LinuxPhaseCounters()


def _open_pinned(path):
    # FIFO-safe: O_NONBLOCK never blocks a regular image; nonregular files are
    # rejected by the callers. O_NOFOLLOW refuses symlink substitution.
    return os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0)
                   | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))


def verify_pinned_bytes(path, expected_sha256, expected_size, *, max_bytes, require_elf):
    """Hash one pathname exactly once for admission; returns the first bytes.

    This alone never proves execution: callers must execute the sealed
    snapshot, never a reopened pathname.
    """
    fd = _open_pinned(path)
    failure = None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
            raise ValueError('research_process_artifact_invalid')
        digest, size, prefix = sha256(), 0, b''
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            if not prefix:
                prefix = block[:4]
            size += len(block)
            if size > max_bytes:
                raise ValueError('research_process_artifact_invalid')
            digest.update(block)
        if (size != expected_size or digest.hexdigest() != expected_sha256
                or (require_elf and not prefix.startswith(ELF_MAGIC))):
            raise ValueError('research_process_artifact_invalid')
    except BaseException as error:
        failure = error
    finally:
        try:
            os.close(fd)
        except BaseException as error:
            failure = failure if failure is not None else error
    if failure is not None:
        raise failure
    return prefix


def _seal_payload(payload, expected_sha256):
    """Copy exact in-memory bytes into a sealed immutable memfd snapshot."""
    memfd = os.memfd_create('pal-artifact',
                            os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING | _MFD_EXEC)
    failure = None
    try:
        digest, offset = sha256(), 0
        view = memoryview(payload)
        while offset < len(view):
            written = os.write(memfd, view[offset:offset + 65536])
            offset += written
            digest.update(view[offset - written:offset])
        if digest.hexdigest() != expected_sha256 or offset != len(payload):
            raise ValueError('research_process_artifact_invalid')
        os.lseek(memfd, 0, os.SEEK_SET)
        os.fchmod(memfd, 0o555)
        fcntl.fcntl(memfd, _F_ADD_SEALS, _F_SEAL_ALL)
    except BaseException as error:
        failure = error
    finally:
        if failure is not None:
            try:
                os.close(memfd)
            except OSError:
                pass
    if failure is not None:
        raise failure
    return memfd


def _seal_file(path, expected_sha256, expected_size, max_bytes, require_elf):
    """Verify a pathname once, then seal its bytes; the executed image is the
    sealed snapshot, not the pathname."""
    fd = _open_pinned(path)
    failure = None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
            raise ValueError('research_process_artifact_invalid')
        digest, size, prefix = sha256(), 0, b''
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            if not prefix:
                prefix = block[:4]
            size += len(block)
            digest.update(block)
        if (size != expected_size or size > max_bytes
                or digest.hexdigest() != expected_sha256
                or (require_elf and not prefix.startswith(ELF_MAGIC))):
            raise ValueError('research_process_artifact_invalid')
        os.lseek(fd, 0, os.SEEK_SET)
        memfd = os.memfd_create('pal-artifact',
                                os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING | _MFD_EXEC)
        try:
            snapshot = sha256()
            os.lseek(fd, 0, os.SEEK_SET)
            while True:
                block = os.read(fd, 65536)
                if not block:
                    break
                offset = 0
                while offset < len(block):
                    offset += os.write(memfd, memoryview(block)[offset:])
                snapshot.update(block)
            if snapshot.hexdigest() != expected_sha256:
                raise ValueError('research_process_artifact_invalid')
            os.lseek(memfd, 0, os.SEEK_SET)
            if os.read(memfd, 4)[:4] != prefix[:4]:
                raise ValueError('research_process_artifact_invalid')
            # Rewind: consumers (the wrapper's fd copy) read from the current
            # offset, so the sealed snapshot must rest at zero.
            os.lseek(memfd, 0, os.SEEK_SET)
            os.fchmod(memfd, 0o555)
            fcntl.fcntl(memfd, _F_ADD_SEALS, _F_SEAL_ALL)
            return memfd
        except BaseException:
            try:
                os.close(memfd)
            except OSError:
                pass
            raise
    except BaseException as error:
        failure = error
    finally:
        try:
            os.close(fd)
        except BaseException as error:
            failure = failure if failure is not None else error
    if failure is not None:
        raise failure


def _check_no_elevation(path):
    info = os.stat(path, follow_symlinks=False)
    if info.st_mode & (stat.S_ISUID | stat.S_ISGID):
        raise ValueError('research_process_wrapper_elevated')
    try:
        if os.getxattr(path, 'security.capability'):
            raise ValueError('research_process_wrapper_elevated')
    except OSError:
        pass


def _fresh_copy(fd):
    """Duplicate a descriptor to a number >= 100, safe from target reuse."""
    return fcntl.fcntl(fd, fcntl.F_DUPFD, 100)


class _Admission:
    """Sealed descriptor snapshots retained through cleanup."""

    __slots__ = ('vendor_fd', 'wrapper_fd', 'helper_fd', 'interp_fd',
                 'runtime_fds', 'closed')

    def __init__(self, spec, launch):
        if sys.platform != 'linux':
            raise ResearchProcessError('research_process_platform_unsupported')
        if not hasattr(os, 'memfd_create'):
            raise ResearchProcessError('research_process_memfd_unavailable')
        # Egress-driven source selection (L9 Amendment 1): the sealed helper
        # bytes are the frozen offline source or the strictly-additive relay
        # helper, per the launch's closed egress value; the digest pin above
        # already guarantees the matching value, so a mismatch here is an
        # artifact refusal. The sealed source is read back by the native
        # probes to prove the selection.
        helper_bytes = _helper_source(launch).encode('utf-8')
        if sha256(helper_bytes).hexdigest() != launch.helper_sha256:
            raise ValueError('research_process_artifact_invalid')
        if (spec.executable_sha256 in (launch.wrapper.sha256, launch.interpreter.sha256)
                or spec.argv[0] in (launch.wrapper.path, launch.interpreter.path)):
            raise ValueError('research_process_artifact_invalid')
        self.closed = False
        self.vendor_fd = self.wrapper_fd = self.helper_fd = self.interp_fd = None
        self.runtime_fds = []
        failure = None
        try:
            verify_pinned_bytes(launch.wrapper.path, launch.wrapper.sha256,
                                launch.wrapper.size_bytes, max_bytes=WRAPPER_SIZE_CAP,
                                require_elf=True)
            _check_no_elevation(launch.wrapper.path)
            verify_pinned_bytes(launch.interpreter.path, launch.interpreter.sha256,
                                launch.interpreter.size_bytes,
                                max_bytes=INTERPRETER_SIZE_CAP, require_elf=True)
            verify_pinned_bytes(spec.argv[0], spec.executable_sha256,
                                launch.vendor_size_bytes,
                                max_bytes=spec.max_executable_bytes, require_elf=True)
            for item in launch.runtime_files:
                verify_pinned_bytes(item.host_path, item.sha256, item.size_bytes,
                                    max_bytes=RUNTIME_MEMBER_SIZE_CAP, require_elf=False)
            self.vendor_fd = _seal_file(spec.argv[0], spec.executable_sha256,
                                        launch.vendor_size_bytes,
                                        spec.max_executable_bytes, True)
            self.wrapper_fd = _seal_file(launch.wrapper.path, launch.wrapper.sha256,
                                         launch.wrapper.size_bytes, WRAPPER_SIZE_CAP, True)
            self.interp_fd = _seal_file(launch.interpreter.path, launch.interpreter.sha256,
                                        launch.interpreter.size_bytes,
                                        INTERPRETER_SIZE_CAP, True)
            self.helper_fd = _seal_payload(helper_bytes, launch.helper_sha256)
            for item in launch.runtime_files:
                self.runtime_fds.append(_seal_file(item.host_path, item.sha256,
                                                   item.size_bytes,
                                                   RUNTIME_MEMBER_SIZE_CAP, False))
            if not Path(launch.cgroup_root).is_dir():
                raise ValueError('research_process_cgroup_unavailable')
            controllers = Path(launch.cgroup_root, 'cgroup.controllers')
            if not controllers.is_file():
                raise ValueError('research_process_cgroup_unavailable')
            available = controllers.read_text().split()
            if 'memory' not in available or 'pids' not in available:
                raise ValueError('research_process_cgroup_unavailable')
            if not Path(launch.supervisor_python_home).is_dir():
                raise ValueError('research_process_interpreter_home_invalid')
        except BaseException as error:
            self.close()
            failure = error
        if failure is not None:
            raise failure

    def protect(self):
        """Move every sealed snapshot to a descriptor >= 100 so later channel
        placement can never close one."""
        for name in ('vendor_fd', 'wrapper_fd', 'helper_fd', 'interp_fd'):
            fresh = _fresh_copy(getattr(self, name))
            os.close(getattr(self, name))
            setattr(self, name, fresh)
        self.runtime_fds = [self._protect_one(fd) for fd in self.runtime_fds]

    @staticmethod
    def _protect_one(fd):
        fresh = _fresh_copy(fd)
        os.close(fd)
        return fresh

    def close(self):
        if self.closed:
            return
        self.closed = True
        for fd in (self.vendor_fd, self.wrapper_fd, self.helper_fd, self.interp_fd,
                   *self.runtime_fds):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass


def _guest_configuration(spec, launch):
    """Build the supervisor configuration inputs and the separated credential.

    The credential value never enters the configuration, the supervisor
    environment, or any launcher argv; it travels only the one-use bounded
    anonymous pipe after readiness. HOME, CLAUDE_CONFIG_DIR and
    LD_LIBRARY_PATH are substituted with guest literals, never passed through.
    """
    env = dict(spec.environment)
    credential = env.pop('ANTHROPIC_API_KEY', None)
    if (type(credential) is not str or not 1 <= len(credential) <= MAX_CREDENTIAL_BYTES
            or any(not 33 <= ord(character) <= 126 for character in credential)):
        raise ResearchProcessError('research_process_launch_credential_missing')
    forbidden = set(env) - set(launch.allowed_guest_env)
    if forbidden:
        raise ResearchProcessError('research_process_launch_env_forbidden')
    passthrough = tuple(sorted(key for key in env if key not in SUBSTITUTED_ENV))
    pairs = tuple((key, env[key]) for key in passthrough)
    return pairs, credential


def _supervisor_configuration(spec, launch, *, wrapper_fd, helper_fd, interp_fd,
                              vendor_fd, runtime_fds, allocation, report_fd,
                              liveness_fd, prompt_fd, credential_fd,
                              relay_channel_fd=None, relay_port=None):
    """Pure supervisor configuration; no I/O and no credential value.

    The channel descriptors are the parent-side numbers inherited via
    ``pass_fds``; the supervisor installs them at its canonical 3..6 itself.
    A relay-bearing launch additionally names the inherited relay channel
    descriptor and the one drawn relay port: both are required, the channel
    number must clear the supervisor's canonical 3..6 slots, and the port must
    sit inside the exact reviewed (20000, 32767) window. The keys never exist
    on the offline branch (whose CONF bytes stay frozen), and supplying them
    for an offline launch refuses.
    """
    configuration = dict(
        wrapper_fd=wrapper_fd, helper_fd=helper_fd, interp_fd=interp_fd,
        vendor_fd=vendor_fd,
        wrapper_path=launch.wrapper.path, wrapper_sha256=launch.wrapper.sha256,
        wrapper_size_bytes=launch.wrapper.size_bytes,
        report_fd=report_fd, liveness_fd=liveness_fd, prompt_fd=prompt_fd,
        credential_fd=credential_fd,
        runtime=[dict(guest=item.guest_path, fd=fd)
                 for item, fd in zip(launch.runtime_files, runtime_fds)],
        supervisor_pid=os.getpid(), cgroup_root=launch.cgroup_root,
        alloc_name=allocation, memory_max_bytes=launch.memory_max_bytes,
        memory_swap_max_bytes=launch.memory_swap_max_bytes,
        pids_max=launch.pids_max,
        guest=dict(vendor=launch.vendor_guest_path,
                   helper=launch.helper_guest_path,
                   interp=launch.interpreter_guest_path,
                   home=launch.guest_home_path, config=launch.guest_config_path,
                   work=launch.guest_work_path, scratch=launch.guest_scratch_path,
                   credential=launch.guest_credential_path,
                   ld_library_path=launch.guest_ld_library_path,
                   path_bin=str(Path(launch.interpreter_guest_path).parent)),
        scratch_size_bytes=launch.scratch_size_bytes,
        tmp_size_bytes=launch.guest_tmp_size_bytes,
        env_pairs=None,  # filled by the caller with the credential-free pairs
        model_argv_tail=list(spec.argv[1:]),
        version_argv_tail=[launch.version_argument],
        passthrough_env_keys=None,  # filled by the caller
        max_version_output_bytes=launch.max_version_output_bytes,
        max_stdout_bytes=spec.max_stdout_bytes,
        max_stderr_bytes=spec.max_stderr_bytes,
        expected_version_output_hex=launch.expected_version_output.encode('utf-8').hex())
    if launch.egress_policy == EGRESS_RELAY:
        if (type(relay_channel_fd) is not int or relay_channel_fd < 7
                or type(relay_port) is not int
                or not RELAY_PORT_WINDOW[0] <= relay_port <= RELAY_PORT_WINDOW[1]):
            raise ValueError('linux_launch_spec_invalid')
        configuration['relay_channel_fd'] = relay_channel_fd
        configuration['relay_port'] = relay_port
    elif relay_channel_fd is not None or relay_port is not None:
        raise ValueError('linux_launch_spec_invalid')
    return configuration


def _model_phase_error(code):
    """Map a supervisor model-phase failure code to its fixed parent error."""
    if code == 'wrapper_option_unsupported':
        return ResearchProcessError('research_process_wrapper_unsupported')
    if code == 'teardown_failed':
        return ResearchProcessError('research_process_cleanup_failed')
    if code == 'phase_timeout':
        return ResearchProcessError('research_process_timeout')
    if code == 'model_output_limit':
        return ResearchProcessError('research_process_output_limit')
    if code == 'model_input_incomplete':
        return ResearchProcessError('research_process_input_incomplete')
    if code == 'model_relay_failed':
        return ResearchProcessError('research_process_relay_failed')
    return ResearchProcessError('research_process_failed')


class _ContainedSession:
    """Parent-side driver for one supervisor and its two contained phases."""

    def __init__(self, spec, launch, stop, deadline_ns):
        self._spec = spec
        self._stop = stop
        self._deadline = deadline_ns
        self._prompt_w = self._credential_w = self._control_w = None
        self._stdout_r = self._stderr_r = self._report_r = self._liveness_w = None
        self._relay_channel = None
        self._relay_child_fd = None
        self._supervisor = None
        admission = _Admission(spec, launch)
        self._admission = admission
        pairs, self._credential = _guest_configuration(spec, launch)
        try:
            admission.protect()
            # The parent NEVER rewrites its own low descriptors: the host
            # process (pytest under the native opt-in) owns them. The control
            # channel rides the child's stdin (fd 0) and the relay channels
            # ride stdout/stderr (fds 1/2) via Popen semantics; the remaining
            # four channel ends are inherited at arbitrary descriptor numbers
            # listed in the CONF line, and the SUPERVISOR installs them at its
            # canonical numbers 3..6 inside its own fresh process.
            ctrl_r, self._control_w = os.pipe()
            self._stdout_r, vout_w = os.pipe()
            self._stderr_r, verr_w = os.pipe()
            self._report_r, rep_w = os.pipe()
            live_r, self._liveness_w = os.pipe()
            prom_r, self._prompt_w = os.pipe()
            # The prompt write end deliberately stays BLOCKING: pipe ends
            # share one open-file description with the supervisor child via
            # pass_fds, so O_NONBLOCK here would leak into its blocking
            # reads. The supervisor sets non-blocking only on its own relay
            # descriptors; the parent's chunked writes stay bounded by the
            # select loop's deadline and stop checks.
            cred_r, self._credential_w = os.pipe()
            artifact_fds = [admission.vendor_fd, admission.wrapper_fd,
                            admission.helper_fd, admission.interp_fd,
                            *admission.runtime_fds]
            relay_child_fd = None
            relay_kwargs = {}
            if launch.egress_policy == EGRESS_RELAY:
                # The inherited relay channel (L9 Amendment 1): one AF_UNIX
                # socketpair per call. The child-bound half moves to a
                # descriptor >= 100 through the existing F_DUPFD idiom (the
                # canonical 3..6 supervisor slots and the staged artifact
                # descriptors are never touched); the drawn port comes from
                # the production draw inside the exact reviewed window; the
                # parent half stays here for the trusted-parent engine peer
                # and is closed only by cleanup. Nothing crosses the wrapper
                # argv except the two PAL_RELAY_* setenv values.
                channel_parent, channel_child = socket.socketpair()
                relay_child_fd = _fresh_copy(channel_child.fileno())
                channel_child.close()
                self._relay_channel = channel_parent
                # cleanup owns the duplicate until the supervisor has
                # inherited it, so a failure below cannot leak it
                self._relay_child_fd = relay_child_fd
                relay_kwargs = dict(relay_channel_fd=relay_child_fd,
                                    relay_port=draw_relay_port())
            allocation = 'pal-call-' + sha256(
                (str(os.getpid()) + ':' + str(time.monotonic_ns())).encode('ascii')
            ).hexdigest()[:16]
            configuration = _supervisor_configuration(
                spec, launch, wrapper_fd=admission.wrapper_fd,
                helper_fd=admission.helper_fd, interp_fd=admission.interp_fd,
                vendor_fd=admission.vendor_fd, runtime_fds=admission.runtime_fds,
                allocation=allocation, report_fd=rep_w, liveness_fd=live_r,
                prompt_fd=prom_r, credential_fd=cred_r, **relay_kwargs)
            configuration['env_pairs'] = [list(pair) for pair in pairs]
            configuration['passthrough_env_keys'] = [key for key, _ in pairs]
            self._supervisor = subprocess.Popen(
                ['/proc/self/fd/%d' % admission.interp_fd, '-S', '-B',
                 '/proc/self/fd/%d' % admission.helper_fd, 'supervise'],
                stdin=ctrl_r, stdout=vout_w, stderr=verr_w,
                pass_fds=[rep_w, live_r, prom_r, cred_r, *artifact_fds]
                + ([relay_child_fd] if relay_child_fd is not None else []),
                env={'PYTHONHOME': launch.supervisor_python_home},
                cwd=launch.cgroup_root, shell=False, close_fds=True,
                start_new_session=True)
            for fd in (ctrl_r, vout_w, verr_w, rep_w, live_r, prom_r, cred_r):
                try:
                    os.close(fd)
                except OSError:
                    pass
            if relay_child_fd is not None:
                try:
                    os.close(relay_child_fd)
                except OSError:
                    pass
                self._relay_child_fd = None
            self._send_conf(configuration)
            event = self._await_first_event()
            if event.get('type') != 'started':
                raise ResearchProcessError('research_process_failed')
        except BaseException:
            self._cleanup(spec.cleanup_timeout_ms)
            raise

    def _send_conf(self, configuration):
        line = b'CONF ' + json.dumps(configuration, separators=(',', ':')).encode('utf-8')
        os.write(self._control_w, line.hex().encode('ascii') + b'\n')

    def _remaining_ms(self):
        return max((self._deadline - time.monotonic_ns()) // 1000000, 1)

    def _stopped(self):
        return self._stop is not None and self._stop.is_stopped()

    def _send(self, line):
        os.write(self._control_w, line + b'\n')

    def _read_report(self):
        data = bytearray()
        while True:
            block = os.read(self._report_r, 4096)
            if block:
                data.extend(block)
                if data.endswith(b'\n'):
                    return json.loads(bytes(data).decode('utf-8'))
            if not block:
                raise ResearchProcessError('research_process_failed')
            if not select.select([self._report_r], [], [], 1.0)[0]:
                raise ResearchProcessError('research_process_failed')

    def _await_first_event(self):
        while True:
            if self._stopped():
                raise ResearchProcessError('research_process_stopped')
            if time.monotonic_ns() >= self._deadline:
                raise ResearchProcessError('research_process_timeout')
            if self._supervisor.poll() is not None:
                raise ResearchProcessError('research_process_failed')
            if select.select([self._report_r], [], [], 0.05)[0]:
                return self._read_report()

    def run_version_phase(self):
        LINUX_PHASE_COUNTERS.version_execution()
        self._send(b'VERSION %d' % self._remaining_ms())
        while True:
            if self._stopped():
                raise ResearchProcessError('research_process_stopped')
            if time.monotonic_ns() >= self._deadline:
                raise ResearchProcessError('research_process_timeout')
            if self._supervisor.poll() is not None:
                raise ResearchProcessError('research_process_failed')
            event = self._read_report()
            kind = event.get('type')
            code = event.get('code')
            if kind == 'version_done':
                if code == 'version_mismatch':
                    raise ResearchProcessError('research_process_version_mismatch')
                if code == 'wrapper_option_unsupported':
                    raise ResearchProcessError('research_process_wrapper_unsupported')
                if code == 'teardown_failed':
                    raise ResearchProcessError('research_process_cleanup_failed')
                if code == 'phase_timeout':
                    raise ResearchProcessError('research_process_timeout')
                if code is not None or event.get('exit_code') != 0 \
                        or event.get('stderr_bytes') != 0:
                    raise ResearchProcessError('research_process_failed')
                return
            if kind == 'error':
                if code == 'wrapper_option_unsupported':
                    raise ResearchProcessError('research_process_wrapper_unsupported')
                raise ResearchProcessError('research_process_failed')
            raise ResearchProcessError('research_process_failed')

    def run_model_phase(self, stdin):
        self._send(b'MODEL %d' % self._remaining_ms())
        while True:
            if self._stopped():
                raise ResearchProcessError('research_process_stopped')
            if time.monotonic_ns() >= self._deadline:
                raise ResearchProcessError('research_process_timeout')
            if self._supervisor.poll() is not None:
                raise ResearchProcessError('research_process_failed')
            event = self._read_report()
            if event.get('type') == 'ready':
                break
            if event.get('type') == 'error' \
                    and event.get('code') == 'wrapper_option_unsupported':
                raise ResearchProcessError('research_process_wrapper_unsupported')
            raise ResearchProcessError('research_process_failed')
        # Readiness validated: release the one-use bounded credential channel.
        payload = (len(self._credential).to_bytes(8, 'big')
                   + self._credential.encode('utf-8'))
        os.write(self._credential_w, payload)
        os.close(self._credential_w)
        self._credential_w = None
        LINUX_PHASE_COUNTERS.model_execution()
        return self._drain_model(stdin)

    def _drain_model(self, stdin):
        collected, stderr_bytes, offset = bytearray(), 0, 0
        source = self._prompt_w
        done = False
        while not done:
            if self._stopped():
                raise ResearchProcessError('research_process_stopped')
            if time.monotonic_ns() >= self._deadline:
                raise ResearchProcessError('research_process_timeout')
            # Drive the prompt write directly each iteration: a pipe write
            # end never reports readable, so it must not join the read set.
            if source is not None:
                if offset == len(stdin):
                    # Relinquish before close: cancellation can arrive after
                    # the OS already released the descriptor number.
                    fd, source = source, None
                    self._prompt_w = None
                    os.close(fd)
                else:
                    try:
                        count = os.write(source, stdin[offset:offset + 4096])
                    except BlockingIOError:
                        count = 0
                    offset += count
            watched = [self._stdout_r, self._stderr_r, self._report_r]
            try:
                readable = select.select(watched, [], [], 0.05)[0]
            except (OSError, ValueError):
                raise ResearchProcessError('research_process_failed') from None
            for index, fd in ((1, self._stdout_r), (2, self._stderr_r)):
                if fd not in readable:
                    continue
                used = len(collected) if index == 1 else stderr_bytes
                cap = self._spec.max_stdout_bytes if index == 1 else self._spec.max_stderr_bytes
                try:
                    block = os.read(fd, min(65536, cap - used + 1))
                except BlockingIOError:
                    continue
                if not block:
                    continue
                if len(block) + used > cap:
                    raise ResearchProcessError('research_process_output_limit')
                if index == 1:
                    collected.extend(block)
                else:
                    stderr_bytes += len(block)
            if self._report_r in readable:
                event = self._read_report()
                code = event.get('code')
                if event.get('type') == 'model_done':
                    if code is not None:
                        raise _model_phase_error(code)
                    if event.get('exit_code') != 0:
                        raise ResearchProcessError('research_process_nonzero_exit')
                    if source is not None:
                        # A protocol-conforming vendor reads all stdin before
                        # exiting 0; a success report with the prompt pipe
                        # still open means accepted bytes never reached it.
                        raise ResearchProcessError(
                            'research_process_input_incomplete')
                    done = True
                elif event.get('type') == 'error':
                    raise ResearchProcessError('research_process_failed')
                else:
                    raise ResearchProcessError('research_process_failed')
            elif self._supervisor.poll() is not None and not readable:
                raise ResearchProcessError('research_process_failed')
        return self._final_drain(collected, stderr_bytes)

    def _final_drain(self, collected, stderr_bytes):
        deadline = time.monotonic_ns() + 1000000000
        while time.monotonic_ns() < deadline:
            try:
                readable = select.select([self._stdout_r, self._stderr_r], [], [], 0.05)[0]
            except (OSError, ValueError):
                break
            progress = False
            for index, fd in ((1, self._stdout_r), (2, self._stderr_r)):
                if fd not in readable:
                    continue
                progress = True
                try:
                    block = os.read(fd, 65536)
                except BlockingIOError:
                    continue
                if not block:
                    continue
                used = len(collected) if index == 1 else stderr_bytes
                cap = (self._spec.max_stdout_bytes if index == 1
                       else self._spec.max_stderr_bytes)
                if len(block) + used > cap:
                    raise ResearchProcessError('research_process_output_limit')
                if index == 1:
                    collected.extend(block)
                else:
                    stderr_bytes += len(block)
            if not progress:
                break
        return bytes(collected), stderr_bytes

    def _cleanup(self, timeout_ms):
        failure = None
        try:
            for name in ('_liveness_w', '_prompt_w', '_credential_w', '_control_w'):
                fd = getattr(self, name, None)
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    setattr(self, name, None)
            channel = getattr(self, '_relay_channel', None)
            if channel is not None:
                try:
                    channel.close()
                except OSError:
                    pass
                self._relay_channel = None
            relay_child = getattr(self, '_relay_child_fd', None)
            if relay_child is not None:
                try:
                    os.close(relay_child)
                except OSError:
                    pass
                self._relay_child_fd = None
            if self._supervisor is not None:
                deadline = time.monotonic_ns() + timeout_ms * 1000000
                while self._supervisor.poll() is None and time.monotonic_ns() < deadline:
                    time.sleep(0.005)
                if self._supervisor.poll() is None:
                    self._supervisor.kill()
                    try:
                        self._supervisor.wait(timeout=max(timeout_ms // 1000, 1))
                    except subprocess.TimeoutExpired:
                        failure = ResearchProcessError('research_process_cleanup_failed')
            for name in ('_stdout_r', '_stderr_r', '_report_r'):
                fd = getattr(self, name, None)
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    setattr(self, name, None)
        except BaseException as error:
            failure = failure if failure is not None else error
        finally:
            self._admission.close()
        if failure is not None and isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure
        return failure


_ADMITTED_ERRORS = frozenset((
    'research_process_stopped', 'research_process_timeout',
    'research_process_not_started', 'research_process_output_limit',
    'research_process_nonzero_exit', 'research_process_cleanup_failed',
    'research_process_version_mismatch', 'research_process_wrapper_unsupported',
    'research_process_failed', 'research_process_platform_unsupported',
    'research_process_memfd_unavailable', 'research_process_launch_credential_missing',
    'research_process_launch_env_forbidden', 'research_process_input_incomplete',
    'research_process_relay_failed'))
_ADMITTED_VALUE_ERRORS = frozenset((
    'research_process_artifact_invalid', 'research_process_wrapper_elevated',
    'research_process_cgroup_unavailable', 'research_process_interpreter_home_invalid',
    'research_process_launch_invalid', 'research_process_sigchld_unsupported',
    'research_process_stop_invalid', 'research_process_input_invalid'))


def run_linux_contained_process(*, spec, launch, stdin, stop):
    """Two contained executions for one admitted call; never a retry in either."""
    if sys.platform != 'linux':
        raise ResearchProcessError('research_process_platform_unsupported')
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise ValueError('research_process_sigchld_unsupported')
    if stop is not None and type(stop) is not ResearchDispatchStop:
        raise ValueError('research_process_stop_invalid')
    if stop is not None and stop.is_stopped():
        raise ResearchProcessError('research_process_stopped')
    if type(stdin) is not bytes or len(stdin) > spec.max_stdin_bytes:
        raise ValueError('research_process_input_invalid')
    started = time.monotonic_ns()
    deadline = started + spec.timeout_ms * 1000000
    LINUX_PHASE_COUNTERS.contained_call()
    session = None
    failure = None
    result = None
    try:
        session = _ContainedSession(spec, launch, stop, deadline)
        if time.monotonic_ns() >= deadline or session._stopped():
            raise ResearchProcessError('research_process_not_started')
        session.run_version_phase()
        if time.monotonic_ns() >= deadline:
            raise ResearchProcessError('research_process_timeout')
        if session._stopped():
            raise ResearchProcessError('research_process_stopped')
        output, stderr_bytes = session.run_model_phase(stdin)
        # Candidate only: the elapsed time still excludes cleanup. Success is
        # returned AFTER cleanup and the error handling below, so a cleanup
        # failure recorded in ``finally`` suppresses the successful output
        # instead of bypassing this handling via an early return.
        result = ResearchProcessResult(output, stderr_bytes,
                                       (time.monotonic_ns() - started) // 1000000)
    except BaseException as error:
        failure = error
    finally:
        if session is not None:
            cleanup_failure = session._cleanup(spec.cleanup_timeout_ms)
            if cleanup_failure is not None and (failure is None
                                                or isinstance(failure, Exception)):
                failure = cleanup_failure
    if failure is not None:
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure from None
        if type(failure) is ResearchProcessError and failure.args \
                and failure.args[0] in _ADMITTED_ERRORS:
            raise ResearchProcessError(failure.args[0]) from None
        if isinstance(failure, ValueError) and failure.args \
                and type(failure.args[0]) is str and failure.args[0] in _ADMITTED_VALUE_ERRORS:
            raise ValueError(failure.args[0]) from None
        raise ResearchProcessError('research_process_failed') from None
    return result
