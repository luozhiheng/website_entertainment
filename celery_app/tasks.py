from __future__ import absolute_import, unicode_literals
from celery import shared_task
from website_entertainment.celery import app  # import the instance then share_task can work need issue
from celery.signals import task_success
from PIL import Image, ImageGrab
import pytesseract
import cv2
import os
import time
import numpy as np


@shared_task(name='website_entertainment.celery_app.tasks.add')  # specify name if you like
def add(x, y):
    return x + y


@task_success.connect(sender='website_entertainment.celery_app.tasks.add')
def add_success(sender=None, headers=None, body=None, **kwargs):
    # information about task are located in headers for task messages
    # using the task protocol version 2.
    info = headers if 'task' in headers else body
    print('after_task_success for task id {info[id]}'.format(
        info=info,
    ))


@app.task(bind=True)
def mulit(self, x, y):
    print(self)
    return x * y


min_confidence = 0.5


def _non_max_suppression(boxes, probs=None, overlapThresh=0.3):
    # if there are no boxes, return an empty list
    if len(boxes) == 0:
        return []
    # if the bounding boxes are integers, convert them to floats -- this
    # is important since we'll be doing a bunch of divisions
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # initialize the list of picked indexes
    pick = []

    # grab the coordinates of the bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # compute the area of the bounding boxes and grab the indexes to sort
    # (in the case that no probabilities are provided, simply sort on the
    # bottom-left y-coordinate)
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = y2

    # if probabilities are provided, sort on them instead
    if probs is not None:
        idxs = probs

    # sort the indexes
    idxs = np.argsort(idxs)

    # keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the index value
        # to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # find the largest (x, y) coordinates for the start of the bounding
        # box and the smallest (x, y) coordinates for the end of the bounding
        # box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # delete all indexes from the index list that have overlap greater
        # than the provided overlap threshold
        idxs = np.delete(idxs, np.concatenate(([last],
                                               np.where(overlap > overlapThresh)[0])))

    # return only the bounding boxes that were picked
    return boxes[pick].astype("int")


def _decode_prediction(scores, geometry):
    global min_confidence
    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the geometrical
        # data used to derive potential bounding box coordinates that
        # surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        # loop over the number of columns
        for x in range(0, numCols):
            # if our score does not have sufficient probability, ignore it
            if scoresData[x] < min_confidence:
                continue

            # compute the offset factor as our resulting feature maps will
            # be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            # extract the rotation angle for the prediction and then
            # compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height of
            # the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score to
            # our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
    return rects, confidences


