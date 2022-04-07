#!/usr/bin/env python

#  Author: Gurvinder Singh
#  Date: 2022/04/01
#
# Image Classification.
#
# python classify.py --model_path ./model/mobilenet.tflite
# 
# *************************************** #

"""A very simple Image classifier.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import json
import requests

import cv2
import pandas as pd
import numpy as np
import urllib
from PIL import Image
from io import BytesIO

import dataclasses
# import tensorflow as tf
import tflite_runtime.interpreter as tflite
from PIL import Image

FLAGS = None

@dataclasses.dataclass
class Category(object):
  """A result of a image classification."""
  label: str
  score: float

def url_to_img(url, save_as=''):
    img = Image.open(BytesIO(requests.get(url).content))
    if save_as:
        img.save(save_as)
    #   return np.array(img)
    return img


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def set_config():   
    with open(FLAGS.config_file, 'r') as f:
        MODEL_CONFIG = json.load(f)

    # ensure_dir(FLAGS.model_path)
    global CONFIG
    CONFIG = {
                "MODEL_PATH": FLAGS.model_path,
                "MODEL_CONFIG": MODEL_CONFIG
             }

def classify(img_array):
    class_names = ['Fire', 'Non Fire']
    lite_model_path = CONFIG['MODEL_PATH']
    # interpreter = tf.lite.Interpreter(lite_model_path)
    interpreter = tflite.Interpreter(model_path=lite_model_path)
    interpreter.allocate_tensors()
    input_index = interpreter.get_input_details()[0]["index"]
    output_details = interpreter.get_output_details()[0]
    output_index = output_details["index"]

    interpreter.set_tensor(input_index, img_array)
    interpreter.invoke()

    predictions = np.squeeze(interpreter.get_tensor(output_index))
    print(predictions)
    prob_descending = sorted(
        range(len(predictions)), key=lambda k: predictions[k], reverse=True)
    categories = [
        Category(label=class_names[idx], score=predictions[idx])
        for idx in prob_descending
    ]
    print('Predictions : >> ', categories)
    for c in categories:
        if c.score > 0.5:
            print(
                "\n\nThis image most likely belongs to {} with a {:.2f} percent confidence.\n\n"
                .format(c.label, 100 * c.score)
            )
    
   
    

def execute():
    print('IN execute method of Classify >>>>>>>>> ')
    # img_url = 'https://climate.esa.int/media/images/Fire-CCI-banner_1.2e16d0ba.fill-600x314-c100.format-jpeg.jpg'
    # img_url = 'https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/small-kitchen-1572367025.png'
    # img_url = 'https://images.indianexpress.com/2021/03/Pune-fire-1.jpg'
    # img_url = 'https://i.insider.com/56843d15dd0895dc648b47fd?width=1000&format=jpeg&auto=webp'
    # img_url = 'https://charlestonfire.org/images/public-news/large/news-1501509679.jpg' 
    # img_url = 'https://cf.ltkcdn.net/safety/images/std/116578-232x317r1-Kitchenfireprevention.jpg' # No_Fire
    # img_url ='https://www.kutchina.com/wp-content/uploads/2020/07/straight-line-2-min-600x350.jpg' # No_Fire
    # img_url = 'https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/kitchen-ideas-wall-display-1603743563.jpg'
    img_url = 'https://media.springernature.com/lw725/springer-cms/rest/v1/content/19831396/data/v1' # False Negative
    # img_url = 'https://media-exp1.licdn.com/dms/image/C4D1BAQGrF7AoQDBPXQ/company-background_10000/0/1631550860606?e=2147483647&v=beta&t=0MXoiDfXevwDLrZ8ZHFEXxlcS0T_iyMShpgHlunLMQo'
    # img_url = 'https://www.thespruce.com/thmb/XMuqYgCjvYclSkDrm7ALrwnoXw8=/1777x1333/smart/filters:no_upscale()/fire-pit-backyard-ideas-4177680-hero-4b2d98b9204b4cd4bdb534a5a9b106f4.jpg' # False Negative
    # img_path = tflite.keras.utils.get_file('test_img', origin=img_url, cache_dir='data')
    # img = url_to_img(img_url)
    # cv2.imshow('lalala', img)
    # if cv2.waitKey() & 0xff == 27: quit()
    # image = cv2.imread(img_url)
    # print(image)
    img_size = CONFIG['MODEL_CONFIG']['IMAGE_SIZE']
    img = Image.open(BytesIO(requests.get(img_url).content))
    image = img.convert('RGB').resize((img_size, img_size), Image.ANTIALIAS)
    img_array = np.float32(image) / 255
    img_array = np.expand_dims(img_array, axis=0)
    classify(img_array)
    # os.remove(img_path)

def main():
    set_config()
    execute()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # environment variable when name starts with $
  parser.add_argument('--model_path', type=str, default='model/model.tflite', help='AI Model Path')
  parser.add_argument('--config_file', type=str, default='model/model_config.json', help='Model Configuration file name')
  parser.add_argument('--action', type=str, default='classify', help='ML Framework to use')

  FLAGS, unparsed = parser.parse_known_args()
  print("Start model training")
#   tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
  main()
