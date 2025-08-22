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
        libopenblas-dev \
        liblapack-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --force-reinstall numpy scipy \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

COPY . .
