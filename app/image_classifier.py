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
"""A wrapper for TensorFlow Lite image classification models."""

import os
import dataclasses
import json
import platform
from typing import List
import logging

import cv2
# from PIL import Image
import numpy as np
from tflite_support import metadata

# pylint: disable=g-import-not-at-top
try:
  # Import TFLite interpreter from tflite_runtime package if it's available.
  from tflite_runtime.interpreter import Interpreter
  from tflite_runtime.interpreter import load_delegate
except ImportError:
  # If not, fallback to use the TFLite interpreter from the full TF package.
  import tensorflow as tf
  Interpreter = tf.lite.Interpreter
  load_delegate = tf.lite.experimental.load_delegate
# pylint: enable=g-import-not-at-top


@dataclasses.dataclass
class ImageClassifierOptions(object):
  """A config to initialize an image classifier."""

  enable_edgetpu: bool = False
  """Enable the model to run on EdgeTPU."""

  label_allow_list: List[str] = None
  """The optional allow list of labels."""

  label_deny_list: List[str] = None
  """The optional deny list of labels."""

  max_results: int = 3
  """The maximum number of top-scored classification results to return."""

  num_threads: int = 1
  """The number of CPU threads to be used."""

  score_threshold: float = 0.80
  """The score threshold of classification results to return."""


@dataclasses.dataclass
class Category(object):
  """A result of a image classification."""
  label: str
  score: float


def edgetpu_lib_name():
  """Returns the library name of EdgeTPU in the current platform."""
  return {
      'Darwin': 'libedgetpu.1.dylib',
      'Linux': 'libedgetpu.so.1',
      'Windows': 'edgetpu.dll',
  }.get(platform.system(), None)


class ImageClassifier(object):
  """A wrapper class for a TFLite image classification model."""

  def __init__(
      self,
      model_path: str,
      options: ImageClassifierOptions = ImageClassifierOptions()
  ) -> None:
    """Initialize a image classification model.

    Args:
        model_path: Path of the TFLite image classification model.
        options: The config to initialize an image classifier. (Optional)

    Raises:
        ValueError: If the TFLite model is invalid.
        OSError: If the current OS isn't supported by EdgeTPU.
    """
    # Load metadata from model.
    # displayer = metadata.MetadataDisplayer.with_model_file(model_path)

    # Save model metadata for preprocessing later.
    # model_metadata = json.loads(displayer.get_metadata_json())
    # process_units = model_metadata['subgraph_metadata'][0][
    #     'input_tensor_metadata'][0]['process_units']
    mean = 127.5
    std = 127.5
    # for option in process_units:
    #   if option['options_type'] == 'NormalizationOptions':
    #     mean = option['options']['mean'][0]
    #     std = option['options']['std'][0]
    self._mean = mean
    self._std = std

    # Load label list from metadata.
    # file_name = displayer.get_packed_associated_file_list()[0]
    # label_map_file = displayer.get_associated_file_buffer(file_name).decode()
    # label_list = list(filter(len, label_map_file.splitlines()))
    # label_list = ['Fire', 'Non Fire']
    label_list = options.label_allow_list
    self._model_path = model_path
    self.setupInterpreter(options, label_list)
  
  def setupInterpreter(self, options, label_list):
    self._options = options
    self._label_list = label_list
      # Initialize TFLite model.
    if options.enable_edgetpu:
      if edgetpu_lib_name() is None:
        raise OSError("The current OS isn't supported by Coral EdgeTPU.")
      interpreter = Interpreter(
          model_path=self._model_path,
          experimental_delegates=[load_delegate(edgetpu_lib_name())],
          num_threads=options.num_threads)
    else:
      interpreter = Interpreter(
          model_path=self._model_path, num_threads=options.num_threads)
    interpreter.allocate_tensors()

    self._input_details = interpreter.get_input_details()
    self._output_details = interpreter.get_output_details()

    self._input_height = interpreter.get_input_details()[0]['shape'][1]
    self._input_width = interpreter.get_input_details()[0]['shape'][2]

    self._is_quantized_input = self._input_details[0]['dtype'] == np.uint8
    self._is_quantized_output = self._output_details[0]['dtype'] == np.uint8

    self._interpreter = interpreter

  def _set_input_tensor(self, image: np.ndarray) -> None:
    """Sets the input tensor."""
    tensor_index = self._input_details[0]['index']
    input_tensor = self._interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image

  def _preprocess(self, image: np.ndarray) -> np.ndarray:
    """Preprocess the input image as required by the TFLite model."""
    # input_tensor = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    input_tensor = cv2.resize(image, (self._input_width, self._input_height))
    # logging.debug('Quantized: ', self._is_quantized_input)
    self._is_quantized_input = True
    if not self._is_quantized_input:
        input_tensor = (np.float32(input_tensor) - self._mean) / self._std
        # input_tensor = np.float32(input_tensor) / 255
        # input_tensor = np.expand_dims(input_tensor, axis=0)
    else:
        input_tensor = np.float32(input_tensor) / 255
    return input_tensor

  def classify(self, image: np.ndarray) -> List[Category]:
    """Classify an input image.

    Args:
        image: A [height, width, 3] RGB image.

    Returns:
        A list of prediction result. Sorted by probability descending.
    """
    image = self._preprocess(image)
    self._set_input_tensor(image)
    # self._interpreter.set_tensor(self._input_details[0]['index'], image)
    self._interpreter.invoke()
    output_tensor = self._interpreter.get_tensor(self._output_details[0]['index'])
    output_tensor = np.squeeze(output_tensor)    
    return self._postprocess(output_tensor)

  def _postprocess(self, output_tensor: np.ndarray) -> List[Category]:
    """Post-process the output tensor into a list of Category objects.

    Args:
        output_tensor: Output tensor of TFLite model.

    Returns:
        A list of prediction result.
    """
    # If the model is quantized (uint8 data), then dequantize the results
    if self._is_quantized_output:
      scale, zero_point = self._output_details[0]['quantization']
      output_tensor = scale * (output_tensor - zero_point)

    # Sort output by probability descending.
    prob_descending = sorted(
        range(len(output_tensor)), key=lambda k: output_tensor[k], reverse=True)
   
    categories = [
        Category(label=self._label_list[idx], score=output_tensor[idx])
        for idx in prob_descending
    ]
    
    # Filter out classification in deny list
    filtered_results = categories
    if self._options.label_deny_list is not None:
      filtered_results = list(
          filter(
              lambda category: category.label not in self._options.
              label_deny_list, filtered_results))

    # Keep only classification in allow list
    if self._options.label_allow_list is not None:
      filtered_results = list(
          filter(
              lambda category: category.label in self._options.label_allow_list,
              filtered_results))
    # Filter out classification in score threshold
    if self._options.score_threshold is not None:
      filtered_results = list(
          filter(
              lambda category: category.score >= (self._options.score_threshold),
              filtered_results))
    
    # Only return maximum of max_results classification.
    if self._options.max_results > 0:
      result_count = min(len(filtered_results), self._options.max_results)
      filtered_results = filtered_results[:result_count]
    
    return filtered_results