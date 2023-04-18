import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'translators'))
from eptobrick.extractor import epparser
from eptobrick.extractor.utils import utils
import opyplus as op
import random as rd

#### INIT ####
# Verbosity
m = utils.Nuncius(debug=3)

# Inputs
SMALLOFFICE = 'ASHRAE901_OfficeSmall_STD2013_Denver.idf'
MEDIUMOFFICE = 'ASHRAE901_OfficeMedium_STD2013_Denver.idf'
HOSPITAL = 'ASHRAE901_Hospital_STD2016_Denver.idf'

SOAHUS = 5
MOAHUS = 3
HOAHUS = 8

class Tests():

    def __init__(self, idfpath) -> None:
        # Accounting
        self.successes = []
        self.failures = []
        self.parser = epparser.Extractor()
        self.idfp = idfpath
        if self.idfp == SMALLOFFICE:
            self.nahus = SOAHUS
        elif self.idfp == MEDIUMOFFICE:
            self.nahus = MOAHUS
        elif self.idfp == HOSPITAL:
            self.nahus = HOAHUS

    def runTests(self, testlist):
        for test in testlist:
            self.testStatus(test)
        final, fails, succ = self.displayResults()
        return final, fails, succ

    def testStatus(self, testres):
        res, name, v = testres
        msg = f'{name} with {v}'
        if res:
            self.successes.append(msg)
        else:
            self.failures.append(msg)

    def displayResults(self):
        if self.successes != []:
            m.printMessage('Passed:', lvl='success')
            for success in self.successes:
                m.printMessage(f'\t{success}', lvl='success')
        if self.failures != []:
            m.printMessage('\tFailed:', lvl='failure')
            for failure in self.failures:
                m.printMessage(f'\t\t{failure}', lvl='failure')
            return False, self.failures, self.successes
        else:
            return True, self.failures, self.successes

    def loadIDF(self):
        name = 'loadIDF'
        try:
            self.idf = self.parser.load(os.path.join(os.path.dirname(__file__), 'resources', self.idfp))
            if isinstance(self.idf, op.epm.epm.Epm):
                m.printMessage(f'Loaded {self.idfp}', lvl='success')
                return [True, name, self.idfp]
            else:
                m.printMessage(f'Expected {op.epm.epm.Epm.__class__} but got {self.idf.__class__} instead', lvl='failure')
                return [False, name, self.idfp]
        except Exception as e:
            m.printMessage(f'{name} failed with the following error: {e}', lvl='failure')
            return [False, name, self.idfp]

    def bindBuilding(self):
        name = 'bindBuildings'
        try:
            self.parser.bindBuilding(self.idf)
            m.printMessage(f'Bound namespace to graph for {self.idfp}', lvl='success')
            return [True, name, self.idfp]
        except Exception as e:
            m.printMessage(f'{name} failed with the following error: {e}', lvl='failure')
            m.printMessage(f'Could not bind namespace for {self.idfp}', lvl='failure')
            return [False, name, self.idfp]

    def createAHUs(self):
        name = 'createAHUs'
        try:
            self.parser.createAHUs(self.idf)
            created = []
            for triple in self.parser.graph.triples((None, None, self.parser.BRICK['AHU'])):
                created.append(triple)
            if len(created) == self.nahus:
                return [True, name, self.idfp]
            else:
                return [False, name, self.idfp]
        except Exception as e:
            m.printMessage(f'{name} failed with the following error: {e}', lvl='failure')
            return [False, name, self.idfp]

    def saveGraph(self):
        name = 'saveGraph'
        try:
            self.parser.saveGraph()
            return [True, name, self.idfp]
        except Exception as e:
            m.printMessage(f'{name} failed with the following error: {e}', lvl='failure')
            return [False, name, self.idfp]