 #!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
 This script is for testing purposes only.

 This script illustrates the usage of class mlepProcess.

 This example is taken from an example distributed with BCVTB version
 0.8.0 (https://gaia.lbl.gov/bcvtb).

 This script is free software.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
"""
import sys
#sys.path.append("./")
import mlep
import shutil
import os

# Create an mlepProcess instance and configure it
ep = mlep.mlepProcess()
idfFileOriginal = '../resources/OpenStudio/LargeOfficeDC_HX_econ2_bcvtb/run/in.idf'
#idfFileOriginal = 'SmOffPSZ.idf'
idfFileOriginalDetails = os.path.split(idfFileOriginal)
idfFile = os.path.join(idfFileOriginalDetails[0],'mlep.idf')
shutil.copy(idfFileOriginal,idfFile)
#weatherFile = '../resources/OpenStudio/weather/USA_MD_Baltimore-Washington.Intl.AP.724060_TMY3.epw'
weatherFile = '/Applications/EnergyPlus-8-7-0/WeatherData/USA_MD_Baltimore-Washington.Intl.AP.724060_TMY3.epw'
ep.arguments = (idfFile, weatherFile)
ep.acceptTimeout = 200000

# Start EnergyPlus cosimulation
(status,msg) = ep.start()

# Check E+
if status != 0:
    raise Exception('Could not start EnergyPlus: %s.'%(msg))

# Accept Socket
[status, msg] = ep.acceptSocket()

if status != 0:
    print('Could not connect to EnergyPlus: %s.', msg)

# The main simulation loop
deltaT = 15*60          # time step = 15 minutes
kStep = 1               # current simulation step
MAXSTEPS = 4*24*4+1     # max simulation time = 4 days

TCRooLow = 22           # Zone temperature is kept between TCRooLow & TCRooHi
TCRooHi = 26
TOutLow = 22            # Low level of outdoor temperature
TOutHi = 24             # High level of outdoor temperature
ratio = (TCRooHi - TCRooLow)/(TOutHi - TOutLow)

# logdata stores set-points, outdoor temperature, and zone temperature at
# each time step.
logdata = ()
flag = 0
print('Stopped with flag %d'%flag)

while kStep <= MAXSTEPS:
    # Read a data packet from E+
    packet = ep.read()
    if packet == '':
        raise InputError('packet','Message Empty: %s.'%(msg))

    # Parse it to obtain building outputs
    [flag, eptime, outputs] = mlep.mlepDecodePacket(packet)
    eptime = kStep
    if flag != 0:
        break

    # Inputs
    #inputs = (18,19,)
    inputs = (1,1,1,1,1,1,1,1,)

    # Write to inputs of E+
    ep.write(mlep.mlepEncodeRealData(2, 0, (kStep-1)*deltaT, inputs));    
    
    # Advance time
    kStep = kStep + 1
    
# Stop EnergyPlus
ep.stop(True)

'''
# ==========FLAGS==============
# Flag	Description
# +1	Simulation reached end time.
# 0	    Normal operation.
# -1	Simulation terminated due to an unspecified error.
# -10	Simulation terminated due to an error during the initialization.
# -20	Simulation terminated due to an error during the time integration.
'''


