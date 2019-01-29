import sys
import os
import json
import uuid
from pyfmi import load_fmu

fmupath = sys.argv[1]
jsonpath = sys.argv[2]
fmu = load_fmu(fmupath)

input_names = fmu.get_model_variables(causality = 2).keys()
output_names = fmu.get_model_variables(causality = 3).keys()

print ("input names are: )))))): ", input_names )
print ("output names are: )))))): ", output_names )

tags = []

fmuname = os.path.basename(fmupath) # without directories
fmuname = os.path.splitext(fmuname)[0] # without extension

siteid = uuid.uuid4()
sitetag = {
    "dis": "s:%s" % fmuname,
    "id": "r:%s" % siteid,
    "site": "m:",
    "simStatus": "s:Stopped",
    "simType": "s:fmu",
    "siteRef": "r:%s" % siteid
}
tags.append(sitetag)

for var_input in input_names:
    tag_input = {
        "id": "s:%s" % uuid.uuid4(),
        "dis": "s:%s" % var_input,
        "point": "input",
        "kind": "Number",
        "siteRef": "r:%s" % siteid,
        "unit": "1",
        "curVal": ""
    }
    tags.append(tag_input)
    tag_input={}

for var_output in output_names:
    tag_output = {
        "id": "s:%s" % uuid.uuid4(),
        "dis": "s:%s" % var_input,
        "point": "output",
        "kind": "Number",
        "siteRef": "r:%s" % siteid,
        "unit": "1",
        "curVal": ""
    }
    tags.append(tag_output)
    tag_output={}


with open(jsonpath, 'w') as outfile:
    json.dump(tags, outfile)
    print("Hey ((((((((((((((", tags, outfile)

print("jsonpath is: ", jsonpath )
print ("jsonpath is: ", jsonpath )

currentpath= os.getcwd()
print ("+++++++++++++ current path is: +++++++++++++ ", currentpath)
with open(currentpath+'/test_tagging.json') as test:
    json.dump(tags, test)

