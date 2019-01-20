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

tags = []

fmuname = os.path.basename(fmupath) # without directories
fmuname = os.path.splitext(fmuname)[0] # without extension

siteid = uuid.uuid4()
sitetag = {
    "dis": "s:%s" % fmuname,
    "id": "r:%s" % siteid,
    "site": "m:",
    "simStatus": "s:Stopped",
    "siteRef": "r:%s" % siteid
}
tags.append(sitetag)

with open(jsonpath, 'w') as outfile:
    json.dump(tags, outfile)
