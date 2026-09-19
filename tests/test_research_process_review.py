"""Separate failure-injection and ownership review of the real process boundary."""
from dataclasses import replace
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab import research_process as core
from polymarket_alpha_lab import research_process_windows as windows
from tests.test_research_process import executable,spec,run


def test_temporary_zero_write_is_backpressure_not_truncated_input(monkeypatch,executable,tmp_path):
    original=core.os.write;count=[0]
    def write(fd,data):
        count[0]+=1
        return 0 if count[0]==1 else original(fd,data)
    monkeypatch.setattr(core.os,'write',write)
    assert run(spec(executable,tmp_path),b'exact-input').stdout==b'exact-input'
    assert count[0]>=2


def test_fixed_error_type_does_not_accept_an_external_secret_message(monkeypatch,executable,tmp_path):
    def fail(_):raise core.ResearchProcessError('PRIVATE-SENTINEL')
    monkeypatch.setattr(core,'_verify_executable',fail)
    with pytest.raises(core.ResearchProcessError) as error:run(spec(executable,tmp_path))
    assert 'PRIVATE-SENTINEL' not in str(error.value)


def test_descriptor_cleanup_preserves_first_interrupt_and_attempts_all(monkeypatch):
    events=[];original=KeyboardInterrupt()
    owner=SimpleNamespace(terminate=lambda:events.append('terminate'),is_closed=lambda:True,
                          close=lambda:events.append('owner-close'))
    def close(fd):
        events.append(fd)
        if fd==1:raise original
        if fd==2:raise OSError('secondary')
    monkeypatch.setattr(core.os,'close',close)
    with pytest.raises(KeyboardInterrupt) as error:core._cleanup(owner,[1,2,3],1000)
    assert error.value is original and events==['terminate',1,2,3,'owner-close']


def test_windows_handle_close_errors_are_not_success_and_do_not_skip_other_handle():
    closed=[]
    def close(handle):closed.append(handle);return False
    owner=windows.OwnedWindowsProcess.__new__(windows.OwnedWindowsProcess)
    owner.api=SimpleNamespace(CloseHandle=close);owner.job=11;owner.process=12
    with pytest.raises(OSError):owner.close()
    assert closed==[11,12]


@pytest.mark.parametrize('fault',[KeyboardInterrupt(),SystemExit(0),OSError('PRIVATE-SENTINEL')])
def test_real_started_process_is_reaped_when_driver_raises(monkeypatch,executable,tmp_path,fault):
    # Inject after real launch; the same owner must be terminated, not another PID.
    seen=[];original=core._spawn
    def spawn(value):
        result=original(value);seen.append(result[0]);return result
    def drive(*a,**kw):raise fault
    monkeypatch.setattr(core,'_spawn',spawn);monkeypatch.setattr(core,'_drain',drive)
    expected=type(fault) if not isinstance(fault,Exception) else core.ResearchProcessError
    with pytest.raises(expected) as error:run(spec(executable,tmp_path,'import time;time.sleep(10)'))
    assert len(seen)==1
    if not isinstance(fault,Exception):assert error.value is fault
    if sys.platform=='linux':assert seen[0].process.returncode is not None
    else:assert seen[0].job is seen[0].process is None


def test_partial_pipe_creation_closes_only_allocated_descriptors(monkeypatch,executable,tmp_path):
    original=core.os.pipe;closed=[];allocated=[]
    def pipe():
        if allocated:raise OSError('no descriptors')
        pair=original();allocated.extend(pair);return pair
    close_original=core.os.close
    def close(fd):closed.append(fd);close_original(fd)
    monkeypatch.setattr(core.os,'pipe',pipe);monkeypatch.setattr(core.os,'close',close)
    with pytest.raises(OSError):core._spawn(spec(executable,tmp_path))
    assert sorted(closed)==sorted(allocated)


def test_cleanup_failure_never_returns_a_valid_reply(monkeypatch,executable,tmp_path):
    original=core._cleanup
    def cleanup(*a,**kw):
        original(*a,**kw)
        raise OSError('PRIVATE-SENTINEL')
    monkeypatch.setattr(core,'_cleanup',cleanup)
    with pytest.raises(core.ResearchProcessError) as error:run(spec(executable,tmp_path),b'valid')
    assert 'PRIVATE-SENTINEL' not in str(error.value)


