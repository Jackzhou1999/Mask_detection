from __future__ import division
import os
import math
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np

from PIL import Image, ImageDraw, ImageFont

class DecodeBox(nn.Module):
    """
    将网络的输出解码,
    输入的array size=(batchsize, anchorboxnum*(5+classnum), featureimg_h, featureimg_w)
    输出的size = (batchsize, anchorboxnum*featureimg_h*featureimg_w, 4 + cofnum + classnum)

    其中：
    anchorboxnum = 3
    classnum = 2
    featureimg_h, featureimg_w = (13, 13) or (26, 26) or (52, 52)
    box参数形式为[中心点x, 中心点y, 宽, 高)
    1. 在特征图中中心点, 宽高计算
        中心点 = 左上角坐标 + sigmoid(net_output[0:2])
        w = anchor_w * exp(net_output[2])
        h = anchor_h * exp(net_output[3])
    2. 转换到416x416尺寸下的中心点, 宽, 高
    """
    def __init__(self, anchors, num_classes, img_size):
        super(DecodeBox, self).__init__()
        self.anchors = anchors
        self.num_anchors = len(anchors)
        self.num_classes = num_classes
        self.bbox_attrs = 5 + num_classes
        self.img_size = img_size

    def forward(self, input):
        batch_size = input.size(0)
        input_height = input.size(2)
        input_width = input.size(3)

        # 计算步长
        stride_h = self.img_size[1] / input_height
        stride_w = self.img_size[0] / input_width
        # 归一到特征层上
        scaled_anchors = [(anchor_width / stride_w, anchor_height / stride_h) for anchor_width, anchor_height in self.anchors]
        # 对预测结果进行resize
        prediction = input.view(batch_size, self.num_anchors,
                                self.bbox_attrs, input_height, input_width).permute(0, 1, 3, 4, 2).contiguous()

        # 先验框的中心位置的调整参数
        x = torch.sigmoid(prediction[..., 0])
        y = torch.sigmoid(prediction[..., 1])
        # 先验框的宽高调整参数
        w = prediction[..., 2]  # Width
        h = prediction[..., 3]  # Height

        # 获得置信度，是否有物体
        conf = torch.sigmoid(prediction[..., 4])
        # 种类置信度
        pred_cls = torch.sigmoid(prediction[..., 5:])  # Cls pred.

        FloatTensor = torch.cuda.FloatTensor if x.is_cuda else torch.FloatTensor
        LongTensor = torch.cuda.LongTensor if x.is_cuda else torch.LongTensor

        # 生成网格，先验框中心，网格左上角
        grid_x = torch.linspace(0, input_width - 1, input_width).repeat(input_width, 1).repeat(
            batch_size * self.num_anchors, 1, 1).view(x.shape).type(FloatTensor)
        grid_y = torch.linspace(0, input_height - 1, input_height).repeat(input_height, 1).t().repeat(
            batch_size * self.num_anchors, 1, 1).view(y.shape).type(FloatTensor)

        # 生成先验框的宽高
        anchor_w = FloatTensor(scaled_anchors).index_select(1, LongTensor([0]))
        anchor_h = FloatTensor(scaled_anchors).index_select(1, LongTensor([1]))
        anchor_w = anchor_w.repeat(batch_size, 1).repeat(1, 1, input_height * input_width).view(w.shape)
        anchor_h = anchor_h.repeat(batch_size, 1).repeat(1, 1, input_height * input_width).view(h.shape)

        # 计算调整后的先验框中心与宽高
        pred_boxes = FloatTensor(prediction[..., :4].shape)
        pred_boxes[..., 0] = x.data + grid_x
        pred_boxes[..., 1] = y.data + grid_y
        pred_boxes[..., 2] = torch.exp(w.data) * anchor_w
        pred_boxes[..., 3] = torch.exp(h.data) * anchor_h

        # 用于将输出调整为相对于416x416的大小
        _scale = torch.Tensor([stride_w, stride_h] * 2).type(FloatTensor)
        # print(_scale)
        # print(pred_boxes.view(batch_size, -1, 4).shape)
        # print(conf.view(batch_size, -1, 1).shape)
        # print(pred_cls.view(batch_size, -1, self.num_classes).shape)
        output = torch.cat((pred_boxes.view(batch_size, -1, 4) * _scale,
                            conf.view(batch_size, -1, 1), pred_cls.view(batch_size, -1, self.num_classes)), -1)
        print("decoder:", output.shape)
        return output.data
        
