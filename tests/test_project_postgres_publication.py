"""Runtime rename resilience only; no database, native executable or network."""
import errno
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.project_postgres import files, runtime


def denied(code=5):
    error = PermissionError(errno.EACCES, 'private-path-or-loader-detail')
    error.winerror = code
    return error


@pytest.fixture
def staged(tmp_path, monkeypatch):
    root = tmp_path / 'Project With Spaces'
    root.mkdir()
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (root / 'database').mkdir()
    (root / 'database/migrations.lock.json').write_text('{}')
    layout = files.Layout(root)
    target = runtime._staging(layout)
    for name in ('bin', 'lib', 'share'):
        (target / name).mkdir()
        (target / name / 'fixture').write_bytes(b'synthetic engine bytes')
    probes = []
    monkeypatch.setattr(runtime, 'runtime_version', lambda p: probes.append(p) or '17.11')
    # Set on the old code too so the RED check reaches its real rename path.
    monkeypatch.setattr(runtime, '_WINDOWS_PUBLICATION', True, raising=False)
    return layout, target, probes


@pytest.mark.parametrize('code', (5, 32, 33))
def test_transient_rename_reuses_verified_staging_and_probes_only_once(staged, monkeypatch, code):
    layout, target, probes = staged
    calls = []
    original = Path.rename

    def rename(path, destination):
        calls.append((path, destination))
        if len(calls) <= 2:
            raise denied(code)
        return original(path, destination)

    monkeypatch.setattr(Path, 'rename', rename)
    assert runtime._finish_import(layout, target) == '17.11'
    assert len(calls) == 3
    assert probes == [target]
    assert not target.exists()
    assert json.loads((layout.runtime / 'runtime.json').read_text())['version'] == '17.11'
    assert (layout.runtime / 'bin/fixture').read_bytes() == b'synthetic engine bytes'


@pytest.fixture
def pauses(monkeypatch):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    calls = []
    monkeypatch.setattr(p, 'sleep', calls.append)
    return calls


@pytest.mark.parametrize('code', (5, 32, 33))
def test_permanent_denial_has_finite_budget_and_keeps_staging(staged, pauses, monkeypatch, code, capsys):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    layout, target, probes = staged
    attempts = []

    def blocked(path, destination):
        attempts.append(path)
        raise denied(code)

    monkeypatch.setattr(Path, 'rename', blocked)
    with pytest.raises(files.ProjectDatabaseError, match='^project_postgres_runtime_publish_blocked$') as caught:
        runtime._finish_import(layout, target)
    assert len(attempts) == 7 and tuple(pauses) == p.RETRY_DELAYS
    assert sum(pauses) == pytest.approx(5.1)
    assert probes == [target] and target.is_dir() and not layout.runtime.exists()
    assert (target / 'bin/fixture').read_bytes() == b'synthetic engine bytes'
    assert 'private-path' not in repr(caught.value)
    assert caught.value.__suppress_context__ is True and capsys.readouterr() == ('', '')
    with pytest.raises(files.ProjectDatabaseError, match='incomplete_runtime_install'):
        runtime._staging(layout)


@pytest.mark.parametrize('windows,code', ((False, 5), (False, 32), (True, 2), (True, 3),
    (True, 17), (True, 80), (True, 112), (True, 183), (True, None)))
def test_other_errors_do_not_retry(staged, pauses, monkeypatch, windows, code):
    layout, target, _ = staged
    attempts = []
    monkeypatch.setattr(runtime, '_WINDOWS_PUBLICATION', windows)

    def fail_once(*_):
        attempts.append(1)
        raise denied(code)

    monkeypatch.setattr(Path, 'rename', fail_once)
    with pytest.raises(files.ProjectDatabaseError, match='^project_postgres_runtime_publish_failed$'):
        runtime._finish_import(layout, target)
    assert attempts == [1] and pauses == []
    assert target.is_dir() and not layout.runtime.exists()


