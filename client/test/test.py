# Execute this file from the test directory
# python test.py

import boptest
import time

bop = boptest.Boptest(url='http://web')

siteids = []
for _ in range(5):
    site = bop.submit('test/SmallOffice.osm')
    siteids.append(site)

    bop.start(site, external_clock = "true")

for _ in range(500):
    bop.advance(siteids)
    time.sleep(1)

for site in siteids:
    bop.stop(site)

