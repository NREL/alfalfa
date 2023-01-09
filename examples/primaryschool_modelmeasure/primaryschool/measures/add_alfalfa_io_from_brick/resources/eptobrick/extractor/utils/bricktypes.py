"manualPredicate": {
    "predicate": "",
    "elements": []
}

,
{
    "method": "manualPredicate",
    "type_": "chiller_heater_modules_performance_component_name",
    "attr_": "",
    "predicate": "hasPart"
}

,
                
"Branch": {
        "BrickType": "",
        "modelica": {},
        "rules": {
            "extensibleMethod":[
                {
                    "method": "genericUnpack",
                    "type_": "component",
                    "attr_": "name"
                },
                {
                    "method": "manualPredicate",
                    "type_": "component",
                    "attr_": "name",
                    "predicate": "hasPart"
                }
            ]
        }
    },
    "BranchList": {
        "BrickType": "",
        "modelica": {},
        "rules": {
            "extensibleMethod":[
                {
                    "method": "genericUnpack",
                    "type_": "branch",
                    "attr_": "name"
                },
                {
                    "method": "manualPredicate",
                    "type_": "branch",
                    "attr_": "name",
                    "predicate": "hasPart"
                }
            ]
        }
    },

Site:Location
Site:VariableLocation

RoofIrrigation

ScheduleTypeLimits
Schedule:Day:Hourly
Schedule:Day:Interval
Schedule:Day:List
Schedule:Week:Daily
Schedule:Week:Compact
Schedule:Year
Schedule:Compact
Schedule:Constant
Schedule:File:Shading
Schedule:File

RoomAir:Node
RoomAir:Node:AirflowNetwork
RoomAir:Node:AirflowNetwork:AdjacentSurfaceList
RoomAir:Node:AirflowNetwork:InternalGains
RoomAir:Node:AirflowNetwork:HVACEquipment
RoomAirSettings:AirflowNetwork

People
ComfortViewFactorAngles

Daylighting:Controls
Daylighting:ReferencePoint
Daylighting:DELight:ComplexFenestration
DaylightingDevice:Tubular
DaylightingDevice:Shelf
DaylightingDevice:LightWell

ZoneInfiltration:DesignFlowRate
ZoneInfiltration:EffectiveLeakageArea
ZoneInfiltration:FlowCoefficient
ZoneVentilation:DesignFlowRate
ZoneVentilation:WindandStackOpenArea
ZoneAirBalance:OutdoorAir

ZoneMixing
ZoneCrossMixing
ZoneRefrigerationDoorMixing
ZoneEarthtube
ZoneCoolTower:Shower
ZoneThermalChimney

AirflowNetwork:SimulationControl
AirflowNetwork:MultiZone:Zone
AirflowNetwork:MultiZone:Surface
AirflowNetwork:MultiZone:ReferenceCrackConditions
AirflowNetwork:MultiZone:Surface:Crack
AirflowNetwork:MultiZone:Surface:EffectiveLeakageArea
AirflowNetwork:MultiZone:SpecifiedFlowRate
AirflowNetwork:MultiZone:Component:DetailedOpening
AirflowNetwork:MultiZone:Component:SimpleOpening
AirflowNetwork:MultiZone:Component:HorizontalOpening
AirflowNetwork:MultiZone:Component:ZoneExhaustFan
AirflowNetwork:MultiZone:ExternalNode
AirflowNetwork:MultiZone:WindPressureCoefficientArray
AirflowNetwork:MultiZone:WindPressureCoefficientValues
AirflowNetwork:ZoneControl:PressureController
AirflowNetwork:Distribution:Node
AirflowNetwork:Distribution:Component:Leak
AirflowNetwork:Distribution:Component:LeakageRatio
AirflowNetwork:Distribution:Component:Duct
AirflowNetwork:Distribution:Component:Fan
AirflowNetwork:Distribution:Component:Coil
AirflowNetwork:Distribution:Component:HeatExchanger
AirflowNetwork:Distribution:Component:TerminalUnit
AirflowNetwork:Distribution:Component:ConstantPressureDrop
AirflowNetwork:Distribution:Component:OutdoorAirFlow
AirflowNetwork:Distribution:Component:ReliefAirFlow
AirflowNetwork:Distribution:Linkage
AirflowNetwork:Distribution:DuctViewFactors
AirflowNetwork:OccupantVentilationControl
AirflowNetwork:IntraZone:Node
AirflowNetwork:IntraZone:Linkage

