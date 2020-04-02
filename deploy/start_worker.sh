#!/bin/bash

# Make sure that all of these other servers are ready before starting the worker node

echo "Waiting for minio to start"
/usr/local/wait-for-it.sh --strict -t 0 minio:9000

echo "Waiting for redis to start"
/usr/local/wait-for-it.sh --strict redis:6379

echo "Waiting for mongo to start"
/usr/local/wait-for-it.sh --strict redis:27017

cd /alfalfa
python3.5 -m alfalfa_worker
