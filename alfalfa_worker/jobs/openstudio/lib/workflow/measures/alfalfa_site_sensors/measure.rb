require 'alfalfa'
# start the measure
class AlfalfaSiteSensors < OpenStudio::Measure::EnergyPlusMeasure


  FuelMeter = Struct.new(:fuel, :adjustment_factor)

  include OpenStudio::Alfalfa::EnergyPlusMixin
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Alfalfa Site Sensors'
  end

  # human readable description
  def description
    return 'Add Site Sensors to Alfalfa'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Add Site Sensors to Alfalfa'
  end

  # define the arguments that the user will input
  def arguments(workspace)
    args = OpenStudio::Measure::OSArgumentVector.new

    return args
  end

  def create_output_meter(name, adjustment_factor=1)
    sensor_name = "#{create_ems_str(name)}_sensor"
    output_name = "#{create_ems_str(name)}_output"
    adjusted_name = "#{create_ems_str(name)}_sensor_adjusted"
    program_calling_manager_name = "#{create_ems_str(name)}_calling_point"
    program_name = "#{create_ems_str(name)}_program"

    new_meter_string = "
    Output:Meter,
      #{name};
    "
    new_meter_object = OpenStudio::IdfObject.load(new_meter_string).get
    @workspace.addObject(new_meter_object)

    new_sensor_string = "
    EnergyManagementSystem:Sensor,
      #{sensor_name},
      ,
      #{name};
    "
    new_sensor_object = OpenStudio::IdfObject.load(new_sensor_string).get
    @workspace.addObject(new_sensor_object)

    new_global_variable_string= "
    EnergyManagementSystem:GlobalVariable,
    #{adjusted_name};    !- Name
    "

    new_global_variable_object = OpenStudio::IdfObject.load(new_global_variable_string).get
    @workspace.addObject(new_global_variable_object)

    new_program_string = "
    EnergyManagementSystem:Program,
      #{program_name},           !- Name
      SET #{adjusted_name} = #{sensor_name}*#{adjustment_factor};
      "
    new_program_object = OpenStudio::IdfObject.load(new_program_string).get
    @workspace.addObject(new_program_object)

    new_calling_manager_string = "
    EnergyManagementSystem:ProgramCallingManager,
      #{program_calling_manager_name},          !- Name
      EndOfZoneTimestepAfterZoneReporting,    !- EnergyPlus Model Calling Point
      #{program_name};
      "
    new_calling_manager_object = OpenStudio::IdfObject.load(new_calling_manager_string).get
    @workspace.addObject(new_calling_manager_object)

    create_ems_output_variable(output_name, adjusted_name)
  end

  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(workspace), user_arguments)
      return false
    end

    fuels = [
      FuelMeter.new('Electricity', 1.0/60)
    ]

    fuels.each do |fuel|
      register_output(create_output_meter("#{fuel.fuel}:Facility", fuel.adjustment_factor)).display_name = "Whole Building #{fuel.fuel}"
    end

    report_inputs_outputs

    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
