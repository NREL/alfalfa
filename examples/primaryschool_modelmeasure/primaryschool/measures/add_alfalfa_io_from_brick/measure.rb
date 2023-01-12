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
class AddAlfalfaIOFromBRICK < OpenStudio::Measure::ModelMeasure
    require 'openstudio-standards'
    require 'securerandom'
  
    # Define the name of the Measure.
    def name
      return 'Add IO for alfalfa from BRICK'
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
    def arguments(model)
      args = OpenStudio::Measure::OSArgumentVector.new
  
      #TODO
  
      return args
    end
  
    def find_points(ttlpath, runner)

        pypath = "#{File.join(File.dirname(__FILE__), "resources", "getpoints.py")}"
        pointnames = `python3 #{pypath} #{ttlpath}`
        pointnames = pointnames.tr('[]', '')
        pointnames = pointnames.split(',')
        runner.registerInfo("Found #{pointnames.length()} points in the EnergyPlus model")
        return pointnames.uniq
  
  
    end
  
    def create_output(model, var, key, name, freq, runner)

      # key = element ID
      # name = given name
      # var = measured quantity
      
      runner.registerInfo("Creating output for #{name}")


      if var == "Temperature"
        vartype = "System Node Temperature"
      else
        vartype = nil
      end
      # create reporting output variable
      new_var = OpenStudio::Model::OutputVariable.new(
        vartype, # from variable dictionary (eplusout.rdd)
        model
      )
      new_var.setName(name)
      new_var.setReportingFrequency(freq) # Detailed, Timestep, Hourly, Daily, Monthly, RunPeriod, Annual
      new_var.setKeyValue(key) # from variable dictionary (eplusout.rdd)
      new_var.setExportToBCVTB(true)
    
    end
  
    def create_input(model, name, freq, runner)

      runner.registerInfo("Creating input for #{name}")


      # create global variable
      global_var = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(
        model,
        name
      )
      global_var.setExportToBCVTB(true)
    
      # create EMS output variable of global variable
      ems_out_var = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(
        model,
        global_var
      )
      ems_out_var.setName(name + '_EMS_Value')
      ems_out_var.setUpdateFrequency('SystemTimestep')
    
      # create reporting output variable of EMS output variable of global variable
      global_out_var = OpenStudio::Model::OutputVariable.new(
        ems_out_var.nameString(),
        model
      )
      global_out_var.setName(name + '_Value')
      global_out_var.setReportingFrequency(freq) # Detailed, Timestep, Hourly, Daily, Monthly, RunPeriod, Annual
      global_out_var.setKeyValue('EMS')
      global_out_var.setExportToBCVTB(true)
    
      # create enable of global variable
      global_var_enable = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(
        model,
        name + "_Enable"
      )
      global_var_enable.setExportToBCVTB(true)
    
      # create EMS output variable of enable global variable
      ems_out_var_enable = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(
        model,
        global_var_enable
      )
      ems_out_var_enable.setName(name + '_Enable_EMS_Value')
      ems_out_var_enable.setUpdateFrequency('SystemTimestep')
    
      # create reporting output variable of EMS output variable of enable global variable
      global_out_var_enable = OpenStudio::Model::OutputVariable.new(
        ems_out_var_enable.nameString(),
        model
      )
      global_out_var_enable.setName(name + '_Enable_Value')
      global_out_var_enable.setReportingFrequency(freq) # Detailed, Timestep, Hourly, Daily, Monthly, RunPeriod, Annual
      global_out_var_enable.setKeyValue('EMS')
      global_out_var_enable.setExportToBCVTB(true)
    
    end

    def extract_graph(idf_file, runner)
      pypath = "#{File.join(File.dirname(__FILE__), "resources", "runparser.py")}"
      ttlpath = `python3 #{pypath} #{idf_file}`
      runner.registerInfo("Created BRICK model for #{idf_file}.")
      return idf_file.to_s.gsub('.idf', '.ttl')
    end

    def create_io(model, points, freq, runner)
      # TODO: replace Temperature key with actual key!
      points.each do |point|
        pointtype = "Unknown"
        if point.include? "_Setpoint"
          pointtype = "Setpoint"
          create_input(model, point.tr(" ", "_").tr("'", "").tr("-", "_").tr("\n", ""), freq, runner)
        elsif point.include? "_Sensor"
          pointtype = "Sensor"
          create_output(model, "Temperature", point.gsub("_Sensor", ""), point.tr(" ", "_").tr("'", "").tr("-", "_").tr("\n", ""), freq, runner)
        end
        runner.registerInfo("#{point} is a: #{pointtype}")
      end

    end
  
    def fixidf(path, runner)
      pypath = "#{File.join(File.dirname(__FILE__), "resources", "fixidf.py")}"
      ttlpath = `python3 #{pypath} #{path}`
      runner.registerInfo("Truncated IDF fields to 100 characters for #{path}.")
    end

    # Define what happens when the measure is run.
    def run(model, runner, user_arguments)
      super(model, runner, user_arguments)
        
      freq = 'TimeStep'

      # Use the built-in error checking
      if !runner.validateUserArguments(arguments(model), user_arguments)
        return false
      end

      # Generate graph
      temp_files = "#{File.dirname(__FILE__)}/resources/temp"
      if !Dir.exist?(temp_files)
        Dir.mkdir(temp_files)
      end

      # Make sure no names are too long
      #model.modelObjects.each do |mobj|
      #mobj.setName(SecureRandom.hex(10))
      #end

      temp_idf = File.join(temp_files, 'initial.idf')
      translator = OpenStudio::EnergyPlus::ForwardTranslator.new
      workspace = translator.translateModel(model)
      workspace.save(temp_idf, true)
      #fixidf(temp_idf, runner)
      ttlpath = extract_graph(temp_idf, runner)

      # Find all sensors and setpoints
      points = find_points(ttlpath, runner)
      create_io(model, points, freq, runner)

      temp_idf = File.join(temp_files, 'final.idf')
      workspace = translator.translateModel(model)
      workspace.save(temp_idf, true)
  
      return true
    end # end the run method

  end # end the measure
  
  # this allows the measure to be use by the application
  AddAlfalfaIOFromBRICK.new.registerWithApplication
  