# insert your copyright here

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class AlfalfaVariables < OpenStudio::Measure::ModelMeasure
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

  def create_input(model, name, freq)
    # The purpose of this function is to create an Alfalfa input that is accessible via python plugins

    global = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, name)
    global.setExportToBCVTB(true)

    # The global variable's value must be sent to output an variable so that python programs can read it
    # don't be mistaken, An OuputVariable object is created, but this is "input" to the simulation, from Alfalfa clients
    global_ems_output = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, global)
    global_ems_output.setName(name + "_EMS_Value")
    global_ems_output.setUpdateFrequency("SystemTimestep")

    # Request the custom ems output var creaed in the previous step
    global_output = OpenStudio::Model::OutputVariable.new(global_ems_output.nameString(), model)
    global_output.setName(name + "_Value")
    global_output.setReportingFrequency(freq)
    global_output.setKeyValue("EMS")
    # Setting exportToBCVTB to true is optional, and will result in the output variable showing up in the Alfalfa api,
    # this might be useful for confirmation of the input
    global_output.setExportToBCVTB(true)

    # repeat the previous steps for an "Enable" input
    # This value will be 1 (instead of 0) anytime a client writes to the input via the Alfalfa api
    global_enable = OpenStudio::Model::EnergyManagementSystemGlobalVariable.new(model, name + "_Enable")
    global_enable.setExportToBCVTB(true)

    global_enable_ems_output = OpenStudio::Model::EnergyManagementSystemOutputVariable.new(model, global_enable)
    global_enable_ems_output.setName(name + "_Enable_EMS_Value")
    global_enable_ems_output.setUpdateFrequency("SystemTimestep")

    global_enable_output = OpenStudio::Model::OutputVariable.new(global_enable_ems_output.nameString(), model)
    global_enable_output.setName(name + "_Enable_Value")
    global_enable_output.setReportingFrequency(freq)
    global_enable_output.setKeyValue("EMS")
    global_enable_output.setExportToBCVTB(true)
  end

  def create_output(model, var, key, name, freq)
    new_var = OpenStudio::Model::OutputVariable.new(var, model)
    new_var.setName(name)
    new_var.setReportingFrequency(freq)
    new_var.setKeyValue(key)
    new_var.setExportToBCVTB(true)
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # Alfalfa inputs
    # These can be set through the Alfalfa API, they will be available as OutputVariables
    # in the simulation. Use them as you will
    # Also see comments on the create_input method
    create_input(model, "HVACFanOnOff", "Timestep")
    create_input(model, "HVACCompressorOnOff", "Timestep")
    create_input(model, "CaseOnOff", "Timestep")
    create_input(model, "CaseDoorStatus", "Timestep")
    create_input(model, "CaseDefrostStatus", "Timestep")
    create_input(model, "CaseAntiSweatStatus", "Timestep")
    create_input(model, "CaseLightStatus", "Timestep")
    create_input(model, "ZoneLightStatus", "Timestep")
    create_input(model, "ZoneOccStatus", "Timestep")
    create_input(model, "Test_Point_1", "Timestep")

    # Alfalfa outputs
    create_output(model, "PythonPlugin:OutputVariable", "mt1_t_case", "MT1 Case Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "mt2_t_case", "MT2 Case Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "lt1_t_case", "LT1 Case Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "lt2_t_case", "LT2 Case Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "mt1_t_food", "MT1 Prod Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "mt2_t_food", "MT2 Prod Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "lt1_t_food", "LT1 Prod Temp", "Timestep")
    create_output(model, "PythonPlugin:OutputVariable", "lt2_t_food", "LT2 Prod Temp", "Timestep")
    create_output(model, "Zone Air Temperature", "Zn1", "Zone Temp", "Timestep")
    create_output(model, "Zone Air Relative Humidity", "Zn1", "Zone RH", "Timestep")
    create_output(model, "Refrigeration Case Evaporator Fan Electricity Rate", "MT1", "Case Fan Power", "Timestep")
    create_output(model, "Refrigeration Case Evaporator Fan Electricity Rate", "MT2", "Case Fan Power", "Timestep")
    create_output(model, "Refrigeration Case Evaporator Fan Electricity Rate", "LT1", "Case Fan Power", "Timestep")
    create_output(model, "Refrigeration Case Evaporator Fan Electricity Rate", "LT2", "Case Fan Power", "Timestep")
    create_output(model, "Refrigeration Case Lighting Electricity Rate", "MT1", "Case Light Power", "Timestep")
    create_output(model, "Refrigeration Case Lighting Electricity Rate", "MT2", "Case Light Power", "Timestep")
    create_output(model, "Refrigeration Case Lighting Electricity Rate", "LT1", "Case Light Power", "Timestep")
    create_output(model, "Refrigeration Case Lighting Electricity Rate", "LT2", "Case Light Power", "Timestep")
    create_output(model, "Refrigeration Case Anti Sweat Electricity Rate", "LT2", "Case Anti Sweat Power", "Timestep")
    create_output(model, "Refrigeration Case Defrost Electricity Rate", "LT1", "Case Defrost Power", "Timestep")
    create_output(model, "Refrigeration Case Defrost Electricity Rate", "LT2", "Case Defrost Power", "Timestep")
    create_output(model, "Refrigeration Compressor Electricity Rate", "MT Comp 1", "Case Compressor Power", "Timestep")
    create_output(model, "Refrigeration Compressor Electricity Rate", "MT Comp 2", "Case Compressor Power", "Timestep")
    create_output(model, "Refrigeration Compressor Electricity Rate", "LT Comp 1", "Case Compressor Power", "Timestep")
    create_output(model, "Refrigeration Compressor Electricity Rate", "LT Comp 2", "Case Compressor Power", "Timestep")
    create_output(model, "Fan Electricity Rate", "RTU Fan", "HVAC Fan Power", "Timestep")
    create_output(model, "Heating Coil Electricity Rate", "RTU Reheat Coil", "HVAC Heating Power", "Timestep")
    create_output(model, "Cooling Coil Electricity Rate", "RTU Cool Coil", "HVAC Cooling Power", "Timestep")

    # other OutputVariables might be custom python defined output variables,
    # you should still be able to request them here, and as long as exportToBCVTB is true they will be available via Alfalfa

    return true
  end
end

# register the measure to be used by the application
AlfalfaVariables.new.registerWithApplication
