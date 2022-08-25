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
class PrepareIDF < OpenStudio::Ruleset::WorkspaceUserScript

  # human readable name
  def name
    return 'Prepare IDF'
  end

  # human readable description
  def description
    return 'Add python script path to IDF'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Add python script path to IDF'
  end

  # define the arguments that the user will input
  def arguments(workspace)
    args = OpenStudio::Ruleset::OSArgumentVector.new
    # python script name
    py_name = OpenStudio::Ruleset::OSArgument.makeStringArgument('py_name',true)
    py_name.setDisplayName('Python File Name')
    py_name.setDescription('Name of the python script without the extension')
    py_name.setDefaultValue('main')
    args << py_name
    return args
  end

  # define what happens when the measure is run
  def run(workspace,runner,usr_args)
    super(workspace,runner,usr_args)
    # use the built-in error checking
    return false unless runner.validateUserArguments(arguments(workspace),usr_args)
    # assign the user inputs to variables
    py_name = runner.getStringArgumentValue('py_name',usr_args)
    # find python script
    py_file = runner.workflow.findFile(py_name + '.py')
    unless py_file.is_initialized
      runner.registerError("Did not find #{py_file} in paths described in OSW file.")
      runner.registerError("File is #{py_name + '.py'}.")
      runner.registerError("Looked for #{py_file} in the following locations")
      runner.workflow.absoluteFilePaths.each {|p| runner.registerError("#{p}")}
      return false
    end
    # modify python plugin search paths
    workspace.getObjectsByType('PythonPlugin_SearchPaths'.to_IddObjectType).each do |o|
      if (RUBY_PLATFORM =~ /linux/) != nil
        o.setString(3,'/usr/local/lib/python3.7/dist-packages')
        o.setString(4,'/usr/local/EnergyPlus-9-6-0')
      elsif (RUBY_PLATFORM =~ /darwin/) != nil
        o.setString(3,'/usr/local/lib/python3.8/site-packages')
        o.setString(4,'/Applications/EnergyPlus-9-6-0')
      elsif (RUBY_PLATFORM =~ /cygwin|mswin|mingw|bccwin|wince|emx/) != nil
        o.setString(3,"#{ENV['USERPROFILE']}/AppData/Local/Programs/Python/Python37/Lib/site-packages")
        o.setString(4,'C:/EnergyPlusV9-6-0')
      end
      runner.workflow.absoluteFilePaths.each {|p| o.setString(5,p.to_s) if p.to_s.include?('python')}
    end
  end

end

# register the measure to be used by the application
PrepareIDF.new.registerWithApplication
