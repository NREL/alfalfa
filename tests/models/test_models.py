from workflow.lib.inputs import Inputs
from workflow.lib.models import Models
from pathlib import Path
import pytest
import os
import shutil


def test_model_downloads_comstock():

    current_directory = Path(__file__).resolve().parent

    # folder to download models
    folder_name = Path(os.path.join(current_directory, 'comsstock'))
    # folder to configure and upload to alfalfa

    id = ['bldg0000001','bldg0000002']

    objA = Inputs
    objA.__init__(Inputs, '2021','comstock_tmy3_release_1','00', id,  folder_name)

    # remove if folder exists
    shutil.rmtree(folder_name, ignore_errors=True)

    objB = Models
    objB.download_models(objA)

    save_folder_1 = os.path.join(folder_name, id[0], 'models', id[0] + '.osm')
    workflow_1 = os.path.join(folder_name, id[0], 'workflow.osw')
    save_folder_2 = os.path.join(folder_name, id[1], 'models', id[1] + '.osm')
    workflow_2 = os.path.join(folder_name, id[1], 'workflow.osw')

    # check if models are downloaded
    assert os.path.exists(save_folder_1)
    assert os.path.exists(save_folder_2)
    assert os.path.exists(workflow_1)
    assert os.path.exists(workflow_2)

def test_model_downloads_resstock():

    current_directory = Path(__file__).resolve().parent

    folder_name = Path(os.path.join(current_directory, 'resstock'))
    id = ['bldg0000003','bldg0000004']

    objA = Inputs
    objA.__init__(Inputs, '2021','resstock_tmy3_release_1','00', id, folder_name)

    shutil.rmtree(folder_name, ignore_errors=True)

    objB = Models
    objB.download_models(objA)


    save_folder_1 = os.path.join(folder_name, id[0], 'models', id[0] + '.osm')
    workflow_1 = os.path.join(folder_name, id[0], 'workflow.osw')
    save_folder_2 = os.path.join(folder_name, id[1], 'models', id[1] + '.osm')
    workflow_2 = os.path.join(folder_name, id[1], 'workflow.osw')

    assert os.path.exists(save_folder_1)
    assert os.path.exists(workflow_1)
    assert os.path.exists(save_folder_2)
    assert os.path.exists(workflow_2)
