"""Separate same-assistant adversarial checks of test-evidence boundaries."""
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from tests import packaged_research_flow as flow


@pytest.mark.parametrize('origin', ['other/src/mod.py', 'kit-sibling/src/mod.py'])
def test_foreign_or_similarly_named_root_cannot_count_as_kit_source(monkeypatch, tmp_path, origin):
    module = SimpleNamespace(__file__=str(tmp_path/origin))
    monkeypatch.setattr(flow, 'sys', SimpleNamespace(modules={'polymarket_alpha_lab.fake': module}))
    with pytest.raises(AssertionError, match='checkout code used'):
        flow.assert_origins(tmp_path/'kit')


def test_no_project_modules_is_not_a_successful_origin_check(monkeypatch, tmp_path):
    monkeypatch.setattr(flow, 'sys', SimpleNamespace(modules={}))
    with pytest.raises(AssertionError, match='no project modules'):
        flow.assert_origins(tmp_path)


def test_recipe_timeout_is_preserved_without_retry(monkeypatch, tmp_path):
    original = subprocess.TimeoutExpired('synthetic', 300)
    calls = []
    def fail(*args, **kwargs):
        calls.append(1); raise original
    monkeypatch.setattr(flow.subprocess, 'run', fail)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        flow.run_packaged_recipe(tmp_path, sys.executable, tmp_path)
    assert caught.value is original and calls == [1]


def test_missing_kit_cannot_use_installed_checkout_or_start_database(tmp_path):
    root = tmp_path/'missing-kit'; root.mkdir()
    before = list(root.iterdir())
    result = flow.run_packaged_recipe(root, sys.executable, tmp_path)
    assert result.returncode != 0 and 'kit source missing' in result.stderr
    assert 'packaged_flow_verified' not in result.stdout
    assert list(root.iterdir()) == before


def test_read_failure_does_not_launch_an_empty_recipe(monkeypatch, tmp_path):
    def fail(*args, **kwargs): raise OSError('synthetic fixture unavailable')
    monkeypatch.setattr(Path, 'read_text', fail)
    monkeypatch.setattr(flow.subprocess, 'run', lambda *a, **k: pytest.fail('empty recipe launched'))
    with pytest.raises(OSError, match='synthetic fixture unavailable'):
        flow.run_packaged_recipe(tmp_path, sys.executable, tmp_path)
