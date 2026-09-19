"""Windows-only owned process: suspended start -> Job assignment -> resume.

No global process enumeration, taskkill, breakaway flag, shell or privilege change.
The anonymous noninheritable job handle remains in the parent, so parent process
loss closes it and terminates the job. Nested-job denial fails without fallback.
"""
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
import os
import subprocess
from threading import Lock


_LAUNCH_LOCK = Lock()
SIZE_T = c.c_size_t


class _Startup(c.Structure):
    _fields_ = [('cb', w.DWORD), ('lpReserved', w.LPWSTR), ('lpDesktop', w.LPWSTR),
        ('lpTitle', w.LPWSTR), ('dwX', w.DWORD), ('dwY', w.DWORD),
        ('dwXSize', w.DWORD), ('dwYSize', w.DWORD), ('dwXCountChars', w.DWORD),
        ('dwYCountChars', w.DWORD), ('dwFillAttribute', w.DWORD), ('dwFlags', w.DWORD),
        ('wShowWindow', w.WORD), ('cbReserved2', w.WORD), ('lpReserved2', c.c_void_p),
        ('hStdInput', w.HANDLE), ('hStdOutput', w.HANDLE), ('hStdError', w.HANDLE)]


class _StartupEx(c.Structure):
    _fields_ = [('StartupInfo', _Startup), ('lpAttributeList', c.c_void_p)]


class _ProcessInfo(c.Structure):
    _fields_ = [('hProcess', w.HANDLE), ('hThread', w.HANDLE),
                ('dwProcessId', w.DWORD), ('dwThreadId', w.DWORD)]


class _BasicLimits(c.Structure):
    _fields_ = [('PerProcessUserTimeLimit', c.c_int64), ('PerJobUserTimeLimit', c.c_int64),
        ('LimitFlags', w.DWORD), ('MinimumWorkingSetSize', SIZE_T), ('MaximumWorkingSetSize', SIZE_T),
        ('ActiveProcessLimit', w.DWORD), ('Affinity', SIZE_T), ('PriorityClass', w.DWORD),
        ('SchedulingClass', w.DWORD)]


