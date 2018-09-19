FROM ubuntu:trusty

RUN apt-get update && apt-get -y install ca-certificates curl
RUN apt-get update && apt-get -y install python-software-properties
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get update && apt-get -y install nodejs npm

RUN cd /root

WORKDIR /root

COPY package.json package-lock.json /root/
COPY package.json /root/
RUN npm install

COPY . /root

ARG NODE_ENV
RUN npm run build

CMD [ "npm", "start" ]
