# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

require 'json'

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
    #initialize variables
    haystack_json = []
    num_economizers = 0
    airloops = []
    
    # Report initial condition of model
    #runner.registerInitialCondition("The building started with ") 
    
    #Site and WeatherFile Data
    if model.weatherFile.is_initialized 
      site_json = Hash.new
      weather_json = Hash.new
      
      wf = model.weatherFile.get
      building = model.getBuilding
      
      site_json[:id] = "@#{building.name.to_s}"
      site_json[:dis] = building.name.to_s
      site_json[:site] = "m:"
      site_json[:area] = building.floorArea
      site_json[:weatherRef] = "@#{wf.city}"
      site_json[:tz] = "#{wf.timeZone}"
      site_json[:geoCity] = wf.city
      site_json[:geoState] = wf.stateProvinceRegion
      site_json[:geoCountry] = wf.country
      site_json[:geoCoord] = "C(#{wf.latitude},#{wf.longitude})"
      haystack_json << site_json
      
      weather_json[:id] = "@#{wf.city}"
      weather_json[:dis] = wf.city
      weather_json[:weather] = "m:"
      weather_json[:tz] = "#{wf.timeZone}"
      weather_json[:geoCoord] = "C(#{wf.latitude},#{wf.longitude})"
      haystack_json << weather_json      
    end
    
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
      ahu_json = Hash.new
      ahu_json[:id] = "@#{airloop.name.to_s}"
      ahu_json[:dis] = airloop.name.to_s
      ahu_json[:ahu] = "m:"
      ahu_json[:hvac] = "m:"
      ahu_json[:equip] = "m:"
      ahu_json[:siteRef] = "@#{building.name.to_s}"
          
      supply_components = airloop.supplyComponents

      #find fan, cooling coil and heating coil on loop
      supply_components.each do |sc|
        #get economizer on outdoor air system
        if sc.to_AirLoopHVACOutdoorAirSystem.is_initialized
          sc = sc.to_AirLoopHVACOutdoorAirSystem.get
          #get ControllerOutdoorAir
          controller_oa = sc.getControllerOutdoorAir
          #mixed air node
          if sc.mixedAirModelObject.is_initialized
            mix_air_node = sc.mixedAirModelObject.get.to_Node.get
            runner.registerInfo("found mixed air node #{mix_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            mixed_json_temp = Hash.new
            mixed_json_temp[:id] = "@#{airloop.name.to_s}-mixed-air-temp-sensor"
            mixed_json_temp[:dis] = "#{airloop.name.to_s}-mixed-air-temp-sensor"
            mixed_json_temp[:siteRef] = "@#{building.name.to_s}"
            mixed_json_temp[:equipRef] = "@#{airloop.name.to_s}"
            mixed_json_temp[:point] = "m:"
            mixed_json_temp[:sensor] = "m:"
            mixed_json_temp[:temp] = "m:"   
            mixed_json_temp[:mixed] = "m:" 
            mixed_json_temp[:air] = "m:" 
            mixed_json_temp[:kind] = "Number" 
            mixed_json_temp[:unit] = "C" 
            haystack_json << mixed_json_temp  
            mixed_json_press = Hash.new
            mixed_json_press[:id] = "@#{airloop.name.to_s}-mixed-air-pressure-sensor"
            mixed_json_press[:dis] = "#{airloop.name.to_s}-mixed-air-pressure-sensor"
            mixed_json_press[:siteRef] = "@#{building.name.to_s}"
            mixed_json_press[:equipRef] = "@#{airloop.name.to_s}"
            mixed_json_press[:point] = "m:"
            mixed_json_press[:sensor] = "m:"
            mixed_json_press[:pressure] = "m:"   
            mixed_json_press[:mixed] = "m:" 
            mixed_json_press[:air] = "m:" 
            mixed_json_press[:kind] = "Number" 
            mixed_json_press[:unit] = "Pa" 
            haystack_json << mixed_json_press  
            mixed_json_humid = Hash.new
            mixed_json_humid[:id] = "@#{airloop.name.to_s}-mixed-air-humidity-sensor"
            mixed_json_humid[:dis] = "#{airloop.name.to_s}-mixed-air-humidity-sensor"
            mixed_json_humid[:siteRef] = "@#{building.name.to_s}"
            mixed_json_humid[:equipRef] = "@#{airloop.name.to_s}"
            mixed_json_humid[:point] = "m:"
            mixed_json_humid[:sensor] = "m:"
            mixed_json_humid[:pressure] = "m:"   
            mixed_json_humid[:mixed] = "m:" 
            mixed_json_humid[:air] = "m:" 
            mixed_json_humid[:kind] = "Number" 
            mixed_json_humid[:unit] = "%" 
            haystack_json << mixed_json_humid 
            mixed_json_flow = Hash.new
            mixed_json_flow[:id] = "@#{airloop.name.to_s}-mixed-air-flow-sensor"
            mixed_json_flow[:dis] = "#{airloop.name.to_s}-mixed-air-flow-sensor"
            mixed_json_flow[:siteRef] = "@#{building.name.to_s}"
            mixed_json_flow[:equipRef] = "@#{airloop.name.to_s}"
            mixed_json_flow[:point] = "m:"
            mixed_json_flow[:sensor] = "m:"
            mixed_json_flow[:flow] = "m:"   
            mixed_json_flow[:mixed] = "m:" 
            mixed_json_flow[:air] = "m:" 
            mixed_json_flow[:kind] = "Number" 
            mixed_json_flow[:unit] = "Kg/s"  
            haystack_json << mixed_json_flow
            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{mix_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly") 
            mix_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            mix_air_node_sensor.setKeyName(mix_air_node.handle.to_s)
            #mix_air_node_sensor.setName("#{mix_air_node.name.to_s} System Node Mass Flow Rate")      
            mix_air_node_sensor.setName("#{mix_air_node.name.to_s.gsub('-','_')} Sensor")                
          end          
          #outdoor air node
          if sc.outdoorAirModelObject.is_initialized
            outdoor_air_node = sc.outdoorAirModelObject.get.to_Node.get
            runner.registerInfo("found outdoor air node #{outdoor_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{outdoor_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly")
            outdoor_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            outdoor_air_node_sensor.setKeyName(outdoor_air_node.handle.to_s)
            #outdoor_air_node_sensor.setName("#{outdoor_air_node.name.to_s} System Node Mass Flow Rate") 
            outdoor_air_node_sensor.setName("#{outdoor_air_node.name.to_s.gsub('-','_')} Sensor")    
          end         
          #return air node
          if sc.returnAirModelObject.is_initialized
            return_air_node = sc.returnAirModelObject.get.to_Node.get
            runner.registerInfo("found return air node #{return_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{return_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly")
            return_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            return_air_node_sensor.setKeyName(return_air_node.handle.to_s)
            #return_air_node_sensor.setName("#{return_air_node.name.to_s} System Node Mass Flow Rate")  
            return_air_node_sensor.setName("#{return_air_node.name.to_s.gsub('-','_')} Sensor")    
          end        
          #relief air node
          if sc.reliefAirModelObject.is_initialized
            relief_air_node = sc.reliefAirModelObject.get.to_Node.get
            runner.registerInfo("found relief air node #{relief_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{relief_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly")
            relief_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            relief_air_node_sensor.setKeyName(relief_air_node.handle.to_s)
            #relief_air_node_sensor.setName("#{relief_air_node.name.to_s} System Node Mass Flow Rate") 
            relief_air_node_sensor.setName("#{relief_air_node.name.to_s.gsub('-','_')} Sensor")                
          end
          
          outdoor_air_fraction_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, "Air System Outdoor Air Flow Fraction")
          outdoor_air_fraction_sensor.setKeyName(airloop.handle.to_s)
          #outdoor_air_fraction_sensor.setName("#{airloop.name.to_s} Air System Outdoor Air Flow Fraction")
          outdoor_air_fraction_sensor.setName("#{airloop.name.to_s.gsub('-','_')} Sensor")    

          #add outputvariables for testing
          outputVariable = OpenStudio::Model::OutputVariable.new("Air System Outdoor Air Flow Fraction",model)
          outputVariable.setKeyValue("*")
          outputVariable.setReportingFrequency("hourly")
          
          outputVariable = OpenStudio::Model::OutputVariable.new("Air System Outdoor Air Mass Flow Rate",model)
          outputVariable.setKeyValue("*")
          outputVariable.setReportingFrequency("hourly")      

          oa_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
          oa_sensor.setKeyName(airloop.handle.to_s)
          oa_sensor.setName("#{sc.name.to_s.gsub('-','_')} Sensor")            

          #add EMS Actuator
          damper_actuator = OpenStudio::Model::EnergyManagementSystemActuator.new(controller_oa,"Outdoor Air Controller","Air Mass Flow Rate") 
          damper_actuator.setName("#{controller_oa.name.to_s.gsub('-','_')} Actuator")    
              
          program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
          program.setName("#{airloop.name.to_s.gsub('-','_')}_OutdoorAir_Prgm")   
          program.addLine("SET Temp = #{oa_sensor.handle.to_s}")
          program.addLine("SET Temp2 = #{mix_air_node_sensor.handle.to_s}")
          program.addLine("SET #{damper_actuator.handle.to_s} = 0.5*#{mix_air_node_sensor.handle.to_s}")

          pcm = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
          pcm.setName("#{airloop.name.to_s.gsub('-','_')}__OutdoorAir_Prgm_Mgr")
          pcm.setCallingPoint("AfterPredictorAfterHVACManagers")
          pcm.addProgram(program)
      
        #its a UnitarySystem so get sub components
        elsif sc.to_AirLoopHVACUnitarySystem.is_initialized
          sc = sc.to_AirLoopHVACUnitarySystem.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:rooftop] = "m:"
          fan = sc.supplyFan
          if fan.is_initialized
            if fan.get.to_FanVariableVolume.is_initialized
              runner.registerInfo("found VAV #{fan.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:variableVolume] = "m:"
              fan_json = Hash.new
              fan_json[:id] = "@#{fan.get.name.to_s}"
              fan_json[:dis] = "#{fan.get.name.to_s}"
              fan_json[:fan] = "m:"
              fan_json[:vfd] = "m:"
              fan_json[:variableVolume] = "m:"
              fan_json[:equip] = "m:"
              fan_json[:equipRef] = "@#{airloop.name.to_s}"
              fan_json[:siteRef] = "@#{building.name.to_s}"
              haystack_json << fan_json
            else
              runner.registerInfo("found CAV #{fan.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:constantVolume] = "m:"
              fan_json = Hash.new
              fan_json[:id] = "@#{fan.get.name.to_s}"
              fan_json[:dis] = "#{fan.get.name.to_s}"
              fan_json[:fan] = "m:"
              fan_json[:constantVolume] = "m:"
              fan_json[:equip] = "m:"
              fan_json[:equipRef] = "@#{airloop.name.to_s}"
              fan_json[:siteRef] = "@#{building.name.to_s}"
              haystack_json << fan_json
            end
          end
          cc = sc.coolingCoil
          if cc.is_initialized
            if cc.get.to_CoilCoolingWater.is_initialized || cc.get.to_CoilCoolingWaterToAirHeatPumpEquationFit.is_initialized
              runner.registerInfo("found WATER #{cc.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:chilledWaterCool] = "m:"
              if cc.get.plantLoop.is_initialized
                pl = cc.get.plantLoop.get
                ahu_json[:chilledWaterPlantRef] = "@#{pl.name.to_s}"
              end
              if cc.get.to_CoilCoolingWaterToAirHeatPumpEquationFit.is_initialized
                ahu_json[:heatPump] = "m:"
              end
            else
              runner.registerInfo("found DX #{cc.get.name.to_s} on airloop #{airloop.name.to_s}")   
              ahu_json[:dxCool] = "m:"              
            end
          end
          hc = sc.heatingCoil
          if hc.is_initialized
            if hc.get.to_CoilHeatingElectric.is_initialized
              runner.registerInfo("found ELECTRIC #{hc.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:elecHeat] = "m:"
            elsif hc.get.to_CoilHeatingGas.is_initialized
              runner.registerInfo("found GAS #{hc.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:gasHeat] = "m:"
            elsif hc.get.to_CoilHeatingWater.is_initialized || hc.get.to_CoilHeatingWaterToAirHeatPumpEquationFit.is_initialized
              runner.registerInfo("found WATER #{hc.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:hotWaterHeat] = "m:"
              if hc.get.plantLoop.is_initialized
                pl = hc.get.plantLoop.get
                ahu_json[:hotWaterPlantRef] = "@#{pl.name.to_s}"
              end
              if hc.get.to_CoilHeatingWaterToAirHeatPumpEquationFit.is_initialized
                ahu_json[:heatPump] = "m:"
              end
            end
          end
        #END UnitarySystem  
        elsif sc.to_FanConstantVolume.is_initialized
          sc = sc.to_FanConstantVolume.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:constantVolume] = "m:"
          fan_json = Hash.new
          fan_json[:id] = "@#{sc.name.to_s}"
          fan_json[:dis] = "#{sc.name.to_s}"
          fan_json[:fan] = "m:"
          fan_json[:constantVolume] = "m:"
          fan_json[:equip] = "m:"
          fan_json[:equipRef] = "@#{airloop.name.to_s}"
          fan_json[:siteRef] = "@#{building.name.to_s}"
          haystack_json << fan_json
        elsif sc.to_FanVariableVolume.is_initialized
          sc = sc.to_FanVariableVolume.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:variableVolume] = "m:"
          fan_json = Hash.new
          fan_json[:id] = "@#{sc.name.to_s}"
          fan_json[:dis] = "#{sc.name.to_s}"
          fan_json[:fan] = "m:"
          fan_json[:vfd] = "m:"
          fan_json[:variableVolume] = "m:"
          fan_json[:equip] = "m:"
          fan_json[:equipRef] = "@#{airloop.name.to_s}"
          fan_json[:siteRef] = "@#{building.name.to_s}"
          haystack_json << fan_json
        elsif sc.to_FanOnOff.is_initialized
          sc = sc.to_FanOnOff.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:constantVolume] = "m:"
          fan_json = Hash.new
          fan_json[:id] = "@#{sc.name.to_s}"
          fan_json[:dis] = "#{sc.name.to_s}"
          fan_json[:fan] = "m:"
          fan_json[:constantVolume] = "m:"
          fan_json[:equip] = "m:"
          fan_json[:equipRef] = "@#{airloop.name.to_s}"
          fan_json[:siteRef] = "@#{building.name.to_s}"
          haystack_json << fan_json
        elsif sc.to_CoilCoolingWater.is_initialized
          sc = sc.to_CoilCoolingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:chilledWaterCool] = "m:"
          if sc.plantLoop.is_initialized
            pl = sc.plantLoop.get
            ahu_json[:chilledWaterPlantRef] = "@#{pl.name.to_s}"
          end
        elsif sc.to_CoilHeatingWater.is_initialized
          sc = sc.to_CoilHeatingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}") 
          ahu_json[:hotWaterHeat] = "m:"
          if sc.plantLoop.is_initialized
            pl = sc.plantLoop.get
            ahu_json[:hotWaterPlantRef] = "@#{pl.name.to_s}"
          end          
        elsif sc.to_CoilHeatingElectric.is_initialized
          sc = sc.to_CoilHeatingElectric.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")  
          ahu_json[:elecHeat] = "m:"          
        end

      end   #end supplycomponents
    
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
    end #end demandcomponents
    haystack_json << ahu_json
              
    end  #end airloops
      
    runner.registerFinalCondition("The building has #{num_economizers} economizers") 
    #write out the haystack json
    File.open("./report_haystack.json","w") do |f|
      f.write(haystack_json.to_json)
    end
 
    return true
 
  end #end the run method

end #end the measure

# register the measure to be used by the application
Haystack.new.registerWithApplication
