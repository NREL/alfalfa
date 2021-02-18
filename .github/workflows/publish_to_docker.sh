export VERSION_TAG=develop
export WEB_REGISTRY_URI=nrel/alfalfa-web
export WORKER_REGISTRY_URI=nrel/alfalfa-worker
docker-compose build
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
docker push ${WEB_REGISTRY_URI}:${VERSION_TAG}
docker push ${WORKER_REGISTRY_URI}:${VERSION_TAG}
