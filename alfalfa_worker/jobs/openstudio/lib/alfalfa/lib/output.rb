require 'securerandom'
require 'openstudio'
require_relative 'utils'
require_relative 'point'
module OpenStudio
  module Alfalfa
    class Output < Point
      ##
      # Output
      #
      # Class which represents an Output point to Alfalfa
      include OpenStudio::Alfalfa::Utils
      def initialize(output_object)
        super(output_object)
        output_type = get_idd_type(@object)

        case output_type
        when 'Output:Variable'.to_IddObjectType
          @hash['component'] = @object.getString(0).get
          @hash['variable'] = @object.getString(1).get
        when 'EnergyManagementSystem:OutputVariable'.to_IddObjectType
          @hash['component'] = 'EMS'
          self.display_name = @object.name.get
          @hash['variable'] = @object.getString(0).get
          self.units = @object.getString(5).get
        when 'OS:Output:Variable'.to_IddObjectType
          @hash['component'] = @object.keyValue
          @hash['variable'] = @object.variableName
          self.display_name = @object.name.get
        when 'OS:EnergyManagementSystem:OutputVariable'.to_IddObjectType
          @hash['component'] = 'EMS'
          @hash['variable'] = @object.emsVariableName
          self.display_name = @object.name.get
        else
          raise "#{output_type.valueDescription} is not a valid output type"
        end
      end

      def component
        @hash['component']
      end

      def variable
        @hash['variable']
      end
    end
  end
end
