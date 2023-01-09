FROM ubuntu:20.04 AS base

USER root

ENV HOME /home/alfalfa

# Need to set the lang to use Python 3.8 with Poetry
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV ROOT_DIR /usr/local
ENV BUILD_DIR $HOME/build

WORKDIR /home/alfalfa

# Until we can support E+ 22.1.0 we need to install python 3.8 (thus deadsnakes/ppa)
# This step should probably be connected to the next one, but due to the nature of NREL's
# firewall this step must be run off VPN. This way you don't need to log off everytime you
# update apt packaged, at least.
RUN apt-get update --allow-unauthenticated --allow-insecure-repositories\
    && apt install -y software-properties-common \
    && add-apt-repository ppa:openjdk-r/ppa \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y \
    ca-certificates \
    curl \
    gdebi-core \
    vim \
    wget \
    git \
    openjdk-8-jdk-headless \
    liblapack-dev \
    gfortran \
    libgfortran4 \
    cmake \
    python3-venv \
    python3-pip \
    libblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Use set in update-alternatives instead of config to
# provide non-interactive input.
RUN update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java \
    && update-alternatives --set javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac \
    && curl -SLO http://openstudio-resources.s3.amazonaws.com/bcvtb-linux.tar.gz \
    && tar -xzf bcvtb-linux.tar.gz \
    && rm bcvtb-linux.tar.gz

WORKDIR $BUILD_DIR


ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-3.5.0+7b14ce1588-Ubuntu-20.04.deb
ENV OPENSTUDIO_DOWNLOAD_URL https://github.com/NREL/OpenStudio/releases/download/v3.5.0/OpenStudio-3.5.0+7b14ce1588-Ubuntu-20.04.deb

ENV ENERGYPLUS_VERSION 22.2.0
ENV ENERGYPLUS_TAG 22.2.0
ENV ENERGYPLUS_SHA c249759bad
ENV ENERGYPLUS_DIR /usr/local/EnergyPlus-22-2-0

# mlep / external interface needs parts of EnergyPlus that are not included with OpenStudio
# expandobjects, runenergyplus might be two examples, but the need to install EnergyPlus separately from OpenStudio
# might be revaluated
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/TShapinsky/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-22.2.0-c249759bad-Linux-Ubuntu20.04-x86_64.tar.gz
ENV ENERGYPLUS_DOWNLOAD_URL https://github.com/NREL/EnergyPlus/releases/download/v22.2.0/EnergyPlus-22.2.0-c249759bad-Linux-Ubuntu20.04-x86_64.tar.gz
# ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-3.3.0+ad235ff36e-Ubuntu-20.04.deb
# ENV OPENSTUDIO_DOWNLOAD_URL https://github.com/NREL/OpenStudio/releases/download/v3.3.0/OpenStudio-3.3.0+ad235ff36e-Ubuntu-20.04.deb

# ENV ENERGYPLUS_VERSION 9.6.0
# ENV ENERGYPLUS_TAG 9.6-3.8
# ENV ENERGYPLUS_SHA e78d88a246
# ENV ENERGYPLUS_DIR /usr/local/EnergyPlus-9-6-0

# # mlep / external interface needs parts of EnergyPlus that are not included with OpenStudio
# # expandobjects, runenergyplus might be two examples, but the need to install EnergyPlus separately from OpenStudio
# # might be revaluated
# ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/TShapinsky/EnergyPlus/releases/download/$ENERGYPLUS_TAG
# ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-Ubuntu20.04-x86_64.tar.gz
# ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

