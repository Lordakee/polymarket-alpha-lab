"""Synthetic Linux containment fixtures and launch-policy tests; no provider.

Non-native tests validate declaration-only construction, artifact pinning,
credential separation and fixed-code refusals on any host. Native opt-in tests
(``POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT=1``) compile the checked-in C
stand-in ELF at test time and exercise the real rootless namespace lifecycle;
missing prerequisites after an explicit opt-in are failures, never skips. The
stand-in's version output and envelope are explicitly synthetic and are never
official-image evidence.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import posixpath
import shutil
import signal
import subprocess
import sys
import threading
import time
import types

import pytest

from polymarket_alpha_lab import research_linux_relay as relay
from polymarket_alpha_lab import research_process_linux as linux
from polymarket_alpha_lab.research_claude_exec import CLAUDE_VERSION
from polymarket_alpha_lab.research_process import (
    ResearchProcessError, ResearchProcessSpec, run_research_process,
)

CONTAINMENT_ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT') == '1'
HELPER_DIGEST = linux._helper_digest()

# Fixed synthetic paths: golden digests must not depend on tmp_path layout.
FIXED_WRAPPER = '/opt/pal-synthetic/bin/bwrap'
FIXED_INTERP = '/opt/pal-synthetic/bin/python3'
FIXED_RUNTIME = '/opt/pal-synthetic/runtime/libc.so.6'
FIXED_CGROUP = '/opt/pal-synthetic/cgroup'

STANDIN_C_SOURCE = r'''
/* Synthetic stand-in vendor for contained Linux tests (compile at test time).
 * Explicitly NOT the official Claude CLI: its version output and result
 * envelope are fixed synthetic fixtures and never official-image evidence.
 * Behavior is selected by argv flags and stdin markers. */
#include <arpa/inet.h>
#include <dlfcn.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>

#define BUF_CAP (1u << 21)
static char input[BUF_CAP];
static char work[BUF_CAP];
static char escaped[BUF_CAP];

static void die(int code) { _exit(code); }

static void read_stdin(void) {
    size_t used = 0;
    for (;;) {
        if (used >= BUF_CAP) die(80);
        ssize_t n = read(0, input + used, BUF_CAP - used);
        if (n < 0) die(81);
        if (n == 0) break;
        used += (size_t)n;
    }
    input[used] = 0;
}

static void json_escape(const char *src) {
    char *out = escaped;
    while (*src && out + 8 < escaped + BUF_CAP) {
        unsigned char c = (unsigned char)*src++;
        if (c == '"' || c == '\\') { *out++ = '\\'; *out++ = (char)c; }
        else if (c < 0x20) { out += sprintf(out, "\\u%04x", c); }
        else { *out++ = (char)c; }
    }
    *out = 0;
}

static int find_ids(char ids[][160]) {
    /* Depth-independent extraction with deduplication: the prompt embeds
     * the transcript one or more times, keys carry varying backslash
     * runs, and later observations repeat earlier source ids. */
    const char *cursor = strstr(input, "sources");
    if (!cursor) return -1;
    int count = 0;
    while (count < 8) {
        const char *hit = strstr(cursor, "source_id");
        if (!hit) break;
        const char *after = hit + 9;
        int guard = 0;
        while ((*after == '"' || *after == '\\') && guard < 6) { after++; guard++; }
        if (*after != ':') { cursor = hit + 9; continue; }
        after++;
        while (*after == ' ' || *after == '\\') after++;
        if (*after != '"') { cursor = hit + 9; continue; }
        after++;
        const char *value = after;
        const char *endp = value;
        while (*endp && *endp != '"' && *endp != '\\') endp++;
        size_t length = (size_t)(endp - value);
        if (length == 0 || length >= 159) break;
        int duplicate = 0;
        for (int i = 0; i < count; i++)
            if (strncmp(ids[i], value, length) == 0 && ids[i][length] == 0) { duplicate = 1; break; }
        if (!duplicate) {
            memcpy(ids[count], value, length);
            ids[count][length] = 0;
            count++;
        }
        cursor = endp;
    }
    return count;
}
static void emit(const char *calls) {
    json_escape(calls);
    snprintf(work, BUF_CAP,
        "{\"type\":\"result\",\"subtype\":\"success\",\"is_error\":false,"
        "\"num_turns\":1,\"session_id\":\"11111111-1111-4111-8111-111111111111\","
        "\"duration_ms\":4,\"duration_api_ms\":3,\"stop_reason\":\"end_turn\","
        "\"result\":\"%s\",\"permission_denials\":[],"
        "\"usage\":{\"input_tokens\":3,\"output_tokens\":5,"
        "\"cache_creation_input_tokens\":7,\"cache_read_input_tokens\":11},"
        "\"modelUsage\":{\"claude-opus-5\":{\"inputTokens\":3,\"outputTokens\":5,"
        "\"cacheCreationInputTokens\":7,\"cacheReadInputTokens\":11}}}",
        escaped);
    fputs(work, stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

static long flag_number(int argc, char **argv, const char *prefix) {
    size_t n = strlen(prefix);
    for (int i = 1; i < argc; i++)
        if (strncmp(argv[i], prefix, n) == 0) return strtol(argv[i] + n, 0, 10);
    return -1;
}

static int has(int argc, char **argv, const char *flag) {
    for (int i = 1; i < argc; i++) if (strcmp(argv[i], flag) == 0) return 1;
    return 0;
}

static void sleepers(int count) {
    for (int i = 0; i < count; i++) {
        pid_t pid = fork();
        if (pid == 0) { setsid(); signal(SIGHUP, SIG_IGN); pause(); die(90); }
    }
}

int main(int argc, char **argv) {
    if (has(argc, argv, "--version")) {
        long hang = flag_number(argc, argv, "--pal-version-hang=");
        if (hang > 0) sleep((unsigned)hang);
        fputs("2.1.278 (Claude Code)\n", stdout);
        return 0;
    }
    read_stdin();
    if (strstr(input, "blocked-eth") && !strstr(input, "\\\"tool_calls\\\"")) {
        pause(); die(90);
    }
    {
        long port = flag_number(argc, argv, "--pal-deny-net=");
        if (port >= 0) {
            int fd = socket(AF_INET, SOCK_STREAM, 0);
            struct sockaddr_in address;
            memset(&address, 0, sizeof(address));
            address.sin_family = AF_INET;
            address.sin_port = htons((unsigned short)port);
            address.sin_addr.s_addr = htonl(0x7f000001u);
            if (connect(fd, (struct sockaddr *)&address, sizeof(address)) == 0) {
                fputs("NET-OPEN\n", stdout);
                return 2;
            }
            fputs("NET-DENIED\n", stdout);
            fflush(stdout);
            close(fd);
        }
    }
    if (has(argc, argv, "--pal-hang")) { pause(); die(90); }
    if (has(argc, argv, "--pal-deny-host")) {
        FILE *handle = fopen("/etc/passwd", "r");
        if (handle) { fputs("HOST-OPEN\n", stdout); return 3; }
        fputs("HOST-DENIED\n", stdout);
        fflush(stdout);
    }
    if (has(argc, argv, "--pal-write-home")) {
        char path[512];
        const char *home = getenv("HOME");
        snprintf(path, sizeof(path), "%s/marker", home ? home : "/");
        FILE *handle = fopen(path, "w");
        if (handle) { fprintf(handle, "%ld\n", (long)getpid()); fclose(handle); }
        fputs("HOME-WRITTEN\n", stdout);
        fflush(stdout);
    }
    if (has(argc, argv, "--pal-escape")) sleepers(2);
    long forks = flag_number(argc, argv, "--pal-forks=");
    if (forks >= 0) sleepers((int)forks);
    long fill = flag_number(argc, argv, "--pal-fill=");
    if (fill >= 0) {
        char path[512];
        snprintf(path, sizeof(path), "%s", fill == 1 ? "/tmp/fill" : "/pal/scratch/fill");
        FILE *handle = fopen(path, "w");
        unsigned long blocks = 0;
        static char chunk[65536];
        memset(chunk, 'x', sizeof(chunk));
        while (handle && fwrite(chunk, 1, sizeof(chunk), handle) == sizeof(chunk)) blocks++;
        if (handle) fclose(handle);
        printf("FILLED=%lu\n", blocks);
        fflush(stdout);
    }
    long allocate = flag_number(argc, argv, "--pal-alloc=");
    if (allocate > 0) {
        char *memory = calloc((size_t)allocate, 1024 * 1024);
        if (!memory) { fputs("ALLOC-REFUSED\n", stdout); return 0; }
        for (long i = 0; i < allocate; i++) memory[i * 1024 * 1024] = 1;
        fputs("ALLOC-OK\n", stdout);
        fflush(stdout);
    }
    if (has(argc, argv, "--pal-dep")) {
        void *library = dlopen("libpaldep.so", RTLD_NOW);
        if (!library) { fputs("DEP-MISSING\n", stdout); return 4; }
        int (*value)(void) = (int (*)(void))dlsym(library, "pal_dep_value");
        if (!value) { fputs("DEP-NOSYM\n", stdout); return 5; }
        printf("DEP=%d\n", value());
        fflush(stdout);
    }
    if (has(argc, argv, "--pal-stderr")) { fputs("SENTINEL-STDERR\n", stderr); fflush(stderr); }
    if (has(argc, argv, "--pal-flood")) {
        static char chunk[65536];
        memset(chunk, 'F', sizeof(chunk));
        for (;;) { ssize_t n = write(1, chunk, sizeof(chunk)); (void)n; }
    }
    long delay = flag_number(argc, argv, "--pal-delay=");
    if (delay > 0) sleep((unsigned)delay);
    char ids[8][160];
    if (strstr(input, "tool_calls") == NULL) {
        emit("{\"calls\":[{\"name\":\"search_evidence\","
             "\"arguments_json\":\"{\\\"query\\\":\\\"*\\\"}\"}]}");
    } else {
        int count = find_ids(ids);
        int finish = strstr(input, "reference") != NULL;
        if (count <= 0) die(82);
        if (!finish) {
            snprintf(work, BUF_CAP, "{\"calls\":[");
            size_t used = strlen(work);
            for (int i = 0; i < count; i++)
                used += (size_t)snprintf(work + used, BUF_CAP - used,
                    "%s{\"name\":\"read_evidence\","
                    "\"arguments_json\":\"{\\\"source_id\\\":\\\"%s\\\"}\"}",
                    i ? "," : "", ids[i]);
            snprintf(work + used, BUF_CAP - used, "]}");
            emit(work);
        } else {
            snprintf(work, BUF_CAP, "{\"calls\":[{\"name\":\"finish_research\",\"arguments_json\":\"{\\\"probability_yes\\\":\\\"0.6\\\",\\\"confidence\\\":\\\"0.5\\\",\\\"summary\\\":\\\"Synthetic contained research\\\",\\\"source_ids\\\":[");
            size_t used = strlen(work);
            for (int i = 0; i < count; i++)
                used += (size_t)snprintf(work + used, BUF_CAP - used, "%s\\\"%s\\\"",
                                         i ? "," : "", ids[i]);
            snprintf(work + used, BUF_CAP - used, "]}\"}]}");
            emit(work);
        }
    }
    long code = flag_number(argc, argv, "--pal-exit=");
    return code >= 0 ? (int)code : 0;
}
'''

DEP_C_SOURCE = 'int pal_dep_value(void) { return 42; }\n'

FAKE_WRAPPER_C_SOURCE = r'''
#include <stdio.h>
int main(int argc, char **argv) {
    (void)argc;
    fputs("bwrap: Unknown option --pass-fd\n", stderr);
    return 1;
}
'''


def _compile(directory, name, source, *flags):
    compiler = shutil.which('cc') or shutil.which('gcc')
    if compiler is None:
        pytest.fail('C compiler (cc/gcc) required to compile the synthetic ELF')
    target = directory / name
    (directory / (name + '.c')).write_text(source, encoding='ascii')
    subprocess.run([compiler, '-O1', '-o', str(target), str(directory / (name + '.c')), *flags],
                   check=True, capture_output=True, timeout=180)
    payload = target.read_bytes()
    return str(target), sha256(payload).hexdigest(), len(payload)


def compile_standin(directory):
    """Compile the synthetic stand-in ELF from checked-in source at test time.

    No prebuilt binary blobs and no Python-command shims (A3)."""
    return _compile(directory, 'pal-standin', STANDIN_C_SOURCE, '-ldl')


def require_native_containment():
    """Fail closed (never skip) when the explicit opt-in lacks prerequisites."""
    if not CONTAINMENT_ENABLED:
        pytest.skip('explicit native containment proof is opt-in')
    problems = []
    if sys.platform != 'linux':
        problems.append('linux host required')
    if not (shutil.which('cc') or shutil.which('gcc')):
        problems.append('C compiler (cc/gcc) required')
    if not (shutil.which('bwrap') or Path('/usr/bin/bwrap').is_file()):
        problems.append('bwrap containment executable required')
    root = os.environ.get('POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT', '')
    if not root or not Path(root, 'cgroup.controllers').is_file():
        problems.append('POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT must name a delegated '
                        'cgroup v2 subtree with memory and pids controllers')
    else:
        controllers = Path(root, 'cgroup.controllers').read_text().split()
        if 'memory' not in controllers or 'pids' not in controllers:
            problems.append('delegated cgroup subtree lacks memory/pids controllers')
    if problems:
        pytest.fail('containment prerequisites missing: ' + '; '.join(problems))


def _interpreter_stdlib_root(interpreter):
    probe = 'import sysconfig;print(sysconfig.get_paths()["stdlib"])'
    completed = subprocess.run([interpreter, '-S', '-c', probe], capture_output=True,
                               check=True, timeout=60, env={'PATH': '/usr/bin:/bin'})
    return Path(completed.stdout.decode('utf-8').strip())


def parse_ld_trace_pairs(trace_text):
    """Extract ``soname => hostpath`` pairs from LD_TRACE_LOADED_OBJECTS text.

    Arrow-less lines (linux-vdso, the dynamic loader itself, statically
    linked binaries) and ``=> not found`` resolutions carry no bindable
    host path and are ignored. Pure string parsing, so it is testable on
    any host; the traced subprocess itself runs only on Linux.
    """
    pairs = []
    for line in trace_text.splitlines():
        if '=>' not in line:
            continue
        left, right = line.split('=>', 1)
        soname = left.strip()
        target = right.strip().split(' ', 1)[0] if right.strip() else ''
        if not soname or not target.startswith('/'):
            continue
        pairs.append((soname, target))
    return pairs


def soname_default_search_bindings(trace_text):
    """Map interpreter trace pairs to guest bindings reachable by soname.

    /proc/self/maps exposes version-suffixed real paths (libz.so.1.3,
    libexpat.so.1.9.1) while the guest binary's DT_NEEDED entries name the
    soname, and the namespace carries no ld.so cache: the loader therefore
    falls back to its default search directories and needs the soname path
    there. Every traced pair binds at ``dirname(hostpath)/soname`` (the
    trace's right side is usually already that soname-resolved path, e.g.
    /lib/x86_64-linux-gnu/libz.so.1); pairs collapsing onto one guest path
    keep the first binding. posixpath keeps the guest path POSIX-shaped on
    Windows development hosts.
    """
    bindings = {}
    for soname, hostpath in parse_ld_trace_pairs(trace_text):
        guest = posixpath.join(posixpath.dirname(hostpath), soname)
        bindings.setdefault(guest, hostpath)
    return bindings


# The stdlib modules the closure probe imports before tracing: pure-Python
# stdlib files are only captured when actually imported by the probe, so this
# tuple is the union of the top-level stdlib imports of BOTH guest helper
# sources (HELPER_SOURCE and RELAY_HELPER_SOURCE). A helper import outside
# this tuple dies in the namespace with ModuleNotFoundError because its file
# was never bound into /pal/runtime/lib/python3.12/ (preview run 37716295041:
# the relay helper's socket). The coupling test at the bottom of this module
# keeps this tuple a superset of both sources' imports.
CLOSURE_PROBE_STDLIB_MODULES = (
    'hashlib', 'json', 'os', 'select', 'signal', 'socket', 'sys', 'time')


def _closure_probe_program():
    """The single ``-c`` program whose import and loaded-object trace defines
    the guest runtime closure: one import statement over the sorted module
    tuple, then sys.modules files plus /proc/self/maps objects."""
    return (
        'import ' + ','.join(CLOSURE_PROBE_STDLIB_MODULES) + '\n'
        'files={m.__file__ for m in sys.modules.values() if getattr(m,"__file__",None)}\n'
        'mapped=set()\n'
        'for line in open("/proc/self/maps"):\n'
        '    path=line.rstrip().rsplit(" ",1)[-1]\n'
        '    if path.startswith("/") and ".so" in path: mapped.add(path)\n'
        'print(json.dumps(sorted(files|mapped)))\n')


def discover_runtime_closure(interpreter, vendor_path):
    """Measure the interpreter stdlib/lib closure plus the vendor's ELF deps.

    Every entry comes from an actual import trace or loaded-object listing;
    nothing is invented or defaulted."""
    probe = _closure_probe_program()
    completed = subprocess.run([interpreter, '-S', '-B', '-c', probe], capture_output=True,
                               check=True, timeout=120, env={'PATH': '/usr/bin:/bin'})
    traced = set(json.loads(completed.stdout.decode('utf-8')))
    traced_env = dict(os.environ)
    traced_env['LD_TRACE_LOADED_OBJECTS'] = '1'
    vendor_deps = subprocess.run([vendor_path], capture_output=True, check=False, timeout=60,
                                 env=traced_env)
    for line in vendor_deps.stdout.decode('utf-8', 'replace').splitlines():
        for token in line.split():
            if token.startswith('/'):
                traced.add(token)
    # The interpreter's own DT_NEEDED closure must also be reachable by
    # soname in the loader's default search directories: maps only exposed
    # version-suffixed real paths and the namespace has no ld.so cache.
    interpreter_deps = subprocess.run([interpreter], capture_output=True, check=False,
                                      timeout=60, env=traced_env)
    soname_bindings = soname_default_search_bindings(
        interpreter_deps.stdout.decode('utf-8', 'replace'))
    traced.update(soname_bindings.values())
    soname_guests = {host_path: guest for guest, host_path in soname_bindings.items()}
    stdlib_root = _interpreter_stdlib_root(interpreter)
    runtime, seen, digests = [], set(), set()
    for host in sorted(traced):
        path = Path(host)
        if not path.is_file():
            continue
        payload = path.read_bytes()
        digest = sha256(payload).hexdigest()
        if digest in digests:
            continue
        try:
            relative = path.relative_to(stdlib_root)
            guest = '/pal/runtime/lib/python3.12/' + str(relative).replace('\\', '/')
        except ValueError:
            # System libraries (dynamic loader, libc, ...) bind at their
            # original absolute paths: the ELF PT_INTERP interpreter and the
            # loader's default search must resolve inside the namespace.
            # Interpreter-traced dependencies prefer their default-search
            # soname path so DT_NEEDED resolution succeeds without a cache.
            guest = soname_guests.get(host, str(path))
        if guest in seen:
            continue
        seen.add(guest)
        digests.add(digest)
        runtime.append(linux.LinuxRuntimeFile(guest, str(path.resolve()), digest, len(payload)))
    assert runtime, 'runtime closure discovery found nothing'
    return runtime


def build_native_launch(directory, **launch_changes):
    """Assemble a real launch from measured host facts (native tests only)."""
    require_native_containment()
    vendor = directory / 'vendor'
    vendor.mkdir(parents=True, exist_ok=True)
    binary, digest, size = compile_standin(vendor)
    interpreter = str(Path(sys.executable).resolve())
    interp_bytes = Path(interpreter).read_bytes()
    wrapper_path = shutil.which('bwrap') or '/usr/bin/bwrap'
    wrapper_bytes = Path(wrapper_path).read_bytes()
    dep_directory = directory / 'dep'
    dep_directory.mkdir(parents=True, exist_ok=True)
    dep_path, dep_digest, dep_size = _compile(dep_directory, 'libpaldep.so', DEP_C_SOURCE,
                                              '-shared', '-fPIC')
    runtime = discover_runtime_closure(interpreter, binary)
    runtime.append(linux.LinuxRuntimeFile('/pal/runtime/lib/libpaldep.so', dep_path,
                                          dep_digest, dep_size))
    values = dict(
        wrapper=linux.LinuxArtifactPin(str(Path(wrapper_path).resolve()),
                                       sha256(wrapper_bytes).hexdigest(), len(wrapper_bytes)),
        helper_sha256=HELPER_DIGEST,
        interpreter=linux.LinuxArtifactPin(interpreter, sha256(interp_bytes).hexdigest(),
                                           len(interp_bytes)),
        supervisor_python_home=sys.base_prefix,
        runtime_files=tuple(runtime),
        vendor_guest_path='/pal/vendor/claude',
        helper_guest_path='/pal/runtime/helper.py',
        vendor_size_bytes=size,
        expected_version_output=CLAUDE_VERSION + ' (Claude Code)\n',
        cgroup_root=os.environ['POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT'],
        scratch_size_bytes=64 * 1024 * 1024,
        guest_tmp_size_bytes=32 * 1024 * 1024,
        memory_max_bytes=512 * 1024 * 1024,
        pids_max=32)
    values.update(launch_changes)
    return binary, digest, size, linux.LinuxLaunchSpec(**values)


def contained_vendor_spec(binary, digest, work, key='SYNTHETIC-NOT-A-REAL-KEY', argv=()):
    return ResearchProcessSpec(
        (binary, '--print', '--bare', *argv), str(work),
        (('HOME', str(work / 'host-home')), ('CLAUDE_CONFIG_DIR', str(work / 'host-config')),
         ('ANTHROPIC_BASE_URL', 'https://gateway.example.invalid'),
         ('CLAUDE_CODE_MAX_OUTPUT_TOKENS', '8192'),
         ('ANTHROPIC_API_KEY', key)), digest, 30000)


def fixed_runtime_files():
    return (linux.LinuxRuntimeFile('/pal/runtime/lib/libc.so.6', FIXED_RUNTIME,
                                   'e' * 64, 123456),)


def fixed_launch():
    return linux.LinuxLaunchSpec(
        wrapper=linux.LinuxArtifactPin(FIXED_WRAPPER, 'a' * 64, 65536),
        helper_sha256=HELPER_DIGEST,
        interpreter=linux.LinuxArtifactPin(FIXED_INTERP, 'b' * 64, 12345678),
        supervisor_python_home='/opt/pal-synthetic/python-home',
        runtime_files=fixed_runtime_files(),
        vendor_guest_path='/pal/vendor/claude',
        helper_guest_path='/pal/runtime/helper.py',
        vendor_size_bytes=98765432,
        expected_version_output=CLAUDE_VERSION + ' (Claude Code)\n',
        cgroup_root=FIXED_CGROUP)


def synthetic_launch(tmp_path=None, **changes):
    """Declaration-only launch with fixed synthetic POSIX paths (no files)."""
    values = dict(
        wrapper=linux.LinuxArtifactPin(FIXED_WRAPPER, 'a' * 64, 65536),
        helper_sha256=HELPER_DIGEST,
        interpreter=linux.LinuxArtifactPin(FIXED_INTERP, 'b' * 64, 12345678),
        supervisor_python_home='/opt/pal-synthetic/python-home',
        runtime_files=fixed_runtime_files(),
        vendor_guest_path='/pal/vendor/claude',
        helper_guest_path='/pal/runtime/helper.py',
        vendor_size_bytes=98765432,
        expected_version_output=CLAUDE_VERSION + ' (Claude Code)\n',
        cgroup_root=FIXED_CGROUP)
    values.update(changes)
    return linux.LinuxLaunchSpec(**values)


def vendor_spec(tmp_path, environment=None):
    return ResearchProcessSpec(
        (str(tmp_path / 'claude-native'), '--print', '--bare'), str(tmp_path / 'work'),
        tuple(environment or (
            ('HOME', str(tmp_path / 'home')), ('CLAUDE_CONFIG_DIR', str(tmp_path / 'config')),
            ('ANTHROPIC_BASE_URL', 'https://gateway.example.invalid'),
            ('CLAUDE_CODE_MAX_OUTPUT_TOKENS', '8192'),
            ('ANTHROPIC_API_KEY', 'SYNTHETIC-NOT-A-REAL-KEY'))),
        'd' * 64, 15000)


def relaunch(launch, **changes):
    values = {name: getattr(launch, name) for name in
              linux.LinuxLaunchSpec.__dataclass_fields__}
    values.update(changes)
    return linux.LinuxLaunchSpec(**values)


_REAL_POPEN = subprocess.Popen


@pytest.fixture(autouse=True)
def no_external_io(monkeypatch):
    # Native opt-in tests intentionally spawn real supervisors and wrappers;
    # the tripwires apply only to the synthetic unit tests.
    if CONTAINMENT_ENABLED:
        return
    monkeypatch.setattr('socket.socket', lambda *a, **k: pytest.fail('network entered'))
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('process spawned'))


def test_no_external_io_fixture_is_inert_under_the_native_optin(no_external_io):
    """Regression: with the explicit opt-in the autouse tripwire must leave
    the real process/network surfaces untouched (native tests spawn on
    purpose); without it, the synthetic unit tests stay guarded."""
    if CONTAINMENT_ENABLED:
        assert subprocess.Popen is _REAL_POPEN
    else:
        assert subprocess.Popen is not _REAL_POPEN


def test_launch_spec_construction_is_declaration_only(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail('launch construction performed I/O')
    monkeypatch.setattr(Path, 'read_bytes', forbidden)
    monkeypatch.setattr(Path, 'is_dir', forbidden)
    launch = synthetic_launch(tmp_path)
    assert launch.launch_schema == 'research-linux-launch-v1'
    assert launch.egress_policy == 'offline'
    assert launch.memory_swap_max_bytes == 0
    assert list(tmp_path.iterdir()) == []


def test_helper_pin_binds_the_checked_in_source(tmp_path):
    assert HELPER_DIGEST == sha256(linux.HELPER_SOURCE.encode('utf-8')).hexdigest()
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        synthetic_launch(tmp_path, helper_sha256='0' * 64)


@pytest.mark.parametrize('changes', [
    {'launch_schema': 'research-linux-launch-v2'},
    {'helper_protocol_version': 'research-linux-helper-v2'},
    {'namespaces': ('user', 'mount', 'pid', 'net', 'ipc')},
    {'namespaces': ('user', 'mount', 'pid', 'net', 'ipc', 'uts', 'cgroup')},
    {'version_argument': '-V'},
    {'cgroup_allocation_rule': 'shared-directory'},
    {'guest_home_path': '/pal/work'},
    {'guest_scratch_path': '/pal/work'},
    {'vendor_guest_path': 'relative/claude'},
    {'helper_guest_path': '/'},
    {'cgroup_root': '/not/../absolute'},
    {'supervisor_python_home': 'relative'},
    {'expected_version_output': '2.1.278'},
    {'expected_version_output': '2.1.278\n\n'},
    {'expected_version_output': '2.1.278\r\n'},
    {'expected_version_output': '2.1.278\n\x01'},
    {'expected_version_output': ''},
    {'runtime_files': ()},
    {'wrapper': linux.LinuxArtifactPin('/other-wrapper', 'b' * 64, 10)},
    {'interpreter': linux.LinuxArtifactPin('/other-interpreter', 'a' * 64, 10)},
])
def test_invalid_launch_mutations_fail_closed(tmp_path, changes):
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(synthetic_launch(tmp_path), **changes)


@pytest.mark.parametrize('egress', ['host', 'loopback-relay', 'qualified', 'online', ''])
def test_no_production_egress_constructor_exists(tmp_path, egress):
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(synthetic_launch(tmp_path), egress_policy=egress)


@pytest.mark.parametrize('field,weak,strong', [
    ('memory_max_bytes', 4294967297, 8388608),
    ('scratch_size_bytes', 1073741825, 1048576),
    ('guest_tmp_size_bytes', 536870913, 1048576),
    ('pids_max', 65, 8),
    ('memory_max_bytes', 0, 8388608),
    ('pids_max', 0, 8),
    ('memory_swap_max_bytes', 1, 0),
])
def test_declared_resource_bounds_cannot_be_weakened(tmp_path, field, weak, strong):
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(synthetic_launch(tmp_path), **{field: weak})
    assert getattr(relaunch(synthetic_launch(tmp_path), **{field: strong}), field) == strong


@pytest.mark.parametrize('changes', [
    {'wrapper': linux.LinuxArtifactPin('/same', 'a' * 64, 10),
     'interpreter': linux.LinuxArtifactPin('/same', 'b' * 64, 20)},
    {'wrapper': linux.LinuxArtifactPin('/w1', 'a' * 64, 10),
     'interpreter': linux.LinuxArtifactPin('/w2', 'a' * 64, 20)},
])
def test_wrapper_and_interpreter_keep_separate_identities(tmp_path, changes):
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(synthetic_launch(tmp_path), **changes)


def test_runtime_members_cannot_alias_wrapper_or_interpreter(tmp_path):
    alias_path = linux.LinuxArtifactPin('/w', 'a' * 64, 10)
    member = linux.LinuxRuntimeFile('/pal/runtime/lib/x.so', '/w', 'a' * 64, 10)
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(synthetic_launch(tmp_path), wrapper=alias_path,
                 interpreter=linux.LinuxArtifactPin('/i', 'b' * 64, 20),
                 runtime_files=(member,))


@pytest.mark.parametrize('allowed', [
    (), ('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS',
         'CLAUDE_CONFIG_DIR'),
    ('ANTHROPIC_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL',
     'CLAUDE_CODE_MAX_OUTPUT_TOKENS', 'CLAUDE_CONFIG_DIR', 'HOME'),
    ('ANTHROPIC_BASE_URL', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS', 'CLAUDE_CONFIG_DIR',
     'HOME', 'ANTHROPIC_API_KEY'),
    tuple(sorted(('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS',
                  'CLAUDE_CONFIG_DIR', 'HOME', 'PATH-HOST'))),
    ('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_MAX_OUTPUT_TOKENS',
     'CLAUDE_CONFIG_DIR', 'HOME', 7),
])
def test_allowed_guest_env_is_sorted_unique_and_required(tmp_path, allowed):
    with pytest.raises(ValueError, match='linux_launch_spec_invalid'):
        relaunch(synthetic_launch(tmp_path), allowed_guest_env=allowed)


def test_policy_dict_is_secret_free_ephemeral_free_and_stable():
    policy = fixed_launch().policy_dict()
    encoded = json.dumps(policy, sort_keys=True)
    # Key NAMES are policy; credential VALUES, random allocation names and
    # prompt material must never appear.
    for forbidden in ('pal-call', 'SYNTHETIC', 'stdin', 'messages_json'):
        assert forbidden not in encoded
    assert 'ANTHROPIC_API_KEY' in policy['environment']['allowlist']
    assert policy['egress']['production_egress'] == 'unavailable'
    assert policy['egress']['host_network_fallback'] == 'forbidden'
    assert policy['egress']['relay'] == 'not-shipped-in-this-node'
    assert policy['protocol']['retries'] == 'none'
    assert policy['protocol']['per_phase_executions'] == 1
    assert policy['protocol']['teardown_between_phases'] == 'verified-empty-subtree'
    assert policy['environment']['credential'] == 'one-use-anonymous-pipe-model-phase-only'
    assert policy['mounts']['writable_host_surfaces'] == []
    assert policy['descriptors']['inherited_from_parent'] == []
    assert fixed_launch().policy_dict() == policy


def _pinned_file(tmp_path, payload=b'\x7fELF' + b'payload' * 8):
    path = tmp_path / 'artifact.bin'
    path.write_bytes(payload)
    return str(path), sha256(payload).hexdigest(), len(payload)


def test_verify_pinned_bytes_accepts_exact_identity(tmp_path):
    path, digest, size = _pinned_file(tmp_path)
    assert linux.verify_pinned_bytes(path, digest, size, max_bytes=size + 1,
                                     require_elf=True) == b'\x7fELF'


@pytest.mark.parametrize('defect', ['sha', 'size', 'max-bytes', 'magic', 'directory', 'missing'])
def test_verify_pinned_bytes_rejects_substitution(tmp_path, defect):
    payload = b'\x7fELF' + b'vendor-bytes' * 16
    path = tmp_path / 'image.bin'
    path.write_bytes(payload)
    digest, size = sha256(payload).hexdigest(), len(payload)
    expect = ('0' * 64, size) if defect == 'sha' else (
        (digest, size - 1) if defect == 'size' else (digest, size))
    limit = size - 1 if defect == 'max-bytes' else size + 1
    if defect == 'magic':
        path = tmp_path / 'script.bin'
        path.write_bytes(b'#!/bin/sh\n')
        expect = (sha256(path.read_bytes()).hexdigest(), path.stat().st_size)
    elif defect == 'directory':
        path = tmp_path / 'dir.bin'
        path.mkdir()
    elif defect == 'missing':
        path = tmp_path / 'missing.bin'
    with pytest.raises((ValueError, OSError)):
        linux.verify_pinned_bytes(str(path), expect[0], expect[1], max_bytes=limit,
                                  require_elf=True)


@pytest.mark.skipif(sys.platform != 'linux' or not hasattr(os, 'O_NOFOLLOW'),
                    reason='O_NOFOLLOW symlink refusal is a Linux admission rule')
def test_verify_pinned_bytes_refuses_symlink_replacement(tmp_path):
    path, digest, size = _pinned_file(tmp_path)
    link = tmp_path / 'link.bin'
    try:
        os.symlink(path, link)
    except OSError:
        pytest.skip('symlink creation unavailable on this host')
    with pytest.raises(OSError):
        linux.verify_pinned_bytes(str(link), digest, size, max_bytes=size + 1,
                                  require_elf=True)


def test_guest_configuration_separates_credential_and_substitutes_paths(tmp_path):
    launch = synthetic_launch(tmp_path)
    spec = vendor_spec(tmp_path)
    pairs, credential = linux._guest_configuration(spec, launch)
    keys = dict(pairs)
    assert credential == 'SYNTHETIC-NOT-A-REAL-KEY'
    assert 'ANTHROPIC_API_KEY' not in keys
    assert 'HOME' not in keys and 'CLAUDE_CONFIG_DIR' not in keys
    assert keys['ANTHROPIC_BASE_URL'] == 'https://gateway.example.invalid'
    assert tuple(keys) == tuple(sorted(keys))
    assert credential not in json.dumps([list(pair) for pair in pairs])


@pytest.mark.parametrize('environment', [
    (('HOME', '/h'), ('ANTHROPIC_API_KEY', 'SYNTHETIC-KEY-1'), ('SECRET_ENV', 'x')),
    (('HOME', '/h'),),
    (('HOME', '/h'), ('ANTHROPIC_API_KEY', '')),
    (('HOME', '/h'), ('ANTHROPIC_API_KEY', 'has space')),
    (('HOME', '/h'), ('ANTHROPIC_API_KEY', 'k' * 4097)),
])
def test_guest_configuration_refuses_forbidden_env_and_bad_credentials(tmp_path, environment):
    with pytest.raises(ResearchProcessError):
        linux._guest_configuration(vendor_spec(tmp_path, environment=environment),
                                   synthetic_launch(tmp_path))


@pytest.mark.skipif(sys.platform == 'linux', reason='non-linux platform refusal')
def test_run_research_process_requires_linux_for_contained_path(tmp_path):
    with pytest.raises(ResearchProcessError, match='platform_unsupported'):
        run_research_process(spec=vendor_spec(tmp_path), stdin=b'{}', allow_process_start=True,
                             linux_launch=synthetic_launch())
    with pytest.raises(ResearchProcessError, match='research_process_failed'):
        run_research_process(spec=vendor_spec(tmp_path), stdin=b'{}', allow_process_start=True,
                             linux_launch=object())


def test_run_research_process_none_launch_keeps_legacy_path(monkeypatch, tmp_path):
    monkeypatch.setattr(linux, 'run_linux_contained_process',
                        lambda **kwargs: pytest.fail('contained path entered'))
    monkeypatch.setattr('polymarket_alpha_lab.research_process._verify_executable',
                        lambda _: None)
    monkeypatch.setattr('polymarket_alpha_lab.research_process._spawn',
                        lambda value: (_ for _ in ()).throw(OSError('legacy path')))
    with pytest.raises(ResearchProcessError, match='research_process_failed'):
        run_research_process(spec=vendor_spec(tmp_path), stdin=b'{}', allow_process_start=True,
                             linux_launch=None)


def test_cleanup_failure_is_reported_not_swallowed():
    class Stuck:
        def poll(self):
            return None

        def kill(self):
            raise SystemExit(0)  # even an interrupt cannot mask cleanup state

    class FakeAdmission:
        closed = False

        def close(self):
            pass

    session = linux._ContainedSession.__new__(linux._ContainedSession)
    session._supervisor = Stuck()
    session._admission = FakeAdmission()
    session._liveness_w = session._prompt_w = session._credential_w = session._control_w = 11
    session._stdout_r = session._stderr_r = session._report_r = 12
    with pytest.raises(SystemExit):
        session._cleanup(5)


MODEL_PHASE_OUTPUT = b'{"synthetic":"model-output"}'


def _driver_session(monkeypatch, record, *, version=None, model=None, cleanup=None,
                    model_output=(MODEL_PHASE_OUTPUT, 7)):
    """Fake two-phase session for driver-ordering tests.

    Every phase call is recorded; version/model/cleanup inject failures. The
    one-use credential channel is written only inside the real run_model_phase
    (after readiness), so ``'model' in record`` marks the earliest point the
    credential could ever be released. Nothing real is spawned.
    """

    class FakeSession:
        def __init__(self, spec, launch, stop, deadline):
            record.append('construct')

        def _stopped(self):
            return False

        def run_version_phase(self):
            record.append('version')
            if version is not None:
                raise version

        def run_model_phase(self, stdin):
            record.append('model')
            if model is not None:
                raise model
            return model_output

        def _cleanup(self, timeout_ms):
            record.append('cleanup')
            return cleanup

    monkeypatch.setattr(linux, '_ContainedSession', FakeSession)


def _drive(monkeypatch, tmp_path, stdin=b'{"schema_version":"probe"}'):
    # Satisfy the driver's fixed platform/SIGCHLD preconditions on any
    # development host; the session itself is the fake installed above.
    monkeypatch.setattr(linux, 'sys', types.SimpleNamespace(platform='linux'))
    monkeypatch.setattr(linux, 'signal', types.SimpleNamespace(
        SIG_DFL=signal.SIG_DFL, SIGCHLD='placeholder', getsignal=lambda _: signal.SIG_DFL))
    return linux.run_linux_contained_process(spec=vendor_spec(tmp_path), stdin=stdin,
                                             launch=synthetic_launch(tmp_path), stop=None)


def test_clean_success_returns_after_cleanup_with_exact_bytes(monkeypatch, tmp_path):
    record = []
    _driver_session(monkeypatch, record)
    result = _drive(monkeypatch, tmp_path)
    assert record == ['construct', 'version', 'model', 'cleanup']
    assert type(result) is linux.ResearchProcessResult
    assert result.stdout == MODEL_PHASE_OUTPUT
    assert result.stderr_bytes == 7
    assert result.elapsed_ms >= 0


def test_cleanup_failure_after_model_success_suppresses_the_output(monkeypatch, tmp_path):
    """Regression for the return-inside-try defect: a cleanup error recorded
    by ``finally`` must suppress the successful output and flow through the
    driver's fixed error handling, never bypass it with an early return."""
    record = []
    _driver_session(monkeypatch, record,
                    cleanup=ResearchProcessError('research_process_cleanup_failed'))
    with pytest.raises(ResearchProcessError, match='research_process_cleanup_failed'):
        _drive(monkeypatch, tmp_path)
    assert record == ['construct', 'version', 'model', 'cleanup']


