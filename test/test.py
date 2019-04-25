# Execute this file from the test directory
# python test.py

#from os.path import dirname
import sys
import os.path
import datetime
import time

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../client/')
import boptest

bop = boptest.Boptest()

(siteref, modelname) = bop.submit('wrapped.fmu')

time.sleep(3)

time_scale=5
start_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
tmp   = datetime.datetime.now() + datetime.timedelta(minutes=10)
end_datetime   = tmp.strftime("%Y-%m-%d %H:%M:%S")
realtime = False
input_params = { "time_scale"    :  time_scale, 
                 "start_datetime":  start_datetime,
                 "end_datetime"  :  end_datetime,
                 "realtime"     :  realtime
               }
bop.start(**input_params)

#bop.remove(siteref)

time.sleep(5)
model_inputs = bop.inputs()

yanfei_inputs = {"oveAct_u": { '1': 0.625 } }
inputs = yanfei_inputs.keys()

for x in model_inputs.keys():
    for y in inputs:
        #y = "u'"+y
        print (y)
        print(model_inputs[x])
        if model_inputs[x] == y:
            print('Hey there!')
            input_id = x
            bop.setInputs(input_id, **yanfei_inputs)

for x in model_inputs.keys():
    if 'TRooAir_y' in model_inputs[x]:
        id = x
        bop.outputs(id)

