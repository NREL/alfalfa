# start the measure
class AlfalfaZoneSensors < OpenStudio::Measure::EnergyPlusMeasure

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

    alfalfa = runner.alfalfa

    zones = workspace.getObjectsByType('Zone'.to_IddObjectType)
    zones.each do |zone|
      zone_name = zone.name.get
      alfalfa.exposeOutputVariable(zone_name, 'Zone Mean Air Temperature', "#{zone_name} Air Temperature")

      alfalfa.exposeOutputVariable(zone_name, 'Zone Air Relative Humidity', "#{zone_name} Humidity")

      zone_equip_connections = zone.getSources('ZoneHVAC:EquipmentConnections'.to_IddObjectType)

      zone_equip_connections.each do |zone_equip_connection|
        zone_air_node = zone_equip_connection.getString(4)

        alfalfa.exposeOutputVariable(zone_air_node.get, 'System Node Setpoint Temperature', "#{zone_name} Temperature Setpoint")
      end
    end

    runner.registerFinalCondition('Done')

    true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
