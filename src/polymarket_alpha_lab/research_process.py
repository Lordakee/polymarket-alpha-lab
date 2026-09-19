"""One explicitly configured research subprocess with bounded binary I/O.

This is process supervision, NOT a filesystem/network sandbox, credential loader,
provider adapter, or CLI persistence approval. The caller owns the executable,
arguments, working directory and complete environment. No shell or PATH lookup.
Linux owns a cooperative process group; Windows owns a non-breakaway Job Object.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.team_research_agent_types import integer


class ResearchProcessError(ValueError):
    """Fixed-code failure; no command, environment, stream or original exception."""


@dataclass(frozen=True, slots=True)
class ResearchProcessSpec:
    argv: tuple[str, ...] = field(repr=False)
    cwd: str = field(repr=False)
    environment: tuple[tuple[str, str], ...] = field(repr=False)
    executable_sha256: str = field(repr=False)
    timeout_ms: int
    max_stdin_bytes: int = 16000000
    max_stdout_bytes: int = 1048576
    max_stderr_bytes: int = 65536
    cleanup_timeout_ms: int = 5000

    def __post_init__(self):
        if type(self.argv) is not tuple or not 1 <= len(self.argv) <= 128:
            raise ValueError('research_process_spec_invalid')
        for arg in self.argv:
            if (type(arg) is not str or '\x00' in arg or len(arg.encode('utf-8')) > 30000):
                raise ValueError('research_process_spec_invalid')
        if (not Path(self.argv[0]).is_absolute() or type(self.cwd) is not str
                or '\x00' in self.cwd or not Path(self.cwd).is_absolute()):
            raise ValueError('research_process_spec_invalid')
        self.cwd.encode('utf-8')
        if (type(self.executable_sha256) is not str
                or re.fullmatch('[0-9a-f]{64}', self.executable_sha256) is None):
            raise ValueError('research_process_spec_invalid')
        if type(self.environment) is not tuple or len(self.environment) > 128:
            raise ValueError('research_process_spec_invalid')
        keys = set()
        for pair in self.environment:
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError('research_process_spec_invalid')
            key, value = pair
            if (type(key) is not str or re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', key) is None
                    or type(value) is not str or '\x00' in value or len(value.encode('utf-8')) > 8192
                    or key.upper() in keys):
                raise ValueError('research_process_spec_invalid')
            keys.add(key.upper())
        # Conservative cross-platform limits, including Windows' terminating NUL.
        if (len(subprocess.list2cmdline(self.argv).encode('utf-16-le')) // 2 + 1 > 30000
                or sum(len((k+'='+v+'\0').encode('utf-16-le')) // 2 for k, v in self.environment) + 1 > 30000):
            raise ValueError('research_process_spec_invalid')
        for name, upper in (('timeout_ms', 3600000), ('cleanup_timeout_ms', 30000),
                            ('max_stdin_bytes', 16000000), ('max_stdout_bytes', 1048576),
                            ('max_stderr_bytes', 1048576)):
            integer(name, getattr(self, name), 1, upper)


@dataclass(frozen=True, slots=True)
class ResearchProcessResult:
    """Successful process bytes only. Raw stderr is never retained or returned."""
    stdout: bytes = field(repr=False)
    stderr_bytes: int
    elapsed_ms: int

    def __post_init__(self):
        if type(self.stdout) is not bytes or len(self.stdout) > 1048576:
            raise ValueError('research_process_result_invalid')
        integer('stderr_bytes', self.stderr_bytes, 0, 1048576)
        integer('elapsed_ms', self.elapsed_ms, 0, 2**63-1)


def _prefer_failure(first, later):
    return later if first is None or isinstance(first, Exception) and not isinstance(later, Exception) else first


def _verify_executable(spec):
    """Pin only the selected native image, not dependencies or filesystem state."""
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(spec.argv[0], flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= 268435456:
            raise ValueError('research_process_image_invalid')
        digest, prefix, size = sha256(), b'', 0
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            if not prefix:
                prefix = block[:4]
            size += len(block)
            if size > 268435456:
                raise ValueError('research_process_image_invalid')
            digest.update(block)
        magic = b'MZ' if os.name == 'nt' else b'\x7fELF'
        if not prefix.startswith(magic) or digest.hexdigest() != spec.executable_sha256:
            raise ValueError('research_process_image_invalid')
    finally:
        os.close(fd)
    if not Path(spec.cwd).is_dir():
        raise ValueError('research_process_cwd_invalid')


class _LinuxProcess:
    """Keep the leader unreaped until group termination to avoid PID reuse."""
    def __init__(self, spec, handles):
        self.process = subprocess.Popen(spec.argv, executable=spec.argv[0], cwd=spec.cwd,
            env=dict(spec.environment), stdin=handles[0], stdout=handles[1], stderr=handles[2],
            shell=False, close_fds=True, start_new_session=True)
        self.terminated = False

    def poll(self):
        result = os.waitid(os.P_PID, self.process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if result is None:
            return None
        return result.si_status if result.si_code == os.CLD_EXITED else -result.si_status

    def terminate(self):
        if not self.terminated:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.terminated = True

    def is_closed(self):
        return self.process.poll() is not None

    def close(self):
        # poll()/wait() after kill reaps only our leader. Escaped groups are not
        # contained by POSIX process groups; callers must not treat this as a sandbox.
        pass


def _spawn(spec):
    pipes, live = [], set()
    owned = None
    try:
        for _ in range(3):
            pair = os.pipe()
            pipes.append(pair); live.update(pair)
        parents = (pipes[0][1], pipes[1][0], pipes[2][0])
        for fd in parents:
            os.set_blocking(fd, False)
        child = (pipes[0][0], pipes[1][1], pipes[2][1])
        if os.name == 'nt':
            from polymarket_alpha_lab.research_process_windows import OwnedWindowsProcess
            owned = OwnedWindowsProcess(spec, child)
        else:
            owned = _LinuxProcess(spec, child)
        for fd in child:
            live.remove(fd)
            os.close(fd)
        return owned, parents
    except BaseException as original:
        failure = original
        if owned is not None:
            try:
                _cleanup(owned, live, spec.cleanup_timeout_ms)
            except BaseException as error:
                failure = _prefer_failure(failure, error)
        else:
            for fd in live:
                try:
                    os.close(fd)
                except BaseException as error:
                    failure = _prefer_failure(failure, error)
        raise failure


def _drain(owned, descriptors, stdin, spec, deadline, stop):
    source, out, err = descriptors
    offset = stderr_bytes = 0
    collected = bytearray()
    while True:
        if stop is not None and stop.is_stopped():
            raise ResearchProcessError('research_process_stopped')
        if time.monotonic_ns() >= deadline:
            raise ResearchProcessError('research_process_timeout')
        progress = False
        if source is not None:
            if offset == len(stdin):
                os.close(source); descriptors[0] = source = None
            else:
                try:
                    count = os.write(source, stdin[offset:offset+4096])
                except BlockingIOError:
                    pass
                else:
                    # Nonblocking Windows byte pipes may successfully write
                    # zero bytes when full. Keep the same operation/deadline.
                    offset += count
                    progress = count > 0
        # One bounded read per stream per iteration; flooding cannot starve stop
        # or deadline checks. stderr is counted, never stored or decoded.
        for index, fd in ((1, out), (2, err)):
            if fd is None:
                continue
            used = len(collected) if index == 1 else stderr_bytes
            cap = spec.max_stdout_bytes if index == 1 else spec.max_stderr_bytes
            try:
                block = os.read(fd, min(65536, cap-used+1))
            except BlockingIOError:
                continue
            progress = True
            if not block:
                os.close(fd); descriptors[index] = None
                if index == 1: out = None
                else: err = None
            elif len(block)+used > cap:
                raise ResearchProcessError('research_process_output_limit')
            elif index == 1:
                collected.extend(block)
            else:
                stderr_bytes += len(block)
        code = owned.poll()
        if code is not None and source is None and out is None and err is None:
            if code != 0:
                raise ResearchProcessError('research_process_nonzero_exit')
            return bytes(collected), stderr_bytes
        if not progress:
            time.sleep(0.005)


def _cleanup(owned, descriptors, timeout_ms):
    """Terminate the owned domain and close descriptors on every exit path."""
    interruption = None
    try:
        deadline = time.monotonic_ns() + timeout_ms*1000000
        while True:
            try:
                owned.terminate()
                while not owned.is_closed():
                    if time.monotonic_ns() >= deadline:
                        raise ResearchProcessError('research_process_cleanup_failed')
                    time.sleep(0.005)
                break
            except (KeyboardInterrupt, SystemExit) as error:
                if interruption is None:
                    interruption = error
                if time.monotonic_ns() >= deadline:
                    raise ResearchProcessError('research_process_cleanup_failed') from None
    finally:
        close_failure = None
        for fd in descriptors:
            if fd is not None:
                try:
                    os.close(fd)
                except BaseException as error:
                    close_failure = _prefer_failure(close_failure, error)
        try:
            owned.close()
        except BaseException as error:
            close_failure = _prefer_failure(close_failure, error)
        if close_failure is not None:
            raise _prefer_failure(interruption, close_failure)
    if interruption is not None:
        raise interruption


def run_research_process(*, spec, stdin, allow_process_start=False, stop=None):
    """Run once. Never retry, run a shell, inherit env or emit raw diagnostics.

    Supervision counts from before image verification; OS file/process creation
    and teardown may be uninterruptible. timeout_ms is not a universal wall-clock
    guarantee. Cleanup failure is an error, never proof all processes are gone.
    Requires Linux or Windows/Python >=3.12 (nonblocking Windows pipes).
    """
    owned = None
    descriptors = []
    failure = None
    try:
        if allow_process_start is not True or type(spec) is not ResearchProcessSpec:
            raise ValueError('research_process_opt_in_required')
        spec = replace(spec)
        if type(stdin) is not bytes or len(stdin) > spec.max_stdin_bytes:
            raise ValueError('research_process_input_invalid')
        if stop is not None and type(stop) is not ResearchDispatchStop:
            raise ValueError('research_process_stop_invalid')
        if sys.platform != 'linux' and not (os.name == 'nt' and sys.version_info >= (3, 12)):
            raise ValueError('research_process_platform_unsupported')
        if stop is not None and stop.is_stopped():
            raise ResearchProcessError('research_process_stopped')
        if sys.platform == 'linux' and signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise ValueError('research_process_sigchld_unsupported')
        started = time.monotonic_ns()
        deadline = started + spec.timeout_ms*1000000
        _verify_executable(spec)
        if time.monotonic_ns() >= deadline or stop is not None and stop.is_stopped():
            raise ResearchProcessError('research_process_not_started')
        owned, raw_descriptors = _spawn(spec)
        descriptors = list(raw_descriptors)
        output, stderr_bytes = _drain(owned, descriptors, stdin, spec, deadline, stop)
    except BaseException as error:
        failure = error
    finally:
        if owned is not None:
            try:
                _cleanup(owned, descriptors, spec.cleanup_timeout_ms)
            except BaseException as error:
                # Retain original cancellation, but never return success after
                # failed cleanup. A new interrupt outranks an ordinary failure.
                if failure is None or isinstance(failure, Exception):
                    failure = error
    if failure is not None:
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure from None
        reasons = ('research_process_stopped', 'research_process_timeout',
                   'research_process_not_started', 'research_process_output_limit',
                   'research_process_input_incomplete', 'research_process_nonzero_exit',
                   'research_process_cleanup_failed')
        if (type(failure) is ResearchProcessError and len(failure.args) == 1
                and type(failure.args[0]) is str and failure.args[0] in reasons):
            raise ResearchProcessError(failure.args[0]) from None
        raise ResearchProcessError('research_process_failed') from None
    return ResearchProcessResult(output, stderr_bytes, (time.monotonic_ns()-started)//1000000)
