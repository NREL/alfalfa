
import os
from pathlib import Path


def pytest_generate_tests(metafunc):
    model_dir = Path(os.path.dirname(__file__)) / 'broken_models'
    if "broken_model_path" in metafunc.fixturenames:
        model_paths = [
            model_dir / 'small_office_missing_python_requirements.zip'
        ]

        metafunc.parametrize("broken_model_path", model_paths)
