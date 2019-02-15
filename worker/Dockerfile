FROM michaelwetter/ubuntu-1604_jmodelica_trunk

USER root
ENV HOME /home/root

RUN cd /root
WORKDIR /root

RUN apt-get update -y && apt-get install -y \
    ca-certificates curl libglu1 libjpeg8 libfreetype6 libxi6 libdbus-glib-1-2 libfontconfig1 libsm6 gdebi-core python3.5 python3-pip

RUN apt-get update \
    && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:openjdk-r/ppa \
    && apt-get update -y \
    && apt-get install -y openjdk-8-jdk-headless \ 
    && update-alternatives --config java \ 
    && update-alternatives --config javac \ 
    && curl -SLO http://openstudio-resources.s3.amazonaws.com/bcvtb-linux.tar.gz \
    && tar -xzf bcvtb-linux.tar.gz \
    && curl -sL https://deb.nodesource.com/setup_6.x | bash - \ 
    && apt-get install -y ca-certificates nodejs

###  ENV OPENSTUDIO_VERSION 2.7.0
###  ENV OPENSTUDIO_TAG v2.7.0
###  ENV OPENSTUDIO_SHA 544f363db5
###  
###  #https://github.com/NREL/OpenStudio/releases/download/v2.7.0/OpenStudio-2.7.0.544f363db5-Linux.deb
###  ENV OPENSTUDIO_DOWNLOAD_BASE_URL https://github.com/NREL/OpenStudio/releases/download/$OPENSTUDIO_TAG
###  #ENV OPENSTUDIO_DOWNLOAD_BASE_URL https://s3.amazonaws.com/openstudio-builds/$OPENSTUDIO_VERSION
###  ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-$OPENSTUDIO_VERSION.$OPENSTUDIO_SHA-Linux.deb
###  ENV OPENSTUDIO_DOWNLOAD_URL $OPENSTUDIO_DOWNLOAD_BASE_URL/$OPENSTUDIO_DOWNLOAD_FILENAME

ENV OPENSTUDIO_VERSION 2.7.2
ENV OPENSTUDIO_TAG v2.7.2
ENV OPENSTUDIO_SHA 5b35dd928c

ENV OPENSTUDIO_DOWNLOAD_BASE_URL https://openstudio-builds.s3.amazonaws.com/2.7.2
ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-$OPENSTUDIO_VERSION.$OPENSTUDIO_SHA-Linux.deb
ENV OPENSTUDIO_DOWNLOAD_URL $OPENSTUDIO_DOWNLOAD_BASE_URL/$OPENSTUDIO_DOWNLOAD_FILENAME

ENV ENERGYPLUS_VERSION 9.0.1
ENV ENERGYPLUS_TAG v9.0.1
ENV ENERGYPLUS_SHA bb7ca4f0da

#https://github.com/NREL/EnergyPlus/releases/download/v9.0.1/EnergyPlus-9.0.1-bb7ca4f0da-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
#ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://s3-us-west-1.amazonaws.com/alfalfa/dependencies 
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && chmod +x $ENERGYPLUS_DOWNLOAD_FILENAME \
    && echo "y\r" | ./$ENERGYPLUS_DOWNLOAD_FILENAME \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL \
    && gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME \
    && rm -f $OPENSTUDIO_DOWNLOAD_FILENAME

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
  && python3.5 get-pip.py

COPY requirements.txt /root/
RUN  python3.5 -m pip install --ignore-installed -r requirements.txt
RUN  python -m pip install --ignore-installed -r requirements.txt

COPY package.json package-lock.json /root/

RUN npm install

COPY . /root
RUN cd addsite && tar -czf ../workflow.tar.gz workflow

ENV ROOT_DIR /usr/local
ENV JMODELICA_HOME $ROOT_DIR/JModelica
ENV IPOPT_HOME $ROOT_DIR/Ipopt-3.12.4
ENV SUNDIALS_HOME $JMODELICA_HOME/ThirdParty/Sundials
ENV SEPARATE_PROCESS_JVM /usr/lib/jvm/java-8-openjdk-amd64/
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
ENV PYTHONPATH $PYTHONPATH:$JMODELICA_HOME/Python:$JMODELICA_HOME/Python/pymodelica

CMD [ "python3.5", "-u", "messageHandler.py" ]

