# Consider factoring this out of the test file
import os
import tempfile
import zipfile
from pathlib import Path


def pytest_generate_tests(metafunc):
    model_dir = Path(os.path.dirname(__file__)) / 'broken_models'
    if "broken_model_path" in metafunc.fixturenames:
        model_paths = [
            model_dir / 'small_office_missing_python_requirements.zip'
        ]

        metafunc.parametrize("broken_model_path", model_paths)


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def create_zip(model_dir):
    osw_dir_path = os.path.join(os.path.dirname(__file__), 'models', model_dir)
    zip_file_fd, zip_file_path = tempfile.mkstemp(suffix='.zip')

    zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(osw_dir_path, zipf)
    zipf.close()
    return zip_file_path
