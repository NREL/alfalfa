require 'json'

module OpenStudio
  module Alfalfa
    class Tagger

      def initialize

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
        return "r:#{id.gsub(/[\s-]/, '_')}"
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
        return "#{id.gsub(/[\s-]/, '_')}"
      end

      def create_point_timevars(outvar_time, siteRef)
        #this function will add haystack tag to the time-variables created by user.
        #the time-variables are also written to variables.cfg file to coupling energyplus
        #the uuid is unique to be used for mapping purpose
        #the point_json generated here caontains the tags for the tim-variables
        point_json = Hash.new
        #id = outvar_time.keyValue.to_s + outvar_time.name.to_s
        uuid = create_uuid("")
        point_json[:id] = uuid
        #point_json[:source] = create_str("EnergyPlus")
        #point_json[:type] = "Output:Variable"
        #point_json[:name] = create_str(outvar_time.name.to_s)
        #point_json[:variable] = create_str(outvar_time.name)
        point_json[:dis] = create_str(outvar_time.nameString)
        point_json[:siteRef] = create_ref(siteRef)
        point_json[:point] = "m:"
        point_json[:cur] = "m:"
        point_json[:curStatus] = "s:disabled"

        return point_json, uuid
      end

      # end of create_point_timevar

      def create_mapping_timevars(outvar_time, uuid)
        #this function will use the uuid generated from create_point_timevars(), to make a mapping.
        #the uuid is unique to be used for mapping purpose; uuid is the belt to connect point_json and mapping_json
        #the mapping_json below contains all the necessary tags
        mapping_json = Hash.new
        mapping_json[:id] = uuid
        mapping_json[:source] = "EnergyPlus"
        mapping_json[:name] = "EMS"
        mapping_json[:type] = outvar_time.nameString
        mapping_json[:variable] = ""

        return mapping_json
      end


      def create_point_uuid(type, id, siteRef, equipRef, floorRef, where, what, measurement, kind, unit)
        point_json = Hash.new
        uuid = create_uuid(id)
        point_json[:id] = uuid
        point_json[:dis] = create_str(id)
        point_json[:siteRef] = create_ref(siteRef)
        point_json[:equipRef] = create_ref(equipRef)
        point_json[:floorRef] = create_ref(floorRef)
        point_json[:point] = "m:"
        point_json["#{type}"] = "m:"
        point_json["#{measurement}"] = "m:"
        point_json["#{where}"] = "m:"
        point_json["#{what}"] = "m:"
        point_json[:kind] = create_str(kind)
        point_json[:unit] = create_str(unit)
        point_json[:cur] = "m:"
        point_json[:curStatus] = "s:disabled"
        return point_json, uuid
      end

      def create_point2_uuid(type, type2, id, siteRef, equipRef, floorRef, where, what, measurement, kind, unit)
        point_json = Hash.new
        uuid = create_uuid(id)
        point_json[:id] = uuid
        point_json[:dis] = create_str(id)
        point_json[:siteRef] = create_ref(siteRef)
        point_json[:equipRef] = create_ref(equipRef)
        point_json[:floorRef] = create_ref(floorRef)
        point_json[:point] = "m:"
        point_json["#{type}"] = "m:"
        point_json["#{type2}"] = "m:"
        point_json["#{measurement}"] = "m:"
        point_json["#{where}"] = "m:"
        point_json["#{what}"] = "m:"
        point_json[:kind] = create_str(kind)
        point_json[:unit] = create_str(unit)
        point_json[:cur] = "m:"
        point_json[:curStatus] = "s:disabled"
        return point_json, uuid
      end

      def create_controlpoint2(type, type2, id, uuid, siteRef, equipRef, floorRef, where, what, measurement, kind, unit)
        point_json = Hash.new
        point_json[:id] = create_ref(uuid)
        point_json[:dis] = create_str(id)
        point_json[:siteRef] = create_ref(siteRef)
        point_json[:equipRef] = create_ref(equipRef)
        point_json[:floorRef] = create_ref(floorRef)
        point_json[:point] = "m:"
        point_json["#{type}"] = "m:"
        point_json["#{type2}"] = "m:"
        point_json["#{measurement}"] = "m:"
        point_json["#{where}"] = "m:"
        point_json["#{what}"] = "m:"
        point_json[:kind] = create_str(kind)
        point_json[:unit] = create_str(unit)
        if type2 == "writable"
          point_json[:writeStatus] = "s:ok"
        end
        return point_json
      end

      def create_fan(id, name, siteRef, equipRef, floorRef, variable)
        point_json = Hash.new
        point_json[:id] = create_ref(id)
        point_json[:dis] = create_str(name)
        point_json[:siteRef] = create_ref(siteRef)
        point_json[:equipRef] = create_ref(equipRef)
        point_json[:floorRef] = create_ref(floorRef)
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

      def create_ahu(id, name, siteRef, floorRef)
        ahu_json = Hash.new
        ahu_json[:id] = create_ref(id)
        ahu_json[:dis] = create_str(name)
        ahu_json[:ahu] = "m:"
        ahu_json[:hvac] = "m:"
        ahu_json[:equip] = "m:"
        ahu_json[:siteRef] = create_ref(siteRef)
        ahu_json[:floorRef] = create_ref(floorRef)
        return ahu_json
      end

      def create_vav(id, name, siteRef, equipRef, floorRef)
        vav_json = Hash.new
        vav_json[:id] = create_ref(id)
        vav_json[:dis] = create_str(name)
        vav_json[:hvac] = "m:"
        vav_json[:vav] = "m:"
        vav_json[:equip] = "m:"
        vav_json[:equipRef] = create_ref(equipRef)
        vav_json[:ahuRef] = create_ref(equipRef)
        vav_json[:siteRef] = create_ref(siteRef)
        vav_json[:floorRef] = create_ref(floorRef)
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
        outputVariable = OpenStudio::Model::OutputVariable.new(outVarName, model)
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
        json[:type] = outVarName
        json[:name] = key.name.to_s
        json[:variable] = ""
        return sensor, json
      end

      #will get deprecated by 'create_EMS_sensor_bcvtb' once Master Algo debugged (dont clutter up the json's with unused points right now)
      def create_EMS_sensor(outVarName, key, emsName, report_freq, model)
        outputVariable = OpenStudio::Model::OutputVariable.new(outVarName, model)
        outputVariable.setKeyValue("#{key.name.to_s}")
        outputVariable.setReportingFrequency(report_freq)
        outputVariable.setName(outVarName)
        sensor = OpenStudio::Model::EnergyManagementSystemSensor.new(model, outputVariable)
        sensor.setKeyName(key.handle.to_s)
        sensor.setName(create_ems_str(emsName))
        return sensor
      end

    end

  end

end