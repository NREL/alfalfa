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

class AlfalfaBRICKTest < Minitest::Test
  def setup
    # Make a directory to save the resulting models
    @test_dir = "#{File.dirname(__FILE__)}/output"
    if !Dir.exist?(@test_dir)
      Dir.mkdir(@test_dir)
    end
    @input_dir = "#{File.dirname(__FILE__)}/input"

  end

  # Create a set of models, return a list of failures
  def test_brick_import
    ab = AlfalfaBRICK.new
    puts ab.find_points(File.join(@input_dir, 'in.ttl'))
  end

  def test_input_creation
    # translator = OpenStudio::OSVersion::VersionTranslator.new
    # path = OpenStudio::Path.new(File.join(@input_dir, 'in.osm'))
    # model = translator.loadModel(path)
    # assert((not model.empty?))
    # model = model.get
    path = OpenStudio::Path.new(File.join(@input_dir, 'smalloffice.idf'))
    workspace = OpenStudio::Workspace.load(path)
    assert((not workspace.empty?))
    workspace = workspace.get

    ab = AlfalfaBRICK.new
    ab.create_input(workspace, 'psz-ac_1:6 supply equipment outlet node', 'Timestep')
  end

  def test_python_binding
    path = OpenStudio::Path.new(File.join(@input_dir, 'smalloffice.idf'))
    ab = AlfalfaBRICK.new
    ttlout = ab.extract_graph(path)
    puts ("Created graph at #{ttlout}")
  end

  def test_entireRun
    path = OpenStudio::Path.new(File.join(@input_dir, 'smalloffice.idf'))
    workspace = OpenStudio::Workspace.load(path)
    assert((not workspace.empty?))
    workspace.get.save(File.join(@test_dir, 'test.idf'), true)
    ab = AlfalfaBRICK.new

    # Generate graph
    temp_files = "#{File.dirname(__FILE__)}/temp"
    if !Dir.exist?(temp_files)
      Dir.mkdir(temp_files)
    end

    temp_idf = File.join(temp_files, 'initial.idf')
    workspace.get.save(temp_idf, true)
    ttlpath = ab.extract_graph(temp_idf)

    # Find all sensors and setpoints
    points = ab.find_points(ttlpath)
    puts points
    ab.create_io(workspace.get, points, "TimeStep")

    temp_idf = File.join(temp_files, 'final.idf')
    workspace.get.save(temp_idf, true)
  end

end
