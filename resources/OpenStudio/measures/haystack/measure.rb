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
  
  def create_ref(id)
    #return string formatted for Ref (ie, "r:xxxxx") with no spaces or '-'
    return "r:#{id.gsub(/[\s-]/,'_')}"
  end
  
  def create_str(str)
    #return string formatted for strings (ie, "s:xxxxx")
    return "s:#{str}"
  end
  
  def create_num(str)
    #return string formatted for numbers (ie, "n:xxxxx")
    return "n:#{str}"
  end
  
  def create_point(type, id, siteRef, equipRef, where,what,measurement,kind,unit)
    point_json = Hash.new
    point_json[:id] = create_ref(id)
    point_json[:dis] = create_str(id)
    point_json[:siteRef] = create_ref(siteRef)
    point_json[:equipRef] = create_ref(equipRef)
    point_json[:point] = "m:"
    point_json["#{type}"] = "m:"
    point_json["#{measurement}"] = "m:"   
    point_json["#{where}"] = "m:" 
    point_json["#{what}"] = "m:" 
    point_json[:kind] = create_str(kind) 
    point_json[:unit] = create_str(unit) 
    return point_json
  end
  
  def create_fan(id, siteRef, equipRef, variable)
    point_json = Hash.new
    point_json[:id] = create_ref(id)
    point_json[:dis] = create_str(id)
    point_json[:siteRef] = create_ref(siteRef)
    point_json[:equipRef] = create_ref(equipRef)
    point_json[:equip] = "m:"
    point_json[:fan] = "m:"
    if variable
      point_json[:vfd] = "m:"
      point_json[:variableVolume] = "m:"
    else
      point_json[:constantVolume] = "m:"
    end     
    return point_json
  end

  def create_ahu(id, siteRef)
    ahu_json = Hash.new
    ahu_json[:id] = create_ref(id)
    ahu_json[:dis] = create_str(id)
    ahu_json[:ahu] = "m:"
    ahu_json[:hvac] = "m:"
    ahu_json[:equip] = "m:"
    ahu_json[:siteRef] = create_ref(siteRef)
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
      
      site_json[:id] = create_ref(building.name.to_s)
      site_json[:dis] = create_str(building.name.to_s)
      site_json[:site] = "m:"
      site_json[:area] = create_num(building.floorArea)
      site_json[:weatherRef] = create_ref(wf.city)
      site_json[:tz] = create_num(wf.timeZone)
      site_json[:geoCity] = create_str(wf.city)
      site_json[:geoState] = create_str(wf.stateProvinceRegion)
      site_json[:geoCountry] = create_str(wf.country)
      site_json[:geoCoord] = "c:#{wf.latitude},#{wf.longitude}"
      haystack_json << site_json
            
      weather_json[:id] = create_ref(wf.city)
      weather_json[:dis] = wf.city
      weather_json[:weather] = "m:"
      weather_json[:tz] = create_num(wf.timeZone)
      weather_json[:geoCoord] = "c:#{wf.latitude},#{wf.longitude}"
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
      ahu_json[:id] = create_ref(airloop.name.to_s)
      ahu_json[:dis] = airloop.name.to_s
      ahu_json[:ahu] = "m:"
      ahu_json[:hvac] = "m:"
      ahu_json[:equip] = "m:"
      ahu_json[:siteRef] = create_ref(building.name.to_s)
      #AHU discharge sensors    
      discharge_node = airloop.supplyOutletNode
      #create sensor points
      haystack_json << create_point("sensor", "#{airloop.name.to_s} Discharge Air Temp Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "discharge", "air", "temp", "Number", "C")            
      haystack_json << create_point("sensor", "#{airloop.name.to_s} Discharge Air Pressure Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "discharge", "air", "pressure", "Number", "Pa")            
      haystack_json << create_point("sensor", "#{airloop.name.to_s} Discharge Air Humidity Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "discharge", "air", "humidity", "Number", "%")            
      haystack_json << create_point("sensor", "#{airloop.name.to_s} Discharge Air Flow Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "discharge", "air", "flow", "Number", "Kg/s")            

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
            #AHU mixed sensors
            mix_air_node = sc.mixedAirModelObject.get.to_Node.get
            runner.registerInfo("found mixed air node #{mix_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #create sensor points
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Mixed Air Temp Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "mixed", "air", "temp", "Number", "C")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Mixed Air Pressure Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "mixed", "air", "pressure", "Number", "Pa")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Mixed Air Humidity Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "mixed", "air", "humidity", "Number", "%")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Mixed Air Flow Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "mixed", "air", "flow", "Number", "Kg/s")            

            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{mix_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly") 
            mix_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            mix_air_node_sensor.setKeyName(mix_air_node.handle.to_s)
            #mix_air_node_sensor.setName("#{mix_air_node.name.to_s} System Node Mass Flow Rate")      
            mix_air_node_sensor.setName("#{mix_air_node.name.to_s.gsub(/[\s-]/,'_')}_Sensor")                
          end          
          #outdoor air node
          if sc.outdoorAirModelObject.is_initialized
            #AHU outside sensors
            outdoor_air_node = sc.outdoorAirModelObject.get.to_Node.get
            runner.registerInfo("found outdoor air node #{outdoor_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #create sensor points
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Outside Air Temp Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "outside", "air", "temp", "Number", "C")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Outside Air Pressure Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "outside", "air", "pressure", "Number", "Pa")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Outside Air Humidity Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "outside", "air", "humidity", "Number", "%")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Outside Air Flow Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "outside", "air", "flow", "Number", "Kg/s")            

            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{outdoor_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly")
            outdoor_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            outdoor_air_node_sensor.setKeyName(outdoor_air_node.handle.to_s)
            #outdoor_air_node_sensor.setName("#{outdoor_air_node.name.to_s} System Node Mass Flow Rate") 
            outdoor_air_node_sensor.setName("#{outdoor_air_node.name.to_s.gsub(/[\s-]/,'_')}_Sensor")    
          end         
          #return air node
          if sc.returnAirModelObject.is_initialized
            #AHU return sensors
            return_air_node = sc.returnAirModelObject.get.to_Node.get
            runner.registerInfo("found return air node #{return_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #create sensor points
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Return Air Temp Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "return", "air", "temp", "Number", "C")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Return Air Pressure Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "return", "air", "pressure", "Number", "Pa")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Return Air Humidity Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "return", "air", "humidity", "Number", "%")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Return Air Flow Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "return", "air", "flow", "Number", "Kg/s")            

            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{return_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly")
            return_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            return_air_node_sensor.setKeyName(return_air_node.handle.to_s)
            #return_air_node_sensor.setName("#{return_air_node.name.to_s} System Node Mass Flow Rate")  
            return_air_node_sensor.setName("#{return_air_node.name.to_s.gsub(/[\s-]/,'_')}_Sensor")    
          end        
          #relief air node
          if sc.reliefAirModelObject.is_initialized
            #AHU exhaust sensors
            relief_air_node = sc.reliefAirModelObject.get.to_Node.get
            runner.registerInfo("found relief air node #{relief_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #create sensor points
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Exhaust Air Temp Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "exhaust", "air", "temp", "Number", "C")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Exhaust Air Pressure Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "exhaust", "air", "pressure", "Number", "Pa")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Exhaust Air Humidity Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "exhaust", "air", "humidity", "Number", "%")            
            haystack_json << create_point("sensor", "#{airloop.name.to_s} Exhaust Air Flow Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "exhaust", "air", "flow", "Number", "Kg/s")            

            outputVariable = OpenStudio::Model::OutputVariable.new("System Node Mass Flow Rate",model)
            outputVariable.setKeyValue("#{relief_air_node.name.to_s}")
            outputVariable.setReportingFrequency("hourly")
            relief_air_node_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
            relief_air_node_sensor.setKeyName(relief_air_node.handle.to_s)
            #relief_air_node_sensor.setName("#{relief_air_node.name.to_s} System Node Mass Flow Rate") 
            relief_air_node_sensor.setName("#{relief_air_node.name.to_s.gsub(/[\s-]/,'_')}_Sensor")                
          end
          
          outdoor_air_fraction_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, "Air System Outdoor Air Flow Fraction")
          outdoor_air_fraction_sensor.setKeyName(airloop.handle.to_s)
          outdoor_air_fraction_sensor.setName("#{airloop.name.to_s.gsub(/[\s-]/,'_')}_Sensor")    

          #add outputvariables for testing
          outputVariable = OpenStudio::Model::OutputVariable.new("Air System Outdoor Air Flow Fraction",model)
          outputVariable.setKeyValue("*")
          outputVariable.setReportingFrequency("hourly")
          
          outputVariable = OpenStudio::Model::OutputVariable.new("Air System Outdoor Air Mass Flow Rate",model)
          outputVariable.setKeyValue("*")
          outputVariable.setReportingFrequency("hourly")      

          oa_sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
          oa_sensor.setKeyName(airloop.handle.to_s)
          oa_sensor.setName("#{sc.name.to_s.gsub(/[\s-]/,'_')}_Sensor")            

          #add EMS Actuator
          damper_actuator = OpenStudio::Model::EnergyManagementSystemActuator.new(controller_oa,"Outdoor Air Controller","Air Mass Flow Rate") 
          damper_actuator.setName("#{controller_oa.name.to_s.gsub(/[\s-]/,'_')}_Actuator")    
              
          program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
          program.setName("#{airloop.name.to_s.gsub(/[\s-]/,'_')}_OutdoorAir_Prgm")   
          program.addLine("SET Temp = #{oa_sensor.handle.to_s}")
          program.addLine("SET Temp2 = #{mix_air_node_sensor.handle.to_s}")
          #program.addLine("SET #{damper_actuator.handle.to_s} = 0.5*#{mix_air_node_sensor.handle.to_s}")

          pcm = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
          pcm.setName("#{airloop.name.to_s.gsub(/[\s-]/,'_')}__OutdoorAir_Prgm_Mgr")
          pcm.setCallingPoint("AfterPredictorAfterHVACManagers")
          pcm.addProgram(program)
      
        #its a UnitarySystem so get sub components
        elsif sc.to_AirLoopHVACUnitarySystem.is_initialized
          sc = sc.to_AirLoopHVACUnitarySystem.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:rooftop] = "m:"
          fan = sc.supplyFan
          if fan.is_initialized
            #AHU FAN equip
            if fan.get.to_FanVariableVolume.is_initialized
              runner.registerInfo("found VAV #{fan.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:variableVolume] = "m:"
              haystack_json << create_fan("#{fan.get.name.to_s}", "#{building.name.to_s}", "#{airloop.name.to_s}", true)
            else
              runner.registerInfo("found CAV #{fan.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:constantVolume] = "m:"
              haystack_json << create_fan("#{fan.get.name.to_s}", "#{building.name.to_s}", "#{airloop.name.to_s}", false)
            end
          end
          cc = sc.coolingCoil
          if cc.is_initialized
            if cc.get.to_CoilCoolingWater.is_initialized || cc.get.to_CoilCoolingWaterToAirHeatPumpEquationFit.is_initialized
              runner.registerInfo("found WATER #{cc.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:chilledWaterCool] = "m:"
              if cc.get.plantLoop.is_initialized
                pl = cc.get.plantLoop.get
                ahu_json[:chilledWaterPlantRef] = create_ref(pl.name.to_s)
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
                ahu_json[:hotWaterPlantRef] = create_ref(pl.name.to_s)
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
          haystack_json << create_fan("#{sc.name.to_s}", "#{building.name.to_s}", "#{airloop.name.to_s}", false)
        elsif sc.to_FanVariableVolume.is_initialized
          sc = sc.to_FanVariableVolume.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:variableVolume] = "m:"
          haystack_json << create_fan("#{sc.name.to_s}", "#{building.name.to_s}", "#{airloop.name.to_s}", true)
        elsif sc.to_FanOnOff.is_initialized
          sc = sc.to_FanOnOff.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:constantVolume] = "m:"
          haystack_json << create_fan("#{sc.name.to_s}", "#{building.name.to_s}", "#{airloop.name.to_s}", false)
        elsif sc.to_CoilCoolingWater.is_initialized
          sc = sc.to_CoilCoolingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:chilledWaterCool] = "m:"
          if sc.plantLoop.is_initialized
            pl = sc.plantLoop.get
            ahu_json[:chilledWaterPlantRef] = create_ref(pl.name.to_s)
          end
        elsif sc.to_CoilHeatingWater.is_initialized
          sc = sc.to_CoilHeatingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}") 
          ahu_json[:hotWaterHeat] = "m:"
          if sc.plantLoop.is_initialized
            pl = sc.plantLoop.get
            ahu_json[:hotWaterPlantRef] = create_ref(pl.name.to_s)
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
        tz = dc.to_ThermalZone.get
        #create sensor points
        zone_json_temp = create_point("sensor", "#{tz.name.to_s} Zone Air Temp Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "zone", "air", "temp", "Number", "C")       
        zone_json_humidity = create_point("sensor", "#{tz.name.to_s} Zone Air Humidity Sensor", "#{building.name.to_s}", "#{airloop.name.to_s}", "zone", "air", "humidity", "Number", "%")                  

        if tz.thermostatSetpointDualSetpoint.is_initialized
          if tz.thermostatSetpointDualSetpoint.get.coolingSetpointTemperatureSchedule.is_initialized
            cool_thermostat = tz.thermostatSetpointDualSetpoint.get.coolingSetpointTemperatureSchedule.get
            runner.registerInfo("found #{cool_thermostat.name.to_s} on airloop #{airloop.name.to_s} in thermalzone #{tz.name.to_s}") 
            zone_json_cooling = create_point("sp", "#{tz.name.to_s} Zone Air Cooling sp", "#{building.name.to_s}", "#{airloop.name.to_s}", "zone", "air", "temp", "Number", "C") 
            zone_json_cooling[:cooling] = "m:"
          end
          if tz.thermostatSetpointDualSetpoint.get.heatingSetpointTemperatureSchedule.is_initialized
            heat_thermostat = tz.thermostatSetpointDualSetpoint.get.heatingSetpointTemperatureSchedule.get
            runner.registerInfo("found #{heat_thermostat.name.to_s} on airloop #{airloop.name.to_s} in thermalzone #{tz.name.to_s}") 
            zone_json_heating = create_point("sp", "#{tz.name.to_s} Zone Air Heating sp", "#{building.name.to_s}", "#{airloop.name.to_s}", "zone", "air", "temp", "Number", "C")   
            zone_json_heating[:heating] = "m:"
          end
        end
        zone_json_temp[:area] = create_num(tz.floorArea)
        zone_json_temp[:volume] = create_num(tz.volume)
        zone_json_humidity[:area] = create_num(tz.floorArea)
        zone_json_humidity[:volume] = create_num(tz.volume)
        
        tz.equipment.each do |equip|
          if equip.to_AirTerminalSingleDuctVAVReheat.is_initialized
            zone_json_temp[:vav] = "m:"
            zone_json_humidity[:vav] = "m:"
            zone_json_cooling[:vav] = "m:"
            zone_json_heating[:vav] = "m:"
            ahu_json[:vavZone] = "m:"
            
            vav_json = Hash.new
            vav_json[:id] = create_ref(equip.name.to_s)
            vav_json[:dis] = create_str(equip.name.to_s)
            vav_json[:hvac] = "m:"
            vav_json[:vav] = "m:"
            vav_json[:equip] = "m:"
            vav_json[:equipRef] = create_ref(airloop.name.to_s)
            vav_json[:ahuRef] = create_ref(airloop.name.to_s)
            vav_json[:siteRef] = create_ref(building.name.to_s)
            #check reheat coil
            rc = equip.to_AirTerminalSingleDuctVAVReheat.get.reheatCoil
            if rc.to_CoilHeatingWater.is_initialized
              rc = rc.to_CoilHeatingWater.get
              runner.registerInfo("found #{rc.name.to_s} on airloop #{airloop.name.to_s}") 
              vav_json[:hotWaterReheat] = "m:"
              if rc.plantLoop.is_initialized
                pl = rc.plantLoop.get
                vav_json[:hotWaterPlantRef] = create_ref(pl.name.to_s)
              end          
            elsif rc.to_CoilHeatingElectric.is_initialized
              rc = rc.to_CoilHeatingElectric.get
              runner.registerInfo("found #{rc.name.to_s} on airloop #{airloop.name.to_s}")  
              vav_json[:elecReheat] = "m:"          
            end
            haystack_json << vav_json
            #entering and discharge sensors
            entering_node = equip.to_AirTerminalSingleDuctVAVReheat.get.inletModelObject.get.to_Node
            haystack_json <<  create_point("sensor", "#{equip.name.to_s} Entering Air Temp Sensor", "#{building.name.to_s}", "#{equip.name.to_s}", "entering", "air", "temp", "Number", "C")   
            discharge_node = equip.to_AirTerminalSingleDuctVAVReheat.get.outletModelObject.get.to_Node
            haystack_json <<  create_point("sensor", "#{equip.name.to_s} Discharge Air Temp Sensor", "#{building.name.to_s}", "#{equip.name.to_s}", "discharge", "air", "temp", "Number", "C")   
            avail_sch = discharge_node = equip.to_AirTerminalSingleDuctVAVReheat.get.availabilitySchedule
            #TODO 'reheat cmd'
          elsif equip.to_AirTerminalSingleDuctUncontrolled.is_initialized
            ahu_json[:directZone] = "m:"
          end
        end
        haystack_json << zone_json_temp
        haystack_json << zone_json_humidity
        haystack_json << zone_json_cooling
        haystack_json << zone_json_heating
      end #end thermalzone
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
