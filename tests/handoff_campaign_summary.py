"""Bounded reader for EXISTING JUnit evidence from the predeclared 30-trial
`handoff-first-run-campaign` capture campaign.

Reads already-downloaded artifact directories (one
`handoff-capture-<trial>-<run>-<attempt>-<sha>` folder per trial, each holding
`handoff-first.xml`) and renders one markdown summary plus a process exit
status. It launches no processes, performs no network access, retries nothing
and adds no new instrumentation; it never infers a root cause for the
intermittent PowerShell 5.1 first-invocation timeout it reports on.

Interpretation rules kept with this reader:
- A valid `handoff_process` property with `last_observed_stage` null means NO
  probe marker was captured (script entry was not observed); that is an
  observation about one run, not a diagnosis.
- Absent, malformed or schema-invalid evidence means 'unavailable'; it is
  reported as incomplete evidence and never counted as an observed negative.
- JUnit pass/fail and the recorded process outcome are independent dimensions;
  both are shown per trial.
- `root_cause_established` must be false in every trial of the whole campaign;
  any other value is invalid evidence.

Exit codes (the markdown file is always written first):
- 0  all 30 trials complete and valid, every target testcase passed and every
     process outcome == 'returned'; the binomial bound line is appended.
- 1  all 30 trials complete but at least one target testcase failed JUnit or a
     process outcome is timeout/launch_failed/interrupted.
- 2  any trial's evidence is incomplete or invalid; exit 2 beats exit 1.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

EXPECTED_TRIALS = 30
TRIAL_NUMBERS = range(1, EXPECTED_TRIALS + 1)
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_UNEXPECTED_LISTED = 10
XML_NAME = 'handoff-first.xml'
PROPERTY_NAME = 'handoff_process'
PROCESS_LIMIT_SECONDS = 30
TARGET_CLASSNAME = 'tests.test_handoff_download'
TARGET_NAME = 'test_real_powershell_download_publication[success-powershell.exe]'
VALID_OUTCOMES = ('returned', 'timeout', 'launch_failed', 'interrupted')
EXPECTED_PROPERTY_KEYS = frozenset((
    'outcome', 'process_limit_seconds', 'elapsed_seconds', 'stages',
    'last_observed_stage', 'trace_truncated', 'malformed_marker_seen',
    'retry_count', 'root_cause_established'))
ARTIFACT_NAME_RE = re.compile(
    r'^handoff-capture-(\d{1,10})-(\d{1,12})-(\d{1,6})-([0-9a-f]{6,40})$')
_UNPARSEABLE = object()


def parse_artifact_name(name):
    """Return parsed artifact identity, or None when the name is not one."""
    match = ARTIFACT_NAME_RE.match(name)
    if match is None:
        return None
    trial, run, attempt, sha = match.groups()
    return {'trial': int(trial), 'run': int(run), 'attempt': int(attempt), 'sha': sha}


def _blank_record(reason):
    return {'state': 'incomplete', 'reason': reason, 'junit': '-',
            'evidence': None, 'other_cases': 0}


def validate_property(evidence):
    """Return None for a schema-valid evidence dict, else the reason string."""
    if not isinstance(evidence, dict):
        return 'property schema invalid: JSON is not an object'
    missing = sorted(EXPECTED_PROPERTY_KEYS - set(evidence))
    if missing:
        return 'property schema invalid: missing key: ' + ', '.join(missing)
    extra = sorted(set(evidence) - EXPECTED_PROPERTY_KEYS)
    if extra:
        return 'property schema invalid: unexpected key: ' + ', '.join(extra)
    outcome = evidence['outcome']
    if not isinstance(outcome, str) or outcome not in VALID_OUTCOMES:
        return ('property schema invalid: outcome must be one of '
                + '/'.join(VALID_OUTCOMES))
    if type(evidence['process_limit_seconds']) is not int \
            or evidence['process_limit_seconds'] != PROCESS_LIMIT_SECONDS:
        return 'property schema invalid: process_limit_seconds must be 30'
    elapsed = evidence['elapsed_seconds']
    if type(elapsed) not in (int, float) or elapsed < 0:
        return 'property schema invalid: elapsed_seconds must be a number >= 0'
    if not isinstance(evidence['stages'], list):
        return 'property schema invalid: stages must be a list'
    last_stage = evidence['last_observed_stage']
    if last_stage is not None and not isinstance(last_stage, str):
        return 'property schema invalid: last_observed_stage must be a string or null'
    for key in ('trace_truncated', 'malformed_marker_seen'):
        if type(evidence[key]) is not bool:
            return 'property schema invalid: ' + key + ' must be a boolean'
    if type(evidence['retry_count']) is not int or evidence['retry_count'] != 0:
        return 'property schema invalid: retry_count must be 0'
    if evidence['root_cause_established'] is not False:
        return 'property schema invalid: root_cause_established must be false'
    return None


def read_trial(xml_path):
    """Read one trial's JUnit XML; never raises, incomplete evidence is a record."""
    if not xml_path.is_file():
        return _blank_record('missing ' + XML_NAME)
    if xml_path.stat().st_size > MAX_XML_BYTES:
        return _blank_record('oversized XML (over 2 MiB)')
    try:
        root = ET.parse(xml_path).getroot()
    except (ET.ParseError, OSError, ValueError):
        return _blank_record('XML parse error')
    cases = list(root.iter('testcase'))
    targets = [case for case in cases
               if case.get('classname') == TARGET_CLASSNAME
               and case.get('name') == TARGET_NAME]
    record = _blank_record('')
    record['other_cases'] = len(cases) - len(targets)
    if not targets:
        record['reason'] = 'no target testcase found'
        return record
    if len(targets) > 1:
        record['reason'] = 'multiple target testcases'
        return record
    target = targets[0]
    if target.find('skipped') is not None:
        record['reason'] = 'JUnit skipped target'
        return record
    if target.find('error') is not None:
        record['reason'] = 'JUnit errored target'
        return record
    properties = [prop for prop in target.iter('property')
                  if prop.get('name') == PROPERTY_NAME]
    if not properties:
        record['reason'] = 'no ' + PROPERTY_NAME + ' property'
        return record
    if len(properties) > 1:
        record['reason'] = 'multiple ' + PROPERTY_NAME + ' properties'
        return record
    raw = properties[0].get('value')
    try:
        evidence = json.loads(raw)
    except (TypeError, ValueError):
        evidence = _UNPARSEABLE
    if evidence is _UNPARSEABLE:
        record['reason'] = 'malformed property JSON'
        return record
    problem = validate_property(evidence)
    if problem is not None:
        record['reason'] = problem
        return record
    record['state'] = 'complete'
    record['reason'] = ''
    record['evidence'] = evidence
    record['junit'] = 'fail' if target.find('failure') is not None else 'pass'
    return record


