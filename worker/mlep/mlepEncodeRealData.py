#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
MLEPENCODEREALDATA Encode real value data to packet.
   packet = mlepEncodeRealData(vernumber, flag, timevalue, realvalues)

   Encode real value data to a packet (a string) that can be sent to the
   external program.  This function is a special version of
   mlepEncodeData in which integer and boolean data does not exist.

   Inputs:
       vernumber: version of the protocol to be used. Currently, version 1
                   and 2 are supported.
       flag: an integer specifying the (status) flag. Refer to the BCVTB
                   protocol for allowed flag values.
       timevalue: a real value which is the current simulation time in
                   seconds.
       realvalues: a tuple of real value data to be sent. Can be empty.

   Output:
       packet is a string that contains the encoded data.

   See also:
       MLEPDECODEPACKET, MLEPENCODEDATA, MLEPENCODESTATUS

   Note: This function is based on the Matlab implementation for mlep. The original
   files were written by Nghiem Truong and Willy Bernal

 Protocol Version 1 & 2:
 Packet has the form:
       v f dr di db t r1 r2 ... i1 i2 ... b1 b2 ...
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

 Note that if f is non-zero, other values after it will not be processed.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
"""
import os
import mlep

def mlepEncodeRealData (vernumber, flag, timevalue, realvalues):
  # Check Inputs
  if type(realvalues) is not tuple:
    raise InputError('realvalues','Real Value not a tuple')

  # Prepare Packet
  if vernumber <= 2:
    if flag == 0:
      realvaluesString = ('%d 0 %d 0 0 %20.15e ' %(vernumber, len(realvalues), timevalue),)
      for i in range(0,len(realvalues)):
        realvaluesString = realvaluesString + ('%20.15e'%realvalues[i],)
      packet = ' '.join(realvaluesString) + ' \n'
    else:
      # flag != 0
      packet = '%d %d'%(vernumber, flag)
  else:
    packet = ''

  # Return
  return(packet)
