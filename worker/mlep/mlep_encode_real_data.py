#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
mlep_encode_real_data Encode real value data to packet.
   packet = mlepEncodeRealData(vernumber, flag, time_value, real_values)

   Encode real value data to a packet (a string) that can be sent to the
   external program.  This function is a special version of
   mlepEncodeData in which integer and boolean data does not exist.

   Inputs:
       vernumber: version of the protocol to be used. Currently, version 1
                   and 2 are supported.
       flag: an integer specifying the (status) flag. Refer to the BCVTB
                   protocol for allowed flag values.
       time_value: a real value which is the current simulation time in
                   seconds.
       real_values: a tuple of real value data to be sent. Can be empty.

   Output:
       packet is a string that contains the encoded data.

   See also:
       mlep_decode_packet.py, mlep_encode_data.py, mlep_encode_status.py

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


def mlep_encode_real_data (vernumber, flag, time_value, real_values):
    # Check Inputs
    if type(real_values) is not tuple:
        raise mlep.InputError('real_values', 'Real Value not a tuple')

    # Prepare Packet
    if vernumber <= 2:
        if flag == 0:
            real_values_string = ('%d 0 %d 0 0 %20.15e ' %(vernumber, len(real_values), time_value),)
            for i in range(0, len(real_values)):
                real_values_string = real_values_string + ('%20.15e'%real_values[i],)
                packet = ' '.join(real_values_string) + ' \n'
        else:
            # flag != 0
            packet = '%d %d ' % (vernumber, flag)
    else:
        packet = ''

    # Return
    return packet