FROM python:3.13-alpine

WORKDIR /app/api

COPY ./requirements.txt .

RUN set -eux \
    && apk add --no-cache --virtual .build-deps build-base \
        libressl-dev libffi-dev gcc musl-dev python3-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install -U spacy \
    && python -m spacy download en_core_web_sm \
    && rm -rf /root/.cache/pip

COPY . .