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
import ShapeRecognition
import cv2
from CommandQueue import CommandQueue
from VehicleApi import QuadcopterApi, Thread
from dronekit_sitl import SITL

import Tkinter

vehicle = None
sitl = None
root = None
modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
modeCamera = VehicleApi.FRONT
searchedObject = None
foundObjColor = None


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
m - set mode of vehicle to Guided
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
    window.cameraFromVehicle(True)
    #window.cameraC.moveFRU(f=-2)

if __name__ == "__main__":
    runTest(True)

DEBUG_MOVEMENT = True
DEBUG_MOVEMENT_DrawPhotoPoints = False
IGNORE_POPUP_IMAGES = True
BUILDING_HEIGHT = 6

import math
import ImageApi
from ImageProcessor import ImageProcessor, RED
from TestApplication.Control import PARAMETER_FILE_NAME
from Utils import getCentroid
from Utils import calcMoveToTargetHorizont
from Utils import calcHeadingChangeForFrontPhoto
import GnuplotDrawer


def runRecMovementTest(sitlTest):
    global DEBUG_MOVEMENT
    global searchedObject
    global foundObjColor
    # todo: make it work with real drone

    clearDebugInfo()

    ###################
    # createGUI() and vehicle
    createVehicle(sitlTest)
    veh = vehicle
    window = Visualizer.createWindow(veh)
    if not isinstance(veh, VehicleApi.QuadcopterApi):
        return

    veh.commandQueue.shouldMakeAdjustment(False)

    if not sitlTest:
        DEBUG_MOVEMENT = False
    else:
        veh.supressMessages(all=True)
        window.cameraFromVehicle(True)
        window.debug_OpenGL = False

    f = ImageApi.Filter()
    img = f.loadCvImage("TestPictures/searched_object.png")
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    vectorizedPolygonSet = processor.getVectorRepresentation(img, f.prepareImage, RED)
    # checking if we have only one searched object
    if len(vectorizedPolygonSet['vect']) != 1:
        raise "Exactly one searched object should be provided"
    
    searchedObject = vectorizedPolygonSet['vect'][0]  
    
    if DEBUG_MOVEMENT:
        print "=========================="
        print searchedObject
        print vectorizedPolygonSet['domain']
        print "=========================="
        gp = GnuplotDrawer.printVectorPicture([searchedObject], vectorizedPolygonSet['domain'][:2]) 
        GnuplotDrawer.saveToFile(gp,"SearchedObject",vectorizedPolygonSet['domain'][:2])

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

    #feed.veh.commandQueue.goto(0., 0., 10, True)
    scanObject(feed)

    MovementTracker.stop()
    veh.close()

    #render trajectory in OpenGL
    if sitlTest:
        ren = window.obtainModelObject(modelType='LINES')   # LINE_STRIP
        ENUPath = MovementTracker.getPath()
        for i in range(0,len(ENUPath)-1):
            ENUPath[i] = Visualizer.tENUtoXYZ(ENUPath[i])
        ren.data = ENUPath
        ren.color = np.array([1.0,1.0,1.0])
        ren.render = False