@pytest.mark.parametrize('kind', ('empty-directory', 'file'))
def test_competing_destination_after_denial_never_overwritten(staged, monkeypatch, kind):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    layout, target, _ = staged
    calls = []

    def blocked(*_):
        calls.append(1)
        raise denied()

    def during_pause(_):
        if kind == 'file':
            layout.runtime.write_bytes(b'foreign')
        else:
            layout.runtime.mkdir()

    monkeypatch.setattr(Path, 'rename', blocked)
    monkeypatch.setattr(p, 'sleep', during_pause)
    with pytest.raises(files.ProjectDatabaseError, match='runtime_already_installed'):
        runtime._finish_import(layout, target)
    assert calls == [1] and target.exists()
    if kind == 'file':
        assert layout.runtime.read_bytes() == b'foreign'
    else:
        assert list(layout.runtime.iterdir()) == []


@pytest.mark.parametrize('kind', ('engine', 'manifest', 'notice', 'new-engine-file', 'removed-engine-file'))
def test_content_mutation_between_attempts_fails_without_another_rename(staged, monkeypatch, kind):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    layout, target, probes = staged
    (target / 'LICENSE').write_bytes(b'original notice')
    calls = []

    def blocked(*_):
        calls.append(1)
        raise denied()

    def mutate(_):
        if kind == 'removed-engine-file':
            (target / 'bin/fixture').unlink()
        else:
            name = {'engine': 'bin/fixture', 'manifest': 'runtime.json',
                    'notice': 'LICENSE', 'new-engine-file': 'bin/extra'}[kind]
            (target / name).write_bytes(b'changed')

    monkeypatch.setattr(Path, 'rename', blocked)
    monkeypatch.setattr(p, 'sleep', mutate)
    with pytest.raises(files.ProjectDatabaseError, match='runtime_changed'):
        runtime._finish_import(layout, target)
    assert calls == [1] and probes == [target] and not layout.runtime.exists()


def test_staging_directory_replacement_detected(staged, monkeypatch):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    import shutil
    layout, target, _ = staged
    original = Path.rename
    calls = []

    def blocked(*_):
        calls.append(1)
        raise denied()

    def replace_staging(_):
        preserved = target.with_name('preserved-original')
        original(target, preserved)
        shutil.copytree(preserved, target)

    monkeypatch.setattr(Path, 'rename', blocked)
    monkeypatch.setattr(p, 'sleep', replace_staging)
    with pytest.raises(files.ProjectDatabaseError, match='runtime_publish_changed'):
        runtime._finish_import(layout, target)
    assert calls == [1] and not layout.runtime.exists()
    assert target.with_name('preserved-original').is_dir()


def test_permission_check_error_is_not_retried_or_repaired(staged, pauses, monkeypatch):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    layout, target, _ = staged
    seen = []

    def bad_acl(path, *, create=False):
        seen.append(create)
        files.fail('project_postgres_private_permissions_required')

    monkeypatch.setattr(p, 'private_directory', bad_acl)
    monkeypatch.setattr(Path, 'rename', lambda *_: pytest.fail('unverified rename'))
    with pytest.raises(files.ProjectDatabaseError, match='private_permissions_required'):
        runtime._finish_import(layout, target)
    assert seen == [False] and pauses == [] and target.exists()


def test_error_during_integrity_check_is_not_treated_as_rename_denial(staged, pauses, monkeypatch):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    layout, target, _ = staged
    monkeypatch.setattr(Path, 'rename', lambda *_: pytest.fail('unverified rename'))
    with pytest.raises(files.ProjectDatabaseError, match='runtime_publish_failed'):
        p.publish_runtime(layout, target, validate=lambda _: (_ for _ in ()).throw(denied()), windows=True)
    assert pauses == [] and target.is_dir()


def test_already_present_destination_is_not_adopted(staged, pauses, monkeypatch):
    layout, target, _ = staged
    layout.runtime.mkdir()
    monkeypatch.setattr(Path, 'rename', lambda *_: pytest.fail('would overwrite'))
    with pytest.raises(files.ProjectDatabaseError, match='runtime_already_installed'):
        runtime._finish_import(layout, target)
    assert target.exists() and list(layout.runtime.iterdir()) == [] and pauses == []


