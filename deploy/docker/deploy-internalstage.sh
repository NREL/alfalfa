#!/bin/bash
# NOTE that ic-docker-registry.nrel.gov:5000/ registry server is available only w/in nrel.  also, ssl certs for internal domains are a major hassle.
# allow your local docker to access ic-docker-registry w/out cert:
# 1. open docker preferences
# 2. Daemons: add 'ic-docker-registry:5000' as an insecure registry

#build images
export BT_DOCKER_REGISTRY_URI=ic-docker-registry.nrel.gov:5000/
export BT_ENV=stage
export STAGE_DOMAIN=ic-docker-registry.nrel.gov #1lv11openstu01.nrel.gov 1lv11inten03.nrel.gov
# export WEB_REGISTRY_URI=313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/web
# export WORKER_REGISTRY_URI=313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/worker
# export AWS_ACCESS_KEY_ID=user
# export AWS_SECRET_ACCESS_KEY=password
# export NODE_ENV=none
docker-compose -f ./deploy/docker/docker-compose-noaws.yml build

#push images to registry
docker push "${BT_DOCKER_REGISTRY_URI}bt-web-${BT_ENV}:latest"
docker push "${BT_DOCKER_REGISTRY_URI}bt-worker-${BT_ENV}:latest"

#copy stack definition to staging server
scp ./deploy/docker/docker-compose-noaws.yml $STAGE_DOMAIN:docker-compose.yml
scp ./deploy/docker/.env-internalstage $STAGE_DOMAIN:.env
ssh $STAGE_DOMAIN "export $(cat .env) && docker pull ${BT_DOCKER_REGISTRY_URI}bt-web-${BT_ENV}:latest && docker pull ${BT_DOCKER_REGISTRY_URI}bt-worker-${BT_ENV}:latest  && docker stack rm bt-${BT_ENV} && sleep 20 && docker stack deploy -c docker-compose.yml bt-${BT_ENV}"
