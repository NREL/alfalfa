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
class ShedLights < OpenStudio::Measure::ModelMeasure

  # human readable name
  def name
    return 'Shed lights'
  end

  # human readable description
  def description
    return 'Shed lighting load'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Halve lighting schedule value at every timestep that the shed signal is true'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new
    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_args)

    # call the parent class method
    super(model, runner, user_args)

    # create array of light object
    light_schs = []

    # get all lights schedules in the model
    model.getLightss.each do |light|
      light_schs << light.schedule.get
    end

    # remove duplicate lighting schedules
    light_schs.uniq!

    # create array for light EMS objects
    light_ems_objs = []

    # add EMS sensor and actuator for each light schedule
    light_schs.each do |light_sch|

      # add EMS sensor
      light_sch_sen = OpenStudio::Model::EnergyManagementSystemSensor.new(
        model,
        'Schedule Value'
      )
      light_sch_sen.setName(light_sch.name.get.gsub(' ', '_').gsub('-','_') + '_Sen')
      light_sch_sen.setKeyName(light_sch.name.get)

      # add EMS actuator
      light_sch_act = OpenStudio::Model::EnergyManagementSystemActuator.new(
        light_sch,
        'Schedule:Year',
        'Schedule Value'
      )
      light_sch_act.setName(light_sch.name.get.gsub(' ', '_').gsub('-','_') + '_Act')

      # add EMS sensor and actuator to object array
      light_ems_objs << [light_sch_sen, light_sch_act]

    end

    # EMS program
    light_sch_prgm = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
    light_sch_prgm.setName('Shed_Lights')
    light_sch_prgm.addLine('SET load_shed = ShedSignal')

    # if shed load
    light_sch_prgm.addLine('IF load_shed == 1')

    # add code block for each sensor/actuator pair
    light_ems_objs.each do |light_ems_obj|
      light_sch_prgm.addLine("IF #{light_ems_obj[0].name} > 0.5")
      light_sch_prgm.addLine("SET #{light_ems_obj[1].name} = 0.5")
      light_sch_prgm.addLine('ELSE')
      light_sch_prgm.addLine("SET #{light_ems_obj[1].name} = NULL")
      light_sch_prgm.addLine('ENDIF')
    end

    # else if don't shed load
    light_sch_prgm.addLine('ELSEIF load_shed == 0')

    # set each actuator to null
    light_ems_objs.each do |light_ems_obj|
      light_sch_prgm.addLine("SET #{light_ems_obj[1].name} = NULL")
    end

    # end if shed load
    light_sch_prgm.addLine('ENDIF')

    # create EMS program calling manager and add EMS program
    light_sch_prgm_mngr = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
    light_sch_prgm_mngr.setName("Shed_Lights_Mngr")
    light_sch_prgm_mngr.setCallingPoint("BeginTimestepBeforePredictor")
    light_sch_prgm_mngr.addProgram(light_sch_prgm)

    return true

  end

end

# register the measure to be used by the application
ShedLights.new.registerWithApplication