@pytest.mark.parametrize('model_error', [
    ResearchProcessError('research_process_nonzero_exit'),
    ValueError('research_process_launch_invalid'),
])
def test_cleanup_failure_keeps_precedence_over_ordinary_model_errors(
        monkeypatch, tmp_path, model_error):
    """An ordinary model-phase exception is superseded by a cleanup failure,
    exactly as before the suppression fix."""
    record = []
    _driver_session(monkeypatch, record, model=model_error,
                    cleanup=ResearchProcessError('research_process_cleanup_failed'))
    with pytest.raises(ResearchProcessError, match='research_process_cleanup_failed'):
        _drive(monkeypatch, tmp_path)
    assert record == ['construct', 'version', 'model', 'cleanup']


def test_original_interrupts_survive_a_concurrent_cleanup_failure(monkeypatch, tmp_path):
    record = []
    _driver_session(monkeypatch, record, model=KeyboardInterrupt('original interrupt'),
                    cleanup=ResearchProcessError('research_process_cleanup_failed'))
    with pytest.raises(KeyboardInterrupt):
        _drive(monkeypatch, tmp_path)
    assert record == ['construct', 'version', 'model', 'cleanup']


def test_version_mismatch_precedes_model_launch_and_credential_release(monkeypatch, tmp_path):
    """A malformed vendor banner fails inside the version phase: the model
    namespace is never launched and the one-use credential channel (released
    only inside run_model_phase after readiness) is never written."""
    record = []
    _driver_session(monkeypatch, record,
                    version=ResearchProcessError('research_process_version_mismatch'))
    with pytest.raises(ResearchProcessError, match='research_process_version_mismatch'):
        _drive(monkeypatch, tmp_path)
    assert record == ['construct', 'version', 'cleanup']
    assert 'model' not in record


