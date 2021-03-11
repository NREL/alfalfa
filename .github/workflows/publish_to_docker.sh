export WEB_REGISTRY_URI=nrel/alfalfa-web
export WORKER_REGISTRY_URI=nrel/alfalfa-worker
export HISTORIAN_GUI_REGISTRY_URI=nrel/alfalfa-grafana

# Here VERSION_TAG will override what is loaded from .env
if [ "${GITHUB_REF}" == "refs/heads/develop" ]; then
    export VERSION_TAG="develop"
# elif [ "${GITHUB_REF}" == "refs/heads/publish-grafana" ]; then
#     export VERSION_TAG="experimental"
elif [ "${GITHUB_REF}" == "refs/heads/main" ]; then
    export VERSION_TAG="$(python ./.github/workflows/parse_version.py)"
fi

docker-compose -f docker-compose.yml -f docker-compose-historian.yml build
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
echo "pushing ${WEB_REGISTRY_URI}:${VERSION_TAG}"
docker push ${WEB_REGISTRY_URI}:${VERSION_TAG}; (( exit_status = exit_status || $? ))
echo "pushing ${WORKER_REGISTRY_URI}:${VERSION_TAG}"
docker push ${WORKER_REGISTRY_URI}:${VERSION_TAG}; (( exit_status = exit_status || $? ))
echo "pushing ${HISTORIAN_GUI_REGISTRY_URI}:${VERSION_TAG}"
docker push ${HISTORIAN_GUI_REGISTRY_URI}:${VERSION_TAG}; (( exit_status = exit_status || $? ))

if [ "${GITHUB_REF}" == "refs/heads/main" ]; then
    # Deploy main as the latest.
    docker tag ${WEB_REGISTRY_URI}:${VERSION_TAG} ${WEB_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
    docker tag ${WORKER_REGISTRY_URI}:${VERSION_TAG} ${WORKER_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
    docker tag ${HISTORIAN_GUI_REGISTRY_URI}:${VERSION_TAG} ${HISTORIAN_GUI_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))

    docker push ${WEB_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
    docker push ${WORKER_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
    docker push ${HISTORIAN_GUI_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
fi

exit $exit_status
