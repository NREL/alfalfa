# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# insert your copyright here
# Yanfei Li
# Yanfei.Li@nrel.gov
# Commercial Buildings Group


# start the measure
class ExposeTimeVariable240 < OpenStudio::Measure::ModelMeasure

  # human readable name
  def name
    return "ExposeTimeVariable240"
  end

  # human readable description
  def description
    return "This measure will output the built-in variables through EMS modules."
  end

  # human readable description of modeling approach
  def modeler_description
    return "EMS:GlobalVariable; EMS:Subroutine; EMS:Program; EMS:ProgramCallingManager; EMS:OutputVariable; and Output:Variable "
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # the name of the space to add to the model
    expose_time_choices = OpenStudio::Measure::OSArgument.makeStringArgument('ExposeTime', true)
    expose_time_choices.setDisplayName('ExposeTimeChoice?')
    expose_time_choices.setDescription("Default=Yes")
	expose_time_choices.setDefaultValue('Yes')
    args << expose_time_choices

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
    expose_time_choices = runner.getStringArgumentValue('ExposeTime', user_arguments)

    # check the expose_time_choices for reasonableness
    if expose_time_choices.empty?
      runner.registerError('Empty expose_time_choices name was entered.')
      return false
    end

    # Add EMS-GlobalVariable
	ems_global_month = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "cur_month")
	ems_global_day = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "cur_day")
	ems_global_hour = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "cur_hour")
	ems_global_minute = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "cur_minute")
	
	# Add EMS-Subroutines-Month
	ems_subroutine_month = OpenStudio::Model::EnergyManagementSystemSubroutine.new(model)
	ems_subroutine_month.setName("set_Month")
	month_body = "set cur_month=Month"
	ems_subroutine_month.setBody(month_body)
	
	# Add EMS-Subroutines-Day
	ems_subroutine_day = OpenStudio::Model::EnergyManagementSystemSubroutine.new(model)
	ems_subroutine_day.setName("set_Day")
	month_body = "set cur_day=DayOfMonth"
	ems_subroutine_day.setBody(month_body)
	
	# Add EMS-Subroutines-hour
	ems_subroutine_hour = OpenStudio::Model::EnergyManagementSystemSubroutine.new(model)
	ems_subroutine_hour.setName("set_Hour")
	month_body = "set cur_hour=Hour"
	ems_subroutine_hour.setBody(month_body)
	
	# Add EMS-Subroutines-minute
	ems_subroutine_minute = OpenStudio::Model::EnergyManagementSystemSubroutine.new(model)
	ems_subroutine_minute.setName("set_Minute")
	month_body = "set cur_minute=Minute"
	ems_subroutine_minute.setBody(month_body)
	
	# Add EMS-Program
	ems_program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
	ems_program.setName("ems_main")
	program_body="run set_Month
	              run set_Day
				  run set_Hour
				  run set_Minute"
	ems_program.setBody(program_body)
	
	# Add EMS-CallingManager
	ems_program_calling_manager = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
	ems_program_calling_manager.addProgram(ems_program)
	ems_program_calling_manager.setName("callingpoint_main")
	ems_program_calling_manager.setCallingPoint("EndOfSystemTimestepAfterHVACReporting")
	
	# Add EMS-OutputVariable
	ems_output_variable_month = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, ems_global_month)
	ems_output_variable_month.setName("current_month")
        ems_output_variable_month.setEMSVariableName(ems_global_month)
	ems_output_variable_month.setTypeOfDataInVariable("Averaged")
	ems_output_variable_month.setUpdateFrequency("ZoneTimeStep")
        ems_output_variable_month.setExportToBCVTB(true)
	
	ems_output_variable_day = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, ems_global_day)
	ems_output_variable_day.setName("current_day")
        ems_output_variable_day.setEMSVariableName(ems_global_day)
	ems_output_variable_day.setTypeOfDataInVariable("Averaged")
	ems_output_variable_day.setUpdateFrequency("ZoneTimeStep")
        ems_output_variable_day.setExportToBCVTB(true)	

	ems_output_variable_hour = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, ems_global_hour)
	ems_output_variable_hour.setName("current_hour")
        ems_output_variable_hour.setEMSVariableName(ems_global_hour)
	ems_output_variable_hour.setTypeOfDataInVariable("Averaged")
	ems_output_variable_hour.setUpdateFrequency("ZoneTimeStep")
	ems_output_variable_hour.setExportToBCVTB(true)

	ems_output_variable_minute = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, ems_global_minute)
	ems_output_variable_minute.setName("current_minute")
        ems_output_variable_minute.setEMSVariableName(ems_global_minute)
	ems_output_variable_minute.setTypeOfDataInVariable("Averaged")
	ems_output_variable_minute.setUpdateFrequency("ZoneTimeStep")
        ems_output_variable_minute.setExportToBCVTB(true)
	
	##Add the EMS:Output variables to the Output:Variables to output
	#output_variable_month = OpenStudio::Model::OutputVariable.new("current_month",model)
	#output_variable_month.setVariableName("current_month")
  #  output_variable_month.setKeyValue("*")
  #  output_variable_month.setReportingFrequency("TimeStep") 
	#output_variable_month.setExportToBCVTB(true)
	#
  #  
	#output_variable_day = OpenStudio::Model::OutputVariable.new("current_day",model)
	#output_variable_day.setVariableName("current_day")
  #  output_variable_day.setKeyValue("*")
  #  output_variable_day.setReportingFrequency("TimeStep")
	#output_variable_day.setExportToBCVTB(true)
	#
  #  
	#output_variable_hour = OpenStudio::Model::OutputVariable.new("current_hour",model)
	#output_variable_hour.setVariableName("current_hour")
  #  output_variable_hour.setKeyValue("*")
  #  output_variable_hour.setReportingFrequency("TimeStep")
	#output_variable_hour.setExportToBCVTB(true)
	#
  #  
	#output_variable_minute = OpenStudio::Model::OutputVariable.new("current_minute",model)
	#output_variable_minute.setVariableName("current_minute")
  #  output_variable_minute.setKeyValue("*")
  #  output_variable_minute.setReportingFrequency("TimeStep") 
	#output_variable_minute.setExportToBCVTB(true) 
	

    return true

  end
  
end

# register the measure to be used by the application
ExposeTimeVariable240.new.registerWithApplication
