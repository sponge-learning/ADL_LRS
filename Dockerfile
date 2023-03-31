FROM python:2.7.18

COPY . /adl_lrs
WORKDIR /adl_lrs

RUN apt-get update
RUN apt-get install -y postgresql
RUN pip install pip==20.3.4 'fabric<2.0' virtualenv .

# This Dockerfile is incomplete, but sufficient to test the installation of the code via `pip install .`
# I had a bit of a look at providing a complete Dockerfile/docker compose build, but decided it wasn't worth it
# since we never deploy the LRS as a standalone service, it's used as a library within Spark


