require 'securerandom'
module OpenStudio
  module Alfalfa
    ##
    # Point
    # Base type for input and output point in alfalfa
    class Point
      attr_reader :echo, :object

      # @param [IdfObject, ModelObject] object
      def initialize(object)
        @hash = {}
        @hash['id'] = SecureRandom.uuid
        @object = object
      end

      # Unique identifier of point
      #
      # @return [String]
      def id
        @hash['id']
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

      def echo=(output)
        @echo = output
        @hash['echo_id'] = output.id
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
        @hash
      end
    end
  end
end
