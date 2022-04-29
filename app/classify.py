
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
from handlers.producer import Producer
from utils import CommonUtils

# Visualization parameters
_ROW_SIZE = 20  # pixels
_LEFT_MARGIN = 24  # pixels
_TEXT_COLOR = (0, 0, 255)  # red
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_FPS_AVERAGE_FRAME_COUNT = 10

class Classify(object):

    def __init__(
        self,
        utils: CommonUtils
    ) -> None:
        load_dotenv()
        self.utils = utils
        self.producer = Producer()

    def execute(self) -> None:
        """Continuously run inference on images acquired from the camera.  """
        try:
            print('\n\nIN Classify RUN method: >>>>>> ')
            # Initialize the image classification model
            options = ImageClassifierOptions(
                num_threads=self.utils.cache['CONFIG']['NO_THREADS'],
                max_results=self.utils.cache['CONFIG']['MAX_RESULTS'],
                enable_edgetpu=self.utils.cache['CONFIG']['ENABLE_EDGE_TPU'],
                score_threshold=self.utils.cache['CONFIG']['SCORE_THRESHOLD'])
            classifier = ImageClassifier(self.utils.cache['CONFIG']['LOCAL_MODEL_PATH'], options)

            # Variables to calculate FPS
            counter, fps, detection_count = 0, 0, 0
            start_time = time.time()
            print('CONFIG: >> ', self.utils.cache['CONFIG'])
            camera = self.getCamera()

            # Continuously capture images from the camera and run inference
            while self.utils.cache['UPDATES'] == False and camera.isOpened():
                success, image = camera.read()
                if not success:
                    # sys.exit(
                    #     'ERROR: Unable to read from webcam. Please verify your webcam settings.'
                    # )
                    print('ERROR: Unable to read from webcam. Please verify your webcam settings.')
                    time.sleep(2)
                    self.getCamera()
                    continue

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
                        serialNumber = self.utils.cache['thisDevice']['deviceSerialNo']
                        result_text = class_name + ' (' + str(score) + ') detected on ' +serialNumber+ ' at: ' +timestr
                        text_location = (_LEFT_MARGIN, (1) * _ROW_SIZE)
                        cv2.putText(fire_img, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                                    _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

                        frame = serialNumber+'_frame_'+timestr+'.jpg' 
                        cv2.imwrite(os.path.join(self.utils.cache['CONFIG']['DATA_DIR'] + '/frames/' , frame), fire_img)

                        if self.producer:
                            payload = {
                                'topic': 'detection',
                                'event': {
                                    'type': 'SecurityAlert',
                                    'params': {
                                        'message': result_text
                                    }
                                }
                            }   
                            self.producer.publish('detection', payload)
                        detection_count = 0
                        start_time = time.time()
                    print(categories[0])

                # Stop the program if the ESC key is pressed.
                if cv2.waitKey(1) == 27:
                    # consumer.stop()
                    break
                # cv2.imshow('image_classification', image)
            camera.release()
            cv2.destroyAllWindows()
            camera = None
            classifier = None
            pass
        except KeyboardInterrupt as ki:
            print('KeyboardInterrupt in run detection: >> ', ki)
        except Exception as err:
            print('Exception in run detection: >> ', err)
        # except (RuntimeError, TypeError, NameError) as err:
        #     print('Error in run detection: >> ', err)
            # pass
        finally:
            print('In Finally of Classify.run().....')
            if camera is not None:
                camera.release()
                cv2.destroyAllWindows()
            
    def getCamera(self):
        # Start capturing video input from the camera
        camera = cv2.VideoCapture(self.utils.cache['CONFIG']['CAMERA_ID'])
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.utils.cache['CONFIG']['FRAME_WIDTH'])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.utils.cache['CONFIG']['FRAME_HEIGHT'])
        return camera

   