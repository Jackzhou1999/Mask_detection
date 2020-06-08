
annotation_path = '/home/jackzhou/PycharmProjects/mask_detection/Data/Trainset.txt'

val_split = 0.1
with open(annotation_path) as f:
    lines = f.readlines()
print(lines)

import numpy as np

a = np.zeros(shape=(2,3))
print(len(a))

output = [None for _ in range(len(a))]
print(output)

import torch
a = torch.tensor([[1,5,62,54], [2,6,2,6], [2,65,2,6]])
c, d = torch.max(a, 1)
print(c, d)

gt_box = torch.FloatTensor(np.array([0, 0, 3, 3]))
print(gt_box.shape)

gt_box = torch.FloatTensor(np.array([0, 0, 2, 2])).unsqueeze(0)
print(gt_box.shape)
import os
from PIL import Image
import matplotlib.pyplot as plt

path = "/home/jackzhou/Downloads/all_mask/"
filelist = os.listdir(path)
x, y = 2, 1
for file in filelist:
    if file[-3:] == 'jpg':
        image = Image.open(os.path.join(path, file))
        f = open(os.path.join(path, file[:-3]+'txt'))
        lines = f.readlines()
        print(lines)
        a = np.array(image)
        h, w, c = a.shape
        print(h, w)
        for box in lines:
            b = box.strip().split()
            print(b)
            xmin = max(int(float(b[x])*h) - int(float(b[3])*w)//2, 0)
            xmax = min(int(float(b[x])*h) + int(float(b[3])*w)//2, h-1)
            ymin = max(int(float(b[y])*w) - int(float(b[4])*h)//2, 0)
            ymax = min(int(float(b[y])*w) + int(float(b[4])*h)//2, w-1)
            print(xmin, xmax, ymin, ymax)
            a[xmin, ymin], a[xmax, ymax] = 0, 0

            for i in range(xmin, xmax):
                a[i, ymin] = [255, 0, 0]
                a[i, ymax] = [255, 0, 0]
            for j in range(ymin, ymax):
                a[xmin, j] = [255, 0, 0]
                a[xmax, j] = [255, 0, 0]
            a[int(float(b[x])*h), int(float(b[y])*w), :] = 0
            # for i in range(int(float(b[4])*h)//2):
            #     a[int(float(b[x]) * h)+i, int(float(b[y]) * w), :] = 0
            # for i in range(int(float(b[3])*w)//2):
            #     a[int(float(b[x]) * h), int(float(b[y]) * w)+i, :] = 0

        plt.figure()
        plt.imshow(a)
        plt.show()
