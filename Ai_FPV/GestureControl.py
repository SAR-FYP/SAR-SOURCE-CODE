#!/usr/bin/python3
# coding=utf8
import os
import sys
import cv2
import math
import time
import numpy as np
import HiwonderSDK.Board as Board
import HiwonderSDK.Misc as Misc
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()
__finger = 0
__t1 = 0
__step = 0
__count = 0
__get_finger = False

# initial position
def initMove():
    Board.setBusServoPulse(1, 500, 800)
    Board.setBusServoPulse(2, 500, 800)
    AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)

def reset():
    global __finger, __t1, __step, __count, __get_finger
    __finger = 0
    __t1 = 0
    __step = 0
    __count = 0
    __get_finger = False
    

def init():
    reset()
    initMove()

class Point(object):  # a coordinate
    x = 0
    y = 0

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Line(object):  # a line
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

def GetCrossAngle(l1, l2):
    '''
    get the angle between two straight line
    :param l1:
    :param l2:
    :return:
    '''
    arr_0 = np.array([(l1.p2.x - l1.p1.x), (l1.p2.y - l1.p1.y)])
    arr_1 = np.array([(l2.p2.x - l2.p1.x), (l2.p2.y - l2.p1.y)])
    cos_value = (float(arr_0.dot(arr_1)) / (np.sqrt(arr_0.dot(arr_0))
                                            * np.sqrt(arr_1.dot(arr_1))))   # convert to floating-point operation
    return np.arccos(cos_value) * (180/np.pi)

def distance(start, end):
    """
    calculate the distance between two points
    :param start: starting point
    :param end: end piont 
    :return: return the distance between two points
    """
    s_x, s_y = start
    e_x, e_y = end
    x = s_x - e_x
    y = s_y - e_y
    return math.sqrt((x**2)+(y**2))

def image_process(image, rw, rh):  # hsv
    '''
    # Affected by light. Please modify cb range.
    # Cr of tone of Asian is about 140~160
    Recognize skin tone
    :param image: image
    :return: binary image after recognition
    '''
    frame_resize = cv2.resize(image, (rw, rh), interpolation=cv2.INTER_CUBIC)
    YUV = cv2.cvtColor(frame_resize, cv2.COLOR_BGR2YCR_CB)  # convert image into YCrCb
    _, Cr, _ = cv2.split(YUV)  # segment YCrCb
    Cr = cv2.GaussianBlur(Cr, (5, 5), 0)
    
    _, Cr = cv2.threshold(Cr, 135, 180, cv2.THRESH_BINARY +
                          cv2.THRESH_OTSU)  # OTSU binaryzation

    # open operation. Remove noise
    open_element = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    opend = cv2.morphologyEx(Cr, cv2.MORPH_OPEN, open_element)
    # corrode
    kernel = np.ones((3, 3), np.uint8)
    erosion = cv2.erode(opend, kernel, iterations=3)

    return erosion

def get_defects_far(defects, contours, img):
    '''
    obtain the furtherest point of the convex hull
    '''
    if defects is None and contours is None:
        return None
    far_list = []
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(contours[s][0])
        end = tuple(contours[e][0])
        far = tuple(contours[f][0])
        # get the distance between two points
        a = distance(start, end)
        b = distance(start, far)
        c = distance(end, far)
        # get the angle between the fingers
        angle = math.acos((b ** 2 + c ** 2 - a ** 2) /
                          (2 * b * c)) * 180 / math.pi
        # the angle between the fingers is generally smaller that 100 degree
        # smaller than 90 degree
        if angle <= 75:  # 90:
            # cv.circle(img, far, 10, [0, 0, 255], 1)
            far_list.append(far)
    return far_list

def get_max_coutour(cou, max_area):
    '''
    find the largest contour
    Calculate according to the area. After the largest contour is found, judge whether it is samller than the smallest area. If it is smaller than the smallest area, then quit.
    :param cou: contour
    :return: return the largest contour
    '''
    max_coutours = 0
    r_c = None
    if len(cou) < 1:
        return None
    else:
        for c in cou:
            # calculate the area
            temp_coutours = math.fabs(cv2.contourArea(c))
            if temp_coutours > max_coutours:
                max_coutours = temp_coutours
                cc = c
        # Determine the maximum area of all contours
        if max_coutours > max_area:
            r_c = cc
        return r_c

