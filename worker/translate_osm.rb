
osm = ARGV[0]
idf = ARGV[1]

vt = OpenStudio::OSVersion::VersionTranslator.new
m = vt.loadModel osm

if not m.empty?
  ft = OpenStudio::EnergyPlus::ForwardTranslator.new
  ws = ft.translateModel m.get
  ws.save(idf,true)
end

