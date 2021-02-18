# Worker

The worker's dependencies are installed the overall Alfalfa project; therefore, to install
the dependencies run `poetry install` in the root directory (`alfalfa`).

# Styling

The worker uses pre-commit for managing styling via the `.pre-commit-config.yaml` file in the root directory.
Installing the dependencies will import the package (see [pre-commit](https://pre-commit.com/#intro)) for the user.
Run the following command to setup pre-commit with your git environment:

```bash
pre-commit install
```

After it is installed, the pre-commit workflow will be run before every `git commit`.  It can also be run manually using: `pre-commit run --all-files`.  The yaml file is setup to ignore: E501,E402,W503,E731 (for both autopep8 and flake8), but runs the following:

* autopep8
* autoflake8 to remove unused variables and imports
* flake8
