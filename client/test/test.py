# Execute this file from the test directory
# python test.py

import boptest
import time
import sys

bop = boptest.Boptest(url='http://web')

siteids = []
for _ in range(1):
    site = bop.submit('test/SmallOffice.osm')
    siteids.append(site)

    bop.start(site, external_clock = "true")

for _ in range(500):
    bop.advance(siteids)
    print(bop.outputs(siteids[0]))
    print(bop.inputs(siteids[0]))
    sys.stdout.flush()
    time.sleep(1)

for site in siteids:
    bop.stop(site)

