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
  
  def create_uuid(dummyinput)
    return "r:#{OpenStudio.removeBraces(OpenStudio.createUUID)}"
  end
  
  def create_ref(id)
    #return string formatted for Ref (ie, "r:xxxxx") with uuid of object
    #return "r:#{id.gsub(/[\s-]/,'_')}"
    return "r:#{OpenStudio.removeBraces(id)}"
  end 
  
  def create_ref_name(id)
    #return string formatted for Ref (ie, "r:xxxxx") with uuid of object
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
  
  def create_ems_str(id)
    #return string formatted with no spaces or '-' (can be used as EMS var name)
    return "#{id.gsub(/[\s-]/,'_')}"
  end
  
  def create_point_uuid(type, id, siteRef, equipRef, where,what,measurement,kind,unit)
    point_json = Hash.new
    uuid = create_uuid(id)
    point_json[:id] = uuid
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
    return point_json, uuid
  end
  
  def create_point2_uuid(type, type2, id, siteRef, equipRef, where,what,measurement,kind,unit)
    point_json = Hash.new
    uuid = create_uuid(id)
    point_json[:id] = uuid
    point_json[:dis] = create_str(id)
    point_json[:siteRef] = create_ref(siteRef)
    point_json[:equipRef] = create_ref(equipRef)
    point_json[:point] = "m:"
    point_json["#{type}"] = "m:"
    point_json["#{type2}"] = "m:"
    point_json["#{measurement}"] = "m:"   
    point_json["#{where}"] = "m:" 
    point_json["#{what}"] = "m:" 
    point_json[:kind] = create_str(kind) 
    point_json[:unit] = create_str(unit) 
    return point_json, uuid
  end
  
  def create_controlpoint2(type, type2, id, uuid, siteRef, equipRef, where,what,measurement,kind,unit)
    point_json = Hash.new
    point_json[:id] = create_ref(uuid)
    point_json[:dis] = create_str(id)
    point_json[:siteRef] = create_ref(siteRef)
    point_json[:equipRef] = create_ref(equipRef)
    point_json[:point] = "m:"
    point_json["#{type}"] = "m:"
    point_json["#{type2}"] = "m:"
    point_json["#{measurement}"] = "m:"   
    point_json["#{where}"] = "m:" 
    point_json["#{what}"] = "m:" 
    point_json[:kind] = create_str(kind) 
    point_json[:unit] = create_str(unit) 
    return point_json
  end
  
  def create_fan(id, name, siteRef, equipRef, variable)
    point_json = Hash.new
    point_json[:id] = create_ref(id)
    point_json[:dis] = create_str(name)
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

  def create_ahu(id, name, siteRef)
    ahu_json = Hash.new
    ahu_json[:id] = create_ref(id)
    ahu_json[:dis] = create_str(name)
    ahu_json[:ahu] = "m:"
    ahu_json[:hvac] = "m:"
    ahu_json[:equip] = "m:"
    ahu_json[:siteRef] = create_ref(siteRef)
    return ahu_json
  end  
  
  def create_vav(id, name, siteRef, equipRef)
    vav_json = Hash.new
    vav_json[:id] = create_ref(id)
    vav_json[:dis] = create_str(name)
    vav_json[:hvac] = "m:"
    vav_json[:vav] = "m:"
    vav_json[:equip] = "m:"
    vav_json[:equipRef] = create_ref(equipRef)
    vav_json[:ahuRef] = create_ref(equipRef)
    vav_json[:siteRef] = create_ref(siteRef)
    return vav_json
  end
  
  def create_mapping_output_uuid(emsName, uuid)
    json = Hash.new
    json[:id] = create_ref(uuid)
    json[:source] = "Ptolemy" 
    json[:name] = ""
    json[:type] = ""
    json[:variable] = emsName
    return json
  end
  
  def create_EMS_sensor_bcvtb(outVarName, key, emsName, uuid, report_freq, model)
    outputVariable = OpenStudio::Model::OutputVariable.new(outVarName,model)
    outputVariable.setKeyValue("#{key.name.to_s}")
    outputVariable.setReportingFrequency(report_freq) 
    outputVariable.setName(outVarName)
    outputVariable.setExportToBCVTB(true)
    
    sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
    sensor.setKeyName(key.handle.to_s)
    sensor.setName(create_ems_str(emsName))
    
    json = Hash.new
    json[:id] = uuid 
    json[:source] = "EnergyPlus" 
    json[:name] = outVarName
    json[:type] = key.name.to_s
    json[:variable] = ""
    return sensor, json
  end
  
  #will get deprecated by 'create_EMS_sensor_bcvtb' once Master Algo debugged (dont clutter up the json's with unused points right now)
  def create_EMS_sensor(outVarName, key, emsName, report_freq, model)
    outputVariable = OpenStudio::Model::OutputVariable.new(outVarName,model)
    outputVariable.setKeyValue("#{key.name.to_s}")
    outputVariable.setReportingFrequency(report_freq) 
    outputVariable.setName(outVarName)
    sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
    sensor.setKeyName(key.handle.to_s)
    sensor.setName(create_ems_str(emsName))
    return sensor
  end
  
  #define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new
    
    local_test = OpenStudio::Ruleset::OSArgument::makeBoolArgument("local_test", false)
    local_test.setDisplayName("Local Test")
    local_test.setDescription("Use EMS for Local Testing")
    local_test.setDefaultValue(true)
    args << local_test
    
    return args
  end #end the arguments method

  #define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)
    
    # Use the built-in error checking 
    if not runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end
    
    local_test = runner.getBoolArgumentValue("local_test",user_arguments) 
    runner.registerInfo("local_test = #{local_test}")
    
    #Global Vars
    report_freq = "hourly"
    
    #initialize variables
    haystack_json = []
    mapping_json = []
    num_economizers = 0
    airloops = []
    
    #Master Enable
    if local_test == false
      #External Interface version
      runner.registerInitialCondition("Initializing ExternalInterface") 
      master_enable = OpenStudio::Model::ExternalInterfaceVariable.new(model, "MasterEnable", 1)
      #TODO uncomment out for real use
      externalInterface = model.getExternalInterface
      externalInterface.setNameofExternalInterface("PtolemyServer")
    else
      #EMS Version
      runner.registerInitialCondition("Initializing EnergyManagementSystem")
      master_enable = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "MasterEnable")
    end
    
    #initialization program
    program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
    program.setName("Master_Enable")   
    program.addLine("SET #{master_enable.handle.to_s} = 1")

    pcm = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
    pcm.setName("Master_Enable_Prgm_Mgr")
    pcm.setCallingPoint("BeginNewEnvironment")
    pcm.addProgram(program)
          
    #Site and WeatherFile Data
    if model.weatherFile.is_initialized 
      site_json = Hash.new
      weather_json = Hash.new
      
      wf = model.weatherFile.get
      building = model.getBuilding
      
      site_json[:id] = create_ref(building.handle)
      site_json[:dis] = create_str(building.name.to_s)
      site_json[:site] = "m:"
      site_json[:area] = create_num(building.floorArea)
      site_json[:weatherRef] = create_ref(wf.handle)
      site_json[:tz] = create_num(wf.timeZone)
      site_json[:geoCity] = create_str(wf.city)
      site_json[:geoState] = create_str(wf.stateProvinceRegion)
      site_json[:geoCountry] = create_str(wf.country)
      site_json[:geoCoord] = "c:#{wf.latitude},#{wf.longitude}"
      haystack_json << site_json
            
      weather_json[:id] = create_ref(wf.handle)
      weather_json[:dis] = create_str(wf.city)
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
      ahu_json = create_ahu(airloop.handle,airloop.name.to_s, building.handle)

      #AHU discharge sensors
      #discharge air node
      discharge_air_node = airloop.supplyOutletNode
      #Temp Sensor
      haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Discharge Air Temp Sensor", building.handle, airloop.handle, "discharge", "air", "temp", "Number", "C")            
      haystack_json << haystack_temp_json
      discharge_air_temp_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Temperature", discharge_air_node, "#{airloop.name.to_s} Discharge Air Temp Sensor", temp_uuid, report_freq, model)
      mapping_json << temp_json
      #Pressure Sensor
      haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Discharge Air Pressure Sensor", building.handle, airloop.handle, "discharge", "air", "pressure", "Number", "Pa")    
      haystack_json << haystack_temp_json      
      discharge_air_pressure_sensor = create_EMS_sensor("System Node Pressure", discharge_air_node, "#{airloop.name.to_s} Discharge Air Pressure Sensor", report_freq, model)
      #Humidity Sensor
      haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Discharge Air Humidity Sensor", building.handle, airloop.handle, "discharge", "air", "humidity", "Number", "%")                      
      haystack_json << haystack_temp_json
      discharge_air_humidity_sensor = create_EMS_sensor("System Node Relative Humidity", discharge_air_node, "#{airloop.name.to_s} Discharge Air Humidity Sensor", report_freq, model)
      #Flow Sensor
      haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Discharge Air Flow Sensor", building.handle, airloop.handle, "discharge", "air", "flow", "Number", "Kg/s")  
      haystack_json << haystack_temp_json
      discharge_air_flow_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Mass Flow Rate", discharge_air_node, "#{airloop.name.to_s} Discharge Air Flow Sensor", temp_uuid, report_freq, model)
      mapping_json << temp_json

      supply_components = airloop.supplyComponents

      #find fan, cooling coil and heating coil on loop
      supply_components.each do |sc|
        #get economizer on outdoor air system
        if sc.to_AirLoopHVACOutdoorAirSystem.is_initialized
          sc = sc.to_AirLoopHVACOutdoorAirSystem.get
          #get ControllerOutdoorAir
          controller_oa = sc.getControllerOutdoorAir
          #create damper sensor and cmd points
          damper_command = create_ems_str("#{airloop.name.to_s} Outside Air Damper CMD")
          damper_command_enable = create_ems_str("#{airloop.name.to_s} Outside Air Damper CMD Enable")
          damper_position = create_ems_str("#{airloop.name.to_s} Outside Air Damper Sensor position")
          #Damper Sensor
          haystack_temp_json, temp_uuid = create_point2_uuid("sensor", "position", damper_position, building.handle, airloop.handle, "outside", "air", "damper", "Number", "%")    
          haystack_json << haystack_temp_json          
          outside_air_damper_sensor, temp_json = create_EMS_sensor_bcvtb("Air System Outdoor Air Flow Fraction", airloop, "#{airloop.name.to_s} Outside Air Damper Sensor", temp_uuid, report_freq, model)         
          mapping_json << temp_json         

          #add EMS Actuator for Damper
          damper_actuator = OpenStudio::Model::EnergyManagementSystemActuator.new(controller_oa,"Outdoor Air Controller","Air Mass Flow Rate") 
          damper_actuator.setName(create_ems_str("#{airloop.name.to_s} Outside Air Mass Flow Rate"))
          #Variable to read the Damper CMD
          if local_test == false
            #ExternalInterfaceVariables
            damper_variable_enable = OpenStudio::Model::ExternalInterfaceVariable.new(model, damper_command_enable, 1)
            mapping_json << create_mapping_output_uuid(damper_command_enable, damper_variable_enable.handle)
            damper_variable = OpenStudio::Model::ExternalInterfaceVariable.new(model, damper_command, 0.5)
            mapping_json << create_mapping_output_uuid(damper_command, damper_variable.handle)
            #Damper CMD
            haystack_temp_json = create_controlpoint2("cmd", "writable", damper_command, damper_variable.handle, building.handle, airloop.handle, "outside", "air", "damper", "Number", "%")     
            haystack_json << haystack_temp_json 
          else
            #EnergyManagementSystemVariables
            damper_variable_enable = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "#{damper_command_enable}")
            mapping_json << create_mapping_output_uuid(damper_command_enable, damper_variable_enable.handle)
            damper_variable = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, "#{damper_command}")
            mapping_json << create_mapping_output_uuid(damper_command, damper_variable.handle) 
            #Damper CMD
            haystack_temp_json = create_controlpoint2("cmd", "writable", damper_command, damper_variable.handle, building.handle, airloop.handle, "outside", "air", "damper", "Number", "%")     
            haystack_json << haystack_temp_json 
            #initialization program
            program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
            program.setName("#{damper_command}_Prgm_init")   
            #Turn off for now
            program.addLine("SET #{damper_variable_enable.handle.to_s} = 0")
            program.addLine("SET #{damper_variable.handle.to_s} = 0.5")

            pcm = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
            pcm.setName("#{damper_command}_Prgm_Mgr_init")
            pcm.setCallingPoint("BeginNewEnvironment")
            pcm.addProgram(program)
          end
          #mixed air node
          if sc.mixedAirModelObject.is_initialized
            #AHU mixed sensors
            #mixed air node
            mix_air_node = sc.mixedAirModelObject.get.to_Node.get
            runner.registerInfo("found mixed air node #{mix_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #Temp Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Mixed Air Temp Sensor", building.handle, airloop.handle, "mixed", "air", "temp", "Number", "C")   
            haystack_json << haystack_temp_json             
            mixed_air_temp_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Temperature", mix_air_node, "#{airloop.name.to_s} Mixed Air Temp Sensor", temp_uuid, report_freq, model)
            mapping_json << temp_json
            #Pressure Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Mixed Air Pressure Sensor", building.handle, airloop.handle, "mixed", "air", "pressure", "Number", "Pa")       
            haystack_json << haystack_temp_json             
            mixed_air_pressure_sensor = create_EMS_sensor("System Node Pressure", mix_air_node, "#{airloop.name.to_s} Mixed Air Pressure Sensor", report_freq, model)
            #Humidity Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Mixed Air Humidity Sensor", building.handle, airloop.handle, "mixed", "air", "humidity", "Number", "%")    
            haystack_json << haystack_temp_json             
            mixed_air_humidity_sensor = create_EMS_sensor("System Node Relative Humidity", mix_air_node, "#{airloop.name.to_s} Mixed Air Humidity Sensor", report_freq, model)
            #Flow Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Mixed Air Flow Sensor", building.handle, airloop.handle, "mixed", "air", "flow", "Number", "Kg/s") 
            haystack_json << haystack_temp_json 
            mixed_air_flow_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Mass Flow Rate", mix_air_node, "#{airloop.name.to_s} Mixed Air Flow Sensor", temp_uuid, report_freq, model)
            mapping_json << temp_json
          end          
          #outdoor air node
          if sc.outdoorAirModelObject.is_initialized
            #AHU outside sensors
            #outdoor air node
            outdoor_air_node = sc.outdoorAirModelObject.get.to_Node.get
            runner.registerInfo("found outdoor air node #{outdoor_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #Temp Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Outside Air Temp Sensor", building.handle, airloop.handle, "outside", "air", "temp", "Number", "C")                    
            haystack_json << haystack_temp_json 
            outside_air_temp_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Temperature", outdoor_air_node, "#{airloop.name.to_s} Outside Air Temp Sensor", temp_uuid, report_freq, model)
            mapping_json << temp_json
            #Pressure Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Outside Air Pressure Sensor", building.handle, airloop.handle, "outside", "air", "pressure", "Number", "Pa")               
            haystack_json << haystack_temp_json 
            outside_air_pressure_sensor = create_EMS_sensor("System Node Pressure", outdoor_air_node, "#{airloop.name.to_s} Outside Air Pressure Sensor", report_freq, model)
            #Humidity Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Outside Air Humidity Sensor", building.handle, airloop.handle, "outside", "air", "humidity", "Number", "%")            
            haystack_json << haystack_temp_json 
            outside_air_humidity_sensor = create_EMS_sensor("System Node Relative Humidity", outdoor_air_node, "#{airloop.name.to_s} Outside Air Humidity Sensor", report_freq, model)
            #Flow Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Outside Air Flow Sensor", building.handle, airloop.handle, "outside", "air", "flow", "Number", "Kg/s") 
            haystack_json << haystack_temp_json 
            outside_air_flow_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Mass Flow Rate", outdoor_air_node, "#{airloop.name.to_s} Outside Air Flow Sensor", temp_uuid, report_freq, model)            
            mapping_json << temp_json
          end         
          #return air node
          if sc.returnAirModelObject.is_initialized
            #AHU return sensors
            #return air node
            return_air_node = sc.returnAirModelObject.get.to_Node.get
            runner.registerInfo("found return air node #{return_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #Temp Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Return Air Temp Sensor", building.handle, airloop.handle, "return", "air", "temp", "Number", "C")                   
            haystack_json << haystack_temp_json
            return_air_temp_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Temperature", return_air_node, "#{airloop.name.to_s} Return Air Temp Sensor", temp_uuid, report_freq, model)
            mapping_json << temp_json
            #Pressure Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Return Air Pressure Sensor", building.handle, airloop.handle, "return", "air", "pressure", "Number", "Pa")            
            haystack_json << haystack_temp_json
            return_air_pressure_sensor = create_EMS_sensor("System Node Pressure", return_air_node, "#{airloop.name.to_s} Return Air Pressure Sensor", report_freq, model)
            #Humidity Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Return Air Humidity Sensor", building.handle, airloop.handle, "return", "air", "humidity", "Number", "%")              
            haystack_json << haystack_temp_json
            return_air_humidity_sensor = create_EMS_sensor("System Node Relative Humidity", return_air_node, "#{airloop.name.to_s} Return Air Humidity Sensor", report_freq, model)
            #Flow Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Return Air Flow Sensor", building.handle, airloop.handle, "return", "air", "flow", "Number", "Kg/s")   
            haystack_json << haystack_temp_json
            return_air_flow_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Mass Flow Rate", return_air_node, "#{airloop.name.to_s} Return Air Flow Sensor", temp_uuid, report_freq, model)          
            mapping_json << temp_json
          end        
          #relief air node
          if sc.reliefAirModelObject.is_initialized
            #AHU exhaust sensors
            #exhaust air node
            exhaust_air_node = sc.reliefAirModelObject.get.to_Node.get
            runner.registerInfo("found relief air node #{exhaust_air_node.name.to_s} on airloop #{airloop.name.to_s}")
            #Temp Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Exhaust Air Temp Sensor", building.handle, airloop.handle, "exhaust", "air", "temp", "Number", "C")                      
            haystack_json << haystack_temp_json
            exhaust_air_temp_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Temperature", exhaust_air_node, "#{airloop.name.to_s} Exhaust Air Temp Sensor", temp_uuid, report_freq, model)
            mapping_json << temp_json
            #Pressure Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Exhaust Air Pressure Sensor", building.handle, airloop.handle, "exhaust", "air", "pressure", "Number", "Pa")            
            haystack_json << haystack_temp_json
            exhaust_air_pressure_sensor = create_EMS_sensor("System Node Pressure", exhaust_air_node, "#{airloop.name.to_s} Exhaust Air Pressure Sensor", report_freq, model)
            #Humidity Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Exhaust Air Humidity Sensor", building.handle, airloop.handle, "exhaust", "air", "humidity", "Number", "%")            
            haystack_json << haystack_temp_json
            exhaust_air_humidity_sensor = create_EMS_sensor("System Node Relative Humidity", exhaust_air_node, "#{airloop.name.to_s} Exhaust Air Humidity Sensor", report_freq, model)
            #Flow Sensor
            haystack_temp_json, temp_uuid = create_point_uuid("sensor", "#{airloop.name.to_s} Exhaust Air Flow Sensor", building.handle, airloop.handle, "exhaust", "air", "flow", "Number", "Kg/s")  
            haystack_json << haystack_temp_json
            exhaust_air_flow_sensor, temp_json = create_EMS_sensor_bcvtb("System Node Mass Flow Rate", exhaust_air_node, "#{airloop.name.to_s} Exhaust Air Flow Sensor", temp_uuid, report_freq, model)        
            mapping_json << temp_json
          end           
          
          #Program to set the Damper Position
          program = OpenStudio::Model::EnergyManagementSystemProgram.new(model)
          program.setName("#{damper_command}_Prgm")
          program.addLine("IF #{master_enable.handle.to_s} == 1")
          program.addLine(" SET DampPos = #{damper_variable.handle.to_s}")
          program.addLine(" SET MixAir = #{mixed_air_flow_sensor.handle.to_s}")
          program.addLine(" IF #{damper_variable_enable.handle.to_s} == 1")
          program.addLine("   SET #{damper_actuator.handle.to_s} = DampPos*MixAir")
          program.addLine(" ENDIF")
          program.addLine("ENDIF")

          pcm = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(model)
          pcm.setName("#{damper_command}_Prgm_Mgr")
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
              haystack_json << create_fan(fan.get.handle, "#{fan.get.name.to_s}", building.handle, airloop.handle, true)
            else
              runner.registerInfo("found CAV #{fan.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:constantVolume] = "m:"
              haystack_json << create_fan(fan.get.handle, "#{fan.get.name.to_s}", building.handle, airloop.handle, false)
            end
          end
          cc = sc.coolingCoil
          if cc.is_initialized
            if cc.get.to_CoilCoolingWater.is_initialized || cc.get.to_CoilCoolingWaterToAirHeatPumpEquationFit.is_initialized
              runner.registerInfo("found WATER #{cc.get.name.to_s} on airloop #{airloop.name.to_s}")
              ahu_json[:chilledWaterCool] = "m:"
              if cc.get.plantLoop.is_initialized
                pl = cc.get.plantLoop.get
                ahu_json[:chilledWaterPlantRef] = create_ref(pl.handle)
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
                ahu_json[:hotWaterPlantRef] = create_ref(pl.handle)
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
          haystack_json << create_fan(sc.handle, "#{sc.name.to_s}", building.handle, airloop.handle, false)
        elsif sc.to_FanVariableVolume.is_initialized
          sc = sc.to_FanVariableVolume.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:variableVolume] = "m:"
          haystack_json << create_fan(sc.handle, "#{sc.name.to_s}", building.handle, airloop.handle, true)
        elsif sc.to_FanOnOff.is_initialized
          sc = sc.to_FanOnOff.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:constantVolume] = "m:"
          haystack_json << create_fan(sc.handle, "#{sc.name.to_s}", building.handle, airloop.handle, false)
        elsif sc.to_CoilCoolingWater.is_initialized
          sc = sc.to_CoilCoolingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}")
          ahu_json[:chilledWaterCool] = "m:"
          if sc.plantLoop.is_initialized
            pl = sc.plantLoop.get
            ahu_json[:chilledWaterPlantRef] = create_ref(pl.handle)
          end
        elsif sc.to_CoilHeatingWater.is_initialized
          sc = sc.to_CoilHeatingWater.get
          runner.registerInfo("found #{sc.name.to_s} on airloop #{airloop.name.to_s}") 
          ahu_json[:hotWaterHeat] = "m:"
          if sc.plantLoop.is_initialized
            pl = sc.plantLoop.get
            ahu_json[:hotWaterPlantRef] = create_ref(pl.handle)
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
        zone_json_temp, dummyvar = create_point_uuid("sensor", "#{tz.name.to_s} Zone Air Temp Sensor", building.handle, airloop.handle, "zone", "air", "temp", "Number", "C")       
        zone_json_humidity, dummyvar = create_point_uuid("sensor", "#{tz.name.to_s} Zone Air Humidity Sensor", building.handle, airloop.handle, "zone", "air", "humidity", "Number", "%")                  

        if tz.thermostatSetpointDualSetpoint.is_initialized
          if tz.thermostatSetpointDualSetpoint.get.coolingSetpointTemperatureSchedule.is_initialized
            cool_thermostat = tz.thermostatSetpointDualSetpoint.get.coolingSetpointTemperatureSchedule.get
            runner.registerInfo("found #{cool_thermostat.name.to_s} on airloop #{airloop.name.to_s} in thermalzone #{tz.name.to_s}") 
            zone_json_cooling, dummyvar = create_point_uuid("sp", "#{tz.name.to_s} Zone Air Cooling sp", building.handle, airloop.handle, "zone", "air", "temp", "Number", "C") 
            zone_json_cooling[:cooling] = "m:"
          end
          if tz.thermostatSetpointDualSetpoint.get.heatingSetpointTemperatureSchedule.is_initialized
            heat_thermostat = tz.thermostatSetpointDualSetpoint.get.heatingSetpointTemperatureSchedule.get
            runner.registerInfo("found #{heat_thermostat.name.to_s} on airloop #{airloop.name.to_s} in thermalzone #{tz.name.to_s}") 
            zone_json_heating, dummyvar = create_point_uuid("sp", "#{tz.name.to_s} Zone Air Heating sp", building.handle, airloop.handle, "zone", "air", "temp", "Number", "C")   
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
            
            vav_json = create_vav(equip.handle, equip.name.to_s, building.handle, airloop.handle)

            #check reheat coil
            rc = equip.to_AirTerminalSingleDuctVAVReheat.get.reheatCoil
            if rc.to_CoilHeatingWater.is_initialized
              rc = rc.to_CoilHeatingWater.get
              runner.registerInfo("found #{rc.name.to_s} on airloop #{airloop.name.to_s}") 
              vav_json[:hotWaterReheat] = "m:"
              if rc.plantLoop.is_initialized
                pl = rc.plantLoop.get
                vav_json[:hotWaterPlantRef] = create_ref(pl.handle)
              end          
            elsif rc.to_CoilHeatingElectric.is_initialized
              rc = rc.to_CoilHeatingElectric.get
              runner.registerInfo("found #{rc.name.to_s} on airloop #{airloop.name.to_s}")  
              vav_json[:elecReheat] = "m:"          
            end
            haystack_json << vav_json
            #entering and discharge sensors
            entering_node = equip.to_AirTerminalSingleDuctVAVReheat.get.inletModelObject.get.to_Node
            haystack_json_temp, temp_uuid = create_point_uuid("sensor", "#{equip.name.to_s} Entering Air Temp Sensor", building.handle, equip.handle, "entering", "air", "temp", "Number", "C")   
            haystack_json << haystack_json_temp
            discharge_node = equip.to_AirTerminalSingleDuctVAVReheat.get.outletModelObject.get.to_Node
            haystack_json_temp, temp_uuid = create_point_uuid("sensor", "#{equip.name.to_s} Discharge Air Temp Sensor", building.handle, equip.handle, "discharge", "air", "temp", "Number", "C")   
            haystack_json << haystack_json_temp
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
    #write out the mapping json
    File.open("./report_mapping.json","w") do |f|
      f.write(mapping_json.to_json)
    end

    return true
 
  end #end the run method

end #end the measure

# register the measure to be used by the application
Haystack.new.registerWithApplication