def letterbox_image(image, size):
    '''
    将图片resize 到416, 416,
    方法：
    设H>W：
    new_H=416
    new_W=416H/W
    然后短边加入灰框
    :param image: 原尺寸图片
    :param size: （416, 416）
    :return: （416, 416）图片
    '''
    iw, ih = image.size
    w, h = size
    scale = min(w/iw, h/ih)
    nw = int(iw*scale)
    nh = int(ih*scale)
    # print("new shape:", nw, nh)
    image = image.resize((nw, nh), Image.BICUBIC)
    new_image = Image.new('RGB', size, (128, 128, 128))
    new_image.paste(image, ((w-nw)//2, (h-nh)//2))
    # import matplotlib.pyplot as plt
    # plt.figure()
    # plt.imshow(new_image)
    # plt.show()
    return new_image

def yolo_correct_boxes(top, left, bottom, right, input_shape, image_shape):
    '''
    将相对于特征图大小的box结果转换到相对与原图的尺寸
    :param top:
    :param left:
    :param bottom:
    :param right:
    :param input_shape: （416, 416）
    :param image_shape: （H, W）
    :return: 相对与原图的尺寸的box的[左上角x, 左上角y, 左下角x, 左下角y]
    '''
    new_shape = image_shape*np.min(input_shape/image_shape)
    print("new shape:", new_shape, image_shape)
    # 计算灰色带相对与特征图的大小（0—1）
    offset = (input_shape-new_shape)/2./input_shape
    scale = input_shape/new_shape

    box_yx = np.concatenate(((top+bottom)/2,  (left+right)/2), axis=-1)/input_shape
    box_hw = np.concatenate((bottom-top, right-left), axis=-1)/input_shape

    box_yx = (box_yx - offset) * scale
    box_hw *= scale

    box_mins = box_yx - (box_hw / 2.)
    box_maxes = box_yx + (box_hw / 2.)
    boxes = np.concatenate([
        box_mins[:, 0:1],
        box_mins[:, 1:2],
        box_maxes[:, 0:1],
        box_maxes[:, 1:2]
    ], axis=-1)
    # tmp = max(image_shape[0], image_shape[1])
    # S = np.array([tmp for i in range(4)]).reshape(1, 4)
    # boxes *= S
    boxes *= np.concatenate([image_shape, image_shape], axis=-1)
    print(boxes)
    return boxes

def bbox_iou(box1, box2, x1y1x2y2=True):
    """
        计算IOU
        1. x1y1x2y2 = false时：
            输入box = [中心点x, 中心点y, 宽, 高]
            所以要计算box的左上角和右下角坐标
        2. x1y1x2y2 = true时：
            输入box = [左上角x, 左上角y, 左下角x, 左下角y]
        计算方法：
        iou = (min(b1_x2, b2_x2) - max(b1_x1, b2_x1)) / ((b1_x2 - b1_x1)*(b1_y2 - b1_y1) + (b2_x2 - b2_x1)*(b2_y2 - b2_y1) - 分子)
    """
    if not x1y1x2y2:
        b1_x1, b1_x2 = box1[:, 0] - box1[:, 2] / 2, box1[:, 0] + box1[:, 2] / 2
        b1_y1, b1_y2 = box1[:, 1] - box1[:, 3] / 2, box1[:, 1] + box1[:, 3] / 2
        b2_x1, b2_x2 = box2[:, 0] - box2[:, 2] / 2, box2[:, 0] + box2[:, 2] / 2
        b2_y1, b2_y2 = box2[:, 1] - box2[:, 3] / 2, box2[:, 1] + box2[:, 3] / 2
    else:
        b1_x1, b1_y1, b1_x2, b1_y2 = box1[:, 0], box1[:, 1], box1[:, 2], box1[:, 3]
        b2_x1, b2_y1, b2_x2, b2_y2 = box2[:, 0], box2[:, 1], box2[:, 2], box2[:, 3]

    inter_rect_x1 = torch.max(b1_x1, b2_x1)
    inter_rect_y1 = torch.max(b1_y1, b2_y1)
    inter_rect_x2 = torch.min(b1_x2, b2_x2)
    inter_rect_y2 = torch.min(b1_y2, b2_y2)

    inter_area = torch.clamp(inter_rect_x2 - inter_rect_x1 + 1, min=0) * \
                 torch.clamp(inter_rect_y2 - inter_rect_y1 + 1, min=0)
                 
    b1_area = (b1_x2 - b1_x1 + 1) * (b1_y2 - b1_y1 + 1)
    b2_area = (b2_x2 - b2_x1 + 1) * (b2_y2 - b2_y1 + 1)

    iou = inter_area / (b1_area + b2_area - inter_area + 1e-16)

    return iou


def non_max_suppression(prediction, num_classes, conf_thres=0.5, nms_thres=0.4):
    """
    计算非极大值抑制

    :param prediction:
    :param num_classes:
    :param conf_thres:
    :param nms_thres:
    :return:
    """
    # 求左上角和右下角
    # [中心点x, 中心点y, 宽, 高] ==> [左上角x, 左上角y, 左下角x, 左下角y]
    box_corner = prediction.new(prediction.shape)
    box_corner[:, :, 0] = prediction[:, :, 0] - prediction[:, :, 2] / 2
    box_corner[:, :, 1] = prediction[:, :, 1] - prediction[:, :, 3] / 2
    box_corner[:, :, 2] = prediction[:, :, 0] + prediction[:, :, 2] / 2
    box_corner[:, :, 3] = prediction[:, :, 1] + prediction[:, :, 3] / 2
    prediction[:, :, :4] = box_corner[:, :, :4]

    # 默认输出为None
    output = [None for _ in range(len(prediction))]
    for image_i, image_pred in enumerate(prediction):
        # 利用置信度进行第一轮筛选
        print(type(image_pred), image_pred.shape)
        conf_mask = (image_pred[:, 4] >= conf_thres).squeeze()
        image_pred = image_pred[conf_mask]

        if not image_pred.size(0):
            continue

        # 获得种类及其置信度
        class_conf, class_pred = torch.max(image_pred[:, 5:5 + num_classes], 1, keepdim=True)

        # 获得的内容为(x1, y1, x2, y2, obj_conf, class_conf, class_pred)
        detections = torch.cat((image_pred[:, :5], class_conf.float(), class_pred.float()), 1)

        # 获得种类
        unique_labels = detections[:, -1].cpu().unique()

        if prediction.is_cuda:
            unique_labels = unique_labels.cuda()

        # 对每一个类进行非极大值抑制
        for c in unique_labels:
            # 获得某一类初步筛选后全部的预测结果
            detections_class = detections[detections[:, -1] == c]
            # 按照存在物体的置信度排序
            _, conf_sort_index = torch.sort(detections_class[:, 4], descending=True)
            detections_class = detections_class[conf_sort_index]
            # 进行非极大抑制
            max_detections = []
            while detections_class.size(0):
                # 取出这一类置信度最高的，一步一步往下判断，判断重合程度是否大于nms_thres，如果是则去除掉
                max_detections.append(detections_class[0].unsqueeze(0))
                if len(detections_class) == 1:
                    break
                ious = bbox_iou(max_detections[-1], detections_class[1:])
                detections_class = detections_class[1:][ious < nms_thres]
            # 堆叠
            max_detections = torch.cat(max_detections).data
            # Add max detections to outputs
            output[image_i] = max_detections if output[image_i] is None else torch.cat(
                (output[image_i], max_detections))


        #################################################################################################
        threshold = 0.55
        _, class_conf_index = torch.sort(output[image_i][:, 5], descending=True)
        output[image_i] = output[image_i][class_conf_index]
        detection = output[image_i]
        image_result = []
        while detection.size(0):
            # 取出这一类置信度最高的，一步一步往下判断，判断重合程度是否大于nms_thres，如果是则去除掉
            image_result.append(detection[0].unsqueeze(0))
            if len(detection) == 1:
                break
            ious = bbox_iou(image_result[-1], detection[1:])
            detection = detection[1:][ious < threshold]
        # 堆叠
        image_result = torch.cat(image_result).data
        # Add max detections to outputs
        output[image_i] = image_result

        # for i in range(len(output[image_i])):
        #     print(i)
        #     for j in range(i+1, len(output[image_i])):
        #         print(i, j)
        # if output[image_i] is not None:
        #     print("test no suppress output", output[image_i].shape)
        ###############################################################################################
    return output


def merge_bboxes(bboxes, cutx, cuty):
    merge_bbox = []
    for i in range(len(bboxes)):
        for box in bboxes[i]:
            tmp_box = []
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]

            if i == 0:
                if y1 > cuty or x1 > cutx:
                    continue
                if y2 >= cuty and y1 <= cuty:
                    y2 = cuty
                    if y2 - y1 < 5:
                        continue
                if x2 >= cutx and x1 <= cutx:
                    x2 = cutx
                    if x2 - x1 < 5:
                        continue

            if i == 1:
                if y2 < cuty or x1 > cutx:
                    continue

                if y2 >= cuty and y1 <= cuty:
                    y1 = cuty
                    if y2 - y1 < 5:
                        continue

                if x2 >= cutx and x1 <= cutx:
                    x2 = cutx
                    if x2 - x1 < 5:
                        continue

            if i == 2:
                if y2 < cuty or x2 < cutx:
                    continue

                if y2 >= cuty and y1 <= cuty:
                    y1 = cuty
                    if y2 - y1 < 5:
                        continue

                if x2 >= cutx and x1 <= cutx:
                    x1 = cutx
                    if x2 - x1 < 5:
                        continue

            if i == 3:
                if y1 > cuty or x2 < cutx:
                    continue

                if y2 >= cuty and y1 <= cuty:
                    y2 = cuty
                    if y2 - y1 < 5:
                        continue

                if x2 >= cutx and x1 <= cutx:
                    x1 = cutx
                    if x2 - x1 < 5:
                        continue

            tmp_box.append(x1)
            tmp_box.append(y1)
            tmp_box.append(x2)
            tmp_box.append(y2)
            tmp_box.append(box[-1])
            merge_bbox.append(tmp_box)
    return merge_bbox