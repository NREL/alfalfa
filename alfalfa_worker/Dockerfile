FROM tobiasshapinsky/alfalfa-dependencies as base


ENV HOME /alfalfa

# Need to set the lang to use Python 3.8 with Poetry
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

ENV BUILD_DIR $HOME/build

WORKDIR $HOME

# There are some tweaks because Ubuntu 20.04 has a PEP404 error with the version.
# See https://bugs.launchpad.net/ubuntu/+source/python-debian/+bug/1926870
# The below installs poetry 1.1.15 because 1.2.1 has the error.
# It then copies over the poetry files and installs the dependencies with --no-dev
RUN pip3 install poetry==1.1.15

COPY . .
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# reinstall setuptools
RUN pip3 install setuptools==65.3.0

# Include the path to where alfalfa_worker is so that system calls can find it.
ENV  PYTHONPATH="${HOME}:${PYTHONPATH}"

COPY ./deploy/wait-for-it.sh /usr/local/wait-for-it.sh
COPY ./deploy/start_worker.sh start_worker.sh

WORKDIR /alfalfa/alfalfa_worker

ENV SEPARATE_PROCESS_JVM /usr/lib/jvm/java-8-openjdk-amd64/
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/

CMD ["/alfalfa/start_worker.sh"]

# **** Staged build for running in development mode ****
FROM base AS dev

# Reinstall poetry's dev dependencies by calling again without --no-dev,
# then reinstall setuptools to have pkg_resources available
RUN pip3 install virtualenv \
    && poetry config virtualenvs.create false \
    && poetry install \
    && pip3 install setuptools==65.3.0

# for remote debugging
RUN pip3 install remote-pdb

# for live reloading celery
RUN pip3 install watchdog[watchmedo]

# The docker-compose will require the mounting
# of the files into the container, see docker-compose.dev.yml

# Enable the ability to restart the service when
# the files change
CMD ["watchmedo", "auto-restart", "--directory=/alfalfa", "--pattern=*.py", "--recursive", "--", "/alfalfa/deploy/start_worker.sh"]
