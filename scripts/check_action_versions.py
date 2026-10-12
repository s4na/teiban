"""Fail if the copyable CI template drifts from the live workflow's action refs."""
import json
import subprocess
import sys


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
    if len(sys.argv) != 3:
        raise SystemExit('usage: check_action_versions.py LIVE TEMPLATE')
    live, template = map(refs, sys.argv[1:])
    differences = [f'{action}: template={ref}, live={live.get(action, "missing")}'
                   for action, ref in template.items() if live.get(action) != ref]
    differences.extend(f'{action}: missing from the copyable template'
                       for action in live.keys() - template.keys())
    if not template:
        raise SystemExit('template has no action refs')
    if differences:
        raise SystemExit('Copyable workflow needs an action update:\n' + '\n'.join(differences))
    print('Copyable workflow action refs match the live workflow.')


if __name__ == '__main__':
    main()
