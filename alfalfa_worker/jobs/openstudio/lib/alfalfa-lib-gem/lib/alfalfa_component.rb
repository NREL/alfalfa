module OpenStudio
  module Alfalfa
    class Component
      attr_reader :parameters

      def initialize(**parameters)
        @parameters = parameters
      end

      def is_input_capable
        raise "is_input_capable not implemented"
      end

      def is_output_capable
        raise "is_output_capable not implemented"
      end

      def to_dict
        raise "to_dict not implemented"
      end
    end

    class GlobalVariable < Component
      def initialize(var_name)
        super(var_name: var_name)
      end
      def is_input_capable
        true
      end

      def is_output_capable
        true
      end

      def to_dict
        return {type: "GlobalVariable", parameters: @parameters}
      end
    end

    class InternalVariable < Component
      def initialize(variable_type, variable_key)
        super(variable_type: variable_type, variable_key: variable_key)
      end

      def is_input_capable
        false
      end

      def is_output_capable
        true
      end

      def to_dict
        return {type: "InternalVariable", parameters: @parameters}
      end
    end

    class OutputVariable < Component
      def initialize(variable_name, variable_key)
        super(variable_name: variable_name, variable_key: variable_key)
      end

      def is_input_capable
        false
      end

      def is_output_capable
        true
      end

      def to_dict
        return {type: "OutputVariable", parameters: @parameters}
      end
    end

    class Meter < Component
      def initialize(meter_name)
        super(meter_name: meter_name)
      end

      def is_input_capable
        false
      end

      def is_output_capable
        true
      end

      def to_dict
        return {type: "Meter", parameters: @parameters}
      end
    end

    class Actuator < Component
      def initialize(component_type, control_type, actuator_key)
        super(component_type: component_type, control_type: control_type, actuator_key: actuator_key)
      end

      def is_input_capable
        true
      end

      def is_output_capable
        true
      end

      def to_dict
        return {type: "Actuator", parameters: @parameters}
      end
    end
  end
end
