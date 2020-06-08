import glob
import xml.etree.ElementTree as ET
import os
import numpy as np

from Kmeans import kmeans, avg_iou

ANNOTATIONS_PATH = "Annotations"
CLUSTERS = 9

def load_dataset():
    dataset = []
    file = open('/home/jackzhou/PycharmProjects/mask_detection/Data/Trainset.txt', 'r')
    for line in file:
        boxes = line.strip().split(" ")[1:]
        for box in boxes:
            tmp = []
            box = box.split(',')
            tmp.append(int((int(box[2])-int(box[0]))/960.*416))
            tmp.append(int((int(box[3])-int(box[1]))/960.*416))

            dataset.append(tmp)
    dataset = np.array(dataset)
    return np.array(dataset)


data = load_dataset()
out = kmeans(data, k=CLUSTERS)
print("Accuracy: {:.2f}%".format(avg_iou(data, out) * 100))
print("Boxes:\n {}".format(out))

ratios = np.around(out[:, 0] / out[:, 1], decimals=2).tolist()
print("Ratios:\n {}".format(sorted(ratios)))