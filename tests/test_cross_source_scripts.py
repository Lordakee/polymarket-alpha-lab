"""Demos and default probe must stay inert even with networking prohibited."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("script,args", (
    ("run_cross_source_research_demo.py", ["--team","crypto_btc"]),
    ("run_cross_source_research_demo.py", ["--team","crypto_eth"]),
    ("probe_crypto_cross_source.py", []),
))
def test_no_network_or_subprocess_in_script(script, args):
    bootstrap = '''import sys, runpy
sys.path.insert(0, "src")
def guard(event, args):
    if event.startswith(("socket.", "subprocess.")):
        raise AssertionError("unexpected I/O")
sys.addaudithook(guard)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
'''
    env = {k:v for k,v in os.environ.items() if not k.startswith("POLYMARKET_ALPHA_LAB_")}
    result = subprocess.run([sys.executable,"-c",bootstrap,"scripts/"+script,*args],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["live_model_called"] is False
    if script.startswith("run_"):
        assert payload["synthetic_demo"] is True and payload["public_network_called"] is False
        assert payload["cross_source_status"] == "matched" and payload["research_status"] == "completed"
        assert payload["cited_source_count"] == 2
    else:
        assert payload["public_fetch_enabled"] is False
