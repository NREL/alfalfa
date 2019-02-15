# -*- coding: utf-8 -*-
'''
Copyright: See the link for details: http://github.com/ibpsa/project1-boptest/blob/master/license.md
BOPTEST. Copyright (c) 2018 International Building Performance Simulation Association (IBPSA) and contributors. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

You are under no obligation whatsoever to provide any bug fixes, patches, or upgrades to the features, functionality or performance of the source code ("Enhancements") to anyone; however, if you choose to make your Enhancements available either publicly, or directly to its copyright holders, without imposing a separate written license agreement for such Enhancements, then you hereby grant the following license: a non-exclusive, royalty-free perpetual license to install, use, modify, prepare derivative works, incorporate into other computer software, distribute, and sublicense such enhancements or derivative works thereof, in binary and source code form.

Note: The license is a revised 3 clause BSD license with an ADDED paragraph at the end that makes it easy to accept improvements.       
           
'''

"""
This module defines the API to the test case used by the REST requests to 
perform functions such as advancing the simulation, retreiving test case 
information, and calculating and reporting results.

"""

from pyfmi import load_fmu
import numpy as np
import copy

class TestCase(object):
    '''Class that implements the test case.
    
    '''
    
    def __init__(self, config):
        '''Constructor.
        
        '''
        
        # Define simulation model
        self.fmupath = config['fmupath']
        # Load fmu
        self.fmu = load_fmu(self.fmupath)
        # Get version
        self.fmu_version = self.fmu.get_version()
        # Get available control inputs and outputs
        if self.fmu_version == '2.0':
            input_names = self.fmu.get_model_variables(causality = 2).keys()
            output_names = self.fmu.get_model_variables(causality = 3).keys()
        else:
            raise ValueError('FMU must be version 2.0.')
        # Define measurements
        self.y = {'time':[]}
        for key in output_names:
            self.y[key] = []
        self.y_store = copy.deepcopy(self.y)
        # Define inputs
        self.u = {'time':[]}
        for key in input_names:
            self.u[key] = []
        self.u_store = copy.deepcopy(self.u)
        # Set default options
        self.options = self.fmu.simulate_options()
        self.options['CVode_options']['rtol'] = 1e-6 
        # Set default communication step
        self.set_step(config['step'])
        # Set initial simulation start
        self.start_time = 0
        self.initialize = True
        self.options['initialize'] = self.initialize
        
    def advance(self,u):
        '''Advances the test case model simulation forward one step.
        
        Parameters
        ----------
        u : dict
            Defines the control input data to be used for the step.
            {<input_name> : <input_value>}
            
        Returns
        -------
        y : dict
            Contains the measurement data at the end of the step.
            {<measurement_name> : <measurement_value>}
            
        '''
        
        # Set final time
        self.final_time = self.start_time + self.step
        # Set control inputs if they exist
        if u.keys():
            u_list = []
            u_trajectory = self.start_time
            for key in u.keys():
                if key != 'time':
                    value = float(u[key])
                    u_list.append(key)
                    u_trajectory = np.vstack((u_trajectory, value))
            input_object = (u_list, np.transpose(u_trajectory))
        else:
            input_object = None
        # Simulate
        self.options['initialize'] = self.initialize
        res = self.fmu.simulate(start_time=self.start_time, 
                                final_time=self.final_time, 
                                options=self.options, 
                                input=input_object)
        # Get result and store measurement
        for key in self.y.keys():
            self.y[key] = res[key][-1]
            self.y_store[key] = self.y_store[key] + res[key].tolist()[1:]
        # Store control inputs
        for key in self.u.keys():
            self.u_store[key] = self.u_store[key] + res[key].tolist()[1:] 
        # Advance start time
        self.start_time = self.final_time
        # Prevent inialize
        self.initialize = False
        
        return self.y

    def reset(self):
        '''Reset the test.
        
        '''
        
        self.__init__()

    def get_step(self):
        '''Returns the current simulation step in seconds.'''

        return self.step

    def set_step(self,step):
        '''Sets the simulation step in seconds.
        
        Parameters
        ----------
        step : int
            Simulation step in seconds.
            
        Returns
        -------
        None
        
        '''
        
        self.step = float(step)
        
        return None
        
    def get_inputs(self):
        '''Returns a list of control input names.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        inputs : list
            List of control input names.
            
        '''

        inputs = self.u.keys()
        
        return inputs
        
    def get_measurements(self):
        '''Returns a list of measurement names.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        measurements : list
            List of measurement names.
            
        '''

        measurements = self.y.keys()
        
        return measurements
        
    def get_results(self):
        '''Returns measurement and control input trajectories.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        Y : dict
            Dictionary of measurement and control input names and their 
            trajectories as lists.
            {'y':{<measurement_name>:<measurement_trajectory>},
             'u':{<input_name>:<input_trajectory>}
            }
        
        '''
        
        Y = {'y':self.y_store, 'u':self.u_store}
        
        return Y
        
    def get_kpis(self):
        '''Returns KPI data.
        
        Requires standard sensor signals.
        
        Parameters
        ----------
        None
        
        Returns
        kpi : dict
            Dictionary containing KPI names and values.
            {<kpi_name>:<kpi_value>}
        
        '''
        
        kpi = dict()
        # Energy
        kpi['Heating Energy'] = self.y_store['ETotHea_y'][-1]
        # Comfort

        return kpi
        
    def get_name(self):
        '''Returns the name of the test case fmu.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        name : str
            Name of test case fmu.
            
        '''
        
        name = self.fmupath[7:-4]
        
        return name
