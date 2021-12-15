FROM ubuntu:18.04

RUN apt-get update && apt-get -y install curl git

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs

RUN cd /root
WORKDIR /root

COPY alfalfa_web/package.json alfalfa_web/package-lock.json /root/

RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
    && curl -fsSL https://deb.nodesource.com/setup_12.x | bash - \
    && apt-get install -y ca-certificates nodejs \
    && npm install

COPY alfalfa_web /root
COPY lib/dbops.js /root/server/

ARG NODE_ENV
RUN npm run build
CMD [ "npm", "start" ]
