#!/bin/bash

mkdir -p data

while getopts m:a: flag
do
    case "${flag}" in
        a) arch=${OPTARG};;
        m) model=${OPTARG};;
    esac
done

if [ -z $model ]; then
  DATA_DIR="model"
else
  DATA_DIR="$model"
fi

mkdir -p $DATA_DIR

# apt-get update

if [ $arch = 'arm32v7' ]; then
  pip install --no-cache-dir --user tflite-runtime==2.5.0
  pip install --no-cache-dir --user  tflite-support==0.3.1
else
  pip install --no-cache-dir --user  tflite-runtime==2.7.0
  pip install --no-cache-dir --user  tflite-support==0.3.1  
fi

# echo $requirement

# Install Python dependencies.
# python -m pip install pip --upgrade
# pip install --no-cache-dir -r $requirement 
    # && find /usr/local \
    #    \( -type d -a -name test -o -name tests \) \
    #    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    #    -exec rm -rf '{}' + \
    # && cd / \
    # && rm -rf /usr/src/python ~/.cache

# Download TF Lite model with metadata.
FILE=${DATA_DIR}/model.tflite
if [ ! -f "$FILE" ]; then
  # curl \
  #   -L 'https://tfhub.dev/tensorflow/lite-model/efficientnet/lite0/uint8/2?lite-format=tflite' \
  #   -o ${FILE}
  curl \
    -L 'https://gurvsin3-visualrecognition.s3.jp-tok.cloud-object-storage.appdomain.cloud/mobilenet.tflite' \
    -o ${FILE}
fi
