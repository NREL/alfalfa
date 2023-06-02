require 'openstudio'

model = OpenStudio::Model::Model.new()
# puts model.site
# puts model.methods.filter { |m| m.to_s.upcase.include? "BUILDING"}
# puts OpenStudio::Model::Building.new
# building = OpenStudio::Model::Building.new(model)

# building = model.building.get
story = OpenStudio::Model::BuildingStory.new(model)
# weather = OpenStudio::Model::WeatherFile.new(model)
# weather.file(OpenStudio::Path.new('USA_OH_Dayton-Wright.Patterson.AFB.745700_TMY3.epw'))

10.times do
    space = OpenStudio::Model::Space.new(model)
    space.setBuildingStory(story)
    tz = OpenStudio::Model::ThermalZone.new(model)
    space.setThermalZone(tz)
    puts tz.methods.filter { |m| m.to_s.include? "name"}
    puts tz.name
    # tz.setName = "Thermal Zone #{idx}"
    tz.setCeilingHeight(4)
    tz.setVolume(4*10*10)

    tstat = OpenStudio::Model::ThermostatSetpointDualSetpoint.new(model)
    tz.setThermostatSetpointDualSetpoint(tstat)

    htg_sch = OpenStudio::Model::ScheduleConstant.new(model)
    htg_sch.setValue(18)

    clg_sch = OpenStudio::Model::ScheduleConstant.new(model)
    clg_sch.setValue(21)

    tstat.setHeatingSchedule(htg_sch)
    tstat.setCoolingSchedule(clg_sch)

end

model_path = OpenStudio::Path.new('test_model.osm')
# puts model.methods
model.save(model_path)