from workflow.lib.inputs import Inputs
from workflow.lib.models import Models
import pytest
import os
import shutil

def test_model_downloads():

    objA = Inputs
    objA.__init__(Inputs, '2023','comstock_amy2018_release_2','18')

    id = ['bldg0000001','bldg0000002']
    folder_name = 'saved'
    shutil.rmtree(folder_name, ignore_errors=True)

    objB = Models
    objB.download_models(id, objA, folder_name)


    save_folder_1 = os.path.join(folder_name, id[0])
    save_folder_2 = os.path.join(folder_name, id[1])

    assert os.path.exists(folder_name)
    assert os.path.exists(save_folder_1)
    assert os.path.exists(save_folder_2)

