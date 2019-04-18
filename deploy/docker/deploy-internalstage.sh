#!/bin/bash
# NOTE that ic-docker-registry.nrel.gov:5000/ registry server is available only w/in nrel.  also, ssl certs for internal domains are a major hassle.
# allow your local docker to access ic-docker-registry w/out cert:
# 1. open docker preferences
# 2. Daemons: add 'ic-docker-registry:5000' as an insecure registry

#build images
export BT_DOCKER_REGISTRY_URI=ic-docker-registry.nrel.gov:5000/
export BT_ENV=stage
docker-compose -f ./deploy/docker/docker-compose-staging.yml build

#push images to registry
docker push "${BT_DOCKER_REGISTRY_URI}bt-web-${BT_ENV}:latest"
docker push "${BT_DOCKER_REGISTRY_URI}bt-worker-${BT_ENV}:latest"

#copy stack definition to staging server
scp ./deploy/docker/docker-compose-development.yml 1lv11openstu01.nrel.gov:docker-compose.yml
ssh 1lv11openstu01.nrel.gov "docker pull ${BT_DOCKER_REGISTRY}bt-web-${BT_ENV}:latest && docker pull ${BT_DOCKER_REGISTRY}bt-worker-${BT_ENV}:latest  && docker stack rm bt-${BT_ENV} && sleep 15 && docker stack deploy -c docker-compose.yml bt-${BT_ENV}"
