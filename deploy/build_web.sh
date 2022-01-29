#!/bin/bash

# install the dependencies after launching the container with the 
# mounted folder
cd /srv/alfalfa
npm install

# Copy over the dbops.js file into the server folder. 
cp -f /srv/scripts/dbops.js /srv/alfalfa/server/dbops.js

# build
npm run build

echo "finished with entrypoint script"