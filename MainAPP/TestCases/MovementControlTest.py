'''
Created on 1 mar 2017

@author: Mateusz Raczynski
'''
from time import sleep

import numpy as np
from datetime import datetime

import MovementTracker
import VehicleApi
import Visualizer
from CommandQueue import CommandQueue
from VehicleApi import QuadcopterApi, Thread
from dronekit_sitl import SITL

import Tkinter

vehicle = None
sitl = None
root = None
modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
modeCamera = VehicleApi.FRONT


def _forward(event):
    if vehicle is None:
        return
    print '_forward called'
    vehicle.commandQueue.moveForward(1)


def _back(event):
    if vehicle is None:
        return
    print '_back called'
    vehicle.commandQueue.moveForward(-1)


def _left(event):
    if vehicle is None:
        return
    print '_left called'
    vehicle.commandQueue.moveToLocRelativeHeading(0, -1)


def _right(event):
    if vehicle is None:
        return
    print '_right called'
    vehicle.commandQueue.moveToLocRelativeHeading(0, 1)


def _rotateLeft(event):
    if vehicle is None:
        return
    print '_rotateLeft called'
    vehicle.commandQueue.changeHeading(-10)


def _rotateRight(event):
    if vehicle is None:
        return
    print '_rotateRight called'
    vehicle.commandQueue.changeHeading(10)


def _increaseHeight(event):
    if vehicle is None:
        return
    print '_increaseHeight called'
    vehicle.commandQueue.goto(0, 0, 2, True)


def _decreaseHeight(event):
    if vehicle is None:
        return
    print '_decreaseHeight called'
    vehicle.commandQueue.goto(0, 0, -2, True)


def _confirmQueue(event):
    if vehicle is None:
        return
    print '_confirmQueue called'
    vehicle.commandQueue.confirm()


def _return(event):
    if vehicle is None:
        return
    print '_return called'
    dvec = np.array([0, 0, 4]) - vehicle.getPositionVector()
    vehicle.goto(dvec[1], dvec[0], dvec[2], True)


def _switchCameraPos(event):
    if vehicle is None:
        return
    print '_switchCameraPos called'
    global modeCamera
    if modeCamera == VehicleApi.FRONT:
        vehicle.setCameraAim(VehicleApi.DOWN)
        modeCamera = VehicleApi.DOWN
    elif modeCamera == VehicleApi.DOWN:
        vehicle.setCameraAim(VehicleApi.FRONT)
        modeCamera = VehicleApi.FRONT
    print vehicle.quad.gimbal


def _switchMode(event):
    if vehicle is None:
        return
    global modeQueue
    print '_switchMode called'
    if (modeQueue == CommandQueue.Mode.QUEUE_COMMANDS):
        print 'Switching mode to IMM_EXECUTE'
        modeQueue = CommandQueue.Mode.IMM_EXECUTE
    else:
        print 'Switching mode to QUEUE_COMMANDS'
        modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
    vehicle.commandQueue.setMode(modeQueue)


def _setGuidedMode(event):
    vehicle.setMode('GUIDED')


def _onClosing():
    MovementTracker.stop()
    root.destroy()
    while vehicle is None:
        sleep(0.5)
    vehicle.close()
    if sitl is not None:
        sitl.stop()
    print("Completed")


def createVehicle(sitlTest=True):
    global vehicle
    if sitlTest:
        global sitl
        sitl = SITL()
        sitl.download('copter', '3.3', verbose=True)
        sitl_args = ['-I0', '--model', 'quad', '--home=49.9880962,19.90333,584,353']
        sitl.launch(sitl_args, await_ready=True, restart=True)
        print "Connecting to vehicle on: 'tcp:127.0.0.1:5760'"
        vehicle = QuadcopterApi('tcp:127.0.0.1:5760')
        vehicle.setMode('GUIDED')
        vehicle.arm()
        vehicle.takeoff(5)
        vehicle.getState()
    else:
        print "Connecting to vehicle on: '127.0.0.1:14550'"
        vehicle = QuadcopterApi('127.0.0.1:14550')
    vehicle.commandQueue.shouldMakeAdjustment(True)
    MovementTracker.start(vehicle)


