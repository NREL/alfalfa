require 'alfalfa_mixin'
module OpenStudio
  module Alfalfa
    ##
    # OpenStudioMixin
    #
    # Mixin to include when developing an Model Measure
    module OpenStudioMixin
      include OpenStudio::Alfalfa::AlfalfaMixin

      # Create Output Variable
      #
      # @param [String] key Key of Output Variable
      # @param [String] var Variable of Output Variable
      #
      # @return [Output]
      def create_output_variable(key, var)
        output_variable = OpenStudio::Model::OutputVariable.new(create_ems_str("#{key}_#{var}"), @model)
        output_variable.setKeyValue(key)
        output_variable.setVariableName(var)

        OpenStudio::Alfalfa::Output.new(output_variable)
      end

      # Create EMS Output Variable
      #
      # @param [String, ModelObject] variable EMS name of variable to connect to Output Variable
      # @param [String] unit Unit of output
      #
      # @return [Output]
      def create_ems_output_variable(variable, unit = 'C')
        output_variable = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(@model, variable)
        output_variable.setUnits(unit)
        Output.new(output_variable)
      end

      # Create External Interface Variable
      #
      # @param [String] name Name of external variable to create
      # @param [Number] initial_value Initial value of external variable
      #
      # @return [Input]
      def create_external_variable(name, initial_value = 0)
        external_variable = OpenStudio::Model::ExternalInterfaceVariable.new(@model, create_ems_str(name),
                                                                             initial_value)
        external_variable.setExportToBCVTB(false)
        Input.new(external_variable)
      end

      # Create enabled input to actuate an EMS variable.
      # This method creates an external variable with the specified name
      # and an EMS program to copy the value to the specified variable if enabled
      # or the default value otherwise
      #
      # @param [String] name Name of input to create
      # @param [String] variable_name EMS name of variable to control
      # @param [String] default Value to have when not enabled. Default to null for actuator control
      #
      # @return [Input]
      def create_enabled_input(name, variable_name, default = 'Null')
        alfalfa_input = create_external_variable(name)
        enable_name = create_ems_str("#{name}_Enable")
        alfalfa_input_enable = create_external_variable(enable_name)
        new_program = OpenStudio::Model::EnergyManagementSystemProgram.new(@model)
        new_program.setLines(["IF #{enable_name},",
                              "SET #{variable_name} = #{name},",
                              'ELSE,',
                              "SET #{variable_name} = #{default},",
                              'ENDIF'])
        register_program(new_program)
        alfalfa_input.enable_variable = alfalfa_input_enable
        alfalfa_input
      end

      # Create actuator
      #
      # @param name [String] Name of actuator to create
      # @param component [ModelObject] component to actuate
      # @param component_type[String] Type of component
      # @param control_type [String] Type of control
      # @param external [Boolean] When true an external interface variable with {name} will be created and returned
      #
      # @return [ModelObject, Input]
      def create_actuator(name, component, component_type, control_type, external = false)
        if external
          actuator_name = create_ems_str("#{name}_actuator")
          actuator_object = create_actuator(actuator_name, component, component_type, control_type)
          input = create_enabled_input(name, actuator_name)
          input.actuator = actuator_object
          output = create_ems_output_variable(actuator_object)
          input.echo = output
          input
        else
          OpenStudio::Model::EnergyManagementSystemActuator.new(component, component_type, control_type)
        end
      end

      def create_calling_point
        @calling_point_manager = OpenStudio::Model::EnergyManagementSystemProgramCallingManager.new(@model)
        @calling_point_manager.setCallingPoint('EndOfZoneTimestepBeforeZoneReporting')
      end

      def register_program(program)
        create_calling_point if @calling_point_manager.nil?
        @calling_point_manager.addProgram(program)
      end

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
