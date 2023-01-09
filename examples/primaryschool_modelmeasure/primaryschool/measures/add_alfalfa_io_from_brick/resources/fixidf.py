import sys, re

path = sys.argv[1]

with open(path, 'r') as inp:
    idf = inp.readlines()

with open(path.replace('.idf', '_og.idf'), 'w') as out:
    out.writelines(idf)

with open(path, 'w') as out:
    lines = []
    replacements = {}
    for line in idf:
        if line[0] != '!':
            field = re.split('[,;]+', line)[0].replace('  ', '')
            if len(field) >= 100:
                print(f"F: {line} - {len(field)}")
                # Find floats
                nfield = field
                floats = re.findall(r"[-+]?(?:\d*\.\d+)", field)
                print(floats)
                for fl in floats:
                    print(f"Replacing {fl} with {str(round(float(fl), 2))}")
                    nfield = nfield.replace(fl, str(round(float(fl), 2)))
                print(f"R: {line.replace(field, nfield)}")

                if len(nfield) >= 100:
                    nfield = nfield.replace(' ', '')
                    if 'SET' in nfield:
                        nfield = nfield.replace('SET', 'SET ')

                # Is it still too long? Let's do something nasty.
                if len(nfield) >= 100:
                    nfield = nfield[:99]
                    print(f"R: {line.replace(field, nfield)}")
                if len(nfield) >= 100:
                    raise ConnectionRefusedError(f"Bad Gateway: {nfield}")
                for line in idf:
                    line = line.replace(field, nfield)
                replacements[line] = nfield
                lines.append(line.replace(field, nfield))
            else:
                lines.append(line)
        else:
            lines.append(line)
    for replacement in replacements.keys():
        for line in lines:
            if replacement in line:
                line = line.replace(replacement, replacements[replacement])
    out.writelines(lines)
