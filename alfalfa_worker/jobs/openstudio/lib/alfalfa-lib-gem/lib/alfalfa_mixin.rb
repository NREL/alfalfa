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
      def alfalfa_generate_reports
        points_dict = {}
        @points.each do |point|
          hash = point.to_dict
          points_dict[hash['id']] = hash
          components = [point.input, point.output]
          components.each do |component|
            if component.class == OpenStudio::Alfalfa::Meter
              STDERR.puts component.parameters
              _add_meter_to_model(component.parameters[:meter_name])
            elsif component.class == OpenStudio::Alfalfa::GlobalVariable
              _add_variable_to_plugin(component.parameters[:var_name])
            end
          end
        end

        File.open('./report_points.json', 'w') do |f|
          JSON.dump(points_dict, f)
        end
      end

      # Add a point for inclusion in alfalfa
      #
      # @param [Point] point to add
      #
      # @return [Point]
      def alfalfa_add_point(point)
        @points.append(point)
        point
      end

      def alfalfa_create_global_variable(var_name)
        global_variable = OpenStudio::Alfalfa::GlobalVariable.new(var_name)
        point = OpenStudio::Alfalfa::Point.new(global_variable, global_variable)
        point.display_name = var_name
        point.id = str_to_id(point.display_name)
        return point
      end

      def alfalfa_add_global_variable(var_name)
        point = alfalfa_create_global_variable(var_name)
        alfalfa_add_point(point)
        return point
      end

      def alfalfa_create_internal_variable(variable_type, variable_key)
        internal_variable = OpenStudio::Alfalfa::InternalVariable.new(variable_type, variable_key)
        point = OpenStudio::Alfalfa::Point.new(nil, internal_variable)
        point.display_name = "#{variable_key} #{variable_type}"
        point.id = str_to_id(output.display_name)
        return point
      end

      def alfalfa_add_internal_variable(variable_type, variable_key)
        point = alfalfa_create_internal_variable(variable_type, variable_key)
        alfalfa_add_point(point)
        return point
      end

      def alfalfa_create_output_variable(variable_name, variable_key)
        output_variable = OpenStudio::Alfalfa::OutputVariable.new(variable_name, variable_key)
        point = OpenStudio::Alfalfa::Point.new(nil,  output_variable)
        point.display_name = "#{variable_name} #{variable_key}"
        point.id = str_to_id(point.display_name)
        return point
      end

      def alfalfa_add_output_variable(variable_name, variable_key)
        point = alfalfa_create_output_variable(variable_name, variable_key)
        alfalfa_add_point(point)
        return point
      end

      def alfalfa_create_meter(meter_name)
        meter = OpenStudio::Alfalfa::Meter.new(meter_name)
        point = OpenStudio::Alfalfa::Point.new(nil, meter)
        point.display_name = meter_name
        point.id = str_to_id(meter_name)
        return point
      end

      def alfalfa_add_meter(meter_name)
        point = alfalfa_create_meter(meter_name)
        alfalfa_add_point(point)
        return point
      end

      def alfalfa_create_actuator(component_type, control_type, actuator_key)
        actuator = OpenStudio::Alfalfa::Actuator.new(component_type, control_type, actuator_key)
        point = OpenStudio::Alfalfa::Point.new(actuator, actuator)
        point.display_name = "#{actuator_key} #{component_type} #{control_type}"
        point.id = str_to_id(point.display_name)
        return point
      end

      def alfalfa_add_actuator(component_type, control_type, actuator_key)
        point = alfalfa_create_actuator(component_type, control_type, actuator_key)
        alfalfa_add_point(point)
        return point
      end
    end
  end
end