def find_contours(binary, max_area):
    '''
    CV_RETR_EXTERNAL - extract only the outermost outline 
    CV_RETR_LIST - extract all the contours, and place them in list
    CV_RETR_CCOMP - extrat all the contours, and organize it into two layers of hierarchy. The top layer is the outer boundary of the connected domain and the second layer is the inner boundary of the hole
    CV_RETR_TREE - extract all contours, and reconstruct all of the nested contours 
    method  approximation method. Work on all nodes, except CV_RETR_RUNS which use inner approximation
    CV_CHAIN_CODE - Freeman The output contour of the chain code. Other methods output polygons (fixed-point sequences).
    CV_CHAIN_APPROX_NONE - Translate all points from chain code form to point sequence form
    CV_CHAIN_APPROX_SIMPLE - Compression horizontal, vertical, and diagonal segmentation, i.e. the function preserves only the terminal pixel points;
    CV_CHAIN_APPROX_TC89_L1,
    CV_CHAIN_APPROX_TC89_KCOS - application Teh-Chin Chain approximation algorithm. CV_LINK_RUNS - Using a completely different contour extraction algorithm through the horizontal fragment connected to 1
    :param binary: passed in binary image
    :return: return the largest contour
    '''
    # find out all the contour
    contours = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
    # return the largest contour
    return get_max_coutour(contours, max_area)

def get_hand_number(binary_image, contours, rw, rh, rgb_image):
    '''
    :param binary_image:
    :param rgb_image:
    :return:
    '''
    # # 2、locate the fingertip
    # # search for the contour. return the largest contour
    x = 0
    y = 0
    coord_list = []
    new_hand_list = []  # obtain the final finger coordinate

    if contours is not None:
        # perimeter  0.035 modify according to the recogniztion result. The better the recognition effect is, the smaller the value is.
        epsilon = 0.020 * cv2.arcLength(contours, True)
        # approximate contour
        approx = cv2.approxPolyDP(contours, epsilon, True)
        # Parameter 2(epsilon) of cv2.approxPolyDP() is a distance value, indicating the extent to which the outline of the polygon is close to the actual outline. The smaller the value is, the more accurate it is. Parameter 3 indicates whether the switch is on
        # cv2.polylines(rgb_image, [approx], True, (0, 255, 0), 1)#draw a polygon

        if approx.shape[0] >= 3:  # there are more than three points#The smallest polygon is triangle. Triangle requires three points. 
            approx_list = []
            for j in range(approx.shape[0]):  # store all the points of the polygon in a list
                # cv2.circle(rgb_image, (approx[j][0][0],approx[j][0][1]), 5, [255, 0, 0], -1)
                approx_list.append(approx[j][0])
            approx_list.append(approx[0][0])    # add a point at the end
            approx_list.append(approx[1][0])    # add second point at the end

            for i in range(1, len(approx_list) - 1):
                p1 = Point(approx_list[i - 1][0],
                           approx_list[i - 1][1])    # declare a point
                p2 = Point(approx_list[i][0], approx_list[i][1])
                p3 = Point(approx_list[i + 1][0], approx_list[i + 1][1])
                line1 = Line(p1, p2)    # declare a straight line 
                line2 = Line(p2, p3)
                angle = GetCrossAngle(line1, line2)     # obtain the angle between two straight lines
                angle = 180 - angle     #
                # print angle
                if angle < 42:  # Find the Angle at which the two lines intersect, less than 37 degrees
                    #cv2.circle(rgb_image, tuple(approx_list[i]), 5, [255, 0, 0], -1)
                    coord_list.append(tuple(approx_list[i]))

        ##############################################################################
        # remove the point between fingers
        # 1、obtain the defect of convex hull, the furthest point
        #cv2.drawContours(rgb_image, contours, -1, (255, 0, 0), 1)
        try:
            hull = cv2.convexHull(contours, returnPoints=False)
            # find the defect of convex hull. Return data, including starting point, ending, the furthest point and the approximate distance of the furthest point
            defects = cv2.convexityDefects(contours, hull)
            # return the point between fingers
            hand_coord = get_defects_far(defects, contours, rgb_image)
        except:
            return rgb_image, 0
        
        # 2、从coord_list remove the furthest point
        alike_flag = False
        if len(coord_list) > 0:
            for l in range(len(coord_list)):
                for k in range(len(hand_coord)):
                    if (-10 <= coord_list[l][0] - hand_coord[k][0] <= 10 and
                            -10 <= coord_list[l][1] - hand_coord[k][1] <= 10):    # compare x to y axis. Remove the approximate
                        alike_flag = True
                        break   #
                if alike_flag is False:
                    new_hand_list.append(coord_list[l])
                alike_flag = False
            # acquire the coordinate list of fingertip and display
            for i in new_hand_list:
                j = list(tuple(i))
                j[0] = int(Misc.map(j[0], 0, rw, 0, 640))
                j[1] = int(Misc.map(j[1], 0, rh, 0, 480))
                cv2.circle(rgb_image, (j[0], j[1]), 20, [0, 255, 255], -1)
    fingers = len(new_hand_list)

    return rgb_image, fingers

