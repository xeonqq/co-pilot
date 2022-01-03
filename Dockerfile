ARG UBUNTU_VERSION=18.04

FROM ubuntu:${UBUNTU_VERSION} AS base
MAINTAINER Qian Qian (xeonqq@gmail.com)
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y \
    python3.7 \
    python3-pip

RUN ln -s $(which python3.7) /usr/local/bin/python3
RUN ln -s $(which python3.7) /usr/local/bin/python
RUN python3 -m pip --no-cache-dir install --upgrade \
    "pip<20.3" \
    setuptools
RUN apt-get update
RUN apt-get install -y \
      build-essential \
      curl \
      git \
      wget \
      openjdk-8-jdk \
      python3-dev \
      virtualenv \
      swig 

RUN apt-get update
RUN apt-get install -y \
      ffmpeg
RUN apt install -y libgl1-mesa-glx protobuf-compiler

RUN python3 -m pip install --no-cache-dir matplotlib videoio opencv-python
RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
RUN apt-get update
RUN apt-get install -y libedgetpu1-std
RUN apt-get install -y python3-pycoral
RUN apt-get install -y python3-tflite-runtime

ADD requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir opencv-contrib-python==4.4.0.46

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin
RUN apt-get install -y python3-tk


EXPOSE 5005
