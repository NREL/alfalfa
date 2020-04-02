########################################################################################################################
#  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#  following conditions are met:
#
#  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#  disclaimer.
#
#  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials provided with the distribution.
#
#  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
#  derived from this software without specific prior written permission from the respective party.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
#  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
########################################################################################################################

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
    return "This measure loops through outputvariables, EMS:outputvariables and ExternalInterface objects and will create the variables.cfg xml file for BCVTB.
            Those variables need to be in cfg file, being used for data exchange."
  end

  def create_ems_str(id)
    #return string formatted with no spaces or '-' (can be used as EMS var name)
    return "#{id.gsub(/[\s-]/,'_')}"
  end

  def add_xml_output(object, energyPlusName)
    #output variable
    variable = REXML::Element.new "variable"
    variable.attributes["source"] = "EnergyPlus"
    energyplus = REXML::Element.new "EnergyPlus"
    energyplus.attributes["name"] = energyPlusName
    energyplus.attributes["type"] = object
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
    target=open('checkvar.txt','w')
    #alphabetize
    #outputVariables = outputVariables.sort_by{ |m| [ m.name.to_s.downcase, m.keyValue.to_s]}
    outputVariables = outputVariables.sort_by{ |m| [ m.keyValue.to_s, m.name.to_s.downcase]}
    outputVariables.each do |outvar|
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml
      #print outvar
      target.write(outvar)
      if (outvar.keyValue.to_s =="*")
        print " \n ****** You are good here ******"
      end
      if (outvar.exportToBCVTB && (outvar.keyValue != "*"))
      #if (outvar.exportToBCVTB )
        bcvtb.add_element add_xml_output(outvar.variableName, outvar.keyValue)
        runner.registerInfo("Added #{outvar.variableName.to_s} #{outvar.keyValue.to_s} to BCVTB XML file.")
        counter += 1
      end
    end  #end outputVariables
    target.close

    #loop through EMSoutputVariables
    #my time variables will be written to cfg file here
    outputVariables = model.getEnergyManagementSystemOutputVariables
    #alphabetize
    outputVariables = outputVariables.sort_by{ |m| m.name.to_s.downcase }
    outputVariables.each do |outvar|
      #print "\n Watchout Here!!!"
      #print outvar.emsVariableName.to_s
      #If flag set to true and keyValue is not * then add output variable to BCVTB xml
      if (outvar.exportToBCVTB)
#         print "\n Watchout Here!!!  "
        print outvar.emsVariableName.to_s
        print outvar.nameString
        bcvtb.add_element add_xml_output(outvar.nameString, "EMS")
        runner.registerInfo("Added #{outvar.nameString} to BCVTB XML file.")
        counter += 1
      end
    end  #end EMSoutputVariables

    # find all EnergyManagementSystemGlobalVariable objects and
    # replace those that have exportToBCVTB set to true
    # We also have to swap handles in any ems programs
    ems_programs = model.getEnergyManagementSystemPrograms
    ems_subroutines = model.getEnergyManagementSystemSubroutines

    emsGlobals = model.getEnergyManagementSystemGlobalVariables

    emsGlobals.each do |emsvar|
      if ( emsvar.exportToBCVTB )
        emsGlobalName = emsvar.nameString
        emsGlobalHandle = emsvar.handle.to_s
        emsvar.remove

        eevar = OpenStudio::Model::ExternalInterfaceVariable.new(model, emsGlobalName, 0)
        eevarHandle = eevar.handle.to_s

        ems_programs.each do |prog|
          body = prog.body
          body.gsub!(emsGlobalHandle, eevarHandle)
          prog.setBody(body)
        end

        ems_subroutines.each do |prog|
          body = prog.body
          body.gsub!(emsGlobalHandle, eevarHandle)
          prog.setBody(body)
        end
      end
    end

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
