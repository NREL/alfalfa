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
mlep_decode_packet Decode packet to data.
   [flag, time_value, real_values, int_values, bool_values] =
           mlepDecodePacket(packet)

   Decode a packet (a string) to data.  The packet format follows the
   BCVTB co-simulation communication protocol.

   Inputs:
       packet: the packet to be decoded (a string).

   Outputs:
       flag: an integer specifying the (status) flag. Refer to the BCVTB
                   protocol for allowed flag values.
       time_value: a real value which is the current simulation time in
                   seconds.
       real_values: a vector of received real value data.
       int_values: a vector of received integer value data.
       bool_values: a vector of received boolean value data.

       Each of the received data vector can be empty if there is no data
       of that type sent.

   See also:
       mlep_encode_data.py, mlep_encode_real_data.py mlep_encode_status.py
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


def mlep_decode_packet(packet):
    flag = 0
    time_value = 0
    real_values = 0

    # Remove non-printable characters from packet
    packet = packet.decode("utf-8")

    # Convert packet string to a vector of numbers
    data = ()
    packet_list = packet.split()
    for i in range(0, len(packet_list)):
        try:
            if i < 5:
                data = data + (int(packet_list[i]),)
            else:
                data = data + (float(packet_list[i]),)
        except ValueError:
            raise mlep.InputError('mlepDecodePacket', 'Error while parsing packet: %s' % packet)

    # Check data
    data_len = len(data)
    if data_len < 2:
        raise mlep.InputError('mlepDecodePacket', 'Invalid packet format: length is only %d.' % data_len)

    # data(1) is version number
    if data[1] <= 2:
        # Get the flag number
        flag = data[1]

        real_values = ()

        # Read on
        if flag == 0:
            if data_len < 5:
                print('Invalid packet: lacks lengths of data.')

            numReal = data[2]
            numInt = data[3]
            numBool = data[4]
            if 6 + numReal + numInt + numBool > data_len:
                print('Invalid packet: not enough data.')

            # Now read data to vectors
            time_value = data[5]
            real_values = data[6:6 + numReal]

        else:
            # Non-zero flag --> don't need to read on
            time_value = ()

    else:
        print('Unsupported packet format version: %d' % data[0])

    # Return
    return flag, time_value, real_values
