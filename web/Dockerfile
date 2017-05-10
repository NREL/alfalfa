FROM ubuntu:16.04

RUN apt-get update
RUN apt-get -y install ca-certificates curl
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get -y install nodejs

RUN cd /root

WORKDIR /root

COPY package.json /root/
RUN npm update

COPY . /root

CMD [ "npm", "start" ]
