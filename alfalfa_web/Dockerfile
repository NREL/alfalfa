FROM node:16 AS base
ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/alfalfa

COPY alfalfa_web/package.json alfalfa_web/package-lock.json /srv/alfalfa/
RUN npm install

COPY alfalfa_web /srv/alfalfa

ARG NODE_ENV
RUN npm run build
CMD [ "npm", "start" ]

# **** Staged build for running in development mode ****
FROM base AS dev

# The docker-compose will require the mounting
# of the files into the container, see docker-compose.dev.yml

WORKDIR /srv/alfalfa

# Run in watch mode so it will automatically restart
CMD [ "npm", "run", "watch" ]
