export WEB_REGISTRY_URI=nrel/alfalfa-web
export WORKER_REGISTRY_URI=nrel/alfalfa-worker

if [ "${GITHUB_REF}" == "refs/heads/develop" ]; then
    export VERSION_TAG="develop"
elif [ "${GITHUB_REF}" == "refs/heads/docker-pub" ]; then
    export VERSION_TAG="$(python ./.github/workflows/parse_version.py)"
elif [ "${GITHUB_REF}" == "refs/heads/master" ]; then
    export VERSION_TAG="$(python ./.github/workflows/parse_version.py)"
fi

docker-compose build
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
docker push ${WEB_REGISTRY_URI}:${VERSION_TAG}; (( exit_status = exit_status || $? ))
docker push ${WORKER_REGISTRY_URI}:${VERSION_TAG}; (( exit_status = exit_status || $? ))

if [ "${GITHUB_REF}" == "refs/heads/master" ]; then
    # Deploy master as the latest.
    docker tag ${WEB_REGISTRY_URI}:${VERSION_TAG} ${WEB_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
    docker tag ${WORKER_REGISTRY_URI}:${VERSION_TAG} ${WORKER_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))

    docker push ${WEB_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
    docker push ${WORKER_REGISTRY_URI}:latest; (( exit_status = exit_status || $? ))
fi

exit $exit_status
