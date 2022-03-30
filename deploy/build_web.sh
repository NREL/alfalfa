#!/bin/bash

# install the dependencies after launching the container with the 
# mounted folder
cd /srv/alfalfa
npm install

# build
npm run build

echo "finished with entrypoint script"