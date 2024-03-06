import boto3  # This is not called directly, but must be installed for Pandas to read files from S3
import pandas as pd
import requests
import shutil
import gzip
import os
import re
import pyarrow
import json
from workflow.lib.inputs import Inputs
from urllib.parse import urljoin, urlsplit, urlunsplit, urlparse
from pathlib import Path
from io import BytesIO

class Models:

    """Class to download models from defined inputs"""

    def download_models(obj):

        folder_path = obj.folder
        id = obj.id

        os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist

        current_directory = Path(__file__).resolve().parent
        base_files = os.path.join(current_directory.parent,'base_files')

        # load mapping
        mapping = os.path.join(base_files, 'end_use_profiles_mapping.xlsx')
        mapping_df = pd.read_excel(mapping)

        metadata_url = mapping_df.loc[(mapping_df['year'] == int(obj.year)) & (mapping_df['database_name'] == str(obj.dataset_name)), 'metadata_url'].values[0] if not mapping_df.empty else None
        # URL to parquet
        parquet_path = os.path.join(folder_path, 'metadata.parquet')

        # get tmy3 external source table
        tmy3_external = os.path.join(base_files, 'external_TMY3_sources.csv')
        tmy3_df = pd.read_csv(tmy3_external)

        # download file
        response = requests.get(metadata_url, stream= True)

        if response.status_code == 200:
            with open(parquet_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            print(f"Parquet file downloaded successfully to {parquet_path}")
            parquet_df = pd.read_parquet(parquet_path)
            #reset index
            parquet_df_reset = parquet_df.reset_index()
        else:
            raise ValueError(f"Failed to download Parquet file. Status code: {response.status_code}")


        weather_dictionary = {}

        for i in id:

            # make folder for building ID
            id = os.path.join(folder_path, i)
            os.makedirs(id, exist_ok=True)

            # make models folder
            models = os.path.join(id, 'models')
            os.makedirs(models, exist_ok=True)  # Create folder using filename if it doesn't exist

            osm_path = os.path.join(models, i + '.osm')

            energy_model_base_url = mapping_df.loc[(mapping_df['year'] == int(obj.year)) & (mapping_df['database_name'] == str(obj.dataset_name)), 'energy_model_base_url'].values[0] if not mapping_df.empty else None
            energy_model_url = mapping_df.loc[(mapping_df['year'] == int(obj.year)) & (mapping_df['database_name'] == str(obj.dataset_name)), 'energy_model_url'].values[0] if not mapping_df.empty else None
            #TO DO check if this works for different database
            energy_model_valid_url = energy_model_base_url + str(i) + energy_model_url.strip('"')

            response = requests.get(energy_model_valid_url, stream= True)

            if response.status_code == 200:
                with gzip.GzipFile(fileobj=BytesIO(response.content), mode='rb') as gz:
                    extracted_content = gz.read()
                    with open(osm_path, 'wb') as extracted_file:
                        extracted_file.write(extracted_content)

                print(f"File downloaded and extracted to {osm_path}")
            else:
                print(f"Failed to download the file: {response.status_code}")

            # Remove 0s at the beginning
            just_id = int(str(i).lstrip('bldg').lstrip('0'))

            if 'parquet_df_reset' in locals():

                # Case-insensitive pattern for matching columns containing 'tmy3' or 'TMY3'
                pattern = re.compile('tmy3', flags=re.IGNORECASE)

                # Filter columns using the regex pattern
                filtered_columns = parquet_df_reset.filter(regex=pattern).columns

                # Check if there are any matching columns
                if not filtered_columns.empty:
                    result = parquet_df_reset.loc[parquet_df_reset['bldg_id'] == just_id, filtered_columns[0]].values[0]
                else:
                    print(f"No columns found containing 'tmy3' or 'TMY3'")

                # Store the column value at the specified ID as a key-value pair
                weather_dictionary.update({f"{just_id}_weather": result})

                # download weather file
                weather_dictionary[f"{just_id}_weather"]

                # get WMO station number
                wmo = tmy3_df.loc[tmy3_df['station_name'].str.lower() == (weather_dictionary[f"{just_id}_weather"]).lower(), 'WMO'].iloc[0]

                # get weather url
                weather_url = tmy3_df.loc[tmy3_df['station_name'].str.lower() == (weather_dictionary[f"{just_id}_weather"]).lower(), 'host'].values[0] + tmy3_df.loc[tmy3_df['station_name'].str.lower() == (weather_dictionary[f"{just_id}_weather"]).lower(), 'http_link'].values[0]

                weather_dictionary.update({f"{just_id}_wmo": wmo})

                weather_dictionary.update({f"{just_id}_url": weather_url})

                zip_filename = os.path.basename(weather_url)

                # copy default measures
                new_measure_path = os.path.join(id, 'measures')
                measure_path = Path(os.path.join(base_files, 'measures'))
                shutil.copytree(measure_path, new_measure_path)

                # create weather folder if it doesn't exist
                weather = os.path.join(id, 'weather')
                os.makedirs(weather, exist_ok=True)  # Create folder using filename if it doesn't exist

                weather_path = os.path.join(weather, zip_filename)

                # Send a GET request to the URL
                response = requests.get(weather_url)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # Open a local file and write the content
                    with open(weather_path, 'wb') as file:
                        file.write(response.content)

                    print(f"File {zip_filename} downloaded successfully.")
                else:
                    # Print an error message if the request was not successful
                    print(f"Error: Unable to download the file. Status code: {response.status_code}")


                # copy osw file
                osw_path = Path(os.path.join(base_files, 'workflow.osw'))
                new_osw_path = os.path.join(id, 'workflow.osw')
                shutil.copy(osw_path, new_osw_path)

                with open(new_osw_path, 'r') as osw:
                    data = json.load(osw)
                    data['seed_file'] =  f"{i}.osm"
                    data['weather_file'] = f"{zip_filename}"

                    # TO DO add better way to do this
                    data['steps'][0]['arguments']['model'] = f"{i}.osm"

                with open(new_osw_path, 'w') as osw:
                    json.dump(data, osw, indent=2)

