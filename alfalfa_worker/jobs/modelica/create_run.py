import json
import os
from pathlib import Path
from uuid import uuid4

from pyfmi import load_fmu

from alfalfa_worker.lib.job import Job
from alfalfa_worker.lib.run import RunStatus
from alfalfa_worker.lib.sim_type import SimType


class CreateRun(Job):

    def __init__(self, upload_id, model_name, run_id=None):
        self.create_run_from_model(upload_id, model_name, SimType.MODELICA, run_id=run_id)
        # Define FMU specific attributes
        self.upload_fmu: Path = self.dir / model_name
        self.fmu_path = self.dir / 'model.fmu'
        self.fmu_json = self.dir / 'tags.json'
        self.model_name = model_name

        # Needs to be set after files are uploaded / parsed.
        self.site_ref = None

    def exec(self):
        self.set_run_status(RunStatus.PREPROCESSING)
        """
        Workflow for fmu.  External call to python2 must be made since currently we are using an
        old version of the Modelica Buildings Library and JModelica.
        :return:
        """
        self.logger.info("add_fmu for {}".format(self.run.ref_id))

        # Create the FMU tags (no longer external now that python2 is deprecated)
        self.create_tags()
        # insert tags into db
        self.insert_fmu_tags()
        self.upload_fmu.rename(self.fmu_path)

    def validate(self) -> None:
        assert (self.dir / 'model.fmu').exists(), "model file not created"
        assert (self.dir / 'tags.json').exists(), "tags file not created"

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.READY)

    def get_site_ref(self, haystack_json):
        """
        Find the site given the haystack JSON file.  Remove 'r:' from string.
        :param haystack_json: json serialized Haystack document
        :return: site_ref: id of site
        """
        site_ref = ''
        with open(haystack_json) as json_file:
            data = json.load(json_file)
            for entity in data:
                if 'site' in entity:
                    if entity['site'] == 'm:':
                        site_ref = entity['id'].replace('r:', '')
                        break
        return site_ref

    def insert_fmu_tags(self):
        with open(self.fmu_json, 'r') as f:
            data = f.read()
        points_json = json.loads(data)

        self.run_manager.add_site_to_mongo(points_json, self.run)

    def create_tags(self):
        # 1.0 setup the inputs
        fmu = load_fmu(self.upload_fmu)

        # 2.0 get input/output variables from the FMU
        input_names = fmu.get_model_variables(causality=2).keys()
        output_names = fmu.get_model_variables(causality=3).keys()

        # 3.0 add site tagging
        tags = []

        fmu_upload_name = os.path.basename(self.model_name)  # without directories
        fmu_upload_name = os.path.splitext(fmu_upload_name)[0]  # without extension

        # TODO: Figure out how to find geo_city
        sitetag = {
            "dis": "s:%s" % fmu_upload_name,
            "id": "r:%s" % self.run.ref_id,
            "site": "m:",
            "datetime": "s:",
            "simStatus": "s:Stopped",
            "simType": "s:fmu",
            "siteRef": "r:%s" % self.run.ref_id
        }
        tags.append(sitetag)

        # 4.0 add input tagging
        for var_input in input_names:
            if not var_input.endswith("_activate"):
                tag_input = {
                    "id": "r:%s" % uuid4(),
                    "dis": "s:%s" % var_input,
                    "siteRef": "r:%s" % self.run.ref_id,
                    "point": "m:",
                    "writable": "m:",
                    "writeStatus": "s:disabled",
                    "kind": "s:Number",
                }
                tags.append(tag_input)
                tag_input = {}

        # 5.0 add output tagging
        for var_output in output_names:
            tag_output = {
                "id": "r:%s" % uuid4(),
                "dis": "s:%s" % var_output,
                "siteRef": "r:%s" % self.run.ref_id,
                "point": "m:",
                "cur": "m:",
                "curVal": "n:",
                "curStatus": "s:disabled",
                "kind": "s:Number",
            }
            tags.append(tag_output)
            tag_output = {}

        # 6.0 write tags to the json file
        with open(self.fmu_json, 'w') as outfile:
            json.dump(tags, outfile)
