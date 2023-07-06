lib = File.expand_path('lib', __dir__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'version'

Gem::Specification.new do |spec|
  spec.name          = 'alfalfa-lib'
  spec.version       = OpenStudio::Alfalfa::VERSION
  spec.authors       = ['Tobias Shapinsky']
  spec.email         = ['tobias.shapinsky@nrel.gov']

  spec.summary       = 'Create input and output points in Aflalfa'
  spec.description   = 'Library and measures to create input and output points in Alfalfa'
  spec.homepage      = 'https://github.com/NREL/alfalfa'

  # Specify which files should be added to the gem when it is released.
  spec.files         = ["lib/alfalfa_mixin.rb", "lib/alfalfa.rb", "lib/energy_plus_mixin.rb", "lib/input.rb", "lib/openstudio_mixin.rb", "lib/output.rb", "lib/point.rb", "lib/utils.rb", "lib/version.rb"]
  spec.require_paths = ['lib']

  spec.required_ruby_version = '~> 2.7.0'

end
