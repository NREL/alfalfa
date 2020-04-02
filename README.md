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

## Running Worker Integration Tests

1. Run ```docker-compose up worker-test```
1. Test output should be located in worker/test/output.
1. See worker/test/test.py for an example.

## Running Unit Tests

1. Run ```pip install -r requirements.txt```
1. Run `py.test`

## Running Integration Tests

1. To run integration tests, then you must first launch the docker compose in the root directory of this repository

    ```bash
    docker-compose up
    ```

1. After the service has launched (successfully?) then run

    ```bash
    py.test -m 'integration'
    ```

These tests have been added to the tox running framework and run on travis as needed. You can also test locally by
simply calling:

    ```bash
    tox -e integration
    ```

## Making changes

1. Make source code changes as needed.
1. Verify that the Docker services are stopped with ```docker-compose down```.
1. Recreate the containers and restart services with ```docker-compose up```.

This is a basic workflow that is sure to work, other docker and docker-compose commands can be used to start / stop services without rebuilding.

## Project Organization

Development of this project is setup to happen in a handful of docker containers. This makes it easy to do ```docker-compose up```, and get a fully working development environment.  There are currently separate containers for web (The Haystack API server), worker (The thing that runs the simulation, aka master algorithm), database (mongo, the thing that holds a model's point dictionary and current / historical values), and queue (The thing where API requests go when they need to trigger something in the master algorithm). In this project there is one top level directory for each docker container.

## Design

https://docs.google.com/presentation/d/1fYtwXvS4jlrhTdHJxPUPpbZZ8PwIM8sGCdLsG_6hwwo/edit#slide=id.p
