# Execute this file from the test directory
# python test2.py

import boptest
import time
import sys
from controllers import pid

bop = boptest.Boptest(url='http://web')

length = 48*3600
step = 60
u = pid.initialize()

print(u)

site = bop.submit('test/simple_1_zone_heating.fmu')
sys.stdout.flush()
bop.start(site, external_clock = "true")

for i in range(int(length/step)):
    bop.setInputs(site, u)
    bop.advance([site])
    y = bop.outputs(site)
    print(u)
    print(y)
    sys.stdout.flush()
    u = pid.compute_control(y)

bop.stop(site)

