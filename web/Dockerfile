FROM ubuntu:14.04

RUN apt-get update
RUN apt-get -y install ca-certificates curl
RUN apt-get -y install python-software-properties
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get -y install nodejs

RUN cd /root

WORKDIR /root

COPY package.json package-lock.json /root/
RUN npm install

COPY . /root

ARG NODE_ENV
RUN npm run build

CMD [ "npm", "start" ]
