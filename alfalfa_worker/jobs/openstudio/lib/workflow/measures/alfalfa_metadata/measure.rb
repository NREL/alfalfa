# start the measure
class AlfalfaMetadata < OpenStudio::Measure::EnergyPlusMeasure

  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Alfalfa Metadata'
  end

  # human readable description
  def description
    return 'Generate metadata report for Alfalfa'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Generate metadata report for Alfalfa'
  end

  # define the arguments that the user will input
  def arguments(workspace)
    args = OpenStudio::Measure::OSArgumentVector.new

    return args
  end

  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(workspace), user_arguments)
      return false
    end

    metadata_dict = {}

    buildings = workspace.getObjectsByType('Building'.to_IddObjectType)
    buildings.each do |building|
      metadata_dict['building_name'] = building.name.get
    end

    File.open('./report_metadata.json', 'w') do |f|
      JSON.dump(metadata_dict, f)
    end

    runner.registerFinalCondition("Done")

    return true
  end
end

# register the measure to be used by the application
AlfalfaMetadata.new.registerWithApplication
