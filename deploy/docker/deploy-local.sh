#!/bin/bash
 # requires that 'docker swarm init' has been run on development machine
export BT_ENV=development
export WEB_REGISTRY_URI=313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/web
export WORKER_REGISTRY_URI=313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/worker
export AWS_ACCESS_KEY_ID=user
export AWS_SECRET_ACCESS_KEY=password
export NODE_ENV=none
export S3_URL=http://minio:9000
docker-compose -f ./deploy/docker/docker-compose-noaws.yml build
docker stack rm "bt-${BT_ENV}"
sleep 25s #docker swarm sometimes has errors w/ default network container if you try to redeploy immediately
docker stack deploy -c ./deploy/docker/docker-compose-noaws.yml bt-$BT_ENV
