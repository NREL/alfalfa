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

# -*- coding: utf-8 -*-

"""
mlepProcess
~~~~~~~~~~~
A class of a co-simulation process. This class represents a co-simulation
process. It enables data exchanges between the host (in Python) and the
client (the co-simulation process - E+), using the communication protocol
defined in BCVTB.

This class wraps the mlep* functions.

See also:
    <a href="https://gaia.lbl.gov/bcvtb">BCVTB (hyperlink)</a>

Usage:
    > mlepProcess()

   Note: This function is based on the Matlab implementation for mlep. The original
   files were written by Nghiem Truong and Willy Bernal

   Protocol Version 1 & 2:
   Packet has the form:
       v f dr di db t r1 r2 ... i1 i2 ... b1 b2 ... \n
       where
       v    - version number (1,2)
       f    - flag (0: communicate, 1: finish, -10: initialization error,
               -20: time integration error, -1: unknown error)
       dr   - number of real values
       di   - number of integer values
       db   - number of boolean values
       t    - current simulation time in seconds (format 20.15e)
       r1 r2 ... are real values (format 20.15e)
       i1 i2 ... are integer values (format d)
       b1 b2 ... are boolean values (format d)
       \n   - carriage return

Note that if f is non-zero, other values after it will not be processed.

:author: Willy Bernal Heredia
:copyright: (c) 2016 by The Alliance for Sustainable Energy
:license: BSD-3
"""

import mlep
import socket


class MlepProcess:
    def __init__(self):
        self.description = 'mlepProcess Object'
        self.version = 2.0                  # Current Version of the Protocol
        self.program = 'runenergyplus'      # Excecutable
        self.env = {'BCVTB_HOME': '/Users/wbernalh/Documents/Projects/J2/Code/TCP/bcvtb/'}  # Environment
        # Arguments to the client program
        self.arguments = ('/Applications/EnergyPlus-8-6-0/ExampleFiles/1ZoneUncontrolled.idf',
                          '/Applications/EnergyPlus-8-6-0/WeatherData/USA_CO_Golden-NREL.724666_TMY3.epw')
        self.workDir = './'                 # Working directory (default is current directory)
        self.port = 0                       # Socket port (default 0 = any free port)
        self.host = 'localhost'             # Host name (default '' = localhost)
        self.bcvtbDir = '/Users/wbernalh/Documents/Projects/J2/Code/TCP/bcvtb/'  # Directory to BCVTB
        # (default '' means that if no environment variable exist, set it to current directory)
        self.configFile = 'socket.cfg'      # Name of socket configuration file
        self.configFileWriteOnce = False  # if true, only write the socket config file
        # for the first time and when server socket changes.
        self.accept_timeout = 20000         # Timeout for waiting for the client to connect
        self.exe_cmd = 'subprocess'         # How to execute EnergyPlus from Matlab (system/Java)
        self.status = 0
        self.msg = ''

        # Property
        self.rwTimeout = 0                  # Timeout for sending/receiving data (0 = infinite)
        self.is_running = False             # Is co-simulation running?
        self.server_socket = None           # Server socket to listen to client
        self.comm_socket = None             # Socket for sending/receiving data
        self.writer = ''                    # Buffered writer stream
        self.reader = ''                    # Buffered reader stream
        self.pid = ()                       # Process ID for E+
        self.deltaT = 0                     # Time step for E+
        self.kStep = 0                      # E+ simulation step
        self.flag = 0                       # Co-simulation flag
        self.MAX_STEPS = 0                  # Co-simulation max. steps
        self.inputs_list = []               # Co-simulation input list
        self.outputs_list = []              # Co-simulation output list
        self.client_address = None          # Client Address
        self.inputs = []                    # E+ Simulation Inputs
        self.outputs = []                   # E+ Simulation Outputs
        self.mapping = ''                   # Path to the haystack mapping file

    # Start
    # ==============================================================
    def start(self):
        # status and msg are returned from the client process
        # status = 0 --> success
        if self.is_running:
            return

        # Check parameters
        if self.program is None:
            print('Program name must be specified.')

        # Call mlepCreate
        try:
            if self.server_socket is not None:
                the_port = self.server_socket
                if self.configFileWriteOnce:
                    the_config_file = -1  # Do not write socket config file
                else:
                    the_config_file = self.configFile
            else:
                the_port = self.port
                the_config_file = self.configFile

            # Call MLEPCreate function
            [self.server_socket, self.comm_socket, status, msg] = \
                mlep.mlep_create(self.program, self.arguments, self.workDir, self.accept_timeout, the_port,
                                 self.host, self.bcvtbDir, the_config_file, self.env, self.exe_cmd)
        except BaseException:
            import traceback
            traceback.print_exc()
            print('Throw Error/Close Socket')
            status = 1
            msg = 'Could not start the process.'

        # Return
        return status, msg

    # Accept Socket
    # ==============================================================
    def accept_socket(self):
        # status and msg are returned from the client process
        # status = 0 --> success
        status = self.status
        msg = self.msg

        # Accept Socket
        (self.comm_socket, self.client_address) = self.server_socket.accept()

        # Create Streams
        if status == 0 and isinstance(self.comm_socket, socket.socket):
            self.is_running = True
            msg = ''

        # Return
        return status, msg

    # Stop
    # ==============================================================
    def stop(self, stop_signal):
        # Not Running
        if not self.is_running:
            return

        try:
            # Send stop signal
            if stop_signal:
                self.write(mlep.mlep_encode_real_data(2, 1, None, (1,)))

            # Close connection
            if self.comm_socket:
                # self.comm_socket.stop() #original way of terminating a socket connection
                # time.sleep(10) # add some extra time for buffer to finish energyplus post-processing
                # pass
                self.comm_socket.close()  # the correct way by Yanfei
                self.comm_socket = None

        except Exception as e:
            print('Error {0}'.format(e))
        # Update
        self.is_running = False

    # Read
    # ==============================================================
    def read(self):
        # Read Packet
        if self.is_running:
            packet = self.comm_socket.recv(5000)
        else:
            packet = ''
            print('Co-simulation is not running.')

        # Return
        return packet

    # Write
    # ==============================================================
    def write(self, packet):
        if self.is_running:
            packet = packet.encode(encoding='UTF-8')
            self.comm_socket.sendall(packet)
        else:
            print('Co-simulation is not running.')
