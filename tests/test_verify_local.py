from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify_local.py"
FOCUSED_TESTS = {
    "test_cli_report_discovery.py",
    "test_phase1_report_discovery_smoke.py",
    "test_phase1_report_modules_import_no_io.py",
    "test_supabase_local_dsn.py",
    "test_verify_local.py",
}
SOURCE_ENV = {
    "PATH": "synthetic-search-path",
    "UNRELATED_SETTING": "preserved",
    "POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE": "1",
    "POLYMARKET_ALPHA_LAB_POSTGRES_DSN": "synthetic-value-never-connect",
    "POLYMARKET_ALPHA_LAB_FUTURE_SETTING": "enabled",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0",
    "PYTEST_ADDOPTS": "-k unintended-selection",
    "PYTEST_PLUGINS": "synthetic_plugin",
    "PYTHONPATH": "synthetic-import-path",
    "PYTHONHOME": "synthetic-python-home",
}
CHILD_ENV = {
    "PATH": "synthetic-search-path",
    "UNRELATED_SETTING": "preserved",
    "POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE": "0",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
}
Step = tuple[list[str], Path, dict[str, str], str | None]


def assert_sanitized_environment(environment: dict[str, str]) -> None:
    assert {key: environment[key] for key in CHILD_ENV} == CHILD_ENV
    assert {key for key in environment if key.startswith("POLYMARKET_ALPHA_LAB_")} == {
        "POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE"
    }
    assert {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH", "PYTHONHOME"}.isdisjoint(environment)


@pytest.fixture
def verifier(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    def unexpected_process(*args: object, **kwargs: object) -> None:
        pytest.fail("Verifier tests must not launch real subprocesses")

    monkeypatch.setattr(subprocess, "run", unexpected_process)
    spec = importlib.util.spec_from_file_location("verify_local_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def steps(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> list[Step]:
    monkeypatch.setattr(os, "environ", SOURCE_ENV.copy())
    monkeypatch.setattr(sys, "base_prefix", sys.prefix + "-base-interpreter")
    console = tmp_path / ("polymarket-alpha-lab.exe" if os.name == "nt" else "polymarket-alpha-lab")
    console.touch()
    original_get_path = sysconfig.get_path
    monkeypatch.setattr(
        sysconfig,
        "get_path",
        lambda name, *args, **kwargs: (
            str(tmp_path) if name == "scripts" else original_get_path(name, *args, **kwargs)
        ),
    )
    recorded: list[Step] = []

    def record(label, command, *, cwd, env, expected_output=None):
        assert isinstance(command, list)
        assert all(isinstance(argument, str) for argument in command)
        recorded.append((command.copy(), Path(cwd).resolve(), env.copy(), expected_output))
        return 0

    monkeypatch.setattr(verifier, "run_step", record)
    monkeypatch.chdir(tmp_path)
    return recorded


def test_build_environment_filters_inherited_settings_without_mutating_parent(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = SOURCE_ENV.copy()
    monkeypatch.setattr(os, "environ", parent)

    child = verifier.build_environment()

    assert_sanitized_environment(child)
    assert child is not parent
    assert os.environ is parent
    assert parent == SOURCE_ENV


def test_run_step_validates_stdout_and_passes_arguments_without_a_shell(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    command = [str(tmp_path / "python with spaces.exe"), "-m", "polymarket_alpha_lab", "--help"]
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return subprocess.CompletedProcess(arguments, 0, "usage: expected-marker\n", "")

    monkeypatch.setattr(subprocess, "run", run)

    assert verifier.run_step(
        "CLI help", command, cwd=tmp_path, env=CHILD_ENV, expected_output="expected-marker"
    ) == 0
    assert len(calls) == 1
    arguments, options = calls[0]
    assert arguments == command
    assert isinstance(arguments, list)
    assert not options.get("shell", False)
    assert options["stdin"] == subprocess.DEVNULL
    assert options["capture_output"] is True
    assert options["text"] is True
    assert options["encoding"] == "utf-8"
    assert options["errors"] == "replace"
    assert options["check"] is False
    assert Path(options["cwd"]) == tmp_path
    assert options["env"] == CHILD_ENV


@pytest.mark.parametrize(
    ("returncode", "expected", "expected_output"),
    [(0, 0, None), (7, 7, None), (-9, 1, None), (7, 7, "expected-marker")],
)
def test_run_step_propagates_process_status_with_or_without_captured_output(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str], returncode: int, expected: int,
    expected_output: str | None,
) -> None:
    def run(command, **kwargs):
        assert bool(kwargs.get("capture_output")) == (expected_output is not None)
        return subprocess.CompletedProcess(command, returncode, expected_output, None)

    monkeypatch.setattr(subprocess, "run", run)

    assert verifier.run_step(
        "focused tests", ["synthetic-python"], cwd=tmp_path, env=CHILD_ENV,
        expected_output=expected_output,
    ) == expected
    if expected:
        captured = capsys.readouterr()
        assert "focused tests" in captured.out + captured.err


@pytest.mark.parametrize("stdout", ["", "unrelated output"])
def test_run_step_rejects_missing_stdout_marker_even_if_stderr_contains_it(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str], stdout: str,
) -> None:
    monkeypatch.setattr(
        subprocess, "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, stdout, "expected-marker"),
    )

    assert verifier.run_step(
        "discovery output", ["synthetic-cli"], cwd=tmp_path, env=CHILD_ENV,
        expected_output="expected-marker",
    ) == 1
    captured = capsys.readouterr()
    assert "discovery output" in captured.out + captured.err


def test_run_step_reports_launch_failure(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def run(*args, **kwargs):
        raise FileNotFoundError("synthetic executable missing")

    monkeypatch.setattr(subprocess, "run", run)

    assert verifier.run_step("console help", ["synthetic-cli"], cwd=tmp_path, env=CHILD_ENV) == 1
    captured = capsys.readouterr()
    assert "console help" in captured.out + captured.err


@pytest.mark.parametrize("argv", [[], ["--quick"], ["--full"]], ids=["default", "quick", "full"])
def test_main_runs_isolated_cli_checks_one_test_suite_and_compilation(
    verifier: ModuleType, steps: list[Step], argv: list[str]
) -> None:
    parent_before = dict(os.environ)
    assert verifier.main(argv) == 0
    assert len(steps) == 7
    for _, _, environment, _ in steps:
        assert_sanitized_environment(environment)
    assert os.environ == parent_before

    installation = [step for step in steps if "-c" in step[0]]
    modules = [step for step in steps if "polymarket_alpha_lab" in step[0]]
    consoles = [step for step in steps if Path(step[0][0]).name in {"polymarket-alpha-lab", "polymarket-alpha-lab.exe"}]
    test_runs = [step for step in steps if "pytest" in step[0]]
    compile_runs = [step for step in steps if "compileall" in step[0]]
    assert len(installation) == len(test_runs) == len(compile_runs) == 1
    assert len(modules) == len(consoles) == 2
    assert installation[0][0][:3] == [sys.executable, "-I", "-c"]
    for command, _, _, _ in modules:
        assert command[:4] == [sys.executable, "-I", "-m", "polymarket_alpha_lab"]
    module_actions = {tuple(step[0][4:]) for step in modules}
    assert module_actions == {tuple(step[0][1:]) for step in consoles}
    assert ("--help",) in module_actions
    assert any(action[0] == "report-discovery" for action in module_actions)
    for _, cwd, _, expected_output in installation + modules + consoles:
        assert cwd != REPO_ROOT and not cwd.is_relative_to(REPO_ROOT)
        assert isinstance(expected_output, str) and expected_output

    test_command, test_cwd, _, _ = test_runs[0]
    assert test_cwd == REPO_ROOT
    assert test_command[:3] == [sys.executable, "-m", "pytest"]
    assert "-q" in test_command
    if argv == ["--full"]:
        assert test_command[3:] == ["-q", "-ra"]
    else:
        selected = {(test_cwd / argument).resolve() for argument in test_command[3:] if not argument.startswith("-")}
        assert selected == {REPO_ROOT / "tests" / name for name in FOCUSED_TESTS}

    compile_command, compile_cwd, _, _ = compile_runs[0]
    assert compile_cwd == REPO_ROOT
    assert compile_command[:3] == [sys.executable, "-m", "compileall"]
    assert "-q" in compile_command
    targets = {(compile_cwd / argument).resolve() for argument in compile_command[3:] if not argument.startswith("-")}
    assert targets == {REPO_ROOT / name for name in ("src", "tests", "scripts")}


@pytest.mark.parametrize(
    "failure_argument", ["-c", "compileall", "pytest"], ids=["installation", "compilation", "test-suite"]
)
def test_main_stops_after_a_failed_step(
    verifier: ModuleType, steps: list[Step], monkeypatch: pytest.MonkeyPatch, failure_argument: str
) -> None:
    record = verifier.run_step
    failed = False

    def fail_step(label, command, **kwargs):
        nonlocal failed
        assert not failed, "No later command may run after a failed check"
        record(label, command, **kwargs)
        failed = failure_argument in command
        return 23 if failed else 0

    monkeypatch.setattr(verifier, "run_step", fail_step)

    assert verifier.main(["--quick"]) == 23
    assert failed


@pytest.mark.parametrize("argv", [["--unknown-mode"], ["--quick", "--full"]])
def test_main_rejects_bad_arguments_before_any_checks(
    verifier: ModuleType, steps: list[Step], argv: list[str]
) -> None:
    try:
        status = verifier.main(argv)
    except SystemExit as error:
        status = error.code

    assert status == 2
    assert steps == []


def test_main_requires_a_virtual_environment_before_any_checks(
    verifier: ModuleType, steps: list[Step], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "base_prefix", sys.prefix)

    assert verifier.main(["--quick"]) == 1
    assert steps == []


@pytest.mark.parametrize("nested", [False, True], ids=["repo-root", "repo-child"])
def test_check_directory_stays_outside_repo_when_temp_is_inside(
    verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, nested: bool
) -> None:
    root = tmp_path / "checkout"
    root.mkdir()
    temporary = root / "temp" if nested else root
    temporary.mkdir(exist_ok=True)
    monkeypatch.setattr(verifier, "ROOT", root)
    monkeypatch.setenv("TMPDIR", str(temporary))
    monkeypatch.setattr(verifier.tempfile, "tempdir", None)

    with verifier.create_check_directory() as name:
        directory = Path(name).resolve()
        assert directory.is_dir()
        assert not directory.is_relative_to(root)
    assert not directory.exists()


def test_main_reports_unavailable_outside_temporary_directory(
    verifier: ModuleType, steps: list[Step], monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_directory(*args, **kwargs):
        raise PermissionError("synthetic temporary directory permission denied")

    monkeypatch.setattr(verifier.tempfile, "TemporaryDirectory", fail_directory)

    assert verifier.main(["--quick"]) == 1
    assert steps == []
    assert "temporary directory" in capsys.readouterr().err