def test_helper_source_is_stdlib_only_and_protocol_pinned():
    import ast
    tree = ast.parse(linux.HELPER_SOURCE)
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.Import) for alias in node.names}
    assert imported <= {'hashlib', 'json', 'os', 'select', 'signal', 'sys', 'time'}
    assert 'polymarket_alpha_lab' not in linux.HELPER_SOURCE
    assert 'psycopg' not in linux.HELPER_SOURCE


# Every stdlib name either checked-in helper source may import: a name outside
# this set is a non-stdlib dependency leaking into the offline guest namespace
# and must fail loudly rather than surface as a namespace ModuleNotFoundError.
_HELPER_STDLIB_ALLOWLIST = frozenset((
    'hashlib', 'json', 'os', 'select', 'signal', 'socket', 'sys', 'time'))


def _helper_imported_module_names(source):
    """Dotted-root module names a helper source imports, from actual parsing.

    ``import X.Y`` counts as X and ``from X import y`` counts as X; relative
    imports (level > 0) cannot exist in a guest script and are ignored. The
    walk also covers function-local imports: a deferred import dies just as
    hard inside the namespace as a top-level one."""
    import ast
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split('.')[0])
    return names


def test_closure_probe_covers_every_helper_stdlib_import():
    """Couple the closure probe to both guest helper sources (pure parsing,
    no subprocess, Windows-runnable). Pure-Python stdlib files reach
    /pal/runtime/lib/python3.12/ only when the probe actually imports them,
    so a helper import the probe lacks killed the guest helper with
    ModuleNotFoundError: No module named 'socket' (preview run 37716295041).
    Both sources must stay inside the stdlib allowlist, and the probe's one
    import statement must import exactly CLOSURE_PROBE_STDLIB_MODULES."""
    import ast
    helper_imports = (_helper_imported_module_names(linux.HELPER_SOURCE)
                      | _helper_imported_module_names(relay.RELAY_HELPER_SOURCE))
    non_stdlib = helper_imports - _HELPER_STDLIB_ALLOWLIST
    assert not non_stdlib, ('helper sources import non-stdlib modules',
                            sorted(non_stdlib))
    program = ast.parse(_closure_probe_program())
    import_nodes = [node for node in program.body
                    if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert len(import_nodes) == 1 and isinstance(import_nodes[0], ast.Import)
    probed = {alias.name for alias in import_nodes[0].names}
    missing = helper_imports - probed
    assert not missing, ('closure probe does not import helper stdlib modules',
                         sorted(missing))
    assert probed == set(CLOSURE_PROBE_STDLIB_MODULES)
    assert list(CLOSURE_PROBE_STDLIB_MODULES) == sorted(CLOSURE_PROBE_STDLIB_MODULES)


def test_helper_source_mirrors_output_caps_and_credential_bound():
    """The supervisor relay must enforce the same byte caps as the parent and
    the guest must mirror the parent's 4096-byte credential bound."""
    assert 'model_output_limit' in linux.HELPER_SOURCE
    assert 'max_stdout_bytes' in linux.HELPER_SOURCE
    assert 'max_stderr_bytes' in linux.HELPER_SOURCE
    assert '8192' not in linux.HELPER_SOURCE
    assert 'size <= 4096' in linux.HELPER_SOURCE


def test_supervisor_configuration_carries_the_spec_output_caps(tmp_path):
    """Pure configuration check: the supervisor receives the parent's exact
    stdout/stderr caps, and no credential value ever enters the config."""
    spec = vendor_spec(tmp_path)
    capped = ResearchProcessSpec(spec.argv, spec.cwd, spec.environment,
                                 spec.executable_sha256, spec.timeout_ms,
                                 max_stdout_bytes=4096, max_stderr_bytes=2048)
    configuration = linux._supervisor_configuration(
        capped, synthetic_launch(), wrapper_fd=101, helper_fd=102, interp_fd=103,
        vendor_fd=104, runtime_fds=(105,), allocation='pal-call-regression',
        report_fd=106, liveness_fd=107, prompt_fd=108, credential_fd=109)
    assert configuration['max_stdout_bytes'] == 4096
    assert configuration['max_stderr_bytes'] == 2048
    encoded = json.dumps(configuration)
    assert 'SYNTHETIC-NOT-A-REAL-KEY' not in encoded
    assert 'pal-call-regression' in configuration['alloc_name']


def test_model_phase_error_maps_relay_cap_to_output_limit():
    """The supervisor's mirrored cap failure maps to the parent's fixed
    output-limit error, never to a generic failure or a hang."""
    mapped = linux._model_phase_error('model_output_limit')
    assert type(mapped) is ResearchProcessError
    assert mapped.args[0] == 'research_process_output_limit'
    assert linux._model_phase_error('phase_timeout').args[0] == 'research_process_timeout'
    assert linux._model_phase_error('teardown_failed').args[0] == 'research_process_cleanup_failed'
    assert (linux._model_phase_error('wrapper_option_unsupported').args[0]
            == 'research_process_wrapper_unsupported')
    assert linux._model_phase_error('model_nonzero_exit').args[0] == 'research_process_failed'
    assert linux._model_phase_error(None).args[0] == 'research_process_failed'


def test_standin_source_is_synthetic_and_secret_free():
    assert 'api_key' not in STANDIN_C_SOURCE
    assert 'ANTHROPIC' not in STANDIN_C_SOURCE
    assert 'sk-' not in STANDIN_C_SOURCE
    # The stand-in prints the exact official identity banner for --version,
    # never the pre-correction bare version line.
    assert '--version' in STANDIN_C_SOURCE
    assert (CLAUDE_VERSION + ' (Claude Code)\\n') in STANDIN_C_SOURCE
    assert (CLAUDE_VERSION + '\\n') not in STANDIN_C_SOURCE


SYNTHETIC_INTERPRETER_LD_TRACE = (
    '\tlinux-vdso.so.1 (0x00007ffc7a9be000)\n'
    '\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f2e8c9a1000)\n'
    '\tlibz.so.1 => /lib/x86_64-linux-gnu/libz.so.1 (0x00007f2e8c3b1000)\n'
    '\tlibexpat.so.1 => /usr/lib/x86_64-linux-gnu/libexpat.so.1.9.1 (0x00007f2e8c12f000)\n'
    '\tlibpalmissing.so.7 => not found\n'
    '\t/lib64/ld-linux-x86-64.so.2 (0x00007f2e8cdff000)\n'
    '\tlibz.so.1 => /lib/x86_64-linux-gnu/libz.so.1.3 (0x00007f2e8c3b1000)\n')


def test_interpreter_ld_trace_binds_sonames_in_default_search_dirs():
    """Pure unit test of the runtime-closure discovery mapping: no
    subprocess and no Linux requirement, so the soname-binding rule is
    verified on Windows development hosts too. Arrow-less lines
    (linux-vdso, the dynamic loader itself) and ``=> not found``
    resolutions are ignored; every real pair binds at
    ``dirname(hostpath)/soname`` so DT_NEEDED resolution succeeds inside
    the namespace where no ld.so cache exists; and a versioned-vs-soname
    duplicate for the same library collapses onto one guest path."""
    assert parse_ld_trace_pairs(SYNTHETIC_INTERPRETER_LD_TRACE) == [
        ('libc.so.6', '/lib/x86_64-linux-gnu/libc.so.6'),
        ('libz.so.1', '/lib/x86_64-linux-gnu/libz.so.1'),
        ('libexpat.so.1', '/usr/lib/x86_64-linux-gnu/libexpat.so.1.9.1'),
        ('libz.so.1', '/lib/x86_64-linux-gnu/libz.so.1.3')]
    assert soname_default_search_bindings(SYNTHETIC_INTERPRETER_LD_TRACE) == {
        '/lib/x86_64-linux-gnu/libc.so.6': '/lib/x86_64-linux-gnu/libc.so.6',
        '/lib/x86_64-linux-gnu/libz.so.1': '/lib/x86_64-linux-gnu/libz.so.1',
        '/usr/lib/x86_64-linux-gnu/libexpat.so.1': '/usr/lib/x86_64-linux-gnu/libexpat.so.1.9.1'}


@pytest.mark.skipif(not CONTAINMENT_ENABLED, reason='explicit native containment proof is opt-in')
def test_native_contained_two_phase_round_trip(tmp_path):
    """Real bwrap/cgroup/memfd lifecycle with the compiled stand-in ELF.

    The version phase and the model phase execute from the same sealed
    snapshots under offline egress; the synthetic envelope returns through
    the relay and the phase counters advance.
    """
    binary, digest, _size, launch = build_native_launch(tmp_path)
    work = tmp_path / 'work'
    work.mkdir()
    before = linux.LINUX_PHASE_COUNTERS.snapshot()
    result = run_research_process(spec=contained_vendor_spec(binary, digest, work),
                                  stdin=b'{"schema_version":"probe"}',
                                  allow_process_start=True, linux_launch=launch)
    after = linux.LINUX_PHASE_COUNTERS.snapshot()
    assert b'"type":"result"' in result.stdout
    assert b'"subtype":"success"' in result.stdout
    assert result.stderr_bytes == 0
    assert after['version_executions'] == before['version_executions'] + 1
    assert after['model_executions'] == before['model_executions'] + 1
    assert not list(work.iterdir()), 'no writable host surface may be used'


@pytest.mark.skipif(not CONTAINMENT_ENABLED, reason='explicit native containment proof is opt-in')
def test_native_in_flight_replacement_of_vendor_and_dependency_is_ignored(tmp_path):
    """Replacing the host vendor image and a runtime dependency file during
    the version phase cannot alter the executed bytes: the model namespace
    binds the same sealed snapshots, never the mutated pathnames."""
    import threading
    binary, digest, _size, launch = build_native_launch(tmp_path)
    dep_host = next(item.host_path for item in launch.runtime_files
                    if item.guest_path.endswith('libpaldep.so'))
    work = tmp_path / 'work'
    work.mkdir()
    swapped = threading.Event()

    def swap_when_admitted():
        seen = linux.LINUX_PHASE_COUNTERS.snapshot()['version_executions']
        while linux.LINUX_PHASE_COUNTERS.snapshot()['version_executions'] == seen:
            time.sleep(0.002)
        time.sleep(0.03)
        Path(binary).write_bytes(b'\x7fELFswapped-not-the-vendor')
        Path(dep_host).write_bytes(b'not an elf object')
        swapped.set()

    thread = threading.Thread(target=swap_when_admitted, daemon=True)
    thread.start()
    result = run_research_process(
        spec=contained_vendor_spec(binary, digest, work, argv=('--pal-dep',)),
        stdin=b'{}', allow_process_start=True, linux_launch=launch)
    assert swapped.is_set()
    assert b'DEP=42' in result.stdout
    assert b'"type":"result"' in result.stdout
    assert result.stderr_bytes == 0


@pytest.mark.skipif(not CONTAINMENT_ENABLED, reason='explicit native containment proof is opt-in')
def test_native_pre_admission_tampering_is_refused(tmp_path):
    binary, digest, _size, launch = build_native_launch(tmp_path)
    Path(binary).write_bytes(b'\x7fELF' + b'tampered-after-pinning' * 4)
    work = tmp_path / 'work'
    work.mkdir()
    with pytest.raises(ResearchProcessError, match='research_process_failed'):
        run_research_process(spec=contained_vendor_spec(binary, digest, work),
                             stdin=b'{}', allow_process_start=True, linux_launch=launch)


@pytest.mark.skipif(not CONTAINMENT_ENABLED, reason='explicit native containment proof is opt-in')
def test_native_unsupported_wrapper_option_fails_closed(tmp_path):
    """A containment executable that does not support the required wrapper
    options is classified and refused, never silently retried."""
    stub = tmp_path / 'stub'
    stub.mkdir()
    stub_path, stub_digest, stub_size = _compile(stub, 'fake-bwrap', FAKE_WRAPPER_C_SOURCE)
    _binary, _digest, _size, launch = build_native_launch(tmp_path)
    launch = relaunch(launch, wrapper=linux.LinuxArtifactPin(
        stub_path, stub_digest, stub_size))
    work = tmp_path / 'work'
    work.mkdir()
    with pytest.raises(ResearchProcessError, match='wrapper_unsupported'):
        run_research_process(spec=contained_vendor_spec(_binary, _digest, work),
                             stdin=b'{}', allow_process_start=True, linux_launch=launch)


def test_model_phase_error_maps_input_incomplete():
    """A relay that loses accepted prompt bytes fails with the public
    input-incomplete code, never a silent success."""
    mapped = linux._model_phase_error('model_input_incomplete')
    assert type(mapped) is ResearchProcessError
    assert mapped.args[0] == 'research_process_input_incomplete'
    assert 'research_process_input_incomplete' in linux._ADMITTED_ERRORS


def test_helper_source_conserves_prompt_bytes():
    """Static regression for the EOF-plus-writable schedule: on parent EOF the
    helper must close only the prompt channel, keep forwarding buffered bytes,
    close guest stdin only when fully drained, treat EPIPE with unsent bytes
    as input-incomplete (output-pipe failures as relay failures), and never
    report success with undelivered buffers."""
    source = linux.HELPER_SOURCE
    assert 'not prompt_open and not prompt_buf' in source
    # Input conservation on the prompt relay; output pipes report relay
    # failures instead of masquerading as lost prompts.
    assert ("failure = failure or ('model_input_incomplete'"
            in source and "'model_relay_failed')" in source)
    assert linux._model_phase_error(
        'model_relay_failed').args[0] == 'research_process_relay_failed'
    assert 'research_process_relay_failed' in linux._ADMITTED_ERRORS
    # The old premature-close branch must be gone.
    assert 'Prompt EOF is the vendor' not in source
    assert ('if failure is None and (out_buf or err_buf or prompt_buf):'
            in source)
    # The flush loop includes the prompt buffer.
    assert "(staged['stdin_w'], prompt_buf))" in source
