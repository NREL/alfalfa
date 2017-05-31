#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
mlepDecodePacket
~~~~~~~~~~~
MLEPDECODEPACKET Decode packet to data.
   [flag, timevalue, realvalues, intvalues, boolvalues] =
           mlepDecodePacket(packet)

   Decode a packet (a string) to data.  The packet format follows the
   BCVTB co-simulation communication protocol.

   Inputs:
       packet: the packet to be decoded (a string).

   Outputs:
       flag: an integer specifying the (status) flag. Refer to the BCVTB
                   protocol for allowed flag values.
       timevalue: a real value which is the current simulation time in
                   seconds.
       realvalues: a vector of received real value data.
       intvalues: a vector of received integer value data.
       boolvalues: a vector of received boolean value data.

       Each of the received data vector can be empty if there is no data
       of that type sent.

   See also:
       MLEPENCODEDATA, MLEPENCODEREALDATA, MLEPENCODESTATUS
See also:
	<a href="https://gaia.lbl.gov/bcvtb">BCVTB (hyperlink)</a>

Usage:
  >>> mlepProcess

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

Note: This function is based on the Matlab implementation for mlep. The original
files were written by Nghiem Truong and Willy Bernal  

:author: Willy Bernal Heredia
:copyright: (c) 2016 by The Alliance for Sustainable Energy
:license: BSD-3
"""
import string
import mlep

def mlepDecodePacket(packet):
  flag = 0
  timevalue = 0
  realvalues = 0
  intvalues = 0
  boolvalues = 0
  
  # Remove non-printable characters from packet
  packet = packet.decode("utf-8")
  
  # Convert packet string to a vector of numbers
  data = ()
  packetList = packet.split()
  for i in range(0,len(packetList)):
    try:
      if i < 5:
        data = data + (int(packetList[i]),)
      else:
        data = data + (float(packetList[i]),)
    except ValueError:
      raise InputError('mlepDecodePacket','Error while parsing packet: %s'%packet)
  
  # Check data
  datalen = len(data)
  if datalen < 2:
    raise InputError('mlepDecodePacket','Invalid packet format: length is only %d.'%datalen)
  
  # data(1) is version number
  if data[1] <= 2:
    # Get the flag number
    flag = data[1];
      
    realvalues = ()
    intvalues = ()
    boolvalues = ()

    # Read on
    if flag == 0:  
      if datalen < 5:
        print('Invalid packet: lacks lengths of data.')

      numReal = data[2]
      numInt = data[3]
      numBool = data[4]
      if 6 + numReal + numInt + numBool > datalen:
        print('Invalid packet: not enough data.')

      # Now read data to vectors
      timevalue = data[5]
      realvalues = data[6:6+numReal]
      intvalues = data[6+numReal:6+numReal+numInt]
      boolvalues = data[6+numReal+numInt:6+numReal+numInt+numBool]

    else:
      # Non-zero flag --> don't need to read on
      timevalue = ()
      
  else:
      print('Unsupported packet format version: %d'%data[0])

  # Return
  return (flag, timevalue, realvalues)
