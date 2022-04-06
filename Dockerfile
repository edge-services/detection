## docker build -t edge-services/detection_arm:latest .
## docker run --rm -it --name detection sinny777/detection_arm:latest


ARG ARCH=arm32v7
ARG PYTHON_VERSION=3.8.13
ARG OS=slim-buster

FROM ${ARCH}/python:${PYTHON_VERSION}-${OS}

LABEL org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.docker.dockerfile=".docker/Dockerfile.arm" \
    org.label-schema.license="Apache-2.0" \
    org.label-schema.name="EdgeDetection" \
    org.label-schema.version=${BUILD_VERSION} \
    org.label-schema.description="Edge Computing - Edge Detection Service" \
    org.label-schema.url="https://github.com/sinny777/edge-services" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-type="Git" \
    org.label-schema.vcs-url="https://github.com/sinny777/edge-services" \
    org.label-schema.arch=${ARCH} \
    authors="Gurvinder Singh <sinny777@gmail.com>"

USER root

# Updates and adds system required packages
RUN apt-get update && \
    apt-get -qy install curl ca-certificates nano make \
    build-essential wget fswebcam \
    cmake \
    gcc \
    -y --no-install-recommends --fix-missing apt-utils netcat && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

ADD . .

RUN chmod 755 /usr/src/app/setup.sh && \
    bash /usr/src/app/setup.sh

ENV LD_LIBRARY_PATH=/opt/vc/lib
ENV PATH="$PATH:/opt/vc/bin"
ENV TZ Asia/Kolkata
RUN echo "/opt/vc/lib" > /etc/ld.so.conf.d/00-vcms.conf \
    && ldconfig
# ADD 00-vmcs.conf /etc/ld.so.conf.d/
# RUN ldconfig

# ENV HOST=0.0.0.0 PORT=3000

# EXPOSE ${PORT}

CMD ["python", "classify.py"]