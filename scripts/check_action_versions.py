"""Fail if the copyable CI template drifts from the live workflow's action refs."""
import re
import sys
from pathlib import Path

PATTERN = re.compile(r'^\s*-\s+uses:\s+([\w.-]+/[\w./-]+)@([^\s#]+)', re.MULTILINE)


def refs(path):
    result = {}
    for action, ref in PATTERN.findall(Path(path).read_text()):
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
    if not template:
        raise SystemExit('template has no action refs')
    if differences:
        raise SystemExit('Copyable workflow needs an action update:\n' + '\n'.join(differences))
    print('Copyable workflow action refs match the live workflow.')


if __name__ == '__main__':
    main()
