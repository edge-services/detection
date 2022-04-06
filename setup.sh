#!/bin/bash

mkdir -p model

if [ $# -eq 0 ]; then
  DATA_DIR="./model"
else
  DATA_DIR="$1"
fi

# Install Python dependencies.
# python -m pip install pip --upgrade
python -m pip install --no-cache-dir -r requirements.txt

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