def findObjectsOnScene(feed):
    ###################
    # raise heigh enough
    feed.veh.commandQueue.goto(0., 0., 45, False)
    # feed.veh.commandQueue.changeHeading(0, False)
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
    rawImage = ImageApi.PILImageToCV(img)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage,"ImageSceneAbove")
        if not IGNORE_POPUP_IMAGES:
            cv2.imshow('image', rawImage)
    # img.save("image_test.jpg")
    

    if DEBUG_MOVEMENT and DEBUG_MOVEMENT_DrawPhotoPoints:
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
        gp =GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain']) 
        GnuplotDrawer.saveToFile(gp,"ImageSceneAboveVec",feed.videoFeed.getWindowSize())


    feed.veh.commandQueue.goto(0,0,30,False)
    feed.veh.commandQueue.confirm()

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
    rawImage = ImageApi.PILImageToCV(img)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage,"ImageForRecogAbove_"+str(id))
        if not IGNORE_POPUP_IMAGES:
            cv2.imshow('image', rawImage)

    ###################
    # parse photo
    flt = ImageApi.Filter()
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    sourceVectors = processor.getVectorRepresentation(rawImage, flt.prepareImage)

    if DEBUG_MOVEMENT:
        gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])
        GnuplotDrawer.saveToFile(gp,"ImageRecogAboveVec_"+str(id),feed.videoFeed.getWindowSize())

    global searchedObject
    global foundObjColor
    ###################
    # recognize
    found = ShapeRecognition.findSinglePattern(searchedObject, sourceVectors['vect'])
    if found:
        print "OBJECT FOUND!"
        foundObjIdx = found[0] 
        foundObjColor = sourceVectors['color'][foundObjIdx]
        return True



