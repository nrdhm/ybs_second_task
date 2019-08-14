FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /opt/app

RUN mkdir -p /opt/app
WORKDIR /opt/app


RUN apk update

RUN apk add tzdata \
    && ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && echo "Europe/Moscow" >  /etc/timezone


ADD Pipfile Pipfile.lock /opt/app/
RUN pip install pipenv
RUN apk add g++ \
    && pipenv install --deploy --system \
    && apk del g++

COPY wait-for.sh /

COPY . /opt/app
