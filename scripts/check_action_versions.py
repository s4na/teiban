"""Check shared action refs in copyable workflows against the live CI and lock."""
import json
import re
import subprocess
import sys
from pathlib import Path


def refs(path):
    # Read YAML structurally so quoting, anchors and reusable workflows work too.
    workflow = json.loads(subprocess.check_output([
        'ruby', '-ryaml', '-rjson', '-e',
        'puts JSON.generate(YAML.safe_load(File.read(ARGV.fetch(0)), aliases: true))',
        str(path)], text=True))
    result = {}
    for job in workflow.get('jobs', {}).values():
        for entry in [job, *job.get('steps', [])]:
            use = entry.get('uses', '')
            if use.startswith(('./', 'docker://')) or '@' not in use:
                continue
            action, ref = use.rsplit('@', 1)
            if action in result and result[action] != ref:
                raise ValueError(f'{path}: {action} has multiple refs')
            result[action] = ref
    return result


def main():
    if len(sys.argv) < 3:
        raise SystemExit('usage: check_action_versions.py LIVE TEMPLATE [TEMPLATE ...]')
    live_path = Path(sys.argv[1])
    live = refs(live_path)
    # Ruby's standard YAML parser avoids guessing the generated lockfile's layout.
    lock = json.loads(subprocess.check_output([
        'ruby', '-ryaml', '-rjson', '-e',
        'puts JSON.generate(YAML.safe_load(File.read(ARGV.fetch(0))))',
        str(live_path.parent / 'actions.lock')], text=True))
    allowed = {}
    pinned_refs = {}
    for action, ref in live.items():
        allowed[action] = {ref}
        pin = lock['dependencies'].get(f'{action}@{ref}')
        if pin:
            pinned_refs[action] = pin['commit'].removeprefix('sha1-')
            allowed[action].add(pinned_refs[action])
        elif re.fullmatch('[0-9a-f]{40}', ref):
            pinned_refs[action] = ref
    differences = []
    primary = refs(sys.argv[2])
    differences.extend(f'{sys.argv[2]}: {action}: missing from the copyable template'
                       for action in live.keys() - primary.keys())
    differences.extend(f'{sys.argv[2]}: {action}: missing from the live workflow'
                       for action in primary.keys() - live.keys())
    for index, template_path in enumerate(sys.argv[2:]):
        template = refs(template_path)
        if not template:
            raise SystemExit(f'{template_path}: no action refs')
        for action, ref in template.items():
            expected = allowed.get(action, set()) if index == 0 else {pinned_refs.get(action)}
            if action in allowed and ref not in expected:
                differences.append(f'{template_path}: {action}: template={ref}, live={live[action]}')
            elif action not in allowed and not re.fullmatch('[0-9a-f]{40}', ref):
                differences.append(f'{template_path}: {action}: unique template action must use a full SHA')
    if differences:
        raise SystemExit('Copyable workflow needs an action update:\n' + '\n'.join(differences))
    print('Shared copyable workflow action refs match the live workflow and lock.')


if __name__ == '__main__':
    main()
