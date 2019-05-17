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


siteref = bop.submit('wrapped.fmu')

time_scale=5

'''
# For OSM models
start_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
tmp   = datetime.datetime.now() + datetime.timedelta(minutes=10)
end_datetime   = tmp.strftime("%Y-%m-%d %H:%M:%S")
'''



# For FMU models
start_datetime = 0
end_datetime   = 300

realtime = False
input_params = { "site_id"       :  siteref,
                 "time_scale"    :  time_scale, 
                 "start_datetime":  str(start_datetime),
                 "end_datetime"  :  str(end_datetime),
                 "realtime"     :  realtime
               }


bop.start(**input_params)


#bop.remove(siteref)


model_inputs = bop.inputs(siteref)

yanfei_inputs = {"oveAct_u": { '1': 0.625 } }
inputs = yanfei_inputs.keys()

for x in model_inputs.keys():
    #print ('check 000: ', x)
    for y in inputs:
        #y = "u'"+y
        #print ('check001 ', y)
        #print('check 002 ', model_inputs[x])
        if model_inputs[x] == y:
            #print('check003 Hey there!')
            input_id = x
            #input_id = input_id.replace("u'","")
            bop.setInputs(input_id, **yanfei_inputs)

for x in model_inputs.keys():
    if 'TRooAir_y' in model_inputs[x]:
        id = x
        #print ('check888: ', id)
        outpus = bop.outputs(id)

