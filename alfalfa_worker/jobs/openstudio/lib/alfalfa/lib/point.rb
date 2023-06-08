require 'securerandom'
module OpenStudio
  module Alfalfa
    class Point
      ##
      # Point
      # Base type for input and output point in alfalfa

      attr_reader :echo, :object

      def initialize(object)
        # @param [IdfObject, ModelObject] object
        @hash = {}
        @hash['id'] = SecureRandom.uuid
        @object = object
      end

      def id
        @hash['id']
      end

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

      def units
        @hash['units']
      end

      def add_zone(zone)
        if @hash.key? 'zone'
          @hash['zone'].append(zone)
        else
          @hash['zone'] = [zone]
        end
      end

      def to_dict
        @hash
      end
    end
  end
end
