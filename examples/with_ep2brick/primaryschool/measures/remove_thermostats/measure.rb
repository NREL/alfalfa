# start the measure
class AlfalfaRemoveThermostats < OpenStudio::Measure::EnergyPlusMeasure

  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Alfalfa Remove Thermostats'
  end

  # human readable description
  def description
    return 'Remove thermostats from the IDF to allow low-level HVAC nodedsetpoint override.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Remove thermostats from the IDF to allow low-level HVAC nodedsetpoint override.'
  end

  # define the arguments that the user will input
  def arguments(workspace)
    args = OpenStudio::Measure::OSArgumentVector.new
    return args
  end

  def removeControls(workspace, runner)
    zone_control_thermostats = workspace.getObjectsByType('ZoneControl:Thermostat'.to_IddObjectType)
    thermostats_to_zones = {}

    zone_control_thermostats.each do |zone_control_thermostat|
      zone_control_thermostat.remove
      # schname = zone_control_thermostat.getString(2).get
      # #schname = thermostat.getString(0).get
      # #schtlname = thermostat.getString(1).get
      # runner.registerInfo("Replacing thermostat schedule: #{schname}")

      # schobj = workspace.getObjectsByName(schname)
      # schobj.each do |sch|
      #   sch.remove
      # end
      # newschtl = "
      # ScheduleTypeLimits,
      # #{schname} Type Limits, !- Name
      # 0,                                      !- Lower Limit Value {BasedOnField A3}
      # 4,                                      !- Upper Limit Value {BasedOnField A3}
      # DISCRETE;                               !- Numeric Type
      # "
      # tlidfObject = OpenStudio::IdfObject::load(newschtl)
      # tlobject = tlidfObject.get
      # tlwsObject = workspace.addObject(tlobject)
      # newsch =  "
      #   Schedule:Compact,
      #   #{schname}, !- Name
      #   #{schname} Type Limits, !- Schedule Type Limits Name
      #   Through: 12/31,                         !- Field 1
      #   For: AllDays,                           !- Field 2
      #   Until: 24:00,                           !- Field 3
      #   0;                                      !- Field 4
      #   "
      # idfObject = OpenStudio::IdfObject::load(newsch)
      # object = idfObject.get
      # wsObject = workspace.addObject(object)
      # zone_control_thermostat.setString(2, schname)
    end
    return workspace
  end


  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)
    # use the built-in error checking
    if !runner.validateUserArguments(arguments(workspace), user_arguments)
      return false
    end

    workspace = removeControls(workspace, runner)
    workspace.save('afterremoval.idf', true)
    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaRemoveThermostats.new.registerWithApplication