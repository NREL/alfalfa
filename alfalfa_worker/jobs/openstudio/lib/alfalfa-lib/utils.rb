require 'openstudio'
module OpenStudio
  module Alfalfa
    ##
    # This module provides utility functions
    # for alfalfa and openstudio
    module Utils
      def get_idd_type(object)
        # Get Idd Type
        # get the Idd type of objects in either an OSW of IDF context
        #
        # @param [ModelObject, IdfObject] object Object to get type of
        #
        # @return [IddType]
        if object.is_a? OpenStudio::Model::ModelObject
          object.iddObjectType
        elsif object.is_a? OpenStudio::IdfObject
          object.iddObject.type
        else
          raise "cannot get idd_type of #{object.class}"
        end
      end

      def create_ems_str(id)
        # return string formatted with no spaces or '-' (can be used as EMS var name)
        # strings beginning with numbers will be prepended with '_'
        # @param [String] id String to process into an EMS valid string
        id = id.gsub(/[\s-]/, '_')
        id = "_#{id}" if !!(id =~ /[0-9].*/)
        id
      end
    end
  end
end