class _IO(c.Structure):
    _fields_ = [(name, c.c_uint64) for name in ('ReadOperationCount', 'WriteOperationCount',
        'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class _Limits(c.Structure):
    _fields_ = [('BasicLimitInformation', _BasicLimits), ('IoInfo', _IO),
        ('ProcessMemoryLimit', SIZE_T), ('JobMemoryLimit', SIZE_T),
        ('PeakProcessMemoryUsed', SIZE_T), ('PeakJobMemoryUsed', SIZE_T)]


class _Accounting(c.Structure):
    _fields_ = [(name, c.c_int64) for name in ('TotalUserTime', 'TotalKernelTime',
        'ThisPeriodTotalUserTime', 'ThisPeriodTotalKernelTime')] + [(name, w.DWORD) for name in
        ('TotalPageFaultCount', 'TotalProcesses', 'ActiveProcesses', 'TotalTerminatedProcesses')]


def _api():
    if os.name != 'nt' or c.sizeof(c.c_void_p) != 8:
        raise OSError('research_process_platform_unsupported')
    api = c.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateJobObjectW': (w.HANDLE, (c.c_void_p, w.LPCWSTR)),
        'SetInformationJobObject': (w.BOOL, (w.HANDLE, c.c_int, c.c_void_p, w.DWORD)),
        'QueryInformationJobObject': (w.BOOL, (w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p)),
        'AssignProcessToJobObject': (w.BOOL, (w.HANDLE, w.HANDLE)),
        'TerminateJobObject': (w.BOOL, (w.HANDLE, w.UINT)),
        'TerminateProcess': (w.BOOL, (w.HANDLE, w.UINT)),
        'WaitForSingleObject': (w.DWORD, (w.HANDLE, w.DWORD)),
        'GetExitCodeProcess': (w.BOOL, (w.HANDLE, c.POINTER(w.DWORD))),
        'CloseHandle': (w.BOOL, (w.HANDLE,)),
        'ResumeThread': (w.DWORD, (w.HANDLE,)),
        'InitializeProcThreadAttributeList': (w.BOOL, (c.c_void_p, w.DWORD, w.DWORD, c.POINTER(SIZE_T))),
        'UpdateProcThreadAttribute': (w.BOOL, (c.c_void_p, w.DWORD, SIZE_T, c.c_void_p, SIZE_T, c.c_void_p, c.c_void_p)),
        'DeleteProcThreadAttributeList': (None, (c.c_void_p,)),
        'CreateProcessW': (w.BOOL, (w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p,
            w.BOOL, w.DWORD, c.c_void_p, w.LPCWSTR, c.c_void_p, c.POINTER(_ProcessInfo))),
    }
    for name, (restype, argtypes) in signatures.items():
        function = getattr(api, name)
        function.restype, function.argtypes = restype, argtypes
    return api


def _checked(result):
    if not result:
        # Do not format a WinError with executable paths or environment content.
        raise OSError('research_process_windows_api_failed')
    return result


class OwnedWindowsProcess:
    def __init__(self, spec, descriptors):
        import msvcrt
        self.api = api = _api()
        self.job = self.process = None
        self.terminated = False
        thread = attributes = None
        initialized = False
        try:
            self.job = _checked(api.CreateJobObjectW(None, None))
            limits = _Limits()
            limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
            _checked(api.SetInformationJobObject(self.job, 9, c.byref(limits), c.sizeof(limits)))
            length = SIZE_T()
            api.InitializeProcThreadAttributeList(None, 1, 0, c.byref(length))
            if not 0 < length.value < 65536:
                raise OSError('research_process_windows_attributes_invalid')
            attributes = c.create_string_buffer(length.value)
            _checked(api.InitializeProcThreadAttributeList(attributes, 1, 0, c.byref(length)))
            initialized = True
            handles = (w.HANDLE * 3)(*(msvcrt.get_osfhandle(fd) for fd in descriptors))
            startup = _StartupEx()
            startup.StartupInfo.cb = c.sizeof(startup)
            startup.StartupInfo.dwFlags = 0x100  # USESTDHANDLES
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = handles
            startup.lpAttributeList = c.cast(attributes, c.c_void_p)
            _checked(api.UpdateProcThreadAttribute(attributes, 0, 0x20002,
                c.cast(handles, c.c_void_p), c.sizeof(handles), None, None))
            command = c.create_unicode_buffer(subprocess.list2cmdline(spec.argv))
            environment = c.create_unicode_buffer('\0'.join(k+'='+v for k, v in
                sorted(spec.environment, key=lambda pair: pair[0].upper())) + '\0\0')
            info = _ProcessInfo()
            # Restrict child inheritance to three pipes. Serialize the temporary
            # inheritance window for this module; other in-process broad-handle
            # launchers are outside this boundary and must follow the same rule.
            with _LAUNCH_LOCK:
                try:
                    for handle in handles:
                        os.set_handle_inheritable(handle, True)
                    _checked(api.CreateProcessW(spec.argv[0], command, None, None, True,
                        0x4 | 0x400 | 0x80000 | 0x8000000, environment, spec.cwd,
                        c.byref(startup), c.byref(info)))
                    self.process, thread = info.hProcess, info.hThread
                finally:
                    for handle in handles:
                        os.set_handle_inheritable(handle, False)
            # No target instruction runs before successful Job assignment.
            _checked(api.AssignProcessToJobObject(self.job, self.process))
            if api.ResumeThread(thread) == 0xffffffff:
                raise OSError('research_process_windows_resume_failed')
            _checked(api.CloseHandle(thread))
            thread = None
        except BaseException as original:
            try:
                if self.process is not None:
                    api.TerminateProcess(self.process, 1)
                    api.WaitForSingleObject(self.process, spec.cleanup_timeout_ms)
            finally:
                try:
                    self.close()
                except BaseException as cleanup:
                    if isinstance(original, Exception) and not isinstance(cleanup, Exception):
                        raise cleanup from None
            raise original
        finally:
            if thread is not None:
                api.CloseHandle(thread)
            if initialized:
                api.DeleteProcThreadAttributeList(attributes)

    def poll(self):
        status = self.api.WaitForSingleObject(self.process, 0)
        if status == 258:  # WAIT_TIMEOUT
            return None
        if status != 0:
            raise OSError('research_process_windows_wait_failed')
        code = w.DWORD()
        _checked(self.api.GetExitCodeProcess(self.process, c.byref(code)))
        return code.value

    def terminate(self):
        if not self.terminated:
            _checked(self.api.TerminateJobObject(self.job, 1))
            self.terminated = True

    def is_closed(self):
        accounting = _Accounting()
        _checked(self.api.QueryInformationJobObject(self.job, 1, c.byref(accounting),
                                                    c.sizeof(accounting), None))
        return accounting.ActiveProcesses == 0 and self.poll() is not None

    def close(self):
        # Attempt both handle closes; a failed close is not successful cleanup.
        failure = None
        for name in ('job', 'process'):
            handle = getattr(self, name)
            if handle is not None:
                try:
                    _checked(self.api.CloseHandle(handle))
                    setattr(self, name, None)
                except BaseException as error:
                    if failure is None or isinstance(failure, Exception) and not isinstance(error, Exception):
                        failure = error
        if failure is not None:
            raise failure
