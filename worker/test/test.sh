#!/usr/bin/env bash

docker run -it --rm -v $(pwd):/test "alfalfa_worker:latest" ls
