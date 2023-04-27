# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2021, Alliance for Sustainable Energy, LLC.
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

require 'openstudio'
require 'openstudio/measure/ShowRunnerOutput'
require 'fileutils'

require_relative '../measure.rb'
require 'minitest/autorun'

require 'json'

class CreateDOEPrototypeBuildingCopyTest < Minitest::Test
  def setup
    # Make a directory to save the resulting models
    @test_dir = "#{File.dirname(__FILE__)}/output"
    if !Dir.exist?(@test_dir)
      Dir.mkdir(@test_dir)
    end
  end

  # Create a set of models, return a list of failures
  def create_models(bldg_types, vintages, climate_zones, epw_files = [])
    #### Create the prototype building
    failures = []

    # Loop through all of the given combinations
    bldg_types.sort.each do |building_type|
      vintages.sort.each do |template|
        climate_zones.sort.each do |climate_zone|
          model_name = "#{building_type}-#{template}-#{climate_zone}"
          puts "****Testing #{model_name}****"

          # Create an instance of the measure
          measure = CreateDOEPrototypeBuildingCopy.new

          # Create an instance of a runner
          runner = OpenStudio::Measure::OSRunner.new(OpenStudio::WorkflowJSON.new)

          # Make an empty model
          model = OpenStudio::Model::Model.new

          # Set argument values
          arguments = measure.arguments(model)
          argument_map = OpenStudio::Measure::OSArgumentMap.new
          building_type_arg = arguments[0].clone
          assert(building_type_arg.setValue(building_type))
          argument_map['building_type'] = building_type_arg

          template_arg = arguments[1].clone
          assert(template_arg.setValue(template))
          argument_map['template'] = template_arg

          climate_zone_arg = arguments[2].clone
          assert(climate_zone_arg.setValue(climate_zone))
          argument_map['climate_zone'] = climate_zone_arg

          epw_arg = arguments[3].clone
          assert(epw_arg.setValue('Not Applicable'))
          argument_map['epw_file'] = epw_arg

          measure.run(model, runner, argument_map)
          result = runner.result
          show_output(result)
          if result.value.valueName != 'Success'
            failures << "Error - #{model_name} - Model was not created successfully."
          end

          model_directory = "#{@test_dir}/#{building_type}-#{template}-#{climate_zone}"

          # Convert the model to energyplus idf
          forward_translator = OpenStudio::EnergyPlus::ForwardTranslator.new
          idf = forward_translator.translateModel(model)
          idf_path_string = "#{model_directory}/#{model_name}.idf"
          idf_path = OpenStudio::Path.new(idf_path_string)
          idf.save(idf_path, true)
        end
      end
    end

    #### Return the list of failures
    return failures
  end

  def dont_test_primary_school
    bldg_types = ['PrimarySchool']
    vintages = ['DOE Ref Pre-1980'] # , 'DOE Ref 1980-2004', '90.1-2004', '90.1-2007', '90.1-2010']
    climate_zones = ['ASHRAE 169-2013-3A']

    all_failures = []

    # Create the models
    all_failures += create_models(bldg_types, vintages, climate_zones)

    # Assert if there are any errors
    puts "There were #{all_failures.size} failures"
    assert(all_failures.empty?, "FAILURES: #{all_failures.join("\n")}")
  end

  def test_secondary_school
    bldg_types = ['SecondarySchool']
    vintages = ['DOE Ref Pre-1980', 'DOE Ref 1980-2004', '90.1-2004', '90.1-2007', '90.1-2010', '90.1-2016']
    climate_zones = ['ASHRAE 169-2013-2A']

    all_failures = []

    # Create the models
    all_failures += create_models(bldg_types, vintages, climate_zones)

    # Assert if there are any errors
    puts "There were #{all_failures.size} failures"
    assert(all_failures.empty?, "FAILURES: #{all_failures.join("\n")}")
  end

  def test_primary_school
    bldg_types = ['PrimarySchool']
    vintages = ['DOE Ref Pre-1980', 'DOE Ref 1980-2004', '90.1-2004', '90.1-2007', '90.1-2010', '90.1-2016']
    climate_zones = ['ASHRAE 169-2013-3A']

    all_failures = []

    # Create the models
    all_failures += create_models(bldg_types, vintages, climate_zones)

    # Assert if there are any errors
    puts "There were #{all_failures.size} failures"
    assert(all_failures.empty?, "FAILURES: #{all_failures.join("\n")}")
  end
end
