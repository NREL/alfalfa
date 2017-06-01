#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
mlepCreate
~~~~~~~~~~~
MLEPCREATE Create a new co-simulation instance.
This function creates a new co-simulation instance by starting a given
external simulation program (E+) in a separate process and establishing a
TCP/IP connection to it.  The simulation program must support the BCVTB
co-simulation protocol.

   Call syntax:
       [serversock, simsock, status, msg, pid] = ...
           mlepCreate(progname, arguments, workdir, timeout, port,
                       host, bcvtbdir, configfile)

   Inputs:
       progname: a nonempty string which is the name of the external
                   program.
       arguments: a string or a cell array of strings which are the
                   arguments to the external program.
       workdir: a string which is the working directory of the simulation
                   program. If it is empty or is omitted, the current
                   directory will be used. The system will change to this
                   directory before executing the external program. The
                   socket configuration file will also be written to this
                   directory by default, so the current user should have
                   write permission to this directory.
       timeout: connection time-out, in milliseconds (10000 by default).
       port:    port number of the server socket for listening to incoming
                   connections; if 0 then any available port will be used;
                   if a ServerSocket java object and it is not closed then
                   that socket will be reused.
       host:    a string which is the host address or name. If it is
                   omitted or empty, the localhost will be used and the
                   socket config file will contain the host name;
                   otherwise, this host address/name will be used and be
                   written to the socket config file.
       bcvtbdir: the directory of BCVTB, which contains the bcvtb library
                   that the client may need to use. By default, it is the
                   current directory.
       configfile: an optional string that specifies the socket config
                   file.  By default, the config file is named
                   "socket.cfg" and is placed in the working directory.
                   If it is the number -1, the config file will not be
                   written (e.g. it is already there).
       env:        environment variables, a cell of cells, each contains
                   two or three strings:
                   + the first is the env variable name
                   + the second is the value if that env name does not
                     exist.
                   + the third is the value that will overwrite the
                     current value.
                   If the variable does not exist, it will be created
                   with the value of the second string.  If it exists and
                   the third string is provided, it will be overwritten
                   with this string; otherwise, it will keep its current
                   value.
       execcmd:    how to execute external processes (E+) from Matlab; one
                   of the following text values:
                   'system'  - Use the standard Matlab's system function
                   'java'    - Use Java

   Outputs:
       serversock: server socket ID/object.
       simsock:    the socket of the connection to the external program.
                   This value must be saved to use in other functions.
       status:     status returned by the external program: 0 if
                   successful, !=0 if error.
       msg:        string message returned by the external program.
       pid:        process ID of the external program (not used now but
                   may be needed later).

   When the cosimulation finishes, the sockets should be closed (e.g. by
   calling mlepClose).

   This function will throw an error if an error happened (e.g. the
   external program could not be started).  In this case, both sockets
   should be empty.  However, if either of them is non-empty, it needs to
   be closed.

   See also:
       <a href="https://gaia.lbl.gov/bcvtb">BCVTB (hyperlink)</a>
       MLEPCLOSE

   Note: This function is based on the Matlab implementation for mlep. The original
   files were written by Nghiem Truong and Willy Bernal

:author: Willy Bernal Heredia
:copyright: (c) 2016 by The Alliance for Sustainable Energy
:license: BSD-3
"""
#from subprocess import call
import subprocess
import os
import sys
import numbers
import socket

def mlepCreate (progname, arguments, workdir, timeout, port, host, bcvtbdir, configfile, env, execcmd):
  # Programe Name
  if progname is None:
    progname = 'runnergyplus'

  # Environment Variable
  if env is None:
    env = {'BCVTB_HOME':bcvtbdir}

  # Exec command by default is 'system'
  if execcmd is None:
    execcmd = 'subprocess'

  # Save current directory and change directory if necessary
  if workdir is not None:
    oldCurDir = os.getcwd()
    os.chdir(workdir)
  # Get the correct directory
  workdir = os.getcwd()  

  # If port is a ServerSocket java object then re-use it
  if isinstance(port,socket.socket):
    if port._closed:
      port = 0  # Create a new socket
    else:
      serversock = port
  
  # Port
  if port is None:
    port = 0

	# Create server socket if necessary
  if isinstance(port, numbers.Number):
    # Create a TCP/IP socket
    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Check host
    if host is None:
      # Check 
      host = '127.0.0.1'

    # Bind the socket to the port
    serversock.bind((host,port))
    # Listen for incoming connections
    serversock.listen(1)
    port = serversock.getsockname()[1]
    server_address = ('127.0.0.1', port)
    print('Server started on %s:%s' % server_address)
    # Hostname
    hostname = host
  else:
    hostname = port.gethostname()

  # Set Timeout
  serversock.settimeout(timeout/1000)

  # Write socket config file if necessary (configfile ~= -1)
  if configfile != -1:
    fid = open(configfile, 'w')
    if fid == -1:
        # error
        serversock.close();
        serversock = None;
        print('Error while creating socket config file: %s').format(fid)
    
    else:
      # Write socket config to file
      socket_config = ['<?xml version="1.0" encoding="ISO-8859-1"?>\n',
      '<BCVTB-client>\n',
      '<ipc>\n',
      '<socket port="%d" hostname="%s"/>\n' %(port, host),
      '</ipc>\n',
      '</BCVTB-client>']
      try:
        fid.write(socket_config[0])
        fid.write(socket_config[1])
        fid.write(socket_config[2])
        fid.write(socket_config[3])
        fid.write(socket_config[4])
        fid.write(socket_config[5])
        
      except:
        print('Error while writing socket config file: %s', femsg)
      
    fid.close()
    print('Wrote socket.cfg')

  # Start Process
  [status,pid] = startProcess(progname, arguments, env, workdir)

  # Return
  simsock = None
  msg = 'msg'
  status = 0
  pid = 0

  return [serversock, simsock, status, msg, pid]

def startProcess(progname, args, env, workdir):
  """
   This function starts a new process of a given program in the
   background and returns the status and process ID.
   progname: the command that will be executed
   args: arguments, either a string or a cell of strings
   env: environment variables, a dictionary that contains key-value pairs:
         + the first is the env variable name
         + the second is the value that will overwrite the current value.
   workdir: working directory

   status: 0 if successful, != 0 if error (then status is error code)
   (obsolete) msg: string message returned by the program (e.g. its standard output)
   pid: process ID/object; this ID is often not used but may be useful later.
  """
  # Set Variables
  cmd = [progname]
  for kk in range(0,len(args)):
    cmd.append(args[kk])

  # Process and set env variables
  for kk in range(0,len(env)):
    os.environ[list(env.keys())[kk]] = env[list(env.keys())[kk]]

  # Start Co-Simulation Program (Write to log file)
  fid_log = open('mlep.log','w')
  completedProcess = 1
  if os.name == 'nt':
    completedProcess = subprocess.Popen(cmd,stdout=fid_log)
  else:
    print('Launch EnergyPlus')
    completedProcess = subprocess.Popen(cmd,stdout=fid_log)
  
  # Status
  if completedProcess is None:
    status = 0
  else:
    status = 1

  # Not Used
  pid = 0

  # Return
  return [status, pid]
