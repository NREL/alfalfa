import xml.etree.ElementTree as ET
import json

# <variable source='EnergyPlus'>
#   <EnergyPlus name='CAV_bas' type='Air System Outdoor Air Flow Fraction'/>
# </variable>
#<variable source='Ptolemy'>
#  <EnergyPlus variable='VAV_mid_WITH_REHEAT_Outside_Air_Damper_CMD_Enable'/>
#</variable>

class Variables:
    def __init__(self,xmlfilepath,jsonfilepath):
        self.xml = ET.parse(xmlfilepath)
        self.json_inputs = dict()
        self.json_outputs = dict()
        self.outputs_list = list()
        self.inputs_list = list()

        root = self.xml.getroot()

        inputIndex = 0
        outputIndex = 0
        for index, child in enumerate(root):
            eptag = child.find('EnergyPlus')

            if child.attrib['source'] == 'EnergyPlus':
                name = eptag.attrib['name']
                variabletype = eptag.attrib['type']

                outputitem = {'name': name, 'type': variabletype, 'index': outputIndex}
                self.outputs_list.append(outputitem)
                outputIndex += 1

            if child.attrib['source'] == 'Ptolemy':
                variable = eptag.attrib['variable']

                inputitem = {'variable': variable, 'index': inputIndex}
                self.inputs_list.append(inputitem)
                inputIndex += 1


        fid = open(jsonfilepath, "r")
        json_string = fid.read()
        parsed_json = json.loads(json_string)

        for i in range(0, len(parsed_json)):
            if parsed_json[i]['source'] == 'EnergyPlus':
                item = {key: parsed_json[i][key] for key in ('type', 'name', 'id')}
                item['id'] = item['id'].replace('r:', '')
                self.json_outputs[item['id']] = item
            elif parsed_json[i]['source'] == 'Ptolemy':
                item = {key: parsed_json[i][key] for key in ('variable', 'id')}
                item['id'] = item['id'].replace('r:', '')
                self.json_inputs[item['id']] = item

    # Return all of the haystack ids corresponding to E+ outputs
    def outputIds(self):
        return self.json_outputs.keys()

    # Given a haystack id, return the index corresponding to the E+ cfg file for the corresponding output variable
    def outputIndex(self,idval):
        if idval in self.json_outputs:
            item = self.json_outputs[idval]
            variabletype = item['type']
            name = item['name']
            return self.outputIndexFromTypeAndName(variabletype,name)
        else:
            return -1

    # Return all of the haystack ids corresponding to E+ inputs
    def inputIds(self):
        return self.json_inputs.keys()

    # Given a haystack id, return the index corresponding to the E+ cfg file for the corresponding input variable
    def inputIndex(self,idval):
        if idval in self.json_inputs:
            item = self.json_inputs[idval]
            variable = item['variable']
            return self.inputIndexFromVariableName(variable)
        else:
            return -1

    def outputIndexFromTypeAndName(self,variabletype,name):
        for outputitem in self.outputs_list:
            if (outputitem['name'] == name) and (outputitem['type'] == variabletype):
                return outputitem['index']

        return -1;

    def inputIndexFromVariableName(self,variable):
        for inputitem in self.inputs_list:
            if inputitem['variable'] == variable:
                return inputitem['index']
                
        return -1;

