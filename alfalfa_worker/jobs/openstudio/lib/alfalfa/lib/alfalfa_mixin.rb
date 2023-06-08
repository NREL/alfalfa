require_relative 'utils'
module OpenStudio
  module Alfalfa
    module AlfalfaMixin
      ##
      # Base mixin for managing alfalfa points
      #

      include OpenStudio::Alfalfa::Utils
      def report_inputs_outputs
        # Create reports of input and outputs for alfalfa
        # Must be executed at the end of the measure to expose points in alfalfa

        inputs_dict = {}
        outputs_dict = {}
        @inputs.each do |input|
          hash = input.to_dict
          inputs_dict[hash['id']] = hash
        end
        @outputs.each do |output|
          hash = output.to_dict
          outputs_dict[hash['id']] = hash
        end

        File.open('./report_inputs.json', 'w') do |f|
          JSON.dump(inputs_dict, f)
        end
        File.open('./report_outputs.json', 'w') do |f|
          JSON.dump(outputs_dict, f)
        end
      end

      def register_input(input)
        # Register an input for inclusion in alfalfa
        #
        # @param [IdfObject, ModelObject, Input] input to register
        # May be:
        # - ExternalInterface:Actuator
        # - ExternalInterface:Variable
        # - ExternalInterface:Schedule
        # - OS:ExternalInterface:Variable
        # - OS:ExternalInterface:Schedule
        # - OS:ExternalInterface:Actuator
        # or:
        # - OpenStudio::Alfalfa::Input
        #
        # @return [Input]
        if input.is_a? OpenStudio::Alfalfa::Input
          @inputs.append(input)
        else
          input = OpenStudio::Alfalfa::Input.new(input)
          register_input(input)
        end
        input
      end

      def get_input_by_name(name)
        # Find an input by it's associated object name
        #
        # @param [String] name Name of input to find
        #
        # @return [Input]
        @inputs.each do |input|
          next unless input.object.name.get == name

          return input
        end
        nil
      end

      def register_output(output)
        # Register an output for inclusion in alfalfa
        #
        # @param [IdfObject, ModelObject, Output] input to register
        # May be:
        # - Output:Variable
        # - EnergyManagementSystem:OutputVariable
        # - OS:Output:Variable
        # - OS:EnergyManagementSystem:OutputVariable
        # or:
        # - OpenStudio::Alfalfa::Output
        #
        # @return [Output]
        if output.is_a? OpenStudio::Alfalfa::Output
          @outputs.append(output)
        else
          output = OpenStudio::Alfalfa::Output.new(output)
          register_output(output)
        end
        output
      end
    end
  end
end
