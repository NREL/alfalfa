import json
import logging
from os import PathLike
from pathlib import Path
from typing import Dict, List
from xml.etree import ElementTree

from alfalfa_worker.lib.enums import PointType
from alfalfa_worker.lib.models import Point, Run


class Variables:
    inputs: Dict[str, Dict]
    outputs: Dict[str, Dict]
    day_index: int = 0
    hour_index: int = 1
    minute_index: int = 2
    month_index: int = 3

    def __init__(self, run: Run) -> None:
        self.run = run
        self.inputs = self._load_json('**/input_points.json')
        self.outputs = self._load_json('**/output_points.json')

    def _load_json(self, glob: str) -> List:
        result = {}
        files = self.run.glob(glob)
        for file in files:
            logging.info(f"reading file: {file}")
            with open(str(file), 'r') as fp:
                result.update(json.load(fp))

        logging.info(f"loaded: {result}")
        return result

    def load_reports(self):
        self.inputs = self._load_json('**/*_report_inputs.json')
        self.outputs = self._load_json('**/*_report_outputs.json')

    def generate_variables_cfg(self) -> str:
        bcvtb_variables_element = ElementTree.fromstring(
            """<?xml version="1.0" encoding="ISO-8859-1"?>
        <BCVTB-variables>
            <variable source='EnergyPlus'>
                <EnergyPlus name='EMS' type='current_day'/>
            </variable>
            <variable source='EnergyPlus'>
                <EnergyPlus name='EMS' type='current_hour'/>
            </variable>
            <variable source='EnergyPlus'>
                <EnergyPlus name='EMS' type='current_minute'/>
            </variable>
            <variable source='EnergyPlus'>
                <EnergyPlus name='EMS' type='current_month'/>
            </variable>
        </BCVTB-variables>
        """)
        input_index = 0
        for id, input in self.inputs.items():
            self.inputs[id]["index"] = input_index
            variable_element = ElementTree.Element('variable', {'source': 'Ptolemy'})
            ElementTree.SubElement(variable_element, 'EnergyPlus', {'variable': input['variable']})
            bcvtb_variables_element.append(variable_element)
            input_index += 1

            if "enable_variable" in input:
                self.inputs[id]["enable_index"] = input_index
                variable_element = ElementTree.Element('variable', {'source': 'Ptolemy'})
                ElementTree.SubElement(variable_element, 'EnergyPlus', {'variable': input['enable_variable']})
                bcvtb_variables_element.append(variable_element)
                input_index += 1

        output_index = 4
        for id, output in self.outputs.items():
            self.outputs[id]["index"] = output_index
            variable_element = ElementTree.Element('variable', {'source': 'EnergyPlus'})
            ElementTree.SubElement(variable_element, 'EnergyPlus', {'name': output['component'], 'type': output['variable']})
            bcvtb_variables_element.append(variable_element)
            output_index += 1

        return '<!DOCTYPE BCVTB-variables SYSTEM "variables.dtd">\n' + ElementTree.tostring(bcvtb_variables_element, encoding="unicode")

    def write_files(self, dir_name: PathLike):
        dir = Path(dir_name)
        inputs_file = dir / 'input_points.json'
        outputs_file = dir / 'output_points.json'
        variables_file = dir / 'variables.cfg'

        with variables_file.open('w') as fp:
            fp.write(self.generate_variables_cfg())

        with inputs_file.open('w') as fp:
            json.dump(self.inputs, fp)

        with outputs_file.open('w') as fp:
            json.dump(self.outputs, fp)

    def generate_points(self):
        echo_ids = []
        for id, input in self.inputs.items():
            point = Point(ref_id=id, point_type=PointType.INPUT, name=input["variable"])
            if "display_name" in input:
                point.name = input["display_name"]
            if "echo_id" in input:
                point.point_type = PointType.BIDIRECTIONAL
                echo_ids.append(input['echo_id'])
            self.run.add_point(point)

        for id, output in self.outputs.items():
            if id in echo_ids:
                continue
            point = Point(ref_id=id, point_type=PointType.OUTPUT, name=f"{output['component']} {output['variable']}")
            if "display_name" in output:
                point.name = output["display_name"]
            self.run.add_point(point)

        self.run.save()

    def get_input_index(self, id):
        return self.inputs[id]["index"]

    def has_enable(self, id):
        return "enable_variable" in self.inputs[id]

    def get_input_enable_index(self, id):
        return self.inputs[id]["enable_index"]

    def get_output_index(self, id):
        if id in self.outputs.keys():
            return self.outputs[id]['index']
        elif id in self.inputs.keys():
            if 'echo_id' in self.inputs[id]:
                return self.get_output_index(self.inputs[id]['echo_id'])

    def get_num_inputs(self):
        if len(self.inputs) == 0:
            return 0
        num_inputs = 0
        for input in self.inputs.values():
            num_inputs = max(input['index'], num_inputs)
            if 'enable_index' in input:
                num_inputs = max(input['enable_index'], num_inputs)
        return num_inputs + 1
