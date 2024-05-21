require 'securerandom'
module OpenStudio
  module Alfalfa
    ##
    # Point
    # Base type for input and output point in alfalfa
    class Point
      attr_reader :input, :output

      # @param [IdfObject, ModelObject] object
      def initialize(input, output)
        @hash = {}
        @hash['id'] = SecureRandom.uuid
        @input = input
        @output = output
      end

      def input=(component)
        if component.is_input_capable
          @input = component
        else
          raise "#{component.class.name} is not capable of providing an input"
        end
      end

      def output=(component)
        if component.is_output_capable
          @output = component
        else
          raise "#{component.class.name} is not capable of providing an output"
        end
      end

      # Unique identifier of point
      #
      # @return [String]
      def id
        @hash['id']
      end

      def id=(id)
        @hash['id'] = id
      end

      # Display name used by Alfalfa
      #
      # @return [String]
      def display_name
        @hash['display_name']
      end

      def display_name=(display_name)
        @hash['display_name'] = display_name
      end

      def units=(units)
        @hash['units'] = units
      end

      # Units for point
      #
      # @return [String]
      def units
        @hash['units']
      end

      # Add zone that point is related to
      #
      # @param zone [String]
      def add_zone(zone)
        if @hash.key? 'zone'
          @hash['zone'].append(zone)
        else
          @hash['zone'] = [zone]
        end
      end

      # Get dictionary of point
      # This is used when compiling reports
      #
      # @return [Hash]
      def to_dict
        if !@input.nil?
          puts @input
          @hash["input"] = @input.to_dict
        end
        if !@output.nil?
          puts @output
          @hash["output"] = @output.to_dict
        end
        @hash
      end
    end
  end
end
