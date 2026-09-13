"""Native children resolve their project libraries, never a caller's PATH."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.project_postgres import files, runtime


@pytest.mark.parametrize('program', runtime.PROGRAMS)
def test_windows_native_spawn_uses_only_private_and_system_search_paths(tmp_path, program):
    prefix = tmp_path / 'Private Runtime'
    exe = prefix / 'bin' / (program + '.exe')
    root = tmp_path / 'Windows'
    env = {'Path': 'UNTRUSTED_PATH', 'PATH': 'another', 'ComSpec': 'foreign-shell',
           'SystemRoot': str(root), 'PGPASSFILE': 'private-passfile', 'OTHER': 'kept'}
    settings = runtime.native_spawn_settings(str(exe), env, windows=True)
    assert settings['cwd'] == str(prefix / 'bin')
    child = settings['env']
    assert child['PATH'].split(';') == [str(prefix / 'bin'), str(prefix / 'lib'),
                                       str(root / 'System32'), str(root)]
    assert child['COMSPEC'] == str(root / 'System32/cmd.exe')
    assert 'Path' not in child and 'ComSpec' not in child
    assert child['PGPASSFILE'] == 'private-passfile'
    assert child['OTHER'] == 'kept'
    assert env['Path'] == 'UNTRUSTED_PATH'
    assert not child.get('PG_RESTRICT_EXEC')  # Never disable PostgreSQL privilege dropping.


def test_nonwindows_spawn_does_not_introduce_library_overrides(tmp_path):
    env = {'PATH': '/usr/bin', 'PGPASSFILE': 'private'}
    settings = runtime.native_spawn_settings(str(tmp_path / 'bin/initdb'), env, windows=False)
    assert settings == {'env': env}
    assert 'LD_LIBRARY_PATH' not in settings['env']


@pytest.mark.parametrize('name', ('other.exe', 'python.exe'))
def test_native_spawn_rejects_other_programs(tmp_path, name):
    with pytest.raises(files.ProjectDatabaseError, match='program_not_allowed'):
        runtime.native_spawn_settings(str(tmp_path / 'bin' / name), {'SystemRoot': str(tmp_path)}, windows=True)


def test_native_spawn_requires_absolute_program_and_system_root(tmp_path):
    for exe, env in (('bin/initdb.exe', {'SystemRoot': str(tmp_path)}),
                     (str(tmp_path / 'bin/initdb.exe'), {}),
                     (str(tmp_path / 'bin/initdb.exe'), {'SystemRoot': 'relative'})):
        with pytest.raises(files.ProjectDatabaseError):
            runtime.native_spawn_settings(exe, env, windows=True)


def test_command_forwards_cwd_without_changing_parent(monkeypatch, tmp_path):
    original = Path.cwd()
    calls = []
    monkeypatch.setattr(files.subprocess, 'run', lambda args, **kw:
        calls.append(kw) or SimpleNamespace(returncode=0))
    files.command(['fixture'], cwd=str(tmp_path))
    assert calls[0]['cwd'] == str(tmp_path)
    assert calls[0]['shell'] is False
    assert Path.cwd() == original


@pytest.mark.parametrize('windows', (True, False))
def test_archive_directories_inherit_private_windows_acl_not_owner_alias(tmp_path, monkeypatch, windows):
    from hashlib import sha256
    import zipfile
    root = tmp_path / 'Project'
    (root / 'database').mkdir(parents=True)
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (root / 'database/migrations.lock.json').write_text('{}')
    archive = tmp_path / 'runtime.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        for name in ('bin/fixture', 'lib/fixture', 'share/fixture'):
            output.writestr('pgsql/' + name, b'Synthetic runtime fixture')
    calls = []
    original = Path.mkdir
    def mkdir(path, *args, **kwargs):
        if path.name in ('bin', 'lib', 'share') and path.parent.name == 'postgres.installing':
            calls.append(kwargs.get('mode', 0o777))
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'mkdir', mkdir)
    monkeypatch.setattr(runtime, 'os', SimpleNamespace(name='nt' if windows else 'posix'))
    monkeypatch.setattr(runtime, 'runtime_version', lambda _: '17.11')
    runtime.import_runtime_archive(root, archive, expected_sha256=sha256(archive.read_bytes()).hexdigest())
    assert calls == ([0o777] * 3 if windows else [0o700] * 3)
    assert (root / 'runtime/postgres/bin/fixture').read_bytes() == b'Synthetic runtime fixture'
