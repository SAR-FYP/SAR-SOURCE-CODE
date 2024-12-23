#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import time
import threading
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.PID as PID
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import HiwonderSDK.yaml_handle as yaml_handle

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

x_dis = 500
y_dis = 10
Z_DIS = 18
z_dis = Z_DIS
x_pid = PID.PID(P=0.1, I=0.00, D=0.008)  # pid initialization 
y_pid = PID.PID(P=0.00001, I=0, D=0)
z_pid = PID.PID(P=0.005, I=0, D=0)
    
    
# initial position
def initMove():
    Board.setPWMServoPulse(1, 500, 800)
    Board.setPWMServoPulse(2, 500, 800)
    AK.setPitchRangeMoving((0, y_dis, z_dis), 0,-90, 0, 1500)
    time.sleep(1.5)

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)


# find the contour with the largest area
# the parameter is the list of the contour to be compared
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    areaMaxContour = None

    for c in contours:  # traverse all the contour
        contour_area_temp = math.fabs(cv2.contourArea(c))  # calculate the contour area
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # only when the area is more than 300, the contour with the largest area is effective so as to avoid interference
                areaMaxContour = c

    return areaMaxContour, contour_area_max  # return the largest contour

#set the color of RGB light on expansion board to match with the tracked color 
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()



get_roi = False
detect_color = 'None'
start_pick_up = False
rect = None
size = (640, 480)
rotation_angle = 0
roi = ()
st = True

def run(img):
    global st 
    global roi
    global rect
    global get_roi
    global detect_color
    global rotation_angle
    global start_pick_up
    global img_h, img_w
    global x_dis, y_dis, z_dis
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
     
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # convert the image into LAB space
    
    area_max = 0
    areaMaxContour = 0
    if not start_pick_up:
        for i in lab_data:
            if i in __target_color:
                detect_color = i
                frame_mask = cv2.inRange(frame_lab,
                                             (lab_data[detect_color]['min'][0],
                                              lab_data[detect_color]['min'][1],
                                              lab_data[detect_color]['min'][2]),
                                             (lab_data[detect_color]['max'][0],
                                              lab_data[detect_color]['max'][1],
                                              lab_data[detect_color]['max'][2]))  #perform bit operation on original image and the mask 
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # open operation
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # close operation
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # find the contour
                areaMaxContour, area_max = getAreaMaxContour(contours)  # find the largest contour
        if area_max > 1000:  # the largest area is found
            (center_x, center_y), radius = cv2.minEnclosingCircle(areaMaxContour)  # acquire the smallest circumscribed circle
            center_x = int(Misc.map(center_x, 0, size[0], 0, img_w))
            center_y = int(Misc.map(center_y, 0, size[1], 0, img_h))
            radius = int(Misc.map(radius, 0, size[0], 0, img_w))
            if radius > 100:
                return img
            
            rect = cv2.minAreaRect(areaMaxContour)
            box = np.int0(cv2.boxPoints(rect))
            cv2.drawContours(img, [box], -1, range_rgb[__target_color], 2)
            
            x_pid.SetPoint = img_w / 2.0  # set
            x_pid.update(center_x)  # current 
            dx = x_pid.output
            x_dis += int(dx)  # output

            x_dis = 0 if x_dis < 0 else x_dis
            x_dis = 1000 if x_dis > 1000 else x_dis

            y_pid.SetPoint = 9000  # set
            if abs(area_max - 9000) < 50:
                area_max = 9000
            y_pid.update(area_max)  # current
            dy = y_pid.output
            y_dis += dy  # output
            y_dis = 5.00 if y_dis < 5.00 else y_dis
            y_dis = 10.00 if y_dis > 10.00 else y_dis
            
            if abs(center_y - img_h/2.0) < 20:
                z_pid.SetPoint = center_y
            else:
                z_pid.SetPoint = img_h / 2.0
                
            z_pid.update(center_y)
            dy = z_pid.output
            z_dis += dy

            z_dis = 32.00 if z_dis > 32.00 else z_dis
            z_dis = 10.00 if z_dis < 10.00 else z_dis
            
            target = AK.setPitchRange((0, round(y_dis, 2), round(z_dis, 2)), -90, 0)
            
            if target:
                servo_data = target[0]
                if st:
                    Board.setBusServoPulse(3, servo_data['servo3'], 1000)
                    Board.setBusServoPulse(4, servo_data['servo4'], 1000)
                    Board.setBusServoPulse(5, servo_data['servo5'], 1000)
                    Board.setBusServoPulse(6, int(x_dis), 1000)
                    time.sleep(1)
                    st = False
                else:
                    Board.setBusServoPulse(3, servo_data['servo3'], 20)
                    Board.setBusServoPulse(4, servo_data['servo4'], 20)
                    Board.setBusServoPulse(5, servo_data['servo5'], 20)
                    Board.setBusServoPulse(6, int(x_dis), 20)
                    time.sleep(0.03)
                
                
                    
    return img

if __name__ == '__main__':
    initMove()
    load_config()
    
    __target_color = ('red')
    cap = cv2.VideoCapture(-1)
    time.sleep(3)
    
    while True:
        ret,img = cap.read()
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
    my_camera.camera_close()
    cv2.destroyAllWindows()
