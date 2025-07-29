# start the measure
class PythonEMS < OpenStudio::Ruleset::WorkspaceUserScript

    # human readable name
    def name
      return 'Python EMS'
    end

    # human readable description
    def description
      return 'Add python EMS to IDF'
    end

    # human readable description of modeling approach
    def modeler_description
      return 'Add python EMS to IDF'
    end

    # define the arguments that the user will input
    def arguments(workspace)
      args = OpenStudio::Ruleset::OSArgumentVector.new

      return args
    end

    # define what happens when the measure is run
    def run(workspace, runner, usr_args)

      # call the parent class method
      super(workspace, runner, usr_args)

      # use the built-in error checking
      return false unless runner.validateUserArguments(
        arguments(workspace),
        usr_args
      )

      # define python script dir
      py_dir = "#{__dir__}/resources"

      # add python plugin search paths
      plugin_paths = OpenStudio::IdfObject.new('PythonPlugin_SearchPaths'.to_IddObjectType)
      plugin_paths.setString(0, 'Python Plugin Search Paths')
      plugin_paths.setString(1, 'Yes')
      plugin_paths.setString(2, 'Yes')
      plugin_paths.setString(3, 'No')
      # add python dir
      plugin_paths.setString(4, py_dir)
      workspace.addObject(plugin_paths)

      # add python plugin instance
      plugin_instance = OpenStudio::IdfObject.new('PythonPlugin_Instance'.to_IddObjectType)
      plugin_instance.setString(0, 'Python Plugin Instance Name')
      plugin_instance.setString(1, 'No')
      plugin_instance.setString(2, 'simple_plugin')
      plugin_instance.setString(3, 'BadPlugin')
      workspace.addObject(plugin_instance)

      plugin_variables = OpenStudio::IdfObject.new('PythonPlugin_Variables'.to_IddObjectType)
      plugin_variables.setString(0, 'Python Plugin Variables')
      plugin_variables.setString(1, 'input')
      plugin_variables.setString(2, 'output')
      workspace.addObject(plugin_variables)

      alfalfa = runner.alfalfa
      alfalfa.exposeGlobalVariable('input', "Python Input")
      alfalfa.exposeGlobalVariable('output', "Python Output")
      alfalfa.exposeConstant(17.5, 'test value')

      return true

    end

  end

  # register the measure to be used by the application
  PythonEMS.new.registerWithApplication