HVACTemplate:Thermostat
HVACTemplate:Zone:IdealLoadsAirSystem
HVACTemplate:Zone:BaseboardHeat
HVACTemplate:Zone:FanCoil
HVACTemplate:Zone:PTAC
HVACTemplate:Zone:PTHP
HVACTemplate:Zone:WaterToAirHeatPump
HVACTemplate:Zone:VRF
HVACTemplate:Zone:Unitary
HVACTemplate:Zone:VAV
HVACTemplate:Zone:VAV:FanPowered
HVACTemplate:Zone:VAV:HeatAndCool
HVACTemplate:Zone:ConstantVolume
HVACTemplate:Zone:DualDuct
HVACTemplate:System:VRF
HVACTemplate:System:Unitary
HVACTemplate:System:UnitaryHeatPump:AirToAir
HVACTemplate:System:UnitarySystem
HVACTemplate:System:VAV
HVACTemplate:System:PackagedVAV
HVACTemplate:System:ConstantVolume
HVACTemplate:System:DualDuct
HVACTemplate:System:DedicatedOutdoorAir
HVACTemplate:Plant:ChilledWaterLoop
HVACTemplate:Plant:Chiller
HVACTemplate:Plant:Chiller:ObjectReference
HVACTemplate:Plant:Tower
HVACTemplate:Plant:Tower:ObjectReference
HVACTemplate:Plant:HotWaterLoop
HVACTemplate:Plant:Boiler
HVACTemplate:Plant:Boiler:ObjectReference
HVACTemplate:Plant:MixedWaterLoop
DesignSpecification:OutdoorAir
DesignSpecification:OutdoorAir:SpaceList
DesignSpecification:ZoneAirDistribution

Sizing:Parameters
Sizing:Zone
DesignSpecification:ZoneHVAC:Sizing
DesignSpecification:AirTerminal:Sizing
Sizing:System
Sizing:Plant
OutputControl:Sizing:Style

ZoneControl:Humidistat
ZoneControl:Thermostat:OperativeTemperature
ZoneControl:Thermostat:ThermalComfort
ZoneControl:Thermostat:TemperatureAndHumidity

ThermostatSetpoint:SingleHeatingOrCooling

ThermostatSetpoint:ThermalComfort:Fanger:SingleHeating
ThermostatSetpoint:ThermalComfort:Fanger:SingleCooling
ThermostatSetpoint:ThermalComfort:Fanger:SingleHeatingOrCooling
ThermostatSetpoint:ThermalComfort:Fanger:DualSetpoint

ZoneControl:Thermostat:StagedDualSetpoint
ZoneControl:ContaminantController

ZoneHVAC:EnergyRecoveryVentilator:Controller
ZoneHVAC:Baseboard:RadiantConvective:Water:Design
ZoneHVAC:Baseboard:RadiantConvective:Steam:Design
ZoneHVAC:LowTemperatureRadiant:VariableFlow:Design
ZoneHVAC:LowTemperatureRadiant:ConstantFlow:Design
ZoneHVAC:LowTemperatureRadiant:SurfaceGroup

FanPerformance:NightVentilation

Coil:Cooling:DX:CurveFit:Performance
Coil:Cooling:DX:CurveFit:OperatingMode
Coil:Cooling:DX:CurveFit:Speed

CoilPerformance:DX:Cooling

Coil:Cooling:WaterToAirHeatPump:ParameterEstimation
Coil:Heating:WaterToAirHeatPump:ParameterEstimation
Coil:Cooling:WaterToAirHeatPump:EquationFit
Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit
Coil:Heating:WaterToAirHeatPump:EquationFit
Coil:Heating:WaterToAirHeatPump:VariableSpeedEquationFit

HeatExchanger:Desiccant:BalancedFlow
HeatExchanger:Desiccant:BalancedFlow:PerformanceDataType1
UnitarySystemPerformance:Multispeed

Controller:WaterCoil
Controller:OutdoorAir
Controller:MechanicalVentilation
AirLoopHVAC:ControllerList

