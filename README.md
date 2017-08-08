# Alfalfa

This is a Haystack implementation backed by a virtual building. Virtual building simulation is performed using OpenStudio and EnergyPlus.

## Getting Started

1. Install [Docker](https://www.docker.com) for your platform.
1. The application depends on Amazon s3 to move simulation files around,
therefore aws credentials must be in the environment. Set the following aws
environment variables:
```
export AWS_ACCESS_KEY_ID=foo
export AWS_SECRET_ACCESS_KEY=bar
```
1. From a command prompt ```docker-compose up```.
1. Navigate to http://localhost:3000/nav to verify that the Haystack implementation is running.
1. Use ```Ctrl-C``` to stop the services.

## Running Tests

1. Install node LTS, https://nodejs.org/. 
1. Follow the Getting Started directions to start the application server. 
1. Navigate to the <project-root>/web directory from a command prompts (ie ```cd /home/harry/alfalfa/web```)
1. Run npm to install dependencies ```npm update```.
1. Run the following command to execute the tests ```./node_modules/.bin/mocha test/economizer.js```.

## Making changes

1. Make source code changes as needed.
1. Verify that the Docker services are stopped with ```docker-compose down```.
1. Recreate the containers and restart services with ```docker-compose up```.

This is a basic workflow that is sure to work, other docker and docker-compose commands can be used to start / stop services without rebuilding. 

## Project Organization 

Development of this project is setup to happen in a handful of docker containers. This makes it easy to do ```docker-compose up```, and get a fully working development environment.  There are currently separate containers for web (The Haystack API server), worker (The thing that runs the simulation, aka master algorithm), database (mongo, the thing that holds a model's point dictionary and current / historical values), and queue (The thing where API requests go when they need to trigger something in the master algorithm). In this project there is one top level directory for each docker container.

## Design

https://docs.google.com/presentation/d/1fYtwXvS4jlrhTdHJxPUPpbZZ8PwIM8sGCdLsG_6hwwo/edit#slide=id.p

## Deployment

1. Export the mongo url, including username and password:
```
export MONGO_URL=mongodb://user:pass@ds129043.mlab.com:29043/alfalfa
```
1. Use ```aws ecr get-login``` to produce a docker login command. Copy and paste the output into a terminal to login.
1. Build current containers with, ```docker-compose build```.
1. Use ```docker-compose push``` to push new images to the aws container registry.
1. ```./deploy/deploy up -c 2```
1. ```./deploy/deploy create```
1. ```./deploy/deploy start```

