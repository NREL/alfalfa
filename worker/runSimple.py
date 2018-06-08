########################################################################################################################
#  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#  following conditions are met:
#
#  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#  disclaimer.
#
#  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials provided with the distribution.
#
#  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
#  derived from this software without specific prior written permission from the respective party.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
#  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
########################################################################################################################

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


