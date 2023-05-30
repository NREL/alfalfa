lib = File.expand_path('lib', __dir__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'version'

Gem::Specification.new do |spec|
  spec.name          = 'alfalfa'
  spec.version       = OpenStudio::Alfalfa::VERSION
  spec.authors       = ['Tobias Shapinsky']
  spec.email         = ['tobias.shapinsky@nrel.gov']

  spec.summary       = 'Create input and output points in Aflalfa'
  spec.description   = 'Library and measures to create input and output points in Alfalfa'
  spec.homepage      = 'https://github.com/NREL/alfalfa/tree/develop/alfalfa_worker/jobs/openstudio/lib/alfalfa-lib'

  # Specify which files should be added to the gem when it is released.
  # The `git ls-files -z` loads the files in the RubyGem that have been added into git.
 # spec.files         = Dir.chdir(File.expand_path(__dir__)) do
 #   `git ls-files -z`.split("\x0").reject { |f| f.match(%r{^(test|lib.measures.*tests|spec|features)/}) }
 # end
  spec.files         = ["lib/alfalfa_mixin.rb", "lib/alfalfa.rb", "lib/energy_plus_mixin.rb", "lib/input.rb", "lib/openstudio_mixin.rb", "lib/output.rb", "lib/point.rb", "lib/utils.rb", "lib/version.rb"]
  spec.bindir        = 'exe'
  spec.executables   = spec.files.grep(%r{^exe/}) { |f| File.basename(f) }
  spec.require_paths = ['lib']

  spec.required_ruby_version = '~> 2.7.0'

end
