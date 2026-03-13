FROM python:3.10

WORKDIR /app

RUN apt-get update
RUN apt-get install -y pipx
RUN pipx ensurepath

# Do this before installing poetry to ensure poetry is installed correctly
# See https://github.com/python-poetry/poetry/issues/4865#issuecomment-1063494729
ENV PATH="/root/.local/bin:$PATH" POETRY_VIRTUALENVS_CREATE="false"
RUN pipx install poetry --python=$(which python)  # https://stackoverflow.com/a/69828751/110255

RUN mkdir '/logs/'
COPY . /app
RUN poetry install --no-interaction --no-ansi