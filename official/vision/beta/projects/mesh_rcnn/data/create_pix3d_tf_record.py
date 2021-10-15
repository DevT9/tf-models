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
# Author: Jacob Zietek

# https://github.com/PurdueDualityLab/tf-models/blob/master/official/vision/beta/data/create_coco_tf_record.py reference

r"""Convert raw Pix3D dataset to TFRecord format.
This scripts follows the label map decoder format and supports detection
boxes, instance masks and captions.
Example usage:
    python create_pix3d_tf_record.py --logtostderr \
      --pix3d_dir="${TRAIN_IMAGE_DIR}" \
      --output_file_prefix="${OUTPUT_DIR/FILE_PREFIX}" \
      --num_shards=100
"""

import collections
import json
import logging
import os
import json

from absl import app  # pylint:disable=unused-import
from absl import flags
import numpy as np

import tensorflow as tf

import multiprocessing as mp
from official.vision.beta.data import tfrecord_lib
from research.object_detection.utils import dataset_util
from official.vision.beta.data.tfrecord_lib import convert_to_feature

flags.DEFINE_multi_string('pix3d_dir', '', 'Directory containing Pix3d.')
flags.DEFINE_string('output_file_prefix', '/tmp/train', 'Path to output file')
flags.DEFINE_integer('num_shards', 32, 'Number of shards for output file.')

FLAGS = flags.FLAGS

logger = tf.get_logger()
logger.setLevel(logging.INFO)


def create_tf_example(image):
    """Converts image and annotations to a tf.Example proto.
    Args:
      image: dict with keys: [img, category, img_size, 2d_keypoints, mask, img_source, model,
                              model_raw, model_source, 3d_keypoints, voxel, rot_mat, trans_mat,
                              focal_length, cam_position, inplane_rotation, truncated, occluded,
                              slightly_occluded, bbox]
    Returns:
      example: The converted tf.Example
      num_annotations_skipped: Number of (invalid) annotations that were ignored.
    Raises:
      ValueError: if the image is not able to be found. This indicates the file structure 
      of the Pix3D folder is incorrect.
    """

    

    with tf.io.gfile.GFile(os.join(image["pix3d_dir"], image["img"]), 'rb') as fid:
      encoded_jpg = fid.read()

    img_width, img_height = image["img_size"]
    img_filename = image["img"]
    img_category = image["category"]
    
    feature_dict = {"img/height": dataset_util.int64_feature(img_height),
                    "img/width": dataset_util.int64_feature(img_width),
                    "img/category": dataset_util.bytes_feature(img_category),
                    "img/filename": dataset_util.bytes_feature(img_filename),
                    "img/encoded": dataset_util.bytes_feature(encoded_jpg)}
  
    example = tf.train.Example(features=tf.train.Features(feature=feature_dict))

    return example, 0


def generate_annotations(images, pix3d_dir):
    """Generator for Pix3D annotations."""
    for image in images:
        yield {"img": image["img"], "category": image["category"], "img_size": image["img_size"], "2d_keypoints": image["2d_keypoints"],
               "mask": image["mask"], "img_source": image["img_source"], "model": image["model"], "model_raw": image["model_raw"],
               "model_source": image["model_source"], "3d_keypoints": image["3d_keypoints"], "voxel": image["voxel"], "rot_mat": image["rot_mat"],
               "trans_mat": image["trans_mat"], "focal_length": image["focal_length"], "cam_position": image["cam_position"],
               "inplane_rotation": image["inplane_rotation"], "truncated": image["truncated"], "occluded": image["occluded"],
               "slightly_ocluded": image["slightly_occluded"], "bbox": image["bbox"], "pix3d_dir": pix3d_dir}


def _create_tf_record_from_pix3d_dir(pix3d_dir,
                                     output_path,
                                     num_shards):
    """Loads Pix3D json files and converts to tf.Record format.
    Args:
      images_info_file: pix3d_dir download directory
      output_path: Path to output tf.Record file.
      num_shards: Number of output files to create.
    """

    logging.info('writing to output path: %s', output_path)

    images = json.load(open(os.join(pix3d_dir, "pix3d.json")))

    pix3d_annotations_iter = generate_annotations(
        images=images, pix3d_dir=pix3d_dir)

    num_skipped = tfrecord_lib.write_tf_record_dataset(
        output_path, pix3d_annotations_iter, create_tf_example, num_shards)

    logging.info('Finished writing, skipped %d annotations.', num_skipped)


def main(_):
    assert FLAGS.pix3d_dir, '`pix3d_dir` missing.'

    directory = os.path.dirname(FLAGS.output_file_prefix)
    if not tf.io.gfile.isdir(directory):
        tf.io.gfile.makedirs(directory)


if __name__ == '__main__':
    app.run(main)
