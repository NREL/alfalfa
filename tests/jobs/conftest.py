import os
from pathlib import Path


def pytest_generate_tests(metafunc):
    model_dir = Path(os.path.dirname(__file__)) / '..' / 'integration' / 'models'
    if "model_path" in metafunc.fixturenames:
        model_paths = [
            model_dir / 'small_office',
            model_dir / 'wrapped.fmu',
            model_dir / 'minimal_osw_resstock'
        ]

        metafunc.parametrize("model_path", model_paths)
