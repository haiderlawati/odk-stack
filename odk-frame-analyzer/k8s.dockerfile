# Dockerfile for Frame Analyzer
# See also:
# https://github.com/python-poetry/poetry/issues/1879

# Build stage for basic Python environment
FROM python:3.8-slim-buster AS python-base

LABEL maintainer="Thomas Brockmeier <t.brockmeier@amsterdam.nl>"

    # Application user name
ENV APP_USER=www \
    # Suppress OS prompts
    DEBIAN_FRONTEND=noninteractive \
    # Poetry home directory
    POETRY_HOME="/opt/poetry" \
    # Suppress prompts from Poetry
    POETRY_NO_INTERACTION=1 \
    # Poetry version
    POETRY_VERSION=1.1.4 \
    # Create virtual environments in .venv directory in project root
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # Requirements and virtual environment directory
    PYSETUP_PATH=/opt/pysetup \
    VENV_PATH=/opt/pysetup/.venv \
    # Don't write .pyc files and don't buffer output to stdin/err
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Matplotlib config/cache directory
    MPLCONFIGDIR=/tmp/matplotlib \
    # Mount point
    APPLICATION_DIR=/srv/frame_analyzer

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Build stage to compile and install dependencies
FROM python-base AS builder-base

# Upgrade and install system libraries
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# Install project dependencies
WORKDIR $PYSETUP_PATH
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

# Continue from clean Python base image
FROM python-base AS development

# Copy in Poetry and virtual environment
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# CD to mount point
WORKDIR $APPLICATION_DIR
ENTRYPOINT python start_worker.py

# Continue from clean Python base image
FROM python-base AS production

# Create unprivileged user
RUN useradd --user-group --shell /bin/false $APP_USER
USER $APP_USER

# Copy in virtual environment and code
COPY --chown=$APP_USER:$APP_USER --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY --chown=$APP_USER:$APP_USER . $APPLICATION_DIR

# CD to application directory
WORKDIR $APPLICATION_DIR
RUN mkdir output && chown $APP_USER:$APP_USER output

ENTRYPOINT ["python", "start_worker_k8s.py"]