PipingSystem:Underground:Domain
PipingSystem:Underground:PipeCircuit
PipingSystem:Underground:PipeSegment

Duct

TemperingValve
LoadProfile:Plant
SolarCollectorPerformance:FlatPlate
SolarCollectorPerformance:IntegralCollectorStorage

CoolingTowerPerformance:CoolTools
CoolingTowerPerformance:YorkCalc

WaterHeater:Sizing

PlantEquipmentOperation:Uncontrolled
PlantEquipmentOperation:CoolingLoad
PlantEquipmentOperation:HeatingLoad
PlantEquipmentOperation:OutdoorDryBulb
PlantEquipmentOperation:OutdoorWetBulb
PlantEquipmentOperation:OutdoorRelativeHumidity
PlantEquipmentOperation:OutdoorDewpoint
PlantEquipmentOperation:ComponentSetpoint
PlantEquipmentOperation:ThermalEnergyStorage
PlantEquipmentOperation:OutdoorDryBulbDifference
PlantEquipmentOperation:OutdoorWetBulbDifference
PlantEquipmentOperation:OutdoorDewpointDifference
PlantEquipmentOperationSchemes
CondenserEquipmentOperationSchemes

EnergyManagementSystem:Sensor
EnergyManagementSystem:Actuator
EnergyManagementSystem:ProgramCallingManager
EnergyManagementSystem:Program
EnergyManagementSystem:Subroutine
EnergyManagementSystem:GlobalVariable
EnergyManagementSystem:OutputVariable
EnergyManagementSystem:MeteredOutputVariable
EnergyManagementSystem:TrendVariable
EnergyManagementSystem:InternalVariable
EnergyManagementSystem:CurveOrTableIndexVariable
EnergyManagementSystem:ConstructionIndexVariable
ExternalInterface
ExternalInterface:Schedule
ExternalInterface:Variable
ExternalInterface:Actuator
ExternalInterface:FunctionalMockupUnitImport
ExternalInterface:FunctionalMockupUnitImport:From:Variable
ExternalInterface:FunctionalMockupUnitImport:To:Schedule
ExternalInterface:FunctionalMockupUnitImport:To:Actuator
ExternalInterface:FunctionalMockupUnitImport:To:Variable
ExternalInterface:FunctionalMockupUnitExport:From:Variable
ExternalInterface:FunctionalMockupUnitExport:To:Schedule
ExternalInterface:FunctionalMockupUnitExport:To:Actuator
ExternalInterface:FunctionalMockupUnitExport:To:Variable

AvailabilityManager:Scheduled
AvailabilityManager:ScheduledOn
AvailabilityManager:ScheduledOff
AvailabilityManager:OptimumStart
AvailabilityManager:NightCycle
AvailabilityManager:DifferentialThermostat
AvailabilityManager:HighTemperatureTurnOff
AvailabilityManager:HighTemperatureTurnOn
AvailabilityManager:LowTemperatureTurnOff
AvailabilityManager:LowTemperatureTurnOn
AvailabilityManager:NightVentilation
AvailabilityManager:HybridVentilation
AvailabilityManagerAssignmentList

SetpointManager:Scheduled
SetpointManager:Scheduled:DualSetpoint
SetpointManager:OutdoorAirReset
SetpointManager:SingleZone:Reheat
SetpointManager:SingleZone:Heating
SetpointManager:SingleZone:Cooling
SetpointManager:SingleZone:Humidity:Minimum
SetpointManager:SingleZone:Humidity:Maximum
SetpointManager:MixedAir
SetpointManager:OutdoorAirPretreat
SetpointManager:Warmest
SetpointManager:Coldest
SetpointManager:ReturnAirBypassFlow
SetpointManager:WarmestTemperatureFlow
SetpointManager:MultiZone:Heating:Average
SetpointManager:MultiZone:Cooling:Average
SetpointManager:MultiZone:MinimumHumidity:Average
SetpointManager:MultiZone:MaximumHumidity:Average
SetpointManager:MultiZone:Humidity:Minimum
SetpointManager:MultiZone:Humidity:Maximum
SetpointManager:FollowOutdoorAirTemperature
SetpointManager:FollowSystemNodeTemperature
SetpointManager:FollowGroundTemperature
SetpointManager:CondenserEnteringReset
SetpointManager:CondenserEnteringReset:Ideal
SetpointManager:SingleZone:OneStageCooling
SetpointManager:SingleZone:OneStageHeating
SetpointManager:ReturnTemperature:ChilledWater
SetpointManager:ReturnTemperature:HotWater

