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

class OpenStudio::Model::ModelObject
  # Convert object to a concrete class if possible
  # @return [Object, nil] returns nil if the object was already
  # of its concrete class, returns the object casted to its concrete
  # class if it was casted successfully.
  def cast_to_concrete_type
    # puts "Casting '#{name}' to concrete type from #{caller_locations(1,1)[0].label}"
    # Get the class type and the IDD object type
    comp_class = self.class.name.to_s.gsub('OpenStudio::Model::', '')
    comp_type = iddObject.type.valueDescription.gsub('OS:', '').delete(':')
    case comp_type
    when 'CoilCoolingLowTemperatureRadiantVariableFlow'
      comp_type = 'CoilCoolingLowTempRadiantVarFlow'
    when 'CoilHeatingLowTemperatureRadiantVariableFlow'
      comp_type = 'CoilHeatingLowTempRadiantVarFlow'
    when 'ZoneHVACLowTemperatureRadiantVariableFlow'
      comp_type = 'ZoneHVACLowTempRadiantVarFlow'
    end
    # If the class type and the IDD object type are identical,
    # this means that the object is already of the concrete class.
    if comp_class == comp_type
      # puts "INFO: #{name} of type #{comp_type} is already concrete"
      return nil
    end
    # Cast the object to its concrete class type
    cast_method = "to_#{comp_type}"
    if respond_to?(cast_method)
      return public_send(cast_method).get
    else
      puts "ERROR: #{name} of type #{comp_type} cannot be made concrete using #{cast_method}"
      # raise "ERROR: #{name} of type #{comp_type} cannot be made concrete using #{cast_method}"
      return nil
    end
  end
end
