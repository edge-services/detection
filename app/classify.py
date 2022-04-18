# Copyright 2022. All Rights Reserved.
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
from dotenv import load_dotenv

# import numpy as np
import cv2
# from PIL import Image
from image_classifier import ImageClassifier
from image_classifier import ImageClassifierOptions
from utils import CommonUtils
from handlers.cloud_sync import CloudSync
from handlers.producer import Producer
from handlers.consumer import Consumer

# Visualization parameters
_ROW_SIZE = 20  # pixels
_LEFT_MARGIN = 24  # pixels
_TEXT_COLOR = (0, 0, 255)  # red
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_FPS_AVERAGE_FRAME_COUNT = 10

utils = CommonUtils()

def init():
    load_dotenv()
    DATA_DIR, MODEL_DIR = checkDirectories()
    global CONFIG
    CONFIG = {
        'ACTION': 'RUN',
        'DATA_DIR': DATA_DIR,
        'MODEL_DIR': MODEL_DIR,
        'LOCAL_MODEL_PATH':  os.path.join(MODEL_DIR, 'model.tflite')
    }
    global cloudAPI
    global producer
    global consumer
    cloudAPI = CloudSync(CONFIG)  
    if utils.is_connected:        
        # cloudAPI.syncWithCloud()
        cloudAPI.syncWithLocal()      
    else:
        print('Load data locally >>>')
        cloudAPI.syncWithLocal()
    
    consumer = Consumer(cloudAPI._thisDevice, restart)
    consumer.start()
    producer = Producer(cloudAPI._thisDevice)

def checkDirectories():
    DATA_DIR = os.environ.get("DATA_DIR")
    MODEL_DIR = os.path.join(DATA_DIR, 'model')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    return DATA_DIR, MODEL_DIR

def stopDetection():
    CONFIG['ACTION'] = 'STOP'

def restart():
    print('\n\n<<<<<<<<< Start Detection >>>>>>>> \n\n')
    stopDetection()
    if utils.is_connected:        
        # cloudAPI.syncWithCloud()
        cloudAPI.syncWithLocal()      
    else:
        print('Load data locally >>>')
        cloudAPI.syncWithLocal()
    time.sleep(5)
    CONFIG['ACTION'] = 'RUN'
    run()


def run() -> None:
    """Continuously run inference on images acquired from the camera.  """
    try:
        # Initialize the image classification model
        options = ImageClassifierOptions(
            num_threads=CONFIG['NO_THREADS'],
            max_results=CONFIG['MAX_RESULTS'],
            enable_edgetpu=CONFIG['ENABLE_EDGE_TPU'],
            score_threshold=CONFIG['SCORE_THRESHOLD'])
        classifier = ImageClassifier(CONFIG['LOCAL_MODEL_PATH'], options)

        # Variables to calculate FPS
        counter, fps, detection_count = 0, 0, 0
        start_time = time.time()

        # Start capturing video input from the camera
        cap = cv2.VideoCapture(CONFIG['CAMERA_ID'])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG['FRAME_WIDTH'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG['FRAME_HEIGHT'])

        # Continuously capture images from the camera and run inference
        while CONFIG['ACTION'] == 'RUN' and cap.isOpened():
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
                if seconds >= 10 and detection_count >= 20:
                    print('Fire Detectected count: >> ', detection_count)
                    class_name = category.label
                    score = round(category.score, 2)
                    timestr = time.strftime("%Y%m%d-%H%M%S")
                    serialNumber = utils.getserial()
                    # print('serialNumber: >> ', serialNumber)
                    result_text = class_name + ' (' + str(score) + ') detected on ' +serialNumber+ ' at: ' +timestr
                    text_location = (_LEFT_MARGIN, (1) * _ROW_SIZE)
                    cv2.putText(fire_img, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                                _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

                    frame = serialNumber+'_frame_'+timestr+'.jpg' 
                    cv2.imwrite(os.path.join(CONFIG['DATA_DIR'] + '/frames/' , frame), fire_img)

                    if cloudAPI:
                        payload = {
                            'topic': 'detection',
                            'event': {
                                'type': 'SecurityAlert',
                                'params': {
                                    'message': result_text
                                }
                            }
                        }
                        
                    producer.publish('detection', payload)
                    detection_count = 0
                    start_time = time.time()
                print(categories[0])

            # Stop the program if the ESC key is pressed.
            if cv2.waitKey(1) == 27:
                consumer.stop()
                break
            # cv2.imshow('image_classification', image)

        cap.release()
        cv2.destroyAllWindows()
    except KeyboardInterrupt as ki:
         print('KeyboardInterrupt in run detection: >> ', ki)
    except Exception as err:
        print('Exception in run detection: >> ', err)
    finally:
        # consumer.stop()
        print('In Finally of Classify.run().....')


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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

  init()

  CONFIG['MAX_RESULTS'] = args.maxResults
  CONFIG['NO_THREADS'] = args.numThreads
  CONFIG['ENABLE_EDGE_TPU'] = args.enableEdgeTPU
  CONFIG['CAMERA_ID'] = args.cameraId
  CONFIG['FRAME_WIDTH'] = args.frameWidth
  CONFIG['FRAME_HEIGHT'] = args.frameHeight
  CONFIG['SCORE_THRESHOLD'] = 0.8
  
  CONFIG['ACTION'] = 'RUN'
  run()


if __name__ == '__main__':
  main()