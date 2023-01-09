# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2021, Alliance for Sustainable Energy, LLC.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# (1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# (2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# (3) Neither the name of the copyright holder nor the names of any contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission from the respective party.
#
# (4) Other than as required in clauses (1) and (2), distributions in any form
# of modifications or other derivative works may not use the "OpenStudio"
# trademark, "OS", "os", or any other confusingly similar designation without
# specific prior written permission from Alliance for Sustainable Energy, LLC.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE
# UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF
# THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *******************************************************************************

require_relative 'Siz.HVACComponent'
require_relative 'Siz.ModelObject'
require_relative 'Siz.AirConditionerVariableRefrigerantFlow'
require_relative 'Siz.AirLoopHVAC'
require_relative 'Siz.AirLoopHVACUnitaryHeatCoolVAVChangeoverBypass'
require_relative 'Siz.AirLoopHVACUnitaryHeatPumpAirToAir'
require_relative 'Siz.AirLoopHVACUnitaryHeatPumpAirToAirMultiSpeed'
require_relative 'Siz.AirLoopHVACUnitarySystem'
require_relative 'Siz.AirTerminalDualDuctVAV'
require_relative 'Siz.AirTerminalSingleDuctConstantVolumeCooledBeam'
require_relative 'Siz.AirTerminalSingleDuctConstantVolumeFourPipeInduction'
require_relative 'Siz.AirTerminalSingleDuctConstantVolumeReheat'
require_relative 'Siz.AirTerminalSingleDuctParallelPIUReheat'
require_relative 'Siz.AirTerminalSingleDuctSeriesPIUReheat'
require_relative 'Siz.AirTerminalSingleDuctUncontrolled'
require_relative 'Siz.AirTerminalSingleDuctVAVHeatAndCoolNoReheat'
require_relative 'Siz.AirTerminalSingleDuctVAVHeatAndCoolReheat'
require_relative 'Siz.AirTerminalSingleDuctVAVNoReheat'
require_relative 'Siz.AirTerminalSingleDuctVAVReheat'
require_relative 'Siz.BoilerHotWater'
require_relative 'Siz.BoilerSteam'
require_relative 'Siz.ChillerAbsorption'
require_relative 'Siz.ChillerAbsorptionIndirect'
require_relative 'Siz.ChillerElectricEIR'
require_relative 'Siz.ChillerHeaterPerformanceElectricEIR'
require_relative 'Siz.CoilCoolingDXMultiSpeed'
require_relative 'Siz.CoilCoolingDXMultiSpeedStageData'
require_relative 'Siz.CoilCoolingDXSingleSpeed'
require_relative 'Siz.CoilCoolingDXTwoSpeed'
require_relative 'Siz.CoilCoolingDXTwoStageWithHumidityControlMode'
require_relative 'Siz.CoilCoolingDXVariableRefrigerantFlow'
require_relative 'Siz.CoilCoolingDXVariableSpeed'
require_relative 'Siz.CoilCoolingDXVariableSpeedSpeedData'
require_relative 'Siz.CoilCoolingLowTempRadiantVarFlow'
require_relative 'Siz.CoilCoolingWater'
require_relative 'Siz.CoilCoolingWaterToAirHeatPumpEquationFit'
require_relative 'Siz.CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFit'
require_relative 'Siz.CoilCoolingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData'
require_relative 'Siz.CoilHeatingDXMultiSpeed'
require_relative 'Siz.CoilHeatingDXMultiSpeedStageData'
require_relative 'Siz.CoilHeatingDXSingleSpeed'
require_relative 'Siz.CoilHeatingDXVariableRefrigerantFlow'
require_relative 'Siz.CoilHeatingDXVariableSpeed'
require_relative 'Siz.CoilHeatingDXVariableSpeedSpeedData'
require_relative 'Siz.CoilHeatingDesuperheater'
require_relative 'Siz.CoilHeatingElectric'
require_relative 'Siz.CoilHeatingGas'
require_relative 'Siz.CoilHeatingGasMultiStage'
require_relative 'Siz.CoilHeatingGasMultiStageStageData'
require_relative 'Siz.CoilHeatingLowTempRadiantVarFlow'
require_relative 'Siz.CoilHeatingWater'
require_relative 'Siz.CoilHeatingWaterBaseboard'
require_relative 'Siz.CoilHeatingWaterBaseboardRadiant'
require_relative 'Siz.CoilHeatingWaterToAirHeatPumpEquationFit'
require_relative 'Siz.CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFit'
require_relative 'Siz.CoilHeatingWaterToAirHeatPumpVariableSpeedEquationFitSpeedData'
require_relative 'Siz.CoilPerformanceDXCooling'
require_relative 'Siz.CoilSystemCoolingDXHeatExchangerAssisted'
require_relative 'Siz.CoilSystemCoolingWaterHeatExchangerAssisted'
require_relative 'Siz.CoilWaterHeatingAirToWaterHeatPump'
require_relative 'Siz.CoilWaterHeatingAirToWaterHeatPumpWrapped'
require_relative 'Siz.CoilWaterHeatingDesuperheater'
require_relative 'Siz.ControllerOutdoorAir'
require_relative 'Siz.CoolingTowerSingleSpeed'
require_relative 'Siz.CoolingTowerTwoSpeed'
require_relative 'Siz.CoolingTowerVariableSpeed'
require_relative 'Siz.DistrictCooling'
require_relative 'Siz.DistrictHeating'
require_relative 'Siz.ElectricLoadCenterInverterLookUpTable'
require_relative 'Siz.ElectricLoadCenterInverterSimple'
require_relative 'Siz.ElectricLoadCenterStorageConverter'
require_relative 'Siz.ElectricLoadCenterStorageSimple'
require_relative 'Siz.EvaporativeCoolerDirectResearchSpecial'
require_relative 'Siz.EvaporativeCoolerIndirectResearchSpecial'
require_relative 'Siz.EvaporativeFluidCoolerSingleSpeed'
require_relative 'Siz.EvaporativeFluidCoolerTwoSpeed'
require_relative 'Siz.FanConstantVolume'
require_relative 'Siz.FanOnOff'
require_relative 'Siz.FanVariableVolume'
require_relative 'Siz.FanZoneExhaust'
require_relative 'Siz.FluidCoolerSingleSpeed'
require_relative 'Siz.FluidCoolerTwoSpeed'
require_relative 'Siz.GeneratorFuelCellElectricalStorage'
require_relative 'Siz.GeneratorFuelCellInverter'
require_relative 'Siz.GeneratorFuelCellPowerModule'
require_relative 'Siz.GeneratorMicroTurbine'
require_relative 'Siz.GeneratorMicroTurbineHeatRecovery'
require_relative 'Siz.HeaderedPumpsConstantSpeed'
require_relative 'Siz.HeaderedPumpsVariableSpeed'
require_relative 'Siz.HeatExchangerAirToAirSensibleAndLatent'
require_relative 'Siz.HeatExchangerFluidToFluid'
require_relative 'Siz.HeatPumpWaterToWaterEquationFitCooling'
require_relative 'Siz.HeatPumpWaterToWaterEquationFitHeating'
# require_relative 'Siz.HumidifierSteamElectric'
require_relative 'Siz.Model'
require_relative 'Siz.PhotovoltaicPerformanceSimple'
require_relative 'Siz.PlantComponentTemperatureSource'
require_relative 'Siz.PlantLoop'
require_relative 'Siz.PumpConstantSpeed'
require_relative 'Siz.PumpVariableSpeed'
require_relative 'Siz.RefrigerationSecondarySystem'
require_relative 'Siz.RefrigerationSystem'
require_relative 'Siz.RefrigerationTranscriticalSystem'
require_relative 'Siz.SizingSystem'
require_relative 'Siz.SolarCollectorFlatPlatePhotovoltaicThermal'
require_relative 'Siz.SolarCollectorPerformancePhotovoltaicThermalSimple'
require_relative 'Siz.ThermalStorageChilledWaterStratified'
require_relative 'Siz.WaterHeaterHeatPump'
require_relative 'Siz.WaterHeaterHeatPumpWrappedCondenser'
require_relative 'Siz.WaterHeaterMixed'
require_relative 'Siz.WaterHeaterStratified'
require_relative 'Siz.ZoneHVACBaseboardConvectiveElectric'
require_relative 'Siz.ZoneHVACBaseboardConvectiveWater'
require_relative 'Siz.ZoneHVACBaseboardRadiantConvectiveElectric'
require_relative 'Siz.ZoneHVACBaseboardRadiantConvectiveWater'
require_relative 'Siz.ZoneHVACEnergyRecoveryVentilator'
require_relative 'Siz.ZoneHVACFourPipeFanCoil'
require_relative 'Siz.ZoneHVACHighTemperatureRadiant'
require_relative 'Siz.ZoneHVACIdealLoadsAirSystem'
require_relative 'Siz.ZoneHVACLowTempRadiantConstFlow'
require_relative 'Siz.ZoneHVACLowTempRadiantVarFlow'
require_relative 'Siz.ZoneHVACPackagedTerminalAirConditioner'
require_relative 'Siz.ZoneHVACPackagedTerminalHeatPump'
require_relative 'Siz.ZoneHVACTerminalUnitVariableRefrigerantFlow'
require_relative 'Siz.ZoneHVACUnitHeater'
require_relative 'Siz.ZoneHVACUnitVentilator'
require_relative 'Siz.ZoneHVACWaterToAirHeatPump'
require_relative 'Siz.ZoneVentilationDesignFlowRate'
