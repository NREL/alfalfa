# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

require 'json'
require 'openstudio'
require 'rexml/document'

# start the measure
class ExportBCVTB < OpenStudio::Ruleset::ModelUserScript

  # human readable name
  def name
    return "ExportBCVTB"
  end

  # human readable description
  def description
    return "This measure will create the variables.cfg xml file for BCVTB"
  end

  # human readable description of modeling approach
  def modeler_description
    return "This measure loops through outputvariables, EMS:outputvariables and ExternalInterface objects and will create the variables.cfg xml file for BCVTB."
  end
    
  def create_ems_str(id)
    #return string formatted with no spaces or '-' (can be used as EMS var name)
    return "#{id.gsub(/[\s-]/,'_')}"
  end
        
  def add_xml_output(name, keyValue)
    #output variable
    variable = REXML::Element.new "variable"
    variable.attributes["source"] = "EnergyPlus"
    energyplus = REXML::Element.new "EnergyPlus"
    energyplus.attributes["name"] = name
    energyplus.attributes["type"] = keyValue
    variable.add_element energyplus
    return variable
  end
  
  def add_xml_ptolemy(type, name)
    #schedule
    variable = REXML::Element.new "variable"
    variable.attributes["source"] = "Ptolemy"
    energyplus = REXML::Element.new "EnergyPlus"
    energyplus.attributes[type] = name
    variable.add_element energyplus
    return variable
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

    runner.registerInitialCondition("Creating BCVTB XML file.") 
    
    counter = 0
    #initialize BCVTB XML config file elements    
    bcvtb = REXML::Element.new "BCVTB-variables"   
    
    #loop through outputVariables 
    outputVariables = model.getOutputVariables
    #alphabetize
    outputVariables = outputVariables.sort_by{ |m| [ m.name.to_s.downcase, m.keyValue.to_s]}  
    #outputVariables = outputVariables.sort_by{ |m| [ m.keyValue.to_s, m.name.to_s.downcase]}    
    outputVariables.each do |outvar|
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml 
      if (outvar.exportToBCVTB && (outvar.keyValue != "*"))
        bcvtb.add_element add_xml_output(outvar.variableName, outvar.keyValue)
        runner.registerInfo("Added #{outvar.variableName.to_s} #{outvar.keyValue.to_s} to BCVTB XML file.") 
        counter += 1
      end
    end  #end outputVariables
    
    #loop through EMSoutputVariables 
    outputVariables = model.getEnergyManagementSystemOutputVariables 
    #alphabetize
    outputVariables = outputVariables.sort_by{ |m| m.name.to_s.downcase } 
    outputVariables.each do |outvar|
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml 
      if (outvar.exportToBCVTB)
        bcvtb.add_element add_xml_output("EMS", outvar.emsVariableName)
        runner.registerInfo("Added #{outvar.emsVariableName.to_s} to BCVTB XML file.") 
        counter += 1
      end
    end  #end EMSoutputVariables
    
    #loop through ExternalInterfaceVariables 
    externalVariables = model.getExternalInterfaceVariables 
    #alphabetize
    externalVariables = externalVariables.sort_by{ |m| m.name.to_s.downcase } 
    externalVariables.each do |outvar|
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml 
      if (outvar.exportToBCVTB)
        bcvtb.add_element add_xml_ptolemy("variable", outvar.name)
        runner.registerInfo("Added #{outvar.name.to_s} to BCVTB XML file.") 
        counter += 1
      end
    end  #end ExternalInterfaceVariables
    
    #loop through ExternalInterfaceSchedule 
    externalSchedules = model.getExternalInterfaceSchedules 
    #alphabetize
    externalSchedules = externalSchedules.sort_by{ |m| m.name.to_s.downcase } 
    externalSchedules.each do |schedule|
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml 
      if (schedule.exportToBCVTB)
        bcvtb.add_element add_xml_ptolemy("schedule", schedule.name)
        runner.registerInfo("Added #{schedule.name.to_s} to BCVTB XML file.") 
        counter += 1
      end
    end  #end ExternalInterfaceSchedules
    
    #loop through ExternalInterfaceActuators 
    externalActuators = model.getExternalInterfaceActuators 
    #alphabetize
    externalActuators = externalActuators.sort_by{ |m| m.name.to_s.downcase } 
    externalActuators.each do |actuator|
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml 
      if (actuator.exportToBCVTB)
        bcvtb.add_element add_xml_ptolemy("actuator", actuator.name)
        runner.registerInfo("Added #{actuator.name.to_s} to BCVTB XML file.") 
        counter += 1
      end
    end  #end ExternalInterfaceActuators
      
    runner.registerFinalCondition("The building has exported #{counter} variables to XML file.") 
 
    #create variables.cfg file for BCVTB
    doc = REXML::Document.new
    doc.add_element bcvtb
    #create header
    fo = File.open('report_variables.cfg', 'w')
      fo.puts '<?xml version="1.0" encoding="ISO-8859-1"?>'
      fo.puts '<!DOCTYPE BCVTB-variables SYSTEM "variables.dtd">'
    fo.close
    #add xml part
    formatter = REXML::Formatters::Pretty.new
    formatter.compact = true
    File.open('report_variables.cfg',"a"){|file| file.puts formatter.write(doc.root,"")}

    return true
 
  end #end the run method

end #end the measure

# register the measure to be used by the application
ExportBCVTB.new.registerWithApplication
