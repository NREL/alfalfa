########################################################################################################################
#  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
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

# The purpose of this file is to combine the default Alfalfa measures,
# to a user submitted workflow
#
# ARGV[0] is the default Alfalfa osw
# ARGV[1] is the user submitted osw

require 'fileutils'

alfalfa_osw_path = OpenStudio::Path.new(ARGV[0])
alfalfa_osw = OpenStudio::WorkflowJSON.new(alfalfa_osw_path)

submitted_osw_path = OpenStudio::Path.new(ARGV[1])
submitted_osw = OpenStudio::WorkflowJSON.new(submitted_osw_path)

model_measure_type = OpenStudio::MeasureType.new('ModelMeasure')
alfalfa_steps = alfalfa_osw.getMeasureSteps(model_measure_type)

# Given a WorkflowJSON, return the local measures directory relative to the osw
# The goal is to avoid any global directories that are outside of the osw directory
def measures_directory(osw)
  measures_dir = nil
  osw.measurePaths().each do |p|
    if p.has_relative_path()
      measures_dir = p
      break
    end
  end
  return OpenStudio::toString(osw.absoluteRootDir() / measures_dir)
end


alfalfa_steps.each do |step|
  bcl_measure = alfalfa_osw.getBCLMeasure(step).get()
  bcl_measure_path = OpenStudio::toString(bcl_measure.directory())
  FileUtils.cp_r(bcl_measure_path, measures_directory(submitted_osw))
end

submitted_steps = submitted_osw.getMeasureSteps(model_measure_type)
new_steps = submitted_steps + alfalfa_steps
submitted_osw.setMeasureSteps(model_measure_type, new_steps)

submitted_osw.save()