@pytest.mark.skipif(sys.platform!='linux',reason='Linux SIGCHLD compatibility boundary')
def test_existing_child_reaper_is_rejected_not_overwritten(monkeypatch,executable,tmp_path):
    monkeypatch.setattr(core.signal,'getsignal',lambda _:signal.SIG_IGN)
    monkeypatch.setattr(core,'_spawn',lambda _:pytest.fail('child launched'))
    with pytest.raises(core.ResearchProcessError):run(spec(executable,tmp_path))


@pytest.mark.skipif(os.name!='nt',reason='actual Windows suspended-job failure path')
@pytest.mark.parametrize('failure',['assignment','resume'])
def test_windows_rejection_never_executes_target_or_retries(monkeypatch,executable,tmp_path,failure):
    actual=windows._api();events=[]
    class Wrapped:
        def __getattr__(self,name):return getattr(actual,name)
        def AssignProcessToJobObject(self,*args):
            events.append('assign')
            return 0 if failure=='assignment' else actual.AssignProcessToJobObject(*args)
        def ResumeThread(self,*args):events.append('resume');return 0xffffffff
    monkeypatch.setattr(windows,'_api',lambda:Wrapped())
    marker=tmp_path/'must-not-exist'
    code=f'from pathlib import Path;Path({str(marker)!r}).write_text("executed")'
    with pytest.raises(core.ResearchProcessError):run(spec(executable,tmp_path,code))
    assert not marker.exists()
    assert events==(['assign'] if failure=='assignment' else ['assign','resume'])


def _gone(pid):
    if os.name=='nt':
        import ctypes as c
        from ctypes import wintypes as w
        api=c.WinDLL('kernel32',use_last_error=True)
        api.OpenProcess.argtypes=(w.DWORD,w.BOOL,w.DWORD);api.OpenProcess.restype=w.HANDLE
        api.WaitForSingleObject.argtypes=(w.HANDLE,w.DWORD);api.WaitForSingleObject.restype=w.DWORD
        api.CloseHandle.argtypes=(w.HANDLE,)
        handle=api.OpenProcess(0x100000,False,pid)
        if not handle:return c.get_last_error()==87
        try:return api.WaitForSingleObject(handle,0)==0
        finally:api.CloseHandle(handle)
    status=Path(f'/proc/{pid}/stat')
    try:return status.read_text().rsplit(')',1)[1].split()[0]=='Z'
    except FileNotFoundError:return True


@pytest.mark.parametrize('mode',['normal','timeout'])
def test_actual_known_descendant_not_left_running(executable,tmp_path,mode):
    marker=tmp_path/'synthetic-pid'
    descendant=f'import os,time;open({str(marker)!r},"w").write(str(os.getpid()));time.sleep(10)'
    leader=('import subprocess,sys,time;from pathlib import Path;'
            f'subprocess.Popen([sys.executable,"-I","-S","-c",{descendant!r}],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);'
            f'path=Path({str(marker)!r});deadline=time.monotonic()+5;\n'
            'while not path.exists() and time.monotonic()<deadline:time.sleep(.01)\n'
            'assert path.exists()\n'+('time.sleep(10)' if mode=='timeout' else 'print("ready")'))
    value=spec(executable,tmp_path,leader,timeout_ms=2500 if mode=='timeout' else 15000)
    if mode=='timeout':
        with pytest.raises(core.ResearchProcessError,match='timeout'):run(value)
    else:assert run(value).stdout.strip()==b'ready'
    pid=int(marker.read_text());deadline=time.monotonic()+5
    while not _gone(pid) and time.monotonic()<deadline:time.sleep(.01)
    assert _gone(pid)


