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
    require 'git'
  
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
  
    def find_points(ttlpath, s, p, o, runner)

        pypath = "#{File.join(File.dirname(__FILE__), "resources", "getpoints.py")}"
        #pointnames = `python3 #{pypath} #{ttlpath}`
        res = `python3 #{pypath} #{ttlpath} #{s} #{p} #{o}`
        res = res
        res = res.split(',')
        res.reject! { |c| c.empty? }
        #res.each_slice(3).to_a
        #puts res
        pnames = Array.new
        i = 0
        res.each do |point|
          #puts point[0]
          if i % 3 == 0
            pnames << point.gsub(/[\[\]\']*/, '').lstrip.rstrip 
            #puts point.gsub(/[\[\]']*/, '').lstrip.rstrip 
          end
          i += 1
        end  
        #puts pnames 
        return pnames.reject { |c| c.empty? }
        # res = res.split('] [')
        # keys = res[0].tr('[]\'', '')
        # keys = keys.split(',')
        # nkeys = Array.new
        # keys.each do |key|
        #   nkeys << key.lstrip
        # end
        # vars = res[1].tr('[]\'', '')
        # vars = vars.split(',')
        # nvars = Array.new
        # vars.each do |var|
        #   nvars << fvar = var.lstrip
        # end
        # runner.registerInfo("Found #{keys.length()} points in the EnergyPlus model")
        # return nkeys, nvars
  
  
    end
  
    def create_output(model, var, key, freq, runner)

      # key = element ID
      # name = given name
      # var = measured quantity
      
      runner.registerInfo("Creating output for #{name}")

      # Supported BRICK sensors:
      # Temperature_Sensor
      # Pressure_Sensor
      # Humidity_Sensor
      # Air_Flow_Sensor
      # Enthalpy_Sensor
      
      if var == "Humidity_Sensor"
        vartype = "System Node Humidity Ratio"
      elsif var == "Air_Flow_Sensor"
        vartype = "System Node Standard Density Volume Flow Rate"
      elsif var == "Zone_Air_Temperature_Sensor"
        vartype = "Zone Air Temperature"
      elsif var == "Zone_Air_Humidity_Sensor"
        vartype = "Zone Air Humidity Ratio"
      elsif ["Temperature_Sensor", "Pressure_Sensor", "Enthalpy_Sensor"].include? var
        vartype = "System Node #{var.gsub('_Sensor', '')}"
      end
      fkey = key.gsub("_#{var}", "")
      outname = key.gsub("_#{var}", " #{var.tr('_', ' ')}")

      # puts key
      # puts var
      # puts vartype
      # puts fkey
      # puts outname
      # create reporting output variable
      new_var = OpenStudio::Model::OutputVariable.new(
        vartype, # from variable dictionary (eplusout.rdd)
        model
      )
      new_var.setName(outname)

      nfkey = model.getModelObjectsByName(fkey, exactMatch=false)
      new_var.setReportingFrequency(freq) # Detailed, Timestep, Hourly, Daily, Monthly, RunPeriod, Annual
      new_var.setKeyValue(fkey) # from variable dictionary (eplusout.rdd)
      #new_var.setKeyValue(key)
      new_var.setExportToBCVTB(true)
      runner.registerInfo("#{key.tr('_', ' ')} has key #{fkey}")
    
    end
  
    def create_input(model, name, freq, runner)

      runner.registerInfo("Creating input for #{name}")


      if name.start_with?("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
        name = "V" + name
      end
      controlledvar = name.match(/_([^_]*)_Setpoint/)
      if controlledvar == nil
        controlledvar = ''
        cstr = ''
        componenttype = ""
      else
        controlledvar = controlledvar[1].tr('_', ' ')
      end

      if controlledvar == 'Flow'
        controlledvar = 'Mass Flow Rate Setpoint'
        cstr = 'Air_Flow_Setpoint'
        componenttype = "System Node Setpoint"
        initval = 0
      elsif controlledvar == 'Temperature'
        if name.include? 'Heating_Temperature_Setpoint'
          controlledvar = 'Heating Setpoint'
          cstr = 'Heating_Temperature_Setpoint'
          componenttype = 'Zone Temperature Control'
        elsif name.include? 'Cooling_Temperature_Setpoint'
          controlledvar = 'Cooling Setpoint'
          cstr = 'Cooling_Temperature_Setpoint'
          componenttype = 'Zone Temperature Control'
        else
          controlledvar = 'Temperature Setpoint'
          cstr = 'Temperature_Setpoint'
          componenttype = "System Node Setpoint"
        end
        initval = 15
      elsif controlledvar == 'Humidity'
        if name.include? 'Zone_Air_Humidity_Setpoint'
          controlledvar = 'Relative Humidity Dehumidifying Setpoint'
          cstr = 'Zone_Air_Humidity_Setpoint'
          componenttype = "Zone Humidity Control"
        else
          controlledvar = 'Humidity Ratio Setpoint'
          cstr = 'Humidity_Setpoint'
          componenttype = "System Node Setpoint"
        end 
        initval = 80
      end

      fname = name.gsub(/\W/, '_')

      componentname = name.gsub("_#{cstr}", '')
      comp = model.getModelObjectByName(componentname)
      #comp = model.getModelObjectByName(name)

      comp = comp.get
      # comp.emsActuatorNames().each do |actuator|

      # end

      # create global variable
      global_var = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(
        model,
        fname
      )
      global_var.setExportToBCVTB(true)
    
      # create EMS output variable of global variable
      ems_out_var = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(
        model,
        global_var
      )
      ems_out_var.setName(fname + '_EMS_Value')
      ems_out_var.setUpdateFrequency('SystemTimestep')
    
      # create reporting output variable of EMS output variable of global variable
      global_out_var = OpenStudio::Model::OutputVariable.new(
        ems_out_var.nameString(),
        model
      )
      global_out_var.setName(fname + '_Value')
      global_out_var.setReportingFrequency(freq) # Detailed, Timestep, Hourly, Daily, Monthly, RunPeriod, Annual
      global_out_var.setKeyValue('EMS')
      global_out_var.setExportToBCVTB(true)
    
      # create enable of global variable
      global_var_enable = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(
        model,
        fname + "_Enable"
      )
      global_var_enable.setExportToBCVTB(true)
    
      # create EMS output variable of enable global variable
      ems_out_var_enable = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(
        model,
        global_var_enable
      )
      ems_out_var_enable.setName(fname + '_Enable_EMS_Value')
      ems_out_var_enable.setUpdateFrequency('SystemTimestep')
    
      # create reporting output variable of EMS output variable of enable global variable
      global_out_var_enable = OpenStudio::Model::OutputVariable.new(
        ems_out_var_enable.nameString(),
        model
      )
      global_out_var_enable.setName(fname + '_Enable_Value')
      global_out_var_enable.setReportingFrequency(freq) # Detailed, Timestep, Hourly, Daily, Monthly, RunPeriod, Annual
      global_out_var_enable.setKeyValue('EMS')
      global_out_var_enable.setExportToBCVTB(true)

      actuator = OpenStudio::Model::EnergyManagementSystemActuator.new(
        comp,
        componenttype,
        controlledvar
      )

      # add EMS initialization program
      init_prgm = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
      init_prgm.setName('Init_' + fname)
      init_prgm.addLine("SET #{fname} = #{initval}")
      init_prgm.addLine("SET #{fname}_Enable = 0")

      # add EMS initialization program calling manager
      init_prgm_mngr = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
      init_prgm_mngr.setName('Init_' + fname)
      init_prgm_mngr.setCallingPoint('BeginNewEnvironment')
      init_prgm_mngr.addProgram(init_prgm)

      # add EMS program
      test_prgm = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
      test_prgm.setName('Override_' + fname)
      test_prgm.addLine("IF (#{fname}_Enable == 1)")
      test_prgm.addLine("SET #{actuator.name} = #{fname}")
      test_prgm.addLine("ELSE")
      test_prgm.addLine("SET #{actuator.name} = Null")
      test_prgm.addLine('ENDIF')

      # add EMS test program calling manager
      test_prgm_mngr = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
      test_prgm_mngr.setName(fname + '_Mgr')

      test_prgm_mngr.setCallingPoint('AfterPredictorAfterHVACManagers')#('InsideHVACSystemIterationLoop')
      test_prgm_mngr.addProgram(test_prgm)
    
    end

    def extract_graph(idf_file, runner)
      pypath = "#{File.join(File.dirname(__FILE__), "resources", "runparser.py")}"
      ttlpath = `python3 #{pypath} #{idf_file}`
      runner.registerInfo("Created BRICK model for #{idf_file}.")
      return idf_file.to_s.gsub('.idf', '.ttl')
    end

    def create_io(model, ttlpath, freq, runner)
      
      ### DEBUG ###
      output_EMS = model.getOutputEnergyManagementSystem
      output_EMS.setInternalVariableAvailabilityDictionaryReporting('Verbose')
      output_EMS.setEMSRuntimeLanguageDebugOutputLevel('Verbose')
      output_EMS.setActuatorAvailabilityDictionaryReporting('ErrorsOnly')
      ### /DEBUG ###


      supportedsen = ["Pressure_Sensor", "Air_Flow_Sensor", "Enthalpy_Sensor", "Zone_Air_Temperature_Sensor", "Zone_Air_Humidity_Sensor", "Humidity_Sensor", "Temperature_Sensor"]
      supportedstp = ["Humidity_Setpoint", "Air_Flow_Setpoint", "Temperature_Setpoint", "Heating_Temperature_Setpoint", "Cooling_Temperature_Setpoint"]#["AHU"]#["Fan", "Exhaust_Fan", "Heating_Coil"]#

      # TODO: Here, read from 2 json files:
      # the 1st one contains a list of brick types or equipment names that the user wants to control
      # the 2nd one contains a list of supported brick types
      # Compare the 2 lists.
      # All the items of list 1 that are supported are added as control points
      # Request these points through the BRICK script
      # if the points have actuators, return a list with modelObject.getEMSActuators()
      suppall = supportedsen + supportedstp
      suppall.each do |ptype|
        res = find_points(ttlpath, 'None', 'rdf:type', "brick:#{ptype}", runner)
        runner.registerInfo("Found #{res.length} points of type #{ptype}")
        if res.length > 0
          res.each do |point|
            puts point
            if supportedsen.include?(ptype)
              create_output(model, ptype, point, freq, runner)
            elsif supportedstp.include?(ptype)
              create_input(model, point, freq, runner)
            end
          end
        end
      end

      # keys.zip(vars).each do |key, var|
      #   puts key, var
      #   if key.include? "_Setpoint"
      #     supportedstp.each do |pointtype|
      #       if var.include? pointtype
      #         create_input(model, fixPythonFormat(key), freq, runner)
      #         runner.registerInfo("#{key} is a: #{pointtype.gsub('_', ' ')}")
      #         break
      #       end
      #     end
      #   elsif key.include? "_Sensor"
      #     supportedsen.each do |pointtype|
      #       if var.include? pointtype
      #         create_output(model, pointtype, fixPythonFormat(key), freq, runner)
      #         runner.registerInfo("#{key} is a: #{pointtype}")
      #         break
      #       end
      #     end
      #   end
        
      # end
    end

    def fixPythonFormat(name)
      return name.lstrip.gsub("'", "")
    end

    def formatname(name)
      return name.gsub("-", "tk#{'-'.ord()}").gsub("_", "tk#{'_'.ord()}").gsub(" ", "_").gsub("\n", "").gsub(".","tk#{'.'.ord()}")
    end

    def unformatname(name)
      return name.lstrip.gsub("_", " ").gsub("tk#{'-'.ord()}", "-").gsub("tk#{'.'.ord()}", ".").gsub("tk#{'_'.ord()}", "_")
    end

    # def getEp2brick():
    #   if !File.exists?('/alfalfa/ep2x'):
    #     Git.clone('https://github.com/NREL/ep2x.git', branch: 'development', path:'/alfalfa')

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
      #keys, vars = find_points(ttlpath, runner)
      create_io(model, ttlpath, freq, runner)#keys, vars, freq, runner)

      temp_idf = File.join(temp_files, 'final.idf')
      workspace = translator.translateModel(model)
      workspace.save(temp_idf, true)
  
      return true
    end # end the run method

  end # end the measure
  
  # this allows the measure to be use by the application
  AddAlfalfaIOFromBRICK.new.registerWithApplication
  