FROM ubuntu:16.04

RUN apt-get update
RUN apt-get -y install ca-certificates curl
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get -y install python
RUN apt-get -y install python-pip
RUN pip install --upgrade pip

RUN cd /root

WORKDIR /root

COPY requirements.txt /root/
RUN pip install -r requirements.txt

COPY . /root

CMD [ "python", "-u", "master.py" ]