def createGUI():
    thread = Thread(name='ControlPanelThread')
    thread.run = _createGUI
    thread.start()


manual = """
a - go left
d - go right
w - go forward
s - go back
q - rotate left
e - rotate right
t - return to [0,0,4]
c - switch camera position
left control - decrease height
space - increase height
enter - confirm command queue
r - switch command queue mode
"""


def _createGUI():
    global root
    root = Tkinter.Tk()
    root.bind('a', _left)
    root.bind('d', _right)
    root.bind('w', _forward)
    root.bind('s', _back)
    root.bind('q', _rotateLeft)
    root.bind('e', _rotateRight)
    root.bind('t', _return)
    root.bind('c', _switchCameraPos)
    root.bind('<Control_L>', _decreaseHeight)
    root.bind('<space>', _increaseHeight)
    root.bind('<Return>', _confirmQueue)
    root.bind('r', _switchMode)
    root.bind('m', _setGuidedMode)
    root.protocol("WM_DELETE_WINDOW", _onClosing)
    text = Tkinter.Text(root)
    text.insert(Tkinter.INSERT, manual)
    text.tag_configure("center", justify='center')
    text.tag_add("center", 1.0, "end")

    text.config(state=Tkinter.DISABLED)
    text.pack()
    root.mainloop()


def runTest(sitlTest):
    createGUI()
    createVehicle(sitlTest)
    veh = vehicle

    window = Visualizer.createWindow(veh)
    window.cameraC.moveFRU(f=-2)


DEBUG_MOVEMENT = True

import math
import ImageApi
from ImageProcessor import ImageProcessor
from TestApplication.Control import PARAMETER_FILE_NAME
from Utils import getCentroid
from Utils import calcMoveToTargetHorizont
from Utils import calcHeadingChangeForFrontPhoto
import GnuplotDrawer


def runRecMovementTest(sitlTest):
    # todo: make it work with real drone

    ###################
    # createGUI() and vehicle
    createVehicle(sitlTest)
    veh = vehicle
    window = Visualizer.createWindow(veh)
    if not isinstance(veh, VehicleApi.QuadcopterApi):
        return
    window.cameraFromVehicle(True)

    imgWidth = window.getWindowSize()[0]
    imgHeight = window.getWindowSize()[1]
    fovH = window.cameraC.fieldOfView
    fovV = fovH * 1. / window.cameraC.aspect

    feed = feedInfo()
    feed.videoFeed = window
    feed.veh = veh
    feed.imgWidth = imgWidth
    feed.imgHeight = imgHeight
    feed.fovH = fovH
    feed.fovV = fovV

    findObjectsOnScene(feed)

    feed.veh.commandQueue.goto(0., 0., 10, True)
    scanObject(feed)

    veh.close()


def findObjectsOnScene(feed):
    ###################
    # raise heigh enough
    feed.veh.commandQueue.goto(0., 0., 25, True)
    feed.veh.commandQueue.changeHeading(0, False)
    feed.veh.commandQueue.confirm()

    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)
    feed.videoFeed.cameraC.lookAtEulerExt(x=math.radians(-90))
    sleep(0.5)
    photo = feed.videoFeed.grabFrame()
    photoDirection = feed.veh.quad.heading
    photoAlt = feed.veh.getPositionVector()[2]
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(img,"ImageSceneAbove")
        img.show()
    # img.save("image_test.jpg")
    rawImage = ImageApi.PILImageToCV(img)

    if DEBUG_MOVEMENT:
        controlPoint = feed.videoFeed.obtainModelObject()
        pos = Visualizer.tENUtoXYZ(feed.veh.getPositionVector())
        print "Making photo at: ", pos
        controlPoint.data = [pos]
        controlPoint.color = np.array([0., 0., 1.])
        controlPoint.render = True

    ###################
    # parse photo
    flt = ImageApi.Filter()
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    sourceVectors = processor.getVectorRepresentation(rawImage, flt.prepareImage)

    points = []
    for objectIndex in range(0, len(sourceVectors['vect'])):
        targetCoords = getCentroid(sourceVectors['vect'][objectIndex])
        points.append(targetCoords)
    if DEBUG_MOVEMENT:
        gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])
        GnuplotDrawer.saveToFile(gp,"ImageSceneAboveVec",feed.videoFeed.getWindowSize())

    for objectIndex in range(0, len(points)):
        points[objectIndex] = calcMoveToTargetHorizont(points[objectIndex], photoAlt, photoDirection, feed.fovV, feed.fovH,
                                                       resolutionX=feed.imgWidth,
                                                       resolutionY=feed.imgHeight)

    objectNum = feed.veh.commandQueue.visitPoints(points, relativeToStartingPos=True, callbackOnVisited=recognizeObject,
                                                  callbackArg=feed)

    ###################
    # reset camera
    feed.veh.setCameraAim(VehicleApi.FRONT)
    feed.videoFeed.cameraC.lookAtEulerExt(x=0)


