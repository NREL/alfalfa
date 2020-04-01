########################################################################################################################
#  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#  following conditions are met:
#
#  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#  disclaimer.
#
#  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials provided with the distribution.
#
#  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
#  derived from this software without specific prior written permission from the respective party.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
#  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
########################################################################################################################

import xml.etree.ElementTree as ET
import json

# <variable source='EnergyPlus'>
#   <EnergyPlus name='CAV_bas' type='Air System Outdoor Air Flow Fraction'/>
# </variable>
# <variable source='Ptolemy'>
#  <EnergyPlus variable='VAV_mid_WITH_REHEAT_Outside_Air_Damper_CMD_Enable'/>
# </variable>


class ParseVariables:
    def __init__(self, xml_file_path, json_file_path):
        self.xml = ET.parse(xml_file_path)

        """
        Mapping of:
            {
                haystack_point_id: {
                    variable: E+ variable name,
                    id: haystack_id
                    }, ...
            }
        """
        self.json_inputs = dict()

        """
        Mapping of:
            {
                haystack_point_id: {
                    type: E+ variable name,
                    name: E+ key value,
                    id: haystack_id
                    }, ...
            }

        """
        self.json_outputs = dict()

        """
        Output refers to being sourced from E+.  list of:
            {
                name: E+ key value,
                type: E+ variable name,
                index: index in XML
            }
        """
        self.outputs_list = list()

        """
        Input refers to being sourced from Ptolemy. list of:
            {
                variable: E+ !- Name
                index: index in XML
            }
        """
        self.inputs_list = list()

        root = self.xml.getroot()

        input_index = 0
        output_index = 0
        for index, child in enumerate(root):
            ep_tag = child.find('EnergyPlus')

            if child.attrib['source'] == 'EnergyPlus':
                name = ep_tag.attrib['name']
                variable_type = ep_tag.attrib['type']

                output_item = {'name': name, 'type': variable_type, 'index': output_index}
                self.outputs_list.append(output_item)
                output_index += 1

            #
            if child.attrib['source'] == 'Ptolemy':
                variable = ep_tag.attrib['variable']

                input_item = {'variable': variable, 'index': input_index}
                self.inputs_list.append(input_item)
                input_index += 1

        # Read in json as dict
        with open(json_file_path, "r") as f:
            parsed_json = json.loads(f.read())

        for i in range(0, len(parsed_json)):
            if parsed_json[i]['source'] == 'EnergyPlus':
                item = {key: parsed_json[i][key] for key in ('type', 'name', 'id')}
                item['id'] = item['id'].replace('r:', '')
                self.json_outputs[item['id']] = item
            elif parsed_json[i]['source'] == 'Ptolemy':
                item = {key: parsed_json[i][key] for key in ('variable', 'id')}
                item['id'] = item['id'].replace('r:', '')
                self.json_inputs[item['id']] = item

    def get_output_ids(self):
        """
        Return all of the haystack ids corresponding to E+ outputs

        :return: TODO what is return type
        """
        return self.json_outputs.keys()

    def get_output_index(self, id_val):
        """
        Given a haystack id, return the index corresponding to the E+ cfg file for the corresponding output variable

        :param id_val:
        :return:
        """
        if id_val in self.json_outputs:
            item = self.json_outputs[id_val]
            variable_type = item['type']
            name = item['name']
            return self.output_index_from_type_and_name(variable_type, name)
        else:
            return -1

    def get_input_ids(self):
        """
        Return all of the haystack ids corresponding to E+ inputs

        :return:
        """
        return self.json_inputs.keys()

    def get_input_index(self, id_val):
        """
        Given a haystack id, return the index corresponding to the E+ cfg file for the corresponding input variable

        :param id_val:
        :return:
        """
        if id_val in self.json_inputs:
            item = self.json_inputs[id_val]
            variable = item['variable']
            return self.input_index_from_variable_name(variable)
        else:
            return -1

    def output_index_from_type_and_name(self, variable_type, name):
        """
        Given a variable type and name, return the XML index

        :param variable_type:
        :param name:
        :return:
        """
        for output_item in self.outputs_list:
            if (output_item['name'] == name) and (output_item['type'] == variable_type):
                return output_item['index']

        return -1

    def input_index_from_variable_name(self, variable):
        for input_item in self.inputs_list:
            if input_item['variable'] == variable:
                return input_item['index']

        return -1
