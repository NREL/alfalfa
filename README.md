# Alfalfa

This is a Haystack implementation backed by a virtual building. Virtual building simulation is performed using OpenStudio and EnergyPlus.

## Getting Started

1. Install [Docker](https://www.docker.com) for your platform.
1. From a command prompt ```docker-compose up web```.
1. Navigate to http://localhost/api/nav to verify that the Haystack implementation is running.
1. Navigate to http://localhost to view web application.
1. Navigate to http://localhost:9000 to view the minio file server. The default login is "user" and "password"
This is a local implementation of Amazon S3 for bulk file storage during development.
1. Use ```Ctrl-C``` to stop the services.

### Running with Historian and Dashboard
The alfalfa stack can optionally be run with a historian (influxdb) and a dashboard (grafana). History data is only added for OSM / OSW models.
1. `export HISTORIAN_ENABLE=true && docker-compose -f docker-compose.yml -f docker-compose-historian.yml up --build -d`
1. Navigate to http://localhost:3000 to view a grafana dashboard. Note that timespans for history data will be based on the time during which the simulation was run (simulation time), not real world time.
1. Only a simple dashboard is supported for now

# Running tests locally
1. Install poetry (similar to Ruby's bundler):  `pip install poetry`
1. Install dependencies:  `poetry install`
1. Run unit tests: `poetry run pytest`
1. Run stack locally in detached mode: `docker-compose up --build -d`
1. Run integration tests: `poetry run pytest -m "integration"`
1. Clean up: `docker-compose down`

