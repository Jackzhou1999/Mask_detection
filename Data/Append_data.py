import os
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

Trainset = open('Trainset.txt', 'a')
path = "/home/jackzhou/Downloads/all_mask/"
filelist = os.listdir(path)
x, y = 2, 1
base_path = "/home/jackzhou/Pictures/photo"
for file in filelist[:2000]:
    if file[-3:] == 'jpg':
        Trainset.write(os.path.join(path, file))
        image = Image.open(os.path.join(path, file))
        print(file)
        image.save(os.path.join(base_path, file))
        f = open(os.path.join(path, file[:-3]+'txt'))
        lines = f.readlines()
        a = np.array(image)
        h, w, c = a.shape
        for box in lines:
            b = box.strip().split()
            xmin = max(int(float(b[x])*h) - int(float(b[3])*w)//2, 0)
            xmax = min(int(float(b[x])*h) + int(float(b[3])*w)//2, h-1)
            ymin = max(int(float(b[y])*w) - int(float(b[4])*h)//2, 0)
            ymax = min(int(float(b[y])*w) + int(float(b[4])*h)//2, w-1)
            if b[0] == '0':
                cls_id = 1
            else:
                cls_id = 0
            BOX = (xmin, ymin, xmax, ymax)
            Trainset.write(" " + ",".join([str(a) for a in BOX]) + ',' + str(cls_id))
            print(os.path.join(path, file))
            print(xmin, xmax, ymin, ymax)
            print(h, w)
            a[xmin, ymin], a[xmax, ymax] = 0, 0

        Trainset.write('\n')

