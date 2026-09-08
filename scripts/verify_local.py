"""Verify an editable local installation without enabling database integration."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FOCUSED_TESTS = (
    "tests/test_cli_report_discovery.py",
    "tests/test_phase1_report_discovery_smoke.py",
    "tests/test_phase1_report_modules_import_no_io.py",
    "tests/test_supabase_local_dsn.py",
    "tests/test_verify_local.py",
)
INSTALL_CHECK = """
import importlib.metadata
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
from urllib.request import url2pathname

root = Path(sys.argv[1]).resolve()
distribution = importlib.metadata.distribution('polymarket-alpha-lab')
direct_url = json.loads(distribution.read_text('direct_url.json') or '{}')
source = urlparse(direct_url.get('url', ''))
if direct_url.get('dir_info', {}).get('editable') is not True:
    raise RuntimeError('Install the project in editable mode with uv sync --locked --extra dev.')
if source.scheme != 'file' or source.netloc not in ('', 'localhost'):
    raise RuntimeError('Editable installation must reference this local repository.')
if Path(url2pathname(source.path)).resolve() != root:
    raise RuntimeError('Editable installation references a different repository.')
import polymarket_alpha_lab
if Path(polymarket_alpha_lab.__file__).resolve().parent != root / 'src' / 'polymarket_alpha_lab':
    raise RuntimeError('Imported package does not come from this repository.')
if not any(entry.group == 'console_scripts' and entry.name == 'polymarket-alpha-lab'
           and entry.value == 'polymarket_alpha_lab.cli:main'
           for entry in distribution.entry_points):
    raise RuntimeError('The installed console entry point is missing or incorrect.')
print('Editable installation verified:', distribution.version)
"""


def build_environment() -> dict[str, str]:
    excluded = {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH", "PYTHONHOME"}
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("POLYMARKET_ALPHA_LAB_")
        and key.upper() not in excluded
    }
    environment["POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE"] = "0"
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONUNBUFFERED"] = "1"
    return environment


def run_step(
    label: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    expected_output: str | None = None,
) -> int:
    print(f"\n[{label}]", flush=True)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=expected_output is not None,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        print(f"FAILED: {label}: {error}", file=sys.stderr, flush=True)
        return 1
    if result.returncode != 0:
        if expected_output is not None:
            if result.stdout:
                print(result.stdout, end="", flush=True)
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr, flush=True)
        print(
            f"FAILED: {label} (exit {result.returncode})",
            file=sys.stderr,
            flush=True,
        )
        return result.returncode if result.returncode > 0 else 1
    if expected_output is not None and expected_output not in (result.stdout or ""):
        print(f"FAILED: {label}: expected output missing", file=sys.stderr, flush=True)
        return 1
    print(f"PASS: {label}", flush=True)
    return 0


def create_check_directory() -> tempfile.TemporaryDirectory[str]:
    parents = (Path(tempfile.gettempdir()).resolve(), ROOT.parent)
    for parent in dict.fromkeys(parents):
        if parent.is_relative_to(ROOT):
            continue
        try:
            directory = tempfile.TemporaryDirectory(prefix="polymarket-local-check-", dir=parent)
        except OSError:
            continue
        if Path(directory.name).resolve().is_relative_to(ROOT):
            directory.cleanup()
            continue
        return directory
    raise OSError("No writable temporary directory outside the repository; check TMPDIR/TEMP.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--quick", action="store_true", help="run focused checks (default)")
    modes.add_argument("--full", action="store_true", help="run the full offline test suite")
    args = parser.parse_args(argv)
    if sys.prefix == sys.base_prefix:
        print("Use this repository's .venv Python to run verification.", file=sys.stderr)
        return 1

    environment = build_environment()
    python = sys.executable
    console = Path(sysconfig.get_path("scripts")) / (
        "polymarket-alpha-lab.exe" if os.name == "nt" else "polymarket-alpha-lab"
    )
    if not console.is_file():
        print(
            "Installed console script is missing; run uv sync --locked --extra dev.",
            file=sys.stderr,
        )
        return 1

    mode = "full" if args.full else "quick"
    print(f"Local verification: {mode}\nRepository: {ROOT}", flush=True)
    print("Real Supabase smoke is disabled; database integration is not verified.", flush=True)
    try:
        check_directory = create_check_directory()
    except OSError as error:
        print(f"FAILED: temporary directory: {error}", file=sys.stderr, flush=True)
        return 1
    with check_directory as directory:
        outside = Path(directory)
        module = [python, "-I", "-m", "polymarket_alpha_lab"]
        help_marker = "usage: polymarket-alpha-lab"
        discovery_marker = "Report discovery: read-only paper/report-only operator entrypoints"
        checks = (
            (
                "editable installation",
                [python, "-I", "-c", INSTALL_CHECK, str(ROOT)],
                "Editable installation verified:",
            ),
            ("module help", [*module, "--help"], help_marker),
            ("module report discovery", [*module, "report-discovery"], discovery_marker),
            ("console help", [str(console), "--help"], help_marker),
            ("console report discovery", [str(console), "report-discovery"], discovery_marker),
        )
        for label, command, marker in checks:
            result = run_step(label, command, cwd=outside, env=environment, expected_output=marker)
            if result:
                return result

    result = run_step(
        "compile source, tests and scripts",
        [python, "-m", "compileall", "-q", "src", "tests", "scripts"],
        cwd=ROOT,
        env=environment,
    )
    if result:
        return result
    tests = [] if args.full else list(FOCUSED_TESTS)
    result = run_step(
        f"{mode} pytest",
        [python, "-m", "pytest", "-q", "-ra", *tests],
        cwd=ROOT,
        env=environment,
    )
    if result:
        return result
    print(f"\nPASS: {mode} local verification", flush=True)
    if not args.full:
        print("Quick checks are not a full test baseline. Use --full for the complete suite.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
