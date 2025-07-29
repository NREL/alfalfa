# start the measure
class AlfalfaSetpointControl < OpenStudio::Measure::EnergyPlusMeasure

  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Alfalfa Setpoint Control'
  end

  # human readable description
  def description
    return 'Add Setpoint Control to Alfalfa'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Add Setpoint Control to Alfalfa'
  end

  # define the arguments that the user will input
  def arguments(workspace)
    args = OpenStudio::Measure::OSArgumentVector.new

    return args
  end

  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)

    alfalfa = runner.alfalfa

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(workspace), user_arguments)
      return false
    end

    zone_control_thermostats = workspace.getObjectsByType('ZoneControl:Thermostat'.to_IddObjectType)
    thermostats_to_zones = {}

    zone_control_thermostats.each do |zone_control_thermostat|
      thermostat = zone_control_thermostat.getTarget(4)
      zone_object = zone_control_thermostat.getString(1).get
      next unless thermostat.is_initialized

      thermostat = thermostat.get
      if thermostats_to_zones.key? thermostat
        thermostats_to_zones[thermostat].append(zone_object)
      else
        thermostats_to_zones[thermostat] = [zone_object]
      end
    end

    schedules_to_zones = {}
    thermostats_to_zones.each do |thermostat, zone_list|
      thermostat.targets.each do |target|
        target_type = target.iddObject.type
        schedule = nil
        if target_type == 'Schedule:Compact'.to_IddObjectType
          schedule = target
        elsif target_type == 'Schedule:Day:Interval'.to_IddObjectType
          schedule = target
        elsif target_type == 'Schedule:Year'.to_IddObjectType
          schedule = target
        elsif target_type == 'Schedule:Constant'.to_IddObjectType
          schedule = target
        end
        next if schedule.nil?

        if schedules_to_zones.key? schedule
          schedules_to_zones[schedule] += zone_list
        else
          schedules_to_zones[schedule] = zone_list
        end
      end
    end

    schedules_to_zones.each do |schedule, zone_list|
      schedule_actuator = alfalfa.exposeActuator(schedule.name.get, schedule.idfObject.iddObject.type.valueDescription, "Schedule Value", schedule.name.get).get
      schedule_value_output = OpenStudio::Alfalfa::AlfalfaOutputVariable.new(schedule.name.get, "Schedule Value")
      schedule_actuator.setOutput(schedule_value_output)
    end

    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
