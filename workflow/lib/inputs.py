import boto3  # This is not called directly, but must be installed for Pandas to read files from S3
import pandas as pd

class Inputs:
    """Class to assign inputs for running buildstock models in Alfalfa."""

    def __init__(self, year, dataset_name, upgrade, id, folder):
        self.year = year
        self.dataset_name = dataset_name
        self.upgrade = upgrade
        self.id = id
        # Folder to download models
        self.folder = folder
