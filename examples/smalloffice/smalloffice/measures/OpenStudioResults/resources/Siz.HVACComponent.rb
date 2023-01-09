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

class OpenStudio::Model::HVACComponent
  def maxHeatingCapacity
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxHeatingCapacity
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxCoolingCapacity
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxCoolingCapacity
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxAirFlowRate
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxAirFlowRate
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxWaterFlowRate
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxWaterFlowRate
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def ratedPower
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.ratedPower
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxHeatingCapacityAutosized
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxHeatingCapacityAutosized
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxCoolingCapacityAutosized
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxCoolingCapacityAutosized
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxAirFlowRateAutosized
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxAirFlowRateAutosized
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def maxWaterFlowRateAutosized
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.maxWaterFlowRateAutosized
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def ratedPowerAutosized
    comp = cast_to_concrete_type
    return OpenStudio::OptionalDouble.new if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.ratedPowerAutosized
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return OpenStudio::OptionalDouble.new
    end
  end

  def performanceCharacteristics
    comp = cast_to_concrete_type
    return [] if comp.nil?
    if comp.respond_to?(__method__.to_s)
      return comp.performanceCharacteristics
    else
      # puts "#{__method__.to_s} not implemented for #{iddObject.type.name}"
      return []
    end
  end
end
