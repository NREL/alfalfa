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
'''
mlep_parse_json Read json file with inputs and outputs. Need to extract the order for both.
Creates a list of inputs and outputs.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
'''
import json


def mlep_parse_json(filename):
    fid = open(filename, "r")
    json_string = fid.read()
    parsed_json = json.loads(json_string)

    # Initialize Variables
    inputs_num = 0
    outputs_num = 0
    inputs_list = list()
    outputs_list = list()

    # Loop
    for i in range(0, len(parsed_json)):
        if parsed_json[i]['source'] == 'EnergyPlus':
            outputs_dict = {key: parsed_json[i][key] for key in ('type', 'name', 'id')}
            outputs_list.append(outputs_dict['id'].replace('r:', ''))
            outputs_num += 1
        elif parsed_json[i]['source'] == 'Ptolemy':
            inputs_dict = {key: parsed_json[i][key] for key in ('variable', 'id')}
            inputs_list.append(inputs_dict['id'].replace('r:', ''))
            inputs_num += 1

    return [outputs_list, inputs_list]
