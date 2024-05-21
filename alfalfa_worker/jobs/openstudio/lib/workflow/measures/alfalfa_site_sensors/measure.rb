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
      alfalfa_add_meter("#{fuel}:Facility").display_name = "Whole Building #{fuel}"
    end

    alfalfa_generate_reports

    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