# We would rather use the self extracting tarball distribution of EnergyPlus, but there appears to
# be a bug in the installation script so using the tar.gz manually here and making our own links
RUN curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && mkdir $ENERGYPLUS_DIR \
    && tar -C $ENERGYPLUS_DIR/ --strip-components=1 -xzf $ENERGYPLUS_DOWNLOAD_FILENAME \
    && ln -s $ENERGYPLUS_DIR/energyplus /usr/local/bin/ \
    && ln -s $ENERGYPLUS_DIR/ExpandObjects /usr/local/bin/ \
    && ln -s $ENERGYPLUS_DIR/runenergyplus /usr/local/bin/ \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL \
    && gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME \
    && rm -f $OPENSTUDIO_DOWNLOAD_FILENAME \
    && cd /usr/local/openstudio* \
    && rm -rf EnergyPlus \
    && ln -s $ENERGYPLUS_DIR EnergyPlus

# Install commands for Spawn
ENV SPAWN_VERSION=0.3.0-69040695f9
RUN wget https://spawn.s3.amazonaws.com/custom/Spawn-$SPAWN_VERSION-Linux.tar.gz \
    && tar -C /usr/local/ -xzf Spawn-$SPAWN_VERSION-Linux.tar.gz \
    && ln -s /usr/local/Spawn-$SPAWN_VERSION-Linux/bin/spawn-$SPAWN_VERSION /usr/local/bin/ \
    && rm Spawn-$SPAWN_VERSION-Linux.tar.gz

## MODELICA
ENV FMIL_TAG 2.4
ENV FMIL_HOME $ROOT_DIR/fmil

ENV SUNDIALS_HOME $ROOT_DIR
ENV SUNDIALS_TAG v4.1.0

ENV ASSIMULO_TAG Assimulo-3.2.9

ENV PYFMI_TAG PyFMI-2.9.5

ENV SUPERLU_HOME $ROOT_DIR/SuperLU_MT_3.1

# Modelica requires libgfortran3 which is not in apt for 20.04
RUN wget http://archive.ubuntu.com/ubuntu/pool/universe/g/gcc-6/gcc-6-base_6.4.0-17ubuntu1_amd64.deb \
    && wget http://archive.ubuntu.com/ubuntu/pool/universe/g/gcc-6/libgfortran3_6.4.0-17ubuntu1_amd64.deb \
    && dpkg -i gcc-6-base_6.4.0-17ubuntu1_amd64.deb \
    && dpkg -i libgfortran3_6.4.0-17ubuntu1_amd64.deb \
    && ln -s /usr/lib/x86_64-linux-gnu/libffi.so.7 /usr/lib/x86_64-linux-gnu/libffi.so.6 \
    && rm *.deb

# Build FMI Library (for PyFMI)
RUN git clone --branch $FMIL_TAG --depth 1 https://github.com/modelon-community/fmi-library.git \
    && mkdir $FMIL_HOME \
    && mkdir fmil_build \
    && cd fmil_build \
    && cmake -DFMILIB_INSTALL_PREFIX=$FMIL_HOME ../fmi-library \
    && make install \
    && cd .. && rm -rf fmi-library fmil_build

# Build SuperLU (groan)
COPY alfalfa_worker/build/make.inc $BUILD_DIR

RUN cd $ROOT_DIR \
    && curl -SLO http://crd-legacy.lbl.gov/~xiaoye/SuperLU/superlu_mt_3.1.tar.gz \
    && tar -xzf superlu_mt_3.1.tar.gz \
    && cd SuperLU_MT_3.1 \
    && rm make.inc \
    && cp $BUILD_DIR/make.inc make.inc \
    && make lib

ENV LD_LIBRARY_PATH $ROOT_DIR/lib:$SUPERLU_HOME/lib:$LD_LIBRARY_PATH

# Build Sundials with SuperLU(for Assimulo)
RUN git clone --branch $SUNDIALS_TAG --depth 1 https://github.com/LLNL/sundials.git \
    && mkdir sundials_build \
    && cd sundials_build \
    && cmake ../sundials \
    -DPTHREAD_ENABLE=1 \
    -DBLAS_ENABLE=1 \
    -DLAPACK_LIBRARIES='-llapack -lblas' \
    -DLAPACK_ENABLE=1 \
    -DSUPERLUMT_ENABLE=1 \
    -DSUNDIALS_INDEX_SIZE=32 \
    -DSUPERLUMT_INCLUDE_DIR=$SUPERLU_HOME/SRC \
    -DSUPERLUMT_LIBRARY_DIR=$SUPERLU_HOME/lib \
    -DSUPERLUMT_LIBRARIES='-lblas' \
    && make \
    && make install \
    && cd .. && rm -rf sundials sundials_build

