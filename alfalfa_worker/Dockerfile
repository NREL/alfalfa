FROM ubuntu:18.04 AS base

USER root

ENV HOME /home/alfalfa

# Need to set the lang to use Python 3.6 with Poetry
ENV  LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV ROOT_DIR /usr/local
ENV BUILD_DIR $HOME/build

WORKDIR /home/alfalfa

RUN apt-get update -y && apt-get install -y \
        ca-certificates \
        curl \
        libglu1 \
        libjpeg8 \
        libfreetype6 \
        libxi6 \
        libdbus-glib-1-2 \
        libfontconfig1 \
        libsm6 \
        gdebi-core \
        python3 \
        python3-pip \
        python3-dev \
        vim \
        liblapack-dev \
        build-essential \
        gfortran \
        libgfortran3 \
        cmake \
        git && \
    apt-get install -y git

# Use set in update-alternatives instead of config to
# provide non-interactive input.
RUN apt-get update \
    && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:openjdk-r/ppa \
    && apt-get update -y \
    && apt-get install -y openjdk-8-jdk-headless \
    && update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java \
    && update-alternatives --set javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac \
    && curl -SLO http://openstudio-resources.s3.amazonaws.com/bcvtb-linux.tar.gz \
    && tar -xzf bcvtb-linux.tar.gz \
    && apt-get install -y ca-certificates nodejs

ENV SPAWN_DOWNLOAD_BASE_URL https://spawn.s3.amazonaws.com/builds
ENV SPAWN_DOWNLOAD_FILENAME Spawn-0.0.1-1ad59a6dbf-Linux.tar.gz
ENV SPAWN_DOWNLOAD_URL ${SPAWN_DOWNLOAD_BASE_URL}/${SPAWN_DOWNLOAD_FILENAME}

ENV OPENSTUDIO_DOWNLOAD_FILENAME OpenStudio-3.1.0+e165090621-Linux.deb
ENV OPENSTUDIO_DOWNLOAD_URL https://github.com/NREL/OpenStudio/releases/download/v3.1.0/OpenStudio-3.1.0+e165090621-Linux.deb

ENV ENERGYPLUS_VERSION 9.4.0
ENV ENERGYPLUS_TAG v9.4.0
ENV ENERGYPLUS_SHA 998c4b761e

# mlep / external interface needs parts of EnergyPlus that are not included with OpenStudio
# expandobjects, runenergyplus might be two examples, but the need to install EnergyPlus separately from OpenStudio
# might be revaluated
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-Ubuntu18.04-x86_64.tar.gz
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

## OPENSTUDIO/ENERGYPLUS

# Extract Spawn executable
RUN curl -SLO ${SPAWN_DOWNLOAD_URL} \
    && mkdir /usr/local/Spawn-0.0.1 \
    && tar -C /usr/local/Spawn-0.0.1/ --strip-components=1 -xzf ${SPAWN_DOWNLOAD_FILENAME} \
    && ln -s /usr/local/Spawn-0.0.1/bin/spawn /usr/local/bin/ \
    && rm ${SPAWN_DOWNLOAD_FILENAME}

# We would rather use the self extracting tarball distribution of EnergyPlus, but there appears to
# be a bug in the installation script so using the tar.gz manually here and making our own links
RUN curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && mkdir /usr/local/EnergyPlus-9-4-0 \
    && tar -C /usr/local/EnergyPlus-9-4-0/ --strip-components=1 -xzf $ENERGYPLUS_DOWNLOAD_FILENAME \
    && ln -s /usr/local/EnergyPlus-9-4-0/energyplus /usr/local/bin/ \
    && ln -s /usr/local/EnergyPlus-9-4-0/ExpandObjects /usr/local/bin/ \
    && ln -s /usr/local/EnergyPlus-9-4-0/runenergyplus /usr/local/bin/ \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL \
    && gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME \
    && rm -f $OPENSTUDIO_DOWNLOAD_FILENAME

## MODELICA

ENV FMIL_TAG 2.4
ENV FMIL_HOME $ROOT_DIR/fmil

ENV SUNDIALS_HOME $ROOT_DIR/sundials
ENV SUNDIALS_TAG v4.1.0

ENV ASSIMULO_TAG Assimulo-3.2.9

ENV PYFMI_TAG PyFMI-2.9.5

