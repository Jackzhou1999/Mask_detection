#-------------------------------------#
#       调用摄像头检测
#-------------------------------------#
from yolo import YOLO
from PIL import Image
import numpy as np
import cv2
import time
yolo = YOLO()
# 调用摄像头
capture = cv2.VideoCapture("/home/jackzhou/Downloads/masknew2.mp4")

width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = capture.get(cv2.CAP_PROP_FPS)
fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', '2')
outVideo = cv2.VideoWriter('Vedio/save_test_video.avi', fourcc, fps, (width, height))

# fps = 0.0
while True:
    t1 = time.time()
    # 读取某一帧
    ref, frame = capture.read()
    if not ref:
        break

    # 格式转变，BGRtoRGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # 转变成Image
    frame = Image.fromarray(np.uint8(frame))

    # 进行检测
    frame = np.array(yolo.detect_image(frame))

    # RGBtoBGR满足opencv显示格式
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # fps = (fps + (1./(time.time()-t1)) ) / 2
    # print("fps= %.2f" % (fps))
    # frame = cv2.putText(frame, "fps= %.2f"%(fps), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.namedWindow("video", 0)  # 0可调大小，注意：窗口名必须imshow里面的一窗口名一直
    cv2.resizeWindow("video", 800, 450)    # 设置长和宽
    cv2.imshow("video",frame)
    outVideo.write(frame)


    c= cv2.waitKey(30) & 0xff
    if c==27:
        capture.release()
        break
