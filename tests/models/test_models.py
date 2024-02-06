from workflow.lib.inputs import Inputs
from workflow.lib.models import Models
from workflow.lib.setup import Setup
from pathlib import Path
import pytest
import os
import shutil


def test_model_downloads_comstock():

    current_directory = Path(__file__).resolve().parent

    # folder to download models
    folder_name = Path(os.path.join(current_directory, 'comsstock'))
    # folder to configure and upload to alfalfa
    alfalfa_folder = Path(os.path.join(current_directory, 'alfalfa_folder'))

    id = ['bldg0000001','bldg0000002']

    objA = Inputs
    objA.__init__(Inputs, '2023','comstock_amy2018_release_2','18', id,  folder_name)

    # remove if folder exists
    shutil.rmtree(folder_name, ignore_errors=True)

    objB = Models
    objB.download_models(objA)


    save_folder_1 = os.path.join(folder_name, id[0])
    save_folder_2 = os.path.join(folder_name, id[1])

    # check if models are downloaded
    assert os.path.exists(folder_name)
    assert os.path.exists(save_folder_1)
    assert os.path.exists(save_folder_2)

    shutil.rmtree(alfalfa_folder, ignore_errors=True)

    # Test Model Setup
    objC = Setup
    objC.create_folder(objA, alfalfa_folder)

    assert os.path.exists(os.path.join(alfalfa_folder, 'files'))
    assert os.path.exists(os.path.join(alfalfa_folder, 'alfalfa_upload', id[0], 'models', f'{id[0]}.osm'))


def test_model_downloads_resstock():

    current_directory = Path(__file__).resolve().parent

    folder_name = Path(os.path.join(current_directory, 'resstock'))
    alfalfa_folder = Path(os.path.join(current_directory, 'alfalfa_folder_res'))
    id = ['bldg0000003','bldg0000004']

    objA = Inputs
    objA.__init__(Inputs, '2021','resstock_tmy3_release_1','00', id, folder_name)

    shutil.rmtree(folder_name, ignore_errors=True)

    objB = Models
    objB.download_models(objA)

    save_folder_1 = os.path.join(folder_name, id[0])
    save_folder_2 = os.path.join(folder_name, id[1])

    assert os.path.exists(folder_name)
    assert os.path.exists(save_folder_1)
    assert os.path.exists(save_folder_2)

    shutil.rmtree(alfalfa_folder, ignore_errors=True)

    # Test Model Setup
    objC = Setup
    objC.create_folder(objA, alfalfa_folder)

    assert os.path.exists(os.path.join(alfalfa_folder, 'files'))
    assert os.path.exists(os.path.join(alfalfa_folder, 'alfalfa_upload',id[0], 'models', f'{id[0]}.osm'))

