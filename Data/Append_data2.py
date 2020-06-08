import os

import numpy as np
import os
import random
import xml.etree.ElementTree as ET


Trainset = open('Trainset.txt', 'a')
path = "/home/jackzhou/Downloads/DATAME/Annotations"
filelist = os.listdir(path)
classes = ["have_mask", "no_mask"]
imgdirpath = "/home/jackzhou/Downloads/all_mask"


for i, xmlpath in enumerate(filelist):
    tree = ET.parse(os.path.join(path, xmlpath))
    root = tree.getroot()
    if root.find('object') == None:
        continue

    imgpath = os.path.join(imgdirpath, xmlpath[:-3]+'jpg')
    print(imgpath)
    Trainset.write(imgpath)
    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        if cls not in classes or int(difficult) == 1:
            continue
        cls_id = classes.index(cls)
        xmlbox = obj.find('bndbox')
        b = (int(xmlbox.find('xmin').text), int(xmlbox.find('ymin').text), int(xmlbox.find('xmax').text),
             int(xmlbox.find('ymax').text))
        Trainset.write(" " + ",".join([str(a) for a in b]) + ',' + str(cls_id))
    Trainset.write('\n')