def scanObject(feed):

    global foundObjColor
    if foundObjColor is None:
        raise RuntimeError("Searched object wasn't found!")

    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)
    feed.videoFeed.cameraC.lookAtEulerExt(x=math.radians(-90))
    sleep(0.5)
    photo = feed.videoFeed.grabFrame()
    photoDirection = feed.veh.quad.heading
    photoAlt = feed.veh.getPositionVector()[2]
    photoPos = feed.veh.getPositionVector()
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    rawImage = ImageApi.PILImageToCV(img)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage,"ImageSearchedObject")
        if not IGNORE_POPUP_IMAGES:
            cv2.imshow('image', rawImage)

    ###################
    # parse photo
    
    flt = ImageApi.Filter()
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    sourceVectors = processor.getVectorRepresentation(rawImage, flt.prepareImage, foundObjColor)
    objectIndex = 0
    if len(sourceVectors['vect']) < objectIndex + 1:
        print "VECTOR REPRESENTATION HAS INVALID AMOUNT OF OBJECTS ... RETURNING"
        feed.veh.setCameraAim(VehicleApi.FRONT)
        feed.window.cameraC.lookAtEulerExt(x=0)
        return
    print "Found objects: ", len(sourceVectors['vect'])
    print "Scanning ", objectIndex, ":"
    print sourceVectors['vect'][objectIndex]
    result = calcHeadingChangeForFrontPhoto(sourceVectors['vect'][objectIndex], sourceVectors['vect'],
                                            photoAlt, BUILDING_HEIGHT,
                                            feed.fovH,feed.fovV,
                                            mapWidth=feed.imgWidth, mapHeight=feed.imgHeight,
                                            photoHeight=0.5)
    photoPoint, headingChange, secondPhotoPoint, secondHeadingChange, chosenEdge = result

    if DEBUG_MOVEMENT:
        GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])

    dposToFrontPhotoPoint = calcMoveToTargetHorizont(photoPoint, photoAlt, photoDirection, feed.fovV, feed.fovH,
                                                resolutionX=feed.imgWidth,
                                                resolutionY=feed.imgHeight)
    dposToFrontPhotoPoint = np.array(dposToFrontPhotoPoint)

    dposToSidePhotoPoint = calcMoveToTargetHorizont(secondPhotoPoint, photoAlt, photoDirection, feed.fovV, feed.fovH,
                                                resolutionX=feed.imgWidth,
                                                resolutionY=feed.imgHeight)
    dposToSidePhotoPoint = np.array(dposToSidePhotoPoint)
    secondPhotoDirection = photoDirection + float(secondHeadingChange)

    scan = scanData()

    feed.veh.commandQueue.changeHeading(photoDirection + float(headingChange), False)
    feed.veh.commandQueue.confirm()

    sleep(0.5)
    photo = feed.videoFeed.grabFrame()
    photoDirection = feed.veh.quad.heading
    scan.abovePosition = feed.veh.getPositionVector()
    scan.aboveDirection = photoDirection
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    rawImage = ImageApi.PILImageToCV(img)
    scan.aboveScan = rawImage
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage, "ImageForScanAbove")
        if not IGNORE_POPUP_IMAGES:
            cv2.imshow('image', rawImage)

    feed.veh.setCameraAim(VehicleApi.FRONT)
    feed.videoFeed.cameraC.lookAtEulerExt(x=math.radians(0))
    sleep(0.5)

    feed.veh.commandQueue.goto(dposToFrontPhotoPoint[1], dposToFrontPhotoPoint[0], 0.5, False)  # <-------
    feed.veh.commandQueue.confirm()


    ###################
    # make a front photo
    photo = feed.videoFeed.grabFrame()
    scan.frontDirection = feed.veh.quad.heading
    scan.frontPosition = feed.veh.getPositionVector()
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    rawImage = ImageApi.PILImageToCV(img)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage,"ImageScanFront")
        if not IGNORE_POPUP_IMAGES:
            cv2.imshow('image', rawImage)

    if DEBUG_MOVEMENT and DEBUG_MOVEMENT_DrawPhotoPoints:
        controlPoint = feed.videoFeed.obtainModelObject()
        pos = Visualizer.tENUtoXYZ(feed.veh.getPositionVector())
        print "Making photo at: ", pos
        controlPoint.data = [pos]
        controlPoint.color = np.array([0., 0., 1.])
        controlPoint.render = True

    ###################
    # go to other position
    feed.veh.commandQueue.goto(dposToSidePhotoPoint[1], dposToSidePhotoPoint[0], 0.5, False)  # <-------
    feed.veh.commandQueue.changeHeading(secondPhotoDirection, False)
    feed.veh.commandQueue.confirm()

    ###################
    # make a side photo

    feed.veh.setCameraAim(VehicleApi.FRONT)
    feed.videoFeed.cameraC.lookAtEulerExt(x=math.radians(0))
    sleep(0.5)
    photo = feed.videoFeed.grabFrame()
    scan.sideDirection = feed.veh.quad.heading
    scan.sidePosition = feed.veh.getPositionVector()
    img = ImageApi.PILimageFromArray(photo, feed.videoFeed.getWindowSize(), "RGBA", True)
    rawImage = ImageApi.PILImageToCV(img)
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage, "ImageScanSide")
        if not IGNORE_POPUP_IMAGES:
            cv2.imshow('image', rawImage)
    scan.sideScan = rawImage

    if DEBUG_MOVEMENT and DEBUG_MOVEMENT_DrawPhotoPoints:
        controlPoint = feed.videoFeed.obtainModelObject()
        pos = Visualizer.tENUtoXYZ(feed.veh.getPositionVector())
        print "Making photo at: ", pos
        controlPoint.data = [pos]
        controlPoint.color = np.array([0., 0., 1.])
        controlPoint.render = True

    ###################
    # reset camera
    feed.veh.setCameraAim(VehicleApi.FRONT)
    feed.videoFeed.cameraC.lookAtEulerExt(x=0)

    ###################
    # build model


class feedInfo(object):
    def __init__(self):
        self.videoFeed = None
        self.veh = None
        self.imgWidth = 0
        self.imgHeight = 0
        self.fovH = 60
        self.fovV = 90

class scanData(object):
    def __init__(self):
        self.frontScan = None
        self.frontPosition = None
        self.frontDirection = None
        self.sideScan = None
        self.sidePosition = None
        self.sideDirection = None
        self.aboveScan = None
        self.abovePosition = None
        self.aboveDirection = None

import os
def saveImageForDebugging(img, name):
    path = "debug/screens/"
    if not os.path.exists(path):
        os.makedirs(path)
    cv2.imwrite(path+name+".jpg", img)    
    print datetime.now(),"Saving "+name+" to "+path+name+".jpg"
import os, shutil

def emptyFolder(path):
    folder = path
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def clearDebugInfo():
    emptyFolder("debug/screens")
    emptyFolder("debug/vecs")

