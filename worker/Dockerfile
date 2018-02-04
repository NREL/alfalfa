FROM ubuntu:14.04

RUN cd /root
WORKDIR /root

RUN apt-get update -y && apt-get install -y \
    ca-certificates curl libglu1 libjpeg8 libfreetype6 libxi6 libdbus-glib-1-2 libfontconfig1 libsm6 gdebi-core python python-pip

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \ 
    && apt-get install -y nodejs

RUN apt-get update \
    && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:openjdk-r/ppa \
    && apt-get update -y \
    && apt-get install -y openjdk-8-jdk-headless \ 
    && update-alternatives --config java \ 
    && update-alternatives --config javac \ 
    && curl -SLO http://openstudio-resources.s3.amazonaws.com/bcvtb-linux.tar.gz \
    && tar -xzf bcvtb-linux.tar.gz

ENV OPENSTUDIO_VERSION 2.4.0
ENV OPENSTUDIO_SHA f58a3e1808

ENV OPENSTUDIO_DOWNLOAD_BASE_URL https://s3.amazonaws.com/openstudio-builds/$OPENSTUDIO_VERSION
ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-$OPENSTUDIO_VERSION.$OPENSTUDIO_SHA-Linux.deb
ENV OPENSTUDIO_DOWNLOAD_URL $OPENSTUDIO_DOWNLOAD_BASE_URL/$OPENSTUDIO_DOWNLOAD_FILENAME

ENV ENERGYPLUS_VERSION 8.8.0
ENV ENERGYPLUS_TAG v8.8.0
ENV ENERGYPLUS_SHA 7c3bbe4830

#ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://s3-us-west-1.amazonaws.com/alfalfa/dependencies 
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && chmod +x $ENERGYPLUS_DOWNLOAD_FILENAME \
    && echo "y\r" | ./$ENERGYPLUS_DOWNLOAD_FILENAME \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL \
    && gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME \
    && rm -f $OPENSTUDIO_DOWNLOAD_FILENAME

COPY requirements.txt /root/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY package.json package-lock.json /root/
RUN npm install 

COPY . /root
RUN tar -czf workflow.tar.gz workflow
RUN rm -rf workflow

CMD [ "python", "-u", "messageHandler.py" ]

