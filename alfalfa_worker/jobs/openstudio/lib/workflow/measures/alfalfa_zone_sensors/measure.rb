require 'alfalfa'
# start the measure
class AlfalfaZoneSensors < OpenStudio::Measure::EnergyPlusMeasure

  include OpenStudio::Alfalfa::EnergyPlusMixin
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    'Alfalfa Zone Sensors'
  end

  # human readable description
  def description
    'Add Zone Sensors to Alfalfa'
  end

  # human readable description of modeling approach
  def modeler_description
    'Add Zone Sensors to Alfalfa'
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
    return false unless runner.validateUserArguments(arguments(workspace), user_arguments)

    zones = workspace.getObjectsByType('Zone'.to_IddObjectType)
    zones.each do |zone|
      zone_name = zone.name.get
      mean_air_temperature_output = alfalfa_create_output_variable('Zone Mean Air Temperature', zone_name)
      mean_air_temperature_output.display_name = "#{zone_name} Air Temperature"
      mean_air_temperature_output.add_zone(zone_name)
      alfalfa_add_point(mean_air_temperature_output)

      air_relative_humidity_output = alfalfa_create_output_variable('Zone Air Relative Humidity', zone_name)
      air_relative_humidity_output.display_name = "#{zone_name} Humidity"
      air_relative_humidity_output.add_zone(zone_name)
      alfalfa_add_point(air_relative_humidity_output)

      zone_equip_connections = zone.getSources('ZoneHVAC:EquipmentConnections'.to_IddObjectType)

      zone_equip_connections.each do |zone_equip_connection|
        zone_air_node = zone_equip_connection.getString(4)
        setpoint_output = alfalfa_create_output_variable('System Node Setpoint Temperature', zone_air_node)
        setpoint_output.display_name = "#{zone_name} Temperature Setpoint"
        setpoint_output.add_zone(zone_name)
        alfalfa_add_point(setpoint_output)
      end
    end

    alfalfa_generate_reports

    runner.registerFinalCondition('Done')

    true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
