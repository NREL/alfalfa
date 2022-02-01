########################################################################################################################
#  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
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

import argparse
from datetime import datetime


def valid_date(s):
    """Raise error if datetime string not formatted correctly"""
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        msg = "Not a valid date: '{0}'".format(s)
        raise argparse.ArgumentTypeError(msg)


def step_sim_arg_parser():
    """Argument parser for both OSM and FMU step simulations"""
    parser = argparse.ArgumentParser()
    parser.add_argument('site_id', help="The _id attribute of the record stored in MongoDB")
    parser.add_argument('step_sim_type', help="The type of step simulation to perform.",
                        choices=['timescale', 'realtime', 'external_clock'])
    parser.add_argument('start_datetime')
    parser.add_argument('end_datetime')

    help_string = ('How quickly the model advances, represented as a '
                   'ratio between model_time:real_time.  1 means the '
                   'model advances 1 minute for every 1 minute in realtime, '
                   'while 5 means the model advances once every 12 seconds in realtime')
    parser.add_argument('--step_sim_value', type=int, choices=range(0, 20), help=help_string)
    args = parser.parse_args()
    if args.step_sim_type == 'timescale' and not args.step_sim_value:
        parser.error('--step_sim_value must be specified if step_sim_type is timescale')
    else:
        print(args)
        return args
