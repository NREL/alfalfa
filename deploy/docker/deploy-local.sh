#!/bin/bash
 # requires that 'docker swarm init' has been run on development machine
 export BT_ENV=development
docker-compose -f ./deploy/docker/docker-compose-noaws.yml build
docker stack rm "bt-${BT_ENV}"
sleep 25s #docker swarm sometimes has errors w/ default network container if you try to redeploy immediately
docker stack deploy -c ./deploy/docker/docker-compose-noaws.yml bt-$BT_ENV
