FROM ubuntu:16.04

ENV OPENSTUDIO_VERSION 2.1.1
ENV OPENSTUDIO_SHA 141d4b9cb6

ENV OPENSTUDIO_DOWNLOAD_BASE_URL https://s3.amazonaws.com/openstudio-builds/$OPENSTUDIO_VERSION
ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-$OPENSTUDIO_VERSION.$OPENSTUDIO_SHA-Linux.deb
ENV OPENSTUDIO_DOWNLOAD_URL $OPENSTUDIO_DOWNLOAD_BASE_URL/$OPENSTUDIO_DOWNLOAD_FILENAME

# EnergyPlus install commands from,
# https://github.com/NREL/docker-energyplus/blob/master/Dockerfile
# This is not ideal. The tarballs are not named nicely and EnergyPlus versioning is strange
ENV ENERGYPLUS_VERSION 8.7.0
ENV ENERGYPLUS_TAG v8.7.0
ENV ENERGYPLUS_SHA 78a111df4a

# This should be x.y.z, but EnergyPlus convention is x-y-z
ENV ENERGYPLUS_INSTALL_VERSION 8-7-0

# Downloading from Github
# e.g. https://github.com/NREL/EnergyPlus/releases/download/v8.3.0/EnergyPlus-8.3.0-6d97d074ea-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME


# Collapse the update of packages, download and installation into one command
# to make the container smaller & remove a bunch of the auxiliary apps/files
# that are not needed in the container
RUN apt-get update && apt-get install -y ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && chmod +x $ENERGYPLUS_DOWNLOAD_FILENAME \
    && echo "y\r" | ./$ENERGYPLUS_DOWNLOAD_FILENAME \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

#RUN apt-get update
#RUN apt-get -y install ca-certificates curl
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

CMD [ "python", "-u", "simulationManager.py" ]
