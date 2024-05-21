require_relative 'alfalfa_mixin'
require_relative 'utils'
module OpenStudio
  module Alfalfa
    ##
    # EnergyPlusMixin
    #
    # Mixin to include when developing an EnergyPlus Measure
    module EnergyPlusMixin
      include OpenStudio::Alfalfa::AlfalfaMixin
      include OpenStudio::Alfalfa::Utils

      # Get first node from NodeList
      #
      # @param [String] node NodeList id
      def get_node_from_nodelist(node)
        node_list_object = @workspace.getObjectByTypeAndName('NodeList'.to_IddObjectType, node)
        return node_list_object.get.getField(1).get if node_list_object.is_initialized

        node
      end

      def _add_meter_to_model(meter_name)
        STDERR.puts "adding meter #{meter_name}"
        STDERR.puts "finding objects of type #{'Output:Meter:MeterFileOnly'.to_IddObjectType}"
        output_meter_file_only_objects = @workspace.getObjectsByType('Output:Meter:MeterFileOnly'.to_IddObjectType)
        STDERR.puts output_meter_file_only_objects.length
        output_meter_file_only_objects.each do | output_meter_object |
          STDERR.puts "found meter #{output_meter_object}"
          if output_meter_object.getString(1) == meter_name
            STDERR.puts "removing meter #{meter_name}"
            output_meter_object.remove()
          end
        end
        output_meter_string = "
        Output:Meter,
          #{meter_name},
          Timestep;"
        output_meter_object = OpenStudio::IdfObject.load(output_meter_string).get
        @workspace.addObject(output_meter_object)
      end

      def _add_variable_to_plugin(variable_name)
        _create_python_plugin_variables if @python_plugin_variables.nil?
        @python_plugin_variables.setString(1+ @python_plugin_variables_count, variable_name)
        @python_plugin_variables_count += 1
        STDERR.puts @python_plugin_variables
      end

      def _create_python_plugin_variables
        python_plugin_variables_string = "
        PythonPlugin:Variables,
          #{create_ems_str(name)};"
        python_plugin_variables_object = OpenStudio::IdfObject.load(python_plugin_variables_string).get
        @python_plugin_variables = @workspace.addObject(python_plugin_variables_object).get
        @python_plugin_variables_count = 0
      end

      def run(workspace, runner, user_arguments)
        super(workspace, runner, user_arguments)
        @workspace = workspace
        @python_plugin_variables = nil
        @points = []
      end
    end
  end
end
