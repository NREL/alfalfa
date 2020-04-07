source 'http://rubygems.org'

gemspec

# Local gems are useful when developing and integrating the various dependencies.
# To favor the use of local gems, set the following environment variable:
#   Mac: export FAVOR_LOCAL_GEMS=1
#   Windows: set FAVOR_LOCAL_GEMS=1
# Note that if allow_local is true, but the gem is not found locally, then it will
# checkout the latest version (develop) from github.
allow_local = ENV['FAVOR_LOCAL_GEMS']

if allow_local && File.exist?('../OpenStudio-extension-gem')
  gem 'openstudio-extension', path: '../OpenStudio-extension-gem'
elsif allow_local
  gem 'openstudio-extension', github: 'NREL/OpenStudio-extension-gem', branch: 'develop'
end

gem 'openstudio_measure_tester', '= 0.2.0' # This includes the dependencies for running unit tests, coverage, and rubocop



