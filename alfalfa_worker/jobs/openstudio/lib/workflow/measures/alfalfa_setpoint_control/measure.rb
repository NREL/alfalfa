require 'alfalfa'
# start the measure
class AlfalfaSetpointControl < OpenStudio::Measure::EnergyPlusMeasure

  include OpenStudio::Alfalfa::EnergyPlusMixin
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

  def create_schedule_actuator(target_schedule)
    schedule_name = target_schedule.name.get
    actuator_input = create_actuator(create_ems_str("#{schedule_name}_setpoint"), schedule_name, target_schedule.idfObject.iddObject.type.valueDescription, "Schedule Value", true)
    schedule_value_output = create_output_variable(schedule_name, "Schedule Value")
    actuator_input.echo = schedule_value_output
    return actuator_input, schedule_value_output
  end

  def control_thermostats
    zone_control_thermostats = @workspace.getObjectsByType('ZoneControl:Thermostat'.to_IddObjectType)
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
        target_type = get_idd_type(target)
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
      schedule_input, schedule_echo = create_schedule_actuator(schedule)
      zone_list.each do |zone|
        schedule_input.add_zone(zone)
        schedule_echo.add_zone(zone)
      end
      schedule_input.display_name = schedule.name.get
      register_input(schedule_input)
      register_output(schedule_echo)
    end
  end

  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(workspace), user_arguments)
      return false
    end

    control_thermostats

    report_inputs_outputs

    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaSetpointControl.new.registerWithApplication
