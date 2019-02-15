# -*- coding: utf-8 -*-
'''
Copyright: See the link for details: http://github.com/ibpsa/project1-boptest/blob/master/license.md
BOPTEST. Copyright (c) 2018 International Building Performance Simulation Association (IBPSA) and contributors. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
'''


import json

def obtain_id_siteref(jsonpath):
    '''
    Purpose: remove the r: from the site id in json file
    Inputs: json file path
    Returns: revised id string for site
    '''
    site_ref = ''
    with open(jsonpath) as json_file:
        data = json.load(json_file)
        for entity in data:
            if 'site' in entity:
                if entity['site'] == 'm:':
                    site_ref = entity['id'].replace('r:', '')
                    break

    return site_ref