def _dectect_region(image, newH, newW):
    global min_confidence
    # detect region using EAST text detector openCV
    orign = image.copy()
    (H, W) = image.shape[:2]
    rH = H / float(newH)
    rW = W / float(newW)
    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]
    # define the two output layer names for the EAST detector model that
    # we are interested -- the first is the output probabilities and the
    # second can be used to derive the bounding box coordinates of text
    layerNames = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]

    # load the pre-trained EAST text detector
    print("[INFO] loading EAST text detector...")
    net = cv2.dnn.readNet('frozen_east_text_detection.pb')

    # construct a blob from the image and then perform a forward pass of
    # the model to obtain the two output layer sets
    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
                                 (123.68, 116.78, 103.94), swapRB=True, crop=False)
    start = time.time()
    net.setInput(blob)
    (scores, geometry) = net.forward(layerNames)
    end = time.time()

    # show timing information on text prediction
    print("[INFO] text detection took {:.6f} seconds".format(end - start))
    # text_region = []
    (rects, confidences) = _decode_prediction(scores, geometry)
    # apply non-maxima suppression to suppress weak, overlapping bounding boxes
    boxes = _non_max_suppression(np.array(rects), probs=confidences)
    # loop over the bounding boxes
    for (start_x, start_y, end_x, end_y) in boxes:
        # scale the bounding box coordinates based on the respective
        # ratios
        start_x = int(start_x * rW)
        start_y = int(start_y * rH)
        end_x = int(end_x * rW)
        end_y = int(end_y * rH)

        # draw the bounding box on the image
        cv2.rectangle(orign, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        # text_region.append(orign[start_x:end_x, start_y:end_y])

    return orign


def _DetectRegionMorphological(image):  # C函数报错
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 1. Sobel算子，x方向求梯度
    sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)
    # 2. 二值化
    ret, binary = cv2.threshold(sobel, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)

    # 3. 膨胀和腐蚀操作的核函数
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 12))
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (24, 6))

    # 4. 膨胀一次，让轮廓突出
    dilation = cv2.dilate(binary, element2, iterations=1)

    # 5. 腐蚀一次，去掉细节，如表格线等。
    erosion = cv2.erode(dilation, element1, iterations=1)

    # 6. 再次膨胀，让轮廓明显一些
    dilation2 = cv2.dilate(erosion, element2, iterations=3)

    # 7. 存储中间图片
    # cv2.imwrite("binary.png", binary)
    # cv2.imwrite("dilation.png", dilation)
    # cv2.imwrite("erosion.png", erosion)
    # cv2.imwrite("dilation2.png", dilation2)

    region = []

    # 1. 查找轮廓
    contours = cv2.findContours(dilation2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # 2. 筛选那些面积小的
    for i in range(len(contours)):
        cnt = contours[i]
        # 计算该轮廓的面积
        area = cv2.contourArea(cnt)

        # 面积小的都筛选掉
        if (area < 1000):
            continue

        # 轮廓近似，作用很小
        epsilon = 0.001 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # 找到最小的矩形，该矩形可能有方向
        rect = cv2.minAreaRect(cnt)

        # box是四个点的坐标
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # 计算高和宽
        height = abs(box[0][1] - box[2][1])
        width = abs(box[0][0] - box[2][0])

        # 筛选那些太细的矩形，留下扁的
        if (height > width * 1.2):
            continue

        region.append(box)
    # 画出区域
    for box in region:
        cv2.drawContours(image, [box], 0, (0, 255, 0), 2)
    return image


@shared_task
def img2text_ocr(filename, preprocess, mylang, tconfig='', newW=320, newH=320, mode='standard'):
    # load the example image and convert it to grayscale
    image = cv2.imread(filename)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #######################################################
    # detect region using Maximally Stable External Regions
    if mode == 'standard':
        mser = cv2.MSER_create(_min_area=100)
        regions, boxes = mser.detectRegions(gray)
        for box in boxes:
            x, y, w, h = box
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 1)
    #######################################################
    # EAST text requires that the input image dimensions be multiples of 32
    elif mode == 'EAST':
        image = _dectect_region(image, newH, newW)
    elif mode == 'Morphological':
        # image = _DetectRegionMorphological(image)
        gray = _dectect_region(gray, newH, newW)
    # if dark text that is overlaid upon gray shapes
    # apply thresholding to preprocess the image
    if preprocess == "thresh":
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 47, 20)
        # gray = cv2.threshold(image, 0, 255,
        #                     cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # median blurring should be done to reduce salt and pepper noise,
    # again making it easier for Tesseract to correctly OCR the image
    elif preprocess == "blur":
        gray = cv2.medianBlur(image, 3)
    # write the grayscale image to disk as a temporary file so we can apply OCR to it
    mydir, name = os.path.split(__file__)
    newfilename = "{0}/{1}.png".format(mydir, os.getpid())
    cv2.imwrite(newfilename, gray)

    # load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
    text = pytesseract.image_to_string(Image.open(newfilename), lang=mylang, config=tconfig)
    text_list=text.split("\r\n")
    # print(text)
    os.remove(newfilename)
    ##############################
    # show the output images
    # cv2.namedWindow("Image", 0)
    # cv2.imshow("Image", image)
    # cv2.namedWindow("Output", 0)
    # cv2.imshow("Output", gray)
    # cv2.resizeWindow("Output", 640, 480)
    # cv2.resizeWindow("Image", 640, 480)
    # cv2.waitKey(0)
    ##############################
    return text_list
# img2text_ocr('D:/EAST/realt_regular.jpg', '', 'chi_sim', mode='EAST')
