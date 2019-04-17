#from os.path import dirname
import sys
import os.path

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../client/')
import boptest

bop = boptest.Boptest()
bop.submit('wrapped.fmu')

