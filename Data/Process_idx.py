import os
import random
import xml.etree.ElementTree as ET

random.seed(0)

xmlfilepath = r'/home/jackzhou/Downloads/mask_dataset/'
saveBasePath = r"/home/jackzhou/PycharmProjects/mask_detection/Data/Maskdataset/Idx/"
 
trainval_percent = 0.95
train_percent = 0.95
classes = ["have_mask", "no_mask"]

temp_xml = os.listdir(xmlfilepath)
print(temp_xml)
imgpathtolabelpath = []
for dirname in temp_xml:
    if dirname.startswith("i"):
        tmppath = os.path.join(xmlfilepath, dirname)
        xmlpath = os.path.join(xmlfilepath, 'label_'+dirname[6:])
        for filename in os.listdir(tmppath):
            if not filename.startswith('.'):
                imagepath = os.path.join(tmppath, filename)
                labelpath = os.path.join(xmlpath, filename[:4]+'.xml')
                imgpathtolabelpath.append([imagepath, labelpath])

random.shuffle(imgpathtolabelpath)

trainval_size = int(len(imgpathtolabelpath) * trainval_percent)
train_size = int(trainval_size * train_percent)
idx = range(len(imgpathtolabelpath))

trainval = random.sample(idx, trainval_size)
train = random.sample(trainval, train_size)

Trainset = open('Trainset.txt', 'w')
Valset = open('Valset.txt', 'w')
Testset = open('Testset.txt', 'w')

for i, imgpath in enumerate(imgpathtolabelpath):
    print(i, imgpath)

for i, (imgpath, xmlpath) in enumerate(imgpathtolabelpath):
    print(imgpath, xmlpath)
    tree = ET.parse(xmlpath)
    root = tree.getroot()
    if root.find('object') == None:
        continue

    if i in trainval:
        if i in train:
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
        else:
            Valset.write(imgpath)
            for obj in root.iter('object'):
                difficult = obj.find('difficult').text
                cls = obj.find('name').text
                if cls not in classes or int(difficult) == 1:
                    continue
                cls_id = classes.index(cls)
                xmlbox = obj.find('bndbox')
                b = (int(xmlbox.find('xmin').text), int(xmlbox.find('ymin').text), int(xmlbox.find('xmax').text),
                     int(xmlbox.find('ymax').text))
                Valset.write(" " + ",".join([str(a) for a in b]) + ',' + str(cls_id))
            Valset.write('\n')
    else:
        Testset.write(imgpath)
        for obj in root.iter('object'):
            difficult = obj.find('difficult').text
            cls = obj.find('name').text
            if cls not in classes or int(difficult) == 1:
                continue
            cls_id = classes.index(cls)
            xmlbox = obj.find('bndbox')
            b = (int(xmlbox.find('xmin').text), int(xmlbox.find('ymin').text), int(xmlbox.find('xmax').text),
                 int(xmlbox.find('ymax').text))
            Testset.write(" " + ",".join([str(a) for a in b]) + ',' + str(cls_id))
        Testset.write('\n')

Trainset.close()
Valset.close()
Testset.close()