def summarize_campaign(artifacts_dir):
    """Build the full campaign summary dict for an artifacts directory."""
    root = Path(artifacts_dir)
    unexpected = []
    per_trial_dirs = {}
    identities = set()
    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            parsed = parse_artifact_name(entry.name)
            if parsed is None:
                unexpected.append(entry.name + ' (name does not parse)')
            elif parsed['trial'] not in TRIAL_NUMBERS:
                unexpected.append(entry.name + ' (trial '
                                  + str(parsed['trial']) + ' outside 1..'
                                  + str(EXPECTED_TRIALS) + ')')
            else:
                per_trial_dirs.setdefault(parsed['trial'], []).append(entry.name)
                identities.add((parsed['run'], parsed['attempt'], parsed['sha']))
    rows = []
    for trial in TRIAL_NUMBERS:
        names = per_trial_dirs.get(trial, [])
        if not names:
            record = _blank_record('missing artifact directory')
        elif len(names) > 1:
            record = _blank_record('multiple artifact directories for trial')
        else:
            record = read_trial(root / names[0] / XML_NAME)
        record['trial'] = trial
        rows.append(record)
    totals = {'passed': 0, 'failed': 0, 'incomplete': 0}
    for row in rows:
        if row['state'] != 'complete':
            totals['incomplete'] += 1
        elif row['junit'] != 'pass' or row['evidence']['outcome'] != 'returned':
            totals['failed'] += 1
        else:
            totals['passed'] += 1
    if totals['incomplete']:
        exit_code = 2
    elif totals['failed']:
        exit_code = 1
    else:
        exit_code = 0
    artifact_dir_count = sum(len(names) for names in per_trial_dirs.values())
    if len(identities) == 1 and artifact_dir_count:
        run, attempt, sha = next(iter(identities))
        identity = 'run ' + str(run) + ' attempt ' + str(attempt) + ' sha ' + sha
    else:
        identity = 'mixed/unknown'
    return {'rows': rows, 'unexpected': unexpected, 'identity': identity,
            'artifact_dir_count': artifact_dir_count,
            'over_bound': artifact_dir_count > EXPECTED_TRIALS,
            'totals': totals, 'exit_code': exit_code}


