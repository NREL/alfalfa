require 'securerandom'
require_relative 'utils'
require_relative 'point'
module OpenStudio
  module Alfalfa
    ##
    # Input
    #
    # Class which represents an Input point to Alfalfa
    class Input < Point
      include OpenStudio::Alfalfa::Utils
      attr_reader :input_object

      def initialize(input_object)
        super(input_object)

        input_type = get_idd_type(input_object)
        name = input_object.name.get

        case input_type
        when 'ExternalInterface:Actuator'.to_IddObjectType
          @hash['actuator'] = name
          self.actuator = input_object
        when 'ExternalInterface:Variable'.to_IddObjectType
          @hash['variable'] = name
        when 'ExternalInterface:Schedule'.to_IddObjectType
          @hash['schedule'] = name
        when 'OS:ExternalInterface:Variable'.to_IddObjectType
          @hash['variable'] = name
        when 'OS:ExternalInterface:Schedule'.to_IddObjectType
          @hash['schedule'] = name
        when 'OS:ExternalInterface:Actuator'.to_IddObjectType
          @hash['actuator'] = name
          self.actuator = input_object
        else
          raise "#{input_type.valueDescription} is not a valid input type"
        end
        self.display_name = name
      end

      def actuator=(actuator_object)
        actuator_type = get_idd_type(actuator_object)

        actuator_types = ['ExternalInterface:Actuator'.to_IddObjectType,
                          'OS:EnergyManagementSystem:Actuator'.to_IddObjectType,
                          'EnergyManagementSystem:Actuator'.to_IddObjectType]

        unless actuator_types.include? actuator_type
          raise "#{actuator_type.valueDescription} is not a valid actuator type"
        end

        @hash['actuated_component'] = actuator_object.getString(1).get
        @hash['actuated_component_type'] = actuator_object.getString(2).get
        @hash['actuated_component_control_type'] = actuator_object.getString(3).get
      end

      def enable_variable=(enable_variable)
        enable_variable = enable_variable.object if enable_variable.instance_of? OpenStudio::Alfalfa::Input

        enable_variable_type = get_idd_type(enable_variable)
        enable_variable_types = ['ExternalInterface:Variable'.to_IddObjectType,
                                 'OS:ExternalInterface:Variable'.to_IddObjectType]

        unless enable_variable_types.include? enable_variable_type
          raise "#{enable_variable_type.valueDescription} is an invalid enable variable type"
        end

        @hash['enable_variable'] = enable_variable.name.get
      end
    end
  end
end
