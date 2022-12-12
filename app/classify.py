
import os
import argparse
from nis import cat
import sys
import time
import logging
from dotenv import load_dotenv

# import numpy as np
import cv2
# from PIL import Image
from image_classifier import ImageClassifier
from image_classifier import ImageClassifierOptions
from handlers.producer import Producer
from handlers.cos import COS
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
        self.producer = Producer(utils)
        self.cos = COS(utils)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.utils.cache['CONFIG']['LOGLEVEL'])
        if self.cos.isCOSAvailable() == True:
            print('COS IS AVAILABLE')

    def execute(self) -> None:
        """Continuously run inference on images acquired from the camera.  """
        try:
            self.logger.info('\n\nIN Classify RUN method: >>>>>> ')
            self.logger.info(self.utils.cache['CONFIG'])

            # Initialize the image classification model
            options = ImageClassifierOptions(
                label_allow_list=['Fire', 'Non Fire'],
                num_threads=self.utils.cache['CONFIG']['NO_THREADS'],
                max_results=self.utils.cache['CONFIG']['MAX_RESULTS'],
                enable_edgetpu=self.utils.cache['CONFIG']['ENABLE_EDGE_TPU'],
                score_threshold=self.utils.cache['CONFIG']['SCORE_THRESHOLD'])
            
            labelToDetect = 'Fire'
            publishType = 'x-in-y'
            timePeriod = 10
            detectionCount = 20
            event = None

            rules = self.utils.cache['rules']
            publish_threshold = self.utils.cache['CONFIG']['SCORE_THRESHOLD']
            if rules and len(rules) > 0:
                condition = rules[0]['condition']
                # self.logger.info('\n\nCondition: >> %s\n', condition)
                if condition and condition['type'] == 'all':
                    children = condition['children']
                    for child in children:
                        if child['type'] == 'fact':
                            if child['fact']['path'] == '$.class':
                                labelToDetect = child['fact']['value'] 
                            if child['fact']['path'] == '$.confidence' and child['fact']['value'] and (type(child['fact']['value']) == int or float):
                                if child['fact']['value'] > 0:
                                    publish_threshold = child['fact']['value'] / 100
                                else:
                                    publish_threshold = child['fact']['value']

                
                event = rules[0]['event']
                self.logger.info('Event: >> %s\n', event)
                if event and event['params'] and event['params']['publish']:
                    publishType = event['params']['publish']['when']
                    if publishType == 'x-in-y':
                        timePeriod = event['params']['publish']['timePeriod']
                        detectionCount = event['params']['publish']['count']
            
            self.logger.info('LabelToDetect: >> %s', labelToDetect)
            self.logger.info('detection_threshold: >> %s', options.score_threshold)
            self.logger.info('publish_threshold: >> %s\n', publish_threshold)

            classifier = ImageClassifier(self.utils.cache['CONFIG']['LOCAL_MODEL_PATH'], options)

            # Variables to calculate FPS
            counter, fps, detection_count = 0, 0, 0
            start_time = time.time()
            # self.logger.info('CONFIG: >> ', self.utils.cache['CONFIG'])
            camera = self.getCamera()

            # Continuously capture images from the camera and run inference
            while self.utils.cache['UPDATES'] == False and camera.isOpened():
                success, image = camera.read()
                # time.sleep(0.5)
                if not success:
                    # sys.exit(
                    #     'ERROR: Unable to read from webcam. Please verify your webcam settings.'
                    # )
                    self.logger.info('ERROR: Unable to read from webcam. Please verify your webcam settings.')
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
                if len(categories) and categories[0].label == labelToDetect and categories[0].score > publish_threshold :
                    self.logger.info(categories)
                    # self.logger.info('%s is Detectected %d times in %d seconds: >> %d \n', labelToDetect, detection_count, seconds)
                    category = categories[0]
                    fire_img = image
                    detection_count += 1
                    if publishType == 'every-time' or (publishType == 'x-in-y' and seconds >= timePeriod and detection_count >= detectionCount):
                        self.logger.info('%s is Detectected %d times in %d seconds !!\n', labelToDetect, detection_count, seconds)
                        class_name = category.label
                        score = round(category.score, 2)
                        timestr = time.strftime("%Y%m%d-%H%M%S")
                        serialNumber = self.utils.cache['thisDevice']['deviceSerialNo']
                        result_text = 'Device Serial No: {0}\nDetected: {1} ({2: .2%} confidence ) \nDetection Count: {3}\nSeconds Count: {4: .2f}\nDate & time: {5}'.format(serialNumber, class_name, score, detection_count, seconds, timestr)
                        text_location = (_LEFT_MARGIN, (1) * _ROW_SIZE)
                        cv2.putText(fire_img, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                                    _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

                        frame = serialNumber+'_frame_'+timestr+'.jpg' 
                        frame_path = self.utils.cache['CONFIG']['DATA_DIR'] + '/frames/'+ frame
                        cv2.imwrite(os.path.join(self.utils.cache['CONFIG']['DATA_DIR'] + '/frames/' , frame), fire_img)
                        
                        if self.cos.isCOSAvailable() == True:
                            result_text = self.uploadFrameToCOS(result_text, frame, frame_path)

                        thisDevice = self.utils.cache['thisDevice']
                        self.logger.info('EVENT: >>> %s', event)
                        event['params']['message'] = event['params']['message'] + '\n\n' +result_text
                        event['params']['metadata'] = {
                                            'deviceId': thisDevice['id']                                            
                                        }
                        
                        if 'location' in thisDevice:
                            event['params']['metadata']['location'] = thisDevice['location']


                        topic = 'detection'
                        if 'topic' in event['params']:
                            topic = event['params']['topic']

                        if self.producer:
                            payload = {
                                'topic': topic,
                                'event': event
                            }  
                            self.producer.publish(topic, payload)
                        detection_count = 0
                        start_time = time.time()
                    self.logger.info(categories[0])

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
        # except KeyboardInterrupt as ki:
        #     self.logger.info('KeyboardInterrupt in run detection: >> ', ki)
        except Exception as err:
            self.logger.error('Exception in run detection: >> %s', err)
        finally:
            self.logger.info('In Finally of Classify.run().....')
            if camera is not None:
                camera.release()
                cv2.destroyAllWindows()
            
    def getCamera(self):
        # Start capturing video input from the camera
        camera = cv2.VideoCapture(self.utils.cache['CONFIG']['CAMERA_ID'])
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.utils.cache['CONFIG']['FRAME_WIDTH'])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.utils.cache['CONFIG']['FRAME_HEIGHT'])
        return camera

    def uploadFrameToCOS(self, result_text, frame, frame_path):
        uploaded_frame_url = self.cos.upload_file(self.utils.cache['CONFIG']['COS_BUCKET'], frame, frame_path)
        if uploaded_frame_url == False:
            print('Frame Not Upoaded Successffuly')
        else:
            print('Frame Upoaded Successffuly')
            result_text = result_text + '\n\n' +uploaded_frame_url
            os.remove(frame_path)
        return result_text

   