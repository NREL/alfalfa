FROM ubuntu:trusty

RUN apt-get update && apt-get -y install ca-certificates curl python-software-properties

RUN cd /root

WORKDIR /root

COPY alfalfa_web/package.json alfalfa_web/package-lock.json /root/

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y ca-certificates nodejs \
    && npm install

COPY alfalfa_web /root
COPY lib/dbops.js /root/server/

ARG NODE_ENV
RUN npm run build

CMD [ "npm", "start" ]
