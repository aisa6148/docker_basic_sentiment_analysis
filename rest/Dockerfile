#!/usr/bin/env bash
FROM python:3.8

ADD rest-server.py /

RUN pip3 install --upgrade pika redis jsonpickle requests flask

WORKDIR /srv
COPY    rest-server.py /srv

EXPOSE 5001
ENV FLASK_APP=rest-server.py
CMD [ "python3", "rest-server.py"]