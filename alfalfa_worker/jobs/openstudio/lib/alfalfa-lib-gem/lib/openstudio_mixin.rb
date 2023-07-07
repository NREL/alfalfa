require 'alfalfa_mixin'
module OpenStudio
  module Alfalfa
    module OpenStudioMixin
      ##
      # OpenStudioMixin
      #
      # Mixin to include when developing an Model Measure
      include OpenStudio::Alfalfa::AlfalfaMixin

      def run(model, runner, user_arguments)
        super(model, runner, user_arguments)
        @model = model
        @calling_point_manager = nil
        @inputs = []
        @outputs = []
      end
    end
  end
end
