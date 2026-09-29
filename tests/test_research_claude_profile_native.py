"""Explicit supplied official image only; NEVER download, authenticate or adopt state.

The operator must first verify publisher provenance and prepare a disposable
secret-free host with external egress denied and loopback allowed. The opt-in is
an operator assertion of that prerequisite, not sandbox enforcement by this test.
All six cases must execute. Missing/mismatched enabled configuration fails, not
skips. No real key/model/database/market request is used. See the fixed handoff.
"""
import json
import os

import pytest

from tests import claude_cli_probe as probe


@pytest.fixture(scope='module')
def supplied_image():
    selected = probe.configured_image(os.environ)
    if selected is None:
        pytest.skip('explicit reviewed Claude image and disposable isolated-host opt-in required')
    return selected


@pytest.mark.parametrize('mode', probe.MODES)
def test_supplied_claude_profile_loopback_and_surviving_state(
        supplied_image, tmp_path_factory, mode, record_property):
    # Six distinct exclusively allocated scenario directories (mkdir 0o700,
    # a collision raises): pytest's numbered machinery — including its
    # `test_<name>current` convenience symlink, which the outer runner's
    # no-follow export correctly reports as unsafe — is opted out with
    # numbered=False; the explicit scenario index supplies unique names.
    case_dir = tmp_path_factory.mktemp(
        f'claude-probe-{probe.MODES.index(mode)}', numbered=False)
    observation = probe.run_probe(*supplied_image, root=case_dir/'claude-probe', mode=mode, allow_probe=True)
    # Metadata has no raw stdout/stderr, headers, paths, prompt or state-file body.
    # Keep failed observations as failed; do not whitelist newly observed writes.
    text = json.dumps(observation, sort_keys=True, separators=(',', ':'))
    record_property('claude_cli_probe', text)
    print('CLAUDE_CLI_PROBE '+text, flush=True)
    assert probe.observation_passed(observation), text
    assert observation['activation_authorized'] is False
    # v2 diagnostic additions (arbitration prescriptions 2-5): observation-only
    # transcript/predecode/inventory captured above regardless of the verdict,
    # with bounded sidecars beside (never inside) the snapshotted root. Their
    # capture status can never influence the qualification above.
    diagnostics = observation['diagnostics']
    assert diagnostics['schema_version'] == probe.DIAGNOSTIC_SCHEMA
    assert diagnostics['sidecars']['status'] in ('written', 'incomplete-and-recorded')
    assert diagnostics['state_inventory']['qualification_baseline'] \
        == 'original initial snapshot (unchanged)'
