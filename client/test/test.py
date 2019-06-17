# Execute this file from the test directory
# python test.py

import boptest
import time

bop = boptest.Boptest(url='http://web')

siteids = []
for _ in range(1):
    site = bop.submit('test/SmallOffice.osm')
    siteids.append(site)

    input_params = { "site_id":  site }
    bop.start(**input_params)

for _ in range(5000):
    bop.advance(siteids)
    time.sleep(1)

for site in siteids:
    bop.stop(site)

