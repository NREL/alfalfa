#!/bin/bash -e

docker-compose up --build -d
until curl -sf --output /dev/null "127.0.0.1"; do echo -n "."; sleep 1; done
