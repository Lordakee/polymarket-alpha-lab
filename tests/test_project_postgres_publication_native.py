"""Actual Windows deny-delete directory handles against the real importer.

No synthetic rename exceptions: CreateFileW holds a real handle without
FILE_SHARE_DELETE. Uses only a fresh private test directory and trusted native
binaries. Never touches user data, service configuration or antivirus settings.
"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import time
import uuid

import pytest

from polymarket_alpha_lab.project_postgres import files, runtime, runtime_publish

ENABLED = (os.name == 'nt' and
           os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1')


def deny_directory_rename(path):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    # FILE_LIST_DIRECTORY; share READ|WRITE (not DELETE); OPEN_EXISTING;
    # FILE_FLAG_BACKUP_SEMANTICS permits a directory handle.
    handle = create(str(path), 1, 3, None, 3, 0x02000000, None)
    if handle == ctypes.c_void_p(-1).value:
        pytest.fail('test lock creation failed, Windows code ' + str(ctypes.get_last_error()))
    return lambda: close(handle)


@pytest.mark.skipif(not ENABLED, reason='explicit Windows native publication proof is opt-in')
@pytest.mark.parametrize('release_after_denial', (True, False))
def test_real_directory_handle_contention(tmp_path, monkeypatch, release_after_denial):
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    assert prefix.is_absolute() and (prefix / 'bin').is_dir()
    proof_root = Path(os.environ['RUNNER_TEMP']) / ('pal-publish-' + uuid.uuid4().hex)
    files.private_directory(proof_root, create=True)
    root = proof_root / 'Project With Spaces'
    root.mkdir()
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (root / 'database').mkdir()
    (root / 'database/migrations.lock.json').write_text('{}')
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    layout = files.Layout(root)
    attempts, errors, delays, versions = [], [], [], []
    original_publish = runtime.publish_runtime
    original_rename = Path.rename
    original_version = runtime.runtime_version

    def version(path):
        versions.append(1)
        return original_version(path)

    def locked_publish(layout, staging, **options):
        release = deny_directory_rename(staging)
        open_handle = True

        def rename(path, destination):
            if path == staging:
                attempts.append(1)
            try:
                return original_rename(path, destination)
            except OSError as error:
                if path == staging: errors.append(error.winerror)
                raise

        def pause(delay):
            nonlocal open_handle
            delays.append(delay)
            if release_after_denial and open_handle:
                assert release()
                open_handle = False
            time.sleep(delay)

        try:
            with monkeypatch.context() as scoped:
                scoped.setattr(Path, 'rename', rename)
                scoped.setattr(runtime_publish, 'sleep', pause)
                original_publish(layout, staging, **options)
        finally:
            if open_handle: assert release()

    monkeypatch.setattr(runtime, 'runtime_version', version)
    monkeypatch.setattr(runtime, 'publish_runtime', locked_publish)
    if release_after_denial:
        result = runtime.import_runtime_directory(root, prefix)
        assert result.startswith('17.')
        assert versions == [1]  # retry does not re-execute the five probes
        assert 2 <= len(attempts) <= 7
        assert not layout.runtime.with_name('postgres.installing').exists()
        assert runtime.verify_runtime(layout)['version'] == result
        print('native publication: transient real handle released; validated runtime published')
    else:
        with pytest.raises(files.ProjectDatabaseError, match='^project_postgres_runtime_publish_blocked$'):
            runtime.import_runtime_directory(root, prefix)
        assert versions == [1] and len(attempts) == 7
        assert tuple(delays) == runtime_publish.RETRY_DELAYS
        assert not layout.runtime.exists()
        staging = layout.runtime.with_name('postgres.installing')
        assert (staging / 'runtime.json').is_file()
        assert runtime.inventory(staging)
        with pytest.raises(files.ProjectDatabaseError, match='incomplete_runtime_install'):
            runtime.import_runtime_directory(root, prefix)
        assert len(attempts) == 7 and versions == [1]
        print('native publication: persistent real handle denied; staging retained, no false success')
    assert errors and all(code in (5, 32, 33) for code in errors)
    assert not layout.home.exists()  # no initdb, server or research execution
    with layout.lock(): pass  # the lifecycle lease was released on either path
