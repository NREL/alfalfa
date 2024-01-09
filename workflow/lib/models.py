import boto3  # This is not called directly, but must be installed for Pandas to read files from S3
import pandas as pd
import requests
import gzip
import os
from workflow.lib.inputs import Inputs
from urllib.parse import urljoin, urlsplit, urlunsplit
from pathlib import Path
from io import BytesIO


class Models:

    """Class to download models from defined inputs"""

    def download_models(id, obj, folder_path):

        os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist

        for i in id:
            # TO DO: check if this url is different for other years/resstock
            osm_url = f'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/{obj.year}/{obj.dataset_name}/building_energy_models/upgrade={obj.upgrade}/{i}-up{obj.upgrade}.osm.gz'
            response = requests.get(osm_url, stream=True)

            save_folder = os.path.join(folder_path, i)
            os.makedirs(save_folder, exist_ok=True)  # Create folder using filename if it doesn't exist
            osm_path = os.path.join(save_folder, i + '.osm')

            if response.status_code == 200:
                with gzip.GzipFile(fileobj=BytesIO(response.content), mode='rb') as gz:
                    extracted_content = gz.read()
                    with open(osm_path, 'wb') as extracted_file:
                        extracted_file.write(extracted_content)

                print(f"File downloaded and extracted to {osm_path}")
            else:
                print(f"Failed to download the file: {response.status_code}")

