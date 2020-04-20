import sys
import os
thispath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thispath + '/../')
import boptest
import time

sys.path.insert(0, './controllers')

from controllers import pid

bop = boptest.Boptest(url='http://localhost')

osm_files = []
for _ in range(5):
    osm_files.append(thispath + '/CBI_EndtoEndTest_20190618_version2.osm')

siteids = bop.submit_many(osm_files)
bop.start_many(siteids, external_clock = "true")

for i in range(30):
    bop.advance(siteids)
    #total_rtu_power = 0.0
    #for siteid in siteids:
    #    rtu_power = bop.outputs(siteid)[u'RTU_Power']
    #    total_rtu_power = total_rtu_power + rtu_power
    #print(total_rtu_power)
    time.sleep(2)

bop.stop_many(siteids)

