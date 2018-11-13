'''
In this example, we will load a RefineDet model and use it to detect objects.
'''

import cv2

import argparse
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import skimage.io as io

# Make sure that caffe is on the python path:
caffe_root = './'
os.chdir(caffe_root)
sys.path.insert(0, os.path.join(caffe_root, 'python'))
import caffe

from google.protobuf import text_format
from caffe.proto import caffe_pb2

from sort import Sort

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu_id', type=int, default=0)
    parser.add_argument('--save_fig', action='store_true')
    parser.add_argument('--video_path')
    args = parser.parse_args()

    video_path = args.video_path

    # gpu preparation
    if args.gpu_id >= 0:
        caffe.set_device(args.gpu_id)
        caffe.set_mode_gpu()

    # load labelmap
    labelmap_file = 'data/VOC0712Plus/labelmap_voc.prototxt'
    file = open(labelmap_file, 'r')
    labelmap = caffe_pb2.LabelMap()
    text_format.Merge(str(file.read()), labelmap)

    # load model
    model_def = 'models/VGGNet/VOC0712Plus/refinedet_vgg16_320x320_ft/deploy.prototxt'
    model_weights = 'models/VGGNet/VOC0712Plus/refinedet_vgg16_320x320_ft/VOC0712Plus_refinedet_vgg16_320x320_ft_final.caffemodel'
    net = caffe.Net(model_def, model_weights, caffe.TEST)

    # image preprocessing
    if '320' in model_def:
        img_resize = 320
    else:
        img_resize = 512
    net.blobs['data'].reshape(1, 3, img_resize, img_resize)
    transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
    transformer.set_transpose('data', (2, 0, 1))
    transformer.set_mean('data', np.array([104, 117, 123]))  # mean pixel
    #transformer.set_raw_scale('data', 255)  # the reference model operates on icons in [0,255] range instead of [0,1]
    #transformer.set_channel_swap('data', (2, 1, 0))  # the reference model has channels in BGR order instead of RGB

    mot_tracker = Sort()

    # im_names = os.listdir('examples/icons')
    num_classes = 32
    colors = plt.cm.hsv(np.linspace(0, 1, num_classes)).tolist()

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():

        ret, image = cap.read()

        transformed_image = transformer.preprocess('data', image)
        net.blobs['data'].data[...] = transformed_image

        detections = net.forward()['detection_out']
        det_label = detections[0, 0, :, 1]
        det_conf = detections[0, 0, :, 2]
        det_xmin = detections[0, 0, :, 3] * image.shape[1]
        det_ymin = detections[0, 0, :, 4] * image.shape[0]
        det_xmax = detections[0, 0, :, 5] * image.shape[1]
        det_ymax = detections[0, 0, :, 6] * image.shape[0]
        result = np.column_stack([det_xmin, det_ymin, det_xmax, det_ymax, det_conf, det_label])

        threshold = 0.4

        result = result[result[:, -2] > threshold]

        trackers = mot_tracker.update(result)

        for d in trackers:
            xmin, ymin, xmax, ymax, obj_id = d.astype(np.int32)

            color = colors[obj_id % 32]
            color = [c * 255 for c in color]

            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color=color, thickness=3)
            display_text = '%s' % (str(obj_id))
            cv2.putText(image, display_text, (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 1, color=color, thickness=1)


        cv2.imshow('RefineDet + SORT', image)
        key = cv2.waitKey(1) & 0xff
        if key == ord('q'):
            break
