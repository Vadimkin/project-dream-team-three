FROM ubuntu:16.04
MAINTAINER Vadim Klimenko <mail@vadimklimenko.com>

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
    python \
    python-dev \
    python-pip \
    ssh libmysqlclient-dev

ADD requirements.txt /dreamteam/requirements.txt
RUN pip install --upgrade pip && pip install -r /dreamteam/requirements.txt
