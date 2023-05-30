require 'alfalfa'
# start the measure
class AlfalfaSiteSensors < OpenStudio::Measure::EnergyPlusMeasure

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

  def create_output_meter(name)
    sensor_name = "#{create_ems_str(name)}_sensor"
    output_name = "#{create_ems_str(name)}_output"
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

    create_ems_output_variable(output_name, sensor_name)
  end

  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(workspace), user_arguments)
      return false
    end

    fuels = [
      'Electricity'
    ]

    fuels.each do |fuel|
      register_output(create_output_meter("#{fuel}:Facility")).display_name = "Whole Building #{fuel}"
    end

    report_inputs_outputs

    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
