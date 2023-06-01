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

# Start the measure
class CreateDOEPrototypeBuildingCopy < OpenStudio::Measure::ModelMeasure
  require 'openstudio-standards'

  # Define the name of the Measure.
  def name
    return "Create DOE Prototype Building Copy"
  end
  # Human readable description
  def description
    return "Creates the DOE Reference Building Models as starting points for other analyses."
  end
  # Human readable description of modeling approach
  def modeler_description
    return ""
  end
  # Define the arguments that the user will input.
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # Make an argument for the building type
    building_type_chs = OpenStudio::StringVector.new
    building_type_chs << 'SecondarySchool'
    building_type_chs << 'PrimarySchool'
    building_type_chs << 'SmallOffice'
    building_type_chs << 'MediumOffice'
    building_type_chs << 'LargeOffice'
    building_type_chs << 'SmallHotel'
    building_type_chs << 'LargeHotel'
    building_type_chs << 'Warehouse'
    building_type_chs << 'RetailStandalone'
    building_type_chs << 'RetailStripmall'
    building_type_chs << 'QuickServiceRestaurant'
    building_type_chs << 'FullServiceRestaurant'
    building_type_chs << 'MidriseApartment'
    building_type_chs << 'HighriseApartment'
    building_type_chs << 'Hospital'
    building_type_chs << 'Outpatient'
    building_type_chs << 'Laboratory'
    building_type_chs << 'LargeDataCenterHighITE'
    building_type_chs << 'LargeDataCenterLowITE'
    building_type_chs << 'SmallDataCenterHighITE'
    building_type_chs << 'SmallDataCenterLowITE'
    building_type = OpenStudio::Measure::OSArgument.makeChoiceArgument('building_type', building_type_chs, true)
    building_type.setDisplayName('Building Type.')
    building_type.setDefaultValue('SmallOffice')
    args << building_type

    # Make an argument for the template
    template_chs = OpenStudio::StringVector.new
    template_chs << 'DOE Ref Pre-1980'
    template_chs << 'DOE Ref 1980-2004'
    template_chs << '90.1-2004'
    template_chs << '90.1-2007'
    # template_chs << '189.1-2009'
    template_chs << '90.1-2010'
    template_chs << '90.1-2013'
    template_chs << '90.1-2016'
    template_chs << 'NECB 2011'
    template = OpenStudio::Measure::OSArgument.makeChoiceArgument('template', template_chs, true)
    template.setDisplayName('Template.')
    template.setDefaultValue('90.1-2010')
    args << template

    # Make an argument for the climate zone
    climate_zone_chs = OpenStudio::StringVector.new
    climate_zone_chs << 'ASHRAE 169-2013-1A'
    # climate_zone_chs << 'ASHRAE 169-2013-1B'
    climate_zone_chs << 'ASHRAE 169-2013-2A'
    climate_zone_chs << 'ASHRAE 169-2013-2B'
    climate_zone_chs << 'ASHRAE 169-2013-3A'
    climate_zone_chs << 'ASHRAE 169-2013-3B'
    climate_zone_chs << 'ASHRAE 169-2013-3C'
    climate_zone_chs << 'ASHRAE 169-2013-4A'
    climate_zone_chs << 'ASHRAE 169-2013-4B'
    climate_zone_chs << 'ASHRAE 169-2013-4C'
    climate_zone_chs << 'ASHRAE 169-2013-5A'
    climate_zone_chs << 'ASHRAE 169-2013-5B'
    # climate_zone_chs << 'ASHRAE 169-2013-5C'
    climate_zone_chs << 'ASHRAE 169-2013-6A'
    climate_zone_chs << 'ASHRAE 169-2013-6B'
    climate_zone_chs << 'ASHRAE 169-2013-7A'
    # climate_zone_chs << 'ASHRAE 169-2013-7B'
    climate_zone_chs << 'ASHRAE 169-2013-8A'
    # climate_zone_chs << 'ASHRAE 169-2013-8B'
    climate_zone_chs << 'NECB HDD Method'
    climate_zone = OpenStudio::Measure::OSArgument.makeChoiceArgument('climate_zone', climate_zone_chs, true)
    climate_zone.setDisplayName('Climate Zone.')
    climate_zone.setDefaultValue('ASHRAE 169-2013-2A')
    args << climate_zone

    # Drop down selector for Canadian weather files.
    epw_files = OpenStudio::StringVector.new
    epw_files << 'Not Applicable'
    BTAP::Environment.get_canadian_weather_file_names.each { |file| epw_files << file }
    epw_file = OpenStudio::Measure::OSArgument.makeChoiceArgument('epw_file', epw_files, true)
    epw_file.setDisplayName('Climate File (NECB only)')
    epw_file.setDefaultValue('Not Applicable')
    args << epw_file

    return args
  end

  # Define what happens when the measure is run.
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # Use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # Assign the user inputs to variables that can be accessed across the measure
    building_type = runner.getStringArgumentValue('building_type', user_arguments)
    template = runner.getStringArgumentValue('template', user_arguments)
    climate_zone = runner.getStringArgumentValue('climate_zone', user_arguments)
    epw_file = runner.getStringArgumentValue('epw_file', user_arguments)

    # Turn debugging output on/off
    @debug = false

    # Open a channel to log info/warning/error messages
    @msg_log = OpenStudio::StringStreamLogSink.new
    if @debug
      @msg_log.setLogLevel(OpenStudio::Debug)
    else
      @msg_log.setLogLevel(OpenStudio::Info)
    end
    @start_time = Time.new
    @runner = runner

    # Make a directory to save the resulting models for debugging
    build_dir = "#{Dir.pwd}/output"
    if !Dir.exist?(build_dir)
      Dir.mkdir(build_dir)
    end

    # Set OSM folder
    osm_directory = ''
    if template == 'NECB 2011'
      osm_directory = "#{build_dir}/#{building_type}-#{template}-#{climate_zone}-#{epw_file}"
    else
      osm_directory = build_dir
    end
    if !Dir.exist?(osm_directory)
      Dir.mkdir(osm_directory)
    end

    # Versions of OpenStudio greater than 2.4.0 use a modified version of
    # openstudio-standards with different method calls.
    if OpenStudio::VersionString.new(OpenStudio.openStudioVersion) < OpenStudio::VersionString.new('2.4.3')
      model.create_prototype_building(building_type,
                                      template,
                                      climate_zone,
                                      epw_file,
                                      osm_directory,
                                      @debug)
    else
      reset_log
      template = 'NECB2011' if template == 'NECB 2011'
      prototype_creator = Standard.build("#{template}_#{building_type}")
      prototype_creator.model_create_prototype_model(climate_zone, epw_file, osm_directory, @debug, model)
    end

    log_msgs
    reset_log

    return true
  end # end the run method

  # Get all the log messages and put into output
  # for users to see.
  def log_msgs
    @msg_log.logMessages.each do |msg|
      # DLM: you can filter on log channel here for now
      if /openstudio.*/.match(msg.logChannel) # /openstudio\.model\..*/
        # Skip certain messages that are irrelevant/misleading
        next if msg.logMessage.include?('Skipping layer') || # Annoying/bogus "Skipping layer" warnings
                msg.logChannel.include?('runmanager') || # RunManager messages
                msg.logChannel.include?('setFileExtension') || # .ddy extension unexpected
                msg.logChannel.include?('Translator') || # Forward translator and geometry translator
                msg.logMessage.include?('UseWeatherFile') # 'UseWeatherFile' is not yet a supported option for YearDescription

        # Report the message in the correct way
        if msg.logLevel == OpenStudio::Info
          @runner.registerInfo(msg.logMessage)
        elsif msg.logLevel == OpenStudio::Warn
          @runner.registerWarning("[#{msg.logChannel}] #{msg.logMessage}")
        elsif msg.logLevel == OpenStudio::Error
          @runner.registerError("[#{msg.logChannel}] #{msg.logMessage}")
        elsif msg.logLevel == OpenStudio::Debug && @debug
          @runner.registerInfo("DEBUG - #{msg.logMessage}")
        end
      end
    end
    @runner.registerInfo("Total Time = #{(Time.new - @start_time).round}sec.")
  end
end # end the measure

# this allows the measure to be use by the application
CreateDOEPrototypeBuildingCopy.new.registerWithApplication