# This is required for Assimulo to build correctly with setuptools 60+
ENV SETUPTOOLS_USE_DISTUTILS stdlib

# Install poetry
RUN pip3 install poetry==1.3.1

WORKDIR /alfalfa

# Copy and install poetry-based dependencies
COPY pyproject.toml /alfalfa
COPY poetry.lock /alfalfa

# Install 'production' dependencies from poetry
RUN poetry install --only main

# Install Assimulo for PyFMI
RUN git clone --branch $ASSIMULO_TAG --depth 1 https://github.com/modelon-community/Assimulo.git \
     && cd Assimulo \
     && poetry run python setup.py install \
     --sundials-home=$SUNDIALS_HOME \
     --blas-home=/usr/lib/x86_64-linux-gnu \
     --lapack-home=/usr/lib/x86_64-linux-gnu/lapack/ \
     --superlu-home=$SUPERLU_HOME \
     && cd .. && rm -rf Assimulo

# Install PyFMI
RUN git clone --branch $PYFMI_TAG --depth 1 https://github.com/modelon-community/PyFMI.git \
    && cd PyFMI \
    && poetry run python setup.py install \
    && cd .. && rm -rf PyFMI

WORKDIR /alfalfa

# Include the path to where alfalfa_worker is so that system calls can find it.
ENV  PYTHONPATH="/alfalfa:${PYTHONPATH}"

COPY . /alfalfa
COPY ./deploy/wait-for-it.sh /usr/local/wait-for-it.sh

# update the path to python, which is in the Poetry virtual environment.
# The path (mfknN3Ol) is generated by Poetry and should be updated if the
# install path changes.
#
# The dependency warning still exists, but it is a warning. Eventually this
# will be resolved when we move to a newer version of Ubuntu.
# See https://bugs.launchpad.net/ubuntu/+source/python-debian/+bug/1926870
# Error: RequestsDependencyWarning: urllib3 (1.26.13) or chardet (3.0.4) doesn't match a supported version!
#        warnings.warn("urllib3 ({}) or chardet ({}) doesn't match a supported
ENV PATH=/home/alfalfa/.cache/pypoetry/virtualenvs/alfalfa-mfknN3Ol-py3.8/bin:$PATH
WORKDIR /alfalfa/alfalfa_worker

ENV SEPARATE_PROCESS_JVM /usr/lib/jvm/java-8-openjdk-amd64/
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
# for EPtoBRICK
RUN pip3 install brickschema rdflib opyplus termcolor

CMD ["/alfalfa/deploy/start_worker.sh"]

# **** Staged build for running in development mode ****
FROM base AS dev

# Reinstall poetry's dev dependencies by calling again without --no-dev,
# then reinstall setuptools to have pkg_resources available
RUN pip3 install virtualenv \
    && poetry config virtualenvs.create false \
    && poetry install --with dev\
    && pip3 install setuptools==65.3.0

# for remote debugging
RUN pip3 install remote-pdb

# for live reloading celery
RUN pip3 install watchdog[watchmedo]

# The docker-compose will require the mounting
# of the files into the container, see docker-compose.dev.yml

# for the EnergyPlus to BRICK measure
RUN gem install rdf-rdfxml sparql-client rdf-turtle

# Enable the ability to restart the service when
# the files change
CMD ["watchmedo", "auto-restart", "--directory=/alfalfa", "--pattern=*.py", "--recursive", "--", "/alfalfa/deploy/start_worker.sh"]
