# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# insert your copyright here
# Yanfei Li
# Yanfei.Li@nrel.gov
# Commercial Buildings Group


# start the measure
class ExposePowerVariable < OpenStudio::Measure::ModelMeasure

  # human readable name
  def name
    return "ExposePowerVariable"
  end

  # human readable description
  def description
    return "This measure will output the Facility:Electricity through EMS modules."
  end

  # human readable description of modeling approach
  def modeler_description
    return "EMS:GlobalVariable; EMS:Subroutine; EMS:Program; EMS:ProgramCallingManager; EMS:OutputVariable; and Output:Variable "
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # the name of the space to add to the model
    expose_power = OpenStudio::Measure::OSArgument.makeStringArgument('ExposePower', true)
    expose_power.setDisplayName('ExposePowerChoice?')
    expose_power.setDescription("Default=Yes")
    expose_power.setDefaultValue('Yes')
    args << expose_power

    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # assign the user inputs to variables
    expose_time_choices = runner.getStringArgumentValue('ExposePower', user_arguments)

    # check the expose_time_choices for reasonableness
    if expose_time_choices.empty?
      runner.registerError('Empty Expose_Power name was entered.')
      return false
    end

    # Add EMS-GlobalVariable
	ems_global_ele = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "ele")
	
        ems_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, "building_electricity_demand_power")	
	# Add EMS-Program
	ems_program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
	ems_program.setName("get_electricity")
	program_body="set ele = building_electricity_demand_power"
	ems_program.setBody(program_body)
	
	# Add EMS-CallingManager
	ems_program_calling_manager = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
	ems_program_calling_manager.addProgram(ems_program)
	ems_program_calling_manager.setName("callingpoint_main")
	ems_program_calling_manager.setCallingPoint("EndOfSystemTimestepAfterHVACReporting")
	
	# Add EMS-OutputVariable
	ems_output_variable_ele = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, ems_global_ele)
	ems_output_variable_ele.setName("ele_tot")
        ems_output_variable_ele.setEMSVariableName(ems_global_ele)
	ems_output_variable_ele.setTypeOfDataInVariable("Averaged")
	ems_output_variable_ele.setUpdateFrequency("SystemTimeStep")
        ems_output_variable_ele.setExportToBCVTB(true)
	
	
	
	

    return true

  end
  
end

# register the measure to be used by the application
ExposePowerVariable.new.registerWithApplication
