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

# start the measure
class ShedSignal < OpenStudio::Measure::ModelMeasure

  # human readable name
  def name
    return 'Load shed signal'
  end

  # human readable description
  def description
    return 'Add load shed signal variable for Alfalfa'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Add EMS global variables required by Alfalfa to represent a load shed signal'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new
    return args
  end

  def create_input(model, name, freq)

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
    ems_out_var.setName(name + "_EMS_Value")
    ems_out_var.setUpdateFrequency("SystemTimestep")

    # create reporting output variable of EMS output variable of global variable
    global_out_var = OpenStudio::Model::OutputVariable.new(
      ems_out_var.nameString(),
      model
    )
    global_out_var.setName(name + "_Value")
    global_out_var.setReportingFrequency(freq)
    global_out_var.setKeyValue("EMS")
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
    ems_out_var_enable.setName(name + "_Enable_EMS_Value")
    ems_out_var_enable.setUpdateFrequency("SystemTimestep")

    # create reporting output variable of EMS output variable of enable global variable
    global_out_var_enable = OpenStudio::Model::OutputVariable.new(
      ems_out_var_enable.nameString(),
      model
    )
    global_out_var_enable.setName(name + "_Enable_Value")
    global_out_var_enable.setReportingFrequency(freq)
    global_out_var_enable.setKeyValue("EMS")
    global_out_var_enable.setExportToBCVTB(true)

    # add EMS initialization program
    init_prgm = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
    init_prgm.setName("Init_" + name)
    init_prgm.addLine("SET #{name} = 0")

    # add initialization program calling manager
    init_prgm_mngr = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
    init_prgm_mngr.setName("Init " + name)
    init_prgm_mngr.setCallingPoint("BeginNewEnvironment")
    init_prgm_mngr.addProgram(init_prgm)

  end

  def create_output(model, var, key, name, freq)

    # create reporting output variable
    new_var = OpenStudio::Model::OutputVariable.new(
      var,
      model
    )
    new_var.setName(name)
    new_var.setReportingFrequency(freq)
    new_var.setKeyValue(key)
    new_var.setExportToBCVTB(true)

  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)

    # call the parent class method
    super(model, runner, user_arguments)

    # alfalfa inputs
    create_input(
      model,
      "ShedSignal",
      "Timestep"
    )

    # alfalfa outputs
    create_output(
      model,
      "Facility Total Purchased Electricity Energy",
      "Whole Building",
      "Electric Meter",
      "Timestep"
    )

    return true
  end

end

# register the measure to be used by the application
ShedSignal.new.registerWithApplication
