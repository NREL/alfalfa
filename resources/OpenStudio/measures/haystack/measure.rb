# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class Haystack < OpenStudio::Ruleset::ModelUserScript

  # human readable name
  def name
    return "Haystack"
  end

  # human readable description
  def description
    return "This measure will find economizers on airloops and add haystack tags."
  end

  # human readable description of modeling approach
  def modeler_description
    return "This measure loops through the existing airloops, looking for loops that have outdoor airsystems with economizers"
  end
  

  #define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    return args
  end #end the arguments method

  #define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)
    
    # Use the built-in error checking 
    if not runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end
    
    num_economizers = 0
    airloops = []
    # Report initial condition of model
    #runner.registerInitialCondition("The building started with ") 
    
    #loop through air loops and find economizers
    model.getAirLoopHVACs.each do |airloop|
      supply_components = airloop.supplyComponents

      #find AirLoopHVACOutdoorAirSystem on loop
      supply_components.each do |supply_component|
        sc = supply_component.to_AirLoopHVACOutdoorAirSystem
        if sc.is_initialized
          sc = sc.get

          #get ControllerOutdoorAir
          controller_oa = sc.getControllerOutdoorAir

          #log initial economizer type
          if not controller_oa.getEconomizerControlType == "NoEconomizer"
            runner.registerInfo("found economizer on airloop #{airloop.name.to_s}")
            #puts "found economizer on airloop #{airloop.name.to_s}"
            num_economizers += 1
            airloops << airloop
          end
          
        end
      end
    end  

    #loop through economizer loops and find fans and cooling coils    
    airloops.each do |airloop|
      supply_components = airloop.supplyComponents

      #find fan, cooling coil and heating coil on loop
      supply_components.each do |sc|
        #its a unitary system so get sub components
        if sc.to_AirLoopHVACUnitarySystem.is_initialized
          sc = sc.to_AirLoopHVACUnitarySystem.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          fan = sc.supplyFan
          if fan.is_initialized
            runner.registerInfo("found #{fan.get.name.to_s} on airloop #{airloop.name.to_s}")
          end
          cc = sc.coolingCoil
          if cc.is_initialized
            runner.registerInfo("found #{cc.get.name.to_s} on airloop #{airloop.name.to_s}")
          end
          hc = sc.heatingCoil
          if hc.is_initialized
            runner.registerInfo("found #{hc.get.name.to_s} on airloop #{airloop.name.to_s}")
          end
        elsif sc.to_FanConstantVolume.is_initialized
          sc = sc.to_FanConstantVolume.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
        elsif sc.to_FanVariableVolume.is_initialized
          sc = sc.to_FanVariableVolume.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
        elsif sc.to_FanOnOff.is_initialized
          sc = sc.to_FanOnOff.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
        elsif sc.to_CoilCoolingWater.is_initialized
          sc = sc.to_CoilCoolingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
        elsif sc.to_CoilHeatingWater.is_initialized
          sc = sc.to_CoilHeatingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")  
        elsif sc.to_CoilHeatingElectric.is_initialized
          sc = sc.to_CoilHeatingElectric.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")           
        end

      end
    
    demand_components = airloop.demandComponents
    demand_components.each do |dc|
      if dc.to_ThermalZone.is_initialized
        dc = dc.to_ThermalZone.get
        if dc.thermostatSetpointDualSetpoint.is_initialized
          if dc.thermostatSetpointDualSetpoint.get.coolingSetpointTemperatureSchedule.is_initialized
            cool_thermostat = dc.thermostatSetpointDualSetpoint.get.coolingSetpointTemperatureSchedule.get
            runner.registerInfo("found #{cool_thermostat.name.to_s} on airloop #{airloop.name.to_s} in thermalzone #{dc.name.to_s}") 
          end
          if dc.thermostatSetpointDualSetpoint.get.heatingSetpointTemperatureSchedule.is_initialized
            heat_thermostat = dc.thermostatSetpointDualSetpoint.get.heatingSetpointTemperatureSchedule.get
            runner.registerInfo("found #{heat_thermostat.name.to_s} on airloop #{airloop.name.to_s} in thermalzone #{dc.name.to_s}") 
          end
        end
      end
    end
    end
      
    runner.registerFinalCondition("The building has #{num_economizers} economizers") 
   
    return true
 
  end #end the run method

end #end the measure

# register the measure to be used by the application
Haystack.new.registerWithApplication
