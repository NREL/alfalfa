import toml

# assumes this script is run from root of repo
f = './pyproject.toml'
t = toml.load(f)
print(t['tool']['poetry']['version'])
