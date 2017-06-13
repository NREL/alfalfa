FROM ubuntu:16.04

ENV OPENSTUDIO_VERSION 2.1.1
ENV OPENSTUDIO_SHA 141d4b9cb6

ENV OPENSTUDIO_DOWNLOAD_BASE_URL https://s3.amazonaws.com/openstudio-builds/$OPENSTUDIO_VERSION
ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-$OPENSTUDIO_VERSION.$OPENSTUDIO_SHA-Linux.deb
ENV OPENSTUDIO_DOWNLOAD_URL $OPENSTUDIO_DOWNLOAD_BASE_URL/$OPENSTUDIO_DOWNLOAD_FILENAME

RUN apt-get update
RUN apt-get -y install ca-certificates curl
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get -y install libglu1 libjpeg8 libfreetype6 libxi6 libdbus-glib-1-2 libfontconfig1 libsm6 
RUN apt-get -y install gdebi-core
RUN apt-get -y install python
RUN apt-get -y install python-pip
RUN pip install --upgrade pip

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL
RUN gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME
RUN rm -f $OPENSTUDIO_DOWNLOAD_FILENAME

RUN cd /root

WORKDIR /root

COPY requirements.txt /root/
RUN pip install -r requirements.txt

COPY . /root

CMD [ "python", "-u", "master.py" ]
