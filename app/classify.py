# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# python classify.py --model ./model/model.tflite --maxResults 3

"""Main script to run image classification."""

import os
import argparse
from nis import cat
import sys
import time

# import numpy as np
import cv2
# from PIL import Image
from image_classifier import ImageClassifier
from image_classifier import ImageClassifierOptions
from utils import CommonUtils

# Visualization parameters
_ROW_SIZE = 20  # pixels
_LEFT_MARGIN = 24  # pixels
_TEXT_COLOR = (0, 0, 255)  # red
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_FPS_AVERAGE_FRAME_COUNT = 10


def run(model: str, max_results: int, num_threads: int, enable_edgetpu: bool,
        camera_id: int, width: int, height: int) -> None:
  """Continuously run inference on images acquired from the camera.

  Args:
      model: Name of the TFLite image classification model.
      max_results: Max of classification results.
      num_threads: Number of CPU threads to run the model.
      enable_edgetpu: Whether to run the model on EdgeTPU.
      camera_id: The camera id to be passed to OpenCV.
      width: The width of the frame captured from the camera.
      height: The height of the frame captured from the camera.
  """

  # Initialize the image classification model
  options = ImageClassifierOptions(
      num_threads=num_threads,
      max_results=max_results,
      enable_edgetpu=enable_edgetpu,
      score_threshold=0.6)
  classifier = ImageClassifier(model, options)

  utils = CommonUtils()
  
  # Variables to calculate FPS
  counter, fps, detection_count = 0, 0, 0
  start_time = time.time()

  # Start capturing video input from the camera
  cap = cv2.VideoCapture(camera_id)
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

  # Continuously capture images from the camera and run inference
  while cap.isOpened():
    success, image = cap.read()
    if not success:
      sys.exit(
          'ERROR: Unable to read from webcam. Please verify your webcam settings.'
      )

    counter += 1
    end_time = time.time()
    seconds = end_time - start_time
    fps = _FPS_AVERAGE_FRAME_COUNT / seconds

    # image = cv2.flip(image, 1)
    # test_image = 'data/Pune-fire-1.jpeg'
    # image = cv2.imread(test_image)
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    categories = classifier.classify(img)
    
    if len(categories) and categories[0].label == 'Fire' and categories[0].score > options.score_threshold :
        category = categories[0]
        fire_img = image
        detection_count += 1
        if seconds >= 5 and detection_count >= 10:
          print('Fire Detectected count: >> ', detection_count)
          class_name = category.label
          score = round(category.score, 2)
          timestr = time.strftime("%Y%m%d-%H%M%S")
          serialNumber = utils.getserial()
          print('serialNumber: >> ', serialNumber)
          result_text = class_name + ' (' + str(score) + ') detected on ' +serialNumber+ ' at: ' +timestr
          text_location = (_LEFT_MARGIN, (1) * _ROW_SIZE)
          cv2.putText(fire_img, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                      _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

          frame = serialNumber+'_frame_'+timestr+'.jpg' 
          cv2.imwrite(os.path.join('./data/frames/' , frame), fire_img)
          detection_count = 0
          start_time = time.time()
        print(categories[0])

    # Stop the program if the ESC key is pressed.
    if cv2.waitKey(1) == 27:
      break
    # cv2.imshow('image_classification', image)

  cap.release()
  cv2.destroyAllWindows()


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model',
      help='Name of image classification model.',
      required=False,
      default='./data/model/efficientnetv2.tflite')
  parser.add_argument(
      '--maxResults',
      help='Max of classification results.',
      required=False,
      default=3)
  parser.add_argument(
      '--numThreads',
      help='Number of CPU threads to run the model.',
      required=False,
      default=4)
  parser.add_argument(
      '--enableEdgeTPU',
      help='Whether to run the model on EdgeTPU.',
      action='store_true',
      required=False,
      default=False)
  parser.add_argument(
      '--cameraId', help='Id of camera.', required=False, default=0)
  parser.add_argument(
      '--frameWidth',
      help='Width of frame to capture from camera.',
      required=False,
      default=640)
  parser.add_argument(
      '--frameHeight',
      help='Height of frame to capture from camera.',
      required=False,
      default=480)
  args = parser.parse_args()

  run(args.model, int(args.maxResults), int(args.numThreads),
      bool(args.enableEdgeTPU), int(args.cameraId), args.frameWidth,
      args.frameHeight)


if __name__ == '__main__':
  main()