@pytest.mark.skipif(os.name!='nt',reason='actual Windows parent-loss Job Object proof')
def test_windows_parent_loss_terminates_owned_job(executable,tmp_path):
    root=Path(__file__).resolve().parents[1]
    marker=tmp_path/'child-pid'
    child=f'import os,time;open({str(marker)!r},"w").write(str(os.getpid()));time.sleep(20)'
    value=spec(executable,tmp_path,child,timeout_ms=30000)
    code=('import sys;sys.path.insert(0,'+repr(str(root/'src'))+');'
          'from polymarket_alpha_lab.research_process import ResearchProcessSpec,run_research_process;'
          f'spec=ResearchProcessSpec({value.argv!r},{value.cwd!r},{value.environment!r},{value.executable_sha256!r},30000);'
          'run_research_process(spec=spec,stdin=b"",allow_process_start=True)')
    parent=subprocess.Popen([executable[0],'-I','-S','-c',code],cwd=tmp_path,env=dict(value.environment),
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+12
        while not marker.exists() and parent.poll() is None and time.monotonic()<deadline:time.sleep(.01)
        assert marker.exists(),'synthetic child did not start'
        pid=int(marker.read_text());assert not _gone(pid)
        parent.kill();parent.wait(timeout=5)
        deadline=time.monotonic()+5
        while not _gone(pid) and time.monotonic()<deadline:time.sleep(.01)
        assert _gone(pid)
    finally:
        if parent.poll() is None:parent.kill()
        parent.wait(timeout=5)


@pytest.mark.parametrize('fault',[KeyboardInterrupt(),SystemExit(0)])
def test_partial_launch_cleanup_error_does_not_swallow_original_interrupt(monkeypatch,executable,tmp_path,fault):
    pairs=iter(((10,11),(12,13),(14,15)))
    monkeypatch.setattr(core.os,'pipe',lambda:next(pairs))
    monkeypatch.setattr(core.os,'set_blocking',lambda *a:None)
    owner=SimpleNamespace()
    monkeypatch.setattr(core,'_LinuxProcess',lambda *a:owner)
    monkeypatch.setattr(windows,'OwnedWindowsProcess',lambda *a:owner)
    def close(_):raise fault
    def cleanup(*args):raise OSError('secondary cleanup failure')
    monkeypatch.setattr(core.os,'close',close)
    monkeypatch.setattr(core,'_cleanup',cleanup)
    with pytest.raises(type(fault)) as error:core._spawn(spec(executable,tmp_path))
    assert error.value is fault


@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize('later', ['wait-error', 'deadline'])
def test_cleanup_retains_first_interrupt_after_wait_failure(monkeypatch, kind, later):
    original = kind('original interruption')
    events = []
    now = [0]
    attempts = [0]

    def terminate():
        events.append('terminate')
        attempts[0] += 1
        if attempts[0] == 1:
            raise original
        if later == 'wait-error':
            raise OSError('secondary failure')
        now[0] = 1000001

    owner = SimpleNamespace(terminate=terminate, is_closed=lambda: False,
                            close=lambda: events.append('owner-close'))
    monkeypatch.setattr(core.time, 'monotonic_ns', lambda: now[0])
    monkeypatch.setattr(core.os, 'close', lambda fd: events.append(fd))
    with pytest.raises(kind) as error:
        core._cleanup(owner, [101, 102, 103], 1)
    assert error.value is original
    assert events == ['terminate', 'terminate', 101, 102, 103, 'owner-close']


@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize('index', [0, 1, 2], ids=['stdin', 'stdout', 'stderr'])
def test_close_interruption_never_closes_reused_descriptor(monkeypatch, executable, tmp_path, kind, index):
    # Simulate close taking effect, then a signal handler allocating the freed
    # descriptor and raising. No real foreign descriptors are closed by the test.
    original = kind('original close interruption')
    target = 101 + index
    closed = []
    foreign_closed = []
    owner = SimpleNamespace(terminate=lambda: None, is_closed=lambda: True,
                            close=lambda: None, poll=lambda: 0)

    def close(fd):
        if fd == target and target in closed:
            foreign_closed.append(fd)
        closed.append(fd)
        if fd == target and closed.count(fd) == 1:
            raise original

    with monkeypatch.context() as patch:
        patch.setattr(core, '_verify_executable', lambda _: None)
        patch.setattr(core, '_spawn', lambda _: (owner, (101, 102, 103)))
        patch.setattr(core.os, 'close', close)
        patch.setattr(core.os, 'read', lambda *_: b'')
        with pytest.raises(kind) as error:
            run(spec(executable, tmp_path))
    assert error.value is original
    assert foreign_closed == []
    assert sorted(closed) == [101, 102, 103]


@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize('name', ['job', 'process'])
def test_windows_closed_handle_is_not_owned_again_after_interruption(kind, name):
    original = kind('original Windows close interruption')
    handles = {'job': 201, 'process': 202}
    closed = []
    foreign_closed = []

    def close(handle):
        if handle in closed:
            foreign_closed.append(handle)
        closed.append(handle)
        if handle == handles[name] and closed.count(handle) == 1:
            raise original
        return True

    owner = windows.OwnedWindowsProcess.__new__(windows.OwnedWindowsProcess)
    owner.api = SimpleNamespace(CloseHandle=close)
    owner.job, owner.process = 201, 202
    with pytest.raises(kind) as error:
        owner.close()
    assert error.value is original
    owner.close()
    assert owner.job is owner.process is None
    assert foreign_closed == [] and closed == [201, 202]


@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
def test_windows_constructor_relinquishes_closed_thread_before_cancel(monkeypatch, executable, tmp_path, kind):
    original = kind('closed thread interruption')
    closed = []
    foreign_closed = []
    def attribute_size(_buffer, _count, _flags, length):
        length._obj.value = 64
        return True
    def create(*args):
        args[-1]._obj.hProcess = 302
        args[-1]._obj.hThread = 303
        return True
    def close(handle):
        if handle in closed:
            foreign_closed.append(handle)
        closed.append(handle)
        if handle == 303 and closed.count(handle) == 1:
            raise original
        return True
    api = SimpleNamespace(CreateJobObjectW=lambda *_: 301,
        SetInformationJobObject=lambda *_: True,
        InitializeProcThreadAttributeList=attribute_size,
        UpdateProcThreadAttribute=lambda *_: True,
        DeleteProcThreadAttributeList=lambda *_: None,
        CreateProcessW=create, AssignProcessToJobObject=lambda *_: True,
        ResumeThread=lambda *_: 1, CloseHandle=close,
        TerminateProcess=lambda *_: True, WaitForSingleObject=lambda *_: 0)
    monkeypatch.setattr(windows, '_api', lambda: api)
    monkeypatch.setitem(sys.modules, 'msvcrt', SimpleNamespace(get_osfhandle=lambda fd: fd))
    monkeypatch.setattr(os, 'set_handle_inheritable', lambda *_: None, raising=False)
    with pytest.raises(kind) as error:
        windows.OwnedWindowsProcess(spec(executable, tmp_path), (401, 402, 403))
    assert error.value is original
    assert foreign_closed == [] and sorted(closed) == [301, 302, 303]


@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
def test_cleanup_relinquishes_descriptors_even_if_close_is_interrupted(monkeypatch, kind):
    original = kind('closed descriptor interruption')
    seen = []
    def close(fd):
        seen.append(fd)
        if fd == 101 and seen.count(fd) == 1:
            raise original
    owner = SimpleNamespace(terminate=lambda: None, is_closed=lambda: True, close=lambda: None)
    descriptors = [101, 102, 103]
    monkeypatch.setattr(core.os, 'close', close)
    with pytest.raises(kind) as error:
        core._cleanup(owner, descriptors, 1000)
    assert error.value is original
    core._cleanup(owner, descriptors, 1000)
    assert seen == [101, 102, 103]
    assert descriptors == [None, None, None]


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux FIFO image validation')
def test_fifo_executable_is_rejected_without_waiting_for_a_writer(executable, tmp_path):
    fifo = tmp_path / 'not-a-native-image'
    os.mkfifo(fifo)
    root = Path(__file__).resolve().parents[1]
    code = (f'import sys;sys.path.insert(0,{str(root / "src")!r})\n'
            'from polymarket_alpha_lab import research_process as core\n'
            f'value=core.ResearchProcessSpec(({str(fifo)!r},),{str(tmp_path)!r},(),"0"*64,100)\n'
            'def forbidden(_): raise AssertionError("unverified process launched")\n'
            'core._spawn=forbidden\n'
            'try: core.run_research_process(spec=value,stdin=b"",allow_process_start=True)\n'
            'except core.ResearchProcessError: print("rejected")\n'
            'else: raise AssertionError("FIFO accepted")\n')
    try:
        child = subprocess.run([executable[0], '-I', '-S', '-c', code],
            cwd=tmp_path, env={}, capture_output=True, check=False, timeout=5)
    except subprocess.TimeoutExpired:
        pytest.fail('Image validation blocked waiting for a FIFO writer')
    assert child.returncode == 0 and child.stdout == b'rejected\n' and child.stderr == b''


@pytest.mark.parametrize('stage', ['fstat', 'read'])
@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
def test_image_close_error_preserves_verification_interruption(monkeypatch, executable, tmp_path, stage, kind):
    """Cancellation before launch must not turn into an ordinary model failure."""
    import stat
    request = spec(executable, tmp_path)
    original = kind('PRIVATE-IMAGE-INTERRUPTION')
    closed = []
    def interrupted(*_): raise original
    def failed_close(fd):
        closed.append(fd)
        raise OSError('PRIVATE-IMAGE-CLOSE-ERROR')
    with monkeypatch.context() as patch:
        patch.setattr(core.os, 'open', lambda *_: 998)
        patch.setattr(core.os, 'fstat', interrupted if stage == 'fstat' else
                      lambda _: SimpleNamespace(st_mode=stat.S_IFREG, st_size=4))
        patch.setattr(core.os, 'read', interrupted)
        patch.setattr(core.os, 'close', failed_close)
        patch.setattr(core, '_spawn', lambda _: pytest.fail('unverified process launched'))
        with pytest.raises(kind) as caught:
            core.run_research_process(spec=request, stdin=b'', allow_process_start=True)
        assert caught.value is original
    assert closed == [998]


@pytest.mark.parametrize('kind', [KeyboardInterrupt, SystemExit])
def test_image_close_interruption_outranks_ordinary_validation_failure(monkeypatch, executable, tmp_path, kind):
    request = spec(executable, tmp_path)
    original = kind('PRIVATE-IMAGE-CLOSE-INTERRUPTION')
    closed = []
    def invalid(*_): raise ValueError('PRIVATE-IMAGE-VALIDATION-ERROR')
    def interrupted_close(fd): closed.append(fd); raise original
    with monkeypatch.context() as patch:
        patch.setattr(core.os, 'open', lambda *_: 998)
        patch.setattr(core.os, 'fstat', invalid)
        patch.setattr(core.os, 'close', interrupted_close)
        patch.setattr(core, '_spawn', lambda _: pytest.fail('unverified process launched'))
        with pytest.raises(kind) as caught:
            core.run_research_process(spec=request, stdin=b'', allow_process_start=True)
        assert caught.value is original
    assert closed == [998]


@pytest.mark.parametrize('kind', [OSError, KeyboardInterrupt, SystemExit])
def test_verified_image_close_failure_never_launches_or_retries(monkeypatch, executable, tmp_path, kind):
    from hashlib import sha256
    import stat
    image = b'MZ' if os.name == 'nt' else b'\x7fELF'
    request = replace(spec(executable, tmp_path), executable_sha256=sha256(image).hexdigest())
    original = kind('PRIVATE-VERIFIED-CLOSE-ERROR')
    blocks = iter((image, b''))
    closed = []
    def close(fd): closed.append(fd); raise original
    with monkeypatch.context() as patch:
        patch.setattr(core.os, 'open', lambda *_: 998)
        patch.setattr(core.os, 'fstat', lambda _: SimpleNamespace(st_mode=stat.S_IFREG, st_size=len(image)))
        patch.setattr(core.os, 'read', lambda *_: next(blocks))
        patch.setattr(core.os, 'close', close)
        patch.setattr(core, '_spawn', lambda _: pytest.fail('process launched after failed close'))
        expected = core.ResearchProcessError if kind is OSError else kind
        with pytest.raises(expected) as caught:
            core.run_research_process(spec=request, stdin=b'', allow_process_start=True)
        if kind is OSError:
            assert str(caught.value) == 'research_process_failed'
        else:
            assert caught.value is original
    assert closed == [998]