DemandManagerAssignmentList
DemandManager:ExteriorLights
DemandManager:Lights
DemandManager:ElectricEquipment
DemandManager:Thermostats
DemandManager:Ventilation

PhotovoltaicPerformance:Simple
PhotovoltaicPerformance:EquivalentOne-Diode
PhotovoltaicPerformance:Sandia
Generator:MicroCHP:NonNormalizedParameters

FaultModel:TemperatureSensorOffset:OutdoorAir
FaultModel:HumiditySensorOffset:OutdoorAir
FaultModel:EnthalpySensorOffset:OutdoorAir
FaultModel:TemperatureSensorOffset:ReturnAir
FaultModel:EnthalpySensorOffset:ReturnAir
FaultModel:TemperatureSensorOffset:ChillerSupplyWater
FaultModel:TemperatureSensorOffset:CoilSupplyAir
FaultModel:TemperatureSensorOffset:CondenserSupplyWater
FaultModel:ThermostatOffset
FaultModel:HumidistatOffset
FaultModel:Fouling:AirFilter
FaultModel:Fouling:Boiler
FaultModel:Fouling:EvaporativeCooler
FaultModel:Fouling:Chiller
FaultModel:Fouling:CoolingTower
FaultModel:Fouling:Coil
Matrix:TwoDimension
HybridModel:Zone
Curve:Linear
Curve:QuadLinear
Curve:QuintLinear
Curve:Quadratic
Curve:Cubic
Curve:Quartic
Curve:Exponent
Curve:Bicubic
Curve:Biquadratic
Curve:QuadraticLinear
Curve:CubicLinear
Curve:Triquadratic
Curve:Functional:PressureDrop
Curve:FanPressureRise
Curve:ExponentialSkewNormal
Curve:Sigmoid
Curve:RectangularHyperbola1
Curve:RectangularHyperbola2
Curve:ExponentialDecay
Curve:DoubleExponentialDecay
Curve:ChillerPartLoadWithLift
Table:IndependentVariable
Table:IndependentVariableList
Table:Lookup
FluidProperties:Name
FluidProperties:GlycolConcentration
FluidProperties:Temperatures
FluidProperties:Saturated
FluidProperties:Superheated
FluidProperties:Concentration
CurrencyType
ComponentCost:Adjustments
ComponentCost:Reference
ComponentCost:LineItem
UtilityCost:Tariff
UtilityCost:Qualify
UtilityCost:Charge:Simple
UtilityCost:Charge:Block
UtilityCost:Ratchet
UtilityCost:Variable
UtilityCost:Computation
LifeCycleCost:Parameters
LifeCycleCost:RecurringCosts
LifeCycleCost:NonrecurringCost
LifeCycleCost:UsePriceEscalation
LifeCycleCost:UseAdjustment
Parametric:SetValueForRun
Parametric:Logic
Parametric:RunControl
Parametric:FileNameSuffix
Output:VariableDictionary
Output:Surfaces:List
Output:Surfaces:Drawing
Output:Schedules
Output:Constructions
Output:EnergyManagementSystem
OutputControl:SurfaceColorScheme
Output:Table:SummaryReports
Output:Table:TimeBins
Output:Table:Monthly
Output:Table:Annual
OutputControl:Table:Style
OutputControl:ReportingTolerances
Output:Variable
Output:Meter
Output:Meter:MeterFileOnly
Output:Meter:Cumulative
Output:Meter:Cumulative:MeterFileOnly
Meter:Custom
Meter:CustomDecrement
OutputControl:Files
Output:JSON
Output:SQLite
Output:EnvironmentalImpactFactors
EnvironmentalImpactFactors
FuelFactors
Output:Diagnostics
Output:DebuggingData
Output:PreprocessorMessage
PythonPlugin:SearchPaths
PythonPlugin:Instance
PythonPlugin:Variables
PythonPlugin:TrendVariable
PythonPlugin:OutputVariable