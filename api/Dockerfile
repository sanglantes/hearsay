FROM python:3.13-slim

WORKDIR /app/api

COPY ./requirements.txt .

RUN set -eux \
    && apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        wget \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install -U spacy \
    && python -m spacy download en_core_web_sm \
    && apt-get remove -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

COPY . .
