# coding: utf-8

from __future__ import division, print_function

import random
import numpy as np
import cv2


def get_color_table(class_num, seed=2):
    random.seed(seed)
    color_table = {}
    for i in range(class_num):
        color_table[i] = [random.randint(0, 255) for _ in range(3)]
    return color_table


def plot_one_box(img, coord, label=None, color=None, line_thickness=None):
    '''
    coord: [x_min, y_min, x_max, y_max] format coordinates.
    img: img to plot on.
    label: str. The label name.
    color: int. color index.
    line_thickness: int. rectangle line thickness.
    '''
    tl = line_thickness or int(round(0.002 * max(img.shape[0:2])))  # line thickness

    c1, c2 = (int(coord[0]), int(coord[1])), (int(coord[2]), int(coord[3]))
    print('label:',label)
    if str(label).__contains__('safe'):
        cv2.rectangle(img, c1, c2, (0, 255, 0), thickness=(tl*2))
    elif str(label).__contains__('warning'):
        cv2.rectangle(img, c1, c2, (0,0, 255), thickness=(tl*2))
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=float(tl) / 2.5, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        # cv2.rectangle(img=img, pt1=c1,pt2=c2, color=[255,0,0])  # filled
        if str(label).__contains__('safe'):
            cv2.rectangle(img, c1, c2, (0, 255, 0), -1)  # filled 绿色
            cv2.putText(img, label, (c1[0], c1[1] - 2), 0, float(tl) / 2.5, color=[255,50, 55], thickness=tf,
                        lineType=cv2.LINE_AA)
        elif str(label).__contains__('warning'):
            cv2.rectangle(img, c1, c2, (0,0, 255), -1)  # filled 红色
            cv2.putText(img, label, (c1[0], c1[1] - 2), 0, float(tl) / 2.5, color=[255,255, 255], thickness=tf,
                        lineType=cv2.LINE_AA)

