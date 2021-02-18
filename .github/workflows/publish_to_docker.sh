export WEB_REGISTRY_URI=nrel/alfalfa-web
export WORKER_REGISTRY_URI=nrel/alfalfa-worker

if [ "${GITHUB_REF}" == "refs/heads/develop" ]; then
    VERSION_TAG="develop"
#TODO remove docker-pub check
elif [ "${GITHUB_REF}" == "refs/heads/docker-pub" ]; then
    VERSION_TAG="$(python ./.github/workflows/parse_version.py)"
elif [ "${GITHUB_REF}" == "refs/heads/master" ]; then
    VERSION_TAG="$(python ./.github/workflows/parse_version.py)"

docker-compose build
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
docker push ${WEB_REGISTRY_URI}:${VERSION_TAG}
docker push ${WORKER_REGISTRY_URI}:${VERSION_TAG}