def recognizeObject(id, feed):
    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)
    feed.videoFeed.cameraC.lookAtEulerExt(x=math.radians(-90))
    sleep(0.5)
    photo = feed.videoFeed.grabFrame()
    photoDirection = feed.veh.quad.heading
    photoAlt = feed.veh.getPositionVector()[2]
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(img,"ImageForRecogAbove_"+str(id))
        img.show()
    # img.save("image_test.jpg")
    rawImage = ImageApi.PILImageToCV(img)

    ###################
    # parse photo
    flt = ImageApi.Filter()
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    sourceVectors = processor.getVectorRepresentation(rawImage, flt.prepareImage)
    # recognize
    found = False
    if found:
        return True


def scanObject(feed):
    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)
    feed.videoFeed.cameraC.lookAtEulerExt(x=math.radians(-90))
    sleep(0.5)
    photo = feed.videoFeed.grabFrame()
    photoDirection = feed.veh.quad.heading
    photoAlt = feed.veh.getPositionVector()[2]
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(img,"ImageForScanAbove")
        img.show()
    # img.save("image_test.jpg")
    rawImage = ImageApi.PILImageToCV(img)

    ###################
    # parse photo
    flt = ImageApi.Filter()
    #todo: use only one color here
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    sourceVectors = processor.getVectorRepresentation(rawImage, flt.prepareImage)
    objectIndex = 0
    if len(sourceVectors['vect']) < objectIndex + 1:
        print "VECTOR REPRESENTATION HAS INVALID AMOUNT OF OBJECTS ... RETURNING"
        feed.veh.setCameraAim(VehicleApi.FRONT)
        feed.window.cameraC.lookAtEulerExt(x=0)
        return
    print "Recognized objects: ", len(sourceVectors['vect'])
    print "Object number ", objectIndex, ":"
    BUILDING_HEIGHT = 6
    result = calcHeadingChangeForFrontPhoto(sourceVectors['vect'][objectIndex], sourceVectors['vect'],
                                            photoAlt, BUILDING_HEIGHT,
                                            feed.fovH,feed.fovV, feed.imgWidth, feed.imgHeight)
    photoPoint, headingChange, secondPhotoPoint, seconHeadingChange, chosenEdge = result

    if DEBUG_MOVEMENT:
        GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])

    dposToPhotoPoint = calcMoveToTargetHorizont(photoPoint, photoAlt, photoDirection, feed.fovV, feed.fovH,
                                                resolutionX=feed.imgWidth,
                                                resolutionY=feed.imgHeight)

    feed.veh.commandQueue.goto(dposToPhotoPoint[0], dposToPhotoPoint[1], BUILDING_HEIGHT/2, False)  # <-------
    feed.veh.commandQueue.changeHeading(photoDirection + float(headingChange), False)
    feed.veh.commandQueue.confirm()

    ###################
    # make a front photo

    ###################
    # go to other position

    ###################
    # make a side photo

    ###################
    # build model


class feedInfo(object):
    def __init__(p):
        p.videoFeed = None
        p.veh = None
        p.imgWidth = 0
        p.imgHeight = 0
        p.fovH = 60
        p.fovV = 90

import os
def saveImageForDebugging(img, name):
    path = "debug/screens/"
    if not os.path.exists(path):
        os.makedirs(path)
    img.save(path+name+".png")
    print datetime.now(),"Saving "+name+" to "+path+name+".png"

if __name__ == "__main__":
    runTest(False)