def render_row(row):
    if row['state'] != 'complete':
        cells = ['incomplete: ' + row['reason']] + ['-'] * 7
    else:
        evidence = row['evidence']
        elapsed = '{:.3f}'.format(float(evidence['elapsed_seconds']))
        stage = evidence['last_observed_stage'] or 'none'
        cells = ['complete', row['junit'], evidence['outcome'], elapsed, stage,
                 'true' if evidence['trace_truncated'] else 'false',
                 'true' if evidence['malformed_marker_seen'] else 'false',
                 'true' if evidence['root_cause_established'] else 'false']
    return '| ' + ' | '.join([str(row['trial'])] + cells) + ' |'


def format_bound_line(result):
    """Exact binomial bound for zero observed non-returns in 30 trials."""
    non_returned = sum(1 for row in result['rows']
                       if row['state'] == 'complete'
                       and row['evidence']['outcome'] != 'returned')
    success = math.pow(0.05, 1.0 / EXPECTED_TRIALS)
    timeout = 1.0 - success
    return ('{} observed timeouts in {} trials; one-sided 95% lower bound on '
            'per-trial success probability \u2248 {:.3f} (upper bound on timeout '
            'probability \u2248 {:.3f}), assuming independent comparable trials; '
            'this is not evidence the defect is absent.'
            ).format(non_returned, EXPECTED_TRIALS, success, timeout)


def render_markdown(result):
    lines = ['# Handoff first-invocation capture campaign summary', '']
    lines.append('- run identity: ' + result['identity'])
    for name in result['unexpected'][:MAX_UNEXPECTED_LISTED]:
        lines.append('- unexpected artifact directory (not selected): ' + name)
    if len(result['unexpected']) > MAX_UNEXPECTED_LISTED:
        lines.append('- unexpected artifact directories (not selected): and '
                     + str(len(result['unexpected']) - MAX_UNEXPECTED_LISTED) + ' more')
    if result['over_bound']:
        lines.append('- artifact directories found: '
                     + str(result['artifact_dir_count']) + ' (bound: '
                     + str(EXPECTED_TRIALS)
                     + '; duplicated trials are incomplete evidence)')
    other_cases = [(row['trial'], row['other_cases'])
                   for row in result['rows'] if row['other_cases']]
    if other_cases:
        lines.append('- other testcases (never selected for the defect count): '
                     + ', '.join('trial {}: {}'.format(trial, count)
                                 for trial, count in other_cases))
    lines.append('')
    lines.append('| trial | evidence | junit | outcome | elapsed_s |'
                 ' last_observed_stage | truncated | malformed |'
                 ' root_cause_established |')
    lines.append('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for row in result['rows']:
        lines.append(render_row(row))
    lines.append('')
    totals = result['totals']
    lines.append('- totals: passed={} failed={} incomplete={}'.format(
        totals['passed'], totals['failed'], totals['incomplete']))
    if result['exit_code'] == 0:
        lines.append('')
        lines.append(format_bound_line(result))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Summarize existing JUnit handoff campaign evidence (read-only).')
    parser.add_argument('--artifacts', required=True,
                        help='directory with one handoff-capture-<trial>-<run>-'
                             '<attempt>-<sha> folder per trial')
    parser.add_argument('--markdown', required=True,
                        help='output markdown path (always written before exiting)')
    args = parser.parse_args(argv)
    result = summarize_campaign(Path(args.artifacts))
    out_path = Path(args.markdown)
    if str(out_path.parent) not in ('', '.'):
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(result), encoding='utf-8')
    return result['exit_code']


if __name__ == '__main__':
    sys.exit(main())
