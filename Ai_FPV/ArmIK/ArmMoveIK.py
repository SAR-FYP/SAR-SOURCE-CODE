#!/usr/bin/env python3
# encoding:utf-8
import sys
sys.path.append('/home/ubuntu/Sensor/')
import time
import numpy as np
from math import sqrt
#import matplotlib.pyplot as plt
from ArmIK.InverseKinematics import *
from ArmIK.Transform import getAngle
#from mpl_toolkits.mplot3d import Axes3D
from HiwonderSDK.Board import setBusServoPulse, getBusServoPulse

#the robotic arm moves according to the angle calculated by inverse kinematics 
ik = IK('arm')
#set the length of link
l1 = ik.l1 + 0.75
l4 = ik.l4 - 0.15
ik.setLinkLength(L1=l1, L4=l4)

class ArmIK:
    servo3Range = (0, 1000.0, 0, 240.0) #pulse width， angle
    servo4Range = (0, 1000.0, 0, 240.0)
    servo5Range = (0, 1000.0, 0, 240.0)
    servo6Range = (0, 1000.0, 0, 240.0)

    def __init__(self):
        self.setServoRange()

    def setServoRange(self, servo3_Range=servo3Range, servo4_Range=servo4Range, servo5_Range=servo5Range, servo6_Range=servo6Range):
        # adapt to different servo
        self.servo3Range = servo3_Range
        self.servo4Range = servo4_Range
        self.servo5Range = servo5_Range
        self.servo6Range = servo6_Range
        self.servo3Param = (self.servo3Range[1] - self.servo3Range[0]) / (self.servo3Range[3] - self.servo3Range[2])
        self.servo4Param = (self.servo4Range[1] - self.servo4Range[0]) / (self.servo4Range[3] - self.servo4Range[2])
        self.servo5Param = (self.servo5Range[1] - self.servo5Range[0]) / (self.servo5Range[3] - self.servo5Range[2])
        self.servo6Param = (self.servo6Range[1] - self.servo6Range[0]) / (self.servo6Range[3] - self.servo6Range[2])

    def transformAngelAdaptArm(self, theta3, theta4, theta5, theta6):
        #convert the angle calculated by inverse kinematics into pulse width corresponding to servo
        servo3 = int(round(theta3 * self.servo3Param + (self.servo3Range[1] + self.servo3Range[0])/2))
        if servo3 > self.servo3Range[1] or servo3 < self.servo3Range[0] + 60:
            logger.info('servo3(%s)exceed the range(%s, %s)', servo3, self.servo3Range[0] + 60, self.servo3Range[1])
            return False

        servo4 = int(round(theta4 * self.servo4Param + (self.servo4Range[1] + self.servo4Range[0])/2))
        if servo4 > self.servo4Range[1] or servo4 < self.servo4Range[0]:
            logger.info('servo4(%s)exceed the range(%s, %s)', servo4, self.servo4Range[0], self.servo4Range[1])
            return False

        servo5 = int(round((self.servo5Range[1] + self.servo5Range[0])/2 - (90.0 - theta5) * self.servo5Param))
        if servo5 > ((self.servo5Range[1] + self.servo5Range[0])/2 + 90*self.servo5Param) or servo5 < ((self.servo5Range[1] + self.servo5Range[0])/2 - 90*self.servo5Param):
            logger.info('servo5(%s)exceed the range(%s, %s)', servo5, self.servo5Range[0], self.servo5Range[1])
            return False
        
        if theta6 < -(self.servo6Range[3] - self.servo6Range[2])/2:
            servo6 = int(round(((self.servo6Range[3] - self.servo6Range[2])/2 + (90 + (180 + theta6))) * self.servo6Param))
        else:
            servo6 = int(round(((self.servo6Range[3] - self.servo6Range[2])/2 - (90 - theta6)) * self.servo6Param))
        if servo6 > self.servo6Range[1] or servo6 < self.servo6Range[0]:
            logger.info('servo6(%s)exceed the range(%s, %s)', servo6, self.servo6Range[0], self.servo6Range[1])
            return False

        return {"servo3": servo3, "servo4": servo4, "servo5": servo5, "servo6": servo6}

    def servosMove(self, servos, movetime=None):
        #drive NO. 3, 4, 5 and 6 servo to rotate
        time.sleep(0.02)
        if movetime is None:
            max_d = 0
            for i in  range(0, 4):
                d = abs(getBusServoPulse(i + 3) - servos[i])
                if d > max_d:
                    max_d = d
            movetime = int(max_d*4)
        setBusServoPulse(3, servos[0], movetime)
        setBusServoPulse(4, servos[1], movetime)
        setBusServoPulse(5, servos[2], movetime)
        setBusServoPulse(6, servos[3], movetime)

        return movetime

    def setPitchRange(self, coordinate_data, alpha1, alpha2, da = 1):
        #The given coordinate is coordinate_data and pitch angle range is alpha1 and alpha2. Automatically search the appropriate solution within the range
        #If there is no solution, return False. Otherwise, return corresponding servo angle and pitch angle. 
        #The coordinate in cm is passed in as tuple, for example (0, 5, 10)
        #da is increased angle in each pitch angle traverse
        x, y, z = coordinate_data
        if alpha1 >= alpha2:
            da = -da
        for alpha in np.arange(alpha1, alpha2, da):#traverse to find solution
            result = ik.getRotationAngle((x, y, z), alpha)
            if result:
                theta3, theta4, theta5, theta6 = result['theta3'], result['theta4'], result['theta5'], result['theta6']
                servos = self.transformAngelAdaptArm(theta3, theta4, theta5, theta6)
                if servos != False:
                    return servos, alpha

        return False

    def setPitchRangeMoving(self, coordinate_data, alpha, alpha1, alpha2, movetime=None):
        #The given coordinate is coordinate_data, pitch angle is alpha, and pitch angle range is alpha1 and alpha2. Automatically search the appropriate solution within the range. And rotate to the target position. 
        #If there is no solution, return False. Otherwise return servo angle, pitch angle and running time.
        #The coordinate in cm is passed in as tuple, for example (0, 5, 10)
        #alpha is the given pitch angle
        #alpha1 and alpha2 are pitch angle range
        #movetime is servo rotation time in ms. If the time is not given, calculate automatically.
        x, y, z = coordinate_data
        result1 = self.setPitchRange((x, y, z), alpha, alpha1)
        result2 = self.setPitchRange((x, y, z), alpha, alpha2)
        if result1 != False:
            data = result1
            if result2 != False:
                if abs(result2[1] - alpha) < abs(result1[1] - alpha):
                    data = result2
        else:
            if result2 != False:
                data = result2
            else:
                return False
        servos, alpha = data[0], data[1]

        movetime = self.servosMove((servos["servo3"], servos["servo4"], servos["servo5"], servos["servo6"]), movetime)

        return servos, alpha, movetime
    '''
    #for test
    def drawMoveRange2D(self, x_min, x_max, dx, y_min, y_max, dy, z, a_min, a_max, da):
        # test the reachable points. Display them in 2d image and fix with z
        #test the reachable points. Display them in 3d image. If the points overwhelm, it is difficult for 3d image to rotate.
        try:
            for y in np.arange(y_min, y_max, dy):
                for x in np.arange(x_min, x_max, dx):
                    result = self.setPitchRange((x, y, z), a_min, a_max, da)
                    if result:
                        plt.scatter(x, y, s=np.pi, c='r')

            plt.xlabel('X Label')
            plt.ylabel('Y Label')

            plt.show()
        except Exception as e:
            print(e)
            pass

    def drawMoveRange3D(self, x_min, x_max, dx, y_min, y_max, dy, z_min, z_max, dz, a_min, a_max, da):
        #test the reachable points. Display them in 3d image. If the points overwhelm, it is difficult for 3d image to rotate.
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        try:
            for z in np.arange(z_min, z_max, dz):
                for y in np.arange(y_min, y_max, dy):
                    for x in np.arange(x_min, x_max, dx):
                        result = self.setPitchRange((x, y, z), a_min, a_max, da)
                        if result:
                            ax.scatter(x, y, z, s=np.pi, c='r')

            ax.set_xlabel('X Label')
            ax.set_ylabel('Y Label')
            ax.set_zlabel('Z Label')

            plt.show()
        except Exception as e:
            print(e)
            pass
    '''

if __name__ == "__main__":
    AK = ArmIK()
    setBusServoPulse(1, 200, 500)
    setBusServoPulse(2, 500, 500)
    #AK.setPitchRangeMoving((0, 10, 10), -30, -90, 0, 2000)
    #time.sleep(2)
    print(AK.setPitchRangeMoving((-4.8, 15, 1.5), 0, -90, 0, 2000))
    #AK.drawMoveRange2D(-10, 10, 0.2, 10, 30, 0.2, 2.5, -90, 90, 1)
