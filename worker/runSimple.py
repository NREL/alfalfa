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
import mlep
import os

# Create an mlepProcess instance and configure it
ep = mlep.mlepProcess()

# Arguments
idfFile = '/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/cosim.idf'
weatherFile = '/Applications/EnergyPlus-8-7-0/WeatherData/USA_MD_Baltimore-Washington.Intl.AP.724060_TMY3.epw'
ep.acceptTimeout = 20000
mapping_file = "/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/haystack_report_mapping.json"

# Parse directory
idfFileDetails = os.path.split(idfFile)
ep.workDir =  idfFileDetails[0]
ep.arguments = (idfFile, weatherFile)

# Get Mapping
[inputs_list, outputs_list] = mlep.mlepJSON(mapping_file)
#print(inputs_list)
#print(outputs_list)

# Start EnergyPlus cosimulation
(status,msg) = ep.start()

# Check E+
if status != 0:
    raise Exception('Could not start EnergyPlus: %s.'%(msg))

# Accept Socket
[status, msg] = ep.acceptSocket()

if status != 0:
    raise Exception('Could not connect EnergyPlus: %s.'%(msg))

# The main simulation loop
deltaT = 15*60          # time step = 15 minutes
kStep = 1               # current simulation step
MAXSTEPS = 4*24*4+1     # max simulation time = 4 days
flag = 0

# Simulation
while kStep <= MAXSTEPS:
    # Read a data packet from E+
    packet = ep.read()
    if packet == '':
        raise InputError('packet','Message Empty: %s.'%(msg))

    # Parse it to obtain building outputs
    [flag, eptime, outputs] = mlep.mlepDecodePacket(packet)
    #print(kStep)
    if flag != 0:
        break

    # Inputs
    inputs = (1,1,0)

    # Write to inputs of E+
    ep.write(mlep.mlepEncodeRealData(2, 0, (kStep-1)*deltaT, inputs))

    # Advance time
    print(kStep)
    kStep = kStep + 1
    
# Stop EnergyPlus
ep.stop(True)
print('Stopped with flag %d'%flag)


'''
# ==========FLAGS==============
# Flag	Description
# +1	Simulation reached end time.
# 0	    Normal operation.
# -1	Simulation terminated due to an unspecified error.
# -10	Simulation terminated due to an error during the initialization.
# -20	Simulation terminated due to an error during the time integration.
'''


