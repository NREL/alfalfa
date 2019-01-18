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

fmuname = os.path.splitext(fmupath)[0]
sitetag = {
    "dis": "s:%s" % fmuname,
    "id": "r:%s" % uuid.uuid4(),
    "site": "m:"
}
tags.append(sitetag)


with open(jsonpath, 'w') as outfile:
    json.dump(tags, outfile)
