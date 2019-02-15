# -*- coding: utf-8 -*-
'''
Copyright: See the link for details: http://github.com/ibpsa/project1-boptest/blob/master/license.md
BOPTEST. Copyright (c) 2018 International Building Performance Simulation Association (IBPSA) and contributors. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
'''

import tarfile


def make_gzip_file(site_ref, folderpath):
    '''
    Purpose: make a new gzipped file with desired inputs
    Inputs: site_ref --- the uuid to be added to the gzip filename
            folderpath   --- the folderpath where to add the new gzip file
    Outputs: a gzip file, for examle, d0f1cc38-764f-4655-870b-c74d80567986.tar.gz 
    '''
    # Open the json file and get a site reference
    # Store the results by site ref
    def reset(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        #print ("))))))(((((: tarinfo: ", tarinfo)
        #print ("))))))tar uid: ", tarinfo.uid)
        #print ("))))))tar uname: ", tarinfo.uname)
        return tarinfo

    tarname = "%s.tar.gz" % site_ref
    tar = tarfile.open(tarname, "w:gz")
    tar.add(folderpath, filter=reset, arcname=site_ref)
    tar.close()
   
    return tarname
    
