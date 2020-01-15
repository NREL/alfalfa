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
mlep_create: Create a new co-simulation instance.
This function creates a new co-simulation instance by starting a given
external simulation program (E+) in a separate process and establishing a
TCP/IP connection to it.  The simulation program must support the BCVTB
co-simulation protocol.

    Call syntax:
        [server_sock, sim_sock, status, msg, pid] = ...
            mlepCreate(program_name, arguments, work_dir, timeout, port,
            host, bcvtb_dir, config_file)

    Inputs:
        program_name:a nonempty string which is the name of the external
                    program.
        arguments:  a string or a cell array of strings which are the
                    arguments to the external program.
        work_dir:   a string which is the working directory of the simulation
                    program. If it is empty or is omitted, the current
                    directory will be used. The system will change to this
                    directory before executing the external program. The
                    socket configuration file will also be written to this
                    directory by default, so the current user should have
                    write permission to this directory.
        timeout:    connection time-out, in milliseconds (10000 by default).
        port:       port number of the server socket for listening to incoming
                    connections; if 0 then any available port will be used;
                    if a ServerSocket java object and it is not closed then
                    that socket will be reused.
        host:       a string which is the host address or name. If it is
                    omitted or empty, the localhost will be used and the
                    socket config file will contain the host name;
                    otherwise, this host address/name will be used and be
                    written to the socket config file.
        bcvtb_dir:  the directory of BCVTB, which contains the bcvtb library
                    that the client may need to use. By default, it is the
                    current directory.
        config_file:an optional string that specifies the socket config
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
        exe_cmd:     how to execute external processes (E+) from Matlab; one
                    of the following text values:
                    'system'  - Use the standard Matlab's system function
                    'java'    - Use Java

    Outputs:
        server_sock:server socket ID/object.
        sim_sock:   the socket of the connection to the external program.
                    This value must be saved to use in other functions.
        status:     status returned by the external program: 0 if
                    successful, !=0 if error.
        msg:        string message returned by the external program.
        pid:        process ID of the external program (not used now but
                    may be needed later).

    When the co-simulation finishes, the sockets should be closed (e.g. by
    calling mlepClose).

    This function will throw an error if an error happened (e.g. the
    external program could not be started).  In this case, both sockets
    should be empty.  However, if either of them is non-empty, it needs to
    be closed.

    See also:
        <a href="https://gaia.lbl.gov/bcvtb">BCVTB (hyperlink)</a>

    Note: This function is based on the Matlab implementation for mlep. The original
    files were written by Nghiem Truong and Willy Bernal

:author: Willy Bernal Heredia
:copyright: (c) 2016 by The Alliance for Sustainable Energy
:license: BSD-3
"""
import subprocess
import os
import numbers
import socket
from socket import gethostbyname, gethostname


def mlep_create(program_name, arguments, work_dir, timeout, port, host, bcvtb_dir, config_file, env, exe_cmd):
    # Program Name
    if program_name is None:
        program_name = 'runnergyplus'

    # Environment Variable
    if env is None:
        env = {'BCVTB_HOME': bcvtb_dir}

    # Exec command by default is 'system'
    if exe_cmd is None:
        exe_cmd = 'subprocess'

    # Save current directory and change directory if necessary
    if work_dir is not None:
        os.getcwd()
        os.chdir(work_dir)
    # Get the correct directory
    work_dir = os.getcwd()

    # If port is a ServerSocket java object then re-use it
    if isinstance(port, socket.socket):
        if port._closed:
            port = 0  # Create a new socket
        else:
            server_sock = port

    # Port
    if port is None:
        port = 0

    # Create server socket if necessary
    if isinstance(port, numbers.Number):
        # Create a TCP/IP socket
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Check host
        if host is None:
            # Check
            host = '127.0.0.1'

        # Bind the socket to the port
        server_sock.bind((host, port))
        # Listen for incoming connections
        server_sock.listen(1)
        port = server_sock.getsockname()[1]
        server_address = ('127.0.0.1', port)
        print('Server started on %s:%s' % server_address)
        # Host name
    else:
        gethostbyname(gethostname())

    # Set Timeout
    server_sock.settimeout(timeout / 1000)

    # Write socket config file if necessary (configfile ~= -1)
    if config_file != -1:
        fid = open(config_file, 'w')
        if fid == -1:
            # error
            server_sock.close()
            server_sock = None
            print('Error while creating socket config file: %s').format(fid)

        else:
            # Write socket config to file
            if not isinstance(port, numbers.Number):
                port_number = port.getsockname()[1]
            else:
                port_number = port

            socket_config = ['<?xml version="1.0" encoding="ISO-8859-1"?>\n', '<BCVTB-client>\n', '<ipc>\n',
                             '<socket port="%d" hostname="%s"/>\n' % (port_number, host), '</ipc>\n', '</BCVTB-client>']
            try:
                fid.write(socket_config[0])
                fid.write(socket_config[1])
                fid.write(socket_config[2])
                fid.write(socket_config[3])
                fid.write(socket_config[4])
                fid.write(socket_config[5])

            except BaseException:
                print('Error while writing socket config file: %s', config_file)

        fid.close()
        print('Wrote socket.cfg')

    # Start Process
    status = start_process(program_name, arguments, env, work_dir)

    # Return
    sim_sock = None
    msg = 'msg'

    return [server_sock, sim_sock, status, msg]


def start_process(program_name, args, env, work_dir):
    """
    This function starts a new process of a given program in the
    background and returns the status and process ID.
    program_name: the command that will be executed
    args: arguments, either a string or a cell of strings
    env: environment variables, a dictionary that contains key-value pairs:
        + the first is the env variable name
        + the second is the value that will overwrite the current value.
    work_dir: working directory

    status: 0 if successful, != 0 if error (then status is error code)
    """

    # Set Variables
    cmd = [program_name]
    for kk in range(0, len(args)):
        cmd.append(args[kk])
    # print ("\n*** Yanfei *** cmd: ", cmd)
    # Process and set env variables
    for kk in range(0, len(env)):
        os.environ[list(env.keys())[kk]] = env[list(env.keys())[kk]]

    # Start Co-Simulation Program (Write to log file)
    fid_log = open('mlep.log', 'w')
    if os.name == 'nt':
        completed_process = subprocess.Popen(cmd, stdout=fid_log)
    else:
        print('Launch EnergyPlus')
        completed_process = subprocess.Popen(cmd, stdout=fid_log)

    # Status
    if completed_process is not None:
        status = 0
    else:
        status = 1

    # Return
    return status
