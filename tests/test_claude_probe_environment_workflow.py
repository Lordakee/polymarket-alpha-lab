"""Required build/relocation wiring, not a new runtime acceptance layer."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_build_and_both_relocations_have_independent_required_time_budgets():
    source=(ROOT/'.github/workflows/claude-probe-environment.yml').read_text()
    build=source.split('  build-environment:',1)[1].split('  relocate-environment:',1)[0]
    relocate=source.split('  relocate-environment:',1)[1].split('  windows-environment:',1)[0]
    aggregate=source.split('  windows-environment:',1)[1]
    assert 'timeout-minutes: 15' in build and 'timeout-minutes: 15' in relocate
    assert 'copy: [1, 2]' in relocate and 'fail-fast: false' in relocate
    assert 'needs: [build-environment]' in relocate
    assert 'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093' in relocate
    assert "name: probe-environment-package-${{ github.sha }}" in build
    assert "name: probe-environment-package-${{ github.sha }}" in relocate
    assert 'archive hash mismatch' in relocate and 'selftest --root' in relocate
    assert 'official_cases_run' in relocate and 'source_commit' in relocate
    assert 'needs: [build-environment, relocate-environment]' in aggregate
    assert 'if: ${{ always() }}' in aggregate
    assert 'test "$BUILD_RESULT" = success' in aggregate
    assert 'test "$RELOCATED_RESULT" = success' in aggregate
    assert build.count('git diff --exit-code') == relocate.count('git diff --exit-code') == 1
