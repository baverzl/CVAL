import cv2

import argparse
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import skimage.io as io

# Make sure that caffe is on the python path:
caffe_root = '/home/stanley0/github_repos/caffe-refinedet'
sys.path.insert(0, os.path.join(caffe_root, 'python'))

import caffe

from google.protobuf import text_format
from caffe.proto import caffe_pb2

from models.refinedet_sort.sort import Sort
from utils.lib import struct

class RefineDet():

    def __init__(self, config, gpu_id=0, tracked=False):

        # gpu preparation
        if gpu_id >= 0:
            caffe.set_device(gpu_id)
            caffe.set_mode_gpu()

        model_config = config['MODEL']

        self.model_def = os.path.join(caffe_root, model_config['DEF'])
        self.model_weights = os.path.join(caffe_root, model_config['WEIGHTS'])
        self.labelmap = os.path.join(caffe_root, model_config['LABELMAP'])

        self.is_tracked_results_ready = False
        self.tracked = tracked
        self.mot_tracker = None

        self.mean_pixel = list([104, 117, 223])

        self.num_classes = 32
        self.colors = plt.cm.hsv(np.linspace(0, 1, self.num_classes)).tolist()

        if self.tracked:
            self.mot_tracker = Sort()

        # load labelmap
        with open(self.labelmap, 'r') as f:
            labelmap = caffe_pb2.LabelMap()
            text_format.Merge(str(f.read()), labelmap)

        # load model
        self.net = caffe.Net(self.model_def, self.model_weights, caffe.TEST)

        # image preprocessing
        if '320' in self.model_def:
            img_resize = 320
        else:
            img_resize = 512

        self.net.blobs['data'].reshape(1, 3, img_resize, img_resize)

        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        self.transformer.set_transpose('data', (2, 0, 1))
        self.transformer.set_mean('data', np.array(self.mean_pixel))  # mean pixel

    def getOutputs(self):
        if self.is_tracked_results_ready:
            self.is_tracked_results_ready = False
            return self.tracked_results
        else:
            return self.result

    def feed(self, image):

        transformed_image = self.transformer.preprocess('data', image)
        self.net.blobs['data'].data[...] = transformed_image

        detections = self.net.forward()['detection_out']
        det_label = detections[0, 0, :, 1]
        det_conf = detections[0, 0, :, 2]
        det_xmin = detections[0, 0, :, 3] * image.shape[1]
        det_ymin = detections[0, 0, :, 4] * image.shape[0]
        det_xmax = detections[0, 0, :, 5] * image.shape[1]
        det_ymax = detections[0, 0, :, 6] * image.shape[0]
        self.result = np.column_stack([det_xmin, det_ymin, det_xmax, det_ymax, det_conf, det_label])

        return self

    def filter(self, threshold=0.5):

        self.result = self.result[self.result[:, -2] >= threshold]

        return self

    def track(self):

        if not self.tracked:
            raise RuntimeError("Tracking is not allowed. To enable this, set 'traced' to True")

        trackers = self.mot_tracker.update(self.result)

        self.tracked_results = []
        for d in trackers:
            xmin, ymin, xmax, ymax, track_id = d.astype(np.int32)

            color = self.colors[track_id % self.num_classes]
            # for cv2
            color = [c * 255 for c in color]
            self.tracked_results.append(struct(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, track_id=track_id, color=color))

        self.is_tracked_results_ready = True

        return self

    def update(self, new_drawn_coords):

        np.append(self.result, new_drawn_coords, axis=0)
        return self.track().getOutputs()


if __name__ == '__main__':

    import configparser
    import glob

    basedirname = 'models/refinedet_sort'

    config = configparser.ConfigParser()
    config.read(os.path.join(basedirname, 'model.ini'))

    # Add tracking functionality to RefineDet
    detector = RefineDet(config, tracked=True)

    images = glob.glob(os.path.join(basedirname, 'images/*.jpg'))
    for image in images:
        image = cv2.imread(image)
        dets = detector.feed(image).filter(0.4).track().getOutputs()
        for det in dets:
            print(det.xmin, det.ymin, det.xmax, det.ymax, det.track_id, det.color)