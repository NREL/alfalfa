
import os
from pathlib import Path


def pytest_generate_tests(metafunc):
    model_dir = Path(os.path.dirname(__file__)).parent.parent / 'integration' / 'models'
    if "model_path" in metafunc.fixturenames:
        model_paths = [
            model_dir / 'simple_thermostat.fmu',
            model_dir / 'single_zone_vav.fmu'
        ]

        metafunc.parametrize("model_path", model_paths)
