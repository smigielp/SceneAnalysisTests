from time import sleep

import numpy as np
from datetime import datetime

import MovementTracker
import VehicleApi
#import ShapeRecognition
import FuzzyShapeRecognition
import cv2
from CommandQueue import CommandQueue
from VehicleApi import QuadcopterApi, Thread
from dronekit_sitl import SITL

import os
import sys
import msvcrt
import ImageApi
from ImageProcessor import ImageProcessor
#from Control import PARAMETER_FILE_NAME
from Utils import getCentroid
from Utils import calcMoveToTargetHorizont
from Utils import calcHeadingChangeForFrontPhoto
import GnuplotDrawer

import Tkinter
from operator import pos


PARAMETER_FILE_NAME = "Parameters/algorithms_parameters.txt"

DEBUG_MOVEMENT = True
DEBUG_MOVEMENT_DrawPhotoPoints = True
IGNORE_POPUP_IMAGES = False
BUILDING_HEIGHT = 1.5
WAITING_TIME = 3.0

IMAGE_WIDTH = 720
IMAGE_HEIGHT = 576
FIELD_OF_VIEW_HORIZONTAL = 28.6
FIELD_OF_VIEW_VERTICAL = 23


vehicle = None
sitl = None
root = None
control = None
modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
modeCamera = VehicleApi.FRONT
searchedObject = None
foundObjColor = None
camera = ImageApi.CameraApi2()
filter = ImageApi.Filter()


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


def runTest(sitlTest):
    createGUI()
    createVehicle(sitlTest)


def createGUI():
    thread = Thread(name='ControlPanelThread')
    thread.run = _createGUI
    thread.start()
    



def runRecMovementTest(appControl, sitlTest=False):
    global DEBUG_MOVEMENT
    global searchedObject
    global foundObjColor
    global control
    
    #clearDebugInfo()
    
    control = appControl

    ###################
    # createGUI() and vehicle
    veh = createVehicle(sitlTest)

    print "setting camera parameters"
    feed = feedInfo()
    feed.veh = veh
    feed.imgWidth = IMAGE_WIDTH
    feed.imgHeight = IMAGE_HEIGHT
    feed.fovH = FIELD_OF_VIEW_HORIZONTAL
    feed.fovV = FIELD_OF_VIEW_VERTICAL

    print "finding objects..."
    findObjectsOnScene(feed)

    #feed.veh.commandQueue.goto(0., 0., 10, True)
    scanObject(feed)

    MovementTracker.stop()
    veh.close()



def createVehicle(sitlTest):
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
        vehicle.takeoff(4)
        vehicle.getState()
    else:
        vehicle = QuadcopterApi()
        vehicle.setMode('GUIDED')
        
        
        vehicle.setCameraAim(VehicleApi.FRONT)
        
        '''
        imageOK = 'n'
        while(imageOK != 'y'):
            rawImage = camera.getFrame()
            filter.showImage(rawImage)
            ###################
            # parse photo
            processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
            sourceVectors = processor.getVectorRepresentation(rawImage, filter.imagePreprocess, filter.imageEdgeDetect)
            if DEBUG_MOVEMENT:
                gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain']) 
                GnuplotDrawer.saveToFile(gp,"ImageSceneAboveVec",(720,540))
            
            imageOK = str(raw_input("Is the image OK? (y/n) >"))
            print imageOK
        '''
                
        print "arming robot..."
        vehicle.arm()         
                
        #filter.showImage(rawImage)
        #vehicle.getState()
    vehicle.commandQueue.shouldMakeAdjustment(True)
    MovementTracker.start(vehicle)
    return vehicle


    

