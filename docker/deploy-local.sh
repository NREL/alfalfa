#!/bin/bash
 # requires that 'docker swarm init' has been run on development machine

# Docker swarm doesn't load .env by default 
export $(cat .env)
docker-compose -f ./docker/docker-compose-noaws.yml build
docker stack rm "bt-${BT_ENV}"
sleep 25s #docker swarm sometimes has errors w/ default network container if you try to redeploy immediately
docker stack deploy -c ./docker/docker-compose-noaws.yml bt-$BT_ENV
