#-------------------------------------#
#       mAP所需文件计算代码
#       具体教程请查看Bilibili
#       Bubbliiiing
#-------------------------------------#
import sys
import os
import glob
import xml.etree.ElementTree as ET
xmlfilepath = r'/home/jackzhou/Downloads/mask_dataset/'
image_ids = open('/home/jackzhou/PycharmProjects/mask_detection/Data/Testset.txt').read().strip().split()
print(image_ids)
if not os.path.exists("./input"):
    os.makedirs("./input")
if not os.path.exists("./input/ground-truth"):
    os.makedirs("./input/ground-truth")

for image_id in image_ids:
    if image_id.startswith("/"):
        tmp = image_id.split('/')
        dirname = tmp[-2][6:]
        image_id = image_id[-8:-4]
        with open("./input/ground-truth/"+image_id+".txt", "w") as new_f:
            xmlpath = os.path.join(xmlfilepath, 'label_' + dirname)
            root = ET.parse(os.path.join(xmlpath, image_id + ".xml")).getroot()
            for obj in root.findall('object'):
                obj_name = obj.find('name').text
                bndbox = obj.find('bndbox')
                left = bndbox.find('xmin').text
                top = bndbox.find('ymin').text
                right = bndbox.find('xmax').text
                bottom = bndbox.find('ymax').text
                print("%s %s %s %s %s\n" % (obj_name, left, top, right, bottom))
                new_f.write("%s %s %s %s %s\n" % (obj_name, left, top, right, bottom))
print("Conversion completed!")
