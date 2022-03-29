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
        wget \
        cmake \
        libopenmpi-dev \
        git && \
    apt-get install -y git

RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

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

WORKDIR $BUILD_DIR

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

# We would rather use the self extracting tarball distribution of EnergyPlus, but there appears to
# be a bug in the installation script so using the tar.gz manually here and making our own links
RUN curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && mkdir /usr/local/EnergyPlus-9-4-0 \
    && tar -C /usr/local/EnergyPlus-9-4-0/ --strip-components=1 -xzf $ENERGYPLUS_DOWNLOAD_FILENAME \
    && ln -s /usr/local/EnergyPlus-9-4-0/energyplus /usr/local/bin/ \
    && ln -s /usr/local/EnergyPlus-9-4-0/ExpandObjects /usr/local/bin/ \
    && ln -s /usr/local/EnergyPlus-9-4-0/runenergyplus /usr/local/bin/ \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME

ENV ENERGYPLUS_DIR /usr/local/EnergyPlus-9-4-0

RUN curl -SLO $OPENSTUDIO_DOWNLOAD_URL \
    && gdebi -n $OPENSTUDIO_DOWNLOAD_FILENAME \
    && rm -f $OPENSTUDIO_DOWNLOAD_FILENAME

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

ENV OPENBLAS_TAG v0.3.20
ENV OPENBLAS_HOME $ROOT_DIR

ENV SUPERLU_HOME $ROOT_DIR/SuperLU_MT_3.1


# Build FMI Library (for PyFMI)
RUN git clone --branch $FMIL_TAG --depth 1 https://github.com/modelon-community/fmi-library.git \
    && mkdir $FMIL_HOME \
    && mkdir fmil_build \
    && cd fmil_build \
    && cmake -DFMILIB_INSTALL_PREFIX=$FMIL_HOME ../fmi-library \
    && make install

ENV LD_LIBRARY_PATH $ROOT_DIR/lib:/home/alfalfa/build/SuperLU_MT_3.1/lib:$LD_LIBRARY_PATH

# Build OpenBLAS (provides BLAS for Assimulo)
RUN git clone --branch $OPENBLAS_TAG --depth 1 https://github.com/xianyi/OpenBLAS.git \
    && cd OpenBLAS \
    && make \
    && make PREFIX=$OPENBLAS_HOME install

# Build SuperLU (groan)
RUN apt install -y libatlas-base-dev liblapack-dev libopenmpi-dev libsuitesparse-dev csh
COPY alfalfa_worker/build/make.inc $BUILD_DIR

RUN cd $ROOT_DIR \
    && curl -SLO http://crd-legacy.lbl.gov/~xiaoye/SuperLU/superlu_mt_3.1.tar.gz \
    && tar -xzf superlu_mt_3.1.tar.gz \
    && cd SuperLU_MT_3.1 \
    && rm make.inc \
    && cp $BUILD_DIR/make.inc make.inc \
    && make lib

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
    -DCMAKE_CXX_FLAGS='-fPIC' \
    -DCMAKE_C_FLAGS='-fPIC' \
    && make \
    && make install

COPY pyproject.toml $BUILD_DIR
COPY poetry.lock $BUILD_DIR

# Reinstall/upgrade setuptools because this is needed for symfit (used in E+ Python)
RUN  pip3 install --upgrade pip setuptools && \
     pip3 install poetry==1.1.12 && \
     python3 -m poetry config virtualenvs.create false && \
     python3 -m poetry install --no-dev

RUN git clone --branch $ASSIMULO_TAG --depth 1 https://github.com/modelon-community/Assimulo.git \
     && cd Assimulo \
     && python3 setup.py install \
     --sundials-home=$SUNDIALS_HOME \
     --blas-home=$OPENBLAS_HOME/lib \
     --blas-name=openblas \
     --lapack-home=$OPENBLAS_HOME/lib \
     --superlu-home=$SUPERLU_HOME \
     --extra-c-flags="-fPIC"


# Install PyFMI
RUN git clone --branch $PYFMI_TAG --depth 1 https://github.com/modelon-community/PyFMI.git \
    && cd PyFMI \
    && python setup.py install

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
    pip install --upgrade pip setuptools && \
    pip install poetry==1.1.12 && \
    python -m poetry config virtualenvs.create false && \
    python -m poetry install

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
