#!/usr/bin/env python

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