def findObjectsOnScene(feed):
    ###################
    # take-off and rise high enough
    targetAlt = 5.0
    print "takin off to altitude: ", targetAlt
    vehicle.takeoff(targetAlt)   

    feed.veh.commandQueue.changeHeading(0, False)
    feed.veh.commandQueue.confirm()

    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)    
    sleep(WAITING_TIME)
    
    photoDirection = feed.veh.quad.heading
    photoAltitude = feed.veh.getPositionVector()[2]
    print "photo direction: ", photoDirection
    print "photo altitude: ", photoAltitude

    sourceVectors = getImageVectorized(feed, imageName="ImageSceneAbove")
    
    points = []
    for objectIndex in range(0, len(sourceVectors['vect'])):
        targetCoords = getCentroid(sourceVectors['vect'][objectIndex])
        points.append(targetCoords)
    
    targetAlt = 4.0
    print "lowering down to ", targetAlt
    feed.veh.commandQueue.goto(0,0,targetAlt,False)
    feed.veh.commandQueue.confirm()

    for objectIndex in range(0, len(points)):
        points[objectIndex] = calcMoveToTargetHorizont(points[objectIndex], photoAltitude, photoDirection, feed.fovV, feed.fovH,
                                                       resolutionX=feed.imgWidth,
                                                       resolutionY=feed.imgHeight)

    objectNum = feed.veh.commandQueue.visitPoints(points, relativeToStartingPos=True, callbackOnVisited=recognizeObject,
                                                  callbackArg=feed)

    ###################
    # reset camera
    feed.veh.setCameraAim(VehicleApi.FRONT)



def recognizeObject(id, feed):
    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)    
    sleep(WAITING_TIME)
        
    sourceVectors = getImageVectorized(feed, imageName="ImageForRecogAbove_"+str(id))
    
    photoDirection = feed.veh.quad.heading
    photoAltitude = feed.veh.getPositionVector()[2]    
    print "taking photo from altitude:", photoAltitude, "at direction: ", photoDirection
        
    global searchedObject
    global foundObjColor
    ###################
    # recognize
    found = FuzzyShapeRecognition.findSinglePattern(searchedObject, sourceVectors['vect'])
    if found:
        print "OBJECT FOUND!"
        foundObjIdx = found[0] 
        foundObjColor = sourceVectors['color'][foundObjIdx]
        return True
    else:
        print "NOT THIS ONE..."
        return False



def scanObject(feed):

    global foundObjColor
    if foundObjColor is None:
        raise RuntimeError("Searched object wasn't found!")

    ###################
    # make a photo
    feed.veh.setCameraAim(VehicleApi.DOWN)    
    sleep(WAITING_TIME)
    
    sourceVectors = getImageVectorized(feed, imageName="ImageForRecogAbove_"+str(id))
    
    photoDirection = feed.veh.quad.heading
    photoAltitude = feed.veh.getPositionVector()[2]
    #photoPos = feed.veh.getPositionVector()    
    print "taking photo from altitude:", photoAltitude, "at direction: ", photoDirection
    
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
                                            photoAltitude, BUILDING_HEIGHT,
                                            feed.fovH,feed.fovV,
                                            mapWidth=feed.imgWidth, mapHeight=feed.imgHeight,
                                            photoHeight=0.5)
    photoPoint, headingChange, secondPhotoPoint, secondHeadingChange, chosenEdge = result

    if DEBUG_MOVEMENT:
        GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])

    dposToFrontPhotoPoint = calcMoveToTargetHorizont(photoPoint, photoAltitude, photoDirection, feed.fovV, feed.fovH,
                                                resolutionX=feed.imgWidth,
                                                resolutionY=feed.imgHeight)
    dposToFrontPhotoPoint = np.array(dposToFrontPhotoPoint)

    dposToSidePhotoPoint = calcMoveToTargetHorizont(secondPhotoPoint, photoAltitude, photoDirection, feed.fovV, feed.fovH,
                                                resolutionX=feed.imgWidth,
                                                resolutionY=feed.imgHeight)
    dposToSidePhotoPoint = np.array(dposToSidePhotoPoint)
    secondPhotoDirection = photoDirection + float(secondHeadingChange)


    ##############################################
    # Scanning object...
    scan = scanData()

    #######################
    # make a top photo
    feed.veh.commandQueue.changeHeading(photoDirection + float(headingChange), False)
    feed.veh.commandQueue.confirm()
    sleep(WAITING_TIME)
    
    rawImage = getRawImage(feed, imageName="ImageForScanAbove")
    scan.abovePosition = feed.veh.getPositionVector()
    scan.aboveDirection = feed.veh.quad.heading
    scan.aboveScan = rawImage
    
    
    #######################
    # make a front photo
    feed.veh.setCameraAim(VehicleApi.FRONT)
    sleep(WAITING_TIME)

    feed.veh.commandQueue.goto(dposToFrontPhotoPoint[1], dposToFrontPhotoPoint[0], 0.5*BUILDING_HEIGHT, False)  # <-------
    feed.veh.commandQueue.confirm()

    rawImage = getRawImage(feed, imageName="ImageScanFront")
    scan.frontDirection = feed.veh.quad.heading
    scan.frontPosition = feed.veh.getPositionVector()        
    scan.frontScan = rawImage
    
    
    #######################
    # make a side photo
    feed.veh.commandQueue.goto(dposToSidePhotoPoint[1], dposToSidePhotoPoint[0], 0.5*BUILDING_HEIGHT, False)  # <-------
    feed.veh.commandQueue.changeHeading(secondPhotoDirection, False)
    feed.veh.commandQueue.confirm()

    feed.veh.setCameraAim(VehicleApi.FRONT)
    sleep(WAITING_TIME)
    
    rawImage = getRawImage(feed, imageName="ImageScanSide")
    scan.sideDirection = feed.veh.quad.heading
    scan.sidePosition = feed.veh.getPositionVector()
    scan.sideScan = rawImage

    ###################
    # reset camera
    feed.veh.setCameraAim(VehicleApi.FRONT)

    flt = ImageApi.Filter()
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    
    
    
    
    # Preparing images for 3D model building
    # TODO - rework, probably not doing what it's supposed to    
    sourceVectors = processor.getVectorRepresentation(scan.frontScan, flt.imagePreprocess, flt.imageEdgeDetect, foundObjColor)
    points = []
    for objectIndex in range(0, len(sourceVectors['vect'])):
        targetCoords = getCentroid(sourceVectors['vect'][objectIndex])
        points.append(targetCoords)
    if DEBUG_MOVEMENT:
        gp =GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])
        GnuplotDrawer.saveToFile(gp,"FrontScanVec",feed.videoFeed.getWindowSize())
    scan.frontScan = points

    sourceVectors = processor.getVectorRepresentation(scan.sideScan, flt.imagePreprocess, flt.imageEdgeDetect, foundObjColor)
    points = []
    for objectIndex in range(0, len(sourceVectors['vect'])):
        targetCoords = getCentroid(sourceVectors['vect'][objectIndex])
        points.append(targetCoords)
    if DEBUG_MOVEMENT:
        gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])
        GnuplotDrawer.saveToFile(gp, "SideScanVec", feed.videoFeed.getWindowSize())
    scan.sideScan = points

    sourceVectors = processor.getVectorRepresentation(scan.aboveScan, flt.imagePreprocess, flt.imageEdgeDetect, foundObjColor)
    points = []
    for objectIndex in range(0, len(sourceVectors['vect'])):
        targetCoords = getCentroid(sourceVectors['vect'][objectIndex])
        points.append(targetCoords)
    if DEBUG_MOVEMENT:
        gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])
        GnuplotDrawer.saveToFile(gp, "AboveScanVec", feed.videoFeed.getWindowSize())
    scan.aboveScan = points
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


