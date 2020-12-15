#!/bin/bash
set -e

# for all
pip install -U pip setuptools
pip install tox

# install docker-compose
export DOCKER_COMPOSE_VERSION=1.23.1
sudo rm /usr/local/bin/docker-compose
curl -L https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-`uname -s`-`uname -m` > docker-compose
chmod +x docker-compose
sudo mv docker-compose /usr/local/bin

if [[ "$COVERAGE" == "true" ]]; then
    pip install -U pytest-cov pytest-virtualenv coverage coveralls flake8 pre-commit
fi

travis-cleanup() {
    printf "Cleaning up environments ... "  # printf avoids new lines
    echo "DONE"
}
