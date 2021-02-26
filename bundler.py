import os
import re

entrypoint = 'calibration_tower/__entrypoint__.py'


tree = {}

imports = []
total = []


def find_pkg(file, _pkg):
    subpaths = file
    for i in range(len(_pkg)):
        if _pkg[i] == '.':
            subpaths = os.path.split(subpaths)[0]
        else:
            rhs = _pkg[i:]
            rhs = os.path.join(*rhs.split('.'))
            rhs += '.py'
            return os.path.join(subpaths, rhs)


def strip_depth(line, _from, depth):
    m = re.match(r'(\.*)(.*)', _from)
    if not m:
        return line

    new = '.' * max(0, len(m.group(1)) - depth) + m.group(2)
    return line.replace(_from, new)


def bundle(file, tree, total, imports, depth=0):
    if file in tree:
        return

    tree[file] = True

    with open(file) as f:
        contents = f.read()
        i = 0
        while i < len(contents):
            m = re.match(r'^import +(.*)$', contents[i:], re.M)
            if m:
                imports.insert(0, m.group(0))
                i += len(m.group(0))
                continue

            m = re.match(
                r'^from (.*) +import +(\([\W\w\n]+?\)|[\w ,]+)$', contents[i:], re.M)
            if m:
                _from = m.group(1)
                if _from.startswith('.'):
                    possible_pkg = find_pkg(file, _from)
                    if os.path.exists(possible_pkg):
                        bundle(possible_pkg, tree, total, imports, depth+1)
                    else:
                        imports.append(strip_depth(m.group(0), _from, depth))
                else:
                    imports.insert(0, m.group(0))

                i += len(m.group(0))
                continue

            next_newline = contents.find('\n', i)
            if next_newline >= 0:
                total.append(contents[i: next_newline])
                i = next_newline + 1
                continue

            i += 1


bundle(entrypoint, tree, total, imports)

result = []
added_imports = set()
for i in imports:
    if i not in added_imports:
        added_imports.add(i)
        result.append(i)

for l in total:
    result.append(l)

with open('CalibrationTower.py', 'w') as f:
    f.write('\n'.join(result))
