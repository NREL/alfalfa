
import os
from pathlib import Path


def pytest_generate_tests(metafunc):
    model_dir = Path(os.path.dirname(__file__)) / '..' / '..' / 'integration' / 'models'
    if "model_path" in metafunc.fixturenames:
        model_paths = [
            model_dir / 'refrig_case_osw',
            model_dir / 'small_office'
        ]

        metafunc.parametrize("model_path", model_paths)