def test_unrelated_staging_path_is_refused(staged, pauses):
    from polymarket_alpha_lab.project_postgres import runtime_publish as p
    layout, target, _ = staged
    with pytest.raises(files.ProjectDatabaseError, match='runtime_publish_changed'):
        p.publish_runtime(layout, target.with_name('other'), validate=lambda _: None, windows=True)
    assert pauses == []


def test_post_rename_validation_cannot_return_false_success(staged, pauses, monkeypatch):
    layout, target, _ = staged
    original = Path.rename

    def change_after_rename(path, destination):
        result = original(path, destination)
        (destination / 'bin/fixture').write_bytes(b'changed')
        return result

    monkeypatch.setattr(Path, 'rename', change_after_rename)
    with pytest.raises(files.ProjectDatabaseError, match='runtime_changed'):
        runtime._finish_import(layout, target)
    assert layout.runtime.is_dir() and not target.exists() and pauses == []


def test_keyboard_interrupt_is_not_swallowed(staged, pauses, monkeypatch):
    layout, target, _ = staged
    monkeypatch.setattr(Path, 'rename', lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        runtime._finish_import(layout, target)
    assert pauses == [] and target.is_dir() and not layout.runtime.exists()


@pytest.mark.parametrize('source_kind', ('directory', 'archive'))
def test_public_import_holds_lease_and_never_repeats_copy_or_probes(tmp_path, monkeypatch, pauses, source_kind):
    from hashlib import sha256
    import zipfile
    root = tmp_path / 'Root'
    root.mkdir()
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (root / 'database').mkdir()
    (root / 'database/migrations.lock.json').write_text('{}')
    source = tmp_path / 'trusted-source'
    for name in ('bin', 'lib', 'share'):
        (source / name).mkdir(parents=True)
        (source / name / 'fixture').write_bytes(b'fixture')
    archive = tmp_path / 'trusted.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for path in source.rglob('*'):
            if path.is_file(): z.write(path, 'pgsql/' + path.relative_to(source).as_posix())
    layout = files.Layout(root)
    monkeypatch.setattr(runtime, '_WINDOWS_PUBLICATION', True)
    versions = []
    monkeypatch.setattr(runtime, 'runtime_version', lambda p: versions.append(p) or '17.11')
    original = Path.rename
    attempts = []

    def rename(path, destination):
        attempts.append(1)
        with pytest.raises(files.ProjectDatabaseError, match='busy'):
            with layout.lock(): pass
        if len(attempts) == 1: raise denied()
        return original(path, destination)

    monkeypatch.setattr(Path, 'rename', rename)
    if source_kind == 'directory':
        version = runtime.import_runtime_directory(root, source)
    else:
        version = runtime.import_runtime_archive(root, archive, expected_sha256=sha256(archive.read_bytes()).hexdigest())
    assert version == '17.11' and attempts == [1, 1] and len(versions) == 1
    assert (layout.runtime / 'bin/fixture').read_bytes() == b'fixture'
    assert not layout.home.exists()  # engine import never initializes a database


def test_cli_returns_fixed_code_without_paths_or_traceback(tmp_path, monkeypatch, capsys):
    from polymarket_alpha_lab.project_postgres import cli
    monkeypatch.setattr(cli, 'import_runtime_directory', lambda *a: files.fail('project_postgres_runtime_publish_blocked'))
    assert cli.main(['--root', str(tmp_path), 'install-runtime', '--from-directory', str(tmp_path)]) == 1
    output = capsys.readouterr()
    assert output.out == ''
    assert json.loads(output.err) == {'status': 'blocked', 'reason_code': 'project_postgres_runtime_publish_blocked'}
    assert str(tmp_path) not in output.err


@pytest.mark.parametrize('failures', (0, 6))
def test_first_and_last_allowed_success(staged, pauses, monkeypatch, failures):
    layout, target, probes = staged
    original = Path.rename
    attempts = []

    def rename(path, destination):
        attempts.append(1)
        if len(attempts) <= failures: raise denied()
        return original(path, destination)

    monkeypatch.setattr(Path, 'rename', rename)
    assert runtime._finish_import(layout, target) == '17.11'
    assert len(attempts) == failures + 1 and len(pauses) == failures
    assert probes == [target]
