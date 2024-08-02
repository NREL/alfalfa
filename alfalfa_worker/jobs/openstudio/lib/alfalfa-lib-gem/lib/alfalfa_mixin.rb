require_relative 'utils'
require 'json'
module OpenStudio
  module Alfalfa
    ##
    # Base mixin for managing alfalfa points
    #
    module AlfalfaMixin
      include OpenStudio::Alfalfa::Utils
      # Create reports of input and outputs for alfalfa
      # Must be executed at the end of the measure to expose points in alfalfa
      def report_inputs_outputs
        @inputs.each do |input|
          next if input.echo.nil?
          next if @outputs.include? input.echo

          @outputs.append(input.echo)
        end

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
      def register_input(input)
        if input.is_a? OpenStudio::Alfalfa::Input
          @inputs.append(input)
        else
          input = OpenStudio::Alfalfa::Input.new(input)
          register_input(input)
        end
        input
      end

      # Find an input by it's associated object name
      #
      # @param [String] name Name of input to find
      #
      # @return [Input]
      def get_input_by_name(name)
        @inputs.each do |input|
          next unless input.object.name.get == name

          return input
        end
        nil
      end

      # Register an output for inclusion in alfalfa
      #
      # @param output [IdfObject, ModelObject, Output] output to register
      # May be:
      # - Output:Variable
      # - EnergyManagementSystem:OutputVariable
      # - OS:Output:Variable
      # - OS:EnergyManagementSystem:OutputVariable
      # or:
      # - OpenStudio::Alfalfa::Output
      #
      # @return [Output]
      def register_output(output)
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
