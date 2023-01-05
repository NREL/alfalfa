#!/bin/bash

# Make sure that all of these other servers are ready before starting the worker node

echo "Waiting for minio to start"
/usr/local/wait-for-it.sh --strict -t 0 minio:9000

echo "Waiting for redis to start"
/usr/local/wait-for-it.sh --strict redis:6379

echo "Waiting for mongo to start"
/usr/local/wait-for-it.sh --strict mongo:27017

echo "Historian Enable"
echo $HISTORIAN_ENABLE

if [[ $HISTORIAN_ENABLE = 'true' ]]
then
  echo "Historian enabled"

  echo "Waiting for influxdb to start"
  /usr/local/wait-for-it.sh --strict influxdb:8086

  echo "Waiting for grafana to start"
  /usr/local/wait-for-it.sh --strict grafana:3000
else
  echo "Historian not enabled"
fi

cd /alfalfa
# update the path to python, which is in the Poetry virtual environment
# The dependency warning still exists, but it is a warning. Eventually this 
# will be resolved when we move to a newer version of Ubuntu. 
# See https://bugs.launchpad.net/ubuntu/+source/python-debian/+bug/1926870
# Error: RequestsDependencyWarning: urllib3 (1.26.13) or chardet (3.0.4) doesn't match a supported version!
#        warnings.warn("urllib3 ({}) or chardet ({}) doesn't match a supported "
export PATH=$(poetry env info -p)/bin:${PATH}
python3 -m alfalfa_worker
