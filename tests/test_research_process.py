"""Real synthetic processes, no provider/credentials/user database or CLI login."""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

import pytest

from polymarket_alpha_lab import research_process as core
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop


@pytest.fixture(scope='module')
def executable():
    # Resolve venv symlinks explicitly in this TEST; production never searches PATH.
    path = str(Path(sys.executable).resolve())
    return path, sha256(Path(path).read_bytes()).hexdigest()


def spec(executable, cwd, code='import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())', **kw):
    path, digest = executable
    # Windows' loader needs SystemRoot. This test copies only that nonsecret
    # system path; production always requires the full environment from its owner.
    environment = (('SystemRoot', os.environ['SystemRoot']),) if os.name == 'nt' else ()
    # Pure stdlib fixture: exclude third-party site startup; real argv is unchanged.
    return core.ResearchProcessSpec((path, '-I', '-S', '-c', code), str(cwd), environment,
                                   digest, kw.pop('timeout_ms', 15000), **kw)


def run(value, data=b'', **kw):
    return core.run_research_process(spec=value, stdin=data, allow_process_start=True, **kw)


@pytest.mark.parametrize('data', [b'', b'Chinese \xe4\xb8\xad\xe6\x96\x87\r\n\x00\xff', b'x'*200000],
                         ids=['empty', 'unicode-and-binary', 'large-200kb'])
def test_actual_binary_round_trip_without_spool_files(executable, tmp_path, data):
    before = list(tmp_path.iterdir())
    result = run(spec(executable, tmp_path), data)
    assert result.stdout == data and result.stderr_bytes == 0
    assert type(result.elapsed_ms) is int and result.elapsed_ms >= 0
    assert list(tmp_path.iterdir()) == before
    assert 'Chinese' not in repr(result)


def test_explicit_env_cwd_and_argument_boundaries(executable, tmp_path, monkeypatch):
    monkeypatch.setenv('PAL_PARENT_SECRET_SENTINEL', 'DO-NOT-INHERIT')
    code = 'import os,sys,json;print(json.dumps([os.getcwd(),sys.argv[1:],os.getenv("PAL_PARENT_SECRET_SENTINEL"),os.getenv("PAL_EXPLICIT")]))'
    item = spec(executable, tmp_path, code)
    item = replace(item, argv=(*item.argv, 'spaces and "quotes" ; & $HOME', ''),
                   environment=(*item.environment, ('PAL_EXPLICIT', 'local-only')))
    values = json.loads(run(item).stdout)
    assert Path(values[0]) == tmp_path
    assert values[1:] == [['spaces and "quotes" ; & $HOME', ''], None, 'local-only']
    assert 'local-only' not in repr(item) and 'PAL_EXPLICIT' not in repr(item)


@pytest.mark.parametrize('changes', [
    {'argv': ('python',)}, {'argv': []}, {'argv': ()}, {'argv': (1,)},
    {'cwd': 'relative'}, {'executable_sha256': 'A'*64}, {'timeout_ms': True},
    {'timeout_ms': 0}, {'timeout_ms': 3600001}, {'max_stdin_bytes': -1},
    {'max_stdout_bytes': 1048577}, {'cleanup_timeout_ms': 30001},
    {'environment': {'X':'Y'}}, {'environment': (('X','y'),('x','z'))},
    {'environment': (('X=Y','z'),)}, {'environment': (('X','\x00'),)},
    {'environment': (('X','\ud800'),)},
])
def test_invalid_inert_profile(executable, tmp_path, changes):
    with pytest.raises((ValueError, TypeError)):
        replace(spec(executable, tmp_path), **changes)


@pytest.mark.parametrize('opt_in', [False, None, 1, 'yes'])
def test_no_opt_in_no_image_or_process_entry(executable, tmp_path, monkeypatch, opt_in):
    monkeypatch.setattr(core, '_verify_executable', lambda _: pytest.fail('image read'))
    with pytest.raises(core.ResearchProcessError):
        core.run_research_process(spec=spec(executable,tmp_path), stdin=b'', allow_process_start=opt_in)


def test_input_cap_and_preexisting_stop_precede_executable_read(executable,tmp_path,monkeypatch):
    monkeypatch.setattr(core, '_verify_executable', lambda _: pytest.fail('image read'))
    value = spec(executable,tmp_path,max_stdin_bytes=1)
    with pytest.raises(core.ResearchProcessError): run(value,b'xx')
    stop = ResearchDispatchStop();stop.request_stop()
    with pytest.raises(core.ResearchProcessError,match='stopped'): run(value,stop=stop)


