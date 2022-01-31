# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# (1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# (2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# (3) Neither the name of the copyright holder nor the names of any contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission from the respective party.
#
# (4) Other than as required in clauses (1) and (2), distributions in any form
# of modifications or other derivative works may not use the "OpenStudio"
# trademark, "OS", "os", or any other confusingly similar designation without
# specific prior written permission from Alliance for Sustainable Energy, LLC.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE
# UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF
# THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *******************************************************************************

# start the measure
class ReplaceIDF < OpenStudio::Ruleset::WorkspaceUserScript

  # human readable name
  def name
    return 'Replace IDF'
  end

  # human readable description
  def description
    return 'Replace OpenStudio generated IDF file with user specified IDF.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Additional EnergyPlus measures can be placed after this measure in the workflow. Weather file should be described in the seed OSM file or in the OSW file used to run the simulation.'
  end

  # define the arguments that the user will input
  def arguments(workspace)
    args = OpenStudio::Ruleset::OSArgumentVector.new
    # argument for IDF name
    idf_name = OpenStudio::Ruleset::OSArgument.makeStringArgument('idf_name',true)
    idf_name.setDisplayName('External IDF File Name')
    idf_name.setDescription('Name of the model to replace current model. This is the filename with the extension (e.g. MyModel.idf). Optionally this can include the full file path, but for most use cases should just be file name.')
    args << idf_name
    return args
  end

  # define what happens when the measure is run
  def run(workspace,runner,usr_args)
    super(workspace,runner,usr_args)
    # use the built-in error checking
    return false unless runner.validateUserArguments(arguments(workspace),usr_args)
    # assign the user inputs to variables
    idf_name = runner.getStringArgumentValue('idf_name',usr_args)
    # find external model
    idf_file = runner.workflow.findFile(idf_name)
    if idf_file.is_initialized
      idf_name = idf_file.get.to_s
    else
      runner.registerError("Did not find #{idf_name} in paths described in OSW file.")
      runner.registerInfo("Looked for #{idf_name} in the following locations")
      runner.workflow.absoluteFilePaths.each {|path| runner.registerInfo("#{path}")}
      return false
    end
    # get model from path and error if empty
    ext_workspace = OpenStudio::Workspace::load(OpenStudio::Path.new(idf_name))
    if ext_workspace.empty?
      runner.registerError("Cannot load #{idf_name}")
      return false
    end
    ext_workspace = ext_workspace.get
    # report initial condition of model
    runner.registerInitialCondition("The initial IDF file had #{workspace.objects.size} objects.")
    runner.registerInfo("Loading #{idf_name}")
    # array of objects to remove
    objs_to_rm = ['Timestep',
                  'LifeCycleCost:Parameters',
                  'LifeCycleCost:UsePriceEscalation',
                  'Building',
                  'SimulationControl',
                  'Sizing:Parameters',
                  'RunPeriod',
                  'Output:Table:SummaryReports',
                  'GlobalGeometryRules',
                  'Schedule:Constant',
                  'OutdoorAir:Node',
                  'OutputControl:Table:Style',
                  'Output:VariableDictionary',
                  'Output:SQLite',
                  'LifeCycleCost:NonrecurringCost']
    # remove existing objects from model
    handles = OpenStudio::UUIDVector.new
    workspace.objects.each {|obj| handles << obj.handle if objs_to_rm.include?(obj.idfObject.iddObject.name)}
    workspace.removeObjects(handles)
    # add new file to empty model
    workspace.addObjects(ext_workspace.toIdfFile.objects)
    # report final condition of model
    runner.registerFinalCondition("The final IDF file had #{workspace.objects.size} objects.")
  end
end

# register the measure to be used by the application
ReplaceIDF.new.registerWithApplication
