"""Regression contracts for the first actual Windows acceptance findings."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.project_postgres import files


def test_invalid_project_path_is_rejected_before_filesystem_lookup(tmp_path, monkeypatch):
    monkeypatch.setattr(files, 'no_links', lambda _: pytest.fail('invalid path reached the filesystem'))
    with pytest.raises(files.ProjectDatabaseError, match='unsupported_project_path'):
        files.Layout(tmp_path / 'invalid\nroot')


def test_windows_acl_uses_typed_constructors_and_only_fixed_diagnostics(tmp_path, monkeypatch):
    observed = []
    def fake(args, **kwargs):
        observed.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr(files, 'command', fake)
    files._windows_acl(tmp_path, create=True)
    args, kwargs = observed[0]
    assert '[System.IO.Directory]::SetAccessControl' in args[-1]
    assert '[System.Security.AccessControl.FileSystemAccessRule]::new' in args[-1]
    assert 'SetAccessRuleProtection($true,$false)' in args[-1]
    assert 'exit 0' in args[-1]
    assert kwargs['env']['PAL_PRIVATE_DIRECTORY'] == str(tmp_path)
    assert kwargs['env']['PAL_CREATE_ACL'] == '1'
    assert kwargs['accepted'] == (0, *range(10, 18))


@pytest.mark.parametrize('code', range(10, 18))
def test_windows_acl_failure_stages_do_not_leak_child_diagnostics(tmp_path, monkeypatch, code):
    monkeypatch.setattr(files, 'command', lambda *a, **kw: SimpleNamespace(
        returncode=code, stdout='synthetic-private-detail', stderr='synthetic-private-detail'))
    with pytest.raises(files.ProjectDatabaseError) as error:
        files._windows_acl(tmp_path, create=False)
    assert str(error.value) == 'project_postgres_private_permissions_required_' + str(code)
    assert 'synthetic-private-detail' not in repr(error.value)


def test_archive_rejects_filename_normalization_before_extraction():
    from polymarket_alpha_lab.project_postgres.runtime import zip_members
    import zipfile
    info = zipfile.ZipInfo('pgsql/bin/exe')
    info.orig_filename = 'pgsql\\bin\\exe'
    archive = SimpleNamespace(infolist=lambda: [info])
    with pytest.raises(files.ProjectDatabaseError, match='invalid_runtime_archive'):
        zip_members(archive)


def test_app_policies_preserve_legacy_row_level_security_without_bypass():
    from polymarket_alpha_lab.project_postgres.sql import GRANTS
    assert 'FOR SELECT TO pal_app USING (true)' in GRANTS
    assert 'FOR INSERT TO pal_app WITH CHECK (true)' in GRANTS
    assert "roles=ARRAY['pal_app']::name[]" in GRANTS
    assert 'DISABLE ROW LEVEL SECURITY' not in GRANTS
    assert 'ALTER ROLE' not in GRANTS
    assert 'project_postgres_policy_conflict' in GRANTS


def test_launcher_commands_do_not_leave_inherited_capture_pipes(monkeypatch):
    calls = []
    monkeypatch.setattr(files.subprocess, 'run', lambda args, **kwargs:
        calls.append(kwargs) or SimpleNamespace(returncode=0, stdout=None, stderr=None))
    files.command(['explicit-native-launcher'], capture_output=False)
    assert calls[0]['stdout'] == files.subprocess.DEVNULL
    assert calls[0]['stderr'] == files.subprocess.DEVNULL
    assert calls[0]['stdin'] == files.subprocess.DEVNULL
    assert not calls[0].get('capture_output')
    assert calls[0]['shell'] is False


def test_sql_commands_retain_captured_output_and_stdin_protocol(monkeypatch):
    calls = []
    monkeypatch.setattr(files.subprocess, 'run', lambda args, **kwargs:
        calls.append(kwargs) or SimpleNamespace(returncode=0, stdout='1', stderr=''))
    assert files.command(['explicit-psql'], stdin='SELECT 1;').stdout == '1'
    assert calls[0]['input'] == 'SELECT 1;'
    assert 'stdin' not in calls[0]
    assert calls[0]['capture_output'] is True


def test_pg_ctl_lifecycle_uses_uncaptured_output(monkeypatch):
    from polymarket_alpha_lab.project_postgres import server
    calls = []
    db = server.ProjectPostgres.__new__(server.ProjectPostgres)
    db.layout = SimpleNamespace(cluster=Path('private-data'))
    monkeypatch.setattr(db, '_program', lambda name: 'project-runtime/' + name)
    monkeypatch.setattr(server, 'command', lambda args, **kwargs:
        calls.append((args, kwargs)) or SimpleNamespace(returncode=0))
    db._control('start', '-w', '-t', '60')
    assert calls[0][1]['capture_output'] is False
    assert calls[0][0][0] == 'project-runtime/pg_ctl'
