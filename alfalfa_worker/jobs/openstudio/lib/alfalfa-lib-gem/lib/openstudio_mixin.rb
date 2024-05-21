require 'alfalfa_mixin'
module OpenStudio
  module Alfalfa
    ##
    # OpenStudioMixin
    #
    # Mixin to include when developing an Model Measure
    module OpenStudioMixin
      include OpenStudio::Alfalfa::AlfalfaMixin

      def _add_meter_to_model(meter_name)
        output_meter_object = OpenStudio::Model::OutputMeter.new(@model)
        output_meter_object.setString(1, meter_name)
      end


      def run(model, runner, user_arguments)
        super(model, runner, user_arguments)
        @model = model
        @python_plugin_variables = nil
        @points = []
      end
    end
  end
end
