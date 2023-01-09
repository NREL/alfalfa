# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# (1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# (2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# (3) Neither the name of the copyright holder nor the names of any contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission from the respective party.
#
# (4) Other than as required in clauses (1) and (2), distributions in any form
# of modifications or other derivative works may not use the "OpenStudio"
# trademark, "OS", "os", or any other confusingly similar designation without
# specific prior written permission from Alliance for Sustainable Energy, LLC.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE
# UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF
# THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *******************************************************************************



# Start the measure
class AlfalfaBRICK < OpenStudio::Measure::EnergyPlusMeasure
    require 'openstudio-standards'
    require 'json'
    # require 'rdf/rdfxml'
    # require 'rdf/turtle'
    # require 'sparql/client'
  
    # Define the name of the Measure.
    def name
      return 'Add I/O for alfalfa from BRICK'
    end
  
    # Human readable description
    def description
      return 'This method adds inputs and outputs for Alfalfa and generates a metadata model that follows the BRICK ontology.'
    end
  
    # Human readable description of modeling approach
    def modeler_description
      return 'The OpenStudio workspace is saved to an IDF in a temporary folder. The measure calls a Python library that parses the IDF and infers the type of components and their parents/children. This information is recorded in a Turtle file using the BRICK ontology. This measure reads the Turtle file and assigns all the necessary input/output bindings for Alfalfa and the BCVTB and saves the new workspace.'
    end
  
    # Define the arguments that the user will input.
    def arguments(workspace)
      args = OpenStudio::Measure::OSArgumentVector.new
  
      #TODO
  
      return args
    end
  
    def find_points(ttlpath)

        pypath = "#{File.join(File.dirname(__FILE__), "resources", "getpoints.py")}"
        pointnames = `python3 #{pypath} #{ttlpath}`
        pointnames = pointnames.tr('[]', '')
        pointnames = pointnames.split(',')
        return pointnames.uniq
  
  
    end
  
    def create_output(workspace, nodename, freq)
        # create reporting output variable

        # Node temp:
        var = 'System Node Temperature'
        idfstrs = []
        #New Output:Variable
        outvar_str = "Output:Variable, #{nodename}, #{var}, #{freq};"

        #New ExternalInterface for BCVTB
        bcvtb_str = "
        ExternalInterface:Variable,
            #{nodename + "_y"}, !- Name
            0; !- Initial value 
        "
        idfstrs << outvar_str
        idfstrs << bcvtb_str

        idfstrs.each do |idfstr|
            idfObject = OpenStudio::IdfObject::load(idfstr)
            object = idfObject.get
            wsObject = workspace.addObject(object)
        end
  
    end
  
    def create_input(workspace, pointname, freq)
      

        strs = []
        # MAKE SURE THAT THE NAME HAS NO SPACES (assert?)
        pointname = pointname.gsub(' ', '')
        # Create global EMS variable
        global_var = "EnergyManagementSystem:GlobalVariable, #{pointname}; "
        strs << global_var
        bcvtb_global = "
        ExternalInterface:Variable,
            #{pointname}, !- Name
            0; !- Initial value 
        "
        strs << bcvtb_global
        # Create EMS output
        # CHECK FOR THE TYPE OF READING
        emsvar = pointname + '_EMS_Value'
        ems_out = "
        EnergyManagementSystem:OutputVariable,
            #{emsvar}, ! Name
            #{emsvar}, ! EMS Variable Name
            Averaged, ! Type of Data in Variable
            SystemTimeStep , ! Update Frequency
            ,           ! EMS Program or Subroutine Name
            C;    
        "
        strs << ems_out

        # Add an output var for the EMS output
        outvar_str = "Output:Variable, EMS, #{emsvar}, #{freq};"
        strs << outvar_str
        bcvtb_outvar = "
        ExternalInterface:Variable,
            #{pointname + '_Value'}, !- Name
            0; !- Initial value 
        "
        strs << bcvtb_outvar

        # Repeat for the enable values

        global_enable_var = "EnergyManagementSystem:GlobalVariable, #{pointname + '_Enable'}; "
        strs << global_enable_var
        bcvtb_global_enable = "
        ExternalInterface:Variable,
            #{pointname + '_Enable'}, !- Name
            0; !- Initial value 
        "
        strs << bcvtb_global_enable
        emsvar_enable = pointname + '_Enable_EMS_Value'
        ems_out_enable = "
        EnergyManagementSystem:OutputVariable,
            #{emsvar_enable}, ! Name
            #{emsvar_enable}, ! EMS Variable Name
            Averaged, ! Type of Data in Variable
            SystemTimeStep , ! Update Frequency
            ,           ! EMS Program or Subroutine Name
            C;    
        "
        strs << ems_out_enable
        outvar_str = "Output:Variable, EMS, #{emsvar_enable}, #{freq};"
        strs << outvar_str
        bcvtb_outvar = "
        ExternalInterface:Variable,
            #{pointname + '_Enable_Value'}, !- Name
            0; !- Initial value 
        "
        strs << bcvtb_outvar
        strs.each do |string_object|
          idfObject = OpenStudio::IdfObject::load(string_object)
          object = idfObject.get
          wsObject = workspace.addObject(object)
        end


  
    end

    def extract_graph(idf_file)
      pypath = "#{File.join(File.dirname(__FILE__), "resources", "runparser.py")}"
      ttlpath = `python3 #{pypath} #{idf_file}`
      return idf_file.to_s.gsub('.idf', '.ttl')
    end

    def create_io(workspace, points, freq)
      points.each do |point|
        if point.include? "_Setpoint"
          create_input(workspace, point.gsub("_Setpoint", ""), freq)
        elsif point.include? "_Sensor"
          create_output(workspace, point.gsub("_Sensor", ""), freq)
        end
      end

    end
  
    # Define what happens when the measure is run.
    def run(workspace, runner, user_arguments)
      super(workspace, runner, user_arguments)
        
      freq = 'TimeStep'

      # Use the built-in error checking
      if !runner.validateUserArguments(arguments(workspace), user_arguments)
        return false
      end

      # Generate graph
      temp_files = "#{File.dirname(__FILE__)}/resources/temp"
      if !Dir.exist?(temp_files)
        Dir.mkdir(temp_files)
      end

      temp_idf = File.join(temp_files, 'initial.idf')
      workspace.save(temp_idf, true)
      ttlpath = extract_graph(temp_idf)

      # Find all sensors and setpoints
      points = find_points(ttlpath)
      create_io(workspace, points, freq)

      temp_idf = File.join(temp_files, 'final.idf')
      workspace.save(temp_idf, true)
  
      return true
    end # end the run method

  end # end the measure
  
  # this allows the measure to be use by the application
  AlfalfaBRICK.new.registerWithApplication
  