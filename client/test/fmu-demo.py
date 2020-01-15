import sys
import os
thispath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thispath + '/../')
import boptest

sys.path.insert(0, './controllers')

from controllers import pid

bop = boptest.Boptest(url='http://localhost')

length = 48 * 3600
step = 300
u = pid.initialize()

site = bop.submit(thispath + '/simple_1_zone_heating.fmu')
bop.start(site, external_clock="true")

for i in range(int(length / step)):
    bop.setInputs(site, u)
    bop.advance([site])
    y = bop.outputs(site)
    print(u)
    print(y)
    sys.stdout.flush()
    u = pid.compute_control(y)

bop.stop(site)
