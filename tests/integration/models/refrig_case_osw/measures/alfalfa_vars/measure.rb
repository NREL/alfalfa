# insert your copyright here
require 'alfalfa'
# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class AlfalfaVariables < OpenStudio::Measure::EnergyPlusMeasure

  include OpenStudio::Alfalfa::EnergyPlusMixin
  # human readable name
  def name
    return 'AlfalfaVariables'
  end

  # human readable description
  def description
    return 'Add custom variables for Alfalfa'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Add EMS global variables required by Alfalfa'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new
    return args
  end

  # define what happens when the measure is run
  def run(workspace, runner, user_arguments)
    super(workspace, runner, user_arguments)

    # Alfalfa inputs
    # These can be set through the Alfalfa API, they will be available as OutputVariables
    # in the simulation. Use them as you will
    # Also see comments on the create_input method
    # alfalfa_add_global_variable("HVACFanOnOff")
    # alfalfa_add_global_variable("HVACCompressorOnOff")
    # alfalfa_add_global_variable("CaseOnOff")
    # alfalfa_add_global_variable("CaseDoorStatus")
    # alfalfa_add_global_variable("CaseDefrostStatus")
    # alfalfa_add_global_variable("CaseAntiSweatStatus")
    # alfalfa_add_global_variable("CaseLightStatus")
    # alfalfa_add_global_variable("ZoneLightStatus")
    # alfalfa_add_global_variable("ZoneOccStatus")
    # alfalfa_add_global_variable("Test_Point_1")

    # Alfalfa outputs
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "mt1_t_case").display_name = "MT1 Case Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "mt2_t_case").display_name = "MT2 Case Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "lt1_t_case").display_name = "LT1 Case Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "lt2_t_case").display_name = "LT2 Case Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "mt1_t_food").display_name = "MT1 Prod Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "mt2_t_food").display_name = "MT2 Prod Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "lt1_t_food").display_name = "LT1 Prod Temp"
    alfalfa_add_output_variable("PythonPlugin:OutputVariable", "lt2_t_food").display_name = "LT2 Prod Temp"
    alfalfa_add_output_variable("Zone Air Temperature", "Zn1").display_name = "Zone Temp"
    alfalfa_add_output_variable("Zone Air Relative Humidity", "Zn1").display_name = "Zone RH"
    alfalfa_add_output_variable("Refrigeration Case Evaporator Fan Electricity Rate", "MT1").display_name = "MT1 Case Fan Power"
    alfalfa_add_output_variable("Refrigeration Case Evaporator Fan Electricity Rate", "MT2").display_name = "MT2 Case Fan Power"
    alfalfa_add_output_variable("Refrigeration Case Evaporator Fan Electricity Rate", "LT1").display_name = "LT1 Case Fan Power"
    alfalfa_add_output_variable("Refrigeration Case Evaporator Fan Electricity Rate", "LT2").display_name = "LT2 Case Fan Power"
    alfalfa_add_output_variable("Refrigeration Case Lighting Electricity Rate", "MT1").display_name = "MT1 Case Light Power"
    alfalfa_add_output_variable("Refrigeration Case Lighting Electricity Rate", "MT2").display_name = "MT2 Case Light Power"
    alfalfa_add_output_variable("Refrigeration Case Lighting Electricity Rate", "LT1").display_name = "LT1 Case Light Power"
    alfalfa_add_output_variable("Refrigeration Case Lighting Electricity Rate", "LT2").display_name = "LT2 Case Light Power"
    alfalfa_add_output_variable("Refrigeration Case Anti Sweat Electricity Rate", "LT2").display_name = "Case Anti Sweat Power"
    alfalfa_add_output_variable("Refrigeration Case Defrost Electricity Rate", "LT1").display_name = "LT1 Case Defrost Power"
    alfalfa_add_output_variable("Refrigeration Case Defrost Electricity Rate", "LT2").display_name = "LT2 Case Defrost Power"
    alfalfa_add_output_variable("Refrigeration Compressor Electricity Rate", "MT Comp 1").display_name = "MT1 Case Compressor Power"
    alfalfa_add_output_variable("Refrigeration Compressor Electricity Rate", "MT Comp 2").display_name = "MT2 Case Compressor Power"
    alfalfa_add_output_variable("Refrigeration Compressor Electricity Rate", "LT Comp 1").display_name = "LT1 Case Compressor Power"
    alfalfa_add_output_variable("Refrigeration Compressor Electricity Rate", "LT Comp 2").display_name = "LT2 Case Compressor Power"
    alfalfa_add_output_variable("Fan Electricity Rate", "RTU Fan").display_name = "HVAC Fan Power"
    alfalfa_add_output_variable("Heating Coil Electricity Rate", "RTU Reheat Coil").display_name = "HVAC Heating Power"
    alfalfa_add_output_variable("Cooling Coil Electricity Rate", "RTU Cool Coil").display_name = "HVAC Cooling Power"


    alfalfa_generate_reports
    # other OutputVariables might be custom python defined output variables,
    # you should still be able to request them here, and as long as exportToBCVTB is true they will be available via Alfalfa

    return true
  end
end

# register the measure to be used by the application
AlfalfaVariables.new.registerWithApplication
