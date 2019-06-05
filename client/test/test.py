# Execute this file from the test directory
# python test.py

import boptest
import time

bop = boptest.Boptest(url='http://web')

for _ in range(10):
    siteid = bop.submit('test/wrapped.fmu')

#input_params = { "site_id":  siteid }
#bop.start(**input_params)
#
#start = time.time()
#
#for _ in range(5000):
#    bop.advance(siteid)
#
#end = time.time()
#
#print(end - start)
#
#bop.stop(siteid)

