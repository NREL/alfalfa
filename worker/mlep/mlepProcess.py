#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
mlepProcess
~~~~~~~~~~~
A class of a cosimulation process. This class represents a co-simulation
process. It enables data exchanges between the host (in Python) and the
client (the cosimulation process - E+), using the communication protocol 
defined in BCVTB.

This class wraps the mlep* functions.

See also:
	<a href="https://gaia.lbl.gov/bcvtb">BCVTB (hyperlink)</a>

Usage:
  >>> mlepProcess

Note: This function is based on the Matlab implementation for mlep. The original
files were written by Nghiem Truong and Willy Bernal

:author: Willy Bernal Heredia
:copyright: (c) 2016 by The Alliance for Sustainable Energy
:license: BSD-3
"""
import mlep
import socket

class mlepProcess:
    def __init__(self):
        self.description = 'mlepProcess Object'
        self.version = 2.0                      # Current Version of the Protocol
        self.program = 'runenergyplus'              # Excecutable
        self.env = {'BCVTB_HOME':'/Users/wbernalh/Documents/Projects/J2/Code/TCP/bcvtb/'}   # Environment
        self.arguments = ('/Applications/EnergyPlus-8-6-0/ExampleFiles/1ZoneUncontrolled.idf', '/Applications/EnergyPlus-8-6-0/WeatherData/USA_CO_Golden-NREL.724666_TMY3.epw')           # Arguments to the client program
        self.workDir = './'                           # Working directory (default is current directory)
        self.port = 0                               # Socket port (default 0 = any free port)
        self.host = 'localhost'                              # Host name (default '' = localhost)
        self.bcvtbDir = '/Users/wbernalh/Documents/Projects/J2/Code/TCP/bcvtb/'                          # Directory to BCVTB 
        # (default '' means that if no environment variable exist, set it to current directory)
        self.configFile = 'socket.cfg'              # Name of socket configuration file
        self.configFileWriteOnce = False                #if true, only write the socket config file
        # for the first time and when server socket changes.
        self.acceptTimeout = 20000                  # Timeout for waiting for the client to connect
        self.execcmd = 'subprocess'                           # How to execute EnergyPlus from Matlab (system/Java)
        self.status = 0
        self.msg = ''

        # Property
        self.rwTimeout = 0                  # Timeout for sending/receiving data (0 = infinite)
        self.isRunning = False              # Is co-simulation running?
        self.serverSocket = None            # Server socket to listen to client
        self.commSocket = None              # Socket for sending/receiving data
        self.writer = ''                    # Buffered writer stream
        self.reader = ''                    # Buffered reader stream
        self.pid = ()                       # Process ID for E+
    
    # Start
    #==============================================================
    def start(self):
        # status and msg are returned from the client process
        # status = 0 --> success
        if self.isRunning:
            return

        # Check parameters
        if self.program is None:
            print('Program name must be specified.');

        # Call mlepCreate
        try:
            if self.serverSocket is not None:
                theport = self.serverSocket
                if self.configFileWriteOnce:
                    theConfigFile = -1;  # Do not write socket config file
                else:
                    theConfigFile = self.configFile
            else:
                theport = self.port;
                theConfigFile = self.configFile

            # Call MLEPCreate function
            [self.serverSocket, self.commSocket, status, msg, self.pid] = mlep.mlepCreate(self.program,self.arguments,self.workDir,self.acceptTimeout, theport, self.host, self.bcvtbDir, theConfigFile, self.env, self.execcmd)
        except:
            import traceback
            traceback.print_exc()
            raise Exception('Throw Error/Close Socket')

        # Return
        return(status, msg)

    # AcceptSocket
    #==============================================================
    def acceptSocket(self):
        # status and msg are returned from the client process
        # status = 0 --> success
        status = self.status
        msg = self.msg

        # Accept Socket
        (self.commSocket, clientAddress) = self.serverSocket.accept()

        # Create Streams
        if status == 0 and isinstance(self.commSocket,socket.socket):
            self.isRunning = True
            msg = ''

        # Return
        return (status,msg)

    # Stop
    #==============================================================
    def stop(self,stopSignal):
        # Not Running
        if not self.isRunning:
            return

        # Send stop signal
        if stopSignal:
            self.write(mlep.mlepEncodeStatus(self.version, 1))

        # Close connection
        self.serverSocket.close()

        # Update
        self.isRunning = False;
    
    # Read
    #==============================================================
    def read(self):
        # Read Packet
        if self.isRunning:
            packet = self.commSocket.recv(500)
        else:
            print('Co-simulation is not running.')

        # Return
        return(packet)

    # Write
    #==============================================================
    def write(self, packet):
        if self.isRunning:
            packet = packet.encode(encoding='UTF-8')
            self.commSocket.sendall(packet)
        else:
            print('Co-simulation is not running.')
