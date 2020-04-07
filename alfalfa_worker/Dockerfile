FROM michaelwetter/ubuntu-1604_jmodelica_trunk

USER root
ENV HOME /home/alfalfa

WORKDIR /alfalfa

RUN apt-get update -y && apt-get install -y \
    ca-certificates curl libglu1 libjpeg8 libfreetype6 libxi6 libdbus-glib-1-2 libfontconfig1 libsm6 gdebi-core python3.5 python3-pip \
    && apt-get install -y git

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

ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-2.8.1.240bd7e1e8-Linux.deb
ENV OPENSTUDIO_DOWNLOAD_URL https://openstudio-ci-builds.s3-us-west-2.amazonaws.com/alfalfa/OpenStudio-2.8.1.240bd7e1e8-Linux.deb

ENV ENERGYPLUS_VERSION 9.1.0
ENV ENERGYPLUS_TAG v9.1.0
ENV ENERGYPLUS_SHA 08d2e308bb

ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-x86_64.tar.gz
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

# We would rather use the self extracting tarball distribution of EnergyPlus, but there appears to
# be a bug in the installation script so using the tar.gz manually here and making our own links
RUN curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && mkdir /usr/local/EnergyPlus-9-1-0 \
    && tar -C /usr/local/EnergyPlus-9-1-0/ --strip-components=1 -xzf $ENERGYPLUS_DOWNLOAD_FILENAME \
    && ln -s /usr/local/EnergyPlus-9-1-0/energyplus /usr/local/bin/ \
    && ln -s /usr/local/EnergyPlus-9-1-0/ExpandObjects /usr/local/bin/ \
    && ln -s /usr/local/EnergyPlus-9-1-0/runenergyplus /usr/local/bin/ \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL \
    && gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME \
    && rm -f $OPENSTUDIO_DOWNLOAD_FILENAME

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
  && python3.5 get-pip.py

COPY alfalfa_worker/requirements/production.txt /alfalfa/
RUN  python3.5 -m pip install --ignore-installed -r /alfalfa/production.txt
RUN  python -m pip install --ignore-installed -r /alfalfa/production.txt

COPY . /alfalfa
COPY ./deploy/wait-for-it.sh /usr/local/wait-for-it.sh
COPY ./deploy/start_worker.sh start_worker.sh

WORKDIR /alfalfa
RUN pip3 install .

WORKDIR /alfalfa/alfalfa_worker
RUN tar -czf workflow.tar.gz workflow

ENV ROOT_DIR /usr/local
ENV JMODELICA_HOME $ROOT_DIR/JModelica
ENV IPOPT_HOME $ROOT_DIR/Ipopt-3.12.4
ENV SUNDIALS_HOME $JMODELICA_HOME/ThirdParty/Sundials
ENV SEPARATE_PROCESS_JVM /usr/lib/jvm/java-8-openjdk-amd64/
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
ENV PYTHONPATH $PYTHONPATH:$JMODELICA_HOME/Python:$JMODELICA_HOME/Python/pymodelica

CMD [ "/alfalfa/start_worker.sh" ]