def f1_act():
    global __t1, __finger, __step, __get_finger, __count

    if not __get_finger:
        return
    if __t1 > time.time():
        return
    if __step == 0:
        Board.setBusServoPulse(1, 200, 800)
        Board.setBusServoPulse(2, 500, 800)
        time.sleep(1)
        AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
        time.sleep(1.5)
        AK.setPitchRangeMoving((-12, 0, 1), -90,-90, 0, 1500)
        time.sleep(1.5)
        Board.setBusServoPulse(1, 500, 800)
        time.sleep(1)
        AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
        time.sleep(1.5)
        AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
        time.sleep(1.5)
        AK.setPitchRangeMoving((0, 12, 1.2), -90,-90, 0, 1500)
        time.sleep(1.5)
        Board.setBusServoPulse(1, 200, 800)
        time.sleep(1)
        AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
        time.sleep(1.5)
        __step = 1
        
    else:
        __get_finger = False

def f2_act():
    global __t1, __finger, __step, __get_finger, __count

    if not __get_finger:
        return
    if __t1 > time.time():
        return
    if __step == 0:
        Board.setBusServoPulse(1, 200, 800)
        Board.setBusServoPulse(2, 500, 800)
        time.sleep(1)
        for i in range(0,2):
            
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((-12, 0, 1), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 500, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 12, 1.2+i*3), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 200, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            
        __step = 1
        
    else:
        __get_finger = False

f3_count = 0
def f3_act():
    global f3_count, __t1, __finger, __step, __get_finger, __count

    if not __get_finger:
        return
    if __t1 > time.time():
        return

    if __step == 0:
        Board.setBusServoPulse(1, 200, 800)
        Board.setBusServoPulse(2, 500, 800)
        time.sleep(1)
        for i in range(0,3):
            
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((-12, 0, 1), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 500, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 12, 1.2+i*3), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 200, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            
        __step = 1
        
    else:
        __get_finger = False
    
f4_count = 0
def f4_act():
    global f4_count, __t1, __finger, __step, __get_finger, __count

    if not __get_finger:
        return
    if __t1 > time.time():
        return

    if __step == 0:
        Board.setBusServoPulse(1, 200, 800)
        Board.setBusServoPulse(2, 500, 800)
        time.sleep(1)
        for i in range(0,4):
            
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((-12, 0, 1), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 500, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 12, 1.2+i*3), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 200, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            
        __step = 1
        
    else:
        __get_finger = False

f5_count = 0
def f5_act():
    global f5_count, __t1, __finger, __step, __get_finger, __count

    if not __get_finger:
        return
    if __t1 > time.time():
        return

    if __step == 0:
        Board.setBusServoPulse(1, 200, 800)
        Board.setBusServoPulse(2, 500, 800)
        time.sleep(1)
        for i in range(0,5):
            
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((-12, 0, 1), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 500, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((-10, 0, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            AK.setPitchRangeMoving((0, 12, 1.2+i*3), -90,-90, 0, 1500)
            time.sleep(1.5)
            Board.setBusServoPulse(1, 200, 800)
            time.sleep(1)
            AK.setPitchRangeMoving((0, 10, 18), 0,-90, 0, 1500)
            time.sleep(1.5)
            
        __step = 1
        
    else:
        __get_finger = False

__act_map = {
    1: f1_act,
    2: f2_act,
    3: f3_act,
    4: f4_act,
    5: f5_act
}


def run(img, debug=False):

    global __act_map, __get_finger
    global __step, __count, __finger

    binary = image_process(img, 320, 240)
    contours = find_contours(binary, 3000)
    img, finger = get_hand_number(binary, contours, 320, 240, img)
    if not __get_finger:
        if finger == __finger:
            __count += 1
        else:
            __count = 0
        __finger = finger
        if finger > 0 and finger < 6 and __count > 10: #call corresponding operation according to the number of recognized number
            __step = 0
            __count = 0
            __get_finger = True
            __act_map[__finger]()
    else:
        __act_map[__finger]()
    cv2.putText(img, "Finger(s):%d" % __finger, (50, 480 - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)#write the number of recognized finger on picture
    
    return img 


if __name__ == '__main__':
    
    init()
    cap = cv2.VideoCapture(-1) #read camera
    
    while True:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)           
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()
