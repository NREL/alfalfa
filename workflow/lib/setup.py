import pandas as pd
import requests
import os
import shutil
import json
from workflow.lib.inputs import Inputs
from pathlib import Path

class Setup:

    """Class to create folder to upload to Alfalfa"""

    # def create_osw(filename, weather):

    #     osw_content = {
    #                     "seed_file": f"{filename}.osm",
    #                     "weather_file": f"{weather}",
    #                     "measure_paths": ["./measures"],
    #                     "run_directory": "./run/",
    #                     "file_paths": [
    #                         "./weather/",
    #                         "./models/"
    #                     ],
    #                     "steps" : [
    #                         {
    #                             "measure_dir_name": "alfalfa_vars",
    #                             "name": "Alfalfa Variables",
    #                             "description": "Add custom variables for Alfalfa",
    #                             "modeler_description": "Add EMS global variables required by Alfalfa",
    #                             "arguments": {
    #                                 "model": f"{filename}.osm"
    #                             }
    #                         }
    #                     ]
    #                 }

    #     return osw_content


    def create_folder(obj, alfalfa_folder):

        # folder where models are downloaded
        folder_path = obj.folder

        # create folder to upload to alfalfa
        alfalfa_upload = Path(os.path.join(alfalfa_folder, 'alfalfa_upload'))
        alfalfa_upload.mkdir(parents=True, exist_ok=True)

        # create a files folder. This is done so users can add more measures and modify osw file
        files = Path(os.path.join(alfalfa_folder, 'files'))
        # Remove the destination folder if it exists
        if os.path.exists(files):
            shutil.rmtree(files)
        #files.mkdir(parents=True, exist_ok=True)

        current_directory = Path(__file__).resolve().parent



        base_files = os.path.join(current_directory.parent,'base_files')
        # copy base files to folder
        shutil.copytree(base_files, files)

        # copy downloaded models to alfalfa folder
        for file in Path(folder_path).iterdir():
            if file.is_dir() and (file/ f'{file.name}.osm').exists:

                # Make folder for model
                model_filepath = Path(os.path.join(alfalfa_upload, file.name))
                model_filepath.mkdir(parents=True, exist_ok=True)
                (model_filepath / 'models').mkdir(parents=True, exist_ok=True)

                # Copy default measures
                #(model_filepath / 'measures').mkdir(parents=True, exist_ok=True)
                shutil.copytree(os.path.join(files, 'measures'), os.path.join(model_filepath/ 'measures'))

                # copy osw file
                osw_path = Path(os.path.join(model_filepath, 'workflow.osw'))
                shutil.copy(os.path.join(files, 'workflow.osw'), osw_path)

                (model_filepath / 'weather').mkdir(parents=True, exist_ok=True)

                # Copy model

                shutil.copy((file / f'{file.name}.osm'), (model_filepath / 'models' / f'{file.name}.osm'))

                # TO DO Copy weather
                with open(osw_path, 'r') as osw:
                    data = json.load(osw)
                    data['seed_file'] =  f"{file.name}.osm"
                    # TO DO add weather
                    # osw['weather_file'] = ""

                    # TO DO add better way to do this
                    data['steps'][0]['arguments']['model'] = f"{file.name}.osm"

                with open(osw_path, 'w') as osw:
                    json.dump(data, osw, indent=2)



