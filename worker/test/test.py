import sys
import os

rootpath = os.path.dirname(__file__)
sys.path.append(os.path.join(rootpath,'../'))
from parsevariables import Variables

mapping_json_path = os.path.join(rootpath,'workflow/reports/haystack_report_mapping.json')
variables_xml_path = os.path.join(rootpath,'workflow/reports/export_bcvtb_report_variables.cfg')

iovars = Variables(variables_xml_path, mapping_json_path)

print(iovars.outputIndex("7fd5d8f3-1993-4f81-9b5a-e73921d63c08")) # return 6
print(iovars.outputIndex("wrong")) # return -1
print(iovars.outputIds())
print(iovars.inputIds())

for outputid in iovars.outputIds():
    print(outputid)