ENV OPENBLAS_TAG v0.3.20
ENV OPENBLAS_HOME $ROOT_DIR/OpenBLAS

WORKDIR $BUILD_DIR

# Build Sundials (for Assimulo)
RUN git clone --branch $SUNDIALS_TAG --depth 1 https://github.com/LLNL/sundials.git \
    && mkdir $SUNDIALS_HOME \
    && mkdir sundials_build \
    && cd sundials_build \
    && cmake -DLAPACK_ENABLE=ON -DCMAKE_INSTALL_PREFIX=$SUNDIALS_HOME ../sundials \
    && make install

# Build FMI Library (for PyFMI)
RUN git clone --branch $FMIL_TAG --depth 1 https://github.com/modelon-community/fmi-library.git \
    && mkdir $FMIL_HOME \
    && mkdir fmil_build \
    && cd fmil_build \
    && cmake -DFMILIB_INSTALL_PREFIX=$FMIL_HOME ../fmi-library \
    && make install

# Build OpenBLAS (provides BLAS for Assimulo)
RUN git clone --branch $OPENBLAS_TAG --depth 1 https://github.com/xianyi/OpenBLAS.git \
    && mkdir $OPENBLAS_HOME \
    && cd OpenBLAS \
    && make \
    && make PREFIX=$OPENBLAS_HOME install


COPY alfalfa_worker/requirements/requirements.txt $BUILD_DIR

# Reinstall/upgrade setuptools because this is needed for symfit (used in E+ Python)
RUN  python3 -m pip install --upgrade pip setuptools && \
     python3 -m pip install --ignore-installed -r $BUILD_DIR/requirements.txt

ENV LD_LIBRARY_PATH $SUNDIALS_HOME/lib:$OPENBLAS_HOME/lib:$LD_LIBRARY_PATH

RUN git clone --branch $ASSIMULO_TAG --depth 1 https://github.com/modelon-community/Assimulo.git \
    && cd Assimulo \
    && python3 setup.py install --sundials-home=$SUNDIALS_HOME --blas-home=$OPENBLAS_HOME/lib --blas-name=openblas --lapack-home=$OPENBLAS_HOME/lib

# Install PyFMI
RUN git clone --branch $PYFMI_TAG --depth 1 https://github.com/modelon-community/PyFMI.git \
     && cd PyFMI \
     && python3 setup.py install

# Clean up builds
RUN rm -rf $BUILD_DIR

WORKDIR /alfalfa
# Include the path to where alfalfa_worker is so that system calls can find it.
ENV  PYTHONPATH="/alfalfa:${PYTHONPATH}"

COPY . /alfalfa
COPY ./deploy/wait-for-it.sh /usr/local/wait-for-it.sh
COPY ./deploy/start_worker.sh start_worker.sh

WORKDIR /alfalfa/alfalfa_worker
# add back in the workflow.tar.gz, but this will be remove (i think)
# when we remove the osm support.
# RUN tar -czf workflow.tar.gz workflow
ENV SEPARATE_PROCESS_JVM /usr/lib/jvm/java-8-openjdk-amd64/
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/

CMD ["/alfalfa/start_worker.sh"]

# **** Staged build for running in development mode ****
FROM base AS dev

# Install poetry's dev dependencies by removing old lock
RUN rm -f poetry.lock && \
    python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install poetry==1.1.12 && \
    python3 -m poetry config virtualenvs.create false && \
    python3 -m poetry install

# for remote debugging
RUN pip install remote-pdb

# for live reloading celery
RUN pip install watchdog[watchmedo]

# The docker-compose will require the mounting
# of the files into the container, see docker-compose.dev.yml

# Enable the ability to restart the service when
# the files change
CMD ["watchmedo", "auto-restart", "--directory=/alfalfa/alfalfa_worker/worker_openstudio", "--pattern=*.py", "--recursive", "--", "/alfalfa/deploy/start_worker.sh"]

# **** Image with just OpenStudio and EnergyPlus ****
FROM ubuntu:18.04 AS alfalfa-openstudio
COPY --from=base /usr/local/EnergyPlus-9-4-0 /usr/local/EnergyPlus-9-4-0
# This is a WIP, need to decide how where the base libraries go because ./energyplus requires
# several libraries to already be installed on the core OS
