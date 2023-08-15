FROM python:3.7

RUN apt-get update
RUN apt-get install -y postgresql

COPY . /adl_lrs
WORKDIR /adl_lrs
RUN pip install -r requirements.txt

# This Dockerfile is incomplete, but sufficient to test the installation of the code via `pip install .`
# I had a bit of a look at providing a complete Dockerfile/docker compose build, but decided it wasn't worth it
# since we never deploy the LRS as a standalone service, it's used as a library within Spark


