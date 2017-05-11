# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class Haystack < OpenStudio::Ruleset::ModelUserScript

  # human readable name
  def name
    return "Haystack"
  end

  # human readable description
  def description
    return "This measure will find economizers on airloops and add haystack tags."
  end

  # human readable description of modeling approach
  def modeler_description
    return "This measure loops through the existing airloops, looking for loops that have outdoor airsystems with economizers"
  end
  

  #define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    return args
  end #end the arguments method

  #define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)
    
    # Use the built-in error checking 
    if not runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end
    
    num_economizers = 0
    
    # Report initial condition of model
    #runner.registerInitialCondition("The building started with ") 
    
    #loop through air loops
    model.getAirLoopHVACs.each do |airloop|
      supply_components = airloop.supplyComponents

      #find AirLoopHVACOutdoorAirSystem on loop
      supply_components.each do |supply_component|
        hVACComponent = supply_component.to_AirLoopHVACOutdoorAirSystem
        if hVACComponent.is_initialized
          hVACComponent = hVACComponent.get

          #get ControllerOutdoorAir
          controller_oa = hVACComponent.getControllerOutdoorAir

          #log initial economizer type
          if not controller_oa.getEconomizerControlType == "NoEconomizer"
            #runner.registerInfo("found economizer on airloop #{airloop.name.to_s}")
            puts "found economizer on airloop #{airloop.name.to_s}"
            num_economizers += 1
          end
          
        end
      end
    end  
      
    runner.registerFinalCondition("The building has #{num_economizers} economizers") 
   
    return true
 
  end #end the run method

end #end the measure

# register the measure to be used by the application
Haystack.new.registerWithApplication
