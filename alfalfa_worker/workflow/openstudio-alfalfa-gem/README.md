# Openstudio Alfalfa Gem

Extrapolation from the [Haystack measure](https://github.com/NREL/alfalfa/tree/develop/worker/workflow/measures/haystack) written for alfalfa

## Installation

Add this line to your application's Gemfile:

```ruby
gem 'openstudio-alfalfa'
```

And then execute:

    $ bundle

Or install it yourself as:

    $ gem install 'openstudio-alfalfa'

## Usage

To be filled out later. 

## TODO

- [ ] Remove measures from OpenStudio-Measures to standardize on this location
- [ ] Update measures to code standards
- [ ] Review and fill out the gemspec file with author and gem description

# Releasing

* Update change log
* Update version in `/lib/openstudio/openstudio-alfalfa/version.rb`
* Merge down to master
* Release via github
* run `rake release` from master
