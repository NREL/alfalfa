require 'openstudio'

# puts OpenStudio::Model::Model.methods.filter { |m| m.to_s.upcase.include? "LOAD"}
# exit
model = OpenStudio::Model::Model.load("small_office.osm").get
# model.load("small_office.osm")
building = model.building.get
story = building.buildingStories()[0]
clg_value = 23
htg_value = 15
model.getThermalZones.each_with_index do |tz, idx|
    puts tz.name
    tstat = tz.thermostatSetpointDualSetpoint.get
    htg_sch = nil
    clg_sch = nil
    if tstat.getHeatingSchedule.is_initialized
        htg_sch = tstat.getHeatingSchedule.get
    end
    if tstat.getCoolingSchedule.is_initialized
        clg_sch = tstat.getCoolingSchedule.get
    end
    if idx == 0
        htg_sch = OpenStudio::Model::ScheduleConstant.new(model)
        htg_sch.setName("CONSTANT HEATING")
        htg_sch.setValue(htg_value)

        clg_sch = OpenStudio::Model::ScheduleCompact.new(model)
        clg_sch.setName("COMPACT COOLING")
        clg_sch.setToConstantValue(clg_value)
    elsif idx == 1
        htg_sch = OpenStudio::Model::ScheduleYear.new(model)
        sch_day = OpenStudio::Model::ScheduleDay.new(model, htg_value)
        sch_week = OpenStudio::Model::ScheduleWeek.new(model)
        sch_week.setAllSchedules(sch_day)
        htg_sch.addScheduleWeek(OpenStudio::Date.new(OpenStudio::MonthOfYear.new("Dec"), 31, 2006), sch_week)
        htg_sch.setName("YEAR HEATING")

        clg_sch = OpenStudio::Model::ScheduleRuleset.new(model, clg_value)
        clg_sch.setName("RULESET COOLING")
    elsif idx == 2
        start_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new("Jan"), 1)
        interval = OpenStudio::Time.new(1,0)
        constant_vec = OpenStudio::Vector.new(365)
        timeseries_htg = OpenStudio::TimeSeries.new(start_date, interval, constant_vec + htg_value, "C")
        htg_sch = OpenStudio::Model::ScheduleFixedInterval.new(model)
        htg_sch.setTimeSeries(timeseries_htg)
        htg_sch.setName("FIXEDINTERVAL HEATING")

        clg_sch = OpenStudio::Model::ScheduleCompact.new(model)
        clg_sch.setToConstantValue(clg_value)
        clg_sch.setName("COMPACT COOLING")
    end

    if !clg_sch.nil? || !htg_sch.nil?
        tstat.setHeatingSchedule(htg_sch)
        tstat.setCoolingSchedule(clg_sch)
    end

end

model_path = OpenStudio::Path.new('test_model.osm')
model.save(model_path)