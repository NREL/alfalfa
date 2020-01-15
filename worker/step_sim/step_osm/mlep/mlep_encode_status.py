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
mlep_encode_status Encode status flag to a packet.
   packet = mlepEncodeStatus(vernumber, flag)

   Encode a status flag to a packet (a string) that can be sent to the
   external program.  This function is a special version of
   mlepEncodeData in which only a flag (non-zero) is transferred.

   Inputs:
       vernumber: version of the protocol to be used. Currently, version 1
                   and 2 are supported.
       flag: an integer specifying the (status) flag. Refer to the BCVTB
                   protocol for allowed flag values.

   Output:
       packet is a string that contains the encoded data.

   See also:
       mlep_decode_packet.py, mlep_encode_data.py, mlep_encode_real_data.py

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


def mlep_encode_status(vernumber, flag):
    # Assemble packet
    if vernumber <= 2:
        packet = ('%d %d' % (vernumber, flag),)
        packet = ' '.join(packet) + ' \n'
    else:
        packet = ''

    # Return
    return packet