def saveImageForDebugging(img, name):
    path = "debug/screens/"
    if not os.path.exists(path):
        os.makedirs(path)
    cv2.imwrite(path+name+".jpg", img)    
    print datetime.now(),"Saving "+name+" to "+path+name+".jpg"



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


def getImageVectorized(feed, imageName):
    imageOK = 'n'
    while(imageOK != 'y'):
        rawImage = camera.getFrame()
        filter.showImage(rawImage)

        processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
        sourceVectors = processor.getVectorRepresentation(rawImage, filter.imagePreprocess, filter.imageEdgeDetect)
        if DEBUG_MOVEMENT:
            gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain']) 
            
        imageOK = str(raw_input("Is the image OK? (y/n) >"))
    
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage, imageName) 
        GnuplotDrawer.saveToFile(gp, imageName+"Vec", (feed.imgWidth,feed.imgHeight))
    return sourceVectors
 
        
def getRawImage(feed, imageName):
    imageOK = 'n'
    while(imageOK != 'y'):
        rawImage = camera.getFrame()
        filter.showImage(rawImage)

        processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
        sourceVectors = processor.getVectorRepresentation(rawImage, filter.imagePreprocess, filter.imageEdgeDetect)
        if DEBUG_MOVEMENT:
            gp = GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain']) 
            
        imageOK = str(raw_input("Is the image OK? (y/n) >"))
    
    if DEBUG_MOVEMENT:
        saveImageForDebugging(rawImage, imageName) 
        GnuplotDrawer.saveToFile(gp, imageName+"Vec", (feed.imgWidth,feed.imgHeight))
        
    return rawImage


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


if __name__ == "__main__":
    runRecMovementTest(appControl=None, sitlTest=False)



