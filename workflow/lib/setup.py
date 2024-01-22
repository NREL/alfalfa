import pandas as pd
import requests
import os
import shutil
import json
from workflow.lib.inputs import Inputs
from pathlib import Path

class Setup:

    """Class to create folder to upload to Alfalfa"""

    def create_osw(filename, weather):

        osw_content = {"seed_file": f"{filename}.osm",
                       "weather_file": f"{weather}",
                       "measure_paths": ["./measures"],
                        "run_directory": "./run/",
                        "file_paths": [
                            "./weather/",
                            "./models/"
                        ],
                            "steps" : [
                                {
                                    "measure_dir_name" : "alfalfa_vars",
                                    "name" : "Alfalfa Variables",
                                    "description" : "Add custom variables for Alfalfa",
                                    "modeler_description" : "Add EMS global variables required by Alfalfa",
                                    "arguments" : {
                                        "model" : f"{filename}.osm"
                                    }
                                }
                            ]
                        }

        return osw_content


    def create_folder(obj, alfalfa_folder):

        # folder where models are downloaded
        folder_path = obj.folder

        print(folder_path)

        # create folder to upload to alfalfa
        os.makedirs(alfalfa_folder, exist_ok=True)

        # copy downloaded models to alfalfa folder
        for file in folder_path.iterdir():
            if file.is_dir() and (file/ f'{file.name}.osm').exists:

                # Make folder for model
                model_filepath = Path(os.path.join(alfalfa_folder, file.name))
                print(model_filepath)
                model_filepath.mkdir(parents=True, exist_ok=True)
                (model_filepath / 'models').mkdir(parents=True, exist_ok=True)
                (model_filepath / 'measures').mkdir(parents=True, exist_ok=True)
                (model_filepath / 'weather').mkdir(parents=True, exist_ok=True)

                # Copy model
                shutil.copy((file / f'{file.name}.osm'), (model_filepath / 'models' / f'{file.name}.osm'))
                # TO DO Copy weather

                # Write OSW file
                osw_path = Path(os.path.join(model_filepath, 'workflow.osw'))

                #TO DO pass weather file
                with open(osw_path, 'w') as osw:
                    json.dump(Setup.create_osw(file.name, ''), osw, indent=2)









