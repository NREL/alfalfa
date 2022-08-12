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
    def arguments(ws)
      args = OpenStudio::Ruleset::OSArgumentVector.new
  
      # argument for python script name
      py_name = OpenStudio::Ruleset::OSArgument.makeStringArgument(
        'py_name',
        true
      )
      py_name.setDisplayName('Python Script Name')
      py_name.setDescription('Name of script with extension (e.g., myPlugin.py)')

      class_name = OpenStudio::Ruleset::OSArgument.makeStringArgument(
        'class_name',
        true
      )
      class_name.setDisplayName('Python Plugin Class Name')
      class_name.setDescription('Name of class in python script (must inherit from EnergyPlusPlugin)')

      args << py_name
      args << class_name
  
      return args
    end
  
    # define what happens when the measure is run
    def run(ws, runner, usr_args)
  
      # call the parent class method
      super(ws, runner, usr_args)
  
      # use the built-in error checking
      return false unless runner.validateUserArguments(
        arguments(ws),
        usr_args
      )
  
      # assign the user inputs to variables
      py_name = runner.getStringArgumentValue(
        'py_name',
        usr_args
      )

      class_name = runner.getStringArgumentValue(
        'class_name',
        usr_args
      )
  
      # define python script dir
      py_dir = "#{__dir__}/resources"
  
      # make sure python script exists
      unless File.exist?("#{py_dir}/#{py_name}")
        runner.registerError("Could not find file at #{py_dir}/#{py_name}.")
        return false
      end
  
      # add python plugin search paths
      n = OpenStudio::IdfObject.new('PythonPlugin_SearchPaths'.to_IddObjectType)
      n.setString(0, 'Python Plugin Search Paths')
      n.setString(1, 'Yes')
      n.setString(2, 'Yes')
      # set site packages location depending on operating system
      if (RUBY_PLATFORM =~ /linux/) != nil
        n.setString(3, '/usr/local/lib/python3.7/dist-packages')
      elsif (RUBY_PLATFORM =~ /darwin/) != nil
        n.setString(3, '/usr/local/lib/python3.7/site-packages')
      elsif (RUBY_PLATFORM =~ /cygwin|mswin|mingw|bccwin|wince|emx/) != nil
        h = ENV['USERPROFILE'].gsub('\\', '/')
        n.setString(3, "#{h}/AppData/Local/Programs/Python/Python37/Lib/site-packages")
      end
      # add python dir
      n.setString(4, py_dir)
      ws.addObject(n)
  
      # add python plugin instance
      n = OpenStudio::IdfObject.new('PythonPlugin_Instance'.to_IddObjectType)
      n.setString(0, 'Python Plugin Instance Name')
      n.setString(1, 'No')
      n.setString(2, py_name.sub('.py', ''))
      n.setString(3, class_name)
      ws.addObject(n)
  
    end
  
  end
  
  # register the measure to be used by the application
  PythonEMS.new.registerWithApplication