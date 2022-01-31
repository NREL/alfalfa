FROM ubuntu:18.04 AS base

RUN apt-get update && \
    apt-get -y install \
        curl \
        git \
        vim

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs

RUN cd /srv
WORKDIR /srv/alfalfa

COPY alfalfa_web/package.json alfalfa_web/package-lock.json /srv/alfalfa/
RUN npm install

COPY alfalfa_web /srv/alfalfa
COPY lib/dbops.js /srv/alfalfa/server/

ARG NODE_ENV
RUN npm run build
CMD [ "npm", "start" ]


# **** Staged build for running in development mode - Still WIP****
FROM base AS dev

# The docker-compose will require the mounting
# of the files into the container, see docker-compose.dev.yml

# Enable the ability to restart the service when
# the files change
RUN npm install watch
COPY deploy/build_web.sh /srv/scripts/
ADD lib/dbops.js /srv/scripts/
RUN chmod +x /srv/scripts/build_web.sh

ENTRYPOINT /srv/scripts/build_web.sh

# Run in watch mode so it will automatically restart
# CMD [ "watch", "'npm run build'" "/srv/alfalfa" ]
CMD [ "npm", "start" ]
