"""M0 baseline measurement: CLI interface latency and command inventory.

Stdlib only; no network, no database. Prints one JSON object:

    {
      "python": "...",
      "interpreter_startup_seconds": ...,
      "cli_import_seconds": ...,
      "cli_help_seconds": ...,
      "commands": ["...", ...]
    }

Representative end-to-end cycle duration is not measured here; it is
measured when the M3 vertical slice exists (see the delivery plan).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time


def _run(argv: list[str]) -> str:
    completed = subprocess.run(
        argv,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _time_process(argv: list[str]) -> float:
    start = time.perf_counter()
    subprocess.run(argv, check=True, capture_output=True)
    return time.perf_counter() - start


def _command_names(help_text: str) -> list[str]:
    match = re.search(r"\{([a-z0-9_-]+(?:,[a-z0-9_-]+)+)\}", help_text)
    if match is None:
        raise SystemExit("could not locate the argparse command list in --help output")
    return sorted(match.group(1).split(","))


def main() -> None:
    interpreter_startup = _time_process([sys.executable, "-c", "pass"])
    import_probe = (
        "import time; start = time.perf_counter(); "
        "import polymarket_alpha_lab.cli; "
        "print(time.perf_counter() - start)"
    )
    cli_import = float(
        _run([sys.executable, "-c", import_probe]).strip()
    )
    start = time.perf_counter()
    help_text = _run([sys.executable, "-m", "polymarket_alpha_lab", "--help"])
    cli_help = time.perf_counter() - start
    print(
        json.dumps(
            {
                "python": sys.version.split()[0],
                "interpreter_startup_seconds": round(interpreter_startup, 4),
                "cli_import_seconds": round(cli_import, 4),
                "cli_help_seconds": round(cli_help, 4),
                "commands": _command_names(help_text),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
