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

require 'json'
require 'openstudio'
require 'rexml/document'
require 'alfalfa'
# start the measure
class ExportBCVTB < OpenStudio::Ruleset::ModelUserScript

  include OpenStudio::Alfalfa::OpenStudioMixin
  include OpenStudio::Alfalfa::Utils
  # human readable name
  def name
    return "ExportBCVTB"
  end

  # human readable description
  def description
    return "This measure will create the variables.cfg xml file for BCVTB"
  end

  # human readable description of modeling approach
  def modeler_description
    return "This measure loops through output_variables, EMS:output_variables and ExternalInterface objects and will create the variables.cfg xml file for BCVTB.
            Those variables need to be in cfg file, being used for data exchange."
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    return args
  end


  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # Use the built-in error checking
    if not runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # loop through output_variables
    output_variables = model.getOutputVariables
    output_variables = output_variables.sort_by { |m| [m.keyValue.to_s, m.name.to_s.downcase] }
    output_variables.each do |outvar|
      next if outvar.variableName.downcase.end_with? '_enable_value'

      register_output(outvar) if outvar.exportToBCVTB
    end

    # loop through ems_output_variables
    ems_output_variables = model.getEnergyManagementSystemOutputVariables
    # alphabetize
    ems_output_variables = ems_output_variables.sort_by { |m| m.name.to_s.downcase }
    ems_output_variables.each do |outvar|
      next unless outvar.exportToBCVTB
      next if outvar.emsVariableName.downcase.end_with? '_enable_value'

      register_output(outvar)
    end

    # find all EnergyManagementSystemGlobalVariable objects and
    # replace those that have exportToBCVTB set to true
    # We also have to swap handles in any ems programs
    ems_programs = model.getEnergyManagementSystemPrograms
    ems_subroutines = model.getEnergyManagementSystemSubroutines

    ems_globals = model.getEnergyManagementSystemGlobalVariables

    ems_globals.each do |emsvar|
      next unless emsvar.exportToBCVTB

      ems_global_name = emsvar.nameString
      ems_global_handle = emsvar.handle.to_s
      emsvar.remove

      eevar = OpenStudio::Model::ExternalInterfaceVariable.new(model, ems_global_name, 0)
      eevar_handle = eevar.handle.to_s

      ems_programs.each do |prog|
        body = prog.body
        body.gsub!(ems_global_handle, eevar_handle)
        prog.setBody(body)
      end

      ems_subroutines.each do |prog|
        body = prog.body
        body.gsub!(ems_global_handle, eevar_handle)
        prog.setBody(body)
      end

      ems_output_variables.each do |outvar|
        this_ems_var_name = outvar.emsVariableName
        outvar.setEMSVariableName(eevar_handle) if this_ems_var_name == ems_global_handle
      end
    end

    # loop through ExternalInterfaceVariables
    external_variables = model.getExternalInterfaceVariables
    # alphabetize
    external_variables = external_variables.sort_by { |m| m.name.to_s.downcase }
    external_variables.each_index do |index|
      outvar = external_variables[index]
      next unless outvar.exportToBCVTB

      var_name = outvar.name.to_s

      input_object = register_input(outvar)
      next unless index + 1 < external_variables.length

      next_variable = external_variables[index + 1]
      next_var_name = next_variable.name.to_s
      if next_var_name.start_with?(var_name) && next_var_name.gsub(var_name, '').downcase == '_enable'
        input_object.enable_variable = next_variable
        external_variables.delete_at(index + 1)
      end
    end

    # loop through ExternalInterfaceSchedule
    external_schedules = model.getExternalInterfaceSchedules
    # alphabetize
    external_schedules = external_schedules.sort_by { |m| m.name.to_s.downcase }
    external_schedules.each do |schedule|
      register_input(schedule) if schedule.exportToBCVTB
    end

    # loop through ExternalInterfaceActuators
    external_actuators = model.getExternalInterfaceActuators
    # alphabetize
    external_actuators = external_actuators.sort_by { |m| m.name.to_s.downcase }
    external_actuators.each do |actuator|
      register_input(actuator) if actuator.exportToBCVTB
    end

    @outputs.delete_if do |output|
      next unless output.component == 'EMS'

      variable_name = output.display_name
      if variable_name.downcase.end_with? '_value'
        variable_name = variable_name[0, variable_name.length - '_value'.length]
      end

      input_object = get_input_by_name(variable_name)
      input_object&.echo = output
      next unless input_object.nil?

      if variable_name.downcase.end_with? '_enable'
        variable_name = variable_name[0, variable_name.length - '_enable'.length]
      end

      input_object = get_input_by_name(variable_name)
      next if input_object.nil?

      true
    end

    report_inputs_outputs

    return true
  end
end
ExportBCVTB.new.registerWithApplication
