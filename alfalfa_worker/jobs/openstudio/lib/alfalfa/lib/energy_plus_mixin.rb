require_relative 'alfalfa_mixin'
require_relative 'utils'
module OpenStudio
  module Alfalfa
    module EnergyPlusMixin
      ##
      # EnergyPlusMixin
      #
      # Mixin to include when developing an EnergyPlus Measure
      include OpenStudio::Alfalfa::AlfalfaMixin
      include OpenStudio::Alfalfa::Utils

      def get_node_from_nodelist(node)
        # Get first node from NodeList
        #
        # @param [String] node NodeList id
        node_list_object = @workspace.getObjectByTypeAndName('NodeList'.to_IddObjectType, node)
        if node_list_object.is_initialized
          return node_list_object.get.getField(1).get
        else
          return node
        end
      end

      def create_output_variable(key, var)
        # Create Output Variable
        #
        # @param[String] key Key of Output Variable
        # @param[String] var Variable of Output Variable
        #
        # @return [Output]
        output_variable_string = "
        Output:Variable,
          #{key},
          #{var},
          Timestep;"
        output_variable_object = OpenStudio::IdfObject.load(output_variable_string).get
        OpenStudio::Alfalfa::Output.new(@workspace.addObject(output_variable_object).get)
      end

      def create_ems_output_variable(name, variable, unit = 'C')
        # Create EMS Output Variable
        #
        # @param[String] name Name of EMS Output Variable to create
        # @param[String] variable EMS name of variable to connect to Output Variable
        # @param[String] unit Unit of output
        #
        # @return [Output]
        output_variable_string = "
        EnergyManagementSystem:OutputVariable,
          #{name},
          #{variable},
          Averaged,
          SystemTimestep,
          ,
          #{unit};"
        output_variable_object = OpenStudio::IdfObject.load(output_variable_string).get
        OpenStudio::Alfalfa::Output.new(@workspace.addObject(output_variable_object).get)
      end

      def create_external_variable(name, initial_value = 0)
        # Create External Interface Variable
        #
        # @param [String] name Name of external variable to create
        # @param [Number] initial_value Initial value of external variable
        #
        # @return [Input]
        new_external_variable_string = "
        ExternalInterface:Variable,
          #{create_ems_str(name)},             !- Name,
          #{initial_value};    !- Initial value
          "
        new_external_variable_object = OpenStudio::IdfObject.load(new_external_variable_string).get
        input = OpenStudio::Alfalfa::Input.new(@workspace.addObject(new_external_variable_object).get)
        input.display_name = name
        input
      end

      def create_enabled_input(name, variable_name, default="Null")
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
        program_name = create_ems_str("#{name}_program")
        alfalfa_input = create_external_variable(name)
        enable_name = create_ems_str("#{name}_Enable")
        alfalfa_input_enable = create_external_variable(enable_name)
        new_program_string = "
        EnergyManagementSystem:Program,
          #{program_name},           !- Name
          IF #{enable_name},
          SET #{variable_name} = #{name},
          ELSE,
          SET #{variable_name} = #{default},
          ENDIF;
          "
        new_program_object = OpenStudio::IdfObject.load(new_program_string).get
        @workspace.addObject(new_program_object)
        register_program(program_name)
        alfalfa_input.enable_variable = alfalfa_input_enable
        alfalfa_input
      end

      def create_actuator(name, component, component_type, control_type, external=false)
        # Create actuator
        #
        # @param [String] name Name of actuator to create
        # @param [String] component Name of component to actuate
        # @param [String] component_type Type of component
        # @param [String] control_type Type of control
        # @param [Boolean] external When true an external interface variable with {name} will be created and returned
        #
        # @return [IdfObject, (Input, Output)]
        if external
          actuator_name = create_ems_str("#{name}_actuator")
          actuator_object = create_actuator(actuator_name, component, component_type, control_type)
          input = create_enabled_input(name, actuator_name)
          input.actuator = actuator_object
          echo_name = create_ems_str("#{actuator_name}_echo")
          output = create_ems_output_variable(echo_name, actuator_name)
          input.echo = output
          return input, output
        else
          new_actuator_string = "
          EnergyManagementSystem:Actuator,
            #{name},                 !- Name
            #{component},            !- Actuated Component Unique Name
            #{component_type},       !- Actuated Component Type
            #{control_type};         !- Actuated Component Control Type
            "
          new_actuator_object = OpenStudio::IdfObject.load(new_actuator_string).get
          @workspace.addObject(new_actuator_object).get
        end
      end

      def create_calling_point
        new_calling_manager_string = "
        EnergyManagementSystem:ProgramCallingManager,
          #{create_ems_str(name())}_calling_point,          !- Name
          EndOfZoneTimestepBeforeZoneReporting;    !- EnergyPlus Model Calling Point
          "
        new_calling_manager_object = OpenStudio::IdfObject.load(new_calling_manager_string).get
        @calling_point_manager = @workspace.addObject(new_calling_manager_object).get
        @program_count = 0
      end

      def register_program(program_name)
        create_calling_point if @calling_point_manager.nil?

        @calling_point_manager.setString(2 + @program_count, program_name)
        @program_count += 1
      end

      def run(workspace, runner, user_arguments)
        super(workspace, runner, user_arguments)
        @workspace = workspace
        @calling_point_manager = nil
        @inputs = []
        @outputs = []
      end
    end
  end
end
