import testing
from testing import SMALLOFFICE, MEDIUMOFFICE, HOSPITAL, m

successes = []
failures = []
cases = [
    SMALLOFFICE, 
    MEDIUMOFFICE, 
    HOSPITAL
    ]

for case in cases:
    t = testing.Tests(case)
    tests = [
        t.loadIDF(),
        t.bindBuilding(),
        t.createAHUs(),
        t.saveGraph()
    ]
    _, fa, su = t.runTests(tests)
    successes.append(su)
    failures.append(fa)

tot_fails = len([x for xs in failures for x in xs])
if tot_fails > 0:
    print('\n\n\n')
    m.printMessage('\t\t#### SOME TESTS HAVE FAILED ####', lvl='failure')
    for ind, failurelist in enumerate(failures):
        if len(failurelist) > 0:
            m.printMessage(f'\t\t---- FOR CASE {cases[ind]} ----', lvl='failure')
            for fail in failurelist:
                m.printMessage(f'\t\t{fail}', lvl='failure')