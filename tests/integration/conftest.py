# Consider factoring this out of the test file
import os
import shutil
import tempfile
from pathlib import Path


def pytest_generate_tests(metafunc):
    model_dir = Path(os.path.dirname(__file__)) / 'broken_models'
    if "broken_model_path" in metafunc.fixturenames:
        model_paths = [
            model_dir / 'small_office_missing_python_requirements.zip'
        ]

        metafunc.parametrize("broken_model_path", model_paths)


def create_zip(model_dir):
    zip_file_fd, zip_file_path = tempfile.mkstemp(suffix='.zip')
    zip_file_path = Path(zip_file_path)
    shutil.make_archive(zip_file_path.parent / zip_file_path.stem, "zip", model_dir)

    return zip_file_path


def prepare_model(model_path):
    model_path = Path(__file__).parents[0] / 'models' / model_path
    if (model_path).is_dir():
        return create_zip(str(model_path))
    else:
        return str(model_path)
