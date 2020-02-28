# Based on https://softwarejourneyman.com/docker-python-install-wheels.html

#########################################
# Image WITH C compiler, building wheels for next stage
FROM python:3.6-alpine as bigimage

ENV LANG C.UTF-8

# Copy project files
COPY . /src/smartglass-core

# install the C compiler
RUN apk add --no-cache jq gcc musl-dev libffi-dev openssl-dev

# instead of installing, create a wheel
RUN pip wheel --wheel-dir=/root/wheels /src/smartglass-core

#########################################
# Image WITHOUT C compiler, installing the component from wheel
FROM python:3.6-alpine as smallimage

RUN apk add --no-cache openssl

COPY --from=bigimage /root/wheels /root/wheels

# Ignore the Python package index
# and look for archives in
# /root/wheels directory
RUN pip install \
      --no-index \
      --find-links=/root/wheels \
      xbox-smartglass-core

CMD [ "xbox-rest-server" ]
