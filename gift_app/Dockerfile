FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /opt/app

RUN mkdir -p /opt/app
WORKDIR /opt/app


# RUN apk update

RUN apk add --no-cache tzdata \
    && ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && echo "Europe/Moscow" >  /etc/timezone


ADD Pipfile Pipfile.lock /opt/app/
RUN pip install --no-cache-dir pipenv
RUN apk add --virtual .build-deps g++ \
    && mkdir /tmp/pipenv \
    && export PIPENV_CACHE_DIR=/tmp/pipenv \
    && pipenv install --deploy --system \
    && rm -rf /tmp/pipenv \
    && apk del .build-deps

COPY wait-for.sh /

RUN addgroup -S gift_app \
    && adduser -S -g gift_app gift_app \
    && chown gift_app:gift_app /home/gift_app \
    && chown gift_app:gift_app /opt/app

USER gift_app:gift_app

COPY . /opt/app

WORKDIR /opt/app

EXPOSE 8080
