# coding: utf-8

from __future__ import division, print_function

import tensorflow as tf
import numpy as np
import argparse
import cv2
import time

from helmet_recognize.utils.misc_utils import parse_anchors, read_class_names
from helmet_recognize.utils.nms_utils import gpu_nms
from helmet_recognize.utils.plot_utils import get_color_table, plot_one_box
from helmet_recognize.utils.data_aug import letterbox_resize

from helmet_recognize.model_config.model import yolov3

parser = argparse.ArgumentParser(description="YOLO-V3 video test procedure.")
parser.add_argument("--input_video", type=str, default="./test_files/video.mp4",
                    help="The path of the input video.")
parser.add_argument("--anchor_path", type=str, default="./train_data/yolo_anchors.txt",
                    help="The path of the anchor txt file.")
parser.add_argument("--new_size", nargs='*', type=int, default=[416, 416],
                    help="Resize the input image with `new_size`, size format: [width, height]")
parser.add_argument("--letterbox_resize", type=lambda x: (str(x).lower() == 'true'), default=True,
                    help="Whether to use the letterbox resize.")
parser.add_argument("--class_name_path", type=str, default="./train_data/coco.names",
                    help="The path of the class names.")
# parser.add_argument("--restore_path", type=str, default="./train_data/darknet_weights/yolov3.ckpt",
#                     help="The path of the weights to restore.")
parser.add_argument("--restore_path", type=str,
                    default="./checkpoint/best_model_Epoch_200_step_34370_mAP_0.8121_loss_9.4284_lr_1e-05",
                    help="The path of the weights to restore.")
parser.add_argument("--save_video", type=lambda x: (str(x).lower() == 'true'), default=True,
                    help="Whether to save the video detection results.")
args = parser.parse_args()

args.anchors = parse_anchors(args.anchor_path)
args.classes = read_class_names(args.class_name_path)
args.num_class = len(args.classes)

color_table = get_color_table(args.num_class)

# VideoCapture()中参数是0，表示打开笔记本的内置摄像头，参数是视频文件路径则打开视频
vid = cv2.VideoCapture(args.input_video)
# vid = cv2.VideoCapture(0)
# get(7)视频文件中的帧数https://blog.csdn.net/qq_36387683/article/details/83652752
video_frame_cnt = int(vid.get(7))
video_width = int(vid.get(3))
video_height = int(vid.get(4))
video_fps = int(vid.get(5))  # get(5)帧速率

if args.save_video:
    # MPEG-4编码,VideoWriter_fourcc为视频编解码器
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    # 创建视频流写入对象
    videoWriter = cv2.VideoWriter(
        './result/video_result.mp4', fourcc, video_fps, (video_width, video_height))

with tf.Session() as sess:
    input_data = tf.placeholder(tf.float32, [1, args.new_size[1], args.new_size[0], 3], name='input_data')
    yolo_model = yolov3(args.num_class, args.anchors)
    with tf.variable_scope('yolov3'):
        pred_feature_maps = yolo_model.forward(input_data, False)
    pred_boxes, pred_confs, pred_probs = yolo_model.predict(pred_feature_maps)

    pred_scores = pred_confs * pred_probs

    boxes, scores, labels = gpu_nms(pred_boxes, pred_scores, args.num_class, max_boxes=200, score_thresh=0.3,
                                    nms_thresh=0.45)

    saver = tf.train.Saver()  # 实例化一个Saver对象
    saver.restore(sess, args.restore_path)  # 重载模型参数，用于训练或者测试数据

    # 对视频文件中每一帧进行处理
    for i in range(video_frame_cnt):
        # vid.read()按帧读取视频，ret是布尔值，如果读取帧是正确的则返回True，如果文件读取到结尾，
        # 它的返回值就为False。img_ori就是每一帧的图像，是个三维矩阵.
        ret, img_ori = vid.read()
        # resize调整大小
        if ret:
            if args.letterbox_resize:
                img, resize_ratio, dw, dh = letterbox_resize(img_ori, args.new_size[0], args.new_size[1])
            else:
                height_ori, width_ori = img_ori.shape[:2]
                img = cv2.resize(img_ori, tuple(args.new_size))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.asarray(img, np.float32)
            img = img[np.newaxis, :] / 255.

            start_time = time.time()
            if i % 3 == 0:
                boxes_, scores_, labels_ = sess.run(
                    [boxes, scores, labels], feed_dict={input_data: img})
            end_time = time.time()

            # rescale the coordinates to the original image
            if i % 3 == 0:
                if args.letterbox_resize:
                    boxes_[:, [0, 2]] = (boxes_[:, [0, 2]] - dw) / resize_ratio
                    boxes_[:, [1, 3]] = (boxes_[:, [1, 3]] - dh) / resize_ratio
                else:
                    boxes_[:, [0, 2]] *= (width_ori / float(args.new_size[0]))
                    boxes_[:, [1, 3]] *= (height_ori / float(args.new_size[1]))

            for i in range(len(boxes_)):
                x0, y0, x1, y1 = boxes_[i]
                plot_one_box(img_ori, [x0, y0, x1, y1],
                             label=args.classes[labels_[i]] + ', {:.2f}%'.format(scores_[i] * 100),
                             color=color_table[labels_[i]])
            # 显示文本（参数有图像，文字内容， 坐标 ，字体，大小，颜色，字体厚度）
            cv2.putText(img_ori, '{:.2f}ms'.format((end_time - start_time) * 1000), (40, 40), 0,
                        fontScale=1, color=(0, 255, 0), thickness=2)
            # 显示图片
            cv2.imshow('image', img_ori)
            if args.save_video:
                videoWriter.write(img_ori)  # 向视频文件写入一帧

            # waitKey（）方法本身表示等待键盘输入，参数是1，表示延时1ms切换到下一帧图像，对于视频而言；
            # 参数为0,如cv2.waitKey(0)只显示当前帧图像,相当于视频暂停;
            # 参数过大如cv2.waitKey(1000),会因为延时过久而卡顿感觉到卡顿.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    vid.release()  # 调用release()释放摄像头，调用destroyAllWindows()关闭所有图像窗口
    if args.save_video:
        videoWriter.release()
