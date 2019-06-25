# Execute this file from the test directory
# python test.py

import boptest
import time
import sys

bop = boptest.Boptest(url='http://web')

siteids = []
for _ in range(1):
    site = bop.submit('test/wrapped.fmu')
    siteids.append(site)

    bop.start(site, external_clock = "true")

for i in range(100):
    bop.advance(siteids)

    if i % 2 == 0:
        # Set inputs by site id and display name
        bop.setInputs(siteids[0], {"oveAct_u": 1.0})
    else:
        # Python None to reset an input
        bop.setInputs(siteids[0], {"oveAct_u": None})

    print(bop.inputs(siteids[0]))
    print(bop.outputs(siteids[0]))
    sys.stdout.flush()
    time.sleep(2)

for site in siteids:
    bop.stop(site)

