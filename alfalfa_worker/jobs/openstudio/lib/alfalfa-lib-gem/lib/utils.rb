require 'openstudio'
module OpenStudio
  module Alfalfa
    ##
    # This module provides utility functions
    # for alfalfa and openstudio
    module Utils
      # Get Idd Type
      # get the Idd type of objects in either an OSW of IDF context
      #
      # @param [ModelObject, IdfObject] object Object to get type of
      #
      # @return [IddType]
      def get_idd_type(object)
        if object.is_a? OpenStudio::Model::ModelObject
          object.iddObjectType
        elsif object.is_a? OpenStudio::IdfObject
          object.iddObject.type
        else
          raise "cannot get idd_type of #{object.class}"
        end
      end

      # return string formatted with no spaces or '-' (can be used as EMS var name)
      # strings beginning with numbers will be prepended with '_'
      # @param [String] id String to process into an EMS valid string
      #
      # @return [String]
      def create_ems_str(id)
        id = id.gsub(/[\s-]/, '_')
        id = id.gsub(/[^\w]/, '_')
        id = "_#{id}" if (id =~ /[0-9].*/) == 0
        id
      end
    end
  end
end
