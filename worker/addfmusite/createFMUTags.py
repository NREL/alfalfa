import sys
import os
import json
import uuid
from pyfmi import load_fmu

#1.0 setup the inputs
fmupath = sys.argv[1]
jsonpath = sys.argv[2]
fmu = load_fmu(fmupath)

#2.0 get input/output variables from the FMU
input_names = fmu.get_model_variables(causality = 2).keys()
output_names = fmu.get_model_variables(causality = 3).keys()

print ("input names are: )))))): ", input_names )
print ("output names are: )))))): ", output_names )

#3.0 add site tagging
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

#4.0 add input tagging
for var_input in input_names:
    tag_input = {
        "id": "r:%s" % uuid.uuid4(),
        "dis": "s:%s" % var_input + ":input",
        "siteRef": "r:%s" % siteid,
        "equipRef": "r:",
        "zone": "m:",
        "air": "m:",
        "point": "m:",
        "kind": "s:Number",
        "unit": "s:%",
        "curVal": "n:"
    }
    tags.append(tag_input)
    tag_input={}

#5.0 add output tagging
for var_output in output_names:
    tag_output = {
        "id": "r:%s" % uuid.uuid4(),
        "dis": "s:%s" % var_output + ":output",
        "siteRef": "r:%s" % siteid,
        "equipRef": "r:",
        "zone": "m:",
        "air": "m:",
        "point": "m:",
        "kind": "s:Number",
        "unit": "s:%",
        "curVal": "n:"
    }
    tags.append(tag_output)
    tag_output={}

# 6.0 write tags to the json file
with open(jsonpath, 'w') as outfile:
    json.dump(tags, outfile)
    print("Hey ((((((((((((((", tags, outfile)

print("jsonpath is: ", jsonpath )
print ("jsonpath is: ", jsonpath )