@pytest.mark.parametrize('defect', ['missing', 'hash', 'script', 'directory'])
def test_image_failure_does_not_start_any_child(executable,tmp_path,monkeypatch,defect):
    value=spec(executable,tmp_path)
    if defect=='missing': value=replace(value,argv=(str(tmp_path/'missing'),))
    if defect=='hash': value=replace(value,executable_sha256='0'*64)
    if defect=='script':
        script=tmp_path/'unsafe.cmd';script.write_bytes(b'echo not-native')
        value=replace(value,argv=(str(script),),executable_sha256=sha256(script.read_bytes()).hexdigest())
    if defect=='directory': value=replace(value,argv=(str(tmp_path),))
    monkeypatch.setattr(core,'_spawn',lambda _:pytest.fail('unverified image entered'))
    with pytest.raises(core.ResearchProcessError): run(value)


@pytest.mark.parametrize('stream', ['stdout','stderr'])
def test_exact_limit_and_one_byte_overflow(executable,tmp_path,stream):
    options={'max_'+stream+'_bytes':4096}
    value=spec(executable,tmp_path,f'import sys;sys.{stream}.buffer.write(b"x"*4096)',**options)
    result=run(value)
    assert result.stdout==(b'x'*4096 if stream=='stdout' else b'')
    assert result.stderr_bytes==(4096 if stream=='stderr' else 0)
    value=replace(value,argv=(*value.argv[:-1],f'import sys;sys.{stream}.buffer.write(b"x"*4097)'))
    with pytest.raises(core.ResearchProcessError,match='output_limit'): run(value)


@pytest.mark.parametrize('stream', ['stdout','stderr'])
def test_flood_is_bounded_redacted_and_has_no_reader_threads(executable,tmp_path,stream):
    before={t.ident for t in threading.enumerate()}
    code=f'import os;\nwhile True:os.write({1 if stream=="stdout" else 2}, b"PRIVATE-SENTINEL"*4096)'
    with pytest.raises(core.ResearchProcessError) as error: run(spec(executable,tmp_path,code))
    assert 'PRIVATE-SENTINEL' not in ''.join(traceback.format_exception(error.value))
    assert {t.ident for t in threading.enumerate()}==before


@pytest.mark.parametrize('code', [
    'import time;time.sleep(10)',
    'import os,time;os.close(1);os.close(2);time.sleep(10)',
    'import subprocess,sys;subprocess.Popen([sys.executable,"-I","-S","-c","import time;time.sleep(10)"]);sys.exit(0)',
])
def test_timeout_covers_silent_closed_streams_and_descendant_held_pipes(executable,tmp_path,code):
    started=time.monotonic()
    with pytest.raises(core.ResearchProcessError,match='timeout'): run(spec(executable,tmp_path,code,timeout_ms=1000))
    assert time.monotonic()-started < 8


def test_unread_large_input_cannot_deadlock(executable,tmp_path):
    with pytest.raises(core.ResearchProcessError,match='timeout'):
        run(spec(executable,tmp_path,'import time;time.sleep(10)',timeout_ms=1000),b'x'*300000)


@pytest.mark.parametrize('code', [
    'import sys;sys.stderr.write("PRIVATE-SENTINEL");sys.exit(19)',
    'import os;os.close(0)',
])
def test_failure_is_redacted_and_not_success(executable,tmp_path,code):
    with pytest.raises(core.ResearchProcessError) as error: run(spec(executable,tmp_path,code),b'x'*500000)
    assert 'PRIVATE-SENTINEL' not in str(error.value)
    assert str(tmp_path) not in ''.join(traceback.format_exception(error.value))


def test_inflight_stop_terminates_only_the_owned_domain(executable,tmp_path):
    stop=ResearchDispatchStop()
    timer=threading.Timer(0.6,stop.request_stop);timer.start()
    try:
        with pytest.raises(core.ResearchProcessError,match='stopped'):
            run(spec(executable,tmp_path,'import time;time.sleep(10)'),stop=stop)
    finally:timer.join()


def test_normal_leader_exit_also_cleans_pipe_detached_descendant(executable,tmp_path):
    code='import subprocess,sys; subprocess.Popen([sys.executable,"-I","-S","-c","import time;time.sleep(10)"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);print("complete")'
    result=run(spec(executable,tmp_path,code))
    assert result.stdout.strip()==b'complete'


@pytest.mark.skipif(os.name!='nt',reason='actual Windows Job Object structures')
def test_windows_64bit_abi_layouts():
    import ctypes
    from polymarket_alpha_lab import research_process_windows as native
    assert ctypes.sizeof(ctypes.c_void_p)==8
    assert [ctypes.sizeof(t) for t in (native._Startup,native._StartupEx,native._ProcessInfo,
             native._BasicLimits,native._Limits,native._Accounting)]==[104,112,24,64,144,48]


@pytest.mark.skipif(sys.platform!='linux',reason='Linux leader is unreaped until cleanup')
def test_linux_leader_is_reaped_after_return(executable,tmp_path):
    child_pid=int(run(spec(executable,tmp_path,'import os;print(os.getpid())')).stdout)
    with pytest.raises(ChildProcessError): os.waitpid(child_pid,os.WNOHANG)
