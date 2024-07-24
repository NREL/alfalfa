FROM ghcr.io/nrel/alfalfa-dependencies:multiplatform AS base

USER root

ENV HOME /alfalfa

WORKDIR $HOME
# Need to set the lang to use Python 3.8 with Poetry
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

# Install poetry
RUN pip3 install poetry==1.8.3
RUN poetry config virtualenvs.options.system-site-packages true \
  && poetry config virtualenvs.create false

# Copy and install poetry-based dependencies
COPY pyproject.toml /alfalfa
COPY poetry.lock /alfalfa

# Install 'production' dependencies from poetry
RUN poetry install --only main

# Include the path to where alfalfa_worker is so that system calls can find it.
ENV  PYTHONPATH="/alfalfa:${PYTHONPATH}"

COPY ./alfalfa_worker /alfalfa/alfalfa_worker

RUN pip3.8 install virtualenv \
  && pip3.8 install -r /alfalfa/alfalfa_worker/energyplus_requirements.txt

COPY ./deploy /alfalfa/deploy
COPY ./deploy/wait-for-it.sh /usr/local/wait-for-it.sh

WORKDIR $HOME/alfalfa_worker


CMD ["/alfalfa/deploy/start_worker.sh"]

# **** Staged build for running in development mode ****
FROM base AS dev

# Reinstall poetry's dev dependencies by calling again without `--only main`,
RUN poetry install --with dev

# for live reloading celery and remote debugging
RUN poetry run pip3 install watchdog[watchmedo] remote-pdb

# COPY all the configuration files needed to run tests correctly
COPY . /alfalfa

# The docker-compose will require the mounting
# of the files into the container, see docker-compose.dev.yml

# Enable the ability to restart the service when
# the files change
CMD ["watchmedo", "auto-restart", "--directory=/alfalfa", "--pattern=*.py", "--recursive", "--", "/alfalfa/deploy/start_worker.sh"]
