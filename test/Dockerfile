FROM ubuntu:bionic

RUN apt-get update -y && apt-get install -y python3 python3-pip
RUN pip3 install alfalfaclient
COPY . /test

CMD [ "python3", "/test/test.py" ]

