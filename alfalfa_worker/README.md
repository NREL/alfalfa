# Worker
Use some sort of virtual environment, then: `pip install -r requirements.txt` while in this dir (`alfalfa/worker/`).

# Styling
The worker repo uses pre-commit for managing styling via the `.pre-commit-config.yaml` file.  Installing requirements.txt will import the package (see [pre-commit](https://pre-commit.com/#intro)) for the user.  Then just run the following:

`pre-commit install`

After it is installed, the pre-commit workflow will be run before every `git commit`.  It can also be run manually using: `pre-commit run --all-files`.  The yaml file is setup to ignore: E501,E402,W503,E731 (for both autopep8 and flake8), but runs the following:
- autopep8
- autoflake8 to remove unused variables and imports
- flake8